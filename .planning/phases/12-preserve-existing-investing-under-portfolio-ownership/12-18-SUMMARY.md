---
phase: 12-preserve-existing-investing-under-portfolio-ownership
plan: "18"
subsystem: infra
tags: [portfolio, recovery, source-provenance, tls, immutable-evidence, restricted-roles]
requires:
  - phase: 12-17
    provides: exact0017 producer/consumer and mixed-marker restore contracts
  - phase: 12-16
    provides: authenticated migration and fixed private authority inventory
provides:
  - Independent mixed-root operational oracle and exclusive hashed source snapshots
  - Exact archived retained-source dispatch and per-child source/image/config bindings
  - Immutable selected application refs with separately authenticated relocated tooling
  - Actual current0017 restricted app/scheduler verified-TLS create and compare smoke
affects: [12-21, 12-26, 12-27]
tech-stack:
  added: []
  patterns: [immutable before-backup oracle, same-archive source dispatch, complete source contexts]
key-files:
  created:
    - deploy/tests/portfolio-execution-fixture.py
    - deploy/tests/test-portfolio-fixture-contracts.py
    - deploy/tests/portfolio-retained-sources.json
    - deploy/tests/portfolio-sources.py
    - deploy/tests/portfolio-smoke.py
  modified:
    - deploy/tests/ops-fixtures.py
    - deploy/tests/selected-cutover.py
    - deploy/tests/test-ci-ops.py
    - deploy/tests/test-selected-cutover-contracts.py
    - deploy/verify-restore.py
key-decisions:
  - Retained execution consumes complete fixed-hash source payloads from the selected recovery archive rather than local latest code
  - Exact schema revisions precede retained app imports; dividend predecessor preparation declares0013 while exercise/verify declare0014
  - Selected cutover checks out complete immutable release refs and authenticates relocated control tooling separately, without synthetic commits
  - Smoke uses a verified locked cached runtime with complete frozen source copy; final Dockerfile/image scans remain Plan27
requirements-completed: []
requirements-addressed: [PFUND-03, PSAFE-03]
duration: 19 min approved continuation
completed: 2026-11-16
---

# Phase 12 Plan 18: Current and Retained Isolated Recovery Lanes

**An independent mixed-portfolio oracle, immutable archived source bindings and a real restricted-role TLS smoke make the recovery graph runnable without inventing retained-source provenance.**

## Performance and Task Commits

- Task01 committed at2026-11-16T12:44:32Z; prior execution and checkpoint are
  preserved in12-18-CONTINUATION.md.
- Approved targeted continuation: approximately13:14–13:34Z on2026-11-16.
- Tasks:2/2; application packages, dependency locks and financial SQL unchanged.
- Task01: `24d9ea9` — deterministic fixture commands and independent oracle.
- Historical handoff: `e89d699` — original incomplete runtime checkpoint.
- Task02: `a613193` — exact archive/source/image dispatch and qualified TLS smoke.

## Accomplishments

- Commands create/projection/verify/compare require explicit safe synthetic
  inputs, canonical ordered evidence and a private exclusively-created expected
  snapshot plus SHA256. Comparison never regenerates or overwrites that oracle.
  The fixed independent books preserve cash25/334/123, baselines9999/1234/7777,
  stock units8/4/4 and basis20/30/20, alongside full economic and causal rows.
- The real fixture seeds a genuine two-user global split under actual0014,
  upgrades through0015/16/17, retains the original NULL marker/digests and
  applies a new global2 split to same-owner siblings while a closed root stays
  frozen. Actual authenticated scheduler/app connections execute splits,
  crypto fill/replay, dividend payments and a held correction using verified TLS.
- Recovery archives carry fixed complete v0.5.0, v0.4.0 and v0.3.1 source
  payloads. The dispatcher checks the selected outer archive SHA and fixed inner
  payload hash before extracting/importing declared schema-specific programs.
  Complete source contexts are read-only and rechecked before child use.
- Content-addressed image ID, source label, Config and RootFS fingerprints are
  captured before use, rechecked before role/TLS/selected children and privately
  recorded beside the selected archive. Missing or conflicting previous bindings
  refuse; existing images are not retagged to manufacture provenance.
