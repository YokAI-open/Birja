# Phase 9: Whole-Share Trading and Combined Portfolio — Pattern Map

**Mapped:** 2026-11-11
**Scope:** proposed targets from 09-CONTEXT, 09-RESEARCH and 09-UI-SPEC; names of new modules are recommendations, not existing files.
**Search stop:** five strong anchor families: trading, ownership, portfolio, typed guarded client, revision-aware recovery. This map authorizes no source edits, provider access or activation.

## File Classification

Paths below are repository-relative. A row containing several paths applies the same assignment to every named file; test families describe proposed suites rather than a requirement to create one file per scenario.

| New/modified file | Role | Data flow | Closest analog | Match |
|---|---|---|---|---|
| `backend/app/services/stock_trade_math.py` (new) | utility | transform | `services/trade_math.py`, ownership basis call | role |
| `backend/app/services/stock_trading.py` (new) | service | request-response / CRUD | `services/trading.py` plus `stock_ownership.py` | role |
| `backend/app/services/trading.py` | service | request-response / CRUD | existing execute/replay functions | exact, scoped change |
| Shared asset-agnostic idempotency helper (new; planner selects path) | utility | CRUD | `trading.py:_find_trade`, `_replay` | partial |
| `backend/app/services/stock_ownership.py` | service | event-driven / CRUD | existing `append_stock_movement` | exact integration |
| `backend/app/services/stock_eligibility.py` (proposed new) | service | transform | ownership DB clock/gate; existing stock rules named in research | partial |
| Status model and status rules/collector modules (new; planner freezes paths) | model / service / provider | event-driven / CRUD | stock authority model and scheduler structure; ownership gate | partial |
| `backend/app/models/trade.py`, `backend/app/models/stock.py` and new immutable stock-fill-facts model | model | CRUD | existing Trade/instrument identity; immutable ownership cause | role |
| Successor migration(s) after `0012` | migration | batch | `0012_stock_action_resolution.py`, existing accounting migration | role |
| `backend/app/schemas/stock_trades.py` (new), `backend/app/api/v1/stock_trades.py` (new) | utility / controller | request-response | `schemas/trades.py`, `api/v1/trades.py` | role |
| `backend/app/schemas/stocks.py`, `backend/app/services/stocks.py`, status scheduler integration | utility / service / config | request-response / batch | existing stock discovery, authority projections | role |
| `backend/app/services/portfolio.py`, `portfolio_math.py` | service / utility | request-response / transform | existing single-statement snapshot | exact extension |
| `backend/app/schemas/portfolio.py`, `api/v1/portfolio.py` | utility / controller | request-response | existing nullable snapshot contract | exact extension |
| `frontend/src/api/stockTrades.ts` (proposed new) | utility | request-response | `api/trades.ts`, stricter `api/stocks.ts` | role |
| `frontend/src/hooks/useStockTrade.ts` (proposed new) | hook | request-response | `hooks/useStocks.ts`, TradePage attempt lifecycle | role |
| `frontend/src/pages/StockTradePage.tsx` and optional extracted ticket/receipt components (new) | component / route | request-response | `pages/TradePage.tsx` | role |
| Frontend route registration and stock discovery trade links | route / component | request-response | existing crypto route/link structure | role |
| `frontend/src/api/stocks.ts`, `hooks/useStocks.ts` | utility / hook | request-response | existing strict parser/deadline guards | exact extension |
| `frontend/src/api/portfolio.ts`, `hooks/usePortfolio.ts` | utility / hook | request-response | stricter stock parser/auth-isolated hook | role |
| `frontend/src/pages/PortfolioPage.tsx`, `components/PortfolioHoldings.tsx`, `components/PortfolioAllocation.tsx` | component | request-response | existing portfolio components, UI-SPEC layout contract | exact extension |
| `deploy/backup-snapshot.py`, `deploy/verify-restore.py` | utility | file-I/O / batch | existing revision dispatch | exact extension |
| `deploy/db/bootstrap-roles.sql` | config | batch | existing explicit stock grants | exact extension |
| `deploy/tests/ops-fixtures.py`, `test-db-operations.sh`, `test-stock-recovery-contracts.py` | test | batch / file-I/O | existing serial recovery/role/TLS lanes | exact extension |
| New stock math/service/API/concurrency tests; existing crypto regression suites | test | request-response / CRUD | `test_trading_concurrency.py`, trading service/API tests | role |
| Extended mixed snapshot/math/service/API tests | test | CRUD / transform | `test_portfolio_snapshot.py` and existing portfolio suites | exact extension |
| Frontend stock client/ticket and portfolio tests; stock-trade browser stories | test | request-response | existing trades/stocks parser tests, trade/portfolio/stock-actions e2e | role |
| CI critical coverage and isolated proof configuration, if needed | config | batch | current checks; add actual new critical modules | exact extension |

