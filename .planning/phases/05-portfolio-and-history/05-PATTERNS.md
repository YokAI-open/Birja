# Phase 5: Portfolio and History — Pattern Map

**Mapped:** 2026-10-29 · **Files classified:** 24 proposed file families · **Analog coverage:** 22/24 families; 5 analog groups.

Scope comes from `05-RESEARCH.md` and approved `05-UI-SPEC.md`; no CONTEXT exists. Paths below are recommendations for planning, not implemented artifacts. `backend/` and `frontend/` remain independent. “Exact” means matching role/data flow or the existing file itself; it does not mean its domain behavior can be copied unchanged.

## File Classification

| New/modified file family | Role | Data flow | Closest analog | Match |
|---|---|---|---|---|
| `backend/app/services/portfolio_math.py` | utility | transform | `services/trade_math.py` | exact |
| `backend/app/services/portfolio.py` | service | request-response, transform | `services/prices.py:list_prices/load_active_coins` | role-match |
| `backend/app/services/history.py` | service | request-response | `services/prices.py` for projection only; no cursor service | partial |
| `backend/app/schemas/{portfolio,history}.py` | model | transform | `schemas/trades.py` | exact |
| `backend/app/api/v1/{portfolio,history}.py` | route | request-response | `api/v1/trades.py:get_holding` | exact |
| `backend/app/api/v1/router.py` | config | request-response | same file | exact |
| `backend/app/models/trade.py` | model | CRUD | same file | exact |
| `backend/alembic/versions/0008_*.py` | migration | batch | `versions/0007_accounts_cash_cents.py` revision structure | role-match |
| `backend/alembic/env.py` | config | batch | same file | exact |
| `frontend/src/api/{portfolio,history}.ts` | utility | request-response | `api/{prices,trades}.ts` | exact |
| `frontend/src/hooks/usePortfolio.ts` | hook | request-response | `hooks/usePrices.ts` | exact |
| `frontend/src/hooks/useHistory.ts` | hook | request-response | none for infinite-query lifecycle | none |
| `frontend/src/pages/{PortfolioPage,HistoryPage}.tsx` and local display components | component | transform, event-driven | `pages/MarketsPage.tsx`, `TradePage.tsx` | role-match |
| `frontend/src/App.tsx` | component | event-driven | same file | exact |
| `frontend/src/hooks/useTrade.ts` | hook | event-driven | same file | exact |
| `frontend/src/hooks/useAuthMutations.ts`, optional shared private-cache helper | hook, utility | event-driven | existing logout cleanup | role-match |
| `frontend/src/lib/money.ts`, optional signed/percent/time display helpers | utility | transform | `lib/money.ts`, `TradePage.tsx:Row/signedUsd` | role-match |
| `backend/tests/test_portfolio_math.py` | test | transform | `tests/test_trade_math.py` | exact |
| `backend/tests/test_{portfolio,history}_{service,api}.py` | test | request-response | `test_prices_service.py`, `test_trades_api.py`, `tests/helpers.py` | exact |
| `backend/tests/{test_accounts,test_migrations}.py` | test | batch, request-response | same files | exact |
| `frontend/src/{api,hooks,pages}/*.test.ts[x]`, `App.test.tsx`, display-helper tests | test | event-driven, request-response | `api/trades.test.ts`, `pages/MarketsPage.test.tsx`, `test/render.tsx` | exact |
| `frontend/e2e/portfolio-history.spec.ts` | test | event-driven | `e2e/trade.spec.ts`, `e2e/helpers.ts` | exact |
| `.github/workflows/ci.yml`, `CLAUDE.md` critical coverage commands | config | batch | existing identical critical-module lists | exact |
| `deploy/RUNBOOK.md` concurrent-index recovery section | config | batch | research operational guidance; no recovery code analog | none |

Coverage: **16 exact, 5 role-match, 1 partial, 2 none**. Related files are grouped deliberately; planner must expand each family into its actual task file list.

