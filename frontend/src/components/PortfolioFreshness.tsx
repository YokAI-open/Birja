import { useState } from "react";
import type { Portfolio } from "@/api/portfolio";
import { formatAge, freshnessStatus, statusLabel } from "@/lib/age";
import { fullLocalTimestamp } from "@/lib/financialDisplay";

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
  const ages = portfolio.holdings.flatMap((h) =>
    h.age_seconds === null ? [] : [h.age_seconds + elapsed],
  );
  const oldest = ages.length ? Math.max(...ages) : null;
  const status =
    oldest === null
      ? null
      : freshnessStatus(oldest, portfolio.fresh_seconds, portfolio.stale_seconds);
  const incomplete = !portfolio.valuation_complete;
  const warning = incomplete
    ? "Some holdings have no price. Total value, profit/loss and allocation are unavailable until prices return."
    : status === "stale"
      ? "Some prices are out of date. Values use the last known prices."
      : status === "aging"
        ? "Some prices are delayed. Values use the last known prices."
        : null;
  const state = incomplete
    ? "Valuation incomplete"
    : status
      ? statusLabel(status)
      : "No market prices needed";
  // Only semantic state and request transitions enter the live region. Ages and
  // full timestamps below remain readable without announcing each display tick.
  const announcement = isFetching
    ? "Refreshing portfolio…"
    : `${!isError && dataUpdatedAt !== firstUpdate ? "Portfolio refreshed. " : ""}${state}. ${warning ?? ""}`;
  return (
    <div className="flex flex-col gap-2 text-[13px] leading-[18px] font-medium">
      <span role="status" aria-live="polite" aria-atomic="true" className="sr-only">
        {announcement}
      </span>
      {warning && <p className="rounded-control bg-warn-soft p-4 text-warn-text">{warning}</p>}
      <p>
        {incomplete
          ? "Valuation incomplete"
          : status
            ? "Values use market mid prices."
            : "No market prices needed"}
      </p>
      {oldest !== null && (
        <p className="wrap-anywhere">
          {incomplete
            ? "Oldest available price"
            : status === "fresh"
              ? "Oldest price"
              : "Last-known valuation · oldest price"}{" "}
          {formatAge(oldest)}
          {portfolio.prices_as_of !== null && (
            <>
              {" "}
              ·{" "}
              <time
                dateTime={portfolio.prices_as_of}
                title={portfolio.prices_as_of}
                aria-label={fullLocalTimestamp(portfolio.prices_as_of)}
              >
                {fullLocalTimestamp(portfolio.prices_as_of)}
              </time>
            </>
          )}
        </p>
      )}
      <p className="wrap-anywhere">
        Calculated at{" "}
        <time
          dateTime={portfolio.valued_at}
          title={portfolio.valued_at}
          aria-label={fullLocalTimestamp(portfolio.valued_at)}
        >
          {fullLocalTimestamp(portfolio.valued_at)}
        </time>
      </p>
    </div>
  );
}
