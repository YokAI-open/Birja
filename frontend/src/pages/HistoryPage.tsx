import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router";
import { useQueryClient } from "@tanstack/react-query";
import type { EventHistoryItem } from "@/api/eventHistory";
import {
  HistoryEventCash,
  HistoryEventDetails,
  HistoryEventTime,
  HistoryEventTitle,
} from "@/components/HistoryEventDetails";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { eventHistorySession, useEventHistory } from "@/hooks/useEventHistory";

function fields(item: EventHistoryItem, prefix: string) {
  return [
    ["Recorded", <HistoryEventTime value={item.recorded_at} />],
    ["Event", <HistoryEventTitle item={item} />],
    [
      "Asset",
      <span className="wrap-anywhere">
        <span className="block text-[13px] text-muted-foreground">
          {item.asset_type === "stock" ? "Stock" : "Crypto"}
        </span>
        <span className="font-medium">{item.symbol}</span> · {item.name}
      </span>,
    ],
    ["Details", <HistoryEventDetails item={item} anchorPrefix={prefix} />],
    ["Cash change", <HistoryEventCash item={item} />],
  ] as const;
}

export default function HistoryPage() {
  const client = useQueryClient();
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
  } = useEventHistory();
  const items = data?.pages.flatMap((page) => page.items);
  const appendButton = useRef<HTMLButtonElement | null>(null);
  const refreshButton = useRef<HTMLButtonElement | null>(null);
  const retryButton = useRef<HTMLButtonElement | null>(null);
  const captureRetryButton = useCallback((node: HTMLButtonElement | null) => {
    if (!node && retryButton.current === document.activeElement) {
      refreshButton.current?.focus({ preventScroll: true });
    }
    retryButton.current = node;
  }, []);
  const focusEnd = useRef<{
    button: HTMLButtonElement;
    session: ReturnType<typeof eventHistorySession>;
  } | null>(null);
  const [announcement, setAnnouncement] = useState<{ updatedAt: number; text: string } | null>(
    null,
  );
  const captureAppendButton = useCallback((node: HTMLButtonElement | null) => {
    appendButton.current = node;
  }, []);
  useEffect(() => {
    const intent = focusEnd.current;
    const button = appendButton.current;
    if (isFetching || !intent || !button) return;
    const current = eventHistorySession(client);
    if (
      current.email === intent.session.email &&
      current.epoch === intent.session.epoch &&
      button === intent.button &&
      (document.activeElement === document.body || document.activeElement === button)
    )
      button.focus({ preventScroll: true });
    focusEnd.current = null;
  }, [client, isFetching, hasNextPage]);

  function refresh() {
    if (!isFetching) void refetch({ cancelRefetch: false });
  }

  async function loadMore() {
    if (isFetching || !hasNextPage) return;
    const session = eventHistorySession(client);
    const button = appendButton.current;
    // Native disabled controls can blur in Chromium before their final unmount.
    // Capture intent before fetching; never infer it from the disabled element.
    const intent = button && button === document.activeElement ? { button, session } : null;
    focusEnd.current = intent;
    const previousCount = items?.length ?? 0;
    const result = await fetchNextPage({ cancelRefetch: false });
    const current = eventHistorySession(client);
    if (current.email !== session.email || current.epoch !== session.epoch) return;
    if (!result.isError) {
      const count =
        result.data?.pages.reduce((sum, page) => sum + page.items.length, 0) ?? previousCount;
      setAnnouncement({
        updatedAt: result.dataUpdatedAt,
        text: `${count - previousCount} more events loaded. ${count} events shown.`,
      });
    }
  }
  return (
    <div className="my-8 flex min-w-0 flex-col gap-4 pb-24 text-[15px] leading-[22px]">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-[32px] leading-9 font-medium tracking-[-0.02em] md:text-[40px] md:leading-[44px]">
          History
        </h1>
        <Button
          ref={refreshButton}
          variant="secondary"
          className="min-h-11 aria-disabled:cursor-not-allowed aria-disabled:opacity-40 motion-reduce:transform-none motion-reduce:transition-none"
          aria-disabled={isFetching}
          onClick={refresh}
        >
          {isFetching && !isFetchingNextPage ? "Refreshing history…" : "Refresh history"}
        </Button>
      </div>
      {isPending ? (
        <Card role="status" aria-label="Loading history" aria-busy="true">
          <CardContent>
            {[0, 1, 2].map((i) => (
              <div key={i} aria-hidden="true" className="h-12 w-full rounded-control bg-muted" />
            ))}
          </CardContent>
        </Card>
      ) : !items ? (
        <Card>
          <CardContent>
            <p role="alert">Can&apos;t load your history right now. Try again.</p>
            <Button ref={captureRetryButton} aria-disabled={isFetching} onClick={refresh}>
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
              <p>Couldn&apos;t refresh your history. Showing the last successful update.</p>
              <Button
                ref={captureRetryButton}
                variant="secondary"
                className="aria-disabled:cursor-not-allowed aria-disabled:opacity-40"
                aria-disabled={isFetching}
                onClick={refresh}
              >
                Retry refresh
              </Button>
            </div>
          )}
          <Card className="min-w-0">
            <CardContent>
              <h2 className="font-medium">Account activity</h2>
              <p className="text-muted-foreground">
                Newest recorded first. Times are shown in your local timezone.
              </p>
              <p className="text-muted-foreground">
                Cash change is the amount actually added to or taken from your shared USD balance.
              </p>
              {items.length === 0 ? (
                <div className="flex flex-col items-start gap-3">
                  <h2 className="font-medium">No activity yet</h2>
                  <p>
                    Your trades, dividends, splits and corrections will appear here. Browse markets
                    to make your first trade.
                  </p>
                  <Button asChild>
                    <Link to="/">Browse markets</Link>
                  </Button>
                </div>
              ) : (
                <>
                  <div
                    className="hidden min-w-0 lg:block"
                    role="region"
                    aria-label="Account activity table"
                    tabIndex={0}
                  >
                    <table aria-label="Account activity" className="w-full table-fixed text-left">
                      <colgroup>
                        <col className="w-[15%]" />
                        <col className="w-[15%]" />
                        <col className="w-[18%]" />
                        <col className="w-[37%]" />
                        <col className="w-[15%]" />
                      </colgroup>
                      <thead>
                        <tr>
                          {fields(items[0]!, "history-desktop-").map(([label], index) => (
                            <th
                              key={label}
                              scope="col"
                              className={`p-4 text-[13px] font-medium text-muted-foreground ${index === 4 ? "text-right" : ""}`}
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
                            id={`history-desktop-${item.id}`}
                            tabIndex={-1}
                            className="h-[52px] scroll-mb-24 border-t border-border align-top wrap-anywhere hover:bg-accent focus-visible:outline-2 focus-visible:outline-ring"
                          >
                            {fields(item, "history-desktop-").map(([label, value], index) =>
                              index === 2 ? (
                                <th key={label} scope="row" className="min-w-0 p-4 font-normal">
                                  {value}
                                </th>
                              ) : (
                                <td
                                  key={label}
                                  className={`min-w-0 p-4 tabular-nums ${index === 4 ? "text-right" : ""}`}
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
                  <ol aria-label="Account activity" className="min-w-0 lg:hidden">
                    {items.map((item) => (
                      <li
                        key={item.id}
                        id={`history-mobile-${item.id}`}
                        tabIndex={-1}
                        className="scroll-mb-24 border-t border-border py-4 focus-visible:outline-2 focus-visible:outline-ring"
                      >
                        <dl className="flex flex-col gap-3">
                          {fields(item, "history-mobile-").map(([label, value]) => (
                            <div key={label} className="flex min-w-0 flex-col items-start gap-2">
                              <dt className="text-muted-foreground">{label}</dt>
                              <dd className="w-full min-w-0 wrap-anywhere tabular-nums">{value}</dd>
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
                    Couldn&apos;t load more events. Your loaded events are still here.
                  </p>
                )}
                <Button
                  ref={captureAppendButton}
                  className="min-h-11 motion-reduce:transform-none motion-reduce:transition-none"
                  disabled={isFetching}
                  onClick={() => void loadMore()}
                >
                  {isFetchingNextPage
                    ? "Loading more events…"
                    : isFetchNextPageError
                      ? "Try loading more"
                      : "Load more"}
                </Button>
              </div>
            ) : (
              <p
                tabIndex={-1}
                className="scroll-mb-24 text-muted-foreground focus-visible:outline-2 focus-visible:outline-ring"
                ref={(node) => {
                  if (node && focusEnd.current) {
                    const intent = focusEnd.current;
                    const current = eventHistorySession(client);
                    if (
                      current.email === intent.session.email &&
                      current.epoch === intent.session.epoch &&
                      (document.activeElement === document.body ||
                        document.activeElement === intent.button)
                    )
                      node.focus({ preventScroll: true });
                    focusEnd.current = null;
                  }
                }}
              >
                All events loaded.
              </p>
            ))}
          <p role="status" aria-live="polite" aria-atomic="true" className="sr-only">
            {isFetchingNextPage
              ? "Loading more events…"
              : isFetching
                ? "Refreshing history…"
                : announcement?.updatedAt === dataUpdatedAt
                  ? announcement.text
                  : `${items.length} events shown.`}
          </p>
        </>
      )}
    </div>
  );
}
