export function MarketOpening({ nextOpen, now }: { nextOpen?: string | null; now: number }) {
  if (!nextOpen) return null;
  const remaining = Math.ceil((Date.parse(nextOpen) - now) / 60_000);
  if (!(remaining > 0)) return null;

  const hours = Math.floor(remaining / 60);
  const minutes = remaining % 60;
  const duration = [hours > 0 && `${hours} hr`, minutes > 0 && `${minutes} min`]
    .filter(Boolean)
    .join(" ");
  return <time dateTime={nextOpen}>Opens in {duration}</time>;
}
