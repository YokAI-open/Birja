# Development approach: MVP first

Build the smallest working version first, then grow it in steps. Never build the whole product at once.

- **v1 = MVP**: only the features needed to deliver the core value end to end. Everything else is v2+ (backlog, seeds, later phases), not part of the first build.
- **Each step leaves the app working**: a phase ends with something runnable and usable, not half-built layers waiting for later phases.
- **No speculative code**: don't add models, endpoints, settings, abstractions or UI for features that aren't in the current step. If a request would pull in out-of-scope work, say so and offer to park it in the backlog instead of building it.
- **Stack grows with need**: the tech stack below is the target, not a day-one checklist. Add a component (e.g. RabbitMQ/Celery, nginx tuning) in the step that first needs it, and say why when you add it.
- When planning (e.g. `/gsd-new-project`, `/gsd-plan-phase`), push back on bloated v1 scope and propose what can move to v2.

# Current project: v1 scope

Planning lives in `.planning/` (GSD): `PROJECT.md` (scope + key decisions), `REQUIREMENTS.md` (REQ-IDs), `ROADMAP.md` (6 phases), `STATE.md` (where we are). Read them before planning or building.

- **v1 = crypto only**, ~10–20 curated coins, market orders (by $ incl. fee, or by quantity), fixed % simulated spread + fee, $10k start with no reset, portfolio + trade history, deployed for a few friends. Everything else is v2 (see `REQUIREMENTS.md`).
- **Prices**: Kraken public Ticker, polled every ~60s by **one simple scheduler-loop container** (no Celery/arq in v1). Holdings are valued at **mid** price.
- **Email**: Resend for one-time codes, sent via FastAPI `BackgroundTasks`; console backend in dev.
- **Branches**: the repo's `main` plays the `master` role below; `develop` was created from it.

# Tech stack

- **Backend**: FastAPI on Python 3.14, SQLAlchemy 2.0 (async) + `asyncpg`, Alembic migrations, Pydantic v2. Dependencies and virtualenv managed with `uv` (`pyproject.toml` + committed `uv.lock`). Never `pip install` into the project directly.
- **Data**: PostgreSQL (primary datastore), Redis (cache, session/rate-limit state, Celery broker/result backend).
- **Background jobs**: *MVP*: Celery + beat with Redis as the broker, or a single scheduler process for a few periodic jobs. Run scheduled jobs in exactly one dedicated container, never inside every web worker, or they run once per worker. *Later*: RabbitMQ as the Celery broker, once job volume or delivery guarantees justify another service.
- **Frontend**: React (Vite + TypeScript), npm (committed `package-lock.json`).
  - *UI*: Tailwind CSS + shadcn/ui components (source copied into `src/components/ui/`, ours to edit). Colors, fonts and style come from the design system in `design-system/<project>/MASTER.md`. Don't invent ad-hoc colors or fonts.
  - *Server data*: TanStack Query for all API calls: caching, loading/error states, refetching. No hand-rolled `useEffect` fetching.
- **Infra**: Docker Compose. nginx (reverse proxy, TLS, static files) is added when the app is first deployed outside local dev.
- **CI**: GitHub Actions. Lint, type checks and the full test suite run on every PR into `develop`/`master`.
- **Lint/format**: `ruff` + `mypy` (backend); `eslint`/`typescript-eslint`/`eslint-plugin-react-hooks` + `prettier` (frontend).

# Common commands

Update this block whenever the real commands change. CI runs the same commands.

