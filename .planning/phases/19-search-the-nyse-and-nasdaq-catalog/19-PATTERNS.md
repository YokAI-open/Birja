# Phase 19 pattern map

Mapped on 2026-11-24 against `33b9b5f`. This maps candidate file boundaries from
the approved Phase 19 context and requirements. The plan should confirm names
against the source research. SC-01 and SC-02 concern catalog identity and search.
SC-03 and SC-04 add detail, one selected display quote, and entry into an owned
portfolio. Expanded financial execution belongs to Phase 20.

## File classification

| Planned file or area | Role and data flow | Closest checked analog | Fit |
|---|---|---|---|
| Additive revision after `0024` and catalog models | Migration and model, durable writes | `backend/alembic/versions/0009_stock_discovery_schema.py`, `backend/app/models/stock.py` | Role match with separate identity requirement |
| New catalog import, validation and publication service | Service, batch transform and atomic writes | `backend/app/services/stock_sessions.py`, `backend/app/tasks/stock_halts.py` | Transaction pattern |
| New search and detail schemas/router/service | Controller/service, authenticated reads | `backend/app/api/v1/stocks.py`, `backend/app/services/event_history.py`, `backend/app/schemas/stocks.py` | Request and query boundaries |
| Scoped selected display quote request and worker | Scheduler and Redis, event-driven fetch | `backend/app/services/stock_quote_demand.py`, `backend/app/tasks/stock_scheduler.py` | Coalescing, quota and task ownership |
| Display quote parsing and authority check | Service/provider, transform | `backend/app/services/alpaca.py`, `backend/app/services/stock_quote_rules.py`, `backend/app/services/stock_admission.py` | Selective reuse |
| Market search/detail client and query hook | Client/hook, request-response | `frontend/src/api/stocks.ts`, `frontend/src/hooks/useStocks.ts` | Decoder and session isolation patterns |
| Stock results and existing Markets layout | Component, UI state | `frontend/src/pages/MarketsPage.tsx` | Exact visual and interaction analog |
| Stable catalog trade entry and owned navigation | Route/component, request-response | `frontend/src/App.tsx`, `frontend/src/components/PortfolioTargetBoundary.tsx`, `frontend/src/components/PortfolioSwitcher.tsx` | Ownership and routing patterns |
| Schema, role and restore integration | Migration/configuration, durable evidence | `backend/app/db/{schema_contract,portfolio_bootstrap,portfolio_migrate,dev_bootstrap}.py`, `deploy/{deploy.sh,db/bootstrap-roles.sql,backup-snapshot.py,verify-restore.py}` | Exact runtime admission and recovery patterns |
| Catalog API and scheduler tests | Tests, isolated PostgreSQL/Redis and simulated HTTP | `backend/tests/{test_stocks_api,test_stock_quote_demand,test_stock_scheduler,test_portfolio_stock_api}.py` | Existing fixtures and invariants |
| Markets and route tests | Tests, component and browser integration | `frontend/src/pages/MarketsPage.test.tsx`, `frontend/e2e/{markets,stocks,stock-trades}.spec.ts`, `deploy/tests/run-stock-browser.py` | Existing navigation and harness |

## Pattern assignments

### Catalog identity, additive migration and classification

- `backend/app/models/stock.py:27–52` uses `CheckConstraint` for the two listing
  exchanges, USD, `common_stock`, source and optional provider evidence. It
  declares `coin_id` as both primary key and foreign key, and makes the
  `provider_asset_id` unique. The analogous Alembic creation is the `op.create_table`
  for `stock_instruments` in revision `0009`, starting at line 154. Use reviewed
  checks, UTC provenance, bounded source identifiers and uniqueness in SQL for
  catalog rows. Give independently classified rows their own stable bigint IDs.
