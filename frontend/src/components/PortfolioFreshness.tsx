import { useState } from "react";
import type { Portfolio } from "@/api/portfolio";
import { freshnessStatus, oldestHoldingAge, statusLabel } from "@/lib/age";

export function PortfolioFreshness({
  portfolio,
  elapsed,
  dataUpdatedAt,
  isFetching,
  isError,
}: {
  portfolio: Portfolio;
  elapsed: number;
  dataUpdatedAt: number;
  isFetching: boolean;
  isError: boolean;
}) {
  const [firstUpdate] = useState(dataUpdatedAt);
  const historical = portfolio.holdings.some(
    (h) => h.stock_mark?.mark_mode === "closed" || h.stock_mark?.mark_mode === "halted",
  );
  const oldest = oldestHoldingAge(portfolio.holdings, elapsed);
  const status =
    oldest === null
      ? null
      : freshnessStatus(oldest, portfolio.fresh_seconds, portfolio.stale_seconds);
  const incomplete = !portfolio.valuation_complete;
  const warning = incomplete
    ? "Some holdings cannot be valued. Overall profit/loss and allocation are unavailable until a verified update."
    : status === "stale"
      ? "Some prices are out of date. Values use the last known prices."
      : status === "aging"
        ? "Some prices are delayed. Values use the last known prices."
        : null;
  const state = incomplete
    ? "Valuation incomplete"
    : historical
      ? "Values include dated stock marks"
      : status
        ? statusLabel(status)
        : "No market prices needed";
  // Only semantic state and request transitions enter the live region. Ages and
  // full timestamps below remain readable without announcing each display tick.
  const announcement = isFetching
    ? "Refreshing portfolio…"
    : `${!isError && dataUpdatedAt !== firstUpdate ? "Portfolio refreshed. " : ""}${state}. ${warning ?? ""}`;
  return (
    <>
      <span role="status" aria-live="polite" aria-atomic="true" className="sr-only">
        {announcement}
      </span>
      {warning && !incomplete && <p className="text-sm text-warn-text">{warning}</p>}
    </>
  );
}
