/**
 * FUTURE — Risk Sentinel
 *
 * backend-v2/risk_sentinel.py defines RiskSentinel, but backend-v2 does not
 * import/run, and no /dedan/v1/risk route exists in the live backend.
 */
import { APIError } from '../../types';
export const riskService = {
  isLive: false as const,
  reason: 'Risk sentinel backend is not live in v1.',
  getRiskProfile(): Promise<APIError> {
    return Promise.resolve({ ok: false, status: 501, code: 'UNAVAILABLE',
      message: 'Risk profiling is not yet available.' });
  },
};
