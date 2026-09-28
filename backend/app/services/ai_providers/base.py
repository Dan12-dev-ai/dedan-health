from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import base64


class Modality(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


@dataclass
class ImageInput:
    image_data: str  # base64 encoded
    mime_type: str
    filename: str = ""
    quality_score: float = 0.0


@dataclass
class PatientContext:
    age: Optional[int] = None
    sex: Optional[str] = None
    location: Optional[str] = None
    pregnancy_status: Optional[bool] = None
    chronic_conditions: List[str] = None
    medications: List[str] = None
    allergies: List[str] = None
    language: str = "en"

    def __post_init__(self):
        if self.chronic_conditions is None:
            self.chronic_conditions = []
        if self.medications is None:
            self.medications = []
        if self.allergies is None:
            self.allergies = []


@dataclass
class ConversationTurn:
    role: str  # "user" or "assistant"
    content: str
    modality: Modality = Modality.TEXT


@dataclass
class AnalysisResult:
    request_id: str
    urgency: str
    recommended_next_step: str
    image_assessment: Optional[Dict[str, Any]] = None
    medical_information: List[Dict[str, Any]] = None
    treatment_information: List[Dict[str, Any]] = None
    warning_signs: List[str] = None
    follow_up_questions: List[str] = None
    sources: List[Dict[str, Any]] = None
    uncertainty: str = ""
    requires_professional_review: bool = True
    safety_notice: str = ""
    confidence_score: float = 0.0
    processing_time_ms: int = 0
    provider: str = ""
    model: str = ""
    raw_response: str = ""

    def __post_init__(self):
        if self.medical_information is None:
            self.medical_information = []
        if self.treatment_information is None:
            self.treatment_information = []
        if self.warning_signs is None:
            self.warning_signs = []
        if self.follow_up_questions is None:
            self.follow_up_questions = []
        if self.sources is None:
            self.sources = []


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        pass

    @property
    @abstractmethod
    def supports_vision(self) -> bool:
        pass

    @property
    @abstractmethod
    def supports_audio(self) -> bool:
        pass

    @abstractmethod
    async def analyze(
        self,
        text: Optional[str] = None,
        images: Optional[List[ImageInput]] = None,
        voice_transcript: Optional[str] = None,
        conversation_history: Optional[List[ConversationTurn]] = None,
        patient_context: Optional[PatientContext] = None,
        system_prompt: Optional[str] = None,
    ) -> AnalysisResult:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass

    def _prepare_system_prompt(self, patient_context: Optional[PatientContext] = None) -> str:
        base_prompt = """You are DEDAN Health's medical AI assistant. Analyze the patient's input (text, images, voice) and provide structured medical guidance.

CRITICAL RULES - NEVER VIOLATE:
1. NEVER claim certainty from visual evidence alone. Use "may be consistent with", "cannot be reliably determined", "suggests".
2. Distinguish OBSERVATION (what you see) from INTERPRETATION (what it might mean).
3. Always include uncertainty and limitations.
4. Ground treatment information in verified medical sources (WHO, CDC, national guidelines).
5. Escalate to professional review when uncertain or high-risk.
6. NEVER prescribe specific dosages or brand names.
7. ALWAYS include strong medical disclaimers.
8. NEVER diagnose - only suggest possible conditions with confidence levels.

OUTPUT FORMAT (JSON only, no markdown):
{
  "urgency": "emergency|see_doctor_soon|self_care",
  "recommended_next_step": "specific actionable guidance",
  "urgency_reasoning": "why this urgency level",
  "possible_conditions": [
    {
      "name": "condition name",
      "confidence": "high|medium|low",
      "confidence_score": 0.0-1.0,
      "reasoning": "why this condition is possible",
      "supporting_evidence": ["finding 1", "finding 2"],
      "contradicting_evidence": ["finding that doesn't fit"],
      "requires_more_info": ["info needed to confirm"]
    }
  ],
  "first_aid_steps": [
    {
      "step_number": 1,
      "title": "step title",
      "description": "detailed instructions",
      "priority": "critical|high|medium|low",
      "time_sensitive": true/false,
      "contraindications": ["when not to do this"]
    }
  ],
  "what_to_tell_doctor": {
    "key_points": ["critical info for doctor"],
    "symptom_timeline": "chronological summary",
    "image_findings": ["what was visible"],
    "home_treatments_tried": ["self-care attempted"],
    "questions_to_ask": ["suggested questions"]
  },
  "recommended_medicine_class": {
    "medicine_class": "class name (e.g., Antimalarial - ACT)",
    "generic_examples": ["generic1", "generic2"],
    "indication": "what this treats",
    "mechanism": "how it works",
    "important_warnings": ["warnings"],
    "contraindications": ["when not to use"],
    "requires_prescription": true/false,
    "evidence_level": "strong|moderate|limited|expert_opinion",
    "source_guideline": "WHO/CDC/national guideline"
  },
  "pharmacy_guidance": {
    "how_to_obtain": "step-by-step guidance",
    "trusted_sources": ["government hospital", "licensed pharmacy"],
    "verification_tips": ["how to verify authenticity"],
    "country_specific": "country guidance",
    "cost_considerations": "cost info",
    "warning_against": ["what to avoid"]
  },
  "uncertainty": "explicit uncertainty statement",
  "requires_professional_review": true/false,
  "safety_notice": "standard medical disclaimer",
  "confidence_score": 0.0-1.0,
  "safety_flags": ["flag1", "flag2"]
}"""

        if patient_context:
            context_parts = []
            if patient_context.age:
                context_parts.append(f"Age: {patient_context.age}")
            if patient_context.sex:
                context_parts.append(f"Sex: {patient_context.sex}")
            if patient_context.location:
                context_parts.append(f"Location: {patient_context.location}")
            if patient_context.pregnancy_status:
                context_parts.append("Pregnant: Yes")
            if patient_context.chronic_conditions:
                context_parts.append(f"Chronic conditions: {', '.join(patient_context.chronic_conditions)}")
            if patient_context.medications:
                context_parts.append(f"Current medications: {', '.join(patient_context.medications)}")
            if patient_context.allergies:
                context_parts.append(f"Allergies: {', '.join(patient_context.allergies)}")

            if context_parts:
                base_prompt += f"\n\nPATIENT CONTEXT:\n" + "\n".join(context_parts)

        return base_prompt

    def _prepare_images(self, images: List[ImageInput]) -> List[Dict[str, Any]]:
        """Convert ImageInput objects to provider-specific format. Override in subclasses."""
        return []

    def _extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """Extract JSON from response, handling various formats."""
        import json
        import re

        # Try direct JSON parse
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON in markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find first complete JSON object
        brace_count = 0
        start_idx = -1
        for i, char in enumerate(response_text):
            if char == '{':
                if brace_count == 0:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_idx != -1:
                    try:
                        return json.loads(response_text[start_idx:i+1])
                    except json.JSONDecodeError:
                        continue

        # Fallback: return minimal structure
        return {
            "urgency": "see_doctor_soon",
            "recommended_next_step": "Please consult a healthcare professional for proper evaluation.",
            "urgency_reasoning": "Unable to parse structured response from AI",
            "possible_conditions": [],
            "first_aid_steps": [],
            "what_to_tell_doctor": {
                "key_points": ["AI response parsing failed"],
                "symptom_timeline": "",
                "image_findings": [],
                "home_treatments_tried": [],
                "questions_to_ask": ["What could be causing these symptoms?"]
            },
            "uncertainty": "Response format was not as expected; parsed from unstructured text.",
            "requires_professional_review": True,
            "safety_notice": "DEDAN Health provides health guidance for informational purposes only. This is not a medical diagnosis. Seek professional medical care for any concerning symptoms or emergencies.",
            "confidence_score": 0.3,
            "safety_flags": ["parse_error"]
        }