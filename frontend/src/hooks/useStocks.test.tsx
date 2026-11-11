import { afterEach, expect, it, vi } from "vitest";
import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { useStocks } from "./useStocks";
import { clearPrivateQueries } from "@/lib/privateQueries";
import { type TimedStocks } from "@/api/stocks";
import { projectStocks } from "./useStocks";

const stamp = (seconds: number) =>
  new Date(Date.parse("2026-11-10T15:00:00Z") + seconds * 1000).toISOString();
function payload({
  generation = 1,
  lifetime = 300,
  age = 10,
  close = 300,
  open = -1800,
  state = "approved",
} = {}) {
  return {
    server_now: stamp(0),
    admission: {
      state,
      generation: state === "approved" ? generation : null,
      valid_until: state === "approved" ? stamp(lifetime) : null,
    },
    attribution: { label: "IEX prices", explanation: "One venue", required_text: "" },
    items: Array.from({ length: 20 }, (_, i) => ({
      id: i + 16,
      symbol: `A${String.fromCharCode(65 + i)}`,
      company_name: "Company",
      listing_exchange: "NASDAQ",
      currency: "USD",
      quote:
        state === "approved"
          ? {
              bid: "100",
              ask: "102",
              mid: "101",
              event_at: stamp(-age),
              collected_at: stamp(-1),
              source: "alpaca",
              feed: "iex",
              age_seconds: age,
            }
          : null,
      session: {
        state: "open",
        opens_at: stamp(open),
        closes_at: stamp(close),
        next_open_at: null,
        valid_until: stamp(lifetime),
        timezone: "America/New_York",
      },
      status: { state: "unknown", observed_at: null, valid_until: null },
      action:
        state === "approved"
          ? {
              state: "current",
              reason: "none",
              epoch: 1,
              checked_at: stamp(-1),
              valid_until: stamp(lifetime),
            }
          : {
              state: "unknown",
              reason: "monitor_unavailable",
              epoch: 0,
              checked_at: null,
              valid_until: null,
            },
      valuation_reason: state === "approved" ? "available" : "action_unavailable",
      execution_enabled: false,
      execution_reason: "phase_disabled",
      quote_reason: state === "approved" ? "recent" : "permission_unavailable",
      session_reason: "open",
      status_reason: "unknown",
    })),
  };
}
function aligned<T extends ReturnType<typeof payload>>(body: T): T {
  body.items.forEach((item) => {
    if (item.quote !== null)
      item.quote.age_seconds = Math.floor(
        (Date.parse(body.server_now) - Date.parse(item.quote.event_at)) / 1000,
      );
  });
  return body;
}
const clients: QueryClient[] = [];
function setup() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: Infinity } },
  });
  clients.push(client);
  client.setQueryData(["me"], { email: "first@example.test", cash_usd: "10000" });
  client.setQueryData(["prices"], { crypto: "unchanged" });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return { client, ...renderHook(() => useStocks(), { wrapper }) };
}
afterEach(() => {
  cleanup();
  clients.forEach((c) => c.clear());
  clients.length = 0;
  vi.useRealTimers();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

it.each([
  ["permission expires", { lifetime: 5 }, 6000, "permission_unavailable", "unknown"],
  ["quote reaches 120", { age: 119 }, 1000, "stale", "open"],
  ["session closes", { close: 5 }, 6000, "session_unavailable", "closed"],
])(
  "classifies %s before the first successful render",
  async (_name, options, delay, reason, session) => {
    let now = 0;
    vi.spyOn(performance, "now").mockImplementation(() => now);
    vi.spyOn(Date, "now").mockReturnValue(0); // Browser time has no authority.
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        now = delay;
        return new Response(JSON.stringify(payload(options)));
      }),
    );
    const { result, client } = setup();
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.items[0].quote_reason).toBe(reason);
    expect(result.current.data?.items[0].session.state).toBe(session);
    if (reason === "permission_unavailable") expect(result.current.data?.items[0].quote).toBeNull();
    expect(client.getQueryData(["prices"])).toEqual({ crypto: "unchanged" });
  },
);

