import { useCallback, useContext, useId, useRef } from "react";
import { createPortal } from "react-dom";
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
import { PortfolioToolbarSlot } from "@/components/PortfolioToolbarSlot";
import { formatUsd } from "@/lib/money";
import { formatAge, freshnessStatus, oldestHoldingAge, statusLabel } from "@/lib/age";
import { fullLocalTimestamp, outcome, signedPercent, signedUsd } from "@/lib/financialDisplay";
import type { PortfolioTarget } from "@/hooks/usePortfolioTarget";
import "./portfolioWorkspace.css";

export default function PortfolioPage() {
  const target = useOutletContext<PortfolioTarget>();
  const toolbarSlot = useContext(PortfolioToolbarSlot);
  const freshnessId = useId();
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
            : liveStatus && liveStatus !== "fresh"
              ? `${statusLabel(liveStatus)} · ${formatAge(oldest ?? elapsed)}`
              : formatAge(oldest ?? elapsed);

  const refreshControl = (
    <Button
      ref={refreshButton}
      variant="secondary"
      className="min-h-11 min-w-11 flex-wrap gap-x-2 rounded-pill px-4 aria-disabled:opacity-40"
      aria-label={isFetching ? "Updating portfolio…" : "Update portfolio"}
      aria-describedby={freshnessId}
      aria-disabled={isFetching}
      onClick={refresh}
    >
      Update
      <span id={freshnessId} className="text-xs font-normal text-muted-foreground tabular-nums">
        {data ? (
          <time dateTime={data.valued_at} title={fullLocalTimestamp(data.valued_at)}>
            {freshness}
          </time>
        ) : (
          freshness
        )}
      </span>
    </Button>
  );

  return (
    <>
      {toolbarSlot === undefined
        ? refreshControl
        : toolbarSlot && createPortal(refreshControl, toolbarSlot)}
      <div className="portfolio-workspace-content">
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
            <section className="portfolio-summary-panel" aria-label="Total portfolio value">
              <div className="flex min-w-0 flex-col gap-1">
                {data.valuation_complete && <p className="text-muted-foreground">Total value</p>}
                <p className="portfolio-summary-value wrap-anywhere tabular-nums">
                  {data.valuation_complete
                    ? data.total_value === null
                      ? "Unavailable"
                      : formatUsd(data.total_value)
                    : data.known_value === null
                      ? "Value unavailable — refresh required"
                      : `Known value: ${formatUsd(data.known_value)} — incomplete`}
                </p>
                {data.valuation_complete && data.total_pl !== null && (
                  <p
                    className={`wrap-anywhere tabular-nums ${
                      returnDirection === "gain"
                        ? "text-gain-text"
                        : returnDirection === "loss"
                          ? "text-loss-text"
                          : "text-muted-foreground"
                    }`}
                  >
                    <span className="sr-only">Return: </span>
                    {signedUsd(data.total_pl)}
                    {data.total_pl_percent === null ? (
                      <span className="sr-only">. Percentage return not applicable.</span>
                    ) : (
                      ` (${signedPercent(data.total_pl_percent)})`
                    )}{" "}
                    <span className="text-muted-foreground">all time</span>
                  </p>
                )}
                {!data.valuation_complete && (
                  <p className="text-sm text-warn-text">
                    {data.unvalued_holding_count}{" "}
                    {data.unvalued_holding_count === 1 ? "holding cannot" : "holdings cannot"} be
                    valued. Overall gain/loss and allocation are unavailable.
                  </p>
                )}
                {metadata?.description && (
                  <p className="line-clamp-2 text-sm wrap-anywhere whitespace-pre-line text-muted-foreground">
                    {metadata.description}
                  </p>
                )}
                <PortfolioFreshness
                  portfolio={data}
                  elapsed={elapsed}
                  dataUpdatedAt={dataUpdatedAt}
                  isFetching={isFetching}
                  isError={isError}
                />
                <p className="sr-only">Compared with your {formatUsd(data.starting_cash)} start</p>
              </div>
              <PortfolioAllocation portfolio={data} />
            </section>
            <PortfolioHoldings
              target={target}
              holdings={data.holdings}
              elapsed={elapsed}
              freshSeconds={data.fresh_seconds}
              staleSeconds={data.stale_seconds}
            />
            {data.holdings.some((h) => h.asset_class === "stock") && (
              <StockAttribution context="valuation" />
            )}
          </>
        )}
      </div>
    </>
  );
}
