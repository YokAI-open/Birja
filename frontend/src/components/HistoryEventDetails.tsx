import { useCallback, useId, useRef, useState, type ReactNode } from "react";
import type { DividendTerms, EventHistoryItem } from "@/api/eventHistory";
import { Button } from "@/components/ui/button";
import { formatQuantity, formatUnitPrice, formatUsd } from "@/lib/money";

function signed(value: string) {
  if (/^-?0+(\.0+)?$/.test(value)) return formatUsd("0");
  return value.startsWith("-") ? `−${formatUsd(value.slice(1))}` : `+${formatUsd(value)}`;
}

export function HistoryEventTime({ value }: { value: string }) {
  const local = new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    timeZoneName: "short",
  }).format(new Date(value));
  return (
    <time dateTime={value} title={value} aria-label={`${local}; UTC ${value}`}>
      {local}
    </time>
  );
}

export function HistoryEventTitle({ item }: { item: EventHistoryItem }) {
  const title =
    item.kind === "trade"
      ? item.side === "buy"
        ? "Buy"
        : "Sell"
      : item.kind === "dividend"
        ? "Dividend"
        : item.kind === "split"
          ? "Forward split"
          : item.outcome.startsWith("held_")
            ? "Dividend correction held"
            : item.outcome === "verified_no_change"
              ? "Dividend correction — no cash adjustment"
              : "Dividend correction";
  return <span className="font-medium">{title}</span>;
}

export function HistoryEventCash({ item }: { item: EventHistoryItem }) {
  const noCash =
    item.kind === "split" ||
    (item.kind === "dividend_correction" && item.outcome.startsWith("held_"));
  const positive = !item.cash_delta.startsWith("-") && !/^0+(\.0+)?$/.test(item.cash_delta);
  return (
    <span
      className={`wrap-anywhere tabular-nums ${item.cash_delta.startsWith("-") ? "text-loss-text" : positive ? "text-gain-text" : ""}`}
    >
      {noCash ? "No cash changed" : signed(item.cash_delta)}
    </span>
  );
}

function Detail({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="min-w-0">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="wrap-anywhere tabular-nums">{children}</dd>
    </div>
  );
}

function Terms({ terms }: { terms: DividendTerms }) {
  const rate = terms.rate.includes(".")
    ? terms.rate.replace(/0+$/, "").replace(/\.$/, "")
    : terms.rate;
  return (
    <>
      <Detail label="Eligible shares at cutoff">{formatQuantity(terms.eligible_quantity)}</Detail>
      <Detail label="Gross rate">USD {rate} per share</Detail>
      <Detail label="Eligibility cutoff">
        <HistoryEventTime value={terms.cutoff} />
      </Detail>
      <Detail label="Ex-dividend date">{terms.ex_date ?? "Not provided"}</Detail>
      <Detail label="Record date">{terms.record_date ?? "Not provided"}</Detail>
      <Detail label="Payable date (New York calendar date)">{terms.payable_date}</Detail>
    </>
  );
}

