import { afterEach, expect, it, vi } from "vitest";
import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { useStockTrade, projectStockContext } from "./useStockTrade";
import type { TimedStockContext, StockTradeQuote } from "@/api/stockTrades";
import { contextFixture, fillFixture, quoteFixture } from "@/test/stockTradeFixtures";

const clients: QueryClient[] = [];
function setup() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: Infinity } },
  });
  clients.push(client);
  client.setQueryData(["me"], { email: "first@example.test", cash_usd: "10000" });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return {
    client,
    wrapper,
    ...renderHook(({ symbol }: { symbol: string }) => useStockTrade(symbol), {
      wrapper,
      initialProps: { symbol: "AAPL" },
    }),
  };
}
afterEach(() => {
  cleanup();
  clients.forEach((c) => c.clear());
  clients.length = 0;
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.useRealTimers();
  document.cookie = "bj_csrf=; Max-Age=0; path=/";
});

it("keeps one frozen attempt after response loss and resolves it explicitly after market closure", async () => {
  document.cookie = "bj_csrf=test; path=/";
  const bodies: unknown[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const path = String(input);
      if (path.endsWith("/me"))
        return new Response(JSON.stringify({ email: "first@example.test", cash_usd: "9796" }));
      if (path.endsWith("/context")) return new Response(JSON.stringify(contextFixture()));
      if (path.endsWith("/quote")) return new Response(JSON.stringify(quoteFixture()));
      bodies.push(JSON.parse(init!.body as string));
      if (bodies.length === 1) throw new Error("response lost");
      return new Response(JSON.stringify(fillFixture()));
    }),
  );
  const { client, result } = setup();
  await waitFor(() => expect(result.current.context?.execution_enabled).toBe(true));
  act(() => result.current.setQuantity("2"));
  await act(async () => {
    await result.current.preview();
  });
  await waitFor(() => expect(result.current.phase).toBe("preview"));
  await act(async () => {
    await result.current.confirm();
  });
  expect(result.current.phase).toBe("unknown");
  const closed = contextFixture();
  closed.execution_enabled = false;
  closed.execution_reason = "market_closed";
  closed.valid_until = null;
  closed.quote = null;
  closed.buy_max_quantity = "0";
  closed.session.state = "closed";
  act(() =>
    client.setQueryData(["stockContext", "first@example.test", "AAPL"], {
      ...closed,
      transport: {
        started_at: performance.now(),
        received_at: performance.now(),
        round_trip_ms: 0,
      },
    }),
  );
  act(() => result.current.setQuantity("3"));
  expect(result.current.quantity).toBe("2");
  await act(async () => {
    await result.current.checkResult();
  });
  expect(result.current.phase).toBe("filled");
  expect(bodies).toHaveLength(2);
  expect(bodies[1]).toEqual(bodies[0]);
});

const timed = (data = contextFixture()): TimedStockContext => ({
  ...data,
  transport: { started_at: performance.now(), received_at: performance.now(), round_trip_ms: 0 },
});
function mockStockHttp(
  options: {
    quote?: () => Promise<Response> | Response;
    trade?: () => Promise<Response> | Response;
    context?: () => Promise<Response> | Response;
  } = {},
) {
  document.cookie = "bj_csrf=test; path=/";
  const calls: { path: string; body: Record<string, unknown> | null }[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const path = String(input);
      calls.push({ path, body: init?.body ? JSON.parse(init.body as string) : null });
      if (path.endsWith("/me"))
        return new Response(JSON.stringify({ email: "first@example.test", cash_usd: "10000" }));
      if (path.endsWith("/context"))
        return options.context?.() ?? new Response(JSON.stringify(contextFixture()));
      if (path.endsWith("/quote"))
        return options.quote?.() ?? new Response(JSON.stringify(quoteFixture()));
      return options.trade?.() ?? new Response(JSON.stringify(fillFixture()));
    }),
  );
  return calls;
}
async function readyPreview(result: ReturnType<typeof setup>["result"]) {
  await waitFor(() => expect(result.current.context?.execution_enabled).toBe(true));
  act(() => result.current.setQuantity("2"));
  await act(async () => {
    await result.current.preview();
  });
  expect(result.current.phase).toBe("preview");
}

