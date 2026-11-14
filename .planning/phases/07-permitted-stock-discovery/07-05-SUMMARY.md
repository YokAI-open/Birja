---
phase: 07-permitted-stock-discovery
plan: "05"
subsystem: api
tags: [admission, calendar, permissions, pydantic, security]
requires:
  - phase: 07-04
    provides: Actual restricted TLS roles and exact authoritative calendar recovery
provides:
  - Pure product/purpose/generation/expiry admission with bounded calendar authority
  - Disabled stock settings and scheduler-only provider SecretStr credentials
  - Migrator-only evidence import/revoke and verified-TLS dry-run packet
affects: [07-06, 07-08, 07-09, 07-10, 07-13, 07-14]
tech-stack:
  added: []
  patterns: [per-product fail-closed evidence, generation-bound authority]
key-files:
  created:
    - backend/app/services/stock_admission.py
    - backend/tests/test_stock_admission.py
    - deploy/STOCK-DATA-ADMISSION.md
  modified:
    - backend/app/core/config.py
    - .env.example
key-decisions:
  - "Decision authority stays exclusively in migrator-owned admission evidence; session rows cannot renew review."
  - "Administrative DSN/evidence paths stay operator-shell-only, never in API/scheduler settings."
requirements-completed: []
duration: 8min
completed: 2026-11-10
---

# Phase 7 Plan 5: Product-specific admission Summary

**Scoped evidence evaluation rejects revoked, expired, mismatched or malformed authority; disabled configuration and a private migrator dry-run packet prepare later activation.**

## Performance

- Started: 2026-11-10T15:00:00Z
- Completed: 2026-11-10T15:08:00Z
- Tasks: 2/2
- Files: 5 implementation/test/documentation files

## Accomplishments

- ProductAdmission/AdmissionDecision/evaluate_admission cover reference, quotes,
  actions, status and calendar independently for collection/display/derived/retention.
  Exact deployment/audience/feed, reviewed terms, fields, quota and UTC validity
  are checked; denial exposes no raw evidence/contracts/credentials.
- Expected generation detects derived-state races. Evaluation expires at the
  earliest permission/calendar-review boundary; downstream callers must reload
  current committed evidence and fresh time after awaited work.
- Calendar review validates both exchange scopes, official NYSE/Nasdaq provenance,
  reviewed version, maximum24h review, fixed45past/90future horizon, unique dated
  closed/shortened overrides and UTC/New York bounds. Sessions confer no authority.
- Shared nonsecret settings default disabled/IEX/60s, bound response/retry/cycle
  limits; only SchedulerSettings parses provider SecretStr keys, and enabled
  scheduler configuration requires both keys. A key/flag cannot authorize data.
- Operator packet covers initial denied rows, locked generation-changing import,
  default rollback, revocation, protected administrative DSN/file, exact shared
  verified-TLS connection and positive/adverse dry-run review. No runtime endpoint.

## Task Commits

1. Task07-05-01 RED `e643529`; GREEN `14ff559`.
2. Task07-05-02 RED `2adf000`; GREEN `dda5ac6`; executable TLS wrapper `1aea40c`.

Task1 RED used explicit deny-only contract values:22 behavioral failures and36
passes, without missing-import failure. Task2 RED showed absent configuration
validation/secret separation. Task1 final58 tests passed; final standalone
admission slice74 passed; admission+scheduler/prices configuration slice114 passed.

## Verification

- `cd backend && uv run pytest tests/test_stock_admission.py -q`:74 passed.
- `cd backend && uv run pytest tests/test_stock_admission.py tests/test_config_scheduler.py tests/test_config_prices.py -q`:114 passed.
- Scoped Ruff check/format and mypy on both changed production modules passed.
- Three operator Python blocks compiled with top-level-await support; they were
  not executed against production or a provider. Full actual administrative
  activation and persisted consumer proof remain later gates.
- `git diff --check` passed; no tracked deletions. Existing unrelated `.claude/`
  remains untouched. Tests used isolated birja-test Redis; no production access.

## Decisions Made

Calendar overrides accept supported closed or shortened regular sessions only;
unverified normal/extended session changes fail closed. Administrative evidence
path and DSN are documented private operator variables rather than granting new
runtime administration settings. Product rights fixtures are not legal truth.

## Deviations from Plan

None requiring scope/architecture changes. Shared nonsecret stock configuration
uses one bounded settings base; provider fields remain scheduler-only. The
operator packet uses existing database_connect_args verified TLS, never a new
connection/security implementation. No dependencies were added.

## Issues Encountered

Sandbox uv cache writes required authorized test-command escalation; no global
packages were changed. Local static commands use the existing virtualenv tools.
The initial documentation phrase-check test was removed: compiling the concrete
examples and reviewing their transaction semantics is more meaningful than
asserting wording; behavioral configuration cases remain mandatory.

## User Setup Required

No current action. Future07-14 scope approval must explicitly establish actual
product rights/account coverage and bounded private verification before activation.
No signup, provider contact, agreement, payment, private request or deployment
was performed. Disabled/offline development requires no provider credentials.

## Next Plan Readiness

07-06 can consume evaluate_admission and the explicit quota/field contracts.
07-08 implements the genuine session evaluator;07-09/10 wire checks at every
fetch/storage/read boundary, including final post-await projection.07-13 must
prove persisted restricted-TLS consumer semantics and full critical coverage.
DATA-01 and whole-phase success criteria remain pending; fixtures do not prove
permitted live discovery. Stock trading stays disabled through Phase8.

## Self-Check: PASSED

All three created files and five task commits exist. Both tasks have ordered
behavioral RED/GREEN commits. No blocking stubs or new unplanned security surface;
source contains no provider networking or administrative write endpoint.
