export type Health = {
  status: "ok" | "degraded";
  db: "ok" | "error";
  redis: "ok" | "error";
};

const isOkOrError = (value: unknown): value is "ok" | "error" =>
  value === "ok" || value === "error";

export function isHealth(value: unknown): value is Health {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return false;
  }
  const v = value as Record<string, unknown>;
  return (
    (v.status === "ok" || v.status === "degraded") && isOkOrError(v.db) && isOkOrError(v.redis)
  );
}

/** 200 and 503 both carry a health body (503 = a dependency is down); anything else throws. */
export async function fetchHealth(): Promise<Health> {
  const response = await fetch("/api/v1/health", { headers: { Accept: "application/json" } });
  if (response.status !== 200 && response.status !== 503) {
    throw new Error(`Health check failed with status ${response.status}`);
  }
  const body: unknown = await response.json();
  if (!isHealth(body)) {
    throw new Error("Unexpected health response");
  }
  return body;
}
