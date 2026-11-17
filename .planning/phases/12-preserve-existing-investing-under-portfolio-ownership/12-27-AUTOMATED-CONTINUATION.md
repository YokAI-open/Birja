# Plan 27 local qualification continuation

This is an internal execution handoff, **not a user checkpoint or completed
Plan27 summary**. The owner's November16 “Finish local automated validation”
approval still authorizes further necessary tested local repairs without
another procedural retry question. No new dependency/provider/production or
publication action is authorized. Owner UI/native200% acceptance remains28.

## Completed repair segment

On feature/milestone-v1.2, source repairs are committed individually:

- `f1c33f9` / owning12-20: six retained frontend API/shared stock fixture files
  now supply required portfolio IDs and scoped endpoints, canonical trade2 and
  mixed3 cursors. All203 retained API cases pass, preserving malformed
  response, CSRF, monetary precision, reprice, response-loss and replay checks.
- `b61f9e2` / owning12-22: five retained hook suites now receive explicit captured
  owner/root/session targets and use scoped financial cache keys. The pure
  `portfolioTargetFixture` is test-only, with frozen epochs and a current-session
  predicate; production target checks remain untouched. All78 retained hook
  cases pass. Old identity cash assertions move to authoritative portfolio
  refresh assertions; mutation promises still wait for all five accepted views.
  New owner/relogin fixture targets explicitly model a new selection boundary.
- `3b88c35` / owning12-19: preserve **only exact `["prices"]`**, Birja's global
  owner-independent crypto price query, across identity changes. Every other
  non-identity query still purges immediately, including price-prefixed owner
  variants, stock/admission/context, portfolio metadata, attempts, History and
  unknown keys. Strengthened auth assertions prove this for logout and owner
  switch. Retained SignInPage mocks/assertions use email-only v2 identity and
  the identity-only Account page. All75 affected auth/stock/sign-in cases pass.
- `397be86` / owning12-14: static backend History cursor fixtures now collect
  with explicit roots. All134 standalone mixed cursor/wire cases pass, including
  wrong/malformed roots, all kinds/timezones and duplicate JSON keys. The old
  HTTP module's static cursor constructor is repaired, **not its whole legacy
  HTTP/data fixture suite**; do not claim that module passes yet.

## Actual frontend verification

Full frontend lint and TypeScript build-project checking pass; the original47
typing errors in11 retained fixture files are resolved. Changed-file Prettier
and production Vite build pass. Full coverage run passes **44files/958tests**:

- statements97.50% (2383/2444)
- branches94.65% (3311/3498)
- functions98.58% (557/565)
- lines98.68% (2177/2206)

No tests were deselected or marked skipped/xfail; no runtime type/financial
guard was weakened. Private logs:

- `/tmp/phase12-27-frontend-full-second.log` — final complete coverage958pass
- `/tmp/phase12-27-frontend-build.log` — actual production build
- `/tmp/phase12-27-api-legacy.log` —203 API cases
- `/tmp/phase12-27-hooks-final.log` —78 retained hook cases
- `/tmp/phase12-27-auth-stock.log` —75 affected auth/stock/sign-in cases
- `/tmp/phase12-27-mixed-cursor-final.log` —134 backend cursor cases
- `/tmp/phase12-27-backend-collection.log` —**3011 backend tests collected**

Final all-security source binding still belongs to the complete runner after
all remaining backend repairs; these frontend results are a real repair
segment, not whole Plan27 qualification. `useMe.ts` is among the covered UI
packet sources, so the previous102-artifact/248-source review packet is now
historical. Regenerate the complete actual-source packet at the final source
with browser widths/reflow and actual image inspection before Plan28.

## Completed backend repair segment

- `f5bdeea` / owning12-12: current synthetic opening/fill/facts/movements and
  reconstruction now carry the real fixture Account root. Sole-root resolution
  asserts uniqueness; explicit sibling roots are ownership-checked, with a new
  ambiguity/foreign-root regression. Synthetic new splits independently encode
  canonical version2 root tuples instead of placeholder hashes; legacy NULL
  applications/digest semantics remain untouched. Real prior regular sessions
  and earlier openings replace weekend-dependent dividend setup. Current role
  proofs use the exact final bootstrap instead of forbidden downgrades or
  ad-hoc grants. Original economic, late/zero/sold-out ownership, rollback,
  oversell and race assertions remain. All240 action/journal/calendar cases pass.
- `e983aa8` / owning12-16: retained dev bootstrap mocks supply their explicit0014
  revision read; CLI assertions include migrate=False. New dispatch assertions
  keep0015/16 migration_only and0017 on its final authority path. All32 cases pass.
- `c0aff80` / owning12-13: the current committed-client dividend repair removes obsolete CREATE/DROP
  scheduler-role assumptions and uses the exact final bootstrap. Entitlements,
  successor snapshots, payment/hold work, History and stock/crypto calls retain
  actual portfolio roots. Root-owned INSERT waiters are observed and serialized;
  mutable global revisions/pending split evidence invalidate stale work without
  disabling guards around running services. Four new tests directly prove
  immutable quantity/cutoff/units/sequence tamper refusal even for setup owner.

