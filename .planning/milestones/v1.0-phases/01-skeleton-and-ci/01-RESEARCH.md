# Phase 1: Skeleton and CI - Research

**Researched:** 2026-10-26
**Domain:** Walking skeleton: FastAPI + React + Postgres + Redis in Docker Compose, plus GitHub Actions CI
**Confidence:** HIGH on versions and patterns, MEDIUM on shadcn-init-with-TS6 and branch protection outcome

<user_constraints>
## User Constraints

No CONTEXT.md exists for this phase (user chose to plan from research + requirements). No UI-SPEC (user chose skip).

### Locked Decisions (project-level, from CLAUDE.md and PROJECT.md, treat as locked)
- Python 3.14, FastAPI, SQLAlchemy 2.0 async + asyncpg, Alembic, Pydantic v2, `uv` with committed `uv.lock`. Never `pip install` into the project.
- Frontend: React + Vite + TypeScript, npm with committed `package-lock.json`, Tailwind + shadcn/ui (source in `src/components/ui/`), colors/fonts only from `design-system/yokaiexchange/MASTER.md`, TanStack Query for all API calls (no hand-rolled `useEffect` fetching).
- Docker Compose; `healthcheck:` on every service; non-root containers; Postgres/Redis ports not published to host in the dev/prod stack; pinned image versions.
- Redis `requirepass`, `maxmemory-policy noeviction`. Create the app in a `create_app()` factory; open/close DB engine + Redis pool in `lifespan`.
- Lint/types: `ruff` + `mypy` (backend); `eslint`/`typescript-eslint`/`eslint-plugin-react-hooks` + `prettier` (frontend). Coverage gate 80%.
- Tests against the isolated `docker-compose.test.yml` stack, never the dev stack. CI set up in this phase.
- MVP-first: no speculative models/endpoints/settings. nginx, Celery/arq, Resend, JWT are NOT in this phase.
- Git-flow: feature branch from `develop`, PR into `develop` with merge commit. Never push without asking.

### Claude's Discretion
Everything else (file layout details, CI job split, Dockerfile targets, whether e2e is in CI).

### Deferred Ideas (OUT OF SCOPE)
Auth, prices, scheduler, trading, portfolio, nginx/TLS/deploy, arq/Celery, Resend, react-router, decimal.js, dark mode.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FOUND-01 | One `docker compose up` starts the full stack and the frontend talks to the backend | Compose layout, `/api/v1/health` endpoint (DB+Redis), Vite proxy, TanStack Query health page, healthchecks |
| FOUND-02 | Every PR into `develop`/`main` runs lint, types, tests in GitHub Actions; a failure blocks merge | `ci.yml` job design, aggregate `ci-pass` job, branch protection (BLOCKED on free private repo, see Open Question 1) |
</phase_requirements>

## Summary

All versions in the project-level STACK.md still hold as of today (re-checked on PyPI, npm and Docker Hub), with three updates: FastAPI is now **0.162.0**, SQLAlchemy 2.1.6 is out (still pin `<2.1`), and **`ORJSONResponse` is deprecated by FastAPI** (official docs: declare a return type/`response_model` and Pydantic serializes to JSON bytes). So drop the CLAUDE.md "default_response_class=ORJSONResponse" rule and do not install `orjson` in this phase. Flag this as a CLAUDE.md deviation for the user to confirm.

The skeleton is small: a `create_app()` with a lifespan that owns an async SQLAlchemy engine and a `redis.asyncio` pool, one endpoint `GET /api/v1/health` (does `SELECT 1` and `PING`, returns 200 or 503), an empty Alembic baseline, a Vite/React/Tailwind 4/shadcn page that polls that endpoint through TanStack Query, `docker-compose.yml` (+ override), `docker-compose.test.yml` (tmpfs Postgres + Redis on localhost-only ports), and one `ci.yml`.

**Two blockers need a human decision before the plan can promise success criterion 2:** (1) the GitHub repo is private on a free plan, and the branch-protection and ruleset APIs both return 403 ("Upgrade to GitHub Pro or make this repository public"), so "a failing check blocks the merge" cannot be enforced by GitHub as things stand [VERIFIED: `gh api repos/YokAI-open/YokaiExchange/branches/main/protection` returned 403]. (2) Local machine has Node 18, Python 3.12 and no `uv`; Docker 29.2.1 and Compose v5.0.0 are present. Docker-only `docker compose up` works without them, but local lint/test commands need Node 24 and uv.

**Primary recommendation:** Build backend skeleton + test stack + CI first (plans 1-2), frontend with design tokens next (plan 3), wire compose + health page + optional single Playwright smoke last (plan 4). Pin everything per the tables below.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Health check (DB + Redis reachable) | API / Backend | Database, Redis | Only the backend can reach both; it returns 503 on failure |
| Show health result | Browser / Client | — | React page via TanStack Query |
| Same-origin API access in dev | Frontend dev server (Vite proxy) | — | Avoids CORS config now; nginx replaces it in Phase 6 |
| Schema migrations | API / Backend (Alembic) | Database | Baseline only; no models yet |
| Design tokens | Browser / Client (Tailwind `@theme`) | — | CSS variables from MASTER.md |
| CI gate | GitHub Actions | GitHub branch protection | Checks run in Actions; blocking needs protection/ruleset |

## Standard Stack

