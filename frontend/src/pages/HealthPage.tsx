import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useHealth } from "@/hooks/useHealth";

type Label = "Connected" | "Unavailable" | "Unknown";

const VARIANT = { Connected: "success", Unavailable: "danger", Unknown: "neutral" } as const;

const timeFormat = new Intl.DateTimeFormat(undefined, { timeStyle: "medium" });

const fromState = (state: "ok" | "error"): Label => (state === "ok" ? "Connected" : "Unavailable");

function HealthPage() {
  const { data, isError, isPending, isFetching, dataUpdatedAt, refetch } = useHealth();

  const services: { name: string; label: Label }[] = [
    { name: "API", label: data ? "Connected" : "Unavailable" },
    { name: "Database", label: data ? fromState(data.db) : "Unknown" },
    { name: "Redis", label: data ? fromState(data.redis) : "Unknown" },
  ];

  let summary = "Checking services…";
  if (data) {
    summary = data.status === "ok" ? "All systems operational" : "Some services are unavailable";
  }

  return (
    <Card className="mx-auto my-8 max-w-xl">
      <CardContent className="flex flex-col gap-4">
        <h1 className="text-[32px] leading-9 font-medium tracking-[-0.02em] md:text-[40px] md:leading-[44px]">
          System status
        </h1>
        <p className="text-muted-foreground">{summary}</p>
        <ul aria-label="Service status" aria-busy={isPending}>
          {isPending
            ? ["API", "Database", "Redis"].map((name) => (
                <li key={name} className="flex h-[52px] items-center border-b border-border">
                  <span className="h-4 w-full rounded-control bg-muted" />
                </li>
              ))
            : services.map(({ name, label }) => (
                <li
                  key={name}
                  className="flex h-[52px] items-center justify-between border-b border-border last:border-b-0"
                >
                  <span>{name}</span>
                  <Badge variant={VARIANT[label]}>{label}</Badge>
                </li>
              ))}
        </ul>
        {isError && (
          <p role="alert" className="text-loss-text">
            Can&apos;t reach the backend. It will retry automatically.
          </p>
        )}
        <div className="flex items-center justify-between gap-4">
          {data ? (
            <p className="text-xs leading-4 text-muted-foreground tabular-nums">
              Last checked {timeFormat.format(dataUpdatedAt)}
            </p>
          ) : (
            <span />
          )}
          <Button aria-label="Check again" disabled={isFetching} onClick={() => void refetch()}>
            {isFetching ? "Checking…" : "Check again"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export default HealthPage;
