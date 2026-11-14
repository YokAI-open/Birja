import { useEffect, useMemo, useReducer, useRef } from "react";
import { useMutation, useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";
import { stockInstant } from "@/api/stocks";
import {
  executeStockTrade,
  fetchStockContext,
  fetchStockQuote,
  isStockOrder,
  StockTradeError,
  stockFixed,
  type StockAttempt,
  type StockFill,
  type StockPriceChanged,
  type StockRefusal,
  type TimedStockContext,
  type TimedStockQuote,
  type AuthorityIdentity,
} from "@/api/stockTrades";
import { useMe } from "./useMe";

type Phase = "draft" | "loading_preview" | "preview" | "submitting" | "unknown" | "filled";
type Attempt = { body: Readonly<StockAttempt>; coin_id: string; provider_asset_id: string };
export type StockTradeState = {
  phase: Phase;
  symbol: string;
  side: "buy" | "sell";
  quantity: string;
  quote: TimedStockQuote | null;
  attempt: Attempt | null;
  fill: StockFill | null;
  replacement: StockPriceChanged | null;
  error: StockRefusal | "unknown" | null;
  interrupted: boolean;
};
const empty = (symbol: string): StockTradeState => ({
  phase: "draft",
  symbol,
  side: "buy",
  quantity: "",
  quote: null,
  attempt: null,
  fill: null,
  replacement: null,
  error: null,
  interrupted: false,
});
const who = (c: QueryClient) => c.getQueryData<{ email: string } | null>(["me"])?.email ?? null;
const floor = (v: string) => Date.parse(v);
const ceil = (v: string) => floor(v) + (/\.\d{3}\d*[1-9]\d*(?:Z|\+00:00)$/.test(v) ? 1 : 0);
export function stockUpper(
  data: TimedStockContext | TimedStockQuote,
  now = performance.now(),
): number {
  const offset = "authority_offset_ms" in data ? (data.authority_offset_ms ?? 0) : 0;
  return (
    ceil(data.observed_at) +
    Math.ceil(data.transport.round_trip_ms + offset + Math.max(0, now - data.transport.received_at))
  );
}
function redact(data: TimedStockContext, reason: StockRefusal): TimedStockContext {
  if (
    !data.execution_enabled &&
    data.quote === null &&
    data.buy_max_quantity === "0" &&
    data.valid_until === null &&
    data.execution_reason === reason
  )
    return data;
  return {
    ...data,
    quote: null,
    buy_max_quantity: "0",
    execution_enabled: false,
    execution_reason: reason,
    valid_until: null,
  };
}
/** Browser projection only removes authority; an opening never enables a draft. */
export function projectStockContext(
  data: TimedStockContext,
  now = performance.now(),
): TimedStockContext {
  const upper = stockUpper(data, now);
  let result = data;
  if (data.status.valid_until !== null && upper >= floor(data.status.valid_until))
    result = {
      ...result,
      status: {
        state: "unknown",
        event_at: null,
        observed_at: null,
        valid_until: null,
        bootstrap_verified: false,
        continuity_current: false,
      },
    };
  if (data.action.valid_until !== null && upper >= floor(data.action.valid_until))
    result = {
      ...result,
      action: {
        state: "unknown",
        reason: "monitor_unavailable",
        valid_until: null,
        next_blocking_at: null,
      },
    };
  if (!data.execution_enabled)
    return redact(
      result,
      data.execution_reason === "available" ? "quote_unavailable" : data.execution_reason,
    );
  let reason: StockRefusal | null = null;
  if (
    data.authority === null ||
    data.authority.admissions.some((a) => upper >= floor(a.valid_until))
  )
    reason = "permission_unavailable";
  else if (
    result.action.state !== "current" ||
    (result.action.next_blocking_at !== null && upper >= floor(result.action.next_blocking_at))
  )
    reason = "action_unavailable";
  else if (
    result.status.state !== "normal" ||
    !result.status.bootstrap_verified ||
    !result.status.continuity_current
  )
    reason =
      result.status.state === "halted"
        ? "halted"
        : result.status.state === "frozen"
          ? "frozen"
          : "status_unavailable";
  else if (data.session.valid_until === null || upper >= floor(data.session.valid_until))
    reason = "session_unavailable";
  else if (
    data.session.state !== "open" ||
    data.session.closes_at === null ||
    upper >= floor(data.session.closes_at)
  )
    reason = "market_closed";
  else if (data.quote === null) reason = "quote_unavailable";
  else if (upper >= floor(data.quote.event_at) + 120_000) reason = "quote_stale";
  else if (data.valid_until === null || upper >= floor(data.valid_until))
    reason = "quote_unavailable";
  return reason === null ? result : redact(result, reason);
}
const authorities = (a: AuthorityIdentity | null) =>
  a === null
    ? []
    : [
        ...a.admissions.map((x) => [x.product, x.generation] as const),
        ["safety", a.safety_epoch] as const,
        ["unit", a.unit_epoch] as const,
        ["status-admission", a.status_admission_generation] as const,
        ["calendar", a.calendar_generation] as const,
        ["continuity", a.continuity_generation] as const,
      ];
type ContextGuard = {
  latest: TimedStockContext | null;
  versions: Map<string, number>;
  continuity: number;
  sequence: number;
  serial: number;
  restrictionAt: bigint | null;
  clock: { upper: number; at: number } | null;
};
type AuthGuard = { email: string | null; version: number; contexts: Map<string, ContextGuard> };
const guards = new WeakMap<QueryClient, AuthGuard>();
function authGuard(client: QueryClient): AuthGuard {
  const existing = guards.get(client);
  if (existing) return existing;
  const g: AuthGuard = { email: who(client), version: 0, contexts: new Map() };
  guards.set(client, g);
  client.getQueryCache().subscribe(() => {
    const email = who(client);
    if (email === g.email) return;
    const old = g.email;
    g.email = email;
    g.version++;
    g.contexts.clear();
    if (old !== null) {
      for (const prefix of ["stockTradeState", "stockContext"])
        client.removeQueries({ queryKey: [prefix, old] });
      client.getMutationCache().clear();
    }
  });
  return g;
}
function contextGuard(g: AuthGuard, symbol: string): ContextGuard {
  let c = g.contexts.get(symbol);
  if (!c) {
    c = {
      latest: null,
      versions: new Map(),
      continuity: 0,
      sequence: 0,
      serial: 0,
      restrictionAt: null,
      clock: null,
    };
    g.contexts.set(symbol, c);
  }
  return c;
}
function acceptContext(g: ContextGuard, incoming: TimedStockContext): TimedStockContext {
  const now = performance.now(),
    previous = g.latest;
  const backwards =
    authorities(incoming.authority).some(([k, v]) => v < (g.versions.get(k) ?? 0)) ||
    (incoming.authority !== null &&
      incoming.authority.continuity_generation === g.continuity &&
      incoming.authority.status_sequence < g.sequence);
  const oldTime =
    previous !== null && stockInstant(incoming.observed_at) < stockInstant(previous.observed_at);
  const identity =
    previous !== null &&
    (incoming.coin_id !== previous.coin_id ||
      incoming.provider_asset_id !== previous.provider_asset_id);
  if (
    incoming.execution_enabled &&
    (backwards ||
      oldTime ||
      (previous !== null &&
        !previous.execution_enabled &&
        stockInstant(incoming.observed_at) <= stockInstant(previous.observed_at)))
  ) {
    if (previous !== null) return projectStockContext(previous, now);
    return redact(incoming, "permission_unavailable");
  }
  if (identity && previous !== null) {
    // A changed mapping is a restriction until fresh, newer safety evidence
    // establishes the new identity. Never retain an old executable mapping.
    const newer =
      !backwards &&
      !oldTime &&
      incoming.authority !== null &&
      incoming.authority.safety_epoch > (previous.authority?.safety_epoch ?? 0) &&
      stockInstant(incoming.observed_at) > stockInstant(previous.observed_at);
    if (!newer) incoming = redact(incoming, "action_unavailable");
  }
  let data =
    !incoming.execution_enabled && (oldTime || backwards) && previous !== null
      ? redact(
          previous,
          incoming.execution_reason === "available"
            ? "quote_unavailable"
            : incoming.execution_reason,
        )
      : incoming;
  const upper = stockUpper(data, now);
  const priorUpper = g.clock === null ? upper : g.clock.upper + Math.max(0, now - g.clock.at);
  if (priorUpper > upper)
    data = {
      ...data,
      authority_offset_ms: (data.authority_offset_ms ?? 0) + Math.ceil(priorUpper - upper),
    };
  data = projectStockContext(data, now);
  for (const [k, v] of authorities(incoming.authority))
    g.versions.set(k, Math.max(g.versions.get(k) ?? 0, v));
  if (incoming.authority !== null && incoming.authority.continuity_generation >= g.continuity) {
    g.sequence =
      incoming.authority.continuity_generation > g.continuity
        ? incoming.authority.status_sequence
        : Math.max(g.sequence, incoming.authority.status_sequence);
    g.continuity = incoming.authority.continuity_generation;
  }
  if (!data.execution_enabled) {
    if (previous !== null && previous.execution_enabled) g.serial++;
    const at = stockInstant(data.observed_at);
    g.restrictionAt = g.restrictionAt !== null && g.restrictionAt > at ? g.restrictionAt : at;
  }
  g.clock = { upper: Math.max(upper, priorUpper), at: now };
  g.latest = data;
  return data;
}
function compatible(q: TimedStockQuote, c: TimedStockContext): boolean {
  return (
    c.execution_enabled &&
    c.authority !== null &&
    q.coin_id === c.coin_id &&
    q.provider_asset_id === c.provider_asset_id &&
    q.authority.safety_epoch === c.authority.safety_epoch &&
    q.authority.unit_epoch === c.authority.unit_epoch &&
    q.authority.continuity_generation === c.authority.continuity_generation &&
    q.authority.admissions.every((a) =>
      c.authority!.admissions.some(
        (b) =>
          a.product === b.product && a.generation === b.generation && a.row_hash === b.row_hash,
      ),
    ) &&
    (stockInstant(c.observed_at) <= stockInstant(q.observed_at) ||
      (stockFixed(c.cash) === stockFixed(q.cash_before) &&
        stockFixed(c.held_quantity) === stockFixed(q.held_before)))
  );
}
function quoteCurrent(q: TimedStockQuote, c: TimedStockContext | undefined): boolean {
  return (
    c !== undefined &&
    compatible(q, c) &&
    Math.max(stockUpper(q), stockUpper(c)) < floor(q.valid_until)
  );
}

export function useStockTrade(routeSymbol: string) {
  const client = useQueryClient();
  const { data: me } = useMe();
  const auth = authGuard(client),
    email = me?.email ?? null;
  const stateKey = useMemo(() => ["stockTradeState", email] as const, [email]);
  const stateQuery = useQuery({
    queryKey: stateKey,
    queryFn: async () => empty(routeSymbol),
    enabled: false,
    initialData: () => empty(routeSymbol),
    gcTime: Infinity,
  });
  const state =
    email === null
      ? empty(routeSymbol)
      : (client.getQueryData<StockTradeState>(stateKey) ?? stateQuery.data);
  const symbol = state.symbol;
  const key = useMemo(() => ["stockContext", email, symbol] as const, [email, symbol]);
  const quoteAbort = useRef<AbortController | null>(null),
    quoteSerial = useRef(0);
  const [, tick] = useReducer((n: number) => n + 1, 0);
  const contextQuery = useQuery({
    queryKey: key,
    enabled: email !== null,
    retry: false,
    gcTime: 0,
    staleTime: 5_000,
    refetchInterval: 15_000,
    refetchOnWindowFocus: true,
    queryFn: async ({ signal }) => {
      const version = auth.version,
        cg = contextGuard(auth, symbol),
        serial = cg.serial;
      const owner = client.getQueryCache().find({ queryKey: key, exact: true });
      const initial = client.getQueryData<TimedStockContext>(key);
      const superseded = new AbortController();
      const requestSignal = AbortSignal.any([signal, superseded.signal]);
      const unsubscribe = client.getQueryCache().subscribe((event) => {
        const current = client.getQueryData<TimedStockContext>(key);
        if (
          who(client) !== email ||
          auth.version !== version ||
          cg.serial !== serial ||
          (event.query === owner && event.type === "removed") ||
          (current !== undefined && current !== initial && !current.execution_enabled)
        )
          superseded.abort();
      });
      try {
        const response = await fetchStockContext(symbol, requestSignal);
        requestSignal.throwIfAborted();
        if (
          auth.version !== version ||
          who(client) !== email ||
          cg.serial !== serial ||
          client.getQueryCache().find({ queryKey: key, exact: true }) !== owner
        )
          throw new StockTradeError("unknown");
        return acceptContext(cg, response);
      } catch (error) {
        if (auth.version === version && who(client) === email) {
          if (error instanceof StockTradeError && error.status === 401)
            client.setQueryData(["me"], null);
          else if (error instanceof StockTradeError && error.kind === "refused") {
            const current = client.getQueryData<TimedStockContext>(key);
            if (current)
              client.setQueryData(
                key,
                acceptContext(cg, redact(current, error.code ?? "quote_unavailable")),
              );
          }
        }
        throw error;
      } finally {
        unsubscribe();
      }
    },
  });
  const raw = client.getQueryData<TimedStockContext>(key);
  const context = email !== null && raw ? projectStockContext(raw) : undefined;
  const quoteMutation = useMutation({
    mutationFn: ({
      order,
      signal,
    }: {
      order: { symbol: string; side: "buy" | "sell"; quantity: string };
      signal: AbortSignal;
    }) => fetchStockQuote(order, signal),
    retry: false,
    gcTime: 0,
  });
  const tradeMutation = useMutation({
    mutationFn: ({ body, signal }: { body: StockAttempt; signal: AbortSignal }) =>
      executeStockTrade(body, signal),
    retry: false,
    gcTime: 0,
  });
  const setState = (update: (s: StockTradeState) => StockTradeState) => {
    if (email !== null && who(client) === email)
      client.setQueryData<StockTradeState>(stateKey, (s) => update(s ?? empty(routeSymbol)));
  };
  const currentContext = () => {
    const data = client.getQueryData<TimedStockContext>(key);
    return email !== null && data ? projectStockContext(data) : undefined;
  };
  const currentState = () => client.getQueryData<StockTradeState>(stateKey) ?? empty(routeSymbol);
  const locked = (s: StockTradeState) =>
    s.phase === "submitting" || s.phase === "unknown" || s.phase === "filled";
  const edit = (changes: Partial<Pick<StockTradeState, "side" | "quantity">>) => {
    if (locked(currentState())) return;
    quoteSerial.current++;
    quoteAbort.current?.abort();
    setState((s) => ({
      ...s,
      ...changes,
      phase: "draft",
      quote: null,
      replacement: null,
      error: null,
      interrupted: false,
    }));
  };
  useEffect(() => {
    const s = client.getQueryData<StockTradeState>(["stockTradeState", email]);
    if (s && s.symbol !== routeSymbol && s.phase !== "submitting" && s.phase !== "unknown")
      client.setQueryData(["stockTradeState", email], empty(routeSymbol));
    // Route changes do not abandon an unresolved attempt. A later receipt stays
    // visible until explicit Trade again, even if another route was requested.
  }, [client, email, routeSymbol]);
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | undefined;
    let writing = false;
    const update = () => {
      if (writing) return;
      clearTimeout(timer);
      const cached = client.getQueryData<TimedStockContext>(key);
      const cg = contextGuard(auth, symbol);
      const safe = cached ? acceptContext(cg, cached) : undefined;
      if (cached && safe !== cached) {
        writing = true;
        client.setQueryData(key, safe);
        writing = false;
      }
      const s = client.getQueryData<StockTradeState>(stateKey);
      if (s?.phase === "preview" && s.quote !== null && !quoteCurrent(s.quote, safe)) {
        writing = true;
        client.setQueryData(stateKey, {
          ...s,
          phase: "draft",
          quote: null,
          replacement: null,
          interrupted: true,
          error: safe?.execution_enabled ? "quote_stale" : null,
        });
        writing = false;
      }
      const bounds: number[] = [];
      if (safe?.valid_until) bounds.push(floor(safe.valid_until) - stockUpper(safe));
      if (safe?.status.valid_until) bounds.push(floor(safe.status.valid_until) - stockUpper(safe));
      if (safe?.action.valid_until) bounds.push(floor(safe.action.valid_until) - stockUpper(safe));
      if (s?.phase === "preview" && s.quote)
        bounds.push(floor(s.quote.valid_until) - stockUpper(s.quote));
      const delay = Math.min(...bounds);
      if (Number.isFinite(delay))
        timer = setTimeout(update, Math.min(2_147_483_647, Math.max(1, delay)));
      tick();
    };
    const unsubscribe = client.getQueryCache().subscribe((event) => {
      const [prefix, owner, stock] = event.query.queryKey;
      if (
        (event.type === "updated" || event.type === "removed") &&
        owner === email &&
        ((prefix === "stockContext" && stock === symbol) || prefix === "stockTradeState")
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
      quoteAbort.current?.abort();
    };
  }, [client, auth, email, symbol, key, stateKey]);

  const preview = async () => {
    const s = currentState(),
      c = currentContext();
    const order = { symbol: s.symbol, side: s.side, quantity: s.quantity };
    if (locked(s) || s.phase === "loading_preview" || !c?.execution_enabled || !isStockOrder(order))
      return;
    quoteAbort.current?.abort();
    const controller = new AbortController();
    quoteAbort.current = controller;
    const serial = ++quoteSerial.current,
      version = auth.version;
    const owner = client.getQueryCache().find({ queryKey: stateKey, exact: true });
    const cg = contextGuard(auth, symbol),
      contextSerial = cg.serial;
    const contextOwner = client.getQueryCache().find({ queryKey: key, exact: true });
    setState((old) => ({
      ...old,
      phase: "loading_preview",
      quote: null,
      error: null,
      replacement: null,
      interrupted: false,
    }));
    try {
      const q = await quoteMutation.mutateAsync({ order, signal: controller.signal });
      if (
        auth.version !== version ||
        who(client) !== email ||
        quoteSerial.current !== serial ||
        client.getQueryCache().find({ queryKey: stateKey, exact: true }) !== owner
      )
        return;
      const current = currentContext();
      if (
        client.getQueryCache().find({ queryKey: key, exact: true }) !== contextOwner ||
        cg.serial !== contextSerial ||
        (cg.restrictionAt !== null && stockInstant(q.observed_at) <= cg.restrictionAt) ||
        !quoteCurrent(q, current)
      ) {
        setState((old) => ({
          ...old,
          phase: "draft",
          quote: null,
          interrupted: true,
          error: null,
        }));
        return;
      }
      setState((old) => ({ ...old, phase: "preview", quote: q, error: null }));
    } catch (error) {
      if (auth.version !== version || who(client) !== email || quoteSerial.current !== serial)
        return;
      if (error instanceof StockTradeError && error.status === 401)
        client.setQueryData(["me"], null);
      else
        setState((old) => ({
          ...old,
          phase: "draft",
          quote: null,
          error: error instanceof StockTradeError ? (error.code ?? "unknown") : "unknown",
        }));
    } finally {
      quoteMutation.reset();
    }
  };
  const resolve = async (attempt: Attempt) => {
    const version = auth.version,
      owner = client.getQueryCache().find({ queryKey: stateKey, exact: true });
    setState((s) => ({
      ...s,
      phase: "submitting",
      attempt,
      quote: null,
      replacement: null,
      error: null,
    }));
    const stillOwn = () =>
      auth.version === version &&
      who(client) === email &&
      client.getQueryCache().find({ queryKey: stateKey, exact: true }) === owner &&
      currentState().attempt?.body.idempotency_key === attempt.body.idempotency_key;
    try {
      const fill = await tradeMutation.mutateAsync({
        body: attempt.body,
        signal: new AbortController().signal,
      });
      if (!stillOwn()) return;
      if (fill.coin_id !== attempt.coin_id || fill.provider_asset_id !== attempt.provider_asset_id)
        throw new StockTradeError("unknown");
      setState((s) => ({ ...s, phase: "filled", attempt: null, quote: null, fill, error: null }));
      auth.contexts.forEach((g) => g.serial++);
      await Promise.all(
        ["me", "holding", "stockContext", "stocks", "prices", "portfolio", "history"]
          .map((prefix) => client.invalidateQueries({ queryKey: [prefix] }))
          .concat(client.invalidateQueries({ queryKey: ["eventHistory", email] })),
      );
    } catch (error) {
      if (!stillOwn()) return;
      if (error instanceof StockTradeError && error.status === 401) {
        client.setQueryData(["me"], null);
        return;
      }
      if (
        error instanceof StockTradeError &&
        error.kind === "reprice" &&
        error.replacement !== null
      ) {
        const replacement = error.replacement;
        const current = currentContext();
        const eligible = quoteCurrent(replacement.quote, current);
        setState((s) => ({
          ...s,
          phase: eligible ? "preview" : "draft",
          attempt: null,
          quote: eligible ? replacement.quote : null,
          replacement: eligible ? replacement : null,
          error: null,
          interrupted: !eligible,
        }));
      } else if (error instanceof StockTradeError && error.kind === "refused")
        setState((s) => ({
          ...s,
          phase: "draft",
          attempt: null,
          quote: null,
          error: error.code,
          interrupted: false,
        }));
      else setState((s) => ({ ...s, phase: "unknown", attempt, quote: null, error: "unknown" }));
    } finally {
      tradeMutation.reset();
    }
  };
  const confirm = async () => {
    const s = currentState(),
      c = currentContext();
    if (s.phase !== "preview" || s.quote === null) return;
    if (!quoteCurrent(s.quote, c)) {
      setState((old) => ({
        ...old,
        phase: "draft",
        quote: null,
        replacement: null,
        interrupted: true,
      }));
      return;
    }
    const body = Object.freeze({
      symbol: s.symbol,
      side: s.side,
      quantity: s.quantity,
      expected_exec_price: s.quote.exec_price,
      idempotency_key: crypto.randomUUID(),
    });
    await resolve({ body, coin_id: s.quote.coin_id, provider_asset_id: s.quote.provider_asset_id });
  };
  const checkResult = async () => {
    const s = currentState();
    if (s.phase === "unknown" && s.attempt !== null) await resolve(s.attempt);
  };
  const canPreview =
    !locked(state) &&
    context?.execution_enabled === true &&
    isStockOrder({ symbol: state.symbol, side: state.side, quantity: state.quantity }) &&
    state.phase !== "loading_preview";
  const canConfirm =
    state.phase === "preview" && state.quote !== null && quoteCurrent(state.quote, context);
  return {
    ...state,
    context,
    contextLoading: contextQuery.isPending,
    contextError: contextQuery.isError,
    refreshContext: () => contextQuery.refetch(),
    canPreview,
    canConfirm,
    setQuantity: (value: string) => edit({ quantity: value }),
    setSide: (side: "buy" | "sell") => edit({ side }),
    buyMax: () => {
      const c = currentContext();
      const quantity = c?.buy_max_quantity.split(".")[0] ?? "0";
      if (c?.execution_enabled && /^[1-9][0-9]{0,11}$/.test(quantity)) edit({ quantity });
    },
    sellAll: () => {
      const c = currentContext();
      const quantity = c?.held_quantity.split(".")[0] ?? "0";
      if (c?.execution_enabled && /^[1-9][0-9]{0,11}$/.test(quantity)) edit({ quantity });
    },
    preview,
    confirm,
    checkResult,
    tradeAgain: () => {
      if (currentState().phase !== "filled") return;
      quoteSerial.current++;
      quoteAbort.current?.abort();
      setState(() => empty(routeSymbol));
    },
  };
}
