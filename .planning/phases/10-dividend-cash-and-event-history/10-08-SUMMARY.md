---
phase: 10-dividend-cash-and-event-history
plan: "08"
subsystem: financial-concurrency
tags: [postgresql, independent-sessions, shared-cash, advancing-authority]
requires:
  - phase: 10-07
    provides: Transaction-owned immutable dividend application and hold services
  - phase: 10-06
    provides: Passed retained recovery and restricted-role/TLS prerequisite
provides:
  - Actual concurrent original/correction/hold and stock/crypto cash proofs
  - Observed gate, account and injected deferred-constraint wait proofs
  - Guarded committed financial fixture with verified role/trigger/grant cleanup
affects: [10-09, 10-11, 10-15, 10-16, 10-17]
tech-stack:
  added: []
  patterns: [independent-restricted-sessions, observed-pg-blocking-pids, authenticated-test-barriers]
key-files:
  created:
    - backend/tests/dividend_fixtures.py
    - backend/tests/test_dividend_concurrency.py
    - backend/tests/test_dividend_waits.py
  modified: []
key-decisions:
  - Prove existing correct SQL behavior without introducing artificial production defects for RED.
  - Distinguish newly loaded valid authority after initial waits from captured authority changed after constraint waits.
  - Inject only a temporary deferred synchronization callback; never weaken or replace an existing financial invariant.
requirements-completed: []
requirements-supported: [DIV-03, DIV-04, DIV-05]
duration: approximately15min
completed: 2026-11-13
---

# Phase10 Plan08: Concurrent cash and advancing authority

**Independent restricted PostgreSQL clients publish originals, corrections and
holds once, preserve shared cash under stock/crypto races and refuse stale
captured authority after actual database waits.**

## Tasks and commits

1. `15013a6` — actual concurrent originals, A→B→A targets, stock/crypto spending,
   original/correction failure before commit, lost response after genuine commit,
   held→funded/reviewed successors and atomic cash/History visibility. Each worker
   has a separate connection/session; SQL owns financial effects and locks.
2. `e9f6e6b` — actual gate/account/constraint waits, changing retained rights,
   current revision, newer held entitlement, cutoff, units, monitor and persistent
   uncertainty; advancing rights/monitor expiry, no-cash hold revalidation,
   cancellation, verified zero, numeric overflow and trading-state independence.

No application service, SQL authority, migration, grant policy, recovery source,
dependency or image changed. Parent owns canonical STATE/ROADMAP/requirements.

## Actual verification

| Gate | Result |
|---|---|
| Initial genuine eight-worker original contention |1 passed/1.50s |
| Final Task1 concurrency suite |13 passed/4.42s |
| Initial complete Task2 wait suite |41 passed/13.84s |
| Final combined suite with persistent uncertainty |57 passed/17.77s |
| Combined new/service/authority/stock-concurrency regressions |161 passed/28.08s;8 existing pandas warnings |
| Existing critical dividend service |41 statements/6 branches,0 missing/partial,100% |
| Scoped Ruff/format |4 files pass |
| Scoped Mypy |Existing dividend service passes |
| Whitespace/owned-file/deletion checks |Pass;3 test files only, no tracked deletion |

Logs: `/tmp/birja-phase10-08-initial.log`,
`/tmp/birja-phase10-08-concurrency-final.log`,
`/tmp/birja-phase10-08-waits-final.log`,
`/tmp/birja-phase10-08-combined.log`,
`/tmp/birja-phase10-08-affected.log`.
Coverage: `/tmp/birja-phase10-08.coverage`.

Final affected command uses existing locked `uv run --no-sync --no-cache pytest`
for dividend_concurrency, dividend_waits, dividend_payments,
dividend_corrections, dividend_authority and stock_trading_concurrency, with
`--cov=app.services.dividends --cov-branch --cov-fail-under=100`.
The57-test combined suite exceeds both plan selectors. Parent retains the
full backend/critical financial-wave gate after Plan11.

## What the waits prove

