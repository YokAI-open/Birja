import { useState } from "react";
import { Link } from "react-router";
import { ArrowDown, ArrowUp, ChevronDown } from "lucide-react";
import { stockFixed } from "@/api/stockTrades";
import type { PortfolioHolding } from "@/api/portfolio";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatAge, freshnessStatus, statusLabel } from "@/lib/age";
import { fullLocalTimestamp, outcome, signedPercent, signedUsd } from "@/lib/financialDisplay";
import { formatQuantity, formatUnitPrice, formatUsd } from "@/lib/money";
import type { PortfolioTarget } from "@/hooks/usePortfolioTarget";

export function PortfolioOutcome({ value, dollars = false }: { value: string; dollars?: boolean }) {
  const state = outcome(value);
  const Icon = state === "loss" ? ArrowDown : ArrowUp;
  return (
    <span
      className={`inline-flex max-w-full flex-wrap items-center gap-1 rounded-control px-2 py-1 wrap-anywhere tabular-nums ${
        state === "zero"
          ? "bg-muted text-foreground"
          : state === "loss"
            ? "bg-loss-soft text-loss-text"
            : "bg-gain-soft text-gain-text"
      }`}
    >
      <span className="sr-only">
        {state === "zero" ? "No change" : state === "loss" ? "Loss" : "Gain"}:{" "}
      </span>
      {state !== "zero" && <Icon aria-hidden="true" className="size-4" />}
      {dollars ? signedUsd(value) : signedPercent(value)}
    </span>
  );
}

function PriceUpdated({
  holding,
  elapsed,
  freshSeconds,
  staleSeconds,
}: {
  holding: PortfolioHolding;
  elapsed: number;
  freshSeconds: number;
  staleSeconds: number;
}) {
  if (holding.as_of === null || holding.age_seconds === null) {
    return (
      <Badge
        variant="neutral"
        className="h-auto whitespace-normal text-[13px] leading-[18px] font-medium"
      >
        Price unavailable
      </Badge>
    );
  }
  const age = holding.age_seconds + elapsed;
  const status = freshnessStatus(age, freshSeconds, staleSeconds);
  const local = fullLocalTimestamp(holding.as_of);
  return (
    <time
      className={status === "fresh" ? "sr-only" : "text-sm text-warn-text"}
      dateTime={holding.as_of}
      title={local}
    >
      {statusLabel(status)} · {formatAge(age)}
    </time>
  );
}

function Return({ holding }: { holding: PortfolioHolding }) {
  const direction = holding.unrealized_pl === null ? "zero" : outcome(holding.unrealized_pl);
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
      {holding.unrealized_pl === null ? "Unavailable" : signedUsd(holding.unrealized_pl)}
      {holding.unrealized_pl_percent !== null &&
        ` · ${signedPercent(holding.unrealized_pl_percent)}`}
      {holding.unrealized_pl_percent === null &&
        holding.mid !== null &&
        outcome(holding.cost_basis) === "zero" && (
          <span className="sr-only">
            Percentage return not applicable because cost basis is zero.
          </span>
        )}
    </span>
  );
}

function Trade({ holding, target }: { holding: PortfolioHolding; target: PortfolioTarget }) {
  return holding.is_active ? (
    <Button asChild variant="secondary" className="min-h-11 min-w-11 px-4">
      <Link
        aria-label={`Trade ${holding.symbol}`}
        to={
          holding.asset_class === "stock"
            ? `/portfolios/${target.portfolioId}/trade/stocks/${encodeURIComponent(holding.symbol)}`
            : `/portfolios/${target.portfolioId}/trade/${encodeURIComponent(holding.symbol)}`
        }
      >
        Trade
      </Link>
    </Button>
  ) : (
    <span>Inactive · trading unavailable</span>
  );
}
function HoldingStatus({
  holding,
  elapsed,
  freshSeconds,
  staleSeconds,
}: {
  holding: PortfolioHolding;
  elapsed: number;
  freshSeconds: number;
  staleSeconds: number;
}) {
  const mark = holding.stock_mark;
  if (mark?.mark_mode === "closed" || mark?.mark_mode === "halted") {
    return (
      <p className="text-sm text-warn-text">
        <span>{mark.mark_mode === "halted" ? "Halted" : "Market closed"}</span>
        {holding.as_of && (
          <>
            {" · Last verified midpoint"}
            {holding.mid !== null && ` ${formatUnitPrice(holding.mid)}`}
            {" · "}
            <time dateTime={holding.as_of} title={fullLocalTimestamp(holding.as_of)}>
              {fullLocalTimestamp(holding.as_of)}
            </time>
          </>
        )}
      </p>
    );
  }
  if (mark?.mark_mode === "unavailable") {
    return (
      <p className="text-sm text-warn-text">
        {mark.valuation_reason === "action_unavailable" || mark.valuation_reason === "units_changed"
          ? "Suspended for corporate-action review. Units and valuation are unavailable."
          : "Stock valuation unavailable. A verified permitted price is required."}
      </p>
    );
  }
  return (
    <PriceUpdated
      holding={holding}
      elapsed={elapsed}
      freshSeconds={freshSeconds}
      staleSeconds={staleSeconds}
    />
  );
}
function compareAmountDescending(first: string | null, second: string | null) {
  const a = stockFixed(first, true);
  const b = stockFixed(second, true);
  if (a === b) return 0;
  if (a === null) return 1;
  if (b === null) return -1;
  return a > b ? -1 : 1;
}

