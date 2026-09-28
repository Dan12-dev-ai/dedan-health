from functools import lru_cache
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "DEDAN Health API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, description="Debug mode")
    ENVIRONMENT: str = Field(default="development", description="Environment: development, staging, production")

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000"],
        description="Allowed CORS origins"
    )

    # AI Providers
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API key")
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, description="Anthropic API key")
    DEFAULT_AI_PROVIDER: str = Field(default="gemini", description="Default AI provider: gemini, openai, anthropic")
    GEMINI_MODEL: str = Field(default="gemini-1.5-pro", description="Gemini model to use")
    OPENAI_MODEL: str = Field(default="gpt-4o", description="OpenAI model to use")
    ANTHROPIC_MODEL: str = Field(default="claude-3-5-sonnet-20241022", description="Anthropic model to use")

    # AI Settings
    AI_TEMPERATURE: float = Field(default=0.3, description="AI temperature for generation")
    AI_MAX_TOKENS: int = Field(default=4096, description="Max output tokens")
    AI_TIMEOUT_SECONDS: int = Field(default=60, description="AI request timeout")

    # Image Upload
    MAX_IMAGE_SIZE_MB: int = Field(default=10, description="Max image size in MB")
    ALLOWED_IMAGE_TYPES: List[str] = Field(
        default=["image/jpeg", "image/png", "image/webp", "image/heic"],
        description="Allowed image MIME types"
    )
    IMAGE_STORAGE_PATH: str = Field(default="/tmp/dedan_images", description="Local image storage path")
    IMAGE_TTL_HOURS: int = Field(default=24, description="Image time-to-live in hours")

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(default=30, description="Requests per minute per IP")
    RATE_LIMIT_WINDOW: int = Field(default=60, description="Rate limit window in seconds")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Log level")
    LOG_FORMAT: str = Field(default="json", description="Log format: json or text")

    # Security
    API_KEY_HEADER: str = Field(default="X-API-Key", description="API key header name")
    ADMIN_API_KEY: Optional[str] = Field(default=None, description="Admin API key for privileged operations")

    # External Services (for pharmacy guidance)
    GOOGLE_MAPS_API_KEY: Optional[str] = Field(default=None, description="Google Maps API key for pharmacy lookup")
    COUNTRY_CODE: str = Field(default="KE", description="Default country code for pharmacy guidance")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()