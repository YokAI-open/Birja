import { afterEach, expect, it, vi } from "vitest";
import { ApiError } from "./client";
import { fetchEventHistory, isEventHistoryPage } from "./eventHistory";
import { fillFixture } from "@/test/stockTradeFixtures";

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
  vi.stubGlobal("fetch", () =>
    Promise.resolve(new Response(JSON.stringify(page([trade, dividend])))),
  );
  await expect(fetchEventHistory({ limit: 1 })).rejects.toThrow(
    "Unexpected event history response",
  );
});
const token = (raw: string) => btoa(raw).replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_");
const cursorBody = {
  v: 2,
  recorded_at: "2026-11-12T15:00:00.000001Z",
  kind_rank: 3,
  source_id: "9007199254740993",
};
it("retains a canonical bounded cursor and sends it without financial ID coercion", async () => {
  const cursor = token(JSON.stringify(cursorBody));
  const body = { items: [dividend], next_cursor: cursor };
  expect(isEventHistoryPage(body)).toBe(true);
  const mock = vi.fn(() => Promise.resolve(new Response(JSON.stringify(body))));
  vi.stubGlobal("fetch", mock);
  expect(await fetchEventHistory({ cursor })).toEqual(body);
  expect(mock).toHaveBeenCalledWith(`/api/v1/history?cursor=${cursor}`, expect.any(Object));
});
it.each([
  "!",
  "a",
  "A".repeat(513),
  token("null"),
  token("{bad}"),
  token(JSON.stringify({ ...cursorBody, v: 1 })),
  token(JSON.stringify({ ...cursorBody, kind_rank: 5 })),
  token(JSON.stringify({ ...cursorBody, source_id: "01" })),
  token(JSON.stringify({ ...cursorBody, recorded_at: "2026-11-12T15:00:00Z" })),
  token('{"v":2,"v":2,"recorded_at":"2026-11-12T15:00:00.000001Z","kind_rank":3,"source_id":"1"}'),
  token(JSON.stringify({ ...cursorBody, extra: true })),
])("rejects noncanonical cursor %s", (next_cursor) => {
  expect(isEventHistoryPage({ items: [], next_cursor })).toBe(false);
});
it("projects an existing immutable stock receipt without recalculating its fill", () => {
  const f = fillFixture();
  expect(
    isEventHistoryPage(
      page([
        {
          kind: "trade",
          id: `trade:${f.trade_id}`,
          recorded_at: f.executed_at,
          asset_type: "stock",
          symbol: f.symbol,
          name: f.company_name,
          cash_delta: f.cash_delta,
          side: f.side,
          quantity: f.quantity,
          exec_price: f.exec_price,
          fee: f.fee,
          filled_at: f.executed_at,
          source: f.source,
          feed: f.feed,
          quote_at: f.event_at,
        },
      ]),
    ),
  ).toBe(true);
});
it("distinguishes verified zero and exact half-even ties from unknown terms", () => {
  for (const [rate, amount] of [
    ["0.005", "0.00"],
    ["0.015", "0.02"],
    ["0.025", "0.02"],
    ["0", "0.00"],
  ]) {
    expect(
      isEventHistoryPage(
        page([
          {
            ...dividend,
            eligible_quantity: "1",
            rate,
            credited_amount: amount,
            cash_delta: amount,
            ex_date: null,
            record_date: null,
          },
        ]),
      ),
    ).toBe(true);
  }
});
it.each([
  { eligible_quantity: "1000000000000" },
  { eligible_quantity: "-1" },
  { rate: "-0" },
  { rate: "-1" },
  { rate: "999999999999.999999999" },
  { credited_amount: "999999999999.99999999" },
  { recorded_at: "0000-01-01T00:00:00Z" },
  { recorded_at: "2026-11-12T15:00:60Z" },
  { name: "x".repeat(257) },
  { name: "a\nb" },
  { asset_type: "crypto" },
  { kind: "income" },
  { cutoff: "2026-11-13T00:00:00Z" },
])("rejects unsupported dividend range or identity %o", (change) => {
  expect(isEventHistoryPage(page([{ ...dividend, ...change }]))).toBe(false);
});
it("rejects stock fractional shares, false feed and foreign original chronology", () => {
  const stock = {
    ...trade,
    asset_type: "stock",
    quantity: "1",
    fee: "0",
    source: "alpaca",
    feed: "iex",
    quote_at: trade.filled_at,
  };
  for (const change of [
    { quantity: "1.5" },
    { source: null },
    { feed: "sip" },
    { quote_at: "2026-11-13T00:00:00Z" },
    { fee: "0.01" },
  ])
    expect(isEventHistoryPage(page([{ ...stock, ...change }]))).toBe(false);
  expect(isEventHistoryPage(page([{ ...correction, recorded_at: "2026-11-12T14:00:00Z" }]))).toBe(
    false,
  );
});

it("accepts an exact tiny rate and bigint identity without financial coercion", () => {
  expect(isEventHistoryPage(page())).toBe(true);
});
it("accepts a real sell cash sign and rejects negative zero/noncanonical encodings", () => {
  expect(isEventHistoryPage(page([{ ...trade, side: "sell", cash_delta: "0.01" }]))).toBe(true);
  expect(isEventHistoryPage({ items: [], next_cursor: "Zh" })).toBe(false);
  for (const change of [
    { cash_delta: "-0.00" },
    { side: "short" },
    { exec_price: "0" },
    { quantity: "NaN" },
    { exec_price: "1000000000000" },
    { extra: 1 },
  ])
    expect(isEventHistoryPage(page([{ ...trade, ...change }]))).toBe(false);
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
