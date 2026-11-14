# Phase 12 — Portfolio Ownership Pattern Map

**Mapped:** 2026-11-14
**Scope:** Read-only mapping of the bounded integration inventory in
`12-RESEARCH.md`; no implementation, tests, package installation or live access.
**Source of decisions:** `12-CONTEXT.md`, approved requirements/roadmap and
`12-UI-SPEC.md`. Candidate names below are planning suggestions, not existing APIs.

## File Classification

Each row assigns the listed files to the same role/data-flow pattern. Existing
files normally retain their layer; proposed files are explicitly labelled.
References to migration 0013/0014 are analogs to read, never files to rewrite.

### Database, identity and financial services

| New/modified candidate files | Role / data flow | Closest existing analog | Match and required extension |
|---|---|---|---|
| `backend/app/models/user.py` | Model / persisted financial root | Same file: `Account`, lines 33–49 | Exact existing root; preserve IDs/cash/baseline, add lifecycle/name and paired identity; relax user uniqueness only at qualified final boundary |
| `backend/app/models/trade.py` | Model / immutable fill and mutable holding | Same file: lines 23–88; `models/stock_execution.py:27–57` | Exact role; holdings become root+coin, cause tuples gain root, user-global retry uniqueness stays |
| `backend/app/models/stock_execution.py` | Model / immutable receipt | Same file: compound FK lines 30–34 | Exact lineage style; add root to receipt/trade pairing without rewriting saved authority |
| `backend/app/models/corporate_action.py` | Model / ordered event journal | Same file; `models/dividend.py:40–72` | Exact role; root-aware movements, entitlements, supersession and split-owner identity; market event/sequence stays global |
| `backend/app/models/dividend.py` | Model / append-only payment/correction | Same file: uniqueness and composite causal FKs, lines 40–72, 115 onward | Exact constraint style; event+root uniqueness and all prior/original/entitlement tuples gain the same root |
| Proposed `backend/alembic/versions/0015_portfolio_expansion.py` | Migration / schema expansion | `0014_dividend_accounting.py:51–90`, `0013_stock_execution.py` | Role match only; nullable associations and finite migrator guard are novel, migration-only state must refuse runtime/recovery |
| Proposed `backend/alembic/versions/0016_portfolio_association.py` | Migration / bounded data association | Existing Alembic revision structure; populated migration tests | Partial: no safe existing immutable-row association to copy; require byte-equality and owner-only transition proofs |
| Proposed `backend/alembic/versions/0017_portfolio_authority.py` | Migration / final constraints and authority | `0014_dividend_accounting.py:92–120,374–440`; exact grant/bootstrap contracts | Role match; finalize NOT NULL/pairing/authority, remove temporary path, support final revision explicitly |
| Proposed `backend/app/services/portfolios.py` | Service / owned-active target resolution and metadata discovery | `core/deps.py:82–117`, `services/accounts.py:32–40`, `services/trading.py:247–255` | Role match; identity auth is reusable, existing account selection is a negative example until ID+owner+active predicates are added |
| `backend/app/core/deps.py` | Dependency / session identity and resource authorization | Same file: user/session join and `Annotated` aliases | Exact identity pattern; do not replace user/session auth with financial-account existence |
| `backend/app/services/accounts.py`, `backend/app/services/auth.py` | Service / signup grant versus returning identity | `accounts.py:13–40` | Exact orchestration pattern; only genuinely new signup funds first root, identity-only reads must not join one Account or regrant |
| `backend/app/schemas/auth.py`, proposed `backend/app/schemas/portfolios.py` | Schema / validated wire contracts | Existing auth/stock-trade/event-history Pydantic schemas | Role match; identity-only v2 output, string browser IDs, explicit metadata/financial response context; no pooled or invented cash |
| Proposed `backend/app/api/v2/router.py`, `auth.py`, `me.py`, `portfolios.py` | Router/controller / request-response | `api/v1/router.py:1–24`, `api/v1/stock_trades.py:20–54,90–132` | Exact registration/private thin-route style; explicit versioned resource paths, existing CSRF/session machinery and non-enumerating target errors |
| `backend/app/api/v1/auth.py`, `me.py`, `trades.py`, `stock_trades.py`, `portfolio.py`, `history.py`, `event_history.py` | Router / legacy compatibility refusal | Existing private stock route wrapper and domain-error mapping | Existing paths remain compatibility surfaces; final-schema unscoped calls must fail before financial/OTP effects, not guess a root |
| `backend/app/main.py` | Composition / router and lifecycle wiring | Existing app factory and v1 router registration | Exact role; wire new router without changing cookie/session/production-doc gates |
| `backend/app/services/trading.py`, `stock_trading.py` | Service / transactional execution | `trading.py:235–291`, `stock_trading.py:242–334` | Exact transaction/replay styles; target root lock+post-wait active recheck, scoped holding/cause, unchanged arithmetic and market gates |
| `backend/app/services/trade_idempotency.py` | Service / immutable request identity | Same file: lines 13–36 | Exact user-global lookup; extend equality with original portfolio, never rewrite original keys or allocate a sibling fill |
| `backend/app/services/stock_ownership.py`, `corporate_actions.py` | Service / instrument-ordered journal and worker effects | `stock_ownership.py:86–119,361–414`; `corporate_actions.py:553–620` | Exact instrument gate and full-journal proof; per-root maps and frozen epoch behavior are novel extensions |
| `backend/app/services/dividends.py` | Service / narrow SQL transaction owner | Same file: lines 45–62,65–88; final definer SQL in new revision | Exact bound-SQL/commit style; root must derive from validated entitlement, final authority guard stays last business operation |
| `backend/app/services/portfolio.py` | Service / read-only financial snapshot | Same file: lines 45–95,119–158 | Exact valuation projection; root predicates and holding join change, exact money/baseline/dated/incomplete semantics do not |
| `backend/app/services/history.py`, `event_history.py` | Service / bounded seek/union/hydration | `event_history.py:35–103,142–195,217–313` | Exact cursor validation/total ordering; add root to every union arm, cursor, hydration and original-reference path |
| `backend/app/api/v1/stock_trades.py`, `backend/app/schemas/stock_trades.py`, `backend/app/schemas/trades.py` | Router/schema / existing execution contract | Their current quote/execute/context/receipt shapes | Keep fees, quantities, repricing and saved fill facts; scope adapters/new versioned routes without broadening financial authority |