## Pattern Assignments

### 1. Decimal valuation and one financial projection

Apply to portfolio calculator/service and their tests. Copy imports and immutable result shape from `backend/app/services/trade_math.py:25-29,61-84`; use `Decimal`, `localcontext`, frozen dataclasses and typed results. Concrete rounding/context excerpts (`:46-47`, `:103-104`):

```python
def q2(x: Decimal) -> Decimal:
    return x.quantize(Q2, rounding=ROUND_HALF_EVEN)
# Inside the pure calculator:
with localcontext() as ctx:
    ctx.prec = 50
```

`backend/app/services/prices.py:7-12` imports SQLAlchemy `select`, `AsyncSession`, project settings/models; `:77-83` gives the scalar projection/optional-price pattern:

```python
result = await db.execute(
    select(Coin.id, Coin.symbol, Coin.kraken_pair, Price.mid)
    .outerjoin(Price, Price.coin_id == Coin.id)
    .where(Coin.is_active)
    .order_by(Coin.sort_order, Coin.id)
)
return [CoinState(cid, symbol, pair, mid) for cid, symbol, pair, mid in result]
```

Adapt this to the **single Account→positive Holding→Coin→optional Price projection** in RESEARCH lines 143-174. Put positive quantity in the outer-join condition so cash-only accounts survive; scope by session user; include inactive coins; sample calculation time after awaited read. The active filter above belongs to market discovery and must be removed for ownership/history. No row locks, identity-map financial inputs, per-position reads, GET funding, or new cache.

Copy only arithmetic discipline, not trade-specific storage limits/rounding: value/P&L/percent output boundaries follow RESEARCH lines 176-199, raw intermediates remain unrounded, derived values may exceed NUMERIC(20,8), normalize negative zero, and missing price makes aggregate totals/all allocations null. Existing `cost_basis_after` (`trade_math.py:171-186`) already includes buy fees; never replay history to derive basis. Reuse `prices.py:17-28` age/freshness functions (119 fresh, 120..300 aging, 301 stale).

### 2. Authenticated read routes, plain Decimal schemas, bounded history

Apply to both route/schema families and router registration. `backend/app/api/v1/trades.py:3-8` imports `APIRouter`, `HTTPException`, `Response`, `CurrentUserDep`, `DbDep`, schema and service modules. Its GET body (`:91-99`) is the concrete thin-route template:

```python
async def get_holding(
    symbol: str, user: CurrentUserDep, db: DbDep, response: Response
) -> HoldingOut:
    response.headers["Cache-Control"] = "no-store"
    try:
        sym, qty = await trading.holding_quantity(db, user_id=user.id, symbol=symbol)
    except TradeRefused as exc:
        raise _refusal(exc) from None
    return HoldingOut(symbol=sym, quantity=qty)
```

Copy explicit response_model, summary/description and user-derived service argument (`:85-90`); GETs require no new CSRF dependency. `_refusal` (`:25-29`) supplies structured `{code,message}` mapping; use an explicit 422 `invalid_cursor` domain mapping for history rather than a generic 500. Register alongside existing routers in `api/v1/router.py:3-14`; retain POST `/trades` while adding GET `/trades`.

`backend/app/schemas/trades.py:1-14` uses Pydantic and a plain JSON serializer:

```python
Money = Annotated[
    Decimal, PlainSerializer(lambda v: format(v, "f"), return_type=str, when_used="json")
]
```

Use this pattern for every monetary/percentage field, nullable where UI-SPEC specifies; return history `id` as a decimal **string**, leaving existing FillOut unchanged. History reads stored `cash_delta` as signed `total` and joins all coins. No existing cursor code is safe to copy: use RESEARCH lines 229-255 for strict bounded decoding, fixed user predicate, `(created_at DESC,id DESC)`, bound tuple seek, limit+1 and cursor from the last returned row.

### 3. Browser API guards, query refresh and identity lifecycle

