/** Contextual metadata; the enclosing target boundary owns authorization. */
export function PortfolioContext({ name, compact = false }: { name: string; compact?: boolean }) {
  return (
    <dl className="flex min-w-0 flex-col gap-1">
      <dt className={compact ? "sr-only" : "text-sm font-medium text-muted-foreground"}>
        Portfolio
      </dt>
      <dd className="min-w-0 break-words text-lg leading-snug font-medium text-foreground [overflow-wrap:anywhere]">
        {name}
      </dd>
    </dl>
  );
}
