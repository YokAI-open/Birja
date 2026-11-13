import { afterEach, expect, it, vi } from "vitest";
import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider, focusManager } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { useEventHistory } from "./useEventHistory";
import type { EventDividend } from "@/api/eventHistory";

const clients: QueryClient[] = [];
function setup(email: string | null = "first@example.test") {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: Infinity } },
  });
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
  focusManager.setFocused(undefined);
});

const item = (id: string): EventDividend => ({
  kind: "dividend",
  id: `dividend:${id}`,
  payment_reference: `dividend:${id}`,
  recorded_at: "2026-11-12T15:00:00.000001Z",
  credited_at: "2026-11-12T15:00:00.000001Z",
  asset_type: "stock",
  symbol: "AAPL",
  name: "Apple",
  cash_delta: "1.00",
  credited_amount: "1.00",
  eligible_quantity: "1",
  rate: "1.00",
  cutoff: "2026-11-10T14:30:00Z",
  ex_date: "2026-11-10",
  record_date: "2026-11-11",
  payable_date: "2026-11-12",
});
const cursor = (id: string) =>
  btoa(
    JSON.stringify({
      v: 2,
      recorded_at: "2026-11-12T15:00:00.000001Z",
      kind_rank: 3,
      source_id: id,
    }),
  )
    .replace(/=/g, "")
    .replace(/\+/g, "-")
    .replace(/\//g, "_");
const page = (ids: string[], next: string | null = null) =>
  new Response(JSON.stringify({ items: ids.map(item), next_cursor: next }));
function pending() {
  let resolve!: (response: Response) => void;
  const promise = new Promise<Response>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}

it("does not fetch or expose private History while logged out", async () => {
  const fetch = vi.fn(() =>
    Promise.resolve(new Response(JSON.stringify({ items: [], next_cursor: null }))),
  );
  vi.stubGlobal("fetch", fetch);
  const { result } = setup(null);
  await act(async () => {
    await Promise.resolve();
  });
  expect(fetch).not.toHaveBeenCalled();
  expect(result.current.data).toBeUndefined();
});

it("loads exact server order under an owner and epoch key without local money", async () => {
  const fetch = vi.fn((_input: RequestInfo | URL) => Promise.resolve(page(["3", "2"])));
  vi.stubGlobal("fetch", fetch);
  const { result, client } = setup();
  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  expect(result.current.data?.pages[0].items.map((event) => event.id)).toEqual([
    "dividend:3",
    "dividend:2",
  ]);
  expect(fetch.mock.calls[0]?.[0]).toBe("/api/v1/history");
  expect(
    client
      .getQueryCache()
      .findAll({ queryKey: ["eventHistory"] })
      .map((query) => query.queryKey),
  ).toEqual([["eventHistory", "first@example.test", 0]]);
  expect(client.getQueryData(["me"])).toEqual({
    email: "first@example.test",
    cash_usd: "10000.00",
  });
});

it.each([null, "second@example.test"])(
  "immediately hides and removes old accepted pages on auth change to %s",
  async (email) => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(page(["3"]))),
    );
    const { result, client } = setup();
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    act(() => client.setQueryData(["me"], email === null ? null : { email }));
    expect(client.getQueryData(["eventHistory", "first@example.test", 0])).toBeUndefined();
    expect(result.current.data).toBeUndefined();
  },
);

it.each([null, "second@example.test"])(
  "drops late old-owner fulfillment after auth change to %s",
  async (email) => {
    const old = pending();
    const fetch = vi
      .fn()
      .mockReturnValueOnce(old.promise)
      .mockResolvedValue(page(["9"]));
    vi.stubGlobal("fetch", fetch);
    const { result, client } = setup();
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
    act(() => client.setQueryData(["me"], email === null ? null : { email }));
    await act(async () => {
      old.resolve(page(["3"]));
    });
    expect(client.getQueryData(["eventHistory", "first@example.test", 0])).toBeUndefined();
    if (email === null) expect(result.current.data).toBeUndefined();
    else await waitFor(() => expect(result.current.data?.pages[0].items[0].id).toBe("dividend:9"));
  },
);

it("gives same-owner relogin a fresh epoch and cannot revive the old request", async () => {
  const old = pending();
  const fetch = vi
    .fn()
    .mockReturnValueOnce(old.promise)
    .mockResolvedValue(page(["9"]));
  vi.stubGlobal("fetch", fetch);
  const { result, client } = setup();
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
  act(() => {
    client.setQueryData(["me"], null);
    client.setQueryData(["me"], { email: "first@example.test" });
  });
  await waitFor(() => expect(result.current.data?.pages[0].items[0].id).toBe("dividend:9"));
  await act(async () => {
    old.resolve(page(["3"]));
  });
  expect(result.current.data?.pages[0].items[0].id).toBe("dividend:9");
  expect(client.getQueryData(["eventHistory", "first@example.test", 0])).toBeUndefined();
  expect(client.getQueryData(["eventHistory", "first@example.test", 2])).toBeDefined();
});

