import { afterEach, expect, it, vi } from "vitest";
import { fetchPortfolio, isPortfolio } from "./portfolio";
import { cashPortfolio, mixedPortfolio, stockHolding } from "@/test/portfolioFixtures";
afterEach(() => vi.unstubAllGlobals());
it("accepts exact complete, incomplete and dated mixed snapshots", () => {
  expect(isPortfolio(cashPortfolio())).toBe(true);
  expect(isPortfolio(mixedPortfolio())).toBe(true);
  const p = mixedPortfolio();
  Object.assign(p, {
    valuation_complete: false,
    known_value: "9796.00",
    unvalued_holding_count: 1,
    total_value: null,
    total_pl: null,
    total_pl_percent: null,
    cash_allocation_percent: null,
    class_values: { cash: p.cash, stocks: null, crypto: "0" },
    class_allocation_percent: { cash: null, stocks: null, crypto: null },
  });
  Object.assign(p.holdings[0], {
    average_cost: null,
    mid: null,
    current_value: null,
    unrealized_pl: null,
    unrealized_pl_percent: null,
    allocation_percent: null,
    as_of: null,
    age_seconds: null,
    status: "unpriced",
    stock_mark: {
      mark_mode: "unavailable",
      valuation_reason: "action_unavailable",
      source: null,
      feed: null,
      event_at: null,
      collected_at: null,
      historical_admission_until: null,
      retained_until: null,
      valid_until: null,
      authority: null,
      units_safe: false,
    },
  });
  expect(isPortfolio(p)).toBe(true);
  for (const mode of ["closed", "halted"] as const) {
    const dated = mixedPortfolio();
    dated.holdings[0].stock_mark!.mark_mode = mode;
    dated.valued_at = "2026-11-10T15:10:00Z";
    expect(isPortfolio(dated)).toBe(true);
  }
});
it.each([
  "cash",
  "starting_cash",
  "total_value",
  "total_pl",
  "total_pl_percent",
  "cash_allocation_percent",
  "known_value",
])("rejects invalid bounded decimals in %s", (field) => {
  for (const value of [2, "1e2", "NaN", undefined, "9".repeat(39), "0.0000000001", "01", "+2"])
    expect(isPortfolio({ ...cashPortfolio(), [field]: value })).toBe(false);
});
it("rejects contradictory complete/count/classes/nulls and extra fields", () => {
  const p = mixedPortfolio();
  for (const change of [
    { unvalued_holding_count: 1 },
    { valuation_complete: false },
    { total_value: null },
    { known_value: "10" },
    { total_pl: "0" },
    { other: true },
    { total_pl_percent: null },
    { class_values: { cash: "1", stocks: "202", crypto: "0" } },
    { class_values: { cash: p.cash, stocks: null, crypto: "0" } },
    { class_allocation_percent: { cash: "101", stocks: "0", crypto: "0" } },
    { holdings: [stockHolding(), stockHolding()] },
    { valued_at: "2026-11-10T00:00:00" },
    { prices_as_of: "2026-02-30T00:00:00Z" },
    { fresh_seconds: -1 },
    { fresh_seconds: 301 },
  ])
    expect(isPortfolio({ ...p, ...change })).toBe(false);
});
it("rejects unsafe stock marks and inconsistent holding facts", () => {
  for (const change of [
    { coin_id: "0" },
    { coin_id: "9223372036854775808" },
    { quantity: "1.1" },
    { quantity: "0" },
    { asset_class: "bond" },
    { provider_asset_id: null },
    { stock_mark: null },
    { average_cost: null },
    { status: "unavailable" },
    { age_seconds: -1 },
    { mid: null },
    { current_value: null },
    { as_of: null },
  ])
    expect(isPortfolio({ ...mixedPortfolio(), holdings: [{ ...stockHolding(), ...change }] })).toBe(
      false,
    );
  for (const change of [
    { feed: "sip" },
    { source: "other" },
    { units_safe: false },
    { retained_until: "2026-11-10T15:00:09Z" },
    { authority: null },
    { other: true },
    { event_at: "2026-11-10T15:00:02Z" },
  ]) {
    const h = stockHolding();
    Object.assign(h.stock_mark!, change);
    expect(isPortfolio({ ...mixedPortfolio(), holdings: [h] })).toBe(false);
  }
});
it("GETs through shared client with cancellation/no-store and rejects malformed bodies", async () => {
  const body = mixedPortfolio();
  const fetch = vi
    .fn()
    .mockResolvedValueOnce(new Response(JSON.stringify(body)))
    .mockResolvedValueOnce(new Response("{}"));
  vi.stubGlobal("fetch", fetch);
  const signal = new AbortController().signal;
  expect(await fetchPortfolio(signal)).toEqual(body);
  expect(fetch.mock.calls[0][0]).toBe("/api/v1/portfolio");
  expect(fetch.mock.calls[0][1]).toMatchObject({ signal, cache: "no-store" });
  await expect(fetchPortfolio()).rejects.toThrow("Unexpected portfolio response");
});
it("rejects a source timestamp after valuation and prices attached to unavailable authority", () => {
  const future = mixedPortfolio();
  future.valued_at = "2026-11-10T14:59:59Z";
  expect(isPortfolio(future)).toBe(false);
  const p = mixedPortfolio();
  p.holdings[0].stock_mark = {
    mark_mode: "unavailable",
    valuation_reason: "action_unavailable",
    source: null,
    feed: null,
    event_at: null,
    collected_at: null,
    historical_admission_until: null,
    retained_until: null,
    valid_until: null,
    authority: null,
    units_safe: false,
  };
  expect(isPortfolio(p)).toBe(false);
});
