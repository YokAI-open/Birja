import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import { fetchPrices } from "@/api/prices";

export function usePrices() {
  const queryClient = useQueryClient();
  return useQuery({
    queryKey: ["prices"],
    queryFn: async ({ signal }) => {
      try {
        return await fetchPrices(signal);
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
          // Session is gone: let the /me switch fall back to the sign-in card.
          void queryClient.invalidateQueries({ queryKey: ["me"] });
        }
        throw error;
      }
    },
    refetchInterval: 30_000,
    refetchOnWindowFocus: true,
    staleTime: 10_000,
  });
}
