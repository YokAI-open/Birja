---
phase: 13-create-and-compare-independent-strategies
plan: "04"
subsystem: recovery
tags: [postgresql, recovery, provenance, source-authentication, portfolios]
requires:
  - phase: 13-03
    provides: Reviewed0020 catalogue, authority and source pins
provides:
  - Complete immutable tested0017 source archive alongside retained0007–0014 lanes
  - Distinct0020 recovery producer, payloadV2 and exact29-table/22-identity projections
  - Independent before-backup metadata, original-grant and initialization oracle
affects: [13-05, 13-15, 13-17]
tech-stack:
  added: []
  patterns: [versioned source/schema dispatch, authenticated source before import, immutable before-backup oracle]
key-files:
  created:
    - deploy/tests/portfolio-management-recovery-fixture.py
    - deploy/tests/test-portfolio-management-recovery.py
    - deploy/tests/fixtures/portfolio-recovery-0020.json
  modified:
    - deploy/tests/portfolio-sources.py
    - deploy/tests/portfolio-retained-sources.json
    - deploy/tests/portfolio-execution-fixture.py
    - deploy/tests/test-portfolio-fixture-contracts.py
    - deploy/backup-snapshot.py
    - deploy/recovery-bundle.sh
key-decisions:
  - "Retained0017 is the complete tested4b4320b release, never an overlay or future HEAD reconstruction."
  - "PayloadV2 is produced separately; Plan05 must explicitly admit it in the restore consumer."
  - "Original canonical creation payloads and legacy initialization provenance remain separate from mutable current metadata."
requirements-completed: [PSAFE-07, PFUND-02]
duration: 19min
completed: 2026-11-18
---

# Phase 13 Plan 04: Immutable Sources and Successor Recovery Producer Summary

**Complete tested0017 source remains immutable while0020 snapshots include canonical metadata, permanent creation grants, all-user initialization provenance and every identity tail.**

## Performance

- Approximately19minutes, 2026-11-18 08:49–09:08UTC.
- Tasks:2/2; nine implementation/test files plus this summary.
- Both tasks have committed failing contracts before implementation.

## Accomplishments

- The new `portfolio0017` source lane authenticates the complete Git archive at `4b4320b4cc373268a8d598612a563cd5ef199700`, SHA256 `361a0fafbb6f1645d7beb9caeadb8bd46c85abc739d957dce7fc439b64eba248`. It includes producer, consumer, CORE, units, complete backend, Dockerfile and lockfile dependencies. Fixed app/alembic trees are independently checked before extracting/importing programs. Existing0007–0014 release identities and bytes remain unchanged. Current0020 uses an explicit separate payload version2 profile; partial0018/0019 and unsupported revisions refuse.
- PayloadV1 remains the original exact inventory. PayloadV2 extends it with0018–0020 migrations, both SQL assets, management model/bootstrap/admission/onboarding sources and the new fixture. `recovery-bundle.sh package --output ...` calls the successor producer. The producer retains pinned restic/image/provenance checks, exact members and checksums, private paths, non-overwrite behavior and the existing backup quota/staging limits. Verify/install remain consumer-owned and fail closed until Plan05 admits V2.
- The new SQL projection retains the entire prior economic projection and adds metadata, immutable creation UUID/canonical-payload/grant rows, initialization provenance, paired owner/FK/schema evidence and both new sequence states. It authenticates the current bootstrap source before importing its SQL, checks the separately pinned catalogue/ACL, rejects missing initialization or invalid canonical/owner/cap state, and carries explicit rewrite-rule/effective-schema/database-owner safety checks from reviewed authority.
- The independently specified synthetic state has ten active managed books plus a closed original, a new ID reusing its name, renamed initial metadata retaining the original `My portfolio` creation payload, an unchanged123.45cash/7777baseline legacy book and a legacy initialized zero-book owner without an invented grant. It has eleven real creation journals and three initialization records. Before-backup snapshots preserve all29tables and22sequence tails privately and compare every byte after replay/restoration; original expectations are never regenerated from restored data.

