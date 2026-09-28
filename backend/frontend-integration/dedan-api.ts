/**
 * DEDAN Health API Client for Next.js/React Frontend
 * 
 * Usage:
 * import { dedanApi } from '@/lib/dedan-api';
 * 
 * const response = await dedanApi.analyze({
 *   patient_age: 25,
 *   patient_sex: 'female',
 *   symptom_description: 'Fever and headache for 2 days...',
 *   image_ids: ['img_123'],
 *   consent: true
 * });
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';

// =============================================================================
// Types (matching backend schemas)
// =============================================================================

export interface PatientProfile {
  patient_age: number;
  patient_sex: 'male' | 'female' | 'other';
  patient_location?: string;
  patient_pregnant?: boolean;
  patient_chronic_conditions?: string[];
  patient_medications?: string[];
  patient_allergies?: string[];
  patient_language?: string;
}

export interface AnalyzeRequest extends PatientProfile {
  symptom_description: string;
  symptom_duration?: string;
  symptom_severity?: 'mild' | 'moderate' | 'severe';
  image_ids?: string[];
  image_data_list?: string[];  // base64 strings or data URLs
  voice_transcript?: string;
  session_id?: string;
  conversation_history?: Array<{ role: string; content: string }>;
  consent: boolean;
}

export interface PossibleCondition {
  name: string;
  confidence: 'high' | 'medium' | 'low';
  confidence_score: number;
  reasoning: string;
  supporting_evidence: string[];
  contradicting_evidence: string[];
  requires_more_info: string[];
}

export interface FirstAidStep {
  step_number: number;
  title: string;
  description: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  time_sensitive: boolean;
  contraindications: string[];
}

export interface WhatToTellDoctor {
  key_points: string[];
  symptom_timeline: string;
  image_findings: string[];
  home_treatments_tried: string[];
  questions_to_ask: string[];
}

export interface RecommendedMedicineClass {
  medicine_class: string;
  generic_examples: string[];
  indication: string;
  mechanism: string;
  important_warnings: string[];
  contraindications: string[];
  requires_prescription: boolean;
  evidence_level: 'strong' | 'moderate' | 'limited' | 'expert_opinion';
  source_guideline: string;
}

export interface PharmacyGuidance {
  how_to_obtain: string;
  trusted_sources: string[];
  verification_tips: string[];
  country_specific: string;
  cost_considerations: string;
  warning_against: string[];
}

export interface Disclaimer {
  text: string;
  short_version: string;
  must_acknowledge: boolean;
}

export interface NextSteps {
  immediate: string[];
  within_hours: string[];
  within_days: string[];
  follow_up_with: string;
}

export interface AnalyzeResponse {
  request_id: string;
  session_id: string;
  timestamp: string;
  possible_conditions: PossibleCondition[];
  urgency_level: 'self_care' | 'see_doctor_soon' | 'emergency';
  urgency_reasoning: string;
  first_aid_steps: FirstAidStep[];
  what_to_tell_your_doctor: WhatToTellDoctor;
  recommended_medicine_class?: RecommendedMedicineClass;
  pharmacy_guidance?: PharmacyGuidance;
  disclaimer: Disclaimer;
  next_steps: NextSteps;
  processing_time_ms: number;
  ai_provider: string;
  ai_model: string;
  confidence_score: number;
  requires_professional_review: boolean;
  safety_flags: string[];
  image_assessment?: Record<string, any>;
}

export interface ImageUploadResponse {
  image_id: string;
  filename: string;
  size_bytes: number;
  mime_type: string;
  quality_score: number;
  is_usable: boolean;
  upload_timestamp: string;
  preview_url?: string;
}

export interface HealthCheckResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version: string;
  components: Record<string, string>;
  ai_providers: Record<string, boolean>;
}

export interface ApiError {
  error: string;
  error_code: string;
  details?: Record<string, any>;
  request_id?: string;
  timestamp: string;
}

// =============================================================================
// API Client Class
// =============================================================================

class DedanApiClient {
  private client: AxiosInstance;
  private baseUrl: string;

  constructor(baseUrl: string = process.env.NEXT_PUBLIC_DEDAN_API_URL || 'http://localhost:8000') {
    this.baseUrl = baseUrl;
    
    this.client = axios.create({
      baseURL: baseUrl,
      timeout: 60000,  // 60 seconds for AI analysis
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor - add auth, logging
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        // Add API key if available
        const apiKey = process.env.NEXT_PUBLIC_DEDAN_API_KEY;
        if (apiKey) {
          config.headers['X-API-Key'] = apiKey;
        }
        
        // Add session ID for tracking
        const sessionId = this.getSessionId();
        if (sessionId) {
          config.headers['X-Session-ID'] = sessionId;
        }

        console.log(`[DedanAPI] ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor - handle errors
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        console.error('[DedanAPI] Error:', error.response?.data || error.message);
        return Promise.reject(this.normalizeError(error));
      }
    );
  }

  private getSessionId(): string {
    if (typeof window !== 'undefined') {
      let sessionId = sessionStorage.getItem('dedan_session_id');
      if (!sessionId) {
        sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        sessionStorage.setItem('dedan_session_id', sessionId);
      }
      return sessionId;
    }
    return `server_${Date.now()}`;
  }

  private normalizeError(error: AxiosError): Error & { code?: string; status?: number; details?: any } {
    const err = new Error(error.message) as Error & { code?: string; status?: number; details?: any };
    err.code = error.code;
    err.status = error.response?.status;
    err.details = error.response?.data;
    return err;
  }

  // =========================================================================
  // Image Upload
  // =========================================================================

  /**
   * Upload an image file for analysis
   */
  async uploadImage(file: File, sessionId?: string): Promise<ImageUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (sessionId) {
      formData.append('session_id', sessionId);
    }

    const response = await this.client.post<ImageUploadResponse>('/api/images/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  }

  /**
   * Upload a base64-encoded image
   */
  async uploadImageBase64(base64Data: string, filename: string = 'image.jpg', sessionId?: string): Promise<ImageUploadResponse> {
    const response = await this.client.post<ImageUploadResponse>('/api/images/upload-base64', {
      image_data: base64Data,
      filename,
      session_id: sessionId,
    });
    return response.data;
  }

  /**
   * Get image metadata
   */
  async getImageMetadata(imageId: string): Promise<any> {
    const response = await this.client.get(`/api/images/${imageId}`);
    return response.data;
  }

  /**
   * Get image preview as base64
   */
  async getImagePreview(imageId: string): Promise<{ image_id: string; content: string; mime_type: string }> {
    const response = await this.client.get(`/api/images/${imageId}/preview`);
    return response.data;
  }

  /**
   * Delete an uploaded image
   */
  async deleteImage(imageId: string): Promise<{ message: string; image_id: string }> {
    const response = await this.client.delete(`/api/images/${imageId}`);
    return response.data;
  }

  // =========================================================================
  // Analysis
  // =========================================================================

  /**
   * Main analysis endpoint - multi-modal medical triage
   */
  async analyze(request: AnalyzeRequest): Promise<AnalyzeResponse> {
    // Ensure session_id is included
    const payload = {
      ...request,
      session_id: request.session_id || this.getSessionId(),
      consent: request.consent ?? true,
    };

    const response = await this.client.post<AnalyzeResponse>('/api/analyze', payload);
    return response.data;
  }

  /**
   * Quick text-only analysis (convenience method)
   */
  async analyzeText(
    symptomDescription: string,
    patient: PatientProfile,
    options?: {
      symptom_duration?: string;
      symptom_severity?: 'mild' | 'moderate' | 'severe';
      session_id?: string;
      conversation_history?: Array<{ role: string; content: string }>;
    }
  ): Promise<AnalyzeResponse> {
    return this.analyze({
      ...patient,
      symptom_description: symptomDescription,
      symptom_duration: options?.symptom_duration,
      symptom_severity: options?.symptom_severity,
      session_id: options?.session_id,
      conversation_history: options?.conversation_history,
      consent: true,
    });
  }

  /**
   * Analysis with image file (convenience method)
   */
  async analyzeWithImage(
    symptomDescription: string,
    patient: PatientProfile,
    imageFile: File,
    options?: {
      symptom_duration?: string;
      symptom_severity?: 'mild' | 'moderate' | 'severe';
      session_id?: string;
      conversation_history?: Array<{ role: string; content: string }>;
    }
  ): Promise<AnalyzeResponse> {
    // Upload image first
    const uploadResult = await this.uploadImage(imageFile, options?.session_id);
    
    // Then analyze with image_id
    return this.analyze({
      ...patient,
      symptom_description: symptomDescription,
      symptom_duration: options?.symptom_duration,
      symptom_severity: options?.symptom_severity,
      image_ids: [uploadResult.image_id],
      session_id: options?.session_id,
      conversation_history: options?.conversation_history,
      consent: true,
    });
  }

  // =========================================================================
  // Health & Providers
  // =========================================================================

  async healthCheck(): Promise<HealthCheckResponse> {
    const response = await this.client.get<HealthCheckResponse>('/api/health');
    return response.data;
  }

  async listProviders(): Promise<{
    providers: Array<{
      name: string;
      model: string;
      supports_vision: boolean;
      supports_audio: boolean;
      is_primary: boolean;
    }>;
    primary: string;
    fallback_order: string[];
  }> {
    const response = await this.client.get('/api/providers');
    return response.data;
  }
}

