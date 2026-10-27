import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchMe, isMe, requestCode, verifyCode } from "./auth";

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
const me = { email: "a@example.com", cash_usd: "10000.00000000" };

afterEach(() => {
  vi.unstubAllGlobals();
  document.cookie = "yk_csrf=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
});

describe("isMe", () => {
  it("accepts only objects with string fields", () => {
    expect(isMe(me)).toBe(true);
    expect(isMe(null)).toBe(false);
    expect(isMe([])).toBe(false);
    expect(isMe({ email: "a", cash_usd: 1 })).toBe(false);
  });
});

describe("fetchMe", () => {
  it("returns Me on 200", async () => {
    vi.stubGlobal("fetch", () => Promise.resolve(json(me)));
    expect(await fetchMe()).toEqual(me);
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
    await expect(fetchMe()).rejects.toThrow("Unexpected account response");
  });
});

describe("requestCode and verifyCode", () => {
  it("posts the email with a CSRF token", async () => {
    document.cookie = "yk_csrf=t; path=/";
    const fetchMock = vi.fn(() => Promise.resolve(json({ status: "code_sent" }, 202)));
    vi.stubGlobal("fetch", fetchMock);
    await requestCode("a@example.com");
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("/api/v1/auth/request-code");
    expect(init.body).toBe(JSON.stringify({ email: "a@example.com" }));
  });

  it("verifyCode returns Me and rejects malformed bodies", async () => {
    document.cookie = "yk_csrf=t; path=/";
    vi.stubGlobal("fetch", () => Promise.resolve(json(me)));
    expect(await verifyCode("a@example.com", "123456")).toEqual(me);
    vi.stubGlobal("fetch", () => Promise.resolve(json({ nope: true })));
    await expect(verifyCode("a@example.com", "123456")).rejects.toThrow();
  });
});
