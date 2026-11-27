import { useEffect, useId, useRef, useState, type FormEvent } from "react";
import { Link, Navigate, useOutletContext, useParams } from "react-router";
import { useQueryClient } from "@tanstack/react-query";
import { TriangleAlert } from "lucide-react";
import { ApiError } from "@/api/client";
import { isQuote, type Order, type Quote, type Side } from "@/api/trades";
import type { PortfolioTarget } from "@/hooks/usePortfolioTarget";
import { usePortfolio } from "@/hooks/usePortfolio";
import { FreshnessBadge } from "@/components/FreshnessBadge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { useHolding } from "@/hooks/useHolding";
import { useNow } from "@/hooks/useNow";
import { usePrices } from "@/hooks/usePrices";
import { quoteKey, useQuote } from "@/hooks/useQuote";
import { useTrade } from "@/hooks/useTrade";
import { freshnessStatus } from "@/lib/age";
import { formatQuantity, formatUnitPrice, formatUsd } from "@/lib/money";
import { cn } from "@/lib/utils";
import "./tradeWorkspace.css";

type Kind = "usd" | "quantity";

const STALE_MESSAGE = "Prices are out of date, so trading is paused. We'll resume automatically.";
const NETWORK_MESSAGE = "Couldn't confirm. Check your connection and try again.";

// Definitive server refusals: nothing was written, so the next attempt is a new order.
const TERMINAL_CODES = new Set([
  "below_minimum",
  "insufficient_cash",
  "insufficient_quantity",
  "order_too_large",
  "invalid_order",
  "stale_price",
  "idempotency_conflict",
  "unknown_coin",
]);

const USD_PATTERN = /^\d+(\.\d{1,2})?$/;
const QUANTITY_PATTERN = /^\d+(\.\d{1,8})?$/;
const ZERO_PATTERN = /^0*(\.0*)?$/;

function validate(kind: Kind, raw: string): string | null {
  if (raw === "") return null;
  if (!(kind === "usd" ? USD_PATTERN : QUANTITY_PATTERN).test(raw)) {
    return kind === "usd"
      ? "Enter an amount with up to 2 decimals."
      : "Enter a quantity with up to 8 decimals.";
  }
  if (ZERO_PATTERN.test(raw)) {
    return kind === "usd" ? "Enter an amount greater than 0." : "Enter a quantity greater than 0.";
  }
  return null;
}

/** Display only: prefix a plus sign to non-negative server decimals. */
const signedUsd = (value: string) => (value.startsWith("-") ? "" : "+") + formatUsd(value);

function Row({ label, value, strong = false }: { label: string; value: string; strong?: boolean }) {
  return (
    <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className={cn("wrap-anywhere tabular-nums", strong && "text-[17px] font-semibold")}>
        {value}
      </dd>
    </div>
  );
}

function SkeletonRows() {
  return (
    <div
      role="status"
      aria-busy="true"
      aria-label="Loading preview"
      className="flex flex-col gap-3"
    >
      {Array.from({ length: 5 }, (_, i) => (
        <span key={i} className="h-5 w-full rounded-control bg-muted" />
      ))}
    </div>
  );
}

