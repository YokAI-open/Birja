import { useMutation, useQueryClient } from "@tanstack/react-query";
import { executeTrade, type Order } from "@/api/trades";

export type TradeVariables = {
  order: Order;
  expectedMid: string;
  idempotencyKey: string;
};

export function useTrade(symbol: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ order, expectedMid, idempotencyKey }: TradeVariables) =>
      executeTrade(order, expectedMid, idempotencyKey),
    retry: false,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["me"] }),
        queryClient.invalidateQueries({ queryKey: ["holding", symbol] }),
        queryClient.invalidateQueries({ queryKey: ["prices"] }),
        queryClient.invalidateQueries({ queryKey: ["portfolio"] }),
        queryClient.invalidateQueries({ queryKey: ["history"] }),
      ]);
    },
  });
}