### Browser and existing screens

| New/modified candidate files | Role / data flow | Closest existing analog | Match and required extension |
|---|---|---|---|
| `frontend/src/App.tsx` | Route/composition / navigation | Existing financial routes, auth boundary and focus behavior | Exact shell pattern; explicit portfolio URLs and safe sole-root entry resolution; no management chooser in Phase 12 |
| `frontend/src/api/auth.ts`, `frontend/src/hooks/useMe.ts`, `useAuthMutations.ts` | Client/hooks / identity/session | Existing API client, identity query and auth mutations | Exact request/cache conventions; identity-only response and no cash default; logout/refresh/CSRF semantics remain |
| Proposed `frontend/src/api/portfolios.ts`, `frontend/src/hooks/usePortfolioTarget.ts` | Client/hook / metadata request and target boundary | `api/stockTrades.ts:599–659`, `hooks/usePortfolio.ts:252–283` | Role match; validate string root/name response, consume AbortSignal, check captured owner+root and prohibit fallback |
| `frontend/src/api/trades.ts`, `stockTrades.ts`, `portfolio.ts`, `history.ts`, `eventHistory.ts` | Client / financial request-response | `stockTrades.ts:599–659` and existing parsers | Exact parser/no-store/error style; explicit scoped URL and response identity, root-bound cursor/attempt; do not only prepend a URL |
| `frontend/src/hooks/useTrade.ts`, `useQuote.ts`, `useHolding.ts` | Hook / draft, quote and execution state | Existing hooks plus `useStockTrade.ts` original-attempt guards | Role match; user+root+instrument keys, captured root in confirmation and unknown retry |
| `frontend/src/hooks/useStockTrade.ts` | Hook/state machine / quote, attempt, replay | Same file: lines 21–47,159–205,306–364,561–590 | Exact guard/mutation pattern; add root to keys, guard maps and immutable attempt identity; no mutable selected-root retargeting |
| `frontend/src/hooks/usePortfolio.ts` | Hook / guarded valuation projection | Same file: lines 21–55,252–283 | Exact session/lifecycle/serial/cache-owner pattern; partition projection state by user+root, not only query key |
| `frontend/src/hooks/useHistory.ts`, `useEventHistory.ts` | Hook / private infinite pagination | `useEventHistory.ts:7–25,35–102` | Exact epoch/cache guard; root-bound cursor, seen set, cache invalidation and original references |
| Proposed `frontend/src/components/PortfolioContext.tsx` | Component / read-only labelled context | `components/StockAttribution.tsx:13–25`; approved UI-SPEC | Role match, not identical semantics: visible neutral `Portfolio`/name text with safe wrapping, not an interactive badge/selector or repeated live region |
| Proposed `frontend/src/components/PortfolioTargetBoundary.tsx` | Component/boundary / loading, zero, ambiguous, unavailable | Existing page loading/refusal cards, `PortfolioPage.tsx:43–68` | Role match; use exact approved copy and normal heading/focus, remove unauthorized finances rather than render stale data |
| `frontend/src/pages/TradePage.tsx`, `StockTradePage.tsx`, `frontend/src/components/StockTradeReceipt.tsx` | Page/component / draft→confirmation→receipt | Existing ticket and original fill UI | Exact layout/data semantics; repeat captured root context and same-root links; keep saved fill values immutable |
| `frontend/src/pages/PortfolioPage.tsx`, `frontend/src/components/PortfolioHoldings.tsx` | Page/component / statement and holdings | `PortfolioPage.tsx:1–92` and existing holdings projection | Exact layout/financial semantics; portfolio context above data, no comparison/creation management here |
| `frontend/src/pages/HistoryPage.tsx`, `frontend/src/components/HistoryEventDetails.tsx` | Page/component / mixed events and original details | Current History table/cards/details | Exact presentation; root follows paging and original reference; no prior-owner/root detail remains visible |
| `frontend/src/pages/AccountPage.tsx` | Page / identity and sign-out | Same file: lines 7–36 | Exact identity/sign-out card; remove lines 17–22 user-wide cash block, do not invent pooled/null/zero cash |

