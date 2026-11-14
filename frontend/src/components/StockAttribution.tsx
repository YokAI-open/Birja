export function StockAttribution({
  context,
  required_text,
}: {
  context: "listing" | "preview" | "valuation";
  required_text?: string;
}) {
  const label = {
    listing: "Stock price source",
    preview: "Stock preview price source",
    valuation: "Stock valuation price source",
  }[context];
  return (
    <div
      role="note"
      aria-label={label}
      className="flex flex-col gap-1 text-[13px] leading-[18px] text-muted-foreground"
    >
      <p className="font-medium text-foreground">IEX prices</p>
      <p>
        Quotes come from IEX, one US exchange, and may differ from other exchanges. Birja uses
        virtual money and simulated execution.
      </p>
      {required_text && <p className="break-words">{required_text}</p>}
    </div>
  );
}
