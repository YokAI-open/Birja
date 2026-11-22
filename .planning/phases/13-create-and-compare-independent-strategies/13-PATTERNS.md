# Phase 13: Create and Compare Independent Strategies - Pattern Map

**Mapped:** 2026-11-18
**Files analyzed:** 32 implementation/test ownership groups below (a group may contain several files)
**Analogs found:** 29 / 32 groups; three new capabilities have only partial scaffolding

This is a read-only source map for the planner. Proposed new filenames are recommendations, not existing APIs. CONTEXT and UI-SPEC govern behavior. Phase12 is complete; existing0015–0017 migrations, SQL asset hashes and retained fingerprints remain immutable. Do not reopen completed plans or change runtime state to perform this map.

## File Classification

| # | New/Modified File or tightly coupled ownership group | Role | Data Flow | Closest actual analog | Match Quality |
|---|---|---|---|---|---|
| 1 | `backend/app/models/user.py` | model | CRUD | Existing `Account` lines34–53 | exact |
| 2 | New creation journal and initialization provenance models; `models/__init__.py` registration | model | append-only CRUD | `Account` identity/owner constraints; `models/dividend.py` causal ledgers | role-match |
| 3 | New `backend/alembic/versions/0018_*.py` and successor SQL assets | migration | batch | `0017_portfolio_ownership.py` checked SQL loader and definer installation | role-match |
| 4 | New SQL canonical name/description helpers, creation/initialization/metadata entry points | service | request-response | No existing owner-locking creation authority;0017 lock routine supplies hardening scaffold only | no close analog |
| 5 | `backend/app/services/accounts.py` and signup integration in `services/auth.py` | service | CRUD | `get_or_create_user` lines13–36 | exact |
| 6 | `backend/app/services/portfolios.py` creation/metadata management | service | CRUD | `resolve_owned_active_portfolio` lines19–33; signup caller-owned transaction | role-match |
| 7 | `backend/app/schemas/portfolios.py` management/overview schemas | model | transform | `PortfolioId` lines7–11; existing `schemas/portfolio.py` statement schema | role-match |
| 8 | `backend/app/api/v2/portfolios.py` create/patch/metadata/overview | route | request-response | Existing same-file routes lines15–34 | exact |
| 9 | Management private response wrapper; `core/config.py` quota settings and existing rate-limit service integration | middleware/config | request-response | `api/v1/stock_trades.py:PrivateRoute`; `services/ratelimit.py` | role-match |
| 10 | `backend/app/services/portfolio.py` shared batch loader/assembler; optional extracted module | service | batch/transform | `get_portfolio` lines49–183 | role-match |
| 11 | `backend/app/db/schema_contract.py` | config | request-response | `require_schema`; current `portfolio` admission is exactly0017 | exact |
| 12 | `backend/app/db/{portfolio_migrate,portfolio_bootstrap,dev_bootstrap}.py` | service/config | batch | Existing source hashes, migrator proof, preflight and grants | exact |
| 13 | `deploy/db/bootstrap-roles.sql` | config | batch | Current role bootstrap plus `portfolio_bootstrap.GRANTS_SQL` | exact |
| 14 | `frontend/src/api/portfolios.ts` and management/overview strict parsers; statement parser if extended | utility | request-response/transform | `parsePortfolios` lines14–39; `api/portfolio.ts` | exact |
| 15 | New `frontend/src/hooks/usePortfolioManagement.ts` (or split create/edit/overview hooks) | hook | request-response/event-driven | `usePortfolioTarget` query guard and `useTrade` immutable-attempt state | role-match |
| 16 | New bounded owner-bound same-tab creation recovery utility | store | file-I/O/event-driven | No existing persisted original creation attempt | no close analog |
| 17 | New metadata cross-tab invalidation utility/hook | hook | pub-sub | Owner/session guards exist; no existing identity-only management broadcast protocol | no close analog |
| 18 | `frontend/src/hooks/usePortfolioTarget.ts` | hook | request-response | Same file lines105–165 | exact |
| 19 | `frontend/src/hooks/{useTrade,useStockTrade,useQuote,usePortfolio,useEventHistory,useHistory}.ts` | hook | event-driven/request-response | Existing target-scoped hooks and mutation invalidations | exact |
| 20 | New `frontend/src/pages/PortfoliosPage.tsx` | component | request-response | `PortfolioPage.tsx` loading/refetch/error/freshness presentation | role-match |
| 21 | New create/edit metadata form component(s) | component | event-driven | Local Button/Input/Card source and existing forms; UI-SPEC defines new inline interaction | role-match |
| 22 | `frontend/src/pages/PortfolioPage.tsx`, `components/PortfolioContext.tsx`, selector component | component | event-driven | Existing context and statement presentation | exact |
| 23 | `frontend/src/App.tsx`, `components/PortfolioTargetBoundary.tsx`, `pages/MarketsPage.tsx` | route/component | event-driven | Existing explicit routes, legacy refusal, heading focus | exact |
| 24 | New backend creation/metadata/API/concurrency tests; existing identity tests | test | CRUD/request-response | `test_portfolio_identity.py`, `test_portfolio_identity_api.py`, `test_portfolio_authority.py` | role-match |
| 25 | New metadata authority/migration tests and `tests/portfolio_fixtures.py` | test | batch/CRUD | Guarded disposable schema and independent economic snapshots | role-match |
| 26 | Overview/detail parity tests; same-asset API-created book and event tests | test | batch/event-driven | `test_portfolio_valuation.py`, crypto/stock API, dividend/split tests | role-match |
| 27 | Frontend parser/hook/page/form tests and target fixtures | test | transform/event-driven | `portfolioReads.test.ts`, `usePortfolioTarget.test.tsx`, portfolio hook/page tests | role-match |
| 28 | New browser management journey and `frontend/e2e/portfolio-browser-fixture.py` | test | request-response/event-driven | `portfolio-ownership.spec.ts`, `portfolio-history.spec.ts` | role-match |
| 29 | `deploy/{backup-snapshot.py,verify-restore.py,recovery-bundle.sh}` | service | file-I/O/batch | Existing portfolio manifest validation, payload producer/consumer and quarantine regrant | exact |
| 30 | `deploy/tests/{portfolio-sources.py,portfolio-retained-sources.json,portfolio-execution-fixture.py}` and new recovery fixture | config/test | file-I/O/batch | Exact source/schema dispatcher; retained0017 fixture/profile | exact |
| 31 | `deploy/tests/{run-portfolio-validation.py,test-portfolio-recovery-contracts.py,test-portfolio-migration-runner.py}` plus existing operations/TLS/cold/browser runners | test | batch | Existing same-source serial recovery campaign | exact |
| 32 | `.github/workflows/ci.yml`, critical-coverage config/test and command documentation when changed | config/test | batch | `backend/tests/test_critical_coverage_config.py:CRITICAL_MODULES` | exact |

