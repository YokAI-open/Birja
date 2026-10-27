# Walking Skeleton: YokaiExchange

**Phase:** 1
**Generated:** 2026-10-26

## Capability Proven End-to-End

A developer runs `cp .env.example .env && docker compose up --build`, opens http://localhost:5173, and sees API, Database and Redis shown as "Connected". The browser fetches this live from `GET /api/v1/health` through TanStack Query and the Vite proxy, and the backend checks it with a real `SELECT 1` on Postgres and a `PING` on Redis. Every PR into `develop`/`main` then runs the same checks in GitHub Actions, aggregated into one `ci-pass` check.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Backend framework | FastAPI 0.162 on Python 3.14, `create_app()` factory + `lifespan` owning the async engine and Redis pool, `uvicorn app.main:create_app --factory` | CLAUDE.md stack; no import-time resources, so tests can build apps with their own settings |
| Response serialization | Pydantic `response_model` / return types, FastAPI default response class, no `orjson` (D-02) | `ORJSONResponse` is deprecated in FastAPI; Pydantic serializes `Decimal` as JSON strings, which the money rules need |
| Backend layering | Route (`api/v1/`) -> service (`services/`) -> DB/Redis via `Annotated` deps in `core/deps.py` (`DbDep`, `RedisDep`, `SettingsDep`) | CLAUDE.md "thin routes"; every later endpoint follows the health endpoint's shape |
| Data layer | PostgreSQL 18.6 via SQLAlchemy 2.0 async + asyncpg; Alembic async template; `Base` with a constraint naming convention; empty baseline revision `0001` | Every schema change is a migration from day one. No domain tables in Phase 1 (CLAUDE.md: no speculative models); Phase 2 adds the first (users/accounts) |
| DB read/write in the skeleton | Read: health `SELECT 1`. Write: Alembic writes `alembic_version` on every backend start | The thinnest real DB round-trip without inventing a table |
| DB timeouts | `statement_timeout` and `idle_in_transaction_session_timeout` = 30 s through asyncpg `server_settings` | CLAUDE.md DB-timeout rule without a custom role; `ALTER ROLE` hardening is Phase 6 |
| Cache / state store | Redis 8.8.3, `requirepass`, `maxmemory-policy noeviction`, `redis.asyncio` client | CLAUDE.md MVP Redis rule; Phase 1 writes no keys |
| Settings / secrets | pydantic-settings `Settings` from env; compose builds `DATABASE_URL`/`REDIS_URL` from a git-ignored `.env`; `.env.example` holds placeholders only | CLAUDE.md secrets rule |
| Frontend | React 19 + Vite 8 + TypeScript 6.0 (not 7.x), TanStack Query 5 for all server data, Tailwind 4 (CSS-first `@theme`) + shadcn/ui (`card`, `badge`, `button`) | CLAUDE.md stack; TS 7 is incompatible with typescript-eslint 8.72 |
| Design system | Every token from `design-system/yokaiexchange/MASTER.md` as CSS variables mapped in `@theme inline`; Inter Variable self-hosted; light mode only; no raw hex in components | MASTER.md is the single source of colors/fonts |
| Frontend -> backend | Relative `/api/...` URLs; Vite dev proxy to `VITE_PROXY_TARGET` (`http://backend:8000` in Compose). No CORS config | Same-origin in dev; nginx takes over the same role in Phase 6 |
| Routing | Backend: URL-versioned `/api/v1/...`. Frontend: single page, no router yet | react-router arrives in Phase 2 with the first second page |
| Auth | None in Phase 1 | Email one-time code + JWT/refresh cookies + CSRF arrive in Phase 2 |
| Containers | Docker Compose: `postgres`, `redis`, `backend`, `frontend`, each with a healthcheck; backend runs as uid 1001, frontend as `node`; datastores only on an `internal: true` `data` network, no published ports; dev override publishes 8000/5173 on 127.0.0.1 only | CLAUDE.md infra/security rules |
| Backend image | Multi-stage: `builder` (`uv sync --locked`, venv in `/opt/venv`), `test-builder` (adds dev group, used by CI smoke test), `runtime` (non-root) | `--locked` proves the image builds from `uv.lock` on 3.14; `/opt/venv` survives dev bind mounts |
| Testing | Backend: pytest + pytest-asyncio (session loop scope) + httpx `ASGITransport` against `docker-compose.test.yml` (tmpfs Postgres/Redis on 127.0.0.1:55432/56379), guarded so tests refuse any other DB. Frontend: Vitest + RTL with stubbed `fetch`. E2E: exactly one Playwright test against the full Compose stack (D-03). 80% coverage gates | CLAUDE.md test culture |
| CI | One GitHub Actions workflow: `backend`, `frontend`, `image`, `e2e` jobs, aggregated by `ci-pass`, the single required check (D-01) | Adding jobs later never touches branch protection |
| Deployment target | Phase 1: documented local full-stack run (`docker compose up --build`). Public server, nginx, TLS, backups: Phase 6 | ROADMAP; nginx is added when the app first leaves local dev |
| Directory layout | `backend/app/{api/v1,core,db,schemas,services}`, `backend/alembic`, `backend/tests`; `frontend/src/{api,hooks,pages,components/ui,lib,test}`, `frontend/e2e`; root compose files + `.github/workflows/ci.yml` | CLAUDE.md "Project structure"; `models/` and `tasks/` are created only when first used |

