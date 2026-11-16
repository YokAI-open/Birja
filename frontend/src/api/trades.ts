import { ApiError, apiFetch } from "./client";
import { isPortfolioId } from "./portfolios";

export type Side = "buy" | "sell";

export type Order = {
  symbol: string;
  side: Side;
  amount_usd?: string;
  quantity?: string;
};

/** Saved by the caller before execution; a retry retains this original portfolio. */
export type TradeAttempt = Readonly<{
  portfolio_id: string;
  order: Readonly<Order>;
  expected_mid: string;
  idempotency_key: string;
}>;

export type Quote = {
  portfolio_id: string;
  symbol: string;
  side: Side;
  input_kind: "usd" | "quantity";
  input_value: string;
  mid: string;
  as_of: string;
  age_seconds: number;
  exec_price: string;
  quantity: string;
  notional: string;
  fee: string;
  cash_delta: string;
  cash_before: string;
  cash_after: string;
  held_before: string;
  held_after: string;
  whole_position: boolean;
};

export type Fill = {
  portfolio_id: string;
  trade_id: number;
  created_at: string;
  symbol: string;
  side: Side;
  input_kind: "usd" | "quantity";
  input_value: string;
  mid: string;
  as_of: string;
  exec_price: string;
  quantity: string;
  notional: string;
  fee: string;
  cash_delta: string;
  cash_after: string;
};

export type Holding = {
  portfolio_id: string;
  symbol: string;
  quantity: string;
};

const UNSIGNED = /^\d+(\.\d+)?$/;
const SIGNED = /^-?\d+(\.\d+)?$/;

const isText = (value: unknown): value is string => typeof value === "string" && value !== "";
const isUnsigned = (value: unknown): boolean => typeof value === "string" && UNSIGNED.test(value);
const isSigned = (value: unknown): boolean => typeof value === "string" && SIGNED.test(value);
const isSide = (value: unknown): boolean => value === "buy" || value === "sell";
const isKind = (value: unknown): boolean => value === "usd" || value === "quantity";
const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

export function isQuote(value: unknown): value is Quote {
  if (!isRecord(value)) {
    return false;
  }
  return (
    isPortfolioId(value.portfolio_id) &&
    isText(value.symbol) &&
    isSide(value.side) &&
    isKind(value.input_kind) &&
    isUnsigned(value.input_value) &&
    isUnsigned(value.mid) &&
    isText(value.as_of) &&
    Number.isInteger(value.age_seconds) &&
    isUnsigned(value.exec_price) &&
    isUnsigned(value.quantity) &&
    isUnsigned(value.notional) &&
    isUnsigned(value.fee) &&
    isSigned(value.cash_delta) &&
    isUnsigned(value.cash_before) &&
    isUnsigned(value.cash_after) &&
    isUnsigned(value.held_before) &&
    isUnsigned(value.held_after) &&
    typeof value.whole_position === "boolean"
  );
}

export function isFill(value: unknown): value is Fill {
  if (!isRecord(value)) {
    return false;
  }
  return (
    isPortfolioId(value.portfolio_id) &&
    Number.isInteger(value.trade_id) &&
    isText(value.created_at) &&
    isText(value.symbol) &&
    isSide(value.side) &&
    isKind(value.input_kind) &&
    isUnsigned(value.input_value) &&
    isUnsigned(value.mid) &&
    isText(value.as_of) &&
    isUnsigned(value.exec_price) &&
    isUnsigned(value.quantity) &&
    isUnsigned(value.notional) &&
    isUnsigned(value.fee) &&
    isSigned(value.cash_delta) &&
    isUnsigned(value.cash_after)
  );
}

export function isHolding(value: unknown): value is Holding {
  return (
    isRecord(value) &&
    isPortfolioId(value.portfolio_id) &&
    isText(value.symbol) &&
    isUnsigned(value.quantity)
  );
}

function path(portfolioId: string): string {
  if (!isPortfolioId(portfolioId)) throw new Error("Invalid portfolio target");
  return `/api/v2/portfolios/${encodeURIComponent(portfolioId)}`;
}

function validOrder(order: unknown): order is Order {
  if (!isRecord(order) || !isText(order.symbol) || !isSide(order.side)) return false;
  const input = order.amount_usd === undefined ? "quantity" : "amount_usd";
  return (
    Object.keys(order).length === 3 &&
    ["symbol", "side", input].every((key) => Object.hasOwn(order, key)) &&
    isUnsigned(order[input]) &&
    /[1-9]/.test(order[input] as string)
  );
}

function sameOrder(value: Quote | Fill, order: Order): boolean {
  const kind = order.amount_usd === undefined ? "quantity" : "usd";
  const input = order.amount_usd ?? order.quantity;
  // Compare exact decimal strings without binary floating point or renewing a receipt.
  const normalized = (text: string) => {
    const [whole, fraction = ""] = text.split(".");
    return `${whole.replace(/^0+(?=\d)/, "")}.${fraction.replace(/0+$/, "")}`;
  };
  return (
    value.symbol === order.symbol &&
    value.side === order.side &&
    value.input_kind === kind &&
    typeof input === "string" &&
    normalized(value.input_value) === normalized(input)
  );
}

export async function fetchQuote(
  portfolioId: string,
  order: Order,
  signal?: AbortSignal,
): Promise<Quote> {
  signal?.throwIfAborted();
  if (!validOrder(order)) throw new Error("Invalid trade order");
  const body = await apiFetch(`${path(portfolioId)}/trades/quote`, {
    method: "POST",
    body: JSON.stringify(order),
    signal,
    cache: "no-store",
  });
  if (!isQuote(body) || body.portfolio_id !== portfolioId || !sameOrder(body, order)) {
    throw new Error("Unexpected quote response");
  }
  signal?.throwIfAborted();
  return body;
}

export async function executeTrade(
  portfolioId: string,
  order: Order,
  expectedMid: string,
  idempotencyKey: string,
  signal?: AbortSignal,
): Promise<Fill> {
  signal?.throwIfAborted();
  const endpoint = `${path(portfolioId)}/trades`;
  if (
    !validOrder(order) ||
    !isUnsigned(expectedMid) ||
    !/[1-9]/.test(expectedMid) ||
    !isText(idempotencyKey)
  )
    throw new Error("Invalid trade attempt");
  let body: unknown;
  try {
    body = await apiFetch(endpoint, {
      method: "POST",
      body: JSON.stringify({
        ...order,
        expected_mid: expectedMid,
        idempotency_key: idempotencyKey,
      }),
      cache: "no-store",
      signal,
    });
  } catch (error) {
    if (
      error instanceof ApiError &&
      error.code === "price_changed" &&
      (!isQuote(error.detail?.quote) ||
        error.detail.quote.portfolio_id !== portfolioId ||
        !sameOrder(error.detail.quote, order))
    )
      throw new Error("Unexpected trade repricing response", { cause: error });
    throw error;
  }
  if (!isFill(body) || body.portfolio_id !== portfolioId || !sameOrder(body, order)) {
    throw new Error("Unexpected trade response");
  }
  signal?.throwIfAborted();
  return body;
}

export async function fetchHolding(
  portfolioId: string,
  symbol: string,
  signal?: AbortSignal,
): Promise<Holding> {
  signal?.throwIfAborted();
  const body = await apiFetch(`${path(portfolioId)}/holdings/${encodeURIComponent(symbol)}`, {
    signal,
    cache: "no-store",
  });
  if (!isHolding(body) || body.portfolio_id !== portfolioId || body.symbol !== symbol) {
    throw new Error("Unexpected holding response");
  }
  signal?.throwIfAborted();
  return body;
}
