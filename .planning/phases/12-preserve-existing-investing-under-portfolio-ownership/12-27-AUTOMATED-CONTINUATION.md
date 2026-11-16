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

## Remaining backend work / next concrete step

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