it("retains admitted original quotes on background failure, then redacts at the deadline", async () => {
  let now = 0;
  vi.spyOn(performance, "now").mockImplementation(() => now);
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(payload({ lifetime: 5 }))))
      .mockRejectedValue(new Error("offline")),
  );
  const { result, rerender } = setup();
  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  await act(async () => {
    await result.current.refetch();
  });
  expect(result.current.data?.items[0].quote?.event_at).toBe(stamp(-10));
  now = 6000;
  rerender();
  expect(result.current.data?.items[0].quote).toBeNull();
});

it("purges on revocation and cannot publish a late cancelled previous-session result", async () => {
  let release: (value: Response) => void = () => {};
  const fetch = vi
    .fn()
    .mockResolvedValueOnce(new Response(JSON.stringify(payload())))
    .mockImplementationOnce(
      () =>
        new Promise<Response>((resolve) => {
          release = resolve;
        }),
    )
    .mockResolvedValue(new Response(JSON.stringify(payload({ state: "unavailable" }))));
  vi.stubGlobal("fetch", fetch);
  const { client, result } = setup();
  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  let pending: Promise<unknown>;
  act(() => {
    pending = result.current.refetch();
  });
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
  await act(async () => {
    await clearPrivateQueries(client);
    client.setQueryData(["me"], null);
  });
  await act(async () => {
    release(new Response(JSON.stringify(payload())));
    await pending;
  });
  expect(result.current.data).toBeUndefined();
  expect(
    client
      .getQueryCache()
      .findAll({ queryKey: ["stocks"] })
      .every((q) => !q.state.data),
  ).toBe(true);
});

it("replaces a permitted generation with denial and never retains its quote", async () => {
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(payload())))
      .mockResolvedValue(new Response(JSON.stringify(payload({ state: "unavailable" })))),
  );
  const { result } = setup();
  await waitFor(() => expect(result.current.data?.items[0].quote?.bid).toBe("100"));
  await act(async () => {
    await result.current.refetch();
  });
  await waitFor(() => expect(result.current.data?.admission.state).toBe("unavailable"));
  expect(result.current.data?.items[0].quote).toBeNull();
});

it.each(["revoked", "newer generation"])(
  "rejects an older in-flight response after %s is installed",
  async (change) => {
    let release: (value: Response) => void = () => {};
    const fetch = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(payload())))
      .mockImplementationOnce(
        () =>
          new Promise<Response>((resolve) => {
            release = resolve;
          }),
      );
    vi.stubGlobal("fetch", fetch);
    const { result, client } = setup();
    await waitFor(() => expect(result.current.data?.items[0].quote?.bid).toBe("100"));
    let pending: Promise<unknown>;
    act(() => {
      pending = result.current.refetch();
    });
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
    const key = ["stocks", "first@example.test"];
    const previous = client.getQueryData<TimedStocks>(key)!;
    const replacement = payload(
      change === "revoked" ? { state: "unavailable" } : { generation: 2 },
    );
    act(() => {
      client.setQueryData(key, { ...replacement, transport: previous.transport });
    });
    const pendingSignal = (fetch.mock.calls[1] as unknown as [string, RequestInit])[1].signal;
    expect(pendingSignal?.aborted).toBe(true);
    await act(async () => {
      release(new Response(JSON.stringify(payload())));
      await pending;
    });
    await waitFor(() =>
      expect(result.current.data?.admission.generation).toBe(change === "revoked" ? null : 2),
    );
    expect(result.current.data?.admission.state).toBe(
      change === "revoked" ? "unavailable" : "approved",
    );
    if (change === "revoked") expect(result.current.data?.items[0].quote).toBeNull();
  },
);

it("does not fetch without identity, and switches auth-scoped keys without carrying quotes", async () => {
  let release: (value: Response) => void = () => {};
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(payload())))
      .mockImplementation(
        () =>
          new Promise<Response>((resolve) => {
            release = resolve;
          }),
      ),
  );
  const { result, client, unmount } = setup();
  await waitFor(() => expect(result.current.data?.items).toHaveLength(20));
  act(() => {
    client.setQueryData(["me"], { email: "second@example.test", cash_usd: "10000" });
  });
  await waitFor(() => expect(result.current.data).toBeUndefined());
  unmount();
  release(new Response(JSON.stringify(payload())));
  await act(async () => {
    await Promise.resolve();
  });
  expect(client.getQueryData(["stocks", "second@example.test"])).toBeUndefined();
});

