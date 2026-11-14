# Phase 8: Corporate-Action Safe Ownership — Pattern Map

**Mapped:** 2026-11-11. Read-only source inspection; no tests, provider requests, secret reads or operational changes.
**Inputs:** approved PROJECT/REQUIREMENTS/ROADMAP/STATE, `08-RESEARCH.md`, `08-UI-SPEC.md`, existing Phase 7 pattern map and actual source. No CONTEXT.md exists. Proposed paths below are planning recommendations, not existing implementation. Five strong analog families suffice; novel accounting semantics are called out explicitly.

## File Classification

Paths are relative to the repository root. A row naming several files assigns the same pattern to each listed file; exact new names remain the planner's choice.

| New/modified file or responsibility | Role | Data flow | Closest existing analog | Match quality |
|---|---|---|---|---|
| `backend/alembic/versions/0011_<action_schema>.py` (proposed next revision) | migration | batch | `0009_stock_discovery_schema.py` | structural; new financial invariants |
| `backend/app/models/corporate_action.py`, model registration | model | CRUD | `models/stock.py`, `models/trade.py` | structural |
| `backend/app/services/stock_admission.py` | utility/service | transform | existing `ProductAdmission`, `evaluate_admission` | exact edit site; product contract must change |
| `backend/app/services/corporate_action_rules.py` | utility | transform | `services/alpaca.py` bounded Decimal parsing, `stock_quote_rules.py` | role match; event semantics new |
| `backend/app/services/alpaca_actions.py` | provider | request-response/batch | `services/alpaca.py` | structural; actions endpoints/pagination differ |
| `backend/app/services/corporate_actions.py` | service | event-driven/CRUD | `services/trading.py` transaction ownership; `stock_quotes.py` persistence entry point | partial; no event-revision ledger exists |
| `backend/app/services/stock_ownership.py` | service | CRUD/transform | `services/trading.py`, `trade_math.py` | partial; immutable movement journal/cutoff reconstruction new |
| `backend/app/services/stock_action_rules.py` | utility | transform | `stock_admission.py`, `stock_sessions.py` | structural; persistent-hold semantics new |
| `backend/app/tasks/stock_actions.py` | service | scheduled batch | `tasks/stock_scheduler.py` | structural; durable action cursor/health new |
| `backend/app/tasks/scheduler.py`, `core/config.py`, `.env.example`, necessary scheduler env wiring | config/service | scheduled batch | existing independent stock-cycle wiring and `SchedulerSettings` | existing edit sites; no new worker/service |
| `backend/app/schemas/stocks.py`, `services/stocks.py`, `api/v1/stocks.py` | model/service/controller | request-response | existing same files | exact edit sites |
| `scripts/stock-actions.py` or equivalent private operator entry point | utility | file-I/O/CRUD | `deploy/datastore-bindings.py` protected-file and redacted CLI conventions | partial; no action reconciliation CLI exists |
| `frontend/src/api/stocks.ts` | provider/validator | request-response/transform | existing same file | exact edit site |
| `frontend/src/hooks/useStocks.ts` | hook | request-response/transform | existing same file | exact edit site; per-stock epoch ordering new |
| `frontend/src/components/StockSection.tsx`, optional `StockActionState.tsx` | component | transform | existing StockSection helpers/status/live region | exact/role match |
| `frontend/src/pages/MarketsPage.tsx` only if necessary | component | request-response | current independent crypto and stock sections | retain integration; no new page |
| `deploy/db/bootstrap-roles.sql` | config | batch | revision-aware explicit grants | exact edit site |
| `deploy/backup-manifest.sql`, `backup-snapshot.py`, `verify-restore.py`, retained recovery packaging inputs | service/config | batch/file-I/O | explicit revision dispatch and canonical contracts | exact edit sites |
| `backend/tests/test_corporate_action_rules.py`, `test_alpaca_actions.py` | test | transform/request-response | `test_stock_quote_rules.py`, `test_alpaca.py` | role match |
| `backend/tests/test_stock_ownership.py`, `test_corporate_actions.py`, `test_stock_action_monitoring.py` | test | CRUD/event-driven | `test_trading_concurrency.py`, `test_stock_scheduler.py` | structural; new financial assertions |
| `backend/tests/test_stock_migrations.py`, `test_stock_admission.py`, `test_stocks_api.py`, scheduler/config tests | test | batch/request-response | existing same files | exact edit sites |
| New operator CLI tests | test | file-I/O/CRUD | `deploy/tests/test-datastore-bindings.py` boundary-test structure | partial; reconciliation authorization new |
| `frontend/src/api/stocks.test.ts`, hook/StockSection tests and `frontend/e2e/stock-actions.spec.ts` | test | request-response/transform | current stock API tests and `frontend/e2e/stocks.spec.ts` | role/existing edit site |
| `deploy/tests/test-stock-recovery-contracts.py`, `test-db-operations.sh`, `ops-fixtures.py`, retained-bundle tests | test | batch/file-I/O | current successor-schema/TLS/restore lanes | exact edit sites |
| `.github/workflows/ci.yml`, CLAUDE critical coverage command, relevant proof inventory | config | batch | existing critical-module/operations gates | conditional edits for added critical paths; never lower gates |

