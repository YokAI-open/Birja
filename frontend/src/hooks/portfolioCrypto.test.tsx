import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { afterEach, expect, it, vi } from "vitest";
import type { PortfolioTarget } from "./usePortfolioTarget";
import { usePortfolioTarget } from "./usePortfolioTarget";
import { useQuote } from "./useQuote";
import { useHolding } from "./useHolding";
import { useTrade } from "./useTrade";
import { broadcastMetadataChange } from "@/lib/portfolioMetadataEvents";

const alice = "alice@example.test",
  bob = "bob@example.test";
const order = { symbol: "BTC", side: "buy", amount_usd: "100" } as const;
const variables = () => ({
  order: { ...order },
  expectedMid: "10000",
  idempotencyKey: "original-key",
});
const quote = (id = "1") => ({
  portfolio_id: id,
  symbol: "BTC",
  side: "buy",
  input_kind: "usd",
  input_value: "100",
  mid: "10000",
  as_of: "2026-11-16T12:00:00Z",
  age_seconds: 0,
  exec_price: "10025",
  quantity: "0.00995018",
  notional: "99.75",
  fee: "0.25",
  cash_delta: "-100",
  cash_before: "10000",
  cash_after: "9900",
  held_before: "0",
  held_after: "0.00995018",
  whole_position: false,
});
const fill = (id = "1") => ({ ...quote(id), trade_id: 17, created_at: "2026-11-16T12:00:00Z" });
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
function deferred() {
  let resolve!: (v: Response) => void;
  const promise = new Promise<Response>((r) => {
    resolve = r;
  });
  return { promise, resolve };
}
const clients: QueryClient[] = [];
it.each(["removed", "owner", "logout", "switch"])(
  "suppresses real-target pending crypto publication after %s",
  async (change) => {
    const { wrapper, client } = setup(),
      late = deferred(),
      success = vi.fn(),
      failure = vi.fn();
    let active = true;
    const fetch = vi.fn((input: RequestInfo | URL) =>
      String(input).endsWith("/portfolios")
        ? Promise.resolve(
            json(
              active
                ? [
                    { id: "1", name: "Original" },
                    { id: "2", name: "Other" },
                  ]
                : [{ id: "2", name: "Other" }],
            ),
          )
        : late.promise,
    );
    vi.stubGlobal("fetch", fetch);
    const h = renderHook(
      ({ id }) => {
        const p = usePortfolioTarget(id);
        return { p, t: useTrade(p.target, "BTC") };
      },
      { wrapper, initialProps: { id: "1" } },
    );
    await waitFor(() => expect(h.result.current.p.status).toBe("ready"));
    let pending!: Promise<unknown>;
    const stale = h.result.current.t.mutateAsync;
    act(() => {
      pending = stale(variables(), { onSuccess: success, onError: failure }).catch(() => undefined);
    });
    await waitFor(() => expect(h.result.current.t.isPending).toBe(true));
    if (change === "removed") {
      active = false;
      act(() => broadcastMetadataChange("1"));
      await waitFor(() => expect(h.result.current.p.status).toBe("unavailable"));
    } else if (change === "switch") h.rerender({ id: "2" });
    else act(() => client.setQueryData(["me"], change === "owner" ? { email: bob } : null));
    await act(async () => {
      late.resolve(json(fill()));
      await pending;
    });
    expect(success).not.toHaveBeenCalled();
    expect(failure).not.toHaveBeenCalled();
    expect(h.result.current.t.data).toBeUndefined();
    await waitFor(() => expect(h.result.current.t.attempt).toBeNull());
    await act(async () => {
      await expect(stale(variables())).rejects.toThrow("Portfolio target changed");
    });
    expect(fetch.mock.calls.filter(([path]) => String(path).endsWith("/trades"))).toHaveLength(1);
    if (change === "switch") {
      h.rerender({ id: "1" });
      await waitFor(() => expect(h.result.current.t.outcomeUnknown).toBe(true));
      expect(h.result.current.t.originalName).toBe("Original");
    }
  },
);
it.each(["lost", "pending"])(
  "keeps the real-target crypto original across a %s rename and explicit replay",
  async (mode) => {
    const { client, wrapper } = setup();
    let name = "Original",
      metadataPending = false;
    const late = deferred(),
      metadata = deferred();
    const bodies: string[] = [];
    const fetch = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const path = String(input);
      if (path.endsWith("/portfolios"))
        return metadataPending ? metadata.promise : Promise.resolve(json([{ id: "1", name }]));
      bodies.push(init!.body as string);
      if (bodies.length === 1)
        return mode === "lost" ? Promise.reject(new Error("lost")) : late.promise;
      return Promise.resolve(json(fill()));
    });
    vi.stubGlobal("fetch", fetch);
    const h = renderHook(
      () => {
        const p = usePortfolioTarget("1");
        return { p, t: useTrade(p.target, "BTC") };
      },
      { wrapper },
    );
    await waitFor(() => expect(h.result.current.p.status).toBe("ready"));
    const stale = h.result.current.t.mutateAsync,
      success = vi.fn();
    let pending!: Promise<unknown>;
    act(() => {
      pending = stale(variables(), { onSuccess: success }).catch(() => undefined);
    });
    await waitFor(() => expect(bodies).toHaveLength(1));
    metadataPending = true;
    act(() => broadcastMetadataChange("1"));
    expect(h.result.current.t.data).toBeUndefined();
    await act(async () => {
      await expect(stale(variables())).rejects.toThrow("Portfolio target changed");
    });
    name = "Renamed";
    metadataPending = false;
    await act(async () => {
      metadata.resolve(json([{ id: "1", name }]));
    });
    await waitFor(() => expect(h.result.current.p.target?.name).toBe(name));
    await act(async () => {
      await expect(stale(variables())).rejects.toThrow("Portfolio target changed");
    });
    await act(async () => {
      if (mode === "pending") late.resolve(json(fill()));
      await pending;
    });
    await waitFor(() => expect(h.result.current.t.outcomeUnknown).toBe(true));
    expect(h.result.current.t.originalName).toBe("Original");
    expect(success).not.toHaveBeenCalled();
    expect(h.result.current.t.attempt).toMatchObject({
      portfolio_id: "1",
      expected_mid: "10000",
      idempotency_key: "original-key",
    });
    expect(bodies).toHaveLength(1);
    await act(async () => {
      await h.result.current.t.mutateAsync(variables());
    });
    await waitFor(() => expect(h.result.current.t.data?.portfolio_id).toBe("1"));
    expect(bodies[1]).toBe(bodies[0]);
    act(() => client.setQueryData(["portfolios", alice], []));
    await waitFor(() => expect(h.result.current.p.status).toBe("unavailable"));
    expect(h.result.current.t.data).toBeUndefined();
  },
);
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
  document.cookie = "bj_csrf=test; path=/";
  return { client, wrapper, target };
}
afterEach(() => {
  cleanup();
  clients.splice(0).forEach((c) => c.clear());
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  document.cookie = "bj_csrf=; max-age=0; path=/";
});