it("redacts missing and denied values and never locally opens a server-closed session", () => {
  const data = payload() as unknown as TimedStocks;
  data.transport = { started_at: 0, received_at: 0, round_trip_ms: 0 };
  data.items[0].quote = null;
  data.items[0].quote_reason = "missing";
  data.items[1].session.state = "closed";
  data.items[1].quote_reason = "session_unavailable";
  data.items[2].quote_reason = "permission_unavailable";
  const output = projectStocks(data, 1000);
  expect(output.items[0].quote).toBeNull();
  expect(output.items[1].session.state).toBe("closed");
  expect(output.items[1].quote?.event_at).toBe(stamp(-10));
  expect(output.items[2].quote).toBeNull();
  expect(output.items.every((item) => item.execution_enabled === false)).toBe(true);
});

it("invalidates identity and purges private stocks after the authenticated retry still returns 401", async () => {
  let denied = false;
  document.cookie = "bj_csrf=test-csrf";
  vi.stubGlobal(
    "fetch",
    vi.fn(async (path: string) => {
      if (path === "/api/v1/auth/refresh") return new Response(null, { status: 204 });
      return denied ? new Response("{}", { status: 401 }) : new Response(JSON.stringify(payload()));
    }),
  );
  const { result, client } = setup();
  await waitFor(() => expect(result.current.data?.items).toHaveLength(20));
  denied = true;
  await act(async () => {
    await result.current.refetch();
  });
  await waitFor(() => expect(result.current.data).toBeUndefined());
  expect(client.getQueryData(["me"])).toBeNull();
  expect(
    client
      .getQueryCache()
      .findAll({ queryKey: ["stocks"] })
      .every((q) => !q.state.data),
  ).toBe(true);
  expect(client.getQueryData(["prices"])).toEqual({ crypto: "unchanged" });
  document.cookie = "bj_csrf=; Max-Age=0";
});

it("adds full RTT and monotonic elapsed once, retaining the original timestamp", async () => {
  let now = 0;
  vi.spyOn(performance, "now").mockImplementation(() => now);
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => {
      now = 5000;
      return new Response(JSON.stringify(payload()));
    }),
  );
  const { result, rerender } = setup();
  await waitFor(() => expect(result.current.data?.items[0].quote?.age_seconds).toBe(15));
  now = 8000;
  rerender();
  expect(result.current.data?.items[0].quote?.age_seconds).toBe(18);
  expect(result.current.data?.items[0].quote?.event_at).toBe(stamp(-10));
});

it("purges expired numbers from the cache on its display tick without fetching", async () => {
  let now = 0;
  vi.spyOn(performance, "now").mockImplementation(() => now);
  const fetch = vi.fn(async () => new Response(JSON.stringify(payload({ lifetime: 5 }))));
  vi.stubGlobal("fetch", fetch);
  const { result, client } = setup();
  await waitFor(() => expect(result.current.data?.items).toHaveLength(20));
  now = 6000;
  await waitFor(
    () =>
      expect(
        client.getQueryData<TimedStocks>(["stocks", "first@example.test"])?.items[0].quote,
      ).toBeNull(),
    { timeout: 1500 },
  );
  expect(fetch).toHaveBeenCalledTimes(1);
});

it("spends transport time against the server's shortened retention deadline before caching", async () => {
  let now = 0;
  vi.spyOn(performance, "now").mockImplementation(() => now);
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => {
      now = 2000;
      return new Response(JSON.stringify(payload({ lifetime: 2 })));
    }),
  );
  const { result, client } = setup();
  await waitFor(() => expect(result.current.data?.items).toHaveLength(20));
  expect(result.current.data?.admission.state).toBe("unavailable");
  expect(result.current.data?.items.every((item) => item.quote === null)).toBe(true);
  expect(
    client
      .getQueryData<TimedStocks>(["stocks", "first@example.test"])
      ?.items.every((item) => item.quote === null),
  ).toBe(true);
});

