import { useEffect, useMemo, useReducer } from "react";
import { useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";
import { ApiError } from "@/api/client";
import { fetchPortfolio, type Portfolio, type PortfolioHolding } from "@/api/portfolio";
import { stockInstant, type TimedStocks } from "@/api/stocks";
import type { AuthorityIdentity, TimedStockContext } from "@/api/stockTrades";
import { useMe } from "./useMe";

type TimedPortfolio = Portfolio & {
  transport: { received_at: number; round_trip_ms: number };
  authority_offset_ms?: number;
};
type HoldingGuard = {
  versions: Map<string, number>;
  hashes: Map<string, string>;
  provider: string | null;
  restrictionAt: bigint | null;
  continuity: number;
  sequence: number;
};
type Guard = {
  email: string | null;
  lifecycle: number;
  serial: number;
  holdings: Map<string, HoldingGuard>;
  latest: TimedPortfolio | null;
  clock: { upper: number; at: number } | null;
};
const guards = new WeakMap<QueryClient, Guard>();
const who = (c: QueryClient) => c.getQueryData<{ email: string } | null>(["me"])?.email ?? null;
function guardFor(client: QueryClient) {
  let g = guards.get(client);
  if (g) return g;
  g = {
    email: who(client),
    lifecycle: 0,
    serial: 0,
    holdings: new Map(),
    latest: null,
    clock: null,
  };
  guards.set(client, g);
  const guard = g;
  client.getQueryCache().subscribe(() => {
    const email = who(client);
    if (email === guard.email) return;
    const old = guard.email;
    guard.email = email;
    guard.lifecycle++;
    guard.serial++;
    guard.holdings.clear();
    guard.latest = null;
    guard.clock = null;
    if (old !== null) client.removeQueries({ queryKey: ["portfolio", old] });
  });
  return g;
}
function versions(a: AuthorityIdentity): [string, number][] {
  return [
    ...a.admissions.map((x) => [x.product, x.generation] as [string, number]),
    ["safety", a.safety_epoch],
    ["unit", a.unit_epoch],
    ["calendar", a.calendar_generation],
    ["status", a.status_admission_generation],
    ["continuity", a.continuity_generation],
  ];
}
function holdingGuard(g: Guard, h: PortfolioHolding): HoldingGuard {
  let saved = g.holdings.get(h.coin_id);
  if (!saved) {
    saved = {
      versions: new Map(),
      hashes: new Map(),
      provider: h.provider_asset_id,
      restrictionAt: null,
      continuity: 0,
      sequence: 0,
    };
    g.holdings.set(h.coin_id, saved);
  }
  return saved;
}
const upperAt = (p: TimedPortfolio, now: number) =>
  Number((stockInstant(p.valued_at) + 999_999n) / 1_000_000n) +
  Math.ceil(
    p.transport.round_trip_ms +
      (p.authority_offset_ms ?? 0) +
      Math.max(0, now - p.transport.received_at),
  );
function hide(h: PortfolioHolding): PortfolioHolding {
  if (
    h.stock_mark?.mark_mode === "unavailable" &&
    !h.stock_mark.units_safe &&
    h.average_cost === null
  )
    return h;
  return {
    ...h,
    average_cost: null,
    mid: null,
    current_value: null,
    unrealized_pl: null,
    unrealized_pl_percent: null,
    allocation_percent: null,
    as_of: null,
    age_seconds: null,
    status: "unpriced",
    stock_mark: {
      mark_mode: "unavailable",
      valuation_reason: "action_unavailable",
      source: null,
      feed: null,
      event_at: null,
      collected_at: null,
      historical_admission_until: null,
      retained_until: null,
      valid_until: null,
      authority: null,
      units_safe: false,
    },
  };
}
function externalRestriction(
  client: QueryClient,
  email: string | null,
  h: PortfolioHolding,
): boolean {
  const a = h.stock_mark?.authority;
  const context = client.getQueryData<TimedStockContext>(["stockContext", email, h.symbol]);
  if (
    context &&
    (context.coin_id !== h.coin_id ||
      context.provider_asset_id !== h.provider_asset_id ||
      context.action.state !== "current" ||
      (a &&
        context.authority &&
        (context.authority.unit_epoch !== a.unit_epoch ||
          context.authority.safety_epoch > a.safety_epoch)) ||
      ["permission_unavailable", "units_changed", "frozen", "status_unavailable"].includes(
        context.execution_reason,
      ))
  )
    return true;
  const stocks = client.getQueryData<TimedStocks>(["stocks", email]);
  if (stocks?.admission.state === "unavailable") return true;
  const item = stocks?.items.find((x) => String(x.id) === h.coin_id);
  return (
    item !== undefined &&
    (item.action.state !== "current" ||
      (a !== null && a !== undefined && item.action.epoch > a.safety_epoch))
  );
}
/** Suppress stock-derived values only; never calculate a replacement financial subtotal. */
function project(client: QueryClient, g: Guard, incoming: TimedPortfolio): TimedPortfolio {
  const now = performance.now();
  let p = incoming;
  const ownUpper = upperAt(p, now),
    upper = Math.max(
      ownUpper,
      g.clock === null ? ownUpper : g.clock.upper + Math.max(0, now - g.clock.at),
    );
  const staleSnapshot =
    g.latest !== null && stockInstant(p.valued_at) < stockInstant(g.latest.valued_at);
  const lateRestrictions = new Set(
    staleSnapshot
      ? p.holdings.filter((h) => h.stock_mark?.mark_mode === "unavailable").map((h) => h.coin_id)
      : [],
  );
  if (staleSnapshot) p = g.latest!;
  let changed = false;
  const at = stockInstant(p.valued_at);
  const holdings = p.holdings.map((h) => {
    if (h.asset_class !== "stock") return h;
    const saved = holdingGuard(g, h),
      mark = h.stock_mark!,
      a = mark.authority;
    const backwards =
      a !== null &&
      (versions(a).some(([k, v]) => v < (saved.versions.get(k) ?? 0)) ||
        (a.continuity_generation === saved.continuity && a.status_sequence < saved.sequence));
    const hashChanged =
      a !== null &&
      a.admissions.some(
        (x) =>
          saved.versions.get(x.product) === x.generation &&
          saved.hashes.has(x.product) &&
          saved.hashes.get(x.product) !== x.row_hash,
      );
    const identityChanged = saved.provider !== h.provider_asset_id;
    const expired = mark.valid_until !== null && upper >= Date.parse(mark.valid_until);
    const boundExpired = [
      mark.historical_admission_until,
      mark.retained_until,
      ...(a?.admissions.map((x) => x.valid_until) ?? []),
    ].some((x) => x !== null && upper >= Date.parse(x));
    const restricted =
      lateRestrictions.has(h.coin_id) ||
      backwards ||
      hashChanged ||
      identityChanged ||
      expired ||
      boundExpired ||
      externalRestriction(client, g.email, h) ||
      (saved.restrictionAt !== null &&
        at <= saved.restrictionAt &&
        mark.mark_mode !== "unavailable");
    if (a !== null) {
      for (const [k, v] of versions(a))
        saved.versions.set(k, Math.max(saved.versions.get(k) ?? 0, v));
      for (const admission of a.admissions)
        if (!backwards && !hashChanged) saved.hashes.set(admission.product, admission.row_hash);
      if (a.continuity_generation > saved.continuity) {
        saved.continuity = a.continuity_generation;
        saved.sequence = a.status_sequence;
      } else saved.sequence = Math.max(saved.sequence, a.status_sequence);
    }
    if (restricted || mark.mark_mode === "unavailable") {
      saved.restrictionAt =
        saved.restrictionAt !== null && saved.restrictionAt > at ? saved.restrictionAt : at;
      if (restricted) {
        const redacted = hide(h);
        changed ||= redacted !== h;
        return redacted;
      }
    }
    return h;
  });
  if (changed) {
    g.serial++;
    p = {
      ...p,
      holdings: holdings.map((h) =>
        h.allocation_percent === null ? h : { ...h, allocation_percent: null },
      ),
      valuation_complete: false,
      known_value: null,
      total_value: null,
      total_pl: null,
      total_pl_percent: null,
      cash_allocation_percent: null,
      unvalued_holding_count: holdings.filter((h) => h.mid === null).length,
      class_values: { cash: p.cash, stocks: null, crypto: p.class_values.crypto },
      class_allocation_percent: { cash: null, stocks: null, crypto: null },
    };
  }
  g.clock = { upper, at: now };
  g.latest = p;
  return p;
}
export function usePortfolio() {
  const client = useQueryClient(),
    { data: me } = useMe();
  const email = me?.email ?? null,
    g = guardFor(client);
  const key = useMemo(() => ["portfolio", email] as const, [email]);
  const [, tick] = useReducer((x: number) => x + 1, 0);
  const query = useQuery({
    queryKey: key,
    enabled: email !== null,
    retry: false,
    gcTime: 0,
    queryFn: async ({ signal }) => {
      const lifecycle = g.lifecycle,
        serial = g.serial;
      const owner = client.getQueryCache().find({ queryKey: key, exact: true });
      const started = performance.now();
      try {
        const body = await fetchPortfolio(signal);
        signal.throwIfAborted();
        if (
          who(client) !== email ||
          lifecycle !== g.lifecycle ||
          serial !== g.serial ||
          client.getQueryCache().find({ queryKey: key, exact: true }) !== owner
        )
          throw new Error("Portfolio session changed");
        const received_at = performance.now();
        return project(client, g, {
          ...body,
          transport: { received_at, round_trip_ms: Math.max(0, received_at - started) },
        });
      } catch (error) {
        if (
          who(client) === email &&
          lifecycle === g.lifecycle &&
          error instanceof ApiError &&
          error.status === 401
        )
          client.setQueryData(["me"], null);
        throw error;
      }
    },
    refetchInterval: 30_000,
    staleTime: 10_000,
    refetchOnWindowFocus: true,
  });
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | undefined,
      writing = false;
    const update = () => {
      if (writing) return;
      clearTimeout(timer);
      const cached = client.getQueryData<TimedPortfolio>(key);
      if (cached) {
        const safe = project(client, g, cached);
        if (safe !== cached) {
          writing = true;
          client.getQueryCache().find({ queryKey: key, exact: true })?.setState({ data: safe });
          writing = false;
        }
        const upper = upperAt(safe, performance.now());
        const deadlines = safe.holdings.flatMap((h) =>
          h.stock_mark?.valid_until ? [Date.parse(h.stock_mark.valid_until) - upper] : [],
        );
        if (deadlines.length)
          timer = setTimeout(update, Math.max(1, Math.min(...deadlines, 2_147_483_647)));
      }
      tick();
    };
    const unsubscribe = client.getQueryCache().subscribe((event) => {
      const [prefix, owner] = event.query.queryKey;
      if (
        (event.type === "updated" || event.type === "removed") &&
        owner === email &&
        ["portfolio", "stockContext", "stocks"].includes(String(prefix))
      )
        update();
    });
    const display = setInterval(update, 1000);
    window.addEventListener("focus", update);
    window.addEventListener("visibilitychange", update);
    update();
    return () => {
      clearTimeout(timer);
      clearInterval(display);
      unsubscribe();
      window.removeEventListener("focus", update);
      window.removeEventListener("visibilitychange", update);
    };
  }, [client, email, key, g]);
  const cached = client.getQueryData<TimedPortfolio>(key);
  // Cache notifications/timers commit reductions; render never restores an older observer snapshot.
  return { ...query, data: email !== null && who(client) === email ? cached : undefined };
}
