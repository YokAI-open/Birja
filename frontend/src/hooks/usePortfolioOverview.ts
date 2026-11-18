import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useReducer,
  useSyncExternalStore,
} from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import { fetchPortfolioOverview, type PortfolioOverview } from "@/api/portfolioOverview";
import { useMe } from "./useMe";
import { eventHistorySession } from "./useEventHistory";
import { portfolioGuardFor, projectPortfolio, type TimedPortfolio } from "./usePortfolio";
import { subscribeMetadataEvents } from "@/lib/portfolioMetadataEvents";
import { stockInstant } from "@/api/stocks";

type TimedOverview = readonly (PortfolioOverview & Pick<TimedPortfolio, "transport">)[];
const activeScopes = new WeakSet<object>();

/** One owner-wide statement request; every book retains its own proof and clock. */
export function usePortfolioOverview() {
  const client = useQueryClient();
  const me = useMe();
  const subscribe = useCallback(
    (notify: () => void) => client.getQueryCache().subscribe(notify),
    [client],
  );
  const epoch = useSyncExternalStore(subscribe, () => eventHistorySession(client).epoch);
  const owner = me.data?.email ?? null;
  const key = useMemo(() => ["portfolioOverview", owner, epoch] as const, [owner, epoch]);
  const scope = useMemo(() => ({ owner, epoch }), [owner, epoch]);
  const current = useCallback(() => {
    const session = eventHistorySession(client);
    return (
      activeScopes.has(scope) &&
      owner !== null &&
      session.email === owner &&
      session.epoch === epoch
    );
  }, [client, scope, owner, epoch]);
  useLayoutEffect(() => {
    activeScopes.add(scope);
    return () => {
      activeScopes.delete(scope);
    };
  }, [scope]);
  const project = useCallback(
    (rows: TimedOverview): TimedOverview => {
      let changed = false;
      const safe = rows.map((row) => {
        const { id, description, ...statement } = row;
        const detail: TimedPortfolio = { ...statement, portfolio_id: id };
        const guarded = projectPortfolio(
          client,
          portfolioGuardFor(client, owner, id, epoch, "overview"),
          detail,
        );
        // Preserve authenticated current metadata even if an older financial snapshot is refused.
        if (guarded === detail) return row;
        changed = true;
        const { portfolio_id: _id, ...values } = guarded;
        void _id;
        return { ...values, id, name: row.name, description };
      });
      return changed ? safe : rows;
    },
    [client, owner, epoch],
  );
  const query = useQuery({
    queryKey: key,
    enabled: current(),
    retry: false,
    gcTime: 0,
    staleTime: 10_000,
    refetchInterval: 30_000,
    refetchOnWindowFocus: true,
    queryFn: async ({ signal }) => {
      if (!current()) throw new Error("Overview session changed");
      const captured = client.getQueryCache().find({ queryKey: key, exact: true });
      const started = performance.now();
      try {
        const rows = await fetchPortfolioOverview(signal);
        signal.throwIfAborted();
        if (!current() || client.getQueryCache().find({ queryKey: key, exact: true }) !== captured)
          throw new Error("Overview session changed");
        // Membership and the common statement time belong to one response.
        // Never splice a retained book into an older comparison response.
        if (
          rows.some((row) => {
            const latest = portfolioGuardFor(client, owner, row.id, epoch, "overview").latest;
            return latest !== null && stockInstant(row.valued_at) < stockInstant(latest.valued_at);
          })
        )
          throw new Error("Overview snapshot moved backwards");
        const received_at = performance.now();
        const transport = { received_at, round_trip_ms: Math.max(0, received_at - started) };
        return project(rows.map((row) => ({ ...row, transport })));
      } catch (error) {
        if (current() && error instanceof ApiError && error.status === 401)
          client.setQueryData(["me"], null);
        throw error;
      }
    },
  });
  const [, tick] = useReducer((value: number) => value + 1, 0);
  useLayoutEffect(() => {
    let writing = false;
    let deadline: ReturnType<typeof setTimeout> | undefined;
    const update = () => {
      if (writing || !current()) return;
      clearTimeout(deadline);
      const cached = client.getQueryData<TimedOverview>(key);
      if (cached) {
        const safe = project(cached);
        if (safe !== cached) {
          writing = true;
          client.getQueryCache().find({ queryKey: key, exact: true })?.setState({ data: safe });
          writing = false;
        }
        const bounds = safe.flatMap((row) => {
          const clock = portfolioGuardFor(client, owner, row.id, epoch, "overview").clock;
          if (!clock) return [];
          return row.holdings.flatMap((holding) => {
            const mark = holding.stock_mark;
            return mark
              ? [
                  mark.valid_until,
                  mark.historical_admission_until,
                  mark.retained_until,
                  ...(mark.authority?.admissions.map((a) => a.valid_until) ?? []),
                ]
                  .filter((value): value is string => value !== null)
                  .map((value) => Date.parse(value) - clock.upper)
                  .filter((value) => value > 0)
              : [];
          });
        });
        if (bounds.length)
          deadline = setTimeout(update, Math.max(1, Math.min(...bounds, 2_147_483_647)));
      }
      tick();
    };
    const dispose = client.getQueryCache().subscribe((event) => {
      const [prefix, email, , session] = event.query.queryKey;
      if (
        (event.type === "updated" || event.type === "removed") &&
        email === owner &&
        (prefix === "portfolioOverview" ||
          prefix === "stocks" ||
          (["stockContext", "portfolio"].includes(String(prefix)) && session === epoch))
      )
        update();
    });
    const timer = setInterval(update, 1000);
    window.addEventListener("focus", update);
    window.addEventListener("visibilitychange", update);
    update();
    return () => {
      dispose();
      clearInterval(timer);
      clearTimeout(deadline);
      window.removeEventListener("focus", update);
      window.removeEventListener("visibilitychange", update);
    };
  }, [client, key, owner, epoch, current, project]);
  useEffect(
    () =>
      subscribeMetadataEvents(() => {
        if (!current()) return;
        void client.invalidateQueries({ queryKey: ["portfolios", owner], exact: true });
        void client.invalidateQueries({ queryKey: key, exact: true });
      }),
    [client, owner, key, current],
  );
  const cached = client.getQueryData<TimedOverview>(key);
  return {
    ...query,
    // Recheck before render as well as on cache notifications, focus and time.
    data: current() && cached ? project(cached) : undefined,
    refetch: (options?: Parameters<typeof query.refetch>[0]) =>
      current() ? query.refetch(options) : Promise.reject(new Error("Overview session changed")),
  };
}
