# Phase 14 — End Strategies Safely: Pattern Map

**Mapped:** 2026-11-19. Five strong analog families; source access read-only.
**Inputs:** approved requirements,14-RESEARCH/UI-SPEC/VALIDATION, current source.
No CONTEXT exists. Names of new files below are proposals for the planner to
allocate, not implemented contracts or owner-locked identifiers. No test run,
provider call, package installation or runtime operation was performed.

## File Classification

Grouped rows classify each named file in the group. Existing analogs are
role/data-flow matches; dedicated multi-instrument closure has no exact analog.

| Proposed new/modified file(s) | Role | Data flow | Closest analog / quality |
|---|---|---|---|
| `backend/app/services/portfolio_closure.py` (new proposed) | service/transaction authority | request-response, financial lifecycle | `services/portfolios.py`, `stock_ownership.py`; partial: combine disciplines, never copy single-instrument guard into a loop |
| Successor `backend/alembic/versions/0021_*.py` and `backend/alembic/sql/0021_*.sql` (names/revision count to lock in plans) | migrations/SQL authority | schema expansion, atomic lifecycle | immutable0018–0020 migrations/SQL; role-match |
| `backend/app/models/user.py`, `models/corporate_action.py` and proposed lifecycle model | model | retained relational evidence | existing Account/PortfolioStockClosure; role-match |
| `backend/app/db/portfolio_bootstrap.py`, `portfolio_migrate.py`, `schema_contract.py`, `dev_bootstrap.py` | admission/bootstrap | exact catalogue/ACL/source verification | existing independently versioned0020/0017 profiles; role-match |
| `backend/app/api/v2/portfolios.py`, `portfolio_management.py`, `backend/app/schemas/portfolios.py` | route/transport/schema | bounded private DELETE request-response | management POST/PATCH transport; strong role-match, dedicated DELETE parsing required |
| `backend/app/services/stock_ownership.py`, `corporate_actions.py`, `dividends.py`, `backend/app/tasks/dividends.py` | financial services/jobs | immutable event application, historical reconstruction | current gate/account and active-state fences; strong match; new terminal policy is additive |
| `backend/app/services/history.py`, `event_history.py`, `portfolio.py`, `trading.py`, `stock_trading.py`; v2 financial routes/dependencies as needed after inventory | service/route/authorization | private reads, original retries, final response | existing owned-active resolver, History recheck and valuation final FOR SHARE; strong match |
| `backend/tests/test_portfolio_closure_api.py`, `_events.py`, `_identity.py`, `_stocks.py`, `_races.py`, `_privacy.py` (new proposed) | tests | real API/DB/concurrency | existing `test_portfolio_management_api.py`, `_authority.py`, `_grants.py`, portfolio split/stock ownership/strategy event tests; role-match |
| `frontend/src/api/portfolioManagement.ts` or dedicated deletion transport | API/parser | strict request-response | existing metadata management transport; strong match |
| `frontend/src/lib/portfolioDeletionAttempt.ts` (new proposed) and tests | utility/recovery journal | same-tab metadata-only file-like storage | actual `portfolioCreationAttempt.ts`; strong match, separate storage key/intent |
| `frontend/src/hooks/usePortfolioDeletion.ts` and test (new proposed) | hook/state machine | TanStack mutation, unresolved original recovery | `usePortfolioManagement.ts`; strong match, owner-wide lifecycle separate from financial Outlet |
| `frontend/src/components/PortfolioDeleteForm.tsx` and test (new proposed) | component | explicit review/cancel/delete/recovery | `PortfolioMetadataForm.tsx`; role-match, use existing destructive Button |
| `frontend/src/hooks/usePortfolioTarget.ts`, `usePortfolioManagement.ts`, `frontend/src/lib/portfolioMetadataEvents.ts`, `frontend/src/components/PortfolioTargetBoundary.tsx`, financial read/trade hooks | hooks/boundary/advisory channel | revocable target authority and identity-only invalidation | actual target revision/session/current guards; strong match |
| `frontend/src/pages/PortfoliosPage.tsx`, current metadata route/shell/switcher, `frontend/src/App.tsx` if routing requires | page/routing | overview, independent recovery lease, zero-active entry | accepted Phase13 overview and metadata lifetime; strong match |
| `frontend/e2e/portfolio-deletion.spec.ts` (new proposed), `deploy/tests/run-stock-browser.py`, browser evidence contracts | full-stack tests/runner | isolated public API/UI journeys and source-bound captures | existing portfolio management e2e plus browser runner; strong match |
| `deploy/backup-snapshot.py`, `verify-restore.py` | recovery producer/consumer | authenticated archive, no-ACL quarantine/regrant | current V2/0020 plus frozen V1/0017 admission; strong match with separately versioned successor |
| `deploy/tests/portfolio-sources.py`, `portfolio-retained-sources.json`, `portfolio-smoke.py`, `portfolio-management-recovery-fixture.py`, successor recovery fixture JSON | dispatch/fixture/oracle | exact source/schema/image binding, cold restore | current fixed0017 and complete source dispatch; role-match; add qualified0020 retained lane |
| `deploy/tests/run-portfolio-validation.py`, recovery/validation/browser/CI/image contracts, DB/TLS/rollback compatibility scripts, `.github/workflows/ci.yml`, `backend/tests/test_critical_coverage_config.py`, `CLAUDE.md` command list | orchestration/contracts | serial source-bound security and seven-stage recovery | current Phase13 whole qualification; strong match, preserve61 critical modules |

