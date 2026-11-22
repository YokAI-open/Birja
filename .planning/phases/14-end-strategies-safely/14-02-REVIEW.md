---
phase: 14-end-strategies-safely
plan: "02"
reviewed: 2026-11-19
depth: standard
source_commit: 08c27f7
diff_base: 3e638e6
files_reviewed: 3
files_reviewed_list:
  - backend/alembic/versions/0023_portfolio_closure_authority.py
  - backend/alembic/sql/0023_portfolio_closure.sql
  - backend/tests/test_portfolio_closure_authority.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 14 Plan 02 — Independent Code Review

## Narrative Findings (AI reviewer)

No proven BLOCKER or WARNING identified in the submitted Plan02 changes.
Reviewed all three scoped files, the3e638e6→08c27f7diff, updated service handoff
and the relevant existing management, lifecycle and stock-verifier contracts.
No structural pre-pass was supplied.

The review is limited to the new migration/SQL authority and its meaningful
tests. It does not certify the future public API, full same-transaction Python
integrity proof, runtime admission or complete Phase14 requirements.

## Assessed invariants

- Migration0023 requires online authenticated migrator execution and verifies
  its exact SQL asset hash before writes. It uses the existing immutable SQL
  parser and refuses downgrade before loss. No historical migration/SQL asset
  was changed in this plan's diff.
- The exact closure definer has trusted ownership, qualified relations and a
  fixed safe search path. PUBLIC/scheduler lack execution, app receives the
  exact signature and no general lifecycle-table mutation authority is added.
  Input validates bounded IDs, canonical name, policy and RFC-variant UUIDv4.
- User FOR NO KEY UPDATE serializes management without introducing the prior
  FK KEY SHARE conflict. Permanent owner/key/body lookup precedes mutable
  checks and quota; conflicting original bodies cannot overwrite or retarget
  an outcome. A durable name refusal remains a refusal after renaming back.
- Historical instrument discovery includes movement history and stock holdings,
  including sold-out positions. Gates are sorted in the established namespace
  before the account lock. The post-lock set is re-read and40001requires a
  whole rollback/retry instead of acquiring an omitted gate behind the root.
- Closure derives instrument-global tails, epochs and one post-lock boundary.
  It rejects inconsistent coarse journal/holding evidence and non-forward
  temporal inputs before inserting terminal rows. Account, lifecycle, intent
  and per-stock evidence share the boundary; no financial value or event is
  manufactured by this operation.
- Closed acknowledgement does not bypass gate/root acquisition or its SQL
  boundary checks. It writes no new intent. Incoming original closed/refusal
  outcomes remain immutable; a fresh key for an owned closed root cannot affect
  a replacement. The declared full Python proof still applies before commit.
- The indexed200new-outcome UTC-day cap is owner-serialized and includes
  refusal and closure outcomes. Original replay and owned-closed acknowledgement
  precede this cap; malformed, foreign and missing requests do not write rows.

## Test reliability and proof limits

The18-case suite uses real authenticated app/migrator connections, transactions,
rollback assertions and concrete immutable original/body/finance comparisons.
The first-buy race observes an actual blocked backend via pg_blocking_pids,
then inserts declared synthetic ownership and asserts40001before a successful
whole retry. Concurrent same-key/conflicting-body and quota-edge cases assert
durable row counts and unchanged/refused targets. Migration tamper/principal
checks assert that installed function bytes do not change on refusal.

The reviewer examined these assertions and called code; it did not rerun the
reported18tests/109.00s or3retained checks/12.38s. Passing counts are executor
evidence, not a substitute for this source analysis. Synthetic historical
stock fixtures do not claim live stock activation or public deletion acceptance.

Plan03 remains a mandatory dependency: execute the definer itself, bind the
actual result to its private originating transaction, verify actual held gates
and exact lifecycle/membership, run the complete shared stock proof on that
same connection, then commit. Every closed acknowledgement needs that proof;
confirmation_changed must be committed before exposing definitive refusal.
Proof/commit/transport failure must not be represented as a guaranteed rollback
or an active GET that cancels an original. Session transaction bounds and
bounded whole-attempt retry remain part of that consumer implementation.

Plan02 creates no temporary successful proof stub or HTTP route. The original
single-instrument financial guard is unchanged. Plan03 must also preserve0021
pre-backfill verification, and Plan04 must complete exact runtime admission.
These declared downstream obligations are not reported as defects in the
completed migration-only producer step.

Only this review document was written. No source changes, test runs, packages,
provider/production operations or commits were performed. Existing work and
the separate01review were preserved.