```bash
# First run, then local dev (full stack). App: http://localhost:5173, API docs: http://127.0.0.1:8000/docs
cp .env.example .env
docker compose up --build
# After frontend dependencies change (package.json): recreate the anonymous node_modules volume,
# or Vite keeps the old one and fails with "Failed to resolve import"
docker compose up --build -d --wait --renew-anon-volumes
docker compose logs -f scheduler   # price refresh loop (one container)
docker compose restart scheduler   # after backend code changes (no auto-reload)
# PRICE_SOURCE=fake in .env runs offline with deterministic prices (dev/CI only; prod refuses it)

# Backend deps
cd backend && uv sync --locked              # install from uv.lock
cd backend && uv add <pkg>                  # add a dependency (updates uv.lock)

# Backend tests: against the isolated test stack, never the dev stack
docker compose -f docker-compose.test.yml up -d --wait
cd backend && uv run pytest --cov=app --cov-fail-under=80
# critical paths: login/OTP, sessions, authz, money, trade execution
cd backend && uv run coverage report --include=app/services/otp.py,app/services/auth.py,app/services/accounts.py,app/services/ratelimit.py,app/services/email.py,app/core/security.py,app/core/deps.py,app/services/price_rules.py,app/services/prices.py,app/services/trade_math.py,app/services/trading.py --fail-under=100
docker compose -f docker-compose.test.yml down -v

# Frontend tests
cd frontend && npm run test -- --coverage   # Vitest

# e2e (needs the full stack running)
docker compose up --build -d --wait
cd frontend && npx playwright test

# Production (on the server, as root). Details: deploy/RUNBOOK.md
/srv/birja/deploy/deploy.sh                 # deploy main (DEPLOY_REF=<ref> for another ref)
/srv/birja/deploy/deploy.sh --rollback      # back to the previous deploy
/srv/birja/deploy/smoke-prod.sh [--public]  # success-criteria checks

# Lint, format, types
cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy app
cd frontend && npm run lint && npm run typecheck && npx prettier --check .

# Migrations: autogenerate, then review the file (see Database migrations).
# The dev Postgres publishes no host port, so run alembic on the host against the
# test stack at head (docker compose -f docker-compose.test.yml up -d --wait first):
cd backend
export DATABASE_URL=postgresql+asyncpg://birja_test:test@127.0.0.1:55432/birja_test
export REDIS_URL=redis://:test@127.0.0.1:56379/0
# alembic/env.py loads Settings, which requires ENV and both secrets (test-only dummies):
export ENV=test
export OTP_HMAC_SECRET=test-only-otp-secret-not-for-prod-000000
export JWT_SECRET=test-only-jwt-secret-not-for-prod-000000
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "<message>"
# The dev stack applies migrations on backend start, or manually:
docker compose exec backend alembic upgrade head
```

# Git workflow (git-flow)

**Before creating a branch, update its base** (`git switch develop && git pull`). On an existing branch that has an upstream, `git pull` before continuing work. Model: nvie.com/posts/a-successful-git-branching-model.

- `master` — production-ready, never commit directly. `develop` — integration branch, default base for new work.
- **Feature/regular change** → `feature/<name>` from `develop`, merge back into `develop`.
- **Release prep** → `release-<version>` from `develop`, merge into `master` + `develop`, tag on `master`.
- **Urgent prod fix** → `hotfix-<name>` from `master`, merge into `master` + `develop`, tag on `master`.
- Always `merge --no-ff`; delete branches after merging; never merge into `master` except via `release-*`/`hotfix-*`.
- Merges into `develop`/`master` go through a GitHub PR (e.g. `/gsd-ship`), merged with **"Create a merge commit"** (the PR equivalent of `--no-ff`), not squash or rebase. Merge only after CI is green and I approve.

## Pushing

Never push without asking. At the end of every step that produced commits (a GSD phase, a `/gsd-quick` task, a feature or fix), stop and ask whether we're ready to push:

- Show a short summary: current branch, commits not yet pushed (`git log --oneline @{u}..` or since branching), and whether tests/lint passed.
- Suggest the target branch (normally the current `feature/*`, `release-*` or `hotfix-*` branch to `origin`) and let me choose: push, push and open a PR, or not yet.
- Never push directly to `master`/`develop` unless I explicitly choose that, and never force-push without explicit approval.
- If there's no remote configured, say so instead of skipping the question silently.

## Commit messages

- Subject line: short, imperative mood ("Fix ...", "Add ..." — not "Fixed"/"Adds"), meaningful on its own since tools like `gitk`/`shortlog` show it in isolation.
- Leave a blank line, then a body wrapped at ~72 chars explaining *why* the change was made — the diff already shows *what* changed.
- Add trailers where relevant (`Reported-by:`, `Co-authored-by:`, etc.).

