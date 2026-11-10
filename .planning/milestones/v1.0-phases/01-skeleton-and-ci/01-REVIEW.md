---
phase: 01-skeleton-and-ci
reviewed: 2026-10-26T15:18:11Z
depth: standard
files_reviewed: 68
files_reviewed_list:
  - .env.example
  - .github/workflows/ci.yml
  - .gitignore
  - backend/.dockerignore
  - backend/.python-version
  - backend/Dockerfile
  - backend/alembic.ini
  - backend/alembic/env.py
  - backend/alembic/script.py.mako
  - backend/alembic/versions/0001_baseline.py
  - backend/app/__init__.py
  - backend/app/api/__init__.py
  - backend/app/api/v1/__init__.py
  - backend/app/api/v1/health.py
  - backend/app/api/v1/router.py
  - backend/app/core/__init__.py
  - backend/app/core/config.py
  - backend/app/core/deps.py
  - backend/app/db/__init__.py
  - backend/app/db/base.py
  - backend/app/main.py
  - backend/app/schemas/__init__.py
  - backend/app/schemas/health.py
  - backend/app/services/__init__.py
  - backend/app/services/health.py
  - backend/pyproject.toml
  - backend/tests/__init__.py
  - backend/tests/conftest.py
  - backend/tests/guard.py
  - backend/tests/test_conftest_guard.py
  - backend/tests/test_health.py
  - backend/tests/test_migrations.py
  - backend/tests/test_smoke.py
  - docker-compose.override.yml
  - docker-compose.test.yml
  - docker-compose.yml
  - frontend/.dockerignore
  - frontend/.gitignore
  - frontend/.nvmrc
  - frontend/.prettierignore
  - frontend/.prettierrc.json
  - frontend/Dockerfile
  - frontend/components.json
  - frontend/e2e/health.spec.ts
  - frontend/eslint.config.js
  - frontend/index.html
  - frontend/package.json
  - frontend/playwright.config.ts
  - frontend/src/App.test.tsx
  - frontend/src/App.tsx
  - frontend/src/api/health.test.ts
  - frontend/src/api/health.ts
  - frontend/src/components/ui/badge.tsx
  - frontend/src/components/ui/button.tsx
  - frontend/src/components/ui/card.tsx
  - frontend/src/hooks/useHealth.ts
  - frontend/src/index.css
  - frontend/src/lib/utils.ts
  - frontend/src/main.tsx
  - frontend/src/pages/HealthPage.test.tsx
  - frontend/src/pages/HealthPage.tsx
  - frontend/src/test/render.tsx
  - frontend/src/test/setup.ts
  - frontend/src/vite-env.d.ts
  - frontend/tsconfig.app.json
  - frontend/tsconfig.json
  - frontend/tsconfig.node.json
  - frontend/vite.config.ts
findings:
  critical: 0
  warning: 5
  info: 9
  total: 14
status: issues_found
---

# Phase 1: Code Review Report

**Reviewed:** 2026-10-26T15:18:11Z
**Depth:** standard
**Files Reviewed:** 68
**Status:** issues_found

## Narrative Findings (AI reviewer)

## Summary

I reviewed the walking skeleton: the FastAPI health endpoint and its service, settings, lifespan, Alembic, the test guard and tests, the Compose dev and test stacks, Dockerfiles, CI, and the React health page. The skeleton is solid. It has non-root images, internal-only data networks, an isolated test stack with a host/port/name guard, timeouts on DB and Redis, docs turned off in prod, and an aggregate `ci-pass` check. I found no blockers.

The main defects:
- A misconfigured `DATABASE_URL` puts the plaintext DB password into startup logs. This was checked by running it.
- The health service's failure log drops the only detail it carries (which dependency failed). This was also checked by running it.
- After an earlier success, the status page shows "Connected / All systems operational" even when the backend is down.
- The Alembic migration template produces files that fail this repo's own `ruff` gate.
- The root `.gitignore` only ignores `.env`, which matters now that the repo is public.

Two things I checked are not defects: the `cn@0.5.0` npm dependency, which is the real `shadcn-ui/cn` package and not a typosquat, and the absence of auth, CSRF and nginx, which is deferred by scope.

## Warnings

### WR-01: A bad DATABASE_URL leaks the DB password into logs

