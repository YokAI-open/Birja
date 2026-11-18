import { apiFetch, ApiError } from "./client";
import { isPortfolioId, isCanonicalPortfolioName, portfolioNameDisplay } from "./portfolios";

export { portfolioNameDisplay } from "./portfolios";
export type PortfolioMetadata = Readonly<{ id: string; name: string; description: string }>;
export type PortfolioCreation = Readonly<{ key: string; name: string; description?: string }>;
export type PortfolioMetadataPatch = Readonly<{ name?: string; description?: string }>;

/** Normalize line endings for validation/counters, without changing submitted intent. */
export function normalizePortfolioDescription(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const normalized = value.replace(/\r\n?/g, "\n");
  return [...normalized].some((c) => {
    const point = c.codePointAt(0)!;
    return (
      (point < 32 && point !== 9 && point !== 10) ||
      (point >= 127 && point <= 159) ||
      (point >= 0xd800 && point <= 0xdfff)
    );
  }) || [...normalized].length > 1000
    ? null
    : normalized;
}

function record(value: unknown): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value) &&
    (Object.getPrototypeOf(value) === Object.prototype || Object.getPrototypeOf(value) === null)
  );
}

export function parsePortfolioMetadata(value: unknown, requestedId?: string): PortfolioMetadata {
  if (
    !record(value) ||
    Object.keys(value).length !== 3 ||
    !isPortfolioId(value.id) ||
    (requestedId !== undefined && value.id !== requestedId) ||
    !isCanonicalPortfolioName(value.name) ||
    typeof value.description !== "string" ||
    normalizePortfolioDescription(value.description) !== value.description
  )
    throw new Error("Unexpected portfolio metadata");
  return Object.freeze({ id: value.id, name: value.name, description: value.description });
}

export class PortfolioManagementError extends Error {
  readonly outcome: "refused" | "unknown";
  readonly code: string | null;
  readonly status: number | null;
  readonly retryAfter: number | null;
  constructor(
    outcome: "refused" | "unknown",
    code: string | null = null,
    status: number | null = null,
    retryAfter: number | null = null,
  ) {
    super(
      outcome === "unknown"
        ? "Portfolio result unavailable. Check the original request."
        : "Portfolio request refused.",
    );
    this.name = "PortfolioManagementError";
    this.outcome = outcome;
    this.code = code;
    this.status = status;
    this.retryAfter = retryAfter;
  }
}

const refusals: Record<number, readonly string[]> = {
  404: ["portfolio_unavailable"],
  409: ["name_taken", "creation_key_conflict", "portfolio_limit"],
  413: ["body_too_large"],
  415: ["unsupported_media_type"],
  422: ["invalid_input", "invalid_creation_key"],
  429: ["creation_quota", "rate_limited"],
  500: ["service_unavailable"],
  503: ["service_unavailable"],
};
function failure(error: unknown): never {
  if (error instanceof Error && error.name === "AbortError") throw error;
  if (error instanceof ApiError) {
    const code =
      error.code !== null && refusals[error.status]?.includes(error.code) ? error.code : null;
    // Do not retain arbitrary server detail, messages or ownership/financial fields.
    const refused =
      (code !== null && error.status < 500) || error.status === 401 || error.status === 403;
    const wait =
      error.retryAfter !== null && Number.isSafeInteger(error.retryAfter) && error.retryAfter >= 0
        ? error.retryAfter
        : null;
    throw new PortfolioManagementError(refused ? "refused" : "unknown", code, error.status, wait);
  }
  throw new PortfolioManagementError("unknown");
}
function invalid(): never {
  throw new PortfolioManagementError("refused", "invalid_input");
}
function validPatch(value: unknown): value is PortfolioMetadataPatch {
  return (
    record(value) &&
    Object.keys(value).length > 0 &&
    Object.keys(value).every((k) => k === "name" || k === "description") &&
    (!("name" in value) || portfolioNameDisplay(value.name) !== null) &&
    (!("description" in value) || normalizePortfolioDescription(value.description) !== null)
  );
}

export async function fetchPortfolioMetadata(
  id: string,
  signal?: AbortSignal,
): Promise<PortfolioMetadata> {
  signal?.throwIfAborted();
  if (!isPortfolioId(id)) invalid();
  try {
    const value = await apiFetch(`/api/v2/portfolios/${id}/metadata`, {
      signal,
      cache: "no-store",
      credentials: "same-origin",
    });
    return parsePortfolioMetadata(value, id);
  } catch (error) {
    failure(error);
  }
}

export async function createPortfolio(
  input: PortfolioCreation,
  signal?: AbortSignal,
): Promise<PortfolioMetadata> {
  signal?.throwIfAborted();
  if (
    !record(input) ||
    Object.keys(input).some((k) => !["key", "name", "description"].includes(k)) ||
    typeof input.key !== "string" ||
    !/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(input.key) ||
    portfolioNameDisplay(input.name) === null ||
    ("description" in input && normalizePortfolioDescription(input.description) === null)
  )
    invalid();
  // Snapshot strings before any CSRF/refresh await; auth recovery reuses these exact bytes.
  const key = input.key;
  const body = JSON.stringify({ name: input.name, description: input.description ?? "" });
  try {
    return parsePortfolioMetadata(
      await apiFetch("/api/v2/portfolios", {
        method: "POST",
        headers: { "Idempotency-Key": key },
        body,
        signal,
        cache: "no-store",
        credentials: "same-origin",
      }),
    );
  } catch (error) {
    failure(error);
  }
}

export async function updatePortfolioMetadata(
  id: string,
  patch: PortfolioMetadataPatch,
  signal?: AbortSignal,
): Promise<PortfolioMetadata> {
  signal?.throwIfAborted();
  if (!isPortfolioId(id) || !validPatch(patch)) invalid();
  const body = JSON.stringify(patch);
  try {
    return parsePortfolioMetadata(
      await apiFetch(`/api/v2/portfolios/${id}`, {
        method: "PATCH",
        body,
        signal,
        cache: "no-store",
        credentials: "same-origin",
      }),
      id,
    );
  } catch (error) {
    failure(error);
  }
}
