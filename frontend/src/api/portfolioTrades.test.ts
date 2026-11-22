import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { executeTrade, fetchHolding, fetchQuote, isFill, isHolding, isQuote } from "./trades";
import {
  executeStockTrade,
  fetchStockContext,
  fetchStockQuote,
  isStockAttempt,
  isStockFill,
  isStockTradeQuote,
} from "./stockTrades";
import { contextFixture, fillFixture, quoteFixture } from "@/test/stockTradeFixtures";

const root = "9007199254740993";
const other = "9007199254740994";
const key = "00000000-0000-0000-0000-000000000001";
const order = { symbol: "BTC", side: "buy", amount_usd: "100.00" } as const;
const stockOrder = { symbol: "AAPL", side: "buy", quantity: "2" } as const;
const attempt = {
  ...stockOrder,
  portfolio_id: root,
  expected_exec_price: "102",
  idempotency_key: key,
};
const quote = () => ({
  portfolio_id: root,
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
});
const fill = () => {
  const q = quote();
  return {
    portfolio_id: root,
    trade_id: 7,
    created_at: "2026-10-28T10:00:01Z",
    symbol: q.symbol,
    side: q.side,
    input_kind: q.input_kind,
    input_value: q.input_value,
    mid: q.mid,
    as_of: q.as_of,
    exec_price: q.exec_price,
    quantity: q.quantity,
    notional: q.notional,
    fee: q.fee,
    cash_delta: q.cash_delta,
    cash_after: q.cash_after,
  };
};
const stockQuote = () => ({ ...quoteFixture(), portfolio_id: root });
const stockFill = () => ({ ...fillFixture(), portfolio_id: root });
const stockContext = () => ({ ...contextFixture(), portfolio_id: root });
const reply = (value: unknown, status = 200) => new Response(JSON.stringify(value), { status });
beforeEach(() => {
  document.cookie = "bj_csrf=test; path=/";
});
afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  document.cookie = "bj_csrf=; Max-Age=0; path=/";
});

it("sends exact crypto bodies on explicit bigint root paths with common CSRF transport", async () => {
  const fetcher = vi.fn(async (input: RequestInfo | URL) =>
    reply(
      String(input).endsWith("/quote")
        ? quote()
        : String(input).includes("/holdings/")
          ? { portfolio_id: root, symbol: "BTC", quantity: "0.5" }
          : fill(),
    ),
  );
  vi.stubGlobal("fetch", fetcher);
  const signal = new AbortController().signal;
  expect(await fetchQuote(root, order, signal)).toEqual(quote());
  expect(await executeTrade(root, order, "100000.00", key)).toEqual(fill());
  expect(await fetchHolding(root, "BTC", signal)).toEqual({
    portfolio_id: root,
    symbol: "BTC",
    quantity: "0.5",
  });
  expect(fetcher.mock.calls.map(([path]) => path)).toEqual([
    `/api/v2/portfolios/${root}/trades/quote`,
    `/api/v2/portfolios/${root}/trades`,
    `/api/v2/portfolios/${root}/holdings/BTC`,
  ]);
  const calls = fetcher.mock.calls as unknown as [string, RequestInit][];
  expect(JSON.parse(calls[0][1].body as string)).toEqual(order);
  expect(JSON.parse(calls[1][1].body as string)).toEqual({
    ...order,
    expected_mid: "100000.00",
    idempotency_key: key,
  });
  expect(new Headers(calls[1][1].headers).get("X-CSRF-Token")).toBe("test");
  expect(calls[0][1].signal).toBe(signal);
  expect(calls.every(([, init]) => init.cache === "no-store")).toBe(true);
});

it("keeps immutable stock attempt root out of the unchanged server order body", async () => {
  const fetcher = vi.fn(async (input: RequestInfo | URL) =>
    reply(
      String(input).endsWith("/context")
        ? stockContext()
        : String(input).endsWith("/quote")
          ? stockQuote()
          : stockFill(),
    ),
  );
  vi.stubGlobal("fetch", fetcher);
  expect((await fetchStockQuote(root, stockOrder)).portfolio_id).toBe(root);
  expect((await fetchStockContext(root, "AAPL")).portfolio_id).toBe(root);
  expect(await executeStockTrade(root, attempt)).toEqual(stockFill());
  const calls = fetcher.mock.calls as unknown as [string, RequestInit][];
  expect(calls.map(([path]) => path)).toEqual([
    `/api/v2/portfolios/${root}/stock-trades/quote`,
    `/api/v2/portfolios/${root}/stock-trades/AAPL/context`,
    `/api/v2/portfolios/${root}/stock-trades`,
  ]);
  expect(JSON.parse(calls[2][1].body as string)).toEqual({
    ...stockOrder,
    expected_exec_price: "102",
    idempotency_key: key,
  });
  expect(isStockAttempt(attempt)).toBe(true);
  expect(isStockAttempt({ ...attempt, portfolio_id: undefined })).toBe(false);
});

