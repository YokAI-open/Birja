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
export type EventDividend = EventBase<"dividend", "stock"> &
  DividendTerms & {
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

const record = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);
const exact = (v: Record<string, unknown>, keys: string) =>
  Object.keys(v).length === keys.split(" ").length &&
  keys.split(" ").every((k) => Object.hasOwn(v, k));
const text = (v: unknown, max: number): v is string =>
  typeof v === "string" &&
  v.trim().length > 0 &&
  v.length <= max &&
  [...v].every((c) => c.charCodeAt(0) >= 32 && c.charCodeAt(0) !== 127);
const id = (v: unknown): v is string =>
  typeof v === "string" && /^[1-9][0-9]{0,18}$/.test(v) && BigInt(v) <= 9223372036854775807n;
const publicId = (v: unknown, kind: string): v is string =>
  typeof v === "string" && v.startsWith(kind + ":") && id(v.slice(kind.length + 1));
function timestamp(v: unknown): v is string {
  if (
    typeof v !== "string" ||
    !/^[1-9][0-9]{3}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$/.test(v)
  )
    return false;
  const d = new Date(v);
  return Number.isFinite(d.getTime()) && d.toISOString().slice(0, 19) === v.slice(0, 19);
}
const instant = (v: string) => {
  const [base, fraction = ""] = v.slice(0, -1).split(".");
  return BigInt(new Date(base + "Z").getTime()) * 1000n + BigInt(fraction.padEnd(6, "0"));
};
const dateOnly = (v: unknown): v is string =>
  typeof v === "string" && /^\d{4}-\d{2}-\d{2}$/.test(v) && timestamp(v + "T00:00:00Z");
const SCALE = 100000000n,
  CENT = 1000000n,
  MAX = 99999999999999999999n;