## Task Commits

1. Task1 RED: `3d9fb4b` — Specify immutable0017 recovery source profiles; missing dispatcher/profile failures.
2. Task1 GREEN: `331a2b3` — Freeze complete qualified0017 recovery source; seven initial contracts pass.
3. Task2 RED: `640c81c` — Specify exact0020 recovery producer contracts; unsupported revision, missing inventory and fixture fail.
4. Task2 GREEN: `61eb95d` — Produce exact versioned0020 recovery payloads, including strengthened source/image contracts.
5. Task2 tooling: `a15decb` — Mark the two new commands executable; unfiltered new-file lint/format pass.

## Verification

Final focused commands:

- `python3 deploy/tests/test-portfolio-fixture-contracts.py` — **8passed**,1.58s. Complete source/archive inventory, revision/version/commit/tree substitution, image revision/config/RootFS/content-ID mutation, independent retained money/evidence oracle and immutable snapshots.
- `python3 deploy/tests/test-portfolio-management-recovery.py` — **6passed**,1.83s. All V2 source-member hash mutations, retained inventory sizes, independently expected populated manifest, schema/function/missing-latch/missing-sequence/missing-journal/unsafe-authority negatives, before-backup original-key/payload/owner/closed/baseline/tail mutations, source drift and generated pre-import admission ordering.
- `python3 deploy/tests/test-portfolio-recovery-contracts.py` — **10passed**,0.42s, retaining exact0017 invariants/identities/authority behavior.
- `env -i PATH="$PATH" HOME=/tmp python3 deploy/tests/test-portfolio-management-recovery.py --postgres` — **passed at final source**. Only verified-owned `birja-p13-04` resources and existing Python3.14/pinned images were used. Actual0017→0020 migrations, grants and creation/metadata routines generate the independent fixture. Separately authenticated `birja_app` replays the original renamed creation at cap, refuses a closed original and conflicting original payload, and leaves all table/sequence bytes equal to the private before-backup snapshot. Original/quarantine/noACL permission projections match their pinned profiles.
- Both new Python command files pass unfiltered Ruff and Ruff format. All six changed Python commands compile; shell syntax and `git diff --check` pass.

The package-assembly test uses real current source files, all four complete retained Git archives and every member checksum. External runtime/image/registry transport is explicitly mocked, with a synthetic saved-image byte stream. This proves assembly/inventory behavior only, **not actual image provenance, restic encryption, TLS or recovery qualification**. The real PostgreSQL proof is local logical/authority evidence, not an encrypted archive restore or source-destruction campaign.

## Pinned0020 Recovery Handoff

- Schema: `7aa08fba535a66c8978dd19f956dc0db1c3da7c4d461f75f9d341ea1e5fe2da7`
- Authority: `785a5086286f815972eb0b09edbb4c8f6b15fe220fd614d233cda9051c191228`
- Quarantined authority: `47e3589ac675ecfc69308d1806a55ee5b9c24db42947d94c5a69fee9ace3aa9a`
- Quarantined ACL: `500ae682129bf6b3bc252d0c4f15cf41bdeed63785b17458c8d1c9ab70eb3f7c`
- NoACL authority: `a0a40e73d9fed9d6a420fcf17f4df6e70f032bd1bbeebfb8ae06d3c2fccd5a7c`
- NoACL privileges: `bd65d43da215a53d24b6a2a384951f57ea03efa76948d7603c953a84250b2b55`
- Plan03 catalogue and ACL remain exactly `d8f42ef33af7989badf342b5295d8d523cd6bf53839de6156a14e5251b5ee263` and `041a948470f9692628da43b35263a47bf58f4815310a0793d5eec099fa64c87e`.

Quarantine expectations revoke app create/initialize/metadata and scheduler dividend apply/hold/root-lock execution. NoACL expectations are measured after transactionally removing all runtime/operator relation/column/sequence permissions and applying PostgreSQL's PUBLIC function-execution defaults. Both permission experiments roll back. They are independent producer expectations; actual no-owner/noACL dump/restore and quarantine reconstruction remain Plan05 proof obligations.

