---
phase: 12-preserve-existing-investing-under-portfolio-ownership
plan: "20"
subsystem: api
tags: [portfolio, browser, transport, receipts, history, cursor, authorization]
requires:
  - phase: 12-15
    provides: actual scoped production financial routes and legacy refusal
  - phase: 12-19
    provides: canonical portfolio IDs and explicit browser target discovery
provides:
  - Required original-root crypto and stock transport and response identities
  - Immutable root-bearing trade attempt types and same-root repricing validation
  - Scoped valuation and trade2/mixed3 History request and continuation contracts
affects: [12-21, 12-22, 12-23, 12-24, 12-25, 12-26, 12-27]
tech-stack:
  added: []
  patterns: [required root argument, response identity comparison, opaque scoped continuation]
key-files:
  created:
    - frontend/src/api/portfolioTrades.test.ts
    - frontend/src/api/portfolioReads.test.ts
  modified:
    - frontend/src/api/trades.ts
    - frontend/src/api/stockTrades.ts
    - frontend/src/api/portfolio.ts
    - frontend/src/api/history.ts
    - frontend/src/api/eventHistory.ts
key-decisions:
  - Every financial client requires a canonical positive bigint string before network access; no default portfolio exists
  - Server quote/context/receipt/valuation identity must match the captured request target without manufacturing identity on old responses
  - Original stock attempt root remains local immutable metadata and is removed from the unchanged server order payload
  - History tokens are forwarded unchanged after version/shape/root checks; cursor contents never select or authorize a portfolio
requirements-completed: []
requirements-addressed: [PFIN-02, PFIN-03, PVIEW-03]
duration: 12 min
completed: 2026-11-16
---

# Phase 12 Plan 20: Explicit Scoped Financial Browser Clients

**Required portfolio targets and matching response identities bind browser trade, valuation and private History transport to the original strategy without fallback.**

## Performance

- Started: 2026-11-16T13:00Z
- Focused gates complete: 2026-11-16T13:11Z
- Tasks: 2/2
- Files created/modified: 7
- Packages, backend authority, recovery tooling and production operations changed: none

## Accomplishments

- Crypto quote/fill/holding and stock quote/fill/context clients use explicit
  /api/v2/portfolios/{id} paths, require canonical positive bigint strings and
  preserve common cookie/CSRF, no-store, status and cancellation transport.
  Missing, numeric, malformed, path-injected and out-of-range roots fail before
  fetch. No URL default or implicit metadata selection is present.
- Quote, Fill, Holding, StockEconomics, StockContext and Portfolio response
  types carry server-returned portfolio_id. Every corresponding fetch compares
  it with the original request root; old missing-root and crossed-root bodies
  are rejected rather than overlaid with the current selection. Crypto symbol,
  side and input identity and existing exact stock arithmetic remain checked.
- StockAttempt is readonly and requires portfolio_id. Execution refuses a path
  that differs from that original root before fetch and sends only the unchanged
  symbol/side/quantity/expected_exec_price/idempotency_key body. TradeAttempt
  provides readonly original portfolio/order/expected_mid/key fields for Plan21.
  Crypto and stock repricing replacements are accepted only for the original
  root and payload. Original receipt values are not recomputed from current marks.
- Valuation requires the returned root and bounded plain-text name alongside
  the existing exact stored-baseline, dated-mark and incomplete-value parser.
  No pooled cash or zero financial fallback was added.
- Trade History uses /history and mixed History /event-history under the same
  explicit portfolio. Their canonical trade2/mixed3 continuations include that
  root. Scope/shape/version checks reject old, malformed, duplicated-field and
  wrong-root tokens before queries; tokens are forwarded byte-for-byte and are
  never used to derive the target. Page limits, duplicate rows and cancelled
  late responses are refused. Mixed original-dividend references remain embedded
  in the server-owned page and retain their immutable reference/economic checks.
- Every unavailable404 and retired409 stays an error after any earlier success;
  these stateless clients have no previous financial projection to return.

## Task Commits

| Task | Commit | Result |
|---|---|---|
|12-20-01|da5dba4|Required trade root paths, original attempt and response/reprice identity checks|
|12-20-02|61ad80d|Scoped valuation and opaque root-bound private History transport|

## Verification

