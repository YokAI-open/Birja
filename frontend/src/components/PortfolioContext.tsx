/** Contextual metadata; the enclosing target boundary owns authorization. */
export function PortfolioContext({ name }: { name: string }) {
  return (
    <dl className="flex min-w-0 flex-col gap-2">
      <dt className="text-[13px] leading-[18px] font-medium text-muted-foreground">Portfolio</dt>
      <dd className="min-w-0 break-words text-[15px] leading-[22px] font-medium text-foreground [overflow-wrap:anywhere]">
        {name}
      </dd>
    </dl>
  );
}
