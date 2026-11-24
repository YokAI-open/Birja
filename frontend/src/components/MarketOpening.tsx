export function MarketOpening({ nextOpen, now }: { nextOpen?: string | null; now: number }) {
  if (!nextOpen) return null;
  const opening = new Date(nextOpen);
  const remaining = Math.ceil((opening.getTime() - now) / 60_000);
  if (!(remaining > 0)) return null;

  const hours = Math.floor(remaining / 60);
  const minutes = remaining % 60;
  const duration = [hours > 0 && `${hours} hr`, minutes > 0 && `${minutes} min`]
    .filter(Boolean)
    .join(" ");
  return (
    <>
      Opens in {duration} (
      <time dateTime={nextOpen}>
        {opening.toLocaleString(undefined, {
          weekday: "short",
          month: "short",
          day: "numeric",
          hour: "numeric",
          minute: "2-digit",
          timeZoneName: "short",
        })}
      </time>
      ).
    </>
  );
}
