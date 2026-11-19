---
phase: 14-end-strategies-safely
plan: "06"
subsystem: recovery-consumer
tags: [postgresql, recovery, quarantine, lifecycle, rollback, source-authentication]
requires:
  - phase: 14-05
    provides: Explicit V3 producer, complete retained source and independent lifecycle oracle
provides:
  - Exact payload3/revision0023/deploy-recovery-v4 consumer and mandatory member authentication
  - Complete source evidence comparison in quarantine before exact runtime regrant
  - Source-database-destroyed logical restore with all31tables and24identity tails
  - Finite selected-source forward compatibility and incompatible old-app rollback refusal
affects: [14-07, 14-15, 14-16, 14-18, recovery, selected-rollback]
tech-stack:
  added: []
  patterns:
    - Source manifest is required before0023 regrant, not checked only after granting
    - Complete fixed retained source is authenticated before historical authority import
    - Quarantine normalizes only the finite built-in PUBLIC function default
key-files:
  created: []
  modified:
    - deploy/verify-restore.py
    - deploy/deploy.sh
    - deploy/RUNBOOK.md
    - deploy/tests/test-portfolio-recovery-contracts.py
    - deploy/tests/test-portfolio-management-recovery.py
    - deploy/tests/test-deploy-compatibility.sh
    - deploy/tests/test-rollback-db-security.sh
key-decisions:
  - Current0023 restored contexts require the original source manifest before any economic runtime grants.
  - Retained0017/0020 consumers import their complete fixed source, never current authority constants.
  - A pending rollback to the same tested0023-compatible source is allowed; an incompatible older source refuses before mutations.
requirements-completed: []
requirements-progress: [PMGT-04, PFIN-05, PFIN-06, PSAFE-01]
duration: 16.5min measured first-RED-to-cleanup-receipt interval
completed: 2026-11-19
---

# Phase 14 Plan 06: Authenticated Closure Recovery and Rollback Refusal

**Complete lifecycle and original-request evidence is compared before runtime
regrant; source-destroyed logical recovery preserves every table and identity.**

## Performance and task commits

| Task | RED | GREEN | Result |
|---|---|---|---|
|1 — exact V3 consumer/quarantine|12d10e1|969ff52|Unsupported V3 regression; real source-destroyed logical PostgreSQL proof and strict package/member tests|
|2 — selected compatibility and retained dispatch|0316043|a7ae892|Finite current source acceptance, old-app refusal and complete retained source import checks|

First RED was2026-11-19T11:20:20UTC; owned cleanup/evidence receipt was captured
at11:36:50UTC. The measured16.5-minute interval includes implementation and
bounded checks, not a task latency promise. Parent owns STATE/ROADMAP and all
whole-requirement checkboxes remain pending.

## Implemented behavior

- V3 is explicit: payload version3, revision0023 and `deploy-recovery-v4`.
  Archive member sets, schema contract, all five fixed source archives and
  reviewed current source pins are mandatory. Coherent omission/repackaging or
  critical source alteration refuses before image/runtime handling. Existing
  V1/V2 semantics remain separate.
- Retained0017/0020 authority imports use the complete authenticated archived
  tree. The fixed archive SHA is checked before extraction/import and on every
  cached lookup. Internal symlinks resolve only inside the private extraction
  root; external links and special members refuse. No current backend overlay
  supplies a retained bootstrap.
- Current restore calls `restored(dc,dump,manifest=source_manifest)`. After
  no-owner/no-ACL import and private clone setup, the consumer authenticates
  exact catalogue/source, role/owner boundaries, lifecycle provenance, terminal
  names, stock state, financial hashes and every identity tail. All source
  evidence is compared **before** any runtime regrant.
- The only accepted pre-normalization non-owner privilege is the built-in
  PUBLIC EXECUTE function default introduced by no-ACL restore. Unexpected
  table/column/function principals or explicit unsafe future defaults refuse.
  Private defaults and fixed PUBLIC revocation establish the separately pinned
  quarantine state; it is validated and compared again before exact0023 grants.
  Final authority and source evidence are checked after regrant. Quarantine
  never qualifies for normal runtime admission.
- Selected deployment authenticates the retained tested commit and exact
  reviewed closure migration, SQL and bootstrap/admission source assets. The
  complete current source can migrate0020 through migration-only0021/22 to0023;
  ordinary deployment/runtime rejects those partial revisions. Incompatible
  older rollback refuses before checkout, routing or state changes. Pending
  rollback to the same tested compatible0023 source can retain candidate data.
