---
phase: 03-prices
plan: 07
subsystem: infra
tags: [scheduler, compose, heartbeat, ci]
requires:
  - phase: 03-prices/05
    provides: run_cycle, build_source, price settings
provides:
  - tasks/scheduler.py run(), amain(), main(), HEARTBEAT_PATH, touch_heartbeat
  - dev compose scheduler service (single instance, heartbeat healthcheck, no ports)
  - PRICE_SOURCE in .env.example; CI e2e forces PRICE_SOURCE=fake
affects: [03-08]
key-files:
  created:
    - backend/tests/test_scheduler_loop.py
  modified:
    - backend/app/tasks/scheduler.py
    - docker-compose.yml
    - docker-compose.override.yml
    - .env.example
    - .github/workflows/ci.yml
    - CLAUDE.md
metrics:
  completed: 2026-10-28
---

# Phase 3 Plan 07: Scheduler loop and compose service Summary

A drift-free 60 s asyncio loop (first cycle immediately, no catch-up burst after overruns, heartbeat touched after every cycle, SIGTERM/SIGINT finish the cycle and close httpx, Redis and the engine) runs as one dedicated `scheduler` compose service; CI e2e uses the fake source.

## Commits
- 525f0e9 feat(03-07): scheduler loop with heartbeat and graceful shutdown
- 8d60c33 feat(03-07): scheduler service in dev compose and CI fake source

## Verification
- Backend suite: 292 passed, 99.83% total; scheduler.py 100%; ruff, format, mypy clean.
- Loop never referenced from `app/main.py` or `app/api` (grep empty).
- Dev compose config valid, lists scheduler; scheduler has `ports: None`, networks app+data.
- actionlint 1.7.7 passes on ci.yml.
- Throwaway stack (project `birja-schedcheck`, no override, `.env.example`, PRICE_SOURCE=fake): `select count(*), max(source) from prices` printed `15|fake`; scheduler `Up (healthy)`. Stack removed with `down -v --rmi local`; no containers remain.
- The user's dev stack (`birja`), prod (`birja-prod`) and `.env` were not touched.

## Deviations from Plan
None - plan executed as written. Note: the fake `wait_for` in loop tests keeps waiting once stop is set (a real one returns immediately), so the overrun test asserts only the first delay.

## Known Stubs
None.

## Self-Check: PASSED
