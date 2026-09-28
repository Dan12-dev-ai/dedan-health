/**
 * Jest stub for `src/services/apiClient.ts`.
 *
 * Babel cannot compile `import.meta` to CommonJS, so under Jest the real
 * module is swapped for this fixture (see `moduleNameMapper` in
 * `jest.config.cjs`). The stub mirrors the real module's public surface:
 * an `API_BASE_URL` driven by `JEST_API_BASE_URL`, plus `DedanAPIClient`
 * and the typed error handling, so tests exercise real code paths.
 */

import { APIError, APIResult } from '../types';

export const ENV: { readonly VITE_API_URL?: string } = {
  VITE_API_URL: process.env.JEST_API_BASE_URL,
};

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
  timeoutMs?: number;
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
        credentials: 'omit',
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

export function isOnline(): boolean {
  return typeof navigator !== 'undefined' ? navigator.onLine : true;
}

