import { afterEach, expect, it, vi } from "vitest";
import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider, focusManager, useQuery } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { useEventHistory } from "./useEventHistory";
import type { EventDividend } from "@/api/eventHistory";
import { useTrade } from "./useTrade";
import { useStockTrade } from "./useStockTrade";
import { contextFixture, quoteFixture, fillFixture } from "@/test/stockTradeFixtures";

const clients: QueryClient[] = [];
function setup(email: string | null = "first@example.test") {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: Infinity } },
  });
  clients.push(client);
  client.setQueryData(["me"], email === null ? null : { email, cash_usd: "10000.00" });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return { client, wrapper, ...renderHook(() => useEventHistory(), { wrapper }) };
}
afterEach(() => {
  cleanup();
  clients.forEach((client) => client.clear());
  clients.length = 0;
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  focusManager.setFocused(undefined);
  document.cookie = "bj_csrf=; Max-Age=0; path=/";
});

const item = (id: string): EventDividend => ({
  kind: "dividend",
  id: `dividend:${id}`,
  payment_reference: `dividend:${id}`,
  recorded_at: "2026-11-12T15:00:00.000001Z",
  credited_at: "2026-11-12T15:00:00.000001Z",
  asset_type: "stock",
  symbol: "AAPL",
  name: "Apple",
  cash_delta: "1.00",
  credited_amount: "1.00",
  eligible_quantity: "1",
  rate: "1.00",
  cutoff: "2026-11-10T14:30:00Z",
  ex_date: "2026-11-10",
  record_date: "2026-11-11",
  payable_date: "2026-11-12",
});
const cursor = (id: string) =>
  btoa(
    JSON.stringify({
      v: 2,
      recorded_at: "2026-11-12T15:00:00.000001Z",
      kind_rank: 3,
      source_id: id,
    }),
  )
    .replace(/=/g, "")
    .replace(/\+/g, "-")
    .replace(/\//g, "_");
const page = (ids: string[], next: string | null = null) =>
  new Response(JSON.stringify({ items: ids.map(item), next_cursor: next }));
function pending() {
  let resolve!: (response: Response) => void;
  const promise = new Promise<Response>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}
function historyTransport(fetch: typeof globalThis.fetch) {
  vi.stubGlobal("fetch", (input: RequestInfo | URL, init?: RequestInit) =>
    String(input) === "/api/v1/me"
      ? Promise.resolve(new Response(JSON.stringify(clients.at(-1)?.getQueryData(["me"]))))
      : fetch(input, init),
  );
}

it("does not fetch or expose private History while logged out", async () => {
  const fetch = vi.fn(() =>
    Promise.resolve(new Response(JSON.stringify({ items: [], next_cursor: null }))),
  );
  historyTransport(fetch);
  const { result } = setup(null);
  await act(async () => {
    await Promise.resolve();
  });
  expect(fetch).not.toHaveBeenCalled();
  expect(result.current.data).toBeUndefined();
});

it("loads exact server order under an owner and epoch key without local money", async () => {
  const fetch = vi.fn((input: RequestInfo | URL) => {
    void input;
    return Promise.resolve(page(["3", "2"]));
  });
  historyTransport(fetch);
  const { result, client } = setup();
  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  expect(result.current.data?.pages[0].items.map((event) => event.id)).toEqual([
    "dividend:3",
    "dividend:2",
  ]);
  expect(fetch.mock.calls[0]?.[0]).toBe("/api/v1/history");
  expect(
    client
      .getQueryCache()
      .findAll({ queryKey: ["eventHistory"] })
      .map((query) => query.queryKey),
  ).toEqual([["eventHistory", "first@example.test", 0]]);
  expect(client.getQueryData(["me"])).toEqual({
    email: "first@example.test",
    cash_usd: "10000.00",
  });
});

it.each([null, "second@example.test"])(
  "immediately hides and removes old accepted pages on auth change to %s",
  async (email) => {
    historyTransport(vi.fn(() => Promise.resolve(page(["3"]))));
    const { result, client } = setup();
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    act(() => client.setQueryData(["me"], email === null ? null : { email }));
    expect(client.getQueryData(["eventHistory", "first@example.test", 0])).toBeUndefined();
    expect(result.current.data).toBeUndefined();
  },
);

it.each([null, "second@example.test"])(
  "drops late old-owner fulfillment after auth change to %s",
  async (email) => {
    const old = pending();
    const fetch = vi
      .fn()
      .mockReturnValueOnce(old.promise)
      .mockResolvedValue(page(["9"]));
    historyTransport(fetch);
    const { result, client } = setup();
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
    act(() => client.setQueryData(["me"], email === null ? null : { email }));
    await act(async () => {
      old.resolve(page(["3"]));
    });
    expect(client.getQueryData(["eventHistory", "first@example.test", 0])).toBeUndefined();
    if (email === null) expect(result.current.data).toBeUndefined();
    else await waitFor(() => expect(result.current.data?.pages[0].items[0].id).toBe("dividend:9"));
  },
);

it("gives same-owner relogin a fresh epoch and cannot revive the old request", async () => {
  const old = pending();
  const fetch = vi
    .fn()
    .mockReturnValueOnce(old.promise)
    .mockResolvedValue(page(["9"]));
  historyTransport(fetch);
  const { result, client } = setup();
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
  act(() => {
    client.setQueryData(["me"], null);
    client.setQueryData(["me"], { email: "first@example.test" });
  });
  await waitFor(() => expect(result.current.data?.pages[0].items[0].id).toBe("dividend:9"));
  await act(async () => {
    old.resolve(page(["3"]));
  });
  expect(result.current.data?.pages[0].items[0].id).toBe("dividend:9");
  expect(client.getQueryData(["eventHistory", "first@example.test", 0])).toBeUndefined();
  expect(client.getQueryData(["eventHistory", "first@example.test", 2])).toBeDefined();
});

it("deduplicates simultaneous appends without cancelling the active page", async () => {
  const next = pending();
  const fetch = vi
    .fn()
    .mockResolvedValueOnce(page(["3"], cursor("3")))
    .mockReturnValueOnce(next.promise);
  historyTransport(fetch);
  const { result } = setup();
  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  let first!: ReturnType<typeof result.current.fetchNextPage>, second!: typeof first;
  act(() => {
    first = result.current.fetchNextPage();
    second = result.current.fetchNextPage();
  });
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
  await act(async () => {
    next.resolve(page(["2"]));
    await Promise.all([first, second]);
  });
  expect(fetch).toHaveBeenCalledTimes(2);
  await waitFor(() =>
    expect(
      result.current.data?.pages.flatMap((body) => body.items.map((event) => event.id)),
    ).toEqual(["dividend:3", "dividend:2"]),
  );
});

it.each([500, "malformed"])("retains accepted pages when append fails with %s", async (failure) => {
  const fetch = vi
    .fn()
    .mockResolvedValueOnce(page(["3"], cursor("3")))
    .mockResolvedValueOnce(
      failure === 500 ? new Response("{}", { status: 500 }) : new Response("{}"),
    );
  historyTransport(fetch);
  const { result } = setup();
  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  await act(async () => {
    await result.current.fetchNextPage();
  });
  await waitFor(() => expect(result.current.isFetchNextPageError).toBe(true));
  expect(result.current.data?.pages[0].items[0].id).toBe("dividend:3");
});

it("retains the whole accepted page chain if a later refresh page is malformed", async () => {
  const fetch = vi
    .fn()
    .mockResolvedValueOnce(page(["3"], cursor("3")))
    .mockResolvedValueOnce(page(["2"]))
    .mockResolvedValueOnce(page(["4"], cursor("4")))
    .mockResolvedValueOnce(new Response("{}"));
  historyTransport(fetch);
  const { result } = setup();
  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  await act(async () => {
    await result.current.fetchNextPage();
  });
  await waitFor(() => expect(result.current.data?.pages).toHaveLength(2));
  await act(async () => {
    const refreshed = await result.current.refetch();
    expect(refreshed.isRefetchError).toBe(true);
  });
  await waitFor(() => expect(result.current.isRefetchError).toBe(true));
  expect(fetch).toHaveBeenCalledTimes(4);
  expect(result.current.data?.pages.flatMap((body) => body.items.map((event) => event.id))).toEqual(
    ["dividend:3", "dividend:2"],
  );
});

it("keeps an initial malformed response empty and allows an explicit retry", async () => {
  const fetch = vi
    .fn()
    .mockResolvedValueOnce(new Response("{}"))
    .mockResolvedValueOnce(page(["3"]));
  historyTransport(fetch);
  const { result } = setup();
  await waitFor(() => expect(result.current.isError).toBe(true));
  expect(result.current.data).toBeUndefined();
  await act(async () => {
    await result.current.refetch();
  });
  await waitFor(() => expect(result.current.data?.pages[0].items[0].id).toBe("dividend:3"));
});

it("logs out only the current owner on final401 without retrying indefinitely", async () => {
  document.cookie = "bj_csrf=test";
  const fetch = vi.fn(() => Promise.resolve(new Response("{}", { status: 401 })));
  vi.stubGlobal("fetch", fetch);
  const { result, client } = setup();
  await waitFor(() => expect(client.getQueryData(["me"])).toBeNull());
  expect(result.current.data).toBeUndefined();
  expect(fetch).toHaveBeenCalledTimes(3);
  document.cookie = "bj_csrf=; Max-Age=0";
});

it("does not log out a new owner when the previous request returns401 late", async () => {
  const old = pending();
  const fetch = vi
    .fn()
    .mockReturnValueOnce(old.promise)
    .mockResolvedValue(page(["9"]));
  historyTransport(fetch);
  const { result, client } = setup();
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
  act(() => client.setQueryData(["me"], { email: "second@example.test" }));
  await waitFor(() => expect(result.current.data?.pages[0].items[0].id).toBe("dividend:9"));
  await act(async () => {
    old.resolve(new Response("{}", { status: 401 }));
  });
  expect(client.getQueryData(["me"])).toEqual({ email: "second@example.test" });
  expect(fetch).toHaveBeenCalledTimes(2);
});

it("invalidates authoritative owner cash and portfolio once for newly accepted event identities", async () => {
  const fetch = vi.fn((input: RequestInfo | URL) =>
    Promise.resolve(
      String(input).endsWith("/me")
        ? new Response(JSON.stringify({ email: "first@example.test", cash_usd: "10001.00" }))
        : page(["3"]),
    ),
  );
  vi.stubGlobal("fetch", fetch);
  const { result, client } = setup();
  const invalidate = vi.spyOn(client, "invalidateQueries");
  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  await waitFor(() =>
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ["portfolio", "first@example.test"] }),
  );
  expect(invalidate).toHaveBeenCalledWith({ queryKey: ["me"], exact: true });
  expect(invalidate).toHaveBeenCalledWith({ queryKey: ["stockContext", "first@example.test"] });
  const count = invalidate.mock.calls.length;
  await act(async () => {
    await result.current.refetch();
  });
  expect(invalidate).toHaveBeenCalledTimes(count);
  expect(client.getQueryData(["me"])).toEqual({
    email: "first@example.test",
    cash_usd: "10001.00",
  });
});

