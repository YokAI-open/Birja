# Phase 3: Prices - Research

**Researched:** 2026-10-28
**Domain:** Kraken public Ticker polling, single scheduler container, price storage and freshness, markets page (FastAPI + React)
**Confidence:** HIGH on the Kraken map (live-verified today), MEDIUM on rate-limit wording, HIGH on codebase integration

## Summary

All 15 D-01 candidates are quoted against USD on Kraken today and every pair returns `status: online` in AssetPairs, so the list stays at 15 with no replacement. BNB is listed (BNBUSD). The one surprise is naming: Kraken's Ticker response keys differ from the common pair names for six coins (XXBTZUSD, XETHZUSD, XXRPZUSD, XLTCZUSD, XXLMZUSD, XDGUSD). Doge is `XDGUSD`, and `DOGEUSD` works only as an alias in the request, not as a key in the response. Requesting the **response key itself** works (live-tested), so the DB stores one `kraken_pair` string per coin that is both what we request and what we look up in `result`. This removes any request/response mapping layer.

One batched GET (`/0/public/Ticker?pair=A,B,...`) returns all 15 coins. A single unknown pair makes the **whole call** fail with `EQuery:Unknown asset pair` (live-tested), so a delisted coin would freeze every price. Mitigation: an `is_active` flag on `coins` and a startup/test check that the seeded keys match Kraken's response.

The scheduler is the backend image with a different command: an asyncio loop on a fixed 60 s schedule, a per-cycle Redis `SET NX PX` lock as belt-and-braces, retries with backoff and jitter, a file-mtime heartbeat for the healthcheck, and an upsert of the latest good price per coin into Postgres. The only new package is `react-router` (8.5.1). Redis is used only for the lock; no price cache (15 rows, trivial query; avoids a second source of truth).

**Primary recommendation:** Two tables (`coins`, `prices`), a pure `evaluate_price()` function holding D-04 plus confirmation (N=3 polls within 5%), a `scheduler` compose service from the backend image, server-computed `status` and `age_seconds` plus the thresholds in the API response, and a gated fake price source so CI e2e never calls Kraken.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** The list is the **top ~15 coins by market cap, excluding stablecoins**. Starting candidates: BTC, ETH, SOL, XRP, BNB, ADA, DOGE, TRX, AVAX, LINK, DOT, LTC, BCH, XLM, ATOM. The final list is pinned to coins that Kraken actually quotes against USD (research confirms each pair and its response key; for example, BNB may not be listed). If a candidate is unavailable, drop it or replace it with the next coin by market cap that is not a stablecoin. Keep the list as data (e.g. a seed migration or config), not hard-coded in the UI.
- **D-02:** The markets page is for **signed-in users only**. Signed-out visitors keep seeing the sign-in card. The prices API sits behind the existing `CurrentUserDep`.
- **D-03:** A price is **fresh under 2 minutes**, **aging from 2 to 5 minutes**, and **stale after 5 minutes**. Age is measured from the price's "as of" timestamp, meaning when the price was fetched or observed, not when the page loaded. The thresholds live in one place, shared by the backend and the UI or sent by the API, so Phase 4 can refuse trades on stale prices with the same definition.
- **D-04:** A new price that is **more than 25% away from the last good price** is rejected. The last good price stays and keeps aging toward stale. Zero, negative and non-numeric prices are always rejected (PRICE-04). Claude's discretion: a confirmation rule so a genuine >25% move is not rejected forever; research proposes it; it must be tested.

### Claude's Discretion
- Scheduler: single scheduler-loop container polling Kraken about every 60 s, exactly once regardless of backend workers, no Celery/arq.
- Storage: Postgres is the source of truth (latest good price per coin with as-of time and source); Redis optional as cache. History tables only if Phase 4 or 5 needs them.
- Retries: backoff with jitter and Kraken's rate limits.
- Money: `Decimal`/`NUMERIC(20,8)`, JSON strings, formatted only in the UI (MASTER.md rules).
- Frontend: react-router arrives now (deferred by Phase 2 D-03): markets route plus existing account view. TanStack Query refetches about every 60 s.
- Production: scheduler added to `docker-compose.prod.yml`, covered by `deploy.sh` and smoke checks. Whether the phase ends with a release is decided at its push gate.

### Deferred Ideas (OUT OF SCOPE)
- Price charts and history graphs: v2
- Stablecoins in the list: excluded (D-01)
- Public markets page: not now (D-02)
- UI-SPEC: skipped by the user
</user_constraints>

<phase_requirements>
## Phase Requirements

REQUIREMENTS.md was not re-quoted here; IDs and the roadmap success criteria are mapped as given by the orchestrator.

| ID | Description (from success criteria) | Research Support |
|----|-------------|------------------|
| PRICE-01 | Markets page lists ~15 coins with USD prices | Verified Kraken map (below), `coins` seed migration, `GET /api/v1/prices`, markets table |
| PRICE-02 | Each price shows "as of" age and fresh/aging/stale badge | `as_of` column, server-computed status + thresholds in response, client-side ticking age |
| PRICE-03 | Prices update ~60 s without reload, one scheduler | Scheduler container, Redis lock, TanStack `refetchInterval: 60_000` |
| PRICE-04 | Zero/negative/implausible spike rejected, last good kept, ages to stale | Pure `evaluate_price()`, 25% rule + N=3 confirmation, tests |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- MVP first: no speculative models/endpoints/abstractions. No price-history table, no Celery/arq, no charts. Add nginx/other tuning only when needed.
- Money: `Decimal` in Python, `NUMERIC(20,8)` in Postgres, JSON as strings, round only at defined points with `ROUND_HALF_EVEN`, timestamps `timestamptz` UTC.
- Postgres source of truth; Redis only for rebuildable data; every Redis key has a TTL and is named `sim:<resource>:<id>`; cold cache must work; no `KEYS`/`FLUSHALL`.
- Staleness visible: data carries its "as of"; define a max age and refuse actions on older data (Phase 4 consumes this).
- Scheduled jobs run in exactly one dedicated container; lock via `SET key token NX PX ttl` plus Lua compare-and-delete in `finally`; TTL must exceed job duration.
- Retries/external APIs: exponential backoff with jitter, max retry count, respect provider rate limits.
- Thin routes, services own logic; `DbDep`/`CurrentUserDep` aliases; `response_model` and `summary` on every endpoint; `/api/v1/` prefix.
- Schema: bigint identity PKs, `text` not varchar, `timestamptz`, CHECK constraints, index FK columns used in joins, migrations via Alembic (autogenerate then review), immutable once merged, working `downgrade()`.
- Frontend: TanStack Query for all API calls (no `useEffect` fetching), Tailwind/shadcn with MASTER.md tokens only, money formatted in UI only.
- Tests: respx for external APIs, DB tests on the isolated test stack, 80% coverage overall; 100% on money/trade/login/authz critical paths (the `--include` list in CLAUDE.md/CI; consider adding the new price-evaluation module, see Validation). Every feature ships with tests; e2e covers main happy path.
- Python 3.14, `uv add` for deps (never `pip install`), `ruff` + `mypy --strict`; frontend `npm`, eslint/prettier/typecheck.
- Never push without asking; git-flow branches.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Fetch Kraken Ticker every 60 s | Scheduler container (backend image) | — | Must run exactly once; never inside web workers |
| Validate price (positive, crossed book, spike, confirmation) | Scheduler / `services/prices.py` pure function | — | Business rule; unit-testable without I/O |
| Store latest good price | Database (`prices`) | — | Postgres is source of truth; Phase 4 reads it in the trade transaction |
| Single-instance guard | Redis lock + compose (one service) | — | Belt-and-braces per CLAUDE.md |
| Freshness status + age | API (server clock) | Browser (ticks display between refetches) | One definition for Phase 4; avoids client clock skew |
| Coin list | Database seed (`coins`) | — | D-01: data, not UI constants |
| Price formatting | Browser | — | MASTER.md: formatting in UI only |
| Routing (markets vs account) | Browser (react-router) | nginx SPA fallback (exists: `try_files $uri /index.html`) | Deep link `/markets` works in prod already |

