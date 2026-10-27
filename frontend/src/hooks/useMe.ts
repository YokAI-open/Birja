import { useQuery } from "@tanstack/react-query";
import { fetchMe } from "@/api/auth";

export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: ({ signal }) => fetchMe(signal),
    retry: false,
    staleTime: 60_000,
  });
}
