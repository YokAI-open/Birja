---
phase: 07-permitted-stock-discovery
plan: "08"
subsystem: api
tags: [calendar, exchange-calendars, postgres, authority, python314, wolfi]
requires:
  - phase: 07-06
    provides: Exact quote rules and structural regular-session bounds
  - phase: 07-07
    provides: Explicit approval of exact calendar dependency resolution
provides:
  - Reproducible approved calendar wheels with actual hardened runtime and strict scan proof
  - Reviewed generation-bound regular sessions, current/next decisions and guarded atomic persistence
affects: [07-09, 07-10, 07-13, 07-14]
tech-stack:
  added: [exchange-calendars 4.13.2, numpy 2.5.4, pandas 3.1.1, pyluach 2.3.0, toolz 1.2.0, tzdata 2026.6, korean-lunar-calendar 0.4.0, python-dateutil 4.0.0]
  patterns: [Immutable package bounds cache with uncached current authority, Full-snapshot guarded INSERT SELECT]
key-files:
  created: [backend/app/services/stock_sessions.py, backend/tests/test_stock_sessions.py, backend/tests/test_stock_calendar_runtime.py]
  modified: [backend/pyproject.toml, backend/uv.lock]
key-decisions:
  - "Calendar package calculates derived bounds only; current migrator-owned admission establishes authority at each evaluation."
  - "Atomic session refresh compares the full authority snapshot and database-clock expiry without admission UPDATE grants."
requirements-completed: []
duration: 14min
completed: 2026-11-10
---

# Phase 7 Plan 8: Reviewed regular-session calendars Summary

**Official-session boundaries, bounded current/next decisions and atomic derived refresh now require current authoritative calendar evidence and matching generations; stock execution remains disabled.**

## Performance

- Approximately 14 minutes, 2026-11-10T18:27Z–18:41Z; two tasks, five owned files.
- Both tasks complete locally. This does not complete the phase or establish provider permission.

## Accomplishments

- `uv add --no-sync` added exactly the eight approved versions. Actual lock
  review confirmed PyPI registry identities, matching reviewed Linux amd64/
  universal wheel hashes, zero existing version changes and zero removals.
  `uv sync --locked --no-build` installed wheels only; no source build or global
  package installation occurred. The source/provenance protocol remains ASSUMED,
  as explicitly disclosed and approved in07-PACKAGE-REVIEW.md.
- `RegularSession` contains derived exchange/date/bounds/coverage/generation only.
  `build_sessions(now, evidence)` generates up to272 rows (two exchanges,
  inclusive45-day past/90-day future horizon) within authoritative coverage.
  Current tagged XNAS/NASDAQ aliases are verified against official NYSE and Nasdaq
  holiday/early-close fixtures; no weekday or fixed UTC algorithm was added.
- `session_at(exchange, now, sessions, current_calendar_admission)` returns
  `SessionDecision(state,current,next_session,valid_until,executable=False)`.
  Unknown/expired/revoked evidence, missing current/next/intervening rows,
  duplicates, forged bounds and mismatched generations fail closed. Open is
  inclusive and close exclusive. Published Thanksgiving, early closes and both
  spring/fall DST boundaries are tested.
- Authoritative closed/shortened overrides are applied from calendar admission
  JSON only. A shortened override cannot invent a holiday session or extend
  package boundaries. Old derived bounds remain unknown after migrator generation
  replacement; a matching refresh works. Fresh derived rows cannot renew expired
  review, establish authority or change its JSON.
- `persist_sessions(db,sessions,evidence,now)` performs one bounded atomic
  INSERT SELECT with full evidence snapshot/generation and database-clock
  validity/review-expiry guards. Caller owns the short commit. Runtime does not
  lock/update admission rows or delete retained evidence. `load_sessions(db,now)`
  reads ordered bounded derived rows; consumers must load current authority too.
- `discovery_eligibility` preserves independent calendar, quote, status and action
  facts. Yesterday/120-second-old quotes fail; status/actions remain unknown
  without their own monitoring. Every result keeps `executable=False`.

## Task Commits

1. Task07-08-01 exact dependency/runtime proof: `57eeee6`.
2. Task07-08-02 meaningful RED contracts/assertions: `3c105b4`;
   GREEN implementation/database proofs: `939375c`.

RED produced24 assertion failures and9 refusal passes against deny-only session
contracts. No import, missing package, unavailable test service or syntax error
is counted as behavioral RED.

## Verification

- Exact Task1 runtime slice:4 passed. Exact Task2 calendar/quote slice:84 passed
  after final refusal cases. Combined owned slice:88 passed on host Python3.14.9.
- Session service scoped coverage:100% statements and branches,103 statements/
  34 branches, with fail-under100. This is scoped evidence; full-phase gates
  remain07-13.
- Real isolated PostgreSQL verifies exact272-row persist/load and same-generation
  refresh, committed migrator generation replacement, stale snapshot refusal,
  unchanged authoritative review/JSON, and DB-clock expiry despite stale injected
  process time. Restricted verified-TLS consumer integration remains07-13.