it("shortcuts edit whole drafts only and pending duplicate confirmation cannot place twice", async () => {
  let finish!: (value: Response) => void;
  const calls = mockStockHttp({
    trade: () =>
      new Promise((r) => {
        finish = r;
      }),
  });
  const { result } = setup();
  await waitFor(() => expect(result.current.context?.execution_enabled).toBe(true));
  act(() => result.current.buyMax());
  expect(result.current.quantity).toBe("98");
  expect(calls.some((c) => c.path === "/api/v1/stock-trades")).toBe(false);
  await readyPreview(result);
  let pending!: Promise<void>;
  act(() => {
    pending = result.current.confirm();
  });
  await waitFor(() => expect(result.current.phase).toBe("submitting"));
  act(() => {
    result.current.setQuantity("8");
    result.current.setSide("sell");
    result.current.tradeAgain();
  });
  await act(async () => {
    await result.current.confirm();
    await result.current.checkResult();
  });
  expect(result.current.quantity).toBe("2");
  expect(result.current.side).toBe("buy");
  expect(calls.filter((c) => c.path === "/api/v1/stock-trades")).toHaveLength(1);
  await act(async () => {
    finish(new Response(JSON.stringify(fillFixture())));
    await pending;
  });
  expect(result.current.phase).toBe("filled");
  expect(result.current.fill?.cash_after).toBe("9796.00000000");
  act(() => result.current.tradeAgain());
  expect(result.current.phase).toBe("draft");
  expect(result.current.quantity).toBe("");
});

it("retains quantity but removes cached preview and estimates exactly at expiry", async () => {
  let clock = 0;
  vi.spyOn(performance, "now").mockImplementation(() => clock);
  mockStockHttp();
  const { result, client } = setup();
  await readyPreview(result);
  clock = 50_000;
  act(() => window.dispatchEvent(new Event("focus")));
  expect(result.current.phase).toBe("draft");
  expect(result.current.quantity).toBe("2");
  expect(result.current.quote).toBeNull();
  expect(result.current.canConfirm).toBe(false);
  expect(result.current.context?.quote).toBeNull();
  expect(
    client.getQueryData<{ quote: unknown }>(["stockTradeState", "first@example.test"])?.quote,
  ).toBeNull();
  expect(
    client.getQueryData<TimedStockContext>(["stockContext", "first@example.test", "AAPL"])?.quote,
  ).toBeNull();
});

it("known no-fill preserves draft and requires another server preview", async () => {
  const calls = mockStockHttp({
    trade: () =>
      new Response(JSON.stringify({ detail: { code: "insufficient_cash" } }), { status: 422 }),
  });
  const { result } = setup();
  await readyPreview(result);
  await act(async () => {
    await result.current.confirm();
  });
  expect(result.current.phase).toBe("draft");
  expect(result.current.quantity).toBe("2");
  expect(result.current.attempt).toBeNull();
  expect(result.current.error).toBe("insufficient_cash");
  await act(async () => {
    await result.current.confirm();
  });
  expect(calls.filter((c) => c.path === "/api/v1/stock-trades")).toHaveLength(1);
});

it("replacement server values need another explicit confirmation and do not autoaccept", async () => {
  let attempts = 0;
  const replacement: StockTradeQuote = {
    ...quoteFixture(),
    ask: "103",
    exact_mid: "101.5",
    exec_price: "103",
    notional: "206",
    cash_delta: "-206",
    cash_after: "9794",
  };
  const calls = mockStockHttp({
    trade: () => {
      attempts++;
      if (attempts === 2)
        return new Response(
          JSON.stringify({
            ...fillFixture(),
            ask: "103",
            exact_mid: "101.5",
            exec_price: "103",
            notional: "206",
            cash_delta: "-206",
            cash_after: "9794",
          }),
        );
      return new Response(
        JSON.stringify({
          detail: {
            code: "price_changed",
            previous_exec_price: "102",
            previous_cash_delta: "-204",
            exec_price_change: "1",
            cash_delta_change: "-2",
            quote: replacement,
          },
        }),
        { status: 409 },
      );
    },
  });
  const { result } = setup();
  await readyPreview(result);
  await act(async () => {
    await result.current.confirm();
  });
  expect(result.current.phase).toBe("preview");
  expect(attempts).toBe(1);
  expect(result.current.quote?.exec_price).toBe("103");
  expect(result.current.replacement?.previous_exec_price).toBe("102");
  expect(result.current.attempt).toBeNull();
  await act(async () => {
    await result.current.confirm();
  });
  expect(attempts).toBe(2);
  expect(result.current.phase).toBe("filled");
  expect(result.current.fill?.cash_after).toBe("9794");
  expect(calls.filter((c) => c.path === "/api/v1/stock-trades")[1].body?.expected_exec_price).toBe(
    "103",
  );
});

