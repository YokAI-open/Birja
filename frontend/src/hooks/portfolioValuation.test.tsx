import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { afterEach, expect, it, vi } from "vitest";
import { mixedPortfolio } from "@/test/portfolioFixtures";
import { contextFixture } from "@/test/stockTradeFixtures";
import type { PortfolioTarget } from "./usePortfolioTarget";
import { usePortfolio } from "./usePortfolio";

const alice = "alice@example.test",
  bob = "bob@example.test";
const clients: QueryClient[] = [];
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
function deferred() {
  let resolve!: (response: Response) => void;
  const promise = new Promise<Response>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}
function portfolio(id = "1") {
  const body = { ...mixedPortfolio(), portfolio_id: id, name: "Strategy " + id };
  if (id === "2") {
    Object.assign(body, {
      cash: "500.00",
      starting_cash: "1000.00",
      total_value: "702.00",
      known_value: "702.00",
      total_pl: "-298.00",
      total_pl_percent: "-29.80",
      cash_allocation_percent: "71.23",
      class_values: { cash: "500.00", stocks: "202.00", crypto: "0.00" },
      class_allocation_percent: { cash: "71.23", stocks: "28.77", crypto: "0.00" },
    });
    body.holdings[0].allocation_percent = "28.77";
  }
  return body;
}
function setup() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: Infinity } },
  });
  clients.push(client);
  client.setQueryData(["me"], { email: alice });
  vi.spyOn(performance, "now").mockReturnValue(0);
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
afterEach(() => {
  cleanup();
  clients.splice(0).forEach((client) => client.clear());
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

it("requires a valid active target even for manually retained refetch actions", async () => {
  const { wrapper } = setup(),
    fetch = vi.fn();
  vi.stubGlobal("fetch", fetch);
  const { result } = renderHook(() => usePortfolio(null), { wrapper });
  await act(async () => {
    await result.current.refetch();
  });
  expect(fetch).not.toHaveBeenCalled();
  expect(result.current.data).toBeUndefined();
});
it("keeps the same asset and unequal baselines/returns independent across roots", async () => {
  const { client, wrapper, target } = setup(),
    one = target(),
    two = target("2"),
    late = deferred();
  vi.stubGlobal(
    "fetch",
    vi.fn((p: RequestInfo | URL) =>
      String(p).includes("/2") ? late.promise : Promise.resolve(json(portfolio())),
    ),
  );
  const hook = renderHook(({ t }) => usePortfolio(t), { wrapper, initialProps: { t: one.value } });
  await waitFor(() => expect(hook.result.current.data?.total_value).toBe("9998.00"));
  one.live.value = false;
  hook.rerender({ t: two.value });
  expect(hook.result.current.data).toBeUndefined();
  await act(async () => {
    late.resolve(json(portfolio("2")));
  });
  await waitFor(() => expect(hook.result.current.data?.cash).toBe("500.00"));
  expect(hook.result.current.data?.starting_cash).toBe("1000.00");
  expect(hook.result.current.data?.total_pl).toBe("-298.00");
  expect(hook.result.current.data?.holdings[0].symbol).toBe("AAPL");
  expect(client.getQueryCache().findAll({ queryKey: ["portfolio", alice, "2"] })).toHaveLength(1);
});
it("discards a delayed old-root valuation even when fetch ignores cancellation", async () => {
  const { wrapper, target } = setup(),
    one = target(),
    two = target("2"),
    late = deferred();
  vi.stubGlobal(
    "fetch",
    vi.fn((p: RequestInfo | URL) =>
      String(p).includes("/1") ? late.promise : Promise.resolve(json(portfolio("2"))),
    ),
  );
  const hook = renderHook(({ t }) => usePortfolio(t), { wrapper, initialProps: { t: one.value } });
  one.live.value = false;
  hook.rerender({ t: two.value });
  await waitFor(() => expect(hook.result.current.data?.portfolio_id).toBe("2"));
  await act(async () => {
    late.resolve(json(portfolio()));
  });
  expect(hook.result.current.data?.portfolio_id).toBe("2");
  expect(hook.result.current.data?.cash).toBe("500.00");
});
it.each([null, bob, alice])(
  "does not resurrect an old owner/session response after logout to %s",
  async (next) => {
    const { client, wrapper, target } = setup(),
      one = target(),
      late = deferred();
    vi.stubGlobal(
      "fetch",
      vi.fn(() => late.promise),
    );
    const hook = renderHook(() => usePortfolio(one.value), { wrapper });
    act(() => {
      client.setQueryData(["me"], null);
      if (next !== null) client.setQueryData(["me"], { email: next });
    });
    await act(async () => {
      late.resolve(json(portfolio()));
    });
    expect(hook.result.current.data).toBeUndefined();
    expect(
      client
        .getQueryCache()
        .findAll({ queryKey: ["portfolio", alice] })
        .every((query) => query.state.data === undefined),
    ).toBe(true);
  },
);
it("hides a retained projection and revokes only the unavailable root after server refusal", async () => {
  const { client, wrapper, target } = setup(),
    one = target();
  let unavailable = false;
  client.setQueryData(
    ["portfolios", alice],
    [
      { id: "1", name: "Strategy 1" },
      { id: "2", name: "Strategy 2" },
    ],
  );
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve(
        unavailable ? json({ detail: { code: "portfolio_unavailable" } }, 404) : json(portfolio()),
      ),
    ),
  );
  const { result } = renderHook(() => usePortfolio(one.value), { wrapper });
  await waitFor(() => expect(result.current.data).toBeDefined());
  unavailable = true;
  await act(async () => {
    await result.current.refetch();
  });
  await waitFor(() => expect(result.current.data).toBeUndefined());
  expect(client.getQueryData(["portfolios", alice])).toEqual([{ id: "2", name: "Strategy 2" }]);
  const calls = vi.mocked(fetch).mock.calls.length;
  await act(async () => {
    await result.current.refetch();
  });
  expect(vi.mocked(fetch).mock.calls).toHaveLength(calls);
});
it("does not let a sibling's same-symbol stock restriction poison this projection", async () => {
  const { client, wrapper, target } = setup(),
    one = target();
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.resolve(json(portfolio()))),
  );
  const { result } = renderHook(() => usePortfolio(one.value), { wrapper });
  await waitFor(() => expect(result.current.data?.total_value).toBe("9998.00"));
  const context = {
    ...contextFixture(),
    portfolio_id: "2",
    execution_enabled: false,
    execution_reason: "halted",
  };
  context.status.state = "halted";
  act(() => client.setQueryData(["stockContext", alice, "2", 0, "AAPL"], context));
  expect(result.current.data?.total_value).toBe("9998.00");
  act(() =>
    client.setQueryData(["stockContext", alice, "1", 0, "AAPL"], { ...context, portfolio_id: "1" }),
  );
  expect(result.current.data?.total_value).toBeNull();
  expect(result.current.data?.cash).toBe("9796.00");
});
it("partitions hidden monotone unit guards by root rather than equal symbol", async () => {
  const { wrapper, target } = setup(),
    one = target(),
    two = target("2");
  const newer = portfolio();
  newer.holdings[0].stock_mark!.authority!.unit_epoch = 3;
  vi.stubGlobal(
    "fetch",
    vi.fn((p: RequestInfo | URL) =>
      Promise.resolve(json(String(p).includes("/2") ? portfolio("2") : newer)),
    ),
  );
  const hook = renderHook(({ t }) => usePortfolio(t), { wrapper, initialProps: { t: one.value } });
  await waitFor(() => expect(hook.result.current.data?.total_value).toBeDefined());
  one.live.value = false;
  hook.rerender({ t: two.value });
  await waitFor(() => expect(hook.result.current.data?.total_value).toBe("702.00"));
  expect(hook.result.current.data?.holdings[0].stock_mark?.authority?.unit_epoch).toBe(0);
});
it("keeps unavailable/known-value semantics without inventing a subtotal", async () => {
  const { wrapper, target } = setup(),
    t = target(),
    body = portfolio();
  Object.assign(body, {
    valuation_complete: false,
    known_value: "9796.00",
    total_value: null,
    total_pl: null,
    total_pl_percent: null,
    unvalued_holding_count: 1,
    cash_allocation_percent: null,
    class_values: { cash: "9796.00", stocks: null, crypto: "0.00" },
    class_allocation_percent: { cash: null, stocks: null, crypto: null },
  });
  Object.assign(body.holdings[0], {
    mid: null,
    current_value: null,
    unrealized_pl: null,
    unrealized_pl_percent: null,
    allocation_percent: null,
    as_of: null,
    age_seconds: null,
    status: "unpriced",
    average_cost: null,
  });
  Object.assign(body.holdings[0].stock_mark!, {
    mark_mode: "unavailable",
    valuation_reason: "quote_unavailable",
    source: null,
    feed: null,
    event_at: null,
    collected_at: null,
    historical_admission_until: null,
    retained_until: null,
    valid_until: null,
    authority: null,
    units_safe: false,
  });
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.resolve(json(body))),
  );
  const { result } = renderHook(() => usePortfolio(t.value), { wrapper });
  await waitFor(() => expect(result.current.data).toBeDefined());
  expect(result.current.data?.known_value).toBe("9796.00");
  expect(result.current.data?.total_pl).toBeNull();
  expect(result.current.data?.cash_allocation_percent).toBeNull();
});
it("suppresses financial data after a failed refresh instead of publishing the old statement", async () => {
  const { wrapper, target } = setup(),
    t = target();
  let failed = false;
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.resolve(failed ? json({ detail: "unavailable" }, 503) : json(portfolio()))),
  );
  const { result } = renderHook(() => usePortfolio(t.value), { wrapper });
  await waitFor(() => expect(result.current.data?.cash).toBe("9796.00"));
  failed = true;
  await act(async () => {
    await result.current.refetch();
  });
  await waitFor(() => expect(result.current.isError).toBe(true));
  expect(result.current.data).toBeUndefined();
});
it("hides a root lost while refreshing and ignores its late financial snapshot", async () => {
  const { wrapper, target } = setup(),
    t = target(),
    late = deferred();
  let refresh = false;
  vi.stubGlobal(
    "fetch",
    vi.fn(() => (refresh ? late.promise : Promise.resolve(json(portfolio())))),
  );
  const hook = renderHook(({ value }: { value: PortfolioTarget | null }) => usePortfolio(value), {
    wrapper,
    initialProps: { value: t.value as PortfolioTarget | null },
  });
  await waitFor(() => expect(hook.result.current.data).toBeDefined());
  refresh = true;
  let work!: ReturnType<typeof hook.result.current.refetch>;
  act(() => {
    work = hook.result.current.refetch();
  });
  t.live.value = false;
  hook.rerender({ value: null });
  expect(hook.result.current.data).toBeUndefined();
  await act(async () => {
    late.resolve(json(portfolio()));
    await work;
  });
  expect(hook.result.current.data).toBeUndefined();
});
it("retains stock expiry reductions and never exposes a crossed-root cache value", async () => {
  const { client, wrapper, target } = setup(),
    t = target();
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.resolve(json(portfolio()))),
  );
  const { result } = renderHook(() => usePortfolio(t.value), { wrapper });
  await waitFor(() => expect(result.current.data?.total_value).toBe("9998.00"));
  vi.mocked(performance.now).mockReturnValue(50_000);
  act(() => window.dispatchEvent(new Event("focus")));
  expect(result.current.data?.total_value).toBeNull();
  expect(result.current.data?.cash).toBe("9796.00");
  act(() => client.setQueryData(["portfolio", alice, "1", 0], portfolio("2")));
  expect(result.current.data).toBeUndefined();
});
it("immediately masks accepted valuations on owner changes without waiting for parent routing", async () => {
  const { client, wrapper, target } = setup(),
    t = target();
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.resolve(json(portfolio()))),
  );
  const { result } = renderHook(() => usePortfolio(t.value), { wrapper });
  await waitFor(() => expect(result.current.data?.cash).toBe("9796.00"));
  act(() => client.setQueryData(["me"], { email: bob }));
  expect(result.current.data).toBeUndefined();
});
