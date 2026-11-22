import { afterEach, expect, it, vi } from "vitest";
import { ApiError } from "./client";
import { fetchPortfolio, isPortfolio } from "./portfolio";
import { fetchHistory, isHistoryPage } from "./history";
import { fetchEventHistory, isEventHistoryPage } from "./eventHistory";
import { cashPortfolio, mixedPortfolio } from "@/test/portfolioFixtures";

const root = "9007199254740993",
  other = "9007199254740994";
const token = (value: unknown) =>
  btoa(typeof value === "string" ? value : JSON.stringify(value))
    .replace(/=/g, "")
    .replace(/\+/g, "-")
    .replace(/\//g, "_");
const stamp = "2026-11-12T15:00:00.000001Z";
const tradeCursor = (id = root) =>
  token({ v: 2, portfolio_id: id, created_at: stamp, id: "9007199254740995" });
const mixedCursor = (id = root) =>
  token({
    v: 3,
    portfolio_id: id,
    recorded_at: stamp,
    kind_rank: 3,
    source_id: "9007199254740995",
  });
const statement = () => ({ ...cashPortfolio(), portfolio_id: root, name: "My portfolio" });
const trade = {
  id: "9007199254740995",
  created_at: stamp,
  symbol: "BTC",
  name: "Bitcoin",
  side: "buy",
  quantity: "0.00001",
  exec_price: "100000",
  fee: "0.01",
  total: "-1.01",
};
const dividend = {
  kind: "dividend",
  id: "dividend:2",
  recorded_at: stamp,
  asset_type: "stock",
  symbol: "AAPL",
  name: "Apple",
  cash_delta: "1.00",
  payment_reference: "dividend:2",
  eligible_quantity: "2",
  rate: "0.50",
  credited_amount: "1.00",
  cutoff: "2026-11-10T14:30:00Z",
  ex_date: "2026-11-10",
  record_date: "2026-11-11",
  payable_date: "2026-11-12",
  credited_at: stamp,
};
const correction = {
  kind: "dividend_correction",
  id: "dividend_correction:3",
  recorded_at: "2026-11-12T16:00:00Z",
  asset_type: "stock",
  symbol: "AAPL",
  name: "Apple",
  cash_delta: "-0.50",
  payment_reference: dividend.id,
  decision_reference: "dividend_correction:3",
  outcome: "applied",
  reason: "target_applied",
  desired_total: "0.50",
  cumulative_applied_before: "1.00",
  proposed_delta: "-0.50",
  applied_delta: "-0.50",
  terms: {
    eligible_quantity: "1",
    rate: "0.50",
    cutoff: dividend.cutoff,
    ex_date: dividend.ex_date,
    record_date: dividend.record_date,
    payable_date: dividend.payable_date,
  },
  original: dividend,
};
const reply = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

it("uses only explicit scoped no-store read URLs and preserves opaque cursors exactly", async () => {
  const history = { items: [trade], next_cursor: tradeCursor() };
  const events = { items: [correction], next_cursor: mixedCursor() };
  const fetcher = vi.fn(async (input: RequestInfo | URL) =>
    reply(
      String(input).includes("/event-history")
        ? events
        : String(input).includes("/history")
          ? history
          : statement(),
    ),
  );
  vi.stubGlobal("fetch", fetcher);
  const signal = new AbortController().signal;
  expect(await fetchPortfolio(root, signal)).toEqual(statement());
  expect(await fetchHistory(root, { cursor: tradeCursor(), limit: 1 }, signal)).toEqual(history);
  const result = await fetchEventHistory(root, { cursor: mixedCursor(), limit: 1 }, signal);
  expect(result).toEqual(events);
  expect(result.items[0]).toMatchObject({ original: dividend });
  const calls = fetcher.mock.calls as unknown as [string, RequestInit][];
  expect(calls.map(([path]) => path)).toEqual([
    `/api/v2/portfolios/${root}`,
    `/api/v2/portfolios/${root}/history?cursor=${tradeCursor()}&limit=1`,
    `/api/v2/portfolios/${root}/event-history?cursor=${mixedCursor()}&limit=1`,
  ]);
  expect(calls.every(([, init]) => init.signal === signal && init.cache === "no-store")).toBe(true);
});
it.each([undefined, null, "", "0", "01", "-1", "1/../2", "1?other=2", 1, "9223372036854775808"])(
  "refuses malformed target %s before all financial read requests",
  async (id) => {
    const fetcher = vi.fn();
    vi.stubGlobal("fetch", fetcher);
    for (const call of [
      () => fetchPortfolio(id as string),
      () => fetchHistory(id as string),
      () => fetchEventHistory(id as string),
    ])
      await expect(call()).rejects.toThrow();
    expect(fetcher).not.toHaveBeenCalled();
  },
);
it.each([undefined, other, 1, "01"])(
  "rejects missing or crossed valuation target %s",
  async (id) => {
    const body = { ...statement(), portfolio_id: id };
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => reply(body)),
    );
    await expect(fetchPortfolio(root)).rejects.toThrow("Unexpected portfolio response");
    if (id !== other) expect(isPortfolio(body)).toBe(false);
  },
);
it.each(["", " ", "\u0000bad", "a".repeat(61)])("rejects invalid portfolio name %s", (name) => {
  expect(isPortfolio({ ...statement(), name })).toBe(false);
});
it("retains exact complete and incomplete valuation semantics with the stored baseline", async () => {
  const complete = {
    ...statement(),
    starting_cash: "9000.00",
    total_pl: "1000.00",
    total_pl_percent: "11.11111111",
  };
  expect(isPortfolio(complete)).toBe(true);
  const incomplete = { ...mixedPortfolio(), portfolio_id: root, name: "Strategy" };
  Object.assign(incomplete, {
    valuation_complete: false,
    known_value: incomplete.cash,
    unvalued_holding_count: 1,
    total_value: null,
    total_pl: null,
    total_pl_percent: null,
    cash_allocation_percent: null,
    class_values: { cash: incomplete.cash, stocks: null, crypto: "0" },
    class_allocation_percent: { cash: null, stocks: null, crypto: null },
  });
  Object.assign(incomplete.holdings[0], {
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
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => reply(incomplete)),
  );
  expect(await fetchPortfolio(root)).toEqual(incomplete);
});
it.each(["trade", "mixed"])("never reuses a previous root's %s request cursor", async (kind) => {
  const fetcher = vi.fn();
  vi.stubGlobal("fetch", fetcher);
  const request =
    kind === "trade"
      ? fetchHistory(other, { cursor: tradeCursor() })
      : fetchEventHistory(other, { cursor: mixedCursor() });
  await expect(request).rejects.toThrow();
  expect(fetcher).not.toHaveBeenCalled();
});
it.each(["trade", "mixed"])("refuses a crossed %s continuation in a response", async (kind) => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () =>
      reply({ items: [], next_cursor: kind === "trade" ? tradeCursor(other) : mixedCursor(other) }),
    ),
  );
  await expect(kind === "trade" ? fetchHistory(root) : fetchEventHistory(root)).rejects.toThrow();
});
it.each(["trade", "mixed"])(
  "keeps malformed and legacy %s tokens from changing target",
  async (kind) => {
    for (const cursor of [
      "!",
      "a",
      "A".repeat(513),
      token(null),
      token({ v: 1 }),
      token({ v: 2, recorded_at: stamp, kind_rank: 3, source_id: "2" }),
      token('{"v":2,"v":2,"portfolio_id":"' + root + '","created_at":"' + stamp + '","id":"2"}'),
    ]) {
      const fetcher = vi.fn();
      vi.stubGlobal("fetch", fetcher);
      await expect(
        kind === "trade" ? fetchHistory(root, { cursor }) : fetchEventHistory(root, { cursor }),
      ).rejects.toThrow();
      expect(fetcher).not.toHaveBeenCalled();
    }
  },
);
it.each([0, -1, 101, 1.5, NaN, "1"])(
  "refuses invalid page limit %s before network",
  async (limit) => {
    const fetcher = vi.fn();
    vi.stubGlobal("fetch", fetcher);
    await expect(fetchHistory(root, { limit: limit as number })).rejects.toThrow();
    await expect(fetchEventHistory(root, { limit: limit as number })).rejects.toThrow();
    expect(fetcher).not.toHaveBeenCalled();
  },
);
it.each([404, 409])(
  "keeps unavailable/version errors %s after a prior financial success",
  async (status) => {
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce(reply(statement()))
      .mockImplementation(async () =>
        reply(
          { detail: { code: status === 404 ? "portfolio_unavailable" : "portfolio_required" } },
          status,
        ),
      );
    vi.stubGlobal("fetch", fetcher);
    await fetchPortfolio(root);
    for (const call of [
      () => fetchPortfolio(other),
      () => fetchHistory(other),
      () => fetchEventHistory(other),
    ])
      await expect(call()).rejects.toBeInstanceOf(ApiError);
  },
);
it("refuses malformed embedded original references instead of hydrating from another request", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () =>
      reply({ items: [{ ...correction, payment_reference: "dividend:999" }], next_cursor: null }),
    ),
  );
  await expect(fetchEventHistory(root)).rejects.toThrow("Unexpected event history response");
});
it("retains versioned page guards without accepting old unbound tokens", () => {
  expect(isHistoryPage({ items: [trade], next_cursor: tradeCursor() }, root)).toBe(true);
  expect(isEventHistoryPage({ items: [correction], next_cursor: mixedCursor() }, root)).toBe(true);
  expect(isHistoryPage({ items: [], next_cursor: tradeCursor(other) }, root)).toBe(false);
  expect(isEventHistoryPage({ items: [], next_cursor: mixedCursor(other) }, root)).toBe(false);
});
it("does not publish a late cancelled financial read", async () => {
  for (const kind of ["statement", "trade", "mixed"]) {
    const controller = new AbortController();
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        controller.abort();
        return reply(kind === "statement" ? statement() : { items: [], next_cursor: null });
      }),
    );
    await expect(
      kind === "statement"
        ? fetchPortfolio(root, controller.signal)
        : kind === "trade"
          ? fetchHistory(root, {}, controller.signal)
          : fetchEventHistory(root, {}, controller.signal),
    ).rejects.toMatchObject({ name: "AbortError" });
  }
});