## Pattern Assignments

### 1. Additive schema, constrained models and product authority

**Analogs:** `backend/alembic/versions/0009_stock_discovery_schema.py:9–25,260–324`; `backend/app/models/stock.py:3–24,89–115,118–190`; `backend/app/services/stock_admission.py:116–240`.

Migration imports and identifiers are the existing Alembic pattern:

```python
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
```

Use a newly autogenerated/reviewed successor of `0010`; do not edit `0009`/`0010`. Preserve existing coins/holdings/trades identities and fills. Schema and any necessary data changes remain separate. Copy conditional explicit grants in `0009:262–290`, restricted to actual new objects, plus the guarded-downgrade principle at `:294–306`. Do not copy discovery's financial-data deletion into an action downgrade: durable ownership/application/entitlement history must prevent destructive downgrade or have a documented irreversible boundary.

Concrete typed model excerpt (`models/stock.py:89–115`):

```python
class StockSession(Base):
    __tablename__ = "stock_sessions"
    __table_args__ = (
        UniqueConstraint("exchange", "session_date", name="uq_stock_sessions_exchange_date"),
        # Other CHECK constraints omitted here.
    )
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    exchange: Mapped[str] = mapped_column(Text)
    session_date: Mapped[date] = mapped_column(Date)
    opens_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
```

Copy `Mapped`/`mapped_column`, identity bigint, explicit FKs/indexes, UTC-aware timestamp columns, bounded JSON/text and named CHECK/UNIQUE constraints. `StockQuote` provides `Mapped[Decimal]` with `Numeric(20, 8)` and finite-value checks. New action identities/revisions, monitor state, ownership movements, application keys, entitlement versions and privileged audit records require their own causal uniqueness and invariants; the session schema does not implement them.

Authority value imports are standard-library dataclasses and typed datetime/dicts. Existing frozen `ProductAdmission` excludes evidence text/scope/quota from repr. Existing evaluator requires explicit `product`, `purpose`, `now`, expected generation and trusted account/server scope, catches malformed JSON shapes and returns a denial without leaking content.

**Do not copy these existing assumptions unchanged:** `stock_admission.py:9–15` actions fields include an assumed `revision`/`effective_date`; `:145–240` hard-requires IEX feed for every product and caps retention at 86,400 seconds. Those are disabled discovery placeholders, not verified corporate-action semantics or adequate long-lived accounting retention. Introduce product-specific reviewed field, endpoint/scope/quota/retention rules, preserving quote/reference/calendar behavior and independently gated action collection/derived/display/retention. Existing quotes permission never admits actions. Schema proof must distinguish runtime monitor rows from migrator-owned authority and operator-owned resolutions.