it("deduplicates simultaneous appends without cancelling the active page", async () => {
  const next = pending();
  const fetch = vi
    .fn()
    .mockResolvedValueOnce(page(["3"], cursor("3")))
    .mockReturnValueOnce(next.promise);
  vi.stubGlobal("fetch", fetch);
  const { result } = setup();
  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  let first!: ReturnType<typeof result.current.fetchNextPage>, second!: typeof first;
  act(() => {
    first = result.current.fetchNextPage();
    second = result.current.fetchNextPage();
  });
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
  await act(async () => {
    next.resolve(page(["2"]));
    await Promise.all([first, second]);
  });
  expect(fetch).toHaveBeenCalledTimes(2);
  await waitFor(() =>
    expect(
      result.current.data?.pages.flatMap((body) => body.items.map((event) => event.id)),
    ).toEqual(["dividend:3", "dividend:2"]),
  );
});

it.each([500, "malformed"])("retains accepted pages when append fails with %s", async (failure) => {
  const fetch = vi
    .fn()
    .mockResolvedValueOnce(page(["3"], cursor("3")))
    .mockResolvedValueOnce(
      failure === 500 ? new Response("{}", { status: 500 }) : new Response("{}"),
    );
  vi.stubGlobal("fetch", fetch);
  const { result } = setup();
  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  await act(async () => {
    await result.current.fetchNextPage();
  });
  await waitFor(() => expect(result.current.isFetchNextPageError).toBe(true));
  expect(result.current.data?.pages[0].items[0].id).toBe("dividend:3");
});

it("retains the whole accepted page chain if a later refresh page is malformed", async () => {
  const fetch = vi
    .fn()
    .mockResolvedValueOnce(page(["3"], cursor("3")))
    .mockResolvedValueOnce(page(["2"]))
    .mockResolvedValueOnce(page(["4"], cursor("4")))
    .mockResolvedValueOnce(new Response("{}"));
  vi.stubGlobal("fetch", fetch);
  const { result } = setup();
  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  await act(async () => {
    await result.current.fetchNextPage();
  });
  await act(async () => {
    await result.current.refetch();
  });
  expect(result.current.isRefetchError).toBe(true);
  expect(result.current.data?.pages.flatMap((body) => body.items.map((event) => event.id))).toEqual(
    ["dividend:3", "dividend:2"],
  );
});

it("keeps an initial malformed response empty and allows an explicit retry", async () => {
  const fetch = vi
    .fn()
    .mockResolvedValueOnce(new Response("{}"))
    .mockResolvedValueOnce(page(["3"]));
  vi.stubGlobal("fetch", fetch);
  const { result } = setup();
  await waitFor(() => expect(result.current.isError).toBe(true));
  expect(result.current.data).toBeUndefined();
  await act(async () => {
    await result.current.refetch();
  });
  await waitFor(() => expect(result.current.data?.pages[0].items[0].id).toBe("dividend:3"));
});

it("logs out only the current owner on final401 without retrying indefinitely", async () => {
  document.cookie = "bj_csrf=test";
  const fetch = vi.fn(() => Promise.resolve(new Response("{}", { status: 401 })));
  vi.stubGlobal("fetch", fetch);
  const { result, client } = setup();
  await waitFor(() => expect(client.getQueryData(["me"])).toBeNull());
  expect(result.current.data).toBeUndefined();
  expect(fetch).toHaveBeenCalledTimes(3);
  document.cookie = "bj_csrf=; Max-Age=0";
});

it("does not log out a new owner when the previous request returns401 late", async () => {
  const old = pending();
  const fetch = vi
    .fn()
    .mockReturnValueOnce(old.promise)
    .mockResolvedValue(page(["9"]));
  vi.stubGlobal("fetch", fetch);
  const { result, client } = setup();
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
  act(() => client.setQueryData(["me"], { email: "second@example.test" }));
  await waitFor(() => expect(result.current.data?.pages[0].items[0].id).toBe("dividend:9"));
  await act(async () => {
    old.resolve(new Response("{}", { status: 401 }));
  });
  expect(client.getQueryData(["me"])).toEqual({ email: "second@example.test" });
  expect(fetch).toHaveBeenCalledTimes(2);
});
