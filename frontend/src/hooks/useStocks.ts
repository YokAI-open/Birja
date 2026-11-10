import { useEffect, useReducer } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import { fetchStocks, type StocksResponse, type TimedStocks } from "@/api/stocks";
import { useMe } from "./useMe";

/** Conservative projection only reduces server authority. No browser wall clock. */
export function projectStocks(data: TimedStocks, now = performance.now()): StocksResponse {
  const elapsed = Math.max(0, now - data.transport.received_at);
  const lower = Date.parse(data.server_now) + elapsed;
  const upper = lower + data.transport.round_trip_ms;
  const allowed =
    data.admission.state === "approved" &&
    data.admission.valid_until !== null &&
    upper < Date.parse(data.admission.valid_until);
  return {
    ...data,
    admission: allowed
      ? data.admission
      : { state: "unavailable", generation: null, valid_until: null },
    items: data.items.map((item) => {
      const bounds = item.session;
      const reviewed = bounds.valid_until !== null && upper < Date.parse(bounds.valid_until);
      let state = bounds.state;
      if (!reviewed) state = "unknown";
      else if (state === "open") {
        if (bounds.closes_at !== null && upper >= Date.parse(bounds.closes_at)) state = "closed";
        else if (bounds.opens_at === null || lower < Date.parse(bounds.opens_at)) state = "unknown";
      }
      // A closed/unknown server state is never locally promoted to open.
      const age =
        item.quote === null
          ? 0
          : Math.max(
              item.quote.age_seconds,
              (Date.parse(data.server_now) - Date.parse(item.quote.event_at)) / 1000,
            ) +
            (data.transport.round_trip_ms + elapsed) / 1000;
      const canDisplay = allowed && reviewed && item.quote_reason !== "permission_unavailable";
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
        quote_reason: reason,
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
    items: data.items.map((item, i) => ({
      ...item,
      // Keep original ages/times: projecting a projected age would count RTT twice.
      quote: projected.items[i].quote === null ? null : item.quote,
      quote_reason: projected.items[i].quote_reason,
      session: projected.items[i].session,
      session_reason: projected.items[i].session_reason,
    })),
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
      const identity = client.getQueryData(["me"]);
      const owner = client.getQueryCache().find({ queryKey: key, exact: true });
      const initial = client.getQueryData<TimedStocks>(key);
      const superseded = new AbortController();
      const requestSignal = AbortSignal.any([signal, superseded.signal]);
      const unsubscribe = client.getQueryCache().subscribe((event) => {
        const current = client.getQueryData<TimedStocks>(key);
        if (
          (event.query === owner && event.type === "removed") ||
          client.getQueryData(["me"]) !== identity ||
          (current &&
            current !== initial &&
            (current.admission.state === "unavailable" ||
              (current.admission.generation ?? 0) > (initial?.admission.generation ?? 0)))
        )
          superseded.abort();
      });
      try {
        const response = await fetchStocks(requestSignal);
        requestSignal.throwIfAborted();
        if (
          !identity ||
          client.getQueryData(["me"]) !== identity ||
          client.getQueryCache().find({ queryKey: key, exact: true }) !== owner
        )
          throw new Error("Stock session changed");
        const current = client.getQueryData<TimedStocks>(key);
        // Concurrent invalidation may have installed newer permission evidence.
        if (
          current &&
          (((current.admission.generation ?? 0) > (response.admission.generation ?? 0) &&
            response.admission.state === "approved") ||
            (current !== initial &&
              current.admission.state === "unavailable" &&
              response.admission.state === "approved") ||
            Date.parse(current.server_now) > Date.parse(response.server_now))
        )
          throw new Error("Superseded stock response");
        // Purge expired permission/review material before entering the cache.
        return purgeExpired(response);
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
          client.setQueryData(["me"], null);
          client.removeQueries({ queryKey: ["stocks"] });
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
    // Display clock only; TanStack owns all networking and cancellation.
    const timer = setInterval(() => {
      const queryKey = ["stocks", me?.email ?? null];
      const cached = client.getQueryData<TimedStocks>(queryKey);
      if (cached) {
        const projected = projectStocks(cached);
        if (
          cached.admission.state !== projected.admission.state ||
          cached.items.some((item, i) => item.quote !== null && projected.items[i].quote === null)
        ) {
          client.setQueryData<TimedStocks>(queryKey, purgeExpired(cached));
        }
      }
      tick();
    }, 1000);
    return () => clearInterval(timer);
  }, [client, me?.email]);
  return { ...query, data: me && query.data ? projectStocks(query.data) : undefined };
}
