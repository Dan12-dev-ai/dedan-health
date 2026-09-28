import asyncio
import base64
import json
import os
import time
import uuid
from typing import List, Optional, Dict, Any

from openai import AsyncOpenAI

from .base import AIProvider, ImageInput, PatientContext, ConversationTurn, AnalysisResult, Modality


class OpenAIProvider(AIProvider):
    """OpenAI provider for multimodal medical analysis (GPT-4o)."""

    MODEL_CONFIGS = {
        "gpt-4o": {
            "context_window": 128_000,
            "max_output_tokens": 4096,
            "cost_per_1k_input": 0.005,
            "cost_per_1k_output": 0.015,
            "cost_per_image": 0.001,  # approximate
        },
        "gpt-4o-mini": {
            "context_window": 128_000,
            "max_output_tokens": 4096,
            "cost_per_1k_input": 0.00015,
            "cost_per_1k_output": 0.0006,
            "cost_per_image": 0.0005,
        },
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
        timeout_seconds: float = 60.0,
        max_retries: int = 3,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not configured")

        self._client = AsyncOpenAI(
            api_key=self.api_key,
            timeout=timeout_seconds,
            max_retries=max_retries,
        )

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def default_model(self) -> str:
        return self.model_name

    @property
    def supports_vision(self) -> bool:
        return "gpt-4o" in self.model_name or "gpt-4-turbo" in self.model_name

    @property
    def supports_audio(self) -> bool:
        return False

    def _prepare_images(self, images: List[ImageInput]) -> List[Dict[str, Any]]:
        """Convert ImageInput to OpenAI format."""
        parts = []
        for img in images:
            if img.image_data:
                # Handle data URLs
                if img.image_data.startswith("data:"):
                    parts.append({
                        "type": "image_url",
                        "image_url": {"url": img.image_data, "detail": "high"}
                    })
                else:
                    # Raw base64
                    parts.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:{img.mime_type};base64,{img.image_data}", "detail": "high"}
                    })
        return parts

    async def analyze(
        self,
        text: Optional[str] = None,
        images: Optional[List[ImageInput]] = None,
        voice_transcript: Optional[str] = None,
        conversation_history: Optional[List[ConversationTurn]] = None,
        patient_context: Optional[PatientContext] = None,
        system_prompt: Optional[str] = None,
    ) -> AnalysisResult:
        request_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            # Build messages
            messages = []

            # System prompt
            system_prompt = system_prompt or self._prepare_system_prompt(patient_context)
            messages.append({"role": "system", "content": system_prompt})

            # Conversation history
            if conversation_history:
                for turn in conversation_history:
                    role = "assistant" if turn.role == "assistant" else "user"
                    messages.append({"role": role, "content": turn.content})

            # Current user message
            user_content = []

            # Combined text
            combined_text = ""
            if text and voice_transcript:
                combined_text = f"{text}\n\n[Voice Input]: {voice_transcript}"
            elif text:
                combined_text = text
            elif voice_transcript:
                combined_text = voice_transcript

            if combined_text:
                user_content.append({"type": "text", "text": combined_text})

            # Images
            if images:
                image_parts = self._prepare_images(images)
                user_content.extend(image_parts)

            if user_content:
                messages.append({"role": "user", "content": user_content})

            # Generate with retry
            response = await self._generate_with_retry(messages)

            # Parse response
            result = self._parse_response(response)
            result.request_id = request_id
            result.processing_time_ms = int((time.time() - start_time) * 1000)
            result.provider = self.provider_name
            result.model = self.model_name

            return result

        except Exception as e:
            return AnalysisResult(
                request_id=request_id,
                urgency="see_doctor_soon",
                recommended_next_step=f"Analysis failed: {str(e)}. Please consult a healthcare professional.",
                urgency_reasoning="Technical error during AI analysis",
                uncertainty=f"Technical error: {str(e)}",
                requires_professional_review=True,
                safety_notice="DEDAN Health provides health guidance for informational purposes only. This is not a medical diagnosis. Seek professional medical care for any concerning symptoms or emergencies.",
                confidence_score=0.0,
                processing_time_ms=int((time.time() - start_time) * 1000),
                provider=self.provider_name,
                model=self.model_name,
                safety_flags=[f"provider_error: {type(e).__name__}"],
            )

    async def _generate_with_retry(self, messages: List[Dict[str, Any]]) -> Any:
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = await self._client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens or self.MODEL_CONFIGS.get(self.model_name, {}).get("max_output_tokens", 4096),
                    response_format={"type": "json_object"},
                )
                return response

            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1.0 * (2 ** attempt))
                else:
                    break

        error_str = str(last_error).lower()
        if "rate" in error_str or "429" in error_str:
            raise Exception(f"Rate limit exceeded: {last_error}")
        elif "timeout" in error_str:
            raise Exception(f"Timeout: {last_error}")
        elif "unavailable" in error_str or "503" in error_str:
            raise Exception(f"Service unavailable: {last_error}")

        raise Exception(f"Generation failed after {self.max_retries} attempts: {last_error}")

    def _parse_response(self, response: Any) -> AnalysisResult:
        result = AnalysisResult(
            request_id="",
            urgency="see_doctor_soon",
            recommended_next_step="",
        )

        try:
            response_text = response.choices[0].message.content
            data = self._extract_json_from_response(response_text)

            result.urgency = data.get("urgency", "see_doctor_soon")
            result.recommended_next_step = data.get("recommended_next_step", "")
            result.urgency_reasoning = data.get("urgency_reasoning", "")
            result.confidence_score = float(data.get("confidence_score", 0.5))
            result.uncertainty = data.get("uncertainty", "")
            result.requires_professional_review = data.get("requires_professional_review", True)
            result.safety_notice = data.get("safety_notice", "")
            result.safety_flags = data.get("safety_flags", [])
            result.warning_signs = data.get("warning_signs", [])
            result.follow_up_questions = data.get("follow_up_questions", [])

            # Store structured data in medical_information for transformation
            result.medical_information = [{
                "topic": "full_analysis",
                "content": json.dumps(data),
                "source": "AI analysis",
                "source_type": "ai_analysis",
                "relevance_score": result.confidence_score,
            }]

            # Token usage
            if hasattr(response, 'usage') and response.usage:
                result.token_usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

        except Exception as e:
            result.uncertainty = f"Failed to parse AI response: {str(e)}"
            result.safety_flags.append(f"parse_error: {type(e).__name__}")
            result.confidence_score = 0.2

        return result

    async def health_check(self) -> bool:
        try:
            await self._client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5,
            )
            return True
        except Exception:
            return False