import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { afterEach, expect, it, vi } from "vitest";
import { cashPortfolio, mixedPortfolio } from "@/test/portfolioFixtures";
import { contextFixture } from "@/test/stockTradeFixtures";
import { usePortfolioOverview } from "./usePortfolioOverview";

const alice = "alice@example.test", bob = "bob@example.test";
const clients: QueryClient[] = [];
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
function row(id = "1", stock = false) {
  const { portfolio_id: _id, ...body } = stock ? mixedPortfolio() : cashPortfolio();
  void _id;
  return { ...body, id, name: "Strategy " + id, description: "Book " + id };
}
function deferred() {
  let resolve!: (value: Response) => void;
  const promise = new Promise<Response>((done) => { resolve = done; });
  return { resolve, promise };
}
function setup() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: Infinity } } });
  clients.push(client);
  client.setQueryData(["me"], { email: alice });
  vi.spyOn(performance, "now").mockReturnValue(0);
  const wrapper = ({ children }: { children: ReactNode }) => <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  return { client, wrapper };
}
afterEach(() => {
  cleanup(); clients.splice(0).forEach((client) => client.clear());
  vi.restoreAllMocks(); vi.unstubAllGlobals();
});
it.each([0, 1, 10])("publishes %s exact independent books in server order through one query", async (count) => {
  const { client, wrapper } = setup();
  const rows = Array.from({ length: count }, (_, index) => row(String(index + 1)));
  const fetch = vi.fn(() => Promise.resolve(json(rows)));
  vi.stubGlobal("fetch", fetch);
  const hook = renderHook(() => usePortfolioOverview(), { wrapper });
  await waitFor(() => expect(hook.result.current.data).toHaveLength(count));
  expect(hook.result.current.data?.map((r) => r.id)).toEqual(rows.map((r) => r.id));
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(client.getQueryData(["portfolioOverview", alice, 0])).toBeDefined();
});
it("does not fetch private rows while signed out", async () => {
  const { client, wrapper } = setup();
  client.setQueryData(["me"], null);
  const fetch = vi.fn(); vi.stubGlobal("fetch", fetch);
  const hook = renderHook(() => usePortfolioOverview(), { wrapper });
  await act(async () => { await expect(hook.result.current.refetch()).rejects.toThrow("Overview session changed"); });
  expect(hook.result.current.data).toBeUndefined(); expect(fetch).not.toHaveBeenCalled();
});
it.each([null, bob, alice])("masks warm rows synchronously across logout/return to %s and rejects captured refresh", async (next) => {
  const { client, wrapper } = setup();
  const late = deferred();
  let refresh = false;
  vi.stubGlobal("fetch", vi.fn(() => refresh ? late.promise : Promise.resolve(json([row("1")]))));
  const hook = renderHook(() => usePortfolioOverview(), { wrapper });
  await waitFor(() => expect(hook.result.current.data?.[0].id).toBe("1"));
  const oldRefresh = hook.result.current.refetch;
  refresh = true;
  act(() => { client.setQueryData(["me"], null); if (next) client.setQueryData(["me"], { email: next }); });
  expect(hook.result.current.data).toBeUndefined();
  expect(client.getQueryData(["portfolioOverview", alice, 0])).toBeUndefined();
  await act(async () => { await expect(oldRefresh()).rejects.toThrow("Overview session changed"); late.resolve(json([row("2")])); });
});
it("discards old-owner replies including late401 while the new owner is active", async () => {
  const { client, wrapper } = setup(); const late = deferred();
  let owner = alice;
  document.cookie = "bj_csrf=; max-age=0; path=/";
  vi.stubGlobal("fetch", vi.fn(() => owner === alice ? late.promise : Promise.resolve(json([row("2")]))));
  const hook = renderHook(() => usePortfolioOverview(), { wrapper });
  owner = bob; act(() => client.setQueryData(["me"], { email: bob }));
  await waitFor(() => expect(hook.result.current.data?.[0].id).toBe("2"));
  await act(async () => { late.resolve(json({}, 401)); });
  expect(client.getQueryData(["me"])).toEqual({ email: bob });
  expect(hook.result.current.data?.[0].id).toBe("2");
});
it("retains only safe permitted rows after failed refresh and expires stock proof per book", async () => {
  const { wrapper } = setup(); let failed = false;
  vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(failed ? json({}, 503) : json([row("1", true), row("2")]))));
  const hook = renderHook(() => usePortfolioOverview(), { wrapper });
  await waitFor(() => expect(hook.result.current.data?.[0].total_value).toBe("9998.00"));
  failed = true;
  await act(async () => { await hook.result.current.refetch(); });
  expect(hook.result.current.isError).toBe(true);
  expect(hook.result.current.data?.[0].total_value).toBe("9998.00");
  vi.mocked(performance.now).mockReturnValue(50_000);
  act(() => window.dispatchEvent(new Event("focus")));
  expect(hook.result.current.data?.[0]).toMatchObject({ cash: "9796.00", total_value: null, total_pl_percent: null, known_value: null, valuation_complete: false });
  expect(hook.result.current.data?.[0].holdings[0].mid).toBeNull();
  expect(hook.result.current.data?.[1].total_value).toBe("10000.00");
});
it("shares root stock restrictions with detail caches without contaminating siblings", async () => {
  const { client, wrapper } = setup();
  vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(json([row("1", true), row("2", true)]))));
  const hook = renderHook(() => usePortfolioOverview(), { wrapper });
  await waitFor(() => expect(hook.result.current.data?.[0].total_value).toBe("9998.00"));
  const context = contextFixture(); context.action.state = "frozen";
  act(() => client.setQueryData(["stockContext", alice, "1", 0, "AAPL"], context));
  expect(hook.result.current.data?.[0].total_value).toBeNull();
  expect(hook.result.current.data?.[1].total_value).toBe("9998.00");
  act(() => client.removeQueries({ queryKey: ["stockContext", alice, "1"] }));
  await act(async () => { await hook.result.current.refetch(); });
  expect(hook.result.current.data?.[0].total_value).toBeNull();
});
it("does not renew source proof when receiving the same expired statement again", async () => {
  const { wrapper } = setup();
  vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(json([row("1", true)]))));
  const hook = renderHook(() => usePortfolioOverview(), { wrapper });
  await waitFor(() => expect(hook.result.current.data?.[0].total_value).toBe("9998.00"));
  vi.mocked(performance.now).mockReturnValue(60_000);
  await act(async () => { await hook.result.current.refetch(); });
  expect(hook.result.current.data?.[0].total_value).toBeNull();
  expect(hook.result.current.data?.[0].valued_at).toBe("2026-11-10T15:00:10Z");
});
it("keeps malformed first responses as errors and never invents an empty success", async () => {
  const { wrapper } = setup();
  vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(json([{ ...row(), cash: 10000 }]))));
  const hook = renderHook(() => usePortfolioOverview(), { wrapper });
  await waitFor(() => expect(hook.result.current.isError).toBe(true));
  expect(hook.result.current.data).toBeUndefined();
});
it("keeps initial loading distinct and ignores a reply after query replacement", async () => {
  const { client, wrapper } = setup(); const late = deferred();
  vi.stubGlobal("fetch", vi.fn(() => late.promise));
  const hook = renderHook(() => usePortfolioOverview(), { wrapper });
  expect(hook.result.current.isPending).toBe(true); expect(hook.result.current.data).toBeUndefined();
  act(() => client.removeQueries({ queryKey: ["portfolioOverview", alice, 0] }));
  await act(async () => { late.resolve(json([row()])); });
  expect(hook.result.current.data).toBeUndefined();
});
