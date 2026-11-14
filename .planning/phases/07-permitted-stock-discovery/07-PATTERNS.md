# Phase 7: Permitted Stock Discovery — Pattern Map

**Mapped:** 2026-11-10. Read-only source inspection; no tests or services run.
**Scope:** Research-proposed paths, not a claim that new modules already exist. No CONTEXT.md exists; approved requirements and UI-SPEC supply decisions. Names below are planner recommendations unless marked existing.

## File Classification

Paths under `backend/app/` unless another root is shown. Five analog families cover the proposed work; novel safety semantics are identified separately.

| New/modified path | Role / flow | Closest current analog | Match |
|---|---|---|---|
| `models/price.py` (existing), `models/stock.py` | model / CRUD | `models/price.py:21–53` | exact structural |
| `backend/alembic/versions/<next>_stock_schema.py`, `<next>_seed_stocks.py` | migration / batch | `0004_coins_and_prices.py`, `0005_seed_coins.py` | role |
| `services/stock_quotes.py` | service / batch + request-response | `services/prices.py:41–113` | exact structural |
| `services/alpaca.py` | provider / request-response | `services/kraken.py:28–84` | role |
| `services/stock_quote_rules.py` | utility / transform | `services/price_rules.py` (research reference), `prices.py:17–28` | partial; stock predicates differ |
| `services/stock_sessions.py` | service / batch + transform | scheduler injected clock; price freshness pure functions | partial; calendar has no exact analog |
| `services/stock_admission.py` | service / request-response + batch | config/settings separation only | no rights/revocation analog |
| `tasks/scheduler.py` (existing), optional `tasks/stock_scheduler.py` | service / scheduled batch | `tasks/scheduler.py:165–199,216–262` | exact structural |
| `api/v1/stocks.py`, `schemas/stocks.py`, `services/stocks.py` | controller/model/service / request-response | `api/v1/prices.py`, `schemas/prices.py`, `services/prices.py` | exact structural |
| `api/v1/router.py` or current router-registration site | route / request-response | existing prices router registration | role; locate actual registration before edit |
| `core/config.py`, `.env.example`, necessary Compose env wiring (existing) | config / transform | `Settings` and `SchedulerSettings` | role |
| `services/prices.py`, `services/trading.py` (existing) | service / CRUD | existing active-coin lookups | exact edit sites; add crypto discriminator |
| `frontend/src/api/stocks.ts` | provider / request-response | `frontend/src/api/prices.ts` | exact structural |
| `frontend/src/hooks/useStocks.ts` | hook / request-response | `frontend/src/hooks/usePrices.ts` | exact structural |
| `frontend/src/components/StockAttribution.tsx`, stock status/list components | component / transform | `FreshnessBadge`, `MarketsPage.tsx` | role |
| `frontend/src/pages/MarketsPage.tsx` (existing) | component / request-response | current Markets retained-data branches | exact edit site |
| `backend/tests/test_stock_catalog.py`, `test_stocks_api.py` | test / CRUD + request-response | `test_seed_coins.py`, `test_prices_api.py` | role |
| `backend/tests/test_alpaca.py`, `test_stock_quote_rules.py` | test / request-response + transform | `test_kraken.py`, existing price-rule tests | role |
| `backend/tests/test_stock_admission.py`, `test_stock_sessions.py`, `test_stock_scheduler.py` | test / batch + transform | `test_scheduler.py`, `test_scheduler_loop.py` | partial; new semantics |
| `backend/tests/test_migrations.py`, config/seed/trade tests (existing) | test / CRUD | populated migration and API fixtures | exact edit sites |
| `frontend/src/api/stocks.test.ts`, `components/StockAttribution.test.tsx`, `pages/MarketsPage.test.tsx` | test / request-response + transform | `api/prices.test.ts`, current Markets tests | role |
| `frontend/e2e/stocks.spec.ts`, `e2e/markets.spec.ts` | test / request-response | current markets browser journey | role |
| `deploy/db/bootstrap-roles.sql`, `backup-manifest.sql`, `backup-snapshot.py`, `verify-restore.py` | config/service / file-I/O + batch | current explicit revision/manifest contracts | exact edit sites |
| `deploy/tests/ops-fixtures.py`, `test-db-operations.sh`, `test-backup.sh` | test / batch + file-I/O | existing 0007/0008 restore and restricted-role lanes | exact edit sites |
| `backend/pyproject.toml`, `backend/uv.lock`, `.github/workflows/ci.yml` if needed | config / batch | current dependency lock and protected CI | exact edit sites; conditional changes only |