Rows group ownership to avoid inventing unnecessary modules. Planner must enumerate final concrete files in plans and update13-VALIDATION with final test IDs. Existing financial services need changes only where shared loading/invalidation or new-root integration requires them.

## Pattern Assignments

### 1. Financial root, initialization and management authority (groups1–6,24–26)

**Actual model scaffold:** `backend/app/models/user.py:34–50`:

```python
class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        UniqueConstraint("id", "user_id", name="uq_accounts_id_user"),
        CheckConstraint("cash >= 0", name="cash_non_negative"),
        CheckConstraint("starting_cash >= 0", name="starting_cash_non_negative"),
        CheckConstraint("cash = round(cash, 2)", name="cash_cents"),
    )
    # Existing columns use BigInteger/Identity(always=True), Text,
    # Numeric(20, 8), DateTime(timezone=True).
```

Retain the paired `(id,user_id)` unique root and composite owner foreign-key approach for the journal. Add non-null defaulted description and canonical name key with source-owned checks; journal has permanent owner/key and portfolio uniqueness, immutable amount/payload/provenance, UTC timestamps and indexed real lookup paths. Existing economic snapshots must account explicitly for added metadata without excluding money or weakening legacy comparison.

**Signup winner to preserve:** `backend/app/services/accounts.py:13–24,34–36`:

