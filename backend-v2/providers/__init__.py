"""
Multimodal AI Providers Package

This package provides an extensible provider abstraction layer for
multimodal AI capabilities (text, vision, audio) with support for
multiple providers (Gemini, OpenAI, etc.) and future extensibility.
"""

from .models import (
    # Capabilities
    Modality,
    ProviderCapabilities,
    # Input Models
    ImageInput,
    AudioInput,
    TextAnalysisRequest,
    ImageAnalysisRequest,
    MultimodalAnalysisRequest,
    # Output Models
    ImageQuality,
    PossibleExplanation,
    ImageAssessment,
    MedicalInformation,
    TreatmentInformation,
    Source,
    AnalysisResponse,
    # Usage/Cost
    TokenUsage,
    ProviderMetrics,
    # Exceptions
    ProviderError,
    ProviderUnavailableError,
    ProviderRateLimitError,
    ProviderInvalidRequestError,
    ProviderSafetyError,
    ProviderTimeoutError,
    # Base Classes
    MultimodalAIProvider,
    # Configuration
    ProviderConfig,
    MultimodalConfig,
)

from .gemini_provider import GeminiProvider
from .openai_provider import OpenAIProvider
from .offline_provider import OfflineProvider
from .provider_factory import ProviderFactory, get_provider_factory, reset_provider_factory
from .image_validation import (
    ImageValidator,
    ImageQualityAssessor,
    ImageValidationPipeline,
    ValidationResult,
    QualityAssessment,
    ALLOWED_MIME_TYPES,
    MAX_FILE_SIZE,
)
from .orchestrator import (
    MultimodalOrchestrator,
    MultimodalContextBuilder,
    SafetyValidator,
    AuditLogger,
    ConversationTurn,
    PatientProfile,
    MultimodalClinicalContext,
)

__all__ = [
    # Models
    "Modality",
    "ProviderCapabilities",
    "ImageInput",
    "AudioInput",
    "TextAnalysisRequest",
    "ImageAnalysisRequest",
    "MultimodalAnalysisRequest",
    "ImageQuality",
    "PossibleExplanation",
    "ImageAssessment",
    "MedicalInformation",
    "TreatmentInformation",
    "Source",
    "AnalysisResponse",
    "TokenUsage",
    "ProviderMetrics",
    "ProviderError",
    "ProviderUnavailableError",
    "ProviderRateLimitError",
    "ProviderInvalidRequestError",
    "ProviderSafetyError",
    "ProviderTimeoutError",
    "MultimodalAIProvider",
    "ProviderConfig",
    "MultimodalConfig",
    # Providers
    "GeminiProvider",
    "OpenAIProvider",
    "OfflineProvider",
    # Factory
    "ProviderFactory",
    "get_provider_factory",
    "reset_provider_factory",
    # Image Validation
    "ImageValidator",
    "ImageQualityAssessor",
    "ImageValidationPipeline",
    "ValidationResult",
    "QualityAssessment",
    "ALLOWED_MIME_TYPES",
    "MAX_FILE_SIZE",
    # Orchestrator
    "MultimodalOrchestrator",
    "MultimodalContextBuilder",
    "SafetyValidator",
    "AuditLogger",
    "ConversationTurn",
    "PatientProfile",
    "MultimodalClinicalContext",
]

__version__ = "1.0.0"