import { apiFetch } from "./client";

export type PriceStatus = "fresh" | "aging" | "stale";

export type PriceItem = {
  symbol: string;
  name: string;
  price: string;
  as_of: string;
  age_seconds: number;
  status: PriceStatus;
};

export type Prices = {
  server_time: string;
  fresh_seconds: number;
  stale_seconds: number;
  items: PriceItem[];
};

const STATUSES: readonly string[] = ["fresh", "aging", "stale"];
const DECIMAL = /^\d+(\.\d+)?$/;

const isText = (value: unknown): value is string => typeof value === "string" && value !== "";

function isPriceItem(value: unknown): value is PriceItem {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return false;
  }
  const v = value as Record<string, unknown>;
  return (
    isText(v.symbol) &&
    isText(v.name) &&
    typeof v.price === "string" &&
    DECIMAL.test(v.price) &&
    isText(v.as_of) &&
    Number.isInteger(v.age_seconds) &&
    typeof v.status === "string" &&
    STATUSES.includes(v.status)
  );
}

export function isPrices(value: unknown): value is Prices {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return false;
  }
  const v = value as Record<string, unknown>;
  return (
    isText(v.server_time) &&
    Number.isInteger(v.fresh_seconds) &&
    Number.isInteger(v.stale_seconds) &&
    Array.isArray(v.items) &&
    v.items.every(isPriceItem)
  );
}

export async function fetchPrices(signal?: AbortSignal): Promise<Prices> {
  const body = await apiFetch("/api/v1/prices", { signal });
  if (!isPrices(body)) {
    throw new Error("Unexpected prices response");
  }
  return body;
}
