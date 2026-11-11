import { useEffect, useReducer } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import { fetchStocks, stockInstant, type StocksResponse, type TimedStocks } from "@/api/stocks";
import { useMe } from "./useMe";

// Date.parse truncates fractional milliseconds. Round authority time up and
// deadlines/source-event times down so browser precision never extends authority.
const floorTime = (value: string) => Date.parse(value);
const ceilTime = (value: string) =>
  Date.parse(value) + (/\.\d{3}\d*[1-9]\d*(?:Z|\+00:00)$/.test(value) ? 1 : 0);
const unknownAction = () =>
  ({
    state: "unknown",
    reason: "monitor_unavailable",
    epoch: 0,
    checked_at: null,
    valid_until: null,
  }) as const;

/** Conservative projection only reduces server authority. No browser wall clock. */
export function projectStocks(data: TimedStocks, now = performance.now()): StocksResponse {
  const elapsed = Math.max(0, now - data.transport.received_at);
  const lower = floorTime(data.server_now) + elapsed;
  const offset = data.authority_offset_ms ?? 0;
  const upper = ceilTime(data.server_now) + elapsed + data.transport.round_trip_ms + offset;
  const allowed =
    data.admission.state === "approved" &&
    data.admission.valid_until !== null &&
    upper < floorTime(data.admission.valid_until);
  return {
    ...data,
    admission: allowed
      ? data.admission
      : { state: "unavailable", generation: null, valid_until: null },
    items: data.items.map((item) => {
      const bounds = item.session;
      const reviewed = bounds.valid_until !== null && upper < floorTime(bounds.valid_until);
      let state = bounds.state;
      if (!reviewed) state = "unknown";
      else if (state === "open") {
        if (bounds.closes_at !== null && upper >= floorTime(bounds.closes_at)) state = "closed";
        else if (bounds.opens_at === null || lower < ceilTime(bounds.opens_at)) state = "unknown";
      }
      const action =
        !allowed || !reviewed
          ? unknownAction()
          : item.action.state === "current" &&
              (item.action.valid_until === null || upper >= floorTime(item.action.valid_until))
            ? {
                ...item.action,
                state: "unknown" as const,
                reason: "monitor_unavailable" as const,
                valid_until: null,
              }
            : item.action;
      const age =
        item.quote === null
          ? 0
          : Math.max(
              item.quote.age_seconds,
              (ceilTime(data.server_now) - floorTime(item.quote.event_at)) / 1000,
            ) +
            (data.transport.round_trip_ms + elapsed + offset) / 1000;
      const canDisplay =
        allowed &&
        reviewed &&
        state !== "unknown" &&
        action.state === "current" &&
        item.quote_reason !== "permission_unavailable" &&
        age < 120;
      const quote =
        canDisplay && item.quote
          ? { ...item.quote, age_seconds: Math.max(0, Math.floor(age)) }
          : null;
      const reason =
        !allowed || !reviewed
          ? "permission_unavailable"
          : item.quote_reason === "recent"
            ? age >= 120
              ? "stale"
              : state !== "open"
                ? "session_unavailable"
                : "recent"
            : item.quote_reason;
      return {
        ...item,
        quote,
        action,
        quote_reason: reason,
        valuation_reason:
          quote !== null
            ? "available"
            : action.reason === "post_split_quote_missing"
              ? "post_split_quote_missing"
              : action.state !== "current"
                ? "action_unavailable"
                : "quote_unavailable",
        session_reason: state,
        session: reviewed
          ? { ...bounds, state }
          : {
              state: "unknown",
              opens_at: null,
              closes_at: null,
              next_open_at: null,
              valid_until: null,
              timezone: "America/New_York",
            },
      };
    }),
  };
}

function purgeExpired(data: TimedStocks): TimedStocks {
  const projected = projectStocks(data);
  return {
    ...data,
    admission: projected.admission,
    items: projected.items.map((item, i) => ({
      ...item,
      // Preserve original ages/times: repeated projection must not add RTT twice.
      quote: item.quote === null ? null : data.items[i].quote,
    })),
  };
}

function safetyChanged(previous: TimedStocks, next: TimedStocks): boolean {
  return (
    previous.admission.state !== next.admission.state ||
    previous.items.some((item, i) => {
      const other = next.items[i];
      return (
        (item.quote !== null && other.quote === null) ||
        item.action.state !== other.action.state ||
        item.action.epoch !== other.action.epoch ||
        item.action.reason !== other.action.reason ||
        item.session.state !== other.session.state ||
        item.quote_reason !== other.quote_reason
      );
    })
  );
}

