import { useCallback, useMemo, useSyncExternalStore } from "react";
import { useInfiniteQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import { fetchEventHistory } from "@/api/eventHistory";
import { useMe } from "./useMe";

type Guard = { email: string | null; epoch: number };
const guards = new WeakMap<QueryClient, Guard>();
const who = (client: QueryClient) =>
  client.getQueryData<{ email: string } | null>(["me"])?.email ?? null;
function guardFor(client: QueryClient) {
  let guard = guards.get(client);
  if (guard) return guard;
  guard = { email: who(client), epoch: 0 };
  guards.set(client, guard);
  const current = guard;
  client.getQueryCache().subscribe(() => {
    const email = who(client);
    if (email === current.email) return;
    const old = current.email;
    current.email = email;
    current.epoch++;
    if (old !== null) client.removeQueries({ queryKey: ["eventHistory", old] });
  });
  return guard;
}

export function useEventHistory() {
  const client = useQueryClient();
  useMe();
  const guard = guardFor(client);
  const subscribe = useCallback(
    (notify: () => void) => client.getQueryCache().subscribe(notify),
    [client],
  );
  const epoch = useSyncExternalStore(subscribe, () => guard.epoch);
  const email = who(client);
  const key = useMemo(() => ["eventHistory", email, epoch] as const, [email, epoch]);
  const query = useInfiniteQuery({
    queryKey: key,
    enabled: email !== null,
    retry: false,
    gcTime: 0,
    initialPageParam: undefined as string | undefined,
    queryFn: async ({ signal, pageParam }) => {
      const owner = client.getQueryCache().find({ queryKey: key, exact: true });
      try {
        const page = await fetchEventHistory({ cursor: pageParam }, signal);
        signal.throwIfAborted();
        if (
          who(client) !== email ||
          guard.epoch !== epoch ||
          client.getQueryCache().find({ queryKey: key, exact: true }) !== owner
        )
          throw new Error("History session changed");
        return page;
      } catch (error) {
        if (
          who(client) === email &&
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
  return {
    ...query,
    data: email !== null && who(client) === email && guard.epoch === epoch ? query.data : undefined,
    fetchNextPage: (options?: Parameters<typeof query.fetchNextPage>[0]) =>
      query.fetchNextPage({ ...options, cancelRefetch: false }),
  };
}
