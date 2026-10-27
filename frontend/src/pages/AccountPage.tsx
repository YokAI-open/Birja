import type { Me } from "@/api/auth";
import { useLogout } from "@/hooks/useAuthMutations";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { formatUsd } from "@/lib/money";

function AccountPage({ me }: { me: Me }) {
  const logout = useLogout();
  return (
    <Card className="mx-auto my-8 max-w-xl">
      <CardContent className="flex flex-col gap-4">
        <h2 className="text-xl leading-7 font-semibold tracking-[-0.01em]">Your account</h2>
        <div>
          <p className="text-[13px] leading-[18px] font-medium text-muted-foreground">Email</p>
          <p className="font-medium">{me.email}</p>
        </div>
        <div>
          <p className="text-[13px] leading-[18px] font-medium text-muted-foreground">Cash</p>
          <p className="text-[32px] leading-9 font-medium tracking-[-0.02em] tabular-nums">
            {formatUsd(me.cash_usd)}
          </p>
        </div>
        {logout.isError ? (
          <p role="alert" className="text-loss-text">
            Couldn&apos;t sign out. Try again.
          </p>
        ) : null}
        <Button variant="secondary" disabled={logout.isPending} onClick={() => logout.mutate()}>
          {logout.isPending ? "Signing out…" : "Sign out"}
        </Button>
      </CardContent>
    </Card>
  );
}

export default AccountPage;