it("discards a committed late old-account reply and clears every private attempt on switch", async () => {
  let finish!: (value: Response) => void;
  mockStockHttp({
    trade: () =>
      new Promise((r) => {
        finish = r;
      }),
  });
  const { result, client } = setup();
  await readyPreview(result);
  let pending!: Promise<void>;
  act(() => {
    pending = result.current.confirm();
  });
  await waitFor(() => expect(result.current.phase).toBe("submitting"));
  act(() => client.setQueryData(["me"], { email: "second@example.test", cash_usd: "10000" }));
  await waitFor(() => expect(result.current.phase).toBe("draft"));
  await act(async () => {
    finish(new Response(JSON.stringify(fillFixture())));
    await pending;
  });
  expect(result.current.fill).toBeNull();
  expect(result.current.quantity).toBe("");
  expect(client.getQueryData(["stockTradeState", "first@example.test"])).toBeUndefined();
  expect(
    client.getQueryData<{ fill: unknown }>(["stockTradeState", "second@example.test"])?.fill,
  ).toBeNull();
});

it("route changes cannot abandon or edit an unresolved original order", async () => {
  const calls = mockStockHttp({
    trade: () => {
      throw new Error("lost");
    },
  });
  const { result, rerender } = setup();
  await readyPreview(result);
  await act(async () => {
    await result.current.confirm();
  });
  expect(result.current.phase).toBe("unknown");
  rerender({ symbol: "MSFT" });
  expect(result.current.symbol).toBe("AAPL");
  expect(result.current.quantity).toBe("2");
  act(() => {
    result.current.tradeAgain();
    result.current.buyMax();
    result.current.sellAll();
  });
  await act(async () => {
    await result.current.preview();
    await result.current.confirm();
  });
  expect(result.current.phase).toBe("unknown");
  expect(calls.filter((c) => c.path === "/api/v1/stock-trades")).toHaveLength(1);
});

it("newer safety epochs purge old previews and delayed lower epochs cannot restore the cache", async () => {
  mockStockHttp();
  const { result, client } = setup();
  await readyPreview(result);
  const newer = contextFixture();
  newer.observed_at = "2026-11-10T15:00:11Z";
  newer.authority!.safety_epoch = 3;
  act(() => client.setQueryData(["stockContext", "first@example.test", "AAPL"], timed(newer)));
  expect(result.current.quote).toBeNull();
  expect(result.current.phase).toBe("draft");
  const older = contextFixture();
  older.observed_at = "2026-11-10T15:00:12Z";
  act(() => client.setQueryData(["stockContext", "first@example.test", "AAPL"], timed(older)));
  expect(result.current.context?.authority?.safety_epoch).toBe(3);
  expect(
    client.getQueryData<TimedStockContext>(["stockContext", "first@example.test", "AAPL"])
      ?.authority?.safety_epoch,
  ).toBe(3);
});

it.each([
  ["status", 55_000, "status_unavailable"],
  ["action", 3_000, "action_unavailable"],
])(
  "independent %s expiry removes executable estimates without opening anything",
  (_kind, elapsed, reason) => {
    const data = timed();
    data.transport = { started_at: 0, received_at: 0, round_trip_ms: 0 };
    data.valid_until = "2026-11-10T15:01:05Z";
    if (_kind === "action") {
      data.action.valid_until = "2026-11-10T15:00:13Z";
      data.valid_until = data.action.valid_until;
    }
    const before = projectStockContext(data, elapsed - 1);
    expect(before.execution_enabled).toBe(true);
    const after = projectStockContext(data, elapsed);
    expect(after.execution_enabled).toBe(false);
    expect(after.execution_reason).toBe(reason);
    expect(after.quote).toBeNull();
  },
);

it("closure interrupts preview but a new opening never submits or restores that preview", async () => {
  const calls = mockStockHttp();
  const { result, client } = setup();
  await readyPreview(result);
  const closed = contextFixture();
  closed.execution_enabled = false;
  closed.execution_reason = "market_closed";
  closed.valid_until = null;
  closed.quote = null;
  closed.buy_max_quantity = "0";
  closed.session.state = "closed";
  closed.observed_at = "2026-11-10T15:00:11Z";
  act(() => client.setQueryData(["stockContext", "first@example.test", "AAPL"], timed(closed)));
  expect(result.current.phase).toBe("draft");
  expect(result.current.quantity).toBe("2");
  expect(result.current.interrupted).toBe(true);
  const reopened = contextFixture();
  reopened.observed_at = "2026-11-10T15:00:12Z";
  act(() => client.setQueryData(["stockContext", "first@example.test", "AAPL"], timed(reopened)));
  expect(result.current.context?.execution_enabled).toBe(true);
  expect(result.current.quote).toBeNull();
  expect(result.current.canConfirm).toBe(false);
  await act(async () => {
    await result.current.confirm();
  });
  expect(calls.filter((c) => c.path === "/api/v1/stock-trades")).toHaveLength(0);
  // A body observed before the closure cannot masquerade as the new preview.
  await act(async () => {
    await result.current.preview();
  });
  expect(result.current.quote).toBeNull();
  expect(result.current.phase).toBe("draft");
});

