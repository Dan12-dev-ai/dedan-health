from typing import Optional, Dict, Any, List
import asyncio

from .base import AIProvider, ImageInput, PatientContext, ConversationTurn, AnalysisResult
from .gemini_provider import GeminiProvider
from .openai_provider import OpenAIProvider

# Try to import Anthropic provider
try:
    from .anthropic_provider import AnthropicProvider
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class ProviderFactory:
    """Factory for creating and managing AI providers with fallback support."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._providers: Dict[str, AIProvider] = {}
        self._primary_provider: Optional[str] = None
        self._fallback_order: List[str] = []

    def initialize(self, settings) -> None:
        """Initialize providers from settings."""
        # Determine provider order
        default_provider = getattr(settings, 'DEFAULT_AI_PROVIDER', 'gemini')
        self._primary_provider = default_provider

        # Initialize Gemini
        gemini_key = getattr(settings, 'GEMINI_API_KEY', None)
        if gemini_key:
            try:
                self._providers["gemini"] = GeminiProvider(
                    api_key=gemini_key,
                    model=getattr(settings, 'GEMINI_MODEL', 'gemini-1.5-pro'),
                    temperature=getattr(settings, 'AI_TEMPERATURE', 0.3),
                    max_tokens=getattr(settings, 'AI_MAX_TOKENS', None),
                    timeout_seconds=getattr(settings, 'AI_TIMEOUT_SECONDS', 60),
                )
                self._fallback_order.append("gemini")
            except Exception as e:
                print(f"Failed to initialize Gemini: {e}")

        # Initialize OpenAI
        openai_key = getattr(settings, 'OPENAI_API_KEY', None)
        if openai_key:
            try:
                self._providers["openai"] = OpenAIProvider(
                    api_key=openai_key,
                    model=getattr(settings, 'OPENAI_MODEL', 'gpt-4o'),
                    temperature=getattr(settings, 'AI_TEMPERATURE', 0.3),
                    max_tokens=getattr(settings, 'AI_MAX_TOKENS', None),
                    timeout_seconds=getattr(settings, 'AI_TIMEOUT_SECONDS', 60),
                )
                if "openai" not in self._fallback_order:
                    self._fallback_order.append("openai")
            except Exception as e:
                print(f"Failed to initialize OpenAI: {e}")

        # Initialize Anthropic (if available)
        if ANTHROPIC_AVAILABLE:
            anthropic_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
            if anthropic_key:
                try:
                    self._providers["anthropic"] = AnthropicProvider(
                        api_key=anthropic_key,
                        model=getattr(settings, 'ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022'),
                        temperature=getattr(settings, 'AI_TEMPERATURE', 0.3),
                        max_tokens=getattr(settings, 'AI_MAX_TOKENS', None),
                        timeout_seconds=getattr(settings, 'AI_TIMEOUT_SECONDS', 60),
                    )
                    if "anthropic" not in self._fallback_order:
                        self._fallback_order.append("anthropic")
                except Exception as e:
                    print(f"Failed to initialize Anthropic: {e}")

        # Ensure primary provider is first in fallback order
        if self._primary_provider in self._fallback_order:
            self._fallback_order.remove(self._primary_provider)
            self._fallback_order.insert(0, self._primary_provider)

    def get_provider(self, name: str) -> Optional[AIProvider]:
        """Get a specific provider by name."""
        return self._providers.get(name)

    def get_primary_provider(self) -> Optional[AIProvider]:
        """Get the primary provider."""
        if self._primary_provider:
            return self._providers.get(self._primary_provider)
        return self._fallback_order[0] if self._fallback_order else None

    async def analyze_with_fallback(
        self,
        text: Optional[str] = None,
        images: Optional[List[ImageInput]] = None,
        voice_transcript: Optional[str] = None,
        conversation_history: Optional[List[ConversationTurn]] = None,
        patient_context: Optional[PatientContext] = None,
        system_prompt: Optional[str] = None,
        require_vision: bool = False,
    ) -> AnalysisResult:
        """Try providers in fallback order until one succeeds."""

        # Filter providers by capability
        available_providers = []
        for name in self._fallback_order:
            provider = self._providers.get(name)
            if provider:
                if require_vision and not provider.supports_vision:
                    continue
                available_providers.append(provider)

        if not available_providers:
            return AnalysisResult(
                request_id="",
                urgency="see_doctor_soon",
                recommended_next_step="No AI providers available. Please consult a healthcare professional directly.",
                urgency_reasoning="No configured AI providers",
                uncertainty="No AI providers configured or available",
                requires_professional_review=True,
                safety_notice="DEDAN Health provides health guidance for informational purposes only. This is not a medical diagnosis. Seek professional medical care for any concerning symptoms or emergencies.",
                confidence_score=0.0,
                provider="none",
                model="none",
                safety_flags=["no_providers_available"],
            )

        last_error = None
        for provider in available_providers:
            try:
                result = await provider.analyze(
                    text=text,
                    images=images,
                    voice_transcript=voice_transcript,
                    conversation_history=conversation_history,
                    patient_context=patient_context,
                    system_prompt=system_prompt,
                )
                # If we get here, the call succeeded
                return result
            except Exception as e:
                last_error = e
                print(f"Provider {provider.provider_name} failed: {e}")
                continue

        # All providers failed
        return AnalysisResult(
            request_id="",
            urgency="see_doctor_soon",
            recommended_next_step=f"All AI providers failed. Last error: {str(last_error)}. Please consult a healthcare professional directly.",
            urgency_reasoning="All AI providers failed",
            uncertainty=f"All providers failed. Last error: {str(last_error)}",
            requires_professional_review=True,
            safety_notice="DEDAN Health provides health guidance for informational purposes only. This is not a medical diagnosis. Seek professional medical care for any concerning symptoms or emergencies.",
            confidence_score=0.0,
            provider="none",
            model="none",
            safety_flags=[f"all_providers_failed: {str(last_error)}"],
        )

    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all providers."""
        results = {}
        for name, provider in self._providers.items():
            try:
                results[name] = await provider.health_check()
            except Exception:
                results[name] = False
        return results

    def list_providers(self) -> List[Dict[str, Any]]:
        """List all configured providers with capabilities."""
        return [
            {
                "name": name,
                "model": provider.default_model,
                "supports_vision": provider.supports_vision,
                "supports_audio": provider.supports_audio,
                "is_primary": name == self._primary_provider,
            }
            for name, provider in self._providers.items()
        ]