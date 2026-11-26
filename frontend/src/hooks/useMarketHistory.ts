import { useCallback, useSyncExternalStore } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  historyInstrumentKey,
  requestMarketHistory,
  type HistoryInstrument,
  type HistoryRange,
} from "@/api/marketHistory";
import { eventHistorySession } from "./useEventHistory";

function waitForHistory(signal: AbortSignal) {
  return new Promise<void>((resolve, reject) => {
    signal.throwIfAborted();
    const timeout = window.setTimeout(() => {
      signal.removeEventListener("abort", abort);
      resolve();
    }, 2_000);
    const abort = () => {
      window.clearTimeout(timeout);
      reject(signal.reason);
    };
    signal.addEventListener("abort", abort, { once: true });
  });
}

export function useMarketHistory(instrument: HistoryInstrument | null, range: HistoryRange) {
  const client = useQueryClient();
  const { email } = eventHistorySession(client);
  const epoch = useSyncExternalStore(
    useCallback(
      (changed) =>
        client.getQueryCache().subscribe(({ query }) => {
          if (query.queryKey.length === 1 && query.queryKey[0] === "me") changed();
        }),
      [client],
    ),
    () => eventHistorySession(client).epoch,
  );
  const current = () => {
    const session = eventHistorySession(client);
    return email !== null && email === session.email && epoch === session.epoch;
  };
  const query = useQuery({
    queryKey: [
      "marketHistory",
      email,
      epoch,
      instrument && historyInstrumentKey(instrument),
      range,
    ],
    enabled: instrument !== null && current(),
    retry: false,
    gcTime: 0,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    queryFn: async ({ signal }) => {
      if (!instrument) throw new Error("No market history instrument");
      const bounded = AbortSignal.any([signal, AbortSignal.timeout(12_000)]);
      let response = await requestMarketHistory(instrument, range, bounded, current);
      for (let retries = 0; response.state === "pending" && retries < 3; retries++) {
        await waitForHistory(bounded);
        response = await requestMarketHistory(instrument, range, bounded, current);
      }
      return response;
    },
  });
  return {
    response: current() && !query.isError ? query.data : undefined,
    loading: instrument !== null && current() && query.isFetching,
    retry:
      instrument !== null && current()
        ? () => void query.refetch({ cancelRefetch: false })
        : undefined,
  };
}