- `backend/app/models/price.py:22–47` shows why search ingestion belongs outside
  the financial `coins` set. `Coin` is unique by `(asset_class, symbol)` even
  for inactive rows. Symbols have a 10-character limit and names a 64-character
  limit. `backend/app/models/trade.py:46,92` holds durable references to those
  IDs. A search result or unchanged ticker cannot safely create or replace a
  book entry. Preserve Phase 18 rows byte-for-byte in migration and refresh.
  Treat a reused ticker as a separate identity only when source evidence
  establishes it. Normalize provider spelling via verified exchange- and
  source-specific alias records rather than collapsing punctuated tickers or
  two share classes into a single canonical string. Preserve prior aliases and
  catalog IDs for historical links. Protect active alias resolution against
  ambiguity with a unique constraint or an explicit conflict state and bound
  approved mappings to the verified underlying identity.
- Preserve financial history's identity access pattern, especially
  `backend/app/services/event_history.py:217–237`. It joins via `Trade.coin_id`
  and requires immutable `StockFillFacts` for every stock trade. Do not derive
  historical positions or receipts from the current alias, refresh generation,
  or a newly minted catalog result. A nullable mapping to a verified financial
  identity may link discovery to the existing curated instruments. Delay any
  new financial projection until Phase 20.

### Catalog refresh and publishing a complete generation

Use the pattern in `backend/app/services/stock_sessions.py:223–266`. The caller
owns the short commit. Expected rows are computed and bounded before the
write. The write compares the complete current review evidence, generation
and DB clock using a guard. The published rows participate in a single
statement. Adapt this to the catalog snapshot, and retain the previous
published generation after a partial, failed or regressive input.

```python
stmt = insert(StockSession).from_select(
    names, select(*(incoming.c[name] for name in names)).where(guard)
)
query = stmt.on_conflict_do_update(
    index_elements=[StockSession.exchange, StockSession.session_date],
    set_={name: stmt.excluded[name] for name in names if name not in ("exchange", "session_date")},
).returning(StockSession.id)
```

`backend/app/tasks/stock_halts.py:76–166` adds an explicit publication fence and
rechecks changed authority. Use a catalog-specific transaction lock where needed.
Never fetch input while holding a financial row lock. Validate source ownership,
complete exchange partitions, stable evidence and coverage before advancing the
published pointer. Treat a failed refresh as operational status alongside the
last verified data. Expired or revoked publication rights still govern display.

### Search and detail API

`backend/app/api/v1/stocks.py:3–27` is the thin, authenticated read pattern.
Keep the explicit response model and cookie/authorization-aware private cache
headers on independently bounded catalog endpoints.

```python
async def get_stocks(
    user: CurrentUserDep, db: DbDep, settings: SettingsDep, response: Response
) -> StocksResponse:
    result = await stocks.list_stocks(db, settings)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Vary"] = "Cookie, Authorization"
    return result
```

`backend/app/services/event_history.py:165–213` supplies a tested
`limit + 1` lookahead and deterministic SQL ordering that ends in a unique
identity. If using a cursor, its codec at lines 37–67 and 79 onwards shows strict
length, shape and version validation. Bind catalog continuation to normalized
query and published generation. Rank exact current ticker first, use stable
identity as the final tiebreaker, and avoid raw wildcard interpolation. An
empty search and quote outage are separate states. Keep search reads local.

### Selected display quote and rights checks

- `backend/app/services/stock_quote_demand.py:24–63` coalesces by scoped key,
  uses `SET NX EX` and a token-bound completion, and bounds wait/TTL. Its
  `pending_stock_quotes` uses `MGET` over the exact curated twenty. For search
  results use a separately bounded pending set keyed by verified catalog
  identity with its mapping/generation, with a hard entry cap and expiry.
  Read a fresh permissible existing display mark before queuing. Re-resolve the
  selected instrument and permission before I/O and again before publication
  so rapid selection, rename or a stale provider response cannot overwrite
  another identity's display. Use an app read path and scheduler-owned data
  write path. Maintain a strict cap on selected work and timeout/byte bounds.
- `backend/app/tasks/stock_scheduler.py:50–75` defines the shared Alpaca
  account budget. It uses Redis time, bounded expiration and the minimum of
  the configured cap and applicable quotes/actions caps. Its request hook at
  lines 182–200 reserves before every actual attempt, including a retry, and
  ensures DB work ends before HTTP. A display request shares the account
  attempt budget. Where it consumes a separate admission, apply that cap too.
  No provider request happens while somebody types, pages local results, or
  simply sees a default result suggestion.
- `backend/app/services/alpaca.py:76–109,130–170` applies byte/structure/decimal
  constraints, accepts only expected response symbols, and distinguishes missing
  from invalid data. `backend/app/services/stock_quote_rules.py:103–175` has
  reusable or extractable price checks for exact decimal sides and mid, IEX
  venue/tape/condition checks and UTC session and freshness checks. At lines
  89–100 `verified_mapping` additionally requires `CURATED_SYMBOLS`, and at
  line 123 `validate_quote` calls it. Retain this execution guard even if
  value checks are factored out for an approved catalog-only display quote.
  Return a price or precise reason against that selection. Store provider
  prices only as long as permitted for their purpose, outside stock execution
  facts and without extending old admission rights to the expanded universe.
- `backend/app/models/stock.py:120–171` protects the current closed product
  list and exact review constraints. `backend/app/services/stock_admission.py:175–250`
  binds audience, account/server, provider feed, field permissions, review
  expiry and quota. `_admissions` in `backend/app/tasks/stock_scheduler.py:78–83`
  loads at most five rows keyed by product. Any new catalog/reference-display
  evidence must leave those Phase 18 trade admissions and exact five-row SQL
  snapshot intact. Keep publication/collection and retention purposes explicit.

### Fixed-twenty consumers to keep intact this phase

| Consumer | Current invariant |
|---|---|
| `services/stock_quotes.py:39–55,152–172` and `services/stock_quote_rules.py:89–100` | Existing financial mappings select only curated active `Coin` rows. Their provider IDs, time and exchange are rechecked. Quote batches are bounded. |
| `tasks/stock_scheduler.py:155–172` and `services/stock_quote_demand.py:29–53` | Full verified set of 20 and 20 distinct provider IDs before existing requests. Demand `MGET` only covers those symbols. |
| `tasks/stock_halts.py:96`, `tasks/stock_actions.py:108–111,386`, `services/stock_admission.py:232–251` | Halt publication and corporate-action access depend on exact curated coverage. One catalog row conveys no action or halt coverage. |
| `services/stock_eligibility.py:144,209,258–259`, `alembic/sql/0024_stock_halt_snapshot.sql` | Financial authority reads the existing scoped snapshots and verifies final evidence. Preserve the guard and existing quote/fill time, decimal and replay contracts. |
| `services/stocks.py:136–168`, `frontend/src/api/stocks.ts:343–380`, `frontend/src/hooks/useStocks.ts:369–388` | The existing stock response requires exactly 20 and its browser authority handling compares row positions across requests. Search needs an independent shape and identity-keyed queries. |

### Markets, client cache and trade-entry navigation

- `frontend/src/pages/MarketsPage.tsx:31–60` holds the market, search and
  selection and currently filters the old client array. Keep the existing
  crypto search and the same visual search field. Bind stocks to a local API
  query keyed by the normalized input and catalog owner scope. Use the request
  `AbortSignal` and discard late responses. Use the current instructions in
  `design-system/birja/pages/markets.md` and retain one accessible input and
  result buttons with keyboard support. `MarketsPage.tsx:109–169,188–211`
  shows labelled search, asset tabs, loading and selected-row focus. Its
  current `asset` falls back to the first result at line 58, so render an
  initial detail if useful without interpreting implicit highlighting as a
  request for a new quote. Use stable catalog ID for explicit selection.
- `frontend/src/api/stocks.ts:343–395` and `frontend/src/hooks/useStocks.ts:358–390`
  show shared API client, strict parsing, abort signalling and cached-session
  fences. Use independent catalog query keys that include query or selected ID
  and scope. Preserve useful results across quote failures. Validate display
  source timestamps and prices and prohibit execution authority in the payload.
  `MarketsPage.tsx:285–320` already uses `MarketOpening`; share exact closed
  countdown behavior and show a retained permitted mark when available.