### Core (backend) — only what Phase 1 uses
| Library | Version | Purpose | Source |
|---------|---------|---------|--------|
| Python | 3.14 (`python:3.14-slim-trixie`, 3.14.9 current) | Runtime | [VERIFIED: Docker Hub tags] |
| fastapi | 0.162.0 | API | [VERIFIED: PyPI 2026-10-26] |
| uvicorn[standard] | 0.54.0 | ASGI server (uvloop, httptools, watchfiles for `--reload`) | [VERIFIED: PyPI] |
| sqlalchemy[asyncio] | `>=2.0.55,<2.1` (2.1.6 exists; stay on 2.0.x) | ORM/engine | [VERIFIED: PyPI]; decision from STACK.md |
| asyncpg | 0.32.0 | Postgres driver | [VERIFIED: PyPI] |
| alembic | 1.20.1 | Migrations (async template) | [VERIFIED: PyPI] |
| pydantic | 2.14.1 | Validation (>=2.12 needed on 3.14) | [VERIFIED: PyPI] |
| pydantic-settings | 2.16.1 | Settings from env/.env | [VERIFIED: PyPI] |
| redis | 8.1.0 | `redis.asyncio` client | [VERIFIED: PyPI] |

### Dev (backend, uv `dev` dependency group)
pytest 9.1.1, pytest-asyncio 1.4.1, pytest-cov 7.1.0, httpx 0.28.1 (AsyncClient with `ASGITransport`), respx 0.23.1 (only add when first external HTTP call exists, Phase 3; skip now), ruff 0.17.2, mypy 2.4.0, pip-audit (CI) [VERIFIED: PyPI]. Not in Phase 1: PyJWT, resend, arq, orjson, respx.

### Core (frontend)
| Library | Version | Notes |
|---------|---------|-------|
| Node | 24 LTS (`node:24-trixie-slim`, 24.22.1) | `.nvmrc` = 24 and `engines`. [VERIFIED: Docker Hub, npm] |
| react / react-dom | 19.3.1 | [VERIFIED: npm] |
| vite | 8.3.5 (node ^20.19 or >=22.12) | [VERIFIED: npm] |
| @vitejs/plugin-react | 6.1.2 | peer vite ^8 |
| typescript | **~6.0.3** (npm `latest` is 7.0.2, do NOT use) | typescript-eslint 8.72.0 peer is `<6.1.0` [VERIFIED: npm view] |
| @tanstack/react-query | 5.105.0 | |
| tailwindcss + @tailwindcss/vite | 4.3.3 | CSS-first, no tailwind.config, no PostCSS |
| shadcn (CLI) | 4.22.1 (node >=20.18.1) | installs clsx, tailwind-merge, class-variance-authority, lucide-react, tw-animate-css |
| @fontsource-variable/inter | 5.3.0 | MASTER.md requires Inter variable; self-host, no Google CDN |
| vitest + @vitest/coverage-v8 | 5.0.5 (needs @types/node ^22 or >=24, node ^22.12/^24) | |
| jsdom 30.1.3, @testing-library/react 16.3.3, @testing-library/jest-dom 7.0.1 | | |
| @playwright/test | 1.64.1 | only if e2e included (see below) |
| eslint 10.13.0, @eslint/js 10.0.1, typescript-eslint 8.72.0, eslint-plugin-react-hooks 7.1.1, eslint-plugin-react-refresh 0.5.7, globals 17.13.0, prettier 3.9.10 | | flat config only |
| @types/node | `^24` (24.19.2) | needed by vite.config + vitest |

Skip in Phase 1 (belongs later): react-router-dom (Phase 2, first multi-page), decimal.js (Phase 4), any shadcn component beyond what the health page needs (`card`, `badge`).

### Infra images
`postgres:18.6-trixie`, `redis:8.8.3-trixie`, `python:3.14.9-slim-trixie`, `node:24.22.1-trixie-slim`, `ghcr.io/astral-sh/uv:0.13.5` (copy `/uv` into builder) [VERIFIED: Docker Hub / ghcr manifest 200 / PyPI uv 0.13.5]. Use full patch tags in Compose, not floating `18`.

## Package Legitimacy Audit

slopcheck could not be installed (the pip install was denied by the sandbox), so per protocol packages are not tagged slopcheck-clean. Mitigation: all packages are the canonical, widely used packages named in the official FastAPI/SQLAlchemy/Alembic/TanStack/Vite/Tailwind/shadcn/uv docs and in the prior STACK.md; every one exists on its correct ecosystem registry (PyPI for Python, npm for JS, queried today); no npm package has a `postinstall`/`install` script (checked vitest, shadcn, @tailwindcss/vite, @tanstack/react-query, @playwright/test, lucide-react, tw-animate-css, @fontsource-variable/inter).

| Package | Registry | Source | slopcheck | Disposition |
|---------|----------|--------|-----------|-------------|
| All backend packages above | PyPI | official docs | not run | Approved (well-known; flag `[ASSUMED]` per protocol) |
| All frontend packages above | npm | official docs | not run | Approved (no install scripts) |

The planner SHOULD still add one `checkpoint:human-verify` before the first `uv add` / `npm i` batch only if the user wants strictness; these names are all canonical so this is low value. **Packages removed:** none. **Flagged [SUS]:** none.

## Architecture Patterns

### System Architecture Diagram