### 2. Bounded HTTP and independent scheduler cycle

**Analogs:** `backend/app/services/alpaca.py:3–35,51–109,189–279`; `backend/app/tasks/stock_scheduler.py:3–35,80–208,210–239`.

Imports/error pattern from the provider boundary:

```python
import asyncio
import json
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal
import httpx
from app.services.stock_admission import ProductAdmission, evaluate_admission

class AlpacaError(Exception):
    def __init__(self, reason: str, *, retryable: bool = False) -> None:
        super().__init__(reason)
        self.retryable = retryable
```

Raw decode pattern (`alpaca.py:95–99`):

```python
body = json.loads(
    raw, parse_float=_number, parse_constant=_constant, object_pairs_hook=_pairs
)
```

Copy duplicate-key rejection, bounded nesting/tokens, nonfinite rejection and bounded streamed bytes. `_decode` currently insists on a `quotes` object, IEX and twenty symbols: copy the mechanics, not its quote schema. New list/detail/replay endpoints need their actual documented shape, explicit USD/ordinary classification and immutable local revision identity; never manufacture provider fields. Pagination tokens must remain constrained query data for a fixed approved origin/path, with loop/page/byte/time bounds and no credential-following redirect. A complete multi-page response is not a complete late-change/deletion history without reviewed coverage evidence.

Whole-operation timeout pattern (`alpaca.py:232–259`):

```python
async with asyncio.timeout(budget_seconds):
    for attempt in range(attempts):
        _admitted(admission, now(), account=account, server=server)
        async with http.stream(
            "GET", LATEST_QUOTES_URL,
            params={"symbols": ",".join(m.symbol for m in symbols), "feed": "iex", "currency": "USD"},
            timeout=min(remaining, 5), follow_redirects=False,
        ) as response:
            # Bound status/body; never log raw response or private headers.
            ...
```

For actions replace URL/params and admission product, preserving actual-attempt accounting, bounded retry/backoff/Retry-After and total deadline. `alpaca.py:263–279` maps transport errors to exception class names; never expose HTTP bodies, private URLs or headers as domain errors. HTTPX client owns private headers; no keys in model/CLI output.

Scheduler uses shared Redis ownership and independent cadence, not an in-process singleton (`stock_scheduler.py:32–35,210–239`):

```python
_RELEASE_LUA = (
    "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) "
    "else return 0 end"
)
token = secrets.token_hex(16)
acquired = await redis.set(LOCK_KEY, token, nx=True, px=LOCK_TTL_MS)
# Work is bounded; release the matching token in finally.
```

Copy the existing per-attempt request hook at `:132–156`, current evidence rereads, fresh UTC, lease checks and short post-I/O persistence transaction at `:177–207`. Integrate actions alongside crypto and quotes in the existing scheduler; provider I/O occurs outside financial locks. Independent lease/cadence names and configurable bounded action budgets must account for the same account's total quota; the current `RESERVED_REQUESTS = 4` comment is not an action quota grant or proof that full pagination fits. Redis lease is duplicate-work prevention only. Durable coverage/cursors, all-pages commit, journal/application constraints and gap recovery are PostgreSQL responsibilities.

### 3. Financial transactions, ownership and operator reconciliation

**Analog:** `backend/app/services/trading.py:15–41,242–352` for imports, explicit lock/refresh, domain errors, rollback and one commit; `trade_math.py` for pure Decimal calculations. This is a structural analogy, not an existing stock ledger.

Imports/core row-lock excerpt (`trading.py:15–35,254–262`):

```python
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

account = (
    await db.execute(
        select(Account)
        .where(Account.user_id == user_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
).scalar_one()
```

Commit/error pattern (`:333–350`):

```python
await db.flush()
await db.refresh(trade)
fill = _fill(trade, coin.symbol)
await db.commit()
# Existing domain refusal and uniqueness branches:
# except TradeRefused: await db.rollback(); raise
# except IntegrityError as exc: await db.rollback(); inspect known constraint/replay
```