it("removes monitor-expired numbers at exact millisecond equality, from projection and cache", async () => {
  let now = 0;
  vi.spyOn(performance, "now").mockImplementation(() => now);
  const body = payload();
  body.items.forEach((x) => {
    x.action.valid_until = stamp(0.125);
  });
  const fetch = vi.fn(async () => new Response(JSON.stringify(aligned(body))));
  vi.stubGlobal("fetch", fetch);
  const { result, client } = setup();
  await waitFor(() => expect(result.current.data?.items[0].quote?.bid).toBe("100"));
  now = 124;
  expect(
    projectStocks(client.getQueryData<TimedStocks>(["stocks", "first@example.test"])!, now).items[0]
      .quote,
  ).not.toBeNull();
  now = 125;
  await waitFor(
    () =>
      expect(
        client.getQueryData<TimedStocks>(["stocks", "first@example.test"])?.items[0].quote,
      ).toBeNull(),
    { timeout: 500 },
  );
  expect(result.current.data?.items[0].action.state).toBe("unknown");
  expect(fetch).toHaveBeenCalledTimes(1);
});

it("accepts generic epoch-zero redaction then refuses an older healthy epoch", async () => {
  const healthy = payload();
  healthy.items.forEach((x) => {
    x.action.epoch = 7;
  });
  const redacted = payload();
  redacted.server_now = stamp(1);
  redacted.items.forEach((x) => {
    x.action = {
      state: "unknown",
      reason: "monitor_unavailable",
      epoch: 0,
      checked_at: null,
      valid_until: null,
    } as never;
    x.quote = null;
    x.quote_reason = "permission_unavailable";
    x.valuation_reason = "action_unavailable";
  });
  const stale = payload();
  stale.server_now = stamp(2);
  stale.items.forEach((x) => {
    x.action.epoch = 6;
  });
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(aligned(healthy))))
      .mockResolvedValueOnce(new Response(JSON.stringify(redacted)))
      .mockResolvedValueOnce(new Response(JSON.stringify(aligned(stale)))),
  );
  const { result, client } = setup();
  await waitFor(() => expect(result.current.data?.items[0].action.epoch).toBe(7));
  await act(async () => {
    await result.current.refetch();
  });
  expect(result.current.data?.items[0].quote).toBeNull();
  expect(result.current.data?.items[0].action.epoch).toBe(0);
  await act(async () => {
    await result.current.refetch();
  });
  expect(
    client.getQueryData<TimedStocks>(["stocks", "first@example.test"])?.items[0].quote,
  ).toBeNull();
});

it("uses sub-millisecond timestamps conservatively and purges source age at120", () => {
  const data = payload({ age: 119 }) as unknown as TimedStocks;
  data.transport = { started_at: 0, received_at: 0, round_trip_ms: 0 };
  data.server_now = "2026-11-10T15:00:00.000999Z";
  data.items[0].quote!.event_at = "2026-11-10T14:58:00.001001Z";
  expect(projectStocks(data, 0).items[0].quote).toBeNull();
});

const timed = (body = payload()): TimedStocks =>
  ({
    ...body,
    transport: { started_at: 0, received_at: 0, round_trip_ms: 0 },
  }) as unknown as TimedStocks;
const hold = (body: ReturnType<typeof payload>, epoch: number, reason = "unsupported") => {
  body.items.forEach((item) => {
    item.action = {
      state: "suspended",
      reason,
      epoch,
      checked_at: stamp(-1),
      valid_until: null,
    } as never;
    item.quote = null;
    item.quote_reason = "permission_unavailable";
    item.valuation_reason = reason === "post_split_quote_missing" ? reason : "action_unavailable";
  });
  return body;
};

it.each([
  [
    "admission",
    (data: TimedStocks) => {
      data.admission.valid_until = stamp(0.1);
    },
  ],
  [
    "calendar",
    (data: TimedStocks) => {
      data.items[0].session.valid_until = stamp(0.1);
    },
  ],
  [
    "action",
    (data: TimedStocks) => {
      data.items[0].action.valid_until = stamp(0.1);
    },
  ],
  [
    "source-age",
    (data: TimedStocks) => {
      data.items[0].quote!.event_at = stamp(-119.9);
      data.items[0].quote!.age_seconds = 119;
    },
  ],
])("purges %s exactly at equality using full RTT once", (_name, change) => {
  const data = timed();
  change(data);
  data.transport.round_trip_ms = 40;
  expect(projectStocks(data, 59).items[0].quote).not.toBeNull();
  expect(projectStocks(data, 60).items[0].quote).toBeNull();
  expect(data.items[0].quote?.event_at).toBeDefined();
});

