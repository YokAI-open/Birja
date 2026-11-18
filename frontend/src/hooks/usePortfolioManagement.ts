import { useLayoutEffect, useMemo, useSyncExternalStore } from "react";
import { useMutation, useQueryClient, type QueryClient } from "@tanstack/react-query";
import {
  createPortfolio,
  PortfolioManagementError,
  type PortfolioCreation,
  type PortfolioMetadata,
} from "@/api/portfolioManagement";
import {
  clearCreationRecovery,
  openCreationRecovery,
  type CreationRecovery,
} from "@/lib/portfolioCreationAttempt";
import { useMe } from "./useMe";

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
  owner: string | null;
  serial: number;
  notify: Set<() => void>;
  creation: CreationState;
  recovery: CreationRecovery | null;
  loading: boolean;
  version: number;
  controllers: Set<AbortController>;
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
    owner: who(client),
    serial: 0,
    notify: new Set(),
    creation: empty(),
    recovery: null,
    loading: false,
    version: 0,
    controllers: new Set(),
  };
  sessions.set(client, session);
  client.getQueryCache().subscribe(() => {
    const owner = who(client);
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
  void portfolioId;
  const client = useQueryClient();
  const me = useMe();
  const session = sessionFor(client);
  const owner = me.data?.email ?? null;
  const serial = session.serial;
  const scope = useMemo(
    () => ({ owner, serial, controllers: new Set<AbortController>() }),
    [owner, serial],
  );
  const current = () =>
    activeScopes.has(scope) && owner !== null && who(client) === owner && session.serial === serial;
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
    const ownsSession = () => who(client) === owner && session.serial === serial;
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
  return {
    ready: current() && session.recovery !== null && !session.loading,
    creation: current() ? session.creation : empty(),
    submitCreation,
    retryCreation,
  };
}
