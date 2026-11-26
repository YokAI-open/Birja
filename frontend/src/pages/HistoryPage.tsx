import { useCallback, useEffect, useRef, useState } from "react";
import { ChevronDown, RefreshCw } from "lucide-react";
import { Link, useOutletContext } from "react-router";
import { useQueryClient } from "@tanstack/react-query";
import type { EventHistoryItem } from "@/api/eventHistory";
import { DEFAULT_EVENT_HISTORY_FILTERS, type EventHistoryFilters } from "@/api/history";
import {
  HistoryEventCash,
  HistoryEventDetails,
  HistoryEventTitle,
} from "@/components/HistoryEventDetails";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { eventHistorySession, useEventHistory } from "@/hooks/useEventHistory";
import type { PortfolioTarget } from "@/hooks/usePortfolioTarget";
import { PortfolioSwitcher } from "@/components/PortfolioSwitcher";
import "./historyWorkspace.css";

const dayFormat = new Intl.DateTimeFormat(undefined, { dateStyle: "long" });
const timeFormat = new Intl.DateTimeFormat(undefined, { timeStyle: "short" });

function EventCard({
  item,
  target,
  prefix,
  day,
}: {
  item: EventHistoryItem;
  target: PortfolioTarget;
  prefix: string;
  day?: string;
}) {
  const time = timeFormat.format(new Date(item.recorded_at));
  return (
    <li id={`${prefix}${item.id}`} tabIndex={-1} className="min-w-0 scroll-mt-4">
      {day && <h2 className="history-date-heading">{day}</h2>}
      <details className="group rounded-card border border-border bg-card">
        <summary className="history-event-summary hover:bg-accent/50 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-ring">
          <span className="min-w-0 wrap-anywhere">
            <span className="block font-semibold [&>span]:font-semibold">
              <HistoryEventTitle item={item} />
              {" · "}
              <span>{item.symbol}</span>
            </span>
            <time
              className="block text-muted-foreground"
              dateTime={item.recorded_at}
              title={item.recorded_at}
              aria-label={`${time}, UTC ${item.recorded_at}`}
            >
              {time}
            </time>
          </span>
          <span className="min-w-0 text-right">
            <span className="sr-only">Cash change: </span>
            <HistoryEventCash item={item} />
          </span>
          <ChevronDown
            aria-hidden="true"
            className="size-4 shrink-0 text-muted-foreground group-open:rotate-180"
          />
        </summary>
        <div className="mx-4 border-t border-border py-4 sm:mx-6 sm:py-5">
          {item.name !== item.symbol && (
            <p className="mb-3 text-sm font-medium wrap-anywhere">
              {item.name}{" "}
              <span className="font-normal text-muted-foreground">
                · {item.asset_type === "stock" ? "Stock" : "Crypto"}
              </span>
            </p>
          )}
          <HistoryEventDetails item={item} target={target} anchorPrefix={prefix} />
          {item.catalog_id && (
            <Link
              to={`/portfolios/${target.portfolioId}/trade/catalog/${item.catalog_id}`}
              aria-label={`View stock ticket for ${item.symbol}`}
              className="mt-2 inline-flex min-h-11 items-center rounded-sm text-sm font-medium underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
            >
              View stock
            </Link>
          )}
        </div>
      </details>
    </li>
  );
}

export default function HistoryPage() {
  const target = useOutletContext<PortfolioTarget>();
  return (
    <OwnedHistory
      key={JSON.stringify([target.owner, target.portfolioId, target.epoch.session])}
      target={target}
    />
  );
}

