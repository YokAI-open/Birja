import { useCallback, useLayoutEffect, useRef, useState } from "react";
import { ArrowRight } from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router";
import { Button } from "@/components/ui/button";
import { PortfolioCreateForm } from "@/components/PortfolioCreateForm";
import { usePortfolioOverview } from "@/hooks/usePortfolioOverview";
import { usePortfolioManagement } from "@/hooks/usePortfolioManagement";
import { formatUsd } from "@/lib/money";
import { fullLocalTimestamp, outcome, signedPercent, signedUsd } from "@/lib/financialDisplay";
import type { PortfolioOverview } from "@/api/portfolioOverview";
import { usePortfolioDeletion } from "@/hooks/usePortfolioDeletion";

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
  const management = usePortfolioManagement();
  const deletion = usePortfolioDeletion();
  const [open, setOpen] = useState(false);
  const trigger = useRef<HTMLButtonElement>(null);
  const reviewTrigger = useRef<HTMLButtonElement>(null);
  const restoring = useRef(false);
  useLayoutEffect(() => {
    if (!open && restoring.current) {
      restoring.current = false;
      (trigger.current ?? reviewTrigger.current)?.focus();
    }
  }, [open]);
  const navigate = useNavigate();
  const location = useLocation();
  const [acknowledgement] = useState(() => location.state?.deletionConfirmed === true);
  useLayoutEffect(() => {
    if (location.state?.deletionConfirmed === true) {
      void navigate(location.pathname, { replace: true, state: null });
    }
  }, [location, navigate]);
  const created = useCallback(
    (metadata: { id: string }, replay: boolean) =>
      navigate(`/portfolios/${metadata.id}`, {
        state: { creationResult: { id: metadata.id, replay } },
      }),
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
    <div className="app-page flex flex-col gap-7 md:gap-9 text-base leading-6 wrap-anywhere">
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
      {limit && (
        <p id="portfolio-cap">
          You have 10 active portfolios. You can&apos;t create another right now.
        </p>
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
          <ul
            aria-label="Portfolios"
            className="grid min-w-0 auto-rows-[minmax(13rem,auto)] grid-cols-1 gap-4 md:grid-cols-2 lg:auto-rows-[minmax(15rem,auto)] lg:gap-6"
          >
            {rows.map((row) => (
              <li key={row.id} className="min-w-0">
                <Link
                  to={`/portfolios/${row.id}`}
                  aria-labelledby={`portfolio-card-${row.id}`}
                  className="group flex h-full min-w-0 flex-col gap-6 rounded-card border border-border bg-card p-5 hover:border-ring/50 lg:p-7"
                >
                  <div>
                    <div className="flex items-start justify-between gap-3">
                      <h2
                        id={`portfolio-card-${row.id}`}
                        className="min-w-0 text-[26px] leading-tight font-semibold tracking-tight lg:text-[32px]"
                      >
                        {row.name}
                      </h2>
                      <ArrowRight
                        aria-hidden="true"
                        className="mt-1 size-5 shrink-0 text-muted-foreground group-focus-visible:text-ring group-hover:text-ring"
                      />
                    </div>
                    {row.description && (
                      <p className="mt-2 line-clamp-2 text-sm whitespace-pre-line text-muted-foreground">
                        {row.description}
                      </p>
                    )}
                  </div>
                  <div className="mt-auto border-t border-border pt-4 tabular-nums">
                    <div
                      className={
                        row.valuation_complete && row.total_value !== null
                          ? "text-[30px] leading-tight font-medium tracking-tight lg:text-[38px]"
                          : "font-medium"
                      }
                    >
                      {row.valuation_complete && row.total_value !== null && (
                        <span className="sr-only">Total value: </span>
                      )}
                      <div>
                        <Value row={row} />
                      </div>
                    </div>
                    <div className="mt-2 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 text-sm">
                      <span className="text-muted-foreground">
                        <span>{formatUsd(row.cash)}</span> cash
                      </span>
                      <Outcome row={row} />
                    </div>
                    {row.prices_as_of &&
                      row.holdings.some(
                        ({ stock_mark }) =>
                          stock_mark?.mark_mode === "closed" || stock_mark?.mark_mode === "halted",
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
            ))}
            <li className="min-w-0">
              <button
                ref={trigger}
                type="button"
                className="flex h-full w-full items-center justify-center rounded-card border border-border bg-accent/60 p-6 text-xl font-semibold text-ring enabled:cursor-pointer enabled:hover:border-ring/50 enabled:hover:bg-accent disabled:opacity-50 lg:text-2xl"
                disabled={open || (!original && (!capKnown || limit))}
                aria-describedby={limit ? "portfolio-cap" : undefined}
                onClick={() => setOpen(true)}
              >
                New portfolio
              </button>
            </li>
          </ul>
        </>
      )}
      {open && <PortfolioCreateForm count={rows?.length} onClose={close} onCreated={created} />}
    </div>
  );
}