All new test files must have explicit creation owners before a plan invokes
their selectors. Existing paths above are candidates, not permission for broad
rewrites. Planner must inventory exact normal route/service/query edges and
declare final file ownership/dependencies; tests and source touching shared
files cannot run as overlapping same-wave writers.

## Pattern Assignments

### 1. Lifecycle transactions and stock terminal evidence

**Analogs:** `backend/alembic/sql/0020_portfolio_management.sql:5–17,85–120`,
`backend/app/services/portfolios.py:80–128`,
`backend/app/services/stock_ownership.py:93–130,550–574,577–625`.

Existing fixed management authority:

```sql
CREATE FUNCTION public.create_portfolio(p_user bigint,p_key uuid,p_name text,p_description text)
RETURNS TABLE(portfolio_id bigint,name text,description text,creation_id bigint,replayed boolean)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,public,pg_temp SET lock_timeout='2s' AS $create$
-- ...
PERFORM u.id FROM public.users u WHERE u.id=p_user FOR NO KEY UPDATE;
```

Service invocation uses bound values, explicit commit, rollback/error translation
(`portfolios.py:85–100`):

```python
row = (
    await db.execute(
        text("SELECT * FROM public.create_portfolio(:u,:k,:n,:d)"),
        {"u": user.id, "k": key, "n": payload.name, "d": payload.description},
    )
).one()
await db.commit()
```

Copy safe search_path, trusted migrator ownership, revoke PUBLIC/service
EXECUTE before narrowly granting app signature, User **FOR NO KEY UPDATE**
management serialization, and service-controlled atomic commit. Do not copy
account-before-instrument ordering: creation/metadata never acquire stock gates.

The exact stable namespace and guard are `stock_ownership.py:100–125`:

```python
previous = db.info.get("stock_gate")
if previous is not None and previous[0] is tx and previous[1] != coin_id:
    raise OwnershipHeld("one_instrument_per_transaction")
# ...
text(
    "SELECT pg_advisory_xact_lock(hashtextextended("
    "'birja.stock.instrument:' || CAST(:coin AS text),0))"
)
```

