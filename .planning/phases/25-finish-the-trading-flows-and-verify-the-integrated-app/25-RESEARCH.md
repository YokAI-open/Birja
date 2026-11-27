# Phase 25 — Integration research

<user_constraints>
## User Constraints

- **D-01:** Match the trade workspace for crypto, curated stocks and catalog
  stocks. Keep one portfolio chooser, cash and holdings, meaningful price and
  market state, the real order preview and receipt. Preserve crypto amount
  and quantity, stock whole shares, fee display, renewed confirmation and
  original-request recovery. Receipts, cash and History must reconcile to
  the same portfolio.
- **D-02:** Match the compact History toolbar and expandable activity list.
  Preserve activity and asset filters, exact cursor ordering, pagination and
  all existing event details, including corrections and held events.
- **D-03:** Match the sign-in panel and header door control. Run the real
  request-code, verify-code and sign-out paths with visible labels, focus and
  feedback. Use the configured console transport on the isolated stack.
- **D-04:** Compare the running app with the approved ZIP on desktop and
  mobile. Verify authenticated and signed-out flows, safe chart fallbacks
  and representative full-stack trades, portfolio and History journeys.
  Preserve existing financial and session checks.
- **D-05:** Qualify the integrated candidate with review and local evidence,
  then require hosted CI on the authorized release candidate. Reuse verified
  Phase 24 recovery evidence for identical relevant local inputs. Account for
  the measured recovery timing during CI planning. Keep Phase 23 CHART-04
  tracked separately as live history qualification.

[Phase context](25-CONTEXT.md)
</user_constraints>

## Summary

**Researched 2026-11-26.** High confidence in the checked-in application, test
and prototype inputs. Implement the three trade layouts over their existing
order hooks, add working filters to the current private mixed History read,
and update the existing real code sign-in form. The History screen currently
has a chooser, Update, event disclosure and Load more. Its client and route
accept the pagination parameters. The prototype filters require new behavior.
[VERIFIED: `HistoryPage.tsx`, `useEventHistory.ts`, `eventHistory.ts`,
`backend/app/api/v2/history.py`, approved ZIP]

The Phase 24 recovery receipt proves the seven-stage sequence on its frozen
inputs. The local 56m 19s run overlapped backend tests. Hosted timing has no
result yet. Qualify Phase 25 with affected local replays and the full required
hosted workflow on an authorized candidate. [VERIFIED: Phase 24 recovery
receipt, verification report and `.github/workflows/ci.yml`]

## Architectural Responsibility Map

| Capability | Primary tier | Secondary tier | Checked authority |
|---|---|---|---|
| Trade draft, layout and confirmation interaction | Browser | API | `TradePage`, `StockTradePage`, `StockCatalogTradePage` and existing order hooks |
| Quote, fill and original receipt | API and database | Browser for rendering | `app/api/v2/{trades,stock_trades}.py`, catalog route, financial services |
| Filtered History membership, ordering and cursor | API and database | Browser for disclosure and scoped query | `app/api/v2/history.py`, `app/services/event_history.py` and event decoder |
| Code request, verification, refresh and logout | API and session stores | Browser for form and feedback | `api/auth.ts`, `useAuthMutations.ts`, `app/api/v1/auth.py`, `app/api/v2/auth.py` |
| Visual and release qualification | Guarded browser and CI | Disposable PostgreSQL and Redis | `run-stock-browser.py` and `ci.yml` |

## Project Constraints (from AGENTS.md)

- Read `CLAUDE.md`, the active GSD documents and relevant plans before changes.
  Use the maintained GSD workflow and preserve planning history and decisions.
- Preserve Birja's design system and use the installed UI/UX Pro Max script for
  relevant interaction checks. Preserve established React/Tailwind and query
  patterns, Decimal wire values, restricted roles, session/ownership checks
  and existing isolated browser and database guards.
