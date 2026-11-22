import { apiFetch } from "./client";
import { isPortfolio, type Portfolio } from "./portfolio";
import { parsePortfolioMetadata } from "./portfolioManagement";
import { stockExact, stockRecord } from "./stockTrades";
import { stockInstant } from "./stocks";

export type PortfolioOverview = Omit<Portfolio, "portfolio_id"> & {
  id: string;
  description: string;
};

export function parsePortfolioOverview(value: unknown): readonly PortfolioOverview[] {
  const invalid = (): never => {
    throw new Error("Unexpected portfolio overview");
  };
  if (!Array.isArray(value) || value.length > 10) return invalid();
  let previous = 0n;
  let valuedAt: bigint | undefined;
  const result = value.map((entry: unknown) => {
    if (
      !stockRecord(entry) ||
      !stockExact(
        entry,
        "id name description cash starting_cash total_value total_pl total_pl_percent cash_allocation_percent valuation_complete known_value unvalued_holding_count class_values class_allocation_percent valued_at prices_as_of fresh_seconds stale_seconds holdings",
      )
    )
      return invalid();
    const { id, description, ...statement } = entry;
    try {
      parsePortfolioMetadata({ id, name: entry.name, description });
    } catch {
      return invalid();
    }
    // The exact-key check precedes adaptation: callers cannot inject/override a
    // second root. All financial/holding/mark guards remain the detail parser's.
    const detail = { ...statement, portfolio_id: id };
    if (!isPortfolio(detail) || BigInt(detail.portfolio_id) <= previous) return invalid();
    previous = BigInt(detail.portfolio_id);
    const instant = stockInstant(detail.valued_at);
    if (valuedAt !== undefined && instant !== valuedAt) return invalid();
    valuedAt = instant;
    let oldest: string | null = null;
    for (const holding of detail.holdings) {
      if (
        holding.as_of !== null &&
        (oldest === null || stockInstant(holding.as_of) < stockInstant(oldest))
      )
        oldest = holding.as_of;
    }
    if (
      (oldest === null) !== (detail.prices_as_of === null) ||
      (oldest !== null &&
        detail.prices_as_of !== null &&
        stockInstant(oldest) !== stockInstant(detail.prices_as_of))
    )
      return invalid();
    // Preserve original monetary strings and proof times. Expiry suppression is
    // the existing projection hook's responsibility, never a renewed timestamp.
    return Object.freeze({ ...statement, id, description }) as PortfolioOverview;
  });
  return Object.freeze(result);
}

export async function fetchPortfolioOverview(
  signal?: AbortSignal,
): Promise<readonly PortfolioOverview[]> {
  signal?.throwIfAborted();
  const value = await apiFetch("/api/v2/portfolios/overview", {
    signal,
    cache: "no-store",
    credentials: "same-origin",
  });
  signal?.throwIfAborted();
  return parsePortfolioOverview(value);
}