// =============================================================================
// Singleton Instance & Helper Functions
// =============================================================================

let apiInstance: DedanApiClient | null = null;

export function getDedanApi(baseUrl?: string): DedanApiClient {
  if (!apiInstance || (baseUrl && apiInstance['baseUrl'] !== baseUrl)) {
    apiInstance = new DedanApiClient(baseUrl);
  }
  return apiInstance;
}

// Convenience exports
export const dedanApi = getDedanApi();

// React hook for using the API (if using React)
export function useDedanApi() {
  return getDedanApi();
}

// =============================================================================
// Helper Functions for Common UI Patterns
// =============================================================================

export function getUrgencyColor(urgency: AnalyzeResponse['urgency_level']): string {
  switch (urgency) {
    case 'emergency': return 'text-red-600 bg-red-50 border-red-200';
    case 'see_doctor_soon': return 'text-amber-600 bg-amber-50 border-amber-200';
    case 'self_care': return 'text-green-600 bg-green-50 border-green-200';
    default: return 'text-gray-600 bg-gray-50 border-gray-200';
  }
}

export function getUrgencyLabel(urgency: AnalyzeResponse['urgency_level']): string {
  switch (urgency) {
    case 'emergency': return '🚨 Emergency - Go to ER Now';
    case 'see_doctor_soon': return '⚠️ See Doctor Soon (within 24h)';
    case 'self_care': return '✅ Self-Care Appropriate';
    default: return 'Unknown';
  }
}

