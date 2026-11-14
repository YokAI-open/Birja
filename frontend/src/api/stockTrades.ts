import { ApiError, apiFetch } from "./client";
import { stockInstant, stockTimestamp } from "./stocks";
import type { Side } from "./trades";

export type StockOrder = { symbol: string; side: Side; quantity: string };
export type StockAttempt = StockOrder & { expected_exec_price: string; idempotency_key: string };
export type AdmissionIdentity = {
  product: "reference" | "quotes" | "actions" | "status" | "calendar";
  generation: number;
  row_hash: string;
  valid_until: string;
};
export type AuthorityIdentity = {
  admissions: AdmissionIdentity[];
  calendar_generation: number;
  safety_epoch: number;
  unit_epoch: number;
  status_admission_generation: number;
  continuity_generation: number;
  status_sequence: number;
};
export type StockEconomics = {
  coin_id: string;
  provider_asset_id: string;
  symbol: string;
  company_name: string;
  listing_exchange: "NYSE" | "NASDAQ";
  currency: "USD";
  side: Side;
  quantity: string;
  bid: string;
  ask: string;
  exact_mid: string;
  exec_price: string;
  source: "alpaca";
  feed: "iex";
  event_at: string;
  collected_at: string;
  observed_at: string;
  age_seconds: number;
  notional: string;
  fee: string;
  cash_delta: string;
  cash_before: string;
  cash_after: string;
  held_before: string;
  held_after: string;
  session_date: string;
  session_opens_at: string;
  session_closes_at: string;
  authority: AuthorityIdentity;
};
export type StockTradeQuote = StockEconomics & { valid_until: string };
export type StockFill = StockEconomics & {
  schema_version: 1;
  trade_id: string;
  executed_at: string;
};

export const STOCK_REFUSALS = [
  "permission_unavailable",
  "action_unavailable",
  "units_changed",
  "halted",
  "frozen",
  "status_unavailable",
  "session_unavailable",
  "market_closed",
  "quote_unavailable",
  "quote_stale",
  "receipt_unavailable",
  "invalid_quantity",
  "insufficient_cash",
  "insufficient_holding",
  "numeric_range",
  "idempotency_conflict",
] as const;
export type StockRefusal = (typeof STOCK_REFUSALS)[number];
export type StockPriceChanged = {
  code: "price_changed";
  previous_exec_price: string;
  previous_cash_delta: string;
  exec_price_change: string;
  cash_delta_change: string;
  quote: StockTradeQuote;
};
export type QuoteFacts = Pick<
  StockEconomics,
  "bid" | "ask" | "exact_mid" | "source" | "feed" | "event_at" | "collected_at" | "session_date"
> & { admission_generation: number; unit_epoch: number };
export type StockContext = Pick<
  StockEconomics,
  "coin_id" | "provider_asset_id" | "symbol" | "company_name" | "listing_exchange" | "observed_at"
> & {
  cash: string;
  held_quantity: string;
  buy_max_quantity: string;
  quote: QuoteFacts | null;
  session: {
    state: "open" | "closed" | "unknown";
    session_date: string;
    opens_at: string | null;
    closes_at: string | null;
    valid_until: string | null;
    next_open_at: string | null;
    timezone: "America/New_York";
  };
  status: {
    state: "normal" | "halted" | "frozen" | "unknown";
    event_at: string | null;
    observed_at: string | null;
    valid_until: string | null;
    bootstrap_verified: boolean;
    continuity_current: boolean;
  };
  action: {
    state: "current" | "unknown" | "reconciling" | "suspended";
    reason: string;
    valid_until: string | null;
    next_blocking_at: string | null;
  };
  authority: AuthorityIdentity | null;
  execution_enabled: boolean;
  execution_reason: StockRefusal | "available";
  valid_until: string | null;
};
export type StockTransport = { started_at: number; received_at: number; round_trip_ms: number };
export type TimedStockQuote = StockTradeQuote & { transport: StockTransport };
export type TimedStockContext = StockContext & {
  transport: StockTransport;
  authority_offset_ms?: number;
};

