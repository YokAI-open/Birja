import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchStocks, isStocks } from "./stocks";

const item = {
  id: 16,
  symbol: "AAPL",
  company_name: "Apple Inc.",
  listing_exchange: "NASDAQ",
  currency: "USD",
  quote: {
    bid: "100.00000001",
    ask: "100.00000003",
    mid: "100.00000002",
    event_at: "2026-11-10T15:00:00Z",
    collected_at: "2026-11-10T15:00:01Z",
    source: "alpaca",
    feed: "iex",
    age_seconds: 10,
  },
  session: {
    state: "open",
    opens_at: "2026-11-10T14:30:00Z",
    closes_at: "2026-11-10T21:00:00Z",
    next_open_at: null,
    valid_until: "2026-11-11T00:00:00Z",
    timezone: "America/New_York",
  },
  status: { state: "unknown", observed_at: null, valid_until: null },
  action: {
    state: "current",
    reason: "none",
    epoch: 1,
    checked_at: "2026-11-10T15:00:00Z",
    valid_until: "2026-11-10T16:00:00Z",
  },
  valuation_reason: "available",
  execution_enabled: false,
  execution_reason: "phase_disabled",
  quote_reason: "recent",
  session_reason: "open",
  status_reason: "unknown",
};
const valid = {
  server_now: "2026-11-10T15:00:10Z",
  admission: { state: "approved", generation: 1, valid_until: "2026-11-11T00:00:00Z" },
  attribution: { label: "IEX prices", explanation: "Single venue", required_text: "" },
  items: Array.from({ length: 20 }, (_, i) => ({
    ...item,
    id: i + 16,
    symbol: `A${String.fromCharCode(65 + i)}`,
  })),
};
afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("strict stock boundary", () => {
  it("accepts the complete exact string-money contract and permission-denied catalogue", () => {
    expect(isStocks(valid)).toBe(true);
    expect(
      isStocks({
        ...valid,
        admission: { state: "unavailable", generation: null, valid_until: null },
        items: valid.items.map((x) => ({
          ...x,
          quote: null,
          quote_reason: "permission_unavailable",
          valuation_reason: "action_unavailable",
          action: {
            state: "unknown",
            reason: "monitor_unavailable",
            epoch: 0,
            checked_at: null,
            valid_until: null,
          },
        })),
      }),
    ).toBe(true);
  });
  it.each([
    ["short catalogue", { ...valid, items: valid.items.slice(1) }],
    ["duplicate identity", { ...valid, items: [...valid.items.slice(1), valid.items[1]] }],
    ["duplicate symbol", { ...valid, items: valid.items.map((x) => ({ ...x, symbol: "AAPL" })) }],
    ["unsafe identity", { ...valid, items: valid.items.map((x) => ({ ...x, id: 2 ** 54 })) }],
    ["naive time", { ...valid, server_now: "2026-11-10T15:00:10" }],
    ["impossible time", { ...valid, server_now: "2026-02-30T15:00:10Z" }],
    [
      "unrecognized venue",
      { ...valid, items: valid.items.map((x) => ({ ...x, listing_exchange: "OTC" })) },
    ],
    [
      "executable",
      { ...valid, items: valid.items.map((x) => ({ ...x, execution_enabled: true })) },
    ],
    [
      "foreign feed",
      { ...valid, items: valid.items.map((x) => ({ ...x, quote: { ...x.quote, feed: "sip" } })) },
    ],
    [
      "float money",
      { ...valid, items: valid.items.map((x) => ({ ...x, quote: { ...x.quote, bid: 100 } })) },
    ],
    [
      "scientific money",
      { ...valid, items: valid.items.map((x) => ({ ...x, quote: { ...x.quote, bid: "1e2" } })) },
    ],
    [
      "zero money",
      { ...valid, items: valid.items.map((x) => ({ ...x, quote: { ...x.quote, bid: "0" } })) },
    ],
    [
      "crossed exact prices",
      {
        ...valid,
        items: valid.items.map((x) => ({ ...x, quote: { ...x.quote, bid: "100.00000004" } })),
      },
    ],
    [
      "out of bounds mid",
      { ...valid, items: valid.items.map((x) => ({ ...x, quote: { ...x.quote, mid: "99" } })) },
    ],
    [
      "unknown reason",
      { ...valid, items: valid.items.map((x) => ({ ...x, quote_reason: "great" })) },
    ],
    [
      "invalid session interval",
      {
        ...valid,
        items: valid.items.map((x) => ({
          ...x,
          session: { ...x.session, closes_at: x.session.opens_at },
        })),
      },
    ],
  ])("rejects %s atomically", (_name, body) => expect(isStocks(body)).toBe(false));
  it("uses the shared authenticated transport and measures its entire duration", async () => {
    let now = 500;
    vi.spyOn(performance, "now").mockImplementation(() => now);
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        now = 5500;
        return new Response(JSON.stringify(valid));
      }),
    );
    const signal = new AbortController().signal;
    const result = await fetchStocks(signal);
    expect(result).toMatchObject({
      ...valid,
      transport: { started_at: 500, received_at: 5500, round_trip_ms: 5000 },
    });
    expect(fetch).toHaveBeenCalledWith("/api/v1/stocks", expect.objectContaining({ signal }));
    vi.restoreAllMocks();
  });
  it("rejects a malformed response before publication", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify({ ...valid, items: [] }))),
    );
    await expect(fetchStocks()).rejects.toThrow("Unexpected stocks response");
  });
  it("never restarts transport timing across an authenticated retry", async () => {
    let now = 100;
    vi.spyOn(performance, "now").mockImplementation(() => now);
    document.cookie = "bj_csrf=test-csrf";
    const fetch = vi
      .fn()
      .mockImplementationOnce(async () => {
        now = 1100;
        return new Response("{}", { status: 401 });
      })
      .mockImplementationOnce(async () => {
        now = 4100;
        return new Response(null, { status: 204 });
      })
      .mockImplementationOnce(async () => {
        now = 6100;
        return new Response(JSON.stringify(valid));
      });
    vi.stubGlobal("fetch", fetch);
    const result = await fetchStocks();
    expect(result.transport).toEqual({ started_at: 100, received_at: 6100, round_trip_ms: 6000 });
    expect(fetch.mock.calls.map((args) => args[0])).toEqual([
      "/api/v1/stocks",
      "/api/v1/auth/refresh",
      "/api/v1/stocks",
    ]);
    document.cookie = "bj_csrf=; Max-Age=0";
  });
});