function OwnedHistory({ target }: { target: PortfolioTarget }) {
  const client = useQueryClient();
  const [filters, setFilters] = useState(DEFAULT_EVENT_HISTORY_FILTERS);
  const activeFilters = useRef(filters);
  const isFiltered = filters.activity !== "all" || filters.asset !== "all";
  const {
    data,
    dataUpdatedAt,
    isPending,
    isError,
    isFetching,
    isFetchingNextPage,
    isFetchNextPageError,
    hasNextPage,
    discardPages,
    fetchNextPage,
    refetch,
  } = useEventHistory(target, filters);
  const prefix = `history-${target.portfolioId}-${target.epoch.session}-`;
  const items = data?.pages.flatMap((page) => page.items);
  const appendButton = useRef<HTMLButtonElement | null>(null);
  const refreshButton = useRef<HTMLButtonElement | null>(null);
  const activitySelect = useRef<HTMLSelectElement>(null);
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
      target.isCurrent() &&
      button === intent.button &&
      (document.activeElement === document.body || document.activeElement === button)
    )
      button.focus({ preventScroll: true });
    focusEnd.current = null;
  }, [client, isFetching, hasNextPage, target]);

  function refresh() {
    if (target.isCurrent() && !isFetching) void refetch({ cancelRefetch: false });
  }

  function changeFilters(next: EventHistoryFilters) {
    if (
      !target.isCurrent() ||
      (next.activity === activeFilters.current.activity &&
        next.asset === activeFilters.current.asset)
    )
      return;
    activeFilters.current = next;
    focusEnd.current = null;
    setAnnouncement(null);
    discardPages();
    setFilters(next);
  }

  async function loadMore() {
    if (!target.isCurrent() || isFetching || !hasNextPage) return;
    const session = eventHistorySession(client);
    const requestFilters = activeFilters.current;
    const button = appendButton.current;
    // Native disabled controls can blur in Chromium before their final unmount.
    // Capture intent before fetching; never infer it from the disabled element.
    const intent = button && button === document.activeElement ? { button, session } : null;
    focusEnd.current = intent;
    const previousCount = items?.length ?? 0;
    const result = await fetchNextPage({ cancelRefetch: false });
    const current = eventHistorySession(client);
    if (
      activeFilters.current !== requestFilters ||
      !target.isCurrent() ||
      current.email !== session.email ||
      current.epoch !== session.epoch
    )
      return;
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
    <div className="history-workspace">
      <h1 className="sr-only">History</h1>
      <div className="history-toolbar">
        <div className="history-portfolio-controls">
          <div className="history-portfolio-picker">
            <PortfolioSwitcher
              portfolioId={target.portfolioId}
              destination={(id) => `/portfolios/${id}/history`}
              label="History portfolio"
              inline
            />
          </div>
          <Button
            ref={refreshButton}
            variant="secondary"
            aria-label={isFetching && !isFetchingNextPage ? "Updating history…" : "Update history"}
            title="Update history"
            className="size-11 shrink-0 p-0 aria-disabled:opacity-40"
            aria-disabled={isFetching}
            onClick={refresh}
          >
            <RefreshCw aria-hidden="true" className="size-4" />
          </Button>
        </div>
        <div className="history-filters">
          <select
            ref={activitySelect}
            aria-label="Filter activity"
            value={filters.activity}
            onChange={(event) =>
              changeFilters({
                ...filters,
                activity: event.target.value as EventHistoryFilters["activity"],
              })
            }
          >
            <option value="all">All activity</option>
            <option value="buy">Buy</option>
            <option value="sell">Sell</option>
            <option value="dividend">Dividend</option>
            <option value="split">Split</option>
          </select>
          <select
            aria-label="Filter assets"
            value={filters.asset}
            onChange={(event) =>
              changeFilters({
                ...filters,
                asset: event.target.value as EventHistoryFilters["asset"],
              })
            }
          >
            <option value="all">All assets</option>
            <option value="stock">Stocks</option>
            <option value="crypto">Crypto</option>
          </select>
        </div>
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
              className="flex flex-wrap items-center gap-4 rounded-control bg-warn-soft p-4 text-warn-text"
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
          {items.length === 0 ? (
            <div className="flex flex-col items-start gap-4 border-t border-border py-8">
              <h2 className="text-2xl font-semibold">
                {isFiltered ? "No matching activity" : "No activity yet"}
              </h2>
              {isFiltered ? (
                <Button
                  variant="secondary"
                  onClick={() => {
                    activitySelect.current?.focus();
                    changeFilters(DEFAULT_EVENT_HISTORY_FILTERS);
                  }}
                >
                  Clear filters
                </Button>
              ) : (
                <Button asChild>
                  <Link to="/">Browse markets</Link>
                </Button>
              )}
            </div>
          ) : (
            <ol
              key={`${filters.activity}-${filters.asset}`}
              aria-label="Account activity"
              className="grid min-w-0 gap-3"
            >
              {items.map((item, index) => {
                const day = dayFormat.format(new Date(item.recorded_at));
                const previous = items[index - 1];
                const startsGroup =
                  !previous || day !== dayFormat.format(new Date(previous.recorded_at));
                return (
                  <EventCard
                    key={item.id}
                    item={item}
                    target={target}
                    prefix={prefix}
                    day={startsGroup ? day : undefined}
                  />
                );
              })}
            </ol>
          )}
          {items.length > 0 &&
            (hasNextPage ? (
              <div className="flex flex-col items-start gap-4">
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
                className="sr-only text-muted-foreground focus:not-sr-only focus-visible:outline-2 focus-visible:outline-ring"
                ref={(node) => {
                  if (node && focusEnd.current) {
                    const intent = focusEnd.current;
                    const current = eventHistorySession(client);
                    if (
                      current.email === intent.session.email &&
                      current.epoch === intent.session.epoch &&
                      target.isCurrent() &&
                      (document.activeElement === document.body ||
                        document.activeElement === intent.button)
                    )
                      node.focus();
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
