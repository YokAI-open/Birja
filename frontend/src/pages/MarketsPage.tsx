import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { FreshnessBadge } from "@/components/FreshnessBadge";
import { useNow } from "@/hooks/useNow";
import { usePrices } from "@/hooks/usePrices";
import { formatAge, freshnessStatus } from "@/lib/age";
import { formatUnitPrice } from "@/lib/money";

function MarketsPage() {
  const { data, isPending, isError, refetch, dataUpdatedAt } = usePrices();
  const now = useNow(1000);
  // Server age plus local elapsed time since the response; never browser clock vs as_of.
  const elapsed = Math.max(0, Math.floor((now - dataUpdatedAt) / 1000));
  const ages = data ? data.items.map((item) => item.age_seconds + elapsed) : [];
  const maxAge = ages.length > 0 ? Math.max(...ages) : null;

  let body;
  if (isPending) {
    body = (
      <div role="status" aria-busy="true" aria-label="Loading prices" className="flex flex-col">
        {Array.from({ length: 5 }, (_, i) => (
          <div key={i} className="flex h-[52px] items-center border-b border-border">
            <span className="h-4 w-full rounded-control bg-muted" />
          </div>
        ))}
      </div>
    );
  } else if (!data) {
    // Only when there is nothing to show: a failed background refetch keeps the last
    // good data (TanStack sets isError but keeps data), so badges age toward Stale.
    body = (
      <div className="flex flex-col items-start gap-4">
        <p role="alert" className="text-loss-text">
          Can&apos;t load prices right now.
        </p>
        <Button variant="secondary" onClick={() => void refetch()}>
          Try again
        </Button>
      </div>
    );
  } else if (data.items.length === 0) {
    body = (
      <p className="text-muted-foreground">Prices are loading. They appear within a minute.</p>
    );
  } else {
    body = (
      <div className="overflow-x-auto">
        <table aria-label="Markets" className="w-full border-collapse text-left">
          <thead>
            <tr className="border-b border-border">
              <th
                scope="col"
                className="h-10 text-[13px] leading-[18px] font-medium text-muted-foreground"
              >
                Coin
              </th>
              <th
                scope="col"
                className="h-10 text-right text-[13px] leading-[18px] font-medium text-muted-foreground"
              >
                Price
              </th>
              <th
                scope="col"
                className="h-10 pl-4 text-[13px] leading-[18px] font-medium text-muted-foreground"
              >
                Updated
              </th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((item, i) => {
              const ageNow = ages[i] ?? item.age_seconds;
              return (
                <tr key={item.symbol} className="h-[52px] border-b border-border hover:bg-accent">
                  <td>
                    <span className="block font-semibold">{item.symbol}</span>
                    <span className="block text-[13px] leading-[18px] text-muted-foreground">
                      {item.name}
                    </span>
                  </td>
                  <td className="text-right tabular-nums">{formatUnitPrice(item.price)}</td>
                  <td className="pl-4">
                    <FreshnessBadge
                      status={freshnessStatus(ageNow, data.fresh_seconds, data.stale_seconds)}
                      ageSeconds={ageNow}
                    />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    );
  }

  return (
    <div className="mx-auto my-8 flex max-w-3xl flex-col gap-6">
      <div className="flex items-baseline justify-between gap-4">
        <h1 className="text-[32px] leading-9 font-medium tracking-[-0.02em] md:text-[40px] md:leading-[44px]">
          Markets
        </h1>
        {maxAge !== null && (
          <p className="text-[13px] leading-[18px] text-muted-foreground">
            Oldest price {formatAge(maxAge)}
          </p>
        )}
      </div>
      {isError && data && (
        <p role="status" className="rounded-control bg-warn-soft px-4 py-2 text-warn-text">
          Couldn&apos;t refresh prices. Showing the last update.
        </p>
      )}
      <Card>
        <CardContent>{body}</CardContent>
      </Card>
    </div>
  );
}

export default MarketsPage;
