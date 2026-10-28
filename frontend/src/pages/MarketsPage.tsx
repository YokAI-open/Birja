import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { usePrices } from "@/hooks/usePrices";
import { formatUnitPrice } from "@/lib/money";

function MarketsPage() {
  const { data, isPending, isError, refetch } = usePrices();

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
  } else if (isError) {
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
              {/* 03-06 adds the freshness column here. */}
            </tr>
          </thead>
          <tbody>
            {data.items.map((item) => (
              <tr key={item.symbol} className="h-[52px] border-b border-border hover:bg-accent">
                <td>
                  <span className="block font-semibold">{item.symbol}</span>
                  <span className="block text-[13px] leading-[18px] text-muted-foreground">
                    {item.name}
                  </span>
                </td>
                <td className="text-right tabular-nums">{formatUnitPrice(item.price)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  return (
    <div className="mx-auto my-8 flex max-w-3xl flex-col gap-6">
      <h1 className="text-[32px] leading-9 font-medium tracking-[-0.02em] md:text-[40px] md:leading-[44px]">
        Markets
      </h1>
      <Card>
        <CardContent>{body}</CardContent>
      </Card>
    </div>
  );
}

export default MarketsPage;