Build immutable result values before rollback expires ORM rows. Catch only known causal conflicts; do not turn unrelated integrity failures into successful replays. A split's once-only key identifies the economic application, not every changed source revision. Quantity updates, movement insertion and application marker must commit together. Preserve total `Holding.cost_basis` exactly; no Phase 8 cash mutation or payment/history insertion. Reject fractional/overflow/ambiguous effects for the whole affected instrument rather than partially applying owners.

**Stock-specific changes to this analogy:** introduce a shared per-instrument transaction gate before deterministic holding locks, with future account lock only after the instrument gate. Existing crypto account→holding order remains unchanged and never takes that gate. Use actual post-lock economic time, not legacy `Trade.created_at`'s transaction-start `now()` default, for cutoff semantics. Reconstruct eligible quantity from immutable signed movements and verified unit/boundary context, never today's holding. Ownership and reconciliation have no exact existing implementation; design from RESEARCH and test real contention.

**Private CLI analogy:** `deploy/datastore-bindings.py:45–80,316–335` supplies protected file reading, narrow command modes, scoped lock and redacted failure behavior:

```python
def protected(path, *, directory=False, mode=None):
    require(path.is_absolute() and path == path.resolve())
    # Inspect every parent and target with lstat; reject unsafe ownership/modes.
    ...
    if mode is not None:
        require(stat.S_IMODE(entry.st_mode) == mode)
```

Its entry point prints a fixed redacted failure and exits1, without dumping exception content. Reuse these input/output safety conventions only; datastore bindings are not action-resolution authority. New inspect/reconcile must validate bounded evidence and expected revision/epoch, take the same SQL gate, append an immutable scoped decision, and reject stale resolution or a blanket `healthy=true`. No HTTP admin router, user bypass, scheduler-minted operator approval or broad app/migrator credential injection.

### 4. Final-authority API projection and strict monotonic UI

**Analogs:** `backend/app/api/v1/stocks.py:3–27`, `schemas/stocks.py`, `services/stocks.py:67–232`; frontend `api/stocks.ts`, `hooks/useStocks.ts`, `components/StockSection.tsx`.

Route auth/import/header pattern:

```python
from app.core.deps import CurrentUserDep, DbDep, SettingsDep
from app.schemas.stocks import StocksResponse
from app.services import stocks

async def get_stocks(
    user: CurrentUserDep, db: DbDep, settings: SettingsDep, response: Response
) -> StocksResponse:
    result = await stocks.list_stocks(db, settings)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Vary"] = "Cookie, Authorization"
    return result
```

Keep this thin authenticated GET; services own projection. Frozen Pydantic response models use `Literal`, `AwareDatetime`, Decimal strings and `execution_enabled: Literal[False]`. Add only safe action facts/reasons/epoch/deadline, no private evidence/payloads/holdings/ratios or new trading controls. Existing StockStatus remains exchange-status unknown, independent of action monitoring.

`services/stocks.py:112–134` reads final current authority and session state in a bounded READ COMMITTED statement, then obtains fresh UTC after awaited reads:

```python
select(
    _json_rows(StockDataAdmission, 6).label("admissions"),
    _json_rows(StockSession, 273, staged_at).label("sessions"),
    func.current_setting("transaction_isolation").label("isolation"),
).execution_options(stock_final_evidence=True)
# After executing/validating the final row:
checked_at = now()
```

Extend that final authority boundary to current action epoch/hold/health, not merely a preparatory read. Existing catalogue-first outer join preserves all twenty identities. Current quote filtering uses independent product retention, generation, calendar and event source time; preserve it and additionally suppress unsafe or old-unit quotes. Derive deadline as the earliest relevant authority/monitor/known effective boundary. Same-request committed holds/resolutions must affect response. No provider request inside this route.

