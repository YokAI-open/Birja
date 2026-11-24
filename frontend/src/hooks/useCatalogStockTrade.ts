import { useEffect, useLayoutEffect, useMemo, useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import {
  catalogRefusal,
  catalogReplacement,
  isCatalogOrder,
  previewCatalogOrder,
  resolveCatalogOrder,
  type CatalogAttempt,
  type CatalogFill,
  type CatalogOrder,
  type CatalogOrderRefusal,
  type CatalogPriceChanged,
  type CatalogTradeContext,
  type TimedCatalogPreview,
} from "@/api/stockCatalog";
import { stockFixed, stockShares } from "@/api/stockTrades";
import type { Side } from "@/api/trades";
import { eventHistorySession } from "./useEventHistory";
import type { PortfolioTarget } from "./usePortfolioTarget";
import { financialScope, revokePortfolioTarget } from "./useQuote";
import { useCatalogOrderQuoteDemand, useCatalogTradeContext } from "./useStockCatalog";
import { stockTradeAuth, stockUpper } from "./useStockTrade";

type CatalogTradeState = {
  phase: "draft" | "loading_preview" | "preview" | "submitting" | "unknown" | "filled";
  side: Side;
  quantity: string;
  quote: TimedCatalogPreview | null;
  replacement: CatalogPriceChanged<TimedCatalogPreview> | null;
  attempt: CatalogAttempt | null;
  fill: CatalogFill | null;
  error: CatalogOrderRefusal | "unknown" | null;
};

const draft = (): CatalogTradeState => ({
  phase: "draft",
  side: "buy",
  quantity: "",
  quote: null,
  replacement: null,
  attempt: null,
  fill: null,
  error: null,
});

function locked(phase: CatalogTradeState["phase"]) {
  return phase === "submitting" || phase === "unknown" || phase === "filled";
}

function executable(context: CatalogTradeContext | undefined, now: number) {
  const session = context?.session;
  return (
    context?.listing.state === "active" &&
    !context.read_only &&
    context.execution_reason === "available" &&
    session?.state === "open" &&
    session.opens_at !== null &&
    session.closes_at !== null &&
    Date.parse(session.opens_at) <= now &&
    now < Date.parse(session.closes_at)
  );
}

function matchingQuote(
  quote: TimedCatalogPreview,
  context: CatalogTradeContext | undefined,
  now: number,
) {
  return (
    context !== undefined &&
    executable(context, now) &&
    quote.catalog_id === context.listing.catalog_id &&
    quote.listing_version === context.listing.listing_version &&
    quote.portfolio_id === context.portfolio_id &&
    stockFixed(quote.cash_before) === stockFixed(context.cash) &&
    stockShares(quote.held_before) === stockShares(context.held_quantity) &&
    Math.max(now, stockUpper(quote)) < Date.parse(quote.valid_until)
  );
}

export function useCatalogStockTrade(target: PortfolioTarget, catalogId: string, now: number) {
  const client = useQueryClient();
  const scope = useMemo(() => financialScope(client, target), [client, target]);
  stockTradeAuth(client);
  const key = useMemo(
    () => ["stockTradeState", target.owner, target.portfolioId, scope.epoch, "catalog", catalogId],
    [target.owner, target.portfolioId, scope.epoch, catalogId],
  );
  const stateQuery = useQuery({
    queryKey: key,
    queryFn: async () => draft(),
    initialData: draft,
    enabled: false,
    gcTime: Infinity,
  });
  const contextQuery = useCatalogTradeContext(target, catalogId);
  const { data: context, refetch: refreshContext, queryKey: contextKey } = contextQuery;
  const demand = useCatalogOrderQuoteDemand(target, context, now);
  const demandSettled = demand.dataUpdatedAt;
  useEffect(() => {
    if (demandSettled && scope.current()) void refreshContext();
  }, [demandSettled, refreshContext, scope]);

  const mounted = useRef(false);
  const previewController = useRef<AbortController | null>(null);
  useLayoutEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      previewController.current?.abort();
      const captured = client.getQueryData<CatalogTradeState>(key);
      if (captured?.phase === "preview" || captured?.phase === "loading_preview")
        client.setQueryData(key, { ...captured, phase: "draft", quote: null, replacement: null });
    };
  }, [client, key]);

  const current = () => mounted.current && scope.current();
  const state = scope.current() ? stateQuery.data : draft();
  const visibleQuote = state.quote && matchingQuote(state.quote, context, now) ? state.quote : null;
  useEffect(() => {
    if (state.phase !== "preview" || visibleQuote !== null || !scope.current()) return;
    client.setQueryData<CatalogTradeState>(key, (saved) =>
      saved?.phase === "preview" && saved.quote === state.quote
        ? { ...saved, phase: "draft", quote: null, replacement: null }
        : saved,
    );
  }, [client, key, scope, state.phase, state.quote, visibleQuote]);

  const getState = () => client.getQueryData<CatalogTradeState>(key) ?? draft();
  const getContext = () =>
    current() && client.getQueryState(contextKey)?.status === "success"
      ? client.getQueryData<CatalogTradeContext>(contextKey)
      : undefined;
  const setState = (update: (value: CatalogTradeState) => CatalogTradeState) => {
    if (current()) client.setQueryData<CatalogTradeState>(key, (saved) => update(saved ?? draft()));
  };
  const previewMutation = useMutation({
    mutationKey: [...key, "preview"],
    mutationFn: ({ order, signal }: { order: CatalogOrder; signal: AbortSignal }) =>
      previewCatalogOrder(target.portfolioId, catalogId, order, signal, current),
    retry: false,
    gcTime: 0,
  });
  const resolutionMutation = useMutation({
    mutationKey: [...key, "resolution"],
    mutationFn: ({
      attempt,
      action,
      isCurrent,
    }: {
      attempt: CatalogAttempt;
      action: "confirm" | "receipt";
      isCurrent: () => boolean;
    }) => resolveCatalogOrder(target.portfolioId, catalogId, attempt, action, isCurrent),
    retry: false,
    gcTime: 0,
  });

  const edit = (changes: Partial<Pick<CatalogTradeState, "side" | "quantity">>) => {
    if (!current() || locked(getState().phase)) return;
    previewController.current?.abort();
    setState((old) => ({ ...draft(), side: old.side, quantity: old.quantity, ...changes }));
  };
  const handleOwnershipRefusal = (error: unknown) => {
    if (!(error instanceof ApiError) || !current()) return false;
    if (error.status === 401) {
      client.setQueryData(["me"], null);
      return true;
    }
    if (error.status === 404 && error.code === "portfolio_unavailable") {
      revokePortfolioTarget(client, target);
      return true;
    }
    return false;
  };

  const preview = async () => {
    const { phase, side, quantity } = getState();
    const live = getContext();
    const order = { listing_version: live?.listing.listing_version, side, quantity };
    if (
      locked(phase) ||
      phase === "loading_preview" ||
      !executable(live, Date.now()) ||
      !isCatalogOrder(order)
    )
      return;
    previewController.current?.abort();
    const controller = new AbortController();
    previewController.current = controller;
    setState((old) => ({
      ...old,
      phase: "loading_preview",
      quote: null,
      error: null,
      replacement: null,
    }));
    try {
      const quote = await previewMutation.mutateAsync({ order, signal: controller.signal });
      if (controller.signal.aborted || !current()) return;
      const accepted = matchingQuote(quote, getContext(), Date.now());
      setState((old) => ({
        ...old,
        phase: accepted ? "preview" : "draft",
        quote: accepted ? quote : null,
        error: accepted ? null : "quote_stale",
      }));
    } catch (error) {
      if (controller.signal.aborted || !current() || handleOwnershipRefusal(error)) return;
      const refused = catalogRefusal(error);
      setState((old) => ({ ...old, phase: "draft", error: refused ?? "unknown" }));
      if (refused === "listing_changed") void refreshContext();
    } finally {
      previewMutation.reset();
    }
  };

  const resolve = async (attempt: CatalogAttempt, action: "confirm" | "receipt") => {
    if (!current() || (target.isOriginalCurrent && !target.isOriginalCurrent())) return;
    const entry = client.getQueryCache().find({ queryKey: key, exact: true });
    setState((old) => ({
      ...old,
      phase: "submitting",
      quote: null,
      replacement: null,
      attempt,
      error: null,
    }));
    const sameAttempt = () => {
      const session = eventHistorySession(client);
      return (
        session.email === target.owner &&
        session.epoch === scope.epoch &&
        client.getQueryCache().find({ queryKey: key, exact: true }) === entry &&
        getState().attempt?.idempotency_key === attempt.idempotency_key
      );
    };
    const ownedAttempt = () => current() && sameAttempt() && (target.isOriginalCurrent?.() ?? true);
    const preserveUnknown = () => {
      if (sameAttempt())
        client.setQueryData<CatalogTradeState>(key, (saved) =>
          saved ? { ...saved, phase: "unknown", error: "unknown" } : saved,
        );
    };
    const started = performance.now();
    try {
      const fill = await resolutionMutation.mutateAsync({
        attempt,
        action,
        isCurrent: ownedAttempt,
      });
      if (!ownedAttempt()) {
        preserveUnknown();
        return;
      }
      setState((old) => ({ ...old, phase: "filled", attempt: null, fill }));
      void Promise.all([
        client.invalidateQueries({
          queryKey: ["stockCatalogTradeContext", target.owner, scope.epoch, target.portfolioId],
        }),
        client.invalidateQueries({ queryKey: ["portfolioOverview", target.owner, scope.epoch] }),
        ...["holding", "quote", "stockContext", "portfolio", "history", "eventHistory"].map(
          (prefix) =>
            client.invalidateQueries({ queryKey: [prefix, target.owner, target.portfolioId] }),
        ),
      ]);
    } catch (error) {
      if (!ownedAttempt() || handleOwnershipRefusal(error)) {
        preserveUnknown();
        return;
      }
      const refused = catalogRefusal(error);
      if (action === "receipt") {
        if (refused === "receipt_missing") {
          setState((old) => ({ ...old, phase: "draft", error: refused, attempt: null }));
          void refreshContext();
        } else {
          preserveUnknown();
        }
        return;
      }
      const replacement = catalogReplacement(error, started);
      if (replacement && matchingQuote(replacement.quote, getContext(), Date.now())) {
        setState((old) => ({
          ...old,
          phase: "preview",
          quote: replacement.quote,
          replacement,
          attempt: null,
        }));
      } else if (replacement || (refused && refused !== "receipt_unavailable")) {
        setState((old) => ({
          ...old,
          phase: "draft",
          error: refused ?? "quote_stale",
          attempt: null,
        }));
        void refreshContext();
      } else preserveUnknown();
    } finally {
      resolutionMutation.reset();
    }
  };

  const confirm = async () => {
    const { phase, quote, side, quantity } = getState();
    if (phase !== "preview" || !quote || !matchingQuote(quote, getContext(), Date.now())) return;
    await resolve(
      Object.freeze({
        listing_version: quote.listing_version,
        side,
        quantity,
        expected_exec_price: quote.exec_price,
        idempotency_key: crypto.randomUUID(),
        preview_token: quote.preview_token,
      }),
      "confirm",
    );
  };
  return {
    ...state,
    context,
    contextLoading: contextQuery.isPending,
    contextError: contextQuery.error,
    quote: visibleQuote,
    replacement: visibleQuote ? state.replacement : null,
    canConfirm: visibleQuote !== null && state.phase === "preview",
    canPreview:
      executable(context, now) &&
      !locked(state.phase) &&
      state.phase !== "loading_preview" &&
      isCatalogOrder({
        listing_version: context?.listing.listing_version,
        side: state.side,
        quantity: state.quantity,
      }),
    preview,
    confirm,
    refreshContext,
    checkResult: () => {
      const saved = getState();
      if (saved.phase === "unknown" && saved.attempt) void resolve(saved.attempt, "receipt");
    },
    setQuantity: (quantity: string) => edit({ quantity }),
    setSide: (side: Side) => edit({ side }),
    useShortcut: () => {
      const live = getContext();
      if (!executable(live, Date.now()) || !live) return;
      const quantity = (
        getState().side === "buy" ? live.buy_max_quantity : live.held_quantity
      ).split(".")[0];
      if (/^[1-9][0-9]{0,11}$/.test(quantity)) edit({ quantity });
    },
    tradeAgain: () => {
      if (getState().phase === "filled") setState(draft);
    },
  };
}