All new trigger maintenance is exact-target, privileged-disposable-fixture
setup/corruption/cleanup only. Original enabled state is required and restored
in finally, then asserted. No production/runtime/migration/SQL-asset/grant body,
dependency, test deselection, skip/xfail or coverage threshold changed.

The strict serial combined action/journal/calendar/bootstrap/dividend/shared
stock regression passes350 cases in64.63s. This precedes the four added direct
immutability cases; the final affected dividend/shared-stock replay passes82
cases in36.01s, including all four added refusals.
Full backend Ruff check and format pass226 files. Logs:

- `/tmp/phase12-27-stock-journal-final.log` —240pass/32.46s
- `/tmp/phase12-27-dev-bootstrap-final.log` —32pass/1.85s
- `/tmp/phase12-27-dividend-concurrency-second.log` —13pass
- `/tmp/phase12-27-dividend-worker-third.log` —56pass/24.58s
- `/tmp/phase12-27-stock-dividend-serial-final.log` —350pass/64.63s
- `/tmp/phase12-27-dividend-final.log` —82pass/36.01s, final affected replay

One prior combined attempt was inconclusive: the executor mistakenly launched
the apparently pure bootstrap pytest concurrently. Its session-autouse
ensure_dividend_test_owner issues ALTER TABLE OWNER over every disposable
relation, causing a lock cycle with another test's fixture cleanup. Both
processes exited; sanitized activity showed zero sessions; a guarded genuine
schema reset and the serial350-case replay pass. **Never run a second pytest
against this stack concurrently, even for apparently pure modules.** Another
diagnostic wait run was interrupted after22 passes when a retained revision
helper tried to append an owned entitlement while the test deliberately held
its root; that fixture now changes only global revision evidence before lock
release. All56 final wait/worker cases pass without guard bypass.

## Earlier backend diagnostic (repaired in segment 2 below)

Full unfiltered diagnostic `/tmp/phase12-27-backend-third.log` reaches548passes,
3failures and37errors before its40-failure stop. Its three dev-bootstrap failures
are now fixed above. Its first remaining family is the separate shared
`tests/test_dividend_schema.py::dividend_case` and
`tests/test_dividend_authority.py::authority_case`, **not** the repaired
`tests/dividend_fixtures.py` independent committed-client fixture.

Read `test_stock_action_migrations.py::ledger`: it creates only a User on current
head. The dividend schema helper inserts rootless entitlements; authority_case
then assumes app/scheduler roles are absent, creates old grants/accounts and
updates financial evidence that is immutable at0017. Current behavioral proofs
need actual owned roots, exact final bootstrap and original snapshot terms
prepared before immutable insertion. Preserve their amount/rounding/causal/
ACL/negative assertions; never relax final triggers to make old setup work.
Existing current-root fixtures in test_portfolio_dividend_authority.py are a
reference. The still-legacy test_dividend_payments/corrections/History callers
also need explicit roots. Helpers that deliberately test old schemas must use
their genuine retained source/model/API and actual specified revisions, rather
than applying current0017 ORM/services to an old DB.

Further expected retained work:

- Current-versus-retained migration head/downgrade fixtures:0017 intentionally
  refuses downgrade. Exact old-schema cases require genuine retained sources,
  explicit supported revisions and authenticated migration child identity.
- Remaining stock/trading/valuation/History/API fixture callers throughout the
  unfiltered suite may still use user-only signatures. The repaired shared
  stock_request helper validates an actual sole/explicit root in tests only;
  production still requires OwnedActivePortfolio with no default/fallback.
- Full backend60-module100% branch /80% overall coverage remains pending,
  including new startup/role/TLS modules. No gate/exclusion change is allowed.

## Test stack ownership and cleanup

The initial prescribed all-security runner correctly refused a preexisting
`birja-test` stack before writes (`/tmp/phase12-27-first-security.log`). Parent
confirmed nobody else uses it. Read-only inspection verified exact own checkout
Compose labels/config, pinned PG/Redis, loopback55432/56379 and **no persistent
volumes**; these are the synthetic tmpfs containers created08:57:41 today.
They were used only for diagnostics and **remain running** for the continuation.
After the82-case final replay, the backend executor used the existing exact
guarded reset and authentic migration lane to leave a clean genuine0017 schema;
all noninternal triggers were checked enabled. No pytest/session or other
subprocess remains active. The next executor may use this stack for diagnostics,
but every DB-touching action must remain serial.
Do not claim adoption as exclusive full-run proof. Before the final runner,
clean only this verified synthetic stack using its exact Compose file, then
let the runner create/clean its own stack. No dev/production resources touched.

## Full security / recovery / closeout still required

Continue the original full12-27 plan and26 summary/handoff. After final repairs,
run actual `--suite all-security`; it must include unchanged audits, actual
declared Dockerfile builds and strict five-image HIGH/CRITICAL scans including
unfixed findings. New dependency fixes need exact review/approval, not a silent
pin change. Existing approved locked builds/audit lookups remain allowed.

