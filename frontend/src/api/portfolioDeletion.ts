import { ApiError, guardedJsonRequest } from "./client";
import { isCanonicalPortfolioName, isPortfolioId } from "./portfolios";

export const DELETION_POLICY = "freeze_at_closure_v1" as const;
export type PortfolioDeletionIntent = Readonly<{
  portfolioId: string;
  intentKey: string;
  confirmationName: string;
  policyVersion: typeof DELETION_POLICY;
}>;
export type PortfolioDeletionReceipt = Readonly<{ portfolioId: string; state: "closed" }>;
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

export class PortfolioDeletionError extends Error {
  readonly outcome: "refused" | "unknown";
  readonly code: string | null;
  readonly status: number | null;
  readonly retryAfter: number | null;
  readonly terminal: boolean;
  constructor(
    outcome: "refused" | "unknown",
    code: string | null = null,
    status: number | null = null,
    retryAfter: number | null = null,
    /** Only a durable original outcome resolves a previously unknown request. */
    terminal = false,
  ) {
    super(
      outcome === "unknown"
        ? "Deletion result unconfirmed. Check the original request."
        : "Portfolio deletion refused.",
    );
    this.name = "PortfolioDeletionError";
    this.outcome = outcome;
    this.code = code;
    this.status = status;
    this.retryAfter = retryAfter;
    this.terminal = terminal;
  }
}

/** Copy exact canonical review metadata, never normalize it or retain caller-owned objects. */
export function capturePortfolioDeletionIntent(value: unknown): PortfolioDeletionIntent {
  if (typeof value !== "object" || value === null || Array.isArray(value)) invalid();
  const input = value as Record<string, unknown>;
  if (Object.keys(input).sort().join() !== "confirmationName,intentKey,policyVersion,portfolioId")
    invalid();
  const v = {
    portfolioId: input.portfolioId,
    intentKey: input.intentKey,
    confirmationName: input.confirmationName,
    policyVersion: input.policyVersion,
  };
  if (
    !isPortfolioId(v.portfolioId) ||
    typeof v.intentKey !== "string" ||
    !uuid.test(v.intentKey) ||
    !isCanonicalPortfolioName(v.confirmationName) ||
    v.policyVersion !== DELETION_POLICY
  )
    invalid();
  return Object.freeze({
    portfolioId: v.portfolioId as string,
    intentKey: v.intentKey as string,
    confirmationName: v.confirmationName as string,
    policyVersion: DELETION_POLICY,
  });
}
function invalid(): never {
  throw new PortfolioDeletionError("refused", "invalid_input");
}
const codes: Record<number, readonly string[]> = {
  401: ["not_authenticated", "invalid_session", "session_expired"],
  403: ["csrf_failed", "csrf_invalid"],
  404: ["portfolio_unavailable"],
  409: ["portfolio_confirmation_changed", "closure_intent_conflict"],
  413: ["body_too_large"],
  415: ["unsupported_media_type"],
  422: ["invalid_input"],
  429: ["closure_quota", "rate_limited"],
  500: ["service_unavailable"],
  503: ["service_unavailable"],
};

export async function deletePortfolio(
  input: PortfolioDeletionIntent,
  signal: AbortSignal | undefined,
  isCurrent: () => boolean,
): Promise<PortfolioDeletionReceipt> {
  // Capture before CSRF, authentication, network or JSON awaits.
  const original = capturePortfolioDeletionIntent(input);
  const body = JSON.stringify({
    intent_key: original.intentKey,
    confirmation_name: original.confirmationName,
    policy_version: original.policyVersion,
  });
  try {
    const value = await guardedJsonRequest(
      `/api/v2/portfolios/${original.portfolioId}`,
      { method: "DELETE", body, signal, credentials: "same-origin", cache: "no-store" },
      isCurrent,
    );
    signal?.throwIfAborted();
    if (!isCurrent()) throw new Error("Request context unavailable");
    if (typeof value !== "object" || value === null || Array.isArray(value)) throw new Error();
    const v = value as Record<string, unknown>;
    if (
      Object.keys(v).sort().join() !== "portfolio_id,state" ||
      v.portfolio_id !== original.portfolioId ||
      v.state !== "closed"
    )
      throw new Error();
    return Object.freeze({ portfolioId: original.portfolioId, state: "closed" });
  } catch (error) {
    if (error instanceof ApiError) {
      const code =
        error.code !== null && codes[error.status]?.includes(error.code) ? error.code : null;
      const terminal = error.status === 409 && code === "portfolio_confirmation_changed";
      const refused = code !== null && error.status < 500;
      throw new PortfolioDeletionError(
        refused ? "refused" : "unknown",
        code,
        error.status,
        error.retryAfter,
        terminal,
      );
    }
    // Cancellation/context revocation can follow commit: neither resolves the original.
    throw new PortfolioDeletionError("unknown");
  }
}
