import { useCallback, useSyncExternalStore } from "react";
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

export function useSelectedCatalogPrice(listing: StockCatalogItem | null) {
  const client = useQueryClient();
  const session = useCatalogSession(client);
  const query = useQuery({
    queryKey: [
      "stockCatalogPrice",
      session.email,
      session.epoch,
      listing?.catalog_id ?? null,
      listing?.listing_version ?? null,
    ],
    enabled: listing?.state === "active" && session.current(),
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
  return { ...query, data: session.current() && !query.isError ? query.data : undefined };
}

export function useCatalogTradeContext(target: PortfolioTarget | null, catalogId: string) {
  const client = useQueryClient();
  const scope = financialScope(client, target);
  const query = useQuery({
    queryKey: [
      "stockCatalogTradeContext",
      scope.owner,
      scope.epoch,
      scope.portfolioId,
      target?.epoch.session ?? null,
      catalogId,
    ],
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
  });
  return { ...query, data: scope.current() && !query.isError ? query.data : undefined };
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