const requests = [
  (id: string) => fetchQuote(id, order),
  (id: string) => executeTrade(id, order, "100000.00", key),
  (id: string) => fetchHolding(id, "BTC"),
  (id: string) => fetchStockQuote(id, stockOrder),
  (id: string) => fetchStockContext(id, "AAPL"),
  (id: string) => executeStockTrade(id, { ...attempt, portfolio_id: id }),
];
it.each([
  undefined,
  null,
  "",
  "0",
  "-1",
  "01",
  "1/../../2",
  "%2f",
  "1?owner=2",
  "9223372036854775808",
  1,
])("refuses invalid root %s before any network request", async (id) => {
  const fetcher = vi.fn();
  vi.stubGlobal("fetch", fetcher);
  for (const request of requests) await expect(request(id as string)).rejects.toThrow();
  expect(fetcher).not.toHaveBeenCalled();
});
it("refuses an attempt against a new active root before sending it", async () => {
  const fetcher = vi.fn();
  vi.stubGlobal("fetch", fetcher);
  await expect(executeStockTrade(other, attempt)).rejects.toThrow();
  expect(fetcher).not.toHaveBeenCalled();
});
it.each([undefined, other, 1, "01", "9223372036854775808"])(
  "rejects missing, foreign or noncanonical root on every successful financial response %s",
  async (id) => {
    for (const [request, value] of [
      [() => fetchQuote(root, order), quote()],
      [() => executeTrade(root, order, "100000.00", key), fill()],
      [() => fetchHolding(root, "BTC"), { portfolio_id: root, symbol: "BTC", quantity: "0.5" }],
      [() => fetchStockQuote(root, stockOrder), stockQuote()],
      [() => fetchStockContext(root, "AAPL"), stockContext()],
      [() => executeStockTrade(root, attempt), stockFill()],
    ] as const) {
      vi.stubGlobal(
        "fetch",
        vi.fn(async () => reply({ ...value, portfolio_id: id })),
      );
      await expect(request()).rejects.toThrow();
    }
  },
);
it("requires stored root identity in crypto and stock parser contracts", () => {
  for (const [guard, value] of [
    [isQuote, quote()],
    [isFill, fill()],
    [isHolding, { portfolio_id: root, symbol: "BTC", quantity: "0" }],
    [isStockTradeQuote, stockQuote()],
    [isStockFill, stockFill()],
  ] as const) {
    expect(guard(value)).toBe(true);
    expect(guard({ ...value, portfolio_id: undefined })).toBe(false);
  }
});
it.each([404, 409])("preserves crypto unavailable/version errors %s", async (status) => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () =>
      reply(
        { detail: { code: status === 404 ? "portfolio_unavailable" : "portfolio_required" } },
        status,
      ),
    ),
  );
  await expect(fetchQuote(root, order)).rejects.toMatchObject({ status });
});
it("refuses a wrong-root stock reprice rather than attaching it to the current attempt", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () =>
      reply(
        {
          detail: {
            code: "price_changed",
            previous_exec_price: "101",
            previous_cash_delta: "-202",
            exec_price_change: "1",
            cash_delta_change: "-2",
            quote: { ...stockQuote(), portfolio_id: other },
          },
        },
        409,
      ),
    ),
  );
  await expect(
    executeStockTrade(root, { ...attempt, expected_exec_price: "101" }),
  ).rejects.toMatchObject({ kind: "unknown", replacement: null });
});

it.each([undefined, other])(
  "rejects crypto repricing with missing or crossed root %s",
  async (id) => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        reply(
          {
            detail: {
              code: "price_changed",
              quote: { ...quote(), portfolio_id: id },
            },
          },
          409,
        ),
      ),
    );
    await expect(executeTrade(root, order, "99999", key)).rejects.toThrow(
      "Unexpected trade repricing response",
    );
  },
);
it("preserves validated same-root repricing for renewed confirmation", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => reply({ detail: { code: "price_changed", quote: quote() } }, 409)),
  );
  await expect(executeTrade(root, order, "99999", key)).rejects.toMatchObject({
    status: 409,
    code: "price_changed",
    detail: { quote: quote() },
  });
  vi.stubGlobal(
    "fetch",
    vi.fn(async () =>
      reply(
        {
          detail: {
            code: "price_changed",
            previous_exec_price: "101",
            previous_cash_delta: "-202",
            exec_price_change: "1",
            cash_delta_change: "-2",
            quote: stockQuote(),
          },
        },
        409,
      ),
    ),
  );
  await expect(
    executeStockTrade(root, { ...attempt, expected_exec_price: "101" }),
  ).rejects.toMatchObject({ kind: "reprice", replacement: { quote: { portfolio_id: root } } });
});
it.each([
  { ...order, amount_usd: 100 },
  { ...order, quantity: "1" },
  { symbol: "BTC", side: "buy" },
  { ...order, amount_usd: "0" },
  { ...order, amount_usd: "1e2" },
  { ...order, side: "hold" },
  { ...order, portfolio_id: other },
])("refuses malformed crypto order before network %j", async (body) => {
  const fetcher = vi.fn();
  vi.stubGlobal("fetch", fetcher);
  await expect(fetchQuote(root, body as typeof order)).rejects.toThrow();
  await expect(executeTrade(root, body as typeof order, "100000", key)).rejects.toThrow();
  expect(fetcher).not.toHaveBeenCalled();
});
it.each(["quote", "fill", "holding"])(
  "rejects crossed crypto symbol in %s response",
  async (which) => {
    const body =
      which === "quote"
        ? quote()
        : which === "fill"
          ? fill()
          : { portfolio_id: root, symbol: "BTC", quantity: "1" };
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => reply({ ...body, symbol: "ETH" })),
    );
    const request =
      which === "quote"
        ? fetchQuote(root, order)
        : which === "fill"
          ? executeTrade(root, order, "100000", key)
          : fetchHolding(root, "BTC");
    await expect(request).rejects.toThrow();
  },
);
it("uses the exact original receipt values and never overlays a new target", async () => {
  const saved = { ...fill(), cash_after: "17.00" };
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => reply(saved)),
  );
  expect(await executeTrade(root, order, "99999", key)).toEqual(saved);
});
it("does not publish financial results after cancellation", async () => {
  const controller = new AbortController();
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => {
      controller.abort();
      return reply(quote());
    }),
  );
  await expect(fetchQuote(root, order, controller.signal)).rejects.toMatchObject({
    name: "AbortError",
  });
});
