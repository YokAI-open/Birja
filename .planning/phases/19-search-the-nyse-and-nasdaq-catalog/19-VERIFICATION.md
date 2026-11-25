---
phase: 19-search-the-nyse-and-nasdaq-catalog
verified: 2026-11-24T19:50:04Z
status: gaps_found
score: 14/15 must-haves verified
overrides_applied: 0
runtime: cc31da5
evidence: 8b69f52
gaps:
  - truth: All active NYSE and Nasdaq common shares are accounted for in a refreshed, admitted catalog.
    status: partial
    reason: The synthetic inventory reconciles. Exact live directory scope, classification and coverage are still open.
    artifacts:
      - path: .planning/phases/19-search-the-nyse-and-nasdaq-catalog/19-SOURCE-DECISION.md
        issue: Dated rights and full live classification receipts have not been established.
    missing:
      - Field-specific evidence for collection, derived classification, display, storage and backup of both directory sources and classification evidence.
      - A complete dated receipt reconciling the admitted exchange snapshots, exclusions, duplicates and any unresolved issue, followed by publication of the complete catalog.
deferred:
  - truth: Eligible out-of-list stocks can be traded and valued.
    addressed_in: Phase 20
    evidence: Roadmap criteria cover new-symbol fills, valuation and corporate actions.
  - truth: A production out-of-list journey uses real expanded IEX data.
    addressed_in: Phase 21
    evidence: Roadmap criterion 3 requires a live IEX buy and sell after approved rollout. Expanded reference and quote use, Redis retention and live quote verification remain open conditions.
---

# Phase 19 verification

The goal is to find and select supported common shares by name or ticker, including shares beyond the original 20. The implemented paths work on the isolated fixture stack. Full phase acceptance remains blocked on live catalog coverage under SC-01. The exact provider and production cache conditions remain open for expanded live use. [Roadmap](../../ROADMAP.md) · [Source decision](19-SOURCE-DECISION.md)

## Observable truths

| # | Truth | Status | Evidence |
|---:|---|---|---|
| 1 | Search the loaded catalog with exact ticker priority, distinct classes and bounded results. Open a distinct out-of-list detail and ticket. | Verified on fixtures | SQL orders exact ticker, exact alias, prefix and name matches with deterministic ties. The browser selects FQXA by keyboard and opens its own portfolio ticket. |
| 2 | Refresh preserves durable issue identities and historical links. Search continues through price failure. | Verified on fixtures | Publication tests exercise rename, venue move and ticker reuse. The browser keeps the original link read-only after reuse and searches through a provider outage. |
| 3 | Selection requests its own market data and shows the price or a reason. | Verified on fixtures | The browser records only the explicitly selected fixture symbol, checks its IEX-shaped price, and verifies the source error and retry state. |
| 4 | Reconcile all live rows of both exchange baselines to included, excluded, duplicate or unresolved classifications. | Failed for live coverage | The five-row fixture reconciles. The earlier approximate exchange screen lacks a complete classification receipt and an admitted pair of live snapshots. |
| 5 | Failed acquisition or unknown field rights prevent live publication. | Verified | Inventory refuses unknown scope before HTTP. The publisher requires a complete manifest and a matching current operator admission. |
| 6 | The classifier distinguishes share classes and requires positive common-stock evidence. | Verified | Directory and mapping checks exercised punctuation, distinct identities, ordinary shares, explicit exclusions and unresolved classifications. |
| 7 | Rejected refresh preserves the last admitted generation. | Verified | Publication validates the candidate under a lock before moving the active pointer and rejects ambiguous cross-source reuse. Tests cover incomplete candidates, stale review and competing publications. |
| 8 | Selected prices require an exact active provider mapping and reviewed USD share units. | Verified on fixtures | Promotion binds the catalog and listing version. Operator staging rechecks the claim before each request. The quote worker rebinds rights and listing state before publication. |
| 9 | Startup and administrative migration enforce exact schema and grants. | Verified | Revision 0025 matches the runtime and migration contracts. Fresh and staged upgrade evidence is recorded under the final schema hashes. |
| 10 | Encrypted recovery preserves catalog identity, prior finance and the original expiry. | Verified | The retained 0024 and current 0025 local TLS restore lanes matched snapshot evidence. The final log records identity continuity and no restored eligibility. |
| 11 | Catalog reads tolerate Redis loss and expanded prices are absent from the PostgreSQL archive. | Verified | The search HTTP test substitutes a Redis dependency that refuses all calls. The encrypted archive test verifies that the Redis quote canary is absent from its extracted SQL. |
| 12 | Authenticated search and stable detail use admitted local data without provider calls. | Verified | Both v1 routes use the SQL search service. The HTTP assertions cover auth, read-only behavior, private response headers and zero outbound traffic. |
| 13 | Selected demand coalesces under the shared provider budget. | Verified | The Redis demand keys bind account and listing context. Scheduler tests cover coalescing, the eight-selection instruction ceiling, reviewed symbol caps, retries and the shared quota. |
| 14 | The new result opens a read-only context for the selected owned active portfolio. | Verified | Owned portfolio dependency and fencing surround the cached read. Browser and API tests verify portfolio switching, unavailable targets and absence of financial writes. |
| 15 | Markets shows the selected listing and session in the existing layout. Curated stock and crypto remain usable. | Verified | Chromium covers mobile focus restoration, closed price and countdown, and outage fallback. The six-case run includes curated and crypto buy/sell journeys. |

