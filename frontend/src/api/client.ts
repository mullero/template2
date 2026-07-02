/**
 * Single typed Axios wrapper (exported singleton).
 *
 * - Request interceptor: prefer an async tokenProvider (Firebase getIdToken, so
 *   auto-refresh applies), fall back to an in-memory token; respect a pre-set
 *   Authorization header so retries are not clobbered.
 * - Response interceptor: on 401, do ONE forced token refresh + retry once;
 *   if still 401, call onUnauthorized() to sign out.
 */
import axios, {
  type AxiosInstance,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from 'axios';

import { config } from '@/config';

type TokenProvider = (forceRefresh?: boolean) => Promise<string | null>;

interface RetryableConfig extends InternalAxiosRequestConfig {
  _retried?: boolean;
}

let inMemoryToken: string | null = null;
let tokenProvider: TokenProvider | null = null;
let onUnauthorized: (() => void) | null = null;

export function setAuthToken(token: string | null): void {
  inMemoryToken = token;
}

export function setTokenProvider(provider: TokenProvider | null): void {
  tokenProvider = provider;
}

export function setOnUnauthorized(handler: (() => void) | null): void {
  onUnauthorized = handler;
}

async function resolveToken(forceRefresh = false): Promise<string | null> {
  if (tokenProvider) {
    return tokenProvider(forceRefresh);
  }
  return inMemoryToken;
}

export const apiClient: AxiosInstance = axios.create({
  baseURL: config.apiUrl,
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.request.use(async (request: InternalAxiosRequestConfig) => {
  // Respect a pre-set Authorization header (e.g. an in-flight retry).
  if (!request.headers.Authorization) {
    const token = await resolveToken(false);
    if (token) {
      request.headers.Authorization = `Bearer ${token}`;
    }
  }
  return request;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: unknown) => {
    if (!axios.isAxiosError(error) || !error.response || !error.config) {
      return Promise.reject(error instanceof Error ? error : new Error(String(error)));
    }

    const original = error.config as RetryableConfig;

    if (error.response.status === 401 && !original._retried) {
      original._retried = true;
      const refreshed = await resolveToken(true);
      if (refreshed) {
        original.headers.Authorization = `Bearer ${refreshed}`;
        return apiClient.request(original);
      }
      onUnauthorized?.();
    } else if (error.response.status === 401) {
      onUnauthorized?.();
    }

    return Promise.reject(error);
  },
);

/** Typed GET helper. */
export async function apiGet<T>(url: string, cfg?: AxiosRequestConfig): Promise<T> {
  const response = await apiClient.get<T>(url, cfg);
  return response.data;
}

/** Typed POST helper. */
export async function apiPost<T, B = unknown>(
  url: string,
  body?: B,
  cfg?: AxiosRequestConfig,
): Promise<T> {
  const response = await apiClient.post<T>(url, body, cfg);
  return response.data;
}

/** Typed PATCH helper. */
export async function apiPatch<T, B = unknown>(
  url: string,
  body?: B,
  cfg?: AxiosRequestConfig,
): Promise<T> {
  const response = await apiClient.patch<T>(url, body, cfg);
  return response.data;
}

/** Typed DELETE helper. */
export async function apiDelete(url: string, cfg?: AxiosRequestConfig): Promise<void> {
  await apiClient.delete(url, cfg);
}
