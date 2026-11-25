import { useCallback, useEffect, useRef, useState } from "react";
import { ChevronDown, RefreshCw } from "lucide-react";
import { Link, useOutletContext } from "react-router";
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
import type { PortfolioTarget } from "@/hooks/usePortfolioTarget";
import { PortfolioSwitcher } from "@/components/PortfolioSwitcher";

function EventCard({
  item,
  target,
  prefix,
}: {
  item: EventHistoryItem;
  target: PortfolioTarget;
  prefix: string;
}) {
  return (
    <li
      id={`${prefix}${item.id}`}
      tabIndex={-1}
      className="min-w-0 scroll-mt-4 rounded-card border border-border bg-card"
    >
      <details className="group">
        <summary className="grid min-h-20 cursor-pointer list-none grid-cols-[minmax(0,1fr)_fit-content(45%)_auto] items-start gap-3 rounded-card px-4 py-4 hover:bg-accent/50 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-ring sm:items-center sm:px-6 [&::-webkit-details-marker]:hidden">
          <span className="min-w-0 wrap-anywhere">
            <span className="block text-lg leading-tight">
              <HistoryEventTitle item={item} />
              {" · "}
              <span className="font-semibold">{item.symbol}</span>
            </span>
            <span className="mt-1 block text-sm text-muted-foreground">
              <HistoryEventTime value={item.recorded_at} />
            </span>
          </span>
          <span className="min-w-0 text-right text-base sm:text-lg">
            <span className="sr-only">Cash change: </span>
            <HistoryEventCash item={item} />
          </span>
          <ChevronDown
            aria-hidden="true"
            className="mt-1 size-4 shrink-0 text-muted-foreground group-open:rotate-180 sm:mt-0"
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
  } = useEventHistory(target);
  const prefix = `history-${target.portfolioId}-${target.epoch.session}-`;
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

  async function loadMore() {
    if (!target.isCurrent() || isFetching || !hasNextPage) return;
    const session = eventHistorySession(client);
    const button = appendButton.current;
    // Native disabled controls can blur in Chromium before their final unmount.
    // Capture intent before fetching; never infer it from the disabled element.
    const intent = button && button === document.activeElement ? { button, session } : null;
    focusEnd.current = intent;
    const previousCount = items?.length ?? 0;
    const result = await fetchNextPage({ cancelRefetch: false });
    const current = eventHistorySession(client);
    if (!target.isCurrent() || current.email !== session.email || current.epoch !== session.epoch)
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
    <div className="mx-auto my-6 flex w-full min-w-0 max-w-[1280px] flex-col gap-7 text-base md:gap-9">
      <h1 className="sr-only">History</h1>
      <div className="flex min-w-0 items-center gap-3">
        <PortfolioSwitcher
          portfolioId={target.portfolioId}
          destination={(id) => `/portfolios/${id}/history`}
          label="History portfolio"
          prominent
          inline
        />
        <Button
          ref={refreshButton}
          variant="secondary"
          aria-label={isFetching && !isFetchingNextPage ? "Updating history…" : "Update history"}
          title="Update history"
          className="min-h-11 min-w-11 gap-2 px-3 aria-disabled:opacity-40 sm:px-4"
          aria-disabled={isFetching}
          onClick={refresh}
        >
          <RefreshCw aria-hidden="true" className="size-4" />
          <span className="hidden sm:inline">Update</span>
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
              <h2 className="text-xl font-semibold">No activity yet</h2>
              <Button asChild>
                <Link to="/">Browse markets</Link>
              </Button>
            </div>
          ) : (
            <ol aria-label="Account activity" className="grid min-w-0 gap-3">
              {items.map((item) => (
                <EventCard key={item.id} item={item} target={target} prefix={prefix} />
              ))}
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
