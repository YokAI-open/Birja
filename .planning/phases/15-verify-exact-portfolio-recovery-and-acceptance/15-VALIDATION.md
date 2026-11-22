---
phase: 15
slug: verify-exact-portfolio-recovery-and-acceptance
status: execution-complete-goal-review-pending
nyquist_compliant: true
wave_0_complete: true
created: 2026-11-22
---

# Phase15 — Validation Strategy

Planning contract only. No Phase15 execution or requirement completion is
claimed. The concrete nine-task map below covers all three assigned requirements.

## Test Infrastructure

Existing offline Python unittest contracts, pytest/real isolated PostgreSQL,
Vitest and Playwright. Configuration: backend/pyproject.toml,
frontend/vite.config.ts and frontend/playwright.config.ts. No installation.

Quick checks use the affected existing contract file:

- `python3 deploy/tests/test-portfolio-smoke-image.py`
- `python3 deploy/tests/test-portfolio-validation-contracts.py`
- `python3 deploy/tests/test-portfolio-fixture-contracts.py`
- `python3 deploy/tests/test-portfolio-management-recovery.py`

## Sampling and Evidence Reuse

- After a small change, run its affected contract and relevant static check.
- Before DB-bearing work, verify finite owned paths, available installed tools,
  authentic installed verifier context and current committed source bindings.
- Use one serial isolated test lane. Never use real .env, provider calls,
  production services, or financial result substitutions.
- Produce one fresh matching Phase15 archive when archived inputs change;
  preserve the existing Phase12/13/14 archives and failed-run history.
- Run affected current restore and original-request retry assertions once.
  Compare exact financial data before business replay; after replay compare
  finances, identities and effect counts without resetting consumed sequences.
- Reuse valid inherited migration, backend/frontend/browser, legacy recovery,
  roles/TLS, image and owner evidence only with explicit unchanged-input scope.
  Rerun components invalidated by a change; do not repeat unrelated campaigns.
- Keep the normal complete CI graph executable. Full required CI must pass
  before merge; local component results are not a hosted-CI or whole-run pass.
- Target quick offline feedback in seconds; actual database/restore exceptions
  use measured receipts, not invented deadlines or automatic whole-suite retries.

## Requirement Coverage

| Requirement | Coverage to inherit | Remaining check |
|---|---|---|
| PSAFE-04 | Phase14 exact current/retained cold restores and frozen-state oracle | Genuine restored original creation/fill/payment retries; matching installed verifier |
| PSAFE-05 | Existing migration/custom-baseline, TLS and rollback/refusal evidence | Reproducible supported runner, finite Phase15 paths and operator support matrix |
| PSAFE-06 | Real lifecycle concurrency/browser suites, strict coverage/image gates and owner approvals | Source-bound complete lifecycle acceptance map and only affected checks |

## Per-Task Verification Map