export const stockRecord = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);
export const stockExact = (v: Record<string, unknown>, keys: string) =>
  Object.keys(v).length === keys.split(" ").length && keys.split(" ").every((k) => k in v);
const text = (v: unknown, max: number): v is string =>
  typeof v === "string" && v.trim().length > 0 && v.length <= max;
const member = (v: unknown, items: readonly string[]): v is string =>
  typeof v === "string" && items.includes(v);
const integer = (v: unknown, min = 0): v is number =>
  Number.isSafeInteger(v) && (v as number) >= min;
const nullableTime = (v: unknown) => v === null || stockTimestamp(v);
const symbol = (v: unknown): v is string =>
  typeof v === "string" && /^[A-Z][A-Z0-9.-]{0,9}$/.test(v);
const id = (v: unknown): v is string =>
  typeof v === "string" && /^[1-9][0-9]{0,18}$/.test(v) && BigInt(v) <= 9223372036854775807n;
export const STOCK_SCALE = 1_000_000_000n;
const CENT = 10_000_000n;
const MAX_BAL = 1_000_000_000_000n * STOCK_SCALE - CENT;
const MAX_SHARES = 999_999_999_999n * STOCK_SCALE;
const MAX_PRICE = 1_000_000_000_000n * STOCK_SCALE - 10n;
/** Bounded exact decimal scale9 for validation, never a displayed accounting calculation. */
export function stockFixed(v: unknown, signed = false): bigint | null {
  if (
    typeof v !== "string" ||
    !/^-?(?:0|[1-9][0-9]{0,37})(?:\.[0-9]{1,9})?$/.test(v) ||
    (!signed && v.startsWith("-"))
  )
    return null;
  const negative = v.startsWith("-");
  const [whole, fraction = ""] = (negative ? v.slice(1) : v).split(".");
  const result = BigInt(whole + fraction.padEnd(9, "0"));
  return negative ? -result : result;
}
const price = (v: unknown) => {
  const n = stockFixed(v);
  return n !== null && n > 0n && n <= MAX_PRICE && n % 10n === 0n ? n : null;
};
const balance = (v: unknown, signed = false) => {
  const n = stockFixed(v, signed);
  return n !== null && n >= -MAX_BAL && n <= MAX_BAL && n % CENT === 0n ? n : null;
};
const shares = (v: unknown, positive = false) => {
  const n = stockFixed(v);
  return n !== null && n >= 0n && (!positive || n > 0n) && n <= MAX_SHARES && n % STOCK_SCALE === 0n
    ? n
    : null;
};
const roundCent = (v: bigint) => {
  const whole = v / CENT,
    rest = v % CENT;
  return (whole + (rest > CENT / 2n || (rest === CENT / 2n && whole % 2n === 1n) ? 1n : 0n)) * CENT;
};
export function isStockOrder(v: unknown): v is StockOrder {
  return (
    stockRecord(v) &&
    stockExact(v, "symbol side quantity") &&
    symbol(v.symbol) &&
    member(v.side, ["buy", "sell"]) &&
    typeof v.quantity === "string" &&
    /^[1-9][0-9]{0,11}$/.test(v.quantity)
  );
}
export function isStockAttempt(v: unknown): v is StockAttempt {
  return (
    stockRecord(v) &&
    stockExact(v, "symbol side quantity expected_exec_price idempotency_key") &&
    isStockOrder({ symbol: v.symbol, side: v.side, quantity: v.quantity }) &&
    price(v.expected_exec_price) !== null &&
    typeof v.idempotency_key === "string" &&
    /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(v.idempotency_key)
  );
}
export function isStockAuthority(v: unknown): v is AuthorityIdentity {
  if (
    !stockRecord(v) ||
    !stockExact(
      v,
      "admissions calendar_generation safety_epoch unit_epoch status_admission_generation continuity_generation status_sequence",
    ) ||
    !Array.isArray(v.admissions) ||
    v.admissions.length !== 5
  )
    return false;
  if (
    ![
      v.calendar_generation,
      v.safety_epoch,
      v.unit_epoch,
      v.status_admission_generation,
      v.continuity_generation,
      v.status_sequence,
    ].every((x) => integer(x))
  )
    return false;
  if (
    !v.admissions.every(
      (a) =>
        stockRecord(a) &&
        stockExact(a, "product generation row_hash valid_until") &&
        member(a.product, ["reference", "quotes", "actions", "status", "calendar"]) &&
        integer(a.generation, 1) &&
        typeof a.row_hash === "string" &&
        /^[a-f0-9]{64}$/.test(a.row_hash) &&
        stockTimestamp(a.valid_until),
    )
  )
    return false;
  return new Set(v.admissions.map((a) => a.product)).size === 5;
}
function approvedAuthority(v: AuthorityIdentity, at: string): boolean {
  return (
    v.calendar_generation === v.admissions.find((a) => a.product === "calendar")?.generation &&
    v.status_admission_generation ===
      v.admissions.find((a) => a.product === "status")?.generation &&
    v.continuity_generation > 0 &&
    v.admissions.every((a) => stockInstant(a.valid_until) > stockInstant(at))
  );
}
const ECONOMIC =
  "coin_id provider_asset_id symbol company_name listing_exchange currency side quantity bid ask exact_mid exec_price source feed event_at collected_at observed_at age_seconds notional fee cash_delta cash_before cash_after held_before held_after session_date session_opens_at session_closes_at authority";
