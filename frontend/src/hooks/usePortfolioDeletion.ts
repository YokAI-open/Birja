import { useCallback, useEffect, useLayoutEffect, useMemo, useSyncExternalStore } from "react";
import { useMutation, useQueryClient, type QueryClient } from "@tanstack/react-query";
import {
  capturePortfolioDeletionIntent,
  DELETION_POLICY,
  deletePortfolio,
  PortfolioDeletionError,
  type PortfolioDeletionIntent,
} from "@/api/portfolioDeletion";
import { type PortfolioMetadata } from "@/api/portfolioManagement";
import { isPortfolioId } from "@/api/portfolios";
import {
  clearDeletionRecovery,
  openDeletionRecovery,
  type DeletionRecovery,
} from "@/lib/portfolioDeletionAttempt";
import { useMe } from "./useMe";
import { broadcastMetadataChange } from "@/lib/portfolioMetadataEvents";

export type PortfolioDeletionCompletion = Readonly<{
  portfolioId: string;
  confirmationName: string;
  isCurrent: () => boolean;
}>;
export type PortfolioDeletionState = Readonly<{
  phase:
    | "idle"
    | "review"
    | "persisting"
    | "submitting"
    | "unknown"
    | "checking"
    | "terminal_refusal"
    | "closed";
  review: PortfolioDeletionIntent | null;
  attempt: PortfolioDeletionIntent | null;
  reviewRequired: boolean;
  error: Error | null;
  retryAt: number | null;
  receipt?: PortfolioDeletionCompletion;
}>;
type Scope = {
  owner: string | null;
  serial: number;
  portfolioId: string | undefined;
  route: string;
};
type Session = {
  owner: string | null;
  known: boolean;
  serial: number;
  version: number;
  now: number;
  listeners: Set<() => void>;
  state: PortfolioDeletionState;
  recovery: DeletionRecovery | null;
  loading: boolean;
  operation: number;
  operationScope: Scope | null;
  reviewScope: Scope | null;
  controller: AbortController | null;
  quarantined: Set<string>;
  releaseAfterReview: string | null;
};
const empty = (): PortfolioDeletionState =>
  Object.freeze({
    phase: "idle",
    review: null,
    attempt: null,
    reviewRequired: false,
    error: null,
    retryAt: null,
  });
const storageError = () =>
  new Error("Deletion recovery storage unavailable. No new deletion was sent.");
const sessions = new WeakMap<QueryClient, Session>();
// A replaced provider's old cache can still emit removal/logout notifications.
// It may revoke its own memory, never erase the current tab's recovery lease.
let persistenceClient: WeakRef<QueryClient> | undefined;
const activeScopes = new WeakSet<Scope>();
const who = (client: QueryClient) =>
  client.getQueryData<{ email: string } | null>(["me"])?.email ?? null;
