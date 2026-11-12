import { afterEach, describe, expect, it, vi } from "vitest";
import {
  isStockFill,
  isStockTradeQuote,
  isStockContext,
  isStockOrder,
  isStockAttempt,
  isStockPriceChanged,
  fetchStockContext,
  fetchStockQuote,
  executeStockTrade,
  StockTradeError,
} from "./stockTrades";
import { quoteFixture, fillFixture, contextFixture } from "@/test/stockTradeFixtures";

describe("stock money and immutable receipt boundary", () => {
  it("accepts exact fee-free economics and saved bigint IDs without renewing old receipts", () => {
    expect(isStockTradeQuote(quoteFixture())).toBe(true);
    expect(isStockFill(fillFixture())).toBe(true);
  });
});

const order = { symbol: "AAPL", side: "buy", quantity: "2" } as const;
const attempt = {
  ...order,
  expected_exec_price: "102",
  idempotency_key: "00000000-0000-0000-0000-000000000001",
};
const changed = () => ({
  code: "price_changed",
  previous_exec_price: "101",
  previous_cash_delta: "-202",
  exec_price_change: "1",
  cash_delta_change: "-2",
  quote: quoteFixture(),
});
afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  document.cookie = "bj_csrf=; Max-Age=0; path=/";
});

it("accepts current independent context, whole requests and exact replacement arithmetic", () => {
  expect(isStockContext(contextFixture())).toBe(true);
  expect(isStockOrder(order)).toBe(true);
  expect(isStockAttempt(attempt)).toBe(true);
  expect(isStockPriceChanged(changed())).toBe(true);
  const q = {
    ...quoteFixture(),
    bid: "1.00000000",
    ask: "1.00000001",
    exact_mid: "1.000000005",
    exec_price: "1.00000001",
    notional: "2.00",
    cash_delta: "-2.00",
    cash_after: "9998.00",
  };
  expect(isStockTradeQuote(q)).toBe(true);
});

