import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useMe } from "@/hooks/useMe";
import AccountPage from "@/pages/AccountPage";
import HealthPage from "@/pages/HealthPage";
import SignInPage from "@/pages/SignInPage";

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
  return data === null ? <SignInPage /> : <AccountPage me={data} />;
}

function App() {
  return (
    <>
      <header className="mx-auto flex max-w-[1440px] items-center gap-3 px-4 py-4 md:px-8">
        <span aria-hidden="true" className="size-8 rounded-control bg-brand" />
        <span className="text-xl font-semibold tracking-[-0.01em]">Birja</span>
      </header>
      <main className="mx-auto max-w-[1440px] px-4 md:px-8">
        <AuthSwitch />
        <HealthPage />
      </main>
    </>
  );
}

export default App;
