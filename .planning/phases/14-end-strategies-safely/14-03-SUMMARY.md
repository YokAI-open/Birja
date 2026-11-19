---
phase: 14-end-strategies-safely
plan: "03"
subsystem: financial-integrity
tags: [postgresql, closure, transactions, stock-ownership, clocks]
requires:
  - phase: 14-01
    provides: Immutable lifecycle schema and verified historical provenance
  - phase: 14-02
    provides: Derived atomic SQL closure and permanent original outcomes
provides:
  - Complete every-instrument integrity proof before closure commit or acknowledgement
  - Transaction-bound closure context with actual granted advisory-lock verification
  - Successor SQL and service terminal-clock fences with normal sibling continuation
affects: [14-04, 14-07, 14-09, recovery, critical-coverage]
tech-stack:
  added: []
  patterns:
    - Private locked read-only verifier core shared without relaxing the financial single-instrument wrapper
    - Actual PostgreSQL lock evidence and immutable original capture before same-transaction proof
key-files:
  created:
    - backend/app/services/portfolio_closure.py
    - backend/tests/test_portfolio_closure_stocks.py
    - backend/tests/test_portfolio_closure_clocks.py
  modified:
    - backend/app/services/stock_ownership.py
    - backend/app/services/corporate_actions.py
    - backend/alembic/sql/0023_portfolio_closure.sql
    - backend/alembic/versions/0023_portfolio_closure_authority.py
    - backend/tests/test_migrations.py
key-decisions:
  - Original closed acknowledgements require the same complete proof as first closure; terminal confirmation_changed commits only its immutable refusal outcome.
  - A private transaction-bound service context and actual pg_locks evidence authorize the closure verifier; no caller boolean or stale receipt does.
  - New stock movement/application timestamps must strictly follow every prior instrument terminal boundary under an already-held gate.
requirements-completed: []
requirements-progress: [PMGT-04, PFIN-05, PFIN-06]
duration: 25min measured RED-commit-to-cleanup interval
completed: 2026-11-19
---

# Phase 14 Plan 03: Complete Closure Proof and Terminal Clock Fences

**A closure is committed or acknowledged only after complete same-transaction
stock/lifecycle verification; later global activity cannot be backdated into a
frozen portfolio's boundary.**

## Task commits and measured evidence

| Task | RED | GREEN | Actual result |
|---|---|---|---|
|1 — complete closure service/proof|3cebf28|564759b|18 combined proof/backfill cases passed124.74s|
|2 — strict global terminal clocks|7e57481|1ad7ce5|53 combined cases passed352.85s; subsequent test-only strengthening passed2cases18.95s|

The measured interval is09:10:19UTC (first RED commit) through09:35:40UTC
(owned-resource cleanup receipt). Initial reading/preparation predates this
interval and is not assigned an invented start time. Both tasks are complete;
no whole requirement or Phase14 completion is claimed.

Raw receipts/logs: `/tmp/birja-phase14-plan03/`, including `receipt.json`.
Source commit: `1ad7ce5fcf4ef432d4f14b620db9257b2be72038`.
Only test coverage was strengthened after the53-case integration run: the
corrupt-open-history case now independently damages the first or second stock.
Both resulting variants passed18.95s; runtime and SQL bytes were unchanged.
This is task-level affected verification, not whole-phase frozen-source CI.

## Implemented behavior

- The original `assert_ownership_consistent` wrapper still invokes the unchanged
  one-instrument financial gate. Its complete validation body moved into a
  private read-only core; normal financial pending-fill/application exceptions
  remain scoped to that original wrapper. No guard marker is cleared or forged.
- `ClosureIntent` and `ClosureResult` provide the internal service contract.
  `close_portfolio(db, original)` invokes the exact bound SQL authority, captures
  a private originating transaction context, validates complete universal
  lifecycle/original intent/stock-boundary membership, confirms actual granted
  advisory locks on this backend/database, and checks every instrument before
  commit. The context is removed after success, error or retry; copied context
  cannot authorize a different transaction. Crypto/empty roots still require
  coherent universal lifecycle evidence.
- First closure and owned already-closed acknowledgements use the same full
  proof. Corrupt sold-out history, a defective second stock baseline, or a
  corrupted closed replay cannot be committed/acknowledged. Proof failure rolls
  back all SQL outcome/lifecycle/per-stock records and account closure together.
  An immutable name-change refusal commits its nonfinancial outcome.40001
  discards the complete attempt and rediscovers instruments, at most3attempts;
  the actual observed first-buy race invoked SQL exactly twice and then passed.
- `assert_stock_terminal_clock` inspects an already-held instrument gate and
  rejects invalid/non-UTC/equal/backward service clocks. It does not acquire
  a gate after root locks or fabricate a later timestamp. Movement append and
  split application creation call it at their authoritative timestamp seams.
