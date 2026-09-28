export interface TriageCase {
  id: string;
  session_id: string;
  patient_info: {
    age_group: string;
    sex: string;
    language: string;
    location?: string;
    chronic_conditions: string[];
  };
  symptoms: {
    keywords: string[];
    description: string;
    timestamp: string;
  };
  dedan_assessment: {
    triage_level: 'emergency' | 'urgent' | 'routine' | 'self_care';
    confidence_score: number;
    risk_flags: string[];
    suggested_next_step: string;
    patient_summary: string;
  };
  clinic_review: {
    status: 'pending' | 'seen' | 'referred' | 'self_care_follow_up' | 'closed';
    reviewed_by?: string;
    reviewed_at?: string;
    doctor_notes?: string;
    final_triage_level?: 'emergency' | 'urgent' | 'routine' | 'self_care';
    final_diagnosis?: string;
    treatment_given?: string;
    follow_up_required?: boolean;
    follow_up_date?: string;
  };
  created_at: string;
  updated_at: string;
}

export interface ClinicStats {
  total_cases: number;
  cases_by_level: {
    emergency: number;
    urgent: number;
    routine: number;
    self_care: number;
  };
  cases_by_language: Record<string, number>;
  cases_by_hour: Array<{ hour: number; cases: number }>;
  cases_by_day: Array<{ date: string; cases: number }>;
  accuracy_metrics: {
    dedan_vs_doctor_agreement: number;
    emergency_detection_accuracy: number;
    average_response_time: number;
  };
  top_symptoms: Array<{ symptom: string; count: number }>;
}

export interface ClinicUser {
  id: string;
  name: string;
  email: string;
  role: 'doctor' | 'nurse' | 'admin' | 'triage_nurse';
  department: string;
  active: boolean;
  last_login: string;
}

export interface ClinicSettings {
  id: string;
  name: string;
  address: string;
  phone: string;
  emergency_services: boolean;
  operating_hours: {
    monday: string;
    tuesday: string;
    wednesday: string;
    thursday: string;
    friday: string;
    saturday: string;
    sunday: string;
  };
  capacity: {
    emergency_beds: number;
    general_beds: number;
    icu_beds: number;
    available_doctors: number;
    available_nurses: number;
  };
  referral_network: string[];
  auto_triage_threshold: number;
}

export interface ExportFilters {
  date_range: {
    start: string;
    end: string;
  };
  triage_levels: string[];
  languages: string[];
  status: string[];
  include_phi: boolean;
}

export interface DashboardWidget {
  id: string;
  title: string;
  type: 'stats' | 'chart' | 'list' | 'alert';
  data: any;
  config: any;
}
