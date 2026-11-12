import { apiFetch } from "./client";
import { stockTimestamp, stockInstant } from "./stocks";
import {
  isStockAuthority,
  stockExact,
  stockRecord,
  stockFixed,
  STOCK_REFUSALS,
  type AuthorityIdentity,
  type StockRefusal,
} from "./stockTrades";

export type StockMark = {
  mark_mode: "fresh" | "closed" | "halted" | "unavailable";
  valuation_reason: StockRefusal | "available";
  source: "alpaca" | null;
  feed: "iex" | null;
  event_at: string | null;
  collected_at: string | null;
  historical_admission_until: string | null;
  retained_until: string | null;
  valid_until: string | null;
  authority: AuthorityIdentity | null;
  units_safe: boolean;
};
export type PortfolioHolding = {
  symbol: string;
  name: string;
  is_active: boolean;
  asset_class: "crypto" | "stock";
  coin_id: string;
  provider_asset_id: string | null;
  stock_mark: StockMark | null;
  quantity: string;
  cost_basis: string;
  average_cost: string | null;
  mid: string | null;
  current_value: string | null;
  unrealized_pl: string | null;
  unrealized_pl_percent: string | null;
  allocation_percent: string | null;
  as_of: string | null;
  age_seconds: number | null;
  status: "fresh" | "aging" | "stale" | "unpriced";
};
export type Portfolio = {
  cash: string;
  starting_cash: string;
  total_value: string | null;
  total_pl: string | null;
  total_pl_percent: string | null;
  cash_allocation_percent: string | null;
  valuation_complete: boolean;
  known_value: string | null;
  unvalued_holding_count: number;
  class_values: { cash: string; stocks: string | null; crypto: string | null };
  class_allocation_percent: { cash: string | null; stocks: string | null; crypto: string | null };
  valued_at: string;
  prices_as_of: string | null;
  fresh_seconds: number;
  stale_seconds: number;
  holdings: PortfolioHolding[];
};
const text = (v: unknown): v is string => typeof v === "string" && v.length > 0 && v.length <= 1000;
const unsigned = (v: unknown): v is string => stockFixed(v) !== null;
const decimal = (v: unknown): v is string => stockFixed(v, true) !== null;
const age = (v: unknown): v is number => typeof v === "number" && Number.isSafeInteger(v) && v >= 0;
const nullable = (v: unknown, guard: (v: unknown) => boolean) => v === null || guard(v);
const allocation = (v: unknown) => {
  const n = stockFixed(v);
  return n !== null && n <= 100_000_000_000n;
};
const id = (v: unknown): v is string =>
  typeof v === "string" && /^[1-9]\d{0,18}$/.test(v) && BigInt(v) <= 9223372036854775807n;
