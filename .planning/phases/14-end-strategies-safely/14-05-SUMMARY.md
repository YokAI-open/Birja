---
phase: 14-end-strategies-safely
plan: "05"
subsystem: recovery-producer
tags: [postgresql, recovery, lifecycle, immutable-source, oracle]
requires:
  - phase: 14-04
    provides: Explicit0023 catalogue, final/default ACL and bootstrap-only quarantine contracts
provides:
  - Fixed complete qualified0020 source lane without current service overlay
  - Current31-table24-identity causal fixture and before-backup oracle
  - Explicit V3 producer, source inventory and package family
  - Actual PostgreSQL producer/authority negatives and authoritative dumped identity tails
affects: [14-06, 14-07, 14-15, 14-16, 14-18]
tech-stack:
  added: []
  patterns:
    - Reviewed authority/source pins precede executable imports and packaging
    - Retained family tests execute the authenticated complete historical source
    - Independent immutable snapshots compare every financial/lifecycle/sequence byte
key-files:
  created:
    - deploy/tests/portfolio-closure-recovery-fixture.py
    - deploy/tests/fixtures/portfolio-recovery-0023.json
  modified:
    - deploy/tests/portfolio-retained-sources.json
    - deploy/tests/portfolio-sources.py
    - deploy/tests/test-portfolio-fixture-contracts.py
    - deploy/backup-snapshot.py
    - deploy/tests/test-portfolio-recovery-contracts.py
    - deploy/tests/test-portfolio-management-recovery.py
key-decisions:
  - Current payloadV3/revision0023 uses recovery_profile deploy-recovery-v4; V1/V2 remain distinct historical families.
  - The new fixture JSON is a format3 wrapper containing manifest, quarantined and projection.
  - Initial fixture closure uses the real complete-proof service; actual public DELETE remains07/09/17.
requirements-completed: []
requirements-progress: [PMGT-04, PFIN-05, PSAFE-01]
duration: 27min measured first-RED-to-cleanup-receipt interval
completed: 2026-11-19
---

# Phase 14 Plan 05: Complete Closure Recovery Producer Summary

**The explicit successor producer captures retained closure outcomes and causal
finances while authenticating fixed historical source and all24 identity tails.**

## Task commits and measured scope

| Task | Commit | Result |
|---|---|---|
|1 RED|d3a7197|Missing0023 source dispatch fails before implementation|
|1 GREEN|d36f584|Fixed complete0020 lane/current fixture, actual producer/causal oracle and manifest prerequisite|
|2 GREEN|7c34c28|Explicit V3 package/inventory, mandatory source/evidence negatives and final qualification|

First RED was2026-11-19T10:45:49UTC; cleanup/evidence receipt was captured
at11:12:46UTC. This27-minute interval includes implementation and bounded
diagnostics; it is not a short task-feedback promise. No STATE/ROADMAP or
whole-requirement checkbox was changed by this executor.

## Implemented contracts

- Added immutable complete0020source
  `9527e358bc6953cec7580043703324db194ba396`, source archive SHA256
  `2ecec604674c7b18ef864b32883b9a6f67d42f9a3080b949b6e126dd47810291`.
  The complete tree is authenticated before old generator import. The old
  generator imports its own qualified producer, never a current service overlay.
  Complete0017source4b4320b and0007–0014 lanes remain unchanged.
- Current profile is0023/payload3 with a separate fixture. Existing image-binding
  checks are retained; an existing campaign record with a missing image alias
  refuses rather than rebuilding an equivalent image. The regression asserts
  no Docker build is invoked in that state.
- The new fixture creates five independently funded roots with two initialized
  user identities. It retains a sold-out stock and a held second stock, an active
  sibling, mixed crypto holdings, a crypto-only closed book, an empty closed book
  and a user with zero active roots. Its independent expected cash/baselines,
  global closure boundaries and complete table/sequence snapshot are captured
  before backup; they are not reconstructed from restored data.
- Declared historical opening/sale/announcement/entitlement inputs obey current
  instrument locks and immutable lineage. Actual crypto fills, dividend payments,
  an uncertain held correction and terminal closure use real services/authority,
  including complete same-transaction closure proof. Earned unpaid entitlements,
  four closed and one refused immutable outcomes are retained. Public HTTP DELETE
  does not exist yet; this is not public-deletion acceptance.
- V3 inventories every required lifecycle/model/migration/SQL/helper/source file.
  Fifteen explicit reviewed source pins authenticate critical source before
  authority import. Every payload member is required; version/revision changes,
  omissions and coherently altered critical source refuse. V1/V2 inventory
  declarations and legacy manifest SQL bytes are not reinterpreted as V3.
- Current manifest has31table hashes,24 authoritative identity states, lifecycle
  counters/linkage/provenance, full schema/authority fingerprints and separate
  exact catalogue/object/effective-default ACL contracts. Invalid global stock
  boundaries and jointly corrupted retained confirmation names refuse. The
  no-ACL quarantine is separately pinned and still requires private future
  defaults; it cannot pass ordinary runtime validation.
