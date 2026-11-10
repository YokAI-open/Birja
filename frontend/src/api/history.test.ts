import { afterEach, expect, it, vi } from "vitest";
import { fetchHistory, isHistoryPage } from "./history";

export const item = {
  id: "9007199254740993",
  created_at: "2026-10-30T08:01:02.123456Z",
  symbol: "BTC",
  name: "Bitcoin",
  side: "buy",
  quantity: "0.00000001",
  exec_price: "123.45678901",
  fee: "0.25",
  total: "-100.00",
};
afterEach(() => vi.unstubAllGlobals());
it("preserves exact string fields and the opaque continuation with abort signal", async () => {
  const body = { items: [item], next_cursor: "opaque_-123" };
  const mock = vi.fn(() => Promise.resolve(new Response(JSON.stringify(body))));
  vi.stubGlobal("fetch", mock);
  const signal = new AbortController().signal;
  expect(await fetchHistory({ cursor: "opaque_-123", limit: 1 }, signal)).toEqual(body);
  expect(mock.mock.calls[0]).toEqual([
    "/api/v1/trades?cursor=opaque_-123&limit=1",
    expect.objectContaining({ signal }),
  ]);
  expect(isHistoryPage({ items: [], next_cursor: null })).toBe(true);
});
it.each([
  { id: 1 },
  { id: "1e2" },
  { id: "0" },
  { id: "9223372036854775808" },
  { quantity: 1 },
  { quantity: "1e-8" },
  { fee: "-1" },
  { exec_price: "1E2" },
  { total: -100 },
  { total: "-1e2" },
  { side: "hold" },
  { created_at: "bad" },
  { created_at: "2026-02-30T08:01:02.123456Z" },
  { created_at: "2026-10-30T08:01:02" },
])("rejects malformed fill %o", (change) => {
  expect(isHistoryPage({ items: [{ ...item, ...change }], next_cursor: null })).toBe(false);
});
it.each([undefined, 1, "", "x".repeat(513), "bad=padding"])(
  "rejects invalid cursor %s",
  (next_cursor) => {
    expect(isHistoryPage({ items: [item], next_cursor })).toBe(false);
  },
);
it("rejects malformed responses from the network", async () => {
  vi.stubGlobal("fetch", () =>
    Promise.resolve(new Response(JSON.stringify({ items: null, next_cursor: null }))),
  );
  await expect(fetchHistory()).rejects.toThrow("Unexpected history response");
});
