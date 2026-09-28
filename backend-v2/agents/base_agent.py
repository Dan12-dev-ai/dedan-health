from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging
import os
from datetime import datetime
from contextlib import contextmanager
import json
import re

from langchain_core.language_models.llms import LLM
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import structlog

try:  # langchain >= 0.2 exposes memory separately; langchain 1.x drops it.
    from langchain.memory import ConversationBufferMemory  # type: ignore
except ImportError:  # pragma: no cover - graceful degradation
    ConversationBufferMemory = None

try:  # removed in langchain 1.x
    from langchain.callbacks import get_openai_callback  # type: ignore
except ImportError:  # pragma: no cover - use local shim below
    get_openai_callback = None

try:
    from models_v2 import AgentInput, AgentOutput, AgentType, Language
except ImportError:  # pragma: no cover - package-relative fallback
    from ..models_v2 import AgentInput, AgentOutput, AgentType, Language


# Configure structured logging
logger = structlog.get_logger()


class _TokenUsageTracker:
    """Stand-in for langchain's removed `get_openai_callback()` context manager.

    Agents only read `.total_tokens` and `.total_cost`, so we expose those and
    populate them from the LLM response `usage_metadata` when available.
    """

    def __init__(self) -> None:
        self.total_tokens: int = 0
        self.total_cost: float = 0.0
        self.prompt_tokens: int = 0
        self.completion_tokens: int = 0

    def add_usage(self, usage: Optional[Dict[str, Any]]) -> None:
        if not usage:
            return
        self.prompt_tokens += int(usage.get("prompt_tokens", 0) or 0)
        self.completion_tokens += int(usage.get("completion_tokens", 0) or 0)
        self.total_tokens = self.prompt_tokens + self.completion_tokens


@contextmanager
def _token_tracker():
    tracker = _TokenUsageTracker()
    yield tracker


if get_openai_callback is None:
    get_openai_callback = _token_tracker


# ---------------------------------------------------------------------------
# Offline / credential-aware degradation.
#
# Agents call ChatOpenAI directly for *reasoning prose only* — every
# structured field (triage level, risk flags, differentials) is produced by
# the rule-based `_process_agent_specific_logic` in each agent. So when no
# usable credential is configured we must not issue a network call that will
# 401; we return deterministic reasoning text instead and stay fully
# functional offline.
# ---------------------------------------------------------------------------
_PLACEHOLDER_MARKERS = (
    "test-key", "test_key", "your-", "your_", "changeme",
    "placeholder", "xxx", "<api", "dummy", "example",
)


def _has_usable_credential(key: Optional[str]) -> bool:
    if not key:
        return False
    lowered = (key or "").strip().lower()
    if not lowered:
        return False
    return not any(marker in lowered for marker in _PLACEHOLDER_MARKERS)


def _should_degrade_to_offline() -> bool:
    """True when agents must not make live LLM calls.

    Mirrors `ProviderFactory._should_use_offline()` so both halves of the
    platform agree on the mode:
      * explicit AI_PROVIDER_MODE=offline|mock|local|rules -> offline
      * AI_FORCE_LIVE=1 -> always live
      * otherwise offline iff no usable GEMINI/OPENAI credential exists
    """
    mode = os.getenv("AI_PROVIDER_MODE", "").strip().lower()
    if mode in ("offline", "mock", "local", "rules"):
        return True
    if os.getenv("AI_FORCE_LIVE", "").strip().lower() in ("1", "true", "yes"):
        return False
    return not (
        _has_usable_credential(os.getenv("GEMINI_API_KEY"))
        or _has_usable_credential(os.getenv("OPENAI_API_KEY"))
    )


class _CompatChain:
    """Langchain-1.x replacement for the removed `LLMChain`.

    Preserves the `arun(**kwargs) -> str` contract used by BaseDEDANAgent but
    executes the supported LCEL `prompt | llm` pipeline instead.
    """

    def __init__(self, llm, prompt, tracker_holder: Optional[Dict[str, Any]] = None):
        self.llm = llm
        self.prompt = prompt
        self._tracker_holder = tracker_holder if tracker_holder is not None else {}
        self._pipeline = prompt | llm

    async def arun(self, **kwargs: Any) -> str:
        # Offline mode: never hit the network. The caller only uses this
        # string as narrative `reasoning`; structured output comes from the
        # agent's rule-based `_process_agent_specific_logic`.
        if _should_degrade_to_offline():
            return self._offline_reasoning(kwargs)

        # Coerce plain-string lists for MessagesPlaceholder variables.
        for key, value in list(kwargs.items()):
            if isinstance(value, list) and value and not hasattr(value[0], "type"):
                kwargs[key] = [HumanMessage(content=str(v)) for v in value]

        try:
            result = await self._pipeline.ainvoke(kwargs)
        except Exception as exc:  # network / auth / provider outage
            # Degrade rather than fail the whole triage: safety rules and
            # differentials are computed locally regardless of the LLM.
            logger.warning(
                f"LLM call failed ({type(exc).__name__}); using offline reasoning"
            )
            return self._offline_reasoning(kwargs)

        usage = getattr(result, "usage_metadata", None)
        if usage is None:
            usage = getattr(getattr(result, "response_metadata", None), "token_usage", None)
        tracker = self._tracker_holder.get("tracker")
        if usage and isinstance(tracker, _TokenUsageTracker):
            tracker.add_usage(usage)

        content = getattr(result, "content", result)
        if isinstance(content, list):
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            )
        return str(content)

    @staticmethod
    def _offline_reasoning(kwargs: Dict[str, Any]) -> str:
        """Deterministic narrative used when no LLM is reachable.

        Explicitly labelled so no reader can mistake it for model output.
        """
        symptoms = str(kwargs.get("symptoms", "")).strip() or "not specified"
        return (
            "OFFLINE ASSESSMENT (no LLM credential configured). "
            "Symptoms considered: "
            f"{symptoms[:300]}. "
            "Structured triage level, risk flags and differentials below were "
            "derived by DEDAN's local rule-based safety engine, not by a "
            "language model. Confirm the assessment with a qualified clinician."
        )


