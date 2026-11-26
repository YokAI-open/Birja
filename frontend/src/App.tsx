import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
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
import StockCatalogTradePage from "@/pages/StockCatalogTradePage";
import StockTradePage from "@/pages/StockTradePage";
import TradePage from "@/pages/TradePage";
import PortfolioPage from "@/pages/PortfolioPage";
import PortfoliosPage from "@/pages/PortfoliosPage";
import { PortfolioSwitcher } from "@/components/PortfolioSwitcher";
import HistoryPage from "@/pages/HistoryPage";
import { PortfolioTargetBoundary } from "@/components/PortfolioTargetBoundary";
import { PortfolioToolbarSlot } from "@/components/PortfolioToolbarSlot";
import { usePortfolioTarget } from "@/hooks/usePortfolioTarget";
import { isPortfolioId } from "@/api/portfolios";
import { isCatalogId } from "@/api/stockCatalog";
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
  const primaryHeading = useRef<HTMLHeadingElement>(null);
  const managementFocus = useRef<Element | null>(null);
  const editTrigger = useRef<HTMLButtonElement>(null);
  const [updateSlot, setUpdateSlot] = useState<HTMLDivElement | null>(null);
  const [removeSlot, setRemoveSlot] = useState<HTMLDivElement | null>(null);
  const [editingId, setEditingId] = useState<string>();
  const detailMatch = useMatch({ path: "/portfolios/:portfolioId", end: true });
  const detail = isPortfolioId(portfolioId) && detailMatch !== null;
  const ready = detail && target.status === "ready";
  const management = usePortfolioManagement(detail ? portfolioId : undefined);
  const editOpen = editingId !== undefined && editingId === portfolioId;
  useEffect(() => {
    if (!updateSlot) return;
    // React focus events follow the portal's logical tree. Use the slot's DOM event.
    const recordUpdateFocus = (event: FocusEvent) => {
      if (event.target instanceof HTMLElement) managementFocus.current = event.target;
    };
    updateSlot.addEventListener("focusin", recordUpdateFocus);
    return () => updateSlot.removeEventListener("focusin", recordUpdateFocus);
  }, [updateSlot]);
  useEffect(() => {
    if (target.status === "loading" || target.status === "ready") return;
    if (
      managementFocus.current &&
      !managementFocus.current.isConnected &&
      document.activeElement === document.body
    )
      primaryHeading.current?.focus();
  }, [target.status]);
  return (
    <div className={detail ? "portfolio-workspace" : "contents"}>
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
        <div
          className="portfolio-managed-toolbar"
          role="group"
          aria-label="Portfolio controls"
          onFocusCapture={(event) => {
            managementFocus.current = event.target;
          }}
        >
          <div className="portfolio-managed-picker">
            <PortfolioSwitcher portfolioId={portfolioId} inline />
          </div>
          {ready && (
            <div className="portfolio-managed-actions">
              <Button
                ref={editTrigger}
                type="button"
                variant="secondary"
                aria-label="Edit portfolio"
                className="min-h-11 rounded-pill px-4"
                disabled={editOpen || management.metadataPending || management.metadataBlocked}
                onClick={() => setEditingId(portfolioId)}
              >
                Edit
              </Button>
              <div ref={setUpdateSlot} className="min-w-0" />
              <div ref={setRemoveSlot} className="min-w-0" />
            </div>
          )}
        </div>
      )}
      <PortfolioToolbarSlot.Provider value={detail ? updateSlot : undefined}>
        <PortfolioTargetBoundary primaryHeading={detail ? primaryHeading : undefined} />
      </PortfolioToolbarSlot.Provider>
      {detail && owner && (
        <div
          className="min-w-0"
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
      className="ml-auto size-11 shrink-0 border-transparent bg-transparent text-muted-foreground aria-disabled:opacity-40"
      aria-label={signedIn ? label : "Go to sign-in form"}
      title={label}
      aria-disabled={pending}
      aria-busy={pending || undefined}
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
        <div className="mx-auto flex min-h-16 max-w-[1440px] flex-wrap items-center gap-x-1 gap-y-2 px-2 py-2 min-[375px]:gap-x-1.5 min-[375px]:px-3 sm:min-h-20 sm:gap-x-8 sm:px-6 md:px-8 lg:gap-x-12">
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

function catalogTradePath(portfolioId: string, catalogId: string) {
  return `/portfolios/${portfolioId}/trade/catalog/${catalogId}`;
}

function CatalogTradeEntry() {
  const { catalogId } = useParams();
  if (!isCatalogId(catalogId)) return <StockCatalogTradePage />;
  return (
    <PortfolioTargetBoundary
      tradeSymbol="this stock"
      legacyDestination={(portfolioId) => catalogTradePath(portfolioId, catalogId)}
    />
  );
}

function SignedIn({ onSignedOut }: { onSignedOut: () => void }) {
  const { pathname } = useLocation();
  const logout = useLogout();
  const logoutInFlight = useRef(false);

  async function signOut() {
    if (logoutInFlight.current || logout.isPending) return;
    logoutInFlight.current = true;
    try {
      await logout.mutateAsync();
      onSignedOut();
    } catch {
      // The mutation drives the existing retryable sign-out alert.
    } finally {
      logoutInFlight.current = false;
    }
  }

  // This memory belongs to this mounted signed-in identity only. Explicit
  // routes take priority, including their refusal; never fall back from one.
  const [openedId, setOpenedId] = useState<string>();
  const matchedId = matchPath("/portfolios/:portfolioId/*", pathname)?.params.portfolioId;
  const explicitId = isPortfolioId(matchedId) ? matchedId : undefined;
  const portfolioDetail = useMatch({ path: "/portfolios/:portfolioId", end: true });
  const portfolioHistory = useMatch({ path: "/portfolios/:portfolioId/history", end: true });
  const catalogId = useMatch("/portfolios/:portfolioId/trade/catalog/:catalogId")?.params.catalogId;
  const curatedTrade = useMatch("/portfolios/:portfolioId/trade/stocks/:symbol");
  const cryptoTrade = useMatch("/portfolios/:portfolioId/trade/:symbol");
  const tradeRoute = Boolean(catalogId || curatedTrade || cryptoTrade);
  const portfolioNavigation = useMatch("/portfolios/*");
  const portfoliosActive = Boolean(portfolioNavigation && !portfolioHistory);
  const navigation = usePortfolioTarget(explicitId ?? openedId);
  const target = navigation.status === "ready" ? navigation.target : null;
  if (explicitId && target && openedId !== explicitId) setOpenedId(explicitId);
  const portfolioBlock =
    openedId && !target ? (navigation.status === "loading" ? "pending" : "unavailable") : undefined;
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
          <nav
            aria-label="Main"
            className="flex min-w-0 flex-wrap items-center gap-0.5 min-[375px]:gap-1 sm:gap-2"
          >
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
          <SessionButton signedIn pending={logout.isPending} onClick={() => void signOut()} />
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
          <div className={tradeRoute ? "trade-chooser-shell" : "mx-auto mt-6 max-w-[1280px]"}>
            <PortfolioSwitcher
              portfolioId={explicitId}
              inline={tradeRoute}
              label={portfolioHistory ? "History portfolio" : undefined}
              destination={
                portfolioHistory
                  ? (id) => `/portfolios/${id}/history`
                  : isCatalogId(catalogId)
                    ? (id) => catalogTradePath(id, catalogId)
                    : undefined
              }
            />
          </div>
        )}
        <Routes>
          <Route
            index
            element={
              <MarketsPage
                portfolioId={openedId}
                onSelectPortfolio={setOpenedId}
                portfolioBlock={portfolioBlock}
              />
            }
          />
          <Route path="portfolios/deletion" element={<PortfolioDeletionPage />} />
          <Route path="portfolios/:portfolioId" element={<PortfolioRoute />}>
            <Route index element={<PortfolioPage />} />
            <Route path="history" element={<HistoryPage />} />
            <Route path="trade/catalog/:catalogId" element={<StockCatalogTradePage />} />
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
          <Route path="trade/catalog/:catalogId" element={<CatalogTradeEntry />} />
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
  const pendingSignInFocus = useRef(false);
  const bindSignInInput = useCallback((input: HTMLInputElement | null) => {
    signInInput.current = input;
    if (input && pendingSignInFocus.current) {
      pendingSignInFocus.current = false;
      input.focus();
    }
  }, []);
  const focusSignIn = () => {
    if (signInInput.current) signInInput.current.focus();
    else pendingSignInFocus.current = true;
  };
  if (data && !isPending && !isError) {
    return <SignedIn key={data.email} onSignedOut={focusSignIn} />;
  }

  return (
    <AppShell navigation={!isPending && !isError && <SessionButton onClick={focusSignIn} />}>
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
        <SignInPage inputRef={bindSignInInput} />
      )}
    </AppShell>
  );
}

export default App;
