import { afterEach, expect, it, vi } from "vitest";
import { ApiError } from "./client";
import { fetchEventHistory, isEventHistoryPage } from "./eventHistory";

export const dividend = {
  kind: "dividend",
  id: "dividend:9007199254740993",
  recorded_at: "2026-11-12T15:00:00.000001Z",
  asset_type: "stock",
  symbol: "AAPL",
  name: "Apple",
  cash_delta: "1.00",
  payment_reference: "dividend:9007199254740993",
  eligible_quantity: "100000000",
  rate: "0.00000001",
  credited_amount: "1.00",
  cutoff: "2026-11-10T14:30:00Z",
  ex_date: "2026-11-10",
  record_date: "2026-11-11",
  payable_date: "2026-11-12",
  credited_at: "2026-11-12T15:00:00.000001Z",
};
export const correction = {
  kind: "dividend_correction",
  id: "dividend_correction:12",
  recorded_at: "2026-11-12T16:00:00Z",
  asset_type: "stock",
  symbol: "AAPL",
  name: "Apple",
  cash_delta: "-0.50",
  payment_reference: dividend.id,
  decision_reference: "dividend_correction:12",
  outcome: "applied",
  reason: "target_applied",
  desired_total: "0.50",
  cumulative_applied_before: "1.00",
  proposed_delta: "-0.50",
  applied_delta: "-0.50",
  terms: {
    eligible_quantity: "100000000",
    rate: "0.000000005",
    cutoff: dividend.cutoff,
    ex_date: dividend.ex_date,
    record_date: dividend.record_date,
    payable_date: dividend.payable_date,
  },
  original: dividend,
};
export const trade = {
  kind: "trade",
  id: "trade:1",
  recorded_at: "2026-11-12T17:00:00Z",
  asset_type: "crypto",
  symbol: "BTC",
  name: "Bitcoin",
  cash_delta: "-1.00",
  side: "buy",
  quantity: "0.00000001",
  exec_price: "999999.99999999",
  fee: "0.01",
  filled_at: "2026-11-12T17:00:00Z",
  source: null,
  feed: null,
  quote_at: null,
};
export const split = {
  kind: "split",
  id: "split:1",
  recorded_at: "2026-11-12T14:00:00Z",
  asset_type: "stock",
  symbol: "AAPL",
  name: "Apple",
  cash_delta: "0.00",
  ratio_new: "4",
  ratio_old: "1",
  quantity_before: "2",
  quantity_after: "8",
  cost_basis_before: "100.00",
  cost_basis_after: "100.00",
  effective_at: "2026-11-12T13:00:00Z",
};
const page = (items: unknown[] = [dividend]) => ({ items, next_cursor: null });
afterEach(() => vi.unstubAllGlobals());

it("refuses a response exceeding the requested page bound", async () => {
  vi.stubGlobal("fetch", () => Promise.resolve(new Response(JSON.stringify(page([trade, dividend])))));
  await expect(fetchEventHistory({ limit: 1 })).rejects.toThrow("Unexpected event history response");
});