- Task01 began with22 failing feature cases and then passes38 real shared-client
  transport/parser cases, including common CSRF body semantics, exact bigint
  strings, response/root mismatches, original-root attempts, malformed crypto
  orders, repricing, response cancellation and immutable saved receipt values.
- Task02 began with21 failing feature cases and then passes41 valuation/History
  transport/parser cases: exact root URLs, opaque cursors, private originals,
  duplicate/limit/malformed pages, wrong/legacy/rootless cursor metadata,
  unavailable/version errors, actual-baseline/incomplete semantics and aborts.
- Final prescribed two-file Vitest run passes79 cases. Fetch is intercepted at
  the HTTP boundary; no backend/provider/production network was used.
- All seven task files pass ESLint and Prettier; git diff --check passes.
- Full frontend typecheck was run. It reports51 errors across17 existing
  consumer/fixture files: hooks still use old client signatures (Plans21/22),
  AccountPage/TradePage still use identity cash (Plans23/24), and old API/page
  test fixtures omit explicit roots (Plan27). None is in the five changed client
  source modules or two new test modules. No complete build/type/suite success
  is claimed, and no optional-root compatibility shim was added.

## Interfaces for Following Plans

- fetchQuote(portfolioId, order, signal?),
  executeTrade(portfolioId, order, expectedMid, idempotencyKey, signal?), and
  fetchHolding(portfolioId, symbol, signal?) require the captured original root.
- TradeAttempt is Readonly<{portfolio_id, order:Readonly<Order>, expected_mid,
  idempotency_key}>. Plan21 must retain it through unknown outcomes and retries.
- fetchStockQuote(portfolioId, order, signal?),
  fetchStockContext(portfolioId, symbol, signal?), and
  executeStockTrade(portfolioId, originalStockAttempt, signal?) require that
  root; StockAttempt now includes readonly portfolio_id.
- fetchPortfolio(portfolioId, signal?), fetchHistory(portfolioId, args?, signal?)
  and fetchEventHistory(portfolioId, args?, signal?) require explicit roots.
  History page wire shapes remain items/next_cursor, with embedded originals;
  Plans21/22 must additionally partition caches and late responses by captured
  owner/root epoch. Client scope checks do not replace server authorization.
- isPortfolioHistoryCursor(token, kind, expectedPortfolioId?) is shared only
  for strict wire validation. Both request clients always supply their required
  root; the optional argument permits generic shape guards, not a request fallback.

## Deviations from Plan

None in scope or file ownership. The shared cursor wire validator lives in the
existing history.ts and is consumed by eventHistory.ts, preserving one exact
scope contract without another file. Crypto request/response and repricing
checks directly implement the assigned malformed-order/root threat controls.
One caught-error lint requirement adds the original ApiError as an internal
cause while the displayed repricing error remains generic.

## Issues Encountered

Initial feature-test failures correctly demonstrated the old unscoped paths and
missing root fields. The control-character name check uses code-point validation
matching metadata rather than a control-character regex, satisfying existing lint.

## Known Stubs

None. Financial hooks and pages are deliberately migrated in Plans21–25. Full
frontend fixture/type/coverage/browser integration belongs to Plan27.

## Carry Forward and Phase Position

- Plan18 Task02 remains incomplete with uncommitted recovery files and its
  12-18-CONTINUATION.md. This independent same-wave Plan20 touched none of them.
  The parent received owner approval for targeted diagnosis/retry; resume18
  before advancing beyond Wave13. No completion summary for18 was created.
- Plans21/22 must capture owner, original root and epoch for queries/attempts;
  Plans23–25 must use those scoped hooks and render the accepted named context.
- Plan27 must update old API and shared fixtures to include returned portfolio
  IDs, StockAttempt roots, new paths and trade2/mixed3 cursor versions while
  retaining financial/security assertions. Current known type failures are not
  hidden or accepted as a final gate result.
- No human UI, full browser/build, coverage/security/image, encrypted recovery,
  provider or production result is claimed. All whole requirements remain
  unchecked, including separately deferred Phase7 live outcomes.
- Commits stay local. Unrelated .claude/ and paused18 work remain untouched.

## Self-Check: PASSED

Both new test modules and both task commits exist. The final79-case run,
changed-file lint/format and diff checks pass. Later consumer type failures and
Plan18's unresolved checkpoint are recorded explicitly without advancing them.