export function getUrgencyAction(urgency: AnalyzeResponse['urgency_level']): string {
  switch (urgency) {
    case 'emergency': return 'Call emergency services or go to nearest emergency department immediately';
    case 'see_doctor_soon': return 'Contact a doctor or clinical officer within 24 hours';
    case 'self_care': return 'Monitor symptoms and follow self-care guidance';
    default: return 'Consult a healthcare professional';
  }
}

export function formatConfidence(score: number): string {
  if (score >= 0.8) return 'High';
  if (score >= 0.5) return 'Medium';
  return 'Low';
}

export function getConfidenceColor(score: number): string {
  if (score >= 0.8) return 'text-green-600';
  if (score >= 0.5) return 'text-amber-600';
  return 'text-red-600';
}

// =============================================================================
// Example Usage in a React Component
// =============================================================================
/*
import { dedanApi, AnalyzeRequest, AnalyzeResponse, useDedanApi } from '@/lib/dedan-api';

function TriageForm() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [image, setImage] = useState<File | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const patient = {
        patient_age: 25,
        patient_sex: 'female' as const,
        patient_location: 'Kenya',
        patient_pregnant: false,
        patient_chronic_conditions: [],
        patient_medications: [],
        patient_allergies: [],
        patient_language: 'en',
      };

      let response: AnalyzeResponse;
      
      if (image) {
        response = await dedanApi.analyzeWithImage(
          formData.symptoms,
          patient,
          image,
          { symptom_duration: '2 days', symptom_severity: 'moderate' }
        );
      } else {
        response = await dedanApi.analyzeText(
          formData.symptoms,
          patient,
          { symptom_duration: '2 days', symptom_severity: 'moderate' }
        );
      }

      setResult(response);
    } catch (err: any) {
      setError(err.details?.error || err.message || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* form fields */}
      {result && (
        <div className={getUrgencyColor(result.urgency_level)}>
          <h3>{getUrgencyLabel(result.urgency_level)}</h3>
          <p>{getUrgencyAction(result.urgency_level)}</p>
        </div>
      )}
    </form>
  );
}
*/