it("accepts an exact tiny rate and bigint identity without financial coercion", () => {
  expect(isEventHistoryPage(page())).toBe(true);
});
it("accepts legacy fractional crypto, whole stock and a basis-conserving split", () => {
  expect(isEventHistoryPage(page([trade, split]))).toBe(true);
  expect(
    isEventHistoryPage(
      page([
        {
          ...trade,
          asset_type: "stock",
          symbol: "AAPL",
          quantity: "2",
          source: "alpaca",
          feed: "iex",
          quote_at: "2026-11-12T16:59:59Z",
          fee: "0.00",
        },
      ]),
    ),
  ).toBe(true);
});
it("preserves a signed applied correction with an offpage original", () => {
  const valid = {
    ...correction,
    terms: { ...correction.terms, eligible_quantity: "50000000", rate: "0.00000001" },
  };
  expect(isEventHistoryPage(page([valid]))).toBe(true);
});
it("preserves uncertain unknown terms and accepts all fixed outcomes", () => {
  expect(
    isEventHistoryPage(
      page([
        {
          ...correction,
          outcome: "held_uncertain",
          reason: "terms_unverified",
          cash_delta: "0.00",
          applied_delta: "0.00",
          proposed_delta: null,
          desired_total: null,
          terms: null,
        },
      ]),
    ),
  ).toBe(true);
  expect(
    isEventHistoryPage(
      page([
        {
          ...correction,
          outcome: "held_unaffordable",
          reason: "insufficient_cash",
          cash_delta: "0.00",
          applied_delta: "0.00",
          terms: { ...correction.terms, eligible_quantity: "50000000", rate: "0.00000001" },
        },
      ]),
    ),
  ).toBe(true);
  expect(
    isEventHistoryPage(
      page([
        {
          ...correction,
          outcome: "verified_no_change",
          reason: "target_unchanged",
          cash_delta: "0.00",
          applied_delta: "0.00",
          proposed_delta: "0.00",
          desired_total: "1.00",
          terms: { ...correction.terms, rate: "0.00000001" },
        },
      ]),
    ),
  ).toBe(true);
});
it.each([
  { cash_delta: "0.99" },
  { rate: "1e-8" },
  { rate: 0.01 },
  { eligible_quantity: "1.5" },
  { id: "dividend:01" },
  { id: "dividend:9223372036854775808" },
  { payment_reference: "dividend:2" },
  { cutoff: "2026-02-30T00:00:00Z" },
  { ex_date: "2026-02-30" },
  { payable_date: "2026-13-01" },
  { recorded_at: "2026-11-12T15:00:00+00:00" },
  { rate: "9".repeat(513) },
  { name: "" },
  { credited_at: "2026-11-13T00:00:00Z" },
  { credited_amount: "1.001" },
  { alien: true },
])("rejects whole page on malformed dividend %o", (change) => {
  expect(isEventHistoryPage(page([trade, { ...dividend, ...change }]))).toBe(false);
});
it.each([
  { original: { ...dividend, id: "dividend:4", payment_reference: "dividend:4" } },
  { decision_reference: "dividend_correction:13" },
  { cash_delta: "-0.49" },
  { outcome: "paid" },
  { reason: "<script>" },
  { original: null },
  { outcome: "held_uncertain", reason: "terms_unverified", applied_delta: "1.00" },
  { outcome: "held_uncertain", reason: "terms_unverified", desired_total: "0.00" },
])("rejects broken correction lineage or held cash %o", (change) => {
  expect(isEventHistoryPage(page([{ ...correction, ...change }]))).toBe(false);
});
it("rejects malformed split/trade/page data", () => {
  for (const change of [
    { quantity_after: "7" },
    { cost_basis_after: "99.00" },
    { cash_delta: "1.00" },
    { ratio_new: "0" },
  ])
    expect(isEventHistoryPage(page([{ ...split, ...change }]))).toBe(false);
  for (const change of [
    { quantity: "0" },
    { fee: "-0.01" },
    { filled_at: "bad" },
    { cash_delta: "1.00" },
  ])
    expect(isEventHistoryPage(page([{ ...trade, ...change }]))).toBe(false);
  for (const value of [
    null,
    {},
    { items: [], next_cursor: "bad=" },
    page(Array(101).fill(dividend)),
    page([dividend, dividend]),
  ])
    expect(isEventHistoryPage(value)).toBe(false);
});
it("fetches only the isolated read-only endpoint with abort and no-store", async () => {
  const mock = vi.fn(() => Promise.resolve(new Response(JSON.stringify(page()))));
  vi.stubGlobal("fetch", mock);
  const signal = new AbortController().signal;
  expect(await fetchEventHistory({ limit: 25 }, signal)).toEqual(page());
  expect(mock.mock.calls[0]).toEqual([
    "/api/v1/history?limit=25",
    expect.objectContaining({ signal, cache: "no-store", method: "GET" }),
  ]);
});
it("rejects malformed network results and invalid request bounds", async () => {
  const mock = vi.fn(() => Promise.resolve(new Response(JSON.stringify({ items: null }))));
  vi.stubGlobal("fetch", mock);
  await expect(fetchEventHistory()).rejects.toThrow("Unexpected event history response");
  for (const args of [{ limit: 0 }, { limit: 101 }, { limit: 1.5 }, { cursor: "a".repeat(513) }])
    await expect(fetchEventHistory(args)).rejects.toThrow("Invalid event history request");
});
it("propagates abort and the existing 401 auth error", async () => {
  const controller = new AbortController();
  controller.abort();
  await expect(fetchEventHistory({}, controller.signal)).rejects.toMatchObject({
    name: "AbortError",
  });
  vi.stubGlobal("fetch", () =>
    Promise.resolve(
      new Response(JSON.stringify({ detail: { code: "unauthenticated" } }), { status: 401 }),
    ),
  );
  await expect(fetchEventHistory()).rejects.toBeInstanceOf(ApiError);
});
