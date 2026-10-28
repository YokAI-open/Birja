import { apiFetch } from "./client";

export type Side = "buy" | "sell";

export type Order = {
  symbol: string;
  side: Side;
  amount_usd?: string;
  quantity?: string;
};

export type Quote = {
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
  return isRecord(value) && isText(value.symbol) && isUnsigned(value.quantity);
}

export async function fetchQuote(order: Order, signal?: AbortSignal): Promise<Quote> {
  const body = await apiFetch("/api/v1/trades/quote", {
    method: "POST",
    body: JSON.stringify(order),
    signal,
  });
  if (!isQuote(body)) {
    throw new Error("Unexpected quote response");
  }
  return body;
}

export async function executeTrade(
  order: Order,
  expectedMid: string,
  idempotencyKey: string,
): Promise<Fill> {
  const body = await apiFetch("/api/v1/trades", {
    method: "POST",
    body: JSON.stringify({ ...order, expected_mid: expectedMid, idempotency_key: idempotencyKey }),
  });
  if (!isFill(body)) {
    throw new Error("Unexpected trade response");
  }
  return body;
}

export async function fetchHolding(symbol: string, signal?: AbortSignal): Promise<Holding> {
  const body = await apiFetch(`/api/v1/holdings/${encodeURIComponent(symbol)}`, { signal });
  if (!isHolding(body)) {
    throw new Error("Unexpected holding response");
  }
  return body;
}
