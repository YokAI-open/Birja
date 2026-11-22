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
claimed. The planner must populate the final per-task map from its actual tasks.

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

Pending the planner's concrete tasks. Every task must map to an existing
automated selector, or to a new bounded test explicitly created by that task
before execution. No missing command or test stub is accepted as passing.

## Wave0 Requirements

Existing infrastructure covers this phase. Tasks create only the missing
installed-context/finite-output contracts and restored-retry assertions, before
using them. No new framework, dependency, schema or product screen is planned.

## Manual Verification

Existing Phase12/13/14 actual UI/native200 outcomes may be reused for unchanged
surfaces with provenance. Ask only for affected outcomes if an interaction
actually changes. Do not generate a new approval gate for unchanged screens.

## Sign-Off

Pending checked plans and later actual execution. Final plan/task mapping,
source-aware reuse ledger, actual restore receipts, required reviews and
independent goal verification are needed before setting compliance complete.