```
Browser ──http://localhost:5173──> frontend (Vite dev server, node:24)
   │                                   │  /api/* proxy (server.proxy -> http://backend:8000)
   │ TanStack Query useQuery           ▼
   │ GET /api/v1/health ──────────> backend (uvicorn, FastAPI create_app)
   │                                   │ lifespan: engine = create_async_engine(asyncpg)
   │                                   │           redis  = Redis.from_url(...)
   │                                   ├── SELECT 1 ──────> postgres:18 (healthcheck pg_isready)
   │                                   └── PING ──────────> redis:8.8 (requirepass, noeviction)
   ◄──── 200 {"status":"ok","db":"ok","redis":"ok"} / 503 {"status":"degraded",...}

CI (PR -> develop|main):
  backend job : uv sync --locked -> ruff -> mypy -> compose.test up --wait -> pytest --cov-fail-under=80 -> down -v
  frontend job: npm ci -> eslint -> tsc -b -> prettier --check -> vitest --coverage
  image job   : docker build backend (uv.lock, py3.14) -> run smoke tests in image against test stack
  e2e job (optional): compose up --build --wait -> playwright health page test
  ci-pass     : needs all above; this is the ONE required status check
```

### Recommended Project Structure (Phase 1 only)
```
backend/
  pyproject.toml  uv.lock  .python-version(3.14)  Dockerfile  .dockerignore  alembic.ini
  alembic/{env.py,script.py.mako,versions/0001_baseline.py}
  app/{main.py, core/{config.py,deps.py}, db/{base.py,session.py}, api/v1/{router.py,health.py}, schemas/health.py}
  tests/{conftest.py, test_health.py, test_smoke.py, test_migrations.py}
frontend/
  package.json package-lock.json .nvmrc Dockerfile .dockerignore components.json vite.config.ts eslint.config.js .prettierrc
  src/{main.tsx, App.tsx, index.css, lib/utils.ts, api/{client.ts,health.ts}, hooks/useHealth.ts, components/ui/{card,badge}.tsx, pages/HealthPage.tsx}
  src/**/*.test.tsx  e2e/health.spec.ts (if included)
docker-compose.yml  docker-compose.override.yml  docker-compose.test.yml  .env.example  .github/workflows/ci.yml  .nvmrc(optional root)
```
No `services/`, `models/`, `tasks/` dirs yet (create empty dirs only when first used).

### Pattern 1: create_app + lifespan (no import-time resources)
```python
# app/main.py  [CITED: fastapi.tiangolo.com lifespan events; CLAUDE.md API section]
from contextlib import asynccontextmanager
from fastapi import FastAPI
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    engine = create_async_engine(
        s.database_url, pool_pre_ping=True,
        connect_args={"server_settings": {
            "statement_timeout": "30000",
            "idle_in_transaction_session_timeout": "30000"}},
    )
    redis = Redis.from_url(s.redis_url, decode_responses=True)
    app.state.engine = engine
    app.state.sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    app.state.redis = redis
    try:
        yield
    finally:
        await redis.aclose()
        await engine.dispose()

def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(lifespan=lifespan,
                  docs_url="/docs" if s.env != "prod" else None,
                  redoc_url="/redoc" if s.env != "prod" else None,
                  openapi_url="/openapi.json" if s.env != "prod" else None)
    app.include_router(api_router, prefix="/api/v1")
    return app
```
Run with `uvicorn app.main:create_app --factory`. Session/redis exposed via `Annotated` aliases in `core/deps.py` (`DbDep`, `RedisDep`) per CLAUDE.md. `statement_timeout` set via asyncpg `server_settings` satisfies the CLAUDE.md DB-timeout rule without a custom role (role-level `ALTER ROLE` can wait for Phase 6 hardening).

### Pattern 2: Health endpoint with typed response (no ORJSONResponse)
```python
class HealthOut(BaseModel):
    status: Literal["ok", "degraded"]
    db: Literal["ok", "error"]
    redis: Literal["ok", "error"]

@router.get("/health", response_model=HealthOut, summary="Liveness + dependency check", tags=["health"])
async def health(request: Request, response: Response) -> HealthOut:
    db = redis = "ok"
    try:
        async with request.app.state.engine.connect() as c: await c.execute(text("SELECT 1"))
    except Exception: db = "error"
    try: await request.app.state.redis.ping()
    except Exception: redis = "error"
    if "error" in (db, redis): response.status_code = 503
    return HealthOut(status="ok" if db == redis == "ok" else "degraded", db=db, redis=redis)
```
Never include exception text or connection strings in the response (information leak). Short timeouts: `socket_connect_timeout=2, socket_timeout=2` on Redis; asyncpg `timeout`. The compose healthcheck for backend should hit `/api/v1/health` with python (`python -c "urllib.request..."`) since slim has no curl.

### Pattern 3: Alembic async baseline
`uv run alembic init -t async alembic`, then edit `env.py`: take URL from `get_settings().database_url`, `target_metadata = Base.metadata` where `Base` has a `MetaData(naming_convention=...)` (index/unique/check/fk/pk names; do this now, it is free and avoids unnamed-constraint pain later). Create an empty baseline with `alembic revision -m "baseline"` (hand-written, `upgrade(): pass`, working `downgrade(): pass`). No models. A test runs `alembic upgrade head` then `downgrade base` against the test DB (use `command.upgrade` via `asyncio.to_thread` or run in a sync fixture, because the async env.py calls `asyncio.run`, which cannot run inside a running loop). [CITED: alembic async template docs] [ASSUMED: exact test mechanics; verify in Wave 1]

### Pattern 4: pytest-asyncio 1.x config (avoids "attached to a different loop" with asyncpg)
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "session"
asyncio_default_test_loop_scope = "session"
testpaths = ["tests"]
```
Create the engine and the ASGI app in session-scoped async fixtures; drive the app with `httpx.AsyncClient(transport=ASGITransport(app=app))` inside `lifespan` (use `asgi-lifespan`-free approach: `async with app.router.lifespan_context(app):`). [CITED: pytest-asyncio 1.x docs for loop scope config] [ASSUMED: lifespan_context approach, trivially verifiable]

### Pattern 5: Dockerfile (uv, Python 3.14, non-root)
```dockerfile
FROM python:3.14.9-slim-trixie AS builder
COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0
WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev

FROM builder AS test-builder          # adds dev group for the CI image smoke test
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked

FROM python:3.14.9-slim-trixie AS runtime
RUN useradd --system --uid 1001 --create-home app
COPY --from=builder --chown=app:app /app /app
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER app
WORKDIR /app
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
```
[CITED: docs.astral.sh/uv/guides/integration/docker] `--locked` fails the build if `uv.lock` is stale (that is the success-criterion-3 guarantee). Pin `requires-python = ">=3.14,<3.15"`. Add `.dockerignore` excluding `.venv`, `__pycache__`, `.env`. Note the cache mount is under `/root` because the builder runs as root; the runtime stage runs as `app`. Dev compose overrides `command` with `--reload` and bind-mounts `./backend/app` (venv stays in the image at `/app/.venv`; bind-mount only `app/`, `alembic/`, `tests/` subdirs, not all of `/app`).

### Pattern 6: Compose files
- `docker-compose.yml`: services `postgres`, `redis`, `backend`, `frontend`, each with `healthcheck`, `restart: unless-stopped` optional, backend `depends_on: {postgres: {condition: service_healthy}, redis: {condition: service_healthy}}`; backend `command: sh -c "alembic upgrade head && exec uvicorn ..."` (fine for single backend instance; revisit in Phase 6). Named volume `pgdata` mounted at `/var/lib/postgresql` (Postgres 18 image changed its data dir layout to `/var/lib/postgresql/18/docker`; mounting the parent is the documented approach, mounting `/var/lib/postgresql/data` as in older images triggers a startup error) [ASSUMED: from PG18 image notes; verify on first `up`]. No `ports:` on postgres/redis.
- `docker-compose.override.yml` (dev, auto-loaded): publishes `backend 8000:8000`, `frontend 5173:5173`, adds bind mounts and `--reload`.
- Redis: `command: ["redis-server","--requirepass","${REDIS_PASSWORD}","--maxmemory","256mb","--maxmemory-policy","noeviction","--appendonly","yes"]`; healthcheck `redis-cli ping` with `REDISCLI_AUTH` env (avoids the `-a` CLI-password warning and keeps the secret out of the process list): `test: ["CMD-SHELL","REDISCLI_AUTH=$$REDIS_PASSWORD redis-cli ping | grep PONG"]`. Every key the app writes later must carry a TTL; Phase 1 writes none.
- Postgres healthcheck: `pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB`.
- Frontend service: `node:24` Dockerfile, `npm ci`, `CMD ["npm","run","dev","--","--host","0.0.0.0"]`, anonymous volume for `/app/node_modules`, run as `node` user. Healthcheck: `node -e "fetch('http://localhost:5173').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"`.
- Vite proxy: `server.proxy['/api'] = { target: process.env.VITE_PROXY_TARGET ?? 'http://localhost:8000' }`; compose sets `VITE_PROXY_TARGET=http://backend:8000`. Frontend calls relative `/api/v1/health`. No CORS needed, no `*` anywhere.
- `.env.example` documents: `ENV`, `POSTGRES_USER/PASSWORD/DB`, `DATABASE_URL` (explicit `postgresql+asyncpg://`), `REDIS_PASSWORD`, `REDIS_URL`. Compose reads `.env` (git-ignored; add `.env` to `.gitignore`, which currently only has `__pycache__/` and `*.pyc` and is locally modified). Provide dev defaults inside the override or `${VAR:?}` so `docker compose up` fails clearly when `.env` is missing; simplest MVP: README step "cp .env.example .env".

### Pattern 7: docker-compose.test.yml
Own project name (`name: yokai-test`), Postgres 18.6 with `tmpfs: /var/lib/postgresql`, `POSTGRES_PASSWORD=test`, Redis with requirepass and `tmpfs: /data`, ports bound to **127.0.0.1 on non-default host ports** (e.g. `127.0.0.1:55432:5432`, `127.0.0.1:56379:6379`) so host `uv run pytest` can reach it and it never collides with the dev stack. Tests read `TEST_DATABASE_URL`/`TEST_REDIS_URL` defaults pointing at those ports. Start with `docker compose -f docker-compose.test.yml up -d --wait` (Compose v2+ `--wait` honors healthchecks). Tests must refuse to run if the DB URL host/port is not the test stack (guard in `conftest.py`) so nobody wipes the dev DB.

### Pattern 8: Tailwind 4 + MASTER.md tokens + shadcn
- `src/index.css`: `@import "tailwindcss"; @import "tw-animate-css"; @import "@fontsource-variable/inter";` then `:root { --background:#F2F2F2; --card:#FAFAFA; ... }` copying every token from MASTER.md section 2 (including `--gain`, `--gain-text`, `--loss`, `--loss-text`, `--warn`, `--warn-text`, `--data-blue`, `--data-blue-text`, the `*-soft` tints, `--brand`, `--highlight-gradient`), then `@theme inline { --color-background: var(--background); ... --color-gain-text: var(--gain-text); --font-sans: "Inter Variable", ui-sans-serif, system-ui, sans-serif; --radius-card:24px; --radius-control:14px; }`. Light mode only: delete the `.dark` block and `@custom-variant dark` that `shadcn init` generates. `shadcn init` will write its own default (oklch) variables; **overwrite them with the MASTER hex values** and then verify no raw hex remains in components.
- `html { font-optical-sizing:auto }`, body tabular numerals utility for numbers.
- shadcn init (CLI 4.22.1): requires the `@/*` alias visible to the CLI in the **root** `tsconfig.json`. TypeScript 6 deprecates `baseUrl`; use `"paths": {"@/*": ["./src/*"]}` without `baseUrl` in both `tsconfig.json` and `tsconfig.app.json`, and `resolve.alias` `@ -> ./src` in `vite.config.ts` [CITED: ui.shadcn.com/docs/installation/vite; TS6 baseUrl deprecation: MEDIUM, secondary sources]. Whether `shadcn init` accepts a root tsconfig with `paths` but no `baseUrl` is **unverified**: fallback is `"ignoreDeprecations": "6.0"` plus `baseUrl: "."`. Run `npx shadcn@latest init` interactively once (flags available: `-t vite`, `-b base|radix|aria`, `-y`, `-d`, `-f`; choose `radix` base [ASSUMED: matches the classic shadcn component set], neutral base color, CSS variables on), then `shadcn add card badge`. Commit `components.json`. Consider running init through the executor with `--yes` and checking the diff; the exact prompts changed in v4 (base/preset prompts) so do not script it blindly.
- Icon library: Lucide (matches MASTER.md).

