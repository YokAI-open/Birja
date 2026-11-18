import { useCallback, useLayoutEffect, useRef, useState, useSyncExternalStore } from "react";
import { Link, useNavigate } from "react-router";
import { Button } from "@/components/ui/button";
import { PortfolioCreateForm } from "@/components/PortfolioCreateForm";
import { PortfolioOutcome } from "@/components/PortfolioHoldings";
import { usePortfolioOverview } from "@/hooks/usePortfolioOverview";
import { usePortfolioManagement } from "@/hooks/usePortfolioManagement";
import { formatUsd } from "@/lib/money";
import type { PortfolioOverview } from "@/api/portfolioOverview";
import { fullLocalTimestamp } from "@/lib/financialDisplay";
const subscribe = (notify: () => void) => {
  const media = window.matchMedia?.("(min-width: 768px)");
  media?.addEventListener("change", notify);
  return () => media?.removeEventListener("change", notify);
};
const wide = () => window.matchMedia?.("(min-width: 768px)").matches ?? false;
function Times({ row }: { row: PortfolioOverview }) {
  const timestamp = fullLocalTimestamp;
  return (
    <div className="flex flex-col gap-1 text-sm text-muted-foreground tabular-nums">
      <p>Starting cash: {formatUsd(row.starting_cash)}</p>
      <p>
        Calculated at <time dateTime={row.valued_at}>{timestamp(row.valued_at)}</time>
      </p>
      {row.holdings.some(
        (holding) =>
          holding.stock_mark?.mark_mode === "closed" || holding.stock_mark?.mark_mode === "halted",
      ) && <p>Values include dated stock marks.</p>}
      <p>
        {row.prices_as_of ? (
          <>
            Oldest source <time dateTime={row.prices_as_of}>{timestamp(row.prices_as_of)}</time>
          </>
        ) : (
          "No market prices needed."
        )}
      </p>
    </div>
  );
}
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
        <p className="text-sm">{row.unvalued_holding_count} holdings cannot be valued.</p>
      )}
    </>
  );
}
function Outcome({ row }: { row: PortfolioOverview }) {
  return !row.valuation_complete || row.total_pl === null ? (
    <span>Return unavailable</span>
  ) : (
    <div className="flex flex-wrap gap-2">
      <PortfolioOutcome value={row.total_pl} dollars />
      {row.total_pl_percent === null ? (
        <span>Not applicable</span>
      ) : (
        <PortfolioOutcome value={row.total_pl_percent} />
      )}
    </div>
  );
}
export default function PortfoliosPage() {
  const query = usePortfolioOverview();
  const management = usePortfolioManagement();
  const [open, setOpen] = useState(false);
  const trigger = useRef<HTMLButtonElement>(null);
  const restoring = useRef(false);
  useLayoutEffect(() => {
    if (!open && restoring.current) {
      restoring.current = false;
      trigger.current?.focus();
    }
  }, [open]);
  const desktop = useSyncExternalStore(subscribe, wide, () => false);
  const navigate = useNavigate();
  const created = useCallback(
    (metadata: { id: string }, replay: boolean) =>
      navigate(`/portfolios/${metadata.id}`, {
        state: { creationResult: { id: metadata.id, replay } },
      }),
    [navigate],
  );
  const rows = query.data;
  const capKnown = rows !== undefined;
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
    <div className="my-8 flex min-w-0 max-w-[1440px] flex-col gap-4 text-base leading-6 wrap-anywhere">
      <div className="flex min-w-0 flex-col justify-between gap-4 md:flex-row md:flex-wrap md:items-center">
        <div>
          <h1 className="text-[32px] leading-10 font-medium">Portfolios</h1>
          {rows && <p className="text-sm tabular-nums">{rows.length} of 10 active portfolios</p>}
        </div>
        <div className="flex flex-col gap-2 min-[375px]:flex-row min-[375px]:flex-wrap">
          <Button
            variant="secondary"
            className="min-h-11 text-base motion-reduce:transform-none motion-reduce:transition-none"
            aria-disabled={query.isFetching}
            onClick={refresh}
          >
            {query.isFetching ? "Refreshing portfolios…" : "Refresh portfolios"}
          </Button>
          <Button
            ref={trigger}
            className="min-h-11 text-base motion-reduce:transform-none motion-reduce:transition-none"
            disabled={open || (!original && (!capKnown || limit))}
            aria-describedby={limit ? "portfolio-cap" : undefined}
            onClick={() => setOpen(true)}
          >
            Create portfolio
          </Button>
        </div>
      </div>
      <p>
        Compare each portfolio with its own starting cash. Returns are since each portfolio began.
      </p>
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
            onClick={() => setOpen(true)}
          >
            Review original creation
          </Button>
        </div>
      )}
      {open && <PortfolioCreateForm count={rows?.length} onClose={close} onCreated={created} />}
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
          {rows.length === 0 ? (
            <div className="rounded-card bg-card p-4 md:p-6">
              <h2 className="text-xl font-medium">No portfolios yet</h2>
              <p>
                Create a portfolio to start an independent strategy with $10,000.00 in virtual cash.
              </p>
            </div>
          ) : desktop ? (
            <table className="w-full table-fixed rounded-card bg-card text-left">
              <caption className="sr-only">
                Your independent portfolios in ascending ID order
              </caption>
              <thead>
                <tr>
                  {["Portfolio", "Cash", "Total / known value", "Return", "Open"].map((label) => (
                    <th key={label} scope="col" className="p-3 text-sm font-medium">
                      {label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.id} className="min-h-[52px] border-t border-border align-top">
                    <td className="p-3">
                      <Link
                        className="flex min-h-11 items-center text-xl font-medium underline"
                        to={`/portfolios/${row.id}`}
                      >
                        {row.name}
                      </Link>
                      <p className="mb-3 whitespace-pre-wrap">
                        {row.description || "No description."}
                      </p>
                      <Times row={row} />
                    </td>
                    <td className="p-3 tabular-nums">{formatUsd(row.cash)}</td>
                    <td className="p-3 tabular-nums">
                      <Value row={row} />
                    </td>
                    <td className="p-3 tabular-nums">
                      <Outcome row={row} />
                    </td>
                    <td className="p-3">
                      <Link
                        className="flex min-h-11 items-center underline"
                        to={`/portfolios/${row.id}`}
                      >
                        Open portfolio
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <ul className="grid min-w-0 gap-3">
              {rows.map((row) => (
                <li key={row.id} className="flex min-w-0 flex-col gap-3 rounded-card bg-card p-4">
                  <h2 className="text-xl leading-7 font-medium">
                    <Link
                      className="flex min-h-11 items-center underline"
                      to={`/portfolios/${row.id}`}
                    >
                      {row.name}
                    </Link>
                  </h2>
                  <p className="whitespace-pre-wrap">{row.description || "No description."}</p>
                  <dl className="flex min-w-0 flex-col gap-3 tabular-nums">
                    <div>
                      <dt className="text-sm">Cash</dt>
                      <dd>{formatUsd(row.cash)}</dd>
                    </div>
                    <div>
                      <dt className="text-sm">Total / known value</dt>
                      <dd className="text-xl leading-7 font-medium">
                        <Value row={row} />
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm">Return</dt>
                      <dd>
                        <Outcome row={row} />
                      </dd>
                    </div>
                  </dl>
                  <Times row={row} />
                  <Link
                    className="flex min-h-11 items-center underline"
                    to={`/portfolios/${row.id}`}
                  >
                    Open portfolio
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </div>
  );
}
