import { useEffect, useRef, useState } from "react";
import { ChartNoAxesCombined, Wallet, History } from "lucide-react";
import {
  NavLink,
  Navigate,
  Route,
  Routes,
  useLocation,
  useParams,
  useMatch,
  matchPath,
} from "react-router";
import type { Me } from "@/api/auth";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import MarketsPage from "@/pages/MarketsPage";
import { Card, CardContent } from "@/components/ui/card";
import { useMe } from "@/hooks/useMe";
import AccountPage from "@/pages/AccountPage";
import HealthPage from "@/pages/HealthPage";
import SignInPage from "@/pages/SignInPage";
import StockTradePage from "@/pages/StockTradePage";
import TradePage from "@/pages/TradePage";
import PortfolioPage from "@/pages/PortfolioPage";
import PortfoliosPage from "@/pages/PortfoliosPage";
import { PortfolioSwitcher } from "@/components/PortfolioSwitcher";
import HistoryPage from "@/pages/HistoryPage";
import { PortfolioTargetBoundary } from "@/components/PortfolioTargetBoundary";
import { usePortfolioTarget } from "@/hooks/usePortfolioTarget";
import { isPortfolioId } from "@/api/portfolios";
import { PortfolioMetadataForm } from "@/components/PortfolioMetadataForm";
import PortfolioDeletionPage from "@/pages/PortfolioDeletionPage";
import { useQueryClient } from "@tanstack/react-query";
import { portfolioDeletionAuthorityGeneration } from "@/hooks/usePortfolioDeletion";

/** Keep the management operation mounted when financial authority is revoked. */
export function PortfolioRoute() {
  const { portfolioId } = useParams();
  const target = usePortfolioTarget(portfolioId);
  const client = useQueryClient();
  const owner = useMe().data?.email;
  const root = useRef<HTMLDivElement>(null);
  const primaryHeading = useRef<HTMLHeadingElement>(null);
  const managementFocus = useRef<Element | null>(null);
  const detailMatch = useMatch({ path: "/portfolios/:portfolioId", end: true });
  const detail = isPortfolioId(portfolioId) && detailMatch !== null;
  useEffect(() => {
    if (target.status === "loading" || target.status === "ready") return;
    if (
      managementFocus.current &&
      !managementFocus.current.isConnected &&
      document.activeElement === document.body
    )
      root.current?.querySelector<HTMLHeadingElement>("h1")?.focus();
  }, [target.status]);
  return (
    <div className="contents" ref={root}>
      {detail && (
        <h1
          ref={primaryHeading}
          tabIndex={-1}
          className="mt-8 mb-4 text-[32px] leading-10 font-medium focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        >
          {target.status === "ready"
            ? "Portfolio"
            : target.status === "loading"
              ? "Checking portfolio access…"
              : "Portfolio unavailable"}
        </h1>
      )}
      {detail && owner && (
        <div
          className="contents"
          onFocusCapture={(event) => {
            managementFocus.current = event.target;
          }}
        >
          <PortfolioMetadataForm
            key={`${owner}:${portfolioId}:${portfolioDeletionAuthorityGeneration(client)}`}
            portfolioId={portfolioId}
            available={target.status === "ready"}
            lastPortfolio={target.portfolios?.length === 1}
          />
        </div>
      )}
      <PortfolioTargetBoundary primaryHeading={detail ? primaryHeading : undefined} />
    </div>
  );
}

function AuthSwitch() {
  const { data, isPending, isError, refetch } = useMe();

  if (isPending) {
    return (
      <Card
        className="mx-auto my-8 max-w-xl"
        role="status"
        aria-busy="true"
        aria-label="Loading your account"
      >
        <CardContent>
          <div className="h-6 w-1/3 rounded-control bg-muted" />
          <div className="h-12 w-full rounded-control bg-muted" />
          <div className="h-11 w-full rounded-pill bg-muted" />
        </CardContent>
      </Card>
    );
  }
  if (isError) {
    return (
      <Card className="mx-auto my-8 max-w-xl">
        <CardContent>
          <p role="alert" className="text-loss-text">
            Can&apos;t reach Birja right now.
          </p>
          <Button variant="secondary" onClick={() => void refetch()}>
            Try again
          </Button>
        </CardContent>
      </Card>
    );
  }
  return data === null ? <SignInPage /> : <SignedIn key={data.email} me={data} />;
}

const navItem = ({ isActive }: { isActive: boolean }) =>
  cn(
    "inline-flex min-h-11 min-w-11 flex-col items-center justify-center gap-1 rounded-pill px-2 text-[13px] md:flex-row md:px-4 md:text-sm font-medium focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 motion-reduce:transition-none",
    isActive
      ? "bg-primary text-primary-foreground shadow-pill"
      : "text-muted-foreground hover:bg-muted",
  );