## Artifacts, links and flowing data

The SDK artifact checks passed all 15 named artifacts. All 14 semantic links were manually confirmed. The literal-path checker recognized two links and missed the Python imports, TypeScript imports and dynamically constructed spec path.

| Plans | Verified artifact and link chain |
|---|---|
| 01–02 | The inventory consumes normalized rows and terminal classifications. The import command calls `publish_catalog` and `promote_catalog_mappings`. The latter rechecks normalized provider evidence against the exact active listing. Migration 0025 creates separate versioned catalog tables. |
| 03 | `deploy.sh` pins `portfolio_migrate.py` and invokes the reviewed preflight. `verify-restore.py` uses `backup-snapshot.py` for versioned catalog projections and compares the restored active pointer, table evidence and grants. |
| 04 | The v1 router includes `stock_catalog`. Its search service queries active durable listings and checks field admissions before returning normalized results and stable IDs. |
| 05 | The v2 router includes the selected quote and owned trade context. `post_catalog_quote` calls the bounded demand service after admission. The scheduler runs `run_catalog_quote_cycle`, which uses `reserve_account_attempt` and rechecks listing identity. The owned GET uses `OwnedActivePortfolioDep`. |
| 06 | `MarketsPage` takes result data from `useStockCatalogSearch`, whose client calls the v1 API. Explicit selection calls `useSelectedCatalogPrice`, which sends the listing version and decodes the matching response. `App.tsx` mounts the ticket beneath `PortfolioRoute`. `StockCatalogTradePage` gets the owned context from `useCatalogTradeContext` and displays a permitted cache mark or reason. `run-stock-browser.py` includes the spec in both `catalog` and `all`. |

## Requirement disposition

| Requirement | Plans | Status | Evidence |
|---|---|---|---|
| SC-01 | 01, 02, 04, 06 | Blocked on live coverage | Search ranking, class distinction, bounds and empty states work on fixtures. A complete admitted live catalog is still absent. |
| SC-02 | 01–06 | Verified | Exact identity and aliases persist. Rename, venue change, rejected refresh, retirement and ticker reuse leave the original historical identity distinct. The read-only catalog route never gains order authority. |
| SC-03 | 02, 05, 06 | Verified for local Phase 19 behavior | The isolated app selects a mapped out-of-list fixture, shows its listing and exact quote or refusal, and opens the owned ticket. Expanded live data use and proof stay open. |
| SC-04 | 01–06 | Verified | Postgres-only reads, bounded selected requests, Redis coalescing, shared quota, retry limits and outage behavior match the contract. Field expiry still controls which listings can be shown. |

## Test and release evidence

- Independently ran four pure fixture parser and classifier checks, both operator CLI help commands, the isolated browser runner help and shell syntax checks, and all 12 catalog trade-page component cases. Direct pytest setup requires the disposable PostgreSQL fixture. The independent check used pure test functions while that stack was down.
- Read the final run receipts for 119 affected backend cases and four Chromium catalog journeys. The resolution record includes 29 focused frontend cases. The earlier full frontend run passed 1,356 cases, the retained backend run passed 216, and the six-case browser run included curated and crypto acceptance. [Phase 19 review](19-REVIEW.md) · [Browser summary](19-06-SUMMARY.md)
- The final local TLS recovery receipt records paired encrypted snapshot integrity, unchanged retained financial evidence, restored catalog identity, original expiry, quote canary exclusion and downgrade refusal with retained catalog evidence. The isolated PostgreSQL recovery suite uses the guarded recovery harness. The plans declare no standalone verification probes. [Recovery summary](19-03-SUMMARY.md)
- The UI run verified keyboard interaction, focus and narrow reflow. It used a 640px viewport as the desktop reflow check. Native desktop 200% zoom remains unmeasured and can be observed during release browser acceptance.
- Expanded live activation still requires verified reference and IEX field rights and a cache that meets them. Production Compose currently uses Redis append-only persistence, so the cache decision must account for retention through log rewrite or provide a volatile instance. The PostgreSQL archive proof is separate from this Redis condition. [Source decision](19-SOURCE-DECISION.md) · [Release handoff](19-VALIDATION.md)

No stub or unresolved blocker marker was found in changed runtime code. The review corrections have passing evidence at `cc31da5`. The live inventory gap keeps Phase 19 open.
