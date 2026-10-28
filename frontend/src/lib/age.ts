import type { PriceStatus } from "@/api/prices";

/** Whole-second age as "42s ago", "7m ago" or "2h ago". Negative values clamp to 0. */
export function formatAge(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds));
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  return `${Math.floor(s / 3600)}h ago`;
}

/** D-03: fresh below freshSeconds, aging up to and including staleSeconds, stale above. */
export function freshnessStatus(
  ageSeconds: number,
  freshSeconds: number,
  staleSeconds: number,
): PriceStatus {
  if (ageSeconds < freshSeconds) return "fresh";
  if (ageSeconds <= staleSeconds) return "aging";
  return "stale";
}

export function statusLabel(status: PriceStatus): "Live" | "Delayed" | "Stale" {
  if (status === "fresh") return "Live";
  if (status === "aging") return "Delayed";
  return "Stale";
}
