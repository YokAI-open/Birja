import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch, readCookie } from "./client";

const json = (body: unknown, status = 200, headers: Record<string, string> = {}) =>
  new Response(JSON.stringify(body), { status, headers });

const EXPIRE = "=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";

beforeEach(() => {
  document.cookie = `yk_csrf${EXPIRE}`;
});
afterEach(() => {
  vi.unstubAllGlobals();
  document.cookie = `yk_csrf${EXPIRE}`;
});

function lastInit(mock: ReturnType<typeof vi.fn>, call = 0): RequestInit {
  return (mock.mock.calls[call] as unknown as [string, RequestInit])[1];
}

describe("readCookie", () => {
  it("reads a cookie by exact name", () => {
    document.cookie = "yk_csrf_other=nope; path=/";
    document.cookie = "yk_csrf=abc; path=/";
    expect(readCookie("yk_csrf")).toBe("abc");
    expect(readCookie("missing")).toBeNull();
    document.cookie = `yk_csrf_other${EXPIRE}`;
  });
});

describe("apiFetch", () => {
  it("sends no CSRF header on GET", async () => {
    const fetchMock = vi.fn(() => Promise.resolve(json({ ok: 1 })));
    vi.stubGlobal("fetch", fetchMock);
    expect(await apiFetch("/api/v1/x")).toEqual({ ok: 1 });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(new Headers(lastInit(fetchMock).headers).has("X-CSRF-Token")).toBe(false);
  });

  it("sends the CSRF cookie value on POST", async () => {
    document.cookie = "yk_csrf=tok123; path=/";
    const fetchMock = vi.fn(() => Promise.resolve(json({ status: "code_sent" }, 202)));
    vi.stubGlobal("fetch", fetchMock);
    await apiFetch("/api/v1/x", { method: "POST", body: "{}" });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const headers = new Headers(lastInit(fetchMock).headers);
    expect(headers.get("X-CSRF-Token")).toBe("tok123");
    expect(headers.get("Content-Type")).toBe("application/json");
  });

  it("fetches a CSRF token first when the cookie is missing", async () => {
    const fetchMock = vi.fn((url: string) => {
      if (url === "/api/v1/auth/csrf") {
        document.cookie = "yk_csrf=fresh; path=/";
        return Promise.resolve(new Response(null, { status: 204 }));
      }
      return Promise.resolve(json({}, 200));
    });
    vi.stubGlobal("fetch", fetchMock);
    await apiFetch("/api/v1/x", { method: "POST", body: "{}" });
    expect(fetchMock.mock.calls.map((c) => c[0])).toEqual(["/api/v1/auth/csrf", "/api/v1/x"]);
    expect(new Headers(lastInit(fetchMock, 1).headers).get("X-CSRF-Token")).toBe("fresh");
  });

  it("returns null for 204", async () => {
    vi.stubGlobal("fetch", () => Promise.resolve(new Response(null, { status: 204 })));
    expect(await apiFetch("/api/v1/x")).toBeNull();
  });

  it("throws ApiError with code, message and Retry-After", async () => {
    vi.stubGlobal("fetch", () =>
      Promise.resolve(
        json({ detail: { code: "rate_limited", message: "Slow down" } }, 429, {
          "Retry-After": "120",
        }),
      ),
    );
    const error = await apiFetch("/api/v1/x").catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 429,
      code: "rate_limited",
      message: "Slow down",
      retryAfter: 120,
    });
  });

  it("uses a null code for array details and absent Retry-After", async () => {
    vi.stubGlobal("fetch", () => Promise.resolve(json({ detail: [{ msg: "bad" }] }, 422)));
    const error = await apiFetch("/api/v1/x").catch((e: unknown) => e);
    expect(error).toMatchObject({ status: 422, code: null, retryAfter: null });
  });

  it("handles non-JSON error bodies and unparsable Retry-After", async () => {
    vi.stubGlobal("fetch", () =>
      Promise.resolve(new Response("<html>", { status: 503, headers: { "Retry-After": "soon" } })),
    );
    const error = await apiFetch("/api/v1/x").catch((e: unknown) => e);
    expect(error).toMatchObject({ status: 503, code: null, retryAfter: null });
  });
});

