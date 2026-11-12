import { afterEach, it, expect, vi } from "vitest";
import { act, renderHook, waitFor, cleanup } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { usePortfolio } from "./usePortfolio";
import { mixedPortfolio } from "@/test/portfolioFixtures";
import type { Portfolio } from "@/api/portfolio";
const clients: QueryClient[] = [];
function setup() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: Infinity } } }); clients.push(client);
  client.setQueryData(["me"], { email: "first@example.test", cash_usd: "9796" });
  const wrapper = ({ children }: { children: ReactNode }) => <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  return { client, ...renderHook(() => usePortfolio(), { wrapper }) };
}
afterEach(() => { cleanup(); clients.forEach(c => c.clear()); clients.length = 0; vi.restoreAllMocks(); vi.unstubAllGlobals(); vi.useRealTimers(); });
function mock(body = mixedPortfolio()) {
  vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response(JSON.stringify(body)))));
}
it("purges expired stock marks and dependent summaries from cache, without inventing a new subtotal", async () => {
  let clock = 0; vi.spyOn(performance, "now").mockImplementation(() => clock); mock();
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
  let clock = 0; vi.spyOn(performance, "now").mockImplementation(() => clock);
  const p = mixedPortfolio(); p.holdings[0].stock_mark!.mark_mode = "closed";
  p.holdings[0].stock_mark!.valid_until = "2026-11-10T16:00:00Z";
  mock(p); const { result } = setup();
  await waitFor(() => expect(result.current.data).toBeDefined());
  clock = 180_000; act(() => window.dispatchEvent(new Event("visibilitychange")));
  expect(result.current.data?.holdings[0].mid).toBe("101.000000000");
  clock = 3_590_000; act(() => window.dispatchEvent(new Event("focus")));
  expect(result.current.data?.holdings[0].mid).toBeNull();
});
