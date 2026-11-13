---
phase: 11-mixed-asset-recovery-and-acceptance
plan: "03"
subsystem: testing
tags: [postgres, recovery, tls, accounting, browser, images, security]
requires:
  - phase: 11-02
    provides: Mandatory same-archive selected lanes and acceptance matrix
provides:
  - Actual full accounting/browser/native/audit/image/dev acceptance
  - Qualified exact same-archive0007–0014 recovery and both selected compatibility lanes
affects: [11-04]
tech-stack:
  added: []
  patterns: [Source-byte-qualified affected reruns, full-field runtime snapshot comparison]
key-files:
  created: [11-LOCAL-PROOF.md, 11-DEPENDENCY-REVIEW.md]
  modified: [backend/uv.lock, deploy/tests/selected-cutover.py, deploy/tests/test-selected-cutover-contracts.py, deploy/tests/test-stock-recovery-contracts.py, deploy/tests/test-rollback-db-security.sh, deploy/tests/test-ci-ops.py, .github/workflows/ci.yml, 11-ACCEPTANCE.md, 11-VALIDATION.md]
key-decisions:
  - Retain five actual stages atfb926d8 and actual legacy lanes at22c44d6; fresh complete current0014 proof is ata7f965f, with identical archive/retained/runtime/build bytes.
  - Preserve every runtime field and duplicate row; canonicalize only CLI JSON ordering and retain full private before/after evidence.
  - Apply only the explicitly owner-approved exact OpenTelemetry1.45.2 artifact; SAFE-02/03 remain pending04.
requirements-completed: []
duration: approximately 110min
completed: 2026-11-13
---

# Phase 11 Plan 03: Actual Mixed-Asset Acceptance Summary

**Full local accounting/browser/security gates and qualified same-archive recovery prove exact mixed-asset state, restricted TLS authority, legacy0008 rollback and current0014 tested-source recovery.**

Both tasks pass. Independent Plan04 reviews and SAFE-02/03 completion remain
pending; no phase, hosted CI, production rollout or live-provider pass is claimed.

## Actual outcomes

- Backend2557/310.53s,99.87%overall; all47critical modules4565statements/
  1462branches100%; static checks pass.
- Frontend697; actual UID1000/networknone fixed-toolchain697/16.29s,98.37%
  statements/94.82%branches, static/build pass. Browser49/326.1s; sole existing
  deployed-CSPskip. Source/build/runtime/response continuity supports existing
 48d970c owner UI/native200% scope;04 must independently review it.
- Patched pip-audit clean; npm high gate passes with2low/15moderate. Five fresh
  strict including-unfixed scans0HIGH/CRITICAL. UID1001/networknone native/import/
  exact target/oversized traceparent checks, in-image5smoke, fresh19.358s and
  upgraded21.964s real dev financial authority all pass.
- Real PostgreSQL24/114.510s, CI16 and selected7 contracts pass. All six owned
  projects independently have zero containers/networks/volumes.

## Exact provenance and approved qualification

One fresh152320000byte archive:
`/tmp/birja-backup-test-phase11-final/recovery.tar`, SHA256
`1faa8277951d0c2a66ac10ffb8b39b5f85372acdacd10b3b3348126c90052cc1`.

Five real stages at `fb926d8c9605452f30e18719d239826ab7d5628a` pass:
image39.639s, retained0007–0014 452.729s, roles178.205s, populatedTLS145.445s,
freshTLS145.753s with authority parity. The full block then failed an offline
self-test. Its failed report/log remain unchanged, never promoted to success.

Actual legacy old-image100.375s and selected0008 276.057s pass at
`22c44d6e4098a8b0fa768a7d0dc542e82072b92b`. Fresh complete current0014
342.673s passes at `a7f965fe27bf3da6172f3110245ff31c3627fa12`: exact original
financial/schema/authority/identity/physical state, clone replay twice and42501,
intended unsupported-source refusal, failed-attempt tested-source recovery.

The orchestrator explicitly approved affected-only reruns after verifying only
three test-harness files differ; all386other sources,11CORE/unit archived bytes,
archive and actual runtime/build images are identical. This is a qualified
three-source proof, **not a fresh full CI-block pass at final source**.

Final receipt `/tmp/birja-phase11-gates/final-receipt.json`, SHA256
`bb90d570e6b2313f7b1fd3fc5d53cf2a6ebe558831b7f0e57a4760d16255f5af`,
contains all source maps, images, archive/tool hashes, failed/pass raw log/report
hashes and independent cleanup. Full details are in11-LOCAL-PROOF.md.

Final private before/after snapshots:
`/tmp/birja-backup-test-selected0014-evidence-p487c9dv`; both full files SHA256
`b5c4d146f2af9b56f8ce8b25079ad834cda01a53ea9824f46e28ea76f50490be`.
Raw runtime bytes differ; independent parsed records match in every field.
The earlier failed payload was not retained, so its historical cause remains
unproven; a real24sample probe independently demonstrated raw ordering variance.

## Task and correction commits

-456c911: repair strict fixture credential paths, explicit18.6→18.7 metadata
  transition and fixed clone maintenance DB; preserve all financial oracles.
-f970d90: exact owner-approved OpenTelemetry1.45.1→1.45.2 lock/artifact repair.
-fed26d8: Task1 measured application acceptance proof.
-fb926d8: actual standalone PG stack/owner prerequisites and failure-cleanup CI.
-4c2dc03: both missing-admission zero-mutation and admitted0008 failure paths.
-22c44d6: exact approved patch fingerprint; all other baseline/calendar artifacts unchanged.
-a7f965f: complete runtime-field comparison/capture and mutation regressions.
-99181c2: Task2 measured qualified recovery proof and matrix/validation update.

## Deviations and retained failures

Rules1–3 corrections above address observed fixture/CI prerequisite defects;
none changes production schema, grants, money, auth or UI. The failed browser
44/5 run showed ERR_NETWORK_CHANGED during overlapping Docker operations;
serial original five cases then full49pass, with no UI/test changes. Interrupted
backend/cache/fixture-copy attempts are separately retained as infrastructure
failures. Exact owner package approval and missing wheel-attestation limits are
in11-DEPENDENCY-REVIEW.md. Failed full/affected recovery attempts remain hashed.
The qualified rerun method is an explicitly approved execution deviation.

## Readiness and self-check

Continue only11-04 independent code/security/UI/goal reviews. Keep SAFE-02/03
unchecked until those pass; SAFE-01/live/provider, production/B2/installed tools/
timers/publication and W-debt remain deferred. No remaining local technical
blocker or implementation stub; synthetic data and offline effect fakes are
intentional test inputs. No new production threat surface or tracked deletion.

## Self-Check: PASSED

Required evidence files/receipts and all listed commits exist. Final source,
archive/11retained bytes/images, full/raw snapshot equality and zero owned
resources are independently asserted in the final receipt; whitespace passes.
