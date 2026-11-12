import type { Side } from "./trades";

export type StockOrder = { symbol: string; side: Side; quantity: string };
export type StockAttempt = StockOrder & { expected_exec_price: string; idempotency_key: string };
export type AdmissionIdentity = {
  product: "reference" | "quotes" | "actions" | "status" | "calendar";
  generation: number; row_hash: string; valid_until: string;
};
export type AuthorityIdentity = {
  admissions: AdmissionIdentity[]; calendar_generation: number; safety_epoch: number;
  unit_epoch: number; status_admission_generation: number; continuity_generation: number;
  status_sequence: number;
};
export type StockEconomics = {
  coin_id: string; provider_asset_id: string; symbol: string; company_name: string;
  listing_exchange: "NYSE" | "NASDAQ"; currency: "USD"; side: Side; quantity: string;
  bid: string; ask: string; exact_mid: string; exec_price: string; source: "alpaca"; feed: "iex";
  event_at: string; collected_at: string; observed_at: string; age_seconds: number;
  notional: string; fee: string; cash_delta: string; cash_before: string; cash_after: string;
  held_before: string; held_after: string; session_date: string;
  session_opens_at: string; session_closes_at: string; authority: AuthorityIdentity;
};
export type StockTradeQuote = StockEconomics & { valid_until: string };
export type StockFill = StockEconomics & { schema_version: 1; trade_id: string; executed_at: string };

export function isStockTradeQuote(_value: unknown): _value is StockTradeQuote { return false; }
export function isStockFill(_value: unknown): _value is StockFill { return false; }