### Roles, recovery and proof candidates

| New/modified candidate files | Role / data flow | Closest existing analog | Match and required extension |
|---|---|---|---|
| `deploy/db/bootstrap-roles.sql`, `backend/app/db/dev_bootstrap.py` | Bootstrap/authority / revision-specific ACL | Existing explicit revision dispatch and table/column grants | Exact qualification style; final root metadata must not inherit broad accounts UPDATE; migration-only revisions refuse normal bootstrap |
| `deploy/backup-snapshot.py` | Utility/producer / exact manifest and encrypted snapshot | Same file: lines 196–233,380–425,522–563 | Exact shape/hash/identity/authority pattern; add final revision explicitly, preserve 0007–0014 bytes/contracts, reject intermediate states |
| `deploy/backup-manifest.sql`, `deploy/verify-restore.py` | Utility/consumer / manifest projection and cold restore | Existing matching producer/consumer contract | Exact paired inventory style; root/lifecycle/cause/sequence equality and pre-grant authority authentication, not aggregate-only totals |
| `deploy/configure-db.sh`, `deploy/deploy.sh` | Operational script / admission and migration orchestration | Existing schema/role/recovery gates | Role match; explicitly classify migration-only states and retain a reviewed migration-to-final path; no host execution authorized now |
| Proposed `backend/tests/test_portfolio_migrations.py` | Test / populated schema transition | `test_stock_execution_migrations.py:12–70`; existing Alembic migration fixtures | Role match, MISSING file: exact pre/post original economic inventory and stage resume/refusal; do not assert only equal balances |
| Proposed `backend/tests/test_portfolio_ownership.py` | Test / authorization, locking and retries | `test_stock_trading_concurrency.py`, `test_stock_trading_waits.py`, `test_accounts.py` | Role match, MISSING file: two roots/same instrument/same user, foreign owner, zero/closed root and real sessions |
| Proposed `backend/tests/test_portfolio_authority.py` | Test / restricted SQL authority | `test_dividend_authority.py`, `test_stock_execution_migrations.py` | Role match, MISSING file: actual migrator/app/scheduler behavior, no residual association bypass or cross-root cause |
| Proposed `backend/tests/test_portfolio_scoped_history.py` | Test / private cursor and original hydration | `test_event_history.py`, `test_event_history_cursor.py`, `test_event_history_api.py` | Role match, MISSING file: every event kind, tie boundaries, sibling cursors and original links |
| `backend/tests/test_accounts.py`, `test_auth_verify.py`, `test_auth_session.py` | Test / grant versus identity | Existing real-DB account/auth fixtures | Exact baseline style; extend identity-only v2 and legacy refusal before OTP consumption; no root creation on returning login |
| `backend/tests/conftest.py` and existing stock/action/dividend fixtures | Fixture / isolated real database | Current guarded test stack/session factory | Exact infrastructure; new root/closed fixtures must not loosen production/dev database guards |
| `frontend/src/hooks/usePortfolio.test.tsx`, `useStockTrade.test.tsx`, `useEventHistory.test.tsx` and adjacent API/page tests | Test / delayed responses and protected rendering | Existing test suites for these modules | Exact tool/style; add user+root transitions and original-attempt assertions, do not substitute direct cache setup for real behavior |
| Proposed `frontend/e2e/portfolio-ownership.spec.ts` | Test / preserved investing journey | Existing `stock-trades.spec.ts`, `dividends-history.spec.ts` | Role match, MISSING file: scoped routes, long names, unavailable states, original receipts and private History with synthetic data |
| Proposed `deploy/tests/test-portfolio-recovery-contracts.py` | Test / revision and restore contract | `test-stock-recovery-contracts.py:37–74`; existing `ops-fixtures.py` | Role match, MISSING file: explicit intermediate refusal and exact final active/closed ownership roundtrip |
| `deploy/tests/test-stock-recovery-contracts.py`, `test-ci-ops.py`, `ops-fixtures.py`, `test-db-operations.sh`, `test-rollback-db-security.sh` | Test/harness / serial real migration, roles, TLS and recovery | Existing owned disposable campaigns | Exact harness family; keep original archive/source binding and old 0008 lane distinct from new final proof |

