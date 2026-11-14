---
phase: 06-deploy
plan: "15"
subsystem: infra
tags: [docker, provenance, recovery, trivy, ci]
requires:
  - phase: 06-deploy
    provides: "Plans07/14 retained recovery and rollback contracts"
provides:
  - "Immutable same-major images and complete justified pip/npm tool changes"
  - "Strict five-target image CI with retained failure evidence"
  - "Authenticated Docker29 attestation compatibility and exact final recovery replay"
affects: [06-08, 06-09, 06-12]
tech-stack:
  added: []
  patterns: [authenticated image graph, imported fixed image alias, strict archive scans]
key-files:
  created: [deploy/scan-images.py, deploy/tests/test-image-contracts.py, .planning/phases/06-deploy/06-IMAGE-GATES.md]
  modified: [backend/Dockerfile, frontend/Dockerfile, deploy/verify-restore.py, .github/workflows/ci.yml]
key-decisions:
  - "Expected raw HIGH/CRITICAL failures complete this bounded evidence prerequisite but keep08 blocked."
  - "Authenticate the optional selected-platform attestation against the pinned index; unknown graph content still rejects."
requirements-completed: []
duration: "Interrupted multi-session execution; final four serial runners282.632s, not total development time"
completed: 2026-11-07
---

# Phase06 Plan15: Image enforcement and recovery compatibility

Immutable same-major consumer pins, complete justified tool changes, strict five-target CI and one authenticated final artifact now have reviewed compatibility evidence. Remaining vendor image vulnerabilities are recorded as blockers, not accepted.

## Task commits

| Task | Commits |
|---|---|
|15-01 image/provenance RED → GREEN|`a126899`, `5bc74ed`|
|15-01 complete npm RED → GREEN/bounded streaming|`4c77542`, `be09c3f`, `3bc1ca7`|
|15-02 scanner/CI RED → GREEN|`500a724`, `a5dd5a2`|
|15-02 reviewed missing-image evidence fix|`26614f5`|
|15-03 actual-export compatibility correction|`de331fb`|

Detailed commands, exact image/config/registry identities, scope refinements, inventory, report hashes and failures/resolution are in `06-IMAGE-GATES.md`. No source work was repeated during closeout.

## Verification

- Final independent source review and both focused rechecks: zero active findings. Final9 image contracts include classic/containerd import-only zero-pull behavior, authenticated attestation tamper/unknown-graph rejection, and missing-image CI failure-evidence collection.15 prerequisites/4 safety, affected lint/format/whitespace passed. Earlier8 image/4 CI,25 backup,20 input rejection and retained real-Git routing checks remain recorded evidence.
- Actual pinned backend stages, locked offline uv/import/migration/test CLIs, nonroot runtime5smoke and pip-audit passed. Current frontend audit/build and actualv0.3.1 locked frontend build passed; finalized bounded-download toolchain rebuilt. No application lock changes. Historical616 backend/264 frontend suite evidence was not unnecessarily repeated.
- Final archive `/tmp/birja-backup-test-plan15-fixed-zl4pb12y/recovery.tar`,199,669,760bytes, SHA256 `cb766040b9eed5eed4dce00400d39c0d8bcb7a02fc4c6d4030c9e6cf6da16814`; separate checksum matches. Profile deploy-recovery-v2 includes19 authenticated payloads, both units/quota preflight and signed-restic provenance. Package/verify8.082s.
- Same exact supplied archive: recovery73.507s and actualv0.3.1 rollback119.673s, both exit0. Populated roles31.845s and TLS57.607s, exit0. Preserve financial/session/schema equality, writer snapshot,65 denied operations, badCA/hostname/plaintext rejection, mount isolation/renewal, old-image services and0008. Actual installed Compose/running image matches authenticated imported platform/config/fixed alias with pulling disabled; absent-registry zero-fallback contract complements actual execution.
- All4fixedproject cleanup commands returned0. Fresh2026-11-07 label queries verify zero containers/networks/volumes. Archive/hash rechecked; no shared cache/images deleted.

## Deviations and interruptions

Docker29 exposes a platform manifest as engineID while classic engines use configID. Implementation preserves distinct authenticated index/platform/config identities and narrowly binds a fixed local alias, rather than assuming every inspect.Id is a config hash.

Authorized ownership refinements add the retained frontend Dockerfile inventory and its one-line rollback-fixture adaptation. The complete official npm distribution, not a partial vendor edit, is used by actual consumers. No new project dependency/framework was introduced.

Review found missing built-image IDs aborted collection before other targets;26614f5 corrects it and passed independent recheck. Actual final packaging then exposed an authenticated OCI attestation sibling: saving the selected ID did not fix it. That ineffective attempt was removed;de331fb authenticates the optional graph and passed separate independent review plus actual package/replays. Unknown blobs remain rejected.

The executor hit a usage limit after starting the last rollback. Persisted JSON/logs prove it finished successfully; parent closed out by inspecting evidence and cleanup rather than repeating the fixtures. Older archive/provisional packaging failures remain historical evidence, not current acceptance.

## Residual blocker and authority

Raw Trivy scans still fail: runtime49HIGH, builder54HIGH (including5 required pip-vendor rows), PostgreSQL91HIGH/2CRITICAL, Redis48HIGH, final Node48HIGH. Global runtime pip and all6npm findings were removed; Debian, required test-tool and gosu findings remain. Image IDs/report hashes/date2026-11-06 are in IMAGE-GATES. No waiver/suppression or clean image claim exists.

**Plan08 task03 remains blocked. No08 SUMMARY, Plan09/live advancement or DEPL-01/02 completion.** Provider setup, real off-server restore/timer, actual remote CI, release/deploy and Gmail/Outlook friend acceptance retain their existing gates. No provider/private-secret/live/realOTP/email/trade/push/PR/merge/release action occurred. Parent owns STATE/ROADMAP/handoff updates; unrelated.claude preserved.

## Self-check: PASSED

Required source/evidence/review and exact archive/checksum exist; bounded source/security review and actual final compatibility proof pass. This summary completes only Plan15's defined prerequisite, with requirements-completed empty.