- New0023 `check_stock_terminal_clock()` is trusted-owner SECURITY DEFINER,
  fixed safe search_path, no public/app/scheduler direct EXECUTE. Its two BEFORE
  INSERT triggers on movements/applications require an already-held matching
  gate and a finite timestamp strictly beyond the latest instrument closure.
  Only the still-under-development0023 checksum changed:
  `1da9076cc99e36c2eb264dcf0801e3752d0329c5e7f54fd4a358e7ea8c3c8949`.
- Normal active sibling fill/split processing resumes after equal/backward
  refusal. Real split processing assembles both active owners under the pending
  application exception, validates complete history/digests, preserves the
  frozen sold-out root, and replays once. An actual queued closer waits on an
  instrument gate while another owner appends, then records global tail5 and
  a strictly later closure timestamp after release. No sleep substitutes for
  an observed PostgreSQL blocking PID relationship.

## Actual verification

| Check | Actual result / receipt |
|---|---|
|Task1 RED|Missing service,9.73s; `task1-red.log`|
|Initial same-transaction proof|7passed57.71s; `task1-final.log`|
|Observed first-buy service retry|1passed6.71s; `task1-race.log`|
|Complete proof + pre-backfill compatibility|18passed124.74s; `task1-retained.log`|
|Task2 RED|Same-clock movement wrongly accepted,10.38s; `task2-red.log`|
|Equal/backward SQL movement/application fences|4passed37.82s; `task2-green.log`|
|Service clock refusal then real sibling fill/split continuation|4passed38.70s; `task2-service2.log`|
|Observed queued instrument/clock boundary|1passed10.07s; `task2-queued.log`|
|Combined proof/clocks + all Plan01/02 regressions|53passed352.85s; `final-combined.log`|
|Final first/second instrument corruption strengthening|2passed18.95s; `second-instrument.log`|
|Scoped Ruff/format|All7touched Python paths pass;7already formatted|
|Scoped mypy|All3service modules pass|
|Historical migration/SQL guard|0015–0022 migrations and existing0017/0020 SQL assets unchanged from0e8e408|
|Owned-resource cleanup|birja-p14-03 containers/networks/volumes all empty|

The combined run exercised all17migration cases,18SQL authority cases,8service
cases and10clock cases serially. Final test-only parameterization adds explicit
second-member coverage without changing implementation. Current app startup,
all-backend critical coverage, image/security scanning, exact recovery, browser
and owner/native200 outcomes remain later execution gates.

## Deviations from Plan

1. **[Rule3 — prerequisite] Exact successor function inventory extension.**
   Added only `check_stock_terminal_clock()` to the0023 migration-only test
   inventory, so repeat provisioning accepts this exact new guard rather than
   failing before fixtures. Old inventories and0021/22 profiles are unchanged;
   no wildcard, autouse skip, runtime admission or privilege broadening. The
   parent explicitly authorized this narrow prerequisite adjustment.
2. **[Rule1 — implementation bug] Existing `utc()` returns a boolean.**
   A service regression caught its mistaken use as a converter; fixed to test
   UTC validity and compare the original aware datetime. Both equal/backward
   refusal and ordinary continuation pass. The initial failed log is retained.
3. **Test-fixture correction.** Changing proceeds of a fully sold position is
   not a cost-basis inconsistency. The initial corruption test was corrected to
   change fill quantity, then strengthened with a second-instrument baseline
   defect that only the full verifier catches. No invariant was weakened.

Existing locked tools were reused. After uv's default cache was read-only,
later uv commands used an isolated `/tmp/birja-phase14-plan03/uv-cache` with
`--no-sync --offline`; no dependency installation or lockfile change occurred.

## Handoff and remaining gates

- Plan04 must include exact `check_stock_terminal_clock()` ownership/ACL/body
  and both `stock_terminal_clock` triggers in independent SQL/Python catalogue
  admission and fresh/upgraded parity. The31table/24sequence count is unchanged.
 0021/22 remain migration-only and normal runtime admission was not modified.
- Plan07 should consume `ClosureIntent`/`ClosureResult` and the service's fixed
  outcomes; it must not commit SQL directly or infer rollback from response loss.
  Public owner/CSRF/rate-limit/private-error transport remains unimplemented.
- Retained0021 pre-backfill verification on the SAME migration connection still
  passes. Preserve it and the original one-instrument financial wrapper during
  later edits. No source/profile from qualified0020 or older was repinned.
- Add the new closure service to the100%critical gate in the planned CI work;
  this summary does not claim whole-suite coverage, images or recovery passed.
- Parent owns STATE/ROADMAP and requirement dispositions. Keep all seven whole
  requirements pending until integrated proof and phase-goal verification.

## Known Stubs and Threat Surface

No goal-blocking stub or unplanned external/auth/file surface was introduced.
Private lifecycle proof, successor triggers and service entrypoints implement
the declared threat model. No new package/provider operation, live activation,
publication or production change occurred. Issue35 and prior archives remain
unchanged; unrelated `.claude/` is preserved.

## Self-Check: PASSED

All8source/test artifacts exist; four task commits are present. Raw receipt
records source/log hashes and empty owned cleanup. Scoped checks and actual
results above are recorded without converting task progress into whole feature
completion. Ready for independent Plan03 review before Plan04.