it("late preview responses cannot replace an edited whole-share draft", async () => {
  let finish!: (value: Response) => void;
  mockStockHttp({
    quote: () =>
      new Promise((r) => {
        finish = r;
      }),
  });
  const { result } = setup();
  await waitFor(() => expect(result.current.context?.execution_enabled).toBe(true));
  act(() => result.current.setQuantity("2"));
  let pending!: Promise<void>;
  act(() => {
    pending = result.current.preview();
  });
  await waitFor(() => expect(result.current.phase).toBe("loading_preview"));
  act(() => result.current.setQuantity("3"));
  await act(async () => {
    finish(new Response(JSON.stringify(quoteFixture())));
    await pending;
  });
  expect(result.current.quantity).toBe("3");
  expect(result.current.quote).toBeNull();
  expect(result.current.phase).toBe("draft");
});

it("same-account logout/login invalidates a delayed response despite identical email", async () => {
  let finish!: (value: Response) => void;
  mockStockHttp({
    trade: () =>
      new Promise((r) => {
        finish = r;
      }),
  });
  const { result, client } = setup();
  await readyPreview(result);
  let pending!: Promise<void>;
  act(() => {
    pending = result.current.confirm();
  });
  await waitFor(() => expect(result.current.phase).toBe("submitting"));
  act(() => {
    client.setQueryData(["me"], null);
    client.setQueryData(["me"], { email: "first@example.test", cash_usd: "10000" });
  });
  await act(async () => {
    finish(new Response(JSON.stringify(fillFixture())));
    await pending;
  });
  expect(result.current.phase).toBe("draft");
  expect(result.current.fill).toBeNull();
  expect(result.current.quantity).toBe("");
});

it("expired replacement responses clear estimates while retaining the known no-fill draft", async () => {
  let clock = 0;
  vi.spyOn(performance, "now").mockImplementation(() => clock);
  const replacement = {
    ...quoteFixture(),
    ask: "103",
    exact_mid: "101.5",
    exec_price: "103",
    notional: "206",
    cash_delta: "-206",
    cash_after: "9794",
  };
  mockStockHttp({
    trade: () => {
      clock = 50_000;
      return new Response(
        JSON.stringify({
          detail: {
            code: "price_changed",
            previous_exec_price: "102",
            previous_cash_delta: "-204",
            exec_price_change: "1",
            cash_delta_change: "-2",
            quote: replacement,
          },
        }),
        { status: 409 },
      );
    },
  });
  const { result } = setup();
  await readyPreview(result);
  await act(async () => {
    await result.current.confirm();
  });
  expect(result.current.phase).toBe("draft");
  expect(result.current.attempt).toBeNull();
  expect(result.current.quantity).toBe("2");
  expect(result.current.quote).toBeNull();
  expect(result.current.replacement).toBeNull();
});

it("an unknown attempt survives unmount and remount without creating a new key", async () => {
  const calls = mockStockHttp({
    trade: () => {
      throw new Error("lost");
    },
  });
  const first = setup();
  await readyPreview(first.result);
  await act(async () => {
    await first.result.current.confirm();
  });
  const body = calls.find((c) => c.path === "/api/v1/stock-trades")!.body;
  first.unmount();
  const second = renderHook(() => useStockTrade("AAPL"), { wrapper: first.wrapper });
  expect(second.result.current.phase).toBe("unknown");
  expect(second.result.current.attempt?.body).toEqual(body);
  await act(async () => {
    await second.result.current.checkResult();
  });
  expect(calls.filter((c) => c.path === "/api/v1/stock-trades").map((c) => c.body)).toEqual([
    body,
    body,
  ]);
  second.unmount();
});

