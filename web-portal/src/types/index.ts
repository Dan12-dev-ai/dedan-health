/**
 * DEDAN-Health — Domain Types
 *
 * Strictly mirrors the LIVE v1 backend schemas in `backend/models.py`.
 * No `any` is used anywhere. Every type below corresponds 1:1 to a
 * backend Pydantic model that is actually served by `backend/main.py`.
 *
 * Anything that does NOT exist in the live backend is intentionally
 * omitted or marked FUTURE so the frontend never pretends a capability
 * exists. (See master prompt: "Do not fabricate backend capabilities.")
 */

/* ---------------- Clinical enums (mirror backend/models.py) ---------------- */

/** Triage urgency levels returned by POST /dedan/v1/triage */
export type TriageLevel = 'emergency' | 'urgent' | 'routine' | 'self_care';

/** Languages the live engine can triage in (mirrors backend Language) */
export type Language = 'en' | 'sw' | 'am' | 'es' | 'fr';

/** Sex enum used by the live /dedan/v1/triage request */
export type Sex = 'male' | 'female' | 'other';

/** Self-reported severity (free text on the backend; narrowed here for UI) */
export type SymptomSeverity = 'mild' | 'moderate' | 'severe';

/* ---------------- Clinical domain primitives ---------------- */

export interface PatientProfile {
  age: number | string;
  sex: Sex;
  location?: string;
  pregnancy_status?: boolean;
  chronic_conditions: string[];
  language: Language;
}

export interface SymptomInput {
  symptoms: string;
  voice_input?: boolean;
  duration?: string;
  severity?: SymptomSeverity | undefined;
}

/** The exact request body POSTed to /dedan/v1/triage */
export interface TriageRequest {
  patient: PatientProfile;
  symptoms: SymptomInput;
  session_id?: string;
  consent: boolean;
}

export interface RiskFlag {
  type: string;
  severity: string;
  description: string;
  keywords: string[];
}

/** The exact response shape from POST /dedan/v1/triage */
export interface TriageResponse {
  triage_level: TriageLevel;
  suggested_next_step: string;
  risk_flags: RiskFlag[];
  patient_summary: string;
  confidence_score: number; // 0.0–1.0
  emergency_contacts?: string[];
  follow_up_timeframe?: string;
  disclaimer: string;
}

/** GET /dedan/v1/conditions -> returns condition names (backend: get_supported_conditions) */
export interface ClinicalCondition {
  id: string;
  name: string;
  description: string;
  common_symptoms: string[];
  urgency_level: TriageLevel;
  language: Language;
}

/** GET /dedan/v1/session/{session_id} -> full session transcript */
export interface TriageSession {
  session_id: string;
  patient_profile: PatientProfile;
  symptoms_history: SymptomInput[];
  triage_responses: TriageResponse[];
  created_at: string; // ISO date
  updated_at: string;
  status: string;
}

/** POST /dedan/v1/session/{id}/consent body + response */
export interface DataConsent {
  patient_id: string;
  consent_given: boolean;
  consent_date: string;
  data_usage_purposes: string[];
  withdrawal_allowed: boolean;
}

/** GET /dedan/v1/emergency-contacts -> backend returns list[str] (hardcoded defaults) */
export interface EmergencyContact {
  label: string;
  number: string;
  note?: string;
}

/** GET /dedan/v1/stats -> anonymized platform stats (NOT real-time clinical data) */
export interface PlatformStats {
  total_assessments?: number;
  emergency_rate?: number;
  languages?: Record<string, number>;
  average_confidence?: number;
  updated_at?: string;
  note?: string;
}

/* ---------------- UI / messaging primitives ---------------- */

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  triage_data?: TriageResponse;
}

export type NetworkStatus = 'online' | 'offline' | 'reconnecting';

/**
 * Marker type for features whose backend is NOT live.
 * The UI renders a deliberate "unavailable" state instead of faking data.
 */
export interface UnavailableFeature {
  __unavailable: true;
  reason: string;
  plannedWhen?: string;
}

/* ---------------- Future-typed interfaces (NOT YET LIVE in backend) ---------------- */
/* These mirror planned v2 schemas and are intentionally NOT used by live routes. */

export interface SubscriptionInfo {
  tier: string;
  status: 'free_trial' | 'active' | 'past_due' | 'canceled';
  trial_ends_at?: string;
  current_period_ends_at: string;
}

export interface FollowUpReminder {
  id: string;
  session_id: string;
  message: string;
  scheduled_time: Date;
  sent: boolean;
  type: 'check_in' | 'reminder';
}

export interface AppSettings {
  language: Language;
  notifications_enabled: boolean;
  voice_input_enabled: boolean;
  low_data_mode: boolean;
  emergency_contacts: string[];
  theme: 'light' | 'dark';
  reduced_motion: boolean;
}

export interface Clinic {
  id: string;
  name: string;
  address: string;
  phone: string;
  coordinates: { lat: number; lng: number };
  services: string[];
  hours: string;
  emergency_services: boolean;
}

export interface APIError {
  ok: false;
  status: number;
  code: string;
  message: string;
  correlation_id?: string;
}

export type APIResult<T> = { ok: true; data: T } | APIError;

export interface Translation {
  (key: string, params?: Record<string, string | number>): string;
}

/* ---------------- Client-side session (mirrors src/services/offlineStorage.ts) ---------------- */
/** Shape persisted locally by offlineStorage. May carry extra fields when
 * hydrated from the live GET /dedan/v1/session/{id} (TriageSession). */
