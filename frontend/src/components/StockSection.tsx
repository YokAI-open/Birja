import { useRef } from "react";
import type { StockItem } from "@/api/stocks";
import { StockAttribution } from "@/components/StockAttribution";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useStocks } from "@/hooks/useStocks";
import { formatAge } from "@/lib/age";
import { formatUnitPrice } from "@/lib/money";

const permissionNotice =
  "Stock prices are unavailable while data permissions are being verified. Crypto trading is available.";
const refreshNotice =
  "Couldn’t refresh stock prices. Showing the last permitted update with its original time.";

function StockTime({ value, exchange = false }: { value: string; exchange?: boolean }) {
  const zone = exchange ? "America/New_York" : Intl.DateTimeFormat().resolvedOptions().timeZone;
  return (
    <time dateTime={value} className="break-words tabular-nums">
      {new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeStyle: "long",
        timeZone: zone,
      }).format(new Date(value))}{" "}
      ({zone})
    </time>
  );
}
function Identity({ item }: { item: StockItem }) {
  return (
    <>
      <span className="block text-[15px] leading-[22px] font-medium">{item.symbol}</span>
      <span className="block text-[15px] leading-[22px] break-words">{item.company_name}</span>
      <span className="block text-[13px] leading-[18px] text-muted-foreground">
        {item.listing_exchange} · USD
      </span>
    </>
  );
}
function Session({ item }: { item: StockItem }) {
  if (item.session.state === "unknown")
    return <p>Session unavailable. We cannot verify the regular trading session.</p>;
  if (item.session.state === "closed")
    return (
      <p>
        Market closed.{" "}
        {item.session.next_open_at ? (
          <>
            Next regular session: <StockTime value={item.session.next_open_at} exchange />.
          </>
        ) : (
          "The next regular session is not yet verified."
        )}
      </p>
    );
  return (
    <div className="flex flex-col gap-1">
      <p>Market open</p>
      <p>
        Regular session: <StockTime value={item.session.opens_at!} exchange /> –{" "}
        <StockTime value={item.session.closes_at!} exchange />
      </p>
    </div>
  );
}
function QuoteTime({ item, allowed }: { item: StockItem; allowed: boolean }) {
  const quote = allowed ? item.quote : null;
  if (!quote) return <p>{allowed ? "Waiting for an IEX quote." : "Unavailable"}</p>;
  if (!Number.isFinite(Date.parse(quote.event_at)))
    return <p>Quote time unavailable. This quote cannot be used for trading.</p>;
  const previous = item.quote_reason === "session_unavailable" && item.session.state === "open";
  const stale = item.quote_reason === "stale";
  return (
    <div className="flex flex-col items-start gap-1">
      {item.session.state === "closed" ? (
        <p>Last quote</p>
      ) : previous ? (
        <p>Previous session</p>
      ) : (
        <Badge variant={stale ? "warning" : "success"}>
          {stale ? "Out of date" : "Recent"} · {formatAge(quote.age_seconds)}
        </Badge>
      )}
      <StockTime value={quote.event_at} />
      {stale && <p>This quote is out of date. Waiting for a recent IEX update.</p>}
    </div>
  );
}
function Side({ item, allowed, side }: { item: StockItem; allowed: boolean; side: "bid" | "ask" }) {
  return (
    <span className="text-[15px] leading-[22px] font-medium tabular-nums">
      {allowed && item.quote ? formatUnitPrice(item.quote[side]) : "Unavailable"}
    </span>
  );
}