function identity(v: Record<string, unknown>): boolean {
  return (
    id(v.coin_id) &&
    text(v.provider_asset_id, 128) &&
    symbol(v.symbol) &&
    text(v.company_name, 256) &&
    member(v.listing_exchange, ["NYSE", "NASDAQ"])
  );
}
function economics(v: Record<string, unknown>): v is Record<string, unknown> & StockEconomics {
  if (
    !identity(v) ||
    v.currency !== "USD" ||
    !member(v.side, ["buy", "sell"]) ||
    v.source !== "alpaca" ||
    v.feed !== "iex" ||
    !integer(v.age_seconds) ||
    ![v.event_at, v.collected_at, v.observed_at, v.session_opens_at, v.session_closes_at].every(
      stockTimestamp,
    ) ||
    !isStockAuthority(v.authority)
  )
    return false;
  const event = stockInstant(v.event_at as string),
    collected = stockInstant(v.collected_at as string),
    observed = stockInstant(v.observed_at as string),
    open = stockInstant(v.session_opens_at as string),
    close = stockInstant(v.session_closes_at as string);
  if (
    !(open <= event && event <= collected && collected <= observed && observed < close) ||
    v.session_date !== (v.event_at as string).slice(0, 10) ||
    v.session_date !== (v.session_opens_at as string).slice(0, 10) ||
    v.age_seconds !== Number((observed - event) / 1_000_000_000n) ||
    observed - event >= 120_000_000_000n ||
    !approvedAuthority(v.authority, v.observed_at as string)
  )
    return false;
  const bid = price(v.bid),
    ask = price(v.ask),
    mid = stockFixed(v.exact_mid),
    exec = price(v.exec_price),
    qty = shares(v.quantity, true),
    notional = balance(v.notional),
    fee = balance(v.fee),
    delta = balance(v.cash_delta, true),
    before = balance(v.cash_before),
    after = balance(v.cash_after),
    held = shares(v.held_before),
    heldAfter = shares(v.held_after);
  if (
    bid === null ||
    ask === null ||
    mid === null ||
    exec === null ||
    qty === null ||
    notional === null ||
    fee === null ||
    delta === null ||
    before === null ||
    after === null ||
    held === null ||
    heldAfter === null
  )
    return false;
  return (
    bid <= ask &&
    mid * 2n === bid + ask &&
    exec === (v.side === "buy" ? ask : bid) &&
    fee === 0n &&
    notional === roundCent(exec * (qty / STOCK_SCALE)) &&
    delta === (v.side === "buy" ? -notional : notional) &&
    (v.side !== "buy" || notional > 0n) &&
    before + delta === after &&
    heldAfter === (v.side === "buy" ? held + qty : held - qty)
  );
}
export function isStockTradeQuote(v: unknown): v is StockTradeQuote {
  if (
    !stockRecord(v) ||
    !stockExact(v, ECONOMIC + " valid_until") ||
    !economics(v) ||
    !stockTimestamp(v.valid_until)
  )
    return false;
  const until = stockInstant(v.valid_until),
    observed = stockInstant(v.observed_at);
  return (
    until > observed &&
    until <= stockInstant(v.session_closes_at) &&
    until <= stockInstant(v.event_at) + 120_000_000_000n &&
    until <= observed + 60_000_000_000n &&
    v.authority.admissions.every((a) => until <= stockInstant(a.valid_until))
  );
}
export function isStockFill(v: unknown): v is StockFill {
  if (
    !stockRecord(v) ||
    !stockExact(v, ECONOMIC + " schema_version trade_id executed_at") ||
    !economics(v) ||
    v.schema_version !== 1 ||
    !id(v.trade_id) ||
    !stockTimestamp(v.executed_at)
  )
    return false;
  const at = stockInstant(v.executed_at);
  return stockInstant(v.collected_at) <= at && at <= stockInstant(v.observed_at);
}
function quoteFacts(v: unknown): v is QuoteFacts {
  if (
    !stockRecord(v) ||
    !stockExact(
      v,
      "bid ask exact_mid source feed event_at collected_at session_date admission_generation unit_epoch",
    )
  )
    return false;
  const bid = price(v.bid),
    ask = price(v.ask),
    mid = stockFixed(v.exact_mid);
  return (
    bid !== null &&
    ask !== null &&
    mid !== null &&
    bid <= ask &&
    mid * 2n === bid + ask &&
    v.source === "alpaca" &&
    v.feed === "iex" &&
    stockTimestamp(v.event_at) &&
    stockTimestamp(v.collected_at) &&
    stockInstant(v.event_at) <= stockInstant(v.collected_at) &&
    v.session_date === v.event_at.slice(0, 10) &&
    integer(v.admission_generation, 1) &&
    integer(v.unit_epoch)
  );
}
export function isStockContext(v: unknown): v is StockContext {
  if (
    !stockRecord(v) ||
    !stockExact(
      v,
      "coin_id provider_asset_id symbol company_name listing_exchange observed_at cash held_quantity buy_max_quantity quote session status action authority execution_enabled execution_reason valid_until",
    ) ||
    !identity(v) ||
    !stockTimestamp(v.observed_at) ||
    balance(v.cash) === null ||
    shares(v.held_quantity) === null ||
    shares(v.buy_max_quantity) === null ||
    (v.quote !== null && !quoteFacts(v.quote)) ||
    (v.authority !== null && !isStockAuthority(v.authority)) ||
    typeof v.execution_enabled !== "boolean" ||
    !member(v.execution_reason, [...STOCK_REFUSALS, "available"]) ||
    !nullableTime(v.valid_until)
  )
    return false;
  const { session: s, status: t, action: a } = v;
  if (
    !stockRecord(s) ||
    !stockExact(s, "state session_date opens_at closes_at valid_until next_open_at timezone") ||
    !member(s.state, ["open", "closed", "unknown"]) ||
    typeof s.session_date !== "string" ||
    !/^\d{4}-\d{2}-\d{2}$/.test(s.session_date) ||
    !stockTimestamp(s.session_date + "T00:00:00Z") ||
    s.timezone !== "America/New_York" ||
    ![s.opens_at, s.closes_at, s.valid_until, s.next_open_at].every(nullableTime) ||
    (s.opens_at === null) !== (s.closes_at === null)
  )
    return false;
  if (
    s.opens_at !== null &&
    stockInstant(s.opens_at as string) >= stockInstant(s.closes_at as string)
  )
    return false;
  if (
    !stockRecord(t) ||
    !stockExact(
      t,
      "state event_at observed_at valid_until bootstrap_verified continuity_current",
    ) ||
    !member(t.state, ["normal", "halted", "frozen", "unknown"]) ||
    ![t.event_at, t.observed_at, t.valid_until].every(nullableTime) ||
    typeof t.bootstrap_verified !== "boolean" ||
    typeof t.continuity_current !== "boolean"
  )
    return false;
  if (
    !stockRecord(a) ||
    !stockExact(a, "state reason valid_until next_blocking_at") ||
    !member(a.state, ["current", "unknown", "reconciling", "suspended"]) ||
    !member(a.reason, ["available", "monitor_unavailable"]) ||
    ![a.valid_until, a.next_blocking_at].every(nullableTime)
  )
    return false;
  if (v.execution_enabled !== (v.execution_reason === "available")) return false;
  if (!v.execution_enabled)
    return (
      shares(v.buy_max_quantity) === 0n &&
      (v.valid_until === null ||
        (v.quote !== null && stockInstant(v.valid_until as string) > stockInstant(v.observed_at)))
    );
  if (
    v.quote === null ||
    v.authority === null ||
    v.valid_until === null ||
    s.state !== "open" ||
    !stockTimestamp(s.opens_at) ||
    !stockTimestamp(s.closes_at) ||
    !stockTimestamp(s.valid_until) ||
    t.state !== "normal" ||
    !t.bootstrap_verified ||
    !t.continuity_current ||
    ![t.event_at, t.observed_at, t.valid_until, a.valid_until].every(stockTimestamp) ||
    a.state !== "current" ||
    a.reason !== "available" ||
    !approvedAuthority(v.authority, v.observed_at)
  )
    return false;
  const at = stockInstant(v.observed_at),
    until = stockInstant(v.valid_until),
    q = v.quote;
  return (
    stockInstant(s.opens_at) <= stockInstant(q.event_at) &&
    stockInstant(q.collected_at) <= at &&
    stockInstant(q.event_at) > at - 120_000_000_000n &&
    s.session_date === q.session_date &&
    stockInstant(s.opens_at) <= at &&
    at < stockInstant(s.closes_at) &&
    stockInstant(t.event_at as string) <= stockInstant(t.observed_at as string) &&
    stockInstant(t.observed_at as string) <= at &&
    stockInstant(t.valid_until as string) <=
      stockInstant(t.observed_at as string) + 60_000_000_000n &&
    until > at &&
    [
      s.closes_at,
      s.valid_until,
      t.valid_until,
      a.valid_until,
      ...v.authority.admissions.map((x) => x.valid_until),
    ].every((x) => until <= stockInstant(x as string)) &&
    (a.next_blocking_at === null || until <= stockInstant(a.next_blocking_at as string)) &&
    until <= stockInstant(q.event_at) + 120_000_000_000n &&
    shares(v.buy_max_quantity)! <= (balance(v.cash)! / price(q.ask)!) * STOCK_SCALE &&
    shares(v.held_quantity)! + shares(v.buy_max_quantity)! <= MAX_SHARES &&
    q.admission_generation ===
      v.authority.admissions.find((x) => x.product === "quotes")?.generation &&
    q.unit_epoch === v.authority.unit_epoch
  );
}
export function isStockPriceChanged(v: unknown): v is StockPriceChanged {
  if (
    !stockRecord(v) ||
    !stockExact(
      v,
      "code previous_exec_price previous_cash_delta exec_price_change cash_delta_change quote",
    ) ||
    v.code !== "price_changed" ||
    !isStockTradeQuote(v.quote)
  )
    return false;
  const previous = price(v.previous_exec_price),
    oldDelta = balance(v.previous_cash_delta, true),
    priceChange = stockFixed(v.exec_price_change, true),
    cashChange = balance(v.cash_delta_change, true);
  if (previous === null || oldDelta === null || priceChange === null || cashChange === null)
    return false;
  const q = v.quote,
    old =
      roundCent(previous * (shares(q.quantity, true)! / STOCK_SCALE)) *
      (q.side === "buy" ? -1n : 1n);
  return (
    old === oldDelta &&
    priceChange !== 0n &&
    priceChange === price(q.exec_price)! - previous &&
    cashChange === balance(q.cash_delta, true)! - oldDelta
  );
}

