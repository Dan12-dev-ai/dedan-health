import asyncio
import json
import os
import time
import uuid
from typing import List, Optional, Dict, Any

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from .base import AIProvider, ImageInput, PatientContext, ConversationTurn, AnalysisResult, Modality


class GeminiProvider(AIProvider):
    """Google Gemini provider for multimodal medical analysis."""

    MODEL_CONFIGS = {
        "gemini-1.5-pro": {
            "context_window": 2_000_000,
            "max_output_tokens": 8192,
            "cost_per_1k_input": 0.00125,
            "cost_per_1k_output": 0.005,
            "cost_per_image": 0.000125,
        },
        "gemini-1.5-flash": {
            "context_window": 1_000_000,
            "max_output_tokens": 8192,
            "cost_per_1k_input": 0.000075,
            "cost_per_1k_output": 0.0003,
            "cost_per_image": 0.0000375,
        },
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-1.5-pro",
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
        timeout_seconds: float = 60.0,
        max_retries: int = 3,
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not configured")

        # Configure SDK
        genai.configure(api_key=self.api_key)

        # Medical safety settings
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }

        # Initialize model
        self._model = genai.GenerativeModel(
            model_name=self.model_name,
            safety_settings=self.safety_settings,
            generation_config=genai.GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens or self.MODEL_CONFIGS.get(self.model_name, {}).get("max_output_tokens", 8192),
                response_mime_type="application/json",
            )
        )

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def default_model(self) -> str:
        return self.model_name

    @property
    def supports_vision(self) -> bool:
        return True

    @property
    def supports_audio(self) -> bool:
        return False  # Gemini 1.5 supports audio but we'll handle via transcript

    def _prepare_images(self, images: List[ImageInput]) -> List[Dict[str, Any]]:
        """Convert ImageInput to Gemini format."""
        parts = []
        for img in images:
            if img.image_data:
                image_bytes = base64.b64decode(img.image_data)
                parts.append({"mime_type": img.mime_type, "data": image_bytes})
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
            # Build prompt parts
            prompt_parts = []

            # System prompt
            system_prompt = system_prompt or self._prepare_system_prompt(patient_context)
            prompt_parts.append(system_prompt)

            # Conversation history
            if conversation_history:
                for turn in conversation_history:
                    role = turn.role.upper()
                    content = turn.content
                    if content:
                        prompt_parts.append(f"[{role}]: {content}")

            # Current inputs
            combined_text = ""
            if text and voice_transcript:
                combined_text = f"{text}\n\n[Voice Input]: {voice_transcript}"
            elif text:
                combined_text = text
            elif voice_transcript:
                combined_text = voice_transcript

            if combined_text:
                prompt_parts.append(f"[PATIENT]: {combined_text}")

            # Images
            image_parts = []
            if images:
                image_parts = self._prepare_images(images)
            prompt_parts.extend(image_parts)

            # Patient context (if not already in system prompt)
            if patient_context and not system_prompt:
                context_str = json.dumps({
                    "age": patient_context.age,
                    "sex": patient_context.sex,
                    "location": patient_context.location,
                    "pregnancy_status": patient_context.pregnancy_status,
                    "chronic_conditions": patient_context.chronic_conditions,
                    "medications": patient_context.medications,
                    "allergies": patient_context.allergies,
                    "language": patient_context.language,
                }, indent=2)
                prompt_parts.append(f"[PATIENT_CONTEXT]: {context_str}")

            # Generate with retry
            response = await self._generate_with_retry(prompt_parts)

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

    async def _generate_with_retry(self, prompt_parts: List[Any]) -> Any:
        last_error = None
        for attempt in range(self.max_retries):
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, lambda: self._model.generate_content(prompt_parts)
                )

                # Check safety filter
                if response.candidates and response.candidates[0].finish_reason == 3:
                    raise Exception("Response blocked by safety filter")

                return response

            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1.0 * (2 ** attempt))
                else:
                    break

        # Classify error
        error_str = str(last_error).lower()
        if "quota" in error_str or "rate" in error_str:
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
            response_text = response.text if hasattr(response, 'text') else str(response)
            data = self._extract_json_from_response(response_text)

            # Populate from parsed JSON
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

            # Possible conditions
            conditions = data.get("possible_conditions", [])
            # Store in medical_information for now, will be transformed later
            result.medical_information = [{
                "topic": "possible_conditions",
                "content": json.dumps(conditions),
                "source": "AI analysis",
                "source_type": "ai_analysis",
                "relevance_score": result.confidence_score,
            }]

            # First aid steps
            first_aid = data.get("first_aid_steps", [])
            result.treatment_information = [{
                "condition": "general",
                "intervention": "first_aid",
                "description": json.dumps(first_aid),
                "evidence_level": "expert_opinion",
                "source": "AI analysis",
            }]

            # What to tell doctor
            doctor_info = data.get("what_to_tell_doctor", {})
            result.medical_information.append({
                "topic": "doctor_communication",
                "content": json.dumps(doctor_info),
                "source": "AI analysis",
                "source_type": "ai_analysis",
                "relevance_score": 0.9,
            })

            # Medicine class
            medicine = data.get("recommended_medicine_class")
            if medicine:
                result.treatment_information.append({
                    "condition": "general",
                    "intervention": "medicine_class",
                    "description": json.dumps(medicine),
                    "evidence_level": medicine.get("evidence_level", "moderate"),
                    "source": medicine.get("source_guideline", "AI analysis"),
                })

            # Pharmacy guidance
            pharmacy = data.get("pharmacy_guidance")
            if pharmacy:
                result.medical_information.append({
                    "topic": "pharmacy_guidance",
                    "content": json.dumps(pharmacy),
                    "source": "AI analysis",
                    "source_type": "ai_analysis",
                    "relevance_score": 0.8,
                })

            # Sources
            sources = data.get("sources", [])
            result.sources = sources if sources else [{
                "id": "ai_analysis",
                "title": "AI Medical Analysis",
                "type": "ai_analysis",
                "url": "",
            }]

            # Image assessment
            if "image_assessment" in data:
                result.image_assessment = data["image_assessment"]

            # Token usage
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                result.token_usage = {
                    "prompt_tokens": getattr(usage, 'prompt_token_count', 0),
                    "completion_tokens": getattr(usage, 'candidates_token_count', 0),
                    "total_tokens": getattr(usage, 'total_token_count', 0),
                }

        except Exception as e:
            result.uncertainty = f"Failed to parse AI response: {str(e)}"
            result.safety_flags.append(f"parse_error: {type(e).__name__}")
            result.confidence_score = 0.2

        return result

    async def health_check(self) -> bool:
        try:
            test_model = genai.GenerativeModel("gemini-1.5-flash")
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: test_model.generate_content(
                    "test",
                    generation_config=genai.GenerationConfig(max_output_tokens=5)
                )
            )
            return True
        except Exception:
            return False


# Import at bottom to avoid circular import
import base64