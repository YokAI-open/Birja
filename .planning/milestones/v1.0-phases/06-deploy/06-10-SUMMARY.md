---
phase: 06-deploy
plan: "10"
subsystem: infra
tags: [ci, github, recovery, integration]
requires:
  - phase: 06-deploy
    provides: "Reviewed local gates and actual off-server recovery; nightly observation deferred by owner"
provides:
  - "Feature PR26 published and actual current-head CI passed"
  - "Approved merge-commit integration into develop"
  - "Owner-selected local release0.4.0 preparation authority"
affects: [06-11, 06-12, 06-13]
tech-stack:
  added: []
  patterns: [exact-head CI, independently reviewed bounded fixes, explicit publication gates]
key-files:
  created: [.planning/phases/06-deploy/06-10-CI-PASS.md]
  modified: [.github/workflows/ci.yml, deploy/tests/test-ci-ops.py, deploy/tests/ops-fixtures.py, deploy/tests/test-rollback-db-security.sh, deploy/tests/check-recovery-image.py]
key-decisions:
  - "Owner deferred genuine nightly observation; preserve09pending and proceed with distinct publication work."
  - "Preserve all security/test/recovery guards while aligning disposable CI prerequisites."
  - "Merge exactgreenPR26 with a merge commit; locally prepare selected0.4.0 only."
requirements-completed: []
duration: "Multi-session publication and bounded runner compatibility corrections"
completed: 2026-11-09
---

# Phase06 Plan10: Feature publication, actual CI and approved integration

PR26 passed every required job at exact
a7d5dcb01d40a916c9cbf9d6ff51525c70c50833, actualrun42618704350.
Owner approved merge plus local0.4.0 preparation. Rechecked exact head/checks
and merged with Create-a-merge-commit into develop as 5ebf62b33b190aaf04a48b107a222e906fbf4c99.

## Task evidence and commits

| Task | Result / commits |
|---|---|
|10-01 publication choice|Owner explicitly approvedc085a766 feature push/PR26; later exact followups and boundedCI-onlycompletion authority recorded|
|10-02 actualCI|Initial failures retained; cache/uvc5fc244→7d5d8c2, rootfixturesb1dd6dd→0637b48, nginx49df53f→eec70c5, DockerAPI8d3466f→f5ad5cc, storeb44f381→57974aa; independent reviews clean|
|10-02 final acceptance|a7d5dcb/run42618704350 backend/frontend/image/e2e/ops/ci-pass SUCCESS|
|10-03 integration/version|Owner “Merge and prepare0.4.0”; actual merge5ebf62b33b190aaf04a48b107a222e906fbf4c99; release publication/deploy excluded|

## Verification

Backend616passed/99.80%overall/100%critical; frontend264passed. Actual browser
10passed/1expectedproduction-onlyCSPskip, full trading andportfolio/history
whole-position flow,375/768/1024/1440 widths passed. All5raw image reports
hashmatch successfulstatus and each0HIGH/CRITICAL.

Ops proves containerd publicexport through unchanged strict verification,
populated transition34.051s/recovery62.533s/roles24.112s+65denials/
TLS23.141s/actualoldrollback96.232s. Source credentials/checkout/Compose
unchanged, badCA/hostname/plaintext denied, stale/missing evidence rejected,
retained immutable routing/locks and0008preservation pass. Cleanup succeeded.

## Deviations and limits

Hosted runner lacked dependencies/root invocations/platform API and retained
classic image store. Bounded reviewed CI/test fixes align its environment
without weakening actual guards. Failed classic archive raw members were
unavailable; exact member differences were not claimed. No VDS Docker upgrade,
service restart, recovery payload/installedbundle change or policy waiver.

Owner explicitly changed sequencing to defer firstnight observation.09 and
DEPL-02 remain pending; neither fakecalendarproof nor09SUMMARY was created.
This summary completes only10. Next11 localreleaseprep; no release push/main
PR/tag/mainmerge/backmerge/deployment authority. Phase acceptance and actual
friend checks remain pending.

## Self-Check: PASSED

- Actual PR/checks/logs/rawreports bound to exact published head; allsixpass.
- Exact approved head merged using merge commit; ownerselected0.4.0.
- Prior private/production/tool/archive evidence preserved and no completion
  claim beyond this plan. Local closeout carried into the release branch.
