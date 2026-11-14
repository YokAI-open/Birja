---
phase: 1
slug: skeleton-and-ci
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-10-26
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9 + pytest-asyncio 1.x + httpx AsyncClient (backend); Vitest + RTL (frontend); Playwright (e2e) |
| **Config file** | none yet. Wave 0 installs `backend/pyproject.toml` pytest config, the Vitest `test` block inside `frontend/vite.config.ts` (no separate vitest.config.ts), and `frontend/playwright.config.ts` |
| **Quick run command** | `cd backend && uv run pytest -x -q` / `cd frontend && npm run test` |
| **Full suite command** | `docker compose -f docker-compose.test.yml up -d --wait && cd backend && uv run pytest --cov=app --cov-fail-under=80; cd ../frontend && npm run test -- --coverage && npx playwright test` |
| **Estimated runtime** | ~60 seconds (excluding image builds) |

---

## Sampling Rate

- **After every task commit:** Run the quick command for the touched side, plus `ruff check` / `npm run lint`
- **After every plan wave:** Run the full suite command
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

One row per auto task in the final plans. Commands are taken from each task's `<automated>` verify (the backend rows assume the test stack is up: `docker compose -f docker-compose.test.yml up -d --wait`).

| Task ID | Plan | Wave | Requirement | Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|----------|-----------|-------------------|-------------|--------|
| 01-01-T1 | 01-01 | 1 | (git-flow) | Work happens on feature/phase-01-skeleton-and-ci, branched from origin/develop | git check | `test "$(git rev-parse --abbrev-ref HEAD)" = feature/phase-01-skeleton-and-ci && git merge-base --is-ancestor origin/develop HEAD` | n/a | ⬜ pending |
| 01-02-T1 | 01-02 | 2 | FOUND-01 | uv.lock syncs; test-stack guard passes; health tests RED (no app yet) | unit + RED check | `cd backend && uv sync --locked && uv run pytest tests/test_conftest_guard.py -q && ! uv run pytest tests/test_health.py -q` | ❌ W0 | ⬜ pending |
| 01-02-T2 | 01-02 | 2 | FOUND-01 | `/api/v1/health` 200 ok and 503 degraded (DB down, Redis down, no internals); smoke (3.14, asyncpg Decimal, Pydantic Decimal string, Redis ping) | API integration + smoke | `cd backend && uv run pytest --cov=app --cov-fail-under=80 -q && uv run ruff check . && uv run ruff format --check . && uv run mypy app` | ❌ W0 | ⬜ pending |
| 01-03-T1 | 01-03 | 3 | FOUND-01 | Alembic baseline 0001 upgrade/downgrade/upgrade inside the full suite; no `asyncio.run` in tests | integration | `cd backend && uv run pytest --cov=app --cov-fail-under=80 -q && ! grep -n 'asyncio.run(' tests/*.py && uv run ruff check . && uv run ruff format --check . && uv run mypy app` | ❌ W0 | ⬜ pending |
| 01-03-T2 | 01-03 | 3 | FOUND-01 / Success 3 | Compose backend healthy, migrated to 0001, uid 1001; test-builder image runs the smoke test | compose + in-image smoke | `docker compose up --build -d --wait postgres redis backend && curl -fsS http://127.0.0.1:8000/api/v1/health \| grep -q '"status":"ok"' && docker compose exec -T backend alembic current \| grep -q '0001 (head)' && docker build -q --target test-builder -t yokai-backend-test backend && docker run --rm --network host yokai-backend-test pytest tests/test_smoke.py -q` | ❌ W0 | ⬜ pending |
| 01-04-T1 | 01-04 | 2 | FOUND-01 | Pinned toolchain (TS 6.0) lints, typechecks, formats, tests and builds on Node 24 | lint/type/unit/build | `cd frontend && npm ci && npm run lint && npm run typecheck && npx prettier --check . && npm run test -- --coverage && npm run build && npm ls typescript \| grep -q 'typescript@6\.0\.'` | ❌ W0 | ⬜ pending |
| 01-04-T2 | 01-04 | 2 | FOUND-01 | MASTER.md tokens in index.css, no dark/oklch, no raw hex in components | lint/unit/build + grep | `cd frontend && npm run lint && npm run typecheck && npx prettier --check . && npm run test -- --coverage && npm run build && grep -q -- '--gain-text: #2E7A2E' src/index.css` | ❌ W0 | ⬜ pending |
| 01-05-T1 | 01-05 | 3 | FOUND-01 | Health client/page/App tests exist and are RED | RED check | `cd frontend && ! npm run test` | ❌ W0 | ⬜ pending |
| 01-05-T2 | 01-05 | 3 | FOUND-01 | Page renders ok / degraded / error / loading; Check again refetches; coverage >= 80% | Vitest + RTL | `cd frontend && npm run test -- --coverage && npm run lint && npm run typecheck && npx prettier --check . && npm run build` | ❌ W0 | ⬜ pending |
| 01-06-T1 | 01-06 | 4 | FOUND-01 | Exactly one e2e test, typechecked and linted; RED with no frontend listening | e2e RED check | `cd frontend && npm run typecheck && npm run lint && test "$(grep -c 'test(' e2e/health.spec.ts)" -eq 1 && ! E2E_BASE_URL=http://127.0.0.1:5999 npx playwright test` | ❌ W0 | ⬜ pending |
| 01-06-T2 | 01-06 | 4 | FOUND-01 | Compose up → browser shows API/Database/Redis Connected; frontend runs as node | e2e | `docker compose up --build -d --wait && curl -fsS http://127.0.0.1:5173/api/v1/health \| grep -q '"status":"ok"' && cd frontend && npx playwright test` | ❌ W0 | ⬜ pending |
| 01-07-T1 | 01-07 | 5 | FOUND-02 | ci.yml lints clean; ci-pass needs backend, frontend, image, e2e; read-only token | workflow lint + grep | `docker run --rm -v "$PWD:/repo" -w /repo rhysd/actionlint:1.7.7 -color=false .github/workflows/ci.yml && grep -q 'needs: \[backend, frontend, image, e2e\]' .github/workflows/ci.yml` | ❌ W0 | ⬜ pending |
| 01-07-T2 | 01-07 | 5 | FOUND-02 | CLAUDE.md Common commands and README match the real commands | grep | `grep -q 'cp .env.example .env' CLAUDE.md && grep -q 'npm run typecheck' CLAUDE.md && grep -q 'Run locally' README.md` | n/a | ⬜ pending |

Checkpoint tasks (verified by the human, see Manual-Only below): 01-01-T2 (toolchain), 01-01-T3 (package legitimacy), 01-07-T3 (D-01 decision; under "convention", FOUND-02 merge blocking is reported as PARTIAL, not PASS).

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/pyproject.toml` pytest/ruff/mypy config; `backend/tests/conftest.py` (loop scope, engine, app/client fixtures, test-stack guard)
- [ ] `backend/tests/test_health.py`, `test_smoke.py`, `test_migrations.py`
- [ ] `frontend/src/test/setup.ts`, `HealthPage.test.tsx`, coverage thresholds in the `test` block of `frontend/vite.config.ts`
- [ ] `docker-compose.test.yml`
- [ ] `frontend/playwright.config.ts` + `frontend/e2e/health.spec.ts`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| A failing check turns `ci-pass` red on a PR | FOUND-02 | Needs a real PR on GitHub | Open a PR with a deliberate lint error, confirm `ci-pass` fails, then revert |
| Merge is blocked while `ci-pass` is red | FOUND-02 | Depends on repo plan (D-01) | After the D-01 checkpoint, try to merge a red PR. If D-01 = convention, record FOUND-02 merge blocking as PARTIAL (accepted deviation) |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