Preserve/move the whole private old `/tmp/birja-phase12-proof` directory to a
unique historical location after ownership/mode/symlink checks before creating
one fresh exclusive final archive. Do not overwrite/rebuild midcampaign. Run
all seven authenticated current/retained serial stages from one final archive,
including actual source-destroyed encrypted0017 cold restore. No stage has been
run for this final Plan27 campaign yet. The runner currently has a fixed archive
path and accepts `--suite recovery` only, although the plan's example includes
`--archive`; reconcile this interface truthfully without weakening the fixed
path/exclusivity checks.

Do not create27SUMMARY or advance26/28 until both tasks actually pass. Preserve
Phase7 consumed campaign evidence: no repeat provider calls; six requirements
remain pending, stock admissions OFF. Keep all commits local; `.claude/` remains
unrelated/untracked and untouched. No private `.env`, real rows or provider
credentials were read. No processes from this segment remain active beyond the
verified synthetic DB/Redis stack. No user action is needed to continue.

## Backend repair segment 2

The earlier separate schema/authority fixtures and their payment/correction/
mixed-History callers now run on genuine0017 with actual Account roots:

- `775abf4` / owning12-16 fixes a real final-bootstrap omission found by retained
  adversarial tests: exact function-body hashes alone did not authenticate OUT
  argument names/types/modes. Both final preflight copies now authenticate exact
  proargnames/proargmodes/proallargtypes, including NULL expectations for scalar
  routines and trigger functions. The three original altered-OUT declaration
  tests now fail closed as intended; owner/body/path/ACL checks remain enforced.
  The separate current dividend fixture prepares quantity/units/cutoff/sequence
  before its immutable INSERT, and installs exact final runtime grants. Legacy
  retained0014 seeding uses explicit original raw columns and a0014 revision
  assertion, independent of current owned ORM/helpers. Two migration-auth cases
  now use the genuine guarded reset fixture rather than expecting upgrade0014
  to downgrade0017. No downgrade or financial immutability guard was weakened.
  Payment/hold/History consumers name their original root. Projection seeds
  include rooted fills/facts/movements and canonical version2 split digests;
  owner-only and malformed-input assertions remain. The cancellation test now
  proves cancellation happens after actual apply SQL, rather than accidentally
  stopping at the new preliminary identity query. Consecutive genuine sessions
  keep changed-ex-date tests independent of weekend timing.
- `d7d3595` / owning12-14 moves all25 retained HTTP mixed-History cases to explicit
  v2 portfolio routes, with real cookie sessions, original saved rows, bounded
  cursors, exact output/OpenAPI, no-store, causal cash and foreign-owner checks.
- `484f2a6` / owning12-14 preserves trade-History pagination/rounding/bigint and
  owner isolation with explicit OwnedActivePortfolio and canonical v2 cursor
  fixtures. Invalid roots and missing roots are covered. The query-count proof
  now requires two lifecycle checks surrounding exactly one bounded ledger
  SELECT, rather than wrongly treating required lifecycle reads as regressions.
- `49479ff` / owning12-16 preserves email HTTP resource closure against the
  genuine admitted disposable schema. The health DB-down case starts with a
  valid schema and then injects an actual request-time loopback connection
  refusal; it still requires503, private sanitized body and dependency logging.

Actual serial receipts:

- `/tmp/phase12-27-dividend-schema-fourth.log`:79 schema/authority cases pass.
- `/tmp/phase12-27-dividend-bootstrap-final.log`:176pass/2fail in223.26s; both
  failures are the subsequently corrected migration-auth fixture assumptions,
  not financial/authority failures. The two corrected cases are included next.
- `/tmp/phase12-27-dividend-history-second.log`:204pass in31.98s, including32
  bootstrap,79 schema/authority, final rooted authority, both migration-auth
  corrections, all payment/correction and real mixed-History cases.
- `/tmp/phase12-27-history-http-first.log`:25 HTTP mixed-History cases pass.
- `/tmp/phase12-27-history-lifecycle-first.log`:78 trade-History/email/health
  cases pass. A subsequent tiny cursor-fixture review separates a valid foreign
  root token from universally malformed tokens because HTTP tests import the
  latter; its dependent replay/commit is recorded below.
- Static CI/runner28, recovery10, fixture5 and selected-source8 contracts pass.
  Backend Ruff check/format and mypy101 source files pass.

No migrations, retained SQL function bodies, dependency pins, exclusions,
coverage thresholds or admissions changed. Final bootstrap source bytes did
change, so the complete final archive/cold/TLS/image campaign must still be
fresh and bind the eventual source. No Plan27 SUMMARY or whole-phase completion
claim is authorized by these bounded repair receipts.

Two final test-only commits complete this bounded segment:

- `48db6df` separates a valid foreign-root cursor from universally malformed
  vectors reused by HTTP tests; a dedicated assertion still refuses continuing
  the cursor under another root.
- `9808652` / owning12-01 updates actual head to0017 and runs original retained
  empty downgrade/base roundtrips, populated0007/0008 index preservation and
  0005/0006 cent guards on genuine authenticated retained revisions after the
  existing guarded reset. The retained index proof ends at0014; independent
  populated portfolio oracles prove the0014→0017 transition. The final0017
  downgrade refusal remains unchanged. Teardown restores genuine final head.

