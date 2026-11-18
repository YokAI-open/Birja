import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { afterEach, expect, it, vi } from "vitest";
import { contextFixture, fillFixture, quoteFixture } from "@/test/stockTradeFixtures";
import { useStockTrade } from "./useStockTrade";
import type { PortfolioTarget } from "./usePortfolioTarget";
import { usePortfolioTarget } from "./usePortfolioTarget";
import { broadcastMetadataChange } from "@/lib/portfolioMetadataEvents";

const alice = "alice@example.test",
  bob = "bob@example.test";
const ctx = (id = "1") => ({ ...contextFixture(), portfolio_id: id });
const quote = (id = "1") => ({ ...quoteFixture(), portfolio_id: id });
const fill = (id = "1") => ({ ...fillFixture(), portfolio_id: id });
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
function deferred() {
  let resolve!: (v: Response) => void;
  const promise = new Promise<Response>((r) => {
    resolve = r;
  });
  return { promise, resolve };
}
const clients: QueryClient[] = [];
it.each(["owner", "logout", "switch", "removed"])(
  "rejects captured stock actions and late finance after real-target %s",
  async (change) => {
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false, gcTime: Infinity } },
    });
    clients.push(client);
    client.setQueryData(["me"], { email: alice });
    document.cookie = "bj_csrf=test; path=/";
    const late = deferred();
    let active = true,
      trades = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const path = String(input);
        if (path.endsWith("/portfolios"))
          return Promise.resolve(
            json(
              active
                ? [
                    { id: "1", name: "Original" },
                    { id: "2", name: "Other" },
                  ]
                : [{ id: "2", name: "Other" }],
            ),
          );
        const id = path.includes("/2/") ? "2" : "1";
        if (path.endsWith("/context")) return Promise.resolve(json(ctx(id)));
        if (path.endsWith("/quote")) return Promise.resolve(json(quote(id)));
        trades++;
        return late.promise;
      }),
    );
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    );
    const h = renderHook(
      ({ id }) => {
        const p = usePortfolioTarget(id);
        return { p, t: useStockTrade(p.target, "AAPL") };
      },
      { wrapper, initialProps: { id: "1" } },
    );
    await waitFor(() => expect(h.result.current.t.context?.execution_enabled).toBe(true));
    act(() => h.result.current.t.setQuantity("2"));
    await act(async () => {
      await h.result.current.t.preview();
    });
    const stale = h.result.current.t;
    let pending!: Promise<void>;
    act(() => {
      pending = stale.confirm();
    });
    await waitFor(() => expect(trades).toBe(1));
    if (change === "switch") h.rerender({ id: "2" });
    else if (change === "removed") {
      active = false;
      act(() => broadcastMetadataChange("1"));
      await waitFor(() => expect(h.result.current.p.status).toBe("unavailable"));
    } else act(() => client.setQueryData(["me"], change === "owner" ? { email: bob } : null));
    await act(async () => {
      late.resolve(json(fill()));
      await pending;
    });
    await waitFor(() => expect(h.result.current.t.attempt).toBeNull());
    expect(h.result.current.t.fill).toBeNull();
    await act(async () => {
      await stale.confirm();
      await stale.checkResult();
      await stale.preview();
    });
    expect(trades).toBe(1);
    if (change === "switch") {
      h.rerender({ id: "1" });
      await waitFor(() => expect(h.result.current.t.phase).toBe("unknown"));
      expect(h.result.current.t.attempt?.portfolioName).toBe("Original");
      expect(trades).toBe(1);
    }
  },
);
it.each(["lost", "pending"])(
  "preserves real-target stock originals during %s rename and closed-market replay",
  async (mode) => {
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false, gcTime: Infinity } },
    });
    clients.push(client);
    client.setQueryData(["me"], { email: alice });
    document.cookie = "bj_csrf=test; path=/";
    let name = "Original",
      marketClosed = false,
      active = true;
    const late = deferred();
    const requests: { path: string; body: string }[] = [];
    const fetch = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const path = String(input);
      if (path.endsWith("/portfolios"))
        return Promise.resolve(
          json(
            active
              ? [
                  { id: "1", name },
                  { id: "2", name: "Other" },
                ]
              : [{ id: "2", name: "Other" }],
          ),
        );
      if (path.endsWith("/context")) return Promise.resolve(json(marketClosed ? closed() : ctx()));
      if (path.endsWith("/quote")) return Promise.resolve(json(quote()));
      requests.push({ path, body: init!.body as string });
      if (requests.length === 1)
        return mode === "lost" ? Promise.reject(new Error("lost")) : late.promise;
      return Promise.resolve(json(fill()));
    });
    vi.stubGlobal("fetch", fetch);
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    );
    const h = renderHook(
      ({ id }) => {
        const p = usePortfolioTarget(id);
        return { p, t: useStockTrade(p.target, "AAPL") };
      },
      { wrapper, initialProps: { id: "1" } },
    );
    await waitFor(() => expect(h.result.current.t.context?.execution_enabled).toBe(true));
    act(() => h.result.current.t.setQuantity("2"));
    await act(async () => {
      await h.result.current.t.preview();
    });
    expect(h.result.current.t.canConfirm).toBe(true);
    let pending!: Promise<void>;
    act(() => {
      pending = h.result.current.t.confirm();
    });
    await waitFor(() => expect(requests).toHaveLength(1));
    const stale = h.result.current.t.checkResult;
    name = "Renamed";
    marketClosed = true;
    act(() => broadcastMetadataChange("1"));
    await waitFor(() => expect(h.result.current.p.target?.name).toBe("Renamed"));
    await act(async () => {
      if (mode === "pending") late.resolve(json(fill()));
      await pending;
    });
    await waitFor(() => expect(h.result.current.t.phase).toBe("unknown"));
    expect(h.result.current.t.attempt?.portfolioName).toBe("Original");
    expect(h.result.current.t.fill).toBeNull();
    await act(async () => {
      await stale();
    });
    expect(requests).toHaveLength(1);
    await act(async () => {
      await h.result.current.t.refreshContext();
    });
    expect(h.result.current.t.context?.execution_enabled).toBe(false);
    expect(h.result.current.t.canConfirm).toBe(false);
    const original = h.result.current.t.attempt!.body;
    h.rerender({ id: "2" });
    expect(h.result.current.t.attempt).toBeNull();
    expect(h.result.current.t.fill).toBeNull();
    h.rerender({ id: "1" });
    await waitFor(() => expect(h.result.current.t.phase).toBe("unknown"));
    expect(h.result.current.t.attempt!.body).toBe(original);
    expect(requests).toHaveLength(1);
    await act(async () => {
      await h.result.current.t.checkResult();
    });
    await waitFor(() => expect(h.result.current.t.phase).toBe("filled"));
    expect(requests[1]).toEqual(requests[0]);
    active = false;
    act(() => broadcastMetadataChange("1"));
    await waitFor(() => expect(h.result.current.p.status).toBe("unavailable"));
    expect(h.result.current.t.context).toBeUndefined();
    expect(h.result.current.t.fill).toBeNull();
    await act(async () => {
      await h.result.current.t.checkResult();
    });
    expect(requests).toHaveLength(2);
  },
);
function setup(
  tweak?: (path: string, init?: RequestInit) => Promise<Response> | Response | undefined,
) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: Infinity } },
  });
  clients.push(client);
  client.setQueryData(["me"], { email: alice });
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
  const one = target(),
    two = target("2");
  const fetch = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const path = String(input),
      id = path.includes("/2/") ? "2" : "1";
    return (
      tweak?.(path, init) ??
      Promise.resolve(
        json(path.endsWith("/context") ? ctx(id) : path.endsWith("/quote") ? quote(id) : fill(id)),
      )
    );
  });
  vi.stubGlobal("fetch", fetch);
  document.cookie = "bj_csrf=test; path=/";
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  const hook = renderHook(
    ({ t, symbol }: { t: PortfolioTarget | null; symbol: string }) => useStockTrade(t, symbol),
    { wrapper, initialProps: { t: one.value as PortfolioTarget | null, symbol: "AAPL" } },
  );
  return { ...hook, client, one, two, target, fetch };
}
afterEach(() => {
  cleanup();
  clients.splice(0).forEach((c) => c.clear());
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.useRealTimers();
  document.cookie = "bj_csrf=; Max-Age=0; path=/";
});
async function preview(h: ReturnType<typeof setup>) {
  await waitFor(() => expect(h.result.current.context?.execution_enabled).toBe(true));
  act(() => h.result.current.setQuantity("2"));
  await act(async () => {
    await h.result.current.preview();
  });
  await waitFor(() => expect(h.result.current.phase).toBe("preview"));
}
function closed(id = "1") {
  const c = ctx(id);
  return {
    ...c,
    execution_enabled: false,
    execution_reason: "market_closed",
    valid_until: null,
    quote: null,
    buy_max_quantity: "0",
    session: { ...c.session, state: "closed" },
  };
}

