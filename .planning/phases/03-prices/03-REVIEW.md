---
phase: 03-prices
reviewed: 2026-10-28T10:30:00Z
depth: standard
files_reviewed: 62
files_reviewed_list:
  - .env.example
  - .github/workflows/ci.yml
  - CLAUDE.md
  - backend/alembic/versions/0004_coins_and_prices.py
  - backend/alembic/versions/0005_seed_coins.py
  - backend/app/api/v1/prices.py
  - backend/app/api/v1/router.py
  - backend/app/core/config.py
  - backend/app/models/__init__.py
  - backend/app/models/price.py
  - backend/app/schemas/prices.py
  - backend/app/services/fake_prices.py
  - backend/app/services/kraken.py
  - backend/app/services/price_rules.py
  - backend/app/services/prices.py
  - backend/app/tasks/__init__.py
  - backend/app/tasks/scheduler.py
  - backend/tests/conftest.py
  - backend/tests/fixtures/kraken_ticker_ok.json
  - backend/tests/test_accounts.py
  - backend/tests/test_config_prices.py
  - backend/tests/test_fake_prices.py
  - backend/tests/test_kraken.py
  - backend/tests/test_migrations.py
  - backend/tests/test_price_rules.py
  - backend/tests/test_prices_api.py
  - backend/tests/test_prices_service.py
  - backend/tests/test_scheduler.py
  - backend/tests/test_scheduler_loop.py
  - backend/tests/test_seed_coins.py
  - deploy/RUNBOOK.md
  - deploy/deploy.sh
  - deploy/smoke-prod.sh
  - deploy/tests/test-reexec.sh
  - deploy/tests/test-smoke-ports.sh
  - docker-compose.override.yml
  - docker-compose.prod.yml
  - docker-compose.yml
  - frontend/e2e/auth.spec.ts
  - frontend/e2e/health.spec.ts
  - frontend/e2e/helpers.ts
  - frontend/e2e/markets.spec.ts
  - frontend/package.json
  - frontend/src/App.test.tsx
  - frontend/src/App.tsx
  - frontend/src/api/prices.test.ts
  - frontend/src/api/prices.ts
  - frontend/src/components/FreshnessBadge.test.tsx
  - frontend/src/components/FreshnessBadge.tsx
  - frontend/src/components/ui/badge.tsx
  - frontend/src/hooks/useNow.test.ts
  - frontend/src/hooks/useNow.ts
  - frontend/src/hooks/usePrices.ts
  - frontend/src/lib/age.test.ts
  - frontend/src/lib/age.ts
  - frontend/src/lib/money.test.ts
  - frontend/src/lib/money.ts
  - frontend/src/main.tsx
  - frontend/src/pages/MarketsPage.test.tsx
  - frontend/src/pages/MarketsPage.tsx
  - frontend/src/pages/SignInPage.test.tsx
  - frontend/src/test/render.tsx
findings:
  critical: 1
  warning: 7
  info: 6
  total: 14
status: fixed
---

# Phase 3: Code Review Report

**Reviewed:** 2026-10-28T10:30:00Z
**Depth:** standard
**Files Reviewed:** 62
**Status:** issues_found

## Summary

Reviewed the Phase 3 price pipeline end to end (b75ebd5..HEAD = v0.2.1, live on birja.nist.one): Kraken client, acceptance rules, scheduler loop and lock, upsert, API, migrations 0004/0005, compose files, deploy.sh re-exec, smoke checks and the React markets page.

What holds up: Decimal is used end to end. Mid is quantized once, half-even, to 8 dp. JSON prices are strings and the frontend formats them through `Intl.NumberFormat` string input with no float. The upsert's `as_of` guard is monotonic. The lock uses a random token with a compare-and-delete Lua release in `finally`. Fake prices are refused in prod at two layers, and prod hardcodes `PRICE_SOURCE: "kraken"`. `/prices` uses `CurrentUserDep`. Freshness boundaries (`< fresh` fresh, `<= stale` aging) match in backend, frontend and the smoke check. Polling is TanStack-only. The deploy lock is inherited across the re-exec.