it("rounds deadline and source fractions down, never granting an extra millisecond", () => {
  const data = timed();
  data.items[0].action.valid_until = "2026-11-10T15:00:00.100999999Z";
  expect(projectStocks(data, 99).items[0].quote).not.toBeNull();
  expect(projectStocks(data, 100).items[0].quote).toBeNull();
  const almost = timed();
  almost.items[0].quote!.event_at = stamp(-119.999);
  almost.items[0].quote!.age_seconds = 119;
  expect(projectStocks(almost, 0).items[0].quote).not.toBeNull();
  expect(projectStocks(almost, 1).items[0].quote).toBeNull();
});

it("keeps original held reasons and never locally establishes action safety", () => {
  const data = timed(hold(payload(), 7, "post_split_quote_missing"));
  expect(projectStocks(data, 100).items[0]).toMatchObject({
    quote: null,
    action: { state: "suspended", reason: "post_split_quote_missing", epoch: 7 },
    valuation_reason: "post_split_quote_missing",
  });
  const unavailable = projectStocks(
    { ...data, admission: { state: "unavailable", generation: null, valid_until: null } },
    100,
  );
  expect(unavailable.items[0]).toMatchObject({
    quote: null,
    action: { state: "unknown", epoch: 0, checked_at: null, valid_until: null },
    valuation_reason: "action_unavailable",
  });
});

it.each(["older epoch", "older server", "equal time hold", "older submillisecond"])(
  "rejects %s after a newer hold without losing cached privacy",
  async (scenario) => {
    const held = hold(payload(), 7);
    held.server_now =
      scenario === "older submillisecond" ? "2026-11-10T15:00:01.000000002Z" : stamp(1);
    const old = payload();
    old.server_now =
      scenario === "older submillisecond"
        ? "2026-11-10T15:00:01.000000001Z"
        : scenario === "older server"
          ? stamp(0)
          : scenario === "equal time hold"
            ? stamp(1)
            : stamp(2);
    old.items.forEach((x) => {
      x.action.epoch = scenario === "older epoch" ? 6 : 7;
    });
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(new Response(JSON.stringify(aligned(held))))
        .mockResolvedValue(new Response(JSON.stringify(aligned(old)))),
    );
    const { result, client } = setup();
    await waitFor(() => expect(result.current.data?.items[0].action.state).toBe("suspended"));
    await act(async () => {
      await result.current.refetch();
    });
    expect(
      client.getQueryData<TimedStocks>(["stocks", "first@example.test"])?.items[0],
    ).toMatchObject({ quote: null, action: { state: "suspended", epoch: 7 } });
  },
);

it("retains high-water across same-user refresh and accepts a newer legitimate resolution", async () => {
  const held = hold(payload(), 7);
  const stale = payload();
  stale.server_now = stamp(1);
  stale.items.forEach((x) => {
    x.action.epoch = 6;
  });
  const resolved = payload();
  resolved.server_now = stamp(2);
  resolved.items.forEach((x) => {
    x.action.epoch = 8;
  });
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(aligned(held))))
      .mockResolvedValueOnce(new Response(JSON.stringify(aligned(stale))))
      .mockResolvedValueOnce(new Response(JSON.stringify(aligned(resolved)))),
  );
  const { result, client } = setup();
  await waitFor(() => expect(result.current.data?.items[0].action.epoch).toBe(7));
  act(() => {
    client.setQueryData(["me"], { email: "first@example.test", cash_usd: "9000" });
  });
  await act(async () => {
    await result.current.refetch();
  });
  expect(result.current.data?.items[0].quote).toBeNull();
  await act(async () => {
    await result.current.refetch();
  });
  expect(result.current.data?.items[0].action.epoch).toBe(8);
  expect(result.current.data?.items[0].quote?.bid).toBe("100");
});

