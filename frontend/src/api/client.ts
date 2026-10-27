export class ApiError extends Error {
  status: number;
  code: string | null;
  retryAfter: number | null;

  constructor(status: number, code: string | null, message: string, retryAfter: number | null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.retryAfter = retryAfter;
  }
}

const CSRF_COOKIE = "bj_csrf";

export function readCookie(name: string): string | null {
  for (const part of document.cookie.split("; ")) {
    const index = part.indexOf("=");
    if (index > 0 && part.slice(0, index) === name) {
      return decodeURIComponent(part.slice(index + 1));
    }
  }
  return null;
}

async function ensureCsrfToken(): Promise<string | null> {
  const existing = readCookie(CSRF_COOKIE);
  if (existing) {
    return existing;
  }
  await fetch("/api/v1/auth/csrf", { headers: { Accept: "application/json" } });
  return readCookie(CSRF_COOKIE);
}

async function toApiError(response: Response): Promise<ApiError> {
  let code: string | null = null;
  let message = `Request failed with status ${response.status}`;
  try {
    const body: unknown = await response.json();
    if (typeof body === "object" && body !== null && "detail" in body) {
      const detail = (body as { detail: unknown }).detail;
      if (typeof detail === "object" && detail !== null && !Array.isArray(detail)) {
        const d = detail as { code?: unknown; message?: unknown };
        if (typeof d.code === "string") code = d.code;
        if (typeof d.message === "string") message = d.message;
      }
    }
  } catch {
    // Non-JSON body: keep the generic message.
  }
  const header = response.headers.get("Retry-After");
  const retryAfter = header !== null && /^\d+$/.test(header.trim()) ? Number(header.trim()) : null;
  return new ApiError(response.status, code, message, retryAfter);
}

let refreshInFlight: Promise<boolean> | null = null;

/** One refresh at a time: concurrent 401s share a single in-flight request. */
function refreshSession(): Promise<boolean> {
  if (refreshInFlight) {
    return refreshInFlight;
  }
  refreshInFlight = (async () => {
    try {
      const token = await ensureCsrfToken();
      const headers = new Headers({ Accept: "application/json" });
      if (token) {
        headers.set("X-CSRF-Token", token);
      }
      const response = await fetch("/api/v1/auth/refresh", { method: "POST", headers });
      return response.status === 204;
    } catch {
      return false;
    } finally {
      refreshInFlight = null;
    }
  })();
  return refreshInFlight;
}

async function send(path: string, init: RequestInit): Promise<Response> {
  const method = (init.method ?? "GET").toUpperCase();
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body !== undefined && init.body !== null) {
    headers.set("Content-Type", "application/json");
  }
  if (method !== "GET" && method !== "HEAD") {
    const token = await ensureCsrfToken();
    if (token) {
      headers.set("X-CSRF-Token", token);
    }
  }
  return fetch(path, { ...init, method, headers });
}

/** The only place that calls fetch for /api. Returns parsed JSON, or null for 204. */
export async function apiFetch(path: string, init: RequestInit = {}): Promise<unknown> {
  let response = await send(path, init);
  if (response.status === 401 && !path.startsWith("/api/v1/auth/")) {
    await refreshSession();
    response = await send(path, init);
  }
  if (!response.ok) {
    throw await toApiError(response);
  }
  if (response.status === 204) {
    return null;
  }
  return response.json();
}
