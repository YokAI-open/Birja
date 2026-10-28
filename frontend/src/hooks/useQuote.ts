import { keepPreviousData, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import { fetchQuote, type Order } from "@/api/trades";

export function quoteKey(order: Order) {
  return [
    "quote",
    order.symbol,
    order.side,
    order.amount_usd !== undefined ? "usd" : "quantity",
    order.amount_usd ?? order.quantity ?? "",
  ] as const;
}

/** Server-computed preview. The page validates and debounces; null means "no valid input". */
export function useQuote(order: Order | null) {
  const queryClient = useQueryClient();
  return useQuery({
    queryKey: order ? quoteKey(order) : ["quote", "none"],
    queryFn: async ({ signal }) => {
      if (order === null) {
        throw new Error("No order to quote");
      }
      try {
        return await fetchQuote(order, signal);
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
          void queryClient.invalidateQueries({ queryKey: ["me"] });
        }
        throw error;
      }
    },
    enabled: order !== null,
    retry: false,
    refetchInterval: 30_000,
    refetchOnWindowFocus: true,
    placeholderData: keepPreviousData,
    staleTime: 0,
  });
}
