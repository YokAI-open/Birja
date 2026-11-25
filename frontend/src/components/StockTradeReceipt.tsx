import { useEffect, useId, useRef, type ReactNode } from "react";
import { Link } from "react-router";
import type { StockFillValues } from "@/api/stockTrades";
import { Button } from "@/components/ui/button";
import type { PortfolioTarget } from "@/hooks/usePortfolioTarget";
import { fullLocalTimestamp, signedUsd } from "@/lib/financialDisplay";
import { formatUnitPrice, formatUsd } from "@/lib/money";
export function StockFigure({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="min-w-0 max-w-full text-right wrap-anywhere tabular-nums">{children}</dd>
    </div>
  );
}
export function StockDate({ value }: { value: string }) {
  return (
    <time dateTime={value} title={value} className="wrap-anywhere">
      {fullLocalTimestamp(value)}
    </time>
  );
}
export function StockTradeReceipt({
  fill: f,
  onTradeAgain,
  target,
  unitPrice = formatUnitPrice,
}: {
  fill: StockFillValues;
  target: PortfolioTarget;
  onTradeAgain: () => void;
  unitPrice?: (value: string) => string;
}) {
  const id = useId(),
    heading = useRef<HTMLHeadingElement>(null),
    focusedReceipt = useRef<string | null>(null);
  useEffect(() => {
    if (
      target.isCurrent() &&
      f.portfolio_id === target.portfolioId &&
      focusedReceipt.current !== f.trade_id
    ) {
      focusedReceipt.current = f.trade_id;
      heading.current?.focus({ preventScroll: true });
    }
  }, [f.trade_id, f.portfolio_id, target]);
  if (!target.isCurrent() || f.portfolio_id !== target.portfolioId) return null;
  return (
    <section aria-labelledby={id} className="flex min-w-0 flex-col gap-4">
      <h2
        id={id}
        ref={heading}
        tabIndex={-1}
        className="text-[24px] leading-7 font-medium focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
      >
        Order filled
      </h2>
      <p className="wrap-anywhere">
        {f.company_name} · {f.symbol} · {f.listing_exchange} · Stock
      </p>
      <p>
        {f.side === "buy" ? "Bought" : "Sold"} {f.quantity.split(".")[0]} shares
      </p>
      <dl className="flex min-w-0 flex-col gap-3">
        <StockFigure label="Execution price">{unitPrice(f.exec_price)}</StockFigure>
        <StockFigure label="IEX bid">{unitPrice(f.bid)}</StockFigure>
        <StockFigure label="IEX ask">{unitPrice(f.ask)}</StockFigure>
        <StockFigure label="Commission">{formatUsd(f.fee)}</StockFigure>
        <StockFigure label="Added spread">0%</StockFigure>
        <StockFigure label="Total cash change">{signedUsd(f.cash_delta)}</StockFigure>
        <StockFigure label="Cash after this trade">{formatUsd(f.cash_after)}</StockFigure>
        <StockFigure label="Shares after this trade">{f.held_after.split(".")[0]}</StockFigure>
        <StockFigure label="Filled at">
          <StockDate value={f.executed_at} />
        </StockFigure>
        <StockFigure label="Source quote">
          <StockDate value={f.event_at} />
        </StockFigure>
        <StockFigure label="Receipt">{f.trade_id}</StockFigure>
      </dl>
      <p className="text-[13px] leading-[18px] text-muted-foreground">
        Balances shown are the recorded balances immediately after this trade.
      </p>
      <div className="flex flex-wrap gap-3">
        <Button asChild className="min-h-11">
          <Link to={`/portfolios/${f.portfolio_id}`}>Portfolio</Link>
        </Button>
        <Button variant="secondary" className="min-h-11" onClick={onTradeAgain}>
          Trade again
        </Button>
      </div>
    </section>
  );
}
