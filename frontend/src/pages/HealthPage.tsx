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

  // TanStack Query keeps the last good data when a refetch fails, so an error wins over it.
  const live = isError ? undefined : data;

  const services: { name: string; label: Label }[] = [
    { name: "API", label: live ? "Connected" : "Unavailable" },
    { name: "Database", label: live ? fromState(live.db) : "Unknown" },
    { name: "Redis", label: live ? fromState(live.redis) : "Unknown" },
  ];

  let summary = "Checking services…";
  if (live) {
    summary = live.status === "ok" ? "All systems operational" : "Some services are unavailable";
  } else if (isError) {
    summary = "Some services are unavailable";
  }

  return (
    <Card role="region" aria-labelledby="health-title">
      <CardContent className="gap-5">
        <h1 id="health-title" className="text-2xl leading-tight font-semibold">
          System status
        </h1>
        <p className="text-muted-foreground">{summary}</p>
        <ul aria-label="Service status" aria-busy={isPending} className="border-y border-border">
          {isPending
            ? ["API", "Database", "Redis"].map((name) => (
                <li key={name} className="flex min-h-15 items-center border-b border-border">
                  <span className="h-4 w-full rounded-control bg-muted" />
                </li>
              ))
            : services.map(({ name, label }) => (
                <li
                  key={name}
                  className="flex min-h-15 items-center justify-between border-b border-border last:border-b-0"
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
        <div className="flex flex-wrap items-center justify-between gap-4">
          {data ? (
            <p className="text-sm text-muted-foreground tabular-nums">
              Last checked {timeFormat.format(dataUpdatedAt)}
            </p>
          ) : (
            <span />
          )}
          <Button
            variant="secondary"
            aria-label="Check again"
            disabled={isFetching}
            onClick={() => void refetch()}
          >
            {isFetching ? "Checking…" : "Check again"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export default HealthPage;