Apply to API wrappers/hooks, trade invalidation and authentication cleanup. `frontend/src/api/prices.ts:1,57-63` is the request/guard/AbortSignal contract:

```typescript
export async function fetchPrices(signal?: AbortSignal): Promise<Prices> {
  const body = await apiFetch("/api/v1/prices", { signal });
  if (!isPrices(body)) throw new Error("Unexpected prices response");
  return body;
}
```

Use `api/trades.ts:54-63,90-109` for signed/unsigned decimal regexes and record guards; add null-aware value guards, strict string history IDs, percentages and timestamps. Preserve rejection of JSON numbers/exponents. `api/client.ts:93-122` forwards RequestInit and centralizes CSRF/401 refresh/error parsing; keep all API traffic through it. Cancellation must remain effective through the refresh/retry path.

Copy `usePrices.ts:1-23`: `@tanstack/react-query` + `@/api/...` imports, queryFn `({signal})`, final 401 invalidates `['me']`, 30s interval/focus refresh/10s stale time. Portfolio follows that pattern; history needs `useInfiniteQuery` from RESEARCH lines 275-285 (initial param, opaque cursor, no polling, sequential chain refresh, disable Load more while any fetch runs).

`useTrade.ts:16-21` already awaits `Promise.all` invalidations of me/holding/prices; add portfolio/history for every success including replay. `useAuthMutations.ts:22-26` preserves the observed me query:

```typescript
queryClient.removeQueries({ predicate: (query) => query.queryKey[0] !== "me" });
queryClient.setQueryData(["me"], null);
```

This is a starting point: **await cancellation, then remove private data before publishing identity**, on both logout and successful verify (`:8-15` currently publishes me immediately). Reuse a small helper only for those real callers. Test passive expiry→B sign-in with A cached and in flight; do not use queryClient.clear(), which detaches useMe's observer.

### 4. Semantic tables, retained data, formatting and signed-in shell

Apply to pages/components/App/display helpers. `MarketsPage.tsx:1-8` shows `@/` imports for Button/Card/FreshnessBadge/hooks/formatters. `:11-16` computes age from server age plus elapsed since dataUpdatedAt. `:19-46,124-127` separates initial skeleton, no-data error, successful empty state and retained-data refresh warning. Preserve those distinctions for portfolio and history, including next-page failure.

Concrete table/definition-list excerpts are `MarketsPage.tsx:48-54` and `TradePage.tsx:59-64`:

```tsx
<div className="overflow-x-auto">
  <table aria-label="Markets" className="w-full border-collapse text-left">
    <thead><tr className="border-b border-border">
      <th scope="col" className="h-10 text-[13px] leading-[18px] font-medium text-muted-foreground">
// TradePage Row, used inside a dl:
<dt className="text-muted-foreground">{label}</dt>
<dd className={cn("tabular-nums", strong && "text-[17px] font-semibold")}>{value}</dd>
```

Adapt to approved UI-SPEC: keyboard-focusable labelled scroll region, row headers, all fields in mobile list/dl, one accessible representation, 44px actions, local full timestamps, retained focus and end marker. Existing font weights/17px Row text above are **not** the new page typography contract. `App.tsx:13-46,57-81` owns authentication switch, nav and signed-in routes; extend with Portfolio/History plus separate Account and responsive bottom tabs, preserving account/health/trade/direct links.

Reuse `lib/money.ts:3-8,20-37` string-safe USD/quantity/unit-price formatting and `lib/age.ts:11-25`, `FreshnessBadge.tsx:16-21`. `TradePage.tsx:56-57` has a display-only signedUsd helper, but Phase 5 needs the approved zero-neutral/U+2212/outcome-text behavior; do not copy its unconditional positive-zero plus. No client financial arithmetic or percent multiplication; validate percentage strings before direct bar widths.

### 5. Behavioral tests, migrations and existing regression tripwires

