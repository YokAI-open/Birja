import { portfolioTargetFixture } from "@/test/portfolioTargetFixture";
import { afterEach, expect, it, vi } from "vitest";
import { act, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider, focusManager } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { useHistory } from "./useHistory";

const cursor = (id: string) =>
  btoa(JSON.stringify({ v: 2, portfolio_id: "1", created_at: "2026-10-30T08:01:02.123456Z", id }))
    .replace(/=/g, "")
    .replace(/\+/g, "-")
    .replace(/\//g, "_");
const item = (id: string) => ({
  id,
  created_at: "2026-10-30T08:01:02.123456Z",
  symbol: "BTC",
  name: "Bitcoin",
  side: "buy",
  quantity: "1",
  exec_price: "100",
  fee: "0.25",
  total: "-100.25",
});
const page = (ids: string[], next_cursor: string | null) =>
  new Response(JSON.stringify({ items: ids.map(item), next_cursor }));
afterEach(() => {
  vi.unstubAllGlobals();
  focusManager.setFocused(undefined);
});

it("refetches the loaded chain sequentially with new boundaries after newer fills and retains it on failure", async () => {
  const fetch = vi
    .fn()
    .mockResolvedValueOnce(page(["9"], cursor("9")))
    .mockResolvedValueOnce(page(["8"], cursor("8")))
    .mockResolvedValueOnce(page(["7"], cursor("7")))
    .mockResolvedValueOnce(page(["10"], cursor("10")))
    .mockResolvedValueOnce(page(["9"], cursor("9")))
    .mockResolvedValueOnce(page(["8"], cursor("8")))
    .mockResolvedValueOnce(page(["11"], cursor("11")))
    .mockResolvedValueOnce(new Response("{}", { status: 500 }));
  vi.stubGlobal("fetch", fetch);
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  client.setQueryDefaults(["me"], { gcTime: Infinity });
  client.setQueryData(["me"], { email: "first@example.test" });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  const { result, unmount } = renderHook(
    () => ({ ...useHistory(portfolioTargetFixture(client)) }),
    { wrapper },
  );
  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  await act(async () => {
    const next = await result.current.fetchNextPage();
    expect(next.error).toBeNull();
  });
  await waitFor(() => expect(result.current.data?.pages).toHaveLength(2));
  await act(async () => {
    await result.current.fetchNextPage();
  });
  await waitFor(() => expect(result.current.data?.pages).toHaveLength(3));
  expect(result.current.data?.pages.flatMap((p) => p.items.map((i) => i.id))).toEqual([
    "9",
    "8",
    "7",
  ]);
  act(() => {
    focusManager.setFocused(false);
    focusManager.setFocused(true);
  });
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(6));
  await waitFor(() => expect(result.current.isFetching).toBe(false));
  expect(result.current.data?.pages.flatMap((p) => p.items.map((i) => i.id))).toEqual([
    "10",
    "9",
    "8",
  ]);
  await act(async () => {
    await result.current.refetch();
  });
  await waitFor(() => expect(result.current.isRefetchError).toBe(true));
  expect(result.current.data?.pages.map((p) => p.next_cursor)).toEqual([
    cursor("10"),
    cursor("9"),
    cursor("8"),
  ]);
  expect(result.current.data?.pages.flatMap((p) => p.items.map((i) => i.id))).toEqual([
    "10",
    "9",
    "8",
  ]);
  expect(fetch.mock.calls.map((args) => String(args[0]))).toEqual([
    "/api/v2/portfolios/1/history",
    `/api/v2/portfolios/1/history?cursor=${cursor("9")}`,
    `/api/v2/portfolios/1/history?cursor=${cursor("8")}`,
    "/api/v2/portfolios/1/history",
    `/api/v2/portfolios/1/history?cursor=${cursor("10")}`,
    `/api/v2/portfolios/1/history?cursor=${cursor("9")}`,
    "/api/v2/portfolios/1/history",
    `/api/v2/portfolios/1/history?cursor=${cursor("11")}`,
  ]);
  unmount();
  client.clear();
});
