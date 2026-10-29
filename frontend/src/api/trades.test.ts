import { afterEach, describe, expect, it, vi } from "vitest";
import {
  executeTrade,
  fetchHolding,
  fetchQuote,
  isFill,
  isHolding,
  isQuote,
  type Fill,
  type Quote,
} from "./trades";

const quote: Quote = {
  symbol: "BTC",
  side: "buy",
  input_kind: "usd",
  input_value: "100.00",
  mid: "100000.00",
  as_of: "2026-10-28T10:00:00Z",
  age_seconds: 5,
  exec_price: "100500.00",
  quantity: "0.00099501",
  notional: "99.99",
  fee: "0.01",
  cash_delta: "-100.00",
  cash_before: "10000.00",
  cash_after: "9900.00",
  held_before: "0",
  held_after: "0.00099501",
  whole_position: false,
};

const fill: Fill = {
  trade_id: 7,
  created_at: "2026-10-28T10:00:01Z",
  symbol: "BTC",
  side: "buy",
  input_kind: "usd",
  input_value: "100.00",
  mid: "100000.00",
  as_of: "2026-10-28T10:00:00Z",
  exec_price: "100500.00",
  quantity: "0.00099501",
  notional: "99.99",
  fee: "0.01",
  cash_delta: "-100.00",
  cash_after: "9900.00",
};

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });

function call(mock: ReturnType<typeof vi.fn>, n: number): [string, RequestInit] {
  return mock.mock.calls[n] as unknown as [string, RequestInit];
}

afterEach(() => {
  vi.unstubAllGlobals();
  document.cookie = "bj_csrf=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
});

describe("guards", () => {
  it("accepts a valid quote including zero and negative cash_delta", () => {
    expect(isQuote(quote)).toBe(true);
    expect(isQuote({ ...quote, cash_delta: "0.00" })).toBe(true);
    expect(isQuote({ ...quote, cash_delta: "-100.00" })).toBe(true);
  });

  it("rejects bad quotes", () => {
    expect(isQuote(null)).toBe(false);
    expect(isQuote([])).toBe(false);
    expect(isQuote({ ...quote, fee: 0.01 })).toBe(false);
    expect(isQuote({ ...quote, quantity: "1E-8" })).toBe(false);
    expect(isQuote({ ...quote, whole_position: "no" })).toBe(false);
    expect(isQuote({ ...quote, side: "hold" })).toBe(false);
    const missing: Partial<Quote> = { ...quote };
    delete missing.mid;
    expect(isQuote(missing)).toBe(false);
  });

  it("guards fills and holdings", () => {
    expect(isFill(fill)).toBe(true);
    expect(isFill({ ...fill, trade_id: "7" })).toBe(false);
    expect(isFill({ ...fill, cash_after: "-1" })).toBe(false);
    expect(isFill("x")).toBe(false);
    expect(isHolding({ symbol: "BTC", quantity: "0.5" })).toBe(true);
    expect(isHolding({ symbol: "BTC", quantity: 0.5 })).toBe(false);
    expect(isHolding(null)).toBe(false);
  });
});

describe("fetchQuote", () => {
  it("POSTs the order with the CSRF header and returns the quote", async () => {
    document.cookie = "bj_csrf=tok; path=/";
    const mock = vi.fn(() => Promise.resolve(json(quote)));
    vi.stubGlobal("fetch", mock);
    const order = { symbol: "BTC", side: "buy" as const, amount_usd: "100" };
    expect(await fetchQuote(order)).toEqual(quote);
    const [url, init] = call(mock, 0);
    expect(url).toBe("/api/v1/trades/quote");
    expect(init.method).toBe("POST");
    expect(new Headers(init.headers).get("X-CSRF-Token")).toBe("tok");
    expect(JSON.parse(init.body as string)).toEqual(order);
  });

  it("throws on a malformed quote", async () => {
    document.cookie = "bj_csrf=tok; path=/";
    vi.stubGlobal("fetch", () => Promise.resolve(json({ ...quote, fee: "1E-8" })));
    await expect(fetchQuote({ symbol: "BTC", side: "buy", amount_usd: "1" })).rejects.toThrow(
      "Unexpected quote response",
    );
  });
});

describe("executeTrade", () => {
  it("POSTs order, expected_mid and key; accepts 201 and 200", async () => {
    document.cookie = "bj_csrf=tok; path=/";
    const mock = vi
      .fn()
      .mockResolvedValueOnce(json(fill, 201))
      .mockResolvedValueOnce(json(fill, 200));
    vi.stubGlobal("fetch", mock);
    const order = { symbol: "BTC", side: "buy" as const, amount_usd: "100" };
    expect(await executeTrade(order, "100000.00", "key-1")).toEqual(fill);
    expect(await executeTrade(order, "100000.00", "key-1")).toEqual(fill);
    const [url, init] = call(mock, 0);
    expect(url).toBe("/api/v1/trades");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toEqual({
      ...order,
      expected_mid: "100000.00",
      idempotency_key: "key-1",
    });
  });

  it("throws on a malformed fill", async () => {
    document.cookie = "bj_csrf=tok; path=/";
    vi.stubGlobal("fetch", () => Promise.resolve(json({ trade_id: 1 }, 201)));
    await expect(
      executeTrade({ symbol: "BTC", side: "sell", quantity: "1" }, "1", "k"),
    ).rejects.toThrow("Unexpected trade response");
  });
});

describe("fetchHolding", () => {
  it("GETs the encoded symbol", async () => {
    const mock = vi.fn(() => Promise.resolve(json({ symbol: "BTC", quantity: "0.5" })));
    vi.stubGlobal("fetch", mock);
    expect(await fetchHolding("BTC")).toEqual({ symbol: "BTC", quantity: "0.5" });
    expect(call(mock, 0)[0]).toBe("/api/v1/holdings/BTC");
    await fetchHolding("A/B").catch(() => undefined);
    expect(call(mock, 1)[0]).toBe("/api/v1/holdings/A%2FB");
  });

  it("throws on a malformed holding", async () => {
    vi.stubGlobal("fetch", () => Promise.resolve(json({ symbol: "BTC" })));
    await expect(fetchHolding("BTC")).rejects.toThrow("Unexpected holding response");
  });
});
