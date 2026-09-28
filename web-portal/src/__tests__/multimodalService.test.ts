/**
 * DEDAN-Health — Multimodal Service Tests
 *
 * Tests the typed API client surface without requiring a live backend.
 * Uses MSW (Mock Service Worker) pattern via fetch interception.
 */

import { APIResult } from '../types';
import {
  uploadImage,
  submitMultimodalAnalysis,
  postClinicalGuidance,
  getEvidence,
  getMedicationSafety,
  getVisualEducation,
  getUrgencyCheck,
  multimodalHealthCheck,
  validateImageFile,
  fileToBase64,
} from '../services/multimodalService';

/**
 * `APIResult<T>` is a discriminated union (`{ok:true,data}` | `APIError`), so
 * reading `.data` requires narrowing on `.ok` first. This helper asserts the
 * success branch and returns the narrowed payload, keeping the tests readable
 * and type-safe without scattering casts.
 */
function expectOk<T>(result: APIResult<T>): T {
  if (!result.ok) {
    throw new Error(
      `Expected an OK result, received error ${result.code}: ${result.message}`
    );
  }
  return result.data;
}

// Simple fetch mock helper.
// The client reads the body via `resp.text()` (see `DedanAPIClient.request`),
// so the mock must expose `text()`; `json()` is kept for parity with the
// error branch and for assertions that inspect the parsed body.
const mockFetch = (response: any, ok = true, status = 200) => {
  const body = response === null || response === undefined ? '' : JSON.stringify(response);
  global.fetch = jest.fn().mockResolvedValue({
    ok,
    status,
    text: () => Promise.resolve(body),
    json: () => Promise.resolve(response),
    headers: new Headers({ 'content-type': 'application/json' }),
  });
};