## Pattern Assignments

### 1. Instrument, migration and read/write family

`backend/app/models/price.py:32,50–53` supplies typed identity/FK, Decimal and UTC conventions:
```python
id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
coin_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("coins.id"), primary_key=True)
mid: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
```
These lines belong to two different classes; do not paste them as one model. Preserve physical `coins`/FK IDs; add stock discrimination and metadata through reviewed migrations. Existing globally unique symbol/non-null Kraken mapping need explicit conditional constraints. Seed separately using the bounded data-migration style in `0005_seed_coins.py`; do not copy its unguarded deletion into a future financial downgrade.

`backend/app/services/prices.py:103–112` supplies caller-owned transaction and monotonic PostgreSQL upsert:
```python
stmt = stmt.on_conflict_do_update(
    index_elements=[Price.coin_id],
    set_={"mid": stmt.excluded.mid, "as_of": stmt.excluded.as_of,
          "source": stmt.excluded.source},
    where=Price.as_of < stmt.excluded.as_of,
)
result = await db.execute(stmt)
```
Adapt columns to quote event/collection time and provenance; equal events cannot refresh age. Stock listing must start from catalogue and **outer join**, as `load_active_coins:75–83` does; do not copy `list_prices:46–48` inner join. Add explicit crypto predicates to original loaders and every legacy trade lookup.

### 2. Provider and scheduler family

Imports from `backend/app/services/kraken.py:8–14`: `asyncio`, `logging`, `Awaitable/Callable/Sequence`, `httpx`; typed provider error `:28–31` carries a retryable flag. Retry/error excerpt `:76–83`:
```python
except httpx.TransportError as exc:
    last = KrakenError(type(exc).__name__, retryable=True)
except KrakenError as exc:
    if not exc.retryable:
        raise
    last = exc
if attempt < attempts - 1:
    await sleep(min(8, 2**attempt) + jitter())
```
Copy injected sleep/jitter and sanitized exception-class reporting. Do **not** copy provider error bodies or `.json()` numeric decoding for credentialed Alpaca: decode raw bytes to Decimal, enforce fixed origin/`feed=iex`, bounded body/batch/time and explicit schema. Do not copy Kraken's per-pair retry fanout without a stock quota budget.

`backend/app/tasks/scheduler.py:176–199` acquires `redis.set(LOCK_KEY, token, nx=True, px=LOCK_TTL_MS)`, wraps refresh in `asyncio.timeout(CYCLE_TIMEOUT_S)` and releases in `finally`. `:216–233` cancels/awaits in-flight work on shutdown; `:236–262` uses an injected monotonic clock and stop event. Apply separate stock lease/deadline/failure state inside the existing one scheduler; sequential unbounded stock work must not delay crypto. Copy lifecycle mechanics, not crypto receipt timestamps or spike-confirmation semantics.

Test analog `backend/tests/test_kraken.py:66–85` uses respx HTTP responses, inspects requested parameters/headers, and asserts fatal errors make one call with no retry sleeps. New tests need raw numeric response bytes, redaction, admission-denied no-call assertions and source timestamp boundaries. Existing scheduler-loop fixtures provide cancellation/clock patterns.

### 3. Protected read API family