it.each([
  { quantity: 2 },
  { quantity: "2.0" },
  { quantity: "0" },
  { quantity: "-1" },
  { quantity: "1e2" },
  { quantity: "1000000000000" },
  { symbol: "aapl" },
  { side: "short" },
  { user_id: 1 },
])("rejects invalid or foreign request fields %j", (change) =>
  expect(isStockOrder({ ...order, ...change })).toBe(false),
);
it.each([
  { exec_price: "101" },
  { bid: 100 },
  { ask: "NaN" },
  { exact_mid: "101.000000001" },
  { quantity: "2.5" },
  { cash_after: "9797" },
  { cash_delta: "204" },
  { fee: "0.01" },
  { notional: "203.99" },
  { held_after: "3" },
  { coin_id: 16 },
  { coin_id: "9223372036854775808" },
  { provider_asset_id: "" },
  { currency: "EUR" },
  { listing_exchange: "OTC" },
  { source: "kraken" },
  { feed: "sip" },
  { raw: "private" },
  { event_at: "2026-02-30T15:00:00Z" },
  { event_at: "2026-11-10T15:00:11Z" },
  { collected_at: "2026-11-10T15:00:11Z" },
  { age_seconds: 9 },
  { session_date: "2026-11-09" },
  { session_opens_at: "2026-11-10T15:00:01Z" },
  { session_closes_at: "2026-11-10T15:00:10Z" },
  { valid_until: "2026-11-10T15:00:10Z" },
  { valid_until: "2026-11-10T15:01:11Z" },
  { ask: "1e2" },
  { ask: "0102" },
  { ask: "102.000000001" },
  { ask: "1000000000000" },
])("rejects inconsistent financial quote %j", (change) =>
  expect(isStockTradeQuote({ ...quoteFixture(), ...change })).toBe(false),
);
it.each([
  { schema_version: 2 },
  { trade_id: 9007199254740992 },
  { executed_at: "2026-11-10T15:00:11Z" },
  { executed_at: "2026-11-10T15:00:00Z" },
  { valid_until: "2026-11-10T15:01:00Z" },
])("rejects malformed immutable receipt %j", (change) =>
  expect(isStockFill({ ...fillFixture(), ...change })).toBe(false),
);
it("does not expire a historical saved receipt against the browser date", () => {
  vi.spyOn(Date, "now").mockReturnValue(Date.parse("2030-01-01T00:00:00Z"));
  expect(isStockFill(fillFixture())).toBe(true);
});
it.each(["generation", "hash", "duplicate", "deadline", "calendar", "continuity", "unsafe"])(
  "rejects invalid authority %s",
  (which) => {
    const q = quoteFixture();
    if (which === "generation") q.authority.admissions[0].generation = 0;
    if (which === "hash") q.authority.admissions[0].row_hash = "f".repeat(63);
    if (which === "duplicate") q.authority.admissions[0].product = "quotes";
    if (which === "deadline") q.authority.admissions[0].valid_until = q.observed_at;
    if (which === "calendar") q.authority.calendar_generation = 5;
    if (which === "continuity") q.authority.continuity_generation = 0;
    if (which === "unsafe") q.authority.unit_epoch = Number.MAX_SAFE_INTEGER + 1;
    expect(isStockTradeQuote(q)).toBe(false);
  },
);
it.each([
  "status",
  "bootstrap",
  "lease",
  "quote-units",
  "session",
  "reason",
  "max",
  "closed-enable",
  "extra",
])("rejects unsafe current context %s", (which) => {
  const c = contextFixture();
  if (which === "status") c.status.state = "unknown";
  if (which === "bootstrap") c.status.bootstrap_verified = false;
  if (which === "lease") c.status.valid_until = c.observed_at;
  if (which === "quote-units") c.quote!.unit_epoch = 1;
  if (which === "session") c.session.session_date = "2026-02-30";
  if (which === "reason") c.execution_reason = "market_closed";
  if (which === "max") c.buy_max_quantity = "1000000000000";
  if (which === "closed-enable") c.session.state = "closed";
  if (which === "extra") Object.assign(c, { user_id: 2 });
  expect(isStockContext(c)).toBe(false);
});
it.each(["price", "delta", "zero", "raw"])("rejects malformed replacement %s", (which) => {
  const value = changed();
  if (which === "price") value.exec_price_change = "2";
  if (which === "delta") value.previous_cash_delta = "-201";
  if (which === "zero") {
    value.previous_exec_price = "102";
    value.previous_cash_delta = "-204";
    value.exec_price_change = "0";
    value.cash_delta_change = "0";
  }
  if (which === "raw") Object.assign(value, { key: "private" });
  expect(isStockPriceChanged(value)).toBe(false);
});
it("accepts closed editable context without authorizing or inventing max quantity", () => {
  const c = contextFixture();
  c.execution_enabled = false;
  c.execution_reason = "market_closed";
  c.session.state = "closed";
  c.valid_until = null;
  c.buy_max_quantity = "0";
  c.quote = null;
  expect(isStockContext(c)).toBe(true);
});
it("fetches all routes through the common client with exact unchanged economic body", async () => {
  document.cookie = "bj_csrf=test; path=/";
  const fetcher = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    void init;
    return new Response(
      JSON.stringify(
        String(input).endsWith("/context")
          ? contextFixture()
          : String(input).endsWith("/quote")
            ? quoteFixture()
            : fillFixture(),
      ),
    );
  });
  vi.stubGlobal("fetch", fetcher);
  const context = await fetchStockContext("AAPL");
  const quote = await fetchStockQuote(order);
  const fill = await executeStockTrade(attempt);
  expect(context.transport.round_trip_ms).toBeGreaterThanOrEqual(0);
  expect(quote.transport.received_at).toBeGreaterThanOrEqual(quote.transport.started_at);
  expect(fill.trade_id).toBe("9007199254740993");
  expect(JSON.parse((fetcher.mock.calls[2][1] as RequestInit).body as string)).toEqual(attempt);
});
it.each(["partial", "foreign-order", "network", "unknown-code", "malformed-reprice"])(
  "treats ambiguous execute %s as UNKNOWN, without keys or raw messages",
  async (which) => {
    document.cookie = "bj_csrf=test; path=/";
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        if (which === "network") throw new Error("private-network-message");
        if (which === "unknown-code")
          return new Response(
            JSON.stringify({ detail: { code: "private-code", message: attempt.idempotency_key } }),
            { status: 409 },
          );
        if (which === "malformed-reprice")
          return new Response(
            JSON.stringify({ detail: { ...changed(), previous_cash_delta: "-99" } }),
            { status: 409 },
          );
        return new Response(
          JSON.stringify(which === "partial" ? {} : { ...fillFixture(), symbol: "MSFT" }),
        );
      }),
    );
    await expect(executeStockTrade(attempt)).rejects.toMatchObject({
      kind: "unknown",
      message: "Stock order result is unconfirmed.",
    });
  },
);
it("recognizes only validated definitive refusals and replacement previews", async () => {
  document.cookie = "bj_csrf=test; path=/";
  vi.stubGlobal(
    "fetch",
    vi.fn(
      async () =>
        new Response(JSON.stringify({ detail: { code: "insufficient_cash" } }), { status: 422 }),
    ),
  );
  await expect(executeStockTrade(attempt)).rejects.toMatchObject({
    kind: "refused",
    code: "insufficient_cash",
  });
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => new Response(JSON.stringify({ detail: changed() }), { status: 409 })),
  );
  const prior = { ...attempt, expected_exec_price: "101" };
  await expect(executeStockTrade(prior)).rejects.toMatchObject({
    kind: "reprice",
    replacement: { quote: { exec_price: "102.00000000" } },
  });
  expect(new StockTradeError("unknown").message).not.toContain(prior.idempotency_key);
});