describe('multimodalService', () => {
  beforeEach(() => {
    jest.resetAllMocks();
    // Reset any modules that cache the apiClient
    jest.resetModules();
  });

  describe('validateImageFile', () => {
    it('accepts valid JPEG under 5MB', () => {
      const file = new File(['x'.repeat(1024 * 1024)], 'test.jpg', { type: 'image/jpeg' });
      const result = validateImageFile(file);
      expect(result.valid).toBe(true);
    });

    it('rejects unsupported file type', () => {
      const file = new File(['x'], 'test.pdf', { type: 'application/pdf' });
      const result = validateImageFile(file);
      expect(result.valid).toBe(false);
      expect(result.error).toContain('Unsupported file type');
    });

    it('rejects files over 20MB', () => {
      const file = new File(['x'.repeat(21 * 1024 * 1024)], 'test.jpg', { type: 'image/jpeg' });
      const result = validateImageFile(file);
      expect(result.valid).toBe(false);
      expect(result.error).toContain('too large');
    });

    it('warns for files over 5MB', () => {
      const file = new File(['x'.repeat(10 * 1024 * 1024)], 'test.jpg', { type: 'image/jpeg' });
      const result = validateImageFile(file);
      expect(result.valid).toBe(true);
      expect(result.warning).toContain('Large file');
    });
  });

  describe('fileToBase64', () => {
    it('converts file to raw base64 (data URL prefix stripped)', async () => {
      const file = new File(['hello'], 'test.txt', { type: 'text/plain' });
      const result = await fileToBase64(file);
      // The backend (`/api/analyze` -> `image_data_list`, and
      // `/api/images/upload-base64`) expects raw base64, not a data URL.
      expect(result).not.toMatch(/^data:/);
      expect(result).toBe(btoa('hello'));
    });
  });

  describe('multimodalHealthCheck', () => {
    it('returns healthy status on success', async () => {
      mockFetch({ status: 'healthy', providers: { gemini: true, openai: false } });
      const { multimodalHealthCheck } = await import('../services/multimodalService');
      const result = await multimodalHealthCheck();
      expect(result.ok).toBe(true);
      expect(expectOk(result).status).toBe('healthy');
    });

    it('returns error on failure', async () => {
      mockFetch(null, false, 500);
      const { multimodalHealthCheck } = await import('../services/multimodalService');
      const result = await multimodalHealthCheck();
      expect(result.ok).toBe(false);
    });
  });

  describe('uploadImage', () => {
    it('uploads file and returns metadata', async () => {
      mockFetch({
        image_id: 'img_123',
        filename: 'test.jpg',
        size: 1024,
        mime_type: 'image/jpeg',
        quality_score: 0.9,
        is_usable: true,
        upload_timestamp: '2024-01-01T00:00:00Z',
      });
      const { uploadImage } = await import('../services/multimodalService');
      const file = new File(['x'], 'test.jpg', { type: 'image/jpeg' });
      const result = await uploadImage(file, 'session_1');
      expect(result.ok).toBe(true);
      expect(expectOk(result).image_id).toBe('img_123');
    });
  });

  describe('submitMultimodalAnalysis', () => {
    it('submits analysis and returns structured response', async () => {
      mockFetch({
        request_id: 'req_123',
        session_id: 'session_1',
        urgency: 'routine',
        recommended_next_step: 'Schedule appointment',
        image_assessment: null,
        medical_information: [],
        treatment_information: [],
        warning_signs: ['Monitor symptoms'],
        follow_up_questions: ['How long?'],
        sources: [],
        uncertainty: '',
        requires_professional_review: false,
        safety_notice: '',
        confidence_score: 0.8,
        processing_time_ms: 100,
        provider: 'offline',
        model: 'dedan-rules-v1',
      });
      const { submitMultimodalAnalysis } = await import('../services/multimodalService');
      const result = await submitMultimodalAnalysis({
        text: 'Headache for 2 days',
        // `PatientProfile` mirrors the backend contract: `pregnancy_status`
        // (not `pregnant`), and no free-form `medications`/`allergies` list.
        patient: {
          age: 30,
          sex: 'female',
          language: 'en',
          location: 'Kenya',
          pregnancy_status: false,
          chronic_conditions: [],
        },
        image_ids: [],
        image_data_list: [],
        conversation_history: [],
        consent: true,
      });
      expect(result.ok).toBe(true);
      expect(expectOk(result).urgency).toBe('routine');
    });
  });

  describe('postClinicalGuidance', () => {
    it('posts clinical guidance request', async () => {
      mockFetch({
        response_id: 'resp_123',
        session_id: 'session_1',
        timestamp: '2024-01-01T00:00:00Z',
        // `ClinicalGuidanceResponse2` is a flat document; `safety.urgency`
        // carries the triage urgency, so the fixture mirrors that shape.
        safety: { urgency: 'routine', requires_immediate_care: false },
        professional_review: false,
      });
      const { postClinicalGuidance } = await import('../services/multimodalService');
      const result = await postClinicalGuidance({
        patient: {
          age: 30,
          sex: 'female',
          language: 'en',
          location: 'Kenya',
          pregnancy_status: false,
          chronic_conditions: [],
        },
        symptoms: {
          symptoms: 'Fever and chills',
          duration: '2 days',
          // `SymptomSeverity` is a string union, not a numeric 1-10 scale.
          severity: 'moderate',
        },
        image_ids: [],
        image_data_list: [],
        consent: true,
      });
      expect(result.ok).toBe(true);
      // `ClinicalGuidanceResponse2` is a flat clinical document: urgency is
      // carried on `safety`, not as a top-level field.
      expect(expectOk(result).safety.urgency).toBe('routine');
    });
  });

  describe('getEvidence', () => {
    it('retrieves evidence for topic', async () => {
      mockFetch({ topic: 'malaria', sources: [] });
      const { getEvidence } = await import('../services/multimodalService');
      const result = await getEvidence('malaria');
      expect(result.ok).toBe(true);
    });
  });

  describe('getMedicationSafety', () => {
    it('retrieves medication info', async () => {
      mockFetch({ medication: 'Artemether', info: '...' });
      const { getMedicationSafety } = await import('../services/multimodalService');
      const result = await getMedicationSafety('Artemether');
      expect(result.ok).toBe(true);
    });
  });

  describe('getVisualEducation', () => {
    it('retrieves visual education', async () => {
      mockFetch({ topic: 'malaria', visuals: [], count: 0 });
      const { getVisualEducation } = await import('../services/multimodalService');
      const result = await getVisualEducation('malaria');
      expect(result.ok).toBe(true);
    });
  });

  describe('getUrgencyCheck', () => {
    it('checks urgency for symptoms', async () => {
      mockFetch({ urgency: 'routine', requires_immediate_care: false, red_flags: [] });
      const { getUrgencyCheck } = await import('../services/multimodalService');
      const result = await getUrgencyCheck('headache');
      expect(result.ok).toBe(true);
      expect(expectOk(result).urgency).toBe('routine');
    });
  });
});