Main concerns:
1. One bad coin stalls all 15 prices. Examples: a delisted pair, an absurd value, a NUMERIC overflow.
2. Prod scheduler INFO logging is silently lost. Verified: `docker logs birja-prod-scheduler-1` has 0 lines while the heartbeat is fresh.
3. A DB transaction stays open across the up-to-35 s Kraken call, under a 30 s `idle_in_transaction_session_timeout`.
4. The lock TTL does not actually bound the worst-case cycle.

## Critical Issues

### CR-01: A single bad coin fails the whole batch, so every price goes stale

**File:** `backend/app/services/kraken.py:20,52-55`, `backend/app/services/price_rules.py:56`, `backend/app/tasks/scheduler.py:96-142`, `backend/app/services/prices.py:107-123`

**Issue:** The cycle is all-or-nothing in three independent ways. Each one turns a per-coin problem into a market-wide outage. That breaks PRICE-04's per-coin "reject and keep last good" intent. Once Phase 4 refuses trades on stale prices, it would also halt all trading.

1. **Unknown pair.** Kraken rejects the whole multi-pair Ticker request with `EQuery:Unknown asset pair` if any one pair is delisted or renamed. `NON_RETRYABLE_ERRORS` makes this fatal, and `_refresh` returns `source_error` for all 15 coins on every cycle. The log line does not say which pair is at fault. The only fix is a migration plus a deploy, because CLAUDE.md forbids hand edits.
2. **Decimal overflow raises instead of rejecting.** `parse_price` accepts any finite positive value, for example `"1e30"`. `((bid+ask)/2).quantize(Decimal("1e-8"))` then raises `InvalidOperation`, because 39 digits exceed the 28-digit context. Verified locally. The exception is not caught in `_refresh`, so `run_cycle`'s broad `except` turns the whole cycle into `source_error`. No coin is updated.
3. **NUMERIC(20,8) overflow kills the single upsert.** Values from 1e12 up to just below 1e20 pass quantize (verified: `1e13` gives `10000000000000.00000000`), but they do not fit `NUMERIC(20,8)` (max < 1e12). Such a value is accepted without a spike check when the coin has no price yet: a newly added coin, or after the prices table is reset. It is also accepted after 3 confirming polls. The one multi-row `INSERT ... ON CONFLICT` then fails with numeric overflow, and the other 14 coins are not stored either. This repeats every cycle while Kraken keeps returning the value.

**Fix:**
```python
# price_rules.py
_MAX_MID = Decimal("1e12")  # NUMERIC(20,8) upper bound

def mid_from_ticker(entry: object) -> Decimal | None:
    ...
    if bid is None or ask is None or bid > ask or ask >= _MAX_MID:
        return None
    try:
        mid = ((bid + ask) / 2).quantize(_MID_QUANTUM, rounding=ROUND_HALF_EVEN)
    except InvalidOperation:
        return None
    ...
```
Also add a `CHECK (mid < 1e12)`-style guard or let NUMERIC enforce it. For unknown pairs, on `Unknown asset pair` fall back to fetching each pair on its own, or bisecting the batch. Log `symbol=... reason=unknown_pair` for the failing pair and keep updating the rest. Add regression tests for all three cases: one unknown pair among valid ones, `"1e30"`, and `"1e13"` on a never-priced coin.

## Warnings

### WR-01: All scheduler INFO logs are dropped in production (logger is `__main__`)

**File:** `backend/app/tasks/scheduler.py:34`, `docker-compose.prod.yml` (`command: ["python", "-m", "app.tasks.scheduler"]`), `backend/app/core/logging.py:13`

