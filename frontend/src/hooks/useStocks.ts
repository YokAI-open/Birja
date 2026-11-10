import { useQuery } from "@tanstack/react-query";
import { fetchStocks } from "@/api/stocks";

export function useStocks() {
  return useQuery({ queryKey: ["stocks"], queryFn: ({ signal }) => fetchStocks(signal), retry: false });
}
