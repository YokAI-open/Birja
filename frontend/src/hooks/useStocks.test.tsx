import { afterEach, expect, it, vi } from "vitest";
import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { useStocks } from "./useStocks";
import { clearPrivateQueries } from "@/lib/privateQueries";

const stamp = (seconds: number) => new Date(Date.parse("2026-11-10T15:00:00Z") + seconds * 1000).toISOString();
function payload({ generation = 1, lifetime = 300, age = 10, close = 300, open = -1800, state = "approved" } = {}) {
  return {
    server_now: stamp(0), admission: { state, generation: state === "approved" ? generation : null, valid_until: state === "approved" ? stamp(lifetime) : null },
    attribution: { label: "IEX prices", explanation: "One venue", required_text: "" },
    items: Array.from({ length: 20 }, (_, i) => ({
      id: i + 16, symbol: `A${String.fromCharCode(65 + i)}`, company_name: "Company", listing_exchange: "NASDAQ", currency: "USD",
      quote: state === "approved" ? { bid: "100", ask: "102", mid: "101", event_at: stamp(-age), collected_at: stamp(-1), source: "alpaca", feed: "iex", age_seconds: age } : null,
      session: { state: "open", opens_at: stamp(open), closes_at: stamp(close), next_open_at: null, valid_until: stamp(lifetime), timezone: "America/New_York" },
      status: { state: "unknown", observed_at: null, valid_until: null },
      execution_enabled: false, execution_reason: "phase_disabled", quote_reason: state === "approved" ? "recent" : "permission_unavailable", session_reason: "open", status_reason: "unknown",
    })),
  };
}
const clients: QueryClient[] = [];
function setup() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  clients.push(client);
  client.setQueryData(["me"], { email: "first@example.test", cash_usd: "10000" });
  client.setQueryData(["prices"], { crypto: "unchanged" });
  const wrapper = ({ children }: { children: ReactNode }) => <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  return { client, ...renderHook(() => useStocks(), { wrapper }) };
}
afterEach(() => { cleanup(); clients.forEach((c) => c.clear()); clients.length = 0; vi.restoreAllMocks(); vi.unstubAllGlobals(); });

it.each([
  ["permission expires", { lifetime: 5 }, 6000, "permission_unavailable", "unknown"],
  ["quote reaches 120", { age: 119 }, 1000, "stale", "open"],
  ["session closes", { close: 5 }, 6000, "session_unavailable", "closed"],
  ["open boundary uncertain", { open: 1 }, 2000, "session_unavailable", "unknown"],
])("classifies %s before the first successful render", async (_name, options, delay, reason, session) => {
  let now = 0;
  vi.spyOn(performance, "now").mockImplementation(() => now);
  vi.spyOn(Date, "now").mockReturnValue(0); // Browser time has no authority.
  vi.stubGlobal("fetch", vi.fn(async () => { now = delay; return new Response(JSON.stringify(payload(options))); }));
  const { result, client } = setup();
  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  expect(result.current.data?.items[0].quote_reason).toBe(reason);
  expect(result.current.data?.items[0].session.state).toBe(session);
  if (reason === "permission_unavailable") expect(result.current.data?.items[0].quote).toBeNull();
  expect(client.getQueryData(["prices"])).toEqual({ crypto: "unchanged" });
});

it("retains admitted original quotes on background failure, then redacts at the deadline", async () => {
  let now = 0;
  vi.spyOn(performance, "now").mockImplementation(() => now);
  vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce(new Response(JSON.stringify(payload({ lifetime: 5 })))).mockRejectedValue(new Error("offline")));
  const { result, rerender } = setup();
  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  await act(async () => { await result.current.refetch(); });
  expect(result.current.data?.items[0].quote?.event_at).toBe(stamp(-10));
  now = 6000;
  rerender();
  expect(result.current.data?.items[0].quote).toBeNull();
});

it("purges on revocation and cannot publish a late cancelled previous-session result", async () => {
  let release: (value: Response) => void = () => {};
  const fetch = vi.fn().mockResolvedValueOnce(new Response(JSON.stringify(payload()))).mockImplementationOnce(() => new Promise<Response>((resolve) => { release = resolve; })).mockResolvedValue(new Response(JSON.stringify(payload({ state: "unavailable" }))));
  vi.stubGlobal("fetch", fetch);
  const { client, result } = setup();
  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  let pending: Promise<unknown>;
  act(() => { pending = result.current.refetch(); });
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
  await act(async () => { await clearPrivateQueries(client); client.setQueryData(["me"], null); });
  await act(async () => { release(new Response(JSON.stringify(payload()))); await pending; });
  expect(result.current.data).toBeUndefined();
  expect(client.getQueryCache().findAll({ queryKey: ["stocks"] }).every((q) => !q.state.data)).toBe(true);
});

it("replaces a permitted generation with denial and never retains its quote", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce(new Response(JSON.stringify(payload()))).mockResolvedValue(new Response(JSON.stringify(payload({ state: "unavailable" })))));
  const { result } = setup();
  await waitFor(() => expect(result.current.data?.items[0].quote).not.toBeNull());
  await act(async () => { await result.current.refetch(); });
  expect(result.current.data?.admission.state).toBe("unavailable");
  expect(result.current.data?.items[0].quote).toBeNull();
});