function publish(session: Session, state?: PortfolioDeletionState) {
  if (state) session.state = Object.freeze(state);
  session.now = Date.now();
  session.version++;
  session.listeners.forEach((notify) => notify());
}
function update(session: Session, changes: Partial<Session>) {
  Object.assign(session, changes);
}
function metadataFor(client: QueryClient, owner: string, id: string): PortfolioMetadata | null {
  const queries = client.getQueryCache().findAll({ queryKey: ["portfolioMetadata", owner, id] });
  const usable = queries.filter(
    (query) =>
      query.state.status === "success" &&
      !query.state.isInvalidated &&
      query.state.fetchStatus === "idle",
  );
  if (usable.length !== 1) return null;
  const data = usable[0].state.data as PortfolioMetadata | undefined;
  return data?.id === id ? data : null;
}
function metadataBusy(client: QueryClient, owner: string, id: string) {
  return client
    .getQueryCache()
    .findAll({ queryKey: ["portfolioMetadataDraft", owner, id] })
    .some((query) => {
      const state = query.state.data as
        | { pending?: unknown; awaitingFetch?: unknown; draft?: unknown; reviewRequired?: unknown }
        | undefined;
      return (
        state?.pending === true ||
        state?.awaitingFetch === true ||
        state?.draft != null ||
        state?.reviewRequired === true
      );
    });
}
function sessionFor(client: QueryClient): Session {
  const existing = sessions.get(client);
  if (existing) return existing;
  const session: Session = {
    owner: who(client),
    known: client.getQueryData(["me"]) !== undefined,
    serial: 0,
    version: 0,
    now: Date.now(),
    listeners: new Set(),
    state: empty(),
    recovery: null,
    loading: false,
    operation: 0,
    operationScope: null,
    reviewScope: null,
    controller: null,
    quarantined: new Set(),
    releaseAfterReview: null,
  };
  sessions.set(client, session);
  client.getQueryCache().subscribe((event) => {
    const owner = who(client);
    const known = client.getQueryData(["me"]) !== undefined;
    if (!session.known && !known) return;
    if (!session.known && owner !== null) {
      session.known = known;
      session.owner = owner;
      session.serial++;
      publish(session);
      return;
    }
    session.known = known;
    if (owner !== session.owner) {
      session.owner = owner;
      session.serial++;
      session.operation++;
      session.controller?.abort();
      session.controller = null;
      session.operationScope = null;
      session.reviewScope = null;
      session.recovery = null;
      session.loading = false;
      session.quarantined.clear();
      session.releaseAfterReview = null;
      // Cache absence/GC revokes in-memory authority but is not an
      // authenticated logout. Keep the original durable recovery marker.
      if (known)
        clearDeletionRecovery(() => persistenceClient?.deref() === client && who(client) === owner);
      publish(session, empty());
      return;
    }
    // Observer option notifications are render bookkeeping, not authority changes.
    // Publishing them would feed a subscribed metadata editor back into itself.
    if (event.type !== "updated" && event.type !== "removed") return;
    const [prefix, email, id] = event.query.queryKey;
    if (email !== owner || typeof id !== "string" || owner === null) return;
    if (prefix !== "portfolioMetadata" && prefix !== "portfolioMetadataDraft") return;
    const state = session.state;
    if (state.phase === "review" && state.review?.portfolioId === id) {
      const data = event.query.state.data as PortfolioMetadata | undefined;
      const changed =
        prefix === "portfolioMetadata" &&
        data?.name !== undefined &&
        data.name !== state.review.confirmationName;
      publish(
        session,
        changed
          ? {
              ...state,
              reviewRequired: true,
              error: new Error(
                "This portfolio's name changed. Review its latest name before confirming deletion again.",
              ),
            }
          : undefined,
      );
    }
    if (session.releaseAfterReview === id && metadataFor(client, owner, id) !== null) {
      session.releaseAfterReview = null;
      session.quarantined.delete(id);
      publish(session);
    }
  });
  return session;
}

/** A private in-memory signal; consumers must still verify owned-active server authority. */
export function subscribePortfolioDeletion(client: QueryClient, changed: () => void) {
  const session = sessionFor(client);
  session.listeners.add(changed);
  return () => {
    session.listeners.delete(changed);
  };
}
export function portfolioDeletionRevision(client: QueryClient) {
  return sessionFor(client).version;
}
/** Captured authority cannot revive after a replacement provider returns. */
export function portfolioDeletionAuthorityGeneration(client: QueryClient) {
  return sessionFor(client).serial;
}
/** Restore the owner-bound marker before rendering private financial authority. */
export function portfolioDeletionAuthorityReady(client: QueryClient, owner: string) {
  const session = sessionFor(client);
  return (
    persistenceClient?.deref() === client &&
    session.owner === owner &&
    session.recovery !== null &&
    !session.loading
  );
}
export function isPortfolioDeletionQuarantined(client: QueryClient, owner: string, id: string) {
  const session = sessionFor(client);
  return session.owner === owner && session.quarantined.has(id);
}
/** Metadata review exclusion is distinct from post-submit financial quarantine. */
export function isPortfolioDeletionMetadataBlocked(client: QueryClient, owner: string, id: string) {
  const session = sessionFor(client);
  return (
    !portfolioDeletionAuthorityReady(client, owner) ||
    isPortfolioDeletionQuarantined(client, owner, id) ||
    (session.owner === owner &&
      session.state.phase === "review" &&
      session.state.review?.portfolioId === id)
  );
}

