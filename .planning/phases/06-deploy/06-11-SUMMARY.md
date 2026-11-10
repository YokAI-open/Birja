---
phase: 06-deploy
plan: "11"
subsystem: infra
tags: [release, ci, recovery, tls, compose, clone-routing]
requires:
  - phase: 06-deploy
    provides: "Approved integration and release0.4.0 preparation; nightly observation deferred"
provides:
  - "Release0.4.0 prepared and PR27 published with explicit approval"
  - "Reviewed protected clone routing and TLS-first startup correction"
  - "Actual exact-head release CI42787743632 passes all six required jobs"
  - "Concrete publication and later rollout proposal with explicit remaining preflight"
affects: [06-12, 06-13]
tech-stack:
  added: []
  patterns: [protected existing-volume binding, exact-head CI, independent recovery, precise Bake filesystem consent]
key-files:
  created: [deploy/datastore-bindings.py, deploy/tests/selected-cutover.py, deploy/tests/test-datastore-bindings.py]
  modified: [.github/workflows/ci.yml, deploy/deploy.sh, deploy/deploy-entrypoint.sh, deploy/configure-db.sh, deploy/RUNBOOK.md]
key-decisions:
  - "Owner approved local rollout correction after initial green release CI exposed source readiness gaps."
  - "Keep independent recovery CORE/archive unchanged and preserve original volumes."
  - "Owner authorized reviewed/tested CI/test/planning follow-ups until CI passes; merge/deploy remain separate."
requirements-completed: []
requirements-addressed: [DEPL-01]
duration: "Multi-session release preparation and bounded rollout/CI corrections"
completed: 2026-11-10
---

# Phase06 Plan11: Verified release candidate and publication checkpoint

**Release0.4.0 PR27 is green at945791115c0bd88fd0cf62835aca3e03c395659f,
with actual protected-clone cutover and old-app rollback evidence.**

## Performance

- Tasks:3 complete.
- Published release paths changed:36 relative to approved develop5ebf62b.
- First version commit:2026-11-09T12:58:22Z; final CI completed2026-11-10.
- Duration spans multiple sessions; no synthetic elapsed-work estimate.

## Accomplishments and task commits

1.11-01: prepared approved0.4.0 from updated develop5ebf62b, including Phase5
and Phase6. Version-only524080f changed four project/lock files without changing
resolved dependencies; local evidence16623a8. Feature closeout0e0a6eb preserved.
2.11-02: owner approved exact16623a8 release push/main PR, later77dcd44, then
38eb25c and bounded CI-only follow-ups. No merge/tag/deployment authority.
3.11-03: published PR27; initial16623a8 CI passed, then owner-authorized local
readiness correction9369351→d876806 and bounded regressions/fixes through
ce55207/b6b717c. Source and actual same-archive proof accepted in the linked
LOCAL-FIX-EVIDENCE/reviews. Actual CI exposed Git configuration and Compose
filesystem-consent fixture boundaries;7d3f8a4→c343f6b and b31f3dd→d7f0cf5
were independently reviewed/tested and published under explicit CI authority.
Final published head9457911 has six successful jobs in run42787743632.

## Actual final-head verification

[PR27](https://github.com/YokAI-open/Birja/pull/27) remains OPEN into main.
[Run42787743632](https://github.com/YokAI-open/Birja/actions/runs/42787743632)
head945791115c0bd88fd0cf62835aca3e03c395659f: backend/frontend/image/e2e/ops /
ci-pass all SUCCESS. Main base0107706617b8bbf9c1a069f3e3ccc9c53b9ab2f7;
GitHub reports MERGEABLE/CLEAN. No merge was performed.

- Backend616 passed; critical-path coverage100%; lint/format/types/audit pass.
- Frontend264 passed; lint/types/format/audit pass.
- Browser9 passed, one health-screen test passed on retry and is marked flaky,
  one expected production-only CSP skip. Do not call this10 first-attempt passes
  or claim the known health flake was fixed. Earlier failures/retries retained.
- All five actual raw image reports independently hash/config-ID verified,
  each0HIGH/0CRITICAL; strict policy includes unfixed findings unchanged.
- Ops transition35.842s, recovery58.140s, roles18.595s/65denials, TLS20.069s,
  existing actual v0.3.1 rollback85.653s, new retained selected cutover206.439s.
  Real TLS-first startup, forced recreation,0008, old-app rollback, Redis state /
  auth, unchanged original fingerprints, same installed pre/post recovery and
  mandatory cleanup all passed on the actual runner.
- Local final Compose5.7.0 supplied d5fe2059 archive proof257.676s passed;
  nine CI contracts, focused lint/format and diff checks pass. Earlier full
  backup25/safety4 and routing/prerequisite/shell regressions are preserved.

## Source acceptance and deviations

Initial readiness review found missing persistent candidate routing and TLS/HBA
startup ordering. Owner explicitly approved the bounded local correction.
Protected root-only JSON, exact existing metadata/data, external-only overlay,
actual sole-container identity and limited TLS-first startup now bind retained
deployment/recreation/rollback to selected candidates. Originals stay unchanged.
Docker full IDs, real Redis AOF formats, HBA readability and containerd image
identity were corrected through meaningful regressions and real proof.

CI-only corrections isolate host Git config in the synthetic launcher and pin
Compose5.7.0 in the disposable runner for precise retained Dockerfile consent.
No wildcard filesystem grant, bypass, changed recovery CORE or production plugin
installation. Independent reviews are clean; see LOCAL-SOURCE-REVIEW,
LOCAL-FINAL-REVIEW, CI-GIT-REVIEW and CI-COMPOSE-REVIEW. The observed health test
flake remains recorded separately from closed source findings.

## Remaining boundaries

Plan11 delivers release preparation and current-head CI, not DEPL-01 completion.
DEPL-01 awaits approved rollout/friend verification; DEPL-02 still awaits the
owner-deferred actual nightly observation.09SUMMARY remains absent.

Installed recovery archive remains
`d5fe2059b3e984ffcd0dff6b1763dd5a97deddb0be638ca23e49381d35a54401`.
No production app/role/TLS/volume/provider operation occurred in this plan.
Current production state has not been re-inspected. Production capacity,
identities/collation scope/custody, final main SHA/MANIFEST and outage window
remain separate measured preflight inputs in the rollout proposal.

Next is Plan12's explicit publication/merge checkpoint. Merge current PR only
with owner approval and a merge commit after rechecking exact-head green CI.
Tag/release publication, back-merge and production rollout remain separate.
Planning closeout is committed locally and may be carried with the next approved
integration; it must not silently change the already verified published PR head.