it("cancels a pending pre-event financial response before authoritative replacement", async () => {
  const old = pending();
  let historyIds: string[] = [];
  const fetch = vi.fn((input: RequestInfo | URL) =>
    Promise.resolve(
      String(input) === "/api/v1/me"
        ? new Response(JSON.stringify({ email: "first@example.test", cash_usd: "10001.00" }))
        : page(historyIds),
    ),
  );
  vi.stubGlobal("fetch", fetch);
  const { result, client, wrapper } = setup();
  client.setQueryData(["portfolio", "second@example.test"], { cash: "20000.00" });
  let requests = 0;
  const portfolio = renderHook(
    () =>
      useQuery({
        queryKey: ["portfolio", "first@example.test"],
        retry: false,
        queryFn: async ({ signal }) => {
          const response =
            requests++ === 0
              ? await old.promise
              : new Response(JSON.stringify({ cash: "10001.00" }));
          signal.throwIfAborted();
          return response.json() as Promise<{ cash: string }>;
        },
      }),
    { wrapper },
  );
  await waitFor(() => expect(requests).toBe(1));
  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  historyIds = ["3"];
  await act(async () => {
    await result.current.refetch();
  });
  await waitFor(() => expect(portfolio.result.current.data?.cash).toBe("10001.00"));
  await act(async () => {
    old.resolve(new Response(JSON.stringify({ cash: "10000.00" })));
  });
  expect(portfolio.result.current.data?.cash).toBe("10001.00");
  expect(client.getQueryData(["portfolio", "second@example.test"])).toEqual({ cash: "20000.00" });
  expect(client.getQueryState(["portfolio", "second@example.test"])?.isInvalidated).toBe(false);
});

it("does not invalidate another owner if auth changes while cancellation settles", async () => {
  let ids: string[] = [];
  historyTransport(vi.fn(() => Promise.resolve(page(ids))));
  const { result, client } = setup();
  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  const wait = pending();
  vi.spyOn(client, "cancelQueries").mockImplementation(() => wait.promise.then(() => {}));
  const invalidate = vi.spyOn(client, "invalidateQueries");
  ids = ["3"];
  await act(async () => {
    await result.current.refetch();
  });
  ids = [];
  act(() => client.setQueryData(["me"], { email: "second@example.test" }));
  await act(async () => {
    wait.resolve(new Response());
  });
  expect(invalidate).not.toHaveBeenCalled();
});

const cryptoFill = {
  trade_id: 17,
  created_at: "2026-11-12T15:00:00Z",
  symbol: "BTC",
  side: "buy",
  input_kind: "quantity",
  input_value: "1",
  mid: "10",
  as_of: "2026-11-12T15:00:00Z",
  exec_price: "10.01",
  quantity: "1",
  notional: "10.01",
  fee: "0.01",
  cash_delta: "-10.02",
  cash_after: "9989.98",
};
const order = {
  order: { symbol: "BTC", side: "buy" as const, quantity: "1" },
  expectedMid: "10",
  idempotencyKey: "test-key",
};