## Stack Touched in Phase 1

- [ ] Project scaffold: backend (uv, ruff, mypy, pytest) and frontend (Vite, ESLint, Prettier, Vitest, Playwright): plans 02, 04, 06
- [ ] Routing: `GET /api/v1/health` (backend) and the single status page at `/` (frontend): plans 02, 05
- [ ] Database: real read (`SELECT 1` in the health check) and real write (Alembic `alembic_version` on startup and in the migration test): plans 02, 03
- [ ] UI: the status page polls every 15 s, and the "Check again" button refetches through TanStack Query: plan 05
- [ ] Deployment: documented local full-stack run, `cp .env.example .env && docker compose up --build`, proven by the Playwright test in plan 06 and in CI in plan 07

## Human Prerequisites and Parallel Tasks (not code)

- **Feature branch (plan 01):** all Phase 1 work happens on `feature/phase-01-skeleton-and-ci`, created from an up-to-date `develop`. Plan 07 pushes it and opens a PR into `develop`, but only with the user's approval.
- **Toolchain (plan 01):** install uv and Node 24 locally. `docker compose up --build` works without them, but lint/test/scaffold commands need them.
- **Package legitimacy (plan 01):** the user confirms the Phase 1 package list before anything is installed.
- **Domain + Resend DNS (start now, outside the plans):** buy the domain and begin Resend domain verification (SPF/DKIM, DMARC `p=none`). DNS takes wall-clock time; Phase 2 email delivery and Phase 6 deployment depend on it. No code is planned for this.
- **Branch protection (plan 07, D-01):** make the repo public, upgrade the GitHub plan, or rely on convention.

## Out of Scope (Deferred to Later Slices)

- Users, accounts, sign-in codes, sessions, CSRF, CORS, react-router (Phase 2)
- Coins, the price scheduler container, Kraken client, respx, Redis price cache (Phase 3)
- Trades, `decimal.js`, money rounding code, row locking (Phase 4)
- Portfolio, history, keyset pagination (Phase 5)
- nginx, TLS, production Compose/Dockerfile targets, a least-privilege Postgres role + SSL, backups, uptime `/healthz` (Phase 6)
- Celery/arq/RabbitMQ, orjson, structured logging, extra shadcn components, dark mode (v2 or when first needed)

## Subsequent Slice Plan

Each later phase adds one vertical slice on top of this skeleton without changing the decisions above:

- Phase 2: A user signs in with an emailed one-time code, stays signed in, and gets a $10,000 account once (first models + migrations, auth cookies, CSRF, react-router)
- Phase 3: A user sees ~10-20 coins with live prices and "as of" ages, refreshed by one scheduler container
- Phase 4: A user buys and sells at real prices with an itemized preview and a correct fill
- Phase 5: A user sees portfolio value, P/L and paginated trade history
- Phase 6: Friends use the app on a public HTTPS domain with nightly backups
