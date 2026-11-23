import type { Portfolio } from "@/api/portfolio";
import { outcome } from "@/lib/financialDisplay";

/** Lexically bound CSS percentages: no conversion, scaling or residual arithmetic. */
function validAllocation(value: string | null): value is string {
  return value !== null && /^(?:\d{1,2}(?:\.\d+)?|100(?:\.0+)?)$/.test(value);
}

export function PortfolioAllocation({ portfolio }: { portfolio: Portfolio }) {
  const rows = [
    { key: "cash", label: "Cash", percent: portfolio.class_allocation_percent.cash },
    { key: "crypto", label: "Crypto", percent: portfolio.class_allocation_percent.crypto },
    { key: "stocks", label: "Stocks", percent: portfolio.class_allocation_percent.stocks },
  ];
  return (
    <section
      aria-label="Portfolio allocation"
      className="flex min-w-0 flex-col gap-3 border-t border-border pt-4 md:border-t-0 md:border-l md:pt-0 md:pl-7"
    >
      {portfolio.valuation_complete &&
        portfolio.cash_allocation_percent === null &&
        portfolio.total_value !== null &&
        outcome(portfolio.total_value) === "zero" && (
          <p>Allocation is unavailable while total portfolio value is zero.</p>
        )}
      {!portfolio.valuation_complete && (
        <p>Allocation is unavailable until every holding can be valued.</p>
      )}
      <ul aria-label="Allocation" className="flex flex-col gap-3">
        {rows.map(({ key, label, percent }) => {
          const valid = portfolio.valuation_complete && validAllocation(percent);
          return (
            <li key={key} className="flex min-w-0 flex-col gap-1">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <span className="min-w-0 wrap-anywhere text-muted-foreground">{label}</span>
                <span className="font-medium tabular-nums">
                  {valid ? `${percent}%` : "Unavailable"}
                </span>
              </div>
              <div
                aria-hidden="true"
                className="h-2 overflow-hidden rounded-[var(--radius-bar)] bg-muted"
              >
                {valid && (
                  <div
                    data-allocation-fill
                    className="h-full rounded-[var(--radius-bar)] bg-data-fill"
                    style={{ width: `${percent}%` }}
                  />
                )}
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
