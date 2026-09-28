/**
 * DEDAN-Health — Live Triage & Session Service
 *
 * Connects ONLY to routes that actually exist in the live backend
 * (backend/main.py). Every method returns APIResult<T> so the UI never
 * mistakes a network failure for a successful (but fake) response.
 *
 * Live backend routes (verified):
 *   POST /dedan/v1/triage
 *   GET  /dedan/v1/conditions?language=
 *   GET  /dedan/v1/session/{session_id}
 *   POST /dedan/v1/session/{session_id}/consent
 *   GET  /dedan/v1/emergency-contacts
 *   GET  /dedan/v1/stats
 */

import { apiClient } from './apiClient';
import {
  TriageRequest,
  TriageResponse,
  Language,
  TriageSession,
  DataConsent,
  EmergencyContact,
  PlatformStats,
  APIResult,
} from '../types';

/** POST /dedan/v1/triage — the core assessment. Server-side LLM, long timeout. */
export async function postTriage(
  request: TriageRequest
): Promise<APIResult<TriageResponse>> {
  return apiClient.request<TriageResponse>('/dedan/v1/triage', {
    method: 'POST',
    body: JSON.stringify(request),
  }, { timeoutMs: 45000 });
}

/** GET /dedan/v1/conditions?language= — localized condition list the engine knows. */
export async function getConditions(language: Language = 'en'): Promise<APIResult<string[]>> {
  return apiClient.request<string[]>(`/dedan/v1/conditions?language=${encodeURIComponent(language)}`, {
    method: 'GET',
  }, { timeoutMs: 15000, allowOffline: true });
}

/** GET /dedan/v1/session/{session_id} — retrieve a prior session transcript. */
export async function getSession(sessionId: string): Promise<APIResult<TriageSession>> {
  return apiClient.request<TriageSession>(`/dedan/v1/session/${encodeURIComponent(sessionId)}`, {
    method: 'GET',
  }, { timeoutMs: 15000, allowOffline: true });
}

/** POST /dedan/v1/session/{session_id}/consent — record data-consent choice. */
export async function saveConsent(
  sessionId: string,
  consent: Pick<DataConsent, 'consent_given' | 'data_usage_purposes'>
): Promise<APIResult<{ success: boolean }>> {
  return apiClient.request<{ success: boolean }>(
    `/dedan/v1/session/${encodeURIComponent(sessionId)}/consent`,
    { method: 'POST', body: JSON.stringify(consent) },
    { timeoutMs: 15000 }
  );
}

/** GET /dedan/v1/emergency-contacts — backend returns hardcoded defaults (location-agnostic). */
export async function getEmergencyContacts(): Promise<APIResult<EmergencyContact[]>> {
  return apiClient.request<any[]>(`/dedan/v1/emergency-contacts`, { method: 'GET' }, { timeoutMs: 10000, allowOffline: true });
}

/** GET /dedan/v1/stats — anonymized platform stats. NOTE: not real-time clinical data. */
export async function getPlatformStats(): Promise<APIResult<PlatformStats>> {
  return apiClient.request<PlatformStats>(`/dedan/v1/stats`, { method: 'GET' }, { timeoutMs: 15000, allowOffline: true });
}

/** GET /health + GET / — connectivity/version probes. */
export async function healthCheck(): Promise<APIResult<{ status: string; engine_status?: string }>> {
  return apiClient.request<{ status: string; engine_status?: string }>(`/health`, { method: 'GET' }, { timeoutMs: 10000, allowOffline: true });
}

export async function getRoot(): Promise<APIResult<{ message: string; version: string; status: string }>> {
  return apiClient.request(`/`, { method: 'GET' }, { timeoutMs: 10000, allowOffline: true });
}

/** POST /dedan/v1/feedback — submit clinician feedback to close the data-flywheel loop. */
export interface FeedbackSubmission {
  triage_data: Record<string, unknown>;
  doctor_feedback: Record<string, unknown>;
}

export async function submitFeedback(
  request: FeedbackSubmission,
): Promise<APIResult<{ success: boolean; message?: string }>> {
  return apiClient.request<{ success: boolean; message?: string }>(
    '/dedan/v1/feedback',
    { method: 'POST', body: JSON.stringify(request) },
    { timeoutMs: 15000 },
  );
}
