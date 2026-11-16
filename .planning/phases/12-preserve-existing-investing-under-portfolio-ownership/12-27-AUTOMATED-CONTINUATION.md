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

## Remaining backend work / next concrete step

Full backend diagnostic invocation `uv run pytest -q --maxfail=20` now collects
and reaches **415passed/20failed** in25.96s. The first failing group is retained
`test_corporate_actions.py`; the root cause is legacy synthetic financial rows
omitting required0017 `portfolio_id`, not failed execution guards. See private
`/tmp/phase12-27-backend-second.log`; all20 names are in its final summary.

Read `tests/stock_action_fixtures.py` first: `synthetic_opening` inserts a movement
and Holding without the required root; `synthetic_fill` inserts Trade and
StockFillFacts without it. These helpers are explicitly synthetic, use the
isolated `new_user` fixture and current-head schema. Bind them to their actual
fixture-owned original account (or add an explicit helper argument for sibling
cases), never add a production default/fallback or relax schema constraints.
Current test-only fixtures can obtain the root from the created Account; assert
the intended sole/original test account rather than guessing arbitrary roots.

Many direct `StockMovementInput` constructions in retained
`test_stock_ownership.py` / `test_corporate_actions.py` also need explicit roots
under owning12-12. Some retained journal callers now require portfolio identity
instead of user identity. Preserve the actual historical split/economic/late
buyer/zero-holder/rollback/oversell/race assertions. Scope all fixture Holding,
Trade, facts and journal rows consistently; do not disable immutable/FK/authority
guards around behavior-under-test.

Further expected retained work already recorded by earlier plans:

- current-versus-retained migration head/downgrade fixtures:0017 intentionally
  refuses downgrade. Exact old-schema cases require genuine retained sources,
  explicit supported revisions and authenticated migration child identity.
- `tests/dividend_fixtures.py` assumes obsolete role/signature/bootstrap and
  user-only service calls; use existing current ownership/dividend fixture
  patterns without broadening privileges.
- retained History/service/API readers still need explicit roots and scopes;
  only collection and standalone mixed cursor/wire tests were repaired here.
- strict backend60-module100% branch /80% overall coverage remains pending,
  including the new startup/role/TLS modules. No exclusion or gate change.

## Test stack ownership and cleanup

The initial prescribed all-security runner correctly refused a preexisting
`birja-test` stack before writes (`/tmp/phase12-27-first-security.log`). Parent
confirmed nobody else uses it. Read-only inspection verified exact own checkout
Compose labels/config, pinned PG/Redis, loopback55432/56379 and **no persistent
volumes**; these are the synthetic tmpfs containers created08:57:41 today.
They were used only for diagnostics and **remain running** for the continuation.
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
