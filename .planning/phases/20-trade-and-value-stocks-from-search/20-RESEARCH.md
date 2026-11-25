# Phase 20 research

Research baseline is `31cba00` on `feature/milestone-v1.4`, reviewed 2026-11-24. Confidence is high for local contracts and medium for the proposed successor layout. Expanded live access and rights remain unverified.

<user_constraints>

## User Constraints

- **D-01:** Reuse the owned active portfolio, exact USD accounting and original
  receipt replay. Use fresh regular-session IEX ask for buys and bid for
  sells, with zero stock commission, whole shares and explicit reconfirmation
  when the executable price changes. Preserve reported-halt refusal and the
  approved report coverage limitation.
- **D-02:** Link promotion and orders to the stable issue and exact reviewed
  listing version. Preserve the original financial identity through a valid
  ticker change. Hold uncertain, retired or reused identities. Keep refresh
  bounded to selected and held stocks under the shared provider budget.
- **D-03:** Keep the approved Markets and trade styles and show the last
  permitted mark when closed with the viewer-local opening countdown. Preserve
  cost, P/L and incompleteness semantics in portfolio detail and overview.
- **D-04:** Apply eligible ordinary USD dividends and supported forward splits
  exactly once, keeping frozen portfolios unchanged and events private.
  Uncertain events hold the affected issue, and verified correction policy,
  historical cash, basis, History and receipt replay survive restart.
- **D-05:** Keep Phase 19 fixture evidence and live gaps explicit. Expanded
  display, execution, valuation, action and retention scope must be verified
  before live activation. Use existing free sources and the locked stack in
  this plan. Preserve legacy stock and crypto paths and reserve full release
  qualification for Phase 21.

</user_constraints>

## Summary

Phase 19's catalog IDs and listing versions support search and a Redis display mark. Its healthy response grants no order authority. Phase 18's execution snapshot has five fixed product rows and covers only the curated 20. Its final SQL checks a current PostgreSQL quote, exact rights, action lease and report provenance. Plan additive schema 0026 with a durable catalog-to-financial binding and scoped evidence. Reuse the established owned trade, action and recovery machinery. Keep 0025 archive compatibility exact. [VERIFIED: backend/app/services/{stock_catalog_quotes,stock_eligibility,stock_trading}.py, backend/alembic/sql/0024_stock_halt_snapshot.sql, 19-VERIFICATION.md] [INFERENCE: proposed successor]

## Architectural Responsibility Map

| Capability | Primary owner |
| --- | --- |
| Issue promotion, durable identities and receipts | PostgreSQL with migrator-controlled promotion |
| Ownership, preview, repricing, new fill and replay | API services, with transaction and last SQL in PostgreSQL |
| Selected/held quotes, reported halts and action coverage | Dedicated scheduler with scoped Redis demand and PostgreSQL authority |
| Mixed valuation, incompleteness and History | Owned API projections |
| Countdown, preview, confirmations and receipt | Browser using existing routes and typed hooks |

<phase_requirements>

## Phase Requirements

| ID | Research support |
| --- | --- |
| SL-01 | Stable binding, exact owned API and shared bounded quote refresh |
| SL-02 | Scoped dated last marks, current exchange session and countdown |
| SL-03 | Scoped action ingestion, trusted baseline and exactly-once accounting |
| SL-04 | Durable coin ID, safe display projection, exact retained data and tests |

</phase_requirements>

## Project Constraints (from AGENTS.md)

Use GSD, exact Decimal/NUMERIC values, UTC, owner-root checks and CSRF. Preserve least privilege and existing coverage gates. Use current UI system, test-only isolated stack and mocked upstream HTTP. Keep implementation checks proportionate and preserve valid evidence. Full release and live rollout belong to Phase 21. [VERIFIED: AGENTS.md, CLAUDE.md, .codex/GSD-ADAPTER.md and 20-CONTEXT.md]

## Standard Stack

Reuse current uv/npm locks, Compose images, FastAPI, SQLAlchemy/asyncpg, Alembic, PostgreSQL, Redis, React/TanStack Query, exchange-calendars, pytest/respx, Vitest, Playwright and the existing restic path. No new package proposed. Observed local Python 3.14.9, Node 24.22.1, Docker 29.2.1 and uv 0.13.5. Test diagnostics use disposable containers. Context7 was unavailable, so external facts use official sources. [VERIFIED: package locks, docker-compose.test.yml, existing browser and recovery scripts, local tool versions]