## Pattern Assignments

### 1. Stock transaction, thin authenticated API and global key helper

**Anchors:** `backend/app/services/trading.py`; `backend/app/api/v1/trades.py`.

Existing service imports use SQLAlchemy async sessions, project models and domain math; new stock code should retain this layering. Keep money in Decimal and keep calculation separate from transactions.

**Shared account serialization** — `trading.py:255–262`:

```python
account = (
    await db.execute(
        select(Account)
        .where(Account.user_id == user_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
).scalar_one()
```

Stock execution acquires its instrument gate BEFORE this account lock; preserve the existing crypto account-first path. Both paths must serialize the SAME account, not introduce another cash row. `trading.py:264–269` returns replay before prices; `333–349` flushes/persists before commit and rolls back refusal/uniqueness races. Copy the transaction/error discipline, not crypto-only eligibility/math.

**Auth, CSRF, cache and replay response** — `api/v1/trades.py:53–82`:

```python
@router.post(
    "/trades",
    response_model=FillOut,
    status_code=201,
    dependencies=[Depends(verify_csrf)],
    # existing description omitted here
)
# Existing signature uses CurrentUserDep, DbDep, SettingsDep, Response.
```

The actual handler sets `Cache-Control: no-store` at line68, passes `user.id` at72, maps domain refusal at78–79, and changes status to200 on replay at80–81. New stock routes use the same aliases/import from `app.core.deps`, explicit response models and fixed domain-code mappings; services own mutations. Existing `_refusal` lines25–29 maps changed-price previews into typed responses.

**Do not copy unchanged:** `_find_trade` lines142–155 filters `Coin.asset_class == "crypto"`. It cannot detect a stock/crypto key collision. A shared user+key lookup must see all asset classes, compare the original economic payload/instrument identity and produce conflict across endpoints. `_fill` lines158–178 joins the current symbol and lacks shares-after facts; a stock receipt must instead use immutable saved symbol/name/identity, bid/ask/feed/time, balances and original input. Expected price and current eligibility are not replay prerequisites. Keep old crypto economic behavior and stored rows intact.

**Tests:** `backend/tests/test_trading_concurrency.py:1–6` explicitly uses real PostgreSQL and separate request sessions. Lines71–79 execute15 concurrent buys and assert exact accepted/refused counts. Extend to stock+crypto spending and same-key/cross-endpoint races; do not mock locks. API suites must assert auth/CSRF and no foreign-user replay.

### 2. Ownership movement and final execution barrier

**Anchor:** `backend/app/services/stock_ownership.py`.

**Stable gate** — lines104–109:

```python
await db.execute(
    text(
        "SELECT pg_advisory_xact_lock(hashtextextended("
        "'birja.stock.instrument:' || CAST(:coin AS text),0))"
    ),
    {"coin": str(coin_id)},
)
```

Keep gate namespace, READ COMMITTED verification and bounded local timeouts (lines86–119). `_clock` lines122–123 uses PostgreSQL `clock_timestamp()`, not transaction-start time. Lock all instrument holdings in deterministic `(user_id,id)` order (lines203–216), so a caller locking only its own holding first is not an equivalent pattern. Movement includes signed quantity, basis, immutable trade cause and no caller-invented economic timestamp.

**Post-wait monitoring check** — lines294–301:

```python
if (
    state.health != "current"
    or state.valid_until is None
    or now >= state.valid_until
    or state.next_blocking_at is not None
    and now >= state.next_blocking_at
):
    raise OwnershipHeld("monitor_unavailable")
```

`append_stock_movement` itself performs awaited gate/account/holdings/history/cause checks, then flushes at357. A stock caller checking quotes/session/status before invoking it is insufficient. Specify the final guarded boundary after the helper's blocking work and every later awaited DB statement; expiration/changed authority must roll back cash, Trade, facts, holding and movement together. Prove closure,120-second equality,status expiry,action cutoff and permission/unit changes while blocked. Do not commit fill separately, mutate holdings twice, grant action-state writes, or substitute `Trade.created_at` for economic ownership time. Retain the existing unsupported transaction-epoch guard.

### 3. Mixed portfolio snapshot and historical valuation projection

**Anchor:** `backend/app/services/portfolio.py:40–86`.

**One financial input statement** — lines57–64:

```python
.select_from(Account)
.outerjoin(Holding, and_(Holding.user_id == Account.user_id, Holding.quantity > 0))
.outerjoin(Coin, Coin.id == Holding.coin_id)
.outerjoin(Price, and_(Price.coin_id == Coin.id, Coin.asset_class == "crypto"))
.where(Account.user_id == user_id)
.order_by(Coin.sort_order, Coin.id)
# after awaited statement:
valued_at = now or datetime.now(UTC)
```

