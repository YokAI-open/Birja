import { useEffect, useId, useRef, useState } from "react";
import { Link, useParams } from "react-router";
import { useStockTrade } from "@/hooks/useStockTrade";
import { isStockOrder, type StockRefusal } from "@/api/stockTrades";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { StockAttribution } from "@/components/StockAttribution";
import {
  StockDate,
  StockDisclosure,
  StockFigure,
  StockTradeReceipt,
} from "@/components/StockTradeReceipt";
import { formatUnitPrice, formatUsd } from "@/lib/money";
import { signedUsd } from "@/lib/financialDisplay";
const reasons: Record<StockRefusal, string> = {
  market_closed: "Market closed. You can edit a draft; no order is queued.",
  halted: "Trading halted. New orders are unavailable.",
  frozen: "Trading frozen. New orders are unavailable.",
  status_unavailable: "Stock status is unverified. New orders are unavailable.",
  permission_unavailable: "Stock data access is unavailable. Crypto remains available.",
  action_unavailable: "Suspended for corporate-action review.",
  units_changed: "Stock units changed. Get a fresh preview after checks finish.",
  session_unavailable: "The regular trading session is unverified. New orders are unavailable.",
  quote_stale: "This quote is out of date. A fresh eligible quote is required before trading.",
  quote_unavailable: "A verified IEX quote is unavailable. New orders are unavailable.",
  receipt_unavailable: "This order needs verification. Check its result before placing another.",
  invalid_quantity: "Enter a whole number greater than 0.",
  numeric_range: "This quantity is too large. Enter a smaller whole number.",
  insufficient_cash: "Not enough cash for this order. Review your quantity and try again.",
  insufficient_holding: "Not enough shares for this sale. Review your quantity and try again.",
  idempotency_conflict: "This order conflicts with an earlier attempt. Get a fresh preview.",
};
function Ticket({ symbol }: { symbol: string }) {
  const t = useStockTrade(symbol),
    c = t.context,
    id = useId(),
    input = useRef<HTMLInputElement>(null);
  const [retrying, setRetrying] = useState(false);
  const oldPhase = useRef(t.phase);
  useEffect(() => {
    if (oldPhase.current === "filled" && t.phase === "draft") input.current?.focus();
    oldPhase.current = t.phase;
  }, [t.phase]);
  const locked = ["submitting", "unknown", "filled"].includes(t.phase);
  const valid = isStockOrder({ symbol: t.symbol, side: t.side, quantity: t.quantity });
  const quantityError =
    t.quantity === "" || valid
      ? null
      : /^[1-9]\d{12,}$/.test(t.quantity)
        ? reasons.numeric_range
        : reasons.invalid_quantity;
  const refusal = c && c.execution_reason !== "available" ? reasons[c.execution_reason] : null;
  const message =
    t.phase === "filled"
      ? "Order filled."
      : t.phase === "unknown"
        ? "We couldn't confirm the result. Check this order before placing another."
        : t.phase === "submitting"
          ? "Checking order result…"
          : t.replacement
            ? "Price updated. Review the changes before confirming again."
            : t.interrupted
              ? "Trading became unavailable. Your quantity is saved here; get a fresh preview before confirming."
              : (refusal ??
                (t.phase === "preview"
                  ? "Preview ready. Review before confirming."
                  : "Enter a quantity to preview this trade."));
  const quote = t.quote;
  const visible = quote ?? c?.quote;
  const noShortcut =
    !c?.execution_enabled ||
    (t.side === "buy"
      ? /^0(?:\.0+)?$/.test(c.buy_max_quantity)
      : /^0(?:\.0+)?$/.test(c.held_quantity));
  return (
    <div className="my-8 flex min-w-0 flex-col gap-4 text-[15px] leading-[22px]">
      <h1 className="text-[32px] leading-9 font-medium wrap-anywhere md:text-[40px] md:leading-[44px]">
        Trade {t.symbol}
      </h1>
      <p
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className={
          refusal || t.interrupted || t.phase === "unknown"
            ? "rounded-control bg-warn-soft p-4 text-warn-text"
            : "sr-only"
        }
      >
        {message}
      </p>
      <div className="grid min-w-0 gap-4 lg:grid-cols-12">
        <Card className="min-w-0 lg:col-span-7">
          <CardContent>
            {c ? (
              <>
                <h2 className="text-[24px] leading-7 font-medium wrap-anywhere">
                  {c.company_name}
                </h2>
                <p>
                  {c.symbol} · {c.listing_exchange} · USD
                </p>
                <Badge variant="neutral">Stock</Badge>
                <div className="flex flex-wrap gap-3">
                  <p>Session: {c.session.state}</p>
                  <p>Status: {c.status.state}</p>
                  <p>Corporate actions: {c.action.state}</p>
                </div>
                {c.session.opens_at && c.session.closes_at && (
                  <p className="text-[13px] leading-[18px] wrap-anywhere">
                    Regular session (America/New_York):{" "}
                    <StockDate value={c.session.opens_at} exchange /> –{" "}
                    <StockDate value={c.session.closes_at} exchange />
                  </p>
                )}
              </>
            ) : t.contextLoading ? (
              <div aria-busy="true" aria-label="Loading stock">
                <div className="h-7 rounded-control bg-muted" />
              </div>
            ) : (
              <p>Can&apos;t load this stock right now. Retry or return to Markets.</p>
            )}
            {t.contextError && (
              <p role="alert">Can&apos;t load this stock right now. Retry or return to Markets.</p>
            )}
            <Button
              variant="secondary"
              className="min-h-11 self-start"
              aria-disabled={retrying}
              onClick={() => {
                if (!retrying) {
                  setRetrying(true);
                  void t.refreshContext().finally(() => setRetrying(false));
                }
              }}
            >
              {retrying ? "Retrying stock…" : "Retry stock"}
            </Button>
            <div className="grid min-w-0 gap-3 sm:grid-cols-2">
              {(["bid", "ask"] as const).map((side) => {
                const selected = side === (t.side === "buy" ? "ask" : "bid");
                return (
                  <div
                    key={side}
                    className={`min-w-0 rounded-control p-4 ${selected ? "bg-accent text-accent-foreground" : "bg-muted"}`}
                  >
                    <p className="font-medium">IEX {side}</p>
                    <p className="text-[24px] leading-7 wrap-anywhere tabular-nums">
                      {visible ? formatUnitPrice(visible[side]) : "Unavailable"}
                    </p>
                    {selected && <p>{t.side === "buy" ? "Buy price" : "Sell price"}</p>}
                  </div>
                );
              })}
            </div>
            {visible && (
              <p className="text-[13px] leading-[18px]">
                Source quote: <StockDate value={visible.event_at} />
              </p>
            )}
            <form
              className="flex min-w-0 flex-col gap-4"
              onSubmit={(e) => {
                e.preventDefault();
                void t.preview();
              }}
            >
              <fieldset disabled={locked} className="flex gap-3">
                <legend className="mb-2 font-medium">Order side</legend>
                {(["buy", "sell"] as const).map((side) => (
                  <label
                    key={side}
                    className={`flex min-h-11 flex-1 cursor-pointer items-center justify-center gap-2 rounded-pill border border-border px-4 ${t.side === side ? "bg-primary text-primary-foreground" : "bg-secondary"}`}
                  >
                    <input
                      type="radio"
                      name={id + "side"}
                      value={side}
                      checked={t.side === side}
                      onChange={() => t.setSide(side)}
                      className="accent-current focus-visible:ring-2 focus-visible:ring-ring"
                    />
                    {side === "buy" ? "Buy" : "Sell"}
                  </label>
                ))}
              </fieldset>
              <div className="flex flex-col gap-2">
                <label htmlFor={id + "quantity"} className="font-medium">
                  Whole-share quantity
                </label>
                <Input
                  id={id + "quantity"}
                  ref={input}
                  type="text"
                  inputMode="numeric"
                  autoComplete="off"
                  value={t.quantity}
                  disabled={locked}
                  onChange={(e) => t.setQuantity(e.target.value)}
                  aria-invalid={quantityError !== null}
                  aria-describedby={
                    id + "help " + id + "restriction" + (quantityError ? " " + id + "error" : "")
                  }
                />
                <p id={id + "help"} className="text-[13px] leading-[18px] text-muted-foreground">
                  Enter a whole number of shares.
                </p>
                {quantityError && (
                  <p id={id + "error"} className="text-loss-text">
                    {quantityError}
                  </p>
                )}
              </div>
              <Button
                type="button"
                variant="secondary"
                className="min-h-11 self-start"
                disabled={locked || noShortcut}
                onClick={t.side === "buy" ? t.buyMax : t.sellAll}
              >
                {t.side === "buy" ? "Buy max" : "Sell all"}
              </Button>
              {c?.execution_enabled && noShortcut && (
                <p>
                  {t.side === "buy"
                    ? "Not enough cash to buy one share at the current ask."
                    : "You do not hold shares of this stock."}
                </p>
              )}
              <p
                id={id + "restriction"}
                className="text-[13px] leading-[18px] text-muted-foreground"
              >
                {refusal
                  ? "Preview unavailable while trading is paused. Your quantity is only a draft."
                  : "A preview does not place an order. Confirm it separately."}
              </p>
              {c && (
                <dl className="flex flex-col gap-2">
                  <StockFigure label="Cash available">{formatUsd(c.cash)}</StockFigure>
                  <StockFigure label="Shares owned">{c.held_quantity.split(".")[0]}</StockFigure>
                </dl>
              )}
              <Button type="submit" disabled={!t.canPreview} className="min-h-11 self-start">
                {t.phase === "loading_preview" ? "Loading preview" : "Preview trade"}
              </Button>
            </form>
            <StockAttribution context="preview" />
            <StockDisclosure />
          </CardContent>
        </Card>
        <Card className="min-w-0 lg:col-span-5">
          <CardContent>
            {t.fill ? (
              <StockTradeReceipt fill={t.fill} onTradeAgain={t.tradeAgain} />
            ) : (
              <>
                <h2 className="text-[24px] leading-7 font-medium">Trade preview</h2>
                {t.phase === "loading_preview" && (
                  <div
                    aria-busy="true"
                    aria-label="Loading preview"
                    className="flex flex-col gap-3"
                  >
                    {[0, 1, 2, 3, 4].map((i) => (
                      <div key={i} className="h-5 rounded-control bg-muted" />
                    ))}
                  </div>
                )}
                {t.error && t.error !== "unknown" && (
                  <p role="alert" className="rounded-control bg-warn-soft p-4 text-warn-text">
                    {reasons[t.error]}
                  </p>
                )}
                {t.replacement && (
                  <section
                    aria-label="Price changes"
                    className="rounded-control bg-warn-soft p-4 text-warn-text"
                  >
                    <p>Price updated. Review the changes before confirming again.</p>
                    <dl className="mt-3 flex flex-col gap-3">
                      <StockFigure label="Previous execution price">
                        {formatUnitPrice(t.replacement.previous_exec_price)}
                      </StockFigure>
                      <StockFigure label="New execution price">
                        {formatUnitPrice(t.replacement.quote.exec_price)}
                      </StockFigure>
                      <StockFigure label="Previous cash change">
                        {signedUsd(t.replacement.previous_cash_delta)}
                      </StockFigure>
                      <StockFigure label="New cash change">
                        {signedUsd(t.replacement.quote.cash_delta)}
                      </StockFigure>
                      <StockFigure label="Difference">
                        {signedUsd(t.replacement.cash_delta_change)}
                      </StockFigure>
                    </dl>
                  </section>
                )}
                {quote ? (
                  <dl className="flex flex-col gap-3">
                    <StockFigure label="Quantity">{quote.quantity.split(".")[0]}</StockFigure>
                    <StockFigure label="Execution price">
                      {formatUnitPrice(quote.exec_price)}
                    </StockFigure>
                    <StockFigure label="Commission">{formatUsd(quote.fee)}</StockFigure>
                    <StockFigure label="Added spread">0%</StockFigure>
                    <StockFigure label="Total cash change">
                      {signedUsd(quote.cash_delta)}
                    </StockFigure>
                  </dl>
                ) : (
                  <p>
                    {t.phase === "unknown"
                      ? "We couldn't confirm the result. Check this order before placing another."
                      : "Enter a quantity to preview this trade."}
                  </p>
                )}
                {t.phase === "unknown" || t.phase === "submitting" ? (
                  <Button
                    className="min-h-11"
                    disabled={t.phase === "submitting"}
                    onClick={() => void t.checkResult()}
                  >
                    {t.phase === "submitting" ? "Checking order result…" : "Check order result"}
                  </Button>
                ) : (
                  <Button
                    className="min-h-11"
                    disabled={!t.canConfirm}
                    onClick={() => void t.confirm()}
                  >
                    {t.side === "buy" ? "Confirm buy" : "Confirm sell"}
                  </Button>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>
      <Link
        to="/"
        className="min-h-11 self-start rounded-control px-2 py-3 text-data-blue-text underline focus-visible:ring-2 focus-visible:ring-ring"
      >
        Back to Markets
      </Link>
    </div>
  );
}
export default function StockTradePage() {
  const symbol = useParams().symbol ?? "";
  if (!/^[A-Z][A-Z0-9.-]{0,9}$/.test(symbol))
    return (
      <div className="my-8">
        <h1 className="text-[32px] leading-9 font-medium">Unknown stock</h1>
        <Link to="/">Back to Markets</Link>
      </div>
    );
  return <Ticket symbol={symbol} />;
}
