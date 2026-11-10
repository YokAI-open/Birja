---
phase: 04-trading
verified: 2026-10-29T13:02:00Z
status: passed
score: 5/5
requirements_verified: [TRADE-01, TRADE-02, TRADE-03, TRADE-04, TRADE-05, TRADE-06, TRADE-07, TRADE-08]
overrides_applied: 0
human_verification: []
---

# Phase 4: Trading Verification Report

**Phase goal:** As a signed-in Birja user, I want to buy and sell coins at
real, recent market prices with the full cost shown before I confirm, so
that I can practise trading and get a result that is correct to the cent.

**Status:** passed; initial verification, all five roadmap criteria verified.

Verification was completed inline by Codex after the delegated verifier
failed with a usage limit (`agent.classify-failure`: `quota-exceeded`). No
partial verification artifact existed. This is a separate verification
pass, not an independent agent review. The independent code review and its
focused hotfix re-review are recorded in `04-REVIEW.md`.

The roadmap's short goal was synchronized with the existing user story in
the Phase 4 plans. Its five success criteria and scope were preserved.
All ten plans' must-haves, context decisions and summaries were checked
against implementation and test assertions; summaries alone were not
treated as proof of behavior.

## User Flow Coverage

| Step | Expected | Code and completed user evidence | Status |
| --- | --- | --- | --- |
| Open Markets and Trade BTC | Signed-in user reaches the coin's trade form | `App.tsx` gates routes through `AuthSwitch`; `MarketsPage.tsx:98` links to `/trade/${item.symbol}`; dev and live checks approved | VERIFIED |
| Enter amount or quantity | Server computes all costs before confirmation | `TradePage.tsx` validates/debounces input, calls `useQuote`, renders mid, execution price, fee, quantity and cash change | VERIFIED |
| Confirm buy | Exact fee-inclusive cash debit and stored fill | `trading.execute` calls `plan_trade`, commits cash/holding/trade together; API and e2e assert $100 buy leaves $9,900.00 | VERIFIED |
| Sell holding | Quantity sale, including the whole-position minimum exemption | `TradePage` loads actual holding; service/math enforce available quantity; CI trade e2e completes the round trip | VERIFIED |
| Observe result | Actual quantity, execution price, fee and resulting cash | Fill is built from the stored trade, returned through `FillOut`, rendered under the named Order filled region; successful mutation invalidates account, holding and prices | VERIFIED |

## Goal Achievement

### Observable Truths

| # | Roadmap success criterion | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Buy by dollar amount with exact fee-inclusive cash debit; buy/sell fractional quantity up to eight decimals | VERIFIED | `trade_math.plan_trade`: USD cash_delta = -value, floor8 quantity; quantity paths use explicit cents rounding. `QuoteIn` permits exactly one positive finite input, USD <=2 dp, quantity <=8 dp, sell quantity only. Math, API and TradePage tests cover all input paths. |
| 2 | Itemized preview before confirmation and actual fill/new balance afterwards | VERIFIED | Both quote and execute use `plan_trade`; `QuoteOut` exposes all preview fields. `TradePage` renders those fields, then `FillOut` values. API test `test_execute_buy_then_replay_is_byte_identical` compares cash_after with `/me`; CI e2e asserts visible preview/fill and exact $9,900.00. |
| 3 | Refuse stale price clearly; replace preview when the price changed | VERIFIED | `trading._require_fresh` reuses Phase 3 `age_seconds`/`freshness`, refusing age >=120. Real clock is sampled after account lock/price read. Mismatching mid raises `PriceChanged` before writes; API returns detail.quote; page installs it and requires another confirmation. Context D-03 explicitly defines changed price as changed mid; a newer timestamp with unchanged mid is allowed and recorded. |
| 4 | Refuse insufficient cash/coins and below minimum, allow whole-position sale; execute retries only once | VERIFIED | `plan_trade` checks funds/quantity/minimum and caps sell fee at notional. Account lock precedes replay lookup; unique (user_id, idempotency_key) backs it. Replay precedes freshness and returns the original fill; changed payload conflicts. UI keeps the key across unknown outcomes/refetches; real-PG same-key concurrency asserts one 201, nine 200 and one trade. |
| 5 | Parallel real-Postgres buys cannot overspend; exactly affordable number succeed | VERIFIED | `test_parallel_buys_never_overspend` issues 15 concurrent HTTP requests with independent sessions: 10 fills, 5 insufficient_cash, final cash 0.00, ten trade rows, matching quantity/cost basis and every intermediate cash_after nonnegative. Account FOR UPDATE serializes execution; DB CHECK independently forbids negative cash. Latest hotfix CI backend job passed this test. |