### Pattern 9: TanStack Query health page
```tsx
// src/hooks/useHealth.ts
export function useHealth() {
  return useQuery({ queryKey: ["health"], queryFn: fetchHealth, refetchInterval: 15_000, retry: 1 });
}
```
`fetchHealth` uses `fetch('/api/v1/health')`; a 503 still has a JSON body, so treat 503 as data (`status: "degraded"`) and only throw on network errors, so the page can show which dependency is down. `QueryClientProvider` in `main.tsx`. Page: a Card with three rows (API, Database, Redis) each with Badge text `Connected` / `Unavailable` (never color alone, per MASTER.md) and loading skeleton / error state. Vitest: mock `fetch` (or MSW is overkill; use `vi.stubGlobal('fetch', ...)`), assert ok, degraded, and network-error render states.

### Pattern 10: GitHub Actions (`.github/workflows/ci.yml`)
Triggers: `pull_request: branches: [develop, main]` and `push: branches: [develop, main]`; `concurrency: group: ci-${{ github.ref }}, cancel-in-progress: true`; `permissions: contents: read`. Action majors today [VERIFIED: gh releases/latest]: `actions/checkout@v7`, `actions/setup-node@v7`, `astral-sh/setup-uv@v10`, `actions/cache@v6` (not needed), `docker/setup-buildx-action@v4`, `docker/build-push-action@v7`, `actions/upload-artifact@v7`. Pin to major tag (or SHA for stricter supply chain; major tag is fine for MVP).

Jobs:
1. `backend`: checkout, `setup-uv` (with `enable-cache: true`, python 3.14 from `.python-version`), `uv sync --locked` in `backend/`, `ruff check`, `ruff format --check`, `mypy app`, `docker compose -f docker-compose.test.yml up -d --wait`, `uv run pytest --cov=app --cov-fail-under=80`, `pip-audit` (via `uv run pip-audit`; make it non-blocking at first if it flakes on advisory DB outages), `down -v` in an `if: always()` step. Uses the same compose file as local dev so CI = local (CLAUDE.md commands).
2. `frontend`: checkout, `setup-node` with `node-version-file: .nvmrc` and `cache: npm`, `npm ci`, `npm run lint`, `npx tsc -b` (typecheck), `npx prettier --check .`, `npm run test -- --coverage` (80% gate configured in `vitest.config`), `npm audit --audit-level=high`.
3. `image`: `docker build --target test-builder` of the backend from `uv.lock` (this proves wheels exist for 3.14 inside Linux image), start test stack, run `pytest tests/test_smoke.py` inside that image with `--network host` (or on the compose network). Smoke test covers: `import app.main`, `create_app()` builds, real asyncpg `SELECT 1` and `SELECT 1.5::numeric` returning `Decimal`, Pydantic `Decimal` round-trip via `model_dump_json` / `model_validate_json` as strings (e.g. `Decimal("0.00015000")`), redis ping. Same file also runs on the host in job 1 (no duplication).
4. `e2e` (see decision below).
5. `ci-pass`: `needs: [backend, frontend, image, (e2e)]`, `if: always()`, step fails if any needed result is not `success`. **This single job name is the required status check**, so adding jobs later does not require editing branch protection.

### Anti-Patterns to Avoid
- `Base.metadata.create_all()` on startup (CLAUDE.md forbids; Alembic only).
- Engine/Redis created at import time; a module-global `settings` read at import in a way that breaks tests (use `lru_cache` `get_settings()`).
- Running tests against the dev DB; `docker compose down -v` against the dev stack.
- Floating image tags (`postgres:18`, `latest`), `npm i typescript` unpinned, `uv sync` without `--locked` in CI/Docker.
- Putting hex colors in components; leaving shadcn's default oklch palette or the dark block.
- Publishing Postgres/Redis ports in the main compose file.
- Returning raw exception strings from `/health`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Wait for DB in compose | sleep/retry loops in entrypoint | `healthcheck` + `depends_on: condition: service_healthy` + `up --wait` | Standard, race-free |
| Env config | `os.environ` scattering | pydantic-settings `BaseSettings` | CLAUDE.md requires it |
| Server-state fetching | `useEffect` + `useState` | TanStack Query | CLAUDE.md |
| UI primitives | custom Card/Badge | shadcn `card`, `badge` | Per design system |
| Migrations | SQL scripts | Alembic async template | Required |
| Required-check bookkeeping | one protection rule per job | single `ci-pass` aggregate job | Stable required check name |
| JSON serialization of Decimal | custom encoders / orjson | Pydantic `response_model` (Decimal -> string) | FastAPI deprecated ORJSONResponse |

