---
phase: 09-whole-share-trading-and-combined-portfolio
plan: "04"
subsystem: database
tags: [recovery, restic, postgresql, tls, immutable-receipts]
requires:
  - phase: 09-03
    provides: additive0013 facts, status, invoker integrity and final execution guard
provides:
  - Exact revision-dispatched0013 recovery preserving0007–0012 contracts
  - Independently authenticated function bodies, owners, triggers and narrow ACLs
  - Two same-stock receipts with real consumable source and restored ownership history
  - Retained encrypted archive and populated/fresh restricted verified-TLS proof
affects: [09-05, 09-06, 09-08, 09-14]
tech-stack:
  added: []
  patterns: [unique receipt hash ordering, quarantined clone grants, real ownership consumption]
key-files:
  created: [deploy/tests/stock-execution-fixture.py]
  modified:
    - deploy/backup-snapshot.py
    - deploy/verify-restore.py
    - deploy/backup-manifest.sql
    - deploy/tests/test-stock-recovery-contracts.py
    - deploy/tests/test-restore-safety.sh
    - deploy/tests/ops-fixtures.py
    - deploy/tests/test-db-operations.sh
key-decisions:
  - Authenticate reviewed invoker definitions independently before fixed clone ACL reconstruction.
  - Keep old financial tables quarantined; privileged fixture readers do not expand app grants.
  - Require actual ownership-service acceptance as well as exact saved bytes.
requirements-completed: []
requirements-supported: [STKTR-03, STKTR-05, PORT-06, MKT-02]
duration: multi-session
completed: 2026-11-12
---

# Plan09-04: Exact execution recovery and restricted TLS

**One retained encrypted recovery archive preserves exact0007–0013 data and
authenticates0013 authority, with usable stock ownership history and narrow
fresh/upgraded runtime permissions over verified TLS.**

## Task commits

1. Task1 RED `51915b3`; implementation `8cfd6b9`: revision dispatch and fixed
   independent execution authority contracts.
2. Review regression `5a59aa0`; fix `603e43a`: canonical receipt rows order by
   unique trade_id rather than nonunique stock identity.
3. Task2 `3a06a32`: retained recovery, ten corruption controls, role and TLS
   consumers, independent two-fill fixture and clone-only identity probes.
4. Ownership regression `e17ef25`; fix `e8d3bb2`: real service rejects the
   synthetic missing baseline; complete baseline and contiguous tail now pass.

Task REDs were behavioral: unsupported recovery and an actual role-driver
successor-head assertion, not missing imports. Review REDs detected wrong generated row ordering and an
actual `OwnershipHeld: missing_baseline` from the existing service. Actual
execution service replay remains Plan06/14 work.

## Verification

Final canonical command: `PYTHONUNBUFFERED=1 bash deploy/tests/test-db-operations.sh --all`.
Final log: `/tmp/birja-phase09-04-all-consistent.log`. All resources are owned
isolated fixtures, with no dev/production database, provider or B2 connection.

| Gate | Final result | Measured time |
| --- | --- | --- |
| Offline recovery contracts |10passed;3 explicit real-SQL-only skips |0.044s |
| Restore extraction/checksum safety |6passed |1.402s |
| Retained0007–0013 encrypted recovery |PASS, exact rows/schema/identities and unchanged source |395.688s |
| Restricted populated/fresh roles |PASS,63 denied operations;12 input/lock refusals |181.408s |
| Populated0012→0013 verified TLS |PASS, no post-upgrade grant repair |126.301s |
| Fresh0013 verified TLS |PASS; all authority/ownership consumers |122.868s |
| Python compile, embedded execution, shell syntax, whitespace |PASS |<1s static checks |

Actual restore checks include nine accounting, seventeen identity and thirteen
operator-authority corruption cases, plus ten new execution data/owner/ACL/
function/trigger cases. Source and restored receipt/history checks reject a
second duplicate effect without consuming identity counters. Both TLS lanes
exercise the actual app execution guard, fixed permissions and real ownership
consistency, and reject bad CA, hostname and plaintext connections.

The final archive is152,197,120bytes, SHA256
`08131798ce5d3893bde0da4cf566d46de5e77654f47b87dbd3f912898e14278c`.
Every0007–0013 roundtrip uses these same installed retained bytes with feature
checkout access denied to the recovery launchers. No per-revision rebuild.
The verified restic0.19.1 test tool remains the previously approved version.

Frozen0013 schema SHA256:
`b90ddfa6cb8c33670f5341b8bc45ec4b71d5c7bc63172d041a4c2b12575e8196`.
Exact table inventory24; identity sequences17. New source helper SHA256:
`7e58339142a098acf98563b006586eb218e4e27d95808ecd6d96eb304116d161`.
Producer `844a2497dd8ebeb98b93a2450a1a5019b1986e1b047ec8ba42daf5792294c2da`;
verifier `94cde8b080a5baaf37918ff0bc73b7c936098b2db4f8a4e27c3c3e1e36616ab5`.

## Deviations and review

Added one independent helper alongside the existing operations fixture to keep
synthetic SQL separate from application test fixtures. Fixed discovered unique
hash ordering and synthetic baseline/identity-probe compatibility within scope.
Two attempted agents had no filesystem/shell tools; execution and a separate
review pass continued inline under AGENTS/GSD fallback. This is not independent
review. See09-04-REVIEW.md for findings, fixes and provenance.

Earlier rehearsals exposed fixture cast, SSL detection, admission conflict and
quarantine assumptions; they are not counted as passing final gates. The first
corrected full run passed before the stronger ownership-consumption check was
added. The final canonical run above uses the final corrected fixture.

No backend application change after the prior1793-test/99.83% full regression
proof; all31 critical modules remain covered by that recorded100% result.
No package/image dependency or production host-tool change was needed.
New facts/status/function grants are narrow; existing financial grants stay fixed.

## Next obligations

Continue09-05 status/eligibility, then09-06 execution and09-07 adversarial waits.
Plan14 must replace synthetic new-fill SQL with the actual stock execution
service through retained recovery and both restricted TLS lanes. SQL duplicate
rejection here is not evidence of API/service idempotency or financial races.
Whole requirements remain pending end-to-end verification and new UI acceptance.
Phase7 quote/live evidence and Phase8 action activation remain owner-deferred.
No provider, production, B2, timer, push, merge or deployment change occurred.

## Self-Check

PASSED: all eight implementation/test artifacts exist; all seven cited source/test commits resolve; final canonical process exited0 with both TLS lanes and cleanup complete.
