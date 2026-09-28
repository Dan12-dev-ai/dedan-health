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
    context: Dict[str, Any] = Field(default_factory=dict)
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
