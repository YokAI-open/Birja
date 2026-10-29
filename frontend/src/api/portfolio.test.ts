import { afterEach, expect, it, vi } from "vitest";
import { fetchPortfolio, isPortfolio, type Portfolio } from "./portfolio";

export const cashPortfolio: Portfolio = {
  cash: "9999.00",
  starting_cash: "10000.00",
  total_value: "9999.00",
  total_pl: "-1.00",
  total_pl_percent: "-0.01",
  cash_allocation_percent: "100.00",
  valuation_complete: true,
  valued_at: "2026-10-29T10:00:00Z",
  prices_as_of: null,
  fresh_seconds: 120,
  stale_seconds: 300,
  holdings: [],
};
const unpriced = {
  symbol: "BTC",
  name: "Bitcoin",
  is_active: false,
  quantity: "1.00000000",
  cost_basis: "2.00",
  average_cost: "2.00000000",
  mid: null,
  current_value: null,
  unrealized_pl: null,
  unrealized_pl_percent: null,
  allocation_percent: null,
  as_of: null,
  age_seconds: null,
  status: "unpriced",
};
afterEach(() => vi.unstubAllGlobals());

it("accepts complete and unpriced full contracts and rejects unavailable status", () => {
  expect(isPortfolio(cashPortfolio)).toBe(true);
  const missing = {
    ...cashPortfolio,
    valuation_complete: false,
    total_value: null,
    total_pl: null,
    total_pl_percent: null,
    cash_allocation_percent: null,
    holdings: [unpriced],
  };
  expect(isPortfolio(missing)).toBe(true);
  expect(isPortfolio({ ...missing, holdings: [{ ...unpriced, status: "unavailable" }] })).toBe(
    false,
  );
});

it("rejects numeric/exponent/missing fields, bad ages and naive timestamps", () => {
  for (const field of [
    "cash",
    "starting_cash",
    "total_value",
    "total_pl",
    "total_pl_percent",
    "cash_allocation_percent",
  ]) {
    for (const value of [2, "1e2", "NaN", undefined]) {
      expect(isPortfolio({ ...cashPortfolio, [field]: value })).toBe(false);
    }
  }
  for (const value of [
    null,
    [],
    {},
    { ...cashPortfolio, fresh_seconds: -1 },
    { ...cashPortfolio, valued_at: "2026-10-29T10:00:00" },
    { ...cashPortfolio, holdings: [{ ...unpriced, age_seconds: -1 }] },
  ]) {
    expect(isPortfolio(value)).toBe(false);
  }
});

it("GETs through the shared client forwarding cancellation and rejects invalid data", async () => {
  const fetch = vi
    .fn()
    .mockResolvedValueOnce(new Response(JSON.stringify(cashPortfolio)))
    .mockResolvedValueOnce(new Response("{}"));
  vi.stubGlobal("fetch", fetch);
  const signal = new AbortController().signal;
  expect(await fetchPortfolio(signal)).toEqual(cashPortfolio);
  expect(fetch.mock.calls[0]?.[0]).toBe("/api/v1/portfolio");
  expect(fetch.mock.calls[0]?.[1].signal).toBe(signal);
  await expect(fetchPortfolio()).rejects.toThrow("Unexpected portfolio response");
});