function Ticket({ target, symbol }: { target: PortfolioTarget; symbol: string }) {
  const summaryHeadingId = useId();
  const resultHeading = useRef<HTMLHeadingElement>(null);
  const focusedReceipt = useRef<number | null>(null);
  const queryClient = useQueryClient();

  const prices = usePrices();
  const portfolio = usePortfolio(target);
  const holding = useHolding(target, symbol);
  const trade = useTrade(target, symbol);
  const now = useNow(1000);
  useEffect(() => {
    if (trade.data && target.isCurrent() && focusedReceipt.current !== trade.data.trade_id) {
      focusedReceipt.current = trade.data.trade_id;
      resultHeading.current?.focus({ preventScroll: true });
    }
  }, [trade.data, target]);

  const [side, setSide] = useState<Side>("buy");
  const [buyKind, setBuyKind] = useState<Kind>("usd");
  const [input, setInput] = useState("");
  // Idempotency key of the current attempt. Cleared only by an order edit, a terminal
  // outcome or price_changed, never by a quote refetch: an attempt with an unknown
  // outcome may already have executed and only the same key makes a retry a replay.
  const keyRef = useRef<string | null>(null);

  const kind: Kind = side === "sell" ? "quantity" : buyKind;
  const fieldError = validate(kind, input);
  const coin = prices.data?.items.find((item) => item.symbol === symbol);

  let status: ReturnType<typeof freshnessStatus> | null = null;
  let age = 0;
  if (prices.data && coin) {
    const elapsed = Math.max(0, Math.floor((now - prices.dataUpdatedAt) / 1000));
    age = coin.age_seconds + elapsed;
    status = freshnessStatus(age, prices.data.fresh_seconds, prices.data.stale_seconds);
  }
  const live = status === "fresh";

  let order: Order | null = null;
  if (input !== "" && fieldError === null) {
    order =
      kind === "usd" ? { symbol, side, amount_usd: input } : { symbol, side, quantity: input };
  }
  const debouncedOrder = useDebouncedValue(order, 300);
  const quoteQuery = useQuote(target, live ? debouncedOrder : null);
  const quote: Quote | undefined = quoteQuery.isPlaceholderData ? undefined : quoteQuery.data;
  const settled =
    order !== null &&
    debouncedOrder !== null &&
    quoteKey(target, order).join("|") === quoteKey(target, debouncedOrder).join("|");

  const error = trade.error;
  const apiError = error instanceof ApiError ? error : null;
  const errorCode = apiError?.code ?? null;
  const refused = errorCode !== null && TERMINAL_CODES.has(errorCode);
  const priceChanged = errorCode === "price_changed";
  const fill = trade.data;

  const quoteApiError = quoteQuery.error instanceof ApiError ? quoteQuery.error : null;
  if (!target.isCurrent()) return null;
  if (
    (prices.data && !coin) ||
    errorCode === "unknown_coin" ||
    quoteApiError?.code === "unknown_coin"
  ) {
    return <Navigate to="/" replace />;
  }

  const edited = () => {
    if (trade.outcomeUnknown || trade.isPending) return;
    keyRef.current = null;
    trade.reset();
  };

  const confirm = (event: FormEvent) => {
    event.preventDefault();
    if (!target.isCurrent() || trade.isPending || fill) return;
    if (trade.outcomeUnknown && trade.attempt) {
      trade.mutate({
        order: trade.attempt.order,
        expectedMid: trade.attempt.expected_mid,
        idempotencyKey: trade.attempt.idempotency_key,
      });
      return;
    }
    if (!order || !quote || !settled || !live || refused) return;
    keyRef.current ??= crypto.randomUUID();
    trade.mutate(
      { order, expectedMid: quote.mid, idempotencyKey: keyRef.current },
      {
        onSuccess: () => {
          keyRef.current = null;
        },
        onError: (failure) => {
          if (!(failure instanceof ApiError) || failure.code === null) {
            return; // Unknown outcome: keep the key so a retry is a replay.
          }
          if (failure.code === "price_changed") {
            keyRef.current = null;
            const fresh = failure.detail?.quote;
            if (isQuote(fresh) && fresh.portfolio_id === target.portfolioId) {
              queryClient.setQueryData(quoteKey(target, order), fresh);
            } else {
              void queryClient.invalidateQueries({ queryKey: quoteKey(target, order) });
            }
          } else if (TERMINAL_CODES.has(failure.code)) {
            keyRef.current = null;
          }
        },
      },
    );
  };

  const newOrder = () => {
    setInput("");
    edited();
  };

  let tradeMessage: string | null = null;
  if (error && !priceChanged) {
    if (!apiError || errorCode === null) {
      tradeMessage = NETWORK_MESSAGE;
    } else if (errorCode === "stale_price") {
      tradeMessage = `${STALE_MESSAGE} ${apiError.message}`;
    } else if (errorCode === "idempotency_conflict") {
      tradeMessage =
        "This order reference belongs to a different portfolio or request. Return to the original portfolio to check it.";
    } else {
      tradeMessage = refused ? apiError.message : NETWORK_MESSAGE;
    }
  }
  const quoteMessage =
    !tradeMessage && settled && quoteQuery.isError
      ? quoteApiError?.code
        ? quoteApiError.message
        : "Couldn't load a preview. Try again in a moment."
      : null;

  const held = holding.data?.quantity;
  const locked = trade.isPending || trade.outcomeUnknown || fill !== undefined;
  const canConfirm =
    target.isCurrent() &&
    !trade.isPending &&
    (trade.outcomeUnknown || (live && settled && quote !== undefined && !refused));
  const unit = kind === "usd" ? "USD" : symbol;
  const inputLabel = kind === "usd" ? "Amount" : "Quantity";

  let preview;
  if (fill) {
    preview = (
      <>
        <h2
          ref={resultHeading}
          tabIndex={-1}
          id={summaryHeadingId}
          className="text-xl leading-7 font-semibold tracking-[-0.01em] focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        >
          Order filled
        </h2>
        <dl className="flex flex-col gap-3">
          <Row label="Quantity" value={`${formatQuantity(fill.quantity)} ${symbol}`} />
          <Row label="Price" value={formatUnitPrice(fill.exec_price)} />
          <Row label="Fee" value={formatUsd(fill.fee)} />
          <Row label="Cash change" value={signedUsd(fill.cash_delta)} />
          <Row label="New cash balance" value={formatUsd(fill.cash_after)} strong />
        </dl>
        <div className="flex flex-wrap gap-3">
          <Button asChild>
            <Link to={`/portfolios/${target.portfolioId}`}>Portfolio</Link>
          </Button>
          <Button type="button" variant="secondary" onClick={newOrder}>
            Trade again
          </Button>
        </div>
      </>
    );
  } else {
    let body;
    if (order === null) {
      body = (
        <p className="text-muted-foreground">
          Enter {kind === "usd" ? "an amount" : "a quantity"} to see the full cost.
        </p>
      );
    } else if (quote && settled) {
      body = (
        <dl className="flex flex-col gap-3">
          <Row label="Market price" value={formatUnitPrice(quote.mid)} />
          <Row label="Execution price" value={formatUnitPrice(quote.exec_price)} />
          <Row label="Fee" value={formatUsd(quote.fee)} />
          <Row label="Quantity" value={`${formatQuantity(quote.quantity)} ${symbol}`} />
          <Row label="Total cash change" value={signedUsd(quote.cash_delta)} strong />
        </dl>
      );
    } else if (live) {
      body = <SkeletonRows />;
    } else {
      body = <p className="text-muted-foreground">No preview while prices are paused.</p>;
    }
    preview = (
      <>
        <h2 id={summaryHeadingId} className="text-xl leading-7 font-semibold tracking-[-0.01em]">
          Preview
        </h2>
        {trade.outcomeUnknown && (
          <p role="status" className="rounded-control bg-warn-soft px-4 py-2 text-warn-text">
            We couldn't confirm the result. Check this order before placing another.
          </p>
        )}
        {priceChanged && (
          <p role="status" className="rounded-control bg-warn-soft px-4 py-2 text-warn-text">
            Price updated. Please review again.
          </p>
        )}
        {body}
        {tradeMessage && (
          <p role="alert" className="text-loss-text">
            {tradeMessage}
          </p>
        )}
        {quoteMessage && (
          <p role="alert" className="text-loss-text">
            {quoteMessage}
          </p>
        )}
        <Button type="submit" form="trade-form" size="lg" disabled={!canConfirm}>
          {trade.outcomeUnknown ? "Check order result" : `Confirm ${side}`}
        </Button>
      </>
    );
  }

  return (
    <div className="trade-workspace">
      <header className="trade-workspace-heading">
        <h1>Trade {symbol}</h1>
        {coin && <p>{coin.name}</p>}
      </header>
      <div className="trade-workspace-grid">
        <Card role="region" aria-label="Trade ticket" className="trade-workspace-ticket">
          <CardContent className="trade-workspace-content">
            <div className="trade-workspace-market">
              {coin ? (
                <div className="flex flex-wrap items-center gap-3">
                  <span className="trade-workspace-price">{formatUnitPrice(coin.price)}</span>
                  {status && <FreshnessBadge status={status} ageSeconds={age} asOf={coin.as_of} />}
                </div>
              ) : (
                <span className="h-9 w-1/2 rounded-control bg-muted" />
              )}
            </div>

            {status !== null && !live && (
              <p role="status" className="rounded-control bg-warn-soft px-4 py-2 text-warn-text">
                {STALE_MESSAGE}
              </p>
            )}

            <form onSubmit={confirm} className="flex flex-col gap-5" id="trade-form" noValidate>
              <div role="radiogroup" aria-label="Side" className="trade-workspace-sides">
                {(["buy", "sell"] as const).map((value) => (
                  <button
                    key={value}
                    type="button"
                    role="radio"
                    aria-checked={side === value}
                    disabled={locked}
                    onClick={() => {
                      setSide(value);
                      edited();
                    }}
                  >
                    {value === "buy" ? "Buy" : "Sell"}
                  </button>
                ))}
              </div>

              <div className="trade-workspace-balances">
                {portfolio.data && <p>Cash available {formatUsd(portfolio.data.cash)}</p>}
                {held !== undefined && (
                  <p>
                    You hold {formatQuantity(held)} {symbol}
                  </p>
                )}
              </div>

              {side === "buy" && (
                <div className="flex flex-wrap gap-2">
                  {(
                    [
                      ["usd", "Amount (USD)"],
                      ["quantity", "Quantity"],
                    ] as const
                  ).map(([value, label]) => (
                    <Button
                      key={value}
                      type="button"
                      size="sm"
                      variant={buyKind === value ? "default" : "secondary"}
                      aria-pressed={buyKind === value}
                      disabled={locked}
                      onClick={() => {
                        setBuyKind(value);
                        edited();
                      }}
                    >
                      {label}
                    </Button>
                  ))}
                </div>
              )}

              <div className="flex flex-col gap-2">
                <label htmlFor="trade-input" className="text-[13px] leading-[18px] font-medium">
                  {inputLabel}
                </label>
                <div className="relative">
                  <Input
                    id="trade-input"
                    inputMode="decimal"
                    autoComplete="off"
                    className="min-h-13 pr-16 text-right tabular-nums"
                    value={input}
                    disabled={locked}
                    aria-invalid={fieldError !== null}
                    aria-describedby={fieldError ? "trade-input-error" : undefined}
                    onChange={(event) => {
                      setInput(event.target.value);
                      edited();
                    }}
                  />
                  <span
                    aria-hidden="true"
                    className="pointer-events-none absolute inset-y-0 right-4 flex items-center text-muted-foreground"
                  >
                    {unit}
                  </span>
                </div>
                {fieldError && (
                  <p
                    id="trade-input-error"
                    className="flex items-center gap-1.5 text-[13px] leading-[18px] text-loss-text"
                  >
                    <TriangleAlert aria-hidden="true" className="size-4" />
                    {fieldError}
                  </p>
                )}
              </div>
            </form>
          </CardContent>
        </Card>

        <Card role="region" aria-labelledby={summaryHeadingId} className="trade-workspace-preview">
          <CardContent className="trade-workspace-content">{preview}</CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function TradePage() {
  const target = useOutletContext<PortfolioTarget>();
  const symbol = (useParams().symbol ?? "").toUpperCase();
  return (
    <Ticket
      key={`${target.owner}:${target.portfolioId}:${target.epoch.session}:${symbol}`}
      target={target}
      symbol={symbol}
    />
  );
}
