---
phase: 15
slug: verify-exact-portfolio-recovery-and-acceptance
status: draft
nyquist_compliant: false
wave_0_complete: false
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
|15-01-01|1|PSAFE-04/05/06|T-15-01|Actual installed verifier/source lifetime|`python3 deploy/tests/test-portfolio-smoke-image.py`|Existing; task adds context contracts|pending|
|15-01-02|1|PSAFE-04/05/06|T-15-01-OWN|Finite outputs; distinct current-only/full result|`python3 deploy/tests/test-portfolio-validation-contracts.py`|Existing; task creates phase/suite contracts before use|pending|
|15-01-03|1|PSAFE-04/05/06|T-15-01-OWN|Immutable request phase/suite propagation and read-only status|same existing validation contracts|Existing; task adds worker/status cases|pending|
|15-02-01|2|PSAFE-04/06|T-15-02|Genuine active fill and independent31/24oracle|`python3 deploy/tests/test-portfolio-management-recovery.py --write-current-fixture`, then fixture/management offline groups|Task creates finite writer; real owned PostgreSQL exception|pending|
|15-02-02|2|PSAFE-04/06|T-15-02-FROZEN|Restored-only real original retries after exact compare|`python3 deploy/tests/test-portfolio-management-recovery.py && python3 deploy/tests/test-portfolio-smoke-image.py`|Task creates replay-restored mode/wiring contracts; actual proof03|pending|
|15-03-01|3|PSAFE-04/05/06|T-15-03|Reviewed unchanged-input reuse and finite proof selection|`python3 deploy/tests/run-portfolio-validation.py --phase 15 --suite recovery-current --dry-run`|New suite created01; review/hash ledger also required|pending|
|15-03-02|3|PSAFE-04/05/06|T-15-03-R|Actual encrypted current cold restore/retries/authority/images/cleanup|Supported phase15 recovery-current campaign; original status must be passed/exit0, strict scans on exact IDs|01supported supervisor;02assertions; one fresh matching archive|pending|
|15-04-01|4|PSAFE-04/05/06|T-15-04|Tested support/refusal matrix matches real interfaces|Same finite dry-run and source/reference checks|Existing RUNBOOK updated by task; no live operation|pending|
|15-04-02|4|PSAFE-04/05/06|T-15-04-E|Actual28requirement/full-lifecycle evidence and honest gate status|`git diff --check`; direct source/receipt comparison and final independent goal verification|Task creates acceptance/security/UI disposition records|pending|

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

The planning map is complete: four serial dependency waves, nine concrete
tasks, existing frameworks and explicit creation owners for missing cases.
Independent plan checking and later actual execution remain pending. Do not
set nyquist_compliant/wave_0_complete or task results green from planning alone.
Source-aware reuse, actual restore receipts, required reviews and independent
goal verification remain execution prerequisites. No hosted CI or human result
is invented; actual unchanged12/13/14owner outcomes have explicit provenance.
