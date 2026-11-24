import { useEffect, useId, useRef } from "react";
import { useOutletContext, useParams } from "react-router";
import type { PortfolioTarget } from "@/hooks/usePortfolioTarget";
import { usePortfolio } from "@/hooks/usePortfolio";
import { useNow } from "@/hooks/useNow";
import { useStocks } from "@/hooks/useStocks";
import { useStockTrade } from "@/hooks/useStockTrade";
import { isStockOrder, type StockRefusal } from "@/api/stockTrades";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { MarketOpening } from "@/components/MarketOpening";
import { StockDate, StockFigure, StockTradeReceipt } from "@/components/StockTradeReceipt";
import { formatUnitPrice, formatUsd } from "@/lib/money";
import { signedUsd } from "@/lib/financialDisplay";
const reasons: Record<StockRefusal, string> = {
  market_closed: "Market closed.",
  halted: "Trading halted. New orders are unavailable.",
  frozen: "Trading frozen. New orders are unavailable.",
  status_unavailable: "The trading status check is unavailable.",
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
  idempotency_conflict:
    "This order reference belongs to a different portfolio or request. Return to the original portfolio to check it.",
};
function Ticket({ target, symbol }: { target: PortfolioTarget; symbol: string }) {
  const t = useStockTrade(target, symbol),
    c = t.context,
    id = useId(),
    input = useRef<HTMLInputElement>(null);
  const { data: stocks } = useStocks();
  const { data: portfolio } = usePortfolio(target);
  const now = useNow(15_000);
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
  // The catalogue has the verified next session even when the ticket cannot
  // load trade context. These facts only affect the copy, never order admission.
  const cataloguedStock = stocks?.items.find((item) => item.symbol === symbol);
  const catalogueSession = cataloguedStock?.session;
  const marketClosed =
    (t.error === "market_closed" && c?.execution_enabled !== true) ||
    c?.execution_reason === "market_closed" ||
    c?.session.state === "closed" ||
    (c?.session.state !== "open" && catalogueSession?.state === "closed");
  const nextOpen = c?.session.next_open_at ?? catalogueSession?.next_open_at;
  const refusal = marketClosed
    ? reasons.market_closed
    : c && c.execution_reason !== "available"
      ? reasons[c.execution_reason]
      : null;
  const message =
    t.phase === "filled"
      ? "Order filled."
      : t.phase === "unknown"
        ? "We couldn't confirm the result. Check this order before placing another."
        : t.phase === "submitting"
          ? "Checking order result…"
          : t.replacement
            ? "Price updated. Review the changes before confirming again."
            : t.interrupted && !marketClosed
              ? "Trading became unavailable. Your quantity is saved here; get a fresh preview before confirming."
              : (refusal ??
                (t.phase === "preview"
                  ? "Preview ready. Review before confirming."
                  : "Enter a quantity to preview this trade."));
  const quote = t.quote;
  const lastQuote = marketClosed ? cataloguedStock?.quote : null;
  const visible = quote ?? c?.quote;
  const requiredAttribution = stocks?.attribution.required_text;
  const noShortcut =
    !c?.execution_enabled ||
    (t.side === "buy"
      ? /^0(?:\.0+)?$/.test(c.buy_max_quantity)
      : /^0(?:\.0+)?$/.test(c.held_quantity));
  if (!target.isCurrent()) return null;
  return (
    <div className="app-page flex flex-col gap-7 text-base md:gap-9">
      <header>
        <h1 className="app-heading wrap-anywhere">Trade {t.symbol}</h1>
      </header>
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
        {message === reasons.market_closed && (
          <>
            {" "}
            <MarketOpening nextOpen={nextOpen} now={now} />
          </>
        )}
      </p>
      <div className="grid min-w-0 gap-6 lg:grid-cols-12 lg:gap-8">
        <Card className="min-w-0 lg:col-span-7 lg:self-start">
          <CardContent>
            {c ? (
              <>
                <h2 className="text-2xl leading-tight font-semibold wrap-anywhere">
                  {c.company_name}
                </h2>
                <p>
                  {c.symbol} · {c.listing_exchange} · USD
                </p>
              </>
            ) : t.contextLoading ? (
              <div aria-busy="true" aria-label="Loading stock">
                <div className="h-7 rounded-control bg-muted" />
              </div>
            ) : null}
            {t.contextError && !marketClosed && (
              <p role="alert">
                {stocks?.admission.state === "unavailable" && cataloguedStock
                  ? "Stock data is paused."
                  : "Couldn't load this stock."}
              </p>
            )}
            {lastQuote && (
              <div>
                <p className="text-2xl font-semibold tabular-nums">
                  {formatUnitPrice(lastQuote.mid)}
                </p>
                <p className="text-sm text-muted-foreground">
                  Last verified IEX midpoint · <StockDate value={lastQuote.event_at} />
                </p>
              </div>
            )}
            {!marketClosed && (visible || c) && (
              <div className="grid min-w-0 gap-3 sm:grid-cols-2">
                {(["bid", "ask"] as const).map((side) => {
                  const selected = side === (t.side === "buy" ? "ask" : "bid");
                  return (
                    <div
                      key={side}
                      className={`min-w-0 rounded-control border p-4 md:p-5 ${selected ? "border-ring bg-accent text-accent-foreground" : "border-border bg-card"}`}
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
            )}
            {visible && !marketClosed && (
              <p className="text-[13px] leading-[18px]">
                Source quote: <StockDate value={visible.event_at} />
              </p>
            )}
            <form
              className="flex min-w-0 flex-col gap-5 border-t border-border pt-5"
              onSubmit={(e) => {
                e.preventDefault();
                if (!marketClosed) void t.preview();
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
                    id +
                    "help" +
                    (marketClosed ? "" : " " + id + "restriction") +
                    (quantityError ? " " + id + "error" : "")
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
                {t.side === "buy" && portfolio && (
                  <p className="text-[13px] leading-[18px] text-muted-foreground">
                    Cash available {formatUsd(portfolio.cash)}
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
              {!marketClosed && (
                <p
                  id={id + "restriction"}
                  className="text-[13px] leading-[18px] text-muted-foreground"
                >
                  {refusal
                    ? "Preview unavailable while trading is paused. Your quantity is only a draft."
                    : "A preview does not place an order. Confirm it separately."}
                </p>
              )}
              {c && (
                <dl className="flex flex-col gap-2">
                  <StockFigure label="Shares owned">{c.held_quantity.split(".")[0]}</StockFigure>
                </dl>
              )}
              {!marketClosed && (
                <Button type="submit" disabled={!t.canPreview} className="min-h-11 self-start">
                  {t.phase === "loading_preview" ? "Loading preview" : "Preview trade"}
                </Button>
              )}
            </form>
            {c?.status.source === "nasdaq-rss" && !marketClosed && (
              <p className="text-[13px] leading-[18px] text-muted-foreground">
                Halt reports can be delayed or incomplete.
              </p>
            )}
            {requiredAttribution && (lastQuote || (!marketClosed && visible) || t.fill) && (
              <p className="text-[13px] leading-[18px] break-words text-muted-foreground">
                {requiredAttribution}
              </p>
            )}
          </CardContent>
        </Card>
        <Card className="min-w-0 bg-muted lg:col-span-5 lg:self-start">
          <CardContent>
            {t.fill ? (
              <StockTradeReceipt fill={t.fill} target={target} onTradeAgain={t.tradeAgain} />
            ) : (
              <>
                <h2 className="text-xl leading-7 font-semibold">Trade preview</h2>
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
                {t.error && t.error !== "unknown" && t.error !== "market_closed" && (
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
                ) : t.phase === "unknown" ? (
                  <p>
                    We couldn&apos;t confirm the result. Check this order before placing another.
                  </p>
                ) : !marketClosed ? (
                  <p>Enter a quantity to preview this trade.</p>
                ) : null}
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
                    disabled={marketClosed || !t.canConfirm}
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
    </div>
  );
}
export default function StockTradePage() {
  const symbol = useParams().symbol ?? "";
  const target = useOutletContext<PortfolioTarget>();
  if (!/^[A-Z][A-Z0-9.-]{0,9}$/.test(symbol))
    return (
      <div className="app-page flex flex-col items-start gap-4">
        <h1 className="app-heading">Unknown stock</h1>
      </div>
    );
  return (
    <Ticket
      key={`${target.owner}:${target.portfolioId}:${target.epoch.session}:${symbol}`}
      target={target}
      symbol={symbol}
    />
  );
}