## Runtime State Inventory
Omitted: greenfield phase, nothing to rename or migrate.

## Common Pitfalls

### Pitfall 1: Branch protection unavailable on private free repo
**What goes wrong:** `gh api -X PUT repos/.../branches/develop/protection` returns 403; "failing check blocks merge" is silently not enforced.
**Why:** Repo `YokAI-open/YokaiExchange` is private and the owner is on a plan without protected branches/rulesets [VERIFIED: gh api 403 on protection and rulesets endpoints].
**How to avoid:** Get a human decision (Open Question 1) before planning the "enforce" task. If the repo goes public or the plan is upgraded, run the `gh api` command in Code Examples; checks must have run at least once on the repo before they can be selected as required.
**Warning signs:** 403 mentioning "Upgrade to GitHub Pro".

### Pitfall 2: typescript@latest is 7.x
`npm i typescript` gives 7.0.2 and typescript-eslint 8.72 refuses it (`<6.1.0`). Pin `typescript@~6.0.3`. Also TS 6 defaults: `strict` true, `types` defaults to `[]` (add `"types": ["node"]`/`vitest/globals` explicitly where needed), `baseUrl` deprecated.

### Pitfall 3: pytest-asyncio event-loop mismatch
Session-scoped engine fixture + function-scoped loop yields "Future attached to a different loop" with asyncpg. Set both default loop scopes to `session` (Pattern 4).

### Pitfall 4: Postgres 18 data directory
Mounting a volume at the old `/var/lib/postgresql/data` path breaks/misbehaves on 18+; mount `/var/lib/postgresql` [ASSUMED, verify on first boot; if wrong the container logs a clear error].

### Pitfall 5: Healthcheck tools missing in slim images
`python:3.14-slim` has no curl/wget. Use a python one-liner for backend; `redis-cli`/`pg_isready` exist in their images; node has `fetch`.

### Pitfall 6: Dev bind mount hides the image venv
Bind-mounting `./backend:/app` shadows `/app/.venv`. Mount only source subdirs, or set `UV_PROJECT_ENVIRONMENT=/opt/venv`. Pick `/opt/venv` outside the app dir for cleanliness (adjust PATH).

### Pitfall 7: alembic async env.py inside pytest
`asyncio.run()` in env.py fails inside a running loop. Invoke Alembic from a sync test or `asyncio.to_thread`.

### Pitfall 8: shadcn init overwrites index.css
Run init before writing the token CSS (or re-apply tokens after). Commit the init diff separately so the token overwrite is reviewable.

### Pitfall 9: Wheel gaps on 3.14
Prior research says cp314 wheels exist for asyncpg 0.32, pydantic-core, uvloop, httptools [CITED: STACK.md]; the image smoke job is exactly the guard. If a wheel is missing, the build fails at `uv sync --locked` loudly, which is the desired behavior.

### Pitfall 10: Local env gaps
Local Node is 18.19.1, Python 3.12.3, `uv` absent. `docker compose up --build` works without them (everything builds in containers), but running `npm`/`uv` commands locally does not. Make installing Node 24 (nvm or NodeSource) and uv an explicit human prerequisite task at the start of the phase.

## Code Examples

### Branch protection (only works once plan/visibility allows)
```bash
# Source: docs.github.com/en/rest/branches/branch-protection (all four top-level keys required, may be null)
for b in develop main; do
gh api -X PUT repos/YokAI-open/YokaiExchange/branches/$b/protection --input - <<'JSON'
{ "required_status_checks": { "strict": true, "contexts": ["ci-pass"] },
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null }
JSON
done
```
`enforce_admins: false` lets the sole owner override in an emergency; set `true` if "even me" is wanted. This is a one-off human/executor step after the first CI run on the repo.

### Pydantic Decimal round trip (smoke test core)
```python
from decimal import Decimal
from pydantic import BaseModel
class M(BaseModel): v: Decimal
def test_decimal_roundtrip():
    j = M(v=Decimal("0.00015000")).model_dump_json()
    assert j == '{"v":"0.00015000"}'          # Decimal serialized as string
    assert M.model_validate_json(j).v == Decimal("0.00015000")
```
[CITED: Pydantic v2 Decimal serialization; CLAUDE.md money rule]

### asyncpg numeric returns Decimal
```python
async with engine.connect() as c:
    v = (await c.execute(text("SELECT 0.00015::numeric(20,8)"))).scalar_one()
    assert isinstance(v, Decimal) and v == Decimal("0.00015000")
```

## State of the Art

| Old | Current | Impact |
|-----|---------|--------|
| `default_response_class=ORJSONResponse` | `response_model`/return annotations; ORJSONResponse deprecated | Drop orjson dep and CLAUDE.md rule [CITED: fastapi.tiangolo.com/reference/responses] |
| `tailwind.config.js` + PostCSS | Tailwind 4 `@import "tailwindcss"` + `@tailwindcss/vite` | No config file |
| `baseUrl` in tsconfig | `paths` with `./` prefixes (TS 6 deprecates baseUrl) | Affects shadcn alias setup |
| pytest-asyncio 0.2x loop fixtures | `asyncio_default_*_loop_scope` | Config in Pattern 4 |
| `pip` + requirements | uv `--locked` | Required |
| Postgres data at `/var/lib/postgresql/data` | PG18 uses versioned dir under `/var/lib/postgresql` | Volume path |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Package legitimacy: slopcheck not run; packages are canonical | Package Legitimacy | Low; names come from official docs and prior research |
| A2 | `shadcn init` works with root tsconfig `paths` and no `baseUrl` under TS 6 | Pattern 8 | Init fails; fallback `ignoreDeprecations` documented |
| A3 | shadcn `radix` base is the classic component set | Pattern 8 | Different generated components; check diff |
| A4 | Postgres 18 volume should mount `/var/lib/postgresql` | Pattern 6, Pitfall 4 | Container fails to start; trivial fix |
| A5 | Alembic test mechanics (sync/`to_thread`) | Pattern 3 | Minor test rewrite |
| A6 | `app.router.lifespan_context(app)` in tests | Pattern 4 | Minor; alternative is `asgi-lifespan` |
| A7 | `uv` 0.13.5 image tag exists on ghcr | Pattern 5 | Verified 200 on manifest; low |

