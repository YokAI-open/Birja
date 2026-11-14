---
phase: 10-dividend-cash-and-event-history
plan: "03"
subsystem: payments
tags: [dividends, decimal, half-even, corrections, pure-rules]
requires:
  - phase: 10-01
    provides: Inspected0014 exact numeric constraints and outcome/reason vocabulary
provides:
  - Immutable exact DividendTarget and evaluate_dividend_target pure evaluator
  - Literal HALF_EVEN vectors for later actual SQL parity checks
  - Target-minus-cumulative applied corrections and explicit no-cash uncertainty/holds
affects: [10-02, 10-07, 10-08, 10-16]
tech-stack:
  added: []
  patterns: [once-rounded-target, isolated-decimal-context, target-minus-applied]
key-files:
  created:
    - backend/app/services/dividend_rules.py
    - backend/tests/test_dividend_rules.py
  modified: []
key-decisions:
  - Unknown quantity or rate is typed None and returns held_uncertain with null target/proposal, never a zero reversal.
  - Outcome/reason literals match0014; target identities and cumulative applied aggregation remain the caller's retained SQL responsibility.
  - Independent precision64 context covers supported exact products and ignores ambient precision/rounding/traps.
requirements-completed: []
requirements-supported: [DIV-03, DIV-05]
duration: approximately6min
completed: 2026-11-12
---

# Phase 10 Plan 03: Exact Dividend Target Rules Summary

**Pure Decimal targets round once with HALF_EVEN and subtract cumulative applied cash, preserving null uncertainty and unchanged cash for unaffordable corrections.**

## Performance

- Tasks2/2;2implementation/test files plus this summary.
- Recorded implementation interval2026-11-12 19:09:31–19:13:07UTC
  is3m36s, plus initial reads and summary preparation; approximately6minutes total.
- Focused final68tests0.39s;43statements/16branches100% with no partial branches.
- No install, dependency/image/lock change, provider call, production/B2/timer/
  installed-tool change, publication or canonical planning-state edit.

## Accomplishments

- Immutable `DividendTarget` retains desired total, cumulative applied before,
  proposed/applied deltas, cash-after and fixed schema-compatible outcome/reason.
  Inputs remain Decimal; integer, float, string and bool coercion is refused.
- Supports whole nonnegative quantities up to999999999999, exact rates through
  eight places within NUMERIC(20,8), and nonnegative cent cash/cumulative/target
  through999999999999.99. NaN, signaling NaN, infinities, negative/fractional or
  out-of-range snapshots fail with fixed `DividendRuleError.code=numeric_range`.
- A fresh precision64 Decimal context computes quantity×rate without intermediate
  rounding; original rate remains exact, including0.00000001. Product, rounded
  target and resulting cash overflow are independently refused. Explicit
  HALF_EVEN quantizes only the final target to cents. An ambient precision2,
  ROUND_UP, Emax2 and Inexact/Rounded traps cannot alter the result or leak state.
- Correction delta is desired total minus cumulative actual applied cash,
  including original income. A→B→A yields +2.50,+1.00,-1.00 and final original
  total; repeated unchanged targets yield verified_no_change. No identity or
  economic-value dedup is invented here; exact retained target identity is SQL's
  responsibility. No current Holdings or source I/O enters this module.
- Unknown quantity/rate yields held_uncertain/terms_unverified with null desired
  total and proposal, applied0, unchanged cash. An actually verified zero may
  instead reverse an original. Known invalid snapshots still fail under unknown
  terms. Repeated unaffordable proposals preserve cumulative applied and cash;
  exact later affordability can apply the full debit with cash ending at zero.
- Public literal `TARGET_VECTORS` in the test module provides independent amounts
  for subsequent C03 SQL parity: .005→.00, .015→.02, .025→.02,3×.005→.02,
  1.005→1.00,1.015→1.02, maximum whole quantity×.00000001→10000.00,
  large upper-cent boundary and both quantity/rate zero cases. Parent received
  the precise import path and contract; actual SQL parity is not claimed here.

## Task Commits and TDD Gates

1. Task1 RED `2bbe03d`: explicit temporary unsafe HALF_UP behavior seam returns
   .01 for1×.005 where the independent vector requires .00; actual financial
   assertion fails, not an import or collection error.
