---
phase: 01-skeleton-and-ci
plan: 03
subsystem: infra
tags: [alembic, docker, compose, postgres, redis]
requires: ["01-02"]
provides:
  - "Alembic async env + empty baseline revision 0001 with tested round-trip"
  - "Base DeclarativeBase with constraint naming convention"
  - "Backend Dockerfile (builder / test-builder / runtime, non-root uid 1001)"
  - "docker-compose.yml (postgres, redis, backend) + dev override + .env.example"
affects: [01-06, 01-07]
key-files:
  created:
    - backend/alembic.ini
    - backend/alembic/env.py
    - backend/alembic/versions/0001_baseline.py
    - backend/app/db/base.py
    - backend/tests/test_migrations.py
    - backend/Dockerfile
    - backend/.dockerignore
    - docker-compose.yml
    - docker-compose.override.yml
    - .env.example
key-decisions:
  - "Migration tests run alembic in asyncio.to_thread; subprocess fallback not needed"
  - "fileConfig(disable_existing_loggers=False) in env.py so alembic does not silence app loggers"
duration: 20min
completed: 2026-10-26
---

# Phase 1 Plan 03: Compose stack and Alembic baseline Summary

**`docker compose up --build` brings up Postgres 18.6, Redis 8.8.3 and a non-root backend that migrates to baseline 0001 and reports `{"status":"ok","db":"ok","redis":"ok"}`.**

## Tasks

| # | Task | Commits |
|---|------|---------|
| 1 | Alembic async baseline + round-trip test | 29db768 (test, RED), 8d6e0a9 (feat) |
| 2 | Dockerfile + Compose stack + dev override | b754449 |

## Verification

- Backend suite: 17 passed, 96.67% coverage; ruff and mypy clean.
- Dev stack (project `yokai-w3`): health ok, `alembic current` = `0001 (head)`, `id -u` = 1001.
- No `ports` on postgres/redis in resolved config; `.env` ignored and untracked.
- `test-builder` image runs `tests/test_smoke.py` (5 passed) against the test stack.
- Stacks torn down with `down -v`; temporary `.env` removed.

## Deviations from Plan

**1. [Rule 3 - Blocking] Worktree base reset.** The worktree started at 91deb8b; reset to the specified base a9a6eae per the branch check.

**2. [Rule 1 - Style] ruff reordered imports** so `from alembic import command` follows third-party imports (the local `alembic/` directory makes ruff treat it as first-party). Behavior unaffected; tests pass.

**3. Compose `name:`** set to `${COMPOSE_PROJECT_NAME:-yokai}` so the project name can be overridden for parallel runs.

The PG18 data-dir layout (`/var/lib/postgresql`) worked as planned with no fix needed.

## Known Stubs

None.

## Threat Flags

None.

## Self-Check: PASSED