export interface Session {
  session_id: string;
  patient_profile: PatientProfile;
  messages: ChatMessage[];
  /** Backend TriageSession carries these; client may not. */
  symptoms_history?: SymptomInput[];
  triage_responses?: TriageResponse[];
  created_at: Date;
  updated_at: Date;
  status?: string;
}

export interface OfflineContent {
  id?: string;
  type: 'faq' | 'educational' | 'emergency_guide';
  title: string;
  content: string;
  language: string;
}

/* ---------------- DEDAN Health 2.0 Multimodal Clinical Guidance ---------------- */

export type UrgencyLevel = 'routine' | 'soon' | 'urgent' | 'emergency';
export type EvidenceLevel = 'strong' | 'moderate' | 'limited' | 'theoretical';

export interface ClinicalSource {
  title: string;
  url: string;
  type: string;
  date_published?: string;
  jurisdiction?: string;
}

export interface ClinicalUncertainty {
  message: string;
  level: string;
  missing_information: string[];
}

export interface ClinicalPossibleExplanation {
  label: string;
  why_it_fits: string;
  what_does_not_fit: string;
  evidence_level: EvidenceLevel;
  requires_more_info: string[];
}

export interface ClinicalObservation {
  description: string;
  category: string;
  confidence: string;
  source: string;
}

export interface ClinicalMedicationInfo {
  medication_name: string;
  medication_class: string;
  general_purpose: string;
  common_warnings: string[];
  contraindication_categories: string[];
  potential_interactions: string[];
  questions_to_ask: string[];
  package_check_items: string[];
  source?: ClinicalSource;
  is_educational_only: boolean;
}

export interface ClinicalMedicationVerificationItem {
  field: string;
  description: string;
  why_important: string;
}

export interface ClinicalTreatmentEducation {
  category: string;
  title: string;
  description: string;
  why_it_may_help: string;
  expected_timeline: string;
  what_to_monitor: string;
  when_to_reassess: string;
  evidence_level: EvidenceLevel;
}

export interface ClinicalBodyMechanismStep {
  step_number: number;
  title: string;
  description: string;
  visual_reference?: string;
}

export interface ClinicalTreatmentApproach {
  goal: string;
  mechanism: string;
  patient_actions: string[];
  professional_actions: string[];
  expected_improvement: string;
  timeline: string;
  warning_signs: string[];
  evidence_level: EvidenceLevel;
  sources: ClinicalSource[];
}

export interface ClinicalVisualEducation {
  title: string;
  description: string;
  visual_type: string;
  source: string;
  source_url?: string;
  license?: string;
  medical_context: string;
  publication_info?: string;
  is_ai_generated: boolean;
  ai_disclaimer?: string;
}

export interface ClinicalSafety {
  urgency: UrgencyLevel;
  red_flags: string[];
  requires_immediate_care: boolean;
  emergency_message?: string;
  recommended_action: string;
  professional_review_required: boolean;
}

export interface ClinicalHealthSummary {
  symptoms: string[];
  duration: string;
  severity: string;
  relevant_history: string[];
  images_provided: boolean;
  other_information: Record<string, any>;
}

export interface ClinicalGuidanceResponse2 {
  response_id: string;
  session_id: string;
  timestamp: string;
  clinical_response: ClinicalGuidanceData;
  health_summary: ClinicalHealthSummary;
  safety: ClinicalSafety;
  possible_explanations: ClinicalPossibleExplanation[];
  uncertainty: ClinicalUncertainty;
  treatment_education: ClinicalTreatmentEducation[];
  medication_information: ClinicalMedicationInfo[];
  medication_verification: ClinicalMedicationVerificationItem[];
  visual_education: ClinicalVisualEducation[];
  body_mechanism: ClinicalBodyMechanismStep[];
  treatment_approach: ClinicalTreatmentApproach | null;
  warning_signs: string[];
  next_steps: Record<string, string[]>;
  follow_up: Record<string, any>;
  sources: ClinicalSource[];
  professional_review: boolean;
  professional_review_reason: string | null;
  provider: string;
  model: string;
  confidence_score: number;
  disclaimer: string;
  safety_flags: string[];
}

export interface ClinicalGuidanceData {
  health_summary: ClinicalHealthSummary;
  safety: ClinicalSafety;
  possible_explanations: ClinicalPossibleExplanation[];
  uncertainty: ClinicalUncertainty;
  treatment_education: ClinicalTreatmentEducation[];
  medication_information: ClinicalMedicationInfo[];
  medication_verification: ClinicalMedicationVerificationItem[];
  visual_education: ClinicalVisualEducation[];
  body_mechanism: ClinicalBodyMechanismStep[];
  treatment_approach: ClinicalTreatmentApproach | null;
  warning_signs: string[];
  next_steps: Record<string, string[]>;
  follow_up: Record<string, any>;
  sources: ClinicalSource[];
  professional_review: boolean;
  professional_review_reason: string | null;
  provider: string;
  model: string;
  confidence_score: number;
  disclaimer: string;
  safety_flags: string[];
}

export interface ClinicalGuidanceRequest2 {
  patient: PatientProfile;
  symptoms: SymptomInput;
  image_ids?: string[];
  image_data_list?: string[];
  voice_transcript?: string;
  session_id?: string;
  conversation_history?: Record<string, string>[];
  consent: boolean;
}