2. Task1 GREEN `a26e52c`: exact immutable original targets and validators;
   ten literal target tests pass0.20s. The staged implementation explicitly
   refused nonzero cumulative corrections until task2, without guessing cash.
3. Task2 RED `7f0011a`: A→B→A test reaches actual existing staged evaluator and
   fails because a valid correction is refused; ten target tests pass first.
4. Task2 GREEN `b5bb275`: full exact correction/hold semantics;68tests pass0.39s,
   module100% statements and branches. Both temporary stage seams are removed.

## Verification Executed

Commands used existing `uv run --no-sync --no-cache`, with no sync/install.
Tests' automatic guarded fixtures connect only to the parent's existing owned
test stack at127.0.0.1:55432/56379; no test here writes financial rows or mocks a
successful SQL financial effect.

| Gate | Actual result / evidence |
|---|---|
| Task1 behavioral RED |1failed0.20s; `/tmp/birja-phase10-03-red.log` |
| Task1 exact target GREEN |10passed0.20s; `/tmp/birja-phase10-03-task1-green.log` |
| Task2 correction RED |1failed,10passed0.26s; `/tmp/birja-phase10-03-task2-red.log` |
| Final pure behavioral/coverage |68passed0.39s; `/tmp/birja-phase10-03-task2-green.log` |
| Final strict critical coverage |43statements,16branches,0missing/partial,100%; isolated coverage data `/tmp/birja-phase10-03.coverage` |
| Scoped Ruff lint/format |PASS, both implementation/test files |
| Scoped Mypy |PASS, new source module |
| Whitespace/deletion check |git diff --check PASS; no task commit deletes tracked files |

Official Python3.14 documentation was consulted for version-specific Decimal
context, explicit quantization and trap behavior:
[Decimal documentation](https://docs.python.org/3.14/library/decimal.html).
Context7 MCP and local ctx7 CLI were unavailable; no package was installed as a
fallback. Full-wave backend/critical coverage is parent's next serial gate; it
was not run in this executor. Actual SQL authority, retained recovery/TLS,
browser/image gates and owner acceptance are not claimed from pure tests.

## Deviations and Issues

- **[Rule3 — Guarded fixture access]** Initial sandbox test attempt failed before
  the behavior assertion because the project's automatic fixture could not reach
  isolated Redis. Scoped approved escalation reran against the existing owned
  test stack and produced the actual RED. No security guard was bypassed.
- No architectural deviation, new table/API/transport or authentication gate.
- The four-argument C02 function accepts typed None for quantity/rate solely to
  express its required uncertain no-target result. All known arguments retain
  strict Decimal validation. This freezes no additional authority or enum.
- Parent owns canonical STATE/ROADMAP/REQUIREMENTS; none was staged or changed.
  Unrelated `.claude/` and parent's existing STATE edit are preserved.

## Threat Results and Stub Scan

- T-10-03-01 CLOSED for pure numeric boundary: fixed input/range/scale checks,
  independent expected constants, immutable result and matched schema enums.
  Owner/source authority remains C03, as planned; this helper never authorizes
  cash writes or invents verified terms.
- T-10-03-02 CLOSED for this plan: cumulative actual applied value is retained
  distinctly from proposed/applied changes; zero and null are separate, and
  amount equality never stands in for retained target identity.
- T-10-03-03 CLOSED for this plan: fixed constant-time arithmetic, bounded numeric
  ranges, no scans, locks, queries or external I/O. Parent's owned stack stays
  running for subsequent work; no new service/resource was created.
- T-10-03-SC CLOSED: zero dependency installation, lock or image change.
- No new network/auth/file/schema trust boundary outside the planned pure helper.
- No TODO/FIXME, temporary behavior seam or success stub remains. Typed null
  target/proposal is intentional required uncertainty, not unfinished work.

## Self-Check: PASSED

Both owned source/test files exist; all four listed task hashes exist. Final
68tests, strict100% coverage and scoped static checks actually passed. Only the
two owned implementation/test files and this summary are committed by this plan;
canonical state and unrelated work remain parent's responsibility.
