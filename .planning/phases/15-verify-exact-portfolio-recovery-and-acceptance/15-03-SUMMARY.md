---
phase: 15-verify-exact-portfolio-recovery-and-acceptance
plan: "03"
subsystem: testing
tags: [recovery, original-retries, evidence-reuse, images]
requires:
  - phase: 15-01
    provides: Installed-consumer and finite supported campaign tooling
  - phase: 15-02
    provides: Genuine active fill and restored original-request assertions
provides:
  - Actual encrypted current0023 cold restore and original-request replay
  - Source-bound inherited coverage and exact current image qualification
  - Preserved failed-history provenance and empty owned resources
affects: [15-04, phase-goal-verification]
tech-stack:
  added: []
  patterns: [existing scoped effective-role session adapter, source-bound component reuse]
key-files:
  created:
    - .planning/phases/15-verify-exact-portfolio-recovery-and-acceptance/15-EVIDENCE-REUSE.md
    - .planning/phases/15-verify-exact-portfolio-recovery-and-acceptance/15-REVIEW.md
    - .planning/phases/15-verify-exact-portfolio-recovery-and-acceptance/15-RECOVERY-PROOF.md
    - .planning/phases/15-verify-exact-portfolio-recovery-and-acceptance/15-LOCAL-VERIFICATION.md
  modified:
    - deploy/tests/test-db-config.sh
    - deploy/tests/test-portfolio-validation-contracts.py
    - deploy/tests/portfolio-smoke.py
    - deploy/tests/portfolio-closure-recovery-fixture.py
    - deploy/tests/test-portfolio-management-recovery.py
    - deploy/backup-snapshot.py
    - deploy/verify-restore.py
key-decisions:
  - Preserve NOLOGIN restored authority; reuse the existing owned-login SET ROLE session adapter for actual restricted service calls.
  - Observe verified TLS before role attenuation on the same bound connection; keep role and financial assertions unchanged.
  - Current-only success remains distinct from full seven-stage and hosted CI qualification.
requirements-completed: []
requirements-addressed: [PSAFE-04, PSAFE-05, PSAFE-06]
completed: 2026-11-22
---

# Phase15 Plan03: Current Restore and Original-Request Proof

**Both tasks complete.** R5actually restores the source-destroyed encrypted
current0023 fixture and replays the original active creation/fill/payment without
another effect; closed, sibling and zero-active state remains unchanged.

| Task | Commits | Actual result |
|---|---|---|
|1 Reviewed source-bound reuse|7206ddc; later repair associations|277backend/155frontend/314browser/139authority/10policy inputs unchanged;28security/sixrecovery logs and365render inputs hash-verified; explicit8765migrated baseline|
|2 Actual current proof and images|25872e4,6436d35,c78e96e,8fc0650,6d7ee7f,c08e9de|R5passed135.998s;5strict scans passed41.220s; source/image/archive guards and empty owned cleanup verified|

Actual proof source`6d7ee7fde201c085d66568d89c036cd2b2c9e86f`;
receipt`/tmp/birja-phase15-campaign-recovery-current-r5`. Preflight139tests pass.
The real retry result retains portfolio3/fill4/payment2, three closed refusals,
no sequence changes, unchanged complete financial tables/lists and exact
before-replay31table/24tail comparison. Mode`owned-login-set-role` is recorded
truthfully; direct runtime-login TLS coverage remains inherited.

Canonical archive`/tmp/birja-phase15-proof/recovery.tar.gz`, SHA256
`bbbec1af156b594f5093ecef8badf918f8b0a7e039dfdb3e486fb8b58823f47a`,
inode943204/device64512,244357120bytes. Current cold authority equals inherited
upgraded/fresh/rollback catalogue59aeeee…a66e/objectACL71896f…f748/defaults4f53cd…b945.
New exact runtime`sha256:dacbd2c31e69610d179638999281bd91b5d3d1d0ad897473371ab1eda0f961b7`
and four measured unchanged image IDs all scan HIGH0/CRITICAL0,0accepted findings.

## Deviations and Bounded Repairs

- R1preflight refused before DB/archive work because its exact Phase15 project
  was missing from the existing finite test validator. Parent-authorized one
  entry plus actual selection/allowlist contract;43tests pass10.233s.
- R2/R3 exposed missing runtime-credential setup and the restored groups'
  intentional NOLOGIN state. No role authority was relaxed. The parent approved
  the existing real-test owned login→SET ROLE→commit→bound AsyncSession adapter,
  with effective identity/nonprivileged checks and finally rollback/reset/commit.
  Migrator stays the read-only oracle; all service calls run at restricted role.
- R4 exposed pg_stat_ssl observation after role attenuation. The executor
  stopped at its repair cap, committed checkpoint8fc0650, and returned it.
  The parent authorized one bounded continuation moving the actual TLS check
  before SET ROLE on the same connection, without grants or transport changes.
  Final14management/25smoke contracts pass15.198/6.246s; all narrow independent
  repair reviews report0blockers/0warnings. R5alone supplies the actual pass.

Only the changed current fixture SHA entry is updated in producer/consumer:
`b8ecf20867f61c3dabbba6ab0e55f5db1a08f5c59c220b9c38fa59da6cc3c4d3`.
Historical/app/SQL/ACL pins are unchanged. Existing economic seed/JSON is not
regenerated, since only restored execution observation/adapter changed.
One small test import omission was corrected before the passing final group;
failed contract/proof logs remain preserved. No new product stub or authority.

## Evidence, Cleanup and Limits

The four evidence documents link raw logs, source-aware reuse and scope. Private
root`/tmp/birja-phase15-plan03/` contains reuse.json, final-integrity.json,
scan argv/IDs/reports and per-attempt terminal/preservation records. Final
read-only integrity command exits0. Original supervisor/preflight/child groups
and all six exact owned projects are empty. Nine prior archive/UI artifacts
and three failed Phase15 archive/record sets retain SHA/inode/device identities.
No unrelated service or production data is inspected or changed.

R1–R4remain refused/failed with unchanged receipts; historical Phase14 failures
remain failed. Current-only flags arewhole7=false/same_archive_final_ci=false;
no all-security/whole-browser/hosted-CI pass is claimed. Full required CI before
merge, original issue35 scope/expiry and deferred Phase7obligations remain.

No application/schema/financial SQL/dependency/image-version/UI/provider/
production/publication change. GlobalSTATE/ROADMAP/requirements remain parent-
owned. All three whole requirements await04acceptance and independent goal
verification. Work remains local; unrelated.claude/ remains untouched.

## Self-Check: PASSED

All four task evidence files and seven recorded task/repair/evidence commits
exist. Actual R5/scan/raw integrity results pass; tracked inputs were frozen
through guarded work, prior identities match and no owned resource remains.
No task or requirement completion is inferred from a still-running receipt.
