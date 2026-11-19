export class ApiError extends Error {
  status: number;
  code: string | null;
  retryAfter: number | null;
  /** The parsed `detail` object of the error body (e.g. detail.quote on price_changed), else null. */
  detail: Record<string, unknown> | null;

  constructor(
    status: number,
    code: string | null,
    message: string,
    retryAfter: number | null,
    detail: Record<string, unknown> | null = null,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.retryAfter = retryAfter;
    this.detail = detail;
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

async function ensureCsrfToken(
  check: () => void = () => {},
  signal?: AbortSignal,
): Promise<string | null> {
  check();
  const existing = readCookie(CSRF_COOKIE);
  if (existing) {
    return existing;
  }
  await fetch("/api/v1/auth/csrf", { headers: { Accept: "application/json" }, signal });
  check();
  return readCookie(CSRF_COOKIE);
}

async function toApiError(response: Response): Promise<ApiError> {
  let code: string | null = null;
  let detailObject: Record<string, unknown> | null = null;
  let message = `Request failed with status ${response.status}`;
  try {
    const body: unknown = await response.json();
    if (typeof body === "object" && body !== null && "detail" in body) {
      const detail = (body as { detail: unknown }).detail;
      if (typeof detail === "object" && detail !== null && !Array.isArray(detail)) {
        detailObject = detail as Record<string, unknown>;
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
  return new ApiError(response.status, code, message, retryAfter, detailObject);
}

let refreshInFlight: Promise<boolean> | null = null;

/** One refresh at a time: concurrent 401s share a single in-flight request. */
function refreshSession(check: () => void = () => {}): Promise<boolean> {
  if (refreshInFlight) {
    return refreshInFlight;
  }
  refreshInFlight = (async () => {
    try {
      const token = await ensureCsrfToken(check);
      check();
      const headers = new Headers({ Accept: "application/json" });
      if (token) {
        headers.set("X-CSRF-Token", token);
      }
      const response = await fetch("/api/v1/auth/refresh", { method: "POST", headers });
      check();
      return response.status === 204;
    } catch {
      return false;
    } finally {
      refreshInFlight = null;
    }
  })();
  return refreshInFlight;
}

async function send(
  path: string,
  init: RequestInit,
  check: () => void = () => {},
): Promise<Response> {
  check();
  init.signal?.throwIfAborted();
  const method = (init.method ?? "GET").toUpperCase();
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body !== undefined && init.body !== null) {
    headers.set("Content-Type", "application/json");
  }
  if (method !== "GET" && method !== "HEAD") {
    const token = await ensureCsrfToken(check, init.signal ?? undefined);
    check();
    if (token) {
      headers.set("X-CSRF-Token", token);
    }
  }
  init.signal?.throwIfAborted();
  check();
  return fetch(path, { ...init, method, headers });
}

/** Opt-in strict transport for immutable originals. Existing apiFetch callers keep their contract. */
export async function guardedJsonRequest(
  path: string,
  init: RequestInit,
  isCurrent: () => boolean,
): Promise<unknown> {
  const check = () => {
    init.signal?.throwIfAborted();
    if (!isCurrent()) throw new DOMException("Request context unavailable", "AbortError");
  };
  const json = async (response: Response): Promise<unknown> => {
    check();
    if (
      response.headers.get("Content-Type")?.split(";", 1)[0].trim().toLowerCase() !==
      "application/json"
    )
      throw new Error("Unexpected response");
    const value: unknown = await response.json();
    check();
    return value;
  };
  check();
  // All request bytes/target must already have been captured by the caller.
  let response = await send(path, init, check);
  check();
  if (response.status === 401) {
    // A well-formed authentication refusal may recover once, never a transport/5xx failure.
    const value = await json(response);
    check();
    const refused = strictError(response, value);
    if (refused.code !== "not_authenticated") throw refused;
    const refreshed = await refreshSession(check);
    check();
    if (refreshed) {
      response = await send(path, init, check);
      check();
    } else {
      throw strictError(response, value);
    }
  }
  const value = await json(response);
  check();
  if (!response.ok) throw strictError(response, value);
  if (response.status !== 200) throw new Error("Unexpected response");
  return value;
}

function strictError(response: Response, value: unknown): ApiError {
  const record = (v: unknown): v is Record<string, unknown> =>
    typeof v === "object" && v !== null && !Array.isArray(v);
  if (!record(value) || Object.keys(value).join() !== "detail" || !record(value.detail))
    throw new Error("Unexpected response");
  const detail = value.detail;
  if (
    typeof detail.code !== "string" ||
    !Object.keys(detail).every(
      (key) =>
        key === "code" ||
        ((response.status === 401 || response.status === 403) &&
          key === "message" &&
          typeof detail.message === "string"),
    )
  )
    throw new Error("Unexpected response");
  const header = response.headers.get("Retry-After");
  const wait = header !== null && /^\d+$/.test(header.trim()) ? Number(header.trim()) : null;
  return new ApiError(
    response.status,
    detail.code,
    "Request refused",
    wait !== null && Number.isSafeInteger(wait) ? wait : null,
  );
}

/** The only place that calls fetch for /api. Returns parsed JSON, or null for 204. */
export async function apiFetch(path: string, init: RequestInit = {}): Promise<unknown> {
  let response = await send(path, init);
  init.signal?.throwIfAborted();
  if (
    response.status === 401 &&
    !path.startsWith("/api/v1/auth/") &&
    !path.startsWith("/api/v2/auth/")
  ) {
    await refreshSession();
    init.signal?.throwIfAborted();
    response = await send(path, init);
    init.signal?.throwIfAborted();
  }
  if (!response.ok) {
    const error = await toApiError(response);
    init.signal?.throwIfAborted();
    throw error;
  }
  if (response.status === 204) {
    return null;
  }
  const body: unknown = await response.json();
  init.signal?.throwIfAborted();
  return body;
}
