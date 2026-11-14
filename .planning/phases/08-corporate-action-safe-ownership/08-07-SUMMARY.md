---
phase: 08-corporate-action-safe-ownership
plan: "07"
subsystem: scheduler
tags: [postgresql, corporate-actions, bounded-replay, redis, least-privilege]
requires:
  - phase: 08-04
    provides: Bounded REST and finite historical mutation replay
  - phase: 08-06
    provides: Instrument-serialized immutable observations and financial actions
provides:
  - Durable fixed-target action catch-up with resumable REST pages and bounded replay intervals
  - Atomic twenty-instrument monitoring health with final authority and epoch checks
  - Independent disabled-by-default action loop and actual shared account-attempt budget
affects: [08-08, 08-09, 08-12, 09-stock-trading, 10-dividend-payments]
tech-stack:
  added: []
  patterns: [durable-segment-frontiers, atomic-monitor-publication, rolling-account-attempt-budget]
key-files:
  created: [backend/app/tasks/stock_actions.py, backend/tests/test_stock_action_monitoring.py]
  modified: [backend/app/tasks/scheduler.py, backend/app/tasks/stock_scheduler.py, backend/app/core/config.py, backend/app/services/alpaca_actions.py, backend/app/services/corporate_actions.py, .env.example, docker-compose.yml, docker-compose.prod.yml]
key-decisions:
  - Partial observations and bounded continuations are durable, but only complete verified intervals advance coverage.
  - One global health publication checks all twenty committed epochs without acquiring multiple ownership gates.
  - A successful feed cannot clear immutable event or missing-identity holds.
  - Real HTTP attempts share a Redis rolling account limit; unrelated denied product rows supply no quota authority.
requirements-completed: []
requirements-addressed: [DIV-01, ACT-02, ACT-03]
duration: 31min
completed: 2026-11-11
---

# Phase 8 Plan 07: Durable Action Monitoring Summary

**Complete fixed-target discovery, retained-ID checks and historical replay establish bounded monitoring health while persistent event holds survive recovery and crypto keeps its independent loop.**

## Scope and implemented interfaces

Two tasks, approximately31minutes, fifteen implementation/test/config files.
All financial fixtures use guarded isolated birja-test PostgreSQL/Redis; all
provider HTTP is mocked. Dependencies, schema, database privileges and recovery
contracts are unchanged. Actions default OFF and stock execution remains OFF.
No private credentials/configuration, provider API, production, B2, timer,
existing Phase7 process, publication or deployment was accessed or changed.

`run_stock_action_cycle(sessionmaker, redis, http, settings, now)` owns a separate
45-second Redis lease and at-least60-second cadence, with a30-second whole-cycle
deadline. The adapter retains its8 actual attempts,20 pages, response/cumulative
byte and mutation/frame bounds. Current action REST/replay, calendar and reference
authority, verified twenty-stock identity and complete ownership journals are
required. Trusted account/server scope is forwarded to every financial service.
No HTTP runs inside an instrument financial gate.

Each instrument commits its observations and progress together under the existing
single-instrument gate. Retained JSON markers bind to exact authority, scope,
mapping and baseline policy, preserve a fixed historical terminal target and
resume validated REST page tokens. Completed process-date segments advance toward
the90-day future horizon. Known IDs are rechecked even after their discovery
window; absence is persisted as uncertainty, never fabricated deletion.

Finite replay preserves a verified completed frontier. A response/mutation/time
bound subdivides the pending time interval on subsequent cycles; inclusive shared
endpoints do not skip mutations. Only completed intervals advance the frontier.
Unfinishable density at the smallest representable interval remains explicitly
`replay_density_limit`, with no invented terminal ID or raised safety cap. The
retained-ID and per-instrument dividend-work bounds are1000; exceeding either
refuses explicitly instead of silently truncating. These are internal capacity
limits, not confirmed provider quotas or readiness evidence.

Partial work stays reconciling and does not renew a healthy lease. Final global
publication locks state rows in deterministic order, compares every committed
epoch/coverage point, checks current authority and actual DB time, and uses the
existing final SQL authority/mapping/unit guard. All twenty health updates commit
or roll back together. The deadline is the minimum of the120-second health cap,
product expirations and independently reviewed calendar expiration. Immutable
unsupported/conflicting/missing-observation reasons remain held regardless of
recovered HTTP. Only cash-dividend events reach entitlement derivation; splits
and unsupported events retain their own action-processing path.

The existing dedicated scheduler runs crypto, optional quotes and optional
actions concurrently with independent bounded cycles and clean cancellation.
Actions can run while quotes remain disabled. Its credentialed HTTP client uses
`trust_env=False`; disabled actions create no action client or action requests.
Only SchedulerSettings and scheduler Compose environments receive action policy
or Alpaca credentials; API settings gain no action-enable flag or credentials.

Every real quote/action request, including retries and failures, reserves one
atomic rolling60-second Redis account slot. Applicable admitted same-account
quote/action quotas and the configured cap bound the shared limit. Denied or
unrelated empty-quota rows cannot break independent quote collection. The old
four-unused-request reservation is removed; it was not an action entitlement.

## Task commits and TDD gates