Apply to all test/config/migration families. `backend/tests/test_trade_math.py:80-84` asserts half-even ties (`q2(D('0.125')) == D('0.12')`, `q2(D('0.135')) == D('0.14')`); `:98-110` asserts independent worked monetary outputs. Add the research worked portfolio/dust/zero-basis/large-value cases, including -$0.50 with neutral 0.00% total return.

`test_prices_service.py:65-85` seeds real isolated PostgreSQL and asserts order/value/as_of/status; `tests/helpers.py:49-86` offers coin_id/put_price/put_holding/set_cash. `test_trades_api.py:90-109,133-150` asserts plain strings, 401, no-store, exact fields and read-only effects. Copy its concrete checks:

```python
assert isinstance(value, str), name
assert PLAIN.match(value), (name, value)
assert "e" not in value.lower()
assert resp.headers["cache-control"] == "no-store"
```

New tests must prove user isolation, missing/inactive prices, real concurrent before/after snapshot, tied timestamps, cursor bounds/foreign boundaries, exact bigint strings, stored signed totals and page continuation; use RESEARCH validation matrix, not DB mocks. `frontend/src/api/trades.test.ts:61-87` mutates valid fixtures to reject numeric/exponent values. `pages/MarketsPage.test.tsx:45-62,99-149,215-248` uses renderWithClient, role queries, fake timers, retry and retained-data assertions; `test/render.tsx` supplies QueryClientProvider/MemoryRouter/userEvent. Extend App/auth/trade regressions and verify cancellation, infinite append/retry/end focus.

`backend/alembic/versions/0007_accounts_cash_cents.py:9-18,21-44` supplies revision typing and reversible upgrade/downgrade shape, **not** concurrent index DDL. Add metadata Index to `models/trade.py:45-68`, create new 0008, and configure transaction_per_migration in `alembic/env.py:49-55,61-65`; copy concurrent/autocommit design from RESEARCH lines 261-269. No existing migration shows that exact operation.

**Update exact existing expectations:** `backend/tests/test_accounts.py:124-146` adds only GET `/api/v1/portfolio` and GET `/api/v1/trades` to its exact route allow-list. `test_migrations.py:34-50` changes head assertions 0007→0008; keep `:53-82` specifically targeting the 0007 cents guard. Reuse `await asyncio.to_thread(command.upgrade, cfg, 'head')` (`:38`) and metadata parity (`:85-94`); add populated 0007→0008→0007→head index validity/key-order/data-preservation checks. Keep destructive migration tests serial.

`frontend/e2e/trade.spec.ts:1-4,21-44` and `e2e/helpers.ts:35-44` provide the CI fake-price/console-email happy path; extend buy→portfolio→history→sell without running against real-email dev/prod. `.github/workflows/ci.yml:45-47` and CLAUDE common commands must both add new critical portfolio/history modules to the existing 100% coverage list. RUNBOOK needs explicit concurrent-index failure/recovery instructions from research.

## Shared Patterns / No Exact Analog

All private reads use CurrentUserDep + explicit user predicates + no-store; routes delegate logic and preserve structured errors. Server owns Decimal arithmetic/freshness, browser owns formatting/interaction, and query cancellation/removal precedes identity publication. UI-SPEC is authoritative for null states, signs, accessibility and new navigation.

No exact implementation exists for **one-statement account+holdings snapshot**, **strict keyset cursor**, **useInfiniteQuery**, **concurrent-index DDL/recovery**, or **cancel-before-new-identity lifecycle**. Use the referenced RESEARCH sections for these additions and keep the actual analogs only for their reusable boundaries.

## Metadata

Search scope: targeted `backend/app`, `backend/tests`, `backend/alembic`, `frontend/src`, `frontend/e2e`, CI and design-system references; stopped after five sufficient analog groups. Read-only source inspection only: no services/tests executed, credentials inspected, authentication/trades performed, source changes or commits. Only this pattern map was written.
