import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import { fetchPortfolio } from "@/api/portfolio";

export function usePortfolio() {
  const queryClient = useQueryClient();
  return useQuery({
    queryKey: ["portfolio"],
    queryFn: async ({ signal }) => {
      try {
        return await fetchPortfolio(signal);
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
          void queryClient.invalidateQueries({ queryKey: ["me"] });
        }
        throw error;
      }
    },
    refetchInterval: 30_000,
    staleTime: 10_000,
    refetchOnWindowFocus: true,
  });
}
