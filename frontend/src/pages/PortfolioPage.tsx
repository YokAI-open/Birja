import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { usePortfolio } from "@/hooks/usePortfolio";
import { useNow } from "@/hooks/useNow";
import { PortfolioFreshness } from "@/components/PortfolioFreshness";
import { PortfolioHoldings, PortfolioOutcome } from "@/components/PortfolioHoldings";
import { PortfolioAllocation } from "@/components/PortfolioAllocation";
import { formatUsd } from "@/lib/money";

export default function PortfolioPage() {
  const { data, isPending, isError, isFetching, refetch, dataUpdatedAt } = usePortfolio();
  const now = useNow();
  const elapsed = Math.max(0, Math.floor((now - dataUpdatedAt) / 1000));
  return (
    <div className="my-8 flex flex-col gap-4 text-[15px] leading-[22px]">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-[32px] leading-9 font-medium tracking-[-0.02em] md:text-[40px] md:leading-[44px]">
          Portfolio
        </h1>
        <Button
          variant="secondary"
          className="min-h-11 motion-reduce:transform-none motion-reduce:transition-none"
          disabled={isFetching}
          onClick={() => void refetch()}
        >
          {isFetching ? "Refreshing portfolio…" : "Refresh portfolio"}
        </Button>
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
              role="alert"
              className="flex flex-wrap items-center gap-3 rounded-control bg-warn-soft p-4 text-warn-text"
            >
              <p>Couldn&apos;t refresh your portfolio. Showing the last successful update.</p>
              <Button variant="secondary" onClick={() => void refetch()} disabled={isFetching}>
                Retry refresh
              </Button>
            </div>
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
                <PortfolioFreshness
                  portfolio={data}
                  elapsed={elapsed}
                  dataUpdatedAt={dataUpdatedAt}
                  isFetching={isFetching}
                  isError={isError}
                />
              </CardContent>
            </Card>
            <Card role="region" aria-label="Cash" className="min-w-0 lg:col-span-4">
              <CardContent>
                <h2 className="font-medium">Cash</h2>
                <p className="text-[32px] leading-9 font-medium wrap-anywhere tabular-nums md:text-[40px] md:leading-[44px]">
                  {formatUsd(data.cash)}
                </p>
                <PortfolioAllocation portfolio={data} />
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