function LegacyTrade({ stock = false }: { stock?: boolean }) {
  const { symbol } = useParams<{ symbol: string }>();
  return (
    <PortfolioTargetBoundary
      legacyDestination={(id) =>
        `/portfolios/${id}/trade/${stock ? "stocks/" : ""}${encodeURIComponent(symbol ?? "")}`
      }
    />
  );
}

function SignedIn({ me }: { me: Me }) {
  const { pathname } = useLocation();
  // This memory belongs to this mounted signed-in identity only. Explicit
  // routes take priority, including their refusal; never fall back from one.
  const [openedId, setOpenedId] = useState<string>();
  const matchedId = matchPath("/portfolios/:portfolioId/*", pathname)?.params.portfolioId;
  const explicitId = isPortfolioId(matchedId) ? matchedId : undefined;
  const navigation = usePortfolioTarget(explicitId ?? openedId);
  const target = navigation.status === "ready" ? navigation.target : null;
  if (explicitId && target && openedId !== explicitId) setOpenedId(explicitId);
  const historyPath = target ? `/portfolios/${target.portfolioId}/history` : "/history";
  const content = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const root = content.current!;
    function focusHeading() {
      const heading = root.querySelector("h1");
      if (!heading) return false;
      heading.tabIndex = -1;
      heading.classList.add(
        "focus-visible:ring-2",
        "focus-visible:ring-ring",
        "focus-visible:ring-offset-2",
      );
      heading.focus();
      return true;
    }
    // Some existing routes render their heading after the initial query settles.
    if (focusHeading()) return;
    const observer = new MutationObserver(() => {
      if (focusHeading()) observer.disconnect();
    });
    observer.observe(root, { childList: true, subtree: true });
    return () => observer.disconnect();
  }, [pathname]);
  return (
    <>
      <div className="flex min-h-11 items-center justify-end gap-2">
        <nav
          aria-label="Main"
          className="fixed inset-x-0 bottom-0 z-20 flex h-[calc(56px+env(safe-area-inset-bottom))] items-start justify-around gap-2 border-t border-border bg-card px-2 pt-1 pb-[env(safe-area-inset-bottom)] md:static md:mr-auto md:h-auto md:flex-wrap md:justify-start md:border-0 md:bg-transparent md:p-0"
        >
          <NavLink to="/" end className={navItem}>
            <ChartNoAxesCombined aria-hidden="true" className="size-5 md:hidden" />
            Markets
          </NavLink>
          <NavLink to="/portfolios" end className={navItem}>
            <Wallet aria-hidden="true" className="size-5 md:hidden" />
            Portfolios
          </NavLink>
          <NavLink to={historyPath} className={navItem}>
            <History aria-hidden="true" className="size-5 md:hidden" />
            History
          </NavLink>
        </nav>
        <NavLink to="/account" className={navItem}>
          Account
        </NavLink>
      </div>
      <div ref={content}>
        {explicitId && <PortfolioSwitcher portfolioId={explicitId} />}
        <Routes>
          <Route index element={<MarketsPage authenticated portfolioId={target?.portfolioId} />} />
          <Route path="portfolios/deletion" element={<PortfolioDeletionPage />} />
          <Route path="portfolios/:portfolioId" element={<PortfolioRoute />}>
            <Route index element={<PortfolioPage />} />
            <Route path="history" element={<HistoryPage />} />
            <Route path="trade/stocks/:symbol" element={<StockTradePage />} />
            <Route path="trade/:symbol" element={<TradePage />} />
          </Route>
          <Route path="portfolios" element={<PortfoliosPage />} />
          <Route
            path="portfolio"
            element={<PortfolioTargetBoundary legacyDestination={(id) => `/portfolios/${id}`} />}
          />
          <Route
            path="history"
            element={
              <PortfolioTargetBoundary legacyDestination={(id) => `/portfolios/${id}/history`} />
            }
          />
          <Route
            path="account"
            element={
              <>
                <h1 className="mt-8 text-[32px] leading-9 font-medium md:text-[40px] md:leading-[44px]">
                  Account
                </h1>
                <AccountPage me={me} />
                <HealthPage />
              </>
            }
          />
          <Route path="trade/stocks/:symbol" element={<LegacyTrade stock />} />
          <Route path="trade/:symbol" element={<LegacyTrade />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </>
  );
}

function App() {
  return (
    <>
      <header className="mx-auto flex max-w-[1440px] items-center gap-3 px-4 py-4 md:px-8">
        <span aria-hidden="true" className="size-8 rounded-control bg-brand" />
        <span className="text-xl font-semibold tracking-[-0.01em]">Birja</span>
      </header>
      <main className="mx-auto max-w-[1440px] px-4 pb-[calc(80px+env(safe-area-inset-bottom))] md:px-8 md:pb-8 [&_:focus]:scroll-mb-[calc(80px+env(safe-area-inset-bottom))] md:[&_:focus]:scroll-mb-0">
        <AuthSwitch />
      </main>
    </>
  );
}

export default App;