it("partitions context/state/shortcuts by root without borrowing sibling cash", async () => {
  const h = setup();
  await waitFor(() => expect(h.result.current.context?.portfolio_id).toBe("1"));
  act(() => h.result.current.buyMax());
  expect(h.result.current.quantity).toBe("98");
  h.one.live.value = false;
  h.rerender({ t: h.two.value, symbol: "AAPL" });
  expect(h.result.current.quantity).toBe("");
  expect(h.result.current.context).toBeUndefined();
  await waitFor(() => expect(h.result.current.context?.portfolio_id).toBe("2"));
  expect(
    h.client
      .getQueryCache()
      .getAll()
      .filter((q) => q.queryKey[0] === "stockContext")
      .every((q) => q.queryKey[1] === alice && ["1", "2"].includes(String(q.queryKey[2]))),
  ).toBe(true);
});
it("drops delayed preview on root change and invalidates the old actionable preview", async () => {
  const late = deferred();
  const h = setup((p) => (p.endsWith("/quote") ? late.promise : undefined));
  await waitFor(() => expect(h.result.current.context?.execution_enabled).toBe(true));
  act(() => h.result.current.setQuantity("2"));
  let pending!: Promise<void>;
  act(() => {
    pending = h.result.current.preview();
  });
  await waitFor(() => expect(h.result.current.phase).toBe("loading_preview"));
  h.one.live.value = false;
  h.rerender({ t: h.two.value, symbol: "AAPL" });
  await act(async () => {
    late.resolve(json(quote()));
    await pending;
  });
  expect(h.result.current.phase).toBe("draft");
  expect(h.result.current.quote).toBeNull();
  h.rerender({ t: h.target().value, symbol: "AAPL" });
  await waitFor(() => expect(h.result.current.quantity).toBe("2"));
  expect(h.result.current.canConfirm).toBe(false);
  expect(h.result.current.quote).toBeNull();
});
it("does not carry hidden context restrictions across sibling roots", async () => {
  const h = setup((p) =>
    p.includes("/1/") && p.endsWith("/context") ? Promise.resolve(json(closed())) : undefined,
  );
  await waitFor(() => expect(h.result.current.context?.execution_reason).toBe("market_closed"));
  h.one.live.value = false;
  h.rerender({ t: h.two.value, symbol: "AAPL" });
  await waitFor(() => expect(h.result.current.context?.execution_enabled).toBe(true));
  act(() => h.result.current.setQuantity("2"));
  expect(h.result.current.canPreview).toBe(true);
});
it("retains one frozen original through loss and recovers after market closure", async () => {
  let lost = true,
    marketClosed = false;
  const bodies: unknown[] = [];
  const h = setup((p, init) => {
    if (p.endsWith("/context") && marketClosed) return Promise.resolve(json(closed()));
    if (p.endsWith("/stock-trades")) {
      bodies.push(JSON.parse(init!.body as string));
      if (lost) {
        lost = false;
        return Promise.reject(new Error("lost"));
      }
    }
    return undefined;
  });
  await preview(h);
  await act(async () => {
    await h.result.current.confirm();
  });
  await waitFor(() => expect(h.result.current.phase).toBe("unknown"));
  expect(h.result.current.attempt?.body.portfolio_id).toBe("1");
  expect(Object.isFrozen(h.result.current.attempt?.body)).toBe(true);
  marketClosed = true;
  await act(async () => {
    await h.result.current.refreshContext();
  });
  act(() => {
    h.result.current.setQuantity("3");
    h.result.current.setSide("sell");
  });
  expect(h.result.current.quantity).toBe("2");
  await act(async () => {
    await h.result.current.checkResult();
  });
  await waitFor(() => expect(h.result.current.phase).toBe("filled"));
  expect(bodies).toHaveLength(2);
  expect(bodies[0]).toEqual(bodies[1]);
});
it("hides late fill after root loss while preserving unknown original recovery", async () => {
  const late = deferred();
  let first = true;
  const paths: string[] = [];
  const h = setup((p) => {
    if (p.endsWith("/stock-trades")) {
      paths.push(p);
      if (first) {
        first = false;
        return late.promise;
      }
    }
    return undefined;
  });
  await preview(h);
  let pending!: Promise<void>;
  act(() => {
    pending = h.result.current.confirm();
  });
  await waitFor(() => expect(h.result.current.phase).toBe("submitting"));
  h.one.live.value = false;
  h.rerender({ t: h.two.value, symbol: "AAPL" });
  await act(async () => {
    late.resolve(json(fill()));
    await pending;
  });
  expect(h.result.current.fill).toBeNull();
  expect(h.result.current.attempt).toBeNull();
  expect(h.result.current.phase).toBe("draft");
  h.rerender({ t: h.target().value, symbol: "AAPL" });
  await waitFor(() => expect(h.result.current.phase).toBe("unknown"));
  await act(async () => {
    await h.result.current.checkResult();
  });
  await waitFor(() => expect(h.result.current.phase).toBe("filled"));
  expect(paths).toEqual(["/api/v2/portfolios/1/stock-trades", "/api/v2/portfolios/1/stock-trades"]);
});
it("refuses stale confirm/recovery callbacks before network on unavailable target", async () => {
  const h = setup();
  await preview(h);
  const confirm = h.result.current.confirm;
  const before = h.fetch.mock.calls.length;
  h.one.live.value = false;
  h.rerender({ t: null, symbol: "AAPL" });
  await act(async () => {
    await confirm();
    await h.result.current.checkResult();
  });
  expect(h.fetch.mock.calls).toHaveLength(before);
  expect(h.result.current.context).toBeUndefined();
  expect(h.result.current.fill).toBeNull();
  expect(h.result.current.canConfirm).toBe(false);
});
it("cannot publish late fill or revive attempts after logout and same-owner return", async () => {
  const late = deferred();
  const h = setup((p) => (p.endsWith("/stock-trades") ? late.promise : undefined));
  await preview(h);
  let pending!: Promise<void>;
  act(() => {
    pending = h.result.current.confirm();
  });
  await waitFor(() => expect(h.result.current.phase).toBe("submitting"));
  act(() => {
    h.client.setQueryData(["me"], null);
    h.client.setQueryData(["me"], { email: alice });
  });
  h.rerender({ t: h.target().value, symbol: "AAPL" });
  await act(async () => {
    late.resolve(json(fill()));
    await pending;
  });
  expect(h.result.current.fill).toBeNull();
  expect(h.result.current.attempt).toBeNull();
});
it("never sends an old owner attempt as another owner", async () => {
  const late = deferred();
  const h = setup((p) => (p.endsWith("/quote") ? late.promise : undefined));
  await waitFor(() => expect(h.result.current.context?.execution_enabled).toBe(true));
  act(() => h.result.current.setQuantity("2"));
  let pending!: Promise<void>;
  act(() => {
    pending = h.result.current.preview();
  });
  h.one.live.value = false;
  act(() => h.client.setQueryData(["me"], { email: bob }));
  h.rerender({ t: h.target("1", bob).value, symbol: "AAPL" });
  await act(async () => {
    late.resolve(json(quote()));
    await pending;
  });
  expect(h.result.current.quote).toBeNull();
  expect(h.result.current.canConfirm).toBe(false);
});
it("rejects a wrong-root receipt as unknown instead of displaying it", async () => {
  const h = setup((p) =>
    p.endsWith("/stock-trades") ? Promise.resolve(json(fill("2"))) : undefined,
  );
  await preview(h);
  await act(async () => {
    await h.result.current.confirm();
  });
  await waitFor(() => expect(h.result.current.phase).toBe("unknown"));
  expect(h.result.current.fill).toBeNull();
  expect(h.result.current.attempt?.body.portfolio_id).toBe("1");
});
it("requires a second confirmation after same-root repricing", async () => {
  let changed = true;
  const economics = {
    ask: "103",
    exact_mid: "101.5",
    exec_price: "103",
    notional: "206",
    cash_delta: "-206",
    cash_after: "9794",
  };
  const h = setup((p) => {
    if (!p.endsWith("/stock-trades")) return undefined;
    if (changed) {
      changed = false;
      return Promise.resolve(
        json(
          {
            detail: {
              code: "price_changed",
              previous_exec_price: "102",
              previous_cash_delta: "-204",
              exec_price_change: "1",
              cash_delta_change: "-2",
              quote: { ...quote(), ...economics },
            },
          },
          409,
        ),
      );
    }
    return Promise.resolve(json({ ...fill(), ...economics }));
  });
  await preview(h);
  await act(async () => {
    await h.result.current.confirm();
  });
  await waitFor(() => expect(h.result.current.replacement).not.toBeNull());
  expect(h.result.current.phase).toBe("preview");
  expect(h.fetch.mock.calls.filter(([p]) => String(p).endsWith("/stock-trades"))).toHaveLength(1);
  await act(async () => {
    await h.result.current.confirm();
  });
  await waitFor(() => expect(h.result.current.phase).toBe("filled"));
});
it("drops preview when market closes but keeps quantity editable and never queues", async () => {
  let marketClosed = false;
  const h = setup((p) =>
    p.endsWith("/context") && marketClosed ? Promise.resolve(json(closed())) : undefined,
  );
  await preview(h);
  marketClosed = true;
  await act(async () => {
    await h.result.current.refreshContext();
  });
  await waitFor(() => expect(h.result.current.canConfirm).toBe(false));
  expect(h.result.current.quantity).toBe("2");
  act(() => h.result.current.setQuantity("4"));
  expect(h.result.current.quantity).toBe("4");
  await act(async () => {
    await h.result.current.confirm();
  });
  expect(h.fetch.mock.calls.some(([p]) => String(p).endsWith("/stock-trades"))).toBe(false);
});
it("revokes unavailable portfolio before retrying an unknown attempt", async () => {
  let unavailable = false;
  const h = setup((p) =>
    p.endsWith("/stock-trades")
      ? unavailable
        ? Promise.resolve(json({ detail: { code: "portfolio_unavailable" } }, 404))
        : Promise.reject(new Error("lost"))
      : undefined,
  );
  await preview(h);
  await act(async () => {
    await h.result.current.confirm();
  });
  await waitFor(() => expect(h.result.current.phase).toBe("unknown"));
  unavailable = true;
  await act(async () => {
    await h.result.current.checkResult();
  });
  const count = h.fetch.mock.calls.length;
  await act(async () => {
    await h.result.current.checkResult();
  });
  expect(h.fetch.mock.calls).toHaveLength(count);
  expect(h.result.current.fill).toBeNull();
  expect(h.result.current.context).toBeUndefined();
});
it("invalidates only the filled root's financial views", async () => {
  const h = setup();
  await preview(h);
  const invalidate = vi.spyOn(h.client, "invalidateQueries");
  await act(async () => {
    await h.result.current.confirm();
  });
  expect(
    invalidate.mock.calls.every(
      ([f]) =>
        ["stocks", "prices"].includes(String(f?.queryKey?.[0])) ||
        (f?.queryKey?.[1] === alice && f?.queryKey?.[2] === "1"),
    ),
  ).toBe(true);
});