**File:** `backend/app/core/config.py:9-20`
**Issue:** `Field(repr=False)` hides the URL from `repr`, but it does not hide it from validation errors. When `_check_database_url` rejects a value, pydantic's `ValidationError` includes `input_value=...` with the whole URL. I reproduced it:
```
Value error, database_url must start with 'postgresql+asyncpg://' [type=value_error, input_value='postgresql://u:SuperSecret@h/db', input_type=str]
```
This error is raised in `create_app()`/`env.py` at container start (`alembic upgrade head`), so the password ends up in `docker compose logs` and in CI logs. The repo is public, so the CI logs are public too. A plain `postgresql://` scheme is exactly the mistake people make.
**Fix:**
```python
model_config = SettingsConfigDict(extra="ignore", hide_input_in_errors=True)
```
Also consider typing `database_url`/`redis_url` as `SecretStr`, or keep them `str` and add a regression test that asserts the password is not in `str(exc)`.

### WR-02: Health-check failure log drops which dependency failed and why

**File:** `backend/app/services/health.py:23-25, 35-37`
**Issue:** The `dependency` and `error_type` values go into `extra=`, but nothing configures app logging. Uvicorn's log config only covers the `uvicorn.*` loggers, so `app.services.health` falls through to Python's last-resort handler, whose format is `%(message)s`. I confirmed that the only output is `health check failed`, with no dependency and no error type. Combined with the bare `except Exception`, which also swallows programming errors such as a wrong attribute or bad SQL, an operator cannot tell a Redis outage from a DB outage or a code bug.
**Fix:** Put the fields in the message and keep the traceback out of the response but in the log:
```python
logger.warning("health check failed: dependency=%s error_type=%s", "db", type(exc).__name__)
```
Or add a minimal `logging.basicConfig`/dictConfig in `create_app` whose formatter includes the extras. Add a `caplog` assertion in `test_health_redis_down`.

### WR-03: The status page reports "Connected" while the backend is unreachable

**File:** `frontend/src/pages/HealthPage.tsx:18-26, 52-60`
**Issue:** TanStack Query keeps the last successful `data` when a later refetch fails. After one success, a failed poll gives both `isError === true` and `data !== undefined`. The page then shows all three badges as "Connected" with "All systems operational", plus the "Can't reach the backend" alert and an old "Last checked" time. The API badge is derived only from `data`, so the outage never shows. The only status screen in the app contradicts itself, and the tests miss it because they always start from an empty cache.
**Fix:** Derive state from the error first:
```tsx
const live = isError ? undefined : data;
const services = [
  { name: "API", label: live ? "Connected" : isError ? "Unavailable" : "Unknown" },
  { name: "Database", label: live ? fromState(live.db) : "Unknown" },
  { name: "Redis", label: live ? fromState(live.redis) : "Unknown" },
];
```
Base the summary on `live`, and keep "Last checked" showing `dataUpdatedAt`, marked as stale. Add a test that resolves once, then rejects, calls `refetch`, and asserts `APIUnavailable`.

### WR-04: The Alembic template generates migrations that fail this repo's ruff gate

**File:** `backend/alembic/script.py.mako:8-18`
**Issue:** The template uses `from typing import Sequence, Union` and `Union[...]`, and puts `from alembic import op` before `import sqlalchemy as sa`. With `select = [..., "I", "UP"]` and `target-version = "py314"`, every autogenerated migration triggers UP035 (deprecated `typing.Sequence`), UP007 (`Union`), and possibly I001. CI runs `ruff check .`, which includes `alembic/versions`, so every new migration fails CI until someone hand-edits it. The baseline (`0001_baseline.py`) was clearly hand-written in a different style, which hides this.
**Fix:** Make the template match the baseline:
```mako
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: str | Sequence[str] | None = ${repr(down_revision)}
branch_labels: str | Sequence[str] | None = ${repr(branch_labels)}
depends_on: str | Sequence[str] | None = ${repr(depends_on)}
```
Or enable the `ruff` post-write hook in `alembic.ini`, which is already sketched there in comments.

### WR-05: Root .gitignore misses common env-file variants in a public repo

**File:** `.gitignore:3`
**Issue:** Only the exact `.env` is ignored. Files like `.env.prod`, `.env.local` and `backend/.env.test`, which people commonly create when the prod deploy arrives (Phase 6) or for local overrides, would show as untracked and can be committed with `git add .`. The repo is public, and CLAUDE.md requires that secrets only ever live in git-ignored env files. `backend/.dockerignore` and `frontend/.dockerignore` have the same gap and would bake such files into images, since `COPY . /app`/`COPY . .`.
**Fix:**
```gitignore
.env
.env.*
!.env.example
```
Mirror `.env.*` into both `.dockerignore` files.

## Info

### IN-01: Ruff treats `alembic` as first-party

**File:** `backend/alembic/env.py:8`, `backend/tests/test_migrations.py:10`
**Issue:** Because there is a local `backend/alembic/` directory, ruff's isort treats `alembic` as first-party. That is why `from alembic import context` is sorted after `sqlalchemy`, next to `app`. This is confusing and spreads the odd ordering to every file that imports Alembic.
**Fix:** Add `[tool.ruff.lint.isort] known-third-party = ["alembic"]`.