`/tmp/phase12-27-baseline-history-final.log` passes all80 baseline migration,
trade-History service/cursor and dependent HTTP cases in36.86s. Full backend
Ruff check and format pass226 files; mypy passes101 app source files. No
tracked deletion occurred, and all commits remain local.

## Latest unfiltered diagnostic and concrete next work

`/tmp/phase12-27-backend-fourth.log` advanced from548 to1004 passes, stopping
at40 failures in90.76s. The subsequent full unfiltered
`/tmp/phase12-27-backend-fifth.log` advances to **1822pass/34fail/6errors** in
630.94s (10m30s). It contains3023 collected cases after added malformed-root
vectors. Its five baseline migration failures are now repaired and included in
the80-case final replay above. This diagnostic predates the final cursor/
baseline test-only commits and is not a final-source full-suite pass.

The next remaining families in that actual log are:

1. `test_portfolio_service.py` (11 failures) and `test_portfolio_snapshot.py`
   (4 failures): legacy user-only valuation calls and committed snapshot fixtures
   need explicit owned roots. Preserve original one-snapshot/no-mixed-commit,
   price-clock, P/L, unavailable/inactive/zero, dividend and concurrency assertions.
   Authenticate root/lifecycle reads without replacing the authoritative single
   financial projection or faking committed-client behavior. Do not default a
   production root or weaken original finance/snapshot guarantees.
2. `test_stock_action_migrations.py` (14 failures/5 setup errors): its shared
   ledger still creates only a User, current movement/entitlement/split seeds
   omit owned roots/digest version, and its original runtime_roles/upgrade cases
   attempt forbidden final0017 downgrades. Separate genuine retained lanes and
   current0017 behavioral/ACL proofs. The raw movement helper is ALSO used by
   the deliberately old0014 `seed_legacy_books`; do not blindly root all its SQL
   or apply current ORM/services/authority to0013/14. `dividend_case` now creates
   its own real Account; do not add another default Account via ledger without
   reconciling that dependency. Use exact final bootstrap for current-role tests,
   genuine fixed retained source/revision for historical grant/body/index proofs.
   Preserve all uniqueness, causal foreign-key, hostile-role and concurrent-index
   assertions; canonical new2 global split digests do not rewrite legacy NULL.
3. `test_stock_action_resolutions.py` has one setup error at the diagnostic stop,
   initially inherited from that same old runtime_roles/downgrade fixture. Later
   cases and all later suites still require unfiltered qualification.

All database invocations in this segment were serial. The10m30 diagnostic
includes genuine migration/admission cases; it was actively progressing, not
a concurrent-pytest lock cycle. The final guarded reset restores a clean actual
0017 diagnostic schema and checks all noninternal triggers enabled. No pytest,
migration child or reset process is left active at handoff; the same verified
synthetic tmpfs DB/Redis stack remains available. Preserve its ownership guards,
and destroy only that exact stack before the eventual exclusive all-security
runner creates a fresh one. No provider/production operation or private.env read
occurred. Phase7's consumed authorization/evidence and six pending requirements
remain unchanged; stock admissions remain OFF. Continue locally without another
procedural retry question. Phase12 remains26/28, with27 incomplete and noSUMMARY.

## Backend repair segment 3 — 2026-11-17

Two additional local test-only commits repair every remaining family named in
the prior fifth diagnostic, without treating that partial diagnostic as a full
backend pass:

- `dd125be` / owning12-14 supplies verified OwnedActivePortfolio roots to the
  retained valuation and committed-client snapshot tests. Real writes and the
  negative split-reader control remain; cash, positions, price clock, exact
  original totals and dividend/correction assertions are unchanged. Root lookup
  happens before statement capture, so the original single financial SELECT
  assertion remains exact. Current missing-root behavior explicitly asserts the
  private404 portfolio_unavailable contract.
- `4d1d951` / owning12-12 separates current0017 journal constraints from genuine
  retained action migrations/ACLs. The shared User-only ledger fixture remains
  unchanged so the dividend fixture does not acquire an accidental sibling.
  Only current financial consumers create and name an actual Account root;
  current split rows explicitly carry version2. Original pre-portfolio raw
  movement columns remain in retained_movement, now explicitly imported by the
  independent0014 seed_legacy_books oracle. Original narrow scheduler trade
  reads, actual foreign causal FKs, uniqueness, nonfinite/bounded inputs,
  hostile-role, interrupted concurrent-index and downgrade refusal assertions
  all remain. The foreign split/event coin FK is exercised at INSERT, before
  immutable UPDATE refusal could obscure that causal constraint.

Historical migration/ACL tests use the guarded disposable reset rather than
trying to downgrade irreversible0017. They run genuine0010–0014 revisions;
teardown restores actual final0017. Upgrade-only grants remain separate from
deployed-bootstrap fixtures, preserving independent upgrade/bootstrap parity.
The exact retained0013 script comes from immutable commit
c408be806fdad8e8b6ee5961c123d5be52ab096c and is stored at
backend/tests/fixtures/bootstrap-roles-0013.sql with checked SHA256
06880ad0cf3592cd6d436c588eafaad8f4490560a1ae0e4dc23da120676421bb.
The checked-in exact bytes avoid depending on old git objects in shallow backend
CI checkouts. No current bootstrap is evaluated against a retained schema.