export function StockSection() {
  const heading = useRef<HTMLHeadingElement>(null);
  const { data, isPending, isError, isFetching, refetch } = useStocks();
  const retry = async () => {
    const result = await refetch();
    if (!result?.isError) heading.current?.focus();
  };
  const allowed = data?.admission.state === "approved";
  const items = data?.items ?? [];
  // Only categorical transitions enter the live region. Source ages stay ordinary text.
  const categories = [
    ...new Set(
      items.map(
        (item) =>
          `${item.session.state === "open" ? "Market open" : item.session.state === "closed" ? "Market closed" : "Session unavailable"}; ${item.quote_reason === "stale" ? "Out of date" : item.quote_reason === "recent" ? "Recent quotes" : "Waiting for a current quote"}`,
      ),
    ),
  ].join(". ");
  const message = isPending
    ? "Loading stocks"
    : !data
      ? "Can’t load stock prices right now. Retry stock prices or continue with crypto."
      : !allowed
        ? permissionNotice
        : isError
          ? refreshNotice
          : categories;
  return (
    <section aria-labelledby="stocks-heading" className="min-w-0">
      <Card>
        <CardContent className="gap-4">
          <h2 ref={heading} tabIndex={-1} id="stocks-heading" className="font-medium">
            US stocks · 20
          </h2>
          <StockAttribution context="listing" required_text={data?.attribution.required_text} />
          <p>Stock trading coming later. You can browse prices; crypto trading is available.</p>
          <p className="text-[13px] leading-[18px] text-muted-foreground">
            IEX quotes are checked about every minute. A check may return an older quote; the time
            shown is the source quote time.
          </p>
          <p
            role="status"
            aria-atomic="true"
            aria-label={isPending ? "Loading stocks" : undefined}
            aria-busy={isPending}
            className={
              data && allowed && !isError
                ? "sr-only"
                : "text-[13px] leading-[18px] text-muted-foreground"
            }
          >
            {message}
          </p>
          {data && allowed && isError && (
            <Button
              variant="secondary"
              disabled={isFetching}
              className="min-h-11 self-start whitespace-normal"
              onClick={() => void retry()}
            >
              {isFetching ? "Retrying stock prices…" : "Retry stock prices"}
            </Button>
          )}
          {isPending ? (
            <div aria-hidden="true" className="flex flex-col gap-4">
              {Array.from({ length: 20 }, (_, i) => (
                <div key={i} className="h-[320px] rounded-control bg-muted lg:h-[160px]" />
              ))}
            </div>
          ) : !data ? (
            <Button
              variant="secondary"
              disabled={isFetching}
              className="min-h-11 self-start whitespace-normal"
              onClick={() => void retry()}
            >
              {isFetching ? "Retrying stock prices…" : "Retry stock prices"}
            </Button>
          ) : (
            <>
              {allowed && !items.some((item) => item.quote) && (
                <div>
                  <h3 className="font-medium">Stock quotes are not ready</h3>
                  <p>
                    The stock list is available. Quotes will appear after data access is verified
                    and an IEX update arrives.
                  </p>
                </div>
              )}
              <div className="hidden lg:block">
                <table
                  aria-label="US stocks"
                  className="w-full table-fixed border-collapse text-left text-[13px] leading-[18px]"
                >
                  <thead>
                    <tr className="border-b border-border">
                      {["Stock", "Bid", "Ask", "Quote time", "Session", "Status"].map((name, i) => (
                        <th
                          key={name}
                          scope="col"
                          className={`py-3 pr-3 font-medium text-muted-foreground ${i === 1 || i === 2 ? "w-[10%] text-right" : ""}`}
                        >
                          {name}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((item) => (
                      <tr
                        key={item.id}
                        className="h-[52px] border-b border-border align-top hover:bg-accent"
                      >
                        <td className="py-4 pr-3">
                          <Identity item={item} />
                        </td>
                        <td className="py-4 pr-3 text-right">
                          <Side item={item} side="bid" allowed={allowed} />
                        </td>
                        <td className="py-4 pr-3 text-right">
                          <Side item={item} side="ask" allowed={allowed} />
                        </td>
                        <td className="py-4 pr-3">
                          <QuoteTime item={item} allowed={allowed} />
                        </td>
                        <td className="py-4 pr-3">
                          <Session item={item} />
                        </td>
                        <td className="py-4">
                          <p>Stock status unverified.</p>
                          <p>Trading coming later.</p>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <ul aria-label="US stocks" className="flex flex-col lg:hidden">
                {items.map((item) => (
                  <li
                    key={item.id}
                    className="flex min-w-0 flex-col gap-3 border-b border-border py-4"
                  >
                    <div>
                      <Identity item={item} />
                    </div>
                    <dl className="grid grid-cols-2 gap-4">
                      <div>
                        <dt className="text-[13px] leading-[18px] text-muted-foreground">Bid</dt>
                        <dd>
                          <Side item={item} side="bid" allowed={allowed} />
                        </dd>
                      </div>
                      <div>
                        <dt className="text-[13px] leading-[18px] text-muted-foreground">Ask</dt>
                        <dd>
                          <Side item={item} side="ask" allowed={allowed} />
                        </dd>
                      </div>
                    </dl>
                    <div className="text-[13px] leading-[18px]">
                      <QuoteTime item={item} allowed={allowed} />
                    </div>
                    <div className="text-[13px] leading-[18px] text-muted-foreground">
                      <Session item={item} />
                      <p>Stock status unverified.</p>
                      <p>Trading coming later.</p>
                    </div>
                  </li>
                ))}
              </ul>
            </>
          )}
        </CardContent>
      </Card>
    </section>
  );
}
