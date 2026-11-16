import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import { executeTrade, type Fill, type Order, type TradeAttempt } from "@/api/trades";
import type { PortfolioTarget } from "./usePortfolioTarget";
import { financialScope, revokePortfolioTarget } from "./useQuote";

export type TradeVariables = { order: Order; expectedMid: string; idempotencyKey: string };
type State = {
  phase: "idle" | "submitting" | "unknown" | "filled" | "refused";
  attempt: TradeAttempt | null;
  fill?: Fill;
  error: Error | null;
};
const empty = (): State => ({ phase: "idle", attempt: null, error: null });
const terminal = new Set([
  "price_changed",
  "insufficient_cash",
  "insufficient_holding",
  "price_stale",
  "price_unavailable",
  "invalid_order",
  "idempotency_conflict",
  "unknown_coin",
]);
function sameAttempt(a: TradeAttempt, b: TradeAttempt) {
  return (
    a.portfolio_id === b.portfolio_id &&
    a.idempotency_key === b.idempotency_key &&
    a.expected_mid === b.expected_mid &&
    a.order.symbol === b.order.symbol &&
    a.order.side === b.order.side &&
    a.order.amount_usd === b.order.amount_usd &&
    a.order.quantity === b.order.quantity
  );
}

export function useTrade(target: PortfolioTarget | null, symbol: string) {
  const client = useQueryClient();
  const scope = financialScope(client, target);
  const key = ["cryptoTradeState", scope.owner, scope.portfolioId, scope.epoch, symbol] as const;
  const stateQuery = useQuery({
    queryKey: key,
    queryFn: async () => empty(),
    enabled: false,
    initialData: empty,
    gcTime: Infinity,
  });
  const currentState = () => client.getQueryData<State>(key) ?? empty();
  const mutation = useMutation<Fill, Error, TradeVariables>({
    mutationKey: ["cryptoTrade", scope.owner, scope.portfolioId, scope.epoch, symbol],
    retry: false,
    gcTime: 0,
    mutationFn: async ({ order, expectedMid, idempotencyKey }) => {
      if (target === null || !scope.current() || order.symbol !== symbol)
        throw new Error("Portfolio target changed");
      const attempt = Object.freeze({
        portfolio_id: target.portfolioId,
        order: Object.freeze({ ...order }),
        expected_mid: expectedMid,
        idempotency_key: idempotencyKey,
      });
      const state = currentState();
      if (
        state.phase === "submitting" ||
        state.phase === "filled" ||
        (state.attempt !== null && !sameAttempt(state.attempt, attempt))
      )
        throw new Error("Original trade attempt must be resolved");
      const owner = client.getQueryCache().find({ queryKey: key, exact: true });
      const owns = () =>
        client.getQueryCache().find({ queryKey: key, exact: true }) === owner &&
        client.getQueryData<{ email: string } | null>(["me"])?.email === scope.owner;
      client.setQueryData<State>(key, { phase: "submitting", attempt, error: null });
      try {
        const fill = await executeTrade(
          attempt.portfolio_id,
          attempt.order,
          attempt.expected_mid,
          attempt.idempotency_key,
        );
        if (!scope.current()) throw new Error("Portfolio target changed");
        client.setQueryData<State>(key, { phase: "filled", attempt: null, fill, error: null });
        await Promise.all([
          ...["holding", "quote", "portfolio", "history", "eventHistory", "stockContext"].map(
            (prefix) =>
              client.invalidateQueries({ queryKey: [prefix, scope.owner, scope.portfolioId] }),
          ),
          client.invalidateQueries({ queryKey: ["prices"] }),
        ]);
        if (!scope.current()) throw new Error("Portfolio target changed");
        return fill;
      } catch (error) {
        const failure = error instanceof Error ? error : new Error("Unknown trade result");
        if (owns()) {
          const refused =
            scope.current() && error instanceof ApiError && terminal.has(error.code ?? "");
          client.setQueryData<State>(key, {
            phase: refused ? "refused" : "unknown",
            attempt: refused ? null : attempt,
            error: failure,
          });
        }
        if (scope.current() && error instanceof ApiError && error.code === "portfolio_unavailable")
          revokePortfolioTarget(client, target);
        if (scope.current() && error instanceof ApiError && error.status === 401)
          client.setQueryData(["me"], null);
        throw failure;
      }
    },
  });
  type Options = Parameters<typeof mutation.mutate>[1];
  const optionsFor = (options: Options): Options =>
    options && {
      onSuccess: (...args) => {
        if (scope.current()) options.onSuccess?.(...args);
      },
      onError: (...args) => {
        if (scope.current()) options.onError?.(...args);
      },
      onSettled: (...args) => {
        if (scope.current()) options.onSettled?.(...args);
      },
    };
  const visible = scope.current() ? stateQuery.data : empty();
  return {
    ...mutation,
    data: visible.fill,
    error: visible.error,
    isPending: visible.phase === "submitting",
    isSuccess: visible.phase === "filled",
    isError: visible.phase === "unknown" || visible.phase === "refused",
    isIdle: visible.phase === "idle",
    status:
      visible.phase === "submitting"
        ? ("pending" as const)
        : visible.phase === "filled"
          ? ("success" as const)
          : visible.error
            ? ("error" as const)
            : ("idle" as const),
    variables: visible.attempt
      ? {
          order: visible.attempt.order,
          expectedMid: visible.attempt.expected_mid,
          idempotencyKey: visible.attempt.idempotency_key,
        }
      : undefined,
    failureReason: visible.error,
    attempt: visible.attempt,
    outcomeUnknown: visible.phase === "unknown",
    mutate: (variables: TradeVariables, options?: Options) =>
      mutation.mutate(variables, optionsFor(options)),
    mutateAsync: (variables: TradeVariables, options?: Options) =>
      mutation.mutateAsync(variables, optionsFor(options)),
    reset: () => {
      if (!scope.current() || ["submitting", "unknown"].includes(currentState().phase)) return;
      client.setQueryData(key, empty());
      mutation.reset();
    },
  };
}
