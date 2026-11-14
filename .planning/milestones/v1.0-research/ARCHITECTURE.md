# Architecture Patterns

**Domain:** Crypto paper-trading web app (virtual USD, real prices, market orders only)
**Researched:** 2026-10-20
**Confidence:** MEDIUM-HIGH. The patterns come from standard ledger/brokerage design and the fixed rules in CLAUDE.md. I did not verify provider-specific details (see Gaps).

## Recommended Architecture

A modular monolith with one extra process. This fits tens of users and the MVP-first rule.

```
Browser (React/Vite, TanStack Query)
   |  HTTPS, cookies (access JWT, refresh, CSRF)
   v
[nginx]  (added in deploy slice; Vite dev server / direct in dev)
   |
   v
[backend: FastAPI, N uvicorn workers]  -- never schedules jobs
   |-- api/v1 routers (thin)
   |-- services: auth, prices, trading, portfolio
   |       |
   |       +--> Postgres (source of truth)
   |       +--> Redis (OTP HMAC, rate limits, price cache, locks)
   |
[scheduler: ONE container]  -- price refresh job every ~60s
   |-- httpx --> market-data provider (free tier)
   |-- writes: Postgres (latest_prices upsert) then Redis (cache set)

[email]: Resend via background send (console backend in dev)
```

MVP process count: `backend`, `scheduler`, `postgres`, `redis` (plus `frontend` in dev). nginx joins at deploy. No RabbitMQ.

**Scheduler choice (opinionated):** use a single dedicated scheduler process (APScheduler `AsyncIOScheduler`, or a plain `asyncio` loop) for the price refresh. It reuses the async engine, `httpx.AsyncClient` and `redis.asyncio`. Celery would need a sync engine, a worker, and beat for one periodic job. CLAUDE.md allows "a single scheduler process for a few periodic jobs". Adopt Celery only when email sending or snapshot jobs make a queue worthwhile.

**OTP email sending:** the "send from a background job" rule is satisfied cheaply with FastAPI `BackgroundTasks` (in-process, after the response). This has no queue and no new service. It is fire-and-forget and loses the email if the process dies, which is acceptable because the user can request a new code. Upgrade to Celery only if delivery guarantees are needed. The 200 "code sent" response must not depend on whether the email was sent, to avoid enumeration timing leaks.

### Component Boundaries

| Component | Responsibility | Talks To |
|-----------|---------------|----------|
| `api/v1/*` routers | Parse input, call ONE service method, map domain errors to HTTP | services only |
| `core/` | Settings, `DbDep`/`CurrentUserDep`/`CsrfDep` aliases, security (JWT, HMAC, CSRF), error types | all layers |
| `services/auth` | OTP issue/verify, session + refresh rotation, user get-or-create | Postgres, Redis, email sender |
| `services/prices` | Provider client, upsert latest prices, cache read (cache-aside, DB fallback), freshness check | Postgres, Redis, provider |
| `services/trading` | Quote and execute (transaction, locks, rounding) | Postgres, `services/prices` (read only) |
| `services/portfolio` | Valuation of cash + holdings at latest prices, P/L | Postgres, `services/prices` |
| `services/email` | Interface with Resend and console implementations | Resend API |
| `scheduler` (`tasks/`) | Calls `prices.refresh_all()` on an interval, with lock | `services/prices` |
| Frontend `api/` + `hooks/` | Typed fetch wrapper (credentials, CSRF header, Decimal strings), TanStack Query hooks | backend only |
| Frontend `pages/` | Routed screens | hooks |

Rules: the scheduler and the web app share `services/prices` code but run in different processes (the `backend/` layer is one codebase and two entrypoints). Trading never calls the provider. It reads only the latest price already stored, so a trade never depends on provider uptime.

## Data Model

All money and quantity columns: `NUMERIC(20,8)`. PKs: `bigint GENERATED ALWAYS AS IDENTITY`. All timestamps `timestamptz` (UTC). Every column `NOT NULL` unless noted.

### users
- `id`, `email text UNIQUE` (store lowercased/normalised; CHECK `email = lower(email)`), `created_at`.

