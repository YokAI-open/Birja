---
phase: 13-create-and-compare-independent-strategies
reviewed: 2026-11-18T20:33:54Z
depth: standard
diff_base: 61e14af
reviewed_scope: committed backend/tests changes at acbcd4e and 203815f
reviewed_head: 203815f
runtime_resolution_reviewed_head: 99166d9
subsequent_test_only_reviewed_head: 5dc6c45
deployment_compatibility_reviewed_head: 74ee5ea
subsequent_tail_fixture_reviewed_head: 531cf48
borrowed_configuration_stack_reviewed_head: fa28d8e
campaign_image_reuse_reviewed_head: 312d8c9
campaign_image_reuse_files:
  - deploy/tests/portfolio-smoke.py
  - deploy/tests/test-portfolio-smoke-image.py
subsequent_tail_fixture_files:
  - deploy/tests/test-deploy-prerequisites.py
  - deploy/tests/test-dev-bootstrap.py
  - deploy/tests/test-stock-recovery-contracts.py
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
  - CR-03
  - CR-04
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

## Final Bootstrap ACL Refusal Regression — 5dc6c45

**Disposition: clean, no new findings.** Independently reviewed the23-line
test-only addition to `backend/tests/test_dev_bootstrap.py:186`. It calls the
public bootstrap path with the real `_authorize_portfolios` implementation and
an existing mocked driver protocol. It supplies a valid current0020 revision
but an incorrect resulting ACL hash, then requires the exact failure message,
canonical preflight and grants execution in order, evaluation of the exact
ACL query, propagation of ValueError through the transaction context exit and
connection close. The authorizer itself is not replaced by a mock raising the
expected error. This is a meaningful negative authorization/cleanup regression,
not an assertion that code was merely executed.

The mocked transaction assertion establishes exception propagation to the
driver context; it does not itself prove a real PostgreSQL rollback. The
existing real-driver final SQL/privilege test remains intact. No gate, runtime
source, financial expectation, fixture fingerprint, coverage threshold or
historical test was changed. This source addition is outside the UI packet's
render-input inventory and changes no rendered behavior.

Verified the committed test and raw focused-log hashes against
`/tmp/birja-p13-dev-bootstrap-focused-receipt.json`; the log records48pass in2.84s
and dev_bootstrap116statements/56branches at100%. No command was rerun by this
reviewer. The preceding full campaign stopped at critical coverage after its
backend suite; this focused result does not convert that failed campaign into
a complete pass. A new complete final qualification remains required.

## Deployment Compatibility Fixtures and Pin — 0e55743 / 74ee5ea

**Disposition: clean; CR-03 resolved.** Reviewed the actual compatibility-test
delta and one-line deployment marker-pin repair. The fixture now supplies real
legacy, immutable-marker and corrupted-marker Git commits rather than empty
commits that accidentally exercise the wrong source predicate. It preserves
the real source-admission function. Its47 cases cover finite upgrade/runtime
rollback lanes and source/revision/pending-state refusals, assert no calls or
record mutation on refusal, and assert stop/configure/start ordering plus
the inherited operation-lock FD on valid upgrades. Neither acceptance checks
nor runtime source validation were stubbed to turn failure into a pass.

The genuine positive uncovered stale deployed-tool source pin CR-03. Independently
hashed the current0017 migration and its retained4b4320b Git object: both equal
`92cff0699a40b0b8f5f4d66bc56a39a2ef88e3184860d86d6957607a3413f32b`,
also already pinned by `portfolio_migrate.py`. The repair changes only that
expected marker hash in `deploy/deploy.sh`; no immutable migration, schema,
retained profile, finite revision predicate or rollback rule changed. Missing
and corrupt sources remain refused, including a corrupt declared tested source.
See `13-REVIEW.md` for preserved CR-03 history and full disposition.

This source review ran no tests or DB commands. The earlier whole campaign3
failed at compatibility; passing earlier stages and focused47-case evidence
do not make it a full pass. Subsequent tail diagnostics and final full security/
image/recovery qualification remain pending. No UI render input changed here.

## Final Security Tail Test Fixtures — 531cf48

**Disposition: clean, no new findings.** Standard source/diff review covers exactly
the three paths named in `subsequent_tail_fixture_files` above. The original
35-file committed scope/hash and its limits remain unchanged.

- `test-deploy-prerequisites.py:349` clears inherited environment only inside the
  in-process synthetic Evidence fixture and registers restoration with unittest
  cleanup. Existing real restore/recovery assertions remain. The new negative
  at419 supplies an ambient DATABASE_URL, calls the real restore entry point and
  requires guard refusal before configuration loading or success publication.
  It proves that environment isolation is not removal of the operational guard.
- `test-dev-bootstrap.py:177` still requires an unsuccessful real bootstrap
  command. Its four callers now identify the intended migration-only,
  unsafe-owner/membership or catalogue-mismatch reason, and still prove the
  unsafe role flag, membership or object owner remains unchanged after refusal.
  Cash/baseline positive oracles remain124.45/7777 and321.12/8765; no message
  assertion is substituted for these financial checks.