## Deviations from Plan

None requiring scope or architecture changes. The producer packages V2 in `backup-snapshot.py` so the separately owned restore consumer is untouched. Routine implementation corrections narrowed metadata SQL augmentation to the accounts row projection and accepted SQLAlchemy's already-decoded JSON result; final focused and real-source runs pass. No financial guard, historical SQL/hash meaning, dependency, pin or coverage gate was changed.

## Limits and Cleanup

Plan05 owns consumer V2 admission, exact quarantine/grant reconstruction, restore and rollback/smoke wiring. Plan15 owns broader source/critical/serial campaign inventory. Plan17 must run the actual frozen-source encrypted same-archive/current+retained/cold/TLS/image campaign; none is claimed here. No full backend coverage, security campaign, UI or whole-requirement completion is inferred.

Exact owned Docker labels were checked before teardown. Container, network and volume queries for `birja-p13-04` are empty. The earlier archive remains untouched at SHA256 `d253bc51b876c7d629ee246ee47bd57274a5d9333e71318e11fcef586cff26be`. No provider/private.env/production/package/push/merge operation occurred. Unrelated `.claude/` is preserved. Parent exclusively owns STATE/ROADMAP/REQUIREMENTS updates; none were modified or staged here.

## Self-Check: PASSED

All nine declared paths exist; all five task commits exist, with RED before GREEN for each task. Focused contracts, final real-source proof, new-file static checks and preserved old archive hash pass. No tracked deletions, goal-blocking stubs or unplanned network/auth/schema surface was introduced. Only the intended new sources/fixture/summary are added.

## Independent Review Repair — 2026-11-18

**[Rule2 — Missing critical authority check] CR-01: operator LOGIN drift.** Independent review established that the current producer omitted the action operator's NOLOGIN flag even though shared/production admission already enforce it. The actual0020 manifest remained accepted after `ALTER ROLE birja_action_operator LOGIN` because the frozen role projection intentionally omits LOGIN and neither the catalogue nor ACL hashes include it.

- RED `c26ba5b` adds a real PostgreSQL regression: validate the normal manifest, enable operator LOGIN, regenerate the actual producer manifest and require validation refusal. It fails on the original producer with `LOGIN-enabled action operator admitted by actual0020 producer`. A `finally` block rolls back the experiment and explicitly restores/commits NOLOGIN even when the assertion fails.
- GREEN `9a54623` adds exactly one term to the0020-only `management_contract.unsafe` aggregate for the operator's `rolcanlogin`. Existing validation rejects nonzero unsafe counts. Frozen0017 SQL/projections and every independently pinned schema, catalogue, authority, quarantine and noACL constant remain unchanged; no fixture/hash repinning is needed.
- Final real command `env -i PATH="$PATH" HOME=/tmp python3 deploy/tests/test-portfolio-management-recovery.py --postgres-operator-login` passes. It includes the new actual LOGIN negative and all existing populated producer, normal/quarantine/noACL fingerprints, separately authenticated original replay, closed-original/key-conflict refusal and immutable before/after table/sequence equality checks.
- Final affected offline regression passes:8 source/image contracts in1.65s,6 management recovery contracts in1.79s and10 retained recovery contracts in0.42s. Unfiltered new-file Ruff/format, changed command compilation, shell syntax and diff checks pass.
- Owned `birja-p13-04` labels were checked before teardown; container/network/volume queries are empty. No review report, global planning file, dependency, provider, production or publication operation was changed. Consumer/full encrypted/TLS qualification limits above remain in force. Parent owns independent re-review.

### Repair Self-Check: PASSED

Both repair commits exist with actual RED before GREEN. The sole production change is the current unsafe-role term; the regression restores NOLOGIN in `finally`. All affected focused and actual database checks pass, and owned resources are removed.
