import { apiFetch } from "./client";

export type StockQuote = {
  bid: string;
  ask: string;
  mid: string;
  event_at: string;
  collected_at: string;
  source: "alpaca";
  feed: "iex";
  age_seconds: number;
};
export type StockSession = {
  state: "open" | "closed" | "unknown";
  opens_at: string | null;
  closes_at: string | null;
  next_open_at: string | null;
  valid_until: string | null;
  timezone: "America/New_York";
};
export type StockItem = {
  id: number;
  symbol: string;
  company_name: string;
  listing_exchange: "NYSE" | "NASDAQ";
  currency: "USD";
  quote: StockQuote | null;
  session: StockSession;
  status: { state: "unknown"; observed_at: string | null; valid_until: string | null };
  execution_enabled: false;
  execution_reason: "phase_disabled";
  quote_reason: "permission_unavailable" | "missing" | "stale" | "session_unavailable" | "recent";
  session_reason: "open" | "closed" | "unknown";
  status_reason: "unknown";
};
export type StocksResponse = {
  server_now: string;
  admission: {
    state: "approved" | "unavailable";
    generation: number | null;
    valid_until: string | null;
  };
  attribution: { label: "IEX prices"; explanation: string; required_text: string };
  items: StockItem[];
};
export type TimedStocks = StocksResponse & {
  transport: { started_at: number; received_at: number; round_trip_ms: number };
};

const record = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);
const text = (value: unknown): value is string => typeof value === "string" && value.trim() !== "";
const positiveInteger = (value: unknown): value is number =>
  Number.isSafeInteger(value) && (value as number) > 0;
const enumValue = (value: unknown, values: readonly string[]) =>
  typeof value === "string" && values.includes(value);

/** Validate civil fields too: Date.parse alone normalizes e.g. February 30. */
function timestamp(value: unknown): value is string {
  if (typeof value !== "string") return false;
  const match =
    /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d{1,9})?(Z|[+-]\d{2}:\d{2})$/.exec(
      value,
    );
  if (!match) return false;
  const [, year, month, day, hour, minute, second, zone] = match;
  const days = new Date(Date.UTC(Number(year), Number(month), 0)).getUTCDate();
  return (
    Number(month) >= 1 &&
    Number(month) <= 12 &&
    Number(day) >= 1 &&
    Number(day) <= days &&
    Number(hour) < 24 &&
    Number(minute) < 60 &&
    Number(second) < 60 &&
    (zone === "Z" || (Number(zone.slice(1, 3)) < 24 && Number(zone.slice(4)) < 60)) &&
    Number.isFinite(Date.parse(value))
  );
}
const nullableTime = (value: unknown) => value === null || timestamp(value);

/** Exact NUMERIC(20,8) comparison; money never enters JS Number arithmetic. */
function units(value: unknown): bigint | null {
  if (typeof value !== "string" || !/^\d{1,12}(?:\.\d{1,8})?$/.test(value)) return null;
  const [whole, fraction = ""] = value.split(".");
  const result = BigInt(whole + fraction.padEnd(8, "0"));
  return result > 0n ? result : null;
}
function quote(value: unknown): value is StockQuote {
  if (!record(value)) return false;
  const bid = units(value.bid),
    ask = units(value.ask),
    mid = units(value.mid);
  return (
    bid !== null &&
    ask !== null &&
    mid !== null &&
    bid <= mid &&
    mid <= ask &&
    timestamp(value.event_at) &&
    timestamp(value.collected_at) &&
    value.source === "alpaca" &&
    value.feed === "iex" &&
    Number.isSafeInteger(value.age_seconds) &&
    (value.age_seconds as number) >= 0
  );
}
function session(value: unknown): value is StockSession {
  if (!record(value)) return false;
  if (
    !enumValue(value.state, ["open", "closed", "unknown"]) ||
    value.timezone !== "America/New_York" ||
    ![value.opens_at, value.closes_at, value.next_open_at, value.valid_until].every(nullableTime)
  )
    return false;
  if ((value.opens_at === null) !== (value.closes_at === null)) return false;
  if (
    value.opens_at !== null &&
    Date.parse(value.opens_at as string) >= Date.parse(value.closes_at as string)
  )
    return false;
  return value.state !== "open" || (value.opens_at !== null && value.valid_until !== null);
}
function item(value: unknown): value is StockItem {
  if (!record(value) || !record(value.status)) return false;
  return (
    positiveInteger(value.id) &&
    typeof value.symbol === "string" &&
    /^[A-Z][A-Z0-9.-]{0,9}$/.test(value.symbol) &&
    text(value.company_name) &&
    enumValue(value.listing_exchange, ["NYSE", "NASDAQ"]) &&
    value.currency === "USD" &&
    (value.quote === null || quote(value.quote)) &&
    session(value.session) &&
    value.status.state === "unknown" &&
    nullableTime(value.status.observed_at) &&
    nullableTime(value.status.valid_until) &&
    value.execution_enabled === false &&
    value.execution_reason === "phase_disabled" &&
    enumValue(value.quote_reason, [
      "permission_unavailable",
      "missing",
      "stale",
      "session_unavailable",
      "recent",
    ]) &&
    enumValue(value.session_reason, ["open", "closed", "unknown"]) &&
    value.status_reason === "unknown"
  );
}
export function isStocks(value: unknown): value is StocksResponse {
  if (
    !record(value) ||
    !timestamp(value.server_now) ||
    !record(value.admission) ||
    !record(value.attribution)
  )
    return false;
  const admission = value.admission;
  if (admission.state === "approved") {
    if (!positiveInteger(admission.generation) || !timestamp(admission.valid_until)) return false;
  } else if (
    admission.state !== "unavailable" ||
    admission.generation !== null ||
    admission.valid_until !== null
  )
    return false;
  return (
    value.attribution.label === "IEX prices" &&
    text(value.attribution.explanation) &&
    typeof value.attribution.required_text === "string" &&
    Array.isArray(value.items) &&
    value.items.length === 20 &&
    value.items.every(item) &&
    new Set(value.items.map((x) => x.id)).size === 20 &&
    new Set(value.items.map((x) => x.symbol)).size === 20
  );
}

export async function fetchStocks(signal?: AbortSignal): Promise<TimedStocks> {
  // Enclose apiFetch's entire shared refresh/retry path and JSON validation.
  const started_at = performance.now();
  const body = await apiFetch("/api/v1/stocks", { signal });
  if (!isStocks(body)) throw new Error("Unexpected stocks response");
  signal?.throwIfAborted();
  const received_at = performance.now();
  return {
    ...body,
    transport: { started_at, received_at, round_trip_ms: Math.max(0, received_at - started_at) },
  };
}
