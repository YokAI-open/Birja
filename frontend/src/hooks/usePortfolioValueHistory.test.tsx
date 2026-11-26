import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { afterEach, expect, it, vi } from "vitest";
import { broadcastMetadataChange } from "@/lib/portfolioMetadataEvents";
import { cashPortfolio } from "@/test/portfolioFixtures";
import { usePortfolioOverview } from "./usePortfolioOverview";
import { usePortfolioValueHistory } from "./usePortfolioValueHistory";

const alice = "alice@example.test";
const bob = "bob@example.test";
const overviewPath = "/api/v2/portfolios/overview";
const historyPath = "/api/v2/portfolios/value-history";
const clients: QueryClient[] = [];
function rows(...ids: string[]) {
  const { portfolio_id: id, ...body } = cashPortfolio();
  void id;
  return ids.map((id) => ({ ...body, id, name: `Strategy ${id}`, description: "" }));
}
function history(...ids: string[]) {
  return Response.json({
    start_day: "2026-10-28",
    end_day: "2026-11-26",
    portfolios: ids.map((portfolio_id) => ({ portfolio_id, points: [] })),
  });
}
function deferred() {
  let resolve!: (value: Response) => void;
  const promise = new Promise<Response>((done) => {
    resolve = done;
  });
  return { resolve, promise };
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
  const hook = renderHook(
    () => {
      const overview = usePortfolioOverview();
      const trend = usePortfolioValueHistory(
        overview.membershipUncertain ? undefined : overview.data,
      );
      return { overview, trend };
    },
    { wrapper },
  );
  return { client, hook };
}
afterEach(() => {
  cleanup();
  clients.splice(0).forEach((client) => client.clear());
  vi.unstubAllGlobals();
  sessionStorage.clear();
});

it("keeps current values through a malformed history response and retries only history", async () => {
  let attempt = 0;
  const fetch = vi.fn(async (url: string) => {
    if (url === overviewPath) return Response.json(rows("1", "2"));
    return attempt++ === 0 ? history("1", "3") : history("1", "2");
  });
  vi.stubGlobal("fetch", fetch);
  const { hook } = setup();
  await waitFor(() => expect(hook.result.current.trend.failed).toBe(true));
  expect(hook.result.current.overview.data?.map(({ total_value }) => total_value)).toEqual([
    "10000.00",
    "10000.00",
  ]);
  act(() => hook.result.current.trend.retry());
  await waitFor(() => expect(hook.result.current.trend.data?.portfolios).toHaveLength(2));
  expect(fetch.mock.calls.map(([url]) => url)).toEqual([overviewPath, historyPath, historyPath]);
});

it("discards a late response across sign-out and an owner change even when the IDs match", async () => {
  const old = deferred();
  let calls = 0;
  const fetch = vi.fn((url: string, _init?: RequestInit) => {
    if (url === overviewPath) return Promise.resolve(Response.json(rows("1")));
    return calls++ === 0 ? old.promise : Promise.resolve(history("1"));
  });
  vi.stubGlobal("fetch", fetch);
  const { client, hook } = setup();
  await waitFor(() => expect(calls).toBe(1));
  const oldSignal = fetch.mock.calls.find(([url]) => url === historyPath)?.[1]?.signal;
  act(() => {
    client.setQueryData(["me"], null);
  });
  expect(hook.result.current.trend.data).toBeUndefined();
  act(() => {
    client.setQueryData(["me"], { email: bob });
  });
  await waitFor(() => expect(hook.result.current.trend.data?.portfolios).toHaveLength(1));
  const result = hook.result.current.trend.data;
  await act(async () => old.resolve(history("999")));
  expect(hook.result.current.trend.data).toBe(result);
  expect(oldSignal?.aborted).toBe(true);
});

it("fences the original active set when a deletion hint arrives before overview refresh", async () => {
  const old = deferred();
  const nextOverview = deferred();
  let overviews = 0;
  let histories = 0;
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) => {
      if (url === overviewPath)
        return overviews++ === 0
          ? Promise.resolve(Response.json(rows("1", "2")))
          : nextOverview.promise;
      return histories++ === 0 ? old.promise : Promise.resolve(history("2"));
    }),
  );
  const { hook } = setup();
  await waitFor(() => expect(histories).toBe(1));
  act(() => broadcastMetadataChange("1", "lifecycle"));
  await act(async () => old.resolve(history("1", "2")));
  expect(hook.result.current.trend.data).toBeUndefined();
  expect(hook.result.current.overview.data?.map(({ id }) => id)).toEqual(["2"]);
  await act(async () => nextOverview.resolve(Response.json(rows("2"))));
  await waitFor(() =>
    expect(
      hook.result.current.trend.data?.portfolios.map(({ portfolio_id }) => portfolio_id),
    ).toEqual(["2"]),
  );
});