### accounts (cash balance, 1:1 with user)
- `id`, `user_id UNIQUE FK`, `cash NUMERIC(20,8) CHECK (cash >= 0)`, `starting_cash NUMERIC(20,8)` (10000; stored for the P/L baseline, so a config change never rewrites history), `created_at`.
- Created in the same transaction as the user (the $10k grant happens once, because user creation is guarded by the UNIQUE email constraint).
- Could be merged into `users`; keep it separate only if you expect multiple accounts or currencies later. For the MVP, **merging `cash` and `starting_cash` onto `users` is the smaller schema**. Recommendation: separate `accounts` is still cheap, and gives one lock target distinct from the identity row. Pick `accounts` and lock it.

### assets (curated list)
- `id`, `symbol text UNIQUE` (e.g. `BTC`), `name text`, `provider_id text` (the provider's coin id), `quantity_decimals smallint` (quantity precision, e.g. 8), `is_active boolean`.
- Seeded by a data migration (separate from the schema migration). Adding a coin = new migration or seed script, never a user action.

### latest_prices (one row per asset, upserted)
- `asset_id PK/FK`, `price NUMERIC(20,8) CHECK (price > 0)` (mid), `as_of timestamptz` (**the provider's observation timestamp if given, else fetch time**), `fetched_at timestamptz`, `source text`.
- Upsert by `INSERT ... ON CONFLICT (asset_id) DO UPDATE`. Guard against out-of-order writes with `WHERE excluded.as_of > latest_prices.as_of`.
- No price history table in v1 (the value-over-time chart is v2). The trade record preserves the price used, which is all v1 needs.

### holdings (current position, derived-but-stored)
- `id`, `account_id FK`, `asset_id FK`, `quantity NUMERIC(20,8) CHECK (quantity >= 0)`, `cost_basis NUMERIC(20,8) CHECK (cost_basis >= 0)` (total USD spent on the remaining quantity, including fees), `updated_at`. `UNIQUE (account_id, asset_id)`.
- **Store total cost, not average cost.** Average = `cost_basis / quantity`, computed when displayed. Storing the average introduces rounding drift on every buy.
- On buy: `quantity += q`, `cost_basis += notional + fee`. On sell: reduce cost basis proportionally: `cost_basis -= cost_basis * (q_sold / quantity_before)`, rounded once with `ROUND_HALF_EVEN`. When the quantity reaches 0, set `cost_basis = 0` (CHECK enforces consistency: `quantity = 0 -> cost_basis = 0`). This is the average-cost method, which is simple and standard. FIFO lots are out of scope.
- Decision to settle at requirements time: whether the fee counts into the cost basis (recommended: yes for buys, so P/L shows the true cost). Realised P/L on sells is stored on the trade row (below).
- The unique constraint `(account_id, asset_id)` doubles as the index for lookups.

### trades (immutable ledger)
- `id`, `account_id FK`, `asset_id FK`, `side` (CHECK in `('buy','sell')`), `quantity NUMERIC(20,8) CHECK (>0)`, `mid_price`, `executed_price` (mid with spread applied), `spread_rate`, `fee_rate`, `notional` (`quantity * executed_price`, rounded), `fee`, `price_as_of timestamptz` (the timestamp of the mid used), `cash_delta` (signed: negative for buy = notional + fee, positive for sell = notional - fee), `realized_pnl NUMERIC(20,8) NULL` (sells only), `created_at`.
- Index `(account_id, created_at DESC, id DESC)` for the keyset-paginated history. Add an index on `asset_id` only if a query needs it.
- Insert-only. No UPDATE or DELETE path exists in code (and optionally a trigger or a revoked privilege on the app role).
- Storing rates and `mid_price` alongside the results makes every trade auditable without joining config history.

### Auth tables
- `refresh_tokens`: `id`, `user_id FK`, `family_id` (uuid or bigint, groups a rotation chain), `token_hash text UNIQUE` (SHA-256 of the opaque token; a fast hash is fine for a 256-bit random value), `expires_at`, `used_at NULL`, `revoked_at NULL`, `created_at`. Index on `user_id` (revoke all) and `family_id`.
- OTP lives only in Redis (not in Postgres), per CLAUDE.md.

### Ledger vs stored balances: the trade-off

| Approach | Pros | Cons |
|----------|------|------|
| Pure ledger (derive cash and holdings by summing trades) | Cannot drift; perfect audit | Every read aggregates; no cheap row to lock; `CHECK (cash >= 0)` impossible; concurrency control is hard |
| Balances only | Fast, lockable, CHECKable | No audit trail; bugs are unrecoverable |
| **Both: ledger + materialised balances updated in the same transaction (recommended)** | Row locks and CHECK constraints protect invariants; ledger allows verification | Two sources must agree, so test it |

Recommendation: balances are authoritative for enforcement (`accounts.cash`, `holdings.quantity`), and the trades ledger is the audit trail. Add a **reconciliation test** (and optionally a small admin check script) asserting for every account: `starting_cash + SUM(cash_delta) == cash` and `SUM(signed qty) == holdings.quantity`. This gives the ledger's integrity benefit without the aggregate-on-read cost, and it directly serves "correct to the cent".

## Data Flow

### Price ingestion (scheduler -> provider -> Postgres + Redis)

```
scheduler tick (every 60s)
  1. acquire Redis lock  sim:lock:price-refresh  (SET NX PX ttl > job duration; token; release via Lua in finally)
  2. ONE batched provider call for all active assets (e.g. a "markets"/"simple price" endpoint with comma-separated ids). Never one call per coin.
  3. validate: price present, > 0, Decimal parsed from string (never float), plausible vs previous (reject jumps > configured % as bad data, log)
  4. Postgres: upsert latest_prices (single statement/transaction)   <- source of truth FIRST
  5. Redis: SET sim:price:<SYMBOL> {price, as_of} EX ~180            <- cache SECOND
  6. on provider failure: log, back off (exponential + jitter, max retries, respect Retry-After / 429), keep old rows (they simply go stale)
```

Readers (cache-aside): `GET /prices` and the quote path read Redis (`MGET`), and on a miss or Redis outage fall back to Postgres `latest_prices`, optionally repopulating Redis. A cold cache never fails a request. Because the scheduler refreshes all hot keys before TTL expiry (refresh-ahead), a stampede lock on read is unnecessary here: the DB fallback is a single cheap row-per-asset query, so skip read-side locking in the MVP.

**Staleness / max age:**
- Config `PRICE_MAX_AGE_SECONDS` (suggest 180s = 3 refresh cycles, which tolerates one or two missed cycles) and `PRICE_REFRESH_SECONDS` (60).
- Age is computed server-side as `now() - as_of` where `as_of` is the price's own timestamp. Do not use `fetched_at` if the provider reports a staler observation time.
- Every price API payload carries `as_of` plus a server-computed `age_seconds` and an `is_stale` flag. The UI shows "as of 12:03 UTC (45s ago)" and disables the trade button when stale.
- **The authoritative check is inside the execution transaction**, against the price row read there. The client-side flag is only UX. Refusal returns a clear error (e.g. `409`/`422` with code `PRICE_STALE`).
- The Postgres row is the one used for execution, not Redis. This keeps the recorded `price_as_of` exactly what was read and removes cache inconsistency from the money path. (Redis is for browse/quote speed only.)

### Trade execution (quote then execute)

Two endpoints:

1. `POST /api/v1/quotes` (or `GET /quote?symbol&side&amount|quantity`) reads only, **no DB writes and no CSRF need if GET**. It returns: `mid`, `executed_price` (spread applied), `quantity`, `notional`, `fee`, `total` (cash required or received), `as_of`, `age_seconds`, `expires_at`, plus a feasibility flag (insufficient cash or holdings). It uses the same pure pricing function as execution, so preview and result cannot disagree.
2. `POST /api/v1/trades` (CSRF required) takes `{symbol, side, quantity | amount, quote_price_as_of?}` and executes. The client does not send a price. The server uses the latest price. Optionally the client sends the `as_of` of the quote it displayed, and the server rejects with `409 PRICE_CHANGED` if the latest price differs, so the user confirms what they saw. For a 60s-refresh app this is a nice-to-have. Recommended for correctness-to-the-cent. A simple alternative is to execute at the latest price and show the real result. Decide in the trading phase.

Execution inside one transaction (service owns it):

```
BEGIN
  1. SELECT accounts WHERE user_id=:u FOR UPDATE            (serialises this user's trades)
  2. SELECT holdings WHERE (account, asset) FOR UPDATE      (may not exist on first buy; INSERT ... ON CONFLICT DO NOTHING first, then lock)
  3. SELECT latest_prices WHERE asset_id=:a                 (read; check as_of age <= max, else abort PRICE_STALE)
  4. compute via pure function (Decimal, no float):
       buy : exec = mid*(1+spread) ; sell: exec = mid*(1-spread)
       by amount: quantity = quantize(amount / exec, asset qty decimals, ROUND_DOWN-or-HALF_EVEN*)
       notional = quantize(quantity*exec, 8, HALF_EVEN) ; fee = quantize(notional*fee_rate, 8, HALF_EVEN)
       buy  : cash_delta = -(notional+fee) ; sell : cash_delta = +(notional-fee)
  5. validate: buy needs cash >= notional+fee ; sell needs holding.quantity >= quantity ; quantity > 0 ; min notional
  6. UPDATE accounts.cash ; UPSERT holdings (qty, cost_basis) ; INSERT trades row (all recorded fields)
COMMIT   (CHECK constraints are the backstop; map IntegrityError to a domain error)
```

*Rounding rules (define once, in one module, 100% tested):* quantize at fixed points only: quantity (when derived from a dollar amount), notional, fee, cost-basis reduction. Never round intermediate results. Execution price is stored at full computed precision up to 8 dp (quantize once, store, and compute notional from the **stored** executed price so the ledger is internally reproducible). For amount-based orders, rounding the derived quantity *down* (so the user never spends more than the amount entered) is the friendlier convention; this is a decision to make explicitly and document. Keep `ROUND_HALF_EVEN` for the money fields as CLAUDE.md requires.

Locking order is always accounts -> holdings, which prevents deadlocks. Locking the account row first serialises all of one user's trades, which is simple and enough at this scale. Idempotency: accept an optional `Idempotency-Key` header, with a `UNIQUE (account_id, idempotency_key)` column on trades, so a double-click or retry cannot double-trade. Cheap, and directly protects "correct to the cent". Recommended in the trading phase (small), not a v2 item.

### Auth flow components

```
POST /auth/request-code {email}
  rate limit per email + per IP (Redis INCR+EXPIRE pipeline)
  code = secrets 6-digit ; store HMAC-SHA256(server_secret, email|code) at sim:otp:<email-hash> TTL 10m, attempts=0 (replaces any old code)
  email via BackgroundTasks -> Resend (console in dev)
  ALWAYS return identical 200 body/timing
POST /auth/verify-code {email, code}
  rate limit ; hmac.compare_digest ; attempts++ ; >=5 wrong -> delete ; success -> delete (single use)
  get-or-create user (+account with $10k in same txn; UNIQUE email, catch IntegrityError on race)
  issue: access JWT (15m, PyJWT) cookie HttpOnly/Secure/SameSite=Strict ;
         refresh opaque token (30d) cookie, Path=/api/v1/auth/refresh, hash in Postgres ;
         CSRF token cookie (JS-readable) for double-submit
POST /auth/refresh   rotate: mark used, issue new in same family ; reuse of a used token -> revoke family
POST /auth/logout    delete refresh row, clear cookies
GET  /auth/me        CurrentUserDep (401 if unauthenticated)
```

Components: `OtpStore` (Redis), `RateLimiter` (Redis fixed window), `EmailSender` (interface: Console, Resend), `TokenService` (JWT + refresh rotation), `CsrfDep` (applied to all state-changing routes), `CurrentUserDep`. Note: the CSRF cookie must be readable by JS while the auth cookies are not. The SPA wrapper copies the cookie into an `X-CSRF-Token` header. `SameSite=Strict` cookies and a frontend served same-origin (via the Vite proxy in dev, nginx in prod) avoid CORS entirely, so do that instead of configuring cross-origin CORS.

### Portfolio valuation

`GET /portfolio` reads: the account, all holdings joined to `latest_prices` (one query, plus the asset), and computes server-side (Decimal): per holding `market_value = quantity * mid`, `avg_cost = cost_basis/quantity`, `unrealized_pnl = market_value - cost_basis`, pnl %; totals: `holdings_value`, `total_value = cash + holdings_value`, `total_pnl = total_value - starting_cash`. Valuation uses **mid** (not the sell price) and the UI should label this. Decide that explicitly: a mid valuation makes P/L right after a buy show the loss of spread + fee only if valuation is at the bid. Recommended: value at **mid** for simplicity; note that this shows a small initial gain relative to the true liquidation value. Alternatively value at the sell price (mid*(1-spread)) so "what it's worth now" equals what you would get. Given the core value "see what it's worth now", valuing at the sell-side price (liquidation value) is the more honest choice, and is a one-line config. Flag for requirements decision. Include the oldest `as_of` among the used prices in the response.

Compute on read; no snapshots in v1.

## Frontend Pages

| Route | Purpose | Data |
|-------|---------|------|
| `/login` | Email entry, then code entry (one page, two steps) | `request-code`, `verify-code` |
| `/` or `/markets` | Coin list: price, "as of" with age, stale badge, Trade button | `GET /prices` (poll about 30-60s via `refetchInterval`) |
| `/trade/:symbol` (or modal on markets) | Buy/sell form: by amount or quantity, live quote preview with spread + fee + total, confirm | `GET /quote`, `POST /trades` |
| `/portfolio` | Cash, holdings with avg cost and P/L, total value, total P/L | `GET /portfolio` |
| `/history` | Trades table, keyset "load more" (`useInfiniteQuery`) | `GET /trades?cursor=` |

Plus an app shell with auth guard (`/auth/me`), a 401-triggered silent refresh in the fetch wrapper (single in-flight refresh, then retry once), and an error/stale banner. Money values arrive as strings and are formatted only for display. Do the arithmetic for previews on the server, not in JS floats (use the quote endpoint, debounced). Invalidate `portfolio`, `trades` and `prices` queries after a successful trade.

## Patterns to Follow

### Pattern 1: Pure pricing/rounding module
**What:** One `services/trading/pricing.py` of pure `Decimal` functions (quote, fee, cost basis) used by both quote and execute.
**When:** Always. It is the 100%-coverage critical path and is unit-testable without a DB.

### Pattern 2: Postgres-first, cache-second writes
**What:** The scheduler writes Postgres and then Redis. Money paths read Postgres only.
**When:** All price data.

### Pattern 3: Lock the account row, then work
**What:** `SELECT ... FOR UPDATE` on the account first in every trade. Constraints are the backstop.
**Example:**
```python
async with session.begin():
    acct = (await session.execute(
        select(Account).where(Account.user_id == uid).with_for_update())).scalar_one()
    ...
```

### Pattern 4: Same-origin deployment
**What:** The SPA and the API share an origin (Vite proxy in dev, nginx in prod). **Why:** it makes SameSite=Strict cookies and CSRF simple and removes CORS.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Client-supplied price
**Why bad:** It lets users trade at any price. **Instead:** the server picks the price. The client may only send the `as_of` it saw, for a conflict check.

### Anti-Pattern 2: Trading reads the Redis cache
**Why bad:** Cache can be stale or evicted; the recorded timestamp may not match. **Instead:** read `latest_prices` in the transaction.

### Anti-Pattern 3: Storing average cost
**Why bad:** Rounding drift. **Instead:** store total cost basis and derive the average.

### Anti-Pattern 4: Scheduler inside web workers
**Why bad:** Runs once per worker (CLAUDE.md). **Instead:** the dedicated scheduler container, plus the Redis lock as a safety net.

### Anti-Pattern 5: Float anywhere in the money path
Including provider JSON: parse with `json.loads(..., parse_float=Decimal)` or `httpx` text -> `Decimal(str)`.

### Anti-Pattern 6: Check-then-insert for first holding or user
**Instead:** `INSERT ... ON CONFLICT DO NOTHING`, or catch `IntegrityError`.

## Scalability Considerations

| Concern | 10s of users (target) | 10K users | 1M users |
|---------|-----------------------|-----------|----------|
| Trade contention | Per-account lock; trivial | Same; locks are per user, not global | Same |
| Price reads | Redis MGET, DB fallback | Same | Replicas, CDN-cached /prices |
| Price refresh | One batched call/min | Same | Same, plus a streaming feed |
| History | Keyset index on `(account_id, created_at, id)` | Same | Partition trades |
| Portfolio valuation | Compute on read | Same | Snapshot table (also enables the v2 chart) |

Out of scope per CLAUDE.md: sharding, replicas now.

## Suggested Build Order (vertical slices)

Each slice ends runnable and tested. CI starts in slice 1. The stack grows only when needed.

| # | Slice | Delivers (runnable end to end) | Depends on | Adds to stack (why now) |
|---|-------|--------------------------------|------------|--------------------------|
| 1 | **Skeleton + CI** | `docker compose up` gives FastAPI `/health` (checks DB + Redis), a React page that calls it via TanStack Query, the Alembic baseline, `docker-compose.test.yml`, GitHub Actions (ruff, mypy, pytest cov, eslint, vitest), `develop` branch exists. Node upgrade + Tailwind + shadcn + design system (`MASTER.md`) here (first frontend phase). | none | Postgres, Redis, backend, frontend. First tests, so CI now. |
| 2 | **Auth (OTP + session)** | Enter an email, get a code (console log in dev), land logged in, `/me`, refresh, logout; account row with $10k created on first login; protected app shell. Resend adapter behind the interface (enable on deploy at the latest). | 1 | `users`, `accounts`, `refresh_tokens`; Redis OTP/rate limit; CSRF; BackgroundTasks email. 100% coverage here. |
| 3 | **Prices** | `assets` seeded; the scheduler container fetches the provider every minute, upserts `latest_prices`, and fills the cache. Markets page shows the coin list with "as of" and a stale badge. | 1 (2 only for page auth; backend ingestion is independent and could be built in parallel) | `scheduler` container, `httpx`, `respx` tests, Redis lock, backoff. |
| 4 | **Trading** | The quote preview (spread + fee shown), the confirm, the transaction. Cash and holdings change, trade rows are written, stale prices refused, the first minimal "result" feedback. The pure pricing module and concurrency tests (two parallel buys cannot overspend). | 2 (account), 3 (prices) | `holdings`, `trades`, constraints, idempotency key. Highest-risk slice: put the most review and 100% coverage here. |
| 5 | **Portfolio + history** | Cash, holdings with average cost and P/L, totals vs $10k; the keyset-paginated trade history page. Also the reconciliation test. | 4 | No new tables. Pure read side, so it is low risk. |
| 6 | **Deploy** | nginx (TLS, headers, static, rate limits), prod compose, domain, Resend live, docs disabled in prod, secrets, backups of Postgres, Playwright happy-path e2e in CI, the friends sign up. | 1-5 | nginx, Resend creds, prod env. |

**Ordering rationale:**
- Auth before trading because trades need an authenticated account to own cash. Prices before trading because a trade needs a price row.
- Slices 2 and 3 are independent of each other, so they can be reordered or overlapped. Recommended: auth first because the account row is the trade's lock target and auth has the most security surface to get right early. If the provider choice is uncertain, a prices spike first de-risks the free-tier question.
- Portfolio comes after trading, because holdings only exist once trades do. Splitting "trading" and "portfolio" keeps each slice small, but trade execution needs some visible feedback (the result response and a toast), so slice 4 should show the resulting balance without waiting for slice 5.
- Deploy last, but write the nginx and prod-compose files knowing the same-origin assumption from slice 1. Consider a throwaway early deploy smoke test to catch Secure-cookie and TLS surprises, because `Secure` cookies do not work over plain HTTP outside localhost.

**v2 candidates to push back on in v1 scope:** value-over-time chart and snapshot job, Celery/RabbitMQ, price history table, FIFO lots, realized-P/L reporting views, admin UI, WebSocket prices, multiple providers/failover. (Keep `realized_pnl` on the trade row only if the history UI shows it. Otherwise defer the column, because adding a nullable column later is cheap.)

## Gaps

- The market-data provider is not chosen here (see STACK.md): confirm its batch endpoint, rate limits, whether it reports a per-price observation timestamp, and its attribution terms. This determines the `as_of` semantics.
- Valuation basis (mid or liquidation price) and amount-to-quantity rounding direction need explicit product decisions.
- Python 3.14 compatibility of `asyncpg`, `uvloop` and `pydantic-core` wheels was not verified in this pass.

## Sources

- /home/Birja/CLAUDE.md (fixed rules: layering, transactions, Redis, auth). HIGH.
- /home/Birja/.planning/PROJECT.md (requirements and scope). HIGH.
- Design patterns (ledger plus materialised balances, average-cost basis, idempotency keys, row-lock serialisation): established brokerage and accounting practice from training knowledge, not re-verified online. MEDIUM.
