---
phase: 12-preserve-existing-investing-under-portfolio-ownership
plan: "06"
subsystem: database
tags: [postgresql, dividend-authority, portfolio, immutable-evidence, authorization]
requires:
  - phase: 12-04
    provides: migration-only0015/16 associations and authenticated test prerequisites
  - phase: 12-03
    provides: root-paired dividend model and correction-chain contract
provides:
  - Static0017 dividend authority companion with retained signatures and entitlement-derived root
  - Active-root payment/correction/hold locks and exact root-bound cash mutation
  - Eighteen collected final SQL scenarios and four passing static contracts
affects: [12-07, 12-13, 12-16, 12-17, 12-27]
tech-stack:
  added: []
  patterns: [fixed versioned SQL companion, entitlement-derived root, same-root immutable correction chain]
key-files:
  created:
    - backend/tests/test_portfolio_dividend_authority.py
    - backend/alembic/sql/0017_dividend_portfolio.sql
  modified: []
key-decisions:
  - Keep existing routine signatures and derive portfolio entirely from retained entitlement/payment
  - Lock instrument then exact active root before replay or economic mutation, including earned unpaid work
  - Keep final retained authority validation last and qualify real SQL only after actual0017
requirements-completed: []
requirements-addressed: [PFUND-03, PSAFE-03]
duration: 10 min
completed: 2026-11-16
---

# Phase 12 Plan 06: Versioned Root-Aware Dividend SQL Authority

**Entitlement-derived dividend authority binds cash and correction ancestry to one active portfolio while retaining the original signatures, rounding and held-decision semantics.**

## Performance

- Started: 2026-11-16T09:00Z
- Focused verification/commits completed: 2026-11-16T09:09:50Z
- Tasks: 2/2
- Files created: 2
- New packages, runtime SQL installation, provider and production actions: none

## Accomplishments

- Added real final-schema fixture setup for sibling portfolios sharing an owner
  and event, plus a foreign owner. Business operations assume installed narrow
  scheduler/app roles; fixture creates no functions or permissions and requires
  actual Alembic0017. All synthetic evidence rolls back after each case.
- Eighteen collected SQL scenarios cover independent once-only payments, exact
  original/correction/affordability cash math, immutable causal records,
  cross-root entitlement/payment tuples and direct restricted-role denials.
  Closed portfolios refuse earned unpaid payments, corrections and uncertain
  holds before any mutation or old-result replay.
- Static companion preserves the retained0014 rights/calendar/freshness/terms,
  historical ownership, uncertainty, numeric range and half-even rounding
  checks. Only owned historical quantity/latest-entitlement/decision chains and
  the account lock/payment lookup/cash update acquire portfolio predicates;
  instrument sequence and shared market evidence remain global.
- Root is derived from entitlement/payment, not an added caller root argument.
  Both definers retain instrument-advisory-lock then exact active-root lock
  ordering. Final authority snapshot includes root identity/owner/closure, with
  no additional table reads after its clock sample or after final validation.
- Public and app access to the fixed scheduler entrypoints/private helper is
  explicitly revoked; only apply/hold receive scheduler EXECUTE. Scheduler has
  no direct cash or accounting-row writes/sequence usage. Function owners and
  protected search paths stay exact. Previous applied decisions require the
  same portfolio as the new decision as well as payment/user/event identity.

## Task Commits

1. **12-06-01: Create root payment/correction and freeze authority proofs** — `b414b26`
2. **12-06-02: Write immutable entitled-root dividend SQL asset** — `9a19420`

## Verification

| Command | Result |
|---|---|
| `uv run --no-sync pytest tests/test_portfolio_dividend_authority.py --collect-only -q` | 22 cases collect:18 final_sql and4 static contracts |
| `uv run --no-sync pytest tests/test_portfolio_dividend_authority.py -q -k asset_contract` | 4 passed,18 deselected |
| Ruff check/format for the new test module | PASS |
| `git diff --check` | PASS |

The existing locked virtualenv was used with a temporary uv cache. The initial
static run hit the sandbox socket restriction in the existing autouse test
bootstrap; the scoped retry accessed only guarded localhost birja_test. No
package installation or final-schema test ran. Static tests compare retained
source refusal outcomes and independent money/market expressions, exact routine
inventory/signatures/owners/grants, paired root predicates and final-statement
ordering. They are not PostgreSQL runtime or verified-TLS evidence.

## Deviations from Plan

None. Additional direct-owner tuple and routine-security scenarios strengthen
the assigned adversarial matrix within the same two creation files. Guarded
local pytest transport remains distinct from verified-TLS ops proof in16/18/27.

## Known Stubs

None. The uninstalled SQL companion and collected final_sql tests are deliberate
Plan07 inputs, not simulated passing runtime implementation.

## User Setup Required

None.

## Next Plan Readiness

- Plan07 must install this exact static asset after the final paired constraints
  and unconditional immutable guards exist; signatures remain unchanged.
- It must execute all18 final_sql cases under actual0017 and retain all old
  accounting guards, global evidence and exact economics. Role bootstrap must
  provide the reviewed runtime permissions rather than tests fabricating them.
- Final SQL, role/TLS, services, exact cold restore, strict full coverage/security/
  images and human UI/native200% proofs remain pending. No milestone requirement
  is completed by collection/static validation. Phase7 deferrals and activation
  gates are unchanged; no publication or production action occurred.

## Self-Check: PASSED

Both creation files exist, and task commitsb414b26/9a19420 exist on
feature/milestone-v1.2. Four static contracts pass and22 cases collect without
skips/xfails or fabricated0017 schema. Unrelated .claude/ remains untouched.