## Pattern Assignments

### 1. Compound lineage and immutable SQL authority

**Read:** `backend/app/models/stock_execution.py:27–34` and
`backend/app/models/dividend.py:40–72`. The existing model already enforces
cause tuples with one composite FK:

```python
ForeignKeyConstraint(
    ["trade_id", "coin_id", "user_id"],
    ["trades.id", "trades.coin_id", "trades.user_id"],
    name="fk_stock_fill_trade_owner_coin",
)
```

Extend the **same paired tuple** with portfolio identity in the new model/schema;
two independent FKs do not establish matching owner/root/cause. Keep existing
NUMERIC, UTC, identity and immutable payload patterns. Do not alter old migrations.

**Read new-migration analogs:** `0014_dividend_accounting.py:51–90` for concurrent
index preparation; lines 92–107 for unconditional mutation rejection; lines
374–440 for bound, instrument-gated SQL-owned cash effects. Its definer declares:

```sql
LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path=pg_catalog,public,pg_temp AS $apply$
```

Current lines 393/432 select/update cash by `user_id`; these are a **negative
scope example**, not safe copy targets after multiple roots. Retain narrow
definer ownership, argument validation, bound invocation and final guard order,
but derive/validate the exact portfolio from immutable entitlement lineage.
The finite immutable association exception has **no existing safe analog**.

### 2. Authenticated thin routes, exact target locks and original replay

**Identity analog:** `backend/app/core/deps.py:82–117` resolves User through
the session, then exports `CurrentUserDep`/`DbDep`/`CsrfDep`. Keep authentication
independent of Account. New owned-active resolution composes after that identity.

**Private route analog:** `backend/app/api/v1/stock_trades.py:20–54,90–132`.

```python
PRIVATE = {"Cache-Control": "no-store", "Vary": "Cookie, Authorization"}
router = APIRouter(tags=["stock trades"], route_class=PrivateRoute)
```

Its wrapper covers success, validation/domain refusal and unknown errors, and
only logs exception type. Reuse this full behavior for private versioned routes;
services retain transactions and routers map fixed codes. Wire with the small
`include_router` style in `backend/app/api/v1/router.py:14–24`.

**Execution analogs:** `services/trading.py:247–276` uses account→holding locks;
`services/stock_trading.py:298–320` uses original replay, instrument gate, account
lock and replay recheck. Preserve that distinction, but replace user-only account
and holding selection with exact root+owner predicates and post-wait lifecycle
checks. Do not call a portfolio row lock before a stock instrument lock merely
because the crypto path does so.

**Retry analog:** `services/trade_idempotency.py:13–20`:

```python
select(Trade)
.where(Trade.user_id == user_id, Trade.idempotency_key == key)
.execution_options(populate_existing=True)
```

