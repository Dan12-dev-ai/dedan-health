/**
 * DEDAN-Health — Multimodal Assessment Service
 * 
 * Connects to the multimodal AI endpoints in backend-v2/main_v2.py.
 * Every method returns APIResult<T> so the UI never mistakes a network
 * failure for a successful (but fake) response.
 * 
 * Live backend routes (verified):
 *   POST /dedan/v2/images/upload
 *   POST /dedan/v2/multimodal-analyze
 *   GET  /dedan/v2/images/{image_id}
 *   GET  /dedan/v2/images/{image_id}/content
 *   DELETE /dedan/v2/images/{image_id}
 *   GET  /dedan/v2/multimodal/health
 */

import { apiClient, DedanAPIClient } from './apiClient';
import { APIResult } from '../types';
import { 
  ImageUploadResponse, 
  MultimodalAnalyzeRequest, 
  MultimodalAnalyzeResponse,
  ImageAssessment 
} from '../components/assessment/types';

export type { ImageUploadResponse };

/**
 * Upload a medical image for analysis.
 * Uses multipart/form-data — let the browser set the Content-Type boundary.
 */
export async function uploadImage(
  file: File,
  sessionId?: string
): Promise<APIResult<ImageUploadResponse>> {
  const formData = new FormData();
  formData.append('file', file);
  if (sessionId) {
    formData.append('session_id', sessionId);
  }

  return apiClient.request<ImageUploadResponse>('/dedan/v2/images/upload', {
    method: 'POST',
    // Do NOT set Content-Type — let browser generate multipart boundary
    body: formData,
  }, { 
    timeoutMs: 60000, // Longer timeout for uploads
  });
}

/**
 * Submit multimodal analysis (text + image + optional voice transcript).
 * Uses application/json.
 */
export async function submitMultimodalAnalysis(
  request: MultimodalAnalyzeRequest
): Promise<APIResult<MultimodalAnalyzeResponse>> {
  return apiClient.request<MultimodalAnalyzeResponse>('/dedan/v2/multimodal-analyze', {
    method: 'POST',
    body: JSON.stringify(request),
  }, { 
    timeoutMs: 90000, // Multimodal analysis takes longer
  });
}

/**
 * Get image metadata by ID.
 */
export async function getImageMetadata(imageId: string): Promise<APIResult<Omit<ImageUploadResponse, 'upload_timestamp'>>> {
  return apiClient.request(`/dedan/v2/images/${encodeURIComponent(imageId)}`, {
    method: 'GET',
  }, { timeoutMs: 10000, allowOffline: true });
}

/**
 * Get image content (base64 encoded).
 */
export async function getImageContent(imageId: string): Promise<APIResult<{ image_id: string; content: string; mime_type: string }>> {
  return apiClient.request(`/dedan/v2/images/${encodeURIComponent(imageId)}/content`, {
    method: 'GET',
  }, { timeoutMs: 15000, allowOffline: true });
}

/**
 * Delete uploaded image.
 */
export async function deleteImage(imageId: string): Promise<APIResult<{ message: string; image_id: string }>> {
  return apiClient.request(`/dedan/v2/images/${encodeURIComponent(imageId)}`, {
    method: 'DELETE',
  }, { timeoutMs: 10000 });
}

/**
 * Health check for multimodal providers.
 */
export async function multimodalHealthCheck(): Promise<APIResult<{ status: string; providers: Record<string, boolean> }>> {
  return apiClient.request('/dedan/v2/multimodal/health', {
    method: 'GET',
  }, { timeoutMs: 10000, allowOffline: true });
}

/**
 * Convert File to base64 string for inline image submission.
 */
export function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      // Remove data URL prefix if present
      const base64 = result.split(',')[1] || result;
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

/**
 * Validate image file on client side before upload.
 */
export interface ImageValidationResult {
  valid: boolean;
  error?: string;
  warning?: string;
}

export function validateImageFile(file: File): ImageValidationResult {
  const SUPPORTED_TYPES = [
    'image/jpeg',
    'image/png',
    'image/webp',
    'image/heic',
    'image/heif',
  ];
  const MAX_SIZE = 20 * 1024 * 1024; // 20 MB

  if (!SUPPORTED_TYPES.includes(file.type)) {
    return {
      valid: false,
      error: `Unsupported file type: ${file.type}. Supported: JPEG, PNG, WebP, HEIC`,
    };
  }

  if (file.size > MAX_SIZE) {
    return {
      valid: false,
      error: `File too large: ${(file.size / 1024 / 1024).toFixed(1)} MB. Maximum: 20 MB`,
    };
  }

  const warnings: string[] = [];
  if (file.size > 5 * 1024 * 1024) {
    warnings.push('Large file may take longer to upload');
  }

  return {
    valid: true,
    warning: warnings.join('; '),
  };
}
/** POST /dedan/v2/clinical-guidance — structured clinical guidance (v2). */
export async function postClinicalGuidance(
  request: import('../types').ClinicalGuidanceRequest2
): Promise<APIResult<import('../types').ClinicalGuidanceResponse2>> {
  return apiClient.request<import('../types').ClinicalGuidanceResponse2>(
    '/dedan/v2/clinical-guidance',
    { method: 'POST', body: JSON.stringify(request) },
    { timeoutMs: 45000 }
  );
}

/** POST /dedan/v2/conversation — a conversation turn. */
export async function postConversationTurn(
  sessionId: string,
  message: string,
  patient: import('../types').PatientProfile
): Promise<APIResult<Record<string, any>>> {
  return apiClient.request<Record<string, any>>(
    `/dedan/v2/conversation`,
    { method: 'POST', body: JSON.stringify({ session_id: sessionId, message, patient }) },
    { timeoutMs: 30000 }
  );
}

/** GET /dedan/v2/evidence/{topic} — evidence retrieval. */
export async function getEvidence(topic: string): Promise<APIResult<Record<string, any>>> {
  return apiClient.request<Record<string, any>>(
    `/dedan/v2/evidence/${encodeURIComponent(topic)}`,
    { method: 'GET' },
    { timeoutMs: 15000 }
  );
}

/** GET /dedan/v2/medication/{medication_name} — medication safety info. */
export async function getMedicationSafety(
  medicationName: string
): Promise<APIResult<Record<string, any>>> {
  return apiClient.request<Record<string, any>>(
    `/dedan/v2/medication/${encodeURIComponent(medicationName)}`,
    { method: 'GET' },
    { timeoutMs: 15000 }
  );
}

/** GET /dedan/v2/visuals/{topic} — educational visuals. */
export async function getVisualEducation(
  topic: string
): Promise<APIResult<Record<string, any>>> {
  return apiClient.request<Record<string, any>>(
    `/dedan/v2/visuals/${encodeURIComponent(topic)}`,
    { method: 'GET' },
    { timeoutMs: 15000 }
  );
}

/** GET /dedan/v2/urgency/check — urgency check. */
export async function getUrgencyCheck(
  symptoms: string,
  severity?: string
): Promise<APIResult<Record<string, any>>> {
  const params = new URLSearchParams({ symptoms });
  if (severity) params.set('severity', severity);
  return apiClient.request<Record<string, any>>(
    `/dedan/v2/urgency/check?${params.toString()}`,
    { method: 'GET' },
    { timeoutMs: 10000 }
  );
}
