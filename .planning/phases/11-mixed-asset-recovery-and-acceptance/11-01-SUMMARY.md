---
phase: 11-mixed-asset-recovery-and-acceptance
plan: "01"
subsystem: infra
tags: [deployment, recovery, postgres, compatibility, offline-contracts]
requires:
  - phase: 10-dividend-cash-and-event-history
    provides: Actual stock/dividend recovery programs and immutable authority
provides:
  - Authenticated 0014 deployment target admission before mutation
  - Separate callable populated0014 selected scenario and offline negative contracts
affects: [11-02, 11-03, 11-04]
tech-stack:
  added: []
  patterns: [Immutable source/schema admission, shared selected-host scenario]
key-files:
  created: [deploy/tests/test-deploy-compatibility.sh, deploy/tests/test-selected-cutover-contracts.py]
  modified: [deploy/deploy.sh, deploy/tests/selected-cutover.py]
key-decisions:
  - Schema0014 admits only the verified retained tested-source SHA; mutable main is resolved before admission.
  - Current0014 owner clone replay and runtime financial quarantine remain distinct from legacy0008 old-application rollback.
requirements-completed: []
duration: 7min
completed: 2026-11-13
---

# Phase 11 Plan 01: Selected Deployment Compatibility Summary

**Authenticated schema0014 deploy and rollback targets now require the retained tested source before application mutation; a separate populated0014 scenario preserves the legacy0008 lane.**

## Performance

- Started: 2026-11-13T17:30:49Z
- Completed: 2026-11-13T17:37:00Z
- Tasks: 2
- Implementation/test files: 4
- Combined final offline checks: 1.12s wall time, below the30s target.

## Accomplishments

- `admit_application_source` checks immutable resolved SHA and authenticated revision;0007–0013 retain prior compatibility. Unknown/malformed revisions and unsupported0014 targets produce `application_schema_incompatible=true`. Deploy pending-marker creation follows admission. Rollback checks admission before checkout/build/start.
- Actual `do_deploy`/`do_rollback` offline regressions cover failed-attempt tested-source recovery, legacy rollback refusal, mismatched mutable main, malformed/missing refs, unknown revisions, unchanged log/pending state, zero mutation calls and inherited lock continuity.
- `integration(archive)` retains actual v0.4.0/0008 behavior. `integration_current0014(archive)` shares setup/cleanup, keeps current app/Alembic bytes, seeds through existing real stock-runtime/dividend programs and records full canonical/authority and independent identity state before copying candidate volumes.
- The new scenario invokes the installed launcher for selected startup/current cutover, requires exact0014 state, verifies TLS owner replay in quarantined clones using existing programs, requires the intended old-runtime refusal with complete state/runtime preservation, and exercises pending-marker recovery to the tested source. Owned failure-path cleanup emits a separate0014 receipt.

## Task Commits

1. Task11-01-1 RED: `602948c` — actual pre-change `do_deploy` admitted v0.3.1 on0014 (`FAIL admitted deploy 0014 v0.3.1`, exit1).
2. Task11-01-1 GREEN: `7ddc5fc` — source/schema admission before deploy mutation.
3. Task11-01-2: `eaccf5f` — populated0014 selected scenario and offline contracts.

## Verification

- `bash deploy/tests/test-deploy-compatibility.sh`:17 actual-flow cases pass.
- `bash deploy/tests/test-rollback-target.sh`:18/18 pass.
- `bash deploy/tests/test-app-services.sh`:8/8 pass.
- `bash -n deploy/deploy.sh`: pass.
- `python3 deploy/tests/test-selected-cutover-contracts.py`:4/4 pass; dispatch/archive forwarding, exact state/authority/identity failure, intended diagnostic, clone replay/recovery orchestration and actual finally-body cleanup exercised with side-effect fakes.
- `python3 deploy/tests/test-stock-recovery-contracts.py RevisionContracts`:16/16 pass; predecessor query hashes and authority guards preserved.
- `git diff --check`: pass.

Offline tests do not establish actual current0014 restricted-service compatibility. No Docker integration was run in this plan. Plan03 must execute the real source-bound same-archive campaign after Plan02 wiring; SAFE-02 remains pending, including its current0014 compatibility clause.

## Decisions Made

Only tested-source failed-attempt recovery is supported on0014; historical application downgrade remains proven by the separate legacy0008 scenario. No override flag, financial grant expansion, schema downgrade, migration or dependency change was introduced.

## Deviations from Plan

None in implementation scope. Requirement completion is deliberately deferred despite the generic executor instruction to mark plan requirements complete: SAFE-02 spans later actual integration and review gates. Shared state progress is reconciled to real tracked plan counts rather than the SDK's historical percentage calculation.

## Threat Outcomes

- T-11-01-01: offline actual-flow guard ordering/refusal and unchanged state pass; actual installed old-runtime refusal remains Plan03.
- T-11-01-02: canonical/schema/authority/identity, owner original receipt/payment/correction replay and quarantine oracles implemented and offline exercised; actual economic equality remains Plan03.
- T-11-01-03: existing private synthetic host, fixed owned projects,180s child bound and owned cleanup preserved; finally cleanup behavior offline verified. Actual resource cleanup receipt awaits integration.
- T-11-01-SC: no installs, dependency/image changes, authority changes or security-gate changes. Final strict scans remain mandatory later.

## Issues Encountered

Local Git metadata is read-only in the default sandbox. Authorized narrowly scoped local commits succeeded through escalation. This was not treated as functional RED evidence. Unrelated `.claude/` and orchestrator state changes were preserved.

## Next Readiness

Plan02 can wire both explicit callables to the same retained archive. Plan03 must execute positive current0014 deployment, intended unsupported-old-source refusal, failed-attempt tested-source recovery, exact money/identity/authority and quarantine assertions with real services. Unknown integration failures must remain failures. Production/provider/B2/installed-host tools/timers, publication and live activation remain outside this work.

## Self-Check: PASSED

All four implementation/test paths exist. Commits602948c,7ddc5fc,eaccf5f exist on the authorized feature branch. No task commit deletes tracked files. Stub scan found no incomplete implementation placeholder; synthetic fixture records are intentional isolated inputs. No new production network/auth/schema surface was added.