Keep this user-global key lookup; extend `require_same_order` (lines 23–36) with
portfolio equality. Ownership/active authorization precedes normal receipt
access, but a matching active-root receipt is still replayed before new market
checks. Cross-root keys conflict; original keys and saved fills are not rewritten.

### 3. Global causal order with root-scoped reads and worker effects

**Journal analog:** `stock_ownership.py:86–119` owns the stable instrument lock
namespace and bounded waits. `assert_ownership_consistent`, lines 361–414, reads
the complete instrument journal in sequence order and cross-checks trade causes.
Keep global order/evidence while changing owner maps and cause checks to roots.

**Worker analog:** `corporate_actions.py:553–620` acquires the same gate before
full consistency and locked holders; `dividends.py:45–62,65–88` owns the short
transaction around a fixed SQL statement:

```python
async with db.begin():
    row = (await db.execute(text(statement), work)).one()
```

Preserve transaction ownership and sanitized domain errors. Add deterministic
root locks/rechecks without reversing instrument ordering. Do not stop at an
HTTP resolver: split/entitlement/payment/correction jobs also need exact root
and terminal lifecycle semantics.

**History analog:** `event_history.py:142–179` filters each source before bounded
lookahead and orders by a total seek tuple:

```python
stmt = stmt.order_by(
    sources.c.recorded_at.desc(), sources.c.kind_rank.desc(), sources.c.source_id.desc()
).limit(limit + 1)
```

Extend every UNION arm, later hydration (lines 184–305), original payment join,
and cursor payload with the requested root. Retain canonical JSON/base64/version
validation from lines 35–103; cursor encoding is not authorization. Preserve
valuation projection using actual `starting_cash` from `portfolio.py:65–95,133`.

### 4. Browser request identity, guarded projections and neutral context

**Client analog:** `frontend/src/api/stockTrades.ts:599–659` validates input,
uses `apiFetch`, `signal`, `cache: "no-store"`, validates response/order identity,
then checks cancellation before returning. Extend both request and response
identity with root rather than only changing the URL.

**Projection analog:** `hooks/usePortfolio.ts:252–278`:

```typescript
const key = useMemo(() => ["portfolio", email] as const, [email]);
const owner = client.getQueryCache().find({ queryKey: key, exact: true });
// After await: check session/lifecycle/serial and the same cache owner.
```

The current key is a **known scope gap to change**, not a sufficient new key.
Its WeakMap Guard (lines 21–55) also needs user+root partitioning; otherwise the
latest projected value/holdings map can cross roots even with a new query key.

**Attempt analog:** `useStockTrade.ts:561–585` captures original `attempt.body`,
auth version, cache owner and key, then checks `stillOwn()` before publishing a
fill. Extend immutable Attempt (line 22), query keys (310/323), context maps
(159–205) and all captured predicates with portfolio identity. Do not replace
the captured target with a global selected portfolio during retry. Event-History
guards/cursors/seen/invalidation follow `useEventHistory.ts:7–25,35–102`.

**Component analog:** `components/StockAttribution.tsx:13–25` is an existing
label/value/supporting-text group with current tokens and wrapping content.
Reuse its semantic layout, not its price-source copy or `role="note"` blindly.
The approved UI-SPEC defines the new neutral `Portfolio`/name text, safe states,
focus, scope, exact copy and native-zoom owner checkpoint. `AccountPage.tsx:17–22`
is the exact cash block to remove from identity-only UI; cash moves only to
appropriately scoped financial responses, never an invented default.

### 5. Exact supported-revision, privilege and real-fixture qualification

**Producer analog:** `deploy/backup-snapshot.py:412–425` admits exact revisions
before constructing column inventory; lines 522–563 verify shape, counts,
hashes, identities and financial invariants. `validate_dividend_functions`,
lines 196–209, compares exact function body hashes and metadata:

```python
require(isinstance(row['body'], str)
        and hashlib.sha256(row['body'].encode()).hexdigest() == body)
require({k: v for k, v in row.items() if k != 'body'} == expected)
```

Retain paired producer/consumer inventory in `backup-manifest.sql` and
`verify-restore.py`; add final root/lifecycle/cause/grant/function shapes and
test exact intermediate refusal. Unknown/staged revisions are not a wildcard
match for the newest supported contract. Existing identity sequence parsing
(snapshot lines 391–409) remains exact and allowlisted.

