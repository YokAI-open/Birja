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
    <Button
      asChild
      variant="secondary"
      className="min-h-11 min-w-11 text-[15px] font-medium motion-reduce:transform-none motion-reduce:transition-none"
    >
      <Link to={`/trade/${encodeURIComponent(holding.symbol)}`}>Trade {holding.symbol}</Link>
    </Button>
  ) : (
    <span>Inactive · trading unavailable</span>
  );
}

const columns = [
  "Coin",
  "Quantity",
  "Average cost",
  "Mid price",
  "Current value",
  "Unrealized P/L",
  "Allocation",
  "Price updated",
  "Trade",
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
  function fields(holding: PortfolioHolding): ReactNode[] {
    return [
      formatQuantity(holding.quantity),
      outcome(holding.average_cost) === "zero"
        ? formatUsd("0")
        : formatUnitPrice(holding.average_cost),
      holding.mid === null ? "Unavailable" : formatUnitPrice(holding.mid),
      holding.current_value === null ? "Unavailable" : formatUsd(holding.current_value),
      <Return holding={holding} />,
      holding.allocation_percent === null ? "Unavailable" : `${holding.allocation_percent}%`,
      <PriceUpdated
        holding={holding}
        elapsed={elapsed}
        freshSeconds={freshSeconds}
        staleSeconds={staleSeconds}
      />,
      <Trade holding={holding} />,
    ];
  }
  return (
    <Card className="min-w-0 md:col-span-2 lg:col-span-12">
      <CardContent>
        <h2 className="font-medium">Holdings</h2>
        <p className="text-muted-foreground">
          Average cost includes buy fees. Values use market mid prices.
        </p>
        {holdings.length === 0 ? (
          <div className="flex flex-col items-start gap-3">
            <h3 className="font-medium">No holdings yet</h3>
            <p>Your cash is available to trade. Browse markets to choose a coin.</p>
            <Button
              asChild
              className="min-h-11 motion-reduce:transform-none motion-reduce:transition-none"
            >
              <Link to="/">Browse markets</Link>
            </Button>
          </div>
        ) : (
          <>
            <div
              role="region"
              aria-label="Holdings table, scroll to see all columns"
              tabIndex={0}
              className="hidden overflow-x-auto rounded-control focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 md:block"
            >
              <table aria-label="Holdings" className="w-full border-collapse text-left">
                <thead>
                  <tr className="border-b border-border">
                    {columns.map((column, index) => (
                      <th
                        key={column}
                        scope="col"
                        className={`px-2 py-3 text-[13px] leading-[18px] font-medium text-muted-foreground ${index > 0 && index < 7 ? "text-right" : ""}`}
                      >
                        {column}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {holdings.map((holding) => (
                    <tr
                      key={holding.symbol}
                      className="h-[52px] border-b border-border hover:bg-accent"
                    >
                      <th scope="row" className="min-w-24 px-2 py-3 font-medium wrap-anywhere">
                        <span className="block">{holding.symbol}</span>
                        <span className="block text-[13px] leading-[18px] font-normal text-muted-foreground">
                          {holding.name}
                        </span>
                      </th>
                      {fields(holding).map((field, index) => (
                        <td
                          key={columns[index + 1]}
                          className={`px-2 py-3 align-top wrap-anywhere tabular-nums ${index < 6 ? "text-right" : "min-w-40"} ${index === 4 ? "min-w-48 [&>div]:items-end" : ""}`}
                        >
                          {field}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <ol aria-label="Holdings" className="flex flex-col gap-3 md:hidden">
              {holdings.map((holding) => {
                const values = fields(holding);
                return (
                  <li
                    key={holding.symbol}
                    className="min-w-0 rounded-control border border-border p-4"
                  >
                    <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <h3 className="font-medium wrap-anywhere">{holding.symbol}</h3>
                        <p className="text-[13px] leading-[18px] text-muted-foreground">
                          {holding.name}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-[13px] leading-[18px] font-medium text-muted-foreground">
                          Current value
                        </p>
                        <p className="wrap-anywhere tabular-nums">{values[3]}</p>
                      </div>
                    </div>
                    <dl className="flex flex-col gap-3">
                      {values.map((value, index) =>
                        index === 3 ? null : (
                          <div
                            key={columns[index + 1]}
                            className="flex flex-wrap justify-between gap-2"
                          >
                            <dt className="text-[13px] leading-[18px] font-medium text-muted-foreground">
                              {columns[index + 1]}
                            </dt>
                            <dd className="min-w-0 max-w-full wrap-anywhere tabular-nums">
                              {value}
                            </dd>
                          </div>
                        ),
                      )}
                    </dl>
                  </li>
                );
              })}
            </ol>
          </>
        )}
      </CardContent>
    </Card>
  );
}