Current resolution consumers execute the complete actual final deployment
bootstrap, including its existing preceding action-grants block. The earlier
test helper's final portfolio grant fragment alone omitted that prerequisite
operator schema USAGE. No production grant, migration or runtime code changed.
The historical unsafe-operator-membership test also uses its own genuine retained
lane; current reconciliation, replay and actual gate-wait tests use0017.

Serial real-database receipts:

- /tmp/phase12-27-portfolio-final.log:29 valuation/snapshot/owned cases pass in6.18s.
- /tmp/phase12-27-action-migrations-second.log:129 current action, independent
  portfolio migration and dividend-schema cases pass in245.92s.
- /tmp/phase12-27-action-final-second.log:109 final current/retained action and
  resolution cases pass in77.61s, including actual stale gate-wait proofs.
- /tmp/phase12-27-retained-source-final.log:3 original retained parity, hostile
  role and valid-cause cases pass in17.03s using the checked-in exact source.
- Full Ruff check and format pass226 files; mypy passes101 app source files.

One first sandboxed valuation run could not create a loopback socket; the
authorized guarded escalation then ran the actual tests. No package install,
provider access, private.env, production operation or publication occurred.
No guard was disabled for these repairs. Post-replay administration verifies
actual0017 and all noninternal triggers enabled. No pytest/migration child is
left running; only the previously verified synthetic tmpfs PG/Redis stack stays
available. No tracked deletion occurred; only unrelated.claude/ is untracked.

Next: run a fresh unfiltered backend diagnostic through later families (the
old fifth run stopped at the first resolution setup error). It has not been
repeated after these commits, so later retained stock service/status/trading
callers may still need explicit-root adaptation. Then qualify full backend
coverage with all60 critical modules, the actual unchanged all-security runner,
five actual-image strict scans and one fresh same-archive seven-stage recovery.
The old archive remains untouched, and final UI packet refresh/owner/native200%
gates remain pending. Do not create27SUMMARY, advance counts or mark whole
requirements complete from these bounded receipts. Phase7's consumed campaign,
six pending requirements and OFF admissions remain unchanged. Continue locally
under the existing approval; no new procedural retry checkpoint is needed.

## Backend repair segment 4 — 2026-11-17

All28 backend test files lexicographically after test_stock_action_resolutions.py
now pass together: **1116passed/72warnings in172.46s** at4dce48c source bytes.
This is the complete later-family diagnostic, not the full backend/coverage or
all-security qualification. No earlier file is excluded from the final gate.

Local commits:

- cf6c43b roots current raw trades/facts/movements and actual final authority
  snapshots, including matching cash/holdings. Catalogue/execution downgrade
  tests use genuine retained0010/13 lanes; final0017 refusal is unchanged.
  Original invalid arithmetic, immutable records, privilege and cross-row
  causal assertions remain.74affected cases pass46.90s.
- 490efd3 roots original crypto/stock isolation proofs and scoped HTTP calls.
  Split-quote teardown uses only the existing privileged exact-target context
  for immutable global applications, with triggers enabled before/after.
  Previously failed cleanup left action state that cascaded into scheduler and
  status failures; no runtime scheduler assertion was weakened. Calendar fixture
  horizons use their actual review date, preserving the expired-review negative
  across UTC midnight.229discovery/isolation/status cases pass36.43s.
- bb70aed preserves original0013 scheduler receipt-read denial, fixed search_path
  and independent pinned historical bootstrap parity in its genuine retained
  lane, alongside current0017's required read-only journal access and mutation
  denial. Fresh connection plans follow schema changes; test SET LOCAL ROLE is
  explicitly reset before administrative parity work. The retained preservation
  case explicitly seeds crypto cash9876.54/baseline12500, holding and fill,
  rather than accidentally testing an empty reset database.
- 4dce48c supplies verified roots to original stock/crypto service calls,
  movements, valuations and HTTP concurrency cases. Rooted schema fixtures
  preserve all original constraint/precision/uniqueness assertions. Immutable
  synthetic crypto trades are removed only in privileged teardown after tests.
  Four historical reconstruction calls now pass actual portfolio_id instead of
  user_id. Standalone runs had accidentally equal identities; the combined run
  exposed and then verified the distinction without weakening the exclusive
  dividend cutoff, split quantity or immutable original receipt assertions.

Receipts:

- /tmp/phase12-27-execution-final.log:74pass/46.90s.
- /tmp/phase12-27-discovery-final.log:229pass/36.43s.
- /tmp/phase12-27-final-preservation-waits.log:87pass/41.91s, strengthened
  populated retained preservation plus all stock wait cases.
- /tmp/phase12-27-backend-tail-qualified.log:all28later files,1116pass/172.46s.
- Full Ruff check/format:226files; mypy:101app sources pass.

