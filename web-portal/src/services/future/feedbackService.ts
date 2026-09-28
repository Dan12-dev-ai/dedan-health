/**
 * FUTURE — Clinician Feedback (data flywheel)
 *
 * BACKEND STATUS: NOT LIVE (publicly).
 *   backend/data_flywheel.py defines collect_feedback (async, L99) but it is
 *   NOT exposed as a route in backend/main.py (only a module-level function,
 *   L489 — no @app decorator). The public /feedback endpoint exists only in
 *   the non-importing backend-v2. Until a route ships, this is UNAVAILABLE.
 */
import { APIError } from '../../types';
export const feedbackService = {
  isLive: false as const,
  reason: 'No public /feedback route exists in the live v1 backend.',
  submitFeedback(): Promise<APIError> {
    return Promise.resolve({ ok: false, status: 501, code: 'UNAVAILABLE',
      message: 'Doctor feedback submission is not yet available.' });
  },
};