**No exact multi-instrument analog exists.** Dedicated closure must collect
all historical stock instruments including sold-out positions; acquire sorted
gates in this namespace before account lock, recheck complete set after root
lock, and roll back/retry discovery if a first buy introduced a new instrument.
Never clear `db.info`, repeatedly call/relax the one-instrument financial guard,
or acquire a newly discovered gate while holding the account.

Use fresh `clock_timestamp()` after all locks (`stock_ownership.py:129–130`);
global instrument sequence tail and unit_epoch at that timestamp, not just
this portfolio's last movement. Existing closure validator requires
`account.closed_at == closure.closed_at` and
`closing_sequence == max(sequence where recorded_at <= closed_at)`
(`stock_ownership.py:556–574`); unit reconstruction excludes closed portfolios
from later epochs (`:609–615`). Preserve these invariants. Existing append
samples time again after awaited validation (`:296,329`) and stores
`recorded_at=now` (`:350`); research's equal/backward-clock fence is a new proof
obligation, not a demonstrated existing pre-wait timestamp bug.

Existing migration0020 authenticates SQL SHA before writes, requires session
`birja_migrator`, uses immutable0017 parser, and refuses downgrade before writes
(`backend/alembic/versions/0020_portfolio_management_authority.py:20–44`).
Use this pattern in new revisions without modifying0015–0020 bytes. Schema
expansion and data backfill stay separate. Do not invent past user confirmation
for historical closed fixture roots; successor provenance must distinguish them.

### 2. Thin authenticated private management transport

**Analogs:** `backend/app/api/v2/portfolios.py:90–143`,
`portfolio_management.py:29–63,93–119`, `services/portfolios.py:27–41,53–77`.

```python
router = APIRouter(prefix="/portfolios", tags=["portfolios"], route_class=ManagementRoute)
# Existing route dependencies:
user: CurrentUserDep,
csrf: CsrfDep,
db: DbDep,
```

`ManagementRoute` attaches PRIVATE headers to success and failures, redacts
validation and logs only exception type. Its body parser checks JSON media,
streams at most8192bytes and rejects duplicate keys. Reuse these properties;
add a dedicated strict DELETE intent schema/parser rather than extending the
existing `patch: bool` into a third ambiguous state. Lock exact success/error
contract before frontend consumers.

Existing owner-active resolution (`services/portfolios.py:32–41`):

```python
select(Account.id, Account.user_id).where(
    Account.id == portfolio_id,
    Account.user_id == user.id,
    Account.closed_at.is_(None),
)
# No result:
raise HTTPException(status_code=404, detail={"code": "portfolio_unavailable"})
```

This is correct for normal reads/actions, but **not** sufficient as DELETE's
only dependency: an already-closed original must allow minimal same-owner
acknowledgement without reopening metadata/finances. Foreign/missing remain
private unavailable. Confirmation name is review context, never authority;
compare canonical reviewed name under lock and map mismatch to dedicated409.
`_management_error` maps known SQL errors only and bounded contention to503
with Retry-After5 (`:53–77`); do not expose raw DB/provider detail.

### 3. Financial freeze, job fences and late-response privacy

**Analogs:** `stock_ownership.py` family above,
`backend/alembic/sql/0017_dividend_portfolio.sql:299,340,378,403`,
`backend/app/services/history.py:105–161`, `portfolio.py:177–195`.

Existing SQL payment paths lock/filter exact active account and condition cash
writes on `closed_at IS NULL`. Keep that authoritative recheck for work selected
before closure; active-only batch selection is not a transaction fence. A
single immutable lifecycle/policy record can explain future/unpaid skipped
effects from retained causal rows; no unbounded future-event×closed-book job
and no later financial History rows belong in a frozen portfolio.

History currently checks lifecycle before and after hydrate:

```python
await validate_portfolio_read(db, portfolio)
# deterministic seek query and response construction
await validate_portfolio_read(db, portfolio)
return HistoryPage(items=items, next_cursor=next_cursor)
```