- The runbook states the supported source/schema families, quarantine/regrant
  ordering, no-repair rule and actual proof limits. Tooling edits do not execute
  deployment, production recovery or provider operations.

## Final bounded verification

Raw receipts are under `/tmp/birja-phase14-plan06/`, including
`final-tests.json` and `receipt.json`. All seven source/test/document hashes
were frozen before the final serial run and verified unchanged after each gate.
The final tested source was committed as a7ae892; summary-only changes follow.

| Check | Actual result |
|---|---|
|Current logical PostgreSQL restore|Passed28.471s; source database dropped before restore, all31tables/24identity tails compared to independent before-backup oracle|
|Pregrant corruption negatives|Four real newly restored clones: changed cash, joint retained-name corruption, missing intent and changed sequence all refuse before runtime regrant|
|Restored outcome replay|Every original closed/refused intent replays without changing the complete oracle; zero-active identity remains zero|
|Recovery contracts|17passed3.644s, including coherent member/source omissions, source-family dispatch and no regrant on altered evidence|
|Package/retained contracts|9passed16.060s: V3 assembly/consumer plus8 fixed complete0020 contracts; external image transport mocked|
|Selected deploy/rollback compatibility|62actual offline control-flow cases pass2.941s; refusals preserve state and issue no mutation calls|
|Retained installation/control-flow self-test|Passed5.998s, including real Git checkout and0023 compatibility assertions|
|Rollback input rejection|Passed0.136s; zero Docker/package/install fallback calls|
|Static/historical checks|ScopedF/E9, Python compile, shell syntax and diff checks pass; no backend/migration/producer/fixed-source profile changed|
|Owned cleanup|Allbirja-p14-06 containers, networks and volumes removed; project-label queries empty|

The database diagnostic is a **logical source-database-destroyed restore on the
owned test PostgreSQL instance**. It does not claim independent-server destruction,
restic encryption, verified TLS or an uninterrupted seven-stage final campaign.
The package test mocks external image transport. Prior qualified archives remain
untouched; Phase13archive SHA is still
`6fb79a45ddcb10725b18fc756e71bd555c827a6e61a5a4a0bd2d183096114b92`.
No canonical Phase14 final campaign archive was created.

## Deviations and corrected diagnostics

1. **Rule2 — compare before regrant.** Existing restored contexts granted older
   authority before the caller's financial comparison. Current0023 now requires
   the authenticated source manifest as a keyword argument and compares full
   evidence in quarantine before grants. Legacy default signatures remain valid.
2. **Rule1 — complete retained extraction.** A new actual retained-import test
   found legitimate internal `.agents/skills` symlinks in the fixed source
   archives. Extraction now accepts only authenticated in-root symlinks with
   the data filter; it still refuses external/special members and never overlays
   current services. The test also proves post-cache archive alteration refuses.
3. The initial selected test expected a pending rollback to select the older
   previous log entry. Real semantics select the current tested entry while a
   deployment is pending. Tests now separately assert old-source refusal and
   compatible same-source preservation; no safety gate was weakened.
4. A first test edit was placed before its synthetic Git variables were defined;
   it was moved to the intended post-setup position. A scoped local variable
   error was corrected before GREEN. Initial failed logs are not passing proof.

No package, authentication, provider, production or publication gate occurred.
No blocking stub remains in this plan's consumer/control-flow scope.

## Later-plan handoff

- Current0023 callers of `restored` must supply `manifest=source_manifest` and
  verify final authority with `quarantined=False`. The CLI restore path is wired.
  Do not bypass the pregrant comparison or reinterpret legacy manifest families.
- Existing unowned `ops-fixtures.py` campaign helpers still explicitly require
  `deploy-recovery-v3`; Plans15/16 must adapt them to the reviewed V3 family and
  new restored-context argument before whole-source qualification in18. The
  full rollback integration/selected TLS/cold campaigns were not run here.
- Later public DELETE acceptance must still replace early service-only closure
  fixture acceptance in07/09/17. Plan06 does not complete normal API/privacy/UI
  requirements or authorize live activation.
- Full critical/security/image/browser, same-archive encrypted/current-retained
  cold/TLS and owner UI/native200 gates remain later phase obligations.

## Self-Check: PASSED

All seven planned files exist, all four task commits are present, final frozen
checks pass and owned cleanup is recorded. Working tree preserves only the
unrelated pre-existing `.claude/` after the summary commit. All whole requirements
remain pending; independent review must precede Plan07.
