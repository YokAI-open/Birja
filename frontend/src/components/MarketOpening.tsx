import { fullLocalTimestamp } from "@/lib/financialDisplay";

export function MarketOpening({ nextOpen, now }: { nextOpen?: string | null; now: number }) {
  if (!nextOpen) return null;
  const remaining = Math.ceil((Date.parse(nextOpen) - now) / 60_000);
  if (!(remaining > 0)) return null;

  const hours = Math.floor(remaining / 60);
  const minutes = remaining % 60;
  const duration = [hours > 0 && `${hours} hr`, minutes > 0 && `${minutes} min`]
    .filter(Boolean)
    .join(" ");
  const localOpening = fullLocalTimestamp(nextOpen);
  return (
    <>
      <time dateTime={nextOpen} title={localOpening}>
        Opens in {duration}
      </time>
      <span className="sr-only">. Local opening time {localOpening}.</span>
    </>
  );
}
