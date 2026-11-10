import { act, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider, useQueries } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "@/api/client";
import { useTrade } from "./useTrade";

const keys = [["me"], ["holding", "BTC"], ["prices"], ["portfolio"], ["history"]];
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });
const fill = {
  trade_id: 17,
  created_at: "2026-10-30T07:00:00Z",
  symbol: "BTC",
  side: "buy",
  input_kind: "usd",
  input_value: "100",
  mid: "10000",
  as_of: "2026-10-30T07:00:00Z",
  exec_price: "10025",
  quantity: "0.00995018",
  notional: "99.75",
  fee: "0.25",
  cash_delta: "-100",
  cash_after: "9900",
};

afterEach(() => {
  vi.unstubAllGlobals();
  document.cookie = "bj_csrf=; max-age=0; path=/";
});

describe("useTrade financial refresh", () => {
  it.each([
    ["buy", 201],
    ["sell", 201],
    ["buy", 200],
  ] as const)(
    "awaits all five server views for %s HTTP %s (including replay)",
    async (side, status) => {
      document.cookie = "bj_csrf=test; path=/";
      const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
      const old = { cash: "10000", rows: [] };
      keys.forEach((key) => client.setQueryData(key, old));
      const releases = new Map<string, (r: Response) => void>();
      const fetchMock = vi.fn((path: string) => {
        if (path === "/api/v1/trades") return Promise.resolve(json({ ...fill, side }, status));
        return new Promise<Response>((resolve) => releases.set(path, resolve));
      });
      vi.stubGlobal("fetch", fetchMock);
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={client}>{children}</QueryClientProvider>
      );
      const { result, unmount } = renderHook(
        () => {
          const views = useQueries({
            queries: keys.map((queryKey) => ({
              queryKey,
              staleTime: Infinity,
              queryFn: ({ signal }: { signal: AbortSignal }) =>
                apiFetch(`/view/${queryKey[0]}`, { signal }),
            })),
          });
          return { trade: useTrade("BTC"), views };
        },
        { wrapper },
      );
      let completed = false;
      let pending!: Promise<unknown>;
      act(() => {
        pending = result.current.trade
          .mutateAsync({
            order: { symbol: "BTC", side, quantity: "0.01" },
            expectedMid: "10000",
            idempotencyKey: "same-key",
          })
          .then((value) => {
            completed = true;
            return value;
          });
      });
      await waitFor(() => expect(releases.size).toBe(5));
      expect(completed).toBe(false);
      expect(result.current.trade.isPending).toBe(true);
      keys.forEach((key) => expect(client.getQueryData(key)).toEqual(old));
      for (const [index, key] of keys.entries()) {
        const server = { cash: "server-value", rows: [{ trade_id: 17 }] };
        await act(async () => {
          releases.get(`/view/${key[0]}`)!(json(server));
        });
        await waitFor(() => expect(result.current.views[index]!.data).toEqual(server));
        if (index < keys.length - 1) expect(completed).toBe(false);
      }
      await act(async () => {
        await pending;
      });
      expect(completed).toBe(true);
      expect(client.getQueryData(["history"])).toEqual({
        cash: "server-value",
        rows: [{ trade_id: 17 }],
      });
      expect(fetchMock.mock.calls.filter(([path]) => path === "/api/v1/trades")).toHaveLength(1);
      unmount();
      client.clear();
    },
  );

  it.each(["refusal", "network"])(
    "does not invalidate or change cached money/history on %s",
    async (failure) => {
      document.cookie = "bj_csrf=test; path=/";
      const client = new QueryClient();
      keys.forEach((key) => client.setQueryData(key, { unchanged: true }));
      const invalidate = vi.spyOn(client, "invalidateQueries");
      const fetchMock = vi.fn(() =>
        failure === "network"
          ? Promise.reject(new TypeError("offline"))
          : Promise.resolve(json({ detail: { code: "insufficient_cash" } }, 422)),
      );
      vi.stubGlobal("fetch", fetchMock);
      const { result, unmount } = renderHook(() => useTrade("BTC"), {
        wrapper: ({ children }: { children: ReactNode }) => (
          <QueryClientProvider client={client}>{children}</QueryClientProvider>
        ),
      });
      await act(async () => {
        await expect(
          result.current.mutateAsync({
            order: { symbol: "BTC", side: "buy", amount_usd: "100" },
            expectedMid: "10000",
            idempotencyKey: "key",
          }),
        ).rejects.toBeInstanceOf(Error);
      });
      expect(invalidate).not.toHaveBeenCalled();
      keys.forEach((key) => expect(client.getQueryData(key)).toEqual({ unchanged: true }));
      expect(fetchMock).toHaveBeenCalledTimes(1);
      unmount();
      client.clear();
    },
  );
});
