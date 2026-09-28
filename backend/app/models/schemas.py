from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from enum import Enum


class UrgencyLevel(str, Enum):
    SELF_CARE = "self_care"
    SEE_DOCTOR_SOON = "see_doctor_soon"
    EMERGENCY = "emergency"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PossibleCondition(BaseModel):
    name: str = Field(..., description="Condition name (e.g., 'Malaria', 'Dengue fever')")
    confidence: ConfidenceLevel = Field(..., description="Confidence level")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Numeric confidence 0-1")
    reasoning: str = Field(..., description="Why this condition is possible based on symptoms/image")
    supporting_evidence: List[str] = Field(default_factory=list, description="Key findings supporting this")
    contradicting_evidence: List[str] = Field(default_factory=list, description="Findings that don't fit")
    requires_more_info: List[str] = Field(default_factory=list, description="Information needed to confirm/rule out")


class FirstAidStep(BaseModel):
    step_number: int = Field(..., ge=1, description="Step number in sequence")
    title: str = Field(..., description="Brief step title")
    description: str = Field(..., description="Detailed instructions")
    priority: Literal["critical", "high", "medium", "low"] = Field(default="medium")
    time_sensitive: bool = Field(default=False, description="Whether this step is time-critical")
    contraindications: List[str] = Field(default_factory=list, description="When NOT to do this step")


class WhatToTellDoctor(BaseModel):
    key_points: List[str] = Field(..., description="Critical information for the doctor")
    symptom_timeline: str = Field(..., description="Chronological summary of symptoms")
    image_findings: List[str] = Field(default_factory=list, description="What was visible in images")
    home_treatments_tried: List[str] = Field(default_factory=list, description="Any self-care attempted")
    questions_to_ask: List[str] = Field(default_factory=list, description="Suggested questions for the doctor")


class RecommendedMedicineClass(BaseModel):
    medicine_class: str = Field(..., description="e.g., 'Antimalarial - Artemisinin-based Combination Therapy (ACT)'")
    generic_examples: List[str] = Field(default_factory=list, description="Generic names only, NO brand names")
    indication: str = Field(..., description="What this class treats")
    mechanism: str = Field(default="", description="How it works (simplified)")
    important_warnings: List[str] = Field(default_factory=list, description="Critical safety warnings")
    contraindications: List[str] = Field(default_factory=list, description="When NOT to use")
    requires_prescription: bool = Field(default=True, description="Whether prescription is required")
    evidence_level: Literal["strong", "moderate", "limited", "expert_opinion"] = Field(default="moderate")
    source_guideline: str = Field(default="", description="Guideline source (WHO, CDC, national)")


class PharmacyGuidance(BaseModel):
    how_to_obtain: str = Field(..., description="Step-by-step guidance to get the correct medicine")
    trusted_sources: List[str] = Field(..., description="Types of trusted sources (government hospital, licensed pharmacy, etc.)")
    verification_tips: List[str] = Field(default_factory=list, description="How to verify medicine authenticity")
    country_specific: str = Field(default="", description="Country-specific guidance")
    cost_considerations: str = Field(default="", description="Generic vs branded, insurance, subsidies")
    warning_against: List[str] = Field(default_factory=list, description="What to avoid (unlicensed sellers, etc.)")


class Disclaimer(BaseModel):
    text: str = Field(..., description="Full disclaimer text")
    short_version: str = Field(..., description="Brief version for UI display")
    must_acknowledge: bool = Field(default=True, description="User must acknowledge before proceeding")


class NextSteps(BaseModel):
    immediate: List[str] = Field(default_factory=list, description="Do right now")
    within_hours: List[str] = Field(default_factory=list, description="Do within 24 hours")
    within_days: List[str] = Field(default_factory=list, description="Do within 3-7 days")
    follow_up_with: str = Field(default="", description="Who to follow up with")


class AnalyzeRequest(BaseModel):
    # Patient info
    patient_age: int = Field(..., ge=0, le=150, description="Patient age in years")
    patient_sex: Literal["male", "female", "other"] = Field(..., description="Biological sex")
    patient_location: Optional[str] = Field(default=None, description="Country/region for localized guidance")
    patient_pregnant: bool = Field(default=False, description="Pregnancy status")
    patient_chronic_conditions: List[str] = Field(default_factory=list, description="Known chronic conditions")
    patient_medications: List[str] = Field(default_factory=list, description="Current medications")
    patient_allergies: List[str] = Field(default_factory=list, description="Known allergies")
    patient_language: str = Field(default="en", description="Preferred language (en, sw, am, es, fr)")

    # Symptoms
    symptom_description: str = Field(..., min_length=10, max_length=3000, description="Free-text symptom description")
    symptom_duration: Optional[str] = Field(default=None, description="How long symptoms have been present")
    symptom_severity: Optional[Literal["mild", "moderate", "severe"]] = Field(default=None)

    # Multi-modal inputs
    image_ids: List[str] = Field(default_factory=list, description="Pre-uploaded image IDs")
    image_data_list: List[str] = Field(default_factory=list, description="Base64 encoded images (data URLs or raw base64)")
    voice_transcript: Optional[str] = Field(default=None, description="Voice input transcript")

    # Session
    session_id: Optional[str] = Field(default=None, description="Conversation session ID")
    conversation_history: List[Dict[str, str]] = Field(default_factory=list, description="Previous conversation turns")

    # Consent
    consent: bool = Field(default=True, description="Patient consent for AI analysis")


class ImageUploadResponse(BaseModel):
    image_id: str
    filename: str
    size_bytes: int
    mime_type: str
    quality_score: float = Field(..., ge=0.0, le=1.0)
    is_usable: bool
    upload_timestamp: datetime
    preview_url: Optional[str] = None


class AnalyzeResponse(BaseModel):
    # Core identification
    request_id: str
    session_id: str
    timestamp: datetime

    # Main analysis results
    possible_conditions: List[PossibleCondition] = Field(default_factory=list)
    urgency_level: UrgencyLevel
    urgency_reasoning: str = Field(..., description="Why this urgency level was assigned")

    # First aid & guidance
    first_aid_steps: List[FirstAidStep] = Field(default_factory=list)
    what_to_tell_your_doctor: WhatToTellDoctor

    # Medicine guidance (educational only)
    recommended_medicine_class: Optional[RecommendedMedicineClass] = None
    pharmacy_guidance: Optional[PharmacyGuidance] = None

    # Safety
    disclaimer: Disclaimer
    next_steps: NextSteps

    # Metadata
    processing_time_ms: int
    ai_provider: str
    ai_model: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    requires_professional_review: bool = Field(default=True)
    safety_flags: List[str] = Field(default_factory=list)

    # Image analysis (if images provided)
    image_assessment: Optional[Dict[str, Any]] = None


class HealthCheckResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    timestamp: datetime
    version: str
    components: Dict[str, str]
    ai_providers: Dict[str, bool]


class ErrorResponse(BaseModel):
    error: str
    error_code: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)