### IN-02: The Redis password is visible in the container command line

**File:** `docker-compose.yml:34-36`
**Issue:** Compose interpolates `--requirepass ${REDIS_PASSWORD}` into the command, so the password is visible in `docker inspect`, `ps`, and `docker compose config` output. The command also breaks if the value contains spaces.
**Fix:** Let the shell expand it inside the container: `command: ["sh", "-c", "exec redis-server --requirepass \"$$REDIS_PASSWORD\" --maxmemory 256mb --maxmemory-policy noeviction --appendonly yes"]`. Better still, use a mounted config or ACL file once prod lands.

### IN-03: .env.example contradicts its own rule, and credentials are not URL-encoded

**File:** `.env.example:2,10,14`; `docker-compose.yml:53-54`
**Issue:** The comment says "letters/digits only", but the placeholders contain hyphens. Hyphens are URL-safe, but the comment and the values disagree. The real constraint is that `@ : / ? # %` break the hand-built `DATABASE_URL`/`REDIS_URL`, because nothing URL-encodes them.
**Fix:** Change the comment to "URL-safe characters only (no @ : / ? # %)", or build the URLs in `Settings` from separate parts with `quote_plus`.

### IN-04: CI never runs a production frontend build

**File:** `.github/workflows/ci.yml:65-70`
**Issue:** CI runs `tsc -b`, lint and vitest, but never runs `npm run build`. `index.css` (Tailwind and the `shadcn/tailwind.css` import) is only compiled by the dev server during e2e, so a broken `vite build` would merge green.
**Fix:** Add `- run: npm run build` to the frontend job.

### IN-05: GitHub Actions are pinned to mutable tags in a public repo

**File:** `.github/workflows/ci.yml:21-22,59-60,77-79,135`
**Issue:** Third-party actions (`astral-sh/setup-uv`, `docker/*`) are pinned by tag, not by commit SHA. The blast radius is small, given `permissions: contents: read` and no secrets, but a moved tag can still run arbitrary code inside the required check.
**Fix:** Pin to full commit SHAs with a version comment, and let Dependabot (`github-actions` ecosystem) bump them.

### IN-06: The health fetch has no timeout and no cancellation

**File:** `frontend/src/api/health.ts:21-22`, `frontend/src/hooks/useHealth.ts:5`
**Issue:** `fetchHealth` ignores the `signal` from the query function context and sets no timeout. If the proxy or backend hangs, the query stays fetching: the button stays disabled on "Checking…" and interval refetches dedupe onto the hung request.
**Fix:** Use `queryFn: ({ signal }) => fetchHealth(signal)` with `fetch(url, { signal: AbortSignal.any([signal, AbortSignal.timeout(10_000)]) })`.

### IN-07: The button's accessible name doesn't match its visible text while fetching

**File:** `frontend/src/pages/HealthPage.tsx:65-67`
**Issue:** `aria-label="Check again"` stays fixed while the visible text changes to "Checking…". This violates WCAG 2.5.3 (Label in Name), and the busy state is never announced.
**Fix:** Drop `aria-label`, since the visible text already serves as the name, and add `aria-busy={isFetching}`.

### IN-08: Duplicate `cn` entry point, and shadcn CLI in runtime dependencies

**File:** `frontend/src/lib/utils.ts:1`, `frontend/package.json:24,29`
**Issue:** `components.json` points shadcn at `@/lib/utils`, but the three UI components import `"cn"` directly, so `lib/utils.ts` is unused and there are two import paths. Also, `shadcn` (the CLI) is listed under `dependencies` only so that `shadcn/tailwind.css` resolves. It belongs in `devDependencies`, because the CSS import is resolved at build time.
**Fix:** Pick one path, preferably `@/lib/utils` to match `components.json`, and move `shadcn` to `devDependencies`.

### IN-09: The backend container healthcheck uses the readiness endpoint

**File:** `docker-compose.yml:65-74, 81-83`
**Issue:** The backend healthcheck calls `/api/v1/health`, which returns 503 when Redis or Postgres is degraded. Any brief Redis blip marks the API container unhealthy and, through `depends_on: service_healthy`, keeps the frontend from starting, even though the API process itself is fine. This is acceptable for the MVP, but it is a coupling to remember when real liveness and readiness probes are needed.
**Fix:** Later, add a dependency-free liveness route for the container healthcheck and keep `/health` as the readiness and status page.

---

_Reviewed: 2026-10-26T15:18:11Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
