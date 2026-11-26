import { useCallback, useRef, useSyncExternalStore } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchPortfolioValueHistory } from "@/api/portfolioValueHistory";
import type { PortfolioOverview } from "@/api/portfolioOverview";
import { subscribeMetadataEvents } from "@/lib/portfolioMetadataEvents";
import { eventHistorySession } from "./useEventHistory";
import {
  isPortfolioDeletionQuarantined,
  portfolioDeletionAuthorityGeneration,
  portfolioDeletionAuthorityReady,
} from "./usePortfolioDeletion";

export function usePortfolioValueHistory(
  active: readonly Pick<PortfolioOverview, "id">[] | undefined,
) {
  const client = useQueryClient();
  const { email } = eventHistorySession(client);
  const epoch = useSyncExternalStore(
    useCallback((changed) => client.getQueryCache().subscribe(changed), [client]),
    () => eventHistorySession(client).epoch,
  );
  const lifecycle = useRef(0);
  const revision = useSyncExternalStore(
    useCallback(
      (changed) =>
        subscribeMetadataEvents((_, kind) => {
          if (kind === "lifecycle") {
            lifecycle.current++;
            changed();
          }
        }),
      [],
    ),
    () => lifecycle.current,
  );
  const generation = portfolioDeletionAuthorityGeneration(client);
  const ids = active?.map(({ id }) => id);
  const current = () => {
    if (!ids?.length || email === null || revision !== lifecycle.current) return false;
    const session = eventHistorySession(client);
    if (
      session.email !== email ||
      session.epoch !== epoch ||
      portfolioDeletionAuthorityGeneration(client) !== generation ||
      !portfolioDeletionAuthorityReady(client, email)
    )
      return false;
    const latest = client.getQueryData<readonly PortfolioOverview[]>([
      "portfolioOverview",
      email,
      epoch,
    ]);
    return (
      latest?.length === ids.length &&
      latest.every(
        ({ id }, index) => id === ids[index] && !isPortfolioDeletionQuarantined(client, email, id),
      )
    );
  };
  const enabled = current();
  const query = useQuery({
    queryKey: ["portfolioValueHistory", email, epoch, generation, revision, ids ?? []],
    enabled,
    retry: false,
    gcTime: 0,
    staleTime: 5 * 60_000,
    queryFn: async ({ signal }) => {
      if (!ids || !current()) throw new DOMException("Request context unavailable", "AbortError");
      return fetchPortfolioValueHistory(ids, signal, current);
    },
  });

  return {
    data: enabled && !query.isError ? query.data : undefined,
    loading: !!ids?.length && (!enabled || (query.isPending && query.isFetching)),
    failed: enabled && query.isError && !query.isFetching,
    retry: () => {
      if (current()) void query.refetch({ cancelRefetch: false });
    },
  };
}