export class StockTradeError extends Error {
  readonly kind: "refused" | "reprice" | "unknown";
  readonly code: StockRefusal | null;
  readonly status: number | null;
  readonly replacement: (StockPriceChanged & { quote: TimedStockQuote }) | null;
  constructor(
    kind: "refused" | "reprice" | "unknown",
    code: StockRefusal | null = null,
    status: number | null = null,
    replacement: (StockPriceChanged & { quote: TimedStockQuote }) | null = null,
  ) {
    super(kind === "unknown" ? "Stock order result is unconfirmed." : "Stock order needs review.");
    this.name = "StockTradeError";
    this.kind = kind;
    this.code = code;
    this.status = status;
    this.replacement = replacement;
  }
}
const timed = <T>(value: T, started: number): T & { transport: StockTransport } => {
  const received = performance.now();
  return {
    ...value,
    transport: {
      started_at: started,
      received_at: received,
      round_trip_ms: Math.max(0, received - started),
    },
  };
};
const sameOrder = (v: StockEconomics, order: StockOrder) =>
  v.symbol === order.symbol &&
  v.side === order.side &&
  shares(v.quantity, true) === stockFixed(order.quantity);
function failure(error: unknown, started: number, order?: StockAttempt): never {
  if (error instanceof ApiError) {
    if (
      error.status === 409 &&
      isStockPriceChanged(error.detail) &&
      order &&
      sameOrder(error.detail.quote, order) &&
      price(error.detail.previous_exec_price) === price(order.expected_exec_price)
    )
      throw new StockTradeError("reprice", null, 409, {
        ...error.detail,
        quote: timed(error.detail.quote, started),
      });
    if (
      error.detail &&
      stockExact(error.detail, "code") &&
      member(error.code, STOCK_REFUSALS) &&
      !(order && error.code === "receipt_unavailable") &&
      ((error.status === 422 &&
        ["invalid_quantity", "insufficient_cash", "insufficient_holding", "numeric_range"].includes(
          error.code,
        )) ||
        (error.status === 409 &&
          ![
            "invalid_quantity",
            "insufficient_cash",
            "insufficient_holding",
            "numeric_range",
          ].includes(error.code)))
    )
      throw new StockTradeError("refused", error.code as StockRefusal, error.status);
    throw new StockTradeError("unknown", null, error.status);
  }
  throw new StockTradeError("unknown");
}
export async function fetchStockQuote(
  order: StockOrder,
  signal?: AbortSignal,
): Promise<TimedStockQuote> {
  const started = performance.now();
  if (!isStockOrder(order)) throw new StockTradeError("refused", "invalid_quantity");
  try {
    const value = await apiFetch("/api/v1/stock-trades/quote", {
      method: "POST",
      body: JSON.stringify(order),
      signal,
      cache: "no-store",
    });
    if (!isStockTradeQuote(value) || !sameOrder(value, order))
      throw new Error("Unexpected stock quote response");
    signal?.throwIfAborted();
    return timed(value, started);
  } catch (error) {
    failure(error, started);
  }
}
export async function fetchStockContext(
  symbolValue: string,
  signal?: AbortSignal,
): Promise<TimedStockContext> {
  const started = performance.now();
  if (!symbol(symbolValue)) throw new StockTradeError("refused", "quote_unavailable");
  try {
    const value = await apiFetch(
      `/api/v1/stock-trades/${encodeURIComponent(symbolValue)}/context`,
      { signal, cache: "no-store" },
    );
    if (!isStockContext(value) || value.symbol !== symbolValue)
      throw new Error("Unexpected stock context response");
    signal?.throwIfAborted();
    return timed(value, started);
  } catch (error) {
    failure(error, started);
  }
}
export async function executeStockTrade(
  order: StockAttempt,
  signal?: AbortSignal,
): Promise<StockFill> {
  const started = performance.now();
  if (!isStockAttempt(order)) throw new StockTradeError("refused", "invalid_quantity");
  try {
    const value = await apiFetch("/api/v1/stock-trades", {
      method: "POST",
      body: JSON.stringify(order),
      signal,
      cache: "no-store",
    });
    if (!isStockFill(value) || !sameOrder(value, order))
      throw new Error("Unexpected stock fill response");
    signal?.throwIfAborted();
    return value;
  } catch (error) {
    failure(error, started, order);
  }
}