it("partitions previews and holdings by owner/root and never carries placeholder cash", async () => {
  const { client, wrapper, target } = setup(),
    first = target(),
    second = target("2");
  const late = deferred();
  const fetch = vi.fn((input: RequestInfo | URL) => {
    const p = String(input),
      id = p.includes("/2/") ? "2" : "1";
    return p.endsWith("/quote") && id === "2"
      ? late.promise
      : Promise.resolve(
          json(
            p.endsWith("/quote") ? quote(id) : { portfolio_id: id, symbol: "BTC", quantity: id },
          ),
        );
  });
  vi.stubGlobal("fetch", fetch);
  const hook = renderHook(({ t }) => ({ q: useQuote(t, order), h: useHolding(t, "BTC") }), {
    wrapper,
    initialProps: { t: first.value },
  });
  await waitFor(() => expect(hook.result.current.q.data?.portfolio_id).toBe("1"));
  expect(hook.result.current.h.data?.quantity).toBe("1");
  first.live.value = false;
  hook.rerender({ t: second.value });
  expect(hook.result.current.q.data).toBeUndefined();
  await act(async () => {
    late.resolve(json(quote("2")));
  });
  await waitFor(() => expect(hook.result.current.q.data?.portfolio_id).toBe("2"));
  expect(
    client
      .getQueryCache()
      .getAll()
      .filter((q) => q.queryKey[0] === "quote")
      .every((q) => q.queryKey[1] === alice),
  ).toBe(true);
});
it("discards a delayed preview after target switch even when transport ignores abort", async () => {
  const { wrapper, target } = setup(),
    first = target(),
    second = target("2"),
    late = deferred();
  vi.stubGlobal(
    "fetch",
    vi.fn((p: RequestInfo | URL) =>
      String(p).includes("/1/") ? late.promise : Promise.resolve(json(quote("2"))),
    ),
  );
  const hook = renderHook(({ t }) => useQuote(t, order), {
    wrapper,
    initialProps: { t: first.value },
  });
  first.live.value = false;
  hook.rerender({ t: second.value });
  await waitFor(() => expect(hook.result.current.data?.portfolio_id).toBe("2"));
  await act(async () => {
    late.resolve(json(quote("1")));
  });
  expect(hook.result.current.data?.portfolio_id).toBe("2");
});
it.each(["quote", "holding"])(
  "hides old %s financial data after unavailable refetch",
  async (kind) => {
    const { wrapper, target } = setup(),
      t = target();
    let unavailable = false;
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(
          unavailable
            ? json({ detail: { code: "portfolio_unavailable" } }, 404)
            : json(
                kind === "quote" ? quote() : { portfolio_id: "1", symbol: "BTC", quantity: "2" },
              ),
        ),
      ),
    );
    const { result } = renderHook(
      () => ({ q: useQuote(t.value, order), h: useHolding(t.value, "BTC") }),
      { wrapper },
    );
    await waitFor(() =>
      expect((kind === "quote" ? result.current.q : result.current.h).data).toBeDefined(),
    );
    unavailable = true;
    await act(async () => {
      await (kind === "quote" ? result.current.q : result.current.h).refetch();
    });
    await waitFor(() =>
      expect((kind === "quote" ? result.current.q : result.current.h).data).toBeUndefined(),
    );
  },
);
it.each([0, 1, 2])(
  "legacy discovery with %i portfolios never starts financial requests",
  async (count) => {
    const { wrapper } = setup();
    const fetch = vi.fn(() =>
      Promise.resolve(
        json(Array.from({ length: count }, (_, i) => ({ id: String(i + 1), name: "Strategy" }))),
      ),
    );
    vi.stubGlobal("fetch", fetch);
    const { result } = renderHook(
      () => {
        const discovery = usePortfolioTarget(undefined, { legacyEntry: true });
        const preview = useQuote(discovery.target, order);
        return { discovery, preview };
      },
      { wrapper },
    );
    await waitFor(() =>
      expect(result.current.discovery.status).toBe(["empty", "redirect", "ambiguous"][count]),
    );
    expect(result.current.preview.data).toBeUndefined();
    expect(fetch.mock.calls).toHaveLength(1);
  },
);
it("never submits or displays finance for a missing/unavailable target", async () => {
  const { wrapper } = setup(),
    fetch = vi.fn();
  vi.stubGlobal("fetch", fetch);
  const { result } = renderHook(
    () => ({ q: useQuote(null, order), h: useHolding(null, "BTC"), t: useTrade(null, "BTC") }),
    { wrapper },
  );
  await act(async () => {
    await expect(result.current.t.mutateAsync(variables())).rejects.toThrow(
      "Portfolio target changed",
    );
  });
  expect(fetch).not.toHaveBeenCalled();
  expect(result.current.t.data).toBeUndefined();
});
it("retains a deep-frozen unknown original and only retries the original payload/root", async () => {
  const { wrapper, target } = setup(),
    one = target(),
    two = target("2");
  let lost = true;
  const fetch = vi.fn((p: RequestInfo | URL) => {
    if (lost) {
      lost = false;
      return Promise.reject(new TypeError("lost"));
    }
    return Promise.resolve(json(fill(String(p).includes("/2/") ? "2" : "1")));
  });
  vi.stubGlobal("fetch", fetch);
  const hook = renderHook(({ t }) => useTrade(t, "BTC"), {
    wrapper,
    initialProps: { t: one.value },
  });
  const input = variables();
  await act(async () => {
    await expect(hook.result.current.mutateAsync(input)).rejects.toThrow("lost");
  });
  await waitFor(() => expect(hook.result.current.outcomeUnknown).toBe(true));
  input.order.amount_usd = "999" as "100";
  expect(hook.result.current.attempt?.order.amount_usd).toBe("100");
  expect(Object.isFrozen(hook.result.current.attempt?.order)).toBe(true);
  act(() => hook.result.current.reset());
  expect(hook.result.current.outcomeUnknown).toBe(true);
  await act(async () => {
    await expect(
      hook.result.current.mutateAsync({ ...variables(), idempotencyKey: "new" }),
    ).rejects.toThrow("Original trade attempt");
  });
  one.live.value = false;
  hook.rerender({ t: two.value });
  expect(hook.result.current.attempt).toBeNull();
  expect(hook.result.current.data).toBeUndefined();
  const returned = target();
  hook.rerender({ t: returned.value });
  await waitFor(() => expect(hook.result.current.outcomeUnknown).toBe(true));
  await act(async () => {
    await hook.result.current.mutateAsync(variables());
  });
  await waitFor(() => expect(hook.result.current.data?.portfolio_id).toBe("1"));
  expect(fetch).toHaveBeenCalledTimes(2);
  expect(fetch.mock.calls.map((c) => String(c[0]))).toEqual([
    "/api/v2/portfolios/1/trades",
    "/api/v2/portfolios/1/trades",
  ]);
});
it("ignores stale callbacks/receipt after a root switch and preserves original recovery", async () => {
  const { wrapper, target } = setup(),
    one = target(),
    two = target("2"),
    late = deferred(),
    success = vi.fn(),
    failure = vi.fn();
  vi.stubGlobal(
    "fetch",
    vi.fn(() => late.promise),
  );
  const hook = renderHook(({ t }) => useTrade(t, "BTC"), {
    wrapper,
    initialProps: { t: one.value },
  });
  let pending!: Promise<unknown>;
  act(() => {
    pending = hook.result.current
      .mutateAsync(variables(), { onSuccess: success, onError: failure })
      .catch(() => undefined);
  });
  await waitFor(() => expect(hook.result.current.isPending).toBe(true));
  one.live.value = false;
  hook.rerender({ t: two.value });
  await act(async () => {
    late.resolve(json(fill()));
    await pending;
  });
  expect(hook.result.current.data).toBeUndefined();
  expect(success).not.toHaveBeenCalled();
  expect(failure).not.toHaveBeenCalled();
  hook.rerender({ t: target().value });
  await waitFor(() => expect(hook.result.current.outcomeUnknown).toBe(true));
  expect(hook.result.current.attempt?.portfolio_id).toBe("1");
});
it("does not resurrect cached attempts after logout and returning as the same owner", async () => {
  const { wrapper, target, client } = setup(),
    t = target(),
    late = deferred();
  vi.stubGlobal(
    "fetch",
    vi.fn(() => late.promise),
  );
  const hook = renderHook(({ t }) => useTrade(t, "BTC"), { wrapper, initialProps: { t: t.value } });
  let pending!: Promise<unknown>;
  act(() => {
    pending = hook.result.current.mutateAsync(variables()).catch(() => undefined);
  });
  await waitFor(() => expect(hook.result.current.isPending).toBe(true));
  act(() => {
    client.setQueryData(["me"], null);
    client.setQueryData(["me"], { email: alice });
  });
  hook.rerender({ t: target().value });
  await act(async () => {
    late.resolve(json(fill()));
    await pending;
  });
  expect(hook.result.current.data).toBeUndefined();
  expect(hook.result.current.attempt).toBeNull();
});
it("never invalidates sibling financial views after an original fill", async () => {
  const { wrapper, target, client } = setup(),
    t = target();
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.resolve(json(fill()))),
  );
  const invalidate = vi.spyOn(client, "invalidateQueries");
  const { result } = renderHook(() => useTrade(t.value, "BTC"), { wrapper });
  await act(async () => {
    await result.current.mutateAsync(variables());
  });
  expect(
    invalidate.mock.calls.every(
      ([filters]) =>
        filters?.queryKey?.[0] === "prices" ||
        (filters?.queryKey?.[1] === alice && filters?.queryKey?.[2] === "1"),
    ),
  ).toBe(true);
});
it("refuses crossed-root receipts rather than publishing them", async () => {
  const { wrapper, target } = setup(),
    t = target();
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.resolve(json(fill("2")))),
  );
  const { result } = renderHook(() => useTrade(t.value, "BTC"), { wrapper });
  await act(async () => {
    await expect(result.current.mutateAsync(variables())).rejects.toThrow(
      "Unexpected trade response",
    );
  });
  expect(result.current.data).toBeUndefined();
  await waitFor(() => expect(result.current.attempt?.portfolio_id).toBe("1"));
});
it("refuses a stale owner callback before any transport", async () => {
  const { wrapper, target, client } = setup(),
    t = target();
  const fetch = vi.fn();
  vi.stubGlobal("fetch", fetch);
  const { result } = renderHook(() => useTrade(t.value, "BTC"), { wrapper });
  const stale = result.current.mutateAsync;
  act(() => client.setQueryData(["me"], { email: bob }));
  await act(async () => {
    await expect(stale(variables())).rejects.toThrow("Portfolio target changed");
  });
  expect(fetch).not.toHaveBeenCalled();
});

