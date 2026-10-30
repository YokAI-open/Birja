import { afterEach, expect, it, vi } from "vitest";
import { act, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider, focusManager } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { useHistory } from "./useHistory";

const item = (id: string) => ({ id, created_at: "2026-10-30T08:01:02.123456Z", symbol: "BTC", name: "Bitcoin", side: "buy", quantity: "1", exec_price: "100", fee: "0.25", total: "-100.25" });
const page = (ids: string[], next_cursor: string | null) => new Response(JSON.stringify({ items: ids.map(item), next_cursor }));
afterEach(() => { vi.unstubAllGlobals(); focusManager.setFocused(undefined); });

it("refetches the loaded chain sequentially with new boundaries after newer fills and retains it on failure", async () => {
  const fetch = vi.fn()
    .mockResolvedValueOnce(page(["9"], "old_A"))
    .mockResolvedValueOnce(page(["8"], "old_B"))
    .mockResolvedValueOnce(page(["7"], "old_C"))
    .mockResolvedValueOnce(page(["10"], "new_A"))
    .mockResolvedValueOnce(page(["9"], "new_B"))
    .mockResolvedValueOnce(page(["8"], "new_C"))
    .mockResolvedValueOnce(page(["11"], "failed_A"))
    .mockResolvedValueOnce(new Response("{}", { status: 500 }));
  vi.stubGlobal("fetch", fetch);
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  const wrapper = ({ children }: { children: ReactNode }) => <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  const { result, unmount } = renderHook(() => useHistory(), { wrapper });
  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  await act(async () => { await result.current.fetchNextPage(); });
  await waitFor(() => expect(result.current.data?.pages).toHaveLength(2));
  await act(async () => { await result.current.fetchNextPage(); });
  await waitFor(() => expect(result.current.data?.pages).toHaveLength(3));
  expect(result.current.data?.pages.flatMap((p) => p.items.map((i) => i.id))).toEqual(["9", "8", "7"]);
  act(() => { focusManager.setFocused(false); focusManager.setFocused(true); });
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(6));
  await waitFor(() => expect(result.current.isFetching).toBe(false));
  expect(result.current.data?.pages.flatMap((p) => p.items.map((i) => i.id))).toEqual(["10", "9", "8"]);
  await act(async () => { await result.current.refetch(); });
  await waitFor(() => expect(result.current.isRefetchError).toBe(true));
  expect(result.current.data?.pages.map((p) => p.next_cursor)).toEqual(["new_A", "new_B", "new_C"]);
  expect(result.current.data?.pages.flatMap((p) => p.items.map((i) => i.id))).toEqual(["10", "9", "8"]);
  expect(fetch.mock.calls.map((args) => String(args[0]))).toEqual([
    "/api/v1/trades", "/api/v1/trades?cursor=old_A", "/api/v1/trades?cursor=old_B",
    "/api/v1/trades", "/api/v1/trades?cursor=new_A", "/api/v1/trades?cursor=new_B",
    "/api/v1/trades", "/api/v1/trades?cursor=failed_A",
  ]);
  unmount(); client.clear();
});