```python
async def get_or_create_user(db: AsyncSession, email: str) -> tuple[int, bool]:
    stmt = (
        pg_insert(User)
        .values(email=email)
        .on_conflict_do_nothing(index_elements=["email"])
        .returning(User.id)
    )
    new_id = (await db.execute(stmt)).scalar_one_or_none()
    # Only the new_id branch currently inserts Account, then flushes.
    # Returning email lookup returns (existing, False).
```

Replace only that winner branch's direct `Account` insertion with initial authority in the SAME caller-owned auth transaction. Do not commit in the helper or infer initialization from active account count. Backfill a latch for every existing user including zero-book identities. The initial authority is separate from public explicit creation.

**Ownership refusal to reuse:** `backend/app/services/portfolios.py:24–33`:

```python
select(Account.id, Account.user_id).where(
    Account.id == portfolio_id,
    Account.user_id == user.id,
    Account.closed_at.is_(None),
)
# row is None:
raise HTTPException(status_code=404, detail={"code": "portfolio_unavailable"})
```

This resolver is a read check, not a substitute for transactional authority. The new definer must independently serialize user → target and validate owned active state. Creation locks `users`, checks successful original owner/key replay BEFORE current name/cap/daily quota, then inserts root+journal atomically. A rename cannot change retry identity/payload; a closed replay cannot recreate. Never grant ordinary users UPDATE merely to obtain a row lock. Metadata updates only name/key/description; ordinary account INSERT must be revoked after signup and explicit create use authority.

**Hardening scaffold only:** `backend/alembic/versions/0017_portfolio_ownership.py:113–129`:

```sql
CREATE FUNCTION public.lock_stock_portfolio_roots(p_coin bigint)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,public,pg_temp AS $locks$
-- Existing body validates the stock, takes its instrument advisory gate,
-- then locks matching account roots ORDER BY a.id FOR UPDATE.
ALTER FUNCTION public.lock_stock_portfolio_roots(bigint) OWNER TO birja_migrator;
REVOKE ALL ON FUNCTION public.lock_stock_portfolio_roots(bigint) FROM PUBLIC;
```

Do not call this stock helper for creation or claim it locks a User. Copy owner/search-path/ACL hardening into NEW assets and review caller authority explicitly; caller-controlled GUCs, SET ROLE and request owners are not authentication. Management takes no stock gate. Financial instrument → ordered account → holding order stays intact. Use existing local timeout/error-redaction discipline.

**Test scaffold:** `backend/tests/test_portfolio_identity.py:89–103` creates eight separate sessions with `asyncio.gather`, commits each signup, asserts one creator, one user and one10000 grant. Lines106–118 explicitly roll back signup and prove both user and root disappeared. Extend with restricted app-role calls, same/different-key races, slot10 races, name races, initialization backfill and rollback, direct INSERT denial, immutable journal/baseline and closed/name-reused replays. Existing `test_portfolio_authority.py:1–90` uses fixed expected role/constraint sets rather than live-derived expected values.

### 2. Strict private API and metadata transport (groups7–9,14,24,27)

**Imports and thin route:** `backend/app/api/v2/portfolios.py:3–12,31–34`:

```python
from app.api.v1.stock_trades import PrivateRoute
from app.core.deps import CurrentUserDep, DbDep, OwnedActivePortfolioDep, SettingsDep
from app.services.portfolio import get_portfolio

async def portfolio(
    portfolio: OwnedActivePortfolioDep, db: DbDep, settings: SettingsDep
) -> PortfolioOut:
    return PortfolioOut.from_value(await get_portfolio(db, portfolio=portfolio, settings=settings))
```

