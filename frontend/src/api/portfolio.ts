import { apiFetch } from "./client";

export type PortfolioHolding = {
  symbol: string;
  name: string;
  is_active: boolean;
  quantity: string;
  cost_basis: string;
  average_cost: string;
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
  valued_at: string;
  prices_as_of: string | null;
  fresh_seconds: number;
  stale_seconds: number;
  holdings: PortfolioHolding[];
};

const record = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);
const text = (v: unknown): v is string => typeof v === "string" && v.length > 0;
const decimal = (v: unknown): v is string => typeof v === "string" && /^-?\d+(\.\d+)?$/.test(v);
const unsigned = (v: unknown): v is string => decimal(v) && !v.startsWith("-");
const age = (v: unknown): v is number => typeof v === "number" && Number.isSafeInteger(v) && v >= 0;
const timestamp = (v: unknown): v is string =>
  typeof v === "string" &&
  /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$/.test(v) &&
  Number.isFinite(Date.parse(v));
const nullable = (v: unknown, guard: (v: unknown) => boolean) => v === null || guard(v);
const allocation = (v: unknown) => unsigned(v) && /^(?:\d{1,2}(?:\.\d+)?|100(?:\.0+)?)$/.test(v);

function isHolding(v: unknown): v is PortfolioHolding {
  return (
    record(v) &&
    text(v.symbol) &&
    text(v.name) &&
    typeof v.is_active === "boolean" &&
    unsigned(v.quantity) &&
    unsigned(v.cost_basis) &&
    unsigned(v.average_cost) &&
    nullable(v.mid, unsigned) &&
    nullable(v.current_value, unsigned) &&
    nullable(v.unrealized_pl, decimal) &&
    nullable(v.unrealized_pl_percent, decimal) &&
    nullable(v.allocation_percent, allocation) &&
    nullable(v.as_of, timestamp) &&
    nullable(v.age_seconds, age) &&
    (v.status === "fresh" ||
      v.status === "aging" ||
      v.status === "stale" ||
      v.status === "unpriced")
  );
}

export function isPortfolio(v: unknown): v is Portfolio {
  return (
    record(v) &&
    unsigned(v.cash) &&
    unsigned(v.starting_cash) &&
    nullable(v.total_value, unsigned) &&
    nullable(v.total_pl, decimal) &&
    nullable(v.total_pl_percent, decimal) &&
    nullable(v.cash_allocation_percent, allocation) &&
    typeof v.valuation_complete === "boolean" &&
    timestamp(v.valued_at) &&
    nullable(v.prices_as_of, timestamp) &&
    age(v.fresh_seconds) &&
    age(v.stale_seconds) &&
    Array.isArray(v.holdings) &&
    v.holdings.every(isHolding)
  );
}

export async function fetchPortfolio(signal?: AbortSignal): Promise<Portfolio> {
  const body = await apiFetch("/api/v1/portfolio", { signal });
  if (!isPortfolio(body)) throw new Error("Unexpected portfolio response");
  return body;
}
