---
phase: 19-search-the-nyse-and-nasdaq-catalog
reviewed: 2026-11-24T19:41:23Z
source: fac7a95
diff_base: e139889
depth: standard
files_reviewed: 38
files_reviewed_list:
  - backend/alembic/sql/0025_stock_catalog.sql
  - backend/alembic/versions/0025_stock_catalog.py
  - backend/app/api/v1/router.py
  - backend/app/api/v1/stock_catalog.py
  - backend/app/api/v2/router.py
  - backend/app/api/v2/stock_catalog.py
  - backend/app/db/dev_bootstrap.py
  - backend/app/db/portfolio_bootstrap.py
  - backend/app/db/portfolio_migrate.py
  - backend/app/db/schema_contract.py
  - backend/app/models/__init__.py
  - backend/app/models/stock_catalog.py
  - backend/app/schemas/stock_catalog.py
  - backend/app/schemas/stock_catalog_quotes.py
  - backend/app/services/alpaca.py
  - backend/app/services/stock_catalog_classification.py
  - backend/app/services/stock_catalog_provider.py
  - backend/app/services/stock_catalog_publish.py
  - backend/app/services/stock_catalog_quote_demand.py
  - backend/app/services/stock_catalog_quotes.py
  - backend/app/services/stock_catalog_search.py
  - backend/app/services/stock_catalog_sources.py
  - backend/app/services/stock_quote_rules.py
  - backend/app/tasks/scheduler.py
  - backend/app/tasks/stock_catalog_import.py
  - backend/app/tasks/stock_catalog_inventory.py
  - backend/app/tasks/stock_catalog_quotes.py
  - backend/app/tasks/stock_scheduler.py
  - deploy/backup-snapshot.py
  - deploy/db/bootstrap-roles.sql
  - deploy/deploy.sh
  - deploy/verify-restore.py
  - docker-compose.prod.yml
  - frontend/src/App.tsx
  - frontend/src/api/stockCatalog.ts
  - frontend/src/hooks/useStockCatalog.ts
  - frontend/src/pages/MarketsPage.tsx
  - frontend/src/pages/StockCatalogTradePage.tsx
findings:
  critical: 1
  warning: 4
  info: 0
  total: 5
status: issues_found
---

# Phase 19 code review

Reviewed the changed runtime, migration and recovery code at `fac7a95`.
Traced server and browser request paths and inspected the relevant fixtures.
The findings below come from static review. Existing integration receipts
remain with the plan summaries.

## Narrative Findings (AI reviewer)

### CR-01 [BLOCKER] Changing the classification source can retire the same issue

`backend/app/services/stock_catalog_classification.py:142` derives a reviewed
issue key from an issue-group hash. The mapping path uses a share-class FIGI
at line 221. `backend/app/services/stock_catalog_publish.py:371` compares
these different namespaces as independent identities. When the reviewed
issuer evidence replaces an unavailable FIGI result for the same issue,
publication can create a new security ID and label the original one
`verified_ticker_reuse` at lines 214–215. A saved link then claims that its
active stock retired. The same problem occurs when mapping becomes available
for a previously reviewed issue.

Require affirmative continuity or new-issue evidence before publishing a
same-ticker conflict across classification sources. Without that evidence,
hold the change and keep the last verified listing. Add a refresh test with
unchanged company, class, ticker and exchange and a different evidence source.

### WR-01 [WARNING] Opening a ticket mid-request can leave its price blank

`frontend/src/pages/MarketsPage.tsx:490` shows the trade link while the selected
quote POST is pending. Clicking it immediately can complete the ticket GET
before the worker caches the mark. `frontend/src/hooks/useStockCatalog.ts:88`
performs a single context read, and the successful empty state in
`frontend/src/pages/StockCatalogTradePage.tsx:82` has no way to refresh the
mark from the ticket. The message can stay on screen after the quote arrives.

Keep the market detail link available after the initial price check resolves,
including refusal. Another option is to refresh the read-only ticket context
while the selected request is outstanding. Test the immediate-click path.

### WR-02 [WARNING] Valid provider price scale can fail browser decoding

`backend/app/services/stock_quote_rules.py:134` checks numerical equality to
the eight-decimal form but returns the original Decimal. A price such as
`18.000000000` passes this check. The catalog quote cache keeps that scale and
the API serializes it verbatim. `frontend/src/api/stockCatalog.ts:155` refuses
more than eight decimal characters and discards the response.

Normalize the accepted sides to at most eight decimal digits before caching
or serialization. Keep exact values and retain ordinary wire formatting. Add
a regression using a valid price with trailing zeros beyond eight places.

### WR-03 [WARNING] Reference staging may use a superseded batch decision

`backend/app/tasks/stock_catalog_import.py:158` claims a reviewed batch and
ends its SQL transaction before transport. `backend/app/services/stock_catalog_provider.py:291`
then checks each request against the batch's captured approval and captured
listing versions. If the first request is in flight while its authority is
revoked or the catalog is refreshed, the second request still uses that
decision. Promotion rechecks the database, which prevents publishing the
result, while the extra acquisition has already occurred.

Recheck the saved claim, effective grant and selected versions with a short
read immediately before each provider attempt. Close that transaction before
HTTP. Verify that revocation between two mocked requests prevents the second.

### WR-04 [WARNING] The production cache writes expanded prices to disk

`backend/app/services/stock_catalog_quote_demand.py:69` writes display prices
to Redis under a transient cache grant. `docker-compose.prod.yml:72` enables
Redis append-only logging on a persistent volume. A quote can remain in the
append-only log after its serving TTL until Redis rewrites that log. The
PostgreSQL backup test covers a separate storage path.

Before live activation, confirm the expanded cache grant covers disk-backed
Redis, including persistence beyond the serving TTL, or put these prices in
a volatile cache. This is a rollout condition while expanded rights and
production activation remain open.

## Resolution

Source `cc31da5` addresses CR-01 and WR-01 through WR-03. A same-ticker
replacement across classification namespaces requires reviewed retirement
proof. The detail action waits for the selected price request to settle.
Wire prices preserve their numeric values at the supported precision.
Reference staging rechecks its claim, grants and listings before every GET.
All 119 affected backend tests, 29 focused frontend cases and four catalog
Chromium journeys passed after the fixes.

WR-04 is a live activation condition in the source decision and Phase 21
handoff. The production deployment must align its Redis persistence with the
expanded quote rights. No expanded live grant or cache was enabled.
