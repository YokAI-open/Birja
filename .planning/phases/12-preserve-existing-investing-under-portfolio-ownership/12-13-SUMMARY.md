---
phase: 12-preserve-existing-investing-under-portfolio-ownership
plan: "13"
subsystem: accounting
tags: [portfolio, dividends, historical-ownership, worker, concurrency, authorization]
requires:
  - phase: 12-06
    provides: entitlement-derived dividend SQL authority with active-root final validation
  - phase: 12-12
    provides: complete root journals, terminal cutoffs and scheduler-only root locking
provides:
  - Active-portfolio historical dividend eligibility and same-root supersession
  - Explicit original-root service targeting without changing retained SQL signatures
  - Active-root VERIFIED/ANCHORS worker discovery and once-only sibling processing
affects: [12-14, 12-17, 12-18, 12-27]
tech-stack:
  added: []
  patterns: [historical root reconstruction, immutable-cause target validation, active-root keyset discovery]
key-files:
  created:
    - backend/tests/test_portfolio_entitlements.py
    - backend/tests/test_portfolio_dividends.py
  modified:
    - backend/app/services/corporate_actions.py
    - backend/app/services/dividends.py
    - backend/app/tasks/dividends.py
key-decisions:
  - Derive and supersede snapshots by portfolio_id, retaining owner pairing and exact historical units
  - Keep closed-root eligibility evidence untouched and exclude closed roots before new decisions or cash effects
  - Validate the caller discovery root against the immutable cause before unchanged SQL derives and locks that root
requirements-completed: []
requirements-addressed: [PFUND-03, PSAFE-03]
duration: 12 min
completed: 2026-11-16
---

# Phase 12 Plan 13: Portfolio Entitlement Derivation and Dividend Worker Safety

**Historical root journals drive separate sibling entitlements while active-root discovery and immutable-cause checks prevent frozen or retargeted dividend effects.**

## Performance

- Started: 2026-11-16T10:47:08Z
- Verification completed: 2026-11-16T10:58Z
- Tasks: 2/2
- Files created/modified: 5
- Packages, SQL signatures, database grants and provider operations changed: none

## Accomplishments

- Entitlement snapshots now expose portfolio_id. Candidate roots come from
  historical movements, prior snapshots and holdings, then exact active Account
  identity; journal reconstruction uses the root rather than its shared user.
  Existing global instrument sequence, ex-date cutoff, calendar provenance,
  unit normalization and uncertainty rules remain intact. Snapshot versions,
  supersession and latest-result deduplication are per root. New fingerprints
  bind root/owner; no retained fingerprint or economic row is updated.
- The instrument gate precedes the existing scheduler-only root-lock routine.
  Owned INSERT guards recheck sold-out roots as well; scheduler gains no cash
  UPDATE. Full journal reconstruction still checks frozen evidence rather than
  hiding corrupt closed history. Closed roots receive no new snapshots and
  latest-verified results exclude them without changing retained snapshots.
- process_dividend and record_dividend_hold require portfolio_id. Inside their
  owned transaction, a paired active-root query validates the original
  entitlement/payment before invoking the unchanged SQL entrypoint. SQL still
  derives and locks its root, validates authority after waits and remains the
  final business statement before commit. A mismatched or closed discovery root
  refuses without another portfolio's receipt, cash or decision.
- VERIFIED and ANCHORS retain bounded deterministic keysets but join the exact
  active root and compare newer snapshots by event/root/owner. Global source
  revisions remain shared. Closed unpaid targets and paid anchors are absent
  from future worker work; immutable retained rows remain untouched.

## Task Commits

1. **12-13-01: Derive and supersede eligibility per owned root** — `3d6d809`
2. **12-13-02: Scope service invocation and worker discovery** — `5cacbc9`

## Verification

Existing locked environment only (`uv run --no-sync`, temporary uv cache).
Scoped socket access reached only the guarded disposable birja_test stack.
No provider, production, installation or live-admission operation occurred.

| Check | Result |
|---|---|
| tests/test_portfolio_entitlements.py | 8 passed |
| tests/test_portfolio_dividends.py | 13 passed |
| Combined final-source focused gate | 21 passed in56.27s,17 warnings |
| Three changed source modules, focused mypy | PASS |
| Five touched source/test files, Ruff check/format | PASS |
| git diff --check | PASS |

The real PostgreSQL suites cover distinct same-owner quantities, idempotent
snapshots, actual scheduler derivation without cash UPDATE, closed earned
eligibility, held/cancelled supersession, sales before/after the cutoff, and a
later split retaining earlier units. Service/worker tests use independent
clients over committed synthetic rows with the installed restricted roles:
six duplicate payment clients, two concurrent full worker cycles, exact sibling
cash, no crossed-root causes, invalid inputs/transaction ownership, application
denial, frozen unpaid/correction/hold exclusion, unaffordable negative correction
and concurrent crypto spending. No skipped/xfail/manual schema substitute is used.

The first expanded fixture run exposed a global revision with no replacement
sibling entitlement; the worker correctly refused to use stale evidence. The
fixture now supplies separate current-revision evidence for each active root.
A synthetic split initially had payable_date before its record_date; the
fixture dates were corrected without weakening classification or source holds.

## Deviations from Plan

None in runtime scope. The explicit service portfolio_id is checked against
the immutable cause before the original definer call; no separately supplied
owner identity or changed SQL signature is trusted. Committed worker tests reuse
the qualified0017 setup under portfolio_migration_db's guarded schema teardown,
allowing real independent connections without disabling immutable triggers.

## Known Stubs

None in the entitlement/service/worker paths delivered by this plan. Synthetic
admission and provider evidence exist only in the isolated test fixtures.

## Carry Forward

- Retained dividend fixture families still create a temporary scheduler role,
  omit required portfolio columns and invoke service helpers without the newly
  required portfolio_id. Their migration to actual0017 fixture contracts belongs
  to Plan27 full-suite integration; no whole-suite success is claimed here.
- Plan14 must scope valuation and mixed History, including original event
  hydration, to the explicit root. Plan15 still owns production router mounting
  and v1 financial refusal (including the previously recorded type call sites).
- Plans16/17 must carry the exact already-installed root-write and stock-root
  lock helper inventories from07/12; this plan adds no function or privilege.
- Complete TLS/cold recovery, coverage/security/image gates, integrated browser
  journeys and owner UI/native200% acceptance remain pending. All milestone
  requirements remain unchecked. Six Phase7 outcomes remain separately deferred
  with live stock admissions gated off.

## Self-Check: PASSED

Both task commits and all five output files exist; focused behavioral gates
pass, no unexpected file deletion occurred, and unrelated .claude/ remains
untouched. Changes are local on feature/milestone-v1.2.
