---
phase: 01-skeleton-and-ci
verified: 2026-10-26T16:30:00Z
status: passed
score: 4/4 must-haves verified
overrides_applied: 0
gaps: []
---

# Phase 1: Skeleton and CI Verification Report

**Phase Goal:** A developer can run the whole stack locally and every PR is checked automatically
**Status:** passed (with advisory warnings)
**Re-verification:** No, initial verification

## Observable Truths (ROADMAP success criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `docker compose up --build` starts Postgres, Redis, backend, frontend; the page shows a live health result via TanStack Query | VERIFIED | Ran `cp .env.example .env && docker compose up --build -d --wait`. All 4 services healthy. `localhost:8000/api/v1/health` and the Vite proxy `localhost:5173/api/v1/health` both returned `{"status":"ok","db":"ok","redis":"ok"}`. After stopping redis the endpoint returned `{"status":"degraded","db":"ok","redis":"error"}`, so the check is live. `HealthPage.tsx` renders `useHealth()`, which is `useQuery` with `refetchInterval` 15s. The CI `e2e` job (Playwright against the full stack) passed. |
| 2 | A PR into develop/main runs lint, types and tests (backend and frontend) in GitHub Actions; a failing check blocks the merge | VERIFIED | `ci.yml` triggers on pull_request to develop/main. Jobs: backend (ruff, format, mypy, pytest with an 80% gate, pip-audit), frontend (eslint, tsc, prettier, vitest coverage, npm audit), image, e2e, and an aggregate `ci-pass` that fails on failure, cancelled or skipped. PR #2 checks: backend, frontend, image, e2e and ci-pass all passed. Branch protection on develop and main requires the `ci-pass` context with strict=true. See the enforce_admins warning below. |
| 3 | Backend image builds from `uv.lock` on Python 3.14 and a smoke test (import app, asyncpg query, Pydantic Decimal round-trip) passes in CI | VERIFIED | `backend/Dockerfile` uses `python:3.14.9-slim-trixie` and `uv sync --locked`, with a runtime image running as non-root. `tests/test_smoke.py` asserts Python 3.14, app import with the health route, an asyncpg `numeric(20,8)` returning Decimal, and a Pydantic Decimal-as-string round-trip. The CI `image` job (build, then in-image smoke test) passed. |
| 4 | `docker-compose.test.yml` runs backend tests against an isolated Postgres and Redis | VERIFIED | Ran `docker compose -f docker-compose.test.yml up -d --wait` (healthy, tmpfs, 127.0.0.1 ports 55432/56379, project name yokai-test). `uv run pytest --cov=app --cov-fail-under=80` gave 17 passed, 96.67% coverage. `tests/guard.py` and `test_conftest_guard.py` refuse non-test hosts. Torn down with `down -v`. |

**Score:** 4/4

## Spot-checks run locally

| Check | Result |
|-------|--------|
| ruff check, ruff format --check, mypy app | pass |
| pytest 17 tests | pass, 96.67% coverage |
| Frontend eslint, tsc -b | pass |
| Frontend vitest | 13 passed, 100% coverage |
| Debt markers (TBD/FIXME/XXX) in backend/app, tests, frontend/src, .github, compose | none |

Cleanup done: the dev stack was removed with `down -v`, the temporary `.env` was deleted, and the test stack was removed with `down -v`. `git status` shows only the pre-existing untracked `.claude/`.

## Requirements Coverage

| Requirement | Source Plans | Status | Evidence |
|-------------|--------------|--------|----------|
| FOUND-01 (one `docker compose up`, frontend talks to backend) | 01-01, 01-03, 01-04, 01-05, 01-06, 01-07 | SATISFIED | Truth 1 |
| FOUND-02 (every PR runs lint, types and tests; a failure blocks merge) | 01-02, 01-05, 01-07 | SATISFIED | Truth 2. The repo is public (D-01), so branch protection is available and `ci-pass` is required on both branches. |

No orphaned requirements: REQUIREMENTS.md maps only FOUND-01 and FOUND-02 to Phase 1, and both are claimed by plans. The traceability table still shows "Pending", so mark them complete when closing the phase.

## Warnings (advisory, not gaps)

- WR-03 (01-REVIEW): `HealthPage.tsx` derives its badges only from `data`. After one success followed by a failed refetch, the page shows "Connected / All systems operational" next to the "Can't reach the backend" alert. This does not defeat the criterion, because a live result is shown and the first-load failure path works. But the only status screen can be stale-wrong, so it is worth fixing early in Phase 2.
- Branch protection has `enforce_admins: false` and no required PR review, so repo admins can bypass the check. For non-admin merges a failing `ci-pass` blocks the merge. Consider enabling `enforce_admins` if strict blocking is wanted.
- WR-01 (01-REVIEW): a malformed `DATABASE_URL` leaks the DB password via the pydantic validation error. The repo and its CI logs are public, so apply `hide_input_in_errors=True`. This does not bear on the phase goal.
- WR-02, WR-04 and WR-05 are not goal-bearing; see 01-REVIEW.md.

## Human Verification Required

None. The browser rendering path is covered by the Playwright e2e job, which passed in CI on PR #2.

---

_Verified: 2026-10-26T16:30:00Z_
_Verifier: Claude (gsd-verifier)_
