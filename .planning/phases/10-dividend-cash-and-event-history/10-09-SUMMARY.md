---
phase: 10-dividend-cash-and-event-history
plan: "09"
subsystem: dividend-scheduler
tags: [retained-keysets, bounded-cycles, restricted-sql, independent-loops]
requires:
  - phase: 10-08
    provides: Actual restricted concurrent financial fixture and wait proofs
  - phase: 10-11
    provides: Private exact mixed History and Portfolio compatibility
  - phase: 10-06
    provides: Passed pre-consumer retained recovery and restricted TLS prerequisite
provides:
  - Two independent bounded retained-work keysets and fair cursor wrap
  - Actual worker-to-restricted-SQL-to-History original/hold/reconciliation proof
  - Independent supervised dividend loop with cancellation cleanup
affects: [10-13, 10-15, 10-16, 10-17]
tech-stack:
  added: []
  patterns: [disposable-progress-cursors, sql-owned-financial-authority, independent-supervision]
key-files:
  created: [backend/app/tasks/dividends.py, backend/tests/test_dividend_scheduler.py]
  modified: [backend/app/tasks/scheduler.py, backend/tests/test_scheduler_loop.py, backend/tests/test_scheduler.py]
key-decisions:
  - Independent retained targets and paid anchors each receive at most50 candidates under one40second timeout.
  - Progress cursors are disposable scheduling hints; restart safely rescans immutable SQL-deduplicated accounting.
  - Conservative uncertainty discovery excludes ordinary healthy anchors without recreating financial authority in Python.
requirements-completed: []
requirements-supported: [DIV-03, DIV-04, DIV-05]
duration: approximately20min
completed: 2026-11-13
---

# Phase10 Plan09: Bounded retained dividend scheduling

**Independent retained keysets dispatch verified payouts and uncertain paid
anchors through existing SQL authority, while supervised failure/cancellation
leaves crypto cadence and committed accounting independent.**

## Tasks and commits

1. RED `e774fa8`: callable absent-worker seam left actual cash100 rather than
   expected101;1failed/1.54s. GREEN `098ed5a`: two durable DB work sources,
   bounded fair cursor wrap and actual financial/History tests.
2. RED `c6765e8`: dividend loop never started beside crypto;1failed/.99s.
   GREEN `ecafe83`: independent lifecycle plus actual financial wait timeout,
   funded correction and sell-after-cutoff discovery checks.

No staged seam remains. SQL functions, service transaction boundaries, schema,
recovery identities, admission policy and runtime grants are unchanged.

## Actual verification

| Gate | Executed result |
|---|---|
| First real retained payout GREEN |1passed/1.37s |
| PaidA→uncertain/cancelledB→reviewed successor |4passed/2.30s |
| Expanded bounded worker suite |9passed/4.71s;53statements/14branches100% |
| Worker/lifecycle/scheduler combined |60passed/8.24s;270statements/58branches100% |
| Actual sell-after-cutoff discovery |1passed/1.57s |
| Final affected financial/API/scheduler gate |132passed/13.99s;4 existing pandas warnings |
| Final critical service+worker+modified scheduler |311statements/64branches,0missing/partial,100% |
| Ruff/format and Mypy |5owned files and2application modules pass |
| Whitespace/deletion/stub check |Pass; no tracked deletion or remaining stub |

Final command uses locked `uv run --no-sync --no-cache pytest` on
test_dividend_scheduler, test_scheduler_loop, test_scheduler, test_dividend_payments,
test_dividend_corrections and test_event_history_api, with branch coverage and
`--cov-fail-under=100` for tasks.dividends, tasks.scheduler and services.dividends.
Log `/tmp/birja-phase10-09-affected.log`; coverage
`/tmp/birja-phase10-09.coverage`. Other retained logs:
`/tmp/birja-phase10-09-task1-{red,green,expanded}.log`,
`/tmp/birja-phase10-09-task2-{red,green}.log`,
`/tmp/birja-phase10-09-sale.log`. Parent owns full Wave8 backend/frontend gates.