describe("action authority validation", () => {
  it.each([
    ["missing action", undefined],
    ["unknown state", { ...item.action, state: "healthy" }],
    ["unknown reason", { ...item.action, reason: "provider raw text" }],
    ["unsafe epoch", { ...item.action, epoch: 2 ** 53 }],
    ["negative epoch", { ...item.action, epoch: -1 }],
    ["fractional epoch", { ...item.action, epoch: 1.1 }],
    ["false current", { ...item.action, epoch: 0 }],
    ["missing check", { ...item.action, checked_at: null }],
    ["future check", { ...item.action, checked_at: "2026-11-10T15:01:00Z" }],
    ["expired current", { ...item.action, valid_until: valid.server_now }],
    ["invalid current reason", { ...item.action, reason: "unsupported" }],
    ["raw evidence", { ...item.action, provider_payload: "private" }],
    ["offset action time", { ...item.action, checked_at: "2026-11-10T16:00:00+01:00" }],
  ])("rejects %s", (_name, action) => {
    expect(isStocks({ ...valid, items: valid.items.map((x) => ({ ...x, action })) })).toBe(false);
  });
  it.each(["unknown", "reconciling", "suspended"])("rejects numeric values on %s", (state) => {
    expect(
      isStocks({
        ...valid,
        items: valid.items.map((x) => ({
          ...x,
          action: {
            ...x.action,
            state,
            reason:
              state === "unknown"
                ? "monitor_unavailable"
                : state === "reconciling"
                  ? "source_gap"
                  : "unsupported",
            valid_until: null,
          },
        })),
      }),
    ).toBe(false);
  });
  it("requires valuation reason and disallows provider/operator extras", () => {
    for (const update of [
      { valuation_reason: undefined },
      { valuation_reason: "guessed" },
      { provider_id: "secret" },
      { valuation_reason: "action_unavailable" },
    ]) {
      expect(isStocks({ ...valid, items: valid.items.map((x) => ({ ...x, ...update })) })).toBe(
        false,
      );
    }
  });
});
