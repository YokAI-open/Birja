import type { ReactNode } from "react";
import { Link } from "react-router";
import { ArrowDown, ArrowUp } from "lucide-react";
import type { PortfolioHolding } from "@/api/portfolio";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { formatAge, freshnessStatus, statusLabel } from "@/lib/age";
import { fullLocalTimestamp, outcome, signedPercent, signedUsd } from "@/lib/financialDisplay";
import { formatQuantity, formatUnitPrice, formatUsd } from "@/lib/money";

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
    <div className="flex flex-col items-start gap-1 text-[13px] leading-[18px] font-medium">
      <Badge
        variant={status === "fresh" ? "success" : status === "aging" ? "warning" : "danger"}
        className="h-auto whitespace-normal text-[13px] leading-[18px] font-medium"
      >
        {statusLabel(status)} · {formatAge(age)}
      </Badge>
      <time
        dateTime={holding.as_of}
        title={holding.as_of}
        aria-label={local}
        className="wrap-anywhere"
      >
        {local}
      </time>
    </div>
  );
}

function Return({ holding }: { holding: PortfolioHolding }) {
  return (
    <div className="flex flex-col items-start gap-1">
      {holding.unrealized_pl === null ? (
        "Unavailable"
      ) : (
        <PortfolioOutcome value={holding.unrealized_pl} dollars />
      )}
      {holding.unrealized_pl_percent === null ? (
        holding.mid !== null && outcome(holding.cost_basis) === "zero" ? (
          <>
            <span>Not applicable</span>
            <span className="text-[13px] leading-[18px] font-medium text-muted-foreground">
              Percentage return is unavailable because cost basis is zero.
            </span>
          </>
        ) : (
          <span>Unavailable</span>
        )
      ) : (
        <PortfolioOutcome value={holding.unrealized_pl_percent} />
      )}
    </div>
  );
}

