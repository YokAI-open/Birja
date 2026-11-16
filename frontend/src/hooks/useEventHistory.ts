import { useCallback, useEffect, useMemo, useSyncExternalStore } from "react";
import { useInfiniteQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import { fetchEventHistory } from "@/api/eventHistory";
import type { PortfolioTarget } from "./usePortfolioTarget";
import { financialScope, revokePortfolioTarget } from "./useQuote";

type Guard = { email: string | null; epoch: number; seen: Map<string, Set<string>> };
const guards = new WeakMap<QueryClient, Guard>();
const who = (client: QueryClient) =>
  client.getQueryData<{ email: string } | null>(["me"])?.email ?? null;
function guardFor(client: QueryClient) {
  let guard = guards.get(client);
  if (guard) return guard;
  guard = { email: who(client), epoch: 0, seen: new Map() };
  guards.set(client, guard);
  const current = guard;
  client.getQueryCache().subscribe(() => {
    const email = who(client);
    if (email === current.email) return;
    const old = current.email;
    current.email = email;
    current.epoch++;
    current.seen.clear();
    if (old !== null) {
      client.removeQueries({ queryKey: ["eventHistory", old] });
      client.removeQueries({ queryKey: ["history", old] });
    }
  });
  return guard;
}

/** Capture the current owner lifecycle when a financial mutation starts. */
export function eventHistorySession(client: QueryClient) {
  const { email, epoch } = guardFor(client);
  return { email, epoch };
}

export function useEventHistory(target: PortfolioTarget | null) {
  const client = useQueryClient();
  const guard = guardFor(client);
  const subscribe = useCallback(
    (notify: () => void) => client.getQueryCache().subscribe(notify),
    [client],
  );
  const epoch = useSyncExternalStore(subscribe, () => guard.epoch);
  const scope = useMemo(() => financialScope(client, target), [client, target]);
  const email = scope.owner,
    portfolioId = scope.portfolioId;
  const seenKey = JSON.stringify([email, portfolioId, epoch]);
  const key = useMemo(
    () => ["eventHistory", email, portfolioId, epoch] as const,
    [email, portfolioId, epoch],
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
        const page = await fetchEventHistory(target.portfolioId, { cursor: pageParam }, signal);
        signal.throwIfAborted();
        if (
          !scope.current() ||
          guard.epoch !== epoch ||
          client.getQueryCache().find({ queryKey: key, exact: true }) !== owner
        )
          throw new Error("History session changed");
        return page;
      } catch (error) {
        if (
          scope.current() &&
          error instanceof ApiError &&
          error.code === "portfolio_unavailable"
        ) {
          guard.seen.delete(seenKey);
          revokePortfolioTarget(client, target);
        }
        if (
          scope.current() &&
          guard.epoch === epoch &&
          error instanceof ApiError &&
          error.status === 401
        )
          client.setQueryData(["me"], null);
        throw error;
      }
    },
    getNextPageParam: (page) => page.next_cursor ?? undefined,
    staleTime: 0,
    refetchInterval: false,
    refetchOnWindowFocus: true,
  });
  useEffect(() => {
    if (!scope.current() || guard.epoch !== epoch || !query.data) return;
    const seen = guard.seen.get(seenKey) ?? new Set<string>();
    guard.seen.set(seenKey, seen);
    const ids = query.data.pages.flatMap((page) => page.items.map((item) => item.id));
    if (ids.every((id) => seen.has(id))) return;
    ids.forEach((id) => seen.add(id));
    const views = [
      { queryKey: ["portfolio", email, portfolioId] },
      { queryKey: ["stockContext", email, portfolioId] },
    ];
    void (async () => {
      // Drop pending pre-event views before requesting authoritative replacements.
      await Promise.all(views.map((view) => client.cancelQueries(view)));
      if (!scope.current() || guard.epoch !== epoch) return;
      await Promise.all(views.map((view) => client.invalidateQueries(view)));
    })();
  }, [client, email, portfolioId, epoch, guard, query.data, scope, seenKey]);
  return {
    ...query,
    data: scope.current() && guard.epoch === epoch ? query.data : undefined,
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