The full unfiltered backend suite has NOT been rerun after these repairs.
Next executor must run it with80% overall and all60critical modules100%branch,
then complete the actual unchanged all-security runner, five actual-image
strict scans and fresh same-archive seven-stage recovery. Final UI packet refresh
and separate owner/native200% gates remain pending. Source/runtime/tooling bytes
did not change in this segment; all changes are fixtures/tests and this record.
No new dependencies, providers, private configurations, production or publication.

All DB tests were strictly serial. The guarded disposable schema reset restores
genuine0017 and verifies all noninternal triggers enabled; its log is
/tmp/phase12-27-backend4-final-reset.log. No pytest/migration process is left;
only the previously verified owned tmpfs PG/Redis diagnostic stack remains.
Before final all-security, clean only this exact verified stack so the runner
can create its own exclusive one. Preserve the old recovery directory and all
prior source/archive guards. Phase12 remains26/28; no27SUMMARY or requirement
completion follows from these focused receipts. Phase7's consumed campaign,
six pending requirements and OFF admissions remain unchanged. Keep work local.

## Full backend and critical-refusal segment — 2026-11-17

The full unfiltered backend branch-coverage diagnostic ran at670b7ba, tree
f9cf760753d081e525ceaeb029aa24effd5547ef. It completed all3032 collected cases:
**3001passed/31failed/119warnings in772.38s**, overall97.16%. Every failure was
in test_portfolio_migrations.py and had the same genuine retained0014 oracle
problem: seed_legacy_books still imported the now-current insert_trade helper,
which queries accounts.closed_at and inserts portfolio_id. Neither column
exists at0014. This was introduced by the later current execution fixture
repair, after the earlier independent migration replay; it was not a runtime
or migration failure. No other family failed in the full diagnostic.

- 5c90b3e / owning12-01 removes that current helper dependency. The independent
  oracle asserts actual0014 and inserts the exact original stock fill columns,
  quantity2, mid/exec10, fee0, delta-20 and cash_after9980. Original economic
  projection, two-owner global split, complete receipts, preserved original
  bytes and finite migrator/refusal assertions are unchanged. All45 genuine
  migration/preservation/interruption/refusal cases pass177.70s afterward.
- 51ac797 / owning12-14 verifies History encoders reject bool/string/None root
  coercion, and retired History modules expose only the shared refusal router.
- 4398c36 / owning12-16 uses actual retained migrations, isolated deliberate
  malformed revision metadata and a fresh driver connection to prove multirow
  and integer revision results refuse. A new driver is important: otherwise
  ALTER COLUMN can stop earlier at a stale prepared-plan error instead of
  exercising the actual non-string admission check. No valid migration or
  production catalogue is changed by this adversarial fixture.
- d1f7050 / owning12-12 exercises actual journal root lineage, legacyNULL
  ambiguity when sibling roots share one user, a corrupt version2 digest,
  missing roots and refusal of postclosure historical cutoffs. The latter uses
  a database timestamp after closure, already in the past at reconstruction;
  future cutoffs correctly hit the earlier missing_baseline guard.
- 28e6cd6 / owning12-11 proves inner stock financial reads cannot substitute an
  absent root and inner replay cannot accept an original crypto fill. Actual
  restricted portfolio finances remain unchanged on refusal.

Actual receipts:

- /tmp/phase12-27-fullbackend-coverage-first.log: full3032 run above, nonzero.
- /tmp/phase12-27-retained-oracle-final.log:45pass/177.70s after oracle fix.
- /tmp/phase12-27-critical-refusals.log:327pass/1new-test fixture failure/98.83s
  across six affected files. The failure was the future cutoff described above,
  corrected to the actual database clock; existing assertions were not weakened.
- /tmp/phase12-27-critical-refusals-corrected.log:3pass/10.80s, corrected closure
  case plus both strengthened actual malformed revision cases.
- Full Ruff check/format226files and mypy101 app sources pass.

The coverage data currently appends those focused refusal diagnostics to the
earlier failed full run. It is **diagnostic only**, not final same-source whole
qualification. The exact CI60-module command was run without changing any
inventory/threshold/exclusion and exits2. Latest diagnostic scope is recorded
in /tmp/phase12-27-critical-after-refusals.log:

| Critical module | Remaining missing lines/branches |
|---|---|
| app/db/dev_bootstrap.py |87–88,93–184,309;52% |
| app/db/portfolio_migrate.py |3–180;0% |
| app/services/corporate_actions.py |659→662 |
| app/services/event_history.py |351 |
| app/services/stock_ownership.py |495,497 |
| app/services/stock_trading.py |383→386 |

The bootstrap/migrator have genuine subprocess deployment proof, but currently
lack backend in-process coverage for their finite orchestration/authentication
and failure cleanup. Add meaningful tests for those boundaries; do not exclude
them or mistake subprocess proof for measured backend100%. All other54critical
modules are100% in this diagnostic, including actual schema_contract after the
fresh-driver malformed test. Final full unfiltered pytest/coverage must run anew
after all branch repairs, followed by actual all-security and the fresh exact
same-archive seven-stage recovery. A test-only fixture repair is not a reason to
reuse the earlier failed result as a final pass.

