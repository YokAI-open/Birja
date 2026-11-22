---
phase: 15-verify-exact-portfolio-recovery-and-acceptance
plan: "02"
reviewed: 2026-11-22
depth: standard
diff_base: 022aa7e
diff_head: 1109d25
files_reviewed: 6
files_reviewed_list:
  - deploy/backup-snapshot.py
  - deploy/verify-restore.py
  - deploy/tests/fixtures/portfolio-recovery-0023.json
  - deploy/tests/portfolio-closure-recovery-fixture.py
  - deploy/tests/portfolio-smoke.py
  - deploy/tests/test-portfolio-management-recovery.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase15 Plan02 — Independent Code Review

## Narrative Findings (AI reviewer)

**Zero blockers and zero warnings** in the bounded six-file diff
`022aa7e..1109d25`. No source changes, tests, services or Docker operations
were performed by this reviewer.

The Active fixture now has a genuine original crypto fill with key103. Its
declared economics match the existing fee-inclusive100USD order:9860.25cash,
0.00995012BTC and100USD basis after its existing dividend. The recorded real
writer result reports actual PostgreSQL and owned cleanup; the checked-in
projection retains31tables,24tails, five roots and four closed roots. This is
inspection of recorded evidence, not a new database execution.

`replay-restored` requires the restored database and authenticated immutable
before-snapshot. Its generated program compares the complete restored state,
including exact sequence tails, before invoking any business retry. Cold wiring
in`portfolio-smoke.py:1062` follows the existing successful restored comparison
and applies only to current0023. Non-cold/historical paths do not gain a restored
replay claim. The transport requires the generated retry report before passing
it back to the fixture parser.

Actual restricted app/scheduler service signatures match their callers.
Creation retains the original key and canonical payload. The active trade retry
requires`new=False` and compares every returned fill field with the original.
Dividend replay uses the retained payment's fingerprints; the existing SQL
original-payment branch returns that original before later revision processing.
Closed creation/fill/dividend calls use normal services and require their actual
unavailable-target exceptions. No financial result or SQL authority is replaced.

The helper requires unchanged full table contents and active/zero-user lists;
this includes grants, fills, payments, decisions, frozen causal records and
sibling finances. Post-retry sequence consumption is recorded separately and
cannot move backward; no sequence is reset. Exact tails remain mandatory before
the retries.

The finite fixture writer refuses preexisting owned resources, uses only the
explicit`birja-p15-02` test project with`/dev/null` environment, and performs owned
cleanup in`finally`. Historical default behavior is preserved. Producer and
consumer diffs change only their authorized current-fixture source entry;
independent file hashing confirms
`eb8417603d32996142d812d55f3416079d6119b1cc0c219be8295557b644fc66`.
Historical, application, SQL and ACL pins remain unchanged.

## Verification Limits

The provided12/11Task1 and14/25Task2 contract results are recorded executor
evidence; this static review did not rerun them. Generated-program compilation
and wiring assertions are not actual restored financial execution. That genuine
encrypted cold/replay proof remains Plan03. The preserved R1 source-pin refusal
and existing whole-run failures are not relabelled as passes. No broader audit,
new hardening requirement, hosted CI, publication or production result is claimed.