**Issue:** `logger = logging.getLogger(__name__)` evaluates to `"__main__"` when the module runs with `python -m`. `configure_logging()` only attaches a handler and INFO level to the `app` logger tree. So "price scheduler started", every "price cycle: status=... accepted=... rejected=..." line and every "lock held elsewhere" line go nowhere. Warnings and errors only reach stderr through Python's unformatted `lastResort` handler, with no timestamp and no level. Verified on the live host: `docker logs birja-prod-scheduler-1` returns 0 lines after several minutes of uptime, while the heartbeat file is about 1 minute old. Tests import `app.tasks.scheduler` by name, so they never see this. One knock-on effect: the smoke check "no codes or keys in scheduler logs" passes vacuously.

**Fix:** `logger = logging.getLogger("app.tasks.scheduler")`. Alternatively, keep `main()` in a tiny `__main__` shim that imports the module, or run it as `python -c "from app.tasks.scheduler import main; main()"`. Add a test that runs `python -m app.tasks.scheduler` (or calls `amain`) and asserts the "started" line appears on stderr.

### WR-02: DB transaction held open across the Kraken call; 30 s idle-in-transaction timeout is below the 35 s source timeout

**File:** `backend/app/tasks/scheduler.py:85-93,141-142`

**Issue:** `load_active_coins(session)` autobegins a transaction. The session then waits up to `SOURCE_TIMEOUT_S = 35` s on Kraken before `upsert_prices` and `commit`. Both the scheduler engine (`idle_in_transaction_session_timeout=30000`) and the prod Postgres server (`-c idle_in_transaction_session_timeout=30000`) kill the backend connection after 30 s idle in a transaction. On a slow Kraken path, the 3-attempt retry (10 s per phase timeouts plus 1-3 s backoff) commonly finishes in 25-35 s. That is exactly when retries have just rescued the fetch, and the upsert then fails on a terminated connection, so the cycle is lost. Holding a transaction (and a pool connection) across external I/O is also an anti-pattern in its own right.

**Fix:** Read the coins in their own short session or transaction, then close it. Fetch with no DB connection held. Then open a new session for evaluate, upsert and commit:
```python
async with sessionmaker() as s:
    coins = await load_active_coins(s)
# fetch outside any transaction
...
async with sessionmaker() as s, s.begin():
    await upsert_prices(s, accepted, settings.price_source)
```
Add a test that uses a source sleeping longer than a short `idle_in_transaction_session_timeout` and asserts the upsert still succeeds.

### WR-03: Lock TTL (45 s) does not cover the worst-case cycle, despite the comment

**File:** `backend/app/tasks/scheduler.py:36-40,83-143`

**Issue:** The comment says the TTL "exceeds the worst-case cycle". But only the source call is bounded (35 s). The time under the lock also includes the session connect (5 s connect timeout plus `pool_pre_ping`), `load_active_coins` (up to the 30 s statement timeout), the upsert (up to 30 s) and the commit. The worst case is above 100 s. If the lock expires mid-cycle, a second scheduler instance (accidental `--scale`, or an old container during recreate) can run a concurrent cycle with its own in-memory `candidates`. The as_of guard then hides the lost-update rather than preventing it. The single-instance guarantee is exactly what the lock exists for.

**Fix:** Wrap the whole `_refresh` in `asyncio.timeout(CYCLE_TIMEOUT_S)` with `CYCLE_TIMEOUT_S < LOCK_TTL_MS/1000` (for example 40 s total, with the source sub-budget at 25 s). Alternatively, extend the lock with a token-checked `PEXPIRE` Lua call before the upsert. Assert the relation in a test.

### WR-04: Any failed background refetch replaces the whole price table with an error

**File:** `frontend/src/pages/MarketsPage.tsx:29-40`, `frontend/src/hooks/usePrices.ts`

**Issue:** In TanStack Query v5, a failed background refetch sets `status: "error"` / `isError: true` while `data` keeps the last good response. `MarketsPage` checks `isError` before `data`. So one transient failure (after `retry: 1`) hides every price and shows "Can't load prices right now." This also happens on a 502 during a deploy, which is a regular event since every deploy recreates backend. It contradicts "staleness is visible": the right UX is to keep showing the last prices and let the badges age toward Stale.