Frontend imports use `@/` aliases, shared `apiFetch`, TanStack Query and auth query identity. `api/stocks.ts:151–191` strictly validates exact twenty distinct identities and encloses shared refresh/retry transport in `performance.now()` measurements. Its `units()` compares NUMERIC strings using bigint. Extend explicit enums/timestamps/safe integers; missing or malformed action fields fail closed. Do not pass amounts through JavaScript Number.

Conservative clock excerpt (`hooks/useStocks.ts:8–15`):

```typescript
const elapsed = Math.max(0, now - data.transport.received_at);
const lower = Date.parse(data.server_now) + elapsed;
const upper = lower + data.transport.round_trip_ms;
const allowed =
  data.admission.state === "approved" &&
  data.admission.valid_until !== null &&
  upper < Date.parse(data.admission.valid_until);
```

Copy auth-scoped `queryKey`, AbortSignal, cache subscription and superseded-result rejection at `:90–147`; expired-data cache removal at `:150–174`. Add per-instrument epoch ordering and equal-epoch later safety-state protection alongside admission generation/server time. The current one-second display timer is an existing baseline, **not proof of exact new action-boundary expiry**: plan a deadline-triggered purge/reprojection so a known split boundary cannot leave old-unit values visible until the next interval/refetch. Browser time only removes eligibility; it cannot establish current action health. Unknown new events still require a new server response.

`StockSection.tsx:1–27,95–145` supplies shadcn Card/Badge/Button imports, semantic `<time dateTime>`, safe company text, independent loading and retry, focus restoration on successful retry and a single atomic `role="status"` region. Extend table/mobile state helpers per UI-SPEC using fixed reason-to-copy maps and existing tokens. Announce meaningful symbol/action transitions, not each tick. Keep IEX attribution, crypto controls and stock execution-disabled notice. UI has no hold-clearance action.

### 5. Revisioned recovery, grants/TLS and test families

**Analogs:** `deploy/backup-snapshot.py:83–185`, `deploy/verify-restore.py:768–812`, `deploy/db/bootstrap-roles.sql:91–115`, `deploy/tests/test-stock-recovery-contracts.py`.

Producer dispatch currently starts with:

```python
SUPPORTED_REVISIONS = ("0007", "0008", "0009", "0010")

def contract_columns(revision):
    require(revision in SUPPORTED_REVISIONS)
    columns = dict(BASE_COLUMNS)
    if revision in ("0009", "0010"):
        columns["coins"] += " asset_class"
        columns.update(STOCK_COLUMNS)
    return {table: set(value.split()) for table, value in columns.items()}
```

This must gain an explicit successor contract. Merely adding revision0011 to an allowlist leaves several `in ("0009", "0010")` branches wrong. Extend producer SQL/schema guards, consumer invariants, relation/column/FK/index/sequence expectations and retained payload together. Preserve byte-identical legacy manifests; selecting revision precedes parsing absent-table SQL. Hash every accounting revision/movement/application/entitlement/hold/audit/cursor field, including empty tables, with deterministic ordered UTC/Decimal canonicalization.

Consumer comparison (`verify-restore.py:780–796`):

```python
contract.validate_manifest(manifest)
actual = canonical(dc)
contract.validate_manifest(actual)
require(all(actual[k] == manifest[k] for k in ["tables", "financial", "revision", "schema"]))
```

`bootstrap-roles.sql:91–108` grants exact app/scheduler objects under revision dispatch, revokes broad defaults and gives no scheduler account/holding mutation today. New scheduler split privileges must be narrowly planned/tested; prove it still cannot debit cash, edit immutable fills, renew permission or author privileged resolution. Test gate lock privilege itself. An upgrade proof runs successor migration as actual migrator and then exercises existing restricted TLS roles **without bootstrap grant repair**; separately prove fresh bootstrap parity.

Test assignment details:

- `backend/tests/test_alpaca.py` / `test_stock_quote_rules.py`: mock provider HTTP only; raw malformed Decimal/JSON, bytes/depth, status/backoff, no-call denial. Add multi-page loop/budget/replay/known-ID and incomplete-coverage assertions.
- `test_trading_concurrency.py:65–101`: real independent async sessions/requests via `asyncio.gather`, final cash/quantity/count assertions. New action tests need observable PG barriers/gates for both lock acquisition orders, rollback injection and cutoff-crossing actual post-lock time, not mocked database locks or sleeps as proof.
- `test_stocks_api.py:23–87,234–369`: synthetic admissions/quote rows on real PostgreSQL, unavailable catalogue preservation, REPEATABLE READ denial, same-request committed change and final-clock boundary cases. Extend to ingest/hold/resolution epochs and split-unit compatibility; synthetic fixtures grant no live rights.
- Existing frontend stock tests: strict validation, cache/auth changes, conservative RTT and API HTTP mocks. Add exact action deadline, older/equal epoch late response, persistent hold after healthy quote, no raw provider text and no stock buttons. Browser proof follows UI-SPEC's 320/375/768/1280px, keyboard/zoom/reduced-motion stories.
- `deploy/tests/test-stock-recovery-contracts.py:31–76,155–326`: revision dispatch, unknown-revision refusal, changed-field hashes and schema mutation cases. Add successor populated financial state, restore then replay idempotency and sequence progression. `test-db-operations.sh`/`ops-fixtures.py` remain isolated TLS/least-privilege/retained-archive proof owners; no production/B2/timer calls.

## Shared Patterns

- **Authentication:** `CurrentUserDep`, thin no-store GET, no new privileged HTTP route. Reconciliation is a private operator command with independently restricted authority.
- **Transactions:** services own one business transaction; row locks refresh ORM state; uniqueness is the final once-only boundary; explicit rollback releases locks. Provider I/O occurs before SQL financial gates.
- **Error handling:** fixed enums/domain reasons and redacted CLI/provider failure classes, never provider response text, keys or operator evidence in UI/logs.
- **Time and numbers:** aware UTC, actual post-lock economic instant, immutable event versus observation time; Decimal/NUMERIC and JSON strings. No price adjustment inferred in the browser.
- **Current evidence:** product/purpose/generation/scope checked at awaited boundaries, fresh final UTC, conservative deadline purge and no automatic recovery of persistent disputes.
- **Scope:** Phase8 records events, split/ownership effects and dividend eligibility. Phase9 fills and combined portfolio, Phase10 cash/payment History and Phase11 final mixed-asset acceptance remain separate. Phase7 live measurement stays deferred independently.

## No Exact Analog Found

| Responsibility | Role / flow | Why implementation needs RESEARCH-driven design |
|---|---|---|
| Immutable economic action identity/revision/deletion replay and complete coverage baseline | service / event-driven | Quote upsert is latest-value storage, not revision history or news-completeness proof |
| Per-instrument ownership gate, append-only movement journal and historical ex-date quantity/unit reconstruction | service / CRUD + transform | Legacy crypto trades mutate current holdings and lock account first; there is no stock ownership history |
| Whole-holder split application and revision-linked entitlement derivation | service / transactional batch | Existing trade math is not a corporate-action engine; total basis and original fills must survive exactly |
| Privileged evidence-based hold reconciliation | CLI/service / file-I/O + CRUD | Existing private scripts validate infrastructure; none resolves financial action disputes |
| Per-stock action epochs/known effective-boundary quote compatibility | service/hook / transform | Existing admission generations and time expiry are structural precedents only, not unit-change ordering |

## Metadata

**Search scope:** backend models/services/tasks/routes/schemas/migrations/tests; frontend stock API/hook/component; deploy canonical producer/consumer, role bootstrap, private CLI and operations tests; Phase7 pattern map. **Strong analog families:** five. **Files classified:** 29 responsibility rows, including explicit multi-file rows. No new dependencies, source modifications, installations, test executions or operational acceptance are claimed by this map.