## Open Questions (RESOLVED)

1. **How to make "a failing check blocks the merge" real?** (needs the user)
   - Known: repo is private; protection and rulesets API return 403 on current plan; token has repo admin rights. Org-plan endpoint needs `admin:org` scope (not checked).
   - Options: (a) make the repo public (free, enables protection + rulesets), (b) upgrade to GitHub Pro/Team, (c) accept convention only: CI runs and shows red, and CLAUDE.md already says "merge only after CI is green and I approve". (c) does not satisfy success criterion 2 literally.
   - Recommendation: ask the user; plan the CI workflow regardless, and make the enforcement step a separate, conditional task (`checkpoint:decision`).
   - RESOLVED: D-01. A single aggregate `ci-pass` job is the required check; enforcement is the final `checkpoint:decision` in the CI plan (01-07 Task 3): make the repo public, upgrade the plan, or rely on convention (which counts as PARTIAL for FOUND-02).
2. **Include a Playwright e2e in Phase 1 CI?** Recommendation: **yes, exactly one test** (`/` shows API, Database, Redis as Connected), as the final plan of the phase. Reason: it is the only automated proof of success criterion 1 (compose up -> browser -> backend -> DB/Redis), CLAUDE.md says full suite incl. e2e must pass before merge, and adding the harness now is cheaper than later. Cost: ~2-4 min CI, `npx playwright install --with-deps chromium`. MVP counter-argument: skip and rely on manual check; if the user prefers, move to Phase 2. Keep it as its own job so it can be dropped without touching the rest.
   - RESOLVED: D-03. Exactly one Playwright test, `e2e/health.spec.ts`, running against the full Compose stack as its own CI job feeding `ci-pass` (plans 01-06 and 01-07).
3. **CLAUDE.md deviation: ORJSONResponse.** Ask the user to confirm dropping it (recommended) and update CLAUDE.md performance bullet.
   - RESOLVED: D-02. Dropped: no `ORJSONResponse`, no `orjson`; endpoints use `response_model`/return types. CLAUDE.md updated 2026-10-26.
4. **Healthcheck path naming.** CLAUDE/PITFALLS mention `/healthz` for uptime monitors in Phase 6; ROADMAP says "health". Recommend `/api/v1/health` now; Phase 3/6 extend it with price age (additive, non-breaking).
   - RESOLVED: `/api/v1/health` (plan 01-02).
5. **Domain + Resend DNS (human task)**: independent of code; do in parallel, no planning impact beyond a tracking checkbox.
   - RESOLVED: Human, non-code task started now (recorded in SKELETON.md); needed by Phase 2 email delivery and Phase 6 deployment.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Docker | compose stack | yes | 29.2.1 | none needed |
| Docker Compose | stack, `--wait` | yes | v5.0.0 | — |
| gh CLI | PR, protection | yes (auth as YokAI-open, repo admin) | 2.102.0 | — |
| Node | local npm/lint/vitest | **no** (18.19.1, need 24) | 18.19.1 | Run via container (`docker run node:24`), or install Node 24 (human task); no nvm present |
| Python 3.14 / uv | local backend commands | **no** (3.12.3, no uv) | — | Install uv (`uv python install 3.14` fetches interpreter); Docker builds need neither |
| Git remotes | CI | `origin` = github.com:YokAI-open/YokaiExchange, branches `main`, `develop` exist | | |
| Branch protection | FOUND-02 enforcement | **blocked** (403) | | See Open Question 1 |
| slopcheck | legitimacy audit | no (install denied) | | Mitigated above |

Missing with no fallback: branch protection enforcement (needs user decision). Missing with fallback: Node 24, uv (install, human prerequisite at start of phase; executing agents can instead use containers).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Backend framework | pytest 9.1.1 + pytest-asyncio 1.4.1 + pytest-cov 7.1.0 + httpx AsyncClient |
| Backend config | `backend/pyproject.toml` `[tool.pytest.ini_options]` (Wave 0) |
| Frontend framework | Vitest 5.0.5 + RTL + jsdom (+ Playwright 1.64.1 for e2e) |
| Frontend config | `frontend/vitest.config.ts` (or inside `vite.config.ts`), `src/test/setup.ts` with jest-dom (Wave 0) |
| Quick run (backend) | `cd backend && uv run pytest -x -q` (test stack up) |
| Full suite | `docker compose -f docker-compose.test.yml up -d --wait && cd backend && uv run pytest --cov=app --cov-fail-under=80; cd ../frontend && npm run test -- --coverage; npx playwright test` |

