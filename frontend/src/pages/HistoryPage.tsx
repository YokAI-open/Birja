import { useCallback, useRef, useState } from "react";
import { Link } from "react-router";
import type { HistoryItem } from "@/api/history";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useHistory } from "@/hooks/useHistory";
import { formatQuantity, formatUnitPrice, formatUsd } from "@/lib/money";

function total(value: string) {
  if (/^-?0+(\.0+)?$/.test(value)) return formatUsd("0");
  return value.startsWith("-") ? `−${formatUsd(value.slice(1))}` : `+${formatUsd(value)}`;
}

function fillTime(value: string) {
  const local = new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    timeZoneName: "short",
  }).format(new Date(value));
  return (
    <time dateTime={value} title={value} aria-label={`${local}; UTC ${value}`}>
      {local}
    </time>
  );
}

function fields(item: HistoryItem) {
  return [
    ["Date/time", fillTime(item.created_at)],
    [
      "Coin",
      <span className="wrap-anywhere">
        <span className="font-medium">{item.symbol}</span> · {item.name}
      </span>,
    ],
    [
      "Side",
      <span className="rounded-pill bg-muted px-2 py-1 text-sm">
        {item.side === "buy" ? "Buy" : "Sell"}
      </span>,
    ],
    ["Quantity", formatQuantity(item.quantity)],
    ["Execution price", formatUnitPrice(item.exec_price)],
    ["Fee", formatUsd(item.fee)],
    ["Total cash change", total(item.total)],
  ] as const;
}

