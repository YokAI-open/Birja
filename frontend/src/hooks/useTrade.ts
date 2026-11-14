import { useMutation, useQueryClient } from "@tanstack/react-query";
import { executeTrade, type Order } from "@/api/trades";
import { eventHistorySession } from "./useEventHistory";

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
    onMutate: () => eventHistorySession(queryClient),
    onSuccess: async (_fill, _variables, session) => {
      const current = eventHistorySession(queryClient);
      if (current.email !== session.email || current.epoch !== session.epoch) return;
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["me"] }),
        queryClient.invalidateQueries({ queryKey: ["holding", symbol] }),
        queryClient.invalidateQueries({ queryKey: ["prices"] }),
        queryClient.invalidateQueries({ queryKey: ["portfolio"] }),
        queryClient.invalidateQueries({ queryKey: ["history"] }),
        ...(session.email === null
          ? []
          : [
              queryClient.invalidateQueries({
                queryKey: ["eventHistory", session.email, session.epoch],
              }),
            ]),
      ]);
    },
  });
}