it("aborts in-flight healthy results when a newer same-generation stock hold enters cache", async () => {
  let release: (value: Response) => void = () => {};
  const fetch = vi
    .fn()
    .mockResolvedValueOnce(new Response(JSON.stringify(payload())))
    .mockImplementationOnce(
      () =>
        new Promise<Response>((resolve) => {
          release = resolve;
        }),
    );
  vi.stubGlobal("fetch", fetch);
  const { result, client } = setup();
  await waitFor(() => expect(result.current.data?.items[0].quote?.bid).toBe("100"));
  let pending: Promise<unknown>;
  act(() => {
    pending = result.current.refetch();
  });
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
  act(() => {
    client.setQueryData(["stocks", "first@example.test"], timed(hold(payload(), 8)));
  });
  expect((fetch.mock.calls[1] as unknown as [string, RequestInit])[1].signal?.aborted).toBe(true);
  await act(async () => {
    release(new Response(JSON.stringify(payload())));
    await pending;
  });
  expect(result.current.data?.items[0]).toMatchObject({
    quote: null,
    action: { state: "suspended", epoch: 8 },
  });
});

it("rejects stale admission generation and newer-cache server evidence", async () => {
  let release: (value: Response) => void = () => {};
  const fetch = vi
    .fn()
    .mockResolvedValueOnce(new Response(JSON.stringify(payload({ generation: 2 }))))
    .mockResolvedValueOnce(new Response(JSON.stringify(payload())))
    .mockImplementationOnce(
      () =>
        new Promise<Response>((resolve) => {
          release = resolve;
        }),
    );
  vi.stubGlobal("fetch", fetch);
  const { result, client } = setup();
  await waitFor(() => expect(result.current.data?.admission.generation).toBe(2));
  await act(async () => {
    await result.current.refetch();
  });
  expect(result.current.data?.admission.generation).toBe(2);
  let pending: Promise<unknown>;
  act(() => {
    pending = result.current.refetch();
  });
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(3));
  const newer = timed(payload({ generation: 2 }));
  newer.server_now = stamp(2);
  act(() => {
    client.setQueryData(["stocks", "first@example.test"], newer);
  });
  await act(async () => {
    release(new Response(JSON.stringify(payload({ generation: 2 }))));
    await pending;
  });
  expect(result.current.data?.server_now).toBe(stamp(2));
});

it("resets high-water only after logout and login, preserving crypto cache", async () => {
  const first = hold(payload(), 9);
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(aligned(first))))
      .mockImplementation(async (path: string) =>
        path === "/api/v1/auth/me"
          ? new Response(JSON.stringify({ email: "first@example.test", cash_usd: "10000" }))
          : new Response(JSON.stringify(payload())),
      ),
  );
  const { result, client } = setup();
  await waitFor(() => expect(result.current.data?.items[0].action.epoch).toBe(9));
  await act(async () => {
    await clearPrivateQueries(client);
    client.setQueryData(["me"], null);
  });
  await waitFor(() => expect(result.current.data).toBeUndefined());
  act(() => {
    client.setQueryData(["me"], { email: "first@example.test", cash_usd: "10000" });
  });
  await waitFor(() => expect(result.current.data?.items[0].action.epoch).toBe(1));
});

it("catches background expiry on focus without waiting for the throttled timer", async () => {
  let now = 0;
  vi.spyOn(performance, "now").mockImplementation(() => now);
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => new Response(JSON.stringify(payload()))),
  );
  const { result, client } = setup();
  await waitFor(() => expect(result.current.data?.items[0].quote?.bid).toBe("100"));
  now = 301_000;
  act(() => {
    window.dispatchEvent(new Event("focus"));
  });
  expect(
    client.getQueryData<TimedStocks>(["stocks", "first@example.test"])?.items[0].quote,
  ).toBeNull();
  expect(result.current.data?.items[0].action.checked_at).toBeNull();
});

