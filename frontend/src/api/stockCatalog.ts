import { guardedJsonRequest } from "./client";
import { isPortfolioId } from "./portfolios";
import { stockInstant } from "./stocks";

const LISTING_REASONS = [
  "reviewed_issue_evidence",
  "corroborated_share_class",
  "missing_without_retirement_evidence",
  "confirmed_retirement",
  "verified_ticker_reuse",
] as const;
export type StockCatalogItem = {
  catalog_id: string;
  listing_version: string;
  ticker: string;
  company_name: string;
  listing_exchange: "NYSE" | "NASDAQ";
  share_class: string | null;
  state: "active" | "review" | "retired";
  reason: (typeof LISTING_REASONS)[number];
};
export type CatalogSearchResult =
  | {
      state: "ready";
      generation_id: string;
      published_at: string;
      has_more: boolean;
      items: StockCatalogItem[];
    }
  | {
      state: "unavailable";
      generation_id: null;
      published_at: null;
      has_more: false;
      items: [];
    };

const QUOTE_REASONS = [
  "ready",
  "missing_permission",
  "mapping_review",
  "identity_review",
  "market_closed",
  "session_unavailable",
  "quote_unavailable",
  "price_disabled",
  "throttled",
  "source_error",
  "failed_check",
  "queue_full",
] as const;
export type CatalogPrice = {
  bid: string;
  ask: string;
  mid: string;
  event_at: string;
  collected_at: string;
  valid_until: string;
  currency: "USD";
  source: "alpaca";
  feed: "iex";
};
type CatalogSession = {
  state: "open" | "closed" | "unknown";
  opens_at: string | null;
  closes_at: string | null;
  next_open_at: string | null;
};
export type CatalogQuoteView = {
  listing: StockCatalogItem;
  quote: CatalogPrice | null;
  session: CatalogSession;
  reason: (typeof QUOTE_REASONS)[number];
};
export type CatalogTradeContext = CatalogQuoteView & { portfolio_id: string; read_only: true };

export const isCatalogId = isPortfolioId;

const record = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);
const exact = (value: Record<string, unknown>, keys: string[]) =>
  Object.keys(value).length === keys.length && keys.every((key) => Object.hasOwn(value, key));
const text = (value: unknown, limit: number): value is string =>
  typeof value === "string" && value.trim().length > 0 && [...value].length <= limit;
const oneOf = <T extends string>(value: unknown, choices: readonly T[]): value is T =>
  typeof value === "string" && choices.some((choice) => choice === value);

function timestamp(value: unknown): value is string {
  if (
    typeof value !== "string" ||
    !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:00)$/.test(value)
  )
    return false;
  const instant = new Date(value);
  return (
    Number.isFinite(instant.getTime()) && instant.toISOString().slice(0, 19) === value.slice(0, 19)
  );
}
const nullableTime = (value: unknown): value is string | null => value === null || timestamp(value);

function isListing(value: unknown): value is StockCatalogItem {
  return (
    record(value) &&
    exact(value, [
      "catalog_id",
      "listing_version",
      "ticker",
      "company_name",
      "listing_exchange",
      "share_class",
      "state",
      "reason",
    ]) &&
    isCatalogId(value.catalog_id) &&
    isCatalogId(value.listing_version) &&
    typeof value.ticker === "string" &&
    /^[A-Z0-9][A-Z0-9.$^+/=-]{0,13}$/.test(value.ticker) &&
    text(value.company_name, 256) &&
    oneOf(value.listing_exchange, ["NYSE", "NASDAQ"]) &&
    (value.share_class === null || text(value.share_class, 64)) &&
    oneOf(value.state, ["active", "review", "retired"]) &&
    oneOf(value.reason, LISTING_REASONS)
  );
}

function isSearchResult(value: unknown): value is CatalogSearchResult {
  if (
    !record(value) ||
    !exact(value, ["state", "generation_id", "published_at", "has_more", "items"]) ||
    !Array.isArray(value.items) ||
    value.items.length > 20 ||
    typeof value.has_more !== "boolean"
  )
    return false;
  if (value.state === "unavailable")
    return (
      value.generation_id === null &&
      value.published_at === null &&
      !value.has_more &&
      value.items.length === 0
    );
  return (
    value.state === "ready" &&
    isCatalogId(value.generation_id) &&
    timestamp(value.published_at) &&
    (!value.has_more || value.items.length === 20) &&
    value.items.every(
      (item): item is StockCatalogItem => isListing(item) && item.state === "active",
    ) &&
    new Set(value.items.map((item) => item.catalog_id)).size === value.items.length
  );
}

function priceUnits(value: unknown): bigint | null {
  if (typeof value !== "string" || !/^(?:0|[1-9]\d{0,11})(?:\.\d{1,8})?$/.test(value)) return null;
  const [whole, fraction = ""] = value.split(".");
  const units = BigInt(whole + fraction.padEnd(8, "0"));
  return units === 0n ? null : units;
}