**Fix:** Branch on data first:
```tsx
if (isPending) ... 
else if (data) { /* table, plus an inline "Couldn't refresh" note when isError */ }
else { /* error card */ }
```
Add a test: first fetch OK, second fetch 500, and the table plus a "Delayed"/"Stale" badge are still rendered.

### WR-05: `app_services` silently drops the scheduler from deploy/rollback on any `dc config` failure

**File:** `deploy/deploy.sh:58-60`

**Issue:** `if dc config --services | grep -qx scheduler` runs inside an `if`, so `set -e` and the ERR trap are suppressed. With `pipefail`, a failing `dc config` makes the condition false. Causes include an env-file or interpolation error, a transient docker CLI error, or SIGPIPE when `grep -q` exits before compose finishes writing. The function then prints `backend`. The deploy proceeds and rebuilds and restarts only backend, so the old scheduler image keeps running the previous release's code. Nothing reports that it happened.

**Fix:** Capture the output first and fail loudly:
```bash
app_services() {
  local svcs
  svcs=$(dc config --services) || { echo "dc config failed" >&2; return 1; }
  if grep -qx scheduler <<<"$svcs"; then echo "backend scheduler"; else echo "backend"; fi
}
```
Then call it as `services=$(app_services)` on its own line, so `set -e` applies before `dc build $services`.

### WR-06: Scheduler container receives every app secret it does not use

**File:** `docker-compose.prod.yml` (scheduler `environment`), `docker-compose.yml` (scheduler `environment`)

**Issue:** The scheduler receives `OTP_HMAC_SECRET`, `JWT_SECRET` and `RESEND_API_KEY` only because the monolithic `Settings` requires them. This container parses responses from a third-party API. A compromise of it would yield the token-signing key, which allows forging sessions for any user, the OTP HMAC key, and the email-provider key. This works against CLAUDE.md's least-privilege intent.

**Fix:** Split a `SchedulerSettings` (env, database_url, redis_url, price_*) out of `Settings`. Use it in `app.tasks.scheduler`, and remove the three secrets from both scheduler service definitions. Keep the prod "fake refused" validator on the new class.

### WR-07: Graceful stop cannot interrupt a cycle; the 20 s grace is shorter than a cycle, so SIGKILL leaks the lock

**File:** `backend/app/tasks/scheduler.py:192-201,214-217`, `docker-compose.prod.yml` (`stop_grace_period: 20s`)

**Issue:** SIGTERM only sets `stop`. `run()` checks it after `await cycle()` returns. A cycle under degraded Kraken takes up to about 35 s or more (see WR-03), so Docker sends SIGKILL after 20 s. `finally: _release` never runs and the lock stays for up to 45 s. Every deploy recreates the scheduler. The new container's first cycle then logs "locked" (invisibly, see WR-01) and waits a full interval, so prices go about 2 minutes without a refresh around each deploy, on top of the killed cycle.

**Fix:** Run the cycle as a task and race it against `stop.wait()`. On stop, cancel the task: CancelledError propagates through `asyncio.timeout`, and `finally` releases the lock. Alternatively, raise `stop_grace_period` above the bounded cycle timeout from WR-03.

## Info

### IN-01: Sub-1e-6 prices serialize in scientific notation and break the whole response on the client

**File:** `backend/app/schemas/prices.py:10`, `frontend/src/api/prices.ts:22,36`

**Issue:** Pydantic serializes `Decimal` with `str()`, so `Decimal("0.00000010")` becomes `"1.0E-7"` (verified). `isPrices` requires `/^\d+(\.\d+)?$/` for every item, so a single such price makes `fetchPrices` throw for the whole list. This cannot happen with today's 15 coins, but it is latent for any small-cap coin added later.

**Fix:** Serialize with `format(value, "f")` through a `PlainSerializer`/`field_serializer` on `price`.

### IN-02: Sub-$1 prices that round up display as "$1.000"

**File:** `frontend/src/lib/money.ts:29-31`

