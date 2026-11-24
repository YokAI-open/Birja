---
phase: 20-trade-and-value-stocks-from-search
reviewed: 2026-11-24T22:50:53Z
depth: standard
review_base: 1d5fb60ce832c8f71beec9c482d35af4cd4ca56f
scope: Phase 20’s seven prior findings, their repairs, and the refreshed 0026 recovery source pins
files_reviewed: 17
files_reviewed_list:
  - backend/app/api/v2/stock_catalog.py
  - backend/app/schemas/stock_catalog_quotes.py
  - backend/app/services/corporate_actions.py
  - backend/app/services/stock_catalog_actions.py
  - backend/app/services/stock_catalog_financial_quotes.py
  - backend/app/services/stock_catalog_trading.py
  - backend/app/services/stock_valuation.py
  - backend/app/tasks/stock_actions.py
  - deploy/backup-snapshot.py
  - deploy/deploy.sh
  - frontend/src/api/portfolio.ts
  - frontend/src/api/stockCatalog.ts
  - frontend/src/hooks/useCatalogStockTrade.ts
  - frontend/src/hooks/useStockCatalog.ts
  - frontend/src/pages/MarketsPage.test.tsx
  - frontend/src/pages/MarketsPage.tsx
  - frontend/src/pages/StockCatalogTradePage.tsx
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 20 Code Review

The scoped re-review traced the repairs for all seven prior findings through the owned stock order, quote, action, and valuation paths. All seven are resolved. The `0026` deployment and backup source checksums match the reviewed corporate-action implementation.

## Narrative Findings (AI reviewer)

### Resolved findings

**CR-01 BLOCKER · Checking an interrupted order could create a new fill, and a missing receipt had no safe terminal outcome.** “Check order result” only looks up the owned immutable receipt. The HTTP confirmation and lookup both require the signed preview. It binds the owner, portfolio, issue, listing, order terms, unit epoch and deadline. The browser retains that token with the original attempt. A new fill checks expiry against the database clock after acquiring the active account lock and at final execution authority. Lookup uses the same account lock. It can return a definitive missing result only after the token expires, when a delayed copy of the original request cannot book a new fill. A committed original receipt remains available on replay. `backend/app/schemas/stock_catalog_quotes.py:57`, `backend/app/api/v2/stock_catalog.py:402` and `:439`, `backend/app/services/stock_catalog_trading.py:110`, `:529`, `:606` and `:701`, `frontend/src/hooks/useCatalogStockTrade.ts:270` and `:310`.

**CR-02 BLOCKER · An expired or pre-split quote permanently disabled the ticket.** Selected browser demand rearms with bounded 15-second retries only when the active open listing needs a quote. Financial refresh now handles `units_changed` for selected and owned order paths. The durable quote and execution checks still enforce exact units. `frontend/src/hooks/useStockCatalog.ts:167`, `backend/app/api/v2/stock_catalog.py:253` and `:328`, `backend/app/services/stock_catalog_trading.py:257`.

**CR-03 BLOCKER · Healthy action refresh repeatedly withdrew eligibility.** The scheduler keeps a still-valid completed lease while staging work, reuses the verified forward scan, groups in-progress authorities by window, and can fetch multiple bounded segments per cycle. The transition clears proof on an observed gap and expires an old lease from its actual coverage target. `backend/app/tasks/stock_actions.py:481`, `:562`, `:682` and `:894`, `backend/app/services/stock_catalog_actions.py:226`.

**CR-04 BLOCKER · Verified events before promotion permanently blocked the first buy.** Scoped ingestion filters a first-seen supported event only when the independently verified cutoff precedes the established journal origin and neither trades nor economic movements exist before that origin. Incomplete and ambiguous events remain on the hold path. Post-origin events and previously known identities retain normal processing. The final SQL is unchanged. `backend/app/services/corporate_actions.py:371` and `:526`.

**WR-01 WARNING · An initially closed ticket hid quantity entry.** An active listing can accept an editable draft during closure. Preview and confirmation remain guarded by execution eligibility. `frontend/src/pages/StockCatalogTradePage.tsx:130` and `:291`, `frontend/src/hooks/useCatalogStockTrade.ts:52`.

**WR-02 WARNING · A selected Markets listing could miss the market close or reopening.** Markets fetches the exact selected listing at both boundaries. A failed response or unchanged session allows one retry after a two-second delay. A successful transition advances to the next boundary. Tests check the normal close/open request counts and cover both an unchanged response and a temporary failure with the retry capped. `frontend/src/hooks/useStockCatalog.ts:86` and `:106`, `frontend/src/pages/MarketsPage.test.tsx:557` and `:602`.

**WR-03 WARNING · Catalog holdings lost the dated halted valuation state.** Portfolio now checks the exact current report and approval with the listing and session. It can retain a permitted dated mark through the shortest applicable halt, unit, session, and quote deadline. The browser accepts the catalog mark and renders the existing Halted label. `backend/app/services/stock_valuation.py:198`, `:416` and `:533`, `backend/app/services/stock_catalog_financial_quotes.py:491`, `frontend/src/api/portfolio.ts:110`.

## Verification

The reviewer statically traced the repaired source. The execution record reports three scoped HTTP cases, two pre-journal action cases, five action-monitor cases, and 39 focused Markets and catalog ticket cases passing. All seven browser journeys passed before the final receipt and boundary adjustments. The execution workflow tracks the final guarded browser and encrypted recovery reruns.

The SHA-256 of `backend/app/services/corporate_actions.py` matches the reviewed `0026` entries in the backup and deployment tools. The two-line change leaves the retained `0025` entries intact. The execution record reports that both revisions passed offline compatibility checks. `deploy/backup-snapshot.py:1204`, `deploy/deploy.sh:167`.