Every wait is observed through `pg_blocking_pids` from an independent observer,
with bounded waits and final task cancellation/rollback. Gate and cash-row locks
are genuine existing locks. Dividend-only transactions currently have no natural
deferred callback to block: the fixture adds a uniquely named, guarded test-only
DEFERRABLE constraint trigger whose only effect is an advisory synchronization
wait during the actual `SET CONSTRAINTS ALL IMMEDIATE` inside the unchanged
financial function. Existing triggers/constraints remain enabled during behavior.
This is an injected timing barrier, not a claim of a naturally occurring
production constraint. Its owner/body/path/function linkage and deferred flags
are authenticated before removal in `finally`.

Invalid rights, units/cutoff, revision, newer held eligibility, monitoring and
persistent uncertainty refuse without cash or published-event changes. Valid
same-generation attribution/calendar-version changes before the initial authority
load are safely accepted using the current loaded rows; those exact changes
after authority capture at the constraint wait refuse. The API input contract
pins revision/entitlement fingerprints, not a caller-provided admission digest.
Actual clock expiry during the wait refuses even without a new row edit.
No-cash hold work needs current rights/revision after waits but no fabricated
verified target. Original replay semantics remain unchanged.

Concurrent readers see neither uncommitted cash nor History, then both after
commit. A held debit applies0, preserves nonnegative cash and can later append
one successful linked successor. Paused actual SQL/failure injection tests never
mock successful financial effects; response-loss simulation occurs after a
genuine committed service result. Existing source tests retain final-business-
statement ordering; no source modification introduced a later query/await.

## TDD gate compliance and fixture corrections

The first genuine behavior test passed because Plans02/07 already implement
the required authority and transaction behavior. Investigated before extending
the test proof; no artificial production defect, staged stub or fabricated RED
commit was introduced. **Deviation: these test-only tasks have proof commits,
not a RED→production-GREEN pair.** Parent explicitly required this honest
handling when existing behavior is already correct.

Initial wait assertions wrongly expected a still-valid metadata change before
initial authority capture to refuse; corrected to the current contract above.
A newer held entitlement fixture initially used NULL quantity, but existing
retained storage requires a quantity even when held; it now retains that prior
quantity while its held state forbids using it as verified eligibility. Lint
cleanup briefly removed pytest fixture imports; explicit fixture exports restore
registration. These were test construction errors, not application defects;
the earlier logs are not represented as passing gates. No invariant was disabled
to obtain a pass.

Context7/ctx7 were unavailable; no tool was installed. Consulted official
[PostgreSQL18 constraint-trigger timing](https://www.postgresql.org/docs/18/sql-createtrigger.html)
and [SQLAlchemy2.0 concurrent-session guidance](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#using-asyncsession-with-concurrent-tasks).
Tests use the existing locked versions, without upgrading them.

## Cleanup, threats and remaining gates

Independent final owned-database query: head0014; originals0, decisions0,
entitlements0; temporary scheduler roles0, barrier functions0, barrier triggers0,
disabled original immutability triggers0, pending clients0. Migrator cash UPDATE
and payment INSERT privileges are false again. Only temporarily missing owner
rights are recorded and revoked; temporary scheduler grants/role are removed.
Immutable cleanup uses the existing guarded privileged test-maintenance pattern
only after behavior finishes. The owned test stack remains available to parent.

T-10-08-01/02: actual once-only cash, owner event publication, immutable originals,
linked holds/successors and authority refusal assertions pass. T-10-08-03: bounded
independent clients/waits with guaranteed cancellation and observed cleanup pass.
T-10-08-SC: no installation/package/image/lock changes. No new application trust
surface, known stub or unresolved implementation defect was found.

No provider, secret/.env, production, B2, timer, installed-tool, push or deployment
operation occurred. Live activation and publication stay deferred. Scheduler,
API/browser integration, final security/recovery gates and actual new owner
UI/native200% acceptance remain later plans, not claimed by this proof.

## Self-Check: PASSED

All3owned test files exist; task commits15013a6/e9f6e6b exist without deletion.
57new/161affected tests, strict service100%, static checks and final cleanup
pass. No canonical planning state or unrelated `.claude/` work was staged.
