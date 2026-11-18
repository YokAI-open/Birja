import { afterEach, expect, it, vi } from "vitest";
import { fetchPortfolioOverview, parsePortfolioOverview } from "./portfolioOverview";
import { isPortfolio, type Portfolio } from "./portfolio";
import { cashPortfolio, mixedPortfolio } from "@/test/portfolioFixtures";
import { ApiError } from "./client";

const root = "9007199254740993";
function row(portfolio: Portfolio = cashPortfolio(), id = root) {
  const { portfolio_id, ...statement } = portfolio;
  void portfolio_id;
  return { ...statement, id, description: "<script>plain text</script>\nStrategy" };
}
function incomplete() {
  const p = mixedPortfolio();
  Object.assign(p, {
    valuation_complete: false,
    known_value: "9796.00",
    unvalued_holding_count: 1,
    total_value: null,
    total_pl: null,
    total_pl_percent: null,
    cash_allocation_percent: null,
    prices_as_of: null,
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
  return p;
}
afterEach(() => vi.unstubAllGlobals());

it("accepts the exact 19-field server contract with precise independent custom/zero baselines", () => {
  const custom = {
    ...cashPortfolio(),
    starting_cash: "7654.00",
    total_pl: "2346.00",
    total_pl_percent: "30.65064019",
  };
  const zero = {
    ...cashPortfolio(),
    starting_cash: "0.00",
    total_pl: "10000.00",
    total_pl_percent: null,
  };
  const rows = [row(custom, "2"), row(zero, root)];
  expect(Object.keys(rows[0])).toHaveLength(19);
  expect(parsePortfolioOverview(rows)).toEqual(rows);
  expect(parsePortfolioOverview([])).toEqual([]);
  expect(Object.isFrozen(parsePortfolioOverview(rows))).toBe(true);
  expect(parsePortfolioOverview(rows)[0].starting_cash).toBe("7654.00");
});
it("preserves complete and incomplete mixed books independently and reuses detail validation", () => {
  const complete = mixedPortfolio(),
    missing = incomplete();
  expect(isPortfolio(complete)).toBe(true);
  expect(isPortfolio(missing)).toBe(true);
  const rows = [row(complete, "1"), row(missing, "2")];
  expect(parsePortfolioOverview(rows)).toEqual(rows);
  expect(parsePortfolioOverview(rows)[1]).toMatchObject({
    known_value: "9796.00",
    total_value: null,
    total_pl: null,
    total_pl_percent: null,
  });
});
it("retains dated/expired proof and original disclosure for later permission suppression, without renewing times", () => {
  for (const mode of ["closed", "halted"] as const) {
    const p = mixedPortfolio();
    p.holdings[0].stock_mark!.mark_mode = mode;
    p.valued_at = "2026-11-10T15:10:00Z";
    expect(parsePortfolioOverview([row(p)])[0].holdings[0].stock_mark).toEqual(
      p.holdings[0].stock_mark,
    );
  }
});
it.each([
  null,
  {},
  "[]",
  [null],
  [row(), row()],
  [row(undefined, "2"), row(undefined, "1")],
  [row(undefined, "01")],
  [row(undefined, "9223372036854775808")],
  [{ ...row(), id: 1 }],
  [{ ...row(), portfolio_id: root }],
  [{ ...row(), owner: "private" }],
  [{ ...row(), description: null }],
  [{ ...row(), description: "x".repeat(1001) }],
  [{ ...row(), description: "\r" }],
  [{ ...row(), description: "\ud800" }],
  [{ ...row(), name: "Cafe\u0301" }],
  Array.from({ length: 11 }, (_, i) => row(undefined, String(i + 1))),
])("rejects malformed/bounded/duplicate/unsorted overview %j", (body) => {
  expect(() => parsePortfolioOverview(body)).toThrow("Unexpected portfolio overview");
});
it.each(["cash", "starting_cash", "total_value", "total_pl", "total_pl_percent", "known_value"])(
  "rejects noncanonical and non-string monetary %s",
  (field) => {
    for (const value of [
      1,
      null,
      undefined,
      "NaN",
      "Infinity",
      "1e4",
      "01",
      "+1",
      "1.0000000001",
      "9".repeat(39),
    ])
      expect(() => parsePortfolioOverview([{ ...row(), [field]: value }])).toThrow();
  },
);
it.each([
  { total_value: null },
  { total_pl: "1" },
  { valuation_complete: false },
  { unvalued_holding_count: 1 },
  { fresh_seconds: Infinity },
  { stale_seconds: -1 },
  { valued_at: "2026-02-30T00:00:00Z" },
  { valued_at: "2026-11-10T00:00:00" },
  { prices_as_of: "2026-11-10T15:00:11Z" },
  { prices_as_of: "2026-11-10T15:00:00Z" },
  { class_values: { cash: "1", stocks: "0", crypto: "0" } },
])("rejects contradictory completeness/money/source-time fields %j", (change) => {
  expect(() => parsePortfolioOverview([{ ...row(), ...change }])).toThrow();
});
it("requires one shared valuation instant and exact oldest per-book source times", () => {
  expect(() =>
    parsePortfolioOverview([
      row(undefined, "1"),
      { ...row(undefined, "2"), valued_at: "2026-11-10T15:00:11Z" },
    ]),
  ).toThrow();
  const mixed = row(mixedPortfolio());
  expect(() => parsePortfolioOverview([{ ...mixed, prices_as_of: null }])).toThrow();
  expect(() =>
    parsePortfolioOverview([{ ...mixed, prices_as_of: "2026-11-10T14:59:59Z" }]),
  ).toThrow();
  const early = mixedPortfolio();
  early.valued_at = "2026-11-10T14:59:59Z";
  expect(() => parsePortfolioOverview([row(early)])).toThrow();
});
it("does not accept forged safe marks or project a total onto incomplete evidence", () => {
  for (const change of [
    { units_safe: false },
    { authority: null },
    { feed: "sip" },
    { retained_until: "2026-11-10T15:00:09Z" },
    { valid_until: "2026-11-10T17:00:00Z" },
    { event_at: "2026-11-10T15:00:02Z" },
    { other: "extra" },
  ]) {
    const p = mixedPortfolio();
    Object.assign(p.holdings[0].stock_mark!, change);
    expect(() => parsePortfolioOverview([row(p)])).toThrow();
  }
  const p = incomplete();
  p.total_value = "9796.00";
  expect(() => parsePortfolioOverview([row(p)])).toThrow();
  const duplicate = mixedPortfolio();
  duplicate.holdings.push(duplicate.holdings[0]);
  expect(() => parsePortfolioOverview([row(duplicate)])).toThrow();
});
it("uses the static overview URL, no-store credentials and AbortSignal", async () => {
  const rows = [row()];
  const fetcher = vi.fn(async () => new Response(JSON.stringify(rows)));
  vi.stubGlobal("fetch", fetcher);
  const signal = new AbortController().signal;
  expect(await fetchPortfolioOverview(signal)).toEqual(rows);
  expect(fetcher.mock.calls[0]).toEqual([
    "/api/v2/portfolios/overview",
    expect.objectContaining({
      signal,
      cache: "no-store",
      credentials: "same-origin",
      method: "GET",
    }),
  ]);
});
it("never replaces failed, malformed or cancelled overview with an empty success", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(
      async () =>
        new Response(JSON.stringify({ detail: { code: "service_unavailable" } }), { status: 503 }),
    ),
  );
  await expect(fetchPortfolioOverview()).rejects.toBeInstanceOf(ApiError);
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => new Response("{}")),
  );
  await expect(fetchPortfolioOverview()).rejects.toThrow();
  const controller = new AbortController();
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => {
      controller.abort();
      return new Response("[]");
    }),
  );
  await expect(fetchPortfolioOverview(controller.signal)).rejects.toMatchObject({
    name: "AbortError",
  });
});