## Live Kraken findings (resolves the STATE.md blocker)

All below confirmed by read-only GETs on 2026-10-28 `[VERIFIED: api.kraken.com live GET]`.

**Endpoint:** `GET https://api.kraken.com/0/public/Ticker?pair=<P1>,<P2>,...` (comma-separated, one call for all coins, no key needed). Success: `{"error":[],"result":{<key>:{...}}}`. Failure: HTTP 200 with `{"error":["EQuery:Unknown asset pair"]}` (no `result`). So **HTTP 200 does not mean success; always check `error` is empty and `result` exists**. Bad arguments gave `EGeneral:Invalid arguments`. Rate-limit error text per docs is `EAPI:Rate limit exceeded` `[CITED: docs.kraken.com/api/docs/guides/spot-rest-ratelimits]`.

**Fields** (`result[key]`): `a` ask `[price, wholeLotVolume, lotVolume]`, `b` bid (same shape), `c` last trade `[price, volume]`, plus `v`, `p`, `t`, `l`, `h`, `o`. All numbers are strings. Use `Decimal(b[0])` and `Decimal(a[0])`; mid = (bid + ask) / 2 (matches PROJECT.md: holdings valued at mid). `c` (last trade) is not used.

**Pair map** (all 15 USD quoted, status online). `kraken_pair` is the string to **request and look up**; each was confirmed to come back under that key. `pair_decimals` from AssetPairs (informational; not stored).

| Symbol | kraken_pair (request = response key) | Common alias | pair_decimals | Live mid today (sanity) |
|--------|------|------|------|------|
| BTC | XXBTZUSD | XBTUSD | 1 | ~81,042 |
| ETH | XETHZUSD | ETHUSD | 2 | ~2,361 |
| SOL | SOLUSD | | 2 | ~102.2 |
| XRP | XXRPZUSD | XRPUSD | 5 | ~1.329 |
| BNB | BNBUSD | | 2 | ~747 |
| ADA | ADAUSD | | 6 | ~0.2066 |
| DOGE | XDGUSD | DOGEUSD (alias, request only) | 7 | ~0.07997 |
| TRX | TRXUSD | | 6 | ~0.3308 |
| AVAX | AVAXUSD | | 3 | ~9.015 |
| LINK | LINKUSD | | 5 | ~11.75 |
| DOT | DOTUSD | | 4 | ~1.008 |
| LTC | XLTCZUSD | LTCUSD | 2 | ~57.65 |
| BCH | BCHUSD | | 2 | ~297.1 |
| XLM | XXLMZUSD | XLMUSD | 6 | ~0.1716 |
| ATOM | ATOMUSD | | 4 | ~1.632 |

Notes: DOGE's base asset in AssetPairs is `XXDG`, wsname `XDG/USD`. Requesting `DOGEUSD` returned key `XDGUSD`, so never rely on a requested alias equalling the response key; seed the response key. The orchestrator's order (market cap) is the seed `sort_order`.

**Rate limits:** Kraken's docs describe a per-API-key REST call counter (most calls +1) and give no separate public/IP limit or recommended polling rate `[CITED: docs.kraken.com/api/docs/guides/spot-rest-ratelimits]`. One call per 60 s is far below any known limit. Six rapid sequential Ticker calls all returned 200 today. Responses are served through Cloudflare with `cache-control: public, max-age=1, s-maxage=1` (1 s edge cache; irrelevant at 60 s cadence). Throttle responses may arrive as `EService: Throttled: <unix ts>` or `EAPI:Rate limit exceeded`: treat any non-empty `error` as a failed attempt and back off. Rate-limit specifics for the public endpoint are `[ASSUMED]` beyond the docs (A2).

**Ticker has no timestamp.** `as_of` therefore = the scheduler's UTC time when the HTTP response was received (record `datetime.now(UTC)` right after the response returns, same value for all coins in a call). `GET /0/public/Time` exists if a clock sanity check is ever wanted; not needed in v1.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| httpx | 0.28.1 (already in pyproject) | Kraken client (`httpx.AsyncClient`, timeouts) | Already the project HTTP client; respx mocks it |
| redis (asyncio) | 8.1.0 (existing) | Lock for single-instance guard | Existing dependency |
| SQLAlchemy 2.0 async + asyncpg, Alembic | existing | `coins`, `prices`, seed migration | Existing stack |
| respx | 0.23.1 (existing dev dep) | Mock Kraken at HTTP boundary | CLAUDE.md test rule |
| react-router | 8.5.1 | Routes `/` (markets) and `/account`; `BrowserRouter`, `Routes`, `Route`, `NavLink`, `Navigate` | Standard; Phase 2 D-03 deferred it to now |

No other backend package is needed (no scheduler library; a 30-line asyncio loop). No `decimal.js` needed: the UI only formats strings.

**Installation:**
```bash
cd frontend && npm install --save-exact react-router@8.5.1   # exact pins match the repo convention (see package.json)
```
Backend: no `uv add`.

