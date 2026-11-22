import type { QueryClient } from "@tanstack/react-query";
import { eventHistorySession } from "@/hooks/useEventHistory";
import type { PortfolioTarget } from "@/hooks/usePortfolioTarget";

const targets = new WeakMap<QueryClient, Map<string, PortfolioTarget>>();

/** Explicit root selected by a unit-test boundary; never infer a production root. */
export function portfolioTargetFixture(
  client: QueryClient,
  portfolioId = "1",
): PortfolioTarget | null {
  const session = eventHistorySession(client);
  if (session.email === null) return null;
  const owner = session.email;
  const key = JSON.stringify([owner, portfolioId, session.epoch]);
  let entries = targets.get(client);
  if (entries === undefined) {
    entries = new Map();
    targets.set(client, entries);
  }
  let target = entries.get(key);
  if (target === undefined) {
    target = Object.freeze({
      owner,
      portfolioId,
      name: "My portfolio",
      epoch: Object.freeze({ owner, portfolioId, session: session.epoch }),
      isCurrent: () => {
        const now = eventHistorySession(client);
        return now.email === owner && now.epoch === session.epoch;
      },
    });
    entries.set(key, target);
  }
  return target;
}
