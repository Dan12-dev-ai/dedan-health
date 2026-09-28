/**
 * FUTURE — EHR / Clinician review workflow
 *
 * backend-v2/emr_connector.py exists but (a) does not import (broken) and
 * (b) references nonexistent model types. No live clinician API exists.
 */
import { APIError } from '../../types';
export const ehrService = {
  isLive: false as const,
  reason: 'EHR/clinician API is not live in v1.',
  listReviews(): Promise<APIError> {
    return Promise.resolve({ ok: false, status: 501, code: 'UNAVAILABLE',
      message: 'Clinician review is not yet available.' });
  },
};
