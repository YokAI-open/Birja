import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchMe, isMe, logout, requestCode, verifyCode } from "./auth";

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
const me = { email: "a@example.com" };

afterEach(() => {
  vi.unstubAllGlobals();
  document.cookie = "bj_csrf=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
});

describe("isMe", () => {
  it("accepts only email-only identity objects, never legacy or invented cash", () => {
    expect(isMe(me)).toBe(true);
    expect(isMe(null)).toBe(false);
    expect(isMe([])).toBe(false);
    expect(isMe({ email: "a", cash_usd: 1 })).toBe(false);
    expect(isMe({ email: "a", cash_usd: "10000.00" })).toBe(false);
    expect(isMe({ email: "a", portfolios: [] })).toBe(false);
    expect(isMe({ email: "" })).toBe(false);
    expect(isMe({ email: 1 })).toBe(false);
  });
});

describe("fetchMe", () => {
  it("returns Me on 200", async () => {
    const fetch = vi.fn(() => Promise.resolve(json(me)));
    vi.stubGlobal("fetch", fetch);
    expect(await fetchMe()).toEqual(me);
    expect(fetch).toHaveBeenCalledWith(
      "/api/v2/me",
      expect.objectContaining({ cache: "no-store" }),
    );
  });

  it("returns null on 401", async () => {
    vi.stubGlobal("fetch", () =>
      Promise.resolve(json({ detail: { code: "not_authenticated", message: "x" } }, 401)),
    );
    expect(await fetchMe()).toBeNull();
  });

  it("throws on 500", async () => {
    vi.stubGlobal("fetch", () => Promise.resolve(json({}, 500)));
    await expect(fetchMe()).rejects.toMatchObject({ status: 500 });
  });

  it("throws on a malformed body", async () => {
    vi.stubGlobal("fetch", () => Promise.resolve(json({ email: 1 })));
    await expect(fetchMe()).rejects.toThrow("Unexpected identity response");
  });
});

describe("requestCode and verifyCode", () => {
  it("posts the email with a CSRF token", async () => {
    document.cookie = "bj_csrf=t; path=/";
    const fetchMock = vi.fn(() => Promise.resolve(json({ status: "code_sent" }, 202)));
    vi.stubGlobal("fetch", fetchMock);
    await requestCode("a@example.com");
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("/api/v1/auth/request-code");
    expect(init.body).toBe(JSON.stringify({ email: "a@example.com" }));
  });

  it("verifyCode returns Me and rejects malformed bodies", async () => {
    document.cookie = "bj_csrf=t; path=/";
    vi.stubGlobal("fetch", () => Promise.resolve(json(me)));
    expect(await verifyCode("a@example.com", "123456")).toEqual(me);
    vi.stubGlobal("fetch", () => Promise.resolve(json({ nope: true })));
    await expect(verifyCode("a@example.com", "123456")).rejects.toThrow();
  });

  it("posts verification only to v2 with existing CSRF and cookie transport", async () => {
    document.cookie = "bj_csrf=t; path=/";
    const fetch = vi.fn(() => Promise.resolve(json(me)));
    vi.stubGlobal("fetch", fetch);
    await verifyCode(me.email, "123456");
    const [path, init] = fetch.mock.calls[0] as unknown as [string, RequestInit];
    expect(path).toBe("/api/v2/auth/verify-code");
    expect(init.body).toBe(JSON.stringify({ email: me.email, code: "123456" }));
    expect(new Headers(init.headers).get("X-CSRF-Token")).toBe("t");
    expect(init.cache).toBe("no-store");
    expect(init.credentials).not.toBe("omit");
  });

  it("does not refresh or repeat a rejected OTP verification", async () => {
    document.cookie = "bj_csrf=t; path=/";
    const fetch = vi.fn(() => Promise.resolve(json({ detail: { code: "invalid_code" } }, 401)));
    vi.stubGlobal("fetch", fetch);
    await expect(verifyCode(me.email, "123456")).rejects.toMatchObject({ status: 401 });
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(fetch).toHaveBeenCalledWith("/api/v2/auth/verify-code", expect.anything());
  });

  it("retains the v1 logout endpoint and CSRF", async () => {
    document.cookie = "bj_csrf=t; path=/";
    const fetch = vi.fn(() => Promise.resolve(new Response(null, { status: 204 })));
    vi.stubGlobal("fetch", fetch);
    await logout();
    expect(fetch).toHaveBeenCalledWith(
      "/api/v1/auth/logout",
      expect.objectContaining({ method: "POST" }),
    );
  });
});

it.each(["/api/v2/me", "/api/v2/auth/verify-code"])(
  "surfaces legacy api_version_required without trying old identity or funding at %s",
  async (path) => {
    document.cookie = "bj_csrf=t; path=/";
    const fetch = vi.fn(() =>
      Promise.resolve(json({ detail: { code: "api_version_required" } }, 409)),
    );
    vi.stubGlobal("fetch", fetch);
    await expect(
      path.endsWith("me") ? fetchMe() : verifyCode(me.email, "123456"),
    ).rejects.toMatchObject({
      status: 409,
      code: "api_version_required",
    });
    expect(fetch).toHaveBeenCalledTimes(1);
  },
);

it("refreshes expired identity through existing v1 lifecycle then retries v2 me", async () => {
  document.cookie = "bj_csrf=t; path=/";
  const fetch = vi
    .fn()
    .mockResolvedValueOnce(json({}, 401))
    .mockResolvedValueOnce(new Response(null, { status: 204 }))
    .mockResolvedValueOnce(json(me));
  vi.stubGlobal("fetch", fetch);
  expect(await fetchMe()).toEqual(me);
  expect(fetch.mock.calls.map(([path]) => path)).toEqual([
    "/api/v2/me",
    "/api/v1/auth/refresh",
    "/api/v2/me",
  ]);
});

it("forwards and honors identity abort signals", async () => {
  const controller = new AbortController();
  controller.abort();
  const fetch = vi.fn();
  vi.stubGlobal("fetch", fetch);
  await expect(fetchMe(controller.signal)).rejects.toThrow();
  expect(fetch).not.toHaveBeenCalled();
});