Preserve scalar projections, cash-only outer join, account scoping and a coherent statement snapshot. Extend the statement with stock facts/authority/compatible midpoint marks rather than sequential cash/holdings queries. Existing crypto-only active-price projection lines51/60 and catalogue ordering must change deliberately: stocks need independent authority/unit semantics and ticker ordering with stable identity tie-break. A timestamp after reads cannot make inconsistent multiple statements coherent.

Extend pure portfolio math and schemas with server known subtotal, unknown count, asset class, class amounts/allocations and deadline/reason facts. Overall P/L and ALL allocation percentages are null if incomplete; zero denominator is not applicable. Original `starting_cash` remains stored account input; future dividend cash comes once from Account.cash. Historical closed/halted marks have source dates and separate permission/action validity, not renewed120s execution authority. Corporate uncertainty overrides historical display and derived unit-cost inference.

**Snapshot test pattern** — `backend/tests/test_portfolio_snapshot.py:15–26`:

```python
OLD = (D("9000"), D("1"), D("1000"), D("10000"))
NEW = (D("8000"), D("2"), D("2000"), D("10000"))

def assert_whole_snapshot(values):
    assert values in (OLD, NEW), "Financial inputs came from different commits"
```

Its event-controlled writer lines44–73 and split-reader negative control from76 are the closest race proof. Extend to mixed positions/cash and actions; assertions must exclude hybrid states.

### 4. Strict typed client, isolated queries and stock ticket

**Anchors:** `frontend/src/api/stocks.ts`, `hooks/useStocks.ts`, `pages/TradePage.tsx`; existing `api/trades.ts` is a weaker parser reference.

**Exact string boundary** — `api/stocks.ts:111–116`:

```typescript
function units(value: unknown): bigint | null {
  if (typeof value !== "string" || !/^\d{1,12}(?:\.\d{1,8})?$/.test(value)) return null;
  const [whole, fraction = ""] = value.split(".");
  const result = BigInt(whole + fraction.padEnd(8, "0"));
  return result > 0n ? result : null;
}
```

Use explicit whole-share lexical/range validation for quantity; adapt zero/null/signed cases deliberately. Money must not enter Number arithmetic. Existing strict exact-key/enum/timestamp parsing is at70–108 and quote relationship validation118–137. `api/trades.ts:116–140` shows `apiFetch`, AbortSignal and rejecting malformed responses; prefer the stricter stock validators for new financial contracts. A malformed execution success is UNKNOWN outcome, not a safe no-fill refusal.

**Auth ownership barrier** — `hooks/useStocks.ts:325–333`:

```typescript
const response = await fetchStocks(requestSignal);
requestSignal.throwIfAborted();
if (
  !identity ||
  emailOf(client) !== identity ||
  guard.lifecycle !== lifecycle ||
  client.getQueryCache().find({ queryKey: key, exact: true }) !== owner
)
  throw new Error("Stock session changed");
```

Preserve user-scoped keys, identity/lifecycle/owner checks, aborts, later restriction high-water marks, generation/epoch ordering and401 handling (381–385). Query settings390–395 disable retry, poll30s and use `gcTime:0`; exact safety timers397–438 purge forbidden values in CACHE as well as view. Existing generic `usePortfolio` key alone is not an adequate stock authority/auth pattern.

**Critical warning:** `projectStocks` currently requires `age < 120` and drops expired quotes (`useStocks.ts:22–116`). Do not copy its fresh-only projection unchanged for closed/halted historical marks. Separate historical display/retention/action/unit deadlines from new-execution validity, while retaining conservative elapsed transport guards and preventing delayed responses from restoring removed values.

**Attempt key** — `pages/TradePage.tsx:105–108`:

```typescript
// Idempotency key of the current attempt. Cleared only by an order edit, a terminal
// outcome or price_changed, never by a quote refetch: an attempt with an unknown
// outcome may already have executed and only the same key makes a retry a replay.
const keyRef = useRef<string | null>(null);
```

Use as an intent anchor, not a wholesale state machine: stock UNKNOWN outcome freezes symbol/side/quantity/key and offers Check order result even after closure/hold. Existing crypto confirm guard159 requires a live quote; that guard must NOT prevent stock result resolution. New unavailable drafts retain quantity while invalidating preview; reopen never autoexecutes. Success remains on immutable saved receipt, invalidates shared server queries and focuses receipt heading; no optimistic cash math. Copy UI primitives/design tokens, but implement the actual09-UI-SPEC whole-share/bid-ask/repricing/table-card/bar contract.

### 5. Successor schema, exact recovery and restricted-role entrypoints

**Anchors:** `deploy/backup-snapshot.py`, `deploy/verify-restore.py`, `deploy/db/bootstrap-roles.sql`, migrations0011/0012 and `deploy/tests/ops-fixtures.py`.

