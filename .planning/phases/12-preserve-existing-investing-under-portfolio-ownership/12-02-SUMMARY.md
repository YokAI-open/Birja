---
phase: 12-preserve-existing-investing-under-portfolio-ownership
plan: "02"
subsystem: database
tags: [sqlalchemy, portfolio, ownership, constraints, exact-money]
requires:
  - phase: 12-01
    provides: guarded isolated test bootstrap and root-isolation fixture matrix
provides:
  - Named Account financial-root metadata with terminal timestamp and compound owner key
  - Required paired portfolio/user lineage on Holding and Trade
  - Per-root holdings and root-aware trade cause key while preserving user-global retries
affects: [12-03, 12-04, 12-07, 12-08, 12-10, 12-14, 12-27]
tech-stack:
  added: []
  patterns: [paired ForeignKeyConstraint, root-first holding/history indexes]
key-files:
  created: []
  modified:
    - backend/app/models/user.py
    - backend/app/models/trade.py
    - backend/tests/test_portfolio_ownership.py
key-decisions:
  - Final model metadata declares the coordinated0017 shape; no existing database was altered
  - Keep the existing trade cause candidate key alongside the extended owned-root key during the coordinated transition
  - SQL feature proofs remain unexecuted until Plan07 applies actual0017
requirements-completed: []
requirements-addressed: [PFUND-03, PSAFE-03]
duration: 5 min
completed: 2026-11-16
---

# Phase 12 Plan 02: Financial Root and Core Row Ownership Models

**Named account roots and paired owner foreign keys express portfolio isolation without changing any stored financial column or granting new cash.**

## Performance

- Started: 2026-11-16T08:15Z
- Completed: 2026-11-16T08:20Z
- Tasks: 2/2
- Files modified: 3
- Packages/schema migrations/HTTP routes changed: none

## Accomplishments

- Account retains its existing identity, cash, starting_cash and UTC creation
  timestamp. Final metadata adds a nonnull text name defaulting to My portfolio,
  nullable timezone-aware closed_at and unique(id,user_id). A user lookup index
  replaces the metadata's old one-account-per-user unique constraint. No
  description or management behavior is exposed.
- Holding and Trade require portfolio_id and one paired foreign key to
  accounts(id,user_id); separate valid-but-unrelated references cannot express
  the ownership contract. Neither FK cascades economic changes/deletions.
- Holdings are unique by(portfolio_id,coin_id), retaining exact quantity/basis
  types and all previous monetary checks. Trade adds an owned-root cause key
  and root-first deterministic History index. Existing fill fields,
  user-global(user_id,idempotency_key) uniqueness and retained trade cause key
  remain unchanged.
- Eight passing metadata/serialization cases inspect root shape, required
  paired constraints, index/unique tuples, exact NUMERIC precision and string
  Decimal JSON output. Five new real SQL cases collect for duplicate same-root
  holdings, forged trade ownership, missing/unknown roots and root lifecycle
  metadata. Together the ownership file collects21 tests.

## Task Commits

| Task | Commit | Result |
|---|---|---|
| 12-02-01 | 0d34066 | Named portfolio root metadata and four passing exact-money/shape cases |
| 12-02-02 | 795536a | Core paired ownership keys, eight passing metadata cases and collected SQL negatives |

## Verification

Used the existing locked environment with
`UV_CACHE_DIR=/tmp/birja-uv-cache uv run --no-sync`; no installation/lock change.

| Check | Result |
|---|---|
| test_portfolio_ownership.py -q -k model_metadata after task01 | 4 passed,9 deselected |
| Same focused command after task02 | 8 passed,13 deselected in0.77s |
| test_portfolio_ownership.py --collect-only -q | 21 collected |
| Ruff check and format --check on the three assigned files | Passed |
| git diff --check | Passed |

The existing session-autouse prerequisite requires a connection to the guarded
disposable database even for metadata tests. The default sandbox denied the
socket; the scoped escalation passed. Test assertions themselves use metadata
and schema serialization without a database session. No feature SQL assertions,
full regression/coverage/security scans or runtime acceptance were run here.

## Decisions and Deviations

Followed the approved model-only coordinated-transition boundary. The added
user lookup indexes retain FK/user-query support after user-only uniqueness is
removed; actual deployed DDL remains the responsibility of04/07. Existing
uq_trades_id_coin_user remains alongside the new
uq_trades_id_portfolio_coin_user because existing stock models still reference
the retained key;03 extends their root lineage without invalidating current
metadata references. Composite FK syntax was checked against the official
[SQLAlchemy2.0 constraints documentation](https://docs.sqlalchemy.org/en/20/core/constraints.html#defining-foreign-keys).
No architectural deviation or new dependency was needed.

## Known Pending Proofs and Next Plan Readiness

- Final model metadata is ahead of retained0014 by design and is not a runnable
  or deployable intermediate service.04 adds staged0015/0016;07 owns actual0017
  constraints, admission and the first green final_sql execution.
- Existing ORM consumers still require later portfolio-aware service/API work.
  Original monetary types/fields/defaults are unchanged, but preservation of
  populated database rows is not claimed from metadata assertions.
-03 owns stock/dividend model lineage.08 and later domain plans own resolver,
  execution, retries and financial readers. No public creation, description,
  rename or deletion feature was added.
- Complete restricted-role/TLS, exact recovery, security/image/coverage and owner
  UI/native200% proof remain pending. Phase7 live gaps/admission gates remain
  intact. All28 milestone requirements remain unchecked.

## Self-Check: PASSED

All three modified files exist; task commits0d34066 and795536a are on
feature/milestone-v1.2. Both metadata verification contracts passed. Collected
SQL cases remain visibly unexecuted, with no skips/xfails or manual final-schema
DDL. No product stub, new endpoint or unrelated file change was introduced.