At handoff no pytest/migration process remains. Read-only administration of the
exact owned tmpfs birja-test stack verifies actual0017, zero disabled noninternal
triggers and zero other active database sessions. That synthetic stack stays
running for diagnostics, not exclusive-run adoption. Only unrelated.claude/ is
untracked; all tracked changes are committed. No application/runtime, SQL asset,
dependency, provider, private configuration, production or publication change
occurred in this segment. Phase12 stays26/28, no27SUMMARY, final UI/native200%
remain pending, and Phase7's consumed campaign/six gaps/OFF admissions are intact.

## Critical branch repair segment — 2026-11-17

All six remaining critical-module diagnostic gaps now have behavioral tests;
no runtime, migration, SQL asset, package, threshold or exclusion changed:

- a9e9da6 / owning12-16 adds finite dev/migrator orchestration tests. Exact
  source bytes, missing/changed/symlink source refusal, explicit endpoint
  admission, child success/failure/spawn/timeout, redacted CLI failures,
  advisory-lock release, engine disposal and temporary login revocation are
  asserted at their process/construction seams. Authentication/catalogue tests
  use actual credentialed birja_migrator connections and genuine0017 or an
  intentionally empty disposable schema: unsafe schema CREATE, multi-version,
  unexpected relation/routine/owner and wrong authenticated identity refuse.
  Actual asyncpg multi-statement final preflight/grants execute against0017;
  scheduler cash UPDATE remains denied and the narrow root-lock call admitted.
- 91cca3c / owning12-12 proves a real sold-out root advances global units while
  retaining sequence2 and exactly its two original movements. Actual closed
  unjournaled holdings refuse interpretation. A loaded holding with a stale
  in-memory owner mismatch also refuses; the invalid pair is never flushed
  through the real composite FK. No financial SQL constraint is disabled.
- 48ddd79 / owning12-14 preserves a real paid dividend and immutable History
  original, fault-injects an empty subsequent projection SQL read and asserts
  Incomplete owned History projection rather than a falsely complete empty
  page. The paid original still reads intact afterward. No fabricated cash,
  entitlement or journal is used to claim a successful financial action.
- d214119 / owning12-11 extends the existing actual-finance retry/race test with
  immediate original detection and a transient miss after that detection. The
  next locked lookup returns the exact original receipt with no duplicate
  effect; unchanged financial snapshots remain asserted.

Actual serial receipts:

- /tmp/phase12-27-critical-real-migrator-first.log:26pass/34.91s, real
  authenticated catalogue and orchestration proofs.
- /tmp/phase12-27-critical-final-focused.log:80pass/40.01s at final test bytes,
  all new bootstrap/migrator/financial branches and original retry negatives.
- /tmp/phase12-27-critical-stock-replay-final.log:6pass/5.69s including the final
  transient locked lookup-miss case.
- Full Ruff lint/format227files and mypy101 app sources pass; diff check passes.
- /tmp/phase12-27-critical-diagnostic-final.log:exact CI60-module inventory,
  5020statements/1604branches, zero misses/partials,100%, exit0.

The coverage file still appends focused diagnostics to the earlier failed full
run. It is **not final qualification**. Next execute a fresh unfiltered backend
branch coverage run with80% overall and the exact60critical100% report from
that clean run. Then complete the unchanged actual all-security graph, all five
actual Dockerfile/image strict scans/audits/browser, and one new same-archive
seven-stage current/retained recovery campaign. Do not reuse appended data or
the earlier3032 failed run as final proof. Preserve/move the old fixed recovery
directory whole before exclusive packaging; no overwrite/rebuild midcampaign.
Final source-bound UI packet refresh and separate owner/native200% acceptance
remain pending. Do not create27SUMMARY or advance26/28 from these receipts.

At handoff the same verified owned tmpfs test stack remains running. Sanitized
administration confirms genuine0017, zero disabled noninternal triggers and
zero other active DB sessions. No pytest/migration process remains. Before the
exclusive all-security runner, clean only this exact verified test Compose so
the runner creates its own stack. Tracked tree is clean after commits; only
unrelated.claude/ remains untouched. No provider/private production access,
installation, publication or branch switch occurred. Keep local and preserve
Phase7's consumed campaign, six pending requirements and OFF admissions.

## Actual all-security campaign and browser handoff — 2026-11-17

The actual unchanged `--suite all-security` runner now has a complete passing
backend/critical/frontend/audit prefix at committed source
261f617f180a4a7c6764a0f262e4f87bb939ad70, tree
1ae42755f3735d42f708076b5b94d809f865f0d1. The whole runner is **not passed**:
it stops at retained browser fixtures, before the three final Dockerfile builds
and strict five-image scans. Plan27 remains incomplete; there is no SUMMARY.

Before the campaign, exact Compose labels, checkout/config paths, pinned images,
loopback55432/56379 and tmpfs/no persistent mounts were verified. The old owned
diagnostic stack was removed, allowing the runner to create its own fresh one.
No competing pytest/Alembic process was present. All DB testing remained serial.

The first actual campaign at fc5da53 completed3090 cases with3049pass/41fail
in867.39s, overall99.40%. All41 failures were the deliberate outer environment's
PRICE_SOURCE=fake selecting a different path in old production trust/config
and mocked-Kraken scheduler tests. Exact critical coverage had59modules100%;
only tasks/scheduler.py missed14lines/5branches because its mock source was not
selected. All actual portfolio migrations/finance cases passed. This was an
environment-dependent test fixture mismatch, not a runtime source-policy bug.

261f617 / owning12-26 makes those six test files explicit: production trust and
secret tests select a production-valid Kraken setting; mocked-Kraken scheduler
fixtures select their mocked source; default-source tests remove only the
PRICE_SOURCE override. Explicit fake-production refusal cases remain unchanged.
All183 affected cases pass25.74s under the **exact runner environment**. No
runtime setting, network mock, provider boundary, threshold or runner gate was
weakened. Ruff/format227files and mypy101 app sources pass.

Fresh actual unchanged runner receipts at261f617:

- /tmp/phase12-27-all-security-final-second.log: **3090/3090 backend pass**
  in846.96s, overall99.85% branch coverage (6409statements,1796branches).
- The same clean run's exact CI60-module critical report: **100%**,
  5020statements/1604branches, zero misses or partials.
- Python pip-audit: no known vulnerabilities.
- Frontend lint, build-project TypeScript and whole Prettier pass.
- Full frontend44files/958tests pass; coverage97.50%statements,
  94.65%branches,98.58%functions and98.68%lines. Production Vite build passes.
- npm audit --audit-level=high passes: zero HIGH/CRITICAL;14 MODERATE
  findings remain reported. This is not a claim of zero npm findings.

Full tracked source hash inventory is preserved in
/tmp/phase12-27-security-source-second.json; comparison after the campaign
found zero changed tracked files. The qualified clean backend coverage data
and source inventory are preserved under
/tmp/phase12-27-qualified-backend-261f617/ for later exact-source comparison.
The earlier first failed campaign/source record and focused repair logs remain
separate; none is described as a final all-security success.

### Actual browser diagnostic and next repair scope

The runner built a new synthetic isolated browser stack, applied the guarded
operator/legacy seed and launched all60 tests. It exposed three concrete old
contracts, then the fourth test waited on an obsolete v1 response. The exact
Playwright process received SIGINT to retain its report instead of waiting
through already-known obsolete URLs. This was a failing **diagnostic**, not a
filtered final qualification: **3failed,1interrupted,1existing CSPskip,
55did not run**. Full60 must still run and pass under unchanged scope/gates.

Evidence: /tmp/birja-phase09-browser-7oqwmmd2/browser-all.log; its private build,
startup and cleanup logs remain alongside it. Detailed error-context.md and
trace.zip artifacts remain in frontend/test-results for these test names:

- auth: a new user signs in, stays signed in, signs out and signs in again.
  It still expects $10,000 on the now identity-only Account screen. Preserve
  the actual grant/no-regrant/session assertions through the owned portfolio;
  Account must remain email/session-only.
- dividends-history: authenticated mixed History starts empty. It requests
  /api/v1/history and correctly receives409 portfolio_required, rather than
  the intended scoped mixed History page.
- dividends-history: real restricted worker credits once and publishes
  uncertainty with no cash change. Actual worker/economic assertions pass up
  to the same obsolete History request; its error response has no items.
- dividends-history: actual mixed pages preserve originals, responsive focus
  and failed-read recovery. Interrupted while cryptoFill waited for a
  /api/v1/trades response, whereas the real UI uses its explicit v2 root.

Read the full retained e2e files before adaptation: auth.spec.ts,
dividends-history.spec.ts, stock-trades.spec.ts, portfolio-history.spec.ts,
trading.spec.ts and their helpers/fixtures. Remaining v1 financial API and old
route/focus expectations need explicit verified root IDs. Public stocks remain
v1; old unscoped financial APIs must continue refusing. Existing
portfolio-ownership.spec.ts supplies current root-aware patterns. Preserve all
original exact cash/quantity/fee/History/replay/keyboard/reflow assertions and
real restricted worker facts; do not introduce a production fallback or reduce
the all60 suite. The worker fixture already completed real payment before its
old History assertion failed. No new product bug is established by this run.

Both browser and security runners executed cleanup. Read-only followup verifies
zero test containers and zero browser-project containers/networks/volumes;
there is no pytest/Alembic process. The diagnostic DB no longer exists: the
next repair must create its own guarded isolated stack, not assume a running
one. Unrelated.claude/ is the only untracked path and is untouched.

Next: reconcile/replay all retained browser cases with explicit ownership, then
finish the actual all-security graph including all final five strict images.
Reuse passing-prefix data only as truthful source-bound evidence, never claim
the whole runner passed from it. Once final source is qualified, task02 still
needs the fresh exclusive one-archive seven-stage recovery campaign and a new
actual-source UI packet; preserve/move the whole old private proof directory
before packaging, never rebuild between stages. Plan28 owner UI/native200%
remains blocking. Phase12 stays26/28; all requirements stay unchecked. No new
dependency/provider/private production/publication action occurred. Phase7's
consumed campaign/six pending requirements/OFF admissions are unchanged.