- Verify project-relative paths in the current milestone checkout. Use scoped
  local changes. Publishing, merging and deployment retain their established
  approval boundaries. Code review is defensive and uses bounded benign
  fixtures. [VERIFIED: `AGENTS.md`, `CLAUDE.md`, `.codex/GSD-ADAPTER.md`]

<phase_requirements>
## Phase Requirements

| ID | Research support |
|---|---|
| FLOW-01 | Existing crypto, curated and catalog hooks, exact economic results, state and visual reference |
| FLOW-02 | Additive pre-pagination filters, scope-bound continuation and retained event content |
| FLOW-03 | Real OTP application endpoints via guarded console transport, signed-out panel and door |
| FLOW-04 | Named browser journeys, same-viewport artifact binding, review, exact CI and recovery receipts |

[Approved requirements](../../REQUIREMENTS.md)
</phase_requirements>

## Standard Stack

Reuse the locked Node 24, React 19.3.1, Vite 8.3.5, TanStack Query 5.105.0,
Tailwind/shadcn and self-hosted Inter. The existing locked browser and frontend
tests use Playwright 1.64.1 and Vitest 5.0.5. The backend uses Python 3.14,
FastAPI 0.162.0, async SQLAlchemy and PostgreSQL with locked pytest 9.1.1.
There are no proposed additions to either dependency lock. [VERIFIED:
`frontend/.nvmrc`, `frontend/package.json`, `frontend/package-lock.json`,
`backend/.python-version`, `backend/uv.lock`]

Node v24.22.1, Docker 29.2.1, the installed Playwright browser and the
repository's frontend dependencies were available here. `npm run e2e --
--list` discovered the retained cases described below. Local Chromium measured
the reference using the installed browser after the default sandbox blocked
Chromium startup. The measured run read the approved local files and blocked
HTTP(S). [VERIFIED: version, discovery and local geometry commands]

## FLOW-01 — Trade integration

The signed-in router has three explicit portfolio-owned routes:
`/portfolios/:portfolioId/trade/:symbol`, `/trade/stocks/:symbol` and
`/trade/catalog/:catalogId` under the same portfolio prefix.
`PortfolioRoute` supplies the active target, and `SignedIn` already owns the
trade-route chooser. Its catalog destination preserves the exact catalog ID.
Keep one chooser, scope retained attempts to the selected route and identity,
and key working form state by the existing target lifecycle.
[VERIFIED: `frontend/src/App.tsx`, the three trade pages]

- Crypto uses `useQuote` for the debounced live preview, `useTrade` for
  the original order attempt, and `usePortfolio` and `useHolding` for
  real cash/quantity. Keep USD and quantity buy modes and quantity sells.
  Show both balance facts when available, position and fee from the server
  strings, and the actual receipt. Price change resets the earlier
  authorization and shows a replacement preview for explicit confirmation.
  Unknown outcomes retry the immutable original payload and key.
- Curated stocks use `useStockTrade` and exact stock context/preview/fill
  decoders. Catalog stocks use `useCatalogStockTrade` with listing identity,
  preview, confirm and receipt requests. Keep the route-specific authority,
  current ask/bid, exact cash and shares, old/new repricing, suspension,
  read-only historical identity and market closure rules. Preserve the
  authorized stored mark and countdown. Historical chart responses have no
  role in trade authorization.
- Use the approved heading, two panels and mobile stack for all three.
  Keep crypto automatic preview and the stock explicit preview control.
  Apply form labels and normal typed `inputMode` consistently. A locked
  unknown submission keeps its recovery action even after quotes go stale or
  close, using the existing original-request rules. Preserve actual receipt
  focus, owned portfolio/History links, and explicit Trade again.

[VERIFIED: `frontend/src/{pages,hooks,api}`, `trade.spec.ts`,
`stock-trades.spec.ts`, `stock-catalog.spec.ts`, `portfolio-ownership.spec.ts`]

## FLOW-02 — History integration

`HistoryPage.tsx` uses `useEventHistory` and `HistoryEventDetails` in the
owned route. The service selects a bounded lookahead from four owner-filtered
streams, then hydrates exact immutable identities and event bodies. It orders
descending by recorded microsecond timestamp, kind rank and source ID.
`validate_portfolio_read` runs before and after hydration. Current events are
buy/sell trades, dividends, splits and posted or held dividend corrections.
The prototype's Funding example belongs to the demo stream. The real
portfolio's starting cash comes from its existing baseline.
[VERIFIED: `backend/app/api/v2/history.py`, `backend/app/services/event_history.py`,
`backend/app/schemas/event_history.py`, `frontend/src/api/eventHistory.ts`,
approved `mock.js`]

1. Add strictly validated optional activity and asset query parameters to
   the mixed endpoint. Use All activity, Buy, Sell, Dividend and Split, and
   All assets, Stocks and Crypto. Dividend includes original payments and
   both posted and held corrections. All activity includes every existing
   event, including split. Funding remains a prototype-only example.
2. Apply filters within the owned SQL result before the seek and limit.
   For a typed stock/crypto filter the trade stream can join `Coin` by
   `Trade.coin_id`; the other three streams are already stock-only.
   Apply buy/sell through the stored trade side. Preserve all owner/root
   conditions, the existing lookahead and order, bounded hydration, immutable
   instrument identity and same-root original correction links. A combination
   with no matches returns an owned empty result.
3. Preserve existing default mixed v3 cursors and trade-only v2 cursors.
   Recommend a canonical filtered mixed v4 cursor including both normalized
   filters, validated against the active request and exact portfolio before
   use. Keep the 512-character bound, integer-string checks and strict version,
   key and microsecond validation already shared with the TypeScript decoder
   in `api/history.ts`. Invalid filters and cross-filter continuation produce
   a private parameter refusal with fixed, sanitized copy. Existing
   unfiltered response entities remain compatible.
4. Include the filter pair in the infinite query key and request. Keep current
   owner, target/session generation, abort and stale-publication checks. A
   filter change starts a new first page and clears old disclosure/pagination
   state. Scope load-more focus and announcements to the current filter as
   well as owner and target. Preserve independent append retry and cached
   refresh failure behavior. Distinguish “No matching activity” from an
   unfiltered empty portfolio.
5. Render the approved compact chooser and filter toolbar and an ordered list
   of real server events. Group by a date heading only within the existing
   monotonic series. Keep native disclosures, stable event anchors,
   `HistoryEventDetails`, correction original links and exact catalog trade
   destinations. Keep the useful refresh/retry affordance as a measured
   difference when needed for the restored page and focus behavior.

**Verification anchor.** Seed equal timestamps across sources and matches
past the first unfiltered page, with another owner, another portfolio and a
closed root. Assert no skips or duplicates across pages, stable keyset ties,
correct split and correction inclusion, and no stale append after a filter,
portfolio or session change. Keep the route-private response and default
legacy behavior. [VERIFIED implementation anchors: `event_history.py`,
`api/history.ts`, `api/eventHistory.ts`, `useEventHistory.ts`,
`test_event_history{,_api,_cursor}.py`, `dividends-history.spec.ts`]

## FLOW-03 — Email code and door

`App.tsx` renders the signed-out door and mounts `SignInPage` when the
session query resolves signed out. The door focuses the active input ref,
which is provided to either the email or code field. Signed in, the same
door uses `useLogout`, with pending and failure feedback. Preserve the
existing route/session completion, query clearing and target fencing.
`api/auth.ts` requests a real code through the existing request endpoint
and verifies through v2, preserving the cookie-based session. The guard reads
the generated code only from the disposable backend logs.
[VERIFIED: `App.tsx`, `SignInPage.tsx`, `api/auth.ts`,
`useAuthMutations.ts`, `e2e/helpers.ts`, `auth.spec.ts`]

Match the centered panel for email and code. Keep visible associated labels,
email and one-time-code autofill, real resend and change-email controls, and
visible focus transfer to the mounted field after each successful step. Gate
duplicate pending actions and preserve sanitized code-expiry, retry-after
and service-failure feedback. Maintain the signed-out header's actual
available navigation. Use the prototype's concise hierarchy and the real
form's adaptive height. Keep prototype-specific demo code and storage out of
app implementation and capture only synthetic account data. The existing
auth e2e confirms refresh, logout, return to sign-in and exact starting
funding when the same user signs in again.
[VERIFIED: same source, `deploy/tests/run-stock-browser.py`, approved ZIP]

## FLOW-04 — Visual and Release Evidence

### Measured approved reference

Chromium rendered the exact approved ZIP SHA-256
`5e361ad60eb0915add082791fd4a8bc2862ec607712b04e00a15d2c53f2b143e` with its
bundled fonts. Numbers are viewport pixels in `x, y, width, height` order at
1440 × 1000 and 390 × 1000. Trade uses BTC draft and History the initial list.

| Element | Desktop | Phone |
|---|---|---|
| Trade chooser | `40,127,220,44` | `16,88,220,44` |
| Trade heading | `40,197,1360,69.2` | `16,158,358,51.9` |
| Trade ticket | `40,289.2,751.5,480.5` | `16,232.9,358,445.5` |
| Trade preview | `809.5,289.2,590.5,142` | `16,696.4,358,108.5` |
| History chooser | `40,127,220,44` | `16,88,220,44` |
| History filters | `1129,127,271,44` | `16,140,252,44` |
| First History summary | `40,219.5,1360,70` | `16,232.5,358,70` |
| Sign-in panel | `512.5,207,415,311.7` | `16,115.3,358,258.9` |
| Email input | `550.5,347.2,339,44` | `37,219.7,316,44` |

The reference uses a 1360px maximum shell, 40px desktop and 16px phone
gutters, an 18px gap and 1.12:0.88 trade columns, and a 415px auth panel.
Integrate with the existing Birja header, Inter, neutral tokens and retained
usable states. Compare heading/chooser/controls, relative sizing, disclosure
and form hierarchy. Explain real-input differences in height, pending/error
content, cookie-gated navigation and exact amounts. Test keyboard reach and
320px reflow with CSS 200% text enlargement, keeping that measurement
separate from native browser zoom.
[VERIFIED: local reference measurement, ZIP `styles.css`, Phase 24 browser
receipt and `design-system/birja/MASTER.md`]

Reuse the existing guarded browser runner with source binding, authenticated
real UI and synthetic market data. Capture PNGs and measured geometry in
test-owned paths. Record test inputs, tested commit, prototype and artifact
hashes. The runner's `--review-dir` accepts only Phase 12 and 14 prefixes.
The Phase 24 pattern used `testInfo.outputPath` and a separate paired packet,
which avoids changing the legacy runner. Include matching pairs for each of
the three surfaces at both sizes, with supplementary state checks for closed
stock, repricing/recovery, expanded correction and code/error screens.
[VERIFIED: `deploy/tests/run-stock-browser.py`,
`frontend/e2e/portfolio-strategies.spec.ts`, Phase 24 browser receipt]

### Bounded candidate checks

The hosted jobs are backend, frontend, image, browser e2e, ops and
`ci-pass` aggregation. They require the existing audits, 80% overall
coverage gates, 100% critical backend coverage, five image scans, isolated
browser tests and authenticated PostgreSQL recovery. Ops uses Phase 24's
same-source preflight, complete seven-stage campaign, receipt verification
against the actual `GITHUB_SHA`, byte checks and success-only artifact upload.
[VERIFIED: `.github/workflows/ci.yml`, `deploy/tests/test-ci-ops.py`,
`deploy/tests/run-portfolio-validation.py`]

**Recommended timing adjustment.** Allow 65 minutes for the existing serial
step, 126 minutes for the UTC clock wait and 225 minutes for its containing
job. The 65-minute budget provides approximately nine minutes of headroom
over the measured 56m 19s. The current wait guard keeps the serial operation
from starting in the first UTC hour or crossing midnight because immutable
fixture setup derives a review date from one hour before the database clock.
Update its horizon with the serial budget. A 65-minute crossing horizon may
wait up to 125 minutes from 22:55 to the following 01:00 UTC. The job budget
adds 34 minutes beyond the worst configured wait and serial limits for other
steps and cleanup. Verify the coupling in the existing offline ops contract,
including 00:00, 01:00, just before 22:55 and at 22:55. Keep the seven stage
checks, fixture bytes, exact hashes and dependencies intact. Published runner
timing will decide whether the proposed headroom suffices.
[VERIFIED: current 45-minute serial / 106-minute wait / 165-minute job,
`ci.yml` clock implementation, Phase 24 recovery receipt. Proposed values
are a planning recommendation.]

Record the Phase 24 backend run's 2h 04m 43s concurrent local duration and
the 120-minute hosted backend limit in the handoff. Hosted timing is unknown.
Reuse passing migration and encrypted recovery outcomes for unchanged
schema, tooling and runtime behavior with a documented input comparison.
The new History query changes the backend app tree, so the Phase 24 exact
artifact receipt remains bound to its actual source. Use real PostgreSQL
owner/cursor/filter checks for the new read, and re-run affected recovery
components if their exact behavior or inputs change. The hosted candidate
must create and verify its own archive through the full seven-stage job.
Preserve CHART-04's separate live qualification record and keep local
fixtures distinct from any production transition. Attach the hosted
six-check and recovery receipt only on the separately authorized candidate.
[VERIFIED: Phase 24 recovery and verification records, Phase 23 source
qualification, `.github/workflows/ci.yml`, `CLAUDE.md`]

## Runtime State Inventory

| Category | Evidence and action |
|---|---|
| Stored data | Existing portfolio IDs, lifecycle, starting balances, fills, event rows, snapshot schema 0028 and sessions stay valid. Apply typed filters to the existing query without a data migration. |
| Live service configuration | Keep production funding, trade statuses, mail and historical provider settings under existing deployment/provider release controls. |
| OS-registered state | The UI and History additions need no timer or service registration. The existing scheduler and archive job continue through current entry points. |
| Secrets and environment | Continue the owned guard with synthetic email/price transport. Use the existing config and secret inputs for real deployments. |
| Build artifacts | Vite asset hashes and workflow receipts are tied to the candidate identity. Match screenshot and hosted recovery evidence to each as specified. |

[VERIFIED: checkout contracts, running-app/test paths and selected scope]

## Validation Architecture

No Wave 0 infrastructure is required. Add coverage for changed filters,
layout and integration states in the existing test files and fixture runner.
Quick checks use Vitest selected cases and targeted guarded pytest, then
the exact Chromium focus set after all layout tasks. The full hosted workflow
remains the release gate. [VERIFIED: `frontend/package.json`,
`frontend/playwright.config.ts`, the guarded browser runner, `ci.yml`]

| Req | Per-task checks and cases | Where |
|---|---|---|
| FLOW-01 | Selected Vitest tests for crypto modes, cash/held state, stale price, explicit fresh confirmation, invalid context and original receipt. Guarded browser crypto BTC, curated AAPL or equivalent and the exact promoted out-of-list fixture including purchase/sale, one receipt and actual cash and History reconciliation. | `TradePage.test.tsx`, `StockTradePage.test.tsx`, `StockCatalogTradePage.test.tsx`, `TradeRenameRecovery.test.tsx`, `e2e/{trade,stock-trades,stock-catalog,portfolio-ownership}.spec.ts` |
| FLOW-02 | Target guarded API, cursor and service tests for default and filtered ordered pages, cross-filter mismatch, ownership, correction detail and exact amounts. Run client/parser, hook and page tests for filter reset, empty and actionable errors, append and focus. Extend real mixed-history browser cases with filters before pagination and source-scoped disclosures. | `backend/tests/test_event_history{,_api,_cursor}.py`, `test_portfolio_routes.py`, `frontend/src/{api/eventHistory,hooks/useEventHistory,pages/HistoryPage}.test.*`, `e2e/dividends-history.spec.ts` |
| FLOW-03 | `SignInPage`, `App` and auth hook/component tests for email and code, pending, error, retry/focus and logout. Guarded console OTP first use, renewal and sign-out/re-entry through actual routes. | `SignInPage.test.tsx`, `App.test.tsx`, `useAuthMutations.test.tsx`, `e2e/auth.spec.ts` |
| FLOW-04 | Frontend lint, TypeScript, full Vitest/build, focused Chromium with approved comparisons. Guarded targeted backend checks for new behavior and impacted critical coverage. Exact offline operational contract and release receipt. | `npm run lint`, `npm run typecheck`, `npm run test -- --coverage`, `npm run build`, `python3 deploy/tests/test-ci-ops.py`, Phase 24 successor recovery runner and the six CI jobs |

For focused local backend work, run the required files from `backend` with
locked pytest on the existing disposable Compose project. Expand only the
backend APIs and financial/session authority modules affected by the diff.
The normal CI command is `uv run pytest --cov=app --cov-branch
--cov-fail-under=80` with the existing 100% critical roster.

The selected reference test-name filter is 227 characters including the
optional Phase 25 names. Discovery at the research baseline returned 15
tests in eight files. Register added comparisons in the existing spec files
so the ordinary CI runner discovers them too. Use the same selection in the
guard after discovery:

```bash
python3 deploy/tests/run-stock-browser.py --suite all --grep 'Phase (23|24|25) |a new user signs in|a signed-in user buys|actual (ask buy|changed ask|committed lost response|mixed pages|scoped crypto and stock fills)|catalog (buys and sells|preserves a permitted closed mark)|closed drafts'
```

The `all` suite keeps `BIRJA_E2E_CATALOG` active for target listing tests.
The existing runner owns one disposable fixed project. Serialize runs in
that namespace. [VERIFIED: local Playwright discovery, `run-stock-browser.py`]

## Security Domain

| Boundary | Required preservation |
|---|---|
| Browser-to-trade API | Current portfolio authority, explicit confirmation, fixed-point server economics, bounded quote freshness and immutable original outcome checks |
| Browser-to-private History | Strict query values, owner and active-root checks before and after read, bounded cursor and query scope, no-store responses, session-scoped browser data |
| Anonymous and signed-in session | Existing code delivery controls, generic refusal, cookie refresh, CSRF, rate limits and logout/cache clearing |
| Evidence and publication | Synthetic data and disposable fixtures for browser/DB, exact source and artifact hashes, verified recovery stage receipt and release approval tracking |

[VERIFIED: `CLAUDE.md`, current route and query implementations, Phase 24
verifier and CI]

## Open Questions

Hosted recovery and backend timings are unmeasured for Phase 25. The
authorized full workflow will resolve the candidate-specific result. Live
history provider scope and measured limits are carried under CHART-04.
The existing source and synthetic measurements support local planning now.
[Phase 23 source qualification](../23-show-historical-market-prices/23-SOURCE-QUALIFICATION.md)

## Primary Sources

- [Approved prototype and SHA-256](../../ui-reviews/v1.5/README.md)
- [Phase 22 browser receipt](../22-adopt-the-market-workspace/22-BROWSER-RECEIPT.md)
- [Phase 23 browser receipt](../23-show-historical-market-prices/23-BROWSER-RECEIPT.md)
- [Phase 24 browser receipt](../24-compare-portfolio-performance/24-BROWSER-RECEIPT.md)
- [Phase 24 verification](../24-compare-portfolio-performance/24-VERIFICATION.md)
- [Phase 24 recovery receipt](../24-compare-portfolio-performance/24-RECOVERY-RECEIPT.md)
