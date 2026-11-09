---
phase: 06-deploy
plan: "08"
subsystem: infra
tags: [backup, systemd, ci, wolfi, chainguard, trivy, recovery]
requires:
  - phase: 06-deploy
    provides: "Plans07/14/15 retained recovery, rollback and strict image enforcement"
provides:
  - "Tested nightly backup units and measured bounded B2 inventory preflight"
  - "Required operational CI without weakening application, browser or security gates"
  - "Reviewed safer images with five actual raw HIGH/CRITICAL scans passing"
  - "Populated datastore transition and one verified final recovery artifact"
affects: [06-09, 06-10, 06-11, 06-12, 06-13]
tech-stack:
  added: []
  patterns: [signed exact Wolfi packages, clone-only datastore transition, independent retained recovery]
key-files:
  created: [deploy/backup-quota.py, deploy/systemd/birja-backup.service, deploy/systemd/birja-backup.timer, deploy/tests/test-ci-ops.py]
  modified: [backend/Dockerfile, backend/pyproject.toml, backend/uv.lock, frontend/Dockerfile, docker-compose.prod.yml, deploy/configure-db.sh, deploy/verify-restore.py, .github/workflows/ci.yml, deploy/RUNBOOK.md]
key-decisions:
  - "Keep raw HIGH/CRITICAL including unfixed findings; replace affected images without exceptions."
  - "Keep the complete audit dependency group default-enabled for host/CI and exclude its unused closure from application/test images."
  - "Never automatically convert live datastore ownership or refresh collations; require reviewed clone maintenance."
  - "Local acceptance does not authorize production/provider/publication actions."
requirements-completed: []
duration: "Interrupted multi-session execution; final serial recovery/role/TLS/rollback commands247.107s, not total development time"
completed: 2026-11-08
---

# Phase06 Plan08: Scheduled recovery and passing local security gates

Nightly recovery tooling and required operational CI are implemented. Reviewed
Wolfi Python3.14/Node24 and pinned Chainguard PostgreSQL18.6/Redis8.10.3 images
now pass all five actual strict scans with zero HIGH or CRITICAL findings.

## Task commits

| Task | Commits |
|---|---|
|08-01 scheduling/quota RED → GREEN|`8d38095`, `e2b02b4`|
|08-02 operational CI RED → GREEN|`5d22241`, `68f622b`|
|Reviewed freshness/quota fixes|`0a68575`, `80a7a2f`, `ea4cd28`, `c8e23fd`; review `8d0e2ba`|
|08-03 T3A image/audit-group RED → GREEN|`956d782`, `b48f80e`|
|08-03 T3B datastore/recovery RED → GREEN|`59819fb`, `e40f688`|
|Independent replacement review / final T3C evidence|`e72dcda`, `10b5241`|

The checked replacement contract revised only task03, preserving completed
tasks01/02 and the existing15-plan dependency graph. Original Debian failures,
Plan15 remediation and the historical cb766040... archive remain recorded.
No scan suppression, vendor/SBOM masking or security exception was introduced.

## Verification

- Independent final replacement source/security review:22 paths,0 blockers and
  0 warnings. Final source is byte-identical to reviewed `e40f688`.
- Fresh unchanged scanner producer exit0,29.325s: runtime, test-builder,
  consumed Node toolchain, PostgreSQL and Redis each0HIGH/0CRITICAL. DB updated
  2026-11-08T06:39:21Z. Exact identities/reports are in IMAGE-GATES.
- Backend616 passed,99.80% overall, unchanged critical-path list100%; native
  imports, offline locked sync, runtimeUID1001/migrations,5 in-image smoke tests,
  default host pip-audit, Ruff/format/mypy passed.
- Actual frontend image264 tests,99.06% statement coverage, lint/types/format/
  static build and high-severity audit passed. npm retains13moderate/2low.
- Actual unfiltered isolated browser suite10 passed/1 expected production-only
  CSP skip,57.406s, retries0. No real email, private configuration or production
  URL was used.
- Operational contracts image13/CI4/prerequisites15/backup25/safety4/config117,
  five shell suites58 assertions, input guards and nginx syntax passed.
- Populated old-to-new transition37.064s proved clone-only PostgreSQLUID70,
  actual glibc/collation drift, REINDEX before refresh, data/index invariants,
  logical restore and untouched-original abort; RedisUID65532 AOF/auth/TTL/
  noeviction/restart and original abort passed. Immutable v0.3.1 dependency
  bytes and actual retained-Dockerfile old-source builds passed in T3B.

## Exact final artifact

Preserved at ignored `.local/phase-06-handoff/candidate-cgr/recovery.tar`,
152,156,160bytes, SHA256
`83f4f5151807b67072d99e13a89c6b5f90617d54b7a8261c55931705d6f5044d`.
Separate checksum,19-payload inventory and trusted verifier are retained;
standalone generic verification of the copied packet passed.

All four serial runners exited0: supplied recovery65.167s, populated roles
30.099s with65 denials, TLS49.578s, actual v0.3.1 supplied rollback102.263s.
Both supplied runners consumed identical archive bytes without repackaging or
checkout fallback. Same installed recovery worked before/after hardening and
after old-application rollback. All six fixed projects have zero remaining
containers/networks/volumes.

## Issues and limits

Measured DHI candidates still failed raw scans; the authorized Wolfi/CGR path
passed. Audit regrouping changes project metadata only, preserving resolved
dependency artifacts and default host/CI auditing. A matching PostgreSQL major
does not permit automatic live volume reuse: later production work requires
the stopped-writer selected-clone/collation procedure in RUNBOOK.

An extra full-suite attempt in the smoke image failed because its environment
lacked host/CI fixtures; the prescribed host suite passed616. A private browser
report filename collision lost detailed JSON after successful execution;
actual list output and passed `.last-run.json` remain verified. Both failures
are retained honestly in T3C evidence, without fabricated reports or source
changes. Freshness/quota source findings from the earlier review were fixed
and independently closed before replacement acceptance.

## Next boundary

Plan08 is complete; Phase06 is10/15, not complete. DEPL-01/02 remain pending.
Plan09 needs separately scoped real host/provider/config/recovery/timer
authority and actual off-server restore plus a genuine nightly trigger.
Plans10..13 retain actual current-head CI, release, secure production transition
and Gmail/Outlook friend acceptance. Local-only scope remains in force; no push,
provider access, production installation/restart or live data action occurred.

## Self-check: PASSED

Final evidence `06-08-T3C-EVIDENCE.md` binds50 passing command records, five
raw reports,22 reviewed source hashes, the exact copied packet and cleanup.
Its166-file private manifest SHA256 is
`6a95813377aa41c9d6daa12beb7404df2a8b2b22c60c09c4b4dc6aacb81e3dad`.
No remaining local acceptance failure or unresolved source finding exists.
