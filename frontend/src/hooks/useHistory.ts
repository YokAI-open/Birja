import { useInfiniteQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import { fetchHistory } from "@/api/history";

export function useHistory() {
  const client = useQueryClient();
  return useInfiniteQuery({
    queryKey: ["history"],
    initialPageParam: undefined as string | undefined,
    queryFn: async ({ signal, pageParam }) => {
      try {
        return await fetchHistory({ cursor: pageParam }, signal);
      } catch (error) {
        if (error instanceof ApiError && error.status === 401)
          void client.invalidateQueries({ queryKey: ["me"] });
        throw error;
      }
    },
    getNextPageParam: (page) => page.next_cursor ?? undefined,
    staleTime: 0,
    refetchInterval: false,
    refetchOnWindowFocus: true,
  });
}
