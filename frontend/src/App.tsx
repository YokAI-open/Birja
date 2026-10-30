import { useEffect, useRef } from "react";
import { ChartNoAxesCombined, Wallet, History } from "lucide-react";
import { NavLink, Navigate, Route, Routes, useLocation } from "react-router";
import type { Me } from "@/api/auth";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import MarketsPage from "@/pages/MarketsPage";
import { Card, CardContent } from "@/components/ui/card";
import { useMe } from "@/hooks/useMe";
import AccountPage from "@/pages/AccountPage";
import HealthPage from "@/pages/HealthPage";
import SignInPage from "@/pages/SignInPage";
import TradePage from "@/pages/TradePage";
import PortfolioPage from "@/pages/PortfolioPage";
import HistoryPage from "@/pages/HistoryPage";

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
  return data === null ? <SignInPage /> : <SignedIn me={data} />;
}

const navItem = ({ isActive }: { isActive: boolean }) =>
  cn(
    "inline-flex min-h-11 min-w-11 items-center justify-center gap-1 rounded-pill px-4 text-sm font-medium focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 motion-reduce:transition-none",
    isActive
      ? "bg-primary text-primary-foreground shadow-pill"
      : "text-muted-foreground hover:bg-muted",
  );

function SignedIn({ me }: { me: Me }) {
  const { pathname } = useLocation();
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
          <NavLink to="/portfolio" className={navItem}>
            <Wallet aria-hidden="true" className="size-5 md:hidden" />
            Portfolio
          </NavLink>
          <NavLink to="/history" className={navItem}>
            <History aria-hidden="true" className="size-5 md:hidden" />
            History
          </NavLink>
        </nav>
        <NavLink to="/account" className={navItem}>
          Account
        </NavLink>
      </div>
      <div ref={content}>
        <Routes>
          <Route index element={<MarketsPage />} />
          <Route path="portfolio" element={<PortfolioPage />} />
          <Route path="history" element={<HistoryPage />} />
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
          <Route path="trade/:symbol" element={<TradePage />} />
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
      <main className="mx-auto max-w-[1440px] px-4 pb-[calc(80px+env(safe-area-inset-bottom))] md:px-8 md:pb-8">
        <AuthSwitch />
      </main>
    </>
  );
}

export default App;