## Architecture Patterns

### Stable financial identity and projection

- `coins` uniquely constrains `(asset_class, symbol)` and caps symbol/name at 10/64 characters. Catalog listings permit 14-character punctuated tickers and 256-character names and identify occupancy by generation, venue and ticker. Provider asset ID is unique on financial instruments. The existing fill facts already allow 32-character symbols and 256-character names. [VERIFIED: backend/app/models/{price,stock,stock_catalog}.py and backend/alembic/versions/0013_stock_execution.py]
- Add one migrator-owned binding with permanent unique catalog ID and financial `coin_id`, and current promoted listing ID constrained to the same issue via the existing `(id, security_id)` listing key. Require explicit current reference, exact provider asset, USD share unit and reviewed listing proof. Repeated promotion of the same issue is idempotent. Verified rename or venue move changes the exact admitted version under the same financial ID only after verified continuity. A new ticker occupant receives its own binding and empty book. Existing provider-asset collision holds new promotion, including duplicates of curated stock, while curated remains reachable separately. Do not attach by text. [INFERENCE: existing durable catalog and trade ownership constraints]
- Preserve the legacy uniqueness rule with a reserved internal symbol for promoted stocks, such as `@<catalog_id>`, plus a tightly bounded stock-only allowance in the existing length constraint. Enforce exact binding in promotion and tests. No crypto key or legacy stock key changes. Same ticker on two venues, same stock and crypto ticker, a rename, and ticker reuse cannot move an existing ledger. Keep legacy symbol endpoints bounded to their prior lane. [INFERENCE: preserve immutable financial identity and public contracts]
- Portfolio detail and overview presently project `Coin.symbol/name`. Project the current permitted human listing instead, or permitted retained identity and an unpriced fallback where the former binding is held. Mark missing valuation visibly incomplete. History trades already use immutable `StockFillFacts.symbol/company_name`, split events use revision terms, and dividends/corrections use payment/decision labels. New dividend SQL currently needs edits where it copies `Coin.symbol` into those facts. Resolve original action label from the reviewed historical version, preserving it on retries, rename and reuse. Internal symbols and private review/provider evidence never become user-facing ticker names. [VERIFIED: backend/app/services/{portfolio,event_history}.py and backend/alembic/sql/0017_dividend_portfolio.sql]

### Exact scoped execution and receipt

- Use owned v2 catalog preview/confirm under stable catalog ID plus canonical string listing version. Preserve the Phase 19 retrieval/discovery route and never redirect catalog confirmation through a ticker. Share existing stock math, movement journal, portfolio cash/holdings and idempotency transaction. Replay uses original immutable request identity, including issue, version for that request, owner/root and order terms. It precedes fresh provider checks and continues after a rename, stale price, Redis loss or market closure. Different issue/order/root with the same key conflicts. A replay is not a new fill. [VERIFIED: backend/app/services/{stock_trading,trade_idempotency,stock_trade_math}.py and backend/alembic/sql/0017_stock_portfolio.sql] [INFERENCE: catalog request shape]
- Legacy `execution_snapshot_query`, `action_rows` and `executions_from_snapshot` hardcode the curated 20; widening the global scan would undermine SL-01 and miss per-target grants. Add target-oriented projection for the particular stock or the returned owner roots' positive holdings, keeping the two coherent financial/authority reads. The existing finalizer expects a durable `stock_quotes` row and fixed five legacy grants. Add a separate scoped catalog branch, preserve legacy rules and pin the exact SQL fingerprint. Bind one authoritative SQL quote per promoted coin to reviewed listing/version, scopes, report, units and cutoff. Store exact bid, ask, source/observed timing, listing and original scope evidence on immutable fill facts or typed adjunct. Use database-owned rows and exact hashes, never a request-supplied digest as authorization. Preserve existing 0025 receipt layouts. [VERIFIED: backend/app/services/{stock_eligibility,portfolio,stock_trading}.py and backend/alembic/sql/0024_stock_halt_snapshot.sql]
- Reuse instrument→root consistency order and choose one deterministic order for catalog publication/promotion and report snapshots. A practical expanded order takes shared catalog fence before instrument and root, then shared report lock for last SQL. The report publisher only holds exclusive report lock and avoids instrument/catalog write locks. Migrator updates use the corresponding exclusive catalog side. Before provider waits release SQL transactions, then re-evaluate identity, ownership, current report, action and session under fresh database time. Finalizer checks exact version, current report, action generation and units, strictly less than 120-second source age and exact economics. Keep no extra business await between final SQL and commit. [VERIFIED: backend/app/services/{stock_catalog_publish,stock_trading}.py] [CITED: https://www.postgresql.org/docs/18/explicit-locking.html]

### Quotes, reported halts and retention

- Phase 19's collection/display/cache grant cannot authorize simulation, derived valuation, stored executable marks or accounting/backup. Qualify separate purposes by exact account/server/feed, field and identity scope. Use the existing IEX decoder and keep a minimal latest SQL quote for eligible held/selected promoted issues where durable marks are authorized. Keep Redis display price independently scoped and avoid storing raw feeds. Storage rights for live fills and separately for latest marks must cover archived backups even when display deadlines expire. Historical facts may replay while rights/routing change within the retained-use scope. [VERIFIED: backend/app/services/{alpaca,stock_catalog_quotes,stock_valuation}.py and 19-SOURCE-DECISION.md]
- Worker takes explicit selected demand and distinct positive positions of active portfolios, with rotating/due work so failures or large held sets do not starve later holdings, selection, curated or crypto. Use existing eight-selection ceiling and reviewed tighter batch caps, account rolling budget and retries, version/purpose coalescing. A sold-out/frozen root stops driving price refresh. Pending event corrections still use their retained obligations. Keep capture and retry bounded with matching current scope before each attempt and before publishing. [VERIFIED: backend/app/tasks/{stock_catalog_quotes,stock_scheduler,scheduler}.py and backend/app/services/stock_catalog_quote_demand.py] [INFERENCE: selected/held request scheduling]
- `parse_halt_report` drops non-curated symbols and report projection uses an exact curated set. Generalize parsing/projection to the selected or held exact binding and valid venue/alias evidence while reusing one report fetch, shared global report fence and market-wide flags. A bounded latest report projection can rebind a newly selected issue inside the same coverage/lease window without another GET. A missing/stale or ambiguous applicable report refuses. Nasdaq documents both venue classes and once-per-minute refresh. The approved simulator policy describes a recent report, whose completeness and publication latency remain limited. Alpaca Basic documents IEX and 200 historical requests per minute, which supplies neither an account-specific effective cap for all products nor expanded use rights. [VERIFIED: backend/app/{services,tasks}/stock_halts.py, 18-VERIFICATION.md] [CITED: https://beta.nasdaqtrader.com/Trader.aspx?id=TradeHaltRSS, https://docs.alpaca.markets/us/docs/about-market-data-api]
- Portfolio valuation currently verifies original authority via a previous fill. Catalog latest marks require a qualified proof from collection even where the latest quote has never been consumed. Bind current display to expiry, units, provenance and the correct original market session, and allow only the last authorized mark during closure. An unavailable mark leaves the aggregate incomplete and the owned cash and quantities correct. Current production Redis AOF can retain older data through rewrite, beyond serving TTL. Phase 21 must qualify disk retention or a volatile cache prior to expanded live usage. [VERIFIED: backend/app/services/{portfolio,stock_valuation}.py, docker-compose.prod.yml and 19-SOURCE-DECISION.md] [CITED: https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/]

### Corporate-action baseline and financial effects

- Current action admission, normalized symbol classifier, worker and SQL dividend authority encode the exact curated set. Refactor explicit catalog scope through request normalization, event resolution, final split/payment authority and receipt fields. `alpaca_actions._normalize` currently routes by ticker. Bind ordinary actions to verified current or dated authoritative alias/issue evidence and combine provider event ID with stable issue linkage. Ambiguous ticker reuse, symbol conflict or invalid terms hold the affected issue. Pay and correct the original event/portfolio with the event's applicable cutoff calendar, including after rename. Legacy paths retain their supported semantics. [VERIFIED: backend/app/services/{stock_admission,alpaca_actions,corporate_actions,corporate_action_rules,stock_action_reconciliation}.py, backend/app/tasks/stock_actions.py, backend/alembic/sql/0017_dividend_portfolio.sql, backend/alembic/versions/0012_stock_action_resolution.py]
- Start newly promoted issue in unknown action state. Use reviewed contiguous journal origin, REST/future and mutation/known-ID coverage and verified due boundaries before first fill. Prove empty pre-promotion ownership without creating artificial zero cash events. Persist per-issue continuation and coverage across interruptions/restarts, binding to reviewed grant and listing scope. A rename preserves journal origin and old receipts, requiring new version checks for continued readiness. Incomplete evidence never marks ready or mutates finance. Share replay catch-up rather than replay the same all-US window separately for each held symbol. [VERIFIED: backend/app/tasks/stock_actions.py, backend/alembic/sql/0024_stock_halt_snapshot.sql] [INFERENCE: expanded actions admission]
- Provider REST documents `data_quality=all` for incomplete records, page tokens and separate ID filter, with variable publication lag. The documented bounded historic replay supports region, time and event-ID filters. Existing adapter's all-US ingress needs separate qualification even when normalization is selective. Neither REST reachability nor a complete single page proves complete correction or mutation coverage. For fixtures drive real cutoff and scheduler behavior with mock upstream, covering partial response and lost continuation. [CITED: https://docs.alpaca.markets/us/reference/corporateactions-1, https://docs.alpaca.markets/us/v1.4.2/changelog/2026-07-20-corporate-actions-b7b8e98] [VERIFIED: backend/app/services/alpaca_actions.py]
- Reuse exactly-once event/entitlement/payment and versioned correction policy. Use supported forward split only when all affected active holdings stay whole and exact. Fractional outcome holds the issue without rounding or inventing a cash credit. Straightforward split preserves total basis and invalidates old-unit quotes. Ordinary USD dividends use the historical owner quantity, closed portfolios stay frozen and uncertain/affordability corrections remain held. [VERIFIED: backend/app/services/{corporate_action_rules,corporate_actions,stock_ownership,dividends}.py and backend/alembic/sql/0017_dividend_portfolio.sql]

### UI, successor and recovery

- Reuse `StockTradePage`, `StockTradeReceipt`, `useStockTrade` and existing Markets/portfolio visual patterns. Adapt to catalog ID and listing version with owner/session fencing. Use stable routes, an actual IEX source where relevant, the existing local countdown and a concise refusal. Repricing stays explicit, and closed ticket preserves the permitted mark. [VERIFIED: frontend/src/pages/{StockCatalogTradePage,StockTradePage,MarketsPage}.tsx, frontend/src/hooks/{useStockCatalog,useStockTrade}.ts and frontend/src/api/{stockCatalog,stockTrades,portfolio,eventHistory}.ts]
- Qualify 0026 schema, role defaults, finance binding obligations and exact app/worker admission. Update `backend/app/db/{schema_contract,portfolio_bootstrap,portfolio_migrate,dev_bootstrap}.py`, `deploy/db/bootstrap-roles.sql`, `deploy/deploy.sh`, `deploy/backup-snapshot.py` and `deploy/verify-restore.py`. Scope an encrypted local successor check on the pattern of `deploy/tests/test-stock-catalog-recovery.sh`. Retain true 0025 archive bytes, verify empty pre-write rollback or protected refusal as appropriate, and block rollback that would discard expanded financial state. Current archive qualification and full production rollout remain Phase 21. [VERIFIED: current exact selector/hash bindings and 19-03-SUMMARY.md] [INFERENCE: additive successor claims]
- Persisted state covers ledgers, listing/binding authority and action history. Redis challenge sessions, burst quotas and unconsumed display cache can start cold. No whole-table backfill or external registry change is indicated. Exact versioned image/backup launcher provenance follows existing archive release workflow. Fixture runs use synthetic account/server scope and locked toolchain. No new secret keys or OS service changes are needed for local planning. [VERIFIED: Compose, schema and recovery profiles; Phase 19 verification]

## Don't Hand-Roll

Reuse stock money and idempotency services, existing PostgreSQL accounting and freezes, exchange-calendars sessions, IEX/action parsers, Redis demand/quota controls and private History. Keep the expanded lane explicit at its authority and identity boundary, sharing the global validated financial invariants. Keep 0025 hashes intact and add measured successor checks. [VERIFIED: implementation paths above]

## Recommended Dependency Order

1. Add stable binding and exact 0026 schema/evidence contracts with migration and role checks.
2. Qualify selected/held pricing, shared report status and scoped action baseline with focused fixtures.
3. Wire owned preview/confirm/replay and SQL financial checks. Bind independent dividend, split and correction effects to the new issue evidence.
4. Expose held valuations and current/retained UI projections with responsive tests.
5. Verify final local browser round trip and narrow exact encrypted recovery. Preserve Phase 19 live gaps and Phase 21 release scope.

## Validation Architecture

Reuse existing infrastructure. Every new test lands with its affected task. Guarded Compose uses disposable PostgreSQL and Redis. Do not run concurrent fixtures that mutate the same database roles/ports.

| ID | Concrete baseline and required evidence |
| --- | --- |
| SL-01 | `backend/tests/test_stock_catalog_quote_scheduler.py`, `test_stock_catalog_trade_context.py`, `test_portfolio_stock_trading.py`, `test_stock_execution_authority.py`. Extend with exact binding and receipt replay, capped selected/held work, changed scope or quote, overlapping portfolio cash and last-SQL timing refusal. |
| SL-02 | `backend/tests/test_stock_sessions.py`, `test_stock_catalog_quotes.py`, `test_stocks_api.py`, and `frontend/src/pages/{MarketsPage,StockCatalogTradePage}.test.tsx`. Verify closure/early-close count, permitted and expired mark, post-reopen price requirement, and incomplete valuation independent of crypto. |
| SL-03 | `backend/tests/test_stock_action_monitoring.py`, `test_stock_action_resolutions.py`, `test_portfolio_splits.py`, `test_portfolio_dividends.py`, `test_dividend_authority.py`. Exercise catch-up resume, issue-local holds, 2-for-1 whole success, fractional refusal, once-only cash and correction, and frozen sibling. |
| SL-04 | `backend/tests/test_portfolio_strategy_lifecycle.py`, current portfolio/History and authority checks, `frontend/e2e/stock-catalog.spec.ts`, `deploy/tests/test-stock-catalog-recovery.sh` successor. Compare owned cash, quantities, basis, history, stable ticker reuse and exact receipt replay through restart and encrypted restore. |

Use `cd backend && uv run --locked pytest -q <affected files>`, direct targeted frontend Vitest and `python3 deploy/tests/run-stock-browser.py --suite catalog`. A real browser with deterministic provider HTTP must demonstrate an out-of-list ask/bid round trip and preserve existing trade controls. Run narrow 0025/0026 encrypted assertions once after schema/runtime stabilize. Use static Ruff/mypy and frontend lint/types in their touched scopes. Existing fixture and harness evidence means no separate tooling setup wave. Maintain full required CI and coverage before merging. [VERIFIED: CLAUDE.md and existing test paths]

## Security Domain

Use bound parameters, canonical string IDs, auth/CSRF and owned active-root checks, exact database clock and grants, and private immutable receipt/accounting facts. Use scope revocation, stale input, mistaken route, retired identity and unauthorized portfolio refusal tests with synthetic fixtures. Keep secrets/raw provider data out of audit artifacts. These controls support the approved outcome without expanding the defensive review beyond affected paths. [VERIFIED: CLAUDE.md and AGENTS.md]

## Resolved questions and live evidence boundary

Local execution uses reviewed synthetic grants, current reported-halt policy, stable issue/coin promotion, strictly eligible IEX facts, bounded eligible action coverage and existing whole-share/correction rules. No local receipt closes the live directory, classification or permission gap. Expanded use needs effective collection, execution, display, cache, action-history, storage and backup scope, current account limits, a qualified Redis persistence disposition and Phase 21's first live out-of-list trade. [Phase 19 source decision](../19-search-the-nyse-and-nasdaq-catalog/19-SOURCE-DECISION.md) · [Phase 19 verification](../19-search-the-nyse-and-nasdaq-catalog/19-VERIFICATION.md)