`backup-snapshot.py:83` currently fixes supported revisions through0012; lines84–110 enumerate exact columns, identity tables at197, `contract_columns`227, `manifest_sql`239, `schema_guard_sql`302 and `validate_manifest`323 dispatch by revision. Extend via successor-only contracts; preserve prior revision hashes/columns, rows, sequences, operator function authority and corrupt-manifest rejection. New schema/function expectations must be independently measured from real migrated PostgreSQL, not trusted because a manifest self-asserts them.

`verify-restore.py`: `canonical`768, `verify`780, `restore_resolution_authority`848, `restored`889 and its revision checks943 are actual consumers. Schema allowlists, constraints, trigger/function authority, dump/restore ordering and restricted grants all need successor dispatch before runtime writers. Bootstrap revision checks at14/17/85, stock grants110–119 and accounting grants123+ are part of both fresh and populated-upgrade contracts.

**Narrow authority / bounded downgrade** — `0012_stock_action_resolution.py:241–254`:

```python
op.execute(FUNCTION)
op.execute(f"REVOKE ALL ON FUNCTION {SIGNATURE} FROM PUBLIC")
op.execute(f"GRANT EXECUTE ON FUNCTION {SIGNATURE} TO birja_action_operator")
# downgrade refuses populated financial authority:
# IF EXISTS(SELECT FROM public.stock_action_resolutions) THEN
#   RAISE EXCEPTION 'populated resolution authority cannot be downgraded';
```

Do not automatically introduce SECURITY DEFINER/new operator access for stock fills. Planner must select concrete cross-row Trade/facts/movement integrity and review exact trigger/function scope. Existing0012 is immutable; no historical patch or fixture-only grant repair. Test actual app/scheduler operations on existing TLS connections, both fresh bootstrap and populated upgrade, with denied direct fractional/nonzero-fee/orphan/mismatched inserts.

**Canonical isolated ops invocation:**

```bash
deploy/tests/test-db-operations.sh --all
```

The wrapper lines1–12 uses strict bash/umask and execs `python3 "$ROOT/deploy/tests/ops-fixtures.py" "$@"`. The Python dispatcher2719–2740 accepts `--all`, executing `roundtrip()`, `roles()`, then `assert tls() == tls(fresh_bootstrap=True)` serially. Thus direct `python3 deploy/tests/ops-fixtures.py --all` exists, but the shell wrapper is the canonical documented entrypoint. Do not start concurrent fixed-project ops lanes or use production. Extend retained revision loop currently at528 and actual TLS consumer lanes, not only lexical schema tests.

## Shared Patterns

- Thin authenticated/CSRF routes pass trusted `user.id`; fixed reason codes and no-store response, no raw provider/operator errors.
- Money remains Decimal/NUMERIC and JSON strings, explicit half-even defined rounding. Server owns max quantity, preview, accounting and known subtotal.
- Transaction owns one instrument gate then shared account then sorted holdings; all effects roll back on final invalidity. Preserve crypto's independent gates/math.
- User+key uniqueness is global across asset routes; replay saved immutable facts before any current quote/status/action requirement.
- TanStack Query owns network state, with auth-generation isolation and immediate conservative cache purging. Drafts remain memory-only.
- Tests use isolated real PostgreSQL races and HTTP-boundary external fakes. Fake clocks and controlled late responses prove both rendered and cached safety; UI/browser acceptance is separate from source contract approval.
- Activation remains explicitly deferred; synthetic normal status/permission fixtures are not provider rights, bootstrap or continuity evidence.

## No Complete Analog Found

| Capability | Reason / planner obligation |
|---|---|
| Independent halt/freeze status collector with continuity lease | Existing discovery status is unknown-only; fresh quotes do not establish normal status. Freeze typed persisted rules and fail-closed bootstrap/reconnect contract; live access remains deferred. |
| Immutable stock receipt + cross-row Trade/facts/movement integrity | Crypto receipt lacks immutable stock identity and historical shares-after; choose explicit successor schema and direct-write constraints. |
| Cross-asset replay/conflict helper | Existing lookup is crypto-filtered; widen conflict visibility while keeping endpoint payload/receipt safety. |
| Authorized retained closed/halted mark projection | Existing browser hook is fresh-only. Define distinct display versus execution deadlines and action-unit overrides. |

## Metadata

**Analogs:** five strong families cover all classified targets; partial items above need explicit new design, not mechanical copying.
**Scope searched:** backend service/API/model/migration/test paths, frontend API/hook/page/component/test paths, deploy recovery/bootstrap/fixture entrypoints.
**Extraction:** concrete anchors read with numbered lines; related paths located with rg. No source, private configuration, provider, production or git mutation performed.