- Actual unchanged hardened test-builder runs all88 tests as UID1001, read-only
  root filesystem, no capabilities and synthetic test-only DB/Redis:88 passed
  under Python3.14.10. Actual final runtime imports NumPy/pandas/calendar and runs
  the genuine session helper for both exchanges' November27 early close as
  nonroot with networking disabled/read-only root.
- `uv run pip-audit`: no known vulnerabilities. Ruff lint/format and strict mypy
  pass on owned files/service; git diff whitespace checks pass. No tracked files
  were deleted, and unrelated `.claude/` was preserved.
- All five final actual-image strict Trivy lanes pass with zero HIGH/CRITICAL
  findings, including unfixed vulnerabilities. Scanner, severity, image family,
  interpreter, Dockerfile and CI gates remain unchanged. Evidence:
  `/tmp/birja-phase07-calendar-final-scans/status.json` and per-lane JSON/logs.
  Database UpdatedAt2026-11-10T13:03:09Z, NextUpdate2026-11-11T13:03:09Z.

### Exact identities

| Artifact | SHA256 |
|---|---|
| uv.lock | `81c8421f541a5a37966bfe5a87f0e642301911ce5ed345b0c49d37a655f73e69` |
| pyproject.toml | `3071054462750bd4297f973d33d685b15d732ba2e3ee2b380c703dadc9db62fd` |
| unchanged backend/Dockerfile | `e7fc0740fdf1423f368d688181e582285f967b30c501a8ce99c73b7951a12cf5` |
| unchanged CI | `349cffc06f7d2f010652fb8961f19a5d40e7e528826467db63e2f09de4a7c633` |
| final runtime image | `83f7a3f680a6f31eae1e013546a1fbafccda7bf77febfb9e59ef9e89f28ee115` |
| final test-builder image | `613ab46aefa877f9fbccb80edfc133db3b23ab92025866fda6a463dd4ac6126d` |
| current unchanged Node toolchain | `e44078913d853de420bdd91a255281140c0265c93c18f5675e5088416d6ff16e` |
| PostgreSQL image | `f131db66371391e404c80cef7dd40f31b1b54eb264a6cb032925d9a3859f93f4` |
| Redis image | `26bb2dd4412f902f3decd44fba5dfaef4360d97004d44f6cff7f28d6aba19c48` |

## Source evidence

- Tagged API documentation: https://raw.githubusercontent.com/gerrymanoim/exchange_calendars/4.13.2/README.md
- Official2026 NYSE dates/regular hours: https://www.nyse.com/trade/hours-calendars
- Official2026 Nasdaq dates/early closes: https://www.nasdaq.com/market-activity/stock-market-holiday-schedule

These public schedule fixtures and synthetic administration values establish
program behavior, not current production calendar review, live quote rights or
account entitlements. The package cannot detect every surprise closure.

## TDD Gate Compliance

Task2 has actual meaningful RED followed by GREEN. Task1's lock/install/runtime
proof is dependency configuration and acceptance validation: tests were added
after the approved wheels-only installation; no package behavioral RED is
claimed. Its `tdd=true` task annotation therefore has no independent RED commit.
Failing a missing import would not be a valid substitute. Plan frontmatter is
`type: execute`, with phase-wide tdd_mode false; this exception is explicit.

## Deviations from Plan

No architecture, provider, image or gate change. Task1's TDD limitation is recorded
above. During tagged API adaptation, package `is_session` rejected closed horizon
edge dates outside its first/last actual session: deriving the open-date set from
the package schedule preserves closed entries without guessing holidays.

## Issues Encountered

- Initial pytest setup correctly refused absent isolated Redis; the disposable
  guarded test stack was recreated before meaningful RED/final tests.
- An initially selected historical Node image had48 findings; rebuilding the
  unchanged current toolchain produced the correct current lane with zero.
- A final Docker export hit a missing cached parent snapshot. An unchanged
  no-cache build succeeded; no cache pruning, daemon restart or image alteration.
- Upstream calendar internals emit40 pandas3.1 deprecation warnings across the
  owned slice. Tests/runtime pass; no warnings or security gates were suppressed.

## User Setup Required

None for these local tasks. No private provider calls, production data/config,
service/timer changes, B2 access, payment, publication or deployment occurred.

## Next Plan Readiness

07-09 can call these real helpers from its bounded stock cycle, keeping package
calendar construction off the async loop on cold calculations. Re-read current
calendar evidence after awaits and use fresh UTC; derived rows never grant
permission. Scope/account/server inputs to admission remain the established
Birja defaults for this plan; deployment-specific callers must use consistently
verified admission scope. Actual restricted-TLS consumer proof, final combined
gates, provider permission/access and UI acceptance remain07-13/14. All Phase7
requirements stay pending; no stock execution is enabled in Phases7–8.

## Self-Check: PASSED

All five owned files and recorded task commits exist. Final owned tests/static
checks, actual hardened native/runtime proof and all five strict image lanes pass.
No blocking stubs or unplanned trust surface: unknown/empty refusal outcomes are
deliberate tested policy. Admission authority remains migrator-owned; no new
endpoint, credentials, financial writes or schema changes were introduced here.