it.each(["trade", "mixed"])(
  "refuses malformed root and ordering fields inside %s cursor",
  async (kind) => {
    const original =
      kind === "trade"
        ? { v: 2, portfolio_id: root, created_at: stamp, id: "5" }
        : { v: 3, portfolio_id: root, recorded_at: stamp, kind_rank: 3, source_id: "5" };
    for (const change of [
      { portfolio_id: "01" },
      { portfolio_id: 1 },
      { portfolio_id: "9223372036854775808" },
      { portfolio_id: undefined },
      { v: 99 },
      { extra: true },
      kind === "trade" ? { id: "0" } : { source_id: "0" },
      kind === "trade"
        ? { created_at: "2026-11-12T15:00:00Z" }
        : { recorded_at: "2026-11-12T15:00:00Z" },
      kind === "trade"
        ? { created_at: "0000-11-12T15:00:00.000001Z" }
        : { recorded_at: "0000-11-12T15:00:00.000001Z" },
    ]) {
      const fetcher = vi.fn();
      vi.stubGlobal("fetch", fetcher);
      const cursor = token({ ...original, ...change });
      await expect(
        kind === "trade" ? fetchHistory(root, { cursor }) : fetchEventHistory(root, { cursor }),
      ).rejects.toThrow();
      expect(fetcher).not.toHaveBeenCalled();
    }
  },
);
it.each(["trade", "mixed"])("refuses duplicate or over-limit %s response rows", async (kind) => {
  for (const limit of [1, 25]) {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        reply({
          items: kind === "trade" ? [trade, trade] : [dividend, dividend],
          next_cursor: null,
        }),
      ),
    );
    await expect(
      kind === "trade" ? fetchHistory(root, { limit }) : fetchEventHistory(root, { limit }),
    ).rejects.toThrow();
  }
});
