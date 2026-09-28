export interface PatientProfile {
  age: number;
  sex: 'male' | 'female' | 'other';
  location?: string;
  pregnancy_status?: boolean;
  chronic_conditions: string[];
  language: 'en' | 'sw' | 'am' | 'es' | 'fr';
}

export interface SymptomInput {
  symptoms: string;
  voice_input?: boolean;
  duration?: string;
  severity?: 'mild' | 'moderate' | 'severe';
}

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

export type TriageLevel = 'emergency' | 'urgent' | 'routine' | 'self_care';

export interface TriageResponse {
  triage_level: TriageLevel;
  suggested_next_step: string;
  risk_flags: RiskFlag[];
  patient_summary: string;
  confidence_score: number;
  emergency_contacts?: string[];
  follow_up_timeframe?: string;
  disclaimer: string;
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  triage_data?: TriageResponse;
}

export interface Clinic {
  id: string;
  name: string;
  address: string;
  phone: string;
  coordinates: {
    lat: number;
    lng: number;
  };
  services: string[];
  hours: string;
  emergency_services: boolean;
  distance?: number;
}

export interface FollowUpReminder {
  id: string;
  session_id: string;
  message: string;
  scheduled_time: Date;
  sent: boolean;
  type: 'check_in' | 'reminder' | 'educational';
}

export interface AppSettings {
  language: string;
  notifications_enabled: boolean;
  voice_input_enabled: boolean;
  low_data_mode: boolean;
  emergency_contacts: string[];
}
