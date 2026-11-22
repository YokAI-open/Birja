import { useCallback, useMemo, useSyncExternalStore } from "react";
import { useInfiniteQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import { fetchHistory } from "@/api/history";
import type { PortfolioTarget } from "./usePortfolioTarget";
import { financialScope, revokePortfolioTarget } from "./useQuote";
import { eventHistorySession } from "./useEventHistory";

export function useHistory(target: PortfolioTarget | null) {
  const client = useQueryClient();
  const subscribe = useCallback(
    (notify: () => void) => client.getQueryCache().subscribe(notify),
    [client],
  );
  const epoch = useSyncExternalStore(subscribe, () => eventHistorySession(client).epoch);
  const scope = useMemo(() => financialScope(client, target), [client, target]);
  const key = useMemo(
    () => ["history", scope.owner, scope.portfolioId, epoch] as const,
    [scope.owner, scope.portfolioId, epoch],
  );
  const query = useInfiniteQuery({
    queryKey: key,
    enabled: scope.current(),
    retry: false,
    gcTime: 0,
    initialPageParam: undefined as string | undefined,
    queryFn: async ({ signal, pageParam }) => {
      if (target === null || !scope.current()) throw new Error("Portfolio target changed");
      const owner = client.getQueryCache().find({ queryKey: key, exact: true });
      try {
        const page = await fetchHistory(target.portfolioId, { cursor: pageParam }, signal);
        signal.throwIfAborted();
        if (
          !scope.current() ||
          eventHistorySession(client).epoch !== epoch ||
          client.getQueryCache().find({ queryKey: key, exact: true }) !== owner
        )
          throw new Error("Portfolio target changed");
        return page;
      } catch (error) {
        if (scope.current() && error instanceof ApiError && error.code === "portfolio_unavailable")
          revokePortfolioTarget(client, target);
        if (scope.current() && error instanceof ApiError && error.status === 401)
          client.setQueryData(["me"], null);
        throw error;
      }
    },
    getNextPageParam: (page) => page.next_cursor ?? undefined,
    staleTime: 0,
    refetchInterval: false,
    refetchOnWindowFocus: true,
  });
  return {
    ...query,
    data: scope.current() && eventHistorySession(client).epoch === epoch ? query.data : undefined,
    refetch: (options?: Parameters<typeof query.refetch>[0]) =>
      scope.current()
        ? query.refetch(options)
        : Promise.reject(new Error("Portfolio target changed")),
    fetchNextPage: (options?: Parameters<typeof query.fetchNextPage>[0]) =>
      scope.current()
        ? query.fetchNextPage({ ...options, cancelRefetch: false })
        : Promise.reject(new Error("Portfolio target changed")),
  };
}