### Phase Requirements -> Test Map
| Req | Behavior | Type | Command | Exists? |
|-----|----------|------|---------|---------|
| FOUND-01 | `/api/v1/health` 200 with db/redis ok | API integration | `uv run pytest tests/test_health.py::test_health_ok` | Wave 0 |
| FOUND-01 | health 503 + degraded when Redis/DB unreachable (override dep / bad URL) | API integration | `uv run pytest tests/test_health.py::test_health_degraded` | Wave 0 |
| FOUND-01 | page renders ok/degraded/error states | Vitest+RTL | `npm run test -- HealthPage` | Wave 0 |
| FOUND-01 | compose up -> browser shows Connected x3 | e2e | `npx playwright test e2e/health.spec.ts` | Wave 0 (if included) |
| FOUND-02 | lint/types/tests run on PR; ci-pass aggregates | CI workflow | open a PR with a deliberately failing lint, observe red `ci-pass`, revert | manual (one-time) |
| Success 3 | image builds from `uv.lock` on 3.14; import app, asyncpg query, Decimal round-trip | smoke | `uv run pytest tests/test_smoke.py` + in-image run in `image` job | Wave 0 |
| Success 4 | test stack isolation (guard refuses non-test DB) | unit | `uv run pytest tests/test_conftest_guard.py` (optional, small) | Wave 0 |
| Alembic | baseline upgrade/downgrade works | integration | `uv run pytest tests/test_migrations.py` | Wave 0 |

Coverage note: 80% gate on this tiny codebase is easy; money-path 100% rule does not apply yet.

### Sampling Rate
- Per task commit: `uv run pytest -x -q` (backend) or `npm run test` (frontend) for the touched side, plus `ruff check` / `npm run lint`.
- Per wave merge: both full suites with coverage.
- Phase gate: `ci-pass` green on the phase PR, `docker compose up --build` manual run showing the page.

### Wave 0 Gaps
- [ ] `backend/pyproject.toml` pytest/ruff/mypy config, `tests/conftest.py` (session loop, engine, app/client fixtures, test-stack guard)
- [ ] `tests/test_health.py`, `tests/test_smoke.py`, `tests/test_migrations.py`
- [ ] `frontend/src/test/setup.ts`, `HealthPage.test.tsx`, coverage thresholds in Vitest config
- [ ] `docker-compose.test.yml`
- [ ] `playwright.config.ts` + `e2e/health.spec.ts` (if included)
- [ ] Framework installs via `uv add --dev ...` / `npm i -D ...`

## Security Domain

Applicable ASVS categories: V2/V3/V4 (auth, sessions, access control) do not apply yet (no users). V5 input validation: no user input in Phase 1. V6 crypto: none. V7 error handling/logging and V14 configuration do apply.

| Pattern | STRIDE | Mitigation |
|---------|--------|------------|
| Secrets committed | Info disclosure | `.env` git-ignored, only `.env.example`; no defaults for real secrets in compose |
| Health endpoint leaks internals | Info disclosure | Return fixed enums only, no exception text |
| Docs exposed in prod | Info disclosure | `docs_url/redoc_url/openapi_url=None` when `ENV=prod` (build the switch now, it is 3 lines) |
| Datastores reachable from host | Elevation | No `ports:` for postgres/redis in main compose; test compose binds 127.0.0.1 only |
| Root containers | Elevation | Backend `USER app`; frontend `USER node`; pinned tags |
| Dependency supply chain | Tampering | Committed `uv.lock`/`package-lock.json`, `--locked`/`npm ci`, `pip-audit` and `npm audit` in CI |
| CI token over-privilege | Elevation | `permissions: contents: read` at workflow level |
| Redis unauthenticated | Elevation | `requirepass` from env |

Postgres least-privilege role (non-superuser app role) and SSL are Phase 6; note it, don't build it now. CSRF/CORS/cookies arrive with Phase 2.

## Scope Flags (push back on bloat, per CLAUDE.md)
- Defer: react-router, decimal.js, respx, extra shadcn components, nginx, prod compose, Dockerfile `prod` target tuning, `ALTER ROLE` DB hardening, Redis cache helpers, rate-limit code, structured logging.
- Keep: the 5 jobs above; the `test-builder` image target (needed for success criterion 3); one e2e test (optional, user's call).
- Keep the Dockerfile to the three stages shown; do not add a separate prod image yet.

## Sources

### Primary (HIGH)
- PyPI JSON API, npm registry, Docker Hub tags API, ghcr manifest, GitHub releases API: queried 2026-10-26 (all versions)
- https://fastapi.tiangolo.com/reference/responses/ (ORJSONResponse deprecated, use response model)
- https://docs.astral.sh/uv/guides/integration/docker/ (multi-stage, `--locked`/`--frozen`, bytecode, pin uv)
- https://ui.shadcn.com/docs/installation/vite and https://ui.shadcn.com/docs/cli (init flags, tsconfig alias steps)
- https://docs.github.com/en/rest/branches/branch-protection (required body fields; Free private repos not supported)
- `gh api` 403 responses on this repo (protection, rulesets)
- /home/YokaiExchange/CLAUDE.md, .planning/* , design-system/yokaiexchange/MASTER.md, .planning/research/STACK.md, PITFALLS.md, ARCHITECTURE.md

### Secondary (MEDIUM)
- Web search on TS 6 `baseUrl` deprecation and shadcn root-tsconfig requirement (multiple community sources agree; not verified against shadcn source)

### Tertiary (LOW)
- Postgres 18 volume path, Alembic/pytest test mechanics (A4-A6): from training knowledge, trivially verifiable on first run

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH (registries queried today)
- Architecture/patterns: HIGH for backend/compose/CI, MEDIUM for shadcn-under-TS6
- Pitfalls: MEDIUM-HIGH
- Branch protection: HIGH that it is currently blocked; outcome depends on user

**Research date:** 2026-10-26
**Valid until:** ~2026-11-09 (fast-moving JS tooling; re-check `npm view` versions at plan execution)