export function HistoryEventDetails({
  item,
  anchorPrefix = "history-",
}: {
  item: EventHistoryItem;
  anchorPrefix?: string;
}) {
  const [originalOpen, setOriginalOpen] = useState(false);
  const originalButton = useRef<HTMLButtonElement>(null);
  const headingId = useId();
  const captureOriginalHeading = useCallback((node: HTMLHeadingElement | null) => {
    node?.focus({ preventScroll: true });
  }, []);
  return (
    <div className="flex min-w-0 flex-col gap-4 text-[13px] leading-[18px]">
      <dl className="grid min-w-0 gap-2">
        {item.kind === "trade" ? (
          <>
            <Detail label={item.asset_type === "stock" ? "Shares" : "Quantity"}>
              {formatQuantity(item.quantity)}
            </Detail>
            <Detail label={item.asset_type === "stock" ? "IEX execution price" : "Execution price"}>
              {formatUnitPrice(item.exec_price)}
            </Detail>
            <Detail label={item.asset_type === "stock" ? "Commission" : "Fee"}>
              {formatUsd(item.fee)}
            </Detail>
            <Detail label="Filled">
              <HistoryEventTime value={item.filled_at} />
            </Detail>
            {item.asset_type === "stock" && (
              <>
                <Detail label="Source quote time">
                  <HistoryEventTime value={item.quote_at!} />
                </Detail>
                <Detail label="Price source">
                  IEX prices · Simulated execution using IEX bid/ask. Not a consolidated US market
                  price.
                </Detail>
              </>
            )}
          </>
        ) : item.kind === "dividend" ? (
          <>
            <Detail label="Dividend explanation">
              Gross ordinary USD dividend. No tax withholding or automatic reinvestment.
            </Detail>
            <Terms terms={item} />
            <Detail label="Credited amount">{formatUsd(item.credited_amount)}</Detail>
            <Detail label="Credited">
              <HistoryEventTime value={item.credited_at} />
            </Detail>
            <Detail label="Payment reference">{item.payment_reference}</Detail>
          </>
        ) : item.kind === "split" ? (
          <>
            <Detail label="Verified ratio (new:old)">
              {item.ratio_new}:{item.ratio_old}
            </Detail>
            <Detail label="Shares before → after">
              {formatQuantity(item.quantity_before)} → {formatQuantity(item.quantity_after)}
            </Detail>
            <Detail label="Total cost basis before → after">
              {formatUsd(item.cost_basis_before)} → {formatUsd(item.cost_basis_after)} (unchanged)
            </Detail>
            <Detail label="Effective">
              <HistoryEventTime value={item.effective_at} />
            </Detail>
            <Detail label="Cash meaning">No cash changed</Detail>
          </>
        ) : (
          <>
            <Detail label="Original payment reference">{item.payment_reference}</Detail>
            <Detail label="Correction reference">{item.decision_reference}</Detail>
            {item.outcome.startsWith("held_") && (
              <Detail label="Held for review">
                <span className="text-warn-text">Held when recorded</span>
                <p>
                  {item.outcome === "held_unaffordable"
                    ? "Not enough available cash for this correction. No cash changed."
                    : "The corrected dividend terms need verification. No cash changed."}
                </p>
              </Detail>
            )}
            <Detail label="Applied change">
              <span>Applied change: {signed(item.applied_delta)}</span>
            </Detail>
            {item.proposed_delta !== null && (
              <Detail label="Proposed change (not the applied cash change)">
                {signed(item.proposed_delta)}
              </Detail>
            )}
            {item.desired_total !== null && (
              <Detail label="Verified total now owed">{formatUsd(item.desired_total)}</Detail>
            )}
            <Detail label="Previously applied total">
              {formatUsd(item.cumulative_applied_before)}
            </Detail>
            {item.terms !== null && <Terms terms={item.terms} />}
          </>
        )}
      </dl>
      {item.kind === "dividend_correction" && (
        <>
          <Button
            ref={originalButton}
            variant="secondary"
            className="min-h-11 self-start whitespace-normal text-left"
            aria-expanded={originalOpen}
            aria-controls={originalOpen ? headingId : undefined}
            onClick={() => {
              const loaded = document.getElementById(`${anchorPrefix}${item.payment_reference}`);
              if (loaded) {
                loaded.focus();
                return;
              }
              setOriginalOpen(true);
            }}
          >
            View original dividend
          </Button>
          {originalOpen && (
            <section
              className="min-w-0 rounded-control border border-border p-4"
              aria-labelledby={headingId}
            >
              <h3
                id={headingId}
                tabIndex={-1}
                className="scroll-mb-24 font-medium wrap-anywhere focus-visible:outline-2 focus-visible:outline-ring"
                ref={captureOriginalHeading}
              >
                Original dividend · {item.original.symbol} · {item.original.name}
              </h3>
              <p>
                <HistoryEventTime value={item.original.recorded_at} />
              </p>
              <p>
                <HistoryEventCash item={item.original} />
              </p>
              <HistoryEventDetails item={item.original} />
              <Button
                variant="secondary"
                className="mt-4 min-h-11"
                onClick={() => {
                  setOriginalOpen(false);
                  originalButton.current?.focus({ preventScroll: true });
                }}
              >
                Back to correction
              </Button>
            </section>
          )}
        </>
      )}
    </div>
  );
}
