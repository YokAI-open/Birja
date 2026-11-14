---
phase: 10-dividend-cash-and-event-history
plan: "07"
subsystem: dividend-payments
tags: [postgresql, transactions, retained-entitlements, immutable-replay, corrections]
requires:
  - phase: 10-02
    provides: Reviewed scheduler-only C03 apply and no-cash hold SQL authorities
  - phase: 10-03
    provides: Exact target and correction vocabulary with independent amount vectors
  - phase: 10-06
    provides: Passed retained0007–0014 recovery and both restricted TLS prerequisite lanes
provides:
  - Thin transaction-owned process_dividend and record_dividend_hold services
  - Frozen typed original/decision result references with sanitized refusal codes
  - Actual PostgreSQL payment, historical eligibility, correction and rollback regressions
affects: [10-08, 10-09, 10-10, 10-11, 10-15, 10-16]
tech-stack:
  added: []
  patterns: [one-sql-boundary-then-commit, immutable-result, sql-owned-authority, no-financial-retry]
key-files:
  created:
    - backend/app/services/dividends.py
    - backend/tests/test_dividend_payments.py
    - backend/tests/test_dividend_corrections.py
  modified: []
key-decisions:
  - Return C03a immutable references directly; no result lookup or authority pre-gating follows the final SQL guard.
  - Reject an already active session transaction rather than committing unrelated caller work.
  - Unknown terms use only the separate no-cash hold function and require an existing original.
requirements-completed: []
requirements-supported: [DIV-03, DIV-04, DIV-05]
duration: approximately15min
completed: 2026-11-13
---

# Phase 10 Plan 07: Retained Dividend Transaction Service Summary

**One owned transaction invokes reviewed SQL for once-only originals, immutable corrections and separate unknown-term holds, returning frozen references without a post-guard business query.**

## Accomplishments

- `process_dividend` accepts only event/entitlement IDs and their expected
  fingerprints. `record_dividend_hold` accepts only original payment ID and
  current revision fingerprint. Both delegate all owner, authority, date, money,
  historical eligibility, locking and replay decisions to the proven C03 functions.
  No extra cash grants, Python financial arithmetic or automatic retry is added.
- Strict positive BIGINT IDs reject bool/string/coercion/overflow; fingerprints
  must be exactly64 lowercase hexadecimal characters. Work is constant-size.
  An active caller transaction is refused without discarding caller work.
- Frozen `DividendResult(payment_id,decision_id,outcome)` preserves `original`
  with null decision ID and existing four decision outcomes. Buffered SQL output
  is converted without another query; transaction commit alone follows. An actual
  SQL statement trace proves function→savepoint release with no business SQL in
  between. Production uses the same transaction context with a regular commit.
- Actual database failures map to fixed `DividendRefused.code` values:
  `invalid_identity`, `transaction_active`, `authority_unavailable`,
  `numeric_range`, `financial_unavailable`. Public exception text is fixed and
  raw SQL context is suppressed. Transaction context rolls back errors and
  cancellation; cancellation injected after a genuine SQL payment, before commit,
  leaves cash and original rows unchanged. No successful financial effect is mocked.
- Original credits/replays preserve stored starting cash, original saved symbol/
  name and all original bytes after rename, monitor uncertainty, corrections and
  rights loss. Successful correction replay also survives authority loss. The
  existing Portfolio service reads credited Account.cash once, without summing
  income separately or allocating another starting grant.
- Real calendar-backed `derive_dividend_entitlements` reconstructs quantity from
  the ownership journal. A departed seller retains its earlier cutoff entitlement;
  a revised next-session cutoff reconstructs zero after that sale and authorizes
  the exact verified reversal. Current Holdings only reconcile the journal and
  never supply the eligibility quantity. The ordinary revision's split-specific
  verified_cutoff remains null. No fixed09:30 fallback is introduced.
- Existing retained predecessor-shaped entitlements are consumed directly.
  Actual pre0014 migration survival and exact retained restore were proven by
  prerequisites01/05/06; this service test does not claim a new migration or
  restore exercise. Its producer/service assertions prove unchanged consumer
  semantics against those retained interfaces.
- New York payable day is checked using genuine database wall time, without
  faking clock or requiring the market to be open. Tomorrow refuses; today pays.
  A newer held snapshot blocks old eligible fallback. Verified zero ownership
  with positive declared rate produces one valid zero original; declared zero
  rate goes through the actual producer and yields held/unverified eligibility.
- A→B→A uses distinct revision/entitlement identities, with exact +.50,-.50 and
  no-change successors. An unaffordable-.80 target remains held with applied0;
  later cash.80 permits a separate linked applied successor once. Paid originals
  followed by uncertain/cancelled revisions retain null target/proposal and zero
  applied cash; stable holds deduplicate without a current eligible snapshot.
  Existing reviewed reconciliation then yields one linked+.50 successor.
  Uncertainty before an original cannot fabricate an anchor or Dividend event.

## Task Commits and TDD Gates

1. Task1 RED `1bcf8f2`: callable staged service did not publish a due retained
   original; real Account.cash100 failed the independent expected101 assertion.
   No import or collection failure substituted for behavior.
