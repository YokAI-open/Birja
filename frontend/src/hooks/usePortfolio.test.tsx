import { afterEach, it, expect, vi } from "vitest";
import { act, renderHook, waitFor, cleanup } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { usePortfolio } from "./usePortfolio";
import { mixedPortfolio } from "@/test/portfolioFixtures";
import { contextFixture } from "@/test/stockTradeFixtures";
import type { Portfolio } from "@/api/portfolio";
const clients: QueryClient[] = [];
function setup() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: Infinity } },
  });
  clients.push(client);
  client.setQueryData(["me"], { email: "first@example.test", cash_usd: "9796" });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return { client, ...renderHook(() => usePortfolio(), { wrapper }) };
}
afterEach(() => {
  cleanup();
  clients.forEach((c) => c.clear());
  clients.length = 0;
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});
function mock(body = mixedPortfolio()) {
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.resolve(new Response(JSON.stringify(body)))),
  );
}
it("purges expired stock marks and dependent summaries from cache, without inventing a new subtotal", async () => {
  let clock = 0;
  vi.spyOn(performance, "now").mockImplementation(() => clock);
  mock();
  const { result, client } = setup();
  await waitFor(() => expect(result.current.data?.total_value).toBe("9998.00"));
  clock = 50_000;
  act(() => window.dispatchEvent(new Event("focus")));
  expect(result.current.data?.holdings[0].mid).toBeNull();
  expect(result.current.data?.known_value).toBeNull();
  expect(result.current.data?.total_value).toBeNull();
  const cached = client.getQueryData<Portfolio>(["portfolio", "first@example.test"]);
  expect(cached?.holdings[0].mid).toBeNull();
  expect(cached?.known_value).toBeNull();
  expect(cached?.cash).toBe("9796.00");
});
it("a permitted closed mark survives execution age but not original retention expiry", async () => {
  let clock = 0;
  vi.spyOn(performance, "now").mockImplementation(() => clock);
  const p = mixedPortfolio();
  p.holdings[0].stock_mark!.mark_mode = "closed";
  p.holdings[0].stock_mark!.valid_until = "2026-11-10T16:00:00Z";
  mock(p);
  const { result } = setup();
  await waitFor(() => expect(result.current.data).toBeDefined());
  clock = 180_000;
  act(() => window.dispatchEvent(new Event("visibilitychange")));
  expect(result.current.data?.holdings[0].mid).toBe("101.000000000");
  clock = 3_590_000;
  act(() => window.dispatchEvent(new Event("focus")));
  expect(result.current.data?.holdings[0].mid).toBeNull();
});
it("newer split epochs suppress delayed old units in both cache and view", async () => {
  mock();
  const { result, client } = setup();
  await waitFor(() => expect(result.current.data?.holdings[0].mid).not.toBeNull());
  const key = ["portfolio", "first@example.test"];
  const old = client.getQueryData(key)!;
  const current = structuredClone(old) as ReturnType<typeof mixedPortfolio>;
  current.valued_at = "2026-11-10T15:00:11Z";
  current.holdings[0].stock_mark!.authority!.unit_epoch = 1;
  act(() => client.setQueryData(key, current));
  act(() => client.setQueryData(key, old));
  expect(result.current.data?.holdings[0].stock_mark?.authority?.unit_epoch).toBe(1);
});
it("same-generation changed admission hash cannot restore a mark on a later timestamp", async () => {
  mock();
  const { result, client } = setup();
  await waitFor(() => expect(result.current.data?.total_value).toBe("9998.00"));
  const key = ["portfolio", "first@example.test"];
  const p = structuredClone(client.getQueryData(key)) as ReturnType<typeof mixedPortfolio>;
  p.holdings[0].stock_mark!.authority!.admissions[0].row_hash = "b".repeat(64);
  p.valued_at = "2026-11-10T15:00:11Z";
  act(() => client.setQueryData(key, p));
  expect(result.current.data?.holdings[0].mid).toBeNull();
  p.valued_at = "2026-11-10T15:00:12Z";
  act(() => client.setQueryData(key, structuredClone(p)));
  expect(result.current.data?.holdings[0].mid).toBeNull();
});
it("auth changes discard a pending old-user reply and remove the old private cache", async () => {
  let finish!: (r: Response) => void;
  vi.stubGlobal(
    "fetch",
    vi.fn(
      () =>
        new Promise<Response>((resolve) => {
          finish = resolve;
        }),
    ),
  );
  const { result, client } = setup();
  await waitFor(() => expect(finish).toBeTypeOf("function"));
  act(() => client.setQueryData(["me"], null));
  await act(async () => {
    finish(new Response(JSON.stringify(mixedPortfolio())));
  });
  expect(result.current.data).toBeUndefined();
  expect(client.getQueryData(["portfolio", "first@example.test"])).toBeUndefined();
});
it("full transport time exhausting the mark suppresses the first result", async () => {
  let clock = 0;
  vi.spyOn(performance, "now").mockImplementation(() => clock);
  vi.stubGlobal(
    "fetch",
    vi.fn(() => {
      clock = 50_000;
      return Promise.resolve(new Response(JSON.stringify(mixedPortfolio())));
    }),
  );
  const { result } = setup();
  await waitFor(() => expect(result.current.data).toBeDefined());
  expect(result.current.data?.known_value).toBeNull();
  expect(result.current.data?.holdings[0].mid).toBeNull();
});
it("exact deadline timers remove values without waiting for the display interval", async () => {
  vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout", "setInterval", "clearInterval"] });
  let clock = 0;
  vi.spyOn(performance, "now").mockImplementation(() => clock);
  const p = mixedPortfolio();
  p.holdings[0].stock_mark!.valid_until = "2026-11-10T15:00:10.125Z";
  mock(p);
  const { result, client } = setup();
  await act(async () => {
    for (let i = 0; i < 8; i++) await vi.advanceTimersByTimeAsync(0);
  });
  expect(result.current.data?.total_value).toBe("9998.00");
  clock = 125;
  await act(async () => {
    await vi.advanceTimersByTimeAsync(125);
  });
  expect(result.current.data?.known_value).toBeNull();
  expect(
    client.getQueryData<Portfolio>(["portfolio", "first@example.test"])?.holdings[0].mid,
  ).toBeNull();
});
it("a later old restrictive response suppresses current values without rolling cash back", async () => {
  mock();
  const { result, client } = setup();
  await waitFor(() => expect(result.current.data?.total_value).toBe("9998.00"));
  const key = ["portfolio", "first@example.test"];
  const older = structuredClone(client.getQueryData(key)) as ReturnType<typeof mixedPortfolio>;
  older.valued_at = "2026-11-10T15:00:09Z";
  older.cash = "9000";
  Object.assign(older.holdings[0].stock_mark!, {
    mark_mode: "unavailable",
    authority: null,
    valid_until: null,
    units_safe: false,
  });
  act(() => client.setQueryData(key, older));
  expect(result.current.data?.cash).toBe("9796.00");
  expect(result.current.data?.holdings[0].mid).toBeNull();
  expect(result.current.data?.known_value).toBeNull();
});
it("an independently observed halt cannot leave a cached fresh stock mark advertised live", async () => {
  mock();
  const { result, client } = setup();
  await waitFor(() => expect(result.current.data?.total_value).toBe("9998.00"));
  const c = contextFixture();
  Object.assign(c, {
    execution_enabled: false,
    execution_reason: "halted",
    quote: null,
    valid_until: null,
    buy_max_quantity: "0",
  });
  c.status.state = "halted";
  act(() => client.setQueryData(["stockContext", "first@example.test", "AAPL"], c));
  expect(result.current.data?.holdings[0].mid).toBeNull();
  expect(result.current.data?.known_value).toBeNull();
});