- Selected cutover no longer overlays app/Alembic bytes or creates a synthetic
  commit. Its complete clean Git ref is exactly the pinned retained release;
  relocated current control tooling has a separate immutable hash inventory.
  A private helper binds selected source, archive and qualified runtime/migrator
  image identities before each Compose child. The distinct0008/old-app rollback
  and0013/14 lanes remain explicit.

## Verification

| Gate | Result |
|---|---|
| `python3 deploy/tests/test-ci-ops.py` |20 tests pass; source/schema/blob/image/config/RootFS/archive substitutions and complete-context mutation reject |
| `python3 deploy/tests/test-portfolio-fixture-contracts.py` |5 tests pass; actual command dispatch plus approximately190 independent evidence mutations and money/marker/sequence/hash/path/overwrite negatives |
| `python3 deploy/tests/test-selected-cutover-contracts.py` |8 tests pass; branch/ref identity, preservation/refusal and owned cleanup |
| `python3 deploy/tests/test-portfolio-recovery-contracts.py` |10 affected producer/consumer contracts pass |
| `python3 deploy/tests/ops-fixtures.py --portfolio-fixture-smoke` |Actual owned PostgreSQL/TLS migration, restricted-role create, exclusive projection, verify and exact compare pass |
| Python syntax and `git diff --check` |Pass |

Synthetic-only final smoke log: `/tmp/phase12-18-retry1-final-smoke.log`.
It ends with `actual_current0017_portfolio_tls_restricted_roles=true` and
`immutable_snapshot_compare=true`. Labeled containers, networks and volumes
were removed and checked absent on success and prior failed probes.

## Deviations and Diagnosed Issues

1. **[Rule3 — Harness separation]** Added portfolio-sources.py and
   portfolio-smoke.py to keep exact source binding and owned TLS lifecycle
   separate from the retained large ops harness. Updated the existing selected
   branch contract test to expect immutable original refs rather than synthetic
   relocation commits. No production endpoint, package or financial rule added.
2. **[Rule3 — Offline smoke image]** A declared Dockerfile rebuild under
   network=none stopped at a Wolfi index fetch. The smoke therefore authenticates
   the cached approved runtime's exact installed distribution set/version against
   the locked offline export, including no extras, then copies the complete
   frozen current app/Alembic. This no-install smoke image is explicitly separate
   from the required actual Dockerfile rebuilds and strict image scans in27.
3. **[Rule1 — Synthetic evidence omission]** The previous smoke failed with
   DividendRefused. Approved continuation exposed its safe code and fixed SQL
   message: authority_unavailable / dividend target unverified or not due.
   The fixture had never supplied stock_action_state.checked_at. Adding its
   synthetic observation time made the unchanged authority pass; no SQL guard,
   expected cash, retained evidence or role permission was weakened.
4. **[Rule2 — Exact child admission]** Removed implicit retained revision defaults,
   bound source bytes to the selected archive rather than local Git, and added
   explicit0013 predecessor preparation versus0014 consumer calls. The full
   retained program bytes remain unchanged and are hashed before compilation.

The previous repair budget checkpoint was honored. The owner explicitly
approved targeted diagnosis/retry; that approval did not authorize provider,
production, package or publication changes.

## Remaining Integrated Qualification

Plan27 must run the complete serial encrypted cold restore, current/retained
source/image transition, fresh/upgraded role/TLS, selected cutover and rollback
campaign against one immutable archive. The retained images and selected lanes
are wired and contract-checked here; this plan does not claim those full real
campaigns passed. Preserve Plan17's fixed ten-signature no-ACL revocation,
quarantined grants and exact authority inventories during that campaign.

Plan26 must maintain the archive/source bindings in CI; Plans21–25/27 still own
browser consumption and complete integration. Requirements and human acceptance
remain unchecked. Plans19/20 already completed while18 was paused, so next is21.
Everything is local; unrelated.claude/ is untouched.

## Self-Check: PASSED

All five created source/test files exist, both task commits and historical
handoff exist, no source deletion occurred, and the stated command results are
recorded. No completion claim was made from offline fixture injection alone.