/** Bounded NUMERIC(20,8) decoding for wire integrity only, never a client credit. */
function fixed(v: unknown, signed = false): bigint | null {
  if (
    typeof v !== "string" ||
    !/^-?(?:0|[1-9][0-9]{0,11})(?:\.[0-9]{1,8})?$/.test(v) ||
    (!signed && v.startsWith("-"))
  )
    return null;
  const negative = v.startsWith("-");
  const [whole, fraction = ""] = (negative ? v.slice(1) : v).split(".");
  const n = BigInt(whole + fraction.padEnd(8, "0"));
  if (n > MAX || (negative && n === 0n)) return null;
  return negative ? -n : n;
}
function cents(v: unknown, signed = false): bigint | null {
  const n = fixed(v, signed);
  return n !== null && n % CENT === 0n ? n : null;
}
function shares(v: unknown): bigint | null {
  const n = fixed(v);
  return n !== null && n % SCALE === 0n ? n / SCALE : null;
}
const baseKeys = "kind id recorded_at asset_type symbol name cash_delta";
const termKeys = "eligible_quantity rate cutoff ex_date record_date payable_date";
function terms(v: Record<string, unknown>): boolean {
  return (
    shares(v.eligible_quantity) !== null &&
    fixed(v.rate) !== null &&
    timestamp(v.cutoff) &&
    (v.ex_date === null || dateOnly(v.ex_date)) &&
    (v.record_date === null || dateOnly(v.record_date)) &&
    dateOnly(v.payable_date)
  );
}
function roundedTarget(v: Record<string, unknown>): bigint {
  const value = shares(v.eligible_quantity)! * fixed(v.rate)!;
  const q = value / CENT,
    r = value % CENT;
  return (q + (r > CENT / 2n || (r === CENT / 2n && q % 2n !== 0n) ? 1n : 0n)) * CENT;
}
function base(v: Record<string, unknown>): boolean {
  return (
    typeof v.kind === "string" &&
    publicId(v.id, v.kind) &&
    timestamp(v.recorded_at) &&
    (v.asset_type === "crypto" || v.asset_type === "stock") &&
    typeof v.symbol === "string" &&
    /^[A-Z][A-Z0-9.-]{0,19}$/.test(v.symbol) &&
    text(v.name, 256) &&
    cents(v.cash_delta, true) !== null
  );
}
function dividend(v: unknown): v is EventDividend {
  if (
    !record(v) ||
    !base(v) ||
    !exact(v, baseKeys + " " + termKeys + " payment_reference credited_amount credited_at") ||
    v.kind !== "dividend" ||
    v.asset_type !== "stock" ||
    !terms(v) ||
    v.payment_reference !== v.id ||
    cents(v.credited_amount) === null ||
    !timestamp(v.credited_at)
  )
    return false;
  return (
    cents(v.cash_delta, true) === cents(v.credited_amount) &&
    roundedTarget(v) === cents(v.credited_amount) &&
    instant(v.cutoff as string) <= instant(v.credited_at) &&
    instant(v.credited_at) <= instant(v.recorded_at as string)
  );
}
function item(v: unknown): v is EventHistoryItem {
  if (!record(v) || !base(v)) return false;
  if (v.kind === "dividend") return dividend(v);
  if (v.kind === "trade") {
    if (
      !exact(v, baseKeys + " side quantity exec_price fee filled_at source feed quote_at") ||
      (v.side !== "buy" && v.side !== "sell") ||
      fixed(v.quantity) === null ||
      fixed(v.quantity)! <= 0n ||
      fixed(v.exec_price) === null ||
      fixed(v.exec_price)! <= 0n ||
      cents(v.fee) === null ||
      !timestamp(v.filled_at)
    )
      return false;
    return (
      instant(v.filled_at) <= instant(v.recorded_at as string) &&
      (v.side === "buy" ? cents(v.cash_delta, true)! < 0n : cents(v.cash_delta, true)! >= 0n) &&
      (v.asset_type === "stock"
        ? shares(v.quantity) !== null &&
          cents(v.fee) === 0n &&
          v.source === "alpaca" &&
          v.feed === "iex" &&
          timestamp(v.quote_at) &&
          instant(v.quote_at) <= instant(v.filled_at)
        : v.source === null && v.feed === null && v.quote_at === null)
    );
  }
  if (v.kind === "split") {
    if (
      !exact(
        v,
        baseKeys +
          " ratio_new ratio_old quantity_before quantity_after cost_basis_before cost_basis_after effective_at",
      ) ||
      v.asset_type !== "stock" ||
      cents(v.cash_delta, true) !== 0n ||
      shares(v.ratio_new) === null ||
      shares(v.ratio_old) === null ||
      shares(v.ratio_old)! <= 0n ||
      shares(v.ratio_new)! <= shares(v.ratio_old)! ||
      shares(v.quantity_before) === null ||
      shares(v.quantity_before)! <= 0n ||
      shares(v.quantity_after) === null ||
      fixed(v.cost_basis_before) === null ||
      fixed(v.cost_basis_after) !== fixed(v.cost_basis_before) ||
      !timestamp(v.effective_at)
    )
      return false;
    return (
      shares(v.quantity_before)! * shares(v.ratio_new)! ===
        shares(v.quantity_after)! * shares(v.ratio_old)! &&
      instant(v.effective_at) <= instant(v.recorded_at as string)
    );
  }
  if (
    v.kind !== "dividend_correction" ||
    v.asset_type !== "stock" ||
    !exact(
      v,
      baseKeys +
        " payment_reference decision_reference outcome reason desired_total cumulative_applied_before proposed_delta applied_delta terms original",
    ) ||
    !dividend(v.original) ||
    v.payment_reference !== v.original.id ||
    v.decision_reference !== v.id ||
    instant(v.original.recorded_at) > instant(v.recorded_at as string) ||
    cents(v.cumulative_applied_before) === null ||
    cents(v.applied_delta, true) === null ||
    cents(v.cash_delta, true) !== cents(v.applied_delta, true)
  )
    return false;
  if (v.outcome === "held_uncertain")
    return (
      v.reason === "terms_unverified" &&
      v.terms === null &&
      v.desired_total === null &&
      v.proposed_delta === null &&
      cents(v.applied_delta, true) === 0n
    );
  if (
    !record(v.terms) ||
    !exact(v.terms, termKeys) ||
    !terms(v.terms) ||
    cents(v.desired_total) === null ||
    cents(v.proposed_delta, true) === null ||
    roundedTarget(v.terms) !== cents(v.desired_total) ||
    cents(v.desired_total)! - cents(v.cumulative_applied_before)! !== cents(v.proposed_delta, true)
  )
    return false;
  if (v.outcome === "applied")
    return (
      v.reason === "target_applied" &&
      cents(v.applied_delta, true) !== 0n &&
      cents(v.applied_delta, true) === cents(v.proposed_delta, true)
    );
  if (v.outcome === "verified_no_change")
    return (
      v.reason === "target_unchanged" &&
      cents(v.proposed_delta, true) === 0n &&
      cents(v.applied_delta, true) === 0n
    );
  return (
    v.outcome === "held_unaffordable" &&
    v.reason === "insufficient_cash" &&
    cents(v.proposed_delta, true)! < 0n &&
    cents(v.applied_delta, true) === 0n
  );
}
function cursorToken(v: unknown): v is string {
  if (typeof v !== "string" || v.length > 512 || !/^[A-Za-z0-9_-]+$/.test(v)) return false;
  try {
    const raw = atob(v.replace(/-/g, "+").replace(/_/g, "/"));
    if (btoa(raw).replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_") !== v) return false;
    const decoded: unknown = JSON.parse(raw);
    return (
      record(decoded) &&
      exact(decoded, "v recorded_at kind_rank source_id") &&
      JSON.stringify(decoded) === raw &&
      decoded.v === 2 &&
      timestamp(decoded.recorded_at) &&
      /^.*\.\d{6}Z$/.test(decoded.recorded_at) &&
      [1, 2, 3, 4].includes(decoded.kind_rank as number) &&
      id(decoded.source_id)
    );
  } catch {
    return false;
  }
}
export function isEventHistoryPage(value: unknown): value is EventHistoryPage {
  return (
    record(value) &&
    exact(value, "items next_cursor") &&
    Array.isArray(value.items) &&
    value.items.length <= 100 &&
    value.items.every(item) &&
    new Set(value.items.map((v) => v.id)).size === value.items.length &&
    (value.next_cursor === null || cursorToken(value.next_cursor))
  );
}

export async function fetchEventHistory(
  { cursor, limit }: { cursor?: string; limit?: number } = {},
  signal?: AbortSignal,
): Promise<EventHistoryPage> {
  signal?.throwIfAborted();
  if (
    (cursor !== undefined && !cursorToken(cursor)) ||
    (limit !== undefined && (!Number.isSafeInteger(limit) || limit < 1 || limit > 100))
  )
    throw new Error("Invalid event history request");
  const params = new URLSearchParams();
  if (cursor !== undefined) params.set("cursor", cursor);
  if (limit !== undefined) params.set("limit", String(limit));
  const query = params.toString();
  const body = await apiFetch(`/api/v1/history${query ? `?${query}` : ""}`, {
    signal,
    cache: "no-store",
  });
  if (!isEventHistoryPage(body)) throw new Error("Unexpected event history response");
  signal?.throwIfAborted();
  return body;
}