export default function HistoryPage() {
  const {
    data,
    dataUpdatedAt,
    isPending,
    isError,
    isFetching,
    isFetchingNextPage,
    isFetchNextPageError,
    hasNextPage,
    fetchNextPage,
    refetch,
  } = useHistory();
  const items = data?.pages.flatMap((page) => page.items);
  const appendButton = useRef<HTMLButtonElement | null>(null);
  const focusEnd = useRef(false);
  const [announcement, setAnnouncement] = useState<{ updatedAt: number; text: string } | null>(
    null,
  );
  const captureAppendButton = useCallback((node: HTMLButtonElement | null) => {
    if (!node && appendButton.current === document.activeElement) focusEnd.current = true;
    appendButton.current = node;
  }, []);

  async function loadMore() {
    if (isFetching || !hasNextPage) return;
    const previousCount = items?.length ?? 0;
    const result = await fetchNextPage({ cancelRefetch: false });
    if (!result.isError) {
      const count =
        result.data?.pages.reduce((sum, page) => sum + page.items.length, 0) ?? previousCount;
      setAnnouncement({
        updatedAt: result.dataUpdatedAt,
        text: `${count - previousCount} more trades loaded. ${count} trades shown.`,
      });
    }
  }
  return (
    <div className="my-8 flex flex-col gap-4 text-[15px] leading-[22px]">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-[32px] leading-9 font-medium tracking-[-0.02em] md:text-[40px] md:leading-[44px]">
          History
        </h1>
        <Button
          variant="secondary"
          className="min-h-11 motion-reduce:transform-none motion-reduce:transition-none"
          disabled={isFetching}
          onClick={() => void refetch()}
        >
          {isFetching && !isFetchingNextPage ? "Refreshing history…" : "Refresh history"}
        </Button>
      </div>
      {isPending ? (
        <Card role="status" aria-label="Loading trade history" aria-busy="true">
          <CardContent>
            {[0, 1, 2].map((i) => (
              <div key={i} aria-hidden="true" className="h-12 w-full rounded-control bg-muted" />
            ))}
          </CardContent>
        </Card>
      ) : !items ? (
        <Card>
          <CardContent>
            <p role="alert">Can&apos;t load your trade history right now. Try again.</p>
            <Button disabled={isFetching} onClick={() => void refetch()}>
              Try again
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          {isError && !isFetchNextPageError && (
            <div
              role="alert"
              className="flex flex-wrap items-center gap-3 rounded-control bg-warn-soft p-4 text-warn-text"
            >
              <p>Couldn&apos;t refresh your trade history. Showing the last successful update.</p>
              <Button variant="secondary" disabled={isFetching} onClick={() => void refetch()}>
                Retry refresh
              </Button>
            </div>
          )}
          <Card className="min-w-0">
            <CardContent>
              <h2 className="font-medium">Executed trades</h2>
              <p className="text-muted-foreground">
                Newest first. Times are shown in your local timezone.
              </p>
              <p className="text-muted-foreground">Total is the cash change including fees.</p>
              {items.length === 0 ? (
                <div className="flex flex-col items-start gap-3">
                  <h2 className="font-medium">No trades yet</h2>
                  <p>
                    Your executed buys and sells will appear here. Browse markets to make your first
                    trade.
                  </p>
                  <Button asChild>
                    <Link to="/">Browse markets</Link>
                  </Button>
                </div>
              ) : (
                <>
                  <div
                    className="hidden min-w-0 overflow-x-auto md:block"
                    role="region"
                    aria-label="Trade history table"
                    tabIndex={0}
                  >
                    <table aria-label="Trade history" className="w-full text-left">
                      <thead>
                        <tr>
                          {fields(items[0]!).map(([label], index) => (
                            <th
                              key={label}
                              scope="col"
                              className={`p-3 text-sm font-medium text-muted-foreground ${index > 2 ? "text-right" : ""}`}
                            >
                              {label}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {items.map((item) => (
                          <tr
                            key={item.id}
                            className="h-[52px] border-t border-border hover:bg-accent"
                          >
                            {fields(item).map(([label, value], index) =>
                              index === 1 ? (
                                <th key={label} scope="row" className="p-3 font-normal">
                                  {value}
                                </th>
                              ) : (
                                <td
                                  key={label}
                                  className={`p-3 tabular-nums ${index > 2 ? "text-right" : ""}`}
                                >
                                  {value}
                                </td>
                              ),
                            )}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <ol aria-label="Trade history" className="min-w-0 md:hidden">
                    {items.map((item) => (
                      <li key={item.id} className="border-t border-border py-4">
                        <dl className="flex flex-col gap-3">
                          {fields(item).map(([label, value]) => (
                            <div
                              key={label}
                              className="flex flex-wrap items-start justify-between gap-2"
                            >
                              <dt className="text-muted-foreground">{label}</dt>
                              <dd className="min-w-0 text-right wrap-anywhere tabular-nums">
                                {value}
                              </dd>
                            </div>
                          ))}
                        </dl>
                      </li>
                    ))}
                  </ol>
                </>
              )}
            </CardContent>
          </Card>
          {items.length > 0 &&
            (hasNextPage ? (
              <div className="flex flex-col items-start gap-3">
                {isFetchNextPageError && (
                  <p role="alert">
                    Couldn&apos;t load more trades. Your loaded trades are still here.
                  </p>
                )}
                <Button
                  ref={captureAppendButton}
                  className="min-h-11 motion-reduce:transform-none motion-reduce:transition-none"
                  disabled={isFetching}
                  onClick={() => void loadMore()}
                >
                  {isFetchingNextPage
                    ? "Loading more trades…"
                    : isFetchNextPageError
                      ? "Try loading more"
                      : "Load more"}
                </Button>
              </div>
            ) : (
              <p
                tabIndex={-1}
                className="text-muted-foreground"
                ref={(node) => {
                  if (node && focusEnd.current) {
                    node.focus({ preventScroll: true });
                    focusEnd.current = false;
                  }
                }}
              >
                All trades loaded.
              </p>
            ))}
          <p role="status" aria-live="polite" aria-atomic="true" className="sr-only">
            {isFetchingNextPage
              ? "Loading more trades…"
              : isFetching
                ? "Refreshing history…"
                : announcement?.updatedAt === dataUpdatedAt
                  ? announcement.text
                  : `${items.length} trades shown.`}
          </p>
        </>
      )}
    </div>
  );
}