For complete late-read overlap tests the stronger available pattern is
valuation's final shared account locks, retained through response transaction:

```python
current_ids = (
    root_query.order_by(Account.id).limit(11).with_for_update(read=True, of=Account).subquery()
)
```

Plan route→service→query inventory for detail/holdings, both previews/execution
and original idempotent retries, legacy+mixed History/cursors and original
event/payment references. Existing stock/cash route authorization cannot be
assumed to cover every original-reference path. Assert no new closed financial
response after a linearized final fence; do not claim deletion erases bytes
already delivered to a remote browser.

### 4. Metadata-only original recovery and revocable browser targets

**Analogs:** `frontend/src/lib/portfolioCreationAttempt.ts:7–120`,
`hooks/usePortfolioManagement.ts:125,181–200,376–475`,
`hooks/usePortfolioTarget.ts:8–44,73–159,163–200`,
`lib/portfolioMetadataEvents.ts:9–51`,
`components/PortfolioTargetBoundary.tsx:18–58,78–118`,
`PortfolioMetadataForm.tsx:14–65,79–104`.

Creation recovery validates exact metadata shape, limits storage, hashes opaque
nonce+owner binding, verifies current owner before writes, refuses overwriting
another immutable original, and reads back the persisted bytes before send:

```typescript
sessionStorage.setItem(CREATION_STORAGE_KEY, encoded);
if (sessionStorage.getItem(CREATION_STORAGE_KEY) !== encoded) throw storageError();
captured.attempt = attempt;
```

Copy discipline into a **separate** deletion marker/storage key. Store one
owner/tab original ID/reviewed name/versioned policy only; no finances/tokens,
and no second deletion overwrites unknown original. Storage failure refuses
before DELETE. Explicit Check deletion result replays the same original intent;
reload/focus must not automatically mutate. Other verified portfolios remain
tradable while one deletion is unknown.

Existing metadata-only route lease lives **outside** revocable financial Outlet
(`usePortfolioManagement.ts:125`, boundary`:21`); use that lifetime so masking
financial subtree cannot destroy deletion recovery UI. Existing captures carry
owner/session/revision/route scope and `isCurrent`; keep checks at invocation
and after every auth/CSRF/network/storage await, including late known refusals.
Use TanStack Query/mutations with no automatic mutation retry.

Identity-only cross-tab validation (`portfolioMetadataEvents.ts:14–19`):

```typescript
Object.keys(v).sort().join() !== "portfolioId,scope"
// accepted event:
return Object.freeze({ scope: v.scope, portfolioId: v.portfolioId });
```

Current target listener increments `scope.authority.revision` before
authoritative refetch (`usePortfolioTarget.ts:151–156`). Lifecycle invalidation
must also quarantine root money/read/previews/actions and prevent a late fetch
from republishing them. Broadcast is advisory identity, never owner proof.
Retain window-focus fallback and clean subscriptions/logout/session epochs.

Boundary currently renders financial Outlet only when ready; unavailable state
inspects **only a boolean** unresolved old-order existence, not its amount/key
or a retry button. Preserve this privacy. Known deletion returns to overview
without selecting a sibling; authoritative zero stays signed in/Create and
never initializes from a read. Name reuse creates a new ID, not restored scope.

Metadata form supplies existing inline Card/Button/error/focus patterns. Use
new named effect disclosure and safe Cancel-focused review specified by14UI;
do not add a dialog package or infer success from a promise merely resolving
(`PortfolioMetadataForm.tsx:61–64` already warns about that distinction).

### 5. Versioned exact recovery and whole qualification

**Analogs:** `deploy/tests/portfolio-sources.py:32–35,131–185,188–218,252–298`,
`portfolio-retained-sources.json:3–6,29–35`,
`deploy/tests/run-portfolio-validation.py:19–43`,
`backend/app/db/portfolio_bootstrap.py:189–341`;
producer/consumer independently versioned payload/authority families.

