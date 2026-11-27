import { ApiError, guardedJsonRequest } from "./client";
import { isPortfolioId } from "./portfolios";
import { stockInstant } from "./stocks";

import {
  STOCK_ECONOMIC_FIELDS,
  STOCK_REFUSALS,
  STOCK_SCALE,
  stockBalance,
  stockEconomicValues,
  stockExact,
  stockFixed,
  stockPrice,
  stockRoundCent,
  stockShares,
  type StockEconomicValues,
  type StockFillValues,
  type StockRefusal,
  type StockTransport,
} from "./stockTrades";
import type { Side } from "./trades";

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
const EXECUTION_REASONS = [
  "available",
  "read_only",
  "permission_unavailable",
  "market_closed",
  "session_unavailable",
  "halted",
  "status_unavailable",
  "action_unavailable",
  "units_changed",
  "quote_unavailable",
  "quote_stale",
] as const;
export type CatalogExecutionReason = (typeof EXECUTION_REASONS)[number];
export type CatalogOrderRefusal =
  StockRefusal | "read_only" | "listing_changed" | "receipt_missing";

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
  read_only: boolean;
  execution_reason: CatalogExecutionReason;
};
export type CatalogTradeContext = CatalogQuoteView & {
  portfolio_id: string;
  cash: string;
  held_quantity: string;
  buy_max_quantity: string;
};
export type CatalogOrder = { listing_version: string; side: Side; quantity: string };
export type CatalogAttempt = Readonly<
  CatalogOrder & { expected_exec_price: string; idempotency_key: string; preview_token: string }
>;
type CatalogIssue = { catalog_id: string; listing_version: string };
export type CatalogPreview = StockEconomicValues &
  CatalogIssue & { valid_until: string; preview_token: string };
export type CatalogFill = StockFillValues & CatalogIssue;
export type TimedCatalogPreview = CatalogPreview & { transport: StockTransport };
export type CatalogPriceChanged<Q = CatalogPreview> = {
  code: "price_changed";
  previous_exec_price: string;
  previous_cash_delta: string;
  exec_price_change: string;
  cash_delta_change: string;
  quote: Q;
};

export const isCatalogId = isPortfolioId;

const record = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);
const exact = (value: Record<string, unknown>, keys: string[]) =>
  Object.keys(value).length === keys.length && keys.every((key) => Object.hasOwn(value, key));
const text = (value: unknown, limit: number): value is string =>
  typeof value === "string" && value.trim().length > 0 && [...value].length <= limit;
const oneOf = <T extends string>(value: unknown, choices: readonly T[]): value is T =>
  typeof value === "string" && choices.some((choice) => choice === value);

