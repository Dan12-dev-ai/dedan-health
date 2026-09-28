/**
 * DEDAN-Health — Typed API Client
 *
 * A small, dependency-light `fetch` wrapper (the existing axios client is
 * retained elsewhere for legacy; this is the canonical typed surface).
 *
 * CONTRACT:
 *  - Every method returns `APIResult<T>` (ok | error) — NO silent fake success.
 *  - Base URL comes from `REACT_APP_API_URL` (default http://localhost:8000).
 *  - Network loss is surfaced as a typed error, never a fabricated 200.
 *  - The ONLY routes wired here are the live v1 routes in backend/main.py:
 *      GET  /  | GET /health | POST /dedan/v1/triage
 *      GET  /dedan/v1/conditions | GET /dedan/v1/session/{id}
 *      POST /dedan/v1/session/{id}/consent | GET /dedan/v1/emergency-contacts
 *      GET  /dedan/v1/stats
 *    Any other route is UNAVAILABLE (see services/future/*).
 *
 * Offline policy: GETs may return a typed offline error; writes that fail due
 * to network are surfaced so the caller can queue them (see offlineStorage).
 */

/**
 * Runtime configuration for the browser build.
 *
 * `import.meta.env` is Vite-specific and cannot be compiled to CommonJS by
 * Babel, which breaks Jest (jsdom runs on CommonJS). Isolating the access
 * here — and mapping this module to a stub under Jest (see jest.config.cjs
 * `moduleNameMapper`) — keeps application code free of `import.meta` and lets
 * the same modules load under both the bundler and the test runner.
 */

import { APIError, APIResult } from '../types';

interface ImportMetaEnv {
  readonly VITE_API_URL?: string;
}

/**
 * Base URL of the DEDAN Health API.
 *
 * Set at build/dev time via `VITE_API_URL` (see `.env.example`).
 * Falls back to the documented local default when unset.
 */
function readEnv(): ImportMetaEnv {
  // `typeof` guard keeps this safe if the module is evaluated outside a
  // bundler context where `import.meta` is unavailable.
  if (typeof import.meta === 'undefined') {
    return {};
  }
  return (import.meta as unknown as { env?: ImportMetaEnv }).env ?? {};
}

export const ENV = readEnv();

/** Default when the operator has not configured `VITE_API_URL`. */
export const DEFAULT_API_BASE_URL = 'http://localhost:8000';

export const API_BASE_URL = (ENV.VITE_API_URL || DEFAULT_API_BASE_URL).replace(/\/+$/, '');

export class DedanAPIError extends Error {
  public readonly status: number;
  public readonly code: string;
  public readonly correlation_id?: string;
  constructor(status: number, code: string, message: string, correlation_id?: string) {
    super(message);
    this.name = 'DedanAPIError';
    this.status = status;
    this.code = code;
    this.correlation_id = correlation_id;
  }
}

export interface RequestOptions {
  /** Milliseconds. Default 30000 (triage is a server-side LLM call). */
  timeoutMs?: number;
  /** When true, network failure resolves to an offline error instead of throwing. */
  allowOffline?: boolean;
}

function isOfflineError(err: unknown): boolean {
  return (
    typeof navigator !== 'undefined' && !navigator.onLine
  ) || (err instanceof TypeError) || (err instanceof DedanAPIError && err.code === 'OFFLINE');
}

function toAPIError(err: unknown): APIError {
  if (err instanceof DedanAPIError) {
    return { ok: false, status: err.status, code: err.code, message: err.message, correlation_id: err.correlation_id };
  }
  if (typeof navigator !== 'undefined' && !navigator.onLine) {
    return { ok: false, status: 0, code: 'OFFLINE', message: 'You are offline. This action will be saved and sent when you reconnect.' };
  }
  if (err instanceof TypeError) {
    return { ok: false, status: 0, code: 'NETWORK_ERROR', message: 'Network error. Check your connection and try again.' };
  }
  const message = err instanceof Error ? err.message : 'Unexpected error';
  return { ok: false, status: 0, code: 'UNKNOWN', message };
}

export class DedanAPIClient {
  private baseURL: string;
  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  async request<T>(path: string, init: RequestInit = {}, opts: RequestOptions = {}): Promise<APIResult<T>> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), opts.timeoutMs ?? 30000);
    const url = `${this.baseURL}${path}`;
    try {
      const resp = await fetch(url, {
        credentials: 'omit', // no cookies/PHI via cookies in this architecture
        headers: { 'Content-Type': 'application/json', ...(init.headers ?? {}) },
        ...init,
        signal: controller.signal,
      });
      clearTimeout(timeout);

      if (!resp.ok) {
        let body: any = undefined;
        try {
          body = await resp.json();
        } catch {
          /* non-JSON error body */
        }
        const code = body?.code ?? `HTTP_${resp.status}`;
        const message = body?.detail ?? `Request failed with status ${resp.status}`;
        const err = new DedanAPIError(resp.status, code, message, body?.correlation_id);
        return toAPIError(err);
      }

      const text = await resp.text();
      if (text.length === 0) return { ok: true, data: undefined as unknown as T };
      try {
        const data: T = JSON.parse(text);
        return { ok: true, data };
      } catch {
        const err = new DedanAPIError(0, 'INVALID_JSON', 'Server returned an unparseable response.');
        return toAPIError(err);
      }
    } catch (err) {
      clearTimeout(timeout);
      if (isOfflineError(err)) return toAPIError(err);
      return toAPIError(err);
    }
  }
}

export const apiClient = new DedanAPIClient();

/** Tiny helper used across the app for connectivity state. */
export function isOnline(): boolean {
  return typeof navigator !== 'undefined' ? navigator.onLine : true;
}
