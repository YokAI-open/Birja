import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import { fetchHolding } from "@/api/trades";
import type { PortfolioTarget } from "./usePortfolioTarget";
import { financialScope, revokePortfolioTarget } from "./useQuote";

export function useHolding(target: PortfolioTarget | null, symbol: string) {
  const client = useQueryClient();
  const scope = financialScope(client, target);
  const key = ["holding", scope.owner, scope.portfolioId, scope.epoch, symbol] as const;
  const query = useQuery({
    queryKey: key,
    enabled: scope.current(),
    queryFn: async ({ signal }) => {
      if (target === null || !scope.current()) throw new Error("Portfolio target changed");
      const owner = client.getQueryCache().find({ queryKey: key, exact: true });
      try {
        const response = await fetchHolding(target.portfolioId, symbol, signal);
        signal.throwIfAborted();
        if (
          !scope.current() ||
          client.getQueryCache().find({ queryKey: key, exact: true }) !== owner
        )
          throw new Error("Portfolio target changed");
        return response;
      } catch (error) {
        if (scope.current() && error instanceof ApiError && error.code === "portfolio_unavailable")
          revokePortfolioTarget(client, target);
        if (scope.current() && error instanceof ApiError && error.status === 401)
          client.setQueryData(["me"], null);
        throw error;
      }
    },
    gcTime: 0,
    retry: false,
    staleTime: 10_000,
  });
  return { ...query, data: scope.current() && !query.isError ? query.data : undefined };
}