it("schedules a cache purge at the nearest millisecond boundary before polling or display ticks", async () => {
  vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout", "setInterval", "clearInterval"] });
  let now = 0;
  vi.spyOn(performance, "now").mockImplementation(() => now);
  const body = payload();
  body.items.forEach((x) => {
    x.action.valid_until = stamp(0.125);
  });
  const fetch = vi.fn(async () => new Response(JSON.stringify(aligned(body))));
  vi.stubGlobal("fetch", fetch);
  const { result, client, unmount } = setup();
  for (let i = 0; i < 5; i++)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
  expect(result.current.data?.items[0].quote?.bid).toBe("100");
  now = 124;
  await act(async () => {
    await vi.advanceTimersByTimeAsync(124);
  });
  expect(
    client.getQueryData<TimedStocks>(["stocks", "first@example.test"])?.items[0].quote?.bid,
  ).toBe("100");
  now = 125;
  await act(async () => {
    await vi.advanceTimersByTimeAsync(1);
  });
  expect(
    client.getQueryData<TimedStocks>(["stocks", "first@example.test"])?.items[0].quote,
  ).toBeNull();
  expect(result.current.data?.items[0].action.state).toBe("unknown");
  expect(fetch).toHaveBeenCalledTimes(1);
  unmount();
  now = 2000;
  await act(async () => {
    await vi.advanceTimersByTimeAsync(1875);
  });
  expect(fetch).toHaveBeenCalledTimes(1);
});

it("reschedules simultaneous permission/calendar/monitor deadlines on cache changes", async () => {
  vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout", "setInterval", "clearInterval"] });
  let now = 0;
  vi.spyOn(performance, "now").mockImplementation(() => now);
  const fetch = vi.fn(async () => new Response(JSON.stringify(payload())));
  vi.stubGlobal("fetch", fetch);
  const { result, client } = setup();
  for (let i = 0; i < 5; i++)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
  expect(result.current.data?.items[0].quote?.bid).toBe("100");
  const replacement = timed();
  replacement.transport.round_trip_ms = 25;
  replacement.admission.valid_until = stamp(0.125);
  replacement.items.forEach((x) => {
    x.session.valid_until = stamp(0.125);
    x.action.valid_until = stamp(0.125);
  });
  act(() => {
    client.setQueryData(["stocks", "first@example.test"], replacement);
  });
  now = 99;
  await act(async () => {
    await vi.advanceTimersByTimeAsync(99);
  });
  expect(
    client.getQueryData<TimedStocks>(["stocks", "first@example.test"])?.items[0].quote?.bid,
  ).toBe("100");
  now = 100;
  await act(async () => {
    await vi.advanceTimersByTimeAsync(1);
  });
  expect(
    client.getQueryData<TimedStocks>(["stocks", "first@example.test"])?.items[0],
  ).toMatchObject({
    quote: null,
    action: { state: "unknown", epoch: 0, checked_at: null, valid_until: null },
    session: { state: "unknown", valid_until: null },
  });
  expect(fetch).toHaveBeenCalledTimes(1);
  // Consumed deadlines are removed; there is no zero-delay busy reschedule.
  const count = vi.getTimerCount();
  await act(async () => {
    await vi.advanceTimersByTimeAsync(10);
  });
  expect(vi.getTimerCount()).toBeLessThanOrEqual(count);
});

it.each(["quote expiry", "session close"])(
  "does not reanchor an equal-time healthy reply after local %s",
  async (kind) => {
    let now = 0;
    vi.spyOn(performance, "now").mockImplementation(() => now);
    const body = payload(kind === "quote expiry" ? { age: 119 } : { close: 1 });
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify(aligned(body)))),
    );
    const { result, client } = setup();
    await waitFor(() => expect(result.current.data?.items[0].quote?.bid).toBe("100"));
    now = 1000;
    act(() => {
      window.dispatchEvent(new Event("focus"));
    });
    if (kind === "quote expiry")
      expect(
        client.getQueryData<TimedStocks>(["stocks", "first@example.test"])?.items[0].quote,
      ).toBeNull();
    else expect(result.current.data?.items[0].session.state).toBe("closed");
    await act(async () => {
      await result.current.refetch();
    });
    if (kind === "quote expiry") expect(result.current.data?.items[0].quote).toBeNull();
    else expect(result.current.data?.items[0].session.state).toBe("closed");
  },
);

