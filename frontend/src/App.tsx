import { useEffect, useRef, useState, type ReactNode } from "react";
import { DoorClosed, DoorOpen } from "lucide-react";
import {
  Link,
  NavLink,
  Navigate,
  Route,
  Routes,
  useLocation,
  useParams,
  useMatch,
  matchPath,
} from "react-router";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import MarketsPage from "@/pages/MarketsPage";
import { Card, CardContent } from "@/components/ui/card";
import { useMe } from "@/hooks/useMe";
import { useLogout } from "@/hooks/useAuthMutations";
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
import { usePortfolioManagement } from "@/hooks/usePortfolioManagement";
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
  const editTrigger = useRef<HTMLButtonElement>(null);
  const [removeSlot, setRemoveSlot] = useState<HTMLDivElement | null>(null);
  const [editingId, setEditingId] = useState<string>();
  const detailMatch = useMatch({ path: "/portfolios/:portfolioId", end: true });
  const detail = isPortfolioId(portfolioId) && detailMatch !== null;
  const ready = detail && target.status === "ready";
  const management = usePortfolioManagement(detail ? portfolioId : undefined);
  const editOpen = editingId !== undefined && editingId === portfolioId;
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
    <div
      className={cn(
        detail ? "mx-auto mt-6 w-full max-w-[1280px]" : "contents",
        ready &&
          "grid min-w-0 grid-cols-[minmax(0,1fr)_auto] items-center gap-x-2 sm:grid-cols-[minmax(0,30rem)_auto_1fr] sm:gap-x-3",
      )}
      ref={root}
    >
      {detail && (
        <h1
          ref={primaryHeading}
          tabIndex={-1}
          className={cn(
            "focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
            target.status === "ready" ? "sr-only" : "app-heading mb-6",
          )}
        >
          {target.status === "ready"
            ? target.target?.name
            : target.status === "loading"
              ? "Checking portfolio access…"
              : "Portfolio unavailable"}
        </h1>
      )}
      {detail && (
        <div className="flex min-w-0 items-center gap-2">
          <PortfolioSwitcher portfolioId={portfolioId} prominent inline />
          {ready && (
            <Button
              ref={editTrigger}
              type="button"
              variant="secondary"
              aria-label="Edit portfolio"
              className="min-h-11 px-3"
              disabled={editOpen || management.metadataPending || management.metadataBlocked}
              onClick={() => setEditingId(portfolioId)}
            >
              Edit
            </Button>
          )}
          {ready && <div ref={setRemoveSlot} className="shrink-0" />}
        </div>
      )}
      <PortfolioTargetBoundary primaryHeading={detail ? primaryHeading : undefined} />
      {detail && owner && (
        <div
          className="col-span-full min-w-0"
          onFocusCapture={(event) => {
            managementFocus.current = event.target;
          }}
        >
          <PortfolioMetadataForm
            key={`${owner}:${portfolioId}:${portfolioDeletionAuthorityGeneration(client)}`}
            portfolioId={portfolioId}
            available={target.status === "ready"}
            removeSlot={removeSlot}
            externalEdit={{
              active: editOpen,
              trigger: editTrigger,
              close: () => setEditingId(undefined),
            }}
            lastPortfolio={target.portfolios?.length === 1}
          />
        </div>
      )}
    </div>
  );
}

function SessionButton({
  signedIn = false,
  pending = false,
  onClick,
}: {
  signedIn?: boolean;
  pending?: boolean;
  onClick: () => void;
}) {
  const label = signedIn ? (pending ? "Signing out…" : "Sign out") : "Sign in";
  const Icon = signedIn ? DoorOpen : DoorClosed;
  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      className="ml-auto size-11 border-transparent bg-transparent text-muted-foreground aria-disabled:opacity-40"
      aria-label={signedIn ? label : "Go to sign-in form"}
      title={label}
      aria-disabled={pending}
      onClick={onClick}
    >
      <Icon aria-hidden="true" />
    </Button>
  );
}

function AppShell({ navigation, children }: { navigation?: ReactNode; children: ReactNode }) {
  return (
    <>
      <header className="border-b border-border">
        <div className="mx-auto flex min-h-16 max-w-[1440px] items-center gap-2 px-2.5 min-[375px]:gap-3 min-[375px]:px-4 sm:min-h-20 sm:gap-8 sm:px-6 md:px-8 lg:gap-12">
          <div className="flex shrink-0 items-center gap-1.5 sm:gap-3">
            <picture className="shrink-0 mix-blend-multiply">
              <source media="(min-width: 640px)" srcSet="/brand/logo-240.webp" />
              <img
                src="/brand/icon-96.png"
                alt=""
                width={40}
                height={40}
                className="size-6 object-contain min-[375px]:size-8 sm:h-14 sm:w-20"
              />
            </picture>
            <span className="text-base font-semibold tracking-tight min-[375px]:text-lg sm:text-2xl">
              Birja
            </span>
          </div>
          {navigation}
        </div>
      </header>
      <main className="mx-auto max-w-[1440px] px-4 pb-8 sm:px-6 md:px-8">{children}</main>
    </>
  );
}

