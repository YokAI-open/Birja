import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchPrices, isPrices } from "./prices";

afterEach(() => {
  vi.unstubAllGlobals();
});

const item = {
  symbol: "BTC",
  name: "Bitcoin",
  price: "81042.35000000",
  as_of: "2026-10-28T10:00:00Z",
  age_seconds: 12,
  status: "fresh",
};
const valid = {
  server_time: "2026-10-28T10:00:12Z",
  fresh_seconds: 90,
  stale_seconds: 300,
  items: [item],
};

describe("isPrices", () => {
  it("accepts the contract", () => {
    expect(isPrices(valid)).toBe(true);
    expect(isPrices({ ...valid, items: [] })).toBe(true);
  });

  it.each([
    ["null", null],
    ["array", []],
    ["missing items", { ...valid, items: undefined }],
    ["non-integer fresh_seconds", { ...valid, fresh_seconds: 1.5 }],
    ["missing server_time", { ...valid, server_time: "" }],
    ["non-object item", { ...valid, items: [null] }],
    ["scientific price", { ...valid, items: [{ ...item, price: "1e5" }] }],
    ["text price", { ...valid, items: [{ ...item, price: "abc" }] }],
    ["number price", { ...valid, items: [{ ...item, price: 1.5 }] }],
    ["bad status", { ...valid, items: [{ ...item, status: "old" }] }],
    ["fractional age", { ...valid, items: [{ ...item, age_seconds: 1.5 }] }],
    ["empty symbol", { ...valid, items: [{ ...item, symbol: "" }] }],
  ])("rejects %s", (_name, value) => {
    expect(isPrices(value)).toBe(false);
  });
});

describe("fetchPrices", () => {
  it("returns validated prices", async () => {
    const fetchMock = vi.fn(() => Promise.resolve(new Response(JSON.stringify(valid))));
    vi.stubGlobal("fetch", fetchMock);
    await expect(fetchPrices()).resolves.toEqual(valid);
    expect((fetchMock.mock.calls[0] as unknown[])[0]).toBe("/api/v1/prices");
  });

  it("throws on a bad shape", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(new Response(JSON.stringify({ items: 1 })))),
    );
    await expect(fetchPrices()).rejects.toThrow("Unexpected prices response");
  });
});