function Trade({ holding }: { holding: PortfolioHolding }) {
  return holding.is_active ? (
    <Button asChild variant="secondary" className="min-h-11 min-w-11">
      <Link
        to={
          holding.asset_class === "stock"
            ? `/trade/stocks/${encodeURIComponent(holding.symbol)}`
            : `/trade/${encodeURIComponent(holding.symbol)}`
        }
      >
        Trade {holding.symbol}
      </Link>
    </Button>
  ) : (
    <span>Inactive · trading unavailable</span>
  );
}
function Asset({
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
  const m = holding.stock_mark;
  const historical = m?.mark_mode === "closed" || m?.mark_mode === "halted";
  return (
    <div className="flex min-w-0 flex-col items-start gap-2 wrap-anywhere">
      <span className="font-medium">{holding.symbol}</span>
      <span>{holding.name}</span>
      <Badge variant="neutral">{holding.asset_class === "stock" ? "Stock" : "Crypto"}</Badge>
      {holding.mid !== null && (
        <span>
          {holding.asset_class === "stock" ? "IEX midpoint" : "Mid price"}:{" "}
          {formatUnitPrice(holding.mid)}
        </span>
      )}
      {historical ? (
        <>
          <Badge variant="warning">{m.mark_mode === "halted" ? "Halted" : "Market closed"}</Badge>
          <span>
            Last verified midpoint ·{" "}
            <time dateTime={holding.as_of!} title={holding.as_of!}>
              {fullLocalTimestamp(holding.as_of!)}
            </time>
          </span>
        </>
      ) : (
        <PriceUpdated
          holding={holding}
          elapsed={elapsed}
          freshSeconds={freshSeconds}
          staleSeconds={staleSeconds}
        />
      )}
      {m?.mark_mode === "unavailable" && (
        <span>
          {m.valuation_reason === "action_unavailable" || m.valuation_reason === "units_changed"
            ? "Suspended for corporate-action review. Units and valuation are unavailable."
            : "Stock valuation unavailable. A verified permitted price is required."}
        </span>
      )}
      <Trade holding={holding} />
    </div>
  );
}
const columns = [
  "Asset",
  "Quantity",
  "Average cost",
  "Cost basis",
  "Current value",
  "Gain/loss",
  "Allocation",
];
export function PortfolioHoldings({
  holdings,
  elapsed,
  freshSeconds,
  staleSeconds,
}: {
  holdings: PortfolioHolding[];
  elapsed: number;
  freshSeconds: number;
  staleSeconds: number;
}) {
  const sorted = [...holdings].sort((a, b) =>
    a.symbol < b.symbol
      ? -1
      : a.symbol > b.symbol
        ? 1
        : BigInt(a.coin_id) < BigInt(b.coin_id)
          ? -1
          : 1,
  );
  function fields(h: PortfolioHolding): ReactNode[] {
    return [
      h.stock_mark && !h.stock_mark.units_safe
        ? "Unavailable"
        : h.asset_class === "stock"
          ? h.quantity.split(".")[0]
          : formatQuantity(h.quantity),
      h.average_cost === null ? "Unavailable" : formatUnitPrice(h.average_cost),
      formatUsd(h.cost_basis),
      h.current_value === null ? "Unavailable" : formatUsd(h.current_value),
      <Return holding={h} />,
      h.allocation_percent === null ? "Unavailable" : `${h.allocation_percent}%`,
    ];
  }
  return (
    <Card className="min-w-0 md:col-span-2 lg:col-span-12">
      <CardContent>
        <h2 className="font-medium">Holdings</h2>
        <p className="text-muted-foreground">
          Average cost includes crypto buy fees. Values use market mid prices.
        </p>
        {sorted.length === 0 ? (
          <div className="flex flex-col items-start gap-3">
            <h3 className="font-medium">No holdings yet</h3>
            <p>Explore Markets to buy your first stock or crypto.</p>
            <Button asChild className="min-h-11">
              <Link to="/">Explore Markets</Link>
            </Button>
          </div>
        ) : (
          <>
            <div className="hidden min-w-0 lg:block">
              <table aria-label="Holdings" className="w-full table-fixed border-collapse text-left">
                <thead>
                  <tr className="border-b border-border">
                    {columns.map((c, i) => (
                      <th
                        key={c}
                        scope="col"
                        className={`px-2 py-3 text-[13px] leading-[18px] font-medium text-muted-foreground ${i ? "text-right" : "w-[24%]"}`}
                      >
                        {c}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {sorted.map((h) => (
                    <tr
                      key={h.coin_id}
                      className="border-b border-border align-top hover:bg-accent"
                    >
                      <th scope="row" className="px-2 py-3 text-[13px] leading-[18px] font-normal">
                        <Asset
                          holding={h}
                          elapsed={elapsed}
                          freshSeconds={freshSeconds}
                          staleSeconds={staleSeconds}
                        />
                      </th>
                      {fields(h).map((v, i) => (
                        <td
                          key={columns[i + 1]}
                          className="min-w-0 px-2 py-3 text-right wrap-anywhere tabular-nums [&>div]:items-end"
                        >
                          {v}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <ol aria-label="Holdings" className="flex flex-col gap-3 lg:hidden">
              {sorted.map((h) => (
                <li key={h.coin_id} className="min-w-0 rounded-control border border-border p-4">
                  <Asset
                    holding={h}
                    elapsed={elapsed}
                    freshSeconds={freshSeconds}
                    staleSeconds={staleSeconds}
                  />
                  <dl className="mt-4 flex flex-col gap-3">
                    {fields(h).map((v, i) => (
                      <div key={columns[i + 1]} className="flex flex-wrap justify-between gap-2">
                        <dt className="text-[13px] leading-[18px] font-medium text-muted-foreground">
                          {columns[i + 1]}
                        </dt>
                        <dd className="min-w-0 max-w-full wrap-anywhere tabular-nums">{v}</dd>
                      </div>
                    ))}
                  </dl>
                </li>
              ))}
            </ol>
          </>
        )}
      </CardContent>
    </Card>
  );
}