Current matrix marks0020/V2 as current, complete0017fixedsource as retained.
Successor must add qualified0020source
`9527e358bc6953cec7580043703324db194ba396` as immutable retained, while
preserving complete0017source`4b4320b4cc373268a8d598612a563cd5ef199700`
and0007–0014 lanes. Existing producer supported revision/table/column/sequence
inventory, consumer exact member validation/quarantine, application admission
and role grants all need explicit new version; do not reinterpret missing V1/V2
fields as valid successor lifecycle evidence.

Exact image reuse compares the whole binding (`portfolio-sources.py:204–209`):

```python
actual = image_binding(inspect, source_commit=expected["source_commit"],
                       app_tree=expected["app_tree"], context_sha256=expected["context_sha256"])
if actual != expected:
    raise ValueError("immutable image/config/rootfs mismatch")
return expected["id"]
```

Keep private campaign image IDs/scoped aliases, refuse lost/changed IDs and
never replace with RootFS-equivalence fallback. Source archive authenticated
before import; no retained fixture importing current service overlay.

Existing whole runner's archive path is Phase13-specific; new campaign must
use a distinct exclusive Phase14 path, preserving qualified Phase13archive.
Seven stage families remain image transition, retained roundtrip, successor
current cold, roles, upgradedTLS, freshTLS parity and selected rollback/refusal.
First run whole all-security successfully, then whole recovery at frozen source;
partial diagnostics cannot combine into a final pass. Plan preflight exact
stripped child PATH including`/usr/sbin`, existing tools, schema/fixture tails,
resource ownership, authenticated images and archive/source guards before long
runs. Durable one-shot PID/start/log/status/exit receipts prevent status-message
interruption from restarting campaigns. Never clean borrowed validated stacks.

## Shared Patterns and Limits

- Server CurrentUser+CSRF establishes intent authority; storage/name/broadcast
  never does. IDs and money remain strings in JSON; Decimal/NUMERIC unchanged.
- SQLAlchemy bound parameters, strict Pydantic/schema parsing, no user-generated
  HTML, exact safe error codes and PRIVATE/no-store responses.
- Frozen financial rows are not erased/reopened/liquidated. No transfer/reset,
  purge/trash/undo/export or provider activation enters this phase.
- Financial and management locks need a combined tested order, not a textual
  copy of one side. Explicit race/clock/sold-out tests precede final SQL pins.
- New critical modules join100% gate without removing61 existing modules.
- All backend pytest/DB/browser/ops share one exclusive serial disposable lane;
  frontend pure units/offline contracts may overlap only with disjoint ownership.
- Prior exact0020/V2 and0017/V1 literals, migrations and profiles stay immutable.
  New successor does not rewrite old fingerprints to accept new authority.

## No Exact Analog Found

| Proposed responsibility | Role/data flow | Why new proof is required |
|---|---|---|
| Dedicated multi-instrument public closure | financial lifecycle transaction | Existing guard intentionally permits one stock per transaction; closure must collect/recheck all historical stocks and serialize first-buy races without weakening it. |
| Immutable universal lifecycle/policy record and skipped-effect interpretation | retained causal audit | Existing per-stock closure exists, but no universal public deletion receipt/policy covers crypto-only/empty roots and unpaid future effects. |
| Strict across-closure clock ordering | financial temporal fence | Current writers sample after awaits, but equal/backward clock cases across global sibling stock history require dedicated refusal/retry proof. |
| Successor retained0020 dispatch | authenticated recovery |0020is currently live-source fixture; complete qualified historical source lane must be added independently. |

## Metadata

Search scope: relevant service/API/model/migration/SQL, frontend management/
target/recovery/boundary, and recovery dispatcher/runner paths. Five analog
families above are sufficient; no unrelated architecture exploration. All
snippets are current-source excerpts with omissions marked; recommendations
remain planning work, not claims that new interfaces already exist.
