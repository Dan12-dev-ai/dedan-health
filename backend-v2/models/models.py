from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum

class TriageLevel(str, Enum):
    EMERGENCY = "emergency"
    URGENT = "urgent"
    ROUTINE = "routine"
    SELF_CARE = "self_care"

class RiskScore(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class RiskTimeHorizon(str, Enum):
    IMMEDIATE = "immediate"
    THIRTY_DAYS = "30_days"
    NINETY_DAYS = "90_days"
    ONE_YEAR = "1_year"
    FIVE_YEARS = "5_years"

class Language(str, Enum):
    EN = "en"
    SW = "sw"
    AM = "am"
    ES = "es"
    FR = "fr"

class ChronicCondition(str, Enum):
    DIABETES = "diabetes"
    HYPERTENSION = "hypertension"
    ASTHMA = "asthma"
    HIV = "hiv"
    TUBERCULOSIS = "tuberculosis"
    MALARIA = "malaria"
    HEART_DISEASE = "heart_disease"
    STROKE = "stroke"
    CANCER = "cancer"

class AgentType(str, Enum):
    TRIAGE = "triage_agent"
    SAFETY_GUARD = "safety_guard_agent"
    GUIDELINE = "guideline_agent"
    RISK_PREDICTION = "risk_prediction_agent"
    COORDINATOR = "coordinator_agent"

# Patient Models
class PatientProfile(BaseModel):
    age: int = Field(..., ge=0, le=150, description="Patient age in years")
    sex: str = Field(..., pattern=r"^(male|female|other)$", description="Biological sex")
    language: Language = Field(default=Language.EN, description="Preferred language")
    location: Optional[str] = Field(None, description="Geographic location")
    pregnancy_status: bool = Field(default=False, description="Pregnancy status")
    chronic_conditions: List[ChronicCondition] = Field(default_factory=list, description="Chronic conditions")
    medications: List[str] = Field(default_factory=list, description="Current medications")
    allergies: List[str] = Field(default_factory=list, description="Known allergies")
    last_checkup: Optional[datetime] = Field(None, description="Last medical checkup date")

class ChronicCareData(BaseModel):
    condition: ChronicCondition
    diagnosis_date: datetime
    current_medications: List[str]
    last_hba1c: Optional[float] = Field(None, ge=0, le=20, description="HbA1c value for diabetes")
    last_bp_systolic: Optional[int] = Field(None, ge=0, le=300, description="Last systolic BP")
    last_bp_diastolic: Optional[int] = Field(None, ge=0, le=200, description="Last diastolic BP")
    last_weight: Optional[float] = Field(None, ge=0, le=500, description="Last weight in kg")
    medication_adherence: Optional[float] = Field(None, ge=0, le=1, description="Medication adherence score (0-1)")
    symptom_evolution: List[Dict[str, Any]] = Field(default_factory=list, description="Symptom progression over time")

# Symptom Models
class SymptomInput(BaseModel):
    symptoms: str = Field(..., min_length=10, max_length=2000, description="Symptom description")
    keywords: List[str] = Field(default_factory=list, description="Extracted symptom keywords")
    duration: Optional[str] = Field(None, description="Duration of symptoms")
    severity: Optional[int] = Field(None, ge=1, le=10, description="Severity scale 1-10")
    voice_input: bool = Field(default=False, description="Whether input was voice-based")
    language: Language = Field(default=Language.EN, description="Input language")

class HomeMeasurement(BaseModel):
    measurement_type: str = Field(..., description="Type of measurement (BP, weight, glucose, etc.)")
    value: Union[float, int] = Field(..., description="Measurement value")
    unit: str = Field(..., description="Measurement unit")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When measurement was taken")
    device_type: Optional[str] = Field(None, description="Type of device used")

# Agent Models
class AgentInput(BaseModel):
    agent_type: AgentType
    session_id: str
    patient: PatientProfile
    symptoms: SymptomInput
    chronic_care_data: Optional[ChronicCareData] = None
    home_measurements: Optional[List[HomeMeasurement]] = None
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context for the agent")

class AgentOutput(BaseModel):
    agent_type: AgentType
    session_id: str
    confidence_score: float = Field(..., ge=0, le=1, description="Agent confidence score")
    reasoning: str = Field(..., description="Agent reasoning process")
    result: Dict[str, Any] = Field(..., description="Agent-specific results")
    risk_flags: List[str] = Field(default_factory=list, description="Risk flags identified")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

# Triage Agent Specific Models
class TriageAgentInput(AgentInput):
    pass

class TriageAgentOutput(AgentOutput):
    triage_level: TriageLevel
    differential_diagnoses: List[str] = Field(default_factory=list, description="Possible diagnoses")
    recommended_tests: List[str] = Field(default_factory=list, description="Recommended diagnostic tests")
    next_step: str = Field(..., description="Recommended next action")

# Safety Guard Agent Specific Models
class SafetyGuardAgentInput(AgentInput):
    triage_output: TriageAgentOutput

class SafetyGuardAgentOutput(AgentOutput):
    emergency_detected: bool
    emergency_type: Optional[str] = None
    safety_concerns: List[str] = Field(default_factory=list, description="Safety concerns identified")
    requires_immediate_action: bool
    recommended_action: str

# Guideline Agent Specific Models
class GuidelineAgentInput(AgentInput):
    triage_output: TriageAgentOutput
    safety_output: SafetyGuardAgentOutput

class GuidelineAgentOutput(AgentOutput):
    relevant_guidelines: List[Dict[str, Any]] = Field(default_factory=list, description="Relevant clinical guidelines")
    local_considerations: List[str] = Field(default_factory=list, description="Local/regional considerations")
    evidence_level: str = Field(..., description="Level of evidence")
    recommendations: List[str] = Field(default_factory=list, description="Specific recommendations")

# Risk Prediction Agent Specific Models
class RiskPredictionAgentInput(AgentInput):
    triage_output: TriageAgentOutput
    safety_output: SafetyGuardAgentOutput
    guideline_output: GuidelineAgentOutput
    chronic_care_data: Optional[ChronicCareData] = None
    historical_data: Optional[List[Dict[str, Any]]] = None

class RiskPredictionAgentOutput(AgentOutput):
    risk_score: RiskScore
    risk_time_horizon: RiskTimeHorizon
    risk_factors: List[str] = Field(default_factory=list, description="Key risk factors")
    risk_explanation: str = Field(..., description="Plain language risk explanation")
    preventive_actions: List[str] = Field(default_factory=list, description="Preventive recommendations")
    follow_up_interval: Optional[str] = Field(None, description="Recommended follow-up interval")

# Coordinator Agent Models
class CoordinatorAgentInput(BaseModel):
    session_id: str
    patient: PatientProfile
    symptoms: SymptomInput
    chronic_care_data: Optional[ChronicCareData] = None
    home_measurements: Optional[List[HomeMeasurement]] = None
    agent_outputs: Dict[AgentType, AgentOutput] = Field(default_factory=dict, description="Outputs from all agents")

class TriageResponseV2(BaseModel):
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    patient_summary: str = Field(..., description="Patient-friendly summary")
    triage_level: TriageLevel
    risk_score: RiskScore
    risk_time_horizon: RiskTimeHorizon
    confidence_score: float = Field(..., ge=0, le=1)
    suggested_next_step: str = Field(..., description="Recommended next action")
    risk_flags: List[str] = Field(default_factory=list, description="Risk flags")
    differential_diagnoses: List[str] = Field(default_factory=list, description="Possible diagnoses")
    recommended_tests: List[str] = Field(default_factory=list, description="Recommended tests")
    relevant_guidelines: List[Dict[str, Any]] = Field(default_factory=list, description="Clinical guidelines used")
    risk_explanation: str = Field(..., description="Risk explanation in plain language")
    preventive_actions: List[str] = Field(default_factory=list, description="Preventive actions")
    follow_up_interval: Optional[str] = Field(None, description="Follow-up recommendation")
    agent_outputs: Dict[AgentType, AgentOutput] = Field(default_factory=dict, description="Individual agent outputs")
    safety_concerns: List[str] = Field(default_factory=list, description="Safety concerns")
    requires_immediate_action: bool = Field(False, description="Whether immediate action is needed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

# Chronic Care Models
class ChronicCareCheckIn(BaseModel):
    session_id: str
    patient_id: str
    condition: ChronicCondition
    check_in_date: datetime = Field(default_factory=datetime.utcnow)
    symptoms: List[str] = Field(default_factory=list, description="Current symptoms")
    medication_taken: bool = Field(..., description="Whether medications were taken")
    side_effects: List[str] = Field(default_factory=list, description="Side effects experienced")
    measurements: List[HomeMeasurement] = Field(default_factory=list, description="Home measurements")
    notes: Optional[str] = Field(None, description="Additional notes")
    risk_score: Optional[RiskScore] = Field(None, description="Current risk assessment")

class ChronicCarePlan(BaseModel):
    patient_id: str
    condition: ChronicCondition
    created_date: datetime = Field(default_factory=datetime.utcnow)
    updated_date: datetime = Field(default_factory=datetime.utcnow)
    goals: List[str] = Field(default_factory=list, description="Care goals")
    medications: List[str] = Field(default_factory=list, description="Prescribed medications")
    monitoring_schedule: Dict[str, str] = Field(default_factory=dict, description="Monitoring schedule")
    red_flags: List[str] = Field(default_factory=list, description="Red flag symptoms")
    follow_up_frequency: str = Field(..., description="Follow-up frequency")
    education_topics: List[str] = Field(default_factory=list, description="Patient education topics")

# Risk Sentinel Models
class RiskSentinelInput(BaseModel):
    patient_id: str
    chronic_care_data: ChronicCareData
    recent_measurements: List[HomeMeasurement] = Field(default_factory=list)
    recent_check_ins: List[ChronicCareCheckIn] = Field(default_factory=list)
    time_window: int = Field(default=30, description="Time window in days")

class RiskSentinelOutput(BaseModel):
    patient_id: str
    risk_status: str = Field(..., pattern=r"^(stable|monitor|escalate)$")
    risk_score: RiskScore
    risk_trend: str = Field(..., pattern=r"^(improving|stable|worsening)$")
    alerts: List[str] = Field(default_factory=list, description="Risk alerts")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    escalation_level: Optional[str] = Field(None, description="Escalation level if needed")
    last_updated: datetime = Field(default_factory=datetime.utcnow)

# Safety & Bias Layer Models
class BiasMetrics(BaseModel):
    language: str
    region: str
    age_group: str
    gender: str
    accuracy: float = Field(..., ge=0, le=1)
    false_negative_rate: float = Field(..., ge=0, le=1)
    over_referral_rate: float = Field(..., ge=0, le=1)
    sample_size: int = Field(..., ge=0)

class SafetyMetrics(BaseModel):
    total_cases: int
    false_negatives: int
    over_referrals: int
    missed_risk_cases: int
    emergency_detection_accuracy: float = Field(..., ge=0, le=1)
    overall_accuracy: float = Field(..., ge=0, le=1)

# EMR Integration Models
class EMRPatientRecord(BaseModel):
    patient_id: str
    external_system: str = Field(..., description="External EMR system name")
    external_id: str = Field(..., description="Patient ID in external system")
    demographic_data: Dict[str, Any]
    medical_history: List[Dict[str, Any]]
    medications: List[Dict[str, Any]]
    allergies: List[str]
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class EMRTriageEvent(BaseModel):
    patient_id: str
    session_id: str
    triage_date: datetime = Field(default_factory=datetime.utcnow)
    triage_level: TriageLevel
    risk_score: RiskScore
    symptoms: str
    recommendations: List[str]
    requires_follow_up: bool
    follow_up_date: Optional[datetime] = Field(None)
    external_system: str = Field(..., description="Target EMR system")
    sync_status: str = Field(default="pending", pattern=r"^(pending|synced|failed)$")

# Hub Models
class HubClinicRegistration(BaseModel):
    clinic_id: str
    clinic_name: str
    region: str
    country: str
    contact_email: str
    api_endpoint: str
    version: str = Field(default="2.0")
    data_sharing_consent: bool = Field(default=True)
    local_rules_enabled: bool = Field(default=False)

class HubTriageRule(BaseModel):
    rule_id: str
    version: str
    condition: str
    symptoms: List[str]
    triage_level: TriageLevel
    evidence_level: str
    source: str
    created_date: datetime = Field(default_factory=datetime.utcnow)
    validated_by: List[str] = Field(default_factory=list, description="Validating clinics")
    usage_count: int = Field(default=0, description="Number of times used")
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