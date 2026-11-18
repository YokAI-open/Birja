import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { afterEach, expect, it, vi } from "vitest";
import type { PortfolioTarget } from "./usePortfolioTarget";
import { useHistory } from "./useHistory";
import { useEventHistory } from "./useEventHistory";
import { usePortfolioTarget } from "./usePortfolioTarget";
import { useTrade } from "./useTrade";
import { useStockTrade } from "./useStockTrade";
import { contextFixture, fillFixture, quoteFixture } from "@/test/stockTradeFixtures";

const alice = "alice@example.test",
  bob = "bob@example.test";
const clients: QueryClient[] = [];
const stamp = "2026-11-12T15:00:00.000001Z";
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
type Lane = "trade" | "mixed";
function token(root: string, lane: Lane, id = "3") {
  const value =
    lane === "trade"
      ? { v: 2, portfolio_id: root, created_at: stamp, id }
      : { v: 3, portfolio_id: root, recorded_at: stamp, kind_rank: 3, source_id: id };
  return btoa(JSON.stringify(value)).replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_");
}
function dividend(id: string) {
  return {
    kind: "dividend",
    id: `dividend:${id}`,
    recorded_at: stamp,
    asset_type: "stock",
    symbol: "AAPL",
    name: "Apple",
    cash_delta: "1.00",
    payment_reference: `dividend:${id}`,
    eligible_quantity: "2",
    rate: "0.50",
    credited_amount: "1.00",
    cutoff: "2026-11-10T14:30:00Z",
    ex_date: "2026-11-10",
    record_date: "2026-11-11",
    payable_date: "2026-11-12",
    credited_at: stamp,
  };
}
function page(lane: Lane, ids: string[], next: string | null = null) {
  return json({
    items: ids.map((id) =>
      lane === "mixed"
        ? dividend(id)
        : {
            id,
            created_at: stamp,
            symbol: "BTC",
            name: "Bitcoin",
            side: "buy",
            quantity: "0.00001",
            exec_price: "100000",
            fee: "0.01",
            total: "-1.01",
          },
    ),
    next_cursor: next,
  });
}
function deferred() {
  let resolve!: (body: Response) => void;
  const promise = new Promise<Response>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}
function setup() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: Infinity } },
  });
  clients.push(client);
  client.setQueryData(["me"], { email: alice });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  function target(id = "1", owner = alice) {
    const live = { value: true };
    const value: PortfolioTarget = Object.freeze({
      owner,
      portfolioId: id,
      name: "Strategy " + id,
      epoch: Object.freeze({ owner, portfolioId: id, session: 0 }),
      isCurrent: () =>
        live.value && client.getQueryData<{ email: string } | null>(["me"])?.email === owner,
    });
    return { value, live };
  }
  return { client, wrapper, target };
}
function useLane(lane: Lane, target: PortfolioTarget | null) {
  const trades = useHistory(lane === "trade" ? target : null);
  const events = useEventHistory(lane === "mixed" ? target : null);
  return lane === "trade" ? trades : events;
}
const ids = (value: ReturnType<typeof useLane>["data"]) =>
  value?.pages.flatMap((p) => p.items.map((item) => item.id));
const expected = (lane: Lane, values: string[]) =>
  values.map((id) => (lane === "mixed" ? `dividend:${id}` : id));
afterEach(() => {
  cleanup();
  clients.splice(0).forEach((client) => client.clear());
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

it.each(["trade", "mixed"] as const)(
  "%s does not query or run stale recovery actions without an active target",
  async (lane) => {
    const { wrapper } = setup(),
      fetch = vi.fn();
    vi.stubGlobal("fetch", fetch);
    const { result } = renderHook(() => useLane(lane, null), { wrapper });
    await act(async () => {
      await expect(result.current.fetchNextPage()).rejects.toThrow("Portfolio target changed");
      await expect(result.current.refetch()).rejects.toThrow("Portfolio target changed");
    });
    expect(fetch).not.toHaveBeenCalled();
    expect(result.current.data).toBeUndefined();
  },
);
it.each(["trade", "mixed"] as const)(
  "%s scopes pages/cursors and preserves same-root append order",
  async (lane) => {
    const { client, wrapper, target } = setup(),
      t = target(),
      next = token("1", lane);
    const fetch = vi.fn((p: RequestInfo | URL) =>
      Promise.resolve(String(p).includes("cursor=") ? page(lane, ["2"]) : page(lane, ["3"], next)),
    );
    vi.stubGlobal("fetch", fetch);
    const { result } = renderHook(() => useLane(lane, t.value), { wrapper });
    await waitFor(() => expect(ids(result.current.data)).toEqual(expected(lane, ["3"])));
    await act(async () => {
      await result.current.fetchNextPage();
    });
    await waitFor(() => expect(ids(result.current.data)).toEqual(expected(lane, ["3", "2"])));
    expect(String(fetch.mock.calls[1][0])).toContain("/portfolios/1/");
    expect(
      new URL(String(fetch.mock.calls[1][0]), "https://example.test").searchParams.get("cursor"),
    ).toBe(next);
    const prefix = lane === "trade" ? "history" : "eventHistory";
    expect(client.getQueryCache().findAll({ queryKey: [prefix, alice, "1"] })).toHaveLength(1);
  },
);
it.each(["trade", "mixed"] as const)(
  "%s discards a late old-root initial page and private details",
  async (lane) => {
    const { wrapper, target } = setup(),
      one = target(),
      two = target("2"),
      late = deferred();
    vi.stubGlobal(
      "fetch",
      vi.fn((p: RequestInfo | URL) =>
        String(p).includes("/1/") ? late.promise : Promise.resolve(page(lane, ["9"])),
      ),
    );
    const hook = renderHook(({ t }) => useLane(lane, t), {
      wrapper,
      initialProps: { t: one.value },
    });
    one.live.value = false;
    hook.rerender({ t: two.value });
    await waitFor(() => expect(ids(hook.result.current.data)).toEqual(expected(lane, ["9"])));
    await act(async () => {
      late.resolve(page(lane, ["3"]));
    });
    expect(ids(hook.result.current.data)).toEqual(expected(lane, ["9"]));
  },
);
it.each(["trade", "mixed"] as const)(
  "%s discards a pending append and cursor after root change",
  async (lane) => {
    const { wrapper, target } = setup(),
      one = target(),
      two = target("2"),
      late = deferred();
    const fetch = vi.fn((p: RequestInfo | URL) =>
      Promise.resolve(
        String(p).includes("/2/") ? page(lane, ["9"]) : page(lane, ["3"], token("1", lane)),
      ),
    );
    fetch.mockImplementation((p: RequestInfo | URL) =>
      String(p).includes("cursor=")
        ? late.promise
        : Promise.resolve(
            String(p).includes("/2/") ? page(lane, ["9"]) : page(lane, ["3"], token("1", lane)),
          ),
    );
    vi.stubGlobal("fetch", fetch);
    const hook = renderHook(({ t }) => useLane(lane, t), {
      wrapper,
      initialProps: { t: one.value },
    });
    await waitFor(() => expect(hook.result.current.hasNextPage).toBe(true));
    const staleAppend = hook.result.current.fetchNextPage,
      staleRefresh = hook.result.current.refetch;
    let pending!: ReturnType<typeof hook.result.current.fetchNextPage>;
    act(() => {
      pending = hook.result.current.fetchNextPage();
    });
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
    one.live.value = false;
    hook.rerender({ t: two.value });
    await waitFor(() => expect(ids(hook.result.current.data)).toEqual(expected(lane, ["9"])));
    await act(async () => {
      late.resolve(page(lane, ["2"]));
      await pending;
    });
    expect(ids(hook.result.current.data)).toEqual(expected(lane, ["9"]));
    const calls = fetch.mock.calls.length;
    await act(async () => {
      await expect(staleAppend()).rejects.toThrow("Portfolio target changed");
      await expect(staleRefresh()).rejects.toThrow("Portfolio target changed");
    });
    expect(fetch).toHaveBeenCalledTimes(calls);
  },
);
it.each(["trade", "mixed"] as const)(
  "%s immediately hides accepted pages on owner loss and does not reuse them on relogin",
  async (lane) => {
    const { client, wrapper, target } = setup(),
      t = target();
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(page(lane, ["3"]))),
    );
    const { result } = renderHook(() => useLane(lane, t.value), { wrapper });
    await waitFor(() => expect(result.current.data).toBeDefined());
    act(() => {
      client.setQueryData(["me"], null);
      client.setQueryData(["me"], { email: alice });
    });
    expect(result.current.data).toBeUndefined();
    const prefix = lane === "trade" ? "history" : "eventHistory";
    expect(client.getQueryCache().findAll({ queryKey: [prefix, alice, "1", 0] })).toHaveLength(0);
  },
);
it.each(["trade", "mixed"] as const)(
  "%s ignores a late old-owner response including logout/return with the same identity",
  async (lane) => {
    const { client, wrapper, target } = setup(),
      one = target(),
      late = deferred();
    vi.stubGlobal(
      "fetch",
      vi.fn(() => late.promise),
    );
    const { result } = renderHook(() => useLane(lane, one.value), { wrapper });
    act(() => {
      client.setQueryData(["me"], null);
      client.setQueryData(["me"], { email: alice });
    });
    await act(async () => {
      late.resolve(page(lane, ["3"]));
    });
    expect(result.current.data).toBeUndefined();
  },
);
it.each(["trade", "mixed"] as const)(
  "%s hides accepted pages on server-unavailable append and revokes only that metadata root",
  async (lane) => {
    const { client, wrapper, target } = setup(),
      t = target();
    client.setQueryData(
      ["portfolios", alice],
      [
        { id: "1", name: "Strategy 1" },
        { id: "2", name: "Strategy 2" },
      ],
    );
    vi.stubGlobal(
      "fetch",
      vi.fn((p: RequestInfo | URL) =>
        Promise.resolve(
          String(p).includes("cursor=")
            ? json({ detail: { code: "portfolio_unavailable" } }, 404)
            : page(lane, ["3"], token("1", lane)),
        ),
      ),
    );
    const { result } = renderHook(() => useLane(lane, t.value), { wrapper });
    await waitFor(() => expect(result.current.hasNextPage).toBe(true));
    await act(async () => {
      await result.current.fetchNextPage();
    });
    await waitFor(() => expect(result.current.data).toBeUndefined());
    expect(client.getQueryData(["portfolios", alice])).toEqual([{ id: "2", name: "Strategy 2" }]);
    await act(async () => {
      await expect(result.current.refetch()).rejects.toThrow("Portfolio target changed");
    });
  },
);
it.each(["trade", "mixed"] as const)(
  "%s preserves accepted pages and cursor for same-root append error retry",
  async (lane) => {
    const { wrapper, target } = setup(),
      t = target();
    let failed = true;
    vi.stubGlobal(
      "fetch",
      vi.fn((p: RequestInfo | URL) =>
        Promise.resolve(
          String(p).includes("cursor=")
            ? failed
              ? json({}, 503)
              : page(lane, ["2"])
            : page(lane, ["3"], token("1", lane)),
        ),
      ),
    );
    const { result } = renderHook(() => useLane(lane, t.value), { wrapper });
    await waitFor(() => expect(result.current.hasNextPage).toBe(true));
    await act(async () => {
      await result.current.fetchNextPage();
    });
    await waitFor(() => expect(result.current.isFetchNextPageError).toBe(true));
    expect(ids(result.current.data)).toEqual(expected(lane, ["3"]));
    failed = false;
    await act(async () => {
      await result.current.fetchNextPage();
    });
    await waitFor(() => expect(ids(result.current.data)).toEqual(expected(lane, ["3", "2"])));
  },
);
it.each(["trade", "mixed"] as const)(
  "%s rejects an old-root cursor returned for the current root",
  async (lane) => {
    const { wrapper, target } = setup(),
      t = target("2");
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(page(lane, ["9"], token("1", lane)))),
    );
    const { result } = renderHook(() => useLane(lane, t.value), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.data).toBeUndefined();
  },
);
it("partitions event seen sets and invalidations even for identical global event IDs", async () => {
  const { client, wrapper, target } = setup(),
    one = target(),
    two = target("2");
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.resolve(page("mixed", ["3"]))),
  );
  const invalidate = vi.spyOn(client, "invalidateQueries");
  const hook = renderHook(({ t }) => useEventHistory(t), {
    wrapper,
    initialProps: { t: one.value },
  });
  await waitFor(() =>
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ["portfolio", alice, "1"] }),
  );
  invalidate.mockClear();
  one.live.value = false;
  hook.rerender({ t: two.value });
  await waitFor(() =>
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ["portfolio", alice, "2"] }),
  );
  expect(
    invalidate.mock.calls.every(
      ([filter]) =>
        filter?.queryKey?.[1] === alice &&
        (filter.queryKey[0] === "portfolioOverview"
          ? filter.queryKey[2] === 0 && filter.exact === true
          : filter.queryKey[2] === "2"),
    ),
  ).toBe(true);
});
it("does not invalidate a newly selected root from a late old-root event", async () => {
  const { client, wrapper, target } = setup(),
    one = target(),
    two = target("2"),
    late = deferred();
  vi.stubGlobal(
    "fetch",
    vi.fn((p: RequestInfo | URL) =>
      String(p).includes("/1/") ? late.promise : Promise.resolve(page("mixed", [])),
    ),
  );
  const hook = renderHook(({ t }) => useEventHistory(t), {
    wrapper,
    initialProps: { t: one.value },
  });
  one.live.value = false;
  hook.rerender({ t: two.value });
  await waitFor(() => expect(hook.result.current.isSuccess).toBe(true));
  const invalidate = vi.spyOn(client, "invalidateQueries");
  await act(async () => {
    late.resolve(page("mixed", ["3"]));
  });
  expect(invalidate).not.toHaveBeenCalled();
});
it("hides embedded original detail hydration after a root switch", async () => {
  const { wrapper, target } = setup(),
    one = target(),
    two = target("2"),
    late = deferred();
  const original = dividend("3");
  const correction = {
    kind: "dividend_correction",
    id: "dividend_correction:4",
    recorded_at: stamp,
    asset_type: "stock",
    symbol: "AAPL",
    name: "Apple",
    cash_delta: "-0.50",
    payment_reference: original.id,
    decision_reference: "dividend_correction:4",
    outcome: "applied",
    reason: "target_applied",
    desired_total: "0.50",
    cumulative_applied_before: "1.00",
    proposed_delta: "-0.50",
    applied_delta: "-0.50",
    terms: {
      eligible_quantity: "1",
      rate: "0.50",
      cutoff: original.cutoff,
      ex_date: original.ex_date,
      record_date: original.record_date,
      payable_date: original.payable_date,
    },
    original,
  };
  vi.stubGlobal(
    "fetch",
    vi.fn((p: RequestInfo | URL) =>
      String(p).includes("/1/") ? late.promise : Promise.resolve(page("mixed", ["9"])),
    ),
  );
  const hook = renderHook(({ t }) => useEventHistory(t), {
    wrapper,
    initialProps: { t: one.value },
  });
  one.live.value = false;
  hook.rerender({ t: two.value });
  await waitFor(() => expect(ids(hook.result.current.data)).toEqual(["dividend:9"]));
  await act(async () => {
    late.resolve(json({ items: [correction], next_cursor: null }));
  });
  expect(ids(hook.result.current.data)).toEqual(["dividend:9"]);
});
it("preserves verified same-root embedded original details and clears them before a sibling loads", async () => {
  const { wrapper, target } = setup(),
    one = target(),
    two = target("2"),
    late = deferred();
  const original = dividend("3");
  const correction = {
    kind: "dividend_correction",
    id: "dividend_correction:4",
    recorded_at: "2026-11-12T16:00:00Z",
    asset_type: "stock",
    symbol: "AAPL",
    name: "Apple",
    cash_delta: "-0.50",
    payment_reference: original.id,
    decision_reference: "dividend_correction:4",
    outcome: "applied",
    reason: "target_applied",
    desired_total: "0.50",
    cumulative_applied_before: "1.00",
    proposed_delta: "-0.50",
    applied_delta: "-0.50",
    terms: {
      eligible_quantity: "1",
      rate: "0.50",
      cutoff: original.cutoff,
      ex_date: original.ex_date,
      record_date: original.record_date,
      payable_date: original.payable_date,
    },
    original,
  };
  vi.stubGlobal(
    "fetch",
    vi.fn((p: RequestInfo | URL) =>
      String(p).includes("/1/")
        ? Promise.resolve(json({ items: [correction], next_cursor: null }))
        : late.promise,
    ),
  );
  const hook = renderHook(({ t }) => useEventHistory(t), {
    wrapper,
    initialProps: { t: one.value },
  });
  await waitFor(() =>
    expect(hook.result.current.data?.pages[0].items[0]).toMatchObject({ original }),
  );
  one.live.value = false;
  hook.rerender({ t: two.value });
  expect(hook.result.current.data).toBeUndefined();
  await act(async () => {
    late.resolve(page("mixed", ["9"]));
  });
  await waitFor(() => expect(ids(hook.result.current.data)).toEqual(["dividend:9"]));
});
it.each(["trade", "mixed"] as const)(
  "%s cannot let a late401 clear a new owner's identity",
  async (lane) => {
    const { client, wrapper, target } = setup(),
      one = target(),
      two = target("2", bob),
      late = deferred();
    // No CSRF token means the real client cannot start a refresh after401.
    document.cookie = "bj_csrf=; max-age=0; path=/";
    vi.stubGlobal(
      "fetch",
      vi.fn((p: RequestInfo | URL) =>
        String(p).includes("/1/") ? late.promise : Promise.resolve(page(lane, ["9"])),
      ),
    );
    const hook = renderHook(({ t }) => useLane(lane, t), {
      wrapper,
      initialProps: { t: one.value },
    });
    one.live.value = false;
    act(() => client.setQueryData(["me"], { email: bob }));
    hook.rerender({ t: two.value });
    await waitFor(() => expect(ids(hook.result.current.data)).toEqual(expected(lane, ["9"])));
    await act(async () => {
      late.resolve(json({}, 401));
    });
    expect(client.getQueryData(["me"])).toEqual({ email: bob });
    expect(ids(hook.result.current.data)).toEqual(expected(lane, ["9"]));
  },
);