**Role analog:** `bootstrap-roles.sql:135–161` transfers known tables and identity
dependencies, revokes broad access, then reapplies explicit grants. Line 156's
table-level Account UPDATE must **not** be copied onto root metadata; final
authority needs the narrower reviewed column/function grants. Keep the existing
scheduler quantity-only holding privilege (line 231) and controlled definer
EXECUTE boundary rather than increasing privileges to resolve a new column error.

**Real-DB test analogs:** `backend/tests/test_stock_execution_migrations.py:12–70`
uses actual engine transactions, bound `text` SQL, and forced deferred-constraint
evaluation (`SET CONSTRAINTS ALL IMMEDIATE`). Extend this style for owner/root
tuples and immutable association negative cases. `test_stock_trading_concurrency.py`
uses independent sessions and `asyncio.gather` with actual cash/row/position
assertions; fake-DB counters cannot prove lifecycle/lock ordering.

**Offline contract analog:** `deploy/tests/test-stock-recovery-contracts.py:37–74`
loads real producer/consumer code and asserts malformed authority is refused
before a GRANT. Keep those source contracts separate from the real PostgreSQL
same-archive migration/roles/TLS/restore campaigns in the existing ops harness.

## Shared Patterns and Planner Rules

- Imports/layers: `app.models`, `app.services`, `app.schemas`, annotated shared
  dependencies; React `@/api`, `@/hooks`, `@/components` aliases. Routes stay thin;
  database transactions and final financial authority remain in services/SQL.
- Exact money and time: preserve existing Decimal/NUMERIC, UTC timestamps,
  string transport and existing formatter/math helpers. Association metadata is
  not permission to recalculate original fill/authority JSON or digest bytes.
- Server authorization: current session resolution is necessary but does not
  establish owned active root; every lookup, replay, query arm and original cause
  requires that same explicit target. Error responses must not enumerate another
  owner's or closed portfolio's private records.
- Query/attempt identity: query keys **and** hidden guard maps, seen sets,
  captured mutation arguments, cursor contexts and late-response checks must
  include root identity. Cancellation alone does not establish authorization.
- Migration stages 0015/0016/0017 are research proposals, not existing source.
  Migration-only admission/refusal and the runner-to-final path need explicit
  tests; final runnable support is a coordinated all-writer/recovery boundary.
- Every new missing test above needs an earlier Wave 0 creation/fixture owner;
  a command naming a proposed file is not already passing coverage.
- Preserve Phase 7's six unchecked outcomes and original campaign path. No
  market-provider, host rollout, package or stock-activation change is implied.

## No Safe Existing Analog / Mandatory New Proof

| New mechanism | Existing nearby code | Why direct copying is insufficient |
|---|---|---|
| Finite migrator-only NULL→correct-original-root immutable association | Current unconditional stock/dividend mutation triggers | No safe existing exception; prove caller identity, unchanged economics, single association and final removal under real roles |
| Migration-only schema admission and resumable finalization | Current explicit final revision allowlists | Refusal alone can strand migrations; prove reviewed migrator path reaches final without ordinary service/bootstrap access |
| Per-root frozen unit/closure reconstruction | Current instrument-global journal and user-based maps | Skipping closed holders cannot prove consistency; prove same-user sibling split/dividend/correction behavior and terminal state |
| Versioned legacy/new split digest interpretation | Existing saved user-based digest material | Original bytes cannot be rewritten; new portfolio interpretation needs explicit versioning and exact replay fixtures |
| Root-aware identity-only v2/legacy retirement | Current cash-bearing `/me` and OTP verification | New wire contract and pre-consumption refusal must be specified/tested; existing `.one()` cash join is not a compatible zero/many identity path |
| Full exact final portfolio restore/rollback refusal | Current 0007–0014 exact manifests and retained campaigns | Root/lifecycle/grant identities and unsafe old-app refusal need new explicit inventory and real cold-restore proof |

## Metadata

Search scope: backend models/services/core/API/migrations/tests, frontend API/
hooks/pages/components, deploy producer/bootstrap/contracts and existing ops
harness. Five strong pattern families were enough; no exhaustive scan or further
domain research was performed. Source anchors reflect the current planning base
and must be reread by the executor before editing. All proposed files remain
unimplemented and untested. Optional descriptions/management remain Phase 13;
public deletion remains Phase 14. Only this pattern-map file was written.