Reuse dependency aliases, explicit response models and service ownership of transactions. Mutations require CSRF. Add static `/overview` before `/{portfolio_id}`. Provide deliberate management metadata GET/response instead of silently broadening existing exact identity shape. `api/v1/stock_trades.py:18–33` sets `Cache-Control: no-store` and `Vary: Cookie, Authorization` and wraps HTTP/validation/unexpected failures; factor/reuse that mechanism with management-specific unknown-result wording. Unknown500/transport responses do not prove that creation failed.

**Bigint schema:** `backend/app/schemas/portfolios.py:7–11`:

```python
PortfolioId = Annotated[
    int,
    Field(gt=0, le=9223372036854775807),
    PlainSerializer(str, return_type=str, when_used="json"),
]
```

New request schemas forbid extras/null/empty PATCH and client financial/owner fields. PATCH absence differs from empty description. New management schemas expose canonical returned metadata; SQL is authoritative for NFC/casefold using the specified PostgreSQL collation, not Python/browser lower(). Adopt the exact research/UI Unicode controls, trim, scalar bounds and newline rules. Idempotency-Key is canonical lowercase UUIDv4. Extend bounded user/IP attempt limits and serialized successful-new-identity daily quota; replay consumes no new identity quota.

**Strict browser parser:** `frontend/src/api/portfolios.ts:14–37`:

```typescript
if (!Array.isArray(body) || body.length > 10) throw new Error("Unexpected portfolio metadata");
// For every entry:
Object.keys(item).length !== 2 ||
!isPortfolioId(item.id) ||
BigInt(item.id) <= previous
// Returned entries and list are Object.freeze(...).
```

Keep `parsePortfolios` exactly `{id,name}`. Reuse `isPortfolioId` lines6–11 and frozen validated data for new separately named parsers. New overview parses string money/incomplete/timestamp/authority contracts from existing `api/portfolio.ts`; do not compute money/returns in JS or accept NaN/numeric money. Description needs its own shape validator, not reuse of name trim. Tests should include malformed, over-cap, unordered, duplicate, huge IDs, Unicode/astral/control/null and omitted-versus-empty payloads.

### 3. Shared exact valuation rather than per-book service loops (groups10,19,20,26)

**Primary analog:** `backend/app/services/portfolio.py:get_portfolio` lines49–183. This is the current financial source to refactor, not a completed multi-book loader.

The consistent query at lines75–114 selects account cash/baseline alongside holdings, price, quote and authority. The positive-quantity condition stays in the outer join:

```python
and_(
    Holding.portfolio_id == Account.id,
    Holding.user_id == Account.user_id,
    Holding.quantity > 0,
)
```

Keep cash-only books. Change proof correlation at lines62–73 from captured single portfolio to EACH selected account: original quote-generation rights must remain root/user scoped. Lines115–135 sample after awaited reads and recheck current stock authority before `value_stock`; share that bounded recheck and timestamp across the batch. Never parallelize queries on one AsyncSession. Do not cache stock marks by coin alone when original proof differs by portfolio; use `(portfolio_id, coin_id)` or equivalent scoped assembly.

**Core exact assembler:** lines142–156:

```python
PositionInput(
    row.symbol, row.name, row.is_active, row.quantity, row.cost_basis,
    stock.mid if stock is not None else row.mid,
    stock.mark.event_at if stock is not None else row.as_of,
    asset_class=row.asset_class, coin_id=str(row.coin_id),
    provider_asset_id=row.provider_asset_id,
    units_safe=stock.mark.units_safe if stock is not None else True,
)
value = calculate_portfolio(rows[0].cash, rows[0].starting_cash, positions)
```

Extract common per-book assembly, retain `portfolio_math.calculate_portfolio` and `stock_valuation.value_stock`, and make detail+overview call it. Never loop existing `get_portfolio` for10 books. At lines174–182 output includes immutable root ID/name, exact calculated fields, `valued_at`, oldest `prices_as_of`, fresh/stale thresholds. Overview adds canonical metadata and each root's own completeness/known value/returns; there is no pooled total. Enforce corrupted11-root refusal rather than LIMIT10 truncation.