it("actual crypto fill invalidates only the current event owner and retains legacy invalidation", async () => {
  document.cookie = "bj_csrf=test; path=/";
  historyTransport(
    vi.fn((input: RequestInfo | URL) =>
      Promise.resolve(
        String(input) === "/api/v1/trades" ? new Response(JSON.stringify(cryptoFill)) : page([]),
      ),
    ),
  );
  const { client, wrapper } = setup();
  const invalidate = vi.spyOn(client, "invalidateQueries");
  const trade = renderHook(() => useTrade("BTC"), { wrapper });
  await act(async () => {
    await trade.result.current.mutateAsync(order);
  });
  expect(invalidate).toHaveBeenCalledWith({ queryKey: ["eventHistory", "first@example.test", 0] });
  expect(invalidate).toHaveBeenCalledWith({ queryKey: ["history"] });
  expect(
    invalidate.mock.calls.filter(([filters]) => filters?.queryKey?.[0] === "eventHistory"),
  ).toHaveLength(1);
});

it.each(["other-owner", "same-owner-relogin"])(
  "late crypto fill cannot refresh %s session",
  async (change) => {
    document.cookie = "bj_csrf=test; path=/";
    const response = pending();
    historyTransport(
      vi.fn((input: RequestInfo | URL) =>
        String(input) === "/api/v1/trades" ? response.promise : Promise.resolve(page([])),
      ),
    );
    const { client, wrapper } = setup();
    const invalidate = vi.spyOn(client, "invalidateQueries");
    const trade = renderHook(() => useTrade("BTC"), { wrapper });
    let execution!: ReturnType<typeof trade.result.current.mutateAsync>;
    act(() => {
      execution = trade.result.current.mutateAsync(order);
    });
    await waitFor(() => expect(trade.result.current.isPending).toBe(true));
    act(() => {
      client.setQueryData(["me"], null);
      client.setQueryData(["me"], {
        email: change === "other-owner" ? "second@example.test" : "first@example.test",
        cash_usd: "10000.00",
      });
    });
    await act(async () => {
      response.resolve(new Response(JSON.stringify(cryptoFill)));
      await execution;
    });
    expect(invalidate).not.toHaveBeenCalled();
  },
);

it("actual stock fill invalidates the current event owner while keeping legacy History", async () => {
  document.cookie = "bj_csrf=test; path=/";
  historyTransport(
    vi.fn((input: RequestInfo | URL) => {
      const path = String(input);
      const body = path.endsWith("/context")
        ? contextFixture()
        : path.endsWith("/quote")
          ? quoteFixture()
          : path === "/api/v1/stock-trades"
            ? fillFixture()
            : { items: [], next_cursor: null };
      return Promise.resolve(new Response(JSON.stringify(body)));
    }),
  );
  const { client, wrapper } = setup();
  const invalidate = vi.spyOn(client, "invalidateQueries");
  const stock = renderHook(() => useStockTrade("AAPL"), { wrapper });
  await waitFor(() => expect(stock.result.current.context?.execution_enabled).toBe(true));
  act(() => stock.result.current.setQuantity("2"));
  await act(async () => {
    await stock.result.current.preview();
  });
  await waitFor(() => expect(stock.result.current.phase).toBe("preview"));
  await act(async () => {
    await stock.result.current.confirm();
  });
  expect(invalidate).toHaveBeenCalledWith({ queryKey: ["eventHistory", "first@example.test"] });
  expect(invalidate).toHaveBeenCalledWith({ queryKey: ["history"] });
});