**Version verification:** `npm view react-router version` returned 8.5.1; engines `node >=22.22.0` (repo uses Node 24); peers react `>=19.2.7` (repo has 19.3.1). Dependencies: `cookie-es`, `@remix-run/route-pattern`. Import everything from `"react-router"` (not `react-router-dom`) `[CITED: reactrouter.com/start/declarative/installation]`. Weekly downloads 49.1M, repo github.com/remix-run/react-router `[VERIFIED: npm registry]`.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| react-router | TanStack Router | More types, new concept; react-router was already named in Phase 2 D-03 |
| In-memory candidate state | Redis/Postgres candidate state | Persisting survives scheduler restarts but adds columns/keys for a rare case (see Spike rule) |
| asyncio loop | APScheduler / Celery | Overkill for one job; contradicts PROJECT.md decision |

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| react-router | npm | many years | 49.1M/wk | github.com/remix-run/react-router | not run (installing slopcheck was denied by the sandbox) | Approved by registry + official docs; tagged `[ASSUMED]` per protocol, planner adds a human-verify check at install |

**Packages removed:** none. **Flagged suspicious:** none. `npm view react-router scripts.postinstall` was not separately checked; the repo installs with `npm ci --ignore-scripts` in deploy.sh anyway. Because slopcheck could not run, the planner should gate the single `npm install react-router@8.5.1` behind a quick `checkpoint:human-verify` (a lone, extremely well-known package; low real risk).

## Architecture Patterns

### System Architecture Diagram

```
                 every 60 s (fixed schedule)
 scheduler ──────────────────────────────────────────┐
 container     1. Redis SET sim:lock:prices NX PX 45s │ (skip cycle if held / Redis down)
 (same image,  2. load active coins from Postgres     │
  own command) 3. GET Kraken Ticker?pair=<all keys>   │──► api.kraken.com (egress via `app` network)
               4. per coin: parse bid/ask → mid       │     retry x3, backoff 1/2/4 s + jitter
               5. evaluate_price(old, mid, candidate) │
                    accept → UPSERT prices (as_of=now)│──► Postgres (source of truth)
                    reject → keep row, log reason     │
               6. release lock (Lua), touch heartbeat │
                                                      │
 browser ─ GET /api/v1/prices (cookie auth) ─► backend (N workers) ─► SELECT coins JOIN prices
    ▲        every 60 s + on window focus              │   compute age_seconds + status (server clock)
    └──────── JSON {server_time, thresholds, items[]} ◄┘
 browser ticks "12 s ago" locally; badge recomputed from thresholds between refetches
```

### Recommended Project Structure
```
backend/app/
├── models/price.py          # Coin, Price
├── schemas/prices.py        # PriceOut, PricesOut (Decimal -> string)
├── services/prices.py       # evaluate_price (pure), freshness(age), list_prices(db), upsert
├── services/kraken.py       # fetch_tickers(http, pairs) -> dict[str, Quote]; parse + error handling
├── tasks/scheduler.py       # run loop, lock, heartbeat, signal handling; `python -m app.tasks.scheduler`
├── api/v1/prices.py         # GET /prices
└── alembic/versions/0004_coins_and_prices.py   # schema (separate from seed per CLAUDE.md)
                    0005_seed_coins.py          # data migration
frontend/src/
├── api/prices.ts            # fetchPrices -> typed, validated
├── hooks/usePrices.ts       # useQuery refetchInterval 60_000
├── lib/age.ts               # formatAge(seconds), freshnessStatus(age, thresholds)
├── lib/money.ts             # add formatUnitPrice (4 sig digits < $1)
├── components/FreshnessBadge.tsx
└── pages/MarketsPage.tsx
```
CLAUDE.md lists `tasks/` for background jobs; use it for the loop even though it is not Celery. Keep `backend/`/`frontend/` independent.

### Pattern 1: Schema (two tables, no history)

```
coins:  id bigint identity PK
        symbol text UNIQUE NOT NULL            -- 'BTC'
        name text NOT NULL                     -- 'Bitcoin'
        kraken_pair text UNIQUE NOT NULL       -- 'XXBTZUSD' (request AND response key)
        sort_order integer NOT NULL            -- market cap order
        is_active boolean NOT NULL DEFAULT true
        CHECK (symbol = upper(symbol))
prices: coin_id bigint PK REFERENCES coins(id)     -- one row per coin; PK is the index
        mid numeric(20,8) NOT NULL CHECK (mid > 0)
        bid numeric(20,8) NOT NULL CHECK (bid > 0)
        ask numeric(20,8) NOT NULL CHECK (ask > 0 AND ask >= bid)
        as_of timestamptz NOT NULL
        source text NOT NULL                   -- 'kraken' (| 'fake' in dev/test)
```
- `bid`/`ask` are stored (not shown on the page) because Phase 4 needs them for the simulated spread basis; storing them now is one extra column pair at the point of writing, not a speculative table. If the planner wants a stricter MVP, drop bid/ask and keep only `mid`; flag as a judgment call (A5).
- No `price_history`, no `last_rejected` columns: rejected observations are logged (structured log with symbol, reason, ratio) which is enough for PRICE-04 and debugging. Phase 4 records the execution price on the trade row (per orchestrator). Phase 5 charts/P&L are v2.
- Seed in a separate data migration `0005` (CLAUDE.md: schema and data separate). `tests/test_migrations.py` asserts head is `"0003"` in three places; those must change to the new head (planner task).
- Precision: all 15 pairs have `pair_decimals <= 7`, so mid of two 7-dp values has at most 8 dp and fits `NUMERIC(20,8)` exactly. Defined rounding point: `mid = ((bid + ask) / 2).quantize(Decimal("1e-8"), ROUND_HALF_EVEN)` once, when computing mid; this is a no-op today but protects against a future 8-dp pair. Store bid/ask as parsed (Kraken pads to 8-9 dp; parse as `Decimal` and quantize to 8 dp with the same rule; `0.079980700` becomes `0.07998070`).

### Pattern 2: `evaluate_price` pure function (D-04 + confirmation)