export function PortfolioHoldings({
  target,
  holdings,
  elapsed,
  freshSeconds,
  staleSeconds,
}: {
  target: PortfolioTarget;
  holdings: PortfolioHolding[];
  elapsed: number;
  freshSeconds: number;
  staleSeconds: number;
}) {
  const [filter, setFilter] = useState("all");
  const [sort, setSort] = useState("symbol");
  const results = holdings
    .filter((holding) => filter === "all" || holding.asset_class === filter)
    .sort((a, b) => {
      const byAmount =
        sort === "value"
          ? compareAmountDescending(a.current_value, b.current_value)
          : sort === "return"
            ? compareAmountDescending(a.unrealized_pl, b.unrealized_pl)
            : 0;
      if (byAmount) return byAmount;
      if (a.symbol !== b.symbol) return a.symbol < b.symbol ? -1 : 1;
      return BigInt(a.coin_id) < BigInt(b.coin_id) ? -1 : 1;
    });
  const filterClass =
    "min-h-11 min-w-0 rounded-control border border-input bg-background px-2 text-sm sm:px-3";

  return (
    <section className="flex min-w-0 flex-col gap-5" aria-labelledby="holdings-heading">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 id="holdings-heading" className="text-2xl font-semibold">
          Holdings
        </h2>
        {holdings.length > 0 && (
          <div className="flex min-w-0 flex-wrap items-center gap-2">
            <select
              aria-label="Filter holdings"
              className={filterClass}
              value={filter}
              onChange={(event) => setFilter(event.currentTarget.value)}
            >
              <option value="all">All assets</option>
              <option value="crypto">Crypto</option>
              <option value="stock">Stocks</option>
            </select>
            <select
              aria-label="Sort holdings"
              className={filterClass}
              value={sort}
              onChange={(event) => setSort(event.currentTarget.value)}
            >
              <option value="symbol">Symbol A–Z</option>
              <option value="value">Highest value</option>
              <option value="return">Highest gain</option>
            </select>
          </div>
        )}
      </div>
      {holdings.length === 0 ? (
        <div className="flex flex-col items-start gap-3">
          <h3 className="font-medium">No holdings yet</h3>
          <Button asChild className="min-h-11">
            <Link to="/">Explore Markets</Link>
          </Button>
        </div>
      ) : results.length === 0 ? (
        <p role="status" className="text-muted-foreground">
          No holdings match this filter.
        </p>
      ) : (
        <ul aria-label="Holdings" className="grid min-w-0 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {results.map((h) => (
            <li
              key={h.coin_id}
              className="flex min-w-0 flex-col gap-5 rounded-card border border-border bg-card p-5"
            >
              <div className="flex min-w-0 flex-wrap items-start justify-between gap-x-4 gap-y-2">
                <div className="min-w-0">
                  <h3 className="text-xl leading-tight font-semibold tracking-tight wrap-anywhere">
                    {h.name}
                  </h3>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {h.symbol === h.name ? "" : `${h.symbol} · `}
                    {h.asset_class === "stock" ? "Stock" : "Crypto"}
                  </p>
                </div>
                <p className="text-2xl leading-tight font-medium tracking-tight wrap-anywhere tabular-nums">
                  <span className="sr-only">Current value: </span>
                  <span>
                    {h.current_value === null ? "Unavailable" : formatUsd(h.current_value)}
                  </span>
                </p>
              </div>
              <HoldingStatus
                holding={h}
                elapsed={elapsed}
                freshSeconds={freshSeconds}
                staleSeconds={staleSeconds}
              />
              <div className="mt-auto flex flex-wrap items-end justify-between gap-3 border-t border-border pt-3">
                <div className="min-w-0 space-y-1 text-sm wrap-anywhere tabular-nums">
                  <p className="text-muted-foreground">
                    <span className="sr-only">Quantity: </span>
                    {h.stock_mark && !h.stock_mark.units_safe
                      ? "Quantity unavailable"
                      : `${h.asset_class === "stock" ? h.quantity.split(".")[0] : formatQuantity(h.quantity)} ${h.symbol}`}
                  </p>
                  <p>
                    <span className="sr-only">Gain/loss: </span>
                    <Return holding={h} />
                  </p>
                </div>
                <Trade holding={h} target={target} />
              </div>
              <details className="group">
                <summary className="flex min-h-11 cursor-pointer list-none items-center gap-2 text-sm text-muted-foreground focus-visible:outline-2 focus-visible:outline-ring [&::-webkit-details-marker]:hidden">
                  <ChevronDown aria-hidden="true" className="size-4 group-open:rotate-180" />
                  Cost and price<span className="sr-only"> for {h.symbol}</span>
                </summary>
                <dl className="grid grid-cols-2 gap-3 pt-2 text-sm wrap-anywhere tabular-nums">
                  <div>
                    <dt className="text-muted-foreground">Average cost</dt>
                    <dd>
                      {h.average_cost === null ? "Unavailable" : formatUnitPrice(h.average_cost)}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Cost basis</dt>
                    <dd>{formatUsd(h.cost_basis)}</dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Price used</dt>
                    <dd>{h.mid === null ? "Unavailable" : formatUnitPrice(h.mid)}</dd>
                    {h.mid !== null &&
                      h.as_of &&
                      h.stock_mark?.mark_mode !== "closed" &&
                      h.stock_mark?.mark_mode !== "halted" && (
                        <dd className="text-muted-foreground">
                          <time dateTime={h.as_of}>{fullLocalTimestamp(h.as_of)}</time>
                        </dd>
                      )}
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Allocation</dt>
                    <dd>
                      {h.allocation_percent === null ? "Unavailable" : `${h.allocation_percent}%`}
                    </dd>
                  </div>
                </dl>
              </details>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
