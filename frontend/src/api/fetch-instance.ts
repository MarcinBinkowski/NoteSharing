import { toast } from "sonner";
import { ApiError } from "@/lib/error";

export interface FetchConfig {
  url: string;
  method: string;
  headers?: Record<string, string>;
  data?: unknown;
  params?: Record<string, string | number | boolean | null | undefined>;
  signal?: AbortSignal;
}

let refreshPromise: Promise<boolean> | null = null;
let hasNotifiedSessionExpired = false;

// /api/auth/me returns 401 for unauthenticated users — no refresh, no toast.
// Session-expired toast will fire on the next authenticated action instead.
const AUTH_ROUTES_WITHOUT_REFRESH = ["/api/auth/refresh", "/api/auth/logout", "/api/auth/me"];

function isAuthRouteWithoutRefresh(url: string): boolean {
  return AUTH_ROUTES_WITHOUT_REFRESH.some((route) => url.startsWith(route));
}

function notifySessionExpiredOnce(): void {
  if (hasNotifiedSessionExpired) {
    return;
  }
  hasNotifiedSessionExpired = true;
  toast.error("Your session has expired. Please sign in again.");
}

export async function tryRefreshToken(): Promise<boolean> {
  try {
    const response = await fetch("/api/auth/refresh", {
      method: "POST",
      credentials: "include",
    });
    return response.ok;
  } catch {
    return false;
  }
}

function getRefreshPromise(): Promise<boolean> {
  if (refreshPromise === null) {
    refreshPromise = tryRefreshToken().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

function buildRequest(config: FetchConfig): { fullUrl: string; init: RequestInit } {
  const { url, method, headers, data, params, signal } = config;
  const requestHeaders: Record<string, string> = {
    ...headers,
  };

  if (data !== undefined) {
    requestHeaders["Content-Type"] = "application/json";
  }

  let fullUrl = url;
  if (params) {
    const searchParams = new URLSearchParams(
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== null)
        .map(([k, v]) => [k, String(v)])
    );
    const qs = searchParams.toString();
    if (qs) {
      fullUrl += `?${qs}`;
    }
  }

  return {
    fullUrl,
    init: {
      method,
      headers: requestHeaders,
      body: data !== undefined ? JSON.stringify(data) : undefined,
      signal,
      credentials: "include",
    },
  };
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type")?.toLowerCase() ?? "";
  const text = await response.text();
  if (!text) {
    return undefined as T;
  }

  if (contentType.includes("application/json")) {
    return JSON.parse(text) as T;
  }

  return text as T;
}

async function throwResponseError(response: Response): Promise<never> {
  let detail: string | undefined;
  try {
    const body = (await response.json()) as { detail?: string };
    detail = body.detail;
  } catch {
    detail = undefined;
  }
  throw new ApiError(response.status, detail);
}

export const customFetch = async <T>(config: FetchConfig): Promise<T> => {
  const { fullUrl, init } = buildRequest(config);
  const response = await fetch(fullUrl, init);
  const shouldAttemptRefresh = !isAuthRouteWithoutRefresh(fullUrl);

  if (response.status === 401 && shouldAttemptRefresh) {
    const refreshed = await getRefreshPromise();
    if (refreshed) {
      hasNotifiedSessionExpired = false;
      const { fullUrl: retryUrl, init: retryInit } = buildRequest(config);
      const retryResponse = await fetch(retryUrl, retryInit);
      if (!retryResponse.ok) {
        return throwResponseError(retryResponse);
      }
      return parseResponse<T>(retryResponse);
    }
    notifySessionExpiredOnce();
  }

  if (!response.ok) {
    return throwResponseError(response);
  }

  return parseResponse<T>(response);
};
