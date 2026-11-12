import { apiFetch } from "./client";

type EventBase<K extends string, A extends "crypto" | "stock"> = {
  kind: K;
  /** Stable public identity, kind + ':' + canonical source bigint. */
  id: string;
  recorded_at: string;
  asset_type: A;
  symbol: string;
  name: string;
  cash_delta: string;
};
export type EventTrade = EventBase<"trade", "crypto" | "stock"> & {
  side: "buy" | "sell";
  quantity: string;
  exec_price: string;
  fee: string;
  filled_at: string;
  source: "alpaca" | null;
  feed: "iex" | null;
  quote_at: string | null;
};
export type DividendTerms = {
  eligible_quantity: string;
  rate: string;
  cutoff: string;
  ex_date: string | null;
  record_date: string | null;
  payable_date: string;
};
export type EventDividend = EventBase<"dividend", "stock"> & DividendTerms & {
  payment_reference: string;
  credited_amount: string;
  credited_at: string;
};
export type EventSplit = EventBase<"split", "stock"> & {
  ratio_new: string;
  ratio_old: string;
  quantity_before: string;
  quantity_after: string;
  cost_basis_before: string;
  cost_basis_after: string;
  effective_at: string;
};
export type EventDividendCorrection = EventBase<"dividend_correction", "stock"> & {
  payment_reference: string;
  decision_reference: string;
  outcome: "applied" | "held_uncertain" | "held_unaffordable" | "verified_no_change";
  reason: "target_applied" | "terms_unverified" | "insufficient_cash" | "target_unchanged";
  desired_total: string | null;
  cumulative_applied_before: string;
  proposed_delta: string | null;
  applied_delta: string;
  /** Null means no current verified terms; never a fabricated zero entitlement. */
  terms: DividendTerms | null;
  /** Bounded, owner-filtered immutable original, including when outside this page. */
  original: EventDividend;
};
export type EventHistoryItem = EventTrade | EventDividend | EventSplit | EventDividendCorrection;
export type EventHistoryPage = { items: EventHistoryItem[]; next_cursor: string | null };

export function isEventHistoryPage(_value: unknown): _value is EventHistoryPage {
  return false;
}

export async function fetchEventHistory(
  { cursor, limit }: { cursor?: string; limit?: number } = {},
  signal?: AbortSignal,
): Promise<EventHistoryPage> {
  const params = new URLSearchParams();
  if (cursor !== undefined) params.set("cursor", cursor);
  if (limit !== undefined) params.set("limit", String(limit));
  const query = params.toString();
  const body = await apiFetch(`/api/v1/history${query ? `?${query}` : ""}`, {
    signal,
    cache: "no-store",
  });
  if (!isEventHistoryPage(body)) throw new Error("Unexpected event history response");
  return body;
}
