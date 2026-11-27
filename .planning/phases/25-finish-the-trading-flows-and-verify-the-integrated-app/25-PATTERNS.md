# Phase 25 — Existing implementation patterns

**Mapped:** 2026-11-26 · **Baseline:** `c6a9940`

Paths and line anchors are relative to the milestone worktree. These are
existing patterns and likely edit surfaces. Use the phase plans for final
file ownership. [Decisions](25-CONTEXT.md) · [Research](25-RESEARCH.md) · [UI contract](25-UI-SPEC.md)

## File classification

| Likely files | Role and data flow | Closest checked pattern |
|---|---|---|
| `frontend/src/pages/{TradePage,StockTradePage,StockCatalogTradePage}.tsx` and targeted style files | Component, scoped quote and result rendering | Existing tickets for each asset family, responsive workspace in `portfolioWorkspace.css:1–29,39–48` |
| `frontend/src/hooks/{useTrade,useStockTrade,useCatalogStockTrade}.ts` and `frontend/src/components/StockTradeReceipt.tsx` | Hook and component, attempt mutations and receipt presentation | Same hooks own their different existing result and quote protocols. Shared stock receipt already renders both stock routes |
| `backend/app/api/v2/history.py` and `backend/app/schemas/event_history.py` | Route and schema, validated request and typed response | Existing `events` route, bounded `_limit`, fixed `_cursor_error` and exact `EventHistoryPage` |
| `backend/app/services/event_history.py` | Service, SQL seek and bounded event hydration | Existing `list_event_history`, `encode_cursor`, `decode_cursor` |
| `frontend/src/api/{eventHistory,history}.ts` and `frontend/src/hooks/useEventHistory.ts` | Client and hook, wire validation and infinite query | Existing `fetchEventHistory`, mixed cursor validator and `financialScope` guard |
| `frontend/src/pages/HistoryPage.tsx` and `frontend/src/components/HistoryEventDetails.tsx` | Component, filter controls and immutable disclosure rendering | Existing `OwnedHistory` target, native `EventCard` disclosure and correction original handling |
| `frontend/src/pages/SignInPage.tsx`, `frontend/src/App.tsx` and relevant styles | Component and route shell, auth mutations and focus | `SignInPage`, `SessionButton`, `SignedIn`, `App` signed-out branch and `useAuthMutations.ts` |
| `backend/tests/test_event_history{,_api,_cursor}.py`, `test_portfolio_routes.py`, `test_auth_{request_code,verify,session}.py` | Tests, real guarded fixtures and pure contract checks | Existing route, typed cursor, exact owner history and OTP fixtures |
| `frontend/src/pages/{TradePage,StockTradePage,StockCatalogTradePage,TradeRenameRecovery,HistoryPage,SignInPage}.test.tsx`, `App.test.tsx`, History client/hook/detail and auth mutation tests | Tests, component interaction, scoped query and mutation outcomes | Existing RTL controls, actual transport mocks, rerender and early/late response checks |
| `frontend/e2e/{auth,trade,stock-trades,stock-catalog,dividends-history,portfolio-ownership,portfolio-strategies}.spec.ts` | Tests, guarded browser request-response and file evidence | Real existing flows, helper for generated code, Phase 24 matched capture instrumentation |
| `.github/workflows/ci.yml`, `deploy/tests/test-ci-ops.py`, `deploy/tests/run-stock-browser.py` and phase receipts | Config, tests and evidence, bounded orchestration and file hashes | Existing ops clock gate and same-archive check, guarded browser runner, Phase 24 evidence |

## Trade workspace and exact attempts

- **Route and chooser.** `App.tsx:322–355` renders one chooser for scoped
  trade routes. The catalog chooser's destination uses
  `catalogTradePath(id, catalogId)`, and the nested routes mount under
  `PortfolioRoute`. The page exports at `TradePage.tsx:470`,
  `StockTradePage.tsx:379` and `StockCatalogTradePage.tsx:401` bind outlet
  target and route symbol or catalog ID to the ticket. Keep these bindings
  and the existing ticket remount keys when adopting the visual shell.
