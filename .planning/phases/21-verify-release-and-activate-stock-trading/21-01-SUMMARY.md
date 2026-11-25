---
phase: 21-verify-release-and-activate-stock-trading
plan: "01"
subsystem: recovery
tags: [ci, recovery, catalog-finance]
requires:
  - phase: 20-09
    provides: Paired local 0025/0026 recovery and v7 producer and consumer
provides:
  - Exact v7 successor campaign selection and authenticated stage contract
  - Success-only CI archive, checksum and receipt staging
affects: [21-03, 21-05]
requirements-addressed: [SV-02, SV-03]
requirements-completed: []
completed: 2026-11-25
tasks: 2
---

# Phase 21 Plan 01 summary

The explicit Phase 21 successor runner selects v7 with payload 6 and schema
0026 in a new exclusive synthetic directory. It checks the clean Git
commit, tree, backend build context and immutable 0026 image before stage
execution and reauthenticates the archive, current source, embedded
retained source and image bindings after every stage. The Phase 14 and 15
selectors and retained source matrix keep their existing semantics.

The required ops job selects the seven-stage successor graph. Its staging
step rechecks the completed receipt, source against `GITHUB_SHA`, profile,
archive checksum and immutable image. The upload carries
`recovery.tar.gz`, `recovery.tar.gz.sha256` and
`recovery-receipt.json` after strict checks on the copied bytes.

| Task | Commit | Verification |
|---|---|---|
| Bind the successor producer, consumer and image | `b818826` | Successor and legacy dry runs and 43 existing runner contracts |
| Require the successor artifact in GitHub CI | `cbda487` | 113 CI contracts, 44 runner contracts, a final targeted image-identity check, and diff checks |

## Plan 03 handoff

`successor_recovery_operations(ops, archive, expected)` is the guarded
entry point for Plan 03. Until wired, it refuses execution. Plan 03 supplies
exactly the seven callbacks in `SUCCESSOR_STAGES` using the selected archive
and digest. The cold, upgraded TLS and fresh TLS callbacks return the same
triple of SHA-256 authority fingerprints. The runner binds the current
0026 image before invoking the first callback and requires its identity
through the last. Portable contracts use disposable inputs and command
doubles to check dispatch, rejection and staging. The real same-bundle
rehearsal remains Plan 03, and hosted qualification remains Plan 05.

## Self-Check: PASSED

Both task commits, the expected sources, the portable exit statuses, and
the successor dry-run path and stage order were checked.