it("invalidates the current owner comparison once for new attributable events without a refetch loop", async () => {
  const { client, wrapper, target } = setup();
  const t = target();
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.resolve(page("mixed", ["3"]))),
  );
  const invalidate = vi.spyOn(client, "invalidateQueries");
  const hook = renderHook(() => useEventHistory(t.value), { wrapper });
  await waitFor(() =>
    expect(invalidate).toHaveBeenCalledWith({
      queryKey: ["portfolioOverview", alice, 0],
      exact: true,
    }),
  );
  invalidate.mockClear();
  await act(async () => {
    await hook.result.current.refetch();
  });
  expect(invalidate).not.toHaveBeenCalled();
});

it.each(["crypto", "stock"] as const)(
  "accepted real-target %s fill invalidates only its root and current owner overview",
  async (asset) => {
    const { client, wrapper } = setup();
    document.cookie = "bj_csrf=test; path=/";
    const crypto = {
      portfolio_id: "1",
      trade_id: 17,
      created_at: stamp,
      symbol: "BTC",
      side: "buy",
      input_kind: "usd",
      input_value: "100",
      mid: "10000",
      as_of: stamp,
      exec_price: "10025",
      quantity: "0.00995018",
      notional: "99.75",
      fee: "0.25",
      cash_delta: "-100",
      cash_after: "9900",
    };
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const path = String(input);
        return Promise.resolve(
          json(
            path.endsWith("/portfolios")
              ? [
                  { id: "1", name: "Original" },
                  { id: "2", name: "Sibling" },
                ]
              : path.endsWith("/context")
                ? contextFixture()
                : path.endsWith("/quote")
                  ? quoteFixture()
                  : asset === "stock"
                    ? fillFixture()
                    : crypto,
          ),
        );
      }),
    );
    const hook = renderHook(
      () => {
        const p = usePortfolioTarget("1");
        return {
          p,
          crypto: useTrade(p.target, "BTC"),
          stock: useStockTrade(asset === "stock" ? p.target : null, "AAPL"),
        };
      },
      { wrapper },
    );
    await waitFor(() => expect(hook.result.current.p.status).toBe("ready"));
    if (asset === "stock") {
      await waitFor(() => expect(hook.result.current.stock.context?.execution_enabled).toBe(true));
      act(() => hook.result.current.stock.setQuantity("2"));
      await act(async () => {
        await hook.result.current.stock.preview();
      });
    }
    const invalidate = vi.spyOn(client, "invalidateQueries");
    await act(async () => {
      if (asset === "stock") await hook.result.current.stock.confirm();
      else
        await hook.result.current.crypto.mutateAsync({
          order: { symbol: "BTC", side: "buy", amount_usd: "100" },
          expectedMid: "10000",
          idempotencyKey: "original-key",
        });
    });
    expect(invalidate).toHaveBeenCalledWith({
      queryKey: ["portfolioOverview", alice, 0],
      exact: true,
    });
    expect(invalidate).toHaveBeenCalledWith({ queryKey: ["portfolio", alice, "1"] });
    expect(
      invalidate.mock.calls.every(
        ([filter]) =>
          ["prices", "stocks"].includes(String(filter?.queryKey?.[0])) ||
          (filter?.queryKey?.[1] === alice &&
            (filter?.queryKey?.[0] === "portfolioOverview"
              ? filter.queryKey[2] === 0
              : filter?.queryKey?.[2] === "1")),
      ),
    ).toBe(true);
  },
);

it("does not invalidate a returned owner's new session while pre-event cancellation is pending", async () => {
  const { client, wrapper, target } = setup();
  const t = target();
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.resolve(page("mixed", ["3"]))),
  );
  let release!: () => void;
  const pending = new Promise<void>((resolve) => {
    release = resolve;
  });
  vi.spyOn(client, "cancelQueries").mockImplementation(() => pending);
  const invalidate = vi.spyOn(client, "invalidateQueries");
  renderHook(() => useEventHistory(t.value), { wrapper });
  await waitFor(() => expect(client.cancelQueries).toHaveBeenCalled());
  act(() => {
    client.setQueryData(["me"], null);
    client.setQueryData(["me"], { email: alice });
  });
  await act(async () => {
    release();
  });
  expect(invalidate).not.toHaveBeenCalled();
});