const navItem = ({ isActive }: { isActive: boolean }) =>
  cn(
    "inline-flex min-h-11 min-w-11 shrink-0 items-center justify-center rounded-pill px-1 text-[13px] font-medium focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 min-[375px]:px-1.5 min-[375px]:text-sm sm:min-h-12 sm:px-4 sm:text-base",
    isActive
      ? "bg-primary text-primary-foreground shadow-pill"
      : "text-muted-foreground hover:bg-muted",
  );

function LegacyTrade({ stock = false }: { stock?: boolean }) {
  const { symbol } = useParams<{ symbol: string }>();
  return (
    <PortfolioTargetBoundary
      tradeSymbol={symbol}
      legacyDestination={(id) =>
        `/portfolios/${id}/trade/${stock ? "stocks/" : ""}${encodeURIComponent(symbol ?? "")}`
      }
    />
  );
}

function SignedIn() {
  const { pathname } = useLocation();
  const logout = useLogout();
  // This memory belongs to this mounted signed-in identity only. Explicit
  // routes take priority, including their refusal; never fall back from one.
  const [openedId, setOpenedId] = useState<string>();
  const matchedId = matchPath("/portfolios/:portfolioId/*", pathname)?.params.portfolioId;
  const explicitId = isPortfolioId(matchedId) ? matchedId : undefined;
  const portfolioDetail = useMatch({ path: "/portfolios/:portfolioId", end: true });
  const portfolioHistory = useMatch({ path: "/portfolios/:portfolioId/history", end: true });
  const portfolioNavigation = useMatch("/portfolios/*");
  const portfoliosActive = Boolean(portfolioNavigation && !portfolioHistory);
  const navigation = usePortfolioTarget(explicitId ?? openedId);
  const target = navigation.status === "ready" ? navigation.target : null;
  if (explicitId && target && openedId !== explicitId) setOpenedId(explicitId);
  const historyId = portfolioHistory ? explicitId : target?.portfolioId;
  const historyPath = historyId ? `/portfolios/${historyId}/history` : "/history";
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
    <AppShell
      navigation={
        <>
          <nav aria-label="Main" className="flex items-center gap-0.5 min-[375px]:gap-1 sm:gap-2">
            <NavLink to="/" end className={navItem}>
              Markets
            </NavLink>
            <Link
              to="/portfolios"
              className={navItem({ isActive: portfoliosActive })}
              aria-current={portfoliosActive ? "page" : undefined}
            >
              Portfolios
            </Link>
            <NavLink to={historyPath} className={navItem}>
              History
            </NavLink>
          </nav>
          <SessionButton
            signedIn
            pending={logout.isPending}
            onClick={() => {
              if (!logout.isPending) logout.mutate();
            }}
          />
        </>
      }
    >
      {logout.isError && (
        <p role="alert" className="mx-auto mt-4 max-w-[1280px] text-sm text-loss-text">
          Couldn&apos;t sign out. Try again.
        </p>
      )}
      <div ref={content}>
        {explicitId && !portfolioDetail && (!portfolioHistory || !target) && (
          <div className="mx-auto mt-6 max-w-[1280px]">
            <PortfolioSwitcher
              portfolioId={explicitId}
              label={portfolioHistory ? "History portfolio" : undefined}
              destination={portfolioHistory ? (id) => `/portfolios/${id}/history` : undefined}
            />
          </div>
        )}
        <Routes>
          <Route index element={<MarketsPage portfolioId={target?.portfolioId} />} />
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
            path="health"
            element={
              <div className="app-page">
                <HealthPage />
              </div>
            }
          />
          <Route path="trade/stocks/:symbol" element={<LegacyTrade stock />} />
          <Route path="trade/:symbol" element={<LegacyTrade />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </AppShell>
  );
}

function App() {
  const { data, isPending, isError, refetch } = useMe();
  const signInInput = useRef<HTMLInputElement>(null);
  if (data && !isPending && !isError) return <SignedIn key={data.email} />;

  return (
    <AppShell
      navigation={
        !isPending && !isError && <SessionButton onClick={() => signInInput.current?.focus()} />
      }
    >
      {isPending ? (
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
      ) : isError ? (
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
      ) : (
        <SignInPage inputRef={signInInput} />
      )}
    </AppShell>
  );
}

export default App;
