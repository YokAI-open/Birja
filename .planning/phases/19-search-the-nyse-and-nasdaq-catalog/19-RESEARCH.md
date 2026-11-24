# Phase 19 research — NYSE and Nasdaq catalog

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked decisions

- **D-01:** Search the refreshed local catalog. Return bounded results with exact
  ticker matches first, support verified aliases and keep share classes distinct.
- **D-02:** Preserve identity and historical links across listing changes.
  Hold ambiguous matches for review and block inactive instruments from
  new orders.
- **D-03:** Show company, ticker and listing exchange. A selection can request
  its own quote and open the trade entry for the selected portfolio. Show the
  actual eligibility reason when a price or order is unavailable.
- **D-04:** Search and the last verified catalog survive quote source failure,
  rate limits and failed catalog refreshes. Use the existing free-data approach
  and require applicable rights for display and retention.
- **D-05:** Keep Birja's approved Markets layout, Inter typography and light
  palette. Use one search field and useful result information. Preserve
  previously approved closed-market copy and the viewer-local countdown.
- **D-06:** Preserve Phase 18 execution authority and all existing crypto and
  portfolio behavior. Full release CI and the remaining historical recovery
  diagnostics stay with Phase 21.

### Scope

Phase 20 owns fills and valuation for newly found stocks. Phase 21 owns release,
production activation and live acceptance of an out-of-list buy and sell.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Behavior | Research support |
| --- | --- | --- |
| SC-01 | Search active common shares by ticker or name, exact ticker first, with auditable coverage | Paired directory baseline, positive classification and reconciled coverage report |
| SC-02 | Distinct share classes, verified aliases, stable historical identity and refusal on ambiguity or inactivity | Internal ID, share-class corroboration and temporal listing records |
| SC-03 | Select an out-of-list company and exchange, request price and reach the selected portfolio's trade entry | Separate selected-price path and owned portfolio entry with explicit reasons |
| SC-04 | Bounded local search and selected-only pricing that tolerates provider outages | Atomic catalog publication, bounded scheduler work and independent cache failures |

</phase_requirements>

## Summary

**Researched:** 2026-11-24. **Confidence:** high on documented inputs and local
boundaries, medium on prospective coverage, open on several exact data rights.

Use the Nasdaq Trader listing files as the candidate exchange baseline and
OpenFIGI's free mapping endpoint as the issue-level classifier and corroboration
source. Use SEC filings for a bounded exception review. Store a local catalog
generation and stable Birja identity for search. Verify specific rights and
reconcile coverage before a live generation is publishable. A synthetic
complete snapshot can exercise the whole implementation and blocked cases.
Missing permission, unresolved securities, and absent live coverage must
remain visible in the execution receipt. [VERIFIED: current source docs and
directory samples below]

## Architectural Responsibility Map

| Capability | Primary tier | Secondary tier | Rationale |
| --- | --- | --- | --- |
| Acquisition, source checks and attempts | Dedicated scheduler or restricted operator command | External source | Shared attempt limits and no browser credentials |
| Snapshot reconciliation and identity | PostgreSQL | Backend service | Atomic publish, stable IDs and indexed local search |
| Search, detail and owned trade entry | Authenticated API | PostgreSQL | Validate bounds and enforce portfolio ownership |
| Search and selected quote presentation | React with TanStack Query | Authenticated API | Independent query states and existing Markets layout |
| Selected quote collection | Existing dedicated stock scheduler | Redis and PostgreSQL | Redis coalesces bounded demand. PostgreSQL retains admitted prices. |

## Source evaluation

### Exchange baseline

