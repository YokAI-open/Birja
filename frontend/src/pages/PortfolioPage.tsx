import { useCallback, useRef } from "react";
import { RefreshCw } from "lucide-react";
import { useLocation, useOutletContext } from "react-router";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { StockAttribution } from "@/components/StockAttribution";
import { usePortfolio } from "@/hooks/usePortfolio";
import { usePortfolioManagement } from "@/hooks/usePortfolioManagement";
import { useNow } from "@/hooks/useNow";
import { PortfolioFreshness } from "@/components/PortfolioFreshness";
import { PortfolioHoldings } from "@/components/PortfolioHoldings";
import { PortfolioAllocation } from "@/components/PortfolioAllocation";
import { formatUsd } from "@/lib/money";
import { formatAge, freshnessStatus, oldestHoldingAge, statusLabel } from "@/lib/age";
import { fullLocalTimestamp, outcome, signedPercent, signedUsd } from "@/lib/financialDisplay";
import type { PortfolioTarget } from "@/hooks/usePortfolioTarget";

export default function PortfolioPage() {
  const target = useOutletContext<PortfolioTarget>();
  const { state } = useLocation();
  const { metadata } = usePortfolioManagement(target.portfolioId);
  const { data, isPending, isError, isFetching, refetch, dataUpdatedAt } = usePortfolio(target);
  const now = useNow();
  const returnDirection = data?.total_pl != null ? outcome(data.total_pl) : "zero";
  const elapsed = Math.max(0, Math.floor((now - dataUpdatedAt) / 1000));
  const refreshButton = useRef<HTMLButtonElement | null>(null);
  const retryButton = useRef<HTMLButtonElement | null>(null);
  const captureRetryButton = useCallback((node: HTMLButtonElement | null) => {
    if (!node && retryButton.current === document.activeElement) {
      refreshButton.current?.focus({ preventScroll: true });
    }
    retryButton.current = node;
  }, []);
  function refresh() {
    if (!isFetching) void refetch({ cancelRefetch: false });
  }
  const oldest = data ? oldestHoldingAge(data.holdings, elapsed) : null;
  const liveStatus =
    data && oldest !== null
      ? freshnessStatus(oldest, data.fresh_seconds, data.stale_seconds)
      : null;
  const historical = data?.holdings.some(
    (holding) =>
      holding.stock_mark?.mark_mode === "closed" || holding.stock_mark?.mark_mode === "halted",
  );
  const freshness = isFetching
    ? "Updating…"
    : isError
      ? "Update failed"
      : !data
        ? "Waiting for data"
        : !data.valuation_complete
          ? "Incomplete"
          : historical
            ? "Dated prices"
            : `${liveStatus ? statusLabel(liveStatus) : "Updated"} · ${formatAge(oldest ?? elapsed)}`;

  return (
    <>
      <div className="flex min-w-0 shrink-0 items-center gap-1.5 sm:gap-3">
        <Button
          ref={refreshButton}
          variant="secondary"
          className="min-h-11 min-w-11 gap-2 px-2.5 aria-disabled:opacity-40 sm:px-4"
          aria-label={isFetching ? "Updating portfolio…" : "Update portfolio"}
          title="Update portfolio"
          aria-disabled={isFetching}
          onClick={refresh}
        >
          <RefreshCw aria-hidden="true" className="size-4" />
          <span className="hidden sm:inline">Update</span>
        </Button>
        <span
          className="max-w-[6ch] text-xs leading-tight text-muted-foreground tabular-nums sm:max-w-none sm:text-sm"
          title={data && fullLocalTimestamp(data.valued_at)}
        >
          {freshness}
        </span>
      </div>
      <div className="col-span-full my-6 flex min-w-0 flex-col gap-7 text-base lg:gap-9">
        {state?.creationResult?.id === target.portfolioId && (
          <p role="status">
            {state.creationResult.replay ? "Original portfolio confirmed." : "Portfolio created."}
          </p>
        )}
        {isPending ? (
          <div
            role="status"
            aria-label="Loading your portfolio"
            aria-busy="true"
            className="grid gap-4 md:grid-cols-2 lg:grid-cols-3"
          >
            {[0, 1].map((i) => (
              <Card key={i} className={i === 0 ? "lg:col-span-2" : ""}>
                <CardContent>
                  <div className="h-4 w-1/2 rounded-control bg-muted" />
                  <div className="h-11 w-full rounded-control bg-muted" />
                  <div className="h-6 w-3/4 rounded-control bg-muted" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : !data ? (
          <Card>
            <CardContent>
              <p role="alert">Can&apos;t load your portfolio right now. Try again.</p>
              <Button ref={captureRetryButton} onClick={refresh} aria-disabled={isFetching}>
                Try again
              </Button>
            </CardContent>
          </Card>
        ) : (
          <>
            {isError && (
              <div
                role="alert"
                className="flex flex-wrap items-center gap-3 rounded-control bg-warn-soft p-4 text-warn-text"
              >
                <p>
                  Couldn&apos;t refresh your portfolio. Only still-permitted values from the last
                  update are shown.
                </p>
                <Button
                  ref={captureRetryButton}
                  variant="secondary"
                  className="aria-disabled:cursor-not-allowed aria-disabled:opacity-40"
                  onClick={refresh}
                  aria-disabled={isFetching}
                >
                  Retry refresh
                </Button>
              </div>
            )}
            {data.holdings.some((h) => h.asset_class === "stock") && (
              <StockAttribution context="valuation" />
            )}
            <Card role="region" aria-label="Total portfolio value">
              {metadata?.description && (
                <p className="line-clamp-2 text-sm whitespace-pre-line text-muted-foreground">
                  {metadata.description}
                </p>
              )}
              <div className="grid min-w-0 gap-7 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] md:items-start md:gap-10">
                <div className="flex min-w-0 flex-col gap-4">
                  <div className="min-w-0">
                    {data.valuation_complete && <p className="sr-only">Total value</p>}
                    <p className="text-4xl leading-tight font-semibold tracking-tight wrap-anywhere tabular-nums md:text-5xl">
                      {data.valuation_complete
                        ? data.total_value === null
                          ? "Unavailable"
                          : formatUsd(data.total_value)
                        : data.known_value === null
                          ? "Value unavailable — refresh required"
                          : `Known value: ${formatUsd(data.known_value)} — incomplete`}
                    </p>
                  </div>
                  <div className="flex flex-wrap items-baseline gap-x-6 gap-y-2 text-base tabular-nums">
                    <div role="region" aria-label="Cash">
                      <span className="font-medium">{formatUsd(data.cash)}</span>{" "}
                      <span className="text-muted-foreground">cash</span>
                    </div>
                    {data.valuation_complete && data.total_pl !== null && (
                      <p
                        className={
                          returnDirection === "gain"
                            ? "text-gain-text"
                            : returnDirection === "loss"
                              ? "text-loss-text"
                              : "text-muted-foreground"
                        }
                      >
                        <span className="sr-only">Return: </span>
                        {signedUsd(data.total_pl)}
                        {data.total_pl_percent === null ? (
                          <span className="sr-only">. Percentage return not applicable.</span>
                        ) : (
                          ` · ${signedPercent(data.total_pl_percent)}`
                        )}
                      </p>
                    )}
                  </div>
                  {!data.valuation_complete && (
                    <p className="text-sm text-warn-text">
                      {data.unvalued_holding_count}{" "}
                      {data.unvalued_holding_count === 1 ? "holding cannot" : "holdings cannot"} be
                      valued. Overall gain/loss and allocation are unavailable.
                    </p>
                  )}
                  <PortfolioFreshness
                    portfolio={data}
                    elapsed={elapsed}
                    dataUpdatedAt={dataUpdatedAt}
                    isFetching={isFetching}
                    isError={isError}
                  />
                  <p className="sr-only">
                    Compared with your {formatUsd(data.starting_cash)} start
                  </p>
                </div>
                <PortfolioAllocation portfolio={data} />
              </div>
            </Card>
            <PortfolioHoldings
              target={target}
              holdings={data.holdings}
              elapsed={elapsed}
              freshSeconds={data.fresh_seconds}
              staleSeconds={data.stale_seconds}
            />
          </>
        )}
      </div>
    </>
  );
}
