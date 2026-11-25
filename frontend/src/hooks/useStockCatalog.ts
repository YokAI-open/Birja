import { useCallback, useEffect, useRef, useSyncExternalStore } from "react";
import { useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import {
  fetchCatalogTradeContext,
  isCatalogId,
  requestCatalogPrice,
  searchStockCatalog,
  type CatalogQuoteView,
  type StockCatalogItem,
} from "@/api/stockCatalog";
import { eventHistorySession } from "./useEventHistory";
import type { PortfolioTarget } from "./usePortfolioTarget";
import { financialScope, revokePortfolioTarget } from "./useQuote";

function useCatalogSession(client: QueryClient) {
  const { email } = eventHistorySession(client);
  const epoch = useSyncExternalStore(
    useCallback(
      (changed) =>
        client.getQueryCache().subscribe(({ query }) => {
          if (query.queryKey.length === 1 && query.queryKey[0] === "me") changed();
        }),
      [client],
    ),
    () => eventHistorySession(client).epoch,
  );
  return {
    email,
    epoch,
    current: () => {
      const current = eventHistorySession(client);
      return email !== null && current.email === email && current.epoch === epoch;
    },
  };
}

export function useStockCatalogSearch(search: string | null) {
  const client = useQueryClient();
  const session = useCatalogSession(client);
  const query = useQuery({
    queryKey: ["stockCatalogSearch", session.email, session.epoch, search],
    enabled: search !== null && session.current(),
    queryFn: ({ signal }) => {
      if (search === null) throw new Error("No stock search");
      return searchStockCatalog(search, signal, session.current);
    },
    retry: false,
    gcTime: 0,
    staleTime: 0,
  });
  const transientFailure =
    query.error instanceof TypeError ||
    (query.error instanceof ApiError && (query.error.status === 429 || query.error.status >= 500));
  return {
    ...query,
    data: session.current() && (!query.isError || transientFailure) ? query.data : undefined,
    enabled: session.current(),
  };
}

export function useSelectedCatalogPrice(listing: StockCatalogItem | null, now: number) {
  const client = useQueryClient();
  const session = useCatalogSession(client);
  const enabled = listing?.state === "active" && session.current();
  const query = useQuery({
    queryKey: [
      "stockCatalogPrice",
      session.email,
      session.epoch,
      listing?.catalog_id ?? null,
      listing?.listing_version ?? null,
    ],
    enabled,
    queryFn: ({ signal }) => {
      if (listing === null) throw new Error("No selected stock listing");
      return requestCatalogPrice(listing, signal, session.current);
    },
    retry: false,
    gcTime: 0,
    refetchOnMount: false,
    refetchOnReconnect: false,
    refetchOnWindowFocus: false,
    staleTime: Infinity,
  });
  const schedule = query.data?.session;
  const nextOpen = schedule?.state === "unknown" ? null : (schedule?.next_open_at ?? null);
  const boundaryAt =
    nextOpen && now >= Date.parse(nextOpen)
      ? nextOpen
      : schedule?.state === "open"
        ? schedule.closes_at
        : null;
  const boundary = JSON.stringify([
    session.epoch,
    listing?.catalog_id,
    listing?.listing_version,
    boundaryAt,
  ]);
  const boundaryRefresh = useRef<{
    key: string;
    retried: boolean;
    retryAt: number | null;
  } | null>(null);
  const { isFetching, refetch } = query;
  useEffect(() => {
    if (!enabled || isFetching || !schedule || !boundaryAt || now < Date.parse(boundaryAt)) return;
    const prior = boundaryRefresh.current;
    const sameBoundary = prior?.key === boundary;
    if (sameBoundary && (prior.retried || prior.retryAt === null || now < prior.retryAt)) return;
    const attempt = { key: boundary, retried: sameBoundary, retryAt: null as number | null };
    boundaryRefresh.current = attempt;
    void refetch().then(({ data, isError }) => {
      const next = data?.session;
      const unchanged =
        next?.state === schedule.state &&
        next.opens_at === schedule.opens_at &&
        next.closes_at === schedule.closes_at;
      if (isError || unchanged) attempt.retryAt = Date.now() + 2_000;
    });
  }, [boundary, boundaryAt, enabled, isFetching, now, refetch, schedule]);
  return { ...query, data: session.current() && !query.isError ? query.data : undefined };
}

export function useCatalogTradeContext(target: PortfolioTarget | null, catalogId: string) {
  const client = useQueryClient();
  const scope = financialScope(client, target);
  const queryKey = [
    "stockCatalogTradeContext",
    scope.owner,
    scope.epoch,
    scope.portfolioId,
    target?.epoch.session ?? null,
    catalogId,
  ] as const;
  const query = useQuery({
    queryKey,
    enabled: isCatalogId(catalogId) && scope.current(),
    queryFn: async ({ signal }) => {
      if (!target || !scope.current()) throw new Error("Portfolio target changed");
      try {
        return await fetchCatalogTradeContext(target.portfolioId, catalogId, signal, scope.current);
      } catch (error) {
        if (scope.current() && error instanceof ApiError) {
          if (error.code === "portfolio_unavailable") revokePortfolioTarget(client, target);
          if (error.status === 401) client.setQueryData(["me"], null);
        }
        throw error;
      }
    },
    retry: false,
    gcTime: 0,
    staleTime: 0,
    refetchInterval: (current) => {
      const view = current.state.data;
      if (!view || current.state.status !== "success" || view.listing.state !== "active")
        return false;
      if (view.session.state === "closed") {
        return view.session.next_open_at ? 60_000 : false;
      }
      return 15_000;
    },
  });
  return { ...query, queryKey, data: scope.current() && !query.isError ? query.data : undefined };
}

export function useCatalogOrderQuoteDemand(
  target: PortfolioTarget,
  view: CatalogQuoteView | undefined,
  now: number,
) {
  const scope = financialScope(useQueryClient(), target);
  const listing = view?.listing;
  return useQuery({
    queryKey: [
      "catalogOrderQuote",
      scope.owner,
      scope.epoch,
      target.portfolioId,
      listing?.catalog_id,
      listing?.listing_version,
    ],
    enabled:
      scope.current() &&
      view?.listing.state === "active" &&
      view.session.state === "open" &&
      view.session.opens_at !== null &&
      view.session.closes_at !== null &&
      Date.parse(view.session.opens_at) <= now &&
      now < Date.parse(view.session.closes_at) &&
      [
        "status_unavailable",
        "action_unavailable",
        "quote_unavailable",
        "quote_stale",
        "units_changed",
      ].includes(view.execution_reason),
    queryFn: ({ signal }) => {
      if (!listing) throw new Error("No selected stock listing");
      return requestCatalogPrice(listing, signal, scope.current);
    },
    retry: false,
    refetchOnMount: false,
    refetchOnReconnect: false,
    refetchOnWindowFocus: false,
    gcTime: 0,
    staleTime: 0,
    refetchInterval: 15_000,
  });
}

const PRICE_MESSAGES: Record<CatalogQuoteView["reason"], string | null> = {
  ready: null,
  missing_permission: "Stock prices haven’t been approved for display.",
  mapping_review: "This stock’s reference data is under review.",
  identity_review: "This listing is under review.",
  market_closed: null,
  session_unavailable: "This stock’s market hours haven’t been confirmed.",
  quote_unavailable: "Waiting for a verified IEX quote.",
  price_disabled: "Stock prices are paused.",
  throttled: "Stock price requests are temporarily limited.",
  source_error: "Couldn’t load this stock price.",
  failed_check: "The stock price could not be verified.",
  queue_full: "Stock price requests are temporarily limited.",
};

export function catalogDisplay(view: CatalogQuoteView, now: number) {
  const { listing, session, reason } = view;
  if (listing.state === "retired")
    return {
      quote: null,
      closed: false,
      message: "This listing has been retired.",
      retryable: false,
    };
  if (listing.state === "review")
    return {
      quote: null,
      closed: false,
      message: PRICE_MESSAGES.identity_review,
      retryable: false,
    };

  const nextOpen = session.next_open_at === null ? null : Date.parse(session.next_open_at);
  const closed =
    (session.state === "closed" && (nextOpen === null || now < nextOpen)) ||
    (session.state === "open" &&
      session.closes_at !== null &&
      now >= Date.parse(session.closes_at) &&
      nextOpen !== null &&
      now < nextOpen);
  const open =
    session.state === "open" &&
    session.opens_at !== null &&
    session.closes_at !== null &&
    Date.parse(session.opens_at) <= now &&
    now < Date.parse(session.closes_at);
  const quote =
    view.quote &&
    now < Date.parse(view.quote.valid_until) &&
    (closed || (open && now - Date.parse(view.quote.event_at) < 120_000))
      ? view.quote
      : null;

  if (closed || quote) return { quote, closed, message: null, retryable: false };
  if ((session.state === "open" && !open) || session.state === "closed")
    return {
      quote: null,
      closed: false,
      message: "Refresh this stock’s market hours.",
      retryable: true,
    };
  return {
    quote: null,
    closed: false,
    message: reason === "ready" ? "This quote is out of date." : PRICE_MESSAGES[reason],
    retryable: [
      "ready",
      "throttled",
      "source_error",
      "failed_check",
      "quote_unavailable",
      "queue_full",
    ].includes(reason),
  };
}