2. Task1 GREEN `848c208`: thin original transaction/replay service;2actual
   PostgreSQL cases pass1.20s.
3. Task2 RED `8e21769`: the callable staged hold path safely refused a paid
   anchor's uncertain successor; actual expected held publication was absent.
4. Task2 GREEN `325d970`: separate hold transaction and complete real-state
   payment/correction/rollback coverage. Both temporary stage seams are removed.

All four hashes exist locally; no task commit deletes tracked files. Only the
three owned source/test files are included in these task commits.

## Verification Executed

Existing locked `uv run --no-sync --no-cache` only; no dependency sync/install.
Recreated solely the owned `docker-compose.test.yml` project `birja-test`,
loopback55432/56379 with test-only credentials. Its guarded conftest migrator
helper provisioned canonical test owner before migrating normally to0014.

| Gate | Actual result / evidence |
|---|---|
| Task1 behavioral RED |1failed/1deselected2.18s; `/tmp/birja-phase10-07-task1-red.log` |
| Task1 GREEN |2passed1.20s; `/tmp/birja-phase10-07-task1-green.log` |
| Task2 behavioral RED |1failed/2deselected1.56s; `/tmp/birja-phase10-07-task2-red.log` |
| Final new service cases |46passed4.19s,4existing pandas deprecation warnings; `/tmp/birja-phase10-07-final.log` |
| Exact critical coverage |41statements/6branches,0missing/partial,100%; `/tmp/birja-phase10-07.coverage` |
| Existing authority/rules/action regressions |198passed18.25s,8existing pandas warnings; `/tmp/birja-phase10-07-affected.log` |
| Scoped Ruff / format |PASS all3owned implementation/test files |
| Scoped Mypy |PASS `app/services/dividends.py` |
| Owned test DB handoff |0014; originals0,decisions0,entitlements0 after rollback fixture cleanup |
| Whitespace / stub / deletion scan |PASS; no staged seam, TODO/FIXME or tracked deletion |

The complete new suite includes the plan's due/correction/original selector;
the full files were run, a superset of that focused selector. Full financial-wave
backend/critical coverage remains the parent's serial gate after07/10. No new
recovery, TLS, browser, image, API or worker pass is claimed by these service tests.

Context7 MCP and ctx7 CLI were unavailable; no package was installed. Consulted
official [SQLAlchemy2.0 async transaction documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#sqlalchemy.ext.asyncio.AsyncSession.begin)
and [external-transaction test integration](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites).
The actual tests use the existing installed locked version, not an upgrade.

## Deviations and Observed Fixture Corrections

- Initial zero-rate test manually forced inconsistent `supported_dividend` plus
  eligible retained terms. C03 accepts retained verified classification; that
  forgery did not demonstrate a producer/runtime defect. Parent confirmed the
  intended boundary. Replaced it with actual retained producer derivation, which
  holds zero-rate terms and causes service refusal without cash/anchor. No Python
  pre-gate, SQL function, migration or recovery authority was changed.
- The historical producer validates the complete current journal: synthetic
  Holdings must reconcile with its actual tail. Added corresponding fixture rows
  without consulting them as cutoff quantity. A synthetic historical stock sale
  also needed its actual stock receipt and identical movement recorded/economic
  timestamps; all existing deferred integrity and ownership checks remain enabled.
- PostgreSQL overloaded date/interval bind inference required explicit integer
  and timestamptz fixture casts. The first cancellation injection inside driver
  event handling invalidated the fixture connection; replaced it with cancellation
  immediately after the real awaited SQL returns, testing transaction rollback
  without simulating the financial effect. Final tests and static gates pass.
- No architecture deviation, package/authentication gate or unrelated fix.
  Parent owns STATE/ROADMAP/REQUIREMENTS updates. No whole requirement is marked
  complete by this bounded service plan.

## Threat Results and Remaining Gates

- T-10-07-01 CLOSED for this consumer: no new financial authority; real derived
  targets, immutable replay, lost-rights replay, current hold refusals and exact
  correction/rollback effects are exercised. Restricted source/TLS denials remain
  prerequisites02/05/06 and are unchanged.
- T-10-07-02 CLOSED: frozen references preserve original/decision lineage;
  no caller owner/amount, raw provider text, secret or personal data is returned.
- T-10-07-03 CLOSED: bounded strict work, one owner transaction, no scans,
  provider I/O, financial retry or later business query. Deep independent-client
  contention and postwait schedules remain Plan08's explicit responsibility.
- T-10-07-SC CLOSED: zero package/image/lock changes. No new endpoint, auth path,
  file operation, schema or trust boundary outside the planned service surface.
- No known stubs remain. Null uncertain target/terms are required truthfulness,
  not placeholders. Provider activation, production, B2/timer/tooling, publication
  and final owner UI/zoom acceptance remain deferred under existing scope.
- The owned empty0014 test stack stays running for the parent's next serial
  consumer. No other Docker project was touched; unrelated `.claude/` is preserved.

## Self-Check: PASSED

All3owned implementation/test files and this summary exist. Four task hashes
exist; no task deletion. Actual46new/198affected tests, strict100%critical coverage,
scoped static checks and empty0014 accounting handoff passed. Canonical project
state and unrelated work were not staged or changed by this executor.