`backend/app/api/v1/prices.py:3–7,22–27`:
```python
from app.core.deps import CurrentUserDep, DbDep, SettingsDep
from app.schemas.prices import PriceOut, PricesOut
from app.services import prices
# In the endpoint:
response.headers["Cache-Control"] = "no-store"
now = datetime.now(UTC)
rows = await prices.list_prices(db, settings, now)
```
Copy explicit `response_model`, CurrentUserDep, request-time UTC, thin service call and no-store. Stock service owns catalogue-first assembly and permission filtering. Money remains Pydantic Decimal JSON strings; missing quotes are nullable, not zero. Return independent session, source age, admission and phase-disabled execution facts. No new stock mutation endpoint or public provider proxy.

### 4. Frontend query and retained-state family

`frontend/src/hooks/usePrices.ts:7–22` supplies queryFn AbortSignal, 401 invalidation of `["me"]`, 30-second refetch and refocus recovery. Use separate stock keys; crypto and stock loading/error/age must remain independent. `frontend/src/api/prices.ts:57–62` demonstrates validation after shared authenticated transport:
```typescript
const body = await apiFetch("/api/v1/prices", { signal });
if (!isPrices(body)) throw new Error("Unexpected prices response");
return body;
```
New validator must additionally validate nullable quotes, parseable UTC timestamps, machine-state enums and the admission envelope. Existing string/timestamp presence checks are insufficient for the stock contract.

`frontend/src/pages/MarketsPage.tsx:11–16,29–40,124–127` preserves accepted data after refresh failure and computes age from server age plus elapsed response time. Preserve permitted data only; revocation requires purge plus protection from late prior-admission responses (new pattern). Reuse Card/Button and semantic table structure `:48–78`; follow UI-SPEC for max width, separate sections, responsive stock list, stable numeric keys and no stock Trade links. Existing crypto symbol keys/Trade controls are not stock patterns. Attribution is a reusable small component; do not build later trade/valuation screens now.

### 5. Explicit operations contract family

`deploy/db/bootstrap-roles.sql:91–96` explicitly grants app `SELECT ON coins, prices`, scheduler `SELECT ON coins` and `SELECT, INSERT, UPDATE ON prices`. Extend exact grants/ownership for new schema; do not introduce broad default privileges or financial writes for scheduler.

`deploy/backup-manifest.sql:3–18` canonicalizes explicit columns, Numeric text and UTC timestamps, hashes ordered rows, and includes empty tables. `deploy/verify-restore.py:752–758` compares `tables`, `financial`, `revision`, `schema`; `:781–814` validates revision-specific indexes and identity progression. Extend producer/consumer together using explicit revision dispatch; old snapshots must not execute SQL referencing new columns. Update fixed table/FK/sequence expectations and retained payload tests, not just pg_dump acceptance. Preserve existing 0007/0008 fixtures and add populated successor-schema restore/TLS least-privilege proofs.

## Shared Patterns and No Analog Found

- **Transactions/auth/errors:** services own DB commit; routes use CurrentUserDep; bounded HTTP errors expose safe classifications only. No provider I/O under financial locks.
- **New semantic boundaries:** no existing verified licensing-evidence/revocation gate, exceptional-closure calendar coverage policy, or combined source-event/session/status eligibility model. Implement these from RESEARCH/UI-SPEC with explicit tests; crypto freshness clamps future times and is unsuitable unchanged.
- **Permission is external evidence:** passing mocks/config flags cannot grant display rights or complete live admission. Keep explicit human checkpoint and disabled defaults; no private API probing or provider agreement implied.

## Metadata

**Search scope:** backend app/tests/migrations, frontend API/hooks/Markets, deploy role/manifest/restore contracts. **Analog families:** five; searches stopped after these strong matches. Referenced untouched secondary fixture paths are research-identified planner entry points, not independently executed or claimed verified. This map creates no source changes and no operational acceptance claim.