Decision (recommended, tunable via Settings): reject if `abs(new - last_good) / last_good > 0.25`. **Confirmation:** keep a per-coin in-memory candidate `{anchor: Decimal, count: int}`. A rejected-by-spike observation either starts a candidate (count=1) or, if within **5%** of the candidate anchor, increments it (count+1); outside 5% of the anchor it replaces the candidate (count=1). When `count` reaches **N=3**, the new level is accepted (written with the third observation's mid and `as_of`) and the candidate cleared. Any observation within 25% of the last good price clears the candidate. Invalid observations (non-numeric, <=0, crossed book `bid > ask`, missing key) never touch the candidate.

Timing: a real move is accepted after 3 consecutive polls (about 2 minutes after the first rejected one), when the old price is about 2-3 minutes old, so it is at worst "aging", never reaches the 5-minute stale line before recovery. A single bad tick (the main risk) is never accepted because a single outlier will not be repeated within 5% on the next two polls. `[ASSUMED]` that N=3/5%/25% are good defaults (A3); they are settings with the values above and tests pin them.

First observation for a coin (no row yet) skips the spike check but still requires valid positive finite numbers (a bad first tick would otherwise anchor everything; acceptable at MVP, noted in pitfalls).

State location: in scheduler process memory. It is rebuildable (losing it on restart only delays acceptance by up to 2 more polls), which satisfies the CLAUDE.md rule that Redis/Postgres should not hold the only copy of anything, and avoids an extra table or Redis keys. Because there is exactly one scheduler this is safe. Function signature sketch:

```python
# services/prices.py  (100% covered, in the critical-path list)
@dataclass(frozen=True)
class Candidate:
    anchor: Decimal
    count: int

Decision = Literal["accept", "reject_invalid", "reject_spike", "accept_confirmed"]

def evaluate_price(
    last_good: Decimal | None,
    new: Decimal,
    candidate: Candidate | None,
    *, max_move: Decimal = Decimal("0.25"), confirm_tol: Decimal = Decimal("0.05"), confirm_n: int = 3,
) -> tuple[Decision, Candidate | None]: ...
```
Parsing (string to `Decimal`, `InvalidOperation`, `is_finite()`, `> 0`) lives next to it in `parse_quote()`: reject `NaN`, `Infinity`, empty, negative, zero.

### Pattern 3: Scheduler loop

```python
# tasks/scheduler.py (sketch; adapt)
async def run(settings, stop: asyncio.Event) -> None:
    ...
    next_tick = time.monotonic()
    while not stop.is_set():
        await run_cycle(...)                      # never raises; logs
        HEARTBEAT.touch()                         # /tmp/scheduler-heartbeat (mtime)
        next_tick += INTERVAL                     # fixed schedule, no drift
        delay = next_tick - time.monotonic()
        if delay < 0:                             # overran: skip missed ticks, don't burst
            next_tick = time.monotonic() + INTERVAL
            delay = INTERVAL
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(stop.wait(), timeout=delay)
```
- **Entry point:** `python -m app.tasks.scheduler` with `loop.add_signal_handler(SIGTERM/SIGINT, stop.set)`; on stop finish the current cycle (bounded by the HTTP timeout), close httpx/redis/engine. Docker's default stop grace is 10 s; set `stop_grace_period: 20s` to cover a mid-cycle request.
- **First cycle runs immediately at start** so the page fills in within seconds of boot (no 60 s empty state).
- **Retries:** up to 3 attempts per cycle on timeout, transport error, 5xx, 429, or non-empty `error`; sleep `min(8, 2**attempt) + uniform(0, 1)` s (full jitter acceptable). Unknown-asset-pair errors are not retried (deterministic): log loudly. Overall worst case about 3 x 10 s timeout + 3 s = 33 s, under the 60 s interval. Lock TTL 45 s (> worst case) with token compare-delete in `finally`.
- **Lock** key `sim:lock:price-refresh` (TTL on every key). If lock is held, skip the cycle and log at info. If Redis raises, skip the cycle (fail closed: better to age than to double-write; it never corrupts since upsert is idempotent anyway). `[ASSUMED]` acceptable that a Redis outage pauses prices (Redis outage also blocks sign-in).
- **Upsert** per accepted coin: `INSERT ... ON CONFLICT (coin_id) DO UPDATE SET mid, bid, ask, as_of, source` in one transaction for the cycle. Guard: `WHERE prices.as_of < EXCLUDED.as_of` so a delayed duplicate cannot move time backwards (idempotent re-run safe).
- **Heartbeat/health:** file mtime updated every loop iteration (including failed Kraken cycles, because Kraken being down should show as stale prices, not restart the container). Compose healthcheck: `python -c "import os,sys,time; sys.exit(0 if time.time()-os.path.getmtime('/tmp/scheduler-heartbeat') < 150 else 1)"` with `start_period: 30s`, `interval: 30s`. The runtime image runs as non-root `app` with a home dir; `/tmp` is writable.
- **No DB engine sharing with web:** the scheduler builds its own async engine (same `statement_timeout` settings as `main.lifespan`). CLAUDE.md mentions a sync engine only once Celery exists; not needed.
- **Settings:** extend `Settings` with `price_source: Literal["kraken","fake"]="kraken"`, `price_poll_interval_seconds=60`, `price_fresh_seconds=120`, `price_stale_seconds=300`, spike params. Validators: positive; `price_stale_seconds > price_fresh_seconds`; **`price_source == "fake"` forbidden when `env == "prod"`** (same pattern as the existing `email_backend` console-in-prod rule). Defaults keep existing `Settings()` tests valid (all optional).

### Pattern 4: API

`GET /api/v1/prices` (tag `prices`, `CurrentUserDep`, `response_model=PricesOut`, `summary`, `Cache-Control: no-store`):

```json
{
  "server_time": "2026-10-28T08:10:00.123456Z",
  "fresh_seconds": 120,
  "stale_seconds": 300,
  "items": [
    {"symbol": "BTC", "name": "Bitcoin", "price": "81042.35000000",
     "as_of": "2026-10-28T08:09:12.004211Z", "age_seconds": 48, "status": "fresh"}
  ]
}
```
- `price` is the mid as a Decimal string (Pydantic serializes `Decimal` as string). Items ordered by `coins.sort_order`, then `id` (deterministic). Only active coins that have a price row are returned; empty list on a brand-new stack, UI shows "Prices are loading".
- **Status is computed on the server** via a single `freshness(age_seconds, settings)` function in `services/prices.py` that Phase 4 will reuse to refuse trades. `age = (now_db_or_app_utc - as_of)`; compute with app UTC clock. Scheduler and API share the Docker host clock (same machine), so skew between `as_of` and "now" is nil in prod/dev. The browser clock is never used for status.
- The response also carries `fresh_seconds`/`stale_seconds` so the UI can keep the badge correct between refetches without a second constant (D-03 "sent by the API"). Boundaries: `age < fresh_seconds` fresh; `fresh_seconds <= age <= stale_seconds` aging; `age > stale_seconds` stale. Note MASTER.md says "Fresh (<=120s)"; D-03 says "under 2 minutes". D-03 governs (locked); the one-second boundary difference is immaterial but the tests must pin it. Negative ages clamp to 0.
- Route is thin: calls `prices.list_prices(db, settings)`. No pagination (about 15 bounded rows; offset-free).

### Pattern 5: Frontend

- `main.tsx`: wrap `<App />` in `<BrowserRouter>`. `App.tsx` keeps `AuthSwitch` (the `/me` switch) but replaces the final line: when signed in, render a small nav (`NavLink` Markets / Account) and `<Routes>`: `index` -> `MarketsPage`, `account` -> `AccountPage me={data}`, `*` -> `<Navigate to="/" replace />`. Signed out: `SignInPage` for every URL (D-02), no redirect needed; after sign-in the user lands on the same URL. Keep `HealthPage` where it is, or only on the Account route (planner choice; existing e2e `auth.spec.ts` expects "$10,000.00", the email and the "System status" heading to be visible right after sign-in, which today is all on `/`. Moving Account to `/account` and making Markets the index breaks that e2e: **update `auth.spec.ts` to navigate to Account**, or keep it simple and keep cash visible on the markets page header). Flag in plan.
- `hooks/usePrices.ts`: `useQuery({ queryKey: ["prices"], queryFn, refetchInterval: 60_000, refetchOnWindowFocus: true, staleTime: 30_000 })`. `refetchIntervalInBackground` stays default false; on tab refocus a refetch fires. Because the scheduler polls at 60 s and the UI at 60 s with a random phase, a displayed price can be up to about 120 s old in practice even when the data is "fresh"; that is why the age is shown. Optionally use `refetchInterval: 30_000` for a snappier UI at trivial cost (15 rows); recommended 30 s (A6) while the success criterion says "about 60 s", both satisfy it.
- `apiFetch` already handles 401 via refresh; a 401 that persists makes `useMe` return null on its next refetch. Prices 401 should invalidate `["me"]`; simplest: let `AuthSwitch` remount on sign-out (existing behavior).
- **Ticking age:** `useNow(1000)` hook using `useSyncExternalStore` or a `setInterval` state inside a small `<Age>` component (a timer is not data fetching, so this does not violate the "no `useEffect` fetching" rule). Compute `ageNow = item.age_seconds + (Date.now() - dataUpdatedAt)/1000` using `dataUpdatedAt` from the query (client-side delta only, so server/client clock skew is irrelevant). Recompute status from the thresholds sent by the API. To avoid 15 timers, run one ticking hook in `MarketsPage` and pass `nowMs` down. Fake timers in tests (`vi.useFakeTimers`).
- **Formatting:** `formatUsd` is currently 2-dp only (it tolerates `-?\d+(\.\d+)?`). Add `formatUnitPrice(value: string)` in `lib/money.ts`: if the numeric value < 1, `Intl.NumberFormat("en-US",{style:"currency",currency:"USD",minimumSignificantDigits:4,maximumSignificantDigits:4})`; else 2-dp `formatUsd`. Examples: `0.20663` -> `$0.2066`, `0.07998070` -> `$0.07998`, `0.3308` -> `$0.3308`, `81042.35` -> `$81,042.35`. Decide "less than 1" by comparing the string's integer part (`startsWith("0.")` after validation), not by `parseFloat`, to honor "no JS number arithmetic on money". `[ASSUMED]` that `Intl` with significant-digit options produces exactly these strings for the currency style; add unit tests and adjust (A4).
- **Badge:** `FreshnessBadge` uses the existing `Badge` variants: fresh -> `success` ("Live · 42s ago"), aging -> need a warn variant (`bg-warn-soft text-warn-text`; the `warn` tokens exist in MASTER.md, add a `warning` variant to `badge.tsx`), stale -> `danger` ("Stale · 7m ago"). Text labels carry the state, never color alone (MASTER rule 3); add an icon (lucide `Circle`/`Clock`/`AlertTriangle`). Accessibility: the label is plain text inside the row (readable by screen readers); do **not** make each tick an `aria-live` announcement (1 s updates would spam); announce nothing for age ticks. Wrap the table in a `<table>` with `<th scope="col">` and the header "Markets" with the oldest-price age on the right (MASTER Markets layout). `Trade` button column is Phase 4: not built now.
- `formatAge(seconds)`: `<60` -> `42s ago`, `<3600` -> `7m ago` (floor), else `1h ago`.
- Markets table on mobile: MASTER says stacked cards; implement the simple responsive version (table on `md+`, card rows below) only if cheap; otherwise a single responsive grid row layout.

### Anti-Patterns to Avoid
- **Parsing Ticker by assuming the requested name is the response key.** Look up `result[kraken_pair]` and treat a missing key as a rejected observation for that coin; assert in a test that the seeded map equals the fixture's keys.
- **Treating HTTP 200 as success.** Check the `error` array.
- **Running the loop inside `create_app` lifespan.** Would run once per uvicorn worker (prod uses `--workers 2`).
- **Float math anywhere** (`float(...)`, `Number(...)` on prices). `Decimal(str)` only.
- **Computing status in the browser from `Date.now() - Date.parse(as_of)`.** Clock skew makes badges lie; use server `age_seconds` plus a local elapsed delta.
- **Resetting the stale clock on rejected polls.** Only an accepted observation updates `as_of` (this is exactly what makes a stuck price age to stale).
- **Calling Kraken from tests or CI e2e.**

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Number-to-currency formatting | Manual string slicing | `Intl.NumberFormat` (already used in `money.ts`) | Locale, grouping, rounding |
| Mocking Kraken | Custom fake server in tests | `respx` | Already a dev dependency; project rule |
| Query polling/refocus | `useEffect` + `setInterval` fetching | TanStack Query `refetchInterval`/`refetchOnWindowFocus` | CLAUDE.md rule |
| Routing | Manual `window.location` switch | `react-router` | Deep links, back button, NavLink active state |
| Cron/scheduling framework | APScheduler/Celery | Plain asyncio loop | One job; PROJECT.md decision |
| Distributed lock | `asyncio.Lock` / file lock | Redis `SET NX PX` + Lua compare-delete | Documented in CLAUDE.md; is cross-process |
| Retry/backoff | Ad-hoc sleeps scattered in code | One small `retry_with_backoff` helper (about 15 lines) | Fine to hand-write; no `tenacity` dep for one call site |

**Key insight:** the only genuinely tricky logic is the price-acceptance rule; isolate it as a pure function so it can be tested exhaustively and later reused/read by Phase 4 without I/O.

## Runtime State Inventory

Not a rename/refactor phase. Omitted.

## Common Pitfalls

### Pitfall 1: One bad pair freezes all prices
**What goes wrong:** Kraken returns `EQuery:Unknown asset pair` for the whole batch if any one pair is invalid or delisted. All 15 prices age to stale.
**Why:** Batched request, all-or-nothing validation.
**How to avoid:** `coins.is_active` lets an operator disable one coin via migration; log the Kraken error text at ERROR; add a test with a respx fixture that returns that error; consider (optional) a fallback to per-coin requests when the error is "Unknown asset pair" (adds code; defer unless planner wants it).
**Warning signs:** ERROR logs with the error text; all badges go stale together.

### Pitfall 2: Response key mismatch
**What goes wrong:** Looking up `XBTUSD` in a response that uses `XXBTZUSD` silently yields no price.
**How to avoid:** Seed the response keys from the table above; test that parsing the recorded fixture yields all 15 symbols; treat missing key as a per-coin failure with a WARN.

### Pitfall 3: Kraken 200-with-error and partial results
**How to avoid:** Require `error == []` AND `result` is a dict; per coin require both `a[0]` and `b[0]` parse as finite positive `Decimal`.

### Pitfall 4: Two schedulers
**What goes wrong:** `docker compose up --scale scheduler=2`, a stray dev stack on the same DB, or a zombie container after a failed deploy writes in parallel.
**How to avoid:** One service, no scaling flags in deploy.sh, Redis lock per cycle, upsert guarded by `as_of`, smoke check "exactly one running scheduler container". Never publish a port.

### Pitfall 5: Stale detection depends on only accepted writes
A bug where rejected polls bump `as_of` would hide Kraken outages. Test: reject then assert row `as_of` unchanged.

### Pitfall 6: Sub-dollar formatting looks frozen / wrong
DOGE ($0.07998), TRX, ADA, XLM, DOT, XRP are sub-$2. MASTER rule: 2 dp at >= $1, 4 significant digits below $1. Note XRP (~$1.33), DOT (~$1.01), ATOM (~$1.63) are just above $1 and show 2 dp (`$1.01`); that matches the rule but coarse; flagged as an open design question (Q3).

### Pitfall 7: Existing e2e and migration tests break
`tests/test_migrations.py` hardcodes head `"0003"` three times. `frontend/e2e/auth.spec.ts` expects cash and "System status" on `/` after sign-in. `App.test.tsx` renders `App` without a router; wrap with `MemoryRouter` in tests. `renderWithClient` in `src/test/render.tsx` should gain a router wrapper option.

### Pitfall 8: Dev hot reload and stale compose images
`docker-compose.override.yml` mounts `./backend/app` read-only into `backend` only. The scheduler needs the same mount (and no `--reload`; restart manually or use `docker compose restart scheduler`).

### Pitfall 9: CSP/connect-src
Fetches are same-origin `/api/...`; no CSP change needed `[VERIFIED: existing nginx SPA config and e2e/csp.spec.ts pass for same-origin API calls]`. SPA fallback `try_files $uri /index.html` already exists, so `/account` deep links work in prod.

### Pitfall 10: First-poll spike anchor
If the very first observation for a coin is garbage but positive, later correct prices would look like >25% spikes and need 3 confirmations to recover. Acceptable (self-heals in about 2 minutes); the CHECK constraints stop non-positive values.

## Code Examples

### Kraken client (parse and validate)
```python
# services/kraken.py  -- Source: live responses 2026-10-28; docs.kraken.com/api (Ticker)
TICKER_URL = "https://api.kraken.com/0/public/Ticker"

async def fetch_tickers(http: httpx.AsyncClient, pairs: list[str]) -> dict[str, dict]:
    resp = await http.get(TICKER_URL, params={"pair": ",".join(pairs)})
    resp.raise_for_status()
    body = resp.json()
    if body.get("error") or not isinstance(body.get("result"), dict):
        raise KrakenError(body.get("error"))
    return body["result"]          # {key: {"a": [...], "b": [...], ...}}

def mid_from_ticker(t: dict) -> tuple[Decimal, Decimal, Decimal]:
    bid, ask = Decimal(t["b"][0]), Decimal(t["a"][0])      # InvalidOperation/KeyError -> reject
    ...
    mid = ((bid + ask) / 2).quantize(Decimal("1e-8"), rounding=ROUND_HALF_EVEN)
```
httpx: `params={"pair": "A,B"}` encodes the commas as `%2C`; live behavior of commas vs `%2C` should be confirmed by the respx test matching on `params` (A7: Kraken's server decodes both, the live test used literal commas).

### Lock (CLAUDE.md pattern)
```python
RELEASE = "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end"
token = secrets.token_hex(16)
if not await redis.set("sim:lock:price-refresh", token, nx=True, px=45_000):
    return  # another instance is running this cycle
try:
    ...
finally:
    await redis.eval(RELEASE, 1, "sim:lock:price-refresh", token)
```

### Compose service (dev; prod analogous)
```yaml
scheduler:
  build: { context: ./backend, target: runtime }
  restart: unless-stopped
  stop_grace_period: 20s
  environment: { ENV, DATABASE_URL, REDIS_URL, OTP_HMAC_SECRET, JWT_SECRET, PRICE_SOURCE }   # same as backend (Settings requires them)
  depends_on: { backend: { condition: service_healthy } }   # migrations applied before first cycle
  command: ["python", "-m", "app.tasks.scheduler"]
  networks: [data, app]          # data: Postgres/Redis; app (non-internal): egress to Kraken
  healthcheck: { test: [...heartbeat mtime...], interval: 30s, timeout: 5s, retries: 3, start_period: 30s }
```
`Settings` requires `OTP_HMAC_SECRET`/`JWT_SECRET`; the scheduler does not use them, but reusing `Settings` keeps one config class. Either pass them (simplest, same env) or make a smaller settings class; recommend passing them (no new abstraction). The `data` network is `internal: true` so it has no egress; the `app` network is a normal bridge (prod subnet `172.29.50.0/24`) and gives egress `[VERIFIED: docker-compose.prod.yml; backend already calls Resend over the app network]`.

### Frontend query
```tsx
export function usePrices() {
  return useQuery({
    queryKey: ["prices"],
    queryFn: ({ signal }) => fetchPrices(signal),   // via apiFetch; validates decimal strings
    refetchInterval: 30_000,
    refetchOnWindowFocus: true,
    staleTime: 10_000,
  });
}
```

## Production changes (docker-compose.prod.yml, deploy.sh, smoke)

- Add `scheduler` to `docker-compose.prod.yml`: same `build` as backend, `restart`, `security_opt: no-new-privileges`, `logging: *logging`, `env`: `ENV: "prod"`, DB/Redis URLs, both secrets, `EMAIL_*` as backend (prod `Settings` requires `email_backend == resend` with a key, so the scheduler needs the same `RESEND_API_KEY`/`EMAIL_FROM`/`EMAIL_BACKEND` env or `Settings` raises). **Gotcha:** this validation couples the scheduler to email config; simplest is to pass the same env as backend. Networks `[data, app]`, no ports, `depends_on` postgres/redis healthy and `backend` healthy.
- `deploy.sh`: lines 231/272 `dc build backend` and 242/286 `dc up -d --wait backend` must include `scheduler` (shared image build is cached, so cost is small). Order after migrations: `up -d --wait backend scheduler`. Failure log tail in `on_err` could also tail `scheduler`. The rollback path (line ~272-286) needs the same edit. `deploy/tests/` only tests `rollback_target`.
- `smoke-prod.sh`: add checks (a) exactly one running container with label `service=scheduler` in project `birja-prod` and it is healthy; (b) `prices` freshness: `docker exec <postgres> psql -U ... -tAc "select count(*), extract(epoch from now()-max(as_of)) from prices"` shows 15 rows and max age below 300 s (reads no secrets: the postgres container env already has the creds; do not echo them); (c) no change to the port-exposure check (scheduler publishes nothing); the "data container only on data" check applies to postgres/redis only. Public-mode check: unauthenticated `GET /api/v1/prices` returns 401 (D-02).
- Prod needs outbound HTTPS to `api.kraken.com`; no firewall expectation documented beyond ufw inbound rules, so verify with a smoke or one-off `docker compose run` curl at first deploy (A8).
- Release question stays with the push gate (CONTEXT).

## Testing approach (CI-safe)

- **Unit:** `evaluate_price` table-driven (valid, zero, negative, NaN, huge, exactly 25%, just over 25%, confirmation after 3 within 5%, candidate reset when outside 5%, reset by return to normal, invalid obs not touching the candidate). `freshness()` boundaries at 119/120/121 and 299/300/301 s. `mid_from_ticker` with Kraken padding (`0.079980700`).
- **Kraken client:** respx fixtures: the full 15-coin success payload (record from today's live response, sanitized to values only), `{"error":["EQuery:Unknown asset pair"]}`, `{"error":["EAPI:Rate limit exceeded"]}`, HTTP 500, timeout, malformed JSON, one coin missing, one coin zero.
- **Scheduler cycle:** run `run_cycle()` directly against the test Postgres/Redis stack with respx and an injected clock (`now: Callable[[], datetime]` param) and injected `sleep` for the backoff (no real sleeping). Cases: accept and upsert; reject keeps row and `as_of`; lock held -> no HTTP call (use respx call count); lock released in `finally` after an exception; second call within a cycle does not move `as_of` backwards. The `run()` loop's drift/overrun math can be tested with an injected monotonic clock and a pre-set `stop` event; cover signal handling by setting the event.
- **DB:** migration up/down (extend `test_migrations.py` to new head), CHECK constraints reject `mid <= 0`, `ask < bid`; seed has 15 active coins, unique symbols/pairs.
- **API:** unauthenticated 401, authenticated shape (strings, ISO `Z`, ordering), age/status with fixed times (insert rows with chosen `as_of`; patch the clock in the service via a `now` parameter, not by sleeping), empty-prices case, inactive coin excluded.
- **Frontend (Vitest):** `formatUnitPrice`, `formatAge`, `freshnessStatus`; `MarketsPage` with mocked fetch: 15 rows, badges with text labels, age ticks with fake timers, refetch updates, empty state, error state; `App` routing with `MemoryRouter` (signed out sees sign-in card on `/`, signed in sees markets, `/account` shows cash, unknown path redirects).
- **E2E (Playwright):** extend the happy path: sign in, markets page shows coins with prices and a "Live" badge, navigate to Account. **Do not hit Kraken in CI.** Recommended: `PRICE_SOURCE=fake` makes the scheduler generate deterministic prices for the seeded coins (static table plus tiny wobble); the CI e2e job writes `PRICE_SOURCE=fake` into `.env` after `cp .env.example .env` (leave `.env.example` default `kraken` so local dev uses real data; document `PRICE_SOURCE=fake` as an offline option). The fake source lives behind the same `fetch_tickers`-shaped interface (returns a Ticker-shaped dict), so the scheduler code path (parse, evaluate, upsert) is exercised end to end; it is rejected by `Settings` when `ENV=prod`. This costs about 20 lines and is not speculative: CI e2e cannot work without it. Alternative considered: seeding rows via `docker compose exec psql` in the Playwright test: rejected as brittle and as_of would age.
- Coverage: add `app/services/prices.py` (and `kraken.py` parsing if split) to the 100% critical-path `--include` list in `ci.yml` and CLAUDE.md since the price rule underpins trades; otherwise 80% gate applies. Coverage config measures `source = ["app"]`; the scheduler entrypoint's signal-handling lines may need `# pragma: no cover` only if untestable; prefer testing.

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| `react-router-dom` separate package | Single `react-router` package (v7+; latest 8.5.1) | Import from `"react-router"` |
| Kraken legacy `XXBTZUSD`-style only | Both altnames and canonical keys accepted in requests; responses use canonical keys (XBT/ETH/XRP/LTC/XLM) and `XDG` for DOGE | Seed the response key |
| `ORJSONResponse` | deprecated in FastAPI; use Pydantic serialization | Already a project rule |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | react-router 8.5.1 is legitimate (slopcheck could not run; registry + official docs agree) | Package Legitimacy | Negligible, but install gated by human-verify |
| A2 | Public Ticker has no tighter limit than the documented counter; 1 call/60 s is safe | Live findings | Throttling would show as errors/backoff; low |
| A3 | N=3 polls, 5% tolerance, 25% threshold are sensible defaults | Pattern 2 | Tuning only; user may want a different N |
| A4 | `Intl.NumberFormat` currency + significant digits outputs `$0.2066` style strings | Frontend | Format tweak; covered by unit tests |
| A5 | Storing bid/ask now (for Phase 4 spread) is justified | Schema | Extra columns if Phase 4 changes approach; trivial |
| A6 | UI refetch of 30 s is acceptable vs "about 60 s" | Frontend | Use 60 s if user prefers literal reading |
| A7 | Kraken accepts `%2C`-encoded commas from httpx | Code Examples | Request fails; verify in implementation with one live read-only call outside CI |
| A8 | Prod host has outbound HTTPS to api.kraken.com | Production | Scheduler cannot fetch; verify at first deploy |
| A9 | A Redis outage pausing the price loop is acceptable | Pattern 3 | Prices go stale during Redis outage |

## Open Questions (RESOLVED)

1. **Should AssetPairs verification run at runtime?** RESOLVED: no runtime AssetPairs call in v1 (as recommended); `is_active` + batch-failure log + fixture-vs-seed test.
   - Known: all 15 verified manually today; pair delisting is rare.
   - Unclear: whether to add an automated startup check.
   - Recommendation: no runtime AssetPairs call in v1 (YAGNI); the batch-failure log plus `is_active` covers it. Keep the fixture-vs-seed test.
2. **Where do the markets and account views live in navigation?** RESOLVED: `/` = Markets, `/account` = Account (health card moves to Account); update `auth.spec.ts` (CONTEXT defaults).
   - Recommendation: `/` = Markets, `/account` = Account, tiny header nav; update `auth.spec.ts` accordingly. Needs planner decision on where `HealthPage` goes (suggest Account page).
3. **Sub-dollar rule near $1:** XRP/DOT/ATOM at $1.0x-$1.6x show only 2 dp per MASTER. Accept as specified (recommended) or extend to 4 sig digits below $10. Follow MASTER; raise with user only if it looks bad. RESOLVED: D-06, keep the MASTER rule (>= $1 → 2 dp).
4. **Candidate-state durability:** in-memory chosen. If the user wants restarts not to lose it, move to Postgres columns later. RESOLVED: in-memory candidate state accepted for v1.
5. **Docker image sharing:** prod compose builds `scheduler` separately (cached). Optionally tag one image for both; not required. RESOLVED: planner's discretion (separate cached build is fine).
6. **Release at end of phase?** Deferred to push gate per CONTEXT. RESOLVED: decided at the push gate (CONTEXT).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| api.kraken.com (HTTPS) | Scheduler, this research | yes (dev host) | Ticker/AssetPairs/Time OK | Fake source for CI/dev |
| npm registry | react-router install | yes | 8.5.1 | — |
| Docker / compose, Postgres 18, Redis 8 | stack and tests | existing project infra | pinned in compose | — |
| slopcheck | package audit | no (install denied) | — | human-verify gate |
| Production egress to Kraken | prod scheduler | unverified | — | verify at deploy (A8) |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Backend framework | pytest 9.1.1 + pytest-asyncio 1.4.1 + respx 0.23.1 + pytest-cov |
| Backend config | `backend/pyproject.toml` (`asyncio_mode=auto`, session loop scope) |
| Frontend framework | Vitest 5.0.5 + React Testing Library 16.3.3 |
| E2E | Playwright 1.64.1 (`frontend/e2e/`, full dev compose stack) |
| Quick run | `cd backend && uv run pytest tests/test_prices*.py tests/test_kraken.py tests/test_scheduler.py -x` (needs the test stack up) ; `cd frontend && npx vitest run src/lib src/pages/MarketsPage.test.tsx` |
| Full suite | `cd backend && uv run pytest --cov=app --cov-fail-under=80` ; `cd frontend && npm run test -- --coverage` ; `npx playwright test` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PRICE-01 | 15 seeded coins; API returns them ordered with price strings; page shows rows | integration + unit + e2e | `pytest tests/test_prices_api.py tests/test_seed_coins.py`; `vitest MarketsPage`; playwright `markets.spec.ts` | Wave 0 |
| PRICE-02 | age/status boundaries; badge text; ticking age | unit + component | `pytest tests/test_prices_service.py`; `vitest age.test.ts FreshnessBadge MarketsPage` | Wave 0 |
| PRICE-03 | one cycle fetches and upserts; lock prevents concurrent run; loop cadence; UI refetch interval | integration (respx + test stack) + component | `pytest tests/test_scheduler.py`; `vitest usePrices` | Wave 0 |
| PRICE-04 | zero/negative/NaN/crossed/spike rejected; last good kept; as_of unchanged; confirmation accept after 3 | unit (100%) + integration | `pytest tests/test_prices_service.py tests/test_scheduler.py` | Wave 0 |

### Sampling Rate
- Per task commit: the quick commands for touched files (under 30 s).
- Per wave merge: full backend and frontend suites.
- Phase gate: full suite plus ruff/mypy/eslint/typecheck/prettier green, e2e green, then `/gsd:verify-work`.

### Wave 0 Gaps
- [ ] `backend/tests/test_prices_service.py` (evaluate_price, freshness, mid parsing)
- [ ] `backend/tests/test_kraken.py` + recorded fixture JSON under `backend/tests/fixtures/`
- [ ] `backend/tests/test_scheduler.py` (cycle, lock, loop timing, shutdown)
- [ ] `backend/tests/test_prices_api.py`, `test_seed_coins.py`; update `test_migrations.py` head from `0003`
- [ ] conftest: clean `sim:lock:*` between tests (autouse fixture currently clears `sim:otp:*` and `sim:rl:*`), truncate `prices`
- [ ] Frontend: `age.test.ts`, `money.test.ts` additions, `MarketsPage.test.tsx`, `App.test.tsx` router wrapper, `test/render.tsx` router option
- [ ] `frontend/e2e/markets.spec.ts` and the `auth.spec.ts` update; CI e2e writes `PRICE_SOURCE=fake` into `.env`
- [ ] Framework install: only `react-router`

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no (existing) | unchanged |
| V3 Session Management | no (existing) | unchanged |
| V4 Access Control | yes | `/api/v1/prices` behind `CurrentUserDep` (401 when signed out, D-02); test it |
| V5 Input Validation | yes | Untrusted external data: strict `Decimal` parse, finite, positive, bounded move; Pydantic response schemas; GET has no user input |
| V6 Cryptography | no | none added |
| V12/V13 (data/API) | yes | Kraken is HTTPS with certificate verification (httpx default); explicit timeouts; response size is small |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Poisoned/garbage upstream price (bug, glitch, MITM) | Tampering | Positive/finite/crossed-book checks, 25% spike rule with confirmation, DB CHECKs, stale surfacing |
| Fake price source reachable in prod | Tampering / Elevation | `Settings` forbids `price_source=fake` when `env=prod`; never a route |
| Upstream outage or throttling causing hammering | DoS | Fixed 60 s cadence, bounded retries with backoff and jitter, single instance |
| SSRF | — | Fixed Kraken URL constant; no user-supplied URLs or pairs (pairs come from DB seed) |
| Unauthenticated data access | Info disclosure | `CurrentUserDep`; `Cache-Control: no-store` |
| Secrets/PII in logs | Info disclosure | Log symbols, reasons and ratios only; never env or keys (scheduler holds same secrets as backend) |
| Scheduler container breakout | Elevation | non-root user (runtime image `app`), `no-new-privileges`, no published ports |

## Sources

### Primary (HIGH)
- Live read-only GETs to `https://api.kraken.com/0/public/{AssetPairs,Ticker,Time}` on 2026-10-28 (pair names, response keys, field shapes, error format, 6 rapid calls OK)
- Repo files: `backend/app/core/{config,deps}.py`, `main.py`, `api/v1/me.py`, `alembic/versions/0003`, `tests/conftest.py`, `docker-compose{,.override,.test,.prod}.yml`, `deploy/deploy.sh`, `deploy/smoke-prod.sh`, `.github/workflows/ci.yml`, `frontend/src/{App,main}.tsx`, `lib/money.ts`, `components/ui/badge.tsx`, `design-system/birja/MASTER.md`
- reactrouter.com/start/declarative/installation (package name, `BrowserRouter`, latest 8.5.1)
- npm registry via `npm view react-router` (8.5.1, engines, deps, 49.1M downloads/week)

### Secondary (MEDIUM)
- docs.kraken.com/api/docs/guides/spot-rest-ratelimits (counter semantics; public-endpoint specifics not stated)

### Tertiary (LOW)
- None beyond the assumptions log.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH (existing deps; one new package verified against registry and docs)
- Kraken pair map and formats: HIGH (live verified today)
- Rate limits: MEDIUM (docs silent on public endpoint)
- Architecture and thresholds: MEDIUM-HIGH (N=3/5%/25% are proposals)
- Pitfalls: HIGH

**Research date:** 2026-10-28
**Valid until:** 2026-11-27 (re-check the pair map if any coin is delisted; Kraken API is stable)
