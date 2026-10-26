import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchHealth, isHealth } from "./health";

function respond(body: unknown, status = 200) {
  return vi.fn((_url: string, _init?: RequestInit) =>
    Promise.resolve(
      new Response(JSON.stringify(body), {
        status,
        headers: { "Content-Type": "application/json" },
      }),
    ),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("fetchHealth", () => {
  it("resolves a 200 body and calls the relative health URL", async () => {
    const fetchMock = respond({ status: "ok", db: "ok", redis: "ok" });
    vi.stubGlobal("fetch", fetchMock);
    await expect(fetchHealth()).resolves.toEqual({ status: "ok", db: "ok", redis: "ok" });
    expect(fetchMock.mock.calls[0]?.[0]).toBe("/api/v1/health");
  });

  it("resolves a 503 degraded body instead of throwing", async () => {
    vi.stubGlobal("fetch", respond({ status: "degraded", db: "ok", redis: "error" }, 503));
    await expect(fetchHealth()).resolves.toEqual({ status: "degraded", db: "ok", redis: "error" });
  });

  it("throws on other statuses", async () => {
    vi.stubGlobal("fetch", respond({ status: "ok", db: "ok", redis: "ok" }, 500));
    await expect(fetchHealth()).rejects.toThrow("Health check failed with status 500");
  });

  it("throws on an invalid body", async () => {
    vi.stubGlobal("fetch", respond({ status: "weird" }));
    await expect(fetchHealth()).rejects.toThrow("Unexpected health response");
  });

  it("throws on a network failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.reject(new TypeError("Failed to fetch"))),
    );
    await expect(fetchHealth()).rejects.toThrow();
  });
});

describe("isHealth", () => {
  it("accepts valid bodies", () => {
    expect(isHealth({ status: "ok", db: "ok", redis: "ok" })).toBe(true);
    expect(isHealth({ status: "degraded", db: "error", redis: "ok" })).toBe(true);
  });

  it("rejects null, arrays, missing keys and unknown values", () => {
    expect(isHealth(null)).toBe(false);
    expect(isHealth([])).toBe(false);
    expect(isHealth({ status: "ok", db: "ok" })).toBe(false);
    expect(isHealth({ status: "ok", db: "ok", redis: "maybe" })).toBe(false);
  });
});