- Both official HTTPS endpoints returned pipe-delimited files with their
  respective headings and a matching November 24 footer captured at 12:11
  source time. Parse `nasdaqlisted.txt` for `Q`, `G`, and `S` markets and
  `otherlisted.txt` for `N` alone. Keep ACT, CQS, and Nasdaq aliases
  distinguishable. Require recognizable headings, terminal creation marker,
  credible recency, coherent pair and exact exchange/test/ETF flag validation.
  The next refresh may produce different counts and times. [VERIFIED: official
  HTTPS samples] [Nasdaq-listed](https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt) ·
  [Other listings](https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt) ·
  [Field definitions](https://nasdaqtrader.com/Trader.aspx?id=SymbolDirDefs)
- Both files contain eligible and out-of-scope securities. The observed
  non-ETF rows include depositary shares, units and warrants. Free-form
  security names help explain classification and supply corroboration.
  Positive issue-level classification is necessary after the initial
  exchange, test and ETF filters. Upcoming listings and intraday changes
  follow exchange update schedules, so publish an as-of time and compare
  coverage against the paired captured snapshots. [VERIFIED: official HTTPS
  samples] [Nasdaq publication notice](https://www.nasdaqtrader.com/TraderNews.aspx?id=ETA2026-64)
- The exchange lookup exempts the named Nasdaq Events Data, including
  Nasdaq Listed, from further license restrictions. Check that this covers
  the exact artifact and intended fields. The notice does not expressly name
  Other Exchange-Listed. Nasdaq's general service terms restrict reuse.
  Public availability and an HTTPS response establish acquisition mechanics.
  Keep production eligibility for the Other Exchange-Listed artifact
  conditional on applicable written terms or an already applicable
  authorization. Use restricted evidence and aggregate counts when field
  display rights are unresolved. [CITED: Nasdaq Symbol Lookup and Legal]
  [Lookup notice](https://www.nasdaqtrader.com/Trader.aspx?id=symbollookup) ·
  [Nasdaq terms](https://www.nasdaq.com/legal)

### Common-stock classification and identity

- OpenFIGI `POST /v3/mapping` accepts ticker lookups constrained by exchange
  code or MIC and returns `marketSector`, `securityType`, `securityType2`,
  `shareClassFIGI` and `compositeFIGI` with possible null values. Start with
  the directory-derived venue and exact sourced ticker. Candidate venue
  codes are NYSE `UN` and Nasdaq G/S/Q mapped to `UQ`/`UR`/`UW`.
  A U.S. composite can corroborate a matching class where it is needed.
  Collect all bounded candidates to check conflicts before selecting a
  classification. Require a positively supported common or ordinary share
  and consistent issue evidence, including class-level identity when available.
  Hold missing, null, conflicting, and unsupported results for review.
  Handle provider punctuation with reviewed exact mappings. Avoid merging class
  A and B through a shared issuer, stripped symbol or fuzzy name. [CITED:
  official OpenFIGI API, exchange codes and allocation rules]
  [API](https://www.openfigi.com/api/documentation) ·
  [Exchange codes](https://www.openfigi.com/about/exchange-codes) ·
  [Allocation rules](https://www.openfigi.com/about/allocation-rules)
- Official OpenFIGI limits are 25 anonymous mapping calls per minute, 10 jobs
  each, and 250 calls with an API key, 100 jobs each. The earlier 7,101
  potential rows would take 711 anonymous calls on a one-job-per-row pass.
  A local target of 20 requests per minute budgets about 36 minutes before
  retries or second lookups. This is a capacity estimate, with no live
  claim about match rate. Stage the first pass outside the request path,
  checkpoint progress, and reclassify changed entries on future refreshes.
  Respect documented response quota headers and Retry-After. Bound response
  size and jobs, avoid turning an error batch into omissions, and use the
  existing no-key path for the plan. [CITED: OpenFIGI API] [VERIFIED: prior
  local source sample and arithmetic]
  [API limits](https://www.openfigi.com/api/documentation) ·
  [v1.4 research](../../research/v1.4/SUMMARY.md)
- OpenFIGI's terms expressly grant reuse of FIGI identifiers. The FAQ
  describes open associated metadata, while the terms distinguish related
  security descriptions from the identifiers. Check stored classification
  fields and derived evidence separately. Use admitted IDs and minimal
  normalized evidence, retain a citation or digest, and source displayed
  names from independently admitted listing or EDGAR facts. Exclude raw
  OpenFIGI responses from serving, backups and committed fixtures. [CITED:
  official OpenFIGI terms and FAQ]
  [Terms](https://www.openfigi.com/docs/terms-of-service) ·
  [FAQ](https://www.openfigi.com/about/faq)
- SEC's exchange ticker file helps cross-check ticker, venue and issuer.
  Its ticker association FAQ disclaims completeness and accuracy. CIK
  identifies the filer, so use it for issuer corroboration. Private name
  enrichment or permanent share-class identity should require issue-level
  evidence. For a finite exception set, join a relevant public filing's
  Section 12(b) security title, ticker and exchange in the same context.
  The SEC allows reuse of its own public content and EDGAR public filing
  content and publishes an access policy for automation. Reuse those
  limited facts, with a contact-bearing User-Agent and a conservative
  shared rate if later automated. Phase 19 does not need a full EDGAR crawler.
  [CITED: SEC FAQ, dissemination policy, exchange ticker file and XBRL Guide]
  [FAQ](https://www.sec.gov/about/webmaster-frequently-asked-questions) ·
  [SEC reuse policy](https://www.sec.gov/about/privacy-information#website) ·
  [Exchange tickers](https://www.sec.gov/file/company-tickers-exchange) ·
  [XBRL Guide](https://www.sec.gov/files/edgar/filer-information/specifications/xbrl-guide-2024-07-08.pdf)

### Provider identity and selected price

- Alpaca's Assets API provides a provider mapping by symbol or ID with
  asset class, listing exchange, and status. Its `us_equity` classification
  includes multiple security types. Alpaca explicitly documents the
  missing stock/ETF categorization in its Asset API FAQ.
  Treat provider ID, exact ticker and exchange as quote lookup evidence.
  Keep exchange membership, share type, provider coverage, and application
  order authority as separate checks. Brokerage `tradable` does not attest
  that a listing has current IEX quotes or is free of halts. [CITED: Alpaca
  Assets and Broker FAQ]
  [Assets](https://docs.alpaca.markets/us/v1.1/reference/get-v2-assets-1) ·
  [FAQ](https://docs.alpaca.markets/us/docs/broker-api-faq)
- The free plan's real-time feed is IEX. It can return sparse or missing
  quotes for an otherwise active listing. Current public customer
  terms constrain distribution of market data and earlier Birja acceptance
  covers its original scope. Record the actual account, feed, field scope,
  usage, display, retention and expiry before broadening access. Keep the
  feature measurable with synthetic HTTP fixtures and a concrete provider
  coverage refusal when an appropriate quote is absent. Treat the prior
  execution evidence as limited to Phase 18. [CITED: Alpaca plan and
  agreements] [VERIFIED: local Phase 18 verification]
  [Market Data API](https://docs.alpaca.markets/us/v1.1/docs/about-market-data-api) ·
  [Alpaca disclosures](https://alpaca.markets/disclosures) ·
  [Phase 18](../18-make-simulated-stock-trades-work/18-VERIFICATION.md)

## Architecture Patterns

1. **Transactional catalog and audit.** Stage both directory inputs, normalize
   names and exact aliases, classify all target rows, then publish one
   generation atomically after validation. Record per source digest and
   creation timestamp, observed/accepted/excluded/review/duplicate counts and
   reason for every input row. Require the dispositions to reconcile exactly
   per exchange. Distinguish rows excluded by established type from rows still
   in review. Report coverage of positively known common shares, unresolved
   coverage and admission status separately. A failure or suspected mass
   removal preserves the prior generation. A valid new snapshot plus
   corroboration can retire an instrument. Record observed time and verified
   use separately from lifecycle state. Expired permissions suppress affected
   fields. Retain the original generation while its use remains allowed.
   [Recommendation based on the paired endpoint structure and D-01–D-04]
2. **Identity separate from aliases.** Allocate a stable internal bigint ID
   and retain source identifiers as evidence. Bind current ticker, venue,
   alias namespace and effective interval to that ID. Keep prior aliases and
   historical financial records attached to their original ID. Verified
   symbol or venue changes transition the same identity. An active conflicting
   reuse must resolve to a new identity or explicit review. Preserve direct
   stable-ID links and reject stale generation/identity across selection,
   provider requests and result display. No automatic money or position
   changes from a catalog refresh. [Recommendation based on OpenFIGI
   allocation rules and D-02]
3. **Bounded local query.** Use a parameterized PostgreSQL query behind a
   separate authenticated additive route. Trim and bound query length,
   case-fold for matching and use literal wildcard handling. Rank current
   exact ticker ahead of verified aliases, prefixes and name matches. End
   ordering with the stable ID and cap results (20 is an initial testable
   default). Search reads local admitted fields and triggers zero external
   calls. Return a stable ID, company, ticker, exchange, class label if
   meaningful and selection state. [Recommendation based on CLAUDE.md
   API and DB rules and D-01, D-04]
4. **Selected display quote.** Leave the existing curated path intact. For an
   expanded entry, enqueue only a selected active mapped ID under effective
   catalog and quote rights. Tie a coalesced key and completion to the ID,
   effective listing generation and provider mapping. Have the existing
   stock scheduler consume a finite ready batch under the shared provider
   attempt budget. Reject mismatched, stale or invalid price data and bind
   results to the same listing identity before returning them. Keep a
   selected display quote distinct from a financial instrument and preserve
   decimal strings, IEX attribution, source timestamp, and actual refusal
   reasons. Retain a legally permitted last mark for closed display when
   available. [Recommendation based on local quote and admission code]
5. **Owned trade entry and execution fence.** Resolve the selected portfolio
   with the existing owned-active guard and recheck after any quote wait.
   An otherwise valid Phase 19 symbol can open the owned existing trade
   experience in its preview/detail state. A missing quote, held identity,
   inactive listing, or execution gate communicates a clear reason.
   Phase 20 owns the financial promotion to the existing money/state
   checks. Preserve current crypto, curated stock execution, immutable
   receipts and historic paths. [Recommendation based on D-03, D-06 and
   Phase 20 requirements]

## Standard Stack and Repository Patterns

| Area | Existing stack and implementation pattern |
| --- | --- |
| Persistent identity and atomic writes | PostgreSQL and SQLAlchemy async 2.0.55 with an explicit Alembic 1.20.1 successor to 0024. Beside existing `StockInstrument`, retain a separate searchable identity and listing/alias provenance when a financial `coin_id` is absent. [VERIFIED: `backend/app/models/stock.py`, `backend/uv.lock`, Phase 18] |
| HTTP ingestion and decoding | Locked httpx 0.28.1 and standard-library parsing. Follow bounded transport and Decimal validation in `backend/app/services/alpaca.py`, purpose-specific admissions in `stock_admission.py` and report scheduling in `tasks/stock_halts.py`. [VERIFIED: source and `backend/pyproject.toml`] |
| Request coalescing | Redis expiring tokens and shared attempt limits in `stock_quote_demand.py` and `tasks/stock_scheduler.py`. Current demand selector reads the fixed curated set. Consume a bounded pending set for expanded IDs or extend that pattern safely. [VERIFIED: source] |
| API and UI | Existing authenticated FastAPI 0.162.0 stock routes and portfolio v2 dependency patterns. React Query 5.105.0, Markets layout and portfolio switch contract. [VERIFIED: `backend/uv.lock`, `backend/app/api/v1/stocks.py`, `backend/app/api/v2/stock_trades.py`, `frontend/package.json`, `StockSection.tsx`] |
| Tests | pytest 9.1.1, respx 0.23.1, Vitest 5.0.5 and Playwright 1.64.1. Use the isolated PostgreSQL/Redis stack and synthetic network fixtures. [VERIFIED: `backend/pyproject.toml`, `frontend/package.json`, CLAUDE.md] |

### Existing choke points to preserve

The current `StockQuote` table references financial `stock_instruments.coin_id`;
`verified_mapping`, existing quote and halt schedulers, stock actions and
current order eligibility all assume `CURATED_SYMBOLS`. The migration's
catalogue and grant fingerprints are enforced by startup and recovery.
Preserve the existing financial path. If shared low-level quote parsing or
attempt accounting is factored for expanded previews, keep curated semantics
verified and separate from the expanded display proof. A new persistent schema
requires a coherent runtime/backup/restore contract, exact roles and localized
restore checks, with Phase 21 retaining full release validation. [VERIFIED:
`backend/app/models/stock.py`, `stock_quote_rules.py`, `stock_eligibility.py`,
`tasks/stock_halts.py`, `tasks/stock_actions.py`, `app/db/schema_contract.py`,
`deploy/RUNBOOK.md`]

## Project Constraints (from AGENTS.md)

Follow shared CLAUDE.md architecture, test, migration, monetary precision and
development rules. Use GSD with the repo adapter and preserve existing phase
history. Use established Markets tokens and the local UI design guidance.
Limit review to defensive outcomes. Preserve explicit push, merge and
deployment approvals. No new dependency, signup, paid tier, or provider
outreach is necessary for the planned synthetic path. [VERIFIED: AGENTS.md,
CLAUDE.md, 19-CONTEXT.md]

## Runtime State Inventory

| Category | Checked item and planned treatment |
| --- | --- |
| Stored data | Phase 18 revision 0024 and its financial stock and portfolio identities. Plan an additive migration with unchanged historical IDs and side-by-side discovery records. Confirm fresh and upgrade paths. [VERIFIED: stock models and Phase 18 verification] |
| Service configuration | Use the existing dedicated scheduler and purpose-specific provider review. Supply a separate default-denied discovery scope where current evidence is narrower. Existing curated settings keep their original scope. [VERIFIED: `tasks/stock_scheduler.py` and `services/stock_admission.py`] |
| OS registrations | Existing service, timer and deploy tooling remain under the project runbook. Catalog collection belongs to the existing scheduler or an operator-run command. Production registration was outside this research. [VERIFIED: `deploy/RUNBOOK.md`] |
| Secrets and variables | The current stock client keeps provider credentials server-side. Anonymous classification needs no added key. Existing keys stay selected by the current environment contract. [VERIFIED: `services/alpaca.py`] [CITED: OpenFIGI API](https://www.openfigi.com/api/documentation) |
| Build artifacts | Locked dependencies and existing dev/CI images suffice for fixture implementation. Any successor schema requires an explicit current startup/recovery contract and a focused restore check. [VERIFIED: lockfiles, Compose test config and Phase 18 verification] |

## Environment Availability

The planning checkout has Python 3.14.9 in the existing backend environment,
Node 24.22.1, uv 0.13.5, and Docker CLI 29.2.1. The Compose test configuration
pins isolated PostgreSQL and Redis images. Existing runtimes support the
proposed fixture path. Live provider credentials, active rights, expanded
mapping fidelity, and live production services were outside the research
verification scope. [VERIFIED: version probes and `docker-compose.test.yml`]

## Validation Architecture

Reuse the existing tests and owned browser harness. Add explicit Phase 19
cases to the owning task before it is accepted. Rights/capability checks
use a dated evidence receipt and synthetic refusal cases. Live exchange
metadata can be measured only where permitted, with zero production writes.

| Requirement | Automated checks |
| --- | --- |
| SC-01 | Fixture snapshot with Nasdaq + NYSE common shares, ETFs, ADRs, preferreds, units, funds, OTC listings, test issues and unresolved types. Assert exact source-row dispositions, deterministic rank, cap and empty response. |
| SC-02 | Same-issuer two classes, exact aliases, verified rename and move, two current aliases in conflict, delist and ticker reuse. Check stable IDs, preserved histories and never attach a stale selected ID to a new occupant. |
| SC-03 | Authenticated out-of-list selection and selected portfolio detail. Assert own/foreign/closed target behavior, shown quote, closed market, absent quote, review/inactive reasons, price source and timestamp. Assert no new-symbol fill during this phase. |
| SC-04 | Search sends zero provider calls. Selected quote request is bounded and coalesced. Test provider throttling, missing quotes, Redis loss, rejected/truncated/regressed catalog refresh, still-searchable last generation and independently active crypto/curated flow. |
| Migration | Fresh and 0024-upgrade catalogs, app/scheduler role boundary, focused exact retained restore, preserved pre-existing identifiers, legitimate downgrade/refusal disposition. |

Use fixture HTTP unit/parser tests, FastAPI application tests with actual local
PostgreSQL and Redis, Vitest component tests and the existing Playwright stock
scenario runner for selection and reflow. Run the repository coverage checks
for affected existing critical modules. Retain historical diagnostics and
release-specific broad runs in Phase 21. [VERIFIED: CLAUDE.md, 18-VALIDATION.md,
deploy/tests/run-stock-browser.py]

## Assumptions and open gates

| Question | Disposition |
| --- | --- |
| Does the exact NYSE candidate artifact permit automated collection and serving/storage for Birja? | Open. Record the per-artifact data-use decision. Existing published notices do not expressly name the other-listed file in the unrestricted grant. |
| Will every baseline common share map uniquely under free access? | Open. Use a bounded, resumable qualifying sample or audit when authorized. Reconcile every captured row precisely. Attribute unknown/missing entries without claiming complete live coverage. |
| Can Birja use the intended OpenFIGI type and issuer metadata? | The identifier grant is confirmed. Confirm the relevant metadata and derived assertions separately, use only the minimum needed fields, and keep raw unrelated fields out of the catalog. |
| Will the existing Alpaca account cover selected prices beyond the original 20? | Open. Preserve current feed, scope and flags with fixture verification. Expanded live enablement follows the account/product/symbol use and quota evidence. |

The implementation can proceed using fixtures under the approved scope.
The later qualification record should state which rights, sources, symbols
and coverage were verified, and which were gated. [Recommendation]

## Security Domain

Use authenticated app routes and the current CSRF guard for selected quote
enqueue. Use predefined official endpoints, strict bounds, validation and
allowlisted fields across provider interfaces, and minimal logged metadata.
Use a restricted ingestion identity, read-only search projection, and separate
financial authorization. Exercise benign permission, source failure and
validation cases in isolation. [VERIFIED: AGENTS.md and CLAUDE.md patterns]

| Applicable control area | Phase check |
| --- | --- |
| Authentication, session and authorization | Missing session, closed portfolio, foreign portfolio and catalog-only order refusal |
| Data validation and business logic | Parameterized bounded search, positive type/identity checks and stale selection refusal |
| API communication and provider access | Fixed HTTPS destinations, payload limits, bounded retries and server-only credentials |
| Data protection and logging | Admission before serving or retaining fields, protected artifacts and redacted failure summaries |

The matrix uses the applicable control areas of the existing repository
rules and the application security verification standard. It defines the
focused checks above. [CITED: OWASP ASVS](https://asvs.owasp.org/)
