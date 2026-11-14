---
phase: 11-mixed-asset-recovery-and-acceptance
plan: "02"
subsystem: testing
tags: [ci, recovery, compatibility, acceptance]
requires:
  - phase: 11-01
    provides: Separate legacy0008/current0014 selected scenarios
provides:
  - Mandatory serial same-archive selected lanes with failure/omission mutations
  - Twenty-seven recovery, money, browser and gate acceptance mappings
affects: [11-03, 11-04]
tech-stack:
  added: []
  patterns: [Actual AST dispatch with effect fakes, source-attributed acceptance matrix]
key-files:
  created: [.planning/phases/11-mixed-asset-recovery-and-acceptance/11-ACCEPTANCE.md]
  modified: [deploy/tests/test-rollback-db-security.sh, deploy/tests/test-ci-ops.py, .github/workflows/ci.yml]
key-decisions:
  - Current0014 and legacy0008 selected scenarios share the unchanged explicit recovery archive.
  - SAFE-02/03 remain pending actual Plan03 gates and Plan04 review.
requirements-completed: []
duration: 7min
completed: 2026-11-13
---

# Phase 11 Plan 02: Mandatory Compatibility and Acceptance Oracles Summary

**Required CI now invokes both selected lanes with the identical archive, and a27-row matrix binds recovery, money and browser clauses to independent existing oracles.**

## Performance and task commits

- Tasks:2; implementation/evidence files:4; approximately7minutes.
- Task11-02-1: `96834e9` — Require both selected recovery lanes in CI.
- Task11-02-2: `1dd1147` — Map mixed-asset acceptance to exact oracles.
- Metadata commit follows this summary.

## Verification

Actual final offline source `96834e9f566530dbff377cf1d09de8123d4b74b0`:

- `python3 deploy/tests/test-ci-ops.py`:15tests pass,0.601s.
- `python3 deploy/tests/test-selected-cutover-contracts.py`:4tests pass,0.189s.
- `bash deploy/tests/test-deploy-compatibility.sh`:17cases pass,0.560s.
- Total1.350s; under30s target. `bash -n` runner and `git diff --check` pass.
- Private receipt `/tmp/birja-phase11-02-offline-1xneg7zh/receipt.json`,SHA256
  `033d8133833cc5b0c8dc2e3a1b684fb663889cf3c7b0afa57554f477f5787bb9`.
  Exact five file hashes and three log paths/hashes are in that receipt and
  the acceptance inventory. No private log contents were copied publicly.

The actual default runner AST is compiled/executed with effect fakes. Seven
mutations remove either lane, replace either archive argument, reorder calls or
swallow either selected failure; all reject. Each of four stage failures must
propagate and stop later dispatch. Existing extracted CI-block compilation and
stage/integrity omission checks remain. Additional mutations remove every fixed
critical module, branch/overall/critical thresholds, audits or required aggregate
jobs/failure/cancel/skip rejection. Existing five strict image policy mutations,
browser isolation and owned cleanup assertions remain.

No Docker integration, actual new image build/scan, financial/browser suite or
current0014 selected pass was claimed. The45min ops timeout is unchanged;
Plan03 must assess measured extra0014 duration before any timeout adjustment.

## Acceptance inventory

R01–R07 map all SAFE-02/criterion1 clauses; F01–F09 map criterion2 races,
waits/expiry, cutoff/revision/split/uncertainty and exact cash/count/identity
assertions; B01–B06/G01–G05 map criterion3 complete browser journeys and gates.
The matrix separates actual service effects, synthetic external authority and
read-only presentation, owner clone replay and42501 runtime quarantine.
Historical2557/697/49+one deployed-CSPskip and1391.017s retain their Phase10
source/image/archive attribution. New real results remain PENDING.

No concrete uncovered financial/browser oracle was found. The selected0014
execution gap remains pending Plan03 despite its implemented/wired scenario.
Historical0008 downgrade rollback cannot satisfy it. UI6/6 contract approval
is distinct from owner execution acceptance. Source comparison to48d970c finds
only operator/CI/harness changes; final build/runtime/served-response continuity
must be assessed before scoped UI/native200% reuse. SAFE-01/live/provider,
production/B2/private.env/installed tools/timers/publication/W-debt exclusions
are preserved. No new package, schema, grant or product UI was introduced.

## Deviations from Plan

No implementation deviation. As in Plan01, generic requirement-completion
instructions are deferred because SAFE-02/03 explicitly require Plans03/04.
SDK state progress is reconciled to actual61/64 tracked plans and3/5 phases;
its handlers rejected documented positional arguments; named metric/session flags
worked while progress metadata is corrected directly. Local Git writes require sandbox
escalation; authorized scoped commits retain normal hooks. Missing optional
`/usr/bin/time` was replaced with shell/Python monotonic timing, no installation.

## Threat outcomes and stubs

T-11-02-01 is covered by actual dispatch and CI omission/failure mutations;
actual service proof awaits03. T-11-02-02 is covered by pending/historical/actual
identity separation and safe summaries. T-11-02-SC preserves all existing audits,
coverage and strict image gates. Stub scan found no incomplete implementation;
PENDING evidence entries are intentional future execution fields, not passed
requirements. No new network/auth/file-trust/schema surface was introduced.

## Next readiness

Execute only Plan03 next: source-frozen actual DB/browser/native/security gates
and one serial same-archive recovery campaign with distinct current0014 positive,
unsupported-target refusal and supported failed-attempt recovery receipts.
SAFE-02/03 and final review remain pending. No push/PR/merge/deployment authorized.

## Self-Check: PASSED

All four task files and this summary exist; commits96834e9 and1dd1147 exist on
the authorized feature branch. Task commits delete no tracked files. Unrelated
untracked `.claude/` is preserved; no generated repository files were added.
