import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # DEDAN Configuration
    dedan_model: str = os.getenv("DEDAN_MODEL", "gpt-3.5-turbo")
    dedan_temperature: float = float(os.getenv("DEDAN_TEMPERATURE", "0.3"))
    dedan_max_tokens: int = int(os.getenv("DEDAN_MAX_TOKENS", "500"))
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./dedan_health.db")
    
    # Clinical Guidelines
    clinical_guidelines_path: str = os.getenv("CLINICAL_GUIDELINES_PATH", "../data/clinical_guidelines/")
    
    # Safety Configuration
    emergency_threshold: float = float(os.getenv("EMERGENCY_THRESHOLD", "0.8"))
    max_response_length: int = int(os.getenv("MAX_RESPONSE_LENGTH", "160"))
    
    # Multilingual Support
    default_language: str = os.getenv("DEFAULT_LANGUAGE", "en")
    supported_languages: List[str] = os.getenv("SUPPORTED_LANGUAGES", "en,sw,am,es,fr").split(",")
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # API Configuration
    api_title: str = "DEDAN HealthEngine API"
    api_description: str = "Digital Empathy-Driven AI Navigator - Primary Care Triage API"
    api_version: str = "1.0.0"
    
    class Config:
        env_file = ".env"

# Global settings instance
settings = Settings()
