/**
 * FUTURE — Billing / Subscription
 *
 * BACKEND STATUS: NOT LIVE.
 *   backend-v2/billing_endpoints.py exposes an APIRouter for /billing/* but
 *   backend-v2/main_v2.py NEVER calls app.include_router(billing_endpoints)
 *   (grep `include_router` in main_v2.py -> none), so /billing/* returns 404
 *   against any running server. The /pricing path is therefore UNAVAILABLE.
 *
 * This module exists so the patient pricing UI can be architecture-complete
 * (Implementation Phase 3) WITHOUT faking success. All functions throw a
 * typed "service unavailable" error. The UI renders a deliberate
 * "Coming soon" state instead of fabricated payment confirmation.
 */

import { APIError, APIResult, SubscriptionInfo } from '../../types';

export const billingService = {
  isLive: false as const,
  reason: 'Billing backend routes are not mounted in the live v1 API.',

  getPricingTiers(): Promise<APIResult<never>> {
    return Promise.resolve(unavailable());
  },
  getCurrentSubscription(): Promise<APIResult<never>> {
    return Promise.resolve(unavailable());
  },
  startTrial(_tier: string): Promise<APIResult<never>> {
    return Promise.resolve(unavailable());
  },
  upgradeSubscription(_tier: string): Promise<APIResult<never>> {
    return Promise.resolve(unavailable());
  },
};

function unavailable(): APIResult<never> {
  const err: APIError = {
    ok: false,
    status: 501,
    code: 'UNAVAILABLE',
    message: 'Billing/subscriptions are not yet available. This feature is coming soon.',
  };
  return err;
}