/** Mount outside the financial Outlet. Storage restoration never submits DELETE. */
export function usePortfolioDeletion(
  portfolioId?: string,
  options: { route?: string; onClosed?: (receipt: PortfolioDeletionCompletion) => void } = {},
) {
  const client = useQueryClient();
  const identity = useMe();
  const session = sessionFor(client);
  const version = useSyncExternalStore(
    useCallback((notify) => subscribePortfolioDeletion(client, notify), [client]),
    useCallback(() => session.version, [session]),
  );
  const owner = identity.data?.email ?? null;
  const serial = session.serial;
  const route = options.route ?? "";
  const scope = useMemo(
    () => ({ owner, serial, portfolioId, route }),
    [owner, serial, portfolioId, route],
  );
  const current = () =>
    activeScopes.has(scope) &&
    persistenceClient?.deref() === client &&
    owner !== null &&
    who(client) === owner &&
    session.owner === owner &&
    session.serial === serial;
  const ownerCurrent = () =>
    persistenceClient?.deref() === client &&
    owner !== null &&
    who(client) === owner &&
    session.owner === owner &&
    session.serial === serial;
  const view = session.state;
  const restore = async () => {
    if (!ownerCurrent() || session.loading || session.recovery) return;
    update(session, { loading: true });
    publish(session);
    try {
      const recovery = await openDeletionRecovery(owner!, ownerCurrent);
      if (!ownerCurrent()) return;
      const attempt = recovery.attempt;
      update(session, { recovery });
      if (attempt) {
        session.quarantined.add(attempt.portfolioId);
        publish(session, { ...empty(), phase: "unknown", attempt });
      }
    } catch {
      if (ownerCurrent()) publish(session, { ...session.state, error: storageError() });
    } finally {
      if (ownerCurrent()) {
        update(session, { loading: false });
        publish(session);
      }
    }
  };
  useLayoutEffect(() => {
    const previous = persistenceClient?.deref();
    persistenceClient = new WeakRef(client);
    if (previous && previous !== client) {
      const retired = sessions.get(previous);
      if (retired) {
        retired.serial++;
        retired.operation++;
        retired.controller?.abort();
        update(retired, {
          controller: null,
          operationScope: null,
          reviewScope: null,
          recovery: null,
          loading: false,
        });
        publish(retired, empty());
      }
    }
    if (session.known && session.owner === null)
      clearDeletionRecovery(() => persistenceClient?.deref() === client && who(client) === null);
  }, [client, session]);
  useLayoutEffect(() => {
    activeScopes.add(scope);
    publish(session);
    void restore();
    return () => {
      activeScopes.delete(scope);
      if (session.reviewScope === scope && session.state.phase === "review") {
        update(session, { reviewScope: null });
        publish(session, empty());
      }
      if (session.operationScope === scope) {
        update(session, { operation: session.operation + 1, operationScope: null });
        session.controller?.abort();
        update(session, { controller: null });
        if (session.state.attempt) publish(session, { ...session.state, phase: "unknown" });
      }
    };
    // The owner-bound recovery handle outlives this route; captured callbacks do not.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [client, scope, session]);
  useEffect(() => {
    if (view.retryAt === null) return;
    const delay = view.retryAt - Date.now();
    if (delay <= 0) return;
    const timer = setTimeout(() => {
      if (ownerCurrent() && session.state === view) publish(session);
    }, delay);
    return () => clearTimeout(timer);
    // A server Retry-After is a wait boundary, never a mutation retry.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [view, session, scope, version]);
  const mutation = useMutation({
    retry: false,
    gcTime: 0,
    mutationFn: ({
      intent,
      controller,
      isCurrent,
    }: {
      intent: PortfolioDeletionIntent;
      controller: AbortController;
      isCurrent: () => boolean;
    }) => deletePortfolio(intent, controller.signal, isCurrent),
  });
  const reviewed = (intent: PortfolioDeletionIntent) =>
    owner !== null &&
    metadataFor(client, owner, intent.portfolioId)?.name === intent.confirmationName &&
    !metadataBusy(client, owner, intent.portfolioId);
  function reviewDeletion(metadata: PortfolioMetadata) {
    if (
      !current() ||
      !session.recovery ||
      session.loading ||
      session.state.attempt ||
      !isPortfolioId(portfolioId) ||
      metadata.id !== portfolioId ||
      session.quarantined.has(portfolioId)
    )
      return false;
    const latest = metadataFor(client, owner!, portfolioId);
    if (
      !latest ||
      latest.name !== metadata.name ||
      latest.description !== metadata.description ||
      metadataBusy(client, owner!, portfolioId)
    )
      return false;
    try {
      const review = capturePortfolioDeletionIntent({
        portfolioId,
        confirmationName: latest.name,
        intentKey: crypto.randomUUID(),
        policyVersion: DELETION_POLICY,
      });
      update(session, { reviewScope: scope });
      publish(session, { ...empty(), phase: "review", review });
      return true;
    } catch {
      return false;
    }
  }
  function cancelReview() {
    if (
      !current() ||
      session.state !== view ||
      view.phase !== "review" ||
      session.reviewScope !== scope
    )
      return;
    update(session, { reviewScope: null });
    publish(session, empty());
  }
  async function perform(intent: PortfolioDeletionIntent, recovering: boolean) {
    const operation = session.operation + 1;
    update(session, { operation, operationScope: scope });
    const operationCurrent = () =>
      current() && session.operation === operation && session.operationScope === scope;
    publish(session, {
      ...view,
      phase: recovering ? "checking" : "persisting",
      error: null,
      retryAt: null,
    });
    let original: PortfolioDeletionIntent;
    try {
      if (!operationCurrent()) return;
      original = session.recovery!.persist(intent);
      if (!operationCurrent()) return;
    } catch {
      if (operationCurrent()) {
        update(session, { operationScope: null });
        publish(session, { ...view, error: storageError() });
      }
      return;
    }
    session.quarantined.add(original.portfolioId);
    const controller = new AbortController();
    update(session, { controller });
    publish(session, {
      ...empty(),
      phase: recovering ? "checking" : "submitting",
      attempt: original,
    });
    if (operationCurrent()) broadcastMetadataChange(original.portfolioId, "lifecycle");
    let result: Awaited<ReturnType<typeof deletePortfolio>>;
    try {
      result = await mutation.mutateAsync({
        intent: original,
        controller,
        isCurrent: operationCurrent,
      });
      if (!operationCurrent()) return;
      session.recovery!.resolve();
    } catch (error) {
      if (!operationCurrent()) return;
      if (error instanceof PortfolioDeletionError && error.terminal) {
        try {
          session.recovery!.resolve();
        } catch {
          publish(session, {
            ...empty(),
            phase: "unknown",
            attempt: original,
            error: storageError(),
          });
          update(session, { operationScope: null });
          return;
        }
        // Fresh owned-active metadata, not the old cached name, releases quarantine.
        await client.invalidateQueries({
          queryKey: ["portfolioMetadata", owner, original.portfolioId],
          refetchType: "none",
        });
        if (!operationCurrent()) return;
        update(session, { releaseAfterReview: original.portfolioId });
        publish(session, { ...empty(), phase: "terminal_refusal", error });
        await client.invalidateQueries({
          queryKey: ["portfolioMetadata", owner, original.portfolioId],
        });
      } else {
        const safe =
          error instanceof PortfolioDeletionError ? error : new PortfolioDeletionError("unknown");
        publish(session, {
          ...empty(),
          phase: "unknown",
          attempt: original,
          error: safe,
          retryAt: safe.retryAfter === null ? null : Date.now() + safe.retryAfter * 1000,
        });
      }
      if (operationCurrent()) {
        update(session, { operationScope: null, controller: null });
      }
      return;
    }
    if (!operationCurrent()) return;
    const receipt: PortfolioDeletionCompletion = Object.freeze({
      portfolioId: result.portfolioId,
      confirmationName: original.confirmationName,
      isCurrent: () =>
        current() && session.operation === operation && session.state.receipt === receipt,
    });
    update(session, { operationScope: null, controller: null, reviewScope: null });
    publish(session, { ...empty(), phase: "closed", receipt });
    if (ownerCurrent()) broadcastMetadataChange(original.portfolioId, "lifecycle");
    // A failed discovery does not change the known committed closure into "unknown".
    try {
      await client.invalidateQueries({
        queryKey: ["portfolioMetadata", owner, original.portfolioId],
        refetchType: "none",
      });
      if (!receipt.isCurrent()) return receipt;
      await client.invalidateQueries({ queryKey: ["portfolios", owner] });
      if (!receipt.isCurrent()) return receipt;
      await client.invalidateQueries({ queryKey: ["portfolioOverview", owner] });
    } catch {
      if (receipt.isCurrent())
        publish(session, {
          ...session.state,
          error: new Error("Portfolio list unavailable. Try again."),
        });
    }
    if (receipt.isCurrent()) options.onClosed?.(receipt);
    return receipt;
  }
  async function confirmDeletion() {
    if (
      !current() ||
      session.state !== view ||
      view.phase !== "review" ||
      view.reviewRequired ||
      !view.review ||
      session.reviewScope !== scope ||
      !reviewed(view.review) ||
      session.state.attempt ||
      !session.recovery
    )
      return;
    return perform(view.review, false);
  }
  async function checkDeletionResult() {
    if (
      !current() ||
      session.state !== view ||
      view.phase !== "unknown" ||
      !view.attempt ||
      !session.recovery ||
      (view.retryAt !== null && Date.now() < view.retryAt)
    )
      return;
    return perform(view.attempt, true);
  }
  return {
    ready: current() && session.recovery !== null && !session.loading,
    deletion: current() && (view.phase !== "closed" || view.receipt?.isCurrent()) ? view : empty(),
    canConfirm:
      current() &&
      view.phase === "review" &&
      !view.reviewRequired &&
      view.review !== null &&
      reviewed(view.review),
    canCheck:
      current() &&
      view.phase === "unknown" &&
      (view.retryAt === null || session.now >= view.retryAt),
    reviewDeletion,
    cancelReview,
    confirmDeletion,
    checkDeletionResult,
    retryRecoveryStorage: () => (current() ? restore() : Promise.resolve()),
  };
}