`backend/tests/test_portfolio_valuation.py` supplies named tests for unequal baselines/same-symbol siblings (25), cash-only/zero-active (63), unpriced incomplete (76), stock midpoint independent cash (101), uncertain mark unavailable returns (112), dated source time (127). Extend with identical-time detail/overview equality, bounded query counts and stock authority changes while awaiting. New same-asset crypto/stock and dividends/corrections/splits must start with API-created roots, not solely privileged fixture inserts.

### 4. Owner/session, unresolved attempts and UI composition (groups15–23,27–28)

**Owner/serial query guard:** `frontend/src/hooks/usePortfolioTarget.ts:108–139` uses owner-keyed TanStack Query, `retry:false`,10s stale time, `gcTime:0`, focus refresh, consumed abort signal and checks captured session, serial and query object identity before publication. Reuse these for management/overview, but creation has an OWNER/session scope even when there are zero targets. Do not require a selected financial target to fetch/create on `/portfolios`.

**Critical rename integration:** same file lines153–162:

```typescript
isCurrent: () => {
  const query = client.getQueryCache().find({ queryKey: key, exact: true });
  const values = query?.state.data as readonly PortfolioSummary[] | undefined;
  return activeScopes.has(scope) && who(client) === owner &&
    guard.session === session && query?.state.status === "success" &&
    values?.some((p) => p.id === selected.id && p.name === selected.name) === true;
}
```

Name refresh currently revokes actionability. Coordinate preview revocation and unresolved-attempt retention; do not simply delete the name check without reviewing consumers, or discard an unknown order when its captured name becomes stale. Original ID/payload/label survive rename and switching.

**Attempt scaffold:** `frontend/src/hooks/useTrade.ts:60–76,98–105`:

```typescript
const attempt = Object.freeze({
  portfolio_id: target.portfolioId,
  order: Object.freeze({ ...order }),
  expected_mid: expectedMid,
  idempotency_key: idempotencyKey,
});
// current state rejects a different same-root unresolved original attempt.
// catch distinguishes a definitive terminal ApiError from an unknown result:
client.setQueryData<State>(key, {
  phase: refused ? "refused" : "unknown",
  attempt: refused ? null : attempt,
  error: failure,
});
```

Lines86–95 invalidate exact financial roots and recheck scope after invalidation; lines118–130 guard callbacks; reset refuses submitting/unknown. Use these principles for creation with creation-specific terminal errors and replay semantics. Add overview invalidation to completed crypto/stock/event paths (`useStockTrade.ts:661–669` is the stock counterpart). Do not copy financial target keys into owner-wide creation state. Existing in-memory trade retention does NOT supply sessionStorage recovery or a broadcast protocol.

New creation recovery stores one strictly bounded opaque-owner/session-bound original key/payload before first POST. Failure to persist blocks submission with retained draft. Refresh restores read-only unknown attempt and explicit Retry, never automatic POST. Closing does not cancel/reset; definitive resolution/logout/owner change clears. Never put tokens, financial data, email, attempt keys or metadata into cross-tab messages/URLs/logs. New cross-tab messages contain only minimal opaque identity invalidation and trigger authoritative refetch; retain edit drafts and signal stale state.

**Actual page composition:** `frontend/src/pages/PortfolioPage.tsx:1–28` imports aliased local UI components, `usePortfolio`, `useNow`, `formatUsd` and `PortfolioContext`; duplicate refresh is prevented by `isFetching` and `cancelRefetch:false`. Lines49–93 distinguish loading, initial failure and failed-refresh retained-safe data. Reuse its source-time/freshness components and exact formatters for overview; reuse `usePortfolio` projection safety rather than rendering raw cached values indefinitely.