| Task | Wave | Requirement | Threat | Behavior | Automated command / entrypoint | Existing / created | Result |
|---|---|---|---|---|---|---|---|
|15-01-01|1|PSAFE-04/05/06|T-15-01|Actual installed verifier/source lifetime|`python3 deploy/tests/test-portfolio-smoke-image.py`|Existing; task adds context contracts|PASS25smoke contracts5.911s;c640789;15-01-SUMMARY|
|15-01-02|1|PSAFE-04/05/06|T-15-01-OWN|Finite outputs; distinct current-only/full result|`python3 deploy/tests/test-portfolio-validation-contracts.py`|Existing; task creates phase/suite contracts before use|PASS38validation contracts8.810s;3ddc579;15-01-SUMMARY|
|15-01-03|1|PSAFE-04/05/06|T-15-01-OWN|Immutable request phase/suite propagation and read-only status|same existing validation contracts|Existing; task adds worker/status cases|PASS42supervisor contracts9.037s;966c10c; later43preflight contracts10.233s;15-03proof|
|15-02-01|2|PSAFE-04/06|T-15-02|Genuine active fill and independent31/24oracle|`python3 deploy/tests/test-portfolio-management-recovery.py --write-current-fixture`, then fixture/management offline groups|Task creates finite writer; real owned PostgreSQL exception|PASS actual_postgres/owned_resources_clean;8dd790b;12fixture/11management contracts5.756/16.138s;15-02-SUMMARY|
|15-02-02|2|PSAFE-04/06|T-15-02-FROZEN|Restored-only real original retries after exact compare|`python3 deploy/tests/test-portfolio-management-recovery.py && python3 deploy/tests/test-portfolio-smoke-image.py`|Task creates replay-restored mode/wiring contracts; actual proof03|PASS14management/25smoke contracts16.286/6.295s;1109d25; final adapter groups15.198/6.246s; real R5replay below|
|15-03-01|3|PSAFE-04/05/06|T-15-03|Reviewed unchanged-input reuse and finite proof selection|`python3 deploy/tests/run-portfolio-validation.py --phase 15 --suite recovery-current --dry-run`|New suite created01; review/hash ledger also required|PASS dry-run; exact input/raw-log/hash reuse at6d7ee7f;7206ddc+repair associations;15-EVIDENCE-REUSE|
|15-03-02|3|PSAFE-04/05/06|T-15-03-R|Actual encrypted current cold restore/retries/authority/images/cleanup|Supported phase15 recovery-current campaign; original status must be passed/exit0, strict scans on exact IDs|01supported supervisor;02assertions; one fresh matching archive|PASS supportedR5exit0/135.998s, actual31/24restore/replay,139preflight,5strict scans41.220s and empty cleanup;15-RECOVERY-PROOF|
|15-04-01|4|PSAFE-04/05/06|T-15-04|Tested support/refusal matrix matches real interfaces|Same finite dry-run and source/reference checks|Existing RUNBOOK updated by task; no live operation|PASS actual finite dry-run exit0, source/support matrix references and diffcheck;b092abc|
|15-04-02|4|PSAFE-04/05/06|T-15-04-E|Actual28requirement/full-lifecycle evidence and honest gate status|`git diff --check`; direct source/receipt comparison and final independent goal verification|Task creates acceptance/security/UI disposition records|PASS28/28assertion rows,4outcomes,9task results, raw receipt/reference and diff checks;15-ACCEPTANCE; independent goal review next|

Task15-03-02 terminal check is explicitly defined in its plan; a still-running
status or launch exit0 is not proof of completion. Task15-02-01 creates its
writer before invocation and runs it once, not on every later format check.
The affected code paths are covered by existing framework groups; there are no
three consecutive tasks without an automated check or uncreated scaffold used
as passing evidence. Documentation-only tasks use source/reference/diff checks
rather than tests mirroring documentation.

## Wave0 Requirements

Existing infrastructure covers this phase. Tasks create only the missing
installed-context/finite-output contracts and restored-retry assertions, before
using them. No new framework, dependency, schema or product screen is planned.

## Manual Verification

Existing Phase12/13/14 actual UI/native200 outcomes may be reused for unchanged
surfaces with provenance. Ask only for affected outcomes if an interaction
actually changes. Do not generate a new approval gate for unchanged screens.

## Sign-Off

Execution sampling complete: nine tasks have concrete results, existing framework
and creation-before-use contracts. The finite real writer and actual R5encrypted
proof are distinct; dry-runs/contracts are not relabelled financial results.
All missing cases were implemented by01/02before use; no Wave0installation.

Source-aware reuse:277backend/155frontend/314browser/139authority/10policy inputs,
28security/sixrecovery raw log hashes and365render inputs match the qualified
scope. Reused literal coverage gates are80%overall/100%critical; actual64critical
modules100%, backend99.87%, frontend96.43%. New exact five-image scans pass.
Actual owner UI/native200 outcomes remain valid for unchanged surfaces.

R1–R4failed receipts and historical whole-run failures remain failed. R5current
component flags whole7=false/same_archive_final_ci=false; no fresh complete
security/browser/seven-stage or hostedCI pass is claimed. Full required CI must
pass before merge. Issue35scope/expiry and Phase7live deferral are unchanged.

Validation mapping/compliance is complete locally; final independent goal review
and global requirement advancement belong to the orchestrator. No new human
interview, provider/production operation or milestone archival was performed.
