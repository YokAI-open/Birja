---
phase: 23-show-historical-market-prices
verified: 2026-11-27
status: passed
score: 6/6 must-haves verified under replacement chart scope
---

# Phase 23 verification

Coin Metrics Community and TradingView replace the original production
history candidates for Birja’s noncommercial simulator.

| Requirement | Result |
|---|---|
| CHART-01 | Native crypto and hosted stock views offer 1D, 1W and 1M. 1W uses five trading days in the stock widget. |
| CHART-02 | Crypto keeps its matching price table and comparable changes. TradingView owns the stock chart and its values. |
| CHART-03 | Browser checks verified quote and trade independence for featured stock, catalog stock and crypto. Stocks provide a fallback link. |
| CHART-04 | The live Coin Metrics adapter returned complete series in 12 windows. AAPL and ORCL rendered live TradingView charts. The source licenses, bounded demand and chart-only rate limit were reviewed. |

See [crypto verification](23-05-SUMMARY.md), [stock verification](23-06-SUMMARY.md)
and [replacement source evidence](23-SOURCE-QUALIFICATION.md#replacement-sources).
The [v0.9.1 release](https://github.com/YokAI-open/Birja/releases/tag/v0.9.1)
records the hosted CI and production verification.

## Earlier verification of the original adapters

The observations below are the original local evidence for Plans 01–04.
Plans 05–07 replace those historical sources for production.

## Observable outcomes

| Truth | Status | Evidence |
|---|---|---|
| A coin, featured stock and catalog listing have 1D, 1W and 1M ranges with a consistent chart and text alternative. | Verified locally | Chromium exercises BTC, AAPL and exact FQZT identity via the running app. `MarketsPage` starts with 1W and passes the exact selector to `useMarketHistory`. `MarketHistoryChart` uses the same points for the Canvas and Price data table. |
| Closures and missing intervals stay distinct. Chart failure leaves the quote, search and eligible order path usable. | Verified locally | The chart breaks at marked gaps, describes sparse and delayed coverage, and retains keyboard retry. The browser exercised an unavailable chart and current AAPL and FQZT preview asks of $102 and $103. The retained stock and crypto fill journeys passed. |
| Historical data uses qualified coverage and measured free-tier limits while orders use current quotes. | Blocker for phase completion | Queue bounds, scope and identity revalidation, expiry, scheduler caps and current-quote order behavior are implemented and locally tested. The live sample verified representative coverage and freshness. The production quota counters and guarded replay verified the shared request budget. Historical display and cache scope remains open. |
| Four actual-app views match the approved layout with recorded data and attribution differences. | Verified locally | Inspected open AAPL, closed AAPL, ORCL on mobile and BTC. Recomputed eight PNG hashes and dimensions and checked panel widths, tile dimensions, plot dimensions and action right edges against the recorded ZIP geometry. |
| Ranges contain validated completed closes with comparable Decimal changes. | Verified locally | The provider adapters map validated bars into the time window. The normalizer retains observed closes, marks gaps and suppresses changes when the qualifying baseline or coverage is missing. A direct Python check preserved two decimal closes, detected a missing interval and excluded an unfinished bar. |
| The available live evidence and any unresolved source limitation are explicit. | Verified | The dated qualification record distinguishes the initial documentation review from the later live sample and records the shared budget and identifies the remaining display and cache scope. |

## Artifacts and connections

`gsd-sdk query verify.artifacts` passed all 12 declared artifacts. The SDK's
literal-path link checks missed the Python module imports, TypeScript aliases,
constructed browser file paths and relative Markdown link. Each of those
seven connections was traced directly through the source.

| Connection | Evidence |
|---|---|
| Provider adapters → normalized history | Both adapters import the window and bar contracts, validate closes, and return batches consumed by the worker's `normalize_history` call. [Adapters](../../../backend/app/services/market_history_providers.py) · [Worker](../../../backend/app/tasks/market_history.py) |
| HTTP route → bounded request and cache | The v2 router mounts `POST /market-history/query`. Authentication and CSRF guard the typed request. `resolve_history` validates the exact instrument and generation before Redis demand. The route checks authority and expiry again before returning data. [Router](../../../backend/app/api/v2/router.py) · [Endpoint](../../../backend/app/api/v2/market_history.py) · [Demand](../../../backend/app/services/market_history_demand.py) |
| Scheduler → independent history cycle | The scheduler registers the history background callback when scope and cache are present. The cycle claims a bounded job, revalidates authority before provider attempts and publication, and caches display data with an absolute expiry. [Scheduler](../../../backend/app/tasks/scheduler.py) · [Worker](../../../backend/app/tasks/market_history.py) |
| Selected instrument → cancellable client query → chart | Markets identifies the selected coin, featured stock or active catalog ID and version. The query key includes identity, range and session. The guarded HTTP client validates the response and the widget renders its series, intervals and exact values. [Markets](../../../frontend/src/pages/MarketsPage.tsx) · [Hook](../../../frontend/src/hooks/useMarketHistory.ts) · [Client](../../../frontend/src/api/marketHistory.ts) · [Chart](../../../frontend/src/components/MarketHistoryChart.tsx) |
| Disposable browser runner → Markets and catalog journeys | `browser_specs` includes `markets` and `stock-catalog` in the selected suite. The runner exercised their real isolated routes with chart response fixtures. [Runner](../../../deploy/tests/run-stock-browser.py) · [Markets cases](../../../frontend/e2e/markets.spec.ts) · [Catalog cases](../../../frontend/e2e/stock-catalog.spec.ts) |
| Browser receipt → source qualification | The receipt links to the initial candidate scope and the later live sample. [Browser receipt](23-BROWSER-RECEIPT.md) · [Source qualification](23-SOURCE-QUALIFICATION.md) |

The history data flow reaches the provider adapters through admitted scope
and the scheduler. Normalized bars return through the cache, validated API
response, query and chart. The local backend tests exercise provider fixture
responses through this path. The isolated browser uses chart HTTP fixtures
while the current quote and order journeys use the existing application
routes. When scope is absent the history endpoint returns an unavailable
state. The current quote and trade inputs come from their separate paths.

## Evidence checks

| Check | Result |
|---|---|
| Isolated Chromium log and discovery receipt | 11 passed on `775c435`, including retained closure, narrow layout, catalog, stock and crypto cases. [Final browser log](/tmp/birja-phase09-browser-lyifniv5/browser-all.log) |
| Frontend check log and built assets | 1,409 tests passed across 63 files. Lint, types, scoped format and Vite build passed. Both built CSS and JS exist. The build reports a bundle size advisory. [Frontend log](/tmp/birja-phase23-frontend-final.log) |
| Backend regression and review | 335 scoped checks, 130 focused scheduler coverage cases and 85 affected review checks are recorded as separate replays. Affected critical scheduler modules and the stock route achieved 100% in the listed runs. [Code review](23-REVIEW.md) |
| Visual proof archive and source binding | Recomputed the outer ZIP checksum, confirmed all eight PNG bytes and dimensions against its manifest and matched 361 input hashes against the current tree. The manifest names `775c435` and there is no diff from that commit in those inputs. The checked-in prototype checksum also matches. [Visual comparison ZIP](/tmp/birja-phase23-visual-proof.zip) |
| Normalization spot-check | The locked Python environment returned the exact supplied Decimal closes, marked the missing interval and discarded the unfinished interval. The check made no network calls. |

The desktop viewports and full-page images are 1440 × 1000. The mobile
comparison shares a 390 × 1000 viewport and includes the longer rendered
document. At a normal 320px width Chromium verified the single-row header.
At 640px with doubled root font it verified reachable controls, navigation
and expanded table without horizontal overflow. Browser-native 200% zoom
acceptance is unrecorded. The approved contract calls for matched captures
and that automated reflow check. The captured styles preserve the required
spacing and right-aligned actions, with differences for session gaps,
attribution, timestamps, the price table and real control states recorded
in the receipt. [Paired comparison](23-BROWSER-RECEIPT.md)

No phase-declared probe scripts apply. The changed production paths contain
no untracked debt markers or placeholder data paths. The live evidence gap
belongs to this phase and does not appear as an explicit later-phase item.

## Requirements

| Requirement | Plans | Result |
|---|---|---|
| CHART-01 | 23-01, 23-02, 23-03, 23-04 | Verified locally for BTC, AAPL and exact catalog identity. Live series activation depends on CHART-04. |
| CHART-02 | 23-01, 23-03, 23-04 | Verified locally for exact closes, source and basis, gaps, split treatment and comparable changes. |
| CHART-03 | 23-02, 23-03, 23-04 | Verified locally for sparse, delayed and failed history with current-quote order behavior. |
| CHART-04 | 23-01, 23-02, 23-04 | Open. The bounded request and cache behavior passed with fixtures. The live sample verified all nine windows and observed the Alpaca historical limit headers. The production budget was measured and the related regressions passed. Historical-use scope remains unverified. [Live sample](23-SOURCE-QUALIFICATION.md#live-sample-on-2026-11-27) |