**Route/focus owner:** `frontend/src/App.tsx:75–113` contains identity-mounted navigation memory and h1 focus via pathname-triggered effect plus MutationObserver. Lines135–146 place financial routes under `PortfolioTargetBoundary` and currently put bare `/portfolios` under that boundary too. Replace only the bare route with signed-in overview, preserve explicit child routes and unavailable-ID refusal, make main Portfolio tab Portfolios. Native select changes draft choice; Open navigates to explicit detail ID and never carries an order ticket across roots. Forms are inline cards with local Button/Input/Card and labeled textarea; no new dialog or UI package. Follow approved UI-SPEC for responsive semantic table/cards, wrapped escaped metadata, focus/errors, cap/empty and unknown states.

Use `frontend/src/test/{portfolioTargetFixture,portfolioFixtures}.ts` and hook/page suites for owner/late-response/rename tests. Browser management extends the actual `frontend/e2e/portfolio-ownership.spec.ts` and disposable `portfolio-browser-fixture.py` pattern with first create, rename/description clear, Unicode, keyboard explicit switch, lost response+reload original retry, cross-tab and independent same-asset events. Actual desktop native200% zoom remains owner UAT, not CSS emulation evidence.

### 5. Immutable migration, authority and recovery profiles (groups3,11–13,25,29–32)

**Migration source pinning:** `backend/alembic/versions/0017_portfolio_ownership.py:70–77` reads fixed SQL bytes, compares SHA256 and installs parsed statements. Copy this into a NEW revision/SQL asset. Do not change the old loader, assets or expected digest. `backend/app/db/portfolio_migrate.py:38,47,114` separates `require_source`, `require_migrator` and `migrate`; extend source-qualified final revision/profile without relabeling old0017 as the new schema. `schema_contract.py` currently admits portfolio consumers only at0017; runnable admission must not accept partially enforced expansion state.

**Exact ordinary grants:** `backend/app/db/portfolio_bootstrap.py:158–170` currently contains:

```sql
REVOKE ALL ON public.accounts,public.holdings,public.portfolio_stock_closures
 FROM PUBLIC,birja_app,birja_scheduler;
REVOKE UPDATE(id,user_id,cash,starting_cash,created_at,name,closed_at)
 ON public.accounts FROM PUBLIC,birja_app,birja_scheduler;
GRANT SELECT,INSERT ON public.accounts,public.holdings TO birja_app;
GRANT UPDATE(cash) ON public.accounts TO birja_app;
GRANT UPDATE(quantity,cost_basis) ON public.holdings TO birja_app;
```

The successor profile must remove ordinary accounts INSERT, revoke metadata/journal/latch mutation, separately authorize narrow definer execution and retain execution cash/holding permissions. Existing `GRANT SELECT,INSERT ON public.users` at129 does not authorize ordinary User row locking. Extend exact body/owner/ACL/search_path/trigger/column/sequence parity tests, and current fresh/upgraded TLS role proof. Keep0017 profile inventory intact rather than rewriting its expectations to current.

**Independent fixture scaffold:** `backend/tests/portfolio_fixtures.py:37–62` guards exact throwaway database/role before schema teardown and always restores genuine head. Lines65–83 compare all economic columns with explicit metadata removals. `LegacyBooks` lines87–97 retains unequal cash/baselines. New migration fixtures must preserve custom/zero baselines and all old economic/history bytes; never grant another10000 during backfill. Current fixture revision allow-list ends at17 and needs an intentional successor extension.

**Recovery ownership map:**