**Score: 5/5 roadmap truths.** No scope overrides or Phase 4 deferrals.

### Plan-Specific Must-Haves

| Plan | Additional contract checked | Evidence and result |
| --- | --- | --- |
| 04-01 | Fresh develop branch; RED e2e target; price_changed tolerance | Original branch/commits and merged PR #19 preserve ancestry; `frontend/e2e/trade.spec.ts` uses signInNewUser, checks buy/sell results, bounds reconfirmation to three attempts. VERIFIED. |
| 04-02 | Configured costs, precise rounding, minimum fee, capped sell fee, cost basis, pure math and 100% coverage | Settings defaults 0.0025 spread/fee, $0.01 minimum fee, $1.00 order; validators enforce bounds/cents. `trade_math.py` has no I/O; worked examples and seeded invariants assert results. Persisted coverage independently reads 100% statements/branches. VERIFIED. |
| 04-03 | Database invariants, exact price/as_of record, cost basis, guarded cents migration and downgrades | `Holding`/`Trade` models and migrations 0006/0007 contain uniqueness/checks and numeric/timestamptz columns; schema tests exercise rejected writes. Migration tests include round trip, guard rejection and model/schema parity. VERIFIED. |
| 04-04 | Decimal-string transport; structured errors; TanStack quote timing; mutation invalidation | `api/trades.ts` guards responses from apiFetch; client preserves detail. Page debounces 300 ms; useQuote refetches 30s with retry:false. useTrade invalidates me/holding/prices. VERIFIED. |
| 04-05 | Signed-out smoke checks, rollout/rollback instructions, no new production services/ports/env vars | `trading_requires_auth` is called by smoke modes; offline test exercises refusal statuses; RUNBOOK Trading section covers migrations, cents precheck and rollback. Actual release smoke 38/38 origin, 9/9 public. VERIFIED. |
| 04-06 | Atomic lock/replay/price/holding/plan/apply ordering, cost basis and shared freshness definition | `trading.execute` traces this order, commits once and rolls back refusals. Freshness uses the late clock fixed by d0ee5fd. Both trade modules appear in CI and CLAUDE critical coverage lists. VERIFIED. |
| 04-07 | Route guards, live preview, clear refusals, retry key lifecycle, actual fill | App/Markets route wiring and TradePage handlers/render branches checked. Tests assert double click, retry after refetch, price_changed, terminal refusals, stale state, unknown symbols and cache refresh. VERIFIED. |
| 04-08 | Auth/CSRF, validation, structured errors, read-only quote, plain decimals, replay statuses and concurrency | Thin registered routes use CurrentUserDep and CSRF on both POSTs. Schemas reject invalid input and format all monetary JSON with format(v, 'f'). API tests cover 401/403/404/409/422, 201 new/200 replay and no writes on refusals; concurrency tests use real Postgres. VERIFIED. |
| 04-09 | Full validation, approved live-price dev flow, authorized PR/release choice | Local/CI evidence in validation record, explicit go/approved and push-pr/release-now, aggregate dev trade count 2. PR #19 merged after CI passed. VERIFIED. |
| 04-10 | Authorized git-flow release, cents precheck, deployment, smoke and human live trade | v0.3.0 tagged on main PR #20 merge, back-merged via #21; both green. Precheck 0; migrations applied; one release deployment; user-approved live buy/sell, aggregate count 0 -> 2. Subsequent reviewed hotfix v0.3.1 followed PR #22/#23 and separate deployment. Version 0.3.0 is verified at its release tag; current files correctly read 0.3.1. VERIFIED. |

### Required Artifacts and Key Links

All 24 declared artifact entries exist and are substantive. SDK artifact
queries passed for plans with artifacts; 04-09 declares none. Historical
version requirements were additionally checked against v0.3.0. The SDK's
substring match is not a substitute for that historical version check.

| From | To | Wiring verified |
| --- | --- | --- |
| MarketsPage / App | TradePage | Actual Link target and signed-in Route element |
| TradePage | useQuote / useTrade / useHolding / usePrices / useMe | Hook results drive enabled state, input, preview, holding and fill |
| Quote/trade/holding hooks | api/trades.ts -> api/client.ts | Imported functions invoked by TanStack query/mutation, CSRF handled centrally |
| api/v1/router.py | api/v1/trades.py | include_router(trades_router) registers three endpoints |
| Trade endpoints | trading service | Calls quote, execute, holding_quantity with session-derived user ID |
| Trading service | trade_math / prices / database | Real imported plan_trade/cost_basis_after and freshness calls; Account/Holding locks and Trade insert |
| Models and migrations | users/coins/accounts | Real ForeignKey("users.id") / ForeignKey("coins.id"), down_revision 0006, named checks and unique constraints |
| Trade e2e | signInNewUser and CI | Helper import invoked; CI config uses fake prices and Playwright |
| Smoke offline test | smoke-prod.sh | Sources real function and stubs curlq; production script invokes it |
| Feature/release/hotfix branches | develop/main | PR #19-23 merge records and tag ancestry verified |

SDK key-link queries produced false negatives for descriptive targets,
escaped regular expressions, TypeScript alias imports and branch names
treated as filenames. Each affected link above was manually traced in
source or git/PR history; none is missing or unwired. All 18 declared links
are accounted for.

### Data-Flow Trace (Level 4)

| UI data | Real source | Flow result |
| --- | --- | --- |
| Coin price/freshness | usePrices -> authenticated prices API -> Coin/Price query populated by Kraken scheduler | FLOWING; production smoke observed all 15 prices |
| Preview | useQuote -> fetchQuote -> post_quote -> trading.quote -> real Price, Account.cash, Holding.quantity -> plan_trade -> QuoteOut | FLOWING; no hardcoded preview values |
| Held quantity | useHolding -> authenticated holdings route -> Holding query scoped by session user ID | FLOWING; no holding returns decimal zero intentionally |
| Fill/new cash | useTrade -> executeTrade -> locked transaction -> stored Trade -> FillOut -> mutation.data | FLOWING; actual persisted fill rendered and related queries invalidated |

### Behavioral Spot-Checks

Read-only, process-local checks were run without starting services or
calling auth/trading endpoints. PYTHONDONTWRITEBYTECODE=1 and Python -B
prevented bytecode writes; only pure trade_math was imported, no settings
were instantiated and no env file was read.

| Behavior | Command / assertion | Result |
| --- | --- | --- |
| Exact fee-inclusive buy | `PYTHONPATH=backend backend/.venv/bin/python -B` invokes plan_trade at mid 100000 with $100 | cash_delta -100, cash_after 9900, fee .25, quantity .00099501; PASS |
| Whole-position dust sale | Same pure-module check, sell .00000001 BTC | Allowed, nonnegative proceeds, holding zero; PASS |
| Funds/minimum refusals | Same check with $99 cash, oversell and $.99 buy | insufficient_cash, insufficient_quantity, below_minimum; PASS |
| Critical trade coverage | `backend/.venv/bin/coverage report --data-file=backend/.coverage --include='*/app/services/trade_math.py,*/app/services/trading.py' --fail-under=100` | Both modules 100%, no missing branches; PASS |
| Unchanged tested application | `git diff --exit-code origin/develop HEAD -- backend frontend deploy .github CLAUDE.md AGENTS.md .codex docs scripts` | No difference; PASS |
| Release ancestry | `git merge-base --is-ancestor v0.3.1 origin/main` and origin/develop | Both exit 0; PASS |
| Production identity | Read deploy-log tail and production checkout HEAD | Both 0107706617b8bbf9c1a069f3e3ccc9c53b9ab2f7 (v0.3.1); PASS |
| Codex migration setup | `python3 scripts/sync-codex-skills.py --check` | 68 skills, 33 roles; PASS |

