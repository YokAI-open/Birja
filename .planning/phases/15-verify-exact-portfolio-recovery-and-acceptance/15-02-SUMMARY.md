---
phase: 15-verify-exact-portfolio-recovery-and-acceptance
plan: "02"
subsystem: testing
tags: [recovery, portfolios, original-retries, financial-oracle]
requires:
  - phase: 15-01
    provides: Authenticated installed verifier and finite Phase15 recovery selection
provides:
  - Actual active original crypto fill in the current independent fixture
  - Exclusive finite current-fixture PostgreSQL generation
  - Restored-only original creation/fill/dividend service checks after exact comparison
affects: [15-03, 15-04]
tech-stack:
  added: []
  patterns: [immutable pre-replay oracle, actual restricted service retries]
key-files:
  created:
    - .planning/phases/15-verify-exact-portfolio-recovery-and-acceptance/15-02-REVIEW.md
  modified:
    - deploy/tests/portfolio-closure-recovery-fixture.py
    - deploy/tests/fixtures/portfolio-recovery-0023.json
    - deploy/tests/test-portfolio-management-recovery.py
    - deploy/tests/portfolio-smoke.py
    - deploy/backup-snapshot.py
    - deploy/verify-restore.py
key-decisions:
  - Compare all31 tables and24 identity tails before actual original requests; retain legitimate later sequence consumption separately.
  - Bind only the changed current fixture source in both producer and consumer; historical/application/SQL/ACL pins remain unchanged.
requirements-completed: []
requirements-addressed: [PSAFE-04, PSAFE-06]
completed: 2026-11-22
---

# Phase15 Plan02: Actual Original-Request Recovery Assertions

**Both tasks complete.** The current fixture now has a genuine original active
fill; the supported encrypted cold path invokes restored-only creation, fill
and paid-dividend retry checks after the exact original snapshot comparison.
Actual encrypted replay execution remains Plan03, not a result claimed here.

| Task | Commit | Actual verification |
|---|---|---|
|1 Active fill and independent oracle|8dd790b|Real exclusive PostgreSQL writer passes;12 fixture contracts5.756s and11 management contracts16.138s pass|
|2 Restored-only actual-service retry wiring|1109d25|14 management contracts16.286s and25 smoke/image contracts6.295s pass; generated role program compiles, syntax/diff checks pass|

## Fixture and Behavior

The real `--write-current-fixture` lane uses only `birja-p15-02`, test Compose
with `/dev/null` environment selection, and an exclusive temporary snapshot.
It refuses existing owned resources and cleans its project on success/failure.
The producer reports `actual_postgres=true`, `encrypted_restore=false` and
`owned_resources_clean=true`. The source-owned JSON contains31tables/24tails,
five roots/four closed roots/two identities. Active has real original key103,
cash9860.25000000, BTCquantity0.00995012 and cost basis100.00000000. Those
economic expectations are declared independently, not copied from observed rows.

`replay-restored` requires `birja_restore_test` and the private before-snapshot
SHA. The generated program compares the complete restored projection before
calling real restricted app/scheduler services. It checks the original active
creation identity, all original fill fields and retained paid-dividend payment
identity/fingerprints; normal closed-target service calls must refuse. Exact
all-table equality and active/zero-user lists protect frozen and sibling state.
Pre-replay sequences are exact; any legitimate later consumption is recorded
without resetting sequences. The success marker follows actual assertions only.

Smoke dispatch is current0023/cold-only, inside the installed consumer lifetime,
after the original encrypted-restore comparison. Historical/non-cold paths do
not invoke or claim restored original-request checks. Offline program/dispatch
contracts are not financial replay or encrypted restore evidence.

## Review, Evidence and Cleanup

Independent bounded six-file review022aa7e..1109d25 is clean:0blockers/0warnings,
recorded in15-02-REVIEW.md. It inspects service signatures, snapshot ordering,
boundaries and exact source associations; it runs no tests/services itself.

Private receipts: `/tmp/birja-phase15-plan02/` contains `generate-r2.json/log`,
Task1/2 contract logs, preserved-before/after records and `final-integrity.json`.
All owned container/network/volume inventories are empty. The Phase13/14 archive
and Phase14 before-snapshot SHA/inodes remain unchanged. Unrelated `.claude/`
and existing services/data are untouched. No application, SQL/schema/ACL,
dependency/image version, UI, provider, production or publication change.

## Deviations and Failed History

**[Rule2 — Current source association]** The first real writer attempt reached
the current fixture source guard and refused its old pinned bytes; no success
is inferred. Its logs remain `generate-r1-failed.*`, with owned cleanup complete.
Parent authorization added only this current fixture entry in the two existing
`CLOSURE_SOURCE_SHA256` dictionaries to scope. Task1's measured fixture hash was
`76bc57fae72fc1b6139f513b568194a0234b5958a7ebc7b1a7c7cadc9b690851`;
the final Task2 fixture hash in both maps is
`eb8417603d32996142d812d55f3416079d6119b1cc0c219be8295557b644fc66`.
Both maps match actual source; every other pin remains unchanged. No automatic
runtime hash adoption or historical repin was introduced. R2 alone is the
successful fixture-generation result.

Two small test-only corrections are retained in task history: a cleanup argv
slice length and selecting the actual cold AST block rather than its earlier
precondition block. Both affected tests pass; neither changed product behavior.

## Next and Self-Check: PASSED

Both implementation commits, the six modified source/fixture paths and independent
review exist; recorded contract commands exit0, Python syntax and diff checks
pass, prior identities match and owned cleanup is empty. No blocking stub or new
unregistered product surface exists. Root retains global state/requirements.
Proceed to15-03's one matching current encrypted proof; whole requirements and
hosted CI remain pending. Work stays local.
