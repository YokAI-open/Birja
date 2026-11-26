import { useEffect, useId, useRef } from "react";
import { useOutletContext, useParams } from "react-router";
import { ApiError } from "@/api/client";
import { isCatalogId, type CatalogOrderRefusal } from "@/api/stockCatalog";
import { stockShares } from "@/api/stockTrades";
import { MarketOpening } from "@/components/MarketOpening";
import { StockDate, StockFigure, StockTradeReceipt } from "@/components/StockTradeReceipt";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useCatalogStockTrade } from "@/hooks/useCatalogStockTrade";
import { useNow } from "@/hooks/useNow";
import type { PortfolioTarget } from "@/hooks/usePortfolioTarget";
import { catalogDisplay } from "@/hooks/useStockCatalog";
import { signedUsd } from "@/lib/financialDisplay";
import { formatStockPrice, formatUnitPrice, formatUsd } from "@/lib/money";
import "./tradeWorkspace.css";

const messages: Record<CatalogOrderRefusal, string> = {
  read_only: "Orders aren't available for this stock yet.",
  listing_changed: "This listing changed. Review the current stock before ordering.",
  market_closed: "Market closed.",
  halted: "Trading halted.",
  frozen: "Trading frozen.",
  permission_unavailable: "Trading is paused for this stock.",
  status_unavailable: "Waiting for the latest halt report.",
  action_unavailable: "Trading paused for corporate-action review.",
  units_changed: "Stock units changed. Review a fresh quote.",
  session_unavailable: "This stock’s market hours haven’t been confirmed.",
  quote_stale: "This quote is out of date.",
  quote_unavailable: "Waiting for a verified IEX quote.",
  receipt_unavailable: "Check the original order to verify its result.",
  receipt_missing: "This order didn’t fill. Preview again to place a new order.",
  invalid_quantity: "Enter a whole number greater than 0.",
  numeric_range: "Enter a smaller whole number.",
  insufficient_cash: "Not enough cash. Enter a smaller quantity.",
  insufficient_holding: "Not enough shares. Enter a smaller quantity.",
  idempotency_conflict: "This order reference belongs to a different request.",
};

const quantityRefusals = new Set([
  "invalid_quantity",
  "numeric_range",
  "insufficient_cash",
  "insufficient_holding",
]);
const shares = (amount: string) => amount.split(".")[0];

function OrderResultCheck({ busy, onCheck }: { busy: boolean; onCheck: () => void }) {
  return (
    <>
      <p role="status">
        {busy
          ? "Checking order result…"
          : "We couldn't confirm the result. Check this order before placing another."}
      </p>
      <Button className="min-h-12" disabled={busy} onClick={onCheck}>
        Check order result
      </Button>
    </>
  );
}

