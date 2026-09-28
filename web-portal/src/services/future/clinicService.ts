/**
 * FUTURE — Clinic Finder
 *
 * BACKEND STATUS: NOT LIVE.
 *   The mobile ClinicFinderScreen calls /dedan/v1/clinics, but that route
 *   does not exist in backend/main.py (verified: only 8 v1 routes). The
 *   clinic-directory backend is absent, so this is UNAVAILABLE.
 */
import { APIError, APIResult, Clinic } from '../../types';
export const clinicService = {
  isLive: false as const,
  reason: 'Clinic directory backend route /dedan/v1/clinics does not exist in the live v1 API.',
  searchNearby(_lat: number, _lng: number): Promise<APIResult<Clinic[]>> {
    return Promise.resolve(unavailable());
  },
  getClinic(_id: string): Promise<APIResult<Clinic>> {
    return Promise.resolve(unavailable());
  },
};
function unavailable(): APIError {
  return { ok: false, status: 501, code: 'UNAVAILABLE',
    message: 'Clinic directory is not yet available.' };
}
