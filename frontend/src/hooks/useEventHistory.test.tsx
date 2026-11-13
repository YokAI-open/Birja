import { afterEach, expect, it, vi } from "vitest";
import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { useEventHistory } from "./useEventHistory";

const clients: QueryClient[] = [];
function setup(email: string | null = "first@example.test") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: Infinity } } });
  clients.push(client);
  client.setQueryData(["me"], email === null ? null : { email, cash_usd: "10000.00" });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return { client, ...renderHook(() => useEventHistory(), { wrapper }) };
}
afterEach(() => {
  cleanup();
  clients.forEach((client) => client.clear());
  clients.length = 0;
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

it("does not fetch or expose private History while logged out", async () => {
  const fetch = vi.fn(() => Promise.resolve(new Response(JSON.stringify({ items: [], next_cursor: null }))));
  vi.stubGlobal("fetch", fetch);
  const { result } = setup(null);
  await act(async () => { await Promise.resolve(); });
  expect(fetch).not.toHaveBeenCalled();
  expect(result.current.data).toBeUndefined();
});