function CatalogTicket({ target, catalogId }: { target: PortfolioTarget; catalogId: string }) {
  const now = useNow(1000);
  const order = useCatalogStockTrade(target, catalogId, now);
  const context = order.context;
  const id = useId();
  const input = useRef<HTMLInputElement>(null);
  const priorPhase = useRef(order.phase);
  const amountRefusal = order.error && quantityRefusals.has(order.error) ? order.error : null;
  useEffect(() => {
    if ((priorPhase.current === "filled" && order.phase === "draft") || amountRefusal)
      input.current?.focus({ preventScroll: true });
    priorPhase.current = order.phase;
  }, [order.phase, amountRefusal]);
  if (!target.isCurrent()) return null;
  const resultUnconfirmed = order.phase === "submitting" || order.phase === "unknown";
  const receipt = order.fill ? (
    <StockTradeReceipt fill={order.fill} target={target} onTradeAgain={order.tradeAgain} />
  ) : null;

  if (!context) {
    if (receipt || resultUnconfirmed)
      return (
        <div className="trade-workspace">
          <Card className="trade-workspace-preview max-w-xl">
            <CardContent className="trade-workspace-content">
              {receipt ?? (
                <OrderResultCheck busy={order.phase === "submitting"} onCheck={order.checkResult} />
              )}
            </CardContent>
          </Card>
        </div>
      );
    if (order.contextLoading)
      return (
        <div className="trade-workspace">
          <p role="status">Loading stock…</p>
        </div>
      );
    const error = order.contextError;
    return (
      <div className="trade-workspace">
        <header className="trade-workspace-heading">
          <h1>
            {error instanceof ApiError && error.code === "portfolio_unavailable"
              ? "Portfolio unavailable"
              : "Stock unavailable"}
          </h1>
        </header>
        {!(error instanceof ApiError && error.status === 404) && (
          <Button variant="secondary" onClick={() => void order.refreshContext()}>
            Try again
          </Button>
        )}
      </div>
    );
  }

  const { listing, session } = context;
  const display = catalogDisplay(context, now);
  const closed = display.closed;
  const canDraft =
    listing.state === "active" &&
    (closed ||
      !context.read_only ||
      order.quantity !== "" ||
      resultUnconfirmed ||
      order.fill !== null);
  const locked = resultUnconfirmed || order.phase === "filled";
  const visible = order.quote ?? display.quote;
  const contextReason = context.execution_reason;
  const orderReason =
    order.error !== null && order.error !== "unknown" && !amountRefusal
      ? messages[order.error]
      : null;
  const restriction =
    listing.state === "retired"
      ? "This listing is no longer active."
      : listing.state === "review"
        ? "This listing needs review."
        : (orderReason ??
          (contextReason !== "available" ? messages[contextReason] : display.message));
  const quantityError =
    amountRefusal && amountRefusal !== "unknown"
      ? messages[amountRefusal]
      : order.quantity === "" || /^[1-9][0-9]{0,11}$/.test(order.quantity)
        ? null
        : /^[1-9][0-9]{12,}$/.test(order.quantity)
          ? messages.numeric_range
          : messages.invalid_quantity;
  const shortcut = order.side === "buy" ? context.buy_max_quantity : context.held_quantity;
  const noShortcut = locked || closed || context.read_only || stockShares(shortcut) === 0n;
  const showPreview = (canDraft && !closed) || receipt || resultUnconfirmed;
  const previewStatus =
    order.phase === "loading_preview"
      ? "Preparing the trade preview."
      : order.phase === "preview" && order.quote
        ? order.replacement
          ? "Price changed. Review the updated preview and confirm again."
          : "Preview ready. Review before confirming."
        : "";

  return (
    <div className="trade-workspace">
      <header className="trade-workspace-heading">
        <h1>{listing.company_name}</h1>
        <p className="wrap-anywhere">
          {listing.ticker} · {listing.listing_exchange}
          {listing.share_class && ` · Class ${listing.share_class}`}
        </p>
      </header>
      <div className="trade-workspace-grid">
        <Card role="region" aria-label="Trade ticket" className="trade-workspace-ticket">
          <CardContent className="trade-workspace-content">
            <div className="trade-workspace-market">
              {display.quote && (closed || !canDraft) && (
                <div>
                  <p className="trade-workspace-price" aria-describedby={id + "price-source"}>
                    {formatUnitPrice(display.quote.mid)}
                  </p>
                  <p
                    id={id + "price-source"}
                    className={closed ? "sr-only" : "text-sm text-muted-foreground"}
                  >
                    {closed ? "Last verified IEX midpoint" : "IEX price"} ·{" "}
                    <StockDate value={display.quote.event_at} />
                  </p>
                </div>
              )}
              {!closed && canDraft && visible && (
                <div className="grid min-w-0 grid-cols-2 gap-3">
                  {(["bid", "ask"] as const).map((side) => {
                    const selected = side === (order.side === "buy" ? "ask" : "bid");
                    return (
                      <div
                        key={side}
                        className={`min-w-0 rounded-control border p-3 ${selected ? "border-input bg-muted" : "border-border"}`}
                      >
                        <p className="text-sm text-muted-foreground">IEX {side}</p>
                        <p className="trade-workspace-price">{formatStockPrice(visible[side])}</p>
                        {selected && (
                          <p className="text-sm text-muted-foreground">
                            {order.side === "buy" ? "Buy price" : "Sell price"}
                          </p>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
              {closed ? (
                <p role="status">
                  Market closed. <MarketOpening nextOpen={session.next_open_at} now={now} />
                </p>
              ) : (
                restriction && (
                  <p role="status" className="text-muted-foreground">
                    {restriction}
                  </p>
                )
              )}
            </div>
            {!canDraft && (
              <div className="trade-workspace-balances">
                <p>Cash available {formatUsd(context.cash)}</p>
                <p>Shares owned {shares(context.held_quantity)}</p>
              </div>
            )}
            {canDraft && (
              <form
                className="flex min-w-0 flex-col gap-4"
                onSubmit={(event) => {
                  event.preventDefault();
                  if (order.canPreview) void order.preview();
                }}
              >
                <fieldset disabled={locked} className="trade-workspace-sides">
                  <legend className="sr-only">Order side</legend>
                  {(["buy", "sell"] as const).map((side) => (
                    <label key={side}>
                      <input
                        type="radio"
                        name={id + "side"}
                        value={side}
                        checked={order.side === side}
                        onChange={() => order.setSide(side)}
                      />
                      {side === "buy" ? "Buy" : "Sell"}
                    </label>
                  ))}
                </fieldset>
                <div className="trade-workspace-balances">
                  <p>Cash available {formatUsd(context.cash)}</p>
                  <p>Shares owned {shares(context.held_quantity)}</p>
                </div>
                <div className="flex flex-col gap-2">
                  <label htmlFor={id + "quantity"} className="font-medium">
                    Whole-share quantity
                  </label>
                  <div className="relative">
                    <Input
                      className="min-h-13 pr-18 text-right tabular-nums"
                      type="text"
                      id={id + "quantity"}
                      ref={input}
                      inputMode="numeric"
                      autoComplete="off"
                      value={order.quantity}
                      disabled={locked}
                      onChange={(event) => order.setQuantity(event.target.value)}
                      aria-invalid={quantityError !== null}
                      aria-describedby={quantityError ? id + "error" : undefined}
                    />
                    <span
                      aria-hidden="true"
                      className="pointer-events-none absolute inset-y-0 right-4 flex items-center text-muted-foreground"
                    >
                      Shares
                    </span>
                  </div>
                  {quantityError && (
                    <p
                      id={id + "error"}
                      className="text-loss-text"
                      role={amountRefusal ? "alert" : undefined}
                    >
                      {quantityError}
                    </p>
                  )}
                </div>
                {!closed && !locked && (
                  <div className="flex flex-wrap gap-3">
                    <Button
                      type="button"
                      variant="secondary"
                      className="min-h-11"
                      disabled={noShortcut}
                      onClick={order.useShortcut}
                    >
                      {order.side === "buy" ? "Buy max" : "Sell all"}
                    </Button>
                    <Button type="submit" className="min-h-11" disabled={!order.canPreview}>
                      {order.phase === "loading_preview" ? "Loading preview" : "Preview trade"}
                    </Button>
                  </div>
                )}
              </form>
            )}
            {!closed && (canDraft || contextReason === "halted") && (
              <p className="text-sm text-muted-foreground">
                Halt reports can be delayed or incomplete.
              </p>
            )}
          </CardContent>
        </Card>
        {showPreview && (
          <Card className="trade-workspace-preview">
            <CardContent className="trade-workspace-content">
              <p role="status" aria-atomic="true" className="sr-only">
                {previewStatus}
              </p>
              {receipt ??
                (resultUnconfirmed ? (
                  <OrderResultCheck
                    busy={order.phase === "submitting"}
                    onCheck={order.checkResult}
                  />
                ) : (
                  <>
                    <h2 className="text-xl font-semibold">Trade preview</h2>
                    {order.phase === "loading_preview" ? (
                      <p>Preparing preview…</p>
                    ) : (
                      order.replacement && (
                        <section
                          aria-label="Price changes"
                          className="rounded-control bg-warn-soft p-4 text-warn-text"
                        >
                          <p>Price updated. Review the changes before confirming again.</p>
                          <dl className="mt-3 flex flex-col gap-3">
                            <StockFigure label="Previous execution price">
                              {formatStockPrice(order.replacement.previous_exec_price)}
                            </StockFigure>
                            <StockFigure label="New execution price">
                              {formatStockPrice(order.replacement.quote.exec_price)}
                            </StockFigure>
                            <StockFigure label="Previous cash change">
                              {signedUsd(order.replacement.previous_cash_delta)}
                            </StockFigure>
                            <StockFigure label="New cash change">
                              {signedUsd(order.replacement.quote.cash_delta)}
                            </StockFigure>
                            <StockFigure label="Difference">
                              {signedUsd(order.replacement.cash_delta_change)}
                            </StockFigure>
                          </dl>
                        </section>
                      )
                    )}
                    {order.quote ? (
                      <>
                        <dl className="flex flex-col gap-3">
                          <StockFigure label="Quantity">{shares(order.quote.quantity)}</StockFigure>
                          {!order.replacement && (
                            <>
                              <StockFigure label="Execution price">
                                {formatStockPrice(order.quote.exec_price)}
                              </StockFigure>
                              <StockFigure label="Total cash change">
                                {signedUsd(order.quote.cash_delta)}
                              </StockFigure>
                            </>
                          )}
                          <StockFigure label="Commission">{formatUsd(order.quote.fee)}</StockFigure>
                          <StockFigure label="IEX source quote">
                            <StockDate value={order.quote.event_at} />
                          </StockFigure>
                        </dl>
                        <Button
                          className="min-h-12"
                          disabled={closed || !order.canConfirm}
                          onClick={() => void order.confirm()}
                        >
                          {order.side === "buy" ? "Confirm buy" : "Confirm sell"}
                        </Button>
                      </>
                    ) : order.error === "unknown" ? (
                      <p role="alert">Couldn’t prepare this preview. Try again.</p>
                    ) : order.phase !== "loading_preview" && !restriction ? (
                      <p className="text-muted-foreground">
                        Enter a quantity to preview this trade.
                      </p>
                    ) : null}
                  </>
                ))}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

export default function StockCatalogTradePage() {
  const { catalogId } = useParams();
  const target = useOutletContext<PortfolioTarget | null>();
  if (!isCatalogId(catalogId))
    return (
      <div className="app-page">
        <h1 className="app-heading">Unknown stock</h1>
      </div>
    );
  if (!target) return null;
  return (
    <CatalogTicket
      key={`${target.owner}:${target.portfolioId}:${target.epoch.session}:${catalogId}`}
      target={target}
      catalogId={catalogId}
    />
  );
}
