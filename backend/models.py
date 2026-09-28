from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class TriageLevel(str, Enum):
    EMERGENCY = "emergency"
    URGENT = "urgent"
    ROUTINE = "routine"
    SELF_CARE = "self_care"

class Language(str, Enum):
    ENGLISH = "en"
    SWAHILI = "sw"
    AMHARIC = "am"
    SPANISH = "es"
    FRENCH = "fr"

class PatientProfile(BaseModel):
    age: int = Field(..., ge=0, le=120, description="Patient age in years")
    sex: str = Field(..., pattern="^(male|female|other)$", description="Patient sex")
    location: Optional[str] = Field(None, description="Patient location/region")
    pregnancy_status: Optional[bool] = Field(None, description="Pregnancy status if applicable")
    chronic_conditions: List[str] = Field(default_factory=list, description="List of chronic conditions")
    language: Language = Field(default=Language.ENGLISH, description="Preferred language")

class SymptomInput(BaseModel):
    symptoms: str = Field(..., min_length=5, max_length=1000, description="Patient symptoms description")
    voice_input: Optional[bool] = Field(False, description="Whether input was voice-to-text")
    duration: Optional[str] = Field(None, description="Duration of symptoms")
    severity: Optional[str] = Field(None, description="Patient-reported severity (mild/moderate/severe)")

class TriageRequest(BaseModel):
    patient: PatientProfile
    symptoms: SymptomInput
    session_id: Optional[str] = Field(None, description="Session identifier for tracking")
    consent: bool = Field(True, description="Patient consent for data processing")

class RiskFlag(BaseModel):
    type: str = Field(..., description="Type of risk flag")
    severity: str = Field(..., description="Risk severity level")
    description: str = Field(..., description="Risk description in patient language")
    keywords: List[str] = Field(default_factory=list, description="Trigger keywords")

class TriageResponse(BaseModel):
    triage_level: TriageLevel
    suggested_next_step: str
    risk_flags: List[RiskFlag]
    patient_summary: str
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="AI confidence in triage decision")
    emergency_contacts: Optional[List[str]] = Field(None, description="Local emergency contacts")
    follow_up_timeframe: Optional[str] = Field(None, description="Recommended follow-up timeframe")
    disclaimer: str = Field(default="DEDAN is not a replacement for professional medical care. Seek immediate medical attention for emergencies.")

class Condition(BaseModel):
    id: str
    name: str
    description: str
    common_symptoms: List[str]
    urgency_level: TriageLevel
    language: Language

class TriageSession(BaseModel):
    session_id: str
    patient_profile: PatientProfile
    symptoms_history: List[SymptomInput]
    triage_responses: List[TriageResponse]
    created_at: datetime
    updated_at: datetime
    status: str = Field(default="active")

class ClinicalGuideline(BaseModel):
    condition: str
    symptoms: List[str]
    triage_criteria: Dict[str, Any]
    recommendations: str
    language: Language
    source: str = Field(..., description="Source of guideline (WHO, MoH, etc.)")

class DataConsent(BaseModel):
    patient_id: str
    consent_given: bool
    consent_date: datetime
    data_usage_purposes: List[str]
    withdrawal_allowed: bool = True
