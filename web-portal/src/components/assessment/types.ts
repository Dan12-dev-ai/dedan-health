/**
 * Multimodal Assessment Types
 * 
 * Mirrors the verified backend contract from backend-v2/main_v2.py
 * See docs/MULTIMODAL_FRONTEND_INTEGRATION.md for full contract.
 */

import { PatientProfile, SymptomSeverity, Language } from '../../types';

/** Supported image MIME types per backend validation */
export const SUPPORTED_IMAGE_MIME_TYPES = [
  'image/jpeg',
  'image/png',
  'image/webp',
  'image/heic',
  'image/heif',
] as const;

export type SupportedImageMimeType = typeof SUPPORTED_IMAGE_MIME_TYPES[number];

/** Maximum file size per backend (20 MB) */
export const MAX_IMAGE_SIZE = 20 * 1024 * 1024;

/** Image quality assessment from backend */
export interface ImageQuality {
  overall_score: number;
  resolution: { width: number; height: number };
  brightness_score: number;
  contrast_score: number;
  blur_score: number;
  is_usable: boolean;
  issues: string[];
  recommendations: string[];
  metadata?: Record<string, unknown>;
}

/** Image upload response from backend */
export interface ImageUploadResponse {
  image_id: string;
  filename: string;
  size: number;
  mime_type: string;
  quality_score: number;
  is_usable: boolean;
  upload_timestamp: string;
}

/** Possible medical explanation from image analysis */
export interface PossibleExplanation {
  condition: string;
  likelihood: 'possible' | 'likely' | 'unlikely' | 'differential';
  confidence: number;
  reasoning: string;
  supporting_observations: string[];
  citations: string[];
  icd10_code?: string;
}

/** Image assessment from multimodal analysis */
export interface ImageAssessment {
  observations: string[];
  possible_explanations: PossibleExplanation[];
  limitations: string[];
  requires_better_image: boolean;
  quality_issues: string[];
  image_quality?: ImageQuality;
}

/** Evidence-based medical information */
export interface MedicalInformation {
  topic: string;
  content: string;
  source: string;
  source_type: 'guideline' | 'literature' | 'protocol' | 'consensus';
  relevance_score: number;
  citation?: string;
}

/** Evidence-based treatment guidance */
export interface TreatmentInformation {
  condition: string;
  intervention: string;
  description: string;
  evidence_level: 'A' | 'B' | 'C' | 'D' | 'expert_opinion';
  source: string;
  contraindications: string[];
  precautions: string[];
  dosage_info?: string;
}

/** Source/citation reference */
export interface Source {
  id: string;
  title: string;
  type: 'guideline' | 'pubmed' | 'textbook' | 'protocol' | 'other';
  url?: string;
  authors: string[];
  publication_date?: string;
  snippet?: string;
}

/** Request for multimodal analysis */
export interface MultimodalAnalyzeRequest {
  text?: string;
  voice_transcript?: string;
  image_ids: string[];
  image_data_list: string[]; // base64 encoded
  patient: PatientProfile;
  session_id?: string;
  conversation_history: Array<{ role: 'user' | 'assistant' | 'system'; content: string }>;
  consent: boolean;
}

/** Response from multimodal analysis */
export interface MultimodalAnalyzeResponse {
  request_id: string;
  session_id: string;
  urgency: 'emergency' | 'urgent' | 'routine' | 'self_care';
  recommended_next_step: string;
  image_assessment?: ImageAssessment;
  medical_information: MedicalInformation[];
  treatment_information: TreatmentInformation[];
  warning_signs: string[];
  follow_up_questions: string[];
  sources: Source[];
  uncertainty: string;
  requires_professional_review: boolean;
  safety_notice: string;
  confidence_score: number;
  processing_time_ms: number;
  provider: string;
  model: string;
}

/** Multimodal input state for the UI */
export interface MultimodalInputState {
  text: string;
  duration?: string;
  severity?: SymptomSeverity | '';
  image?: File;
  imagePreview?: string;
  uploadedImageId?: string;
  voiceTranscript?: string;
  isRecording: boolean;
  isUploading: boolean;
  uploadProgress: number;
  error?: string;
}

/** Voice recorder states */
export type VoiceRecorderState = 
  | 'idle'
  | 'recording'
  | 'stopped'
  | 'processing'
  | 'ready'
  | 'error';

export interface VoiceRecorderStateInfo {
  state: VoiceRecorderState;
  duration: number;
  transcript?: string;
  error?: string;
}