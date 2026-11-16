---
phase: 12-preserve-existing-investing-under-portfolio-ownership
plan: "03"
subsystem: database
tags: [sqlalchemy, stock-lineage, dividends, ownership, immutable-evidence]
requires:
  - phase: 12-01
    provides: guarded migration fixtures and final SQL scenario foundation
  - phase: 12-02
    provides: paired account/trade root keys and core ownership metadata
provides:
  - Paired portfolio ownership on stock facts, movements and dividend entitlements
  - Global split applications with persisted nullable SMALLINT digest interpretation
  - Immutable terminal portfolio-stock closure model and per-root split movement uniqueness
  - Root-preserving entitlement, payment and correction predecessor tuples
affects: [12-04, 12-05, 12-06, 12-07, 12-12, 12-13, 12-17, 12-27]
tech-stack:
  added: []
  patterns: [paired causal ForeignKeyConstraint, global event with owned effects, terminal journal boundary]
key-files:
  created: []
  modified:
    - backend/app/models/stock_execution.py
    - backend/app/models/corporate_action.py
    - backend/app/models/dividend.py
    - backend/tests/test_portfolio_ownership.py
    - backend/tests/test_portfolio_authority.py
key-decisions:
  - Split applications and instrument sequence/unit epochs remain global; only their movements are portfolio-owned
  - Digest interpretation is nullable SMALLINT with no default; NULL is retained v1 and explicit2 is the new interpretation
  - Dividend causal tuples include the same root and owner through entitlement, payment and correction predecessors
requirements-completed: []
requirements-addressed: [PFUND-03, PSAFE-03]
duration: 7 min
completed: 2026-11-16
---

# Phase 12 Plan 03: Stock and Dividend Ownership Lineage Models

**Owned stock and dividend metadata keeps financial causes inside one portfolio while shared split applications and market epochs remain global.**

## Performance

- Started: 2026-11-16T08:21Z
- Task verification/commits completed: 2026-11-16T08:27:39Z
- Tasks: 2/2
- Files modified: 5
- Packages, migrations and runtime services changed: none

## Accomplishments

- StockFillFacts and StockOwnershipMovement carry required portfolio_id with a
  paired Account(id,user_id) FK. Their trade cause includes the identical root,
  coin and owner rather than independently valid references.
- Split movement uniqueness is(application_id,portfolio_id); the causal key is
  root-specific while instrument sequence remains globally unique. Existing
  application/coin/unit cause FK and original economic fields remain intact.
- StockSplitApplication remains global with unchanged economic_event_id
  uniqueness and(id,coin_id,new_unit_epoch) candidate key. The new nullable
  SMALLINT owner_digest_version has neither Python nor server default and a
  CHECK allowing only NULL or2. No user/root columns were added to applications.
- PortfolioStockClosure declares the approved identity, owned root, stock coin,
  UTC closure timestamp, terminal sequence/unit epoch and unique root/coin key.
  Nonnegative safe sequence/epoch checks permit active siblings to advance
  global instrument state without rewriting the terminal boundary.
- Entitlements pair root/owner and keep supersession within the same
  event/root/owner. Payment once-only uniqueness is event/portfolio. Payment and
  correction decisions include root in entitlement, payment and predecessor
  tuples, while event/coin and revision/fingerprint constraints stay present.
- Focused metadata cases resolve each dividend FK to an actual target unique
  candidate key and inspect exact ownership/default/global/terminal contracts.
  New final_sql cases collect for forged closure ownership, unsupported/missing
  new split markers and cross-sibling entitlement supersession.

## Task Commits

| Task | Commit | Result |
|---|---|---|
| 12-03-01 | 61b71e0 | Owned stock causes, global digest marker, terminal boundary and metadata/SQL scenario declarations |
| 12-03-02 | 332917e | Root-preserving dividend payment/decision chains and metadata/supersession scenarios |

## Verification

Used existing locked tools with UV_CACHE_DIR=/tmp/birja-uv-cache and
uv run --no-sync; no installation or lockfile change.

| Check | Result |
|---|---|
| test_portfolio_ownership.py -q -k model_metadata | 16 passed,17 deselected in0.80s |
| test_portfolio_authority.py -q -k model_metadata | 5 passed,6 deselected in0.77s |
| Both ownership/authority files --collect-only -q | 44 collected in0.62s |
| Ruff check on all five modified files | Passed |
| Ruff formatting and git diff --check | Passed |

The default sandbox denied the existing autouse disposable-database
prerequisite's socket; scoped escalation passed. Metadata assertions themselves
use no database session. No final_sql case was executed and no runnable schema,
economic preservation, immutable trigger/ACL or worker behavior is claimed.

## Decisions and Deviations

Executed the approved coordinated metadata-only slice. No architectural
deviation or dependency was needed. The terminal class lives in
corporate_action.py and is registered when that existing module loads; it needs
no package export change. Entitlement coin consistency is inherited through its
event and the existing payment event/coin FK; no additional economic column was
introduced. Composite FK semantics follow the official
[SQLAlchemy2.0 constraints documentation](https://docs.sqlalchemy.org/en/20/core/constraints.html#defining-foreign-keys).

## Known Pending Proofs and Next Plan Readiness

- Models describe final0017, not a deployable intermediate runtime.04 must add
  real0015/0016 migrations;07 applies0017 and first requires final_sql green.
-04 must preserve global applications, original IDs/digest bytes and NULL
  legacy markers, associate only the owned allowlist and extend the guarded
  fixed test inventory for newly created relations/routines.
-05/07 own actual marker insertion/immutability guards; new writers must
  explicitly insert2.12 owns interpretation after reload and sibling split
  continuation; metadata alone does not establish those behaviors.
-06/07 own actual dividend SQL tuple rejection;13 owns entitlement/payment
  worker behavior. Terminal runtime INSERT/UPDATE/DELETE restrictions are
  migration/bootstrap obligations, not proven by this class declaration.
- The ownership file collects33 cases and authority11. Full SQL/TLS, economic
  preservation, recovery, strict security/images and owner UI/native200%
  checkpoints remain pending. All28 requirements remain unchecked; Phase7's
  live prerequisites and stock gates remain unchanged.
- No product placeholder, public management feature, provider call, production
  operation, package change, publication or branch change was introduced.

## Self-Check: PASSED

All five modified files exist. Task commits61b71e0 and332917e are on
feature/milestone-v1.2. Both focused verification commands pass and44 cases
collect without skips/xfails or simulated final-schema DDL. No tracked file was
deleted; unrelated untracked .claude/ remains untouched.
