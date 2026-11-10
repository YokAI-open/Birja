import { apiFetch } from "./client";

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

const record = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);
const decimal = (v: unknown): v is string => typeof v === "string" && /^-?\d+(\.\d+)?$/.test(v);
const unsigned = (v: unknown): v is string => decimal(v) && !v.startsWith("-");
const text = (v: unknown): v is string => typeof v === "string" && v.length > 0;
const identifier = (v: unknown): v is string =>
  typeof v === "string" && /^[1-9]\d{0,18}$/.test(v) && BigInt(v) <= 9223372036854775807n;
function timestamp(v: unknown): v is string {
  if (typeof v !== "string" || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$/.test(v))
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
export function isHistoryPage(v: unknown): v is HistoryPage {
  return (
    record(v) &&
    Array.isArray(v.items) &&
    v.items.length <= 100 &&
    v.items.every(isItem) &&
    (v.next_cursor === null ||
      (typeof v.next_cursor === "string" &&
        v.next_cursor.length <= 512 &&
        /^[A-Za-z0-9_-]+$/.test(v.next_cursor)))
  );
}
export async function fetchHistory(
  { cursor, limit }: { cursor?: string; limit?: number } = {},
  signal?: AbortSignal,
): Promise<HistoryPage> {
  const params = new URLSearchParams();
  if (cursor !== undefined) params.set("cursor", cursor);
  if (limit !== undefined) params.set("limit", String(limit));
  const query = params.toString();
  const body = await apiFetch(`/api/v1/trades${query ? `?${query}` : ""}`, { signal });
  if (!isHistoryPage(body)) throw new Error("Unexpected history response");
  return body;
}
