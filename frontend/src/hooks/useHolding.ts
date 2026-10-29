import { useQuery } from "@tanstack/react-query";
import { fetchHolding } from "@/api/trades";

export function useHolding(symbol: string) {
  return useQuery({
    queryKey: ["holding", symbol],
    queryFn: ({ signal }) => fetchHolding(symbol, signal),
    staleTime: 10_000,
  });
}