it("counts authentication refresh, retry and body parsing in the full RTT", async () => {
  document.cookie = "bj_csrf=test; path=/";
  let clock = 0,
    requests = 0;
  vi.spyOn(performance, "now").mockImplementation(() => clock);
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      if (String(input).endsWith("/auth/refresh")) {
        clock = 15;
        return new Response(null, { status: 204 });
      }
      requests++;
      if (requests === 1) {
        clock = 5;
        return new Response("{}", { status: 401 });
      }
      clock = 25;
      const response = new Response("{}");
      vi.spyOn(response, "json").mockImplementation(async () => {
        clock = 40;
        return quoteFixture();
      });
      return response;
    }),
  );
  const value = await fetchStockQuote(order);
  expect(value.transport).toEqual({ started_at: 0, received_at: 40, round_trip_ms: 40 });
  expect(requests).toBe(2);
});
it("replays the original economic receipt even if confirmation price differs", async () => {
  document.cookie = "bj_csrf=test; path=/";
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => new Response(JSON.stringify(fillFixture()))),
  );
  expect(await executeStockTrade({ ...attempt, expected_exec_price: "999" })).toEqual(
    fillFixture(),
  );
});
it("rejects invalid local requests before any HTTP call", async () => {
  const fetcher = vi.fn();
  vi.stubGlobal("fetch", fetcher);
  await expect(fetchStockQuote({ ...order, quantity: "1.5" })).rejects.toMatchObject({
    kind: "refused",
  });
  await expect(fetchStockContext("../private")).rejects.toMatchObject({ kind: "refused" });
  await expect(executeStockTrade({ ...attempt, idempotency_key: "bad" })).rejects.toMatchObject({
    kind: "refused",
  });
  expect(fetcher).not.toHaveBeenCalled();
});
it("validates sell-side midpoint, proceeds and half-even cent ties exactly", () => {
  const original = quoteFixture();
  const sale = {
    ...original,
    side: "sell",
    quantity: "1",
    bid: "0.005",
    ask: "0.005",
    exact_mid: "0.005",
    exec_price: "0.005",
    notional: "0.00",
    cash_delta: "0.00",
    cash_after: original.cash_before,
    held_before: "1",
    held_after: "0",
  };
  expect(isStockTradeQuote(sale)).toBe(true);
  expect(
    isStockTradeQuote({ ...sale, cash_delta: "0.01", cash_after: "10000.01", notional: "0.01" }),
  ).toBe(false);
  const buy = { ...sale, side: "buy", held_before: "0", held_after: "1" };
  expect(isStockTradeQuote(buy)).toBe(false);
});
it("does not accept a server max above cash or remaining whole-share room", () => {
  const c = contextFixture();
  c.buy_max_quantity = "99";
  expect(isStockContext(c)).toBe(false);
  c.buy_max_quantity = "98";
  c.held_quantity = "999999999999";
  expect(isStockContext(c)).toBe(false);
});
