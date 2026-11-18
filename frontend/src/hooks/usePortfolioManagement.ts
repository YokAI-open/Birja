import { useLayoutEffect, useMemo, useSyncExternalStore } from "react";
import { useMutation, useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";
import {
  createPortfolio,
  fetchPortfolioMetadata,
  updatePortfolioMetadata,
  PortfolioManagementError,
  type PortfolioCreation,
  type PortfolioMetadata,
  type PortfolioMetadataPatch,
} from "@/api/portfolioManagement";
import {
  clearCreationRecovery,
  openCreationRecovery,
  type CreationRecovery,
} from "@/lib/portfolioCreationAttempt";
import { useMe } from "./useMe";
import { isPortfolioId } from "@/api/portfolios";
import { broadcastMetadataChange, subscribeMetadataEvents } from "@/lib/portfolioMetadataEvents";

type Receipt = Readonly<{ metadata: PortfolioMetadata; isCurrent: () => boolean }>;
type CreationState = {
  phase: "editing" | "submitting" | "unknown" | "resolved" | "unavailable";
  attempt: PortfolioCreation | null;
  receipt?: Receipt;
  error: Error | null;
};
const empty = (): CreationState => ({ phase: "editing", attempt: null, error: null });
const who = (client: QueryClient) =>
  client.getQueryData<{ email: string } | null>(["me"])?.email ?? null;
type Session = {
  identityKnown: boolean;
  owner: string | null;
  serial: number;
  notify: Set<() => void>;
  creation: CreationState;
  recovery: CreationRecovery | null;
  loading: boolean;
  version: number;
  controllers: Set<AbortController>;
  creationSerial: number;
  creationScope: object | null;
};
const sessions = new WeakMap<QueryClient, Session>();
const activeScopes = new WeakSet<object>();
function update(session: Session, changes: Partial<Session>) {
  Object.assign(session, changes);
}
function sessionFor(client: QueryClient) {
  const existing = sessions.get(client);
  if (existing) return existing;
  const session: Session = {
    identityKnown: client.getQueryData(["me"]) !== undefined,
    owner: who(client),
    serial: 0,
    notify: new Set(),
    creation: empty(),
    recovery: null,
    loading: false,
    version: 0,
    controllers: new Set(),
    creationSerial: 0,
    creationScope: null,
  };
  sessions.set(client, session);
  if (session.identityKnown && session.owner === null) clearCreationRecovery();
  client.getQueryCache().subscribe(() => {
    const known = client.getQueryData(["me"]) !== undefined;
    const owner = who(client);
    if (!session.identityKnown && !known) return;
    const firstIdentity = !session.identityKnown;
    session.identityKnown = known;
    if (firstIdentity && owner !== null) {
      session.owner = owner;
      session.serial++;
      publish(session);
      return;
    }
    if (owner === session.owner) return;
    session.owner = owner;
    session.serial++;
    session.controllers.forEach((c) => c.abort());
    session.controllers.clear();
    session.creation = empty();
    session.recovery = null;
    session.loading = false;
    clearCreationRecovery();
    publish(session);
  });
  return session;
}
function publish(session: Session) {
  session.version++;
  session.notify.forEach((fn) => fn());
}

/** Owner-wide creation lifetime survives route changes; every rendered action is captured. */
export function usePortfolioManagement(portfolioId?: string) {
  const client = useQueryClient();
  const me = useMe();
  const session = sessionFor(client);
  const owner = me.data?.email ?? null;
  const serial = session.serial;
  const scope = useMemo(
    () => ({ owner, serial, portfolioId, controllers: new Set<AbortController>() }),
    [owner, serial, portfolioId],
  );
  const current = () =>
    activeScopes.has(scope) && owner !== null && who(client) === owner && session.serial === serial;
  const metadataKey = ["portfolioMetadata", owner, portfolioId, serial] as const;
  const editorKey = ["portfolioMetadataDraft", owner, portfolioId, serial] as const;
  type Editor = {
    revision: number;
    draft: PortfolioMetadataPatch | null;
    reviewRequired: boolean;
    awaitingFetch: boolean;
    pending: boolean;
    error: Error | null;
  };
  const emptyEditor = (): Editor => ({
    revision: 0,
    draft: null,
    reviewRequired: false,
    awaitingFetch: false,
    pending: false,
    error: null,
  });
  const editorQuery = useQuery({
    queryKey: editorKey,
    queryFn: async () => emptyEditor(),
    enabled: false,
    initialData: emptyEditor,
    gcTime: 0,
  });
  const editor = () => client.getQueryData<Editor>(editorKey) ?? emptyEditor();
  const setEditor = (next: Editor) => client.setQueryData(editorKey, next);
  const metadataQuery = useQuery({
    queryKey: metadataKey,
    enabled: owner !== null && isPortfolioId(portfolioId),
    retry: false,
    gcTime: 0,
    staleTime: 0,
    refetchOnWindowFocus: true,
    queryFn: async ({ signal }) => {
      const query = client.getQueryCache().find({ queryKey: metadataKey, exact: true });
      try {
        const metadata = await fetchPortfolioMetadata(portfolioId!, signal);
        signal.throwIfAborted();
        if (
          who(client) !== owner ||
          session.serial !== serial ||
          client.getQueryCache().find({ queryKey: metadataKey, exact: true }) !== query
        )
          throw new Error("Metadata session changed");
        return metadata;
      } catch (error) {
        if (
          who(client) === owner &&
          session.serial === serial &&
          error instanceof PortfolioManagementError &&
          error.status === 401
        )
          client.setQueryData(["me"], null);
        throw error;
      }
    },
  });
  const metadataMutation = useMutation({
    retry: false,
    gcTime: 0,
    mutationFn: async (patch: PortfolioMetadataPatch) => {
      const controller = new AbortController();
      session.controllers.add(controller);
      scope.controllers.add(controller);
      try {
        return await updatePortfolioMetadata(portfolioId!, patch, controller.signal);
      } finally {
        session.controllers.delete(controller);
        scope.controllers.delete(controller);
      }
    },
  });
  async function refreshMetadata() {
    if (!current() || !isPortfolioId(portfolioId)) return;
    const draft = editor();
    setEditor({
      ...draft,
      revision: draft.revision + 1,
      reviewRequired: draft.draft !== null || draft.reviewRequired,
      awaitingFetch: true,
    });
    const result = await metadataQuery.refetch();
    if (current()) setEditor({ ...editor(), awaitingFetch: result.isError });
  }
  useLayoutEffect(() => {
    if (!owner || !isPortfolioId(portfolioId)) return;
    const changed = (id: string) => {
      if (
        id === portfolioId &&
        activeScopes.has(scope) &&
        who(client) === owner &&
        session.serial === serial
      )
        void refreshMetadata();
    };
    const dispose = subscribeMetadataEvents(changed);
    const focus = () => changed(portfolioId);
    window.addEventListener("focus", focus);
    return () => {
      dispose();
      window.removeEventListener("focus", focus);
    };
    // The listener captures this exact root/session. Query methods read the current cache.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [client, owner, portfolioId, scope, serial, session]);
  useSyncExternalStore(
    (fn) => {
      session.notify.add(fn);
      return () => {
        session.notify.delete(fn);
      };
    },
    () => session.version,
  );
  useLayoutEffect(() => {
    activeScopes.add(scope);
    publish(session);
    if (owner && !session.recovery && !session.loading) {
      update(session, { loading: true });
      void openCreationRecovery(owner, () => who(client) === owner && session.serial === serial)
        .then((recovery) => {
          if (who(client) !== owner || session.serial !== serial) return;
          update(session, {
            recovery,
            creation: recovery.attempt
              ? { phase: "unknown", attempt: recovery.attempt, error: null }
              : empty(),
          });
        })
        .catch(() => {
          if (who(client) === owner && session.serial === serial)
            update(session, {
              creation: {
                ...empty(),
                error: new Error("Creation recovery storage unavailable."),
              },
            });
        })
        .finally(() => {
          if (who(client) === owner && session.serial === serial) {
            update(session, { loading: false });
            publish(session);
          }
        });
    }
    return () => {
      activeScopes.delete(scope);
      scope.controllers.forEach((c) => c.abort());
      if (session.creationScope === scope && session.creation.phase === "submitting") {
        update(session, {
          creationSerial: session.creationSerial + 1,
          creationScope: null,
          creation: { ...session.creation, phase: "unknown" },
        });
        publish(session);
      }
    };
  }, [client, owner, scope, serial, session]);
  const creationMutation = useMutation({
    retry: false,
    gcTime: 0,
    mutationFn: async (attempt: PortfolioCreation) => {
      const controller = new AbortController();
      session.controllers.add(controller);
      scope.controllers.add(controller);
      try {
        return await createPortfolio(attempt, controller.signal);
      } finally {
        session.controllers.delete(controller);
        scope.controllers.delete(controller);
      }
    },
  });
  async function send(attempt: PortfolioCreation) {
    const operation = session.creationSerial + 1;
    update(session, { creationSerial: operation, creationScope: scope });
    const ownsSession = () =>
      who(client) === owner && session.serial === serial && session.creationSerial === operation;
    update(session, { creation: { phase: "submitting", attempt, error: null } });
    publish(session);
    try {
      const metadata = await creationMutation.mutateAsync(attempt);
      if (!ownsSession()) return;
      session.recovery!.resolve();
      update(session, {
        creation: {
          phase: "resolved",
          attempt: null,
          error: null,
          ...(current() ? { receipt: Object.freeze({ metadata, isCurrent: current }) } : {}),
        },
      });
      publish(session);
      await client.invalidateQueries({ queryKey: ["portfolios", owner] });
      if (!ownsSession()) return;
      await client.invalidateQueries({ queryKey: ["portfolioOverview", owner] });
    } catch (error) {
      if (!ownsSession()) return;
      if (error instanceof PortfolioManagementError && error.status === 401) {
        client.setQueryData(["me"], null);
        return;
      }
      const definitive =
        error instanceof PortfolioManagementError &&
        error.outcome === "refused" &&
        error.code !== "creation_key_conflict";
      if (definitive) {
        try {
          session.recovery!.resolve();
        } catch {
          /* Keep original if storage cannot resolve safely. */
        }
      }
      const retained = !definitive || session.recovery!.attempt !== null;
      update(session, {
        creation: {
          phase: retained
            ? "unknown"
            : error instanceof PortfolioManagementError && error.code === "portfolio_unavailable"
              ? "unavailable"
              : "editing",
          attempt: retained ? attempt : null,
          error: error instanceof Error ? error : new Error("Creation result unavailable"),
        },
      });
      publish(session);
    }
  }
  async function submitCreation(input: Omit<PortfolioCreation, "key">) {
    if (
      !current() ||
      !session.recovery ||
      session.creation.attempt ||
      session.creation.phase === "submitting"
    )
      return;
    try {
      const attempt = session.recovery.persist({ ...input, key: crypto.randomUUID() });
      await send(attempt);
    } catch {
      if (current()) {
        update(session, {
          creation: {
            ...session.creation,
            error: new Error("Creation recovery storage unavailable"),
          },
        });
        publish(session);
      }
    }
  }
  async function retryCreation() {
    if (
      !current() ||
      session.creation.phase !== "unknown" ||
      !session.creation.attempt ||
      !session.recovery
    )
      return;
    try {
      await send(session.recovery.persist(session.creation.attempt));
    } catch (error) {
      if (current()) {
        update(session, {
          creation: {
            ...session.creation,
            error:
              error instanceof Error ? error : new Error("Creation recovery storage unavailable"),
          },
        });
        publish(session);
      }
    }
  }
  function editMetadata(patch: PortfolioMetadataPatch) {
    if (!current() || !metadataQuery.data || metadataQuery.isError || editor().pending) return;
    setEditor({ ...editor(), draft: Object.freeze({ ...editor().draft, ...patch }) });
  }
  function reviewMetadata() {
    if (
      current() &&
      metadataQuery.data &&
      !metadataQuery.isError &&
      !metadataQuery.isFetching &&
      !editor().awaitingFetch
    )
      setEditor({ ...editor(), reviewRequired: false });
  }
  function discardMetadata() {
    if (current() && !editor().pending) setEditor(emptyEditor());
  }
  async function saveMetadata() {
    const state = editor();
    if (
      !current() ||
      !isPortfolioId(portfolioId) ||
      !metadataQuery.data ||
      metadataQuery.isError ||
      !state.draft ||
      state.reviewRequired ||
      state.awaitingFetch ||
      state.pending
    )
      return;
    setEditor({ ...state, pending: true, error: null });
    try {
      const metadata = await metadataMutation.mutateAsync(state.draft);
      if (!current()) return;
      if (editor().revision !== state.revision) {
        setEditor({ ...editor(), pending: false, reviewRequired: true });
        await refreshMetadata();
        return;
      }
      client.setQueryData(metadataKey, metadata);
      setEditor(emptyEditor());
      broadcastMetadataChange(metadata.id);
      await Promise.all([
        client.invalidateQueries({ queryKey: ["portfolios", owner] }),
        client.invalidateQueries({ queryKey: ["portfolioOverview", owner] }),
        ...["portfolio", "history", "eventHistory"].map((prefix) =>
          client.invalidateQueries({ queryKey: [prefix, owner, portfolioId] }),
        ),
      ]);
    } catch (error) {
      if (!current()) return;
      if (error instanceof PortfolioManagementError && error.status === 401) {
        client.setQueryData(["me"], null);
        return;
      }
      const ambiguous = !(error instanceof PortfolioManagementError) || error.outcome === "unknown";
      const latest = editor();
      setEditor({
        ...latest,
        pending: false,
        reviewRequired: latest.reviewRequired || latest.revision !== state.revision || ambiguous,
        error: error instanceof Error ? error : new Error("Metadata result unavailable"),
      });
      if (ambiguous) await refreshMetadata();
    }
  }
  return {
    ready: current() && session.recovery !== null && !session.loading,
    creation: current() ? session.creation : empty(),
    submitCreation,
    retryCreation,
    metadata: current() && !metadataQuery.isError ? metadataQuery.data : undefined,
    metadataError: current() ? (metadataQuery.error ?? editorQuery.data.error) : null,
    metadataPending: current() && (metadataQuery.isFetching || editorQuery.data.pending),
    draft: current() ? editorQuery.data.draft : null,
    reviewRequired: current() && editorQuery.data.reviewRequired,
    editMetadata,
    reviewMetadata,
    discardMetadata,
    saveMetadata,
    refreshMetadata,
  };
}