it("the exact deadline timer purges query cache and preview without waiting for a display tick", async () => {
  vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout", "setInterval", "clearInterval"] });
  let clock = 0;
  vi.spyOn(performance, "now").mockImplementation(() => clock);
  const c = contextFixture();
  c.valid_until = "2026-11-10T15:00:10.125Z";
  const q = quoteFixture();
  q.valid_until = c.valid_until;
  mockStockHttp({
    context: () => new Response(JSON.stringify(c)),
    quote: () => new Response(JSON.stringify(q)),
  });
  const { result, client } = setup();
  await act(async () => {
    for (let i = 0; i < 8; i++) await vi.advanceTimersByTimeAsync(0);
  });
  expect(result.current.context?.execution_enabled).toBe(true);
  act(() => result.current.setQuantity("2"));
  await act(async () => {
    const p = result.current.preview();
    for (let i = 0; i < 8; i++) await vi.advanceTimersByTimeAsync(0);
    await p;
  });
  expect(result.current.phase).toBe("preview");
  clock = 124;
  await act(async () => {
    await vi.advanceTimersByTimeAsync(124);
  });
  expect(result.current.canConfirm).toBe(true);
  clock = 125;
  await act(async () => {
    await vi.advanceTimersByTimeAsync(1);
  });
  expect(result.current.phase).toBe("draft");
  expect(result.current.quantity).toBe("2");
  expect(
    client.getQueryData<TimedStockContext>(["stockContext", "first@example.test", "AAPL"])?.quote,
  ).toBeNull();
  expect(
    client.getQueryData<{ quote: unknown }>(["stockTradeState", "first@example.test"])?.quote,
  ).toBeNull();
});

it("a replaced context query owner rejects a late preview even with matching epochs", async () => {
  let finish!: (value: Response) => void;
  mockStockHttp({
    quote: () =>
      new Promise((r) => {
        finish = r;
      }),
  });
  const { result, client } = setup();
  await waitFor(() => expect(result.current.context?.execution_enabled).toBe(true));
  act(() => result.current.setQuantity("2"));
  let pending!: Promise<void>;
  act(() => {
    pending = result.current.preview();
  });
  await waitFor(() => expect(result.current.phase).toBe("loading_preview"));
  act(() => {
    client.removeQueries({ queryKey: ["stockContext", "first@example.test", "AAPL"], exact: true });
    client.setQueryData(["stockContext", "first@example.test", "AAPL"], timed());
  });
  await act(async () => {
    finish(new Response(JSON.stringify(quoteFixture())));
    await pending;
  });
  expect(result.current.quote).toBeNull();
  expect(result.current.canConfirm).toBe(false);
  expect(result.current.phase).toBe("draft");
});

it("full quote RTT can exhaust eligibility before any preview enters cache", async () => {
  let clock = 0;
  vi.spyOn(performance, "now").mockImplementation(() => clock);
  mockStockHttp({
    quote: () => {
      clock = 50_000;
      return new Response(JSON.stringify(quoteFixture()));
    },
  });
  const { result, client } = setup();
  await waitFor(() => expect(result.current.context?.execution_enabled).toBe(true));
  act(() => result.current.setQuantity("2"));
  await act(async () => {
    await result.current.preview();
  });
  expect(result.current.phase).toBe("draft");
  expect(result.current.quote).toBeNull();
  expect(
    client.getQueryData<{ quote: unknown }>(["stockTradeState", "first@example.test"])?.quote,
  ).toBeNull();
});

it("read-only errors do not publish foreign or unverified context", async () => {
  mockStockHttp({ context: () => new Response("{}") });
  const { result } = setup();
  await waitFor(() => expect(result.current.contextError).toBe(true));
  expect(result.current.context).toBeUndefined();
  act(() => result.current.setQuantity("2"));
  await act(async () => {
    await result.current.preview();
  });
  expect(result.current.quote).toBeNull();
  expect(result.current.canPreview).toBe(false);
});

it("observing a different provider identity removes the previous executable preview", async () => {
  mockStockHttp();
  const { result, client } = setup();
  await readyPreview(result);
  const changed = contextFixture();
  changed.provider_asset_id = "replacement-aapl";
  act(() => client.setQueryData(["stockContext", "first@example.test", "AAPL"], timed(changed)));
  expect(result.current.phase).toBe("draft");
  expect(result.current.context?.execution_enabled).toBe(false);
  expect(result.current.context?.quote).toBeNull();
  expect(result.current.quote).toBeNull();
  expect(result.current.quantity).toBe("2");
  expect(
    client.getQueryData<TimedStockContext>(["stockContext", "first@example.test", "AAPL"])?.quote,
  ).toBeNull();
});
