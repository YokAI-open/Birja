---
phase: 24-compare-portfolio-performance
plan: "06"
subsystem: recovery
tags: [postgresql, restic, portfolios, recovery]
requires:
  - phase: 24-04
    provides: "Exact daily portfolio capture and private owner history on schema 0028"
provides:
  - "Recovery v9 with an exact schema 0028 manifest and restricted role restoration"
  - "Phase 24 recovery campaign with the retained 0027 release and immutable image bindings"
affects: [24-07, 24-08]
tech-stack:
  added: []
  patterns: [finite-recovery-contracts, canonical-ledger, isolated-cold-restore]
key-files:
  modified:
    - deploy/backup-snapshot.py
    - deploy/verify-restore.py
    - deploy/tests/portfolio-sources.py
    - deploy/tests/portfolio-retained-sources.json
    - deploy/tests/test-stock-recovery-contracts.py
    - deploy/tests/test-portfolio-recovery-contracts.py
    - deploy/tests/ops-fixtures.py
    - deploy/tests/portfolio-smoke.py
    - deploy/tests/run-portfolio-validation.py
    - deploy/tests/test-stock-catalog-finance-recovery.sh
    - deploy/tests/test-portfolio-validation-contracts.py
key-decisions:
  - "Select recovery v9 and payload 8 explicitly for 0028 and preserve v8 and payload 7 for 0027."
  - "Measure quarantine authority on a real PostgreSQL restore without archived ACLs before granting runtime authority."
requirements-completed: [TREND-03]
completed: 2026-11-26
---

# Phase 24 Plan 06 — Daily portfolio recovery

Recovery v9 authenticates all eight columns of each daily observation, the
table count, the identity sequence, schema fingerprints and runtime grants.
The restore verifies quarantine before it reapplies exact 0028 grants. The
0027 release remains available as a pinned source with the existing v8
contract.

| Task | Commit |
|---|---|
| Bind v9 producer, consumer, source inventory and canonical proof | `0351ce3` |
| Wire the Phase 24 campaign, pin measured quarantine and rehearse recovery | `08a1948` |

The retained 0027 release is v0.8.1 commit
`0c26810fb0bcb15323705a38aae63b531d69b992`. Its source tar SHA-256 is
`c97958efd402c26a4e81452bda8019c066d977625ff12e5507dcf1d1fa3f9daf`.
The existing v0.8.1 recovery archive was read for its already qualified
registry manifest bytes during the offline component run. Its SHA-256
`2ac4444ec5a45188075ac7baf8f79bfd4335d3e8c9e0fee3a64a47fe1e8916e6`
matched before and after the run.

| Exact 0028 evidence | SHA-256 |
|---|---|
| Canonical schema | `d9a4ee43bdb6fa96891dd087a32131510ceb596548a6947b28c15fd699a7dc0b` |
| Granted role authority | `00e3ccb0993ae129c28969c11063ec6a5a72c29a73eba383f05ca38da03cd3bd` |
| Normalized quarantine authority | `56f9f871fbd03561e84a51a64274c6f1b5cd3daef3ab8d3ce5a1d5ae3e518c47` |
| Bootstrap catalogue | `0484dd48782c9f215d1dea18fd767ae22f1b3ac558559c39837c9eef783fea25` |
| Bootstrap grants | `2faedb917aa58062f5af23449fecb6d699f3580e14d0b69e1ae1c964d2a1eb0b` |

## Verification

- Stock recovery contracts ran 21 checks with 10 optional isolated checks
  skipped. Portfolio recovery passed 19 checks. Campaign contracts passed 44
  checks. Shell syntax, generated Python compilation and diff checks passed.
- The Phase 24 dry run selected the seven ordered stages with
  `current0028-cold`. The receipt requires the exact tested source, current
  immutable image and retained 0027 image. Phase 21 retains its own suite,
  archive, exact v8 inventory and stage names.
- A focused cold component used an independent private archive with
  SHA-256 `9b8d4f01989c48b2c12a31a94a02da7719d1fee765d189212a1d0a5c1ad9aba5`.
  It restored synthetic 0027 records, upgraded the populated book with
  its records and sequences intact and observed an empty daily table.
  The restricted scheduler captured complete, incomplete and terminal
  portfolio observations. A repeated capture retained its first value,
  and the application closed the terminal portfolio before a later capture
  was refused.
- A fresh isolated PostgreSQL server recovered the encrypted 0028 snapshot
  with matching rows, identities, grant evidence and legacy finance receipts.
  Restricted TLS reads matched both owners' expected private series and
  omitted closed and foreign portfolios. Redis quote evidence stayed out of
  the database snapshot and the populated daily ledger refused downgrade.
- The full seven-stage source-bound proof is scheduled for Plan 24-08.
  Its exclusive recovery archive directory remained absent during this plan.

## Deviations

- The canonical SQL now projects `utc_day` in ISO form to make hashes
  independent of PostgreSQL DateStyle.
- The first cold component found that prior migrations supplied grants in
  the scratch database used to estimate quarantine. A real restore with
  ACLs stripped established the correct fingerprint. The fixture now also
  checks the specific downgrade refusal for a populated 0028 daily ledger
  while preserving the 0027 NYSE assertion.

## Self-Check: PASSED

Both task commits and the eleven declared files were checked. The focused
component exited successfully and the prior proof directories remain in place.