| Actual source | Reuse and required successor work |
|---|---|
| `deploy/tests/portfolio-sources.py:43–60` | `validate_matrix` pins current revision/program, immutable retained commit/tree/files/archive hashes; add authenticated retained0017 lane and new current source profile. Do not substitute mutable checkout bytes for retained proof. |
| Same file `63–79,87–99` | `source_archive` verifies archive hash; `qualified_revision` rejects mismatched consumer/schema. Extend explicit lanes, never weaken this refusal. |
| `deploy/verify-restore.py:52` | `PORTFOLIO_PAYLOAD_V1` is the old immutable inventory; introduce successor version and update package/verify/install/restore consumers together. |
| `deploy/verify-restore.py:384,495,502,613,1064` | `bundle_verify`, `verify_portfolio_inventory`, `bundle_package`, `bundle_install`, `restore_portfolio_authority` are the call chain to extend. |
| `deploy/backup-snapshot.py:707–710,828–830` | Separate pinned schema/authority/quarantined/no-ACL hashes; add independently reviewed successor constants/profile, retaining old values. |
| `deploy/tests/fixtures/portfolio-recovery-0017.json` | Preserve exact0017 fixture; add new reviewed fixture for metadata/journal/latch/routines and sequences, not database self-description accepted as expected data. |

Include new canonical metadata/journal/provenance in dump, manifest and exact restore checks, append-only negatives, sequence state, quarantine-before-regrant and source-qualified retained execution. Extend current/retained cold image transition, role, populated/fresh TLS and rollback consumers against the SAME checksum-bound archive and source. No package/dependency refresh is necessary. Existing issue35 risk hashes/expiry and Phase7 provider admission remain binding; creation itself does not poll providers or bypass admission. Preserve backup capacity guards as permanent retained evidence grows.

## Shared Patterns

- **Identity and authorization:** CurrentUserDep for owner identity; explicit owner+active resolver; private no-store/Vary success and failure. No implicit financial fallback or client-supplied owner authority.
- **Transactions and locks:** Signup unique-email winner retains caller transaction. Management user → target; financial instrument → ordered accounts → holdings. A new definer supplies User locking without broader runtime table privileges.
- **Precision and snapshots:** Decimal/NUMERIC and string monetary transport; one consistent financial snapshot, shared batch evidence, bounded safety recheck and exact per-root assembler. No browser arithmetic or pooled balance.
- **Browser publication:** Guard owner/session/query generation and consumed AbortSignal. Cancellation/navigation is not financial cancellation. Persist only the original creation recovery identity/payload; never replay automatically.
- **Errors:** Use explicit service/domain codes and management-specific messages; distinguish definitive refusal, replay conflict, closed original and ambiguous response. Redact SQL internals and honor bounded retry timing.
- **Tests and coverage:** Extend the current100% critical module inventory in CI and `backend/tests/test_critical_coverage_config.py` for every new financial/authorization module. Preserve existing entries. Use actual isolated PostgreSQL and restricted roles for grant/idempotency/concurrency; independent expected values; provider HTTP fakes only.

## No Analog Found

| Capability / proposed files | Role | Data Flow | Gap the planner must address |
|---|---|---|---|
| New owner-serialized creation/initialization/metadata SQL authority | service | CRUD | Existing stock gate helper neither locks User nor enforces permanent original creation replay, once-only latch, Unicode metadata authority or renewable quota. Needs new threat/role/concurrency tests. |
| New sessionStorage original creation recovery utility | store | file-I/O | Trade hooks retain memory only; must design strict bounded persisted attempt, opaque owner binding, storage failure and reload/clear behavior. |
| New identity-only cross-tab management invalidation | hook | pub-sub | Focus-refetch exists but is not immediate cross-tab metadata coherence. Requires new protocol cleanup, owner isolation and draft-staleness tests. |

## Metadata

**Analog search scope:** backend models/services/v2 routes/schemas/DB/migrations/tests; frontend API/hooks/pages/routes/fixtures/e2e; deploy recovery/source runners and CI critical inventory.
**Evidence strategy:** Five strong analog families above; grouped searches stop after sufficient actual call-chain evidence. Line references describe source inspected2026-11-18 and may move during implementation.
**Files scanned:** Bounded path/symbol search plus direct excerpts for primary analogs; not a full repository audit.
**Pattern extraction date:** 2026-11-18.
**Validation:** No source/test/DB/runtime/install/commit operations performed. Only this pattern map written. Planner owns final test IDs and13-VALIDATION updates.
