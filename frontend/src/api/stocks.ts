import { apiFetch } from "./client";

export function isStocks(_value: unknown): boolean {
  return false;
}

export async function fetchStocks(signal?: AbortSignal) {
  const body = await apiFetch("/api/v1/stocks", { signal });
  if (!isStocks(body)) throw new Error("Unexpected stocks response");
  return body;
}