function nextDeadline(data: TimedStocks): number {
  const deadlines: number[] = [];
  const add = (value: string | null) => {
    if (value !== null) deadlines.push(floorTime(value));
  };
  if (data.admission.state === "approved") add(data.admission.valid_until);
  for (const item of data.items) {
    add(item.session.valid_until);
    if (item.session.state === "open") add(item.session.closes_at);
    if (item.action.state === "current") add(item.action.valid_until);
    if (item.quote !== null)
      deadlines.push(
        Math.min(
          floorTime(item.quote.event_at) + 120_000,
          ceilTime(data.server_now) + (120 - item.quote.age_seconds) * 1000,
        ),
      );
  }
  return (
    Math.min(...deadlines) -
    ceilTime(data.server_now) -
    data.transport.round_trip_ms -
    (data.authority_offset_ms ?? 0) -
    Math.max(0, performance.now() - data.transport.received_at)
  );
}

type Mark = { epoch: number; at: bigint };
type Guard = {
  email: string | null;
  lifecycle: number;
  marks: Map<number, Mark>;
  clock: { upper: number; received: number } | null;
  latest: TimedStocks | null;
};
const guards = new WeakMap<ReturnType<typeof useQueryClient>, Guard>();
const emailOf = (client: ReturnType<typeof useQueryClient>) =>
  client.getQueryData<{ email: string } | null>(["me"])?.email ?? null;
function upperClock(data: TimedStocks, now: number): number {
  return (
    ceilTime(data.server_now) +
    data.transport.round_trip_ms +
    (data.authority_offset_ms ?? 0) +
    Math.max(0, now - data.transport.received_at)
  );
}
function observe(guard: Guard, data: TimedStocks) {
  const now = performance.now();
  guard.clock = {
    upper: Math.max(
      upperClock(data, now),
      guard.clock === null
        ? -Infinity
        : guard.clock.upper + Math.max(0, now - guard.clock.received),
    ),
    received: now,
  };
  const at = stockInstant(data.server_now);
  for (const item of data.items) {
    const old = guard.marks.get(item.id);
    guard.marks.set(item.id, {
      epoch: Math.max(old?.epoch ?? 0, item.action.epoch),
      at: old && old.at > at ? old.at : at,
    });
  }
}
function remember(guard: Guard, data: TimedStocks) {
  observe(guard, data);
  guard.latest = data;
}
function withAuthorityClock(guard: Guard, data: TimedStocks): TimedStocks {
  const now = performance.now();
  const previousUpper =
    guard.clock === null ? -Infinity : guard.clock.upper + Math.max(0, now - guard.clock.received);
  return {
    ...data,
    authority_offset_ms:
      (data.authority_offset_ms ?? 0) + Math.max(0, previousUpper - upperClock(data, now)),
  };
}
function guardFor(client: ReturnType<typeof useQueryClient>): Guard {
  const existing = guards.get(client);
  if (existing) return existing;
  const guard: Guard = {
    email: emailOf(client),
    lifecycle: 0,
    marks: new Map(),
    clock: null,
    latest: null,
  };
  guards.set(client, guard);
  client.getQueryCache().subscribe((event) => {
    const email = emailOf(client);
    if (email !== guard.email) {
      guard.email = email;
      guard.lifecycle++;
      guard.marks.clear();
      guard.clock = null;
      guard.latest = null;
    }
    if (
      email !== null &&
      event.query.queryKey[0] === "stocks" &&
      event.query.queryKey[1] === email &&
      event.type === "updated"
    ) {
      const data = event.query.state.data as TimedStocks | undefined;
      if (data) remember(guard, data);
    }
  });
  return guard;
}

/** Late redactions may remove facts, but never replace independent authority. */
function mergeReduction(previous: TimedStocks, response: TimedStocks): TimedStocks {
  const incoming = new Map(response.items.map((item) => [item.id, item]));
  return {
    ...previous,
    admission: response.admission.state === "unavailable" ? response.admission : previous.admission,
    items: previous.items.map((old) => {
      const next = incoming.get(old.id);
      if (!next || next.action.state === "current") return old;
      const action =
        next.action.epoch === 0
          ? next.action
          : old.action.state === "current"
            ? next.action
            : old.action;
      return {
        ...old,
        action,
        quote: null,
        quote_reason: "permission_unavailable",
        valuation_reason:
          action.reason === "post_split_quote_missing"
            ? "post_split_quote_missing"
            : "action_unavailable",
      };
    }),
  };
}

