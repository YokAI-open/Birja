import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { usePortfolio } from "@/hooks/usePortfolio";
import { useNow } from "@/hooks/useNow";
import { formatAge, freshnessStatus } from "@/lib/age";
import { PortfolioHoldings, PortfolioOutcome } from "@/components/PortfolioHoldings";
import { fullLocalTimestamp } from "@/lib/financialDisplay";
import { formatUsd } from "@/lib/money";

export default function PortfolioPage() {
  const { data, isPending, isError, isFetching, refetch, dataUpdatedAt } = usePortfolio();
  const now = useNow();
  const elapsed = Math.max(0, Math.floor((now - dataUpdatedAt) / 1000));
  const ages =
    data?.holdings.flatMap((h) => (h.age_seconds === null ? [] : [h.age_seconds + elapsed])) ?? [];
  const oldest = ages.length > 0 ? Math.max(...ages) : null;
  const status =
    data && oldest !== null
      ? freshnessStatus(oldest, data.fresh_seconds, data.stale_seconds)
      : null;
  return (
    <div className="my-8 flex flex-col gap-4 text-[15px] leading-[22px]">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-[32px] leading-9 font-medium tracking-[-0.02em] md:text-[40px] md:leading-[44px]">
          Portfolio
        </h1>
        <Button variant="secondary" disabled={isFetching} onClick={() => void refetch()}>
          Refresh portfolio
        </Button>
        {isFetching && data && (
          <span role="status" className="sr-only">
            Refreshing portfolio…
          </span>
        )}
      </div>
      {isPending ? (
        <div
          role="status"
          aria-label="Loading your portfolio"
          aria-busy="true"
          className="grid gap-4 md:grid-cols-2 lg:grid-cols-3"
        >
          {[0, 1].map((i) => (
            <Card key={i} className={i === 0 ? "lg:col-span-2" : ""}>
              <CardContent>
                <div className="h-4 w-1/2 rounded-control bg-muted" />
                <div className="h-11 w-full rounded-control bg-muted" />
                <div className="h-6 w-3/4 rounded-control bg-muted" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : !data ? (
        <Card>
          <CardContent>
            <p role="alert">Can&apos;t load your portfolio right now. Try again.</p>
            <Button onClick={() => void refetch()} disabled={isFetching}>
              Try again
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          {isError && (
            <div
              role="status"
              className="flex flex-wrap items-center gap-3 rounded-control bg-warn-soft p-4 text-warn-text"
            >
              <p>Couldn&apos;t refresh your portfolio. Showing the last successful update.</p>
              <Button variant="secondary" onClick={() => void refetch()} disabled={isFetching}>
                Retry refresh
              </Button>
            </div>
          )}
          {!data.valuation_complete && (
            <p role="status" className="rounded-control bg-warn-soft p-4 text-warn-text">
              Some holdings have no price. Total value, profit/loss and allocation are unavailable
              until prices return.
            </p>
          )}
          {data.valuation_complete && status && status !== "fresh" && (
            <p role="status" className="rounded-control bg-warn-soft p-4 text-warn-text">
              {status === "stale"
                ? "Some prices are out of date. Values use the last known prices."
                : "Some prices are delayed. Values use the last known prices."}
            </p>
          )}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-12">
            <Card
              role="region"
              aria-label="Total portfolio value"
              className="min-w-0 bg-[image:var(--highlight-gradient)] lg:col-span-8"
            >
              <CardContent className="items-start rounded-control bg-primary/80 p-4 text-primary-foreground">
                <h2 className="font-medium">Total portfolio value</h2>
                <p className="w-full text-[32px] leading-9 font-medium wrap-anywhere tabular-nums md:text-[40px] md:leading-[44px]">
                  {data.total_value === null ? "Value unavailable" : formatUsd(data.total_value)}
                </p>
                <h3 className="font-medium">Total profit/loss</h3>
                <div className="flex flex-wrap gap-2 tabular-nums">
                  {data.total_pl === null ? (
                    "Unavailable"
                  ) : (
                    <PortfolioOutcome value={data.total_pl} dollars />
                  )}
                  {data.total_pl_percent === null ? (
                    <span>{data.valuation_complete ? "Not applicable" : "Unavailable"}</span>
                  ) : (
                    <PortfolioOutcome value={data.total_pl_percent} />
                  )}
                </div>
                <p>Compared with your {formatUsd(data.starting_cash)} start</p>
                <p className="text-[13px] leading-[18px] font-medium">
                  {data.holdings.length === 0
                    ? "No market prices needed"
                    : data.valuation_complete
                      ? "Values use market mid prices."
                      : "Valuation incomplete"}
                </p>
                {oldest !== null && (
                  <p className="text-[13px] leading-[18px] font-medium">
                    {!data.valuation_complete
                      ? "Oldest available price"
                      : status === "fresh"
                        ? "Oldest price"
                        : "Last-known valuation · oldest price"}{" "}
                    {formatAge(oldest)}
                  </p>
                )}
                {data.prices_as_of !== null && (
                  <p className="text-[13px] leading-[18px] font-medium wrap-anywhere">
                    Price as of{" "}
                    <time
                      dateTime={data.prices_as_of}
                      title={data.prices_as_of}
                      aria-label={fullLocalTimestamp(data.prices_as_of)}
                    >
                      {fullLocalTimestamp(data.prices_as_of)}
                    </time>
                  </p>
                )}
                <p className="text-[13px] leading-[18px] font-medium">
                  Calculated at{" "}
                  <time
                    dateTime={data.valued_at}
                    title={data.valued_at}
                    aria-label={fullLocalTimestamp(data.valued_at)}
                  >
                    {fullLocalTimestamp(data.valued_at)}
                  </time>
                </p>
              </CardContent>
            </Card>
            <Card role="region" aria-label="Cash" className="min-w-0 lg:col-span-4">
              <CardContent>
                <h2 className="font-medium">Cash</h2>
                <p className="text-[32px] leading-9 font-medium wrap-anywhere tabular-nums md:text-[40px] md:leading-[44px]">
                  {formatUsd(data.cash)}
                </p>
              </CardContent>
            </Card>
            <PortfolioHoldings
              holdings={data.holdings}
              elapsed={elapsed}
              freshSeconds={data.fresh_seconds}
              staleSeconds={data.stale_seconds}
            />
          </div>
        </>
      )}
    </div>
  );
}