it("blocks duplicate pending submission and freezes its original payload", async () => {
  const { wrapper, target } = setup(),
    t = target(),
    late = deferred();
  const fetch = vi.fn(() => late.promise);
  vi.stubGlobal("fetch", fetch);
  const { result } = renderHook(() => useTrade(t.value, "BTC"), { wrapper });
  let pending!: Promise<unknown>;
  const input = variables();
  act(() => {
    pending = result.current.mutateAsync(input);
  });
  await waitFor(() => expect(result.current.isPending).toBe(true));
  input.order.amount_usd = "999" as "100";
  expect(result.current.attempt?.order.amount_usd).toBe("100");
  await act(async () => {
    await expect(result.current.mutateAsync(variables())).rejects.toThrow("Original trade attempt");
  });
  await act(async () => {
    late.resolve(json(fill()));
    await pending;
  });
  expect(fetch).toHaveBeenCalledTimes(1);
});
it("revokes a server-unavailable root while preserving only its hidden unknown attempt", async () => {
  const { wrapper, target, client } = setup(),
    t = target();
  client.setQueryData(
    ["portfolios", alice],
    [
      { id: "1", name: "Strategy 1" },
      { id: "2", name: "Strategy 2" },
    ],
  );
  const fetch = vi.fn(() =>
    Promise.resolve(json({ detail: { code: "portfolio_unavailable" } }, 404)),
  );
  vi.stubGlobal("fetch", fetch);
  const { result } = renderHook(() => useTrade(t.value, "BTC"), { wrapper });
  await act(async () => {
    await expect(result.current.mutateAsync(variables())).rejects.toThrow();
  });
  await waitFor(() => expect(result.current.data).toBeUndefined());
  await act(async () => {
    await expect(result.current.mutateAsync(variables())).rejects.toThrow(
      "Portfolio target changed",
    );
  });
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(client.getQueryData(["portfolios", alice])).toEqual([{ id: "2", name: "Strategy 2" }]);
  expect(result.current.isPending).toBe(false);
  expect(result.current.attempt).toBeNull();
});