# Project structure

Standard FastAPI + React + Docker Compose layout (e.g. tiangolo's full-stack-fastapi-postgresql):

```
.
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI routers, versioned (api/v1/...)
│   │   ├── core/           # settings, security, shared dependencies
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── services/       # business logic + DB access (add crud/ only once queries get reused across services)
│   │   ├── tasks/          # background/scheduled jobs (Celery)
│   │   ├── db/             # session, base, init
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   └── Dockerfile
├── frontend/
│   ├── src/{components,pages,hooks,api}/
│   ├── e2e/                # Playwright
│   └── Dockerfile
├── nginx/nginx.conf        # added at first deployment
├── docker-compose.yml
├── docker-compose.override.yml
└── .env.example
```

- Keep `backend/`/`frontend/` independent — no cross-imports. New code goes in its layer (router→`api/`, model→`models/`, logic→`services/`), not directly in routers.
- `app/db/` holds an async engine (FastAPI), plus a sync engine once Celery tasks exist (workers have no event loop).

# Money and numbers

- Prices, balances, quantities and anything else monetary use `Decimal` in Python and `NUMERIC(p, s)` in Postgres. Never `float`. Default to `NUMERIC(20, 8)`. Two decimal places (`numeric(10,2)`) can't hold crypto quantities like 0.00015 BTC or FX rates.
- Send monetary values in JSON as strings (Pydantic `Decimal` serialization), not numbers, so JavaScript doesn't lose precision. Format them for display only in the UI.
- Round explicitly with `quantize(..., rounding=ROUND_HALF_EVEN)` at defined points, such as when a trade executes, to the precision of the asset or currency involved. Never round implicitly, and never round intermediate results.
- Store all timestamps as timezone-aware UTC (`timestamptz`), and convert to local time only in the UI.

# Data, caching & background jobs

- **Postgres is the source of truth.** Redis only holds data that can be lost or rebuilt: cache entries, one-time codes, rate-limit counters. Never keep the only copy of anything in Redis.
- **Transactions**: any change that touches several rows as one business action (e.g. a trade: debit cash, update the holding, insert the trade record) runs in a single DB transaction. Lock the rows it reads and then updates (`SELECT … FOR UPDATE` via `with_for_update()`), so two concurrent requests can't spend the same balance.
- **Let the schema enforce invariants**: `NOT NULL` wherever possible, foreign keys, `UNIQUE`, and `CHECK` constraints (e.g. cash and quantities `>= 0`). Don't rely on application code alone.
- **Column types**: primary keys `bigint GENERATED ALWAYS AS IDENTITY` (not `int`, not random UUIDs); `text` instead of `varchar(n)` unless a real length limit exists, with the limit enforced by a `CHECK`; `timestamptz`, never `timestamp`; `boolean` for flags.
- **Indexes**: index columns used in `WHERE`/`JOIN`/`ORDER BY` of real queries. Every index slows writes, so add them for queries that exist, not speculatively. In practice:
  - Postgres does **not** index foreign keys automatically. Add an index for every FK column you join or filter on.
  - In composite indexes, put equality columns first and range columns last (e.g. `(user_id, created_at)` for "this user's trades, newest first").
  - Use partial indexes (`WHERE status = 'open'`) or covering indexes (`INCLUDE (...)`) when a query hits only a slice of the table.
- **Pagination**: every list query has a deterministic `ORDER BY` that ends in a unique column (e.g. `created_at, id`). Use keyset pagination (`WHERE (created_at, id) < (:last_created_at, :last_id)`) for growing lists such as trade history. Offset is fine only for small, bounded lists.
- **DB timeouts**: set `statement_timeout` and `idle_in_transaction_session_timeout` on the app's role (e.g. 30s each), so a stuck query or forgotten transaction can't hold locks forever. Enable `pg_stat_statements` and use it plus `EXPLAIN ANALYZE` to find slow queries.
- **No large blobs in Postgres**: store files elsewhere and keep only their location.
- **Scaling order**, only when measurements demand it: tune queries and indexes → cache → read replicas → partition hot tables. Denormalize (e.g. snapshot tables, materialized views) only for proven read-heavy joins. Sharding and federation are out of scope for this project's scale.
- **Caching pattern**: default to cache-aside with an explicit TTL: read the cache, on a miss load from the source, then store it. Cache objects or values, not hashed SQL queries, which are hard to invalidate. When the underlying data changes, delete the cache entry. For a known set of hot keys (e.g. prices of the tracked assets), a scheduled job may refresh them before they expire (refresh-ahead). Never use write-behind for anything monetary: it loses data if Redis dies.
- **Redis roles and eviction**: Redis holds three kinds of data: cache (fine to evict), and the Celery queue plus one-time codes and rate-limit counters (must not be evicted silently). Eviction policy is per *instance*, so separate DB numbers don't protect the queue. *MVP*: one instance with `maxmemory-policy noeviction`, a TTL on every key, and an alert on memory use. *Later*: split into a cache instance (`allkeys-lru`) and a state/broker instance (`noeviction`).
- **Redis keys**: name keys `<app>:<resource>:<id>[:<field>]` (e.g. `sim:price:BTC-USD`, `sim:otp:<email-hash>`). Every key has a TTL. Never use `KEYS *` or `FLUSHALL` in app code: use `SCAN` and scoped deletes.
- **Redis primitives** (async, via `redis.asyncio`):
  - *Rate limits*: a fixed window (`INCR` + `EXPIRE` in one pipeline) is enough for the MVP. Switch to a sliding window (atomic Lua script on a sorted set) only if bursts at window edges become a problem.
  - *Locks* (e.g. "only one price refresh at a time"): `SET key <random token> NX PX <ttl>`, released by a Lua script that deletes the key only if it still holds your token. The TTL must exceed the expected job duration. Always release in `finally`.
  - *Stampede protection*: on a cache miss, take the lock above before calling the source. Others wait briefly and re-read the cache. Never use in-process `threading`/`asyncio` locks for this, because they don't work across workers.
- **Cold cache is normal**: the app must work, just slower, with an empty or unavailable cache. Never fail a request only because a cache entry is missing.
- **Staleness is visible**: cached or external data (e.g. prices) carries its "as of" timestamp. Show it in the UI, and record the exact value and timestamp used when an action depends on it (e.g. the execution price of a trade). Define a maximum acceptable age for such actions, and refuse the action with a clear message rather than use data older than that.
- **Sync vs async**: cheap work the user waits for (e.g. executing a trade) runs synchronously in the request. Queue only slow or non-critical work (sending email, refreshing prices, daily snapshots). A queue adds delay and complexity.
- **Jobs can be lost or run twice**: Redis as a broker can lose messages, and any broker can deliver one twice. Every task is idempotent and safe to re-run, and nothing critical depends only on a queued message arriving.
- **Retries and back pressure**: calls to external APIs and task retries use exponential backoff with jitter and a max retry count, and respect the provider's rate limits. Bound queue sizes. When overloaded, return `503` with `Retry-After` rather than queueing without limit.

# Database migrations (Alembic)

- **Every schema change is a migration.** Never alter a database by hand, and never create tables with `Base.metadata.create_all()` on app startup.
- **Autogenerate, then review.** `alembic revision --autogenerate` is a draft: read every generated migration before committing. Autogenerate misses some changes (e.g. `CHECK` constraints, server defaults, some type changes), so add those by hand.
- **Migrations are immutable once merged into `develop`.** To fix one, write a new migration. Every migration has a working `downgrade()`, or says explicitly that it's irreversible.
- **Schema and data changes are separate migrations.** Backfills on large tables run in batches, not one giant `UPDATE`.
- **Safe column changes**: new columns are nullable or have a server default. Never add `NOT NULL` without a default to a table that has rows. Rename or remove columns with expand-contract: add the new column → backfill → switch the code → drop the old one in a later migration.
- **Indexes on existing tables**: `CREATE INDEX CONCURRENTLY` (in Alembic: `op.create_index(..., postgresql_concurrently=True)` inside `with op.get_context().autocommit_block():`). It can't run in a transaction.

# API

- **App setup**: build the app in a `create_app()` factory, and open/close shared resources (DB engine, Redis pool, `httpx.AsyncClient`) in the `lifespan` context manager, not at import time.
- **Dependencies**: define reusable `Annotated` aliases in `core/` (e.g. `DbDep = Annotated[AsyncSession, Depends(get_db)]`, `CurrentUserDep`) instead of repeating `Depends(...)` in every endpoint.
- **Thin routes**: a route parses input, calls one service method and maps domain errors to HTTP errors. Services own transactions and business rules.
- **Uniqueness and races**: rely on DB constraints, not "check then insert". Insert, catch `IntegrityError`, then raise a domain error (e.g. `409 Conflict`). A pre-check alone is a race condition.
- **Auth errors**: `401` means not authenticated (missing or invalid token). `403` means authenticated but not allowed. Keep the checks separate so the status codes are correct.
- **JWT library**: `PyJWT`. Not `python-jose`, which is effectively unmaintained.
- **Docs**: FastAPI auto-generates OpenAPI + Swagger UI (`/docs`) and ReDoc (`/redoc`) — no extra library needed. Give every endpoint a `summary`/`description` and explicit `response_model`; group routers with `tags=[...]` so Swagger UI stays navigable (prod exposure rules are under Security).
- **Versioning**: version in the URL path (`/api/v1/...`, matching the `api/v1/` structure above). Bump to `/api/v2/` only for breaking changes; additive, backward-compatible changes (new optional fields, new endpoints) stay in the current version. *Later, once there are clients we don't deploy together with the API*: run old and new versions side by side during a deprecation window, and announce removal via a `Deprecation`/`Sunset` response header before dropping a version.

# Performance & scalability

During the MVP, the async/no-blocking FastAPI rules, Redis TTLs and pagination always apply. Everything else here (worker sizing, PgBouncer, replicas, nginx tuning, horizontal scaling) is applied when deployment or profiling calls for it, not up front.

- **nginx**: gzip/br + HTTP/2, `limit_req`/`limit_conn` rate limiting (stricter on `/login` etc.), immutable long-lived cache headers on Vite's hashed build output.
- **FastAPI**: run with `uvicorn[standard]` (uvloop/httptools) using its own `--workers N` (or `fastapi run --workers N`), starting at one worker per CPU core; explicit timeouts at every hop; `async def` + async I/O (`asyncpg`, `httpx.AsyncClient`, `redis.asyncio`) for all network calls. Never block the event loop with sync libs (wrap unavoidable ones in `anyio.to_thread.run_sync`) or run CPU-bound work inline (push to Celery instead). Batch independent I/O with `asyncio.gather`. Eager-load SQLAlchemy relationships (`selectinload`/`joinedload`) to avoid `MissingGreenlet`. Return data via `response_model`/return types and let Pydantic serialize it (`ORJSONResponse` is deprecated in FastAPI, so don't add `orjson`); keep response schemas and middleware minimal.
- **PostgreSQL**: tuned async pool (PgBouncer once process count grows); select only needed columns; batch writes. Indexes, pagination, timeouts and the scaling order are in "Data, caching & background jobs".
- **Redis**: one pooled async connection per process. Keys, TTLs, locks and stampede protection are in "Data, caching & background jobs".
- **RabbitMQ/Celery**: offload slow/non-critical work to idempotent tasks; bound prefetch/concurrency; scale `worker` independently of `backend`.
- **Docker Compose**: stateless containers, one per service, scaled horizontally; state only in named volumes; `healthcheck:` on every service.
- **Frontend**: route-based code-splitting, memoize only where profiling shows a win, virtualize long lists, modern image formats + lazy loading, watch bundle size.
- Profile (`py-spy`/`pyinstrument`/React DevTools) before optimizing — don't guess at bottlenecks.

# Security

Hard rules — flag/refuse insecure requests rather than quietly implementing them.

- **Secrets**: never hardcode credentials/keys; load via Pydantic `BaseSettings` from a git-ignored `.env` (commit only `.env.example`); rotate anything ever committed.
- **Injection**: SQLAlchemy ORM/bound params only, never raw SQL string-building; validate all input with Pydantic; rely on React's default escaping (avoid `dangerouslySetInnerHTML`); never `subprocess(shell=True)` with unsanitized input.
- **No backdoors**: no hidden routes/auth bypasses/debug routers reachable outside local dev (gate by `settings.ENV` at import time); disable `/docs`/`/redoc`/OpenAPI schema in prod; never disable CORS/CSRF/auth checks to unblock local dev.
- **Login**: only email + one-time code — no password field, so no password storage/hashing is needed at all.
  - *Code*: generate a 6-digit code with `secrets`. Store only an **HMAC-SHA256 of it keyed with a server secret** (a plain hash of a 6-digit code is reversed in seconds by trying all 1,000,000 values) in Redis, with a short TTL (~10 min). Compare with `hmac.compare_digest`. A code is single-use and dies after **5 wrong attempts**. Requesting a new code invalidates the old one. Never store or log the raw code.
  - *Rate limits*: limit code requests and verification attempts per email and per IP, to block enumeration and brute force.
  - *No enumeration*: "code sent" responses are identical whether or not the email has an account.
  - *Sending email*: one-time codes need a transactional email provider (SMTP or an email API). Keep its credentials in `.env`, send from a background job rather than inside the request, and use a console/log backend in local dev so no real email is sent.
- **Session**: after a successful code check, issue your own tokens, both in cookies. Never in `localStorage` or JS-readable storage.
  - *Access token*: short-lived JWT (~15 min) in an `HttpOnly`, `Secure`, `SameSite=Strict` cookie.
  - *Refresh token*: a random opaque token (~30 days) in its own `HttpOnly` cookie, scoped to the refresh endpoint's path. Store only its hash in **Postgres** (so it survives a Redis restart and can be revoked). Rotate it on every use; if an already-used refresh token is presented, revoke that user's whole token family. Logout deletes it server-side.
  - *CSRF*: because auth is cookie-based, every state-changing request (`POST`/`PUT`/`PATCH`/`DELETE`) needs a CSRF token (double-submit cookie + header).
  - Authorize server-side on every route (`Depends(get_current_user)`) — never trust the frontend; explicit CORS origins, never `*` with credentials; never log tokens/PII.
- **Transport**: TLS 1.2+/1.3 only at nginx, redirect HTTP→HTTPS; `Strict-Transport-Security`/`Content-Security-Policy`/`X-Frame-Options`/`X-Content-Type-Options`/`Referrer-Policy` headers; `server_tokens off`.
- **Infra**: non-root containers; Postgres/Redis (and RabbitMQ, once added) ports internal-only (separate Docker networks, nothing published to host); pinned image versions + scans (`trivy`).
- **Datastores**: least-privilege Postgres role (not superuser) + SSL; Redis `requirepass`; RabbitMQ (once added) non-default creds and management UI internal-only.
- **Dependencies**: committed lockfiles (`uv.lock`, `package-lock.json`); regular `pip-audit`/`npm audit`, run in CI.

# Test culture

- Every new feature ships with tests in the same PR (bug fixes: regression test where practical); fail CI on regression.
- **Coverage gate in CI**: 80% overall (backend and frontend), and 100% on critical paths: money calculations, trade execution, login/one-time codes, authorization checks. Plus API tests for every endpoint. Coverage measures what ran, not what was checked, so tests must assert behavior, not just execute lines.
- **Backend**: `pytest`+`pytest-asyncio`, `httpx.AsyncClient` against the app, run against an isolated `docker-compose.test.yml` stack (own Postgres/Redis, plus RabbitMQ once added, `tmpfs` volumes) — never the dev stack, never mock the DB for anything that matters. Mock external APIs (e.g. market-data providers) at the HTTP boundary (`respx`), never call them from tests.
- **Frontend**: `Vitest` + React Testing Library for units; `Playwright` for e2e (full stack via Compose, real user flows). *MVP*: e2e covers only the main happy paths, then expands with each phase.
- Full suite (backend + frontend + e2e) must pass in CI (GitHub Actions) before merging into `develop`/`master`. Set up the CI workflow in the first phase that adds tests, not at the end.