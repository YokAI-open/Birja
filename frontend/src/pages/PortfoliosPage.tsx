import { useCallback, useLayoutEffect, useRef, useState } from "react";
import { ArrowUpRight, Plus } from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router";
import { Button } from "@/components/ui/button";
import { PortfolioCreateForm } from "@/components/PortfolioCreateForm";
import { PortfolioValueSparkline } from "@/components/PortfolioValueSparkline";
import { usePortfolioOverview } from "@/hooks/usePortfolioOverview";
import { usePortfolioValueHistory } from "@/hooks/usePortfolioValueHistory";
import { usePortfolioManagement } from "@/hooks/usePortfolioManagement";
import { formatUsd } from "@/lib/money";
import { fullLocalTimestamp, outcome, signedPercent, signedUsd } from "@/lib/financialDisplay";
import type { PortfolioOverview } from "@/api/portfolioOverview";
import { usePortfolioDeletion } from "@/hooks/usePortfolioDeletion";
import "./portfolioOverview.css";

function Value({ row }: { row: PortfolioOverview }) {
  return (
    <>
      {row.valuation_complete
        ? row.total_value === null
          ? "Value unavailable — refresh required"
          : formatUsd(row.total_value)
        : row.known_value === null
          ? "Value unavailable — refresh required"
          : `Known value: ${formatUsd(row.known_value)} — incomplete`}
      {!row.valuation_complete && (
        <p className="text-sm">
          {row.unvalued_holding_count} {row.unvalued_holding_count === 1 ? "holding" : "holdings"}{" "}
          cannot be valued.
        </p>
      )}
    </>
  );
}
function Outcome({ row }: { row: PortfolioOverview }) {
  if (!row.valuation_complete || row.total_pl === null) {
    return <span className="text-muted-foreground">Return unavailable</span>;
  }

  const direction = outcome(row.total_pl);
  return (
    <span
      className={
        direction === "gain"
          ? "text-gain-text"
          : direction === "loss"
            ? "text-loss-text"
            : "text-muted-foreground"
      }
    >
      <span className="sr-only">Return: </span>
      {signedUsd(row.total_pl)}
      {row.total_pl_percent !== null && ` · ${signedPercent(row.total_pl_percent)}`}
    </span>
  );
}
export default function PortfoliosPage() {
  const query = usePortfolioOverview();
  const trend = usePortfolioValueHistory(query.membershipUncertain ? undefined : query.data);
  const management = usePortfolioManagement();
  const deletion = usePortfolioDeletion();
  const [open, setOpen] = useState(false);
  const trigger = useRef<HTMLButtonElement>(null);
  const reviewTrigger = useRef<HTMLButtonElement>(null);
  const restoring = useRef(false);
  useLayoutEffect(() => {
    if (!open && restoring.current) {
      restoring.current = false;
      const button = trigger.current;
      (button && !button.disabled ? button : reviewTrigger.current)?.focus();
    }
  }, [open]);
  const navigate = useNavigate();
  const location = useLocation();
  const overviewPath = useRef(window.location.pathname);
  const [acknowledgement] = useState(() => location.state?.deletionConfirmed === true);
  useLayoutEffect(() => {
    if (location.state?.deletionConfirmed === true) {
      void navigate(location.pathname, { replace: true, state: null });
    }
  }, [location, navigate]);
  const created = useCallback(
    (metadata: { id: string }, replay: boolean) => {
      // BrowserRouter updates the URL before React commits the next route.
      // A creation receipt can arrive while this overview is still mounted.
      if (window.location.pathname !== overviewPath.current) return;
      void navigate(`/portfolios/${metadata.id}`, {
        state: { creationResult: { id: metadata.id, replay } },
      });
    },
    [navigate],
  );
  const rows = query.data;
  const capKnown = rows !== undefined && !query.membershipUncertain;
  const limit = capKnown && rows.length >= 10;
  const original =
    management.creation.phase === "unknown" || management.creation.phase === "submitting";
  const refresh = () => {
    if (!query.isFetching) void query.refetch({ cancelRefetch: false });
  };
  const close = () => {
    restoring.current = true;
    setOpen(false);
  };
  return (
    <div className="portfolio-overview flex flex-col gap-7 text-base leading-6 wrap-anywhere md:gap-9">
      <h1 className="sr-only">Portfolios</h1>
      {acknowledgement && <p role="status">Portfolio deleted.</p>}
      {deletion.deletion.attempt && (
        <div className="flex min-w-0 flex-col gap-2 rounded-control bg-warn-soft p-4 text-warn-text">
          <p>
            A portfolio deletion result is unconfirmed. Review the original request to check its
            result.
          </p>
          <Link
            className="flex min-h-11 min-w-11 items-center underline focus-visible:ring-2 focus-visible:ring-ring"
            to="/portfolios/deletion"
          >
            Review deletion request
          </Link>
        </div>
      )}
      {!open && original && (
        <div role="status" className="rounded-control bg-warn-soft p-4 text-warn-text">
          <p>An original creation request is unresolved. Closing creation does not cancel it.</p>
          <Button
            className="mt-2 min-h-11 text-base motion-reduce:transform-none motion-reduce:transition-none"
            variant="secondary"
            ref={reviewTrigger}
            onClick={() => setOpen(true)}
          >
            Review original creation
          </Button>
        </div>
      )}
      {query.isPending ? (
        <div role="status" aria-busy="true">
          <p>Loading portfolios…</p>
          <div aria-hidden="true" className="mt-4 h-24 rounded-card bg-muted" />
        </div>
      ) : !rows ? (
        <div role="alert">
          <p>Can&apos;t load your portfolios right now. Try again.</p>
          <Button
            className="mt-2 min-h-11 text-base motion-reduce:transform-none motion-reduce:transition-none"
            onClick={refresh}
            aria-disabled={query.isFetching}
          >
            Try again
          </Button>
        </div>
      ) : (
        <>
          {!query.isError && (
            <p role="status" aria-live="polite" className="sr-only">
              {query.isFetching ? "Refreshing portfolios…" : "Portfolios updated."}
            </p>
          )}
          {query.isError && (
            <div role="alert" className="rounded-control bg-warn-soft p-4 text-warn-text">
              <p>
                Couldn&apos;t refresh your portfolios. Only still-permitted values from the last
                update are shown.
              </p>
              <Button
                className="mt-2 min-h-11 text-base motion-reduce:transform-none motion-reduce:transition-none"
                variant="secondary"
                onClick={refresh}
                aria-disabled={query.isFetching}
              >
                Retry refresh
              </Button>
            </div>
          )}
          {rows.length === 0 &&
            (query.membershipUncertain ? (
              <p>
                Checking portfolio membership. Review any original deletion request before using an
                unavailable portfolio.
              </p>
            ) : (
              <h2 className="sr-only">No portfolios yet</h2>
            ))}
          <ul aria-label="Portfolios" className="portfolio-overview-grid">
            {rows.map((row) => {
              const points = trend.data?.portfolios.find(
                (series) => series.portfolio_id === row.id,
              )?.points;
              const series =
                trend.data && points
                  ? { start_day: trend.data.start_day, end_day: trend.data.end_day, points }
                  : undefined;
              const trendId = `portfolio-trend-${row.id}`;
              return (
                <li key={row.id} className="min-w-0">
                  <Link
                    to={`/portfolios/${row.id}`}
                    aria-labelledby={`portfolio-card-${row.id}`}
                    aria-describedby={trendId}
                    className="portfolio-overview-card portfolio-overview-link group"
                  >
                    <div className="flex items-start justify-between gap-2.5">
                      <h2 id={`portfolio-card-${row.id}`} className="portfolio-overview-name">
                        {row.name}
                      </h2>
                      <ArrowUpRight
                        aria-hidden="true"
                        className="size-5 shrink-0 text-muted-foreground group-hover:text-foreground group-focus-visible:text-foreground"
                      />
                    </div>
                    {row.description && (
                      <p className="mt-1 line-clamp-2 whitespace-pre-line text-muted-foreground">
                        {row.description}
                      </p>
                    )}
                    <PortfolioValueSparkline
                      id={trendId}
                      series={series}
                      loading={trend.loading || query.membershipUncertain}
                      failed={trend.failed}
                    />
                    <div className="portfolio-overview-amounts tabular-nums">
                      <div className="portfolio-overview-value">
                        <div
                          className={
                            row.valuation_complete && row.total_value !== null
                              ? "portfolio-overview-total"
                              : "font-medium"
                          }
                        >
                          {row.valuation_complete && row.total_value !== null && (
                            <span className="sr-only">Total value: </span>
                          )}
                          <Value row={row} />
                        </div>
                        <Outcome row={row} />
                      </div>
                      <span className="portfolio-overview-cash">{formatUsd(row.cash)} cash</span>
                      {row.prices_as_of &&
                        row.holdings.some(
                          ({ stock_mark }) =>
                            stock_mark?.mark_mode === "closed" ||
                            stock_mark?.mark_mode === "halted",
                        ) && (
                          <p className="mt-2 text-sm text-muted-foreground">
                            Includes dated stock prices
                            <time className="sr-only" dateTime={row.prices_as_of}>
                              {fullLocalTimestamp(row.prices_as_of)}
                            </time>
                          </p>
                        )}
                    </div>
                  </Link>
                </li>
              );
            })}
            <li className="min-w-0">
              <button
                ref={trigger}
                type="button"
                className="portfolio-overview-card portfolio-overview-new"
                disabled={open || limit || (!original && !capKnown)}
                aria-describedby={limit ? "portfolio-cap" : undefined}
                onClick={() => setOpen(true)}
              >
                <span aria-hidden="true" className="portfolio-overview-plus">
                  <Plus className="size-5" />
                </span>
                <span className="portfolio-overview-name">New portfolio</span>
              </button>
            </li>
          </ul>
          {limit && (
            <p id="portfolio-cap">
              You have 10 active portfolios. You can&apos;t create another right now.
            </p>
          )}
          {(trend.failed || trend.retrying) && (
            <div className="flex flex-wrap items-center gap-3">
              {trend.failed && <p role="status">Value history unavailable</p>}
              <Button
                className="min-h-11"
                variant="secondary"
                aria-disabled={trend.retrying}
                onClick={() => {
                  if (!trend.retrying) trend.retry();
                }}
              >
                Retry value history
              </Button>
            </div>
          )}
        </>
      )}
      {open && <PortfolioCreateForm count={rows?.length} onClose={close} onCreated={created} />}
    </div>
  );
}