describe("apiFetch silent refresh", () => {
  const unauthorized = () => new Response("{}", { status: 401 });

  it("refreshes once on 401 and retries the original request", async () => {
    document.cookie = "yk_csrf=tok; path=/";
    let meCalls = 0;
    const fetchMock = vi.fn((url: string) => {
      if (url === "/api/v1/auth/refresh")
        return Promise.resolve(new Response(null, { status: 204 }));
      meCalls += 1;
      return Promise.resolve(meCalls === 1 ? unauthorized() : json({ ok: 1 }));
    });
    vi.stubGlobal("fetch", fetchMock);
    expect(await apiFetch("/api/v1/me")).toEqual({ ok: 1 });
    const urls = fetchMock.mock.calls.map((c) => (c as unknown as [string])[0]);
    expect(urls).toEqual(["/api/v1/me", "/api/v1/auth/refresh", "/api/v1/me"]);
    const refreshInit = (fetchMock.mock.calls[1] as unknown as [string, RequestInit])[1];
    expect(refreshInit.method).toBe("POST");
    expect(new Headers(refreshInit.headers).get("X-CSRF-Token")).toBe("tok");
  });

  it("shares one refresh between concurrent 401s and retries both", async () => {
    document.cookie = "yk_csrf=tok; path=/";
    let release: (r: Response) => void = () => {};
    const seen: Record<string, number> = {};
    const fetchMock = vi.fn((url: string) => {
      seen[url] = (seen[url] ?? 0) + 1;
      if (url === "/api/v1/auth/refresh") {
        return new Promise<Response>((resolve) => {
          release = resolve;
        });
      }
      return Promise.resolve(seen[url] === 1 ? unauthorized() : json({ url }));
    });
    vi.stubGlobal("fetch", fetchMock);
    const both = Promise.all([apiFetch("/api/v1/a"), apiFetch("/api/v1/b")]);
    await vi.waitFor(() => expect(seen["/api/v1/auth/refresh"]).toBe(1));
    await new Promise((r) => setTimeout(r, 0));
    release(new Response(null, { status: 204 }));
    expect(await both).toEqual([{ url: "/api/v1/a" }, { url: "/api/v1/b" }]);
    expect(seen["/api/v1/auth/refresh"]).toBe(1);
  });

  it("never refreshes for /api/v1/auth/ paths", async () => {
    document.cookie = "yk_csrf=tok; path=/";
    const fetchMock = vi.fn(() => Promise.resolve(unauthorized()));
    vi.stubGlobal("fetch", fetchMock);
    await expect(apiFetch("/api/v1/auth/refresh", { method: "POST" })).rejects.toMatchObject({
      status: 401,
    });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("throws 401 when the retry is still unauthorized, and survives a failed refresh", async () => {
    document.cookie = "yk_csrf=tok; path=/";
    const fetchMock = vi.fn((url: string) =>
      url === "/api/v1/auth/refresh"
        ? Promise.reject(new TypeError("network"))
        : Promise.resolve(unauthorized()),
    );
    vi.stubGlobal("fetch", fetchMock);
    await expect(apiFetch("/api/v1/me")).rejects.toMatchObject({ status: 401 });
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it("treats a non-204 refresh as failure but still retries once", async () => {
    document.cookie = "yk_csrf=tok; path=/";
    const fetchMock = vi.fn((url: string) =>
      Promise.resolve(url === "/api/v1/auth/refresh" ? unauthorized() : unauthorized()),
    );
    vi.stubGlobal("fetch", fetchMock);
    await expect(apiFetch("/api/v1/me")).rejects.toMatchObject({ status: 401 });
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });
});
