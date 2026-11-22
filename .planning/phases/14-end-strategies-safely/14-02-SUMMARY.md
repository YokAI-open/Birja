---
phase: 14-end-strategies-safely
plan: "02"
subsystem: database
tags: [postgresql, closure, idempotency, concurrency, authorization]
requires:
  - phase: 14-01
    provides: Immutable lifecycle/intent schema and verified retained provenance
provides:
  - Checksum-authenticated0023 and narrow app-only closure definer
  - Sorted historical instrument gates, root-locked set recheck and derived terminal evidence
  - Permanent original refusal/closure outcomes with bounded daily journal growth
affects: [14-03, 14-04, 14-07, recovery, closure]
tech-stack:
  added: []
  patterns:
    - Same-owner non-key serialization with sorted stock gates before the account
    - Durable named refusal prevents delayed original requests from closing after definitive refusal
key-files:
  created:
    - backend/alembic/versions/0023_portfolio_closure_authority.py
    - backend/alembic/sql/0023_portfolio_closure.sql
    - backend/tests/test_portfolio_closure_authority.py
  modified:
    - .planning/phases/14-end-strategies-safely/14-INTERFACES.md
key-decisions:
  - The definer derives boundary inputs; the complete same-transaction Python proof and commit remain Plan03 obligations.
  - Original closed and confirmation_changed outcomes precede quota; an owned already-closed acknowledgement creates no new intent row.
requirements-completed: []
requirements-progress: [PMGT-03, PMGT-04, PFIN-06, PSAFE-01]
duration: 16min measured owned-proof interval
completed: 2026-11-19
---

# Phase 14 Plan 02: Atomic Original Closure Authority

**Authenticated0023 SQL freezes one owned strategy at a derived locked boundary
and retains original outcomes without retargeting a replacement portfolio.**

## Task commits and scope

| Task | Commit | Result |
|---|---|---|
| Task1 RED |0166e91|Real PostgreSQL fails on missing close_portfolio,5.76s|
| Task1 GREEN |b429e65|11actual authority tests pass70.42s; scoped static checks pass|
| Task2 |a861d58|Permanent refusal/quota and migration tamper proof; complete18-case suite passes109.00s|

Both tasks are complete. The owned proof directory was created08:48:30UTC;
the09:04:21UTC receipt records completed cleanup. The proof interval excludes initial
source reading and is not a promised task latency. Current source is recorded
in `/tmp/birja-phase14-plan02/receipt.json`.

## Implemented authority

- `close_portfolio(bigint,bigint,uuid,text,text)` is migrator-owned, SECURITY
  DEFINER, with fixed safe search_path and2s lock/10s statement/30s idle bounds.
  PUBLIC and scheduler cannot execute it; app receives only the exact signature.
  No new lifecycle/table DML or sequence privilege is granted.
- Owner management takes User FOR NO KEY UPDATE. Permanent same-owner key/body
  lookup precedes mutable state, name and quota. Foreign/missing and malformed
  requests do not write outcome rows. Confirmation names/policy and UUIDv4 are
  validated; an original key cannot select another target or body.
- All historical stock participation includes sold-out positions and stock
  holdings. Sorted gates in the established instrument namespace precede the
  root lock. A changed instrument set after waiting raises40001 so the caller
  must roll back and retry discovery, never acquire a missing gate behind root.
  The actual lock-wait test observes pg_blocking_pids before inserting the
  synthetic first ownership, then verifies rollback and successful whole retry.
- The SQL derives the global instrument journal tail and unit epoch, samples one
  fresh post-lock wall clock and writes intent/lifecycle/per-stock boundaries
  with Account.closed_at atomically. Existing financial values and History stay
  unchanged. Orphan holdings, inconsistent boundaries and non-forward stock
  history/clock inputs refuse before writes.
- A name mismatch records an immutable confirmation_changed outcome. Renaming
  back cannot turn a delayed original into a new deletion. Same-key concurrent
  calls yield one durable outcome; conflicting bodies cannot overwrite it.