**Issue:** The branch is chosen from the integer part before rounding. A value of `0.99996` gets 4 significant digits and renders as `$1.000`, not the D-06 form `$1.00`.

**Fix:** For integer part `0` with a value of at least `0.99995`, use the 2-decimal formatter. Alternatively, compare the formatted result.

### IN-03: Rate-limit responses are retried after 1-3 s and Retry-After is ignored

**File:** `backend/app/services/kraken.py:35-36,79-80`

**Issue:** HTTP 429 and `EAPI:Rate limit exceeded` are retried after `min(8, 2**attempt) + jitter`, which is 1-3 s. That makes Kraken's penalty worse, and it conflicts with CLAUDE.md's "respect the provider's rate limits".

**Fix:** On a rate-limit error, stop retrying for this cycle (treat it as non-retryable within the cycle), or honour `Retry-After` within the budget.

### IN-04: Heartbeat path and health semantics

**File:** `backend/app/tasks/scheduler.py:166,177-180`, compose healthcheck `/tmp/birja-scheduler-heartbeat`

**Issue:** The code uses `tempfile.gettempdir()`, but the healthcheck hardcodes `/tmp`, so they diverge if `TMPDIR` is ever set. The docstring implies an unhealthy container would restart. Docker's `restart: unless-stopped` never restarts an unhealthy container, so health is report-only. Only the smoke freshness check catches a scheduler that has failed on every cycle.

**Fix:** Hardcode `Path("/tmp/birja-scheduler-heartbeat")` or pass the path through an env var. Fix the docstring.

### IN-05: `parse_price` accepts Decimal-lenient strings

**File:** `backend/app/services/price_rules.py:27-36`

**Issue:** `Decimal()` accepts surrounding whitespace and underscores, so `" 1_0 "` parses as `10` (verified). It also accepts exponent forms. These are not valid Kraken prices.

**Fix:** Pre-validate with `re.fullmatch(r"\d+(\.\d+)?", raw)`.

### IN-06: Smoke log-hygiene greps cannot fail when `docker logs` itself fails

**File:** `deploy/smoke-prod.sh:366,389`

**Issue:** `docker logs ... 2>&1 | grep -c` counts 0 if `docker logs` errors. Together with WR-01, the scheduler check is always green.

**Fix:** Capture `docker logs` output and its status separately, and fail if the command fails.

---

_Reviewed: 2026-10-28T10:30:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

## Fix log

All in-scope findings were fixed in **hotfix 0.2.2** (PR #16 into `main`, tag `v0.2.2`, back-merge PR #17) and deployed to production on 2026-10-28.

| Finding | Commit | Status |
|---------|--------|--------|
| CR-01 (one bad coin stops all 15) | 683e09d (unknown-pair per-pair fallback), c8bc58b (per-coin isolation), 52bf406 (NUMERIC(20,8) range) | Fixed |
| WR-01 (prod scheduler logs lost) | cc77f26 | Fixed. Prod `docker logs` shows `price cycle: status=ok accepted=15 rejected=0` |
| WR-02 (transaction held across Kraken call) | 0852308 | Fixed |
| WR-03 (lock TTL < worst-case cycle) | 5b01ca6 | Fixed: whole cycle under `asyncio.timeout(40)` < 45 s TTL |
| WR-04 (failed refetch blanks MarketsPage) | 70133a0 | Fixed |
| WR-05 (deploy silently skips scheduler) | d18207a | Fixed |
| WR-06 (scheduler gets app secrets) | 699850a | Fixed: prod scheduler env is only DATABASE_URL, ENV, PRICE_SOURCE, REDIS_URL |
| WR-07 (shutdown leaves lock held) | 7985a58 | Fixed |
| IN-01..IN-06 | — | Backlog (advisory) |

Before this review, two deploy-tooling bugs found during the v0.2.0 deploy were fixed in **hotfix 0.2.1** (PR #14, tag `v0.2.1`). `deploy.sh` now re-runs the new version when the checkout changes it; this was confirmed live during the v0.2.2 deploy. The smoke check now inspects real host port bindings.
