import { useCallback, useLayoutEffect, useMemo, useSyncExternalStore } from "react";
import { useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import { fetchPortfolios, isPortfolioId, type PortfolioSummary } from "@/api/portfolios";
import { useMe } from "./useMe";
import { subscribeMetadataEvents } from "@/lib/portfolioMetadataEvents";
import {
  isPortfolioDeletionQuarantined,
  portfolioDeletionAuthorityReady,
  portfolioDeletionRevision,
  subscribePortfolioDeletion,
  usePortfolioDeletion,
} from "./usePortfolioDeletion";

type Guard = { owner: string | null; session: number; serial: number };
const guards = new WeakMap<QueryClient, Guard>();
const activeScopes = new WeakSet<object>();
const who = (client: QueryClient) =>
  client.getQueryData<{ email: string } | null>(["me"])?.email ?? null;

function guardFor(client: QueryClient): Guard {
  const existing = guards.get(client);
  if (existing) return existing;
  const guard = { owner: who(client), session: 0, serial: 0 };
  guards.set(client, guard);
  client.getQueryCache().subscribe(() => {
    const owner = who(client);
    if (owner === guard.owner) return;
    const previous = guard.owner;
    guard.owner = owner;
    guard.session++;
    guard.serial++;
    if (previous !== null) client.removeQueries({ queryKey: ["portfolios", previous] });
  });
  return guard;
}

export type PortfolioTargetEpoch = Readonly<{
  owner: string;
  portfolioId: string;
  session: number;
}>;
export type PortfolioTarget = Readonly<{
  owner: string;
  portfolioId: string;
  name: string;
  epoch: PortfolioTargetEpoch;
  /** Captured previews/callbacks must check this before publishing or submitting. */
  isCurrent: () => boolean;
  /** Original recovery only: stable identity, never preview/receipt authority. */
  isOriginalCurrent?: () => boolean;
}>;
export type PortfolioTargetStatus =
  | "signed_out"
  | "loading"
  | "required"
  | "empty"
  | "ambiguous"
  | "unavailable"
  | "error"
  | "redirect"
  | "ready";

/**
 * Explicit targets never fall back. Legacy discovery is an opt-in navigation
 * state, not financial authority; even its sole result must be opened first.
 */
export function usePortfolioTarget(
  routePortfolioId?: string,
  { legacyEntry = false }: { legacyEntry?: boolean } = {},
) {
  const client = useQueryClient();
  const identity = useMe();
  // This lease remains mounted when the financial Outlet is removed.
  const recovery = usePortfolioDeletion();
  const deletionRevision = useSyncExternalStore(
    useCallback((notify) => subscribePortfolioDeletion(client, notify), [client]),
    useCallback(() => portfolioDeletionRevision(client), [client]),
  );
  const owner = identity.data?.email ?? null;
  const guard = guardFor(client);
  const session = guard.session;
  const explicit = routePortfolioId !== undefined;
  const valid = explicit ? isPortfolioId(routePortfolioId) : legacyEntry;
  const key = useMemo(() => ["portfolios", owner] as const, [owner]);
  const scope = useMemo(
    () =>
      Object.freeze({
        owner,
        routePortfolioId,
        legacyEntry,
        session,
        listeners: new Set<() => void>(),
        authority: { revision: 0 },
      }),
    [owner, routePortfolioId, legacyEntry, session],
  );
  useLayoutEffect(() => {
    activeScopes.add(scope);
    scope.listeners.forEach((notify) => notify());
    return () => {
      activeScopes.delete(scope);
      scope.listeners.forEach((notify) => notify());
    };
  }, [scope]);
  // Cached metadata may resolve during the route-change render. Financial
  // children must mount only after this scope's committed activation, or their
  // initial query is disabled with no later notification to enable it.
  const subscribe = useCallback(
    (notify: () => void) => {
      scope.listeners.add(notify);
      return () => {
        scope.listeners.delete(notify);
      };
    },
    [scope],
  );
  const activated = useSyncExternalStore(
    subscribe,
    useCallback(() => activeScopes.has(scope), [scope]),
  );
  const current = useCallback(
    () => activeScopes.has(scope) && who(client) === owner && session === guardFor(client).session,
    [scope, client, owner, session],
  );

  const metadata = useQuery({
    queryKey: key,
    enabled: owner !== null && valid,
    retry: false,
    staleTime: 10_000,
    gcTime: 0,
    refetchOnWindowFocus: true,
    queryFn: async ({ signal }) => {
      const capturedSession = guard.session;
      const serial = ++guard.serial;
      const query = client.getQueryCache().find({ queryKey: key, exact: true });
      try {
        const body = await fetchPortfolios(signal);
        signal.throwIfAborted();
        if (
          who(client) !== owner ||
          capturedSession !== guard.session ||
          serial !== guard.serial ||
          client.getQueryCache().find({ queryKey: key, exact: true }) !== query
        )
          throw new Error("Portfolio metadata session changed");
        return body;
      } catch (error) {
        if (
          who(client) === owner &&
          capturedSession === guard.session &&
          error instanceof ApiError &&
          error.status === 401
        )
          client.setQueryData(["me"], null);
        throw error;
      }
    },
  });

  useLayoutEffect(
    () =>
      subscribeMetadataEvents((id) => {
        if (!current() || owner === null || (explicit && id !== routePortfolioId)) return;
        // An event supplies no labels or ownership evidence. Revoke old handles
        // synchronously and renew only from the authenticated discovery endpoint.
        scope.authority.revision++;
        guard.serial++;
        void client.invalidateQueries({ queryKey: key, exact: true });
      }),
    [client, owner, explicit, routePortfolioId, key, scope, current, guard],
  );

  const selected =
    valid && explicit ? metadata.data?.find((p) => p.id === routePortfolioId) : undefined;
  const target = useMemo<PortfolioTarget | null>(() => {
    if (
      !owner ||
      !selected ||
      !portfolioDeletionAuthorityReady(client, owner) ||
      isPortfolioDeletionQuarantined(client, owner, selected.id) ||
      metadata.isError ||
      (metadata.isFetching && client.getQueryState(key)?.isInvalidated)
    )
      return null;
    const epoch = Object.freeze({ owner, portfolioId: selected.id, session });
    const revision = scope.authority.revision;
    const originalCurrent = () => {
      const query = client.getQueryCache().find({ queryKey: key, exact: true });
      const values = query?.state.data as readonly PortfolioSummary[] | undefined;
      return (
        activeScopes.has(scope) &&
        who(client) === owner &&
        guard.session === session &&
        portfolioDeletionAuthorityReady(client, owner) &&
        !isPortfolioDeletionQuarantined(client, owner, selected.id) &&
        query?.state.status === "success" &&
        !query.state.isInvalidated &&
        values?.some((p) => p.id === selected.id) === true
      );
    };
    return Object.freeze({
      owner,
      portfolioId: selected.id,
      name: selected.name,
      epoch,
      isOriginalCurrent: originalCurrent,
      isCurrent: () => {
        const query = client.getQueryCache().find({ queryKey: key, exact: true });
        const values = query?.state.data as readonly PortfolioSummary[] | undefined;
        return (
          originalCurrent() &&
          scope.authority.revision === revision &&
          values?.find((p) => p.id === selected.id) === selected
        );
      },
    });
  }, [
    owner,
    selected,
    metadata.isError,
    metadata.isFetching,
    session,
    client,
    key,
    scope,
    guard,
    deletionRevision,
  ]);

  const portfolios =
    owner && portfolioDeletionAuthorityReady(client, owner)
      ? metadata.data?.filter((row) => !isPortfolioDeletionQuarantined(client, owner, row.id))
      : undefined;

  let status: PortfolioTargetStatus;
  let redirectPortfolioId: string | null = null;
  if (identity.isPending) status = "loading";
  else if (identity.isError) status = "error";
  else if (owner === null || who(client) !== owner) status = "signed_out";
  else if (!valid) status = "required";
  else if (!recovery.ready) status = recovery.deletion.error ? "error" : "loading";
  else if (explicit && isPortfolioDeletionQuarantined(client, owner, routePortfolioId!))
    status = "unavailable";
  else if (metadata.isError) status = "error";
  else if (
    metadata.isPending ||
    !activated ||
    (metadata.isFetching && client.getQueryState(key)?.isInvalidated)
  )
    status = "loading";
  else if (explicit) status = target ? "ready" : "unavailable";
  else if (portfolios?.length === 0) status = "empty";
  else if (portfolios?.length === 1) {
    status = "redirect";
    redirectPortfolioId = portfolios[0].id;
  } else status = "ambiguous";

  return {
    status,
    target: status === "ready" ? target : null,
    redirectPortfolioId,
    portfolios,
    error: identity.error ?? metadata.error ?? recovery.deletion.error,
    isFetching: metadata.isFetching,
    /** A stale rendered recovery action cannot fetch as a new owner/target. */
    refetch: () =>
      valid && owner !== null && current()
        ? !recovery.ready
          ? recovery.retryRecoveryStorage()
          : metadata.refetch()
        : Promise.reject(new Error("Portfolio target changed")),
  };
}