- At most200 new outcome rows per owner/UTCday are serialized under the owner
  lock; the indexed count includes refusals and closures. Existing original
  replays and owned already-closed acknowledgements work at the cap and create
  no new row. Previous-day rows do not consume today's budget. No purge job or
  unbounded arbitrary-error journal is added.
-0023 checks source SHA256 before writes and requires online authenticated
  birja_migrator. Actual wrong-checksum and app-principal invocations refuse
  without changing the installed function. Downgrade refuses before evidence loss.

## Actual verification

Raw receipts and logs: `/tmp/birja-phase14-plan02/`.

| Check | Result |
|---|---|
|Initial real RED|Missing definer,5.76s; `task1-red.log`|
|Initial GREEN|7passed39.56s; `task1-green.log`|
|Stock/first-buy checks after SQL fix|4passed31.04s; `task1-stock-fix.log`|
|Complete Task1 suite|11passed70.42s; `task1-final.log`|
|Task2 selected refusal/quota checks|6passed34.16s; `task2-first.log`|
|Final complete authority suite|18passed109.00s; `task2-final.log`|
|Affected retained migrations/bootstrap/models|3passed12.38s from backend cwd; `retained-regression-backend-cwd.log`|
|Ruff/check/format|Both touched Python files pass; both already formatted|
|Historical bytes|0015–0020 migrations and existing0017/0020 SQL equal3aba99b|
|Diff/stub/cleanup|Diff check passes; no stubs or deletions; owned project resources empty|

The tests use authenticated app/migrator connections, genuine PostgreSQL
transactions and actual table/lock behavior. Financial stock fixtures declare
historical/synthetic openings; they are not public trading/deletion acceptance.
The first-buy race proves SQL membership rediscovery; Plan09 must additionally
exercise actual trading and public closure through the eventual API.

## Deviations and encountered issues

1. **[Rule1 — SQL bug] Row comparison syntax.** The new stock case exposed a
   two-column scalar subquery. Changed only the new0023 SQL to return ROW(...),
   repinned only its new checksum and verified four stock cases plus the full
   suite. This failure is retained in `task1-stock.log`; it was not reported as
   passing evidence.
2. **[Rule3 — test invocation] Retained subprocess working directory.** The
   first retained check was launched from repository root, so its subprocess
   could not import tests. Reran from the documented backend directory; all
   three selected cases pass. No source change or gate relaxation was needed.
3. The finite quota/replay logic is part of the atomic definer introduced in
   Task1. Task2 seals its behavior with concurrency, UTC-day, rollback and
   migration-authentication tests plus the exact service handoff; no duplicate
   or temporary SQL authority was introduced.

No package/authentication gate, architectural scope change or new waiver.

## Handoff and remaining gates

Plan03 must implement the complete shared stock/lifecycle proof on the SAME
transaction after the actual SQL result and before commit. The tested SQL
result is exactly portfolio_id/outcome/replayed; `closed` requires full proof,
including already-closed acknowledgement, while a durable confirmation_changed
can commit only its nonfinancial outcome. The private transaction context,
actual held-gate evidence, exact instrument membership, rollback/three-attempt
retry and commit-failure semantics are specified in14-INTERFACES.

No HTTP route, successful proof stub or normal0023 runtime admission exists in
this plan. Existing one-instrument financial guard is unchanged. Plan03 must
also preserve0021 pre-backfill verification when extracting the shared core;
new guard signatures need explicit finite inventory entries, never wildcards.
Plan04 owns final runtime grants/admission. All seven requirements, full
security/recovery qualification and new owner UI/native200 gates remain pending.
Independent review precedes Plan03. Keep local; no provider/package/publication
or production operation occurred.

## Self-Check: PASSED

All three declared new files and modified interface document exist. Commits
0166e91,b429e65,a861d58 exist. No whole requirement was marked complete. Only
the owned birja-p14-02 containers/network were removed; no matching container,
network or volume remains. Unrelated `.claude/` work is preserved.