- `f44df8d` — Task1 behavioral RED: twenty durable monitor states absent.
- `b906254` — Task1 GREEN: durable source continuity and atomic health.
- `1f40400` — Initial Task2 regression; a missing test import was corrected.
- `f90d204` — Actual Task2 RED: enabled actions with quotes OFF ran only crypto.
- `88f8076` — Review RED: ignored REST continuation, denied unrelated quota,
  calendar review overrun and mixed-event routing reproduced in real tests.
- `b4e2c33` — Review RED: inclusive mutation A replay after later revision B
  incorrectly raised `mutation_conflict`.
- `60c210e` — Task2 GREEN: independent loops, actual shared quota, reviewed
  source-continuity and immutable historical-replay corrections.

The valid RED gates assert observable behavior; missing imports/files are not
counted as behavioral RED. No task was skipped after its first implementation.

## Verification

Final focused command uses the existing venv, six test files and actual isolated
datastores:

```text
cd backend
.venv/bin/python -m pytest tests/test_stock_action_monitoring.py tests/test_alpaca_actions.py tests/test_corporate_actions.py tests/test_stock_scheduler.py tests/test_scheduler.py tests/test_config.py --cov=app.tasks.stock_actions --cov=app.services.alpaca_actions --cov=app.services.corporate_actions --cov=app.tasks.stock_scheduler --cov=app.tasks.scheduler --cov-report=term-missing -q -x
.venv/bin/coverage report --include=app/tasks/stock_actions.py,app/services/alpaca_actions.py,app/services/corporate_actions.py,app/tasks/stock_scheduler.py --fail-under=100
```

The final frozen-source run passes **342tests,20 existing calendar warnings,
74.26seconds**. Combined five-module coverage is99.56%; the four critical
monitor/adapter/accounting/quota modules pass **1155statements/428branches100%**:
alpaca_actions505/220, corporate_actions315/118, stock_actions203/60 and
stock_scheduler132/30. No source changed after this final frozen run.
Earlier actual results:37monitor cases passed44.27s;3 real REST-restart/replay
subdivision/density cases passed10.23s; full accounting77cases passed11.87s with
315statements/118branches100%. The combined342-case behavioral run passed76.38s;
its quote scheduler coverage mapping was invalidated by concurrent format-only
line movement, so that coverage artifact was rejected and the frozen-source
focused run was repeated. No test/security threshold was lowered.

Scoped Ruff lint/format passes on12 source/test files; backend-context mypy passes
on6 source files. Dev and production Compose configuration validation passes
with `.env.example` and explicit synthetic required production role/email values,
without reading real `.env` or protected production files. `git diff --check`
passes. No dependency/image/operations rerun is claimed; the parent owns Wave5's
full integration gate and Plan12 retains final security/image/recovery proofs.

## Deviations from plan

1. **[Rule2 — correctness] Actual shared quota hook.** Narrowly changed
   `tasks/stock_scheduler.py` and tests under parent authorization so both
   products reserve real attempts; no comment-based quota entitlement remains.
2. **[Rule1 — resumability] Incoming REST page token.** Parent authorized the
   narrow existing adapter/test extension. Validated tokens remain query data
   for the fixed origin and original filters; every existing transport/byte/
   page/attempt/permission bound remains enforced. Replay uses documented finite
   timestamp pairs and durable interval subdivision instead of an unsupported
   `since_id + until` combination.
3. **[Rule1 — immutable replay] Historical duplicate observation.** Independent
   review exposed a Plan06 integration bug. Parent authorized a narrow
   `corporate_actions.py`/test correction: find an already recorded mutation
   BEFORE revision/pointer changes, compare incoming economic terms with its
   original immutable observed revision, return that stored result unchanged,
   and reject divergent reuse. Rate/cancellation/units/date adversarial cases
   preserve latest pointer, safety epoch and row counts after rollback.
4. **Task ordering.** Bounded scheduler-only settings were introduced with the
   monitor's first implementation so service tests use the actual policy model;
   Task2 completes its validation, independent loop and Compose integration.

Independent07review closes all five findings, including the historical replay
integration correction. Final `stock_scheduler.py` SHA256
`98878dd757b32b34a960ebf5a7a3813be1b1fb1812720de2893276a041290f56`
differs from its reviewed hash only by Ruff signature formatting; semantics are
unchanged. Final accounting source SHA256
`804be2019da553662f46afa3f8071807c052c6f7e894e2b3a27dfc8a6fe82e60`
is independently re-reviewed.

## Handoff and remaining gates

Plan08 owns privileged resolution and schema0012 recovery. It must preserve the
exact instrument gate key, immutable observation/revision lineage and scoped
review decisions; ordinary source recovery must never resolve historical holds.
Plan09 consumes bounded health, persistent holds, units and known boundaries in
its final API/quote authority checks. Partial progress is not current monitoring.
Plan12 retains full static/build/browser/security/image/exact-recovery gates.
Plan13 retains explicit owner UI and activation disposition. Phase7 live access
and real action rights/quota/replay history remain deferred external gates.
No whole-phase requirement or live readiness is marked complete by this plan.

## Known stubs

None. Source collection is intentionally default-disabled pending separately
verified activation gates; no placeholder cash, History or order path is added.

## Self-Check: PASSED

Created monitor/test files exist. All seven recorded implementation/RED commits
resolve in git, final source/tests are committed and no tracked file was deleted.
Final frozen critical coverage and independent review pass. Only the parent-owned
review record, this summary and preserved unrelated `.claude/` remain outside
the source commit; no runtime output or secret was staged.
