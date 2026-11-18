---
phase: 13-create-and-compare-independent-strategies
reviewed: 2026-11-18T16:32:06Z
depth: standard
diff_base: 61e14af
reviewed_scope: committed backend/tests changes at acbcd4e and 203815f
reviewed_head: 203815f
runtime_resolution_reviewed_head: 99166d9
scope_sha256: c6eb3f6619a13b459b2e48d6f915a72684fa85db8999b7c2b06f354bb38b2863
files_reviewed: 35
files_reviewed_list:
  - backend/tests/portfolio_fixtures.py
  - backend/tests/stock_action_fixtures.py
  - backend/tests/test_accounts.py
  - backend/tests/test_dev_bootstrap.py
  - backend/tests/test_dividend_authority.py
  - backend/tests/test_dividend_scheduler.py
  - backend/tests/test_dividend_schema.py
  - backend/tests/test_event_history.py
  - backend/tests/test_migrations.py
  - backend/tests/test_portfolio_api.py
  - backend/tests/test_portfolio_crypto.py
  - backend/tests/test_portfolio_dividend_authority.py
  - backend/tests/test_portfolio_dividend_first_buy.py
  - backend/tests/test_portfolio_identity_api.py
  - backend/tests/test_portfolio_management_admission.py
  - backend/tests/test_portfolio_management_authority.py
  - backend/tests/test_portfolio_management_grants.py
  - backend/tests/test_portfolio_management_migrations.py
  - backend/tests/test_portfolio_migrate.py
  - backend/tests/test_portfolio_ownership.py
  - backend/tests/test_portfolio_routes.py
  - backend/tests/test_portfolio_schema_admission.py
  - backend/tests/test_portfolio_scoped_history.py
  - backend/tests/test_portfolio_service.py
  - backend/tests/test_portfolio_snapshot.py
  - backend/tests/test_portfolio_stock_authority.py
  - backend/tests/test_portfolio_stock_ownership.py
  - backend/tests/test_portfolio_stock_trading.py
  - backend/tests/test_portfolio_strategy_events.py
  - backend/tests/test_stock_action_migrations.py
  - backend/tests/test_stock_execution_authority.py
  - backend/tests/test_stock_isolation.py
  - backend/tests/test_stock_ownership.py
  - backend/tests/test_stock_valuation.py
  - backend/tests/test_trading_schema.py
fixture_review_status: clean
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
resolved_findings:
  - CR-02
status: clean
---

# Plan17 Fixture Adaptation Review

## Narrative Findings (AI reviewer)

The 35 test-file adaptations are acceptable on source review. No new defect or
weakened financial/authorization oracle was demonstrated in those adaptations.
The separate runtime blocker exposed by the new deterministic regression was
subsequently resolved and independently reviewed at `99166d9`, as recorded
below. This does not claim the final whole suite or recovery campaign passes.

### CR-02: Management owner locks invert the dividend user foreign-key lock

**Original classification:** BLOCKER — valid concurrent operations can deadlock or return
a bounded lock-timeout refusal.
**Disposition:** RESOLVED in `99166d9`; original RED trace retained below.

**Runtime files:** `backend/alembic/sql/0020_portfolio_management.sql:95`
(metadata), also owner locks at `:15` (creation) and `:62`
(initialization); retained dividend account lock at
`backend/alembic/sql/0017_dividend_portfolio.sql:299` followed by
payment/decision insertion at `:332` and later correction paths.

**Demonstration:** The new
`backend/tests/test_portfolio_strategy_events.py:410`
`test_dividend_user_fk_does_not_invert_waiting_metadata_owner_lock` correctly
forces this order using actual restricted scheduler SQL and the actual HTTP
metadata endpoint:

1. Scheduler acquires the stock portfolio root lock.
2. Metadata acquires the owner's user-row `FOR UPDATE` lock and waits for
   that root; an observer verifies an actual active PostgreSQL lock wait with
   the scheduler's blocking PID.
3. The scheduler applies the dividend. Its inserted user foreign key needs
   `KEY SHARE` on the same user row, conflicting with metadata's
   `FOR UPDATE`. Each transaction now waits for the other.

The executor/parent reports the genuine RED reproduced this runtime failure;
this reviewer independently traced the test and SQL but did not rerun a database.
The test should remain RED until the runtime issue is fixed. It must not be
reclassified as stale fixture setup, skipped, changed to accept503, or made
sequential to obtain a green result. The bounded timeout prevents an indefinite
hang but does not satisfy the required successful coexistence of metadata and
dividend processing.

**Fix:** Use an owner-serialization lock compatible with the user FK's
`KEY SHARE`, such as `FOR NO KEY UPDATE`, consistently for the three
management owner-lock sites, while retaining owner serialization, cap/name
checks, permanent intent replay, account locks and transaction atomicity.
Authenticate/update the affected current-source contract pins and prove the
exact intended catalogue/ACL profile; do not rewrite historical0017 dividend
logic or weaken its retained fingerprints. Re-run this deterministic overlap
test, ordinary create/metadata concurrency cases, funding/privilege contracts,
and the final complete security/recovery campaigns after independent runtime
review.

**Resolution:** Independent source and binding re-review of
`203815f..99166d9` confirms that only the three management owner locks become
`FOR NO KEY UPDATE`. These still serialize management against itself while
allowing FK `KEY SHARE`; account locks, cap/quota, once-only grant/replay and
ownership checks remain intact. All1172 measured catalogue records differ only
in those three routine definition lines. ACLs remain exact; source pins and
normal/quarantined/no-ACL authority hashes were independently checked against
the changed specimen and intended privilege projections. The specimen changes
no financial, identity, constraint, owner or ACL oracle. Historical0015–17/0019
and their retained contract definitions are unchanged.

The deterministic regression was strengthened, not relaxed: metadata and original
creation replay both wait on an observed real root blocker before the dividend
FK insert; both require200, the original root, cash10000.50 and exactly two
creation records. The separate restricted-role test now performs actual
initialize/create/rename with unchanged grants. Verified source/log hashes in
`/tmp/birja-p13-cr02-repair-receipt.json` and inspected the actual test outputs:
70 focused pass363.48s, two direct overlap cases pass12.71s, offline contracts
8+11+8+6 pass. This reviewer did not execute those tests. No remaining defect
was demonstrated in the repair. Full resolution details and current source
scope are in `13-REVIEW.md`; final complete campaigns remain required.

## Fixture Safety Assessment

- Canonical `name_key`/name additions only make privileged synthetic seeds
  satisfy the current schema. Unequal cash and custom starting baselines remain
  unchanged. These fixtures do not represent new public grants.
- Destructive staged fixtures still operate only in the guarded disposable
  database; their teardown now restores genuine current head and current
  restricted grants. They do not migrate the schema under an active test or
  bypass admission assertions.
- Updated0020 model/startup expectations retain explicit refusal of migration-only
 0015/16/18/19 and retained0017. The actual0017 split evidence is independently
  compared before forwarding to0020 for current ORM/service imports; historical
  columns/digests and the financial assertions are retained.
- The dollar-quoted grants now run through asyncpg's real multi-statement
  protocol rather than invalid semicolon splitting. Exact grant parity and
  restricted admission assertions remain in place.
- Route inventory adds approved create/overview/metadata routes; malformed empty
  create/PATCH requests still refuse, DELETE remains405 and unscoped financial
  routes remain absent.
- Statement counts acknowledge the final identity/authority proof without
  allowing a second cash/holding read. Tests positively assert the single
  financial snapshot, the separate account `FOR SHARE` proof, owner/active
  predicates and absence of cash from the proof query.
- The final stock-valuation adaptation compiles the actual PostgreSQL dialect
  before checking SQL shape, requires exactly two queries with one financial
  cash/quantity read and a separate cash-free account SHARE proof, and retains
  all original assertions for cash9796, quantity2, basis204, original mid101,
  total9998 and permission/unit/epoch/mapping/continuity suppression. It does
  not accept a new mark or recompute the monetary oracle from production output.
- The tentative extra bootstrap in `test_stock_migrations.py` was removed
  before the final commit; that file is byte-identical to the base and is no
  longer in this change scope. Intermediate retained migration stages therefore
  do not accidentally install current0020 runtime grants.
- The writer/read overlap test waits for observed PostgreSQL blocking PIDs and
  lock state before release, then requires the old complete financial tuple and
  a later new complete tuple. Its negative control deliberately combines old
  cash with new holdings, independently requires the impossible11000 total and
  proves the same invariant rejects it. Neither branch merely waits on an
  asyncio task or accepts any returned value.
- The stock-isolation reader explicitly ends its completed request transaction
  before separate teardown attempts root writes. This preserves the production
  lock lifetime during the tested read.
- Scheduler fixture cleanup retains newly immutable root/grant/latch evidence
  instead of deleting a referenced user or disabling new provenance guards.
  Event-specific disposable cleanup and the bounded-keyset financial results
  remain asserted.

## Scope and Verification Limits

Scope is the exact35 paths above relative to `61e14af`: 34 fixture-adaptation
files committed in `acbcd4e` plus the separate deterministic runtime RED in
`203815f`. The final follow-up inspected the stock-valuation query-shape change,
the reverted stock-migration helper change, and the final formatted RED test.
`scope_sha256` is SHA256 of the canonical
JSON mapping from those sorted paths to their SHA256 content hashes, using
sorted keys and comma/colon separators. This binds the reviewed test bytes even
if a subsequent worker commit changes HEAD without changing them. The mapping
was read from the committed `203815f` objects, not concurrent runtime edits.

The review read every actual diff and followed the relevant fixture, migration,
snapshot negative-control and runtime-lock contexts. It ran no tests, database,
browser, provider or production operations and changed no source/test files.
The active executor owns the exclusive database lane. No new dependency,
skipped test, expected failure marker, relaxed money result or accepted runtime
failure was introduced in the reviewed adaptations. Whole-suite success and
current-source encrypted recovery remain separate pending evidence.
The original committed35-file scope/hash remains bound to `203815f`. A later
separate runtime-resolution review at `99166d9` also inspects the two strengthened
test deltas without rewriting that historical scope hash or claiming concurrent
test execution. It resolves CR-02 as documented above.

_Independent gsd-code-reviewer; no commit created._

