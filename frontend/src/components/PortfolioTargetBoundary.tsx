import {
  useCallback,
  useEffect,
  useRef,
  useSyncExternalStore,
  type ReactNode,
  type RefObject,
} from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Link, Navigate, Outlet, useLocation, useParams } from "react-router";
import { PortfolioSwitcher } from "@/components/PortfolioSwitcher";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { usePortfolioTarget, type PortfolioTarget } from "@/hooks/usePortfolioTarget";
import { eventHistorySession } from "@/hooks/useEventHistory";
import { usePortfolioMetadataLifetime } from "@/hooks/usePortfolioManagement";

/** No financial child mounts until explicit owned-active metadata resolves. */
export function PortfolioTargetBoundary({
  children,
  legacyDestination,
  tradeSymbol,
  primaryHeading,
}: {
  children?: (target: PortfolioTarget) => ReactNode;
  tradeSymbol?: string;
  legacyDestination?: (portfolioId: string) => string;
  /** A detail layout can own its heading before persistent management content. */
  primaryHeading?: RefObject<HTMLHeadingElement | null>;
}) {
  const { portfolioId } = useParams<{ portfolioId: string }>();
  const result = usePortfolioTarget(portfolioId, { legacyEntry: !!legacyDestination });
  const { pathname } = useLocation();
  usePortfolioMetadataLifetime(portfolioId, result.status, pathname);
  const client = useQueryClient();
  // Read only the existence of this session's original unresolved attempt.
  // Unavailable targets never regain financial authority through this notice.
  eventHistorySession(client);
  const subscribe = useCallback(
    (notify: () => void) => client.getQueryCache().subscribe(notify),
    [client],
  );
  const unconfirmed = useSyncExternalStore(subscribe, () => {
    const session = eventHistorySession(client);
    if (!session.email || !portfolioId || result.status !== "unavailable") return false;
    return ["cryptoTradeState", "stockTradeState"].some((prefix) =>
      client
        .getQueryCache()
        .findAll({ queryKey: [prefix, session.email, portfolioId] })
        .some((query) => {
          const state = query.state.data as { phase?: string; attempt?: unknown } | undefined;
          return (
            query.queryKey[3] === session.epoch &&
            !!state?.attempt &&
            (state.phase === "unknown" || state.phase === "submitting")
          );
        }),
    );
  });
  const ownHeading = useRef<HTMLHeadingElement>(null);
  const heading = primaryHeading ?? ownHeading;
  const entered = useRef(false);
  const financial = useRef<HTMLDivElement>(null);
  const financialFocus = useRef<Element | null>(null);
  useEffect(() => {
    const remember = (event: FocusEvent) => {
      const node = event.target;
      financialFocus.current =
        node instanceof Element && financial.current?.contains(node) ? node : null;
    };
    document.addEventListener("focusin", remember);
    return () => document.removeEventListener("focusin", remember);
  }, []);
  useEffect(() => {
    if (result.status === "loading" || result.status === "redirect") return;
    if (entered.current) {
      if (
        financialFocus.current &&
        !financialFocus.current.isConnected &&
        result.status !== "ready" &&
        document.activeElement === document.body
      )
        heading.current?.focus();
      return;
    }
    entered.current = true;
    // Initial refusal replaces the page. Background failures announce without
    // stealing focus from a user who was already interacting with that page.
    if (result.status !== "ready") heading.current?.focus();
  }, [result.status, heading]);

  if (result.status === "ready" && result.target)
    return (
      <div className="contents" ref={financial}>
        {children ? children(result.target) : <Outlet context={result.target} />}
      </div>
    );
  if (result.status === "signed_out") return null;
  if (result.status === "redirect" && result.redirectPortfolioId && legacyDestination)
    return <Navigate replace to={legacyDestination(result.redirectPortfolioId)} />;
  if (result.status === "loading" || result.status === "redirect")
    return (
      <Card
        className="mx-auto my-8 min-w-0 max-w-xl"
        role="status"
        aria-busy="true"
        aria-label="Loading portfolio"
      >
        <CardContent className="flex min-w-0 flex-col gap-4">
          <p>Loading portfolio</p>
          <div aria-hidden="true" className="h-6 w-1/3 rounded-control bg-muted" />
          <div aria-hidden="true" className="h-12 w-full rounded-control bg-muted" />
        </CardContent>
      </Card>
    );

  const title =
    result.status === "empty"
      ? "No portfolio available"
      : result.status === "required" || result.status === "ambiguous"
        ? "Portfolio required"
        : "Portfolio unavailable";
  const message =
    result.status === "empty"
      ? "You're signed in, but no portfolio is available. You can still browse Markets or sign out."
      : result.status === "ambiguous"
        ? tradeSymbol
          ? `Choose a portfolio to continue to ${tradeSymbol}.`
          : "Open a portfolio-specific link to continue. No portfolio was selected."
        : result.status === "required"
          ? "Open a portfolio-specific link to continue."
          : result.status === "error"
            ? "Can't load this portfolio right now. Try again."
            : "This portfolio is unavailable. Choose another portfolio from Portfolios.";
  return (
    <section className="app-page flex max-w-2xl flex-col gap-6" aria-live="polite">
      {!primaryHeading && (
        <h1
          ref={heading}
          tabIndex={-1}
          className="app-heading focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        >
          {title}
        </h1>
      )}
      <Card>
        <CardContent className="flex min-w-0 flex-col items-start gap-4">
          <p
            role={result.status === "error" ? "alert" : undefined}
            className="break-words [overflow-wrap:anywhere]"
          >
            {message}
          </p>
          {unconfirmed && (
            <p>
              An earlier order&apos;s result is unconfirmed for this unavailable portfolio. It
              won&apos;t be retried in another portfolio.
            </p>
          )}
          {result.status === "ambiguous" && tradeSymbol && legacyDestination ? (
            <PortfolioSwitcher destination={legacyDestination} />
          ) : (
            <Button asChild variant="secondary" className="min-h-11 whitespace-normal">
              <Link to="/portfolios">Portfolios</Link>
            </Button>
          )}
          {result.status === "error" ? (
            <Button variant="secondary" onClick={() => void result.refetch().catch(() => {})}>
              Try again
            </Button>
          ) : (
            <Button asChild>
              <Link to="/">
                {result.status === "empty" ? "Browse markets" : "Return to Markets"}
              </Link>
            </Button>
          )}
        </CardContent>
      </Card>
    </section>
  );
}