- **Crypto.** `TradePage.tsx:93–119` binds the real state with
  `const portfolio = usePortfolio(target)`, `const holding = useHolding(target, symbol)`
  and `const trade = useTrade(target, symbol)`. The draft chooses
  `side === "sell" ? "quantity" : buyKind`. Its existing receipt effect
  focuses the new fill only for the current target. Reuse `useQuote` and
  exact money formatting. `useTrade.ts:42–78` freezes an attempt and
  checks `sameAttempt` before continuing. Its unknown and refused
  branches at 121 and 176–185 retain the existing attempt lifecycle.
- **Stocks.** `StockTradePage.tsx:35–86` uses `useStockTrade` and the
  scoped portfolio and current stock data. `useStockTrade.ts:311,627–805`
  separates current-quote confirmation, recovery of the original attempt,
  and replacement preview. Catalog `CatalogTicket` at
  `StockCatalogTradePage.tsx:71–102` uses `useCatalogStockTrade` and
  `StockTradeReceipt`. The catalog hook's `resolve(attempt, action)`
  at `useCatalogStockTrade.ts:220–244` checks the exact original context
  through `current() && sameAttempt() && (target.isOriginalCurrent?.() ?? true)`.
  Keep the catalog confirm and receipt paths distinct. Reuse
  `MarketOpening`, `StockFigure`, and the existing disabled-state reasons.
- **Style.** `portfolioWorkspace.css:1–29` gives a bounded 1360px shell,
  wrap-friendly toolbar and 220px chooser with 44px minimum control
  height. Lines 39–48 use grid, `minmax(0, 1fr)` and existing border,
  card and radius tokens. Reuse that sizing and wrapping pattern for the
  ticket and preview positions in the Phase 25 UI contract.

## History filtering and seek

- **Route authority.** `backend/app/api/v2/history.py:8–18,52–67` uses
  `PrivateRoute`, `OwnedActivePortfolioDep`, `DbDep`, a response model
  and a fixed 422 mapping for invalid cursors. Build optional typed
  filters on `events` and pass them to the existing service. Keep
  untouched `trades` callers and the mixed-event response shape.
- **SQL.** `backend/app/services/event_history.py:180–239` calls
  `await validate_portfolio_read(db, portfolio)`, builds the owned
  `union_all` with rank literals, and seeks and sorts by the exact tuple
  `(recorded_at, kind_rank, source_id)` descending, with
  `.limit(limit + 1)`. Apply the activity and asset predicates on these
  owner-scoped source selects before the lookahead. Use `Trade.side` and
  `Coin.asset_class` for trades, and the fixed stock membership and
  activity of the other streams. The bounded hydration joins already
  carry the exact typed event details and preserve the ordered projection.
  Keep the final owner recheck and the correction's embedded original.
- **Wire scope.** The frozen `EventHistoryCursor` and canonical v3
  serializer and decoder at `backend/app/services/event_history.py:33–131`
  preserve microseconds, rank, exact decimal-text IDs and portfolio
  binding. Extend that pattern with the filtered continuation described
  in research. The corresponding strict `isPortfolioHistoryCursor` at
  `frontend/src/api/history.ts:45–81` is used by both the outbound request
  and `next_cursor` response parser at `frontend/src/api/eventHistory.ts:287–324`.
  Add bounded `URLSearchParams` to the latter and keep the separate plain
  trade cursor contract.
- **Browser scope and presentation.** `useEventHistory.ts:39–97` includes
  account, portfolio and session epoch in `["eventHistory", email, portfolioId, epoch]`,
  forwards the request signal and checks the exact cache entry after the
  response. Extend the query key with the canonical filter pair and keep
  existing invalidation prefixes. Reuse the appended-page continuation
  via `getNextPageParam`. Keep the owner's event invalidation tracking
  distinct from pagination as appropriate. `HistoryPage.tsx:33–43,79–108,173–276`
  provides native disclosure, target-keyed mounting, the single labelled
  chooser and append focus behavior. Reuse `HistoryEventDetails.tsx:108–125,234–273`
  for owned original-dividend focus and fallback.