function isMark(v: unknown): v is StockMark {
  if (
    !stockRecord(v) ||
    !stockExact(
      v,
      "mark_mode valuation_reason source feed event_at collected_at historical_admission_until retained_until valid_until authority units_safe",
    ) ||
    !["fresh", "closed", "halted", "unavailable"].includes(v.mark_mode as string) ||
    !(v.valuation_reason === "available" || STOCK_REFUSALS.includes(v.valuation_reason as StockRefusal)) ||
    typeof v.units_safe !== "boolean"
  )
    return false;
  const fields = [
    "event_at",
    "collected_at",
    "historical_admission_until",
    "retained_until",
    "valid_until",
  ] as const;
  if (v.mark_mode === "unavailable")
    return (
      v.valuation_reason !== "available" &&
      v.source === null &&
      v.feed === null &&
      v.authority === null &&
      fields.every((k) => v[k] === null)
    );
  if (
    !v.units_safe ||
    v.valuation_reason !== "available" ||
    v.source !== "alpaca" ||
    v.feed !== "iex" ||
    !isStockAuthority(v.authority) ||
    !fields.every((k) => stockTimestamp(v[k]))
  )
    return false;
  const event = stockInstant(v.event_at as string),
    collected = stockInstant(v.collected_at as string),
    until = stockInstant(v.valid_until as string);
  return (
    event <= collected &&
    collected < until &&
    until <= stockInstant(v.historical_admission_until as string) &&
    until <= stockInstant(v.retained_until as string) &&
    v.authority.admissions.every((a) => until <= stockInstant(a.valid_until))
  );
}
function isHolding(v: unknown): v is PortfolioHolding {
  if (
    !stockRecord(v) ||
    !stockExact(
      v,
      "symbol name is_active asset_class coin_id provider_asset_id stock_mark quantity cost_basis average_cost mid current_value unrealized_pl unrealized_pl_percent allocation_percent as_of age_seconds status",
    ) ||
    !text(v.symbol) ||
    !text(v.name) ||
    typeof v.is_active !== "boolean" ||
    !id(v.coin_id) ||
    !["crypto", "stock"].includes(v.asset_class as string) ||
    !unsigned(v.quantity) ||
    stockFixed(v.quantity) === 0n ||
    !unsigned(v.cost_basis) ||
    !nullable(v.average_cost, unsigned) ||
    !nullable(v.mid, unsigned) ||
    !nullable(v.current_value, unsigned) ||
    !nullable(v.unrealized_pl, decimal) ||
    !nullable(v.unrealized_pl_percent, decimal) ||
    !nullable(v.allocation_percent, allocation) ||
    !nullable(v.as_of, stockTimestamp) ||
    !nullable(v.age_seconds, age) ||
    !["fresh", "aging", "stale", "unpriced"].includes(v.status as string)
  )
    return false;
  const unpriced = v.mid === null;
  if (
    unpriced !== (v.current_value === null) ||
    unpriced !== (v.as_of === null) ||
    unpriced !== (v.age_seconds === null) ||
    unpriced !== (v.status === "unpriced") ||
    (unpriced &&
      (v.unrealized_pl !== null ||
        v.unrealized_pl_percent !== null ||
        v.allocation_percent !== null))
  )
    return false;
  if (v.asset_class === "crypto")
    return v.provider_asset_id === null && v.stock_mark === null && v.average_cost !== null;
  if (
    !text(v.provider_asset_id) ||
    !/^\d{1,12}(?:\.0{1,9})?$/.test(v.quantity) ||
    !isMark(v.stock_mark)
  )
    return false;
  const mark = v.stock_mark;
  if (
    unpriced !== (mark.mark_mode === "unavailable") ||
    (!mark.units_safe && v.average_cost !== null)
  )
    return false;
  return unpriced || (v.as_of === mark.event_at && v.average_cost !== null);
}
export function isPortfolio(v: unknown): v is Portfolio {
  if (
    !stockRecord(v) ||
    !stockExact(
      v,
      "cash starting_cash total_value total_pl total_pl_percent cash_allocation_percent valuation_complete known_value unvalued_holding_count class_values class_allocation_percent valued_at prices_as_of fresh_seconds stale_seconds holdings",
    ) ||
    !unsigned(v.cash) ||
    !unsigned(v.starting_cash) ||
    !unsigned(v.known_value) ||
    !nullable(v.total_value, unsigned) ||
    !nullable(v.total_pl, decimal) ||
    !nullable(v.total_pl_percent, decimal) ||
    !nullable(v.cash_allocation_percent, allocation) ||
    typeof v.valuation_complete !== "boolean" ||
    !age(v.unvalued_holding_count) ||
    !stockTimestamp(v.valued_at) ||
    !nullable(v.prices_as_of, stockTimestamp) ||
    !age(v.fresh_seconds) ||
    !age(v.stale_seconds) ||
    v.fresh_seconds > v.stale_seconds ||
    !Array.isArray(v.holdings) ||
    v.holdings.length > 1000 ||
    !v.holdings.every(isHolding) ||
    !stockRecord(v.class_values) ||
    !stockExact(v.class_values, "cash stocks crypto") ||
    !unsigned(v.class_values.cash) ||
    !nullable(v.class_values.stocks, unsigned) ||
    !nullable(v.class_values.crypto, unsigned) ||
    !stockRecord(v.class_allocation_percent) ||
    !stockExact(v.class_allocation_percent, "cash stocks crypto") ||
    !Object.values(v.class_allocation_percent).every((x) => nullable(x, allocation))
  )
    return false;
  const p = v as unknown as Portfolio;
  const unvalued = p.holdings.filter((h) => h.mid === null).length;
  if (
    new Set(p.holdings.map((h) => h.coin_id)).size !== p.holdings.length ||
    unvalued !== p.unvalued_holding_count ||
    p.valuation_complete !== (unvalued === 0) ||
    stockFixed(p.class_values.cash) !== stockFixed(p.cash)
  )
    return false;
  if (p.holdings.some((h) => h.as_of !== null && stockInstant(h.as_of) > stockInstant(p.valued_at)))
    return false;
  for (const [asset, key] of [
    ["stock", "stocks"],
    ["crypto", "crypto"],
  ] as const)
    if (
      (p.class_values[key] === null) !==
      p.holdings.some((h) => h.asset_class === asset && h.mid === null)
    )
      return false;
  const allocations = [
    p.cash_allocation_percent,
    ...Object.values(p.class_allocation_percent),
    ...p.holdings.map((h) => h.allocation_percent),
  ];
  if (!p.valuation_complete)
    return (
      p.total_value === null &&
      p.total_pl === null &&
      p.total_pl_percent === null &&
      allocations.every((x) => x === null)
    );
  if (
    p.total_value === null ||
    p.total_pl === null ||
    stockFixed(p.total_value) !== stockFixed(p.known_value) ||
    stockFixed(p.total_pl, true) !== stockFixed(p.total_value)! - stockFixed(p.starting_cash)! ||
    (stockFixed(p.starting_cash) === 0n) !== (p.total_pl_percent === null)
  )
    return false;
  return stockFixed(p.total_value) === 0n
    ? allocations.every((x) => x === null)
    : allocations.every((x) => x !== null) &&
        stockFixed(p.cash_allocation_percent) === stockFixed(p.class_allocation_percent.cash);
}
export async function fetchPortfolio(signal?: AbortSignal): Promise<Portfolio> {
  const body = await apiFetch("/api/v1/portfolio", { signal, cache: "no-store" });
  if (!isPortfolio(body)) throw new Error("Unexpected portfolio response");
  return body;
}