it("retains the original transport anchor when an equal snapshot arrives before expiry", async () => {
  let now = 0;
  vi.spyOn(performance, "now").mockImplementation(() => now);
  const body = payload({ age: 119 });
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => new Response(JSON.stringify(aligned(body)))),
  );
  const { result, client } = setup();
  await waitFor(() => expect(result.current.data?.items[0].quote?.bid).toBe("100"));
  now = 500;
  await act(async () => {
    await result.current.refetch();
  });
  expect(
    client.getQueryData<TimedStocks>(["stocks", "first@example.test"])?.transport.received_at,
  ).toBe(0);
  now = 1000;
  act(() => {
    window.dispatchEvent(new Event("focus"));
  });
  expect(
    client.getQueryData<TimedStocks>(["stocks", "first@example.test"])?.items[0].quote,
  ).toBeNull();
});

it.each(["equal", "older"])(
  "preserves independent consumed session authority on %s generic redaction",
  async (kind) => {
    let now = 0;
    vi.spyOn(performance, "now").mockImplementation(() => now);
    const first = payload({ close: 1 });
    const denied = payload({ close: 1 });
    denied.server_now = kind === "older" ? stamp(-0.5) : stamp(0);
    denied.items.forEach((x) => {
      x.action = {
        state: "unknown",
        reason: "monitor_unavailable",
        epoch: 0,
        checked_at: null,
        valid_until: null,
      } as never;
      x.quote = null;
      x.quote_reason = "permission_unavailable";
      x.valuation_reason = "action_unavailable";
    });
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(new Response(JSON.stringify(first)))
        .mockResolvedValueOnce(new Response(JSON.stringify(denied))),
    );
    const { result, client } = setup();
    await waitFor(() => expect(result.current.data?.items[0].quote?.bid).toBe("100"));
    now = 1000;
    act(() => {
      window.dispatchEvent(new Event("focus"));
    });
    expect(result.current.data?.items[0].session.state).toBe("closed");
    await act(async () => {
      await result.current.refetch();
    });
    expect(result.current.data?.items[0]).toMatchObject({
      quote: null,
      action: { epoch: 0, state: "unknown" },
      session: { state: "closed" },
    });
    expect(
      client.getQueryData<TimedStocks>(["stocks", "first@example.test"])?.items[0].session.state,
    ).toBe("closed");
  },
);

it.each(["same cache", "cache remount"])(
  "retains categorical admission/calendar revocation through older generic facts (%s)",
  async (mode) => {
    const revoked = payload({ state: "unavailable" });
    revoked.server_now = stamp(2);
    revoked.items.forEach((x) => {
      x.session = {
        ...x.session,
        state: "unknown",
        opens_at: null,
        closes_at: null,
        next_open_at: null,
        valid_until: null,
      } as never;
      x.session_reason = "unknown";
    });
    const old = payload();
    old.items.forEach((x) => {
      x.action = {
        state: "unknown",
        reason: "monitor_unavailable",
        epoch: 0,
        checked_at: null,
        valid_until: null,
      } as never;
      x.quote = null;
      x.quote_reason = "permission_unavailable";
      x.valuation_reason = "action_unavailable";
    });
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(new Response(JSON.stringify(revoked)))
        .mockResolvedValue(new Response(JSON.stringify(old))),
    );
    const first = setup();
    await waitFor(() => expect(first.result.current.data?.admission.state).toBe("unavailable"));
    if (mode === "same cache") {
      await act(async () => {
        await first.result.current.refetch();
      });
      expect(first.result.current.data?.admission.state).toBe("unavailable");
      expect(first.result.current.data?.items[0].session.state).toBe("unknown");
    } else {
      first.unmount();
      first.client.removeQueries({ queryKey: ["stocks"] });
      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={first.client}>{children}</QueryClientProvider>
      );
      const next = renderHook(() => useStocks(), { wrapper });
      await waitFor(() => expect(next.result.current.isSuccess).toBe(true));
      expect(next.result.current.data?.admission.state).toBe("unavailable");
      expect(next.result.current.data?.items[0].session.state).toBe("unknown");
    }
    expect(
      first.client.getQueryData<TimedStocks>(["stocks", "first@example.test"])?.server_now,
    ).toBe(stamp(2));
  },
);