- **Fixtures.** Extend `test_event_history.py:149,260` for tied timestamps,
  owned pagination and off-page lineage. `test_event_history_api.py:35,43,104,157`
  adds real HTTP, auth and exact evidence. `test_event_history_cursor.py:20,103`
  checks canonical boundary data and existing cursor behavior. Use a
  matching event beyond the initial unfiltered limit to prove SQL
  filtering order. Reuse the corresponding client, hook and event-detail
  test modules for filter resets, aborted responses and append recovery.

## Authentication and guarded browser evidence

- **Form and door.** `SignInPage.tsx:43–81,95–120,139–174` uses
  `requestCode.mutate` and `verifyCode.mutate`, a forwarded field ref,
  email and one-time-code autocomplete, input association and pending
  actions. `App.tsx:152–175` renders a 44px named door button and marks
  its icon decorative. Lines 307–320 retain logout pending and error
  feedback. Lines 387–395 route authenticated sessions and focus the
  signed-out input with the existing ref. Keep the shared shell and
  use its existing mutations. `useAuthMutations.ts:5–30` owns cache and
  private query changes after verification or logout.
- **Browser test entry points.** `frontend/e2e/helpers.ts:14–65` has
  `readCodeFromLogs`, `signInNewUser` and `portfolioId`. Keep console
  delivery confined to the disposable runner. Extend existing files
  selected by the retained names in research, including
  `auth.spec.ts:4`, `trade.spec.ts:21`, `stock-trades.spec.ts:128,196,215,270`,
  `stock-catalog.spec.ts:309,431`, and `dividends-history.spec.ts:195`.
  The latter already uses `info.outputPath` for viewport and detail
  screenshots. `portfolio-strategies.spec.ts:309–345` captures measured
  geometry at controlled viewports. Prefer its actual comparisons and
  browser expression conventions. Exact artifact and input bindings are
  recorded in the [Phase 24 browser receipt](../24-compare-portfolio-performance/24-BROWSER-RECEIPT.md).
- **Runner.** `deploy/tests/run-stock-browser.py:22–36,44–82,145–147,280`
  enumerates registered suites, captures the input SHA inventory and
  validates the guarded launch. Keep the `all` suite for combined coverage
  including the catalog fixture. Use the bounded discovered selector in
  research. Preserve cleanup, stable input matching and separate proof
  of tested source and approved reference hashes.

## Recovery and hosted qualification

- **Timing seam.** `.github/workflows/ci.yml:337–357` couples a UTC
  finish horizon to the serial recovery step's timeout. Its guard waits
  until 01:00 UTC when started in the first hour or when the full horizon
  would cross midnight. Keep the same predicate and scope contract tests
  around its boundary times. Preserve preflight, complete serial proof
  and exact hosted SHA verification. Job aggregation at lines 397–409
  keeps all six required check results.
- **Receipt seam.** `.github/workflows/ci.yml:358–384` verifies the
  successor receipt for `GITHUB_SHA`, copies the matched private outputs,
  then checks both digests before success-only upload.
  `deploy/tests/test-ci-ops.py:564–591,813+` already checks strict stage
  sequence and archive identity. Use these contract tests for phase
  timing changes. The runner's `successor_source_identity` at
  `deploy/tests/run-portfolio-validation.py:332` and
  `verify_successor_receipt` at 675 bind the exact candidate. Reuse local
  proof only for applicable unchanged inputs. Hosted CI takes a fresh
  same-source receipt.

All planned surfaces have existing analogs. The additional filter-pair
cursor binding and UTC timeout values are extensions of those contracts.