Actual105-owner DB discovery produces batches50/50/5 and wrap50. Both paths
together attempt exactly100 in a cycle. Separate cursor hints advance before
each attempt, so refused/held work cannot pin later owners. A process restart
loses scheduling hints only, rescans retained rows and relies on SQL replay and
dedup; no financial truth resides in memory or Redis. Redis lease is optional
under C04 and is not added.

The verified path selects only the latest `(version,id)` owner/event snapshot
tied to current supported terms and a reached New York payable date. The paid
anchor path is independent of that helper: current unsupported/held/missing
terms, monitoring uncertainty or retained uncertain observations/revisions make
anchors candidates. Ordinary healthy anchors are excluded. Historical uncertainty
is deliberately conservative: after reviewed resolution it may remain a candidate
that SQL safely refuses. Discovery never decides financial rights, sums amounts
or invents verified terms. Every candidate has one separate service transaction;
no immediate failed retry or business query after the final SQL guard is added.

Actual restricted scheduler sessions prove original credit once, zero-cash
uncertain/cancelled hold with empty latest-verified helper, stable repeat dedup,
owner-visible History, reviewed applied successor and immutable original.
Pre-anchor uncertainty publishes nothing. Repeated unaffordable target stays
held; later funding applies one linked successor. Genuine stock sale removes
the holding before retained entitlement discovery but does not erase its credit.
These consume retained interfaces already proven across0013→0014 by06; they do
not claim another migration/restore exercise.

One asyncio timeout encloses both discovery and every financial transaction.
An actual Account lock, observed with pg_blocking_pids, is cancelled under the
same cycle deadline and leaves cash/events unchanged. Discovery timeout and
external cancellation run cleanup; external cancellation propagates. Independent
slow/failing dividend loops do not block three crypto cycles; shutdown awaits
their cleanup. Only sanitized fixed reasons/counts or exception class are logged.

## Deviations and cleanup

Parent approved the narrowly necessary extension to test_scheduler.py's startup
loop count/result assertions. No unrelated test was changed. Initial fixture
draft guessed a nonexistent reconciliation helper; replaced it with the existing
explicit synthetic reviewed-resolution SQL pattern, preserving real authority.
An after-sale draft used an incorrect wire field, corrected to existing
expected_exec_price. These construction failures are not represented as passing
gates. No successful financial effect was mocked or invariant relaxed.

Independent final owned-DB query:0014; payments0, decisions0, entitlements0;
temporary scheduler role0; disabled immutability triggers0; migrator cash UPDATE
and payment INSERT false; pending clients0. Added105-owner test data is cleaned
by its guarded disposable-owner maintenance after behavior, then the existing
fixture restores its temporary grants/role. Only birja-test stays running.

Context7 MCP/ctx7 were unavailable; no tool was installed. Consulted official
[Python3.14 cancellation/timeout documentation](https://docs.python.org/3.14/library/asyncio-task.html#timeouts).
No dependency/runtime upgrade was inferred from documentation patch versions.

T-10-09-01/02 mitigated by SQL-owned authority, real restricted financial effects,
immutable lineage and saved History assertions. T-10-09-03 mitigated by bounded
two-path discovery, observed waits/timeouts, fair wrap and verified cleanup.
T-10-09-SC: no package/image/lock changes. No unplanned trust surface or known
stub remains. Existing actions-enabled/admission gates stay decisive; no new
live escape setting, HTTP/provider transport or optimistic cash exists.

No real.env/secrets, provider, production, B2, timer, installed-tool, publication
or deployment action occurred. Final integration/recovery/security/browser and
owner new-UI/native200% acceptance remain later declared gates. Parent owns
canonical planning state and full requirement completion.

## Self-Check: PASSED

All5owned source/test files and summary exist; four task commits exist without
deletion. Actual132tests, strict311statement/64branch100%, scoped static checks
and independent cleanup pass. Unrelated .claude is preserved; DB ownership is
released to parent.
