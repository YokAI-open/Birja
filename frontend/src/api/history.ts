import { apiFetch } from "./client";
import { isPortfolioId } from "./portfolios";

export type HistoryItem = {
  id: string;
  created_at: string;
  symbol: string;
  name: string;
  side: "buy" | "sell";
  quantity: string;
  exec_price: string;
  fee: string;
  total: string;
};
export type HistoryPage = { items: HistoryItem[]; next_cursor: string | null };

export type EventHistoryFilters = {
  activity: "all" | "buy" | "sell" | "dividend" | "split";
  asset: "all" | "stock" | "crypto";
};
export const DEFAULT_EVENT_HISTORY_FILTERS: Readonly<EventHistoryFilters> = {
  activity: "all",
  asset: "all",
};

const record = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);
const decimal = (v: unknown): v is string => typeof v === "string" && /^-?\d+(\.\d+)?$/.test(v);
const unsigned = (v: unknown): v is string => decimal(v) && !v.startsWith("-");
const text = (v: unknown): v is string => typeof v === "string" && v.length > 0;
const identifier = (v: unknown): v is string =>
  typeof v === "string" && /^[1-9]\d{0,18}$/.test(v) && BigInt(v) <= 9223372036854775807n;
function timestamp(v: unknown): v is string {
  if (typeof v !== "string" || !/^[1-9]\d{3}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$/.test(v))
    return false;
  const date = new Date(v);
  return Number.isFinite(date.getTime()) && date.toISOString().slice(0, 19) === v.slice(0, 19);
}
function isItem(v: unknown): v is HistoryItem {
  return (
    record(v) &&
    identifier(v.id) &&
    timestamp(v.created_at) &&
    text(v.symbol) &&
    text(v.name) &&
    (v.side === "buy" || v.side === "sell") &&
    unsigned(v.quantity) &&
    unsigned(v.exec_price) &&
    unsigned(v.fee) &&
    decimal(v.total)
  );
}
/** Scope/shape validation only: callers forward the opaque token unchanged, never select a root from it. */
export function isPortfolioHistoryCursor(
  value: unknown,
  kind: "trade" | "mixed",
  expectedPortfolioId?: string,
  filters: EventHistoryFilters = DEFAULT_EVENT_HISTORY_FILTERS,
): value is string {
  if (typeof value !== "string" || value.length > 512 || !/^[A-Za-z0-9_-]+$/.test(value))
    return false;
  try {
    const raw = atob(value.replace(/-/g, "+").replace(/_/g, "/"));
    if (btoa(raw).replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_") !== value) return false;
    const decoded: unknown = JSON.parse(raw);
    if (
      !record(decoded) ||
      JSON.stringify(decoded) !== raw ||
      !isPortfolioId(decoded.portfolio_id) ||
      (expectedPortfolioId !== undefined && decoded.portfolio_id !== expectedPortfolioId)
    )
      return false;
    const filtered = kind === "mixed" && (filters.activity !== "all" || filters.asset !== "all");
    const keys =
      kind === "trade"
        ? ["v", "portfolio_id", "created_at", "id"]
        : ["v", "portfolio_id", "recorded_at", "kind_rank", "source_id"];
    if (filtered) keys.push("activity", "asset");
    if (
      Object.keys(decoded).length !== keys.length ||
      !keys.every((key) => Object.hasOwn(decoded, key))
    )
      return false;
    const stamp = kind === "trade" ? decoded.created_at : decoded.recorded_at;
    if (!timestamp(stamp) || !/\.\d{6}Z$/.test(stamp)) return false;
    return kind === "trade"
      ? decoded.v === 2 && identifier(decoded.id)
      : decoded.v === (filtered ? 4 : 3) &&
          (!filtered ||
            (decoded.activity === filters.activity && decoded.asset === filters.asset)) &&
          [1, 2, 3, 4].includes(decoded.kind_rank as number) &&
          identifier(decoded.source_id);
  } catch {
    return false;
  }
}

export function isHistoryPage(v: unknown, portfolioId?: string): v is HistoryPage {
  return (
    record(v) &&
    Object.keys(v).length === 2 &&
    Array.isArray(v.items) &&
    v.items.length <= 100 &&
    v.items.every(isItem) &&
    new Set(v.items.map((item) => item.id)).size === v.items.length &&
    (v.next_cursor === null || isPortfolioHistoryCursor(v.next_cursor, "trade", portfolioId))
  );
}
export async function fetchHistory(
  portfolioId: string,
  { cursor, limit }: { cursor?: string; limit?: number } = {},
  signal?: AbortSignal,
): Promise<HistoryPage> {
  signal?.throwIfAborted();
  if (!isPortfolioId(portfolioId)) throw new Error("Invalid portfolio target");
  if (
    (cursor !== undefined && !isPortfolioHistoryCursor(cursor, "trade", portfolioId)) ||
    (limit !== undefined && (!Number.isSafeInteger(limit) || limit < 1 || limit > 100))
  )
    throw new Error("Invalid history request");
  const params = new URLSearchParams();
  if (cursor !== undefined) params.set("cursor", cursor);
  if (limit !== undefined) params.set("limit", String(limit));
  const query = params.toString();
  const body = await apiFetch(
    `/api/v2/portfolios/${encodeURIComponent(portfolioId)}/history${query ? `?${query}` : ""}`,
    { signal, cache: "no-store" },
  );
  if (!isHistoryPage(body, portfolioId) || body.items.length > (limit ?? 25))
    throw new Error("Unexpected history response");
  signal?.throwIfAborted();
  return body;
}