function isPrice(value: unknown): value is CatalogPrice {
  if (
    !record(value) ||
    !exact(value, [
      "bid",
      "ask",
      "mid",
      "event_at",
      "collected_at",
      "valid_until",
      "currency",
      "source",
      "feed",
    ]) ||
    value.currency !== "USD" ||
    value.source !== "alpaca" ||
    value.feed !== "iex" ||
    !timestamp(value.event_at) ||
    !timestamp(value.collected_at) ||
    !timestamp(value.valid_until)
  )
    return false;
  const bid = priceUnits(value.bid),
    ask = priceUnits(value.ask),
    mid = priceUnits(value.mid);
  const event = stockInstant(value.event_at),
    collected = stockInstant(value.collected_at);
  const cutoff = stockInstant(value.valid_until);
  if (
    bid === null ||
    ask === null ||
    mid === null ||
    bid > ask ||
    event > collected ||
    collected - event >= 120_000_000_000n ||
    cutoff <= collected ||
    cutoff - collected > 600_000_000_000n
  )
    return false;
  const total = bid + ask;
  const half = total / 2n;
  return mid === half + (total % 2n && half % 2n ? 1n : 0n);
}

function isSession(value: unknown): value is CatalogSession {
  return (
    record(value) &&
    exact(value, ["state", "opens_at", "closes_at", "next_open_at"]) &&
    oneOf(value.state, ["open", "closed", "unknown"]) &&
    nullableTime(value.opens_at) &&
    nullableTime(value.closes_at) &&
    nullableTime(value.next_open_at) &&
    (value.opens_at === null
      ? value.closes_at === null && value.state !== "open"
      : value.closes_at !== null && stockInstant(value.opens_at) < stockInstant(value.closes_at))
  );
}

function isQuoteView(
  value: Record<string, unknown>,
): value is Record<string, unknown> & CatalogQuoteView {
  return (
    isListing(value.listing) &&
    isSession(value.session) &&
    oneOf(value.reason, QUOTE_REASONS) &&
    (value.quote === null
      ? value.reason !== "ready"
      : isPrice(value.quote) &&
        value.listing.state === "active" &&
        ((value.reason === "ready" && value.session.state === "open") ||
          (value.reason === "market_closed" && value.session.state === "closed")))
  );
}

export async function searchStockCatalog(
  search: string,
  signal: AbortSignal,
  isCurrent: () => boolean,
): Promise<CatalogSearchResult> {
  const value = await guardedJsonRequest(
    `/api/v1/stock-catalog/search?${new URLSearchParams({ q: search })}`,
    { signal },
    isCurrent,
  );
  if (!isSearchResult(value)) throw new Error("Unexpected stock catalog search");
  return value;
}

export async function requestCatalogPrice(
  listing: StockCatalogItem,
  signal: AbortSignal,
  isCurrent: () => boolean,
): Promise<CatalogQuoteView> {
  if (!isCatalogId(listing.catalog_id) || !isCatalogId(listing.listing_version))
    throw new Error("Unexpected stock catalog identity");
  const value = await guardedJsonRequest(
    `/api/v2/stock-catalog/${listing.catalog_id}/quote`,
    { method: "POST", body: JSON.stringify({ listing_version: listing.listing_version }), signal },
    isCurrent,
  );
  if (
    !record(value) ||
    !exact(value, ["listing", "session", "quote", "reason"]) ||
    !isQuoteView(value) ||
    value.listing.catalog_id !== listing.catalog_id ||
    value.listing.listing_version !== listing.listing_version
  )
    throw new Error("Unexpected selected stock quote");
  return value;
}

export async function fetchCatalogTradeContext(
  portfolioId: string,
  catalogId: string,
  signal?: AbortSignal,
  isCurrent = () => true,
): Promise<CatalogTradeContext> {
  if (!isPortfolioId(portfolioId) || !isCatalogId(catalogId))
    throw new Error("Unexpected stock catalog identity");
  const value = await guardedJsonRequest(
    `/api/v2/portfolios/${portfolioId}/stock-catalog/${catalogId}/trade-context`,
    { signal },
    isCurrent,
  );
  if (
    !record(value) ||
    !exact(value, ["listing", "session", "quote", "reason", "portfolio_id", "read_only"]) ||
    !isQuoteView(value) ||
    value.listing.catalog_id !== catalogId ||
    value.portfolio_id !== portfolioId ||
    value.read_only !== true
  )
    throw new Error("Unexpected portfolio stock catalog context");
  return {
    listing: value.listing,
    quote: value.quote,
    session: value.session,
    reason: value.reason,
    portfolio_id: portfolioId,
    read_only: true,
  };
}