- The signed-in Markets index is `/` and receives `portfolioId` from the
  ready identity in `frontend/src/App.tsx:208–224,295–303`. Existing explicit
  trade route is `/portfolios/:portfolioId/trade/stocks/:symbol`, wrapped by
  `PortfolioRoute`. When no owner target is ready, the unscoped trade route
  reaches `LegacyTrade` (`App.tsx:196–205,323`), which delegates to
  `PortfolioTargetBoundary`; `PortfolioSwitcher.tsx:19–36,59–63` confirms
  a selected choice from current owned portfolios and lets the destination
  revalidate. Reuse that ownership flow for a new listing-ID-specific trade
  entry, including no-portfolio and multiple-portfolio states. Keep that ID
  through the redirect or cross-check it at the destination. A ticker-only
  link could resolve to a different security after a refresh.
- `backend/app/services/stock_trading.py:114–126,515–523` reveals the hard
  distinction: the current ticket needs an active financial `Coin` and full
  execution evidence to build `ContextOut`. It cannot read arbitrary catalog
  rows. For an expanded result, plan a read-only catalog trade entry with
  the verified owned portfolio and clear disabled order controls or reason.
  `backend/app/api/v2/stock_trades.py:23–33,107–135` shows the ownership
  fence and rollback-before-wait pattern. Preserve this behavior for existing
  orders and require the existing CSRF dependency on any new POST.

### Schema and recovery wiring

`backend/app/db/schema_contract.py:17–25,34–64` selects finite runtime consumers
and verifies the catalogue and owned role/default privilege fingerprints.
`backend/app/db/portfolio_bootstrap.py:608–612` pins the current catalogue, and
`backend/app/db/{portfolio_migrate,dev_bootstrap}.py` pins the approved source
and target. A durable catalog addition needs an additive migration and source
branch preflight, reviewed per-role grants, exact fingerprints and checks for
fresh install, upgrade and restore. Preserve the 0023/0024 predicates and
known-good hashes. Use `backend/alembic/versions/0024_stock_halt_snapshot.py:15–55,58–70`
for source pin/authentication and a downgrade that refuses to discard retained
evidence. Set app reads and only the necessary scheduler/catalog writer grants.

Review `deploy/db/bootstrap-roles.sql` and `deploy/deploy.sh:116–135` for the
same finite selection. In `deploy/backup-snapshot.py:83,1089–1108,1133–1164`,
`deploy/verify-restore.py:579–585,609–653,1036–1048`, and
`deploy/tests/test-stock-halt-recovery.sh:50–85`, use the established pattern
of verifying an exact revision, manifest, digest, ACL and unchanged monetary
evidence. Make explicit which data is durable identity/aliases/provenance and
which display cache is reconstructible and may expire. Recovery acceptance
must verify restored stable catalog IDs and aliases alongside existing book
and receipt evidence. Reuse compatible unaffected results and leave full
release operations to Phase 21.

## Verification analogs

- `backend/tests/test_stocks_api.py:85–128,273–306` verifies auth, privacy,
  local metadata when price authority is missing and expiry at 120 seconds.
- `backend/tests/test_stock_quote_demand.py:6–61` and
  `backend/tests/test_stock_scheduler.py` cover coalescing, token ownership,
  no-consumer timeout, shared account limits and bounded source retries.
  Capture selected ID, query counts, and zero requests from search itself.
- `backend/tests/test_portfolio_stock_api.py:112–208,247–329` covers owner
  isolation, no ambiguous fallback, required CSRF and release of the read
  transaction before a bounded source wait. Include that fence at new trade
  entry and assert creation/confirmation changes no ledger data for catalog-only
  selections.
- `frontend/e2e/stock-trades.spec.ts:62–71,162–175` resolves the active portfolio
  by its actual ID. `deploy/tests/run-stock-browser.py:22–32,87–91,143–153`
  selects explicit spec files; `--suite stocks` currently runs `stock-trades`
  only. If adding a new spec, wire it into the selected suite and confirm it
  runs against the disposable stack. Exercise exact/alias/class search,
  open/closed detail, quote outage, stale selection change, restart and
  preserved selected-portfolio route. Use deterministic provider fixtures in CI.

## Gaps where repository patterns stop

The repository has no existing verified full exchange directory importer,
multi-generation security identity model, or nonfinancial expanded quote
lane. Base classification, licensing, source coverage and acquisition on
the research artifact. Avoid treating a permissive sample or a familiar-looking
ticker as evidence for publishing a row or executing an order.