- `test-stock-recovery-contracts.py:268` owns a distinct historical database.
  Setup authenticates birja_test/session/superuser in the fixed disposable stack,
  refuses an existing database before modifying saved ownership state, snapshots
  the original current database and global role/membership state, then creates
  its own database. The real historical migrations, SQL tamper checks, exact
  financial hashes, identity-state checks and fresh-server clone assertions are
  preserved. Only the two old moving-head dividend probes select0014 instead.
- Its new negative at317 calls setup while the owned database exists and asserts
  the original database refusal plus identical fixture dump and role state.
  The refusal occurs before overwriting the outer class's original snapshots or
  created-database flag, so it does not retarget final cleanup.
- Teardown at390 drops only that successfully created database, permits removal
  only of newly introduced allowlisted fixture roles, and lets PostgreSQL refuse
  role deletion with outside dependencies. It then compares the independent
  current database dump and role/membership snapshot. Existing original roles
  are not repaired/dropped; a detected leak fails rather than overwriting the
  original database. A fixed synthetic pg_dump restrict key avoids random
  restrict-key differences in this equality proof.

These are source-review conclusions, not newly measured test outcomes. The
reviewer ran no tests/DB/browser/scans and changed no source or test files. The
executor's focused/tail diagnostics remain separate receipts. Whole campaign3
is still failed; a new complete final-source command and same-archive seven-stage
recovery are mandatory before final qualification. No UI render input changed.

## Borrowed Configuration Stack Lifecycle — fa28d8e

**Disposition: clean, no new findings.** Reviewed all of
`deploy/tests/test-db-config.sh` and traced its unchanged selected backend tests
and conftest setup. The prior unconditional up/down lifecycle removed the current
database before later whole-campaign PostgreSQL contracts. The new ownership
branch fixes that fixture interaction while retaining all136 existing assertion
cases and their real health/database behavior.

- At21, validation derives the two expected services from the fixed checked-in
  Compose configuration, then authenticates inspected project, source config,
  working directory and distinct service labels. It requires healthy running
  state, exact pinned reference plus resolved image ID, exact loopback port maps
  and the test network. Partial/foreign/unhealthy existing containers cannot
  reach pytest through a permissive fallback.
- At50, the existing identity list is captured before ownership selection. The
  borrowed branch only validates; it calls no up operation, so validation cannot
  silently repair or adopt incompatible running services.
- At70, cleanup is conditional on the original owns_stack flag. Failure during
  borrowed validation or a borrowed test does not call down. A standalone
  invocation still creates, validates and cleans its own stack, and propagates
  failed tests, timeouts or cleanup failure. The fixed stack uses tmpfs data;
  no persistent production volume or target is introduced by this change.
- The six selected test modules, uv locked/no-sync arguments, environment guard,
  tests, timeouts and exit handling remain. Authentication of borrowed resources
  is fixture isolation, not a substitute for the existing test database guard.

No tests, Docker/database operations or source changes were performed in this
review. The standalone136 pass and final ordered tail with current-database and
container preservation belong to executor receipts; they do not qualify the
whole command. Actual final-source complete security and same-archive recovery
remain pending. Original35-file fixture scope/hash is not rewritten by this
one-file follow-up; the separate reviewed head above binds this additional scope.

## Authenticated Campaign Image Reuse — 312d8c9

**Disposition: clean; CR-04 resolved after RED5693083.** Reviewed the complete
`portfolio-smoke.py` and `test-portfolio-smoke-image.py` changes and traced the
existing source/archive/image/record helpers and final campaign guard.

The repair uses a private first-use file, not a mutable Docker tag or process
cache, as the image identity for later invocations. It checks archive ownership
and checksum, directory and record ownership/modes/symlink boundaries, expected
commit/app-tree/context, then inspects the recorded exact ID and verifies full
ID/config/RootFS equality. Archive and record bytes are rechecked afterward.
Missing/changed recorded images fail closed without rebuilding, accepting equal
content or rewriting a prior record. Current Git dirty/HEAD checks and extracted
source-tree validation remain. First use still builds from authenticated source
and persists the verified record; new aliases are scoped to private campaign
directory identity so another campaign's tag is not replaced.

The added regressions meaningfully cover both selected revisions through
separate module loads, persisted first-use identity, one build across two uses,
missing/reindexed/config/rootFS substitutions, unsafe or mismatched records,
archive/current-source/private-directory refusals and distinct new-campaign tags.
No financial, source or corruption oracle is weakened. The unchanged runner
still authenticates every recorded ID and detects record disappearance/change
after each stage, including failures.

Verified all source, RED/GREEN-log and real-proof-receipt hashes from
`/tmp/birja-p13-image-binding-repair-receipt.json`. Its measured17 image methods
and26 related contracts pass. The actual separate-process Docker receipt proves
retained0017 and current0020 each build once and then reuse the same ID with zero
build commands. A nonexistent recorded ID causes one exact-ID inspect and no
build. The failed canonical recovery archive remains unchanged. This reviewer
ran no tests or Docker commands and does not independently remeasure those
executor results.

These two paths are a separate follow-up scope; the original35-file fixture list
and hash remain historical. The complete security pass at535a5b7 and failed
recovery do not qualify this new helper. Final-source whole security and fresh
seven-stage same-archive recovery remain pending. No implementation, dependency,
migration, retained profile, UI input or approval record changed in this review;
only the two owned report files were updated, with no commit.

