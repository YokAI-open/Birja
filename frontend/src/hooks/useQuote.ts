import { useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import { fetchQuote, type Order } from "@/api/trades";
import type { PortfolioTarget, PortfolioTargetEpoch } from "./usePortfolioTarget";
import { eventHistorySession } from "./useEventHistory";

const clients = new WeakSet<QueryClient>();
const revoked = new WeakSet<PortfolioTargetEpoch>();

/** A server refusal only removes authority; fresh metadata must resolve it again. */
export function revokePortfolioTarget(client: QueryClient, target: PortfolioTarget) {
  revoked.add(target.epoch);
  client.setQueryData<readonly { id: string; name: string }[]>(
    ["portfolios", target.owner],
    (values) => values?.filter((value) => value.id !== target.portfolioId),
  );
  void client.invalidateQueries({ queryKey: ["portfolios", target.owner] });
}

export function financialScope(client: QueryClient, target: PortfolioTarget | null) {
  if (!clients.has(client)) {
    clients.add(client);
    let owner = eventHistorySession(client).email;
    client.getQueryCache().subscribe(() => {
      const next = eventHistorySession(client).email;
      if (next === owner) return;
      const previous = owner;
      owner = next;
      if (previous !== null)
        for (const prefix of ["quote", "holding", "cryptoTradeState"])
          client.removeQueries({ queryKey: [prefix, previous] });
    });
  }
  const session = eventHistorySession(client);
  return {
    owner: target?.owner ?? null,
    portfolioId: target?.portfolioId ?? null,
    epoch: session.epoch,
    current: () => {
      const now = eventHistorySession(client);
      return (
        target !== null &&
        target.isCurrent() &&
        !revoked.has(target.epoch) &&
        now.email === target.owner &&
        now.epoch === session.epoch
      );
    },
  };
}

export function quoteKey(target: PortfolioTarget | null, order: Order | null) {
  return [
    "quote",
    target?.owner ?? null,
    target?.portfolioId ?? null,
    target?.epoch.session ?? null,
    order?.symbol ?? null,
    order?.side ?? null,
    order?.amount_usd !== undefined ? "usd" : "quantity",
    order?.amount_usd ?? order?.quantity ?? "",
  ] as const;
}

/** Server-computed preview. The page validates and debounces; null means "no valid input". */
export function useQuote(target: PortfolioTarget | null, order: Order | null) {
  const queryClient = useQueryClient();
  const scope = financialScope(queryClient, target);
  const key = quoteKey(target, order);
  const query = useQuery({
    queryKey: key,
    queryFn: async ({ signal }) => {
      if (target === null || order === null || !scope.current()) {
        throw new Error("Portfolio target changed");
      }
      const owner = queryClient.getQueryCache().find({ queryKey: key, exact: true });
      try {
        const response = await fetchQuote(target.portfolioId, order, signal);
        signal.throwIfAborted();
        if (
          !scope.current() ||
          queryClient.getQueryCache().find({ queryKey: key, exact: true }) !== owner
        )
          throw new Error("Portfolio target changed");
        return response;
      } catch (error) {
        if (scope.current() && error instanceof ApiError && error.code === "portfolio_unavailable")
          revokePortfolioTarget(queryClient, target);
        if (scope.current() && error instanceof ApiError && error.status === 401) {
          queryClient.setQueryData(["me"], null);
        }
        throw error;
      }
    },
    enabled: order !== null && scope.current(),
    retry: false,
    gcTime: 0,
    refetchInterval: 30_000,
    refetchOnWindowFocus: true,
    staleTime: 0,
  });
  return { ...query, data: scope.current() && !query.isError ? query.data : undefined };
}