class BaseDEDANAgent(ABC):
    """
    Base class for all DEDAN agents following the agent-orchestrated architecture.
    Each agent is responsible for a specific aspect of the triage process.
    """
    
    def __init__(
        self,
        agent_type: AgentType,
        llm: Optional[LLM] = None,
        temperature: float = 0.3,
        max_tokens: int = 1000,
        enable_memory: bool = False
    ):
        self.agent_type = agent_type
        self.llm = llm or ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=temperature,
            max_tokens=max_tokens,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        self.enable_memory = enable_memory
        if enable_memory and ConversationBufferMemory is not None:
            self.memory = ConversationBufferMemory()
        else:
            # langchain 1.x removed ConversationBufferMemory. Agents never read
            # `self.memory`, so None is a safe degradation.
            self.memory = None
        self.prompt_template = self._build_prompt_template()
        # Per-invocation token tracker surfaced to `_CompatChain` via this holder.
        self._chain_tracker: Dict[str, Any] = {}
        self.chain = _CompatChain(self.llm, self.prompt_template, self._chain_tracker)

        logger.info(f"Initialized {agent_type.value} agent")
    
    @abstractmethod
    def _build_prompt_template(self) -> ChatPromptTemplate:
        """Build the prompt template specific to this agent."""
        pass
    
    @abstractmethod
    def _process_agent_specific_logic(self, input_data: AgentInput) -> Dict[str, Any]:
        """Process the agent-specific logic and return results."""
        pass
    
    @abstractmethod
    def _validate_output(self, output: Dict[str, Any]) -> bool:
        """Validate the agent output before returning."""
        pass
    
    def _extract_confidence_score(self, response_text: str) -> float:
        """Extract confidence score from agent response."""
        try:
            # Look for confidence score in the response
            import re
            confidence_match = re.search(r'confidence[:\s]*([0-9.]+)', response_text.lower())
            if confidence_match:
                confidence = float(confidence_match.group(1))
                return min(max(confidence, 0.0), 1.0)  # Clamp between 0 and 1
        except:
            pass
        
        # Default confidence based on response length and clarity
        if len(response_text) > 100:
            return 0.8
        elif len(response_text) > 50:
            return 0.6
        else:
            return 0.4
    
    def _extract_risk_flags(self, response_text: str, input_data: AgentInput) -> list[str]:
        """Extract risk flags from agent response."""
        risk_flags = []
        
        # Common risk patterns
        risk_patterns = [
            r'chest\s*pain',
            r'breathing\s*difficulty',
            r'shortness\s*of\s*breath',
            r'unconscious',
            r'seizure',
            r'stroke',
            r'bleeding',
            r'fever.*high',
            r'pregnancy.*complication',
            r'diabetes.*complication',
            r'hypertension.*crisis'
        ]
        
        response_lower = response_text.lower()
        for pattern in risk_patterns:
            if re.search(pattern, response_lower):
                risk_flags.append(pattern.replace(r'\s*', ' '))
        
        # Add patient-specific risk flags
        if input_data.patient.age > 65:
            risk_flags.append("elderly_patient")
        
        if input_data.patient.pregnancy_status:
            risk_flags.append("pregnancy")
        
        for condition in input_data.patient.chronic_conditions:
            risk_flags.append(f"chronic_{condition}")
        
        return list(set(risk_flags))  # Remove duplicates
    
    def _get_language_specific_context(self, language: Language) -> str:
        """Get language-specific context for the agent."""
        language_contexts = {
            Language.EN: "Respond in clear, simple English suitable for general healthcare understanding.",
            Language.SW: "Jibu kwa Kiswahili cha wazi na rahisi unaoweza kueleweka kwa afya ya jumuiya.",
            Language.AM: "በግልጽምነት በሚተረጋገው የአማርኛ ቋንቋ ይመልሱ።",
            Language.ES: "Responda en español claro y simple adecuado para comprensión médica general.",
            Language.FR: "Répondez en français clair et simple adapté à la compréhension médicale générale."
        }
        
        return language_contexts.get(language, language_contexts[Language.EN])
    
    def _get_region_specific_context(self, location: Optional[str]) -> str:
        """Get region-specific context for the agent."""
        if not location:
            return ""
        
        location_lower = location.lower()
        
        # Regional considerations
        if any(country in location_lower for country in ["kenya", "tanzania", "uganda"]):
            return "Consider local endemic diseases: malaria, typhoid, and limited access to advanced diagnostics."
        elif any(country in location_lower for country in ["ethiopia", "eritrea"]):
            return "Consider local endemic diseases: malaria, typhoid, malnutrition-related conditions."
        elif any(country in location_lower for country in ["nigeria", "ghana", "senegal"]):
            return "Consider local endemic diseases: malaria, sickle cell disease, Lassa fever."
        elif any(country in location_lower for country in ["india", "bangladesh", "pakistan"]):
            return "Consider local endemic diseases: dengue, typhoid, tuberculosis, and air pollution-related conditions."
        elif any(country in location_lower for country in ["brazil", "mexico", "colombia"]):
            return "Consider local endemic diseases: dengue, Zika, Chagas disease, and tropical infections."
        
        return ""
    
    async def process(self, input_data: AgentInput) -> AgentOutput:
        """
        Main processing method for the agent.
        Orchestrates the entire agent workflow.
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Processing {self.agent_type.value} for session {input_data.session_id}")
            
            # Build context for the agent
            context = self._build_context(input_data)
            
            # Process agent-specific logic
            # Reset per-call tracker so `_CompatChain` reports fresh usage.
            cb = _TokenUsageTracker()
            self._chain_tracker["tracker"] = cb
            try:
                # Generate response using the chain
                response = await self.chain.arun(
                    session_id=input_data.session_id,
                    patient_info=json.dumps(input_data.patient.dict(), indent=2),
                    symptoms=input_data.symptoms.symptoms,
                    language_context=self._get_language_specific_context(input_data.symptoms.language),
                    region_context=self._get_region_specific_context(input_data.patient.location),
                    **context
                )
            finally:
                self._chain_tracker.pop("tracker", None)

            # Log token usage
            logger.info(f"Token usage for {self.agent_type.value}: {cb.total_tokens} tokens, cost: ${cb.total_cost:.4f}")
            
            # Extract confidence score and risk flags
            confidence_score = self._extract_confidence_score(response)
            risk_flags = self._extract_risk_flags(response, input_data)
            
            # Process agent-specific logic
            agent_result = self._process_agent_specific_logic(input_data)
            
            # Validate output
            if not self._validate_output(agent_result):
                logger.error(f"Invalid output from {self.agent_type.value}")
                raise ValueError("Agent output validation failed")
            
            # Create agent output
            output = AgentOutput(
                agent_type=self.agent_type,
                session_id=input_data.session_id,
                confidence_score=confidence_score,
                reasoning=response,
                result=agent_result,
                risk_flags=risk_flags,
                metadata={
                    "processing_time": (datetime.utcnow() - start_time).total_seconds(),
                    "tokens_used": cb.total_tokens,
                    "model": self.llm.model_name if hasattr(self.llm, 'model_name') else "unknown"
                }
            )
            
            logger.info(f"Completed {self.agent_type.value} processing for session {input_data.session_id}")
            return output
            
        except Exception as e:
            logger.error(f"Error in {self.agent_type.value} processing: {str(e)}")
            raise
    
    def _build_context(self, input_data: AgentInput) -> Dict[str, Any]:
        """Build additional context for the agent."""
        context = {}
        
        # Add chronic care data if available
        if hasattr(input_data, 'chronic_care_data') and input_data.chronic_care_data:
            context["chronic_care_info"] = json.dumps(input_data.chronic_care_data.dict(), indent=2)
        
        # Add home measurements if available
        if hasattr(input_data, 'home_measurements') and input_data.home_measurements:
            measurements_json = json.dumps([m.dict() for m in input_data.home_measurements], indent=2)
            context["home_measurements"] = measurements_json
        
        # Add any additional context
        context.update(input_data.context)
        
        return context
    
    def get_agent_capabilities(self) -> Dict[str, Any]:
        """Return the capabilities of this agent."""
        return {
            "agent_type": self.agent_type.value,
            "supports_memory": self.enable_memory,
            "model": self.llm.model_name if hasattr(self.llm, 'model_name') else "unknown",
            "temperature": getattr(self.llm, 'temperature', 0.3),
            "max_tokens": getattr(self.llm, 'max_tokens', 1000)
        }
