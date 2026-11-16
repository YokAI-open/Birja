---
phase: 12-preserve-existing-investing-under-portfolio-ownership
plan: "05"
subsystem: database
tags: [postgresql, stock-authority, portfolio, immutable-evidence, authorization]
requires:
  - phase: 12-04
    provides: staged0015/16 owned association and immutable global split guards
provides:
  - Immutable0017 stock SQL companion with original signatures and root-derived final validation
  - Explicit new split digest marker and active-root stock INSERT guards
  - Thirty collected real final-schema restricted-role cases and five passing static contracts
affects: [12-07, 12-11, 12-12, 12-16, 12-17, 12-27]
tech-stack:
  added: []
  patterns: [fixed versioned SQL companion, paired root snapshot, private invoker validator]
key-files:
  created:
    - backend/tests/test_portfolio_stock_authority.py
    - backend/alembic/sql/0017_stock_portfolio.sql
  modified: []
key-decisions:
  - Derive root from immutable Trade and compare expected portfolio plus facts, movement, owner, cash and holding state
  - Preserve all retained0013 arithmetic, permission, quote, session, status and action checks
  - Install the companion only through actual0017; static checks and collection do not establish runtime success
requirements-completed: []
requirements-addressed: [PFIN-02, PFIN-03, PSAFE-03]
duration: 13 min
completed: 2026-11-16
---

# Phase 12 Plan 05: Versioned Root-Aware Stock SQL Authority

**A static0017 companion retains stock execution safeguards while binding the final snapshot and new stock effects to one owned active portfolio.**

## Performance

- Started: 2026-11-16T08:45Z
- Focused verification completed: 2026-11-16T08:57Z
- Tasks: 2/2
- Files created: 2
- Dependencies, providers, production changes and final SQL installation: none

## Accomplishments

- The immutable companion copies the retained0013 arithmetic and independent
  market-authority checks, including half-even cash/mid/basis, whole quantities,
  zero fees, exact source timestamps, current permissions, actions, status,
  sessions and quotes aged less than120 seconds. It imports no application SQL
  and does not rewrite old migration sources.
- check_stock_fill_integrity() remains SECURITY INVOKER, rejecting immutable
  stock mutations and validating paired trade/fact/movement ownership. Its new
  BEFORE INSERT branch rejects an unknown, foreign or closed root, including
  split/opening movements with no trade_id. Crypto's existing deferred behavior
  remains separate from the final migration's general ownership constraints.
- assert_stock_execution_current(bigint,bigint,jsonb) retains its exact signature.
  The same relational authority snapshot now joins the trade's paired Account,
  holding and movement; compares expected.portfolio_id, active owner, cash,
  held quantity and basis; and scopes pending entitlement evidence to that root.
  clock_timestamp follows the read. No table read, lock, mutation or network
  operation follows that sample; the service retains the last-business-SQL
  invocation contract.
- check_stock_split_digest_version() requires explicit SMALLINT2 on each new
  global application. Existing NULL rows are never changed. The companion
  installs only a BEFORE INSERT marker trigger, retaining0015's unconditional
  global UPDATE/DELETE guard and all global event/cause semantics.
- All three routines are birja_migrator-owned invokers, with pinned
  pg_catalog,public,pg_temp search_path and PUBLIC EXECUTE revoked. Only the
  existing app execution validator receives EXECUTE; internal trigger routines
  and scheduler execution-validator access are denied. No cash setter,
  lifecycle routine, overload or broad table grant is introduced.
- Thirty future real-PostgreSQL cases cover owned receipt success and unchanged
  sibling cash/basis, forged cause/root tuples, closed/foreign targets, altered
  snapshot state, user-global retry keys, immutable payload bytes, exact routine
  ACL/owner/path inventory, missing/unsupported new markers, immutable global
  applications, shared global split causes with once-only portfolio effects,
  forged unit epochs, closed split writes and direct scheduler denial. The
  private fixture installs no SQL or privileges; runtime operations explicitly
  assume the restricted app/scheduler roles supplied by actual0017.

## Task Commits

| Task | Commit | Result |
|---|---|---|
| 12-05-01 | 6ae6d81 | Thirty final_sql scenarios collected against actual future0017 |
| 12-05-02 | 1802977 | Versioned stock SQL companion and five passing static contracts |

## Verification

Existing installed environment only, UV_CACHE_DIR=/tmp/birja-uv-cache and
uv run --no-sync. No package was installed or upgraded.

| Check | Result |
|---|---|
| Task01 pytest collection | 30 cases collected in0.24s |
| Task02 asset_contract gate | 5 passed,30 deselected in0.74s |
| Final module collection | 35 cases collected in0.24s |
| Ruff check and format | Passed |
| git diff --check | Passed |

The initial sandboxed static run could not open the localhost socket required
by the existing autouse disposable-DB prerequisite. A scoped rerun allowed that
bootstrap and passed; no final-schema fixture or SQL asset was executed.
The static tests independently retain every old0013 explicit refusal outcome,
check named money/market invariants, signatures/ACLs, root binding and final
snapshot timing, marker/no-default source and exact new trigger inventory.

## Deviations from Plan

None. The new active INSERT triggers use the existing integrity routine rather
than adding an authority signature or a privileged lifecycle/cash interface.
Requirements remain unchecked: planned collection and static SQL contracts
cannot complete PFIN-02/PFIN-03/PSAFE-03.

## Known Pending Proofs and Next Plan Readiness

- Plan07 must load this exact fixed-path companion only after actual0017 has
  installed paired NOT NULL/root/cause constraints and final indexes. It must
  run all thirty final_sql cases and the other domain matrices against that
  schema, retaining the existing deferred fill-integrity triggers.
- Plan07 removes finite association guards/helper, restores unconditional
  owned-row mutation refusal and preserves0015's global split immutability.
  New trigger names here are stock_split_digest_version on global applications
  and portfolio_stock_active_insert on trades/facts/movements. No association
  helper is referenced in this companion.
- Plan16/17 authenticate the exact installed function bodies, paths, owners,
  column/check/trigger inventories and ACLs for bootstrap/recovery. Tests also
  require actual0017 to supply existing app/scheduler privileges; they never
  manufacture a final schema or grants to make authority assertions pass.
- Plan11 adds captured portfolio_id to every new stock authority snapshot and
  leaves the validator as the last business statement. The new current-root
  cash/holding checks are execution checks, not a replacement for original-fill
  replay authorization or historical journal verification.
- Runtime execution, real SQL role/TLS, legacy/current recovery, full coverage,
  security/image scans and owner UI/native200% remain future gates. Phase7 live
  outcomes and activation remain deferred; production and packages unchanged.
- Ready for12-06 in this wave. Work stays local; unrelated.claude/ untouched.

## Self-Check: PASSED

- Both created paths exist; task commits6ae6d81/1802977 exist on the current branch.
- No stubs, bypasses, skipped/xfail feature cases or fabricated runtime success.
- No tracked files deleted; no new threat surface outside the planned stock
  database authority boundary; no provider/host/publication action performed.
