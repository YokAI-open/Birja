import type { Portfolio } from "@/api/portfolio";
import { outcome } from "@/lib/financialDisplay";
import { formatUsd } from "@/lib/money";

const assetClasses = [
  { key: "cash", label: "Cash", fill: "bg-border" },
  { key: "stocks", label: "Stocks", fill: "bg-data-fill" },
  { key: "crypto", label: "Crypto", fill: "bg-muted-foreground" },
] as const;

/** Lexically bound CSS percentages: no conversion, scaling or residual arithmetic. */
function validAllocation(value: string | null): value is string {
  return value !== null && /^(?:\d{1,2}(?:\.\d+)?|100(?:\.0+)?)$/.test(value);
}

export function PortfolioAllocation({ portfolio }: { portfolio: Portfolio }) {
  return (
    <section aria-label="Portfolio allocation" className="flex min-w-0 flex-col gap-3">
      {portfolio.valuation_complete &&
        portfolio.cash_allocation_percent === null &&
        portfolio.total_value !== null &&
        outcome(portfolio.total_value) === "zero" && (
          <p>Allocation is unavailable while total portfolio value is zero.</p>
        )}
      {!portfolio.valuation_complete && (
        <p>Allocation is unavailable until every holding can be valued.</p>
      )}
      <div aria-hidden="true" className="flex h-3 overflow-hidden rounded-sm bg-muted">
        {assetClasses.map(({ key, fill }) => {
          const percent = portfolio.class_allocation_percent[key];
          return portfolio.valuation_complete && validAllocation(percent) ? (
            <span
              key={key}
              data-allocation-fill={key}
              className={`shrink-0 ${fill}`}
              style={{ width: `${percent}%` }}
            />
          ) : null;
        })}
      </div>
      <ul aria-label="Allocation" className="grid min-w-0 grid-cols-3 gap-2">
        {assetClasses.map(({ key, label, fill }) => {
          const percent = portfolio.class_allocation_percent[key];
          const value = portfolio.class_values[key];
          const valid = portfolio.valuation_complete && validAllocation(percent);
          return (
            <li key={key} className="flex min-w-0 flex-col gap-0.5 wrap-anywhere">
              <span className="flex items-center gap-1.5 text-sm text-muted-foreground">
                <span aria-hidden="true" className={`size-2 shrink-0 rounded-[2px] ${fill}`} />
                {label}
              </span>
              <span className="font-semibold tabular-nums">
                {valid ? `${percent}%` : "Unavailable"}
              </span>
              <div
                role={key === "cash" ? "region" : undefined}
                aria-label={key === "cash" ? label : undefined}
                className="text-sm text-muted-foreground tabular-nums"
              >
                {value === null ? null : formatUsd(value)}
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