### Regression and Probe Evidence

- Latest full backend suite: 481 passed, 99.88% overall, critical list 100%.
  Frontend: 161 passed, 98.88% statements / 99.76% lines. Lint, format,
  types, builds and dependency audits passed as recorded in validation.
- Direct GitHub read confirms PR #23 merged as dd50ad7 with backend,
  frontend, image, e2e and ci-pass all SUCCESS in run 40848088770. No
  application changes followed that tested head.
- Prior auth/account/prices/health/scheduler and migration behavior is
  covered by those suites. Schema drift check found no drift; structural
  drift check skipped because no STRUCTURE.md exists (non-blocking).
- Probe discovery found no declared probe scripts or conventional
  scripts/*/tests/probe-*.sh. No missing probe or substituted probe claim.

### Requirements Coverage

| Requirement | Source plans | Status | Implementation evidence |
| --- | --- | --- | --- |
| TRADE-01 | 01,02,03,06,07,08,09,10 | SATISFIED | Exact USD debit in plan_trade; input schema; buy form and end-to-end assertion |
| TRADE-02 | 01,02,06,07,08,09,10 | SATISFIED | Eight-decimal quantity schema; buy/sell math and controls |
| TRADE-03 | 01,04,05,06,07,08,09,10 | SATISFIED | Server QuoteOut plus rendered five-line preview before Confirm |
| TRADE-04 | 02,03,06,09,10 | SATISFIED | Configured spread/fee and explicit Decimal rounding; exact trade price/as_of stored |
| TRADE-05 | 04,06,07,08,09,10 | SATISFIED | Freshness >=120 refusal after DB wait; changed mid returns fresh quote with no write and new confirmation |
| TRADE-06 | 02,03,06,07,08,09,10 | SATISFIED | Funds, quantity, minimum checks; whole-position exception; DB backstops |
| TRADE-07 | 03,04,06,07,08,09,10 | SATISFIED | User/key uniqueness, locked replay, stable retry key, same-key concurrency |
| TRADE-08 | 01,04,05,07,08,09,10 | SATISFIED | Stored fill serialization/rendering and account refresh |

All eight Phase 4 IDs appear in plans and REQUIREMENTS.md. No orphaned IDs.

### Anti-Patterns and Disconfirmation

The scan of 46 reviewed files found no TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER,
console-only handler or unfinished implementation. Initial empty/null UI
state is populated by real queries/mutations, not a static data source.

Three failure hypotheses were checked explicitly: price aging during a
lock wait, retry after an unknown outcome and concurrent overspending.
The first was a real defect (CR-01), now fixed in v0.3.1 with regressions
that observe actual PostgreSQL blocking before advancing the clock. The
other two have specific behavioral assertions, not just line coverage.

The initial static-time freshness tests did not prove lock-wait aging;
the new tests now reject at ages 120/121 with zero writes and retain a
119-second fresh control. Quote-read aging and stale-price replay are
also covered. No remaining partial Phase 4 requirement or uncovered
error path was identified in this pass. This is not an exhaustive proof
of absence of defects.

### Completed Human Verification

Dev: explicit go before rebuild and approved after the real-price buy/sell
flow; aggregate trade count 2. Production: the user approved the live flow
(`appoved`, followed by `approved`); aggregate count rose from 0 to 2.
Evidence and steps are preserved in `04-VALIDATION.md` and
`04-10-RELEASE-CHECKPOINT.md`. Existing approval is reused. The hotfix
changes an edge case after DB waits; UI and ordinary successful flows are
unchanged and covered by the later green CI e2e.

### Human Verification Required

### Gaps Summary

No remaining Phase 4 gaps. Portfolio valuation, P/L and paginated history
remain Phase 5 work; nightly off-server backup/restore remains Phase 6.
Neither future phase is marked complete by this verification.

_Verifier: Codex, inline gsd-verifier role; verified 2026-10-29._