export function useStocks() {
  const client = useQueryClient();
  const { data: me } = useMe();
  const key = ["stocks", me?.email ?? null] as const;
  const query = useQuery({
    queryKey: key,
    enabled: Boolean(me),
    queryFn: async ({ signal }) => {
      const guard = guardFor(client);
      const lifecycle = guard.lifecycle;
      const identity = emailOf(client);
      const owner = client.getQueryCache().find({ queryKey: key, exact: true });
      const initial = client.getQueryData<TimedStocks>(key);
      const superseded = new AbortController();
      const requestSignal = AbortSignal.any([signal, superseded.signal]);
      const unsubscribe = client.getQueryCache().subscribe((event) => {
        const current = client.getQueryData<TimedStocks>(key);
        if (
          (event.query === owner && event.type === "removed") ||
          emailOf(client) !== identity ||
          guard.lifecycle !== lifecycle ||
          (current &&
            current !== initial &&
            (current.admission.state === "unavailable" ||
              (current.admission.generation ?? 0) > (initial?.admission.generation ?? 0) ||
              current.items.some(
                (item, i) =>
                  item.action.state !== "current" ||
                  item.action.epoch > (initial?.items[i].action.epoch ?? 0),
              )))
        )
          superseded.abort();
      });
      try {
        const response = await fetchStocks(requestSignal);
        requestSignal.throwIfAborted();
        if (
          !identity ||
          emailOf(client) !== identity ||
          guard.lifecycle !== lifecycle ||
          client.getQueryCache().find({ queryKey: key, exact: true }) !== owner
        )
          throw new Error("Stock session changed");
        const current = client.getQueryData<TimedStocks>(key);
        const previous = guard.latest;
        const reducing =
          response.admission.state === "unavailable" ||
          response.items.some((item) => item.action.state !== "current");
        if (
          reducing &&
          previous &&
          ([...guard.marks.values()].some((mark) => stockInstant(response.server_now) <= mark.at) ||
            (response.admission.state === "approved" &&
              (response.admission.generation ?? 0) < (previous.admission.generation ?? 0)))
        ) {
          // Public redaction may omit stronger incoming facts. Keep their raw
          // ordering/clock high-water independently of the retained snapshot.
          observe(guard, response);
          return purgeExpired(withAuthorityClock(guard, mergeReduction(previous, response)));
        }
        // Concurrent invalidation may have installed newer permission evidence.
        if (
          current &&
          (((current.admission.generation ?? 0) > (response.admission.generation ?? 0) &&
            response.admission.state === "approved") ||
            (current !== initial &&
              current.admission.state === "unavailable" &&
              response.admission.state === "approved") ||
            (stockInstant(current.server_now) > stockInstant(response.server_now) &&
              response.items.some((item) => item.action.state === "current")))
        )
          throw new Error("Superseded stock response");
        for (const item of response.items) {
          const mark = guard.marks.get(item.id);
          if (
            item.action.state === "current" &&
            mark &&
            (item.action.epoch < mark.epoch || stockInstant(response.server_now) <= mark.at)
          )
            throw new Error("Superseded stock action response");
        }
        // Purge expired permission/review material before entering the cache.
        return purgeExpired(withAuthorityClock(guard, response));
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
          client.setQueryData(["me"], null);
          void client.invalidateQueries({ queryKey: ["me"] });
        }
        throw error;
      } finally {
        unsubscribe();
      }
    },
    retry: false,
    refetchInterval: 30_000,
    refetchOnWindowFocus: true,
    staleTime: 10_000,
    gcTime: 0,
  });
  const [, tick] = useReducer((n: number) => n + 1, 0);
  useEffect(() => {
    guardFor(client);
    const queryKey = ["stocks", me?.email ?? null];
    let deadline: ReturnType<typeof setTimeout> | undefined;
    let purging = false;
    const update = () => {
      clearTimeout(deadline);
      const cached = client.getQueryData<TimedStocks>(queryKey);
      if (!cached || queryKey[1] === null) return;
      const purged = purgeExpired(cached);
      if (safetyChanged(cached, purged)) {
        purging = true;
        client.setQueryData(queryKey, purged);
        purging = false;
      }
      const delay = nextDeadline(purged);
      if (Number.isFinite(delay))
        deadline = setTimeout(update, Math.min(2_147_483_647, Math.max(1, delay)));
      tick();
    };
    const unsubscribe = client.getQueryCache().subscribe((event) => {
      if (
        !purging &&
        (event.type === "updated" || event.type === "removed") &&
        event.query.queryKey[0] === "stocks" &&
        event.query.queryKey[1] === queryKey[1]
      )
        update();
    });
    // Display age updates are independent of exact safety-boundary timers.
    const display = setInterval(update, 1000);
    window.addEventListener("focus", update);
    window.addEventListener("visibilitychange", update);
    update();
    return () => {
      clearTimeout(deadline);
      clearInterval(display);
      unsubscribe();
      window.removeEventListener("focus", update);
      window.removeEventListener("visibilitychange", update);
    };
  }, [client, me?.email]);
  return { ...query, data: me && query.data ? projectStocks(query.data) : undefined };
}
