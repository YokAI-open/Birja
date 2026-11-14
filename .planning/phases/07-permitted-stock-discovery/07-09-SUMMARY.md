---
phase: 07-permitted-stock-discovery
plan: "09"
subsystem: infra
tags: [scheduler, asyncio, redis, postgres, alpaca, admission]
requires:
  - phase: 07-04
    provides: Restricted scheduler SQL privileges and exact recovery contracts
  - phase: 07-06
    provides: Exact IEX adapter, verified mappings and guarded monotonic quotes
  - phase: 07-08
    provides: Reviewed authority-bound regular sessions and derived persistence
provides:
  - Independently bounded stock collection with per-attempt current admission checks
  - Concurrent crypto/stock loops in one scheduler with orderly cancellation
  - Disabled-by-default Compose configuration with scheduler-only provider secrets
affects: [07-10, 07-13, 07-14]
tech-stack:
  added: []
  patterns: [Independent token leases and cadence guards, Short datastore reads before each HTTP attempt]
key-files:
  created: [backend/app/tasks/stock_scheduler.py, backend/tests/test_stock_scheduler.py]
  modified: [backend/app/tasks/scheduler.py, backend/tests/test_scheduler_loop.py, docker-compose.yml, docker-compose.prod.yml, .env.example]
key-decisions:
  - "One shared stock cadence key bounds repeated cycles even after releasing the shorter token lease."
  - "Each HTTP retry reloads admission and catalogue through a temporary async request hook on the separate stock client."
  - "Calendar authority remains migrator-owned; derived refresh cannot renew review or alter overrides."
requirements-completed: []
requirements-addressed: [DATA-01, STOCK-03, MKT-01, SAFE-01]
duration: 12min
completed: 2026-11-10
---

# Phase 7 Plan 9: Independent stock scheduling Summary

**A separate bounded stock cycle now shares one scheduler process with crypto while preserving independent cadence, source timestamps, current admission checks and cancellation.**

## Performance

- Approximately 12 minutes, 2026-11-10T18:42Z–18:54Z; two tasks, seven owned source/test/config files.
- Both tasks complete locally. Whole-phase requirements remain pending; neither fixtures nor configuration establish live provider permission.

## Accomplishments

- `run_stock_cycle(sessionmaker, redis, http, settings, now)` uses separate
  `sim:lock:stock-refresh` token ownership, 45-second lease, 40-second whole-cycle
  bound and 35-second outer source maximum. Existing configured adapter bounds
  remain tighter. `sim:stock:quote-window` prevents repeated batches inside the
  configured minimum 60-second cadence, including failures after lease release.
- Collection requires approved scoped quote/reference/calendar collection,
  retention and derived rights, all twenty verified unique curated mappings,
  valid reviewed calendar authority and an open regular session. Quote retries
  reserve four account requests/minute for reference/action/status/calendar
  work; no speculative status/action network integration was added.
- Cold calendar construction runs through `asyncio.to_thread`. Derived refresh
  rechecks full current calendar evidence and writes only derived rows. Review
  expiry and exceptional overrides remain untouched. Outside regular sessions
  derived refresh can proceed without quote batches.
- Short read sessions close before HTTP. A temporary async HTTPX request hook
  reloads committed authority/mappings and verifies current time/session/lease
  before every attempt, including retries after 429. Hook removal occurs in
  `finally`. Current evidence, UTC and lease ownership are rechecked after
  source I/O and after guarded quote persistence before commit.
- `amain` runs the existing crypto loop and stock loop concurrently in a single
  `TaskGroup` when enabled. Stock exceptions are contained, and both loops use
  the existing injected monotonic cadence and stop cancellation. Heartbeat
  means process progress, including failed cycles; it does not claim source
  success. Disabled stock needs no provider keys and retains the original
  crypto-only path.
- A dedicated stock HTTP client carries provider headers; the crypto client
  carries none. Only scheduler receives keys in either Compose file. API gets
  nonsecret enable/feed/account/server scope. Every lane defaults to disabled;
  production datastore/TLS routing and crypto source constants are unchanged.

## Task Commits

1. **07-09-01 RED** — `2e11350`: Specify bounded admitted stock collection.
2. **07-09-01 GREEN** — `e2d0ee8`: Collect admitted stocks under independent bounds.
3. **07-09-02 RED** — `42ddbbe`: Require independent stock loop lifecycle.
4. **07-09-02 GREEN** — `503ad95`: Schedule stock and crypto loops independently.

Both tasks have meaningful behavioral RED/GREEN evidence. Task1 RED included
an intentionally disabled initial callable boundary so its observed failure
was zero provider calls versus one required permitted batch, rather than a
missing import. The final implementation replaces that initial boundary.
Task2 RED failed real loop-start and configuration assertions.

## Verification

- Exact combined plan slices: `uv run pytest tests/test_stock_scheduler.py
  tests/test_scheduler_loop.py tests/test_scheduler.py
  tests/test_config_scheduler.py -q` — **90 passed in 10.93 seconds**.
  These comprise 29 stock-cycle tests and 61 lifecycle/crypto/config tests.
- Real disposable PostgreSQL/Redis, with provider HTTP mocked by respx only:
  permitted twenty-symbol persistence with original source times; no open
  transaction during HTTP; denied/expired scopes; missing verification; quota
  refusal; no out-of-session quote requests; immutable calendar review; partial
  symbols; retained previous quotes after 403/429/500; midflight revocation of
  quote/reference/calendar; mapping removal; actual lease expiry/replacement;
  post-I/O session close; retry revocation; cycle deadline; down Redis;
  token-owned release and orderly cancellation.
- Combined live-loop test holds a hanging mocked stock HTTP request while
  real crypto cycles continue. It observes both real Redis leases during a
  later hanging crypto request and confirms both are released on shared stop.
  Separate lifecycle tests prove unexpected stock exceptions cannot terminate
  crypto and the private stock client closes on shutdown.
- Scoped Ruff check/format and mypy on both scheduler modules pass.
- Both Compose files pass `docker compose --env-file /dev/null ... config
  --quiet` using synthetic command-local inputs only. No private env file was
  loaded and no service was started/restarted by these source checks.
- `git diff --check` passes; no tracked file deletion or dependency change.
- Four existing calendar-package pandas deprecation warnings appeared during
  cold calculation. They do not fail the checks; no unrelated package change.

## Deviations from Plan

None requiring scope expansion. Temporary HTTPX request hooks and a separate
TTL cadence key implement the specified retry-admission and one-batch-per-minute
requirements within the owned scheduler module. Per-test cadence cleanup and
calendar horizons were corrected while developing the synthetic fixtures.

Documentation lookup used official
[HTTPX event-hook documentation](https://www.python-httpx.org/advanced/event-hooks/)
for the before-network async hook contract; no Context7 tool/CLI was available.

## Known Stubs

No stub prevents the local scheduling goal. Status/action integration remains
explicitly unknown and unimplemented as required by this phase. Stock execution
remains disabled through Phase8. No fixture grants provider access or rights.

## Next Plan Readiness

Plan10 can consume the authoritative admission/session/quote interfaces for the
authenticated discovery API. Real restricted-TLS consumer evaluation and full
phase gates remain Plan13; provider permission, private quote coverage/freshness
and UI acceptance remain explicit Plan14 checkpoints. The healthy disposable
`birja-test` stack is retained for immediate serial Plan10 reuse.

No production resources, private configuration, provider credentials/services,
B2 storage, publication or deployment were accessed or changed.

## Self-Check: PASSED

All seven owned files exist; all four task commits exist on the current branch.
Final checks above passed. Whole-phase requirements intentionally remain pending.