export function isCanonicalUtcTimestamp(value: unknown): value is string {
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
const nullableTime = (value: unknown): value is string | null =>
  value === null || isCanonicalUtcTimestamp(value);

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
    isCanonicalUtcTimestamp(value.published_at) &&
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

function isPrice(value: unknown, nextOpen: string | null): value is CatalogPrice {
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
    !isCanonicalUtcTimestamp(value.event_at) ||
    !isCanonicalUtcTimestamp(value.collected_at) ||
    !isCanonicalUtcTimestamp(value.valid_until)
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
    (nextOpen !== null ? cutoff > stockInstant(nextOpen) : cutoff - collected > 600_000_000_000n)
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
    typeof value.read_only === "boolean" &&
    oneOf(value.execution_reason, EXECUTION_REASONS) &&
    value.read_only === (value.execution_reason !== "available") &&
    (value.read_only || (value.listing.state === "active" && value.session.state === "open")) &&
    (value.quote === null
      ? value.reason !== "ready"
      : isPrice(
          value.quote,
          value.session.state === "closed" ? value.session.next_open_at : null,
        ) &&
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

const QUOTE_VIEW_FIELDS = "listing session quote reason read_only execution_reason";

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
    !stockExact(value, QUOTE_VIEW_FIELDS) ||
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
    !stockExact(value, QUOTE_VIEW_FIELDS + " portfolio_id cash held_quantity buy_max_quantity") ||
    !isQuoteView(value) ||
    value.listing.catalog_id !== catalogId ||
    value.portfolio_id !== portfolioId ||
    typeof value.cash !== "string" ||
    stockBalance(value.cash) === null ||
    typeof value.held_quantity !== "string" ||
    stockShares(value.held_quantity) === null ||
    typeof value.buy_max_quantity !== "string" ||
    stockShares(value.buy_max_quantity) === null ||
    (value.read_only && stockShares(value.buy_max_quantity) !== 0n)
  )
    throw new Error("Unexpected portfolio stock catalog context");
  return {
    listing: value.listing,
    quote: value.quote,
    session: value.session,
    reason: value.reason,
    portfolio_id: portfolioId,
    read_only: value.read_only,
    execution_reason: value.execution_reason,
    cash: value.cash,
    held_quantity: value.held_quantity,
    buy_max_quantity: value.buy_max_quantity,
  };
}

const ORDER_FIELDS = "listing_version side quantity";
const ECONOMIC_FIELDS = STOCK_ECONOMIC_FIELDS + " catalog_id listing_version";
const previewToken = (value: unknown): value is string =>
  typeof value === "string" &&
  /^[1-9][0-9]{0,18}\.(?:0|[1-9][0-9]{0,15})\.[a-f0-9]{64}$/.test(value);

export function isCatalogOrder(v: unknown): v is CatalogOrder {
  return (
    record(v) &&
    stockExact(v, ORDER_FIELDS) &&
    isCatalogId(v.listing_version) &&
    oneOf(v.side, ["buy", "sell"]) &&
    typeof v.quantity === "string" &&
    /^[1-9][0-9]{0,11}$/.test(v.quantity)
  );
}

function isCatalogAttempt(v: unknown): v is CatalogAttempt {
  return (
    record(v) &&
    stockExact(v, ORDER_FIELDS + " expected_exec_price idempotency_key preview_token") &&
    isCatalogOrder({ listing_version: v.listing_version, side: v.side, quantity: v.quantity }) &&
    stockPrice(v.expected_exec_price) !== null &&
    previewToken(v.preview_token) &&
    typeof v.idempotency_key === "string" &&
    /^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/i.test(v.idempotency_key)
  );
}

function catalogEconomics(
  v: Record<string, unknown>,
): v is Record<string, unknown> & StockEconomicValues & CatalogIssue {
  return (
    stockEconomicValues(v) &&
    isCatalogId(v.catalog_id) &&
    isCatalogId(v.listing_version) &&
    typeof v.symbol === "string" &&
    /^[A-Z0-9][A-Z0-9.$^+/=-]{0,13}$/.test(v.symbol)
  );
}

export function isCatalogPreview(v: unknown): v is CatalogPreview {
  if (
    !record(v) ||
    !stockExact(v, ECONOMIC_FIELDS + " valid_until preview_token") ||
    !catalogEconomics(v) ||
    !isCanonicalUtcTimestamp(v.valid_until) ||
    !previewToken(v.preview_token)
  )
    return false;
  const deadline = stockInstant(v.valid_until);
  return (
    deadline > stockInstant(v.observed_at) &&
    deadline <= stockInstant(v.session_closes_at) &&
    deadline <= stockInstant(v.event_at) + 120_000_000_000n
  );
}

function isCatalogFill(v: unknown): v is CatalogFill {
  if (
    !record(v) ||
    !stockExact(v, ECONOMIC_FIELDS + " schema_version trade_id executed_at") ||
    !catalogEconomics(v) ||
    v.schema_version !== 1 ||
    !isCatalogId(v.trade_id) ||
    !isCanonicalUtcTimestamp(v.executed_at)
  )
    return false;
  const filled = stockInstant(v.executed_at);
  return (
    stockInstant(v.observed_at) <= filled &&
    filled < stockInstant(v.session_closes_at) &&
    filled - stockInstant(v.event_at) < 120_000_000_000n
  );
}

function isCatalogReplacement(v: unknown): v is CatalogPriceChanged {
  if (
    !record(v) ||
    !stockExact(
      v,
      "code previous_exec_price previous_cash_delta exec_price_change cash_delta_change quote",
    ) ||
    v.code !== "price_changed" ||
    !isCatalogPreview(v.quote)
  )
    return false;
  const price = stockPrice(v.previous_exec_price);
  if (price === null || price === stockPrice(v.quote.exec_price)) return false;
  const previousCash =
    stockRoundCent(price * (stockShares(v.quote.quantity, true)! / STOCK_SCALE)) *
    (v.quote.side === "buy" ? -1n : 1n);
  return (
    stockBalance(v.previous_cash_delta, true) === previousCash &&
    stockFixed(v.exec_price_change, true) === stockPrice(v.quote.exec_price)! - price &&
    stockBalance(v.cash_delta_change, true) ===
      stockBalance(v.quote.cash_delta, true)! - previousCash
  );
}

export function withCatalogTiming<T extends { observed_at: string }>(
  value: T,
  started: number,
): T & { transport: StockTransport } {
  const received = performance.now();
  return {
    ...value,
    transport: {
      started_at: started,
      received_at: received,
      round_trip_ms: Math.max(0, received - started),
    },
  };
}

function matchesOrder(
  value: StockEconomicValues & CatalogIssue,
  portfolioId: string,
  catalogId: string,
  order: CatalogOrder,
) {
  return (
    value.portfolio_id === portfolioId &&
    value.catalog_id === catalogId &&
    value.listing_version === order.listing_version &&
    value.side === order.side &&
    stockShares(value.quantity, true) === stockFixed(order.quantity)
  );
}

function orderPath(
  portfolioId: string,
  catalogId: string,
  action: "preview" | "confirm" | "receipt",
) {
  if (!isPortfolioId(portfolioId) || !isCatalogId(catalogId))
    throw new Error("Unexpected order target");
  return `/api/v2/portfolios/${portfolioId}/stock-catalog/${catalogId}/${action}`;
}

export async function previewCatalogOrder(
  portfolioId: string,
  catalogId: string,
  order: CatalogOrder,
  signal: AbortSignal,
  isCurrent: () => boolean,
): Promise<TimedCatalogPreview> {
  if (!isCatalogOrder(order)) throw new Error("Unexpected stock order");
  const started = performance.now();
  const value = await guardedJsonRequest(
    orderPath(portfolioId, catalogId, "preview"),
    { method: "POST", body: JSON.stringify(order), signal, cache: "no-store" },
    isCurrent,
  );
  if (!isCatalogPreview(value) || !matchesOrder(value, portfolioId, catalogId, order))
    throw new Error("Unexpected stock preview");
  return withCatalogTiming(value, started);
}

export async function resolveCatalogOrder(
  portfolioId: string,
  catalogId: string,
  order: CatalogAttempt,
  action: "confirm" | "receipt",
  isCurrent: () => boolean,
): Promise<CatalogFill> {
  if (!isCatalogAttempt(order)) throw new Error("Unexpected stock attempt");
  const value = await guardedJsonRequest(
    orderPath(portfolioId, catalogId, action),
    { method: "POST", body: JSON.stringify(order), cache: "no-store" },
    isCurrent,
    action === "confirm"
      ? {
          successStatuses: [200, 201],
          validateErrorDetail: (status, detail) =>
            status === 409 &&
            isCatalogReplacement(detail) &&
            matchesOrder(detail.quote, portfolioId, catalogId, order) &&
            stockPrice(detail.previous_exec_price) === stockPrice(order.expected_exec_price),
        }
      : { successStatuses: [200] },
  );
  if (
    !isCatalogFill(value) ||
    !matchesOrder(value, portfolioId, catalogId, order) ||
    stockPrice(value.exec_price) !== stockPrice(order.expected_exec_price)
  )
    throw new Error("Unexpected stock receipt");
  return value;
}

export function catalogReplacement(
  error: unknown,
  started: number,
): CatalogPriceChanged<TimedCatalogPreview> | null {
  if (!(error instanceof ApiError) || error.status !== 409 || !isCatalogReplacement(error.detail))
    return null;
  return { ...error.detail, quote: withCatalogTiming(error.detail.quote, started) };
}

const INPUT_REFUSALS = [
  "invalid_quantity",
  "insufficient_cash",
  "insufficient_holding",
  "numeric_range",
];
export function catalogRefusal(error: unknown): CatalogOrderRefusal | null {
  if (
    !(error instanceof ApiError) ||
    !oneOf(error.code, [
      ...STOCK_REFUSALS,
      "read_only",
      "listing_changed",
      "receipt_missing",
    ] as const)
  )
    return null;
  const status = INPUT_REFUSALS.includes(error.code) ? 422 : 409;
  return error.status === status ? error.code : null;
}