- `bundle-v3` produces payload3/revision0023 and `deploy-recovery-v4`, with all
  five complete retained source archives. Package metadata, source payloads and
  current bytes are checked independently. The consumer remains Plan06 work.

## Actual verification and limits

Raw evidence: `/tmp/birja-phase14-plan05/receipt.json` and adjacent logs.
Final qualified source is7c34c28; summary-only changes follow it.

| Check | Actual result |
|---|---|
|Fixture/source/oracle contracts|12passed5.237s; every table/sequence mutation, omission, source dispatch and lost image binding covered|
|Recovery producer contracts|14passed1.364s; mandatory inventory, exact normal/quarantine manifests, coherent source/schema/ACL mutations and pre-import refusal|
|Package and retained-family contracts|9passed12.039s: one current V3 package transport test plus8 complete fixed0020 producer/consumer contracts|
|Actual owned PostgreSQL proof|Passed7.19s: real fills/dividends/hold/closure, full31-table/24-tail oracle, actual catalogue/ACL/default and retained-name corruption refusals|
|Actual dump identity extraction|All24states from custom pg_dump→pg_restore extraction equal the before-backup oracle; uses the same extraction family as the producer|
|Static checks|Six touched Python files pass scopedF/E9; new fixture passes Ruff formatting; producer/fixture/dispatcher compile; git diff check passes|
|Historical bytes|No backend app/migration or fixed0017/0020 fixture bytes changed from309bdd9|
|Owned cleanup|Allbirja-p14-05 containers/networks/volumes removed; project-label queries empty|

The package test mocks only external registry/image transport and runtime
metadata; it proves package assembly/inventory/source binding, not encryption,
cold restore, real registry verification or TLS. The actual PostgreSQL proof is
a logical producer/causal/identity proof, not a restore or verified-TLS claim.
The35offline test cases are not reported as35real PostgreSQL cases.

Qualified Phase13archive `/tmp/birja-phase13-proof/recovery.tar.gz` is untouched
and its SHA256 is still
`6fb79a45ddcb10725b18fc756e71bd555c827a6e61a5a4a0bd2d183096114b92`.
No canonical Phase14 campaign archive was created. Temporary mocked package
artifacts were removed by their owned temporary-directory contexts.

## Deviations and corrected diagnostics

1. **Rule3 — manifest prerequisite ordering.** The explicit successor manifest
   and source-pin core moved into Task1 because the real current fixture/oracle
   needs that interface. Task2 still owns package/inventory qualification. This
   adds no schema or feature beyond the approved plan.
2. **Rule1 — offline generator import.** Code generation initially executed
   backend helper imports under system Python. It now embeds authenticated helper
   source without backend import before the child's source/revision gate.
3. Synthetic openings required the newly enforced sorted instrument gates;
   their typed SQL parameters were corrected. No financial guard was bypassed.
   A first direct pg_dump sequence-selection experiment omitted identity-owned
   states; the final proof uses the actual producer's custom-dump/pg_restore
   extraction and verifies all24, not a weakened parser.
4. Existing0020 contracts now load complete qualified source in a private tree.
   Fixed Git object reads are served from the repository object database; all
   executable files remain the authenticated historical bytes. This avoids
   weakening source pins merely because current bootstrap implementation changed.

Initial failed diagnostic logs are not presented as passing qualification.
No package/dependency, provider, production, publication or authentication gate
occurred. No blocking stub remains in the producer/fixture scope.

## Plan06 and later handoff

- Explicit producer APIs: `closure_payload_inventory`, `verify_closure_inventory`,
  `closure_bootstrap`, `require_closure_source`, `closure_manifest_sql`,
  `validate_closure_manifest`, `bundle_package_v3` and CLI`bundle-v3`.
- Consumer must explicitly admit payload3/revision0023/`deploy-recovery-v4`,
  all new source pins/member paths and five retained source archives. Do not
  widen oldV1/V2 interpretation or run current services on retained0020.
- New source fixture JSON is `{"format":3,"manifest":...,"quarantined":...,
  "projection":...}`. The standalone immutable oracle uses the projection;
  producer/consumer positives use the matching manifest, with exact phase4
  quarantine→regrant and private-default handling before runtime admission.
- Later legitimate edits to pinned source require deliberate reviewed pin refresh
  and affected verification, never runtime hash adoption or disabling checks.
- Public DELETE must still replace the early service-only fixture route in
  integrated07/09/17 acceptance. Same-archive encrypted/cold/TLS, safe rollback,
  critical/full security and new human UI/native200 gates remain06/15–19.

## Self-Check: PASSED

All eight declared source/test/fixture paths exist, all three task commits exist,
static/historical guards pass and owned cleanup is recorded. Working tree has
only the unrelated pre-existing`.claude/` after this summary commit. All whole
requirements remain pending; independent Plan05 review precedes Plan06.
