---
phase: 05-portfolio-and-history
verified: 2026-10-30T13:54:46Z
verified_commit: d4eda41
ci_verified_commit: 0595c89d413dc7248118329f646c5888d4ab72af
verification_scope: Final scoped re-verification after Plan 05-08 checkpoints and actual CI
status: passed
score: 25/25 merged must-haves verified
roadmap_score: 4/4 success criteria verified
requirements_score: 7/7 requirements satisfied
overrides_applied: 0
re_verification:
  previous_status: human_needed
  previous_score: 21/25
  previous_commit: b9dd826
  gaps_closed:
    - Responsive real-browser usability and user checklist approval
    - Actual full-flow and responsive fake-price/console-email CI execution
    - Fresh rebuild and real-price UAT checkpoints
    - Scoped push/PR and release decisions
  gaps_remaining: []
  regressions: []
---

# Phase 5: Portfolio and History Verification Report

**Phase Goal:** As a signed-in Birja user, I want to see my current portfolio value and profit or loss alongside every past trade, so that I can understand how my practice investments are performing.

**Verified:** 2026-10-30T13:54:46Z at `d4eda41`

**Status:** passed
**Re-verification:** Yes — initial `b9dd826` audit was human_needed, 21/25. All four warning concerns are now resolved.

All four roadmap criteria, seven requirements and 25 merged truths are verified. Plan 05-08 has actual rebuild/UAT/decision records. [PR #25](https://github.com/YokAI-open/Birja/pull/25) is open into develop. Merge still requires separate approval; release/deployment is skipped. This report grants no additional authority and changes no shared completion metadata.

## User Flow Coverage

The MVP goal passed centralized story validation in the initial audit. Acceptance now combines the source/data-flow trace, explicit user approval and actual CI, rather than SUMMARY claims.

| Step | Expected | Evidence | Status |
|---|---|---|---|
| Open signed-in app | Private pages remain session-gated | AuthSwitch, registered routes and CurrentUserDep; identity/isolation regressions and successful CI | VERIFIED |
| Open Portfolio | Actual cash/holdings/total at mid and used-price times | One financial SELECT → Decimal response → guarded query → rendered page; user-approved SC1 | VERIFIED |
| Understand performance | Total return against stored start and complete fee-inclusive holding metrics/allocation | Pure exact math/null/zero tests; real rendered values; user-approved SC2/SC3 | VERIFIED |
| Read History / Load more | Stored newest-first complete fills and deterministic pagination/retry/end | User-scoped tuple seek, cursor/infinite query, meaningful page tests; user-approved SC4 checklist and actual buy/sell story | VERIFIED |
| Navigate / refresh / sign out | Responsive routes, zoom/keyboard usability, retained focus/privacy | Approved checklist, actual four-width browser CI, focus fix and clean independent review; prior identity regressions | VERIFIED |
| Outcome | Understand investment performance alongside past trades | Four roadmap outcomes supported by substantive wired source, accepted human review and actual successful CI | VERIFIED |

## Goal Achievement

### Observable Truths

The same merged 25 truths are retained. Previously passed financial/backend/cache items received a regression check: no backend, query-hook, schema, financial component or cache implementation changed since the initial audit. The focused new production/test diff was read in full.

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | User sees cash, each holding and total portfolio value at current mid prices, along with the "as of" time of the prices used | VERIFIED | `portfolio.py:45-62` projects actual cash/start, positive holdings, all owned coins and optional Price.mid/as_of in one statement. `portfolio_math.py:57-61` values raw quantity × mid. PortfolioPage renders the returned data; holding and summary times come from that response. |
| 2 | User sees total profit/loss against the $10,000 start in dollars and percent | VERIFIED | `portfolio_math.py:62,101-103` uses stored starting_cash, raw total and explicit rounding; PortfolioPage:81-92 renders independent signed dollar/percent outcomes and stored-start copy. Pure worked and liquidation cases passed in the initial audit. |
| 3 | For each holding, user sees quantity, average cost (fees included), current value, unrealized P/L in dollars and percent, and its allocation share | VERIFIED | Calculator derives each field from quantity/basis/mid; `trade_math.py:181` adds the full negative cash delta to buy basis. `trading.py:286-302` persists basis atomically. PortfolioHoldings uses all returned fields in table/cards, without browser financial calculation. |
| 4 | User sees past trades newest first (date/time, coin, side, quantity, execution price, fee, total), and a long history loads page by page | VERIFIED | `history.py:92-119` selects persisted fields including cash_delta, orders created_at/id DESC, applies bound tuple seek and limit+1. HistoryPage renders every field and appends via the actual next cursor. Hook/page pagination tests passed in the initial audit. |
| 5 | Cash-only and liquidated accounts retain actual balance and return without new funding (01) | VERIFIED | Outer join preserves cash-only rows; calculator never writes or restores a grant. Actual cash is total when holdings are empty. Twelve pure math cases include liquidation. |
| 6 | One financial snapshot, Decimal calculations and no partial totals on unavailable prices (01) | VERIFIED | One scalar SELECT, no lazy financial reads/locks. Frozen inputs, precision 50, raw intermediates, HALF_EVEN only at response boundaries. Missing price nulls total/P&L and every allocation while retaining known row values. |
| 7 | Cash and holdings share the full denominator with no fabricated balancing percentages (02) | VERIFIED | `portfolio_math.py:59-65` uses raw cash-inclusive total. PortfolioAllocation consumes bounded exact server percentages directly as CSS widths; no residual correction. Pure raw-denominator and 99.99/100.01 regressions passed. |
| 8 | Zero-basis, zero-total, rounded-zero and inactive positions remain accurate and understandable (02) | VERIFIED | Zero denominators produce null percentages; signed zero normalizes. UI distinguishes Not applicable from Unavailable and labels inactive holdings without Trade links. Focused page/math cases passed. |
| 9 | Exact used-price time/age distinguishes incomplete and last-known values (03) | VERIFIED | Clock sampled after awaited financial read; minimum available as_of and configured thresholds returned. PortfolioFreshness prioritizes incomplete valuation, retains last-known warnings, and renders Calculated at separately from price time. |
| 10 | Cached values continue aging through failed refreshes (03) | VERIFIED | PortfolioPage:13 adds elapsed since successful dataUpdatedAt to server age. Failure retains data and alert/retry; failed request does not replace price age. Timer/retention cases passed in the initial audit. |
| 11 | In-flight trades cannot mix cash/holding commits or block on trade row locks (03) | VERIFIED | Production has one nonlocking financial SELECT. Read `test_portfolio_snapshot.py`: independent transactions, bounded uncommitted-writer read, whole OLD/NEW assertions, and deterministic split-reader negative control. Prior isolated-PG execution was supplied by the orchestrator; no DB rerun here. |
| 12 | History includes inactive coins and preserves microseconds and bigint string IDs (04) | VERIFIED | No active-coin predicate; aware stored created_at; cursor requires six microsecond digits; wire IDs use strings and frontend guards use bigint range checks. Round-trip at signed-bigint maximum passed in the initial audit. |
| 13 | Every seek remains user-scoped and bounded with foreign/edited/malformed cursors (04) | VERIFIED | CurrentUserDep-derived ID always adds Trade.user_id equality. Strict canonical ≤512-character codec and 1..100 page bound; bound ORM tuple. Initial audit independently ran 39 invalid cursor cases plus round-trip/naive-time checks. API tests assert foreign-boundary isolation and fixed 422 errors. |
| 14 | Later pages retain loaded rows without duplicate append or focus loss (05) | VERIFIED | HistoryPage:77-89 calls fetchNextPage with cancelRefetch:false, guards all fetching, flattens server pages in order and keys by string ID. Three-page/repeated-click/end-focus tests passed in the initial audit. |
| 15 | Failed append retries its cursor; refresh reloads the chain; end marker is accessible (05) | VERIFIED | useHistory forwards exact opaque pageParam and next_cursor, no polling/manual cursor array. Independently executed chain test proves replacement boundaries and retained old chain on refresh failure. Stable button ref transfers focus only when needed. |
| 16 | Existing data survives reversible concurrent index migration and metadata matches (05) | VERIFIED | 0008 creates/drops only `(user_id, created_at, id)` concurrently in autocommit blocks; model index matches; online/offline per-migration transactions. Read populated roundtrip/catalog/readiness/constraint/parity tests and preserved 0007 guard. Runtime DB evidence is prior orchestrator execution, not independently repeated. |
| 17 | Buy/sell/replay refresh portfolio/history and existing views (06) | VERIFIED | useTrade:20 awaits all five invalidations on every success, retry:false, no optimistic fill insertion. Tests cover 201 buy/sell, 200 replay, waiting for responses and no invalidation on failures. |
| 18 | Passive expiry/new sign-in and late responses cannot expose prior private cache (06) | VERIFIED | clearPrivateQueries now awaits cancellation of **all** queries, including me, removes only non-me queries; both mutation callers await before publication. apiFetch preserves/guards AbortSignal across refresh/retry/parsing. Deferred A→B and late-me regressions were inspected; independent review reran the 50-test boundary selection. |
| 19 | Logout preserves observed me and returns to sign-in (06) | VERIFIED | me query object is retained during removal, cancelled before null publication. Mounted App/observer regression covers late A after logout. This includes resolved review CR-01, rather than the earlier incomplete helper described in 05-06-SUMMARY. |
| 20 | All five route families remain reachable with accessible responsive navigation, complete desktop/mobile fields and no obscured content (02/07) | VERIFIED | User explicitly approved the real-price/mobile/200% zoom/keyboard/navigation checklist after the authorized rebuild. Actual four-width CI passed. Corrected overflow expressions retain the original assertions. |
| 21 | Complete buy→portfolio→history→sell flow is covered by CI fake-price/console-email e2e (07) | VERIFIED | Actual CI run 41066672894 at 0595c89: 10 browser tests passed, one intentional production-only CSP skip, zero failures; full captured-fill story and all four responsive widths passed. |
| 22 | Local CI-equivalent gates pass, new critical services have 100% coverage, no high finding remains open (07) | VERIFIED | Backend unchanged since 573 tests/99.90% overall/100% critical; final frontend 264 passed with lint/types/format/build. Independent review clean, including 39 affected page tests. All five remote jobs independently confirmed successful. |
| 23 | User reviews real-price screens after a newly authorized dev rebuild (08) | VERIFIED | Actual UAT/HUMAN-UAT records and orchestrator-confirmed responses: explicit rebuild approval, five healthy services, Alembic 0008 head, then approval of supplied real-price/four-outcome checklist. |
| 24 | Verification avoids real-email dev/prod sign-in and private balance/secret access (08) | VERIFIED for this verification | Only repository/source reads, stored local coverage, discovery and synthetic/pure checks were used. No services, real account, env file, log, OTP, email, private API or browser were accessed. |
| 25 | Push/PR/merge/release follow fresh explicit choices, without reusing Phase 4 approval (08) | VERIFIED | User chose push=pr; feature PR25 targets develop. Release/deployment skipped because not requested. Merge remains separately unapproved; CI success grants no merge authority. |

**Score:** 25/25 VERIFIED; 0 UNCERTAIN; 0 FAILED; no overrides.

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| Backend portfolio calculator/service/schema/API/router | Exact one-snapshot session-scoped valuation | VERIFIED | Substantive initial source trace retained; unchanged; remote backend passed. |
| Backend history service/schema/API | Bounded cursor and real stored-fill projection | VERIFIED | Mandatory user predicate, tuple seek, limit+1, exact cash_delta; unchanged. |
| Browser API guards/query hooks | Abortable real portfolio and infinite history data | VERIFIED | Signals, response validation and opaque continuation feed actual pages. |
| Portfolio/History pages and components | Complete financial fields, signs/nulls/allocation/times, retained state/focus | VERIFIED | Actual data props; new guarded aria-disabled refresh and conditional retry-focus handling reviewed. |
| Snapshot and migration tests; 0008/model/Alembic env | Real consistency proof and reversible concurrent index | VERIFIED | Initial substantive independent-session/negative-control/catalog/parity assertions; unchanged; approved rebuild reports 0008 head. |
| Private-query helper/auth/trade hooks/client and tests | Identity isolation and five awaited invalidations | VERIFIED | All-query cancellation before publication, non-me removal, retained observer; unchanged. |
| App/browser spec/CI workflow | Reachable navigation and executable browser story | VERIFIED | Corrected direct boolean expressions preserve assertions; actual CI succeeded. |
| VALIDATION/REVIEW/REFRESH-FOCUS-FIX | Auditable gates and correction evidence | VERIFIED | Final closeout, actual source diff, clean independent review and bounded test evidence agree. |
| 05-UAT / 05-HUMAN-UAT / 05-RELEASE-CHECKPOINT / 05-08-SUMMARY | Actual approvals and scoped handoff | VERIFIED | Approved rebuild/checklist, push=pr, PR25, CI success, skipped release and unapproved merge recorded. |

Initial SDK checks for all eight plans had generic Python-export/alias/indirect-link false negatives. Actual definitions, imports, calls, props, API wrappers and CI discovery were manually traced. The two then-pending Plan 08 records now contain actual decisions; no artificial artifact or override was introduced.

### Key Link Verification

| From | To | Via | Status |
|---|---|---|---|
| AuthSwitch / App | New and existing signed-in pages | Actual gated routes, links and heading focus | WIRED |
| Portfolio query/wrapper | API → scoped financial SELECT → calculator/schema | Signal, validated response, user.id and immutable Decimal inputs | WIRED |
| Portfolio page | Holdings/allocation/freshness | Actual API values, bounded server percentages and price metadata | WIRED |
| History query/wrapper | API → current user's stored trades | Opaque pageParam, signal, user equality, bound tuple seek | WIRED |
| History page | Append/retry/end | Guarded fetchNextPage, retained pages and conditional focus | WIRED |
| Metadata / migration / Alembic env | Actual history-query index | Matching user/time/id order, concurrent create/drop and per-revision transactions | WIRED |
| Auth mutations/client | Clean identity publication | Await cancellation/removal; preserve observed me; check AbortSignal across async boundaries | WIRED |
| Trade mutation | Five financial query families | Awaited invalidations on every successful buy/sell/replay | WIRED |
| Refresh/retry controls | Query refetch and persistent focus | Fetch guard, cancelRefetch:false, aria-disabled and conditional callback-ref focus transfer | WIRED |
| CI / tested result | Browser targets and human/remote handoff | Actual full-flow/four-width execution plus explicit approval records | WIRED and VERIFIED |

### Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Produces real data | Status |
|---|---|---|---|---|
| Portfolio summary | cash/start/total/P&L | Account + positive Holding + optional Price → raw Decimal calculator | Actual persisted inputs from one statement | FLOWING |
| Holding metrics/allocation | holdings / percentages | Stored fee-inclusive basis, quantity, mid and full cash-inclusive denominator | No browser financial reconstruction or residual balancing | FLOWING |
| Freshness | age/as_of/prices_as_of/valued_at | Stored price times, late server clock and successful-query elapsed ticks | Missing/last-known/retained aging preserved | FLOWING |
| History | pages/items/next_cursor | User-scoped Trade/Coin SELECT and stored cash_delta | Real persisted fills and exact continuation boundary | FLOWING |
| Identity / refresh | me and financial caches | Session-backed identity and awaited lifecycle | Cancel-before-publish and server-result replacement retained | FLOWING |

### Behavioral Checks and Re-verification Evidence

The initial `b9dd826` audit independently ran twelve pure portfolio cases, 34 frontend page/history-hook tests, cursor round-trip plus 39 malformed cases/naive-time rejection, coverage-list parity and stored critical coverage (797 statements/160 branches, 100%). It established substantive source/wiring/data flow but correctly withheld acceptance at 21/25 while approvals/browser execution were absent.

This final pass read the actual diff since that audit and rechecked its four uncertain truths. It did not repeat the already-passed broad review/suites or access services, private data or a browser.

| Check | Command/evidence | Result | Status |
|---|---|---|---|
| Actual changed source/tests | git diff b9dd826..HEAD on both page/test pairs and browser spec | Guarded focusable refresh; repeated mouse/Enter/Space suppression; conditional retry-focus recovery; direct boolean overflow expressions with assertions retained | PASS |
| Focused independent fix review | REVIEW final addendum at 151c40e | 39 affected page tests independently passed; zero active findings | PASS — existing independent execution |
| Final frontend | Supplied actual execution and REFRESH-FOCUS-FIX | 264 passed; 99.06% statements; lint/types/format/build passed | PASS — prior execution |
| Backend regression boundary | Source comparison and prior isolated/remote results | Unchanged since 573 passed / 99.90% overall / 100% critical; remote backend passed | PASS |
| Actual remote run | Independently read gh api repos/YokAI-open/Birja/actions/runs/41066672894 | completed/success, head 0595c89d413dc7248118329f646c5888d4ab72af | PASS |
| Actual job conclusions | Independently read the run's /jobs API | image, frontend, e2e, backend and ci-pass all completed/success | PASS |
| Actual Playwright count | Orchestrator independently fetched actual job logs; final closeout record | 10 passed in 35.6s, one intentional production-only CSP skip, zero failures; full story and all four widths passed | PASS — counts supplied by orchestrator |
| CI commit versus audited HEAD | git diff 0595c89..d4eda41 --name-only | Only five planning/evidence files; implementation/workflow identical | PASS |
| Human checkpoints | UAT/HUMAN-UAT/RELEASE-CHECKPOINT plus explicit user responses confirmed by orchestrator | Approved rebuild → five healthy services/0008 → approved checklist; push=pr; skipped release, unapproved merge | PASS |
| Changed-source anti-pattern scan | Targeted rg on five changed source/test files | No debt/stub marker match | PASS |

Read-only GitHub API calls initially failed under restricted networking, then succeeded with scoped escalation. No remote mutation occurred. **0595c89 is the successful CI commit; d4eda41 is the audited documentation HEAD.** This is not a claim that the newer docs commit already has its own green run. Required checks must be green at the then-current PR head before any separately approved merge.

### Probe Execution

No declared or conventional scripts/**/tests/probe-*.sh probe existed in the initial audit; none was introduced. Prior offline deploy-gate evidence is not claimed as a fresh probe execution.

### Requirements Coverage

All seven Phase 5 requirements are claimed by plans; none orphaned. Shared checkboxes/phase completion metadata remain owned by the orchestrator.

| Requirement | Source plans | Description | Status | Evidence |
|---|---|---|---|---|
| PORT-01 | 01–03,06–08 | Cash, holdings and total at mid | SATISFIED | Truth 1, actual projection/rendering, approved SC1 and CI |
| PORT-02 | 01–03,06–08 | Total dollar/percent return against start | SATISFIED | Truth 2, raw Decimal/liquidation cases and approved SC2 |
| PORT-03 | 01–03,06–08 | Complete fee-inclusive holding performance | SATISFIED | Truths 3/8, stored basis/complete fields and approved SC3 |
| PORT-04 | 01–03,06–08 | Holding allocation percentage | SATISFIED | Truth 7, full raw denominator/no residual and approved SC3 |
| PORT-05 | 01,03,06–08 | Exact used-price times | SATISFIED | Truths 9/10, actual times/retained aging and approved SC1 |
| HIST-01 | 04–08 | Own stored complete newest-first fills | SATISFIED | Truths 4/12/13, actual persisted projection, approved SC4 and full-flow CI |
| HIST-02 | 04–08 | History loads page by page | SATISFIED | Truths 13–16, keyset/cursor/index and pagination retry/end tests; approved supplied checklist |

### Anti-Patterns and Adversarial Recheck

The initial 50-path scan and final changed-source scan found no blocking debt/stub marker or disconnected rendering. The hypotheses of missing-price understatement, mixed commit snapshots, foreign-cursor disclosure and late identity/cache publication remain addressed by unchanged substantive code and meaningful tests.

Actual CI exposed two failures hidden by discovery/jsdom: uncalled function strings returned undefined (`0790cb0` corrects them), and native disabled refresh controls lost focus (`311c00f` RED → `151c40e` GREEN). Both corrections preserve browser assertions, have clean independent review and passed actual browser CI. New tests assert pending aria-disabled semantics, repeated activation and retry-focus recovery without focus theft. No new code gap was found.

The e2e verifies real server-to-browser values and stored fill identity; pure/isolated tests establish exact financial formulas. Human approval is recorded at the supplied-checklist granularity; this report invents no separate real-account edge-fixture observations. Synthetic null/zero/long-history/refusal states remain fixture evidence. Earlier pending entries in evidence files describe their historical execution boundary and are superseded by final closeout. Existing low npm advisories remain recorded follow-up; no high finding or phase blocker remains.

### Human Verification Required

None outstanding for Phase 5. All seven recorded checks are approved, with no reported issue. The later correction is confined to refresh/retry focus and overflow expression execution; focused regressions, clean independent review and actual CI verify it without reopening unrelated accepted real-price/zoom/layout behavior.

### Gaps and Deferred Scope

No failed/uncertain must-have, missing/stub artifact, unwired link, blocker or outstanding human item remains. No gaps payload or override is needed. Phase goal achieved.

Phase 6 retains off-server backup/restore, friend inbox/live production trading and production app-role/SSL. No Phase 5 requirement was deferred to obtain this pass. PR merge remains separately unapproved and release/deployment skipped. This verifier changed only this report, made no commit, and performed no service mutation, authentication, real trade, email, private-data access, push, merge or deployment.

---

_Verified: 2026-10-30T13:54:46Z_
_Verifier: gsd-verifier — final scoped re-verification_
