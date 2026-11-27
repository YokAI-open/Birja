---
phase: 24-compare-portfolio-performance
plan: "07"
subsystem: deployment
tags: [deployment, recovery, ci, postgresql]
requires:
  - phase: 24-06
    provides: "Exact 0028 recovery v9 archive and authenticated Phase 24 campaign"
provides:
  - "Exact 0028 deployment admission with preserved retained 0027 recovery"
  - "Required CI staging for the tested source, v9 archive and recovery receipt"
affects: [24-08]
tech-stack:
  added: []
  patterns: [finite-schema-admission, source-bound-ci-artifacts]
key-files:
  modified:
    - deploy/deploy.sh
    - deploy/RUNBOOK.md
    - deploy/tests/test-deploy-compatibility.sh
    - deploy/tests/test-rollback-db-security.sh
    - .github/workflows/ci.yml
    - deploy/tests/test-ci-ops.py
key-decisions:
  - "Qualify 0027 for migration to the tested 0028 source and require exact 0028 for candidate runtime."
  - "Stage only the archive and receipt authenticated for Phase 24 and the hosted tested commit."
requirements-completed: [TREND-03]
completed: 2026-11-26
---

# Phase 24 Plan 07 — Deployment and recovery CI

Deployment authenticates the daily portfolio migration, its role sources and
shared catalogue evidence before accepting 0028. It checks the selected database
revision after migration and before any application or scheduler starts. The
exact v0.8.1 code can recover the verified original 0027 state before the write
boundary. Post-write recovery keeps the 0028 candidate and its persisted
observations.

| Task | Commit |
|---|---|
| Qualify candidate deployment and the retained 0027 route | `e9ae84a` |
| Select Phase 24 in required CI and authenticate its staged artifacts | `5026e3c` |

## Verification

- Syntax checks passed for the deployment and rollback scripts.
- 114 offline compatibility cases passed. The tests exercised the actual
  pinned 0027 commit, migration from 0027, candidate runtime on 0028, refusal
  of older code on 0028, altered source evidence, and a migration that
  leaves the selected database at 0027. The last case left writers stopped.
- All 113 CI contract tests passed. They require the six existing jobs,
  the sealed legacy fixture window, the serial Phase 24 graph, and exact
  archive and receipt verification before staging. The tests reject older
  workflow selection, a previous receipt substituted at staging, and
  current source, archive and immutable image mismatches.
- The full integrated recovery rehearsal remains in Plan 24-08.

## Deviations

The deployment guard reads the selected database revision after the migration
command succeeds. This explicitly prevents a migration targeting the wrong
schema from passing admission through the runtime's older statement support.
The historical tests now read 0027 fixture files from the pinned release
because the current application uses 0028 source fingerprints.

## Self-Check: PASSED

Both task commits exist, all six declared files were included and the
compatibility and CI commands exited successfully.
