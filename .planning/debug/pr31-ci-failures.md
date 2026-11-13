---
status: verifying
trigger: "continue"
created: 2026-11-14
updated: 2026-11-14
---

# PR 31 hosted CI failures

## Current Focus

hypothesis: The image contract still includes the old OTEL record; cold CI verifies but never imports/binds the recovery archive before its first Compose use.
next_action: Await explicit owner approval for exact dnspython2.9.2 prospective lock/install; resume only that approved delta and affected checks. Unaffected repairs are committed locally as d855a0f; no push.
reasoning_checkpoint:
  hypothesis: CI exports and verifies the registry image but never binds the alias that the first fresh-cluster test uses with pull_policy never; local prior recovery extraction leaves that alias warm.
  confirming_evidence:
    - check-recovery-image.py verifies_saved_image without image load/bind; CI invokes the fresh-cluster test before serial bundle extraction.
    - Hosted four subtests fail at Compose up before restore; exact required alias is distinct from registry reference.
    - Historical e728855 full package comparison shows only approved calendar additions and OTEL change; local13test image RED exactly matches hosted digest mismatch.
  falsification_test: A missing-alias startup succeeds, or importing/binding the same authenticated export does not permit unchanged guarded startup.
  fix_rationale: Initialize the authenticated image alias at the existing CI prerequisite; isolate the exact approved OTEL record while retaining historical all-other-entry identity.
  blind_spots: Actual cold-alias startup and complete real PostgreSQL contracts still need execution; DNS lock/install remains owner-pending.

## Symptoms

expected: PR31 required CI passes with existing coverage, security and recovery gates enforced.
actual: backend/image/ops/ci-pass fail at head95912e0; frontend/e2e pass.
errors: pip-audit flags dnspython2.9.0 CVE-2026-128089, fix2.9.2; image exact inventory hash mismatch; four fresh-cluster subtests fail starting Compose with ValueError recovery guard.
timeline: First hosted run43502466097 after completed local Phase11 verification.
reproduction: Inspect /tmp/birja-pr31-failed-ci.log and reproduce affected commands with isolated synthetic fixtures.

## Scope and authorization

User requested continuing after the CI failure summary: investigate, make local fixes and affected verification. Existing exact dependency approvals do not approve a different package; prepare concrete review before requesting installation approval. No gate waiver, private credentials, provider/production changes, merge or deployment. New push approval remains separate. Preserve unrelated .claude/ and shared-tree work; do not switch branches.

## Evidence

- timestamp: 2026-11-14
  checked: Official dnspython advisory, artifacts, provenance and temporary uv resolution
  found: Exact review ready in pr31-DEPENDENCY-REVIEW.md; only dnspython entry changes in temporary lock, no project mutation/install.
  implication: Parent can request exact package approval while unaffected fixes continue.
- timestamp: 2026-11-14
  checked: Local image contracts and historical e728855 lock
  found:13tests reproduce one exact hosted failure; only changed preexisting full package record is approved OTEL1.45.2.
  implication: Preserve historical inventory except exact independently authenticated OTEL record.
- timestamp: 2026-11-14
  checked: Actual Docker cold startup using unique owned alias/project, unchanged Compose constraints and check_running guard
  found: Missing synthetic alias produces No such image with pull_policy never; helper verifies export before import/binding, then actual isolated PostgreSQL startup and check_running pass. Existing tags untouched; owned resources removed. Log /tmp/pr31-ops-cold.log.
  implication: Cold-run prerequisite failure reproduced and corrected without changing retained CORE or selecting unverified image.
- timestamp: 2026-11-14
  checked: python3 deploy/tests/test-image-contracts.py; python3 deploy/tests/test-ci-ops.py
  found:15image contracts pass0.604s, including unapproved OTEL version/artifact, unrelated version/artifact, invalid archive and wrong existing alias negative controls;16CI contracts pass0.450s after adjacent mock updated for load/bind. Original13test RED is retained /tmp/pr31-image-red.log.
  implication: Exact artifact/inventory security remains enforced and CI preflight still precedes builds.
- timestamp: 2026-11-14
  checked: Original95912e0 preflight on unique synthetic cold alias, followed by actual same Compose before/after startup
  found: Original strict preflight passes yet alias remains missing; Compose refuses No such image. Patched helper then gives actual guarded PG GREEN. Log /tmp/pr31-ops-cold-before-after.log. Existing aliases preserved, owned tag/network/container cleaned.
  implication: Original-source behavior directly confirms missing prerequisite, rather than inferring it from warm host success.
- timestamp: 2026-11-14
  checked: sudo python3 /tmp/pr31-real-pg.py (actual affected24test PostgreSQL recovery suite)
  found:24tests pass122.519s, including all four original fresh-cluster subtests and function/schema/unsafe-runtime refusal controls. Log /tmp/pr31-ops-postgres.log. Owned birja-test/birja-ops-test containers and cold network absent after cleanup.
  implication: CI cold image initialization fix preserves actual0014 restore, role/quarantine/identity assertions without CORE changes.

- CI run: https://github.com/YokAI-open/Birja/actions/runs/43502466097
- Log: /tmp/birja-pr31-failed-ci.log
- Local accepted prior proof: .planning/phases/11-mixed-asset-recovery-and-acceptance/11-VERIFICATION.md

## Eliminated

None yet.

## Resolution

root_cause: Exact pre-regrouping inventory omitted the separately approved OTEL repair; CI verified a pulled recovery image without importing/binding the fixed alias required before the first fresh-cluster Compose startup. Independently dnspython2.9.0 is affected by CVE-2026-128089.
fix: Exact full-record OTEL exception preserves historical other distributions; preflight imports only authenticated export and binds approved config/platform identity, refusing wrong preexisting alias. DNS replacement pending owner approval.
verification: Original image RED reproduced;15image/16CI contracts and original-helper actual cold-alias RED/GREEN pass. Actual24PostgreSQL contracts pass122.519s with cleanup verified. DNS audit still pending exact patch approval; hosted CI remains unverified.
files_changed: [deploy/tests/test-image-contracts.py, deploy/tests/check-recovery-image.py, deploy/tests/test-ci-ops.py]
commit: d855a0f (reviewed unaffected image/ops fixes, local only)

## Specialist Review

specialist_hint: python/general. Mapped python-expert-best-practices-code-review
and engineering:debug skills are not available locally; none invoked. Independent
affected code/security reviews will be coordinated before local completion.

Independent code review: pr31-CODE-REVIEW.md, no active findings. Independent
security review: pr31-SECURITY-REVIEW.md,6/6closed, no active findings. Both
reviewed the exact three changed source paths; dependency installation is pending.
