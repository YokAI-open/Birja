# Phase 19 source decision

Reviewed November 24, 2026. The local inventory and publisher can use synthetic
fixtures. An expanded live inventory needs dated evidence for the fields and
purposes below. Full live catalog coverage under SC-01 remains open.

| Artifact and fields | Collection and internal use | Derived use and display | Storage and backup | Status |
| --- | --- | --- | --- | --- |
| Nasdaq Trader `nasdaqlisted.txt`. Ticker, primary tier, security name, flag-derived exclusions, source aliases and class label | Public HTTPS format and intended lookup verified. The lookup notice expressly names Nasdaq Listed among Nasdaq Events Data exempt from further license restrictions. Exact application to the downloadable fields and Birja's ongoing use needs a scoped decision. | The notice supports reuse of the named data. Exact directory field coverage and class/name display are open. | Exact long-lived normalized directory field and backup coverage is open. | Fixture path available. [Lookup notice](https://www.nasdaqtrader.com/Trader.aspx?id=symbollookup) · [Definitions](https://www.nasdaqtrader.com/Trader.aspx?id=SymbolDirDefs) · [General terms](https://www.nasdaq.com/legal) |
| Nasdaq Trader `otherlisted.txt`. NYSE ticker, primary exchange, security name, flag-derived exclusions, ACT/CQS/Nasdaq aliases and class label | Public HTTPS capture and file format observed during planning. The lookup notice does not name Other Exchange-Listed in the exempt group. Ongoing catalog collection and internal use are open. | Derived screens and display of the NYSE directory fields are open. | Durable normalized storage and backup are open. | Live audit blocked. [Lookup notice](https://www.nasdaqtrader.com/Trader.aspx?id=symbollookup) · [Definitions](https://www.nasdaqtrader.com/Trader.aspx?id=SymbolDirDefs) · [General terms](https://www.nasdaq.com/legal) |
| OpenFIGI share-class and composite FIGI identifiers | The official API documents anonymous ticker-by-exchange mapping. OpenFIGI grants reuse of FIGI identifiers in its terms. | Identifier reuse is covered by the grant. Birja would display exchange-sourced names rather than OpenFIGI descriptions. | FIGI identifiers fall under the stated reusable identifier grant. | Exact mapping combinations still require current scope for related classification fields. [API documentation](https://www.openfigi.com/api/documentation) · [Terms](https://www.openfigi.com/docs/terms-of-service) · [Exchange codes](https://www.openfigi.com/about/exchange-codes) |
| OpenFIGI exchange and ticker corroboration, sector and two security-type fields, provider alias, normalized classification and evidence digest | The API documents the fields and access mechanics. Terms distinguish related descriptions from FIGI identifiers. Collection and internal use at Birja's intended scale are open for this precise subset. | The FAQ describes associated metadata. The terms and FAQ do not establish the exact scope of durable derived classification and provider alias use for this decision. | Scope for the normalized classification, alias and evidence digest is open. Raw mapping responses remain transient. | Live enrichment blocked. [API documentation](https://www.openfigi.com/api/documentation) · [Terms](https://www.openfigi.com/docs/terms-of-service) · [FAQ](https://www.openfigi.com/about/faq) |
| SEC EDGAR and official exchange exception evidence | The SEC reuse policy covers public material published by the SEC. A specific EDGAR Section 12(b) filing can corroborate its stated ticker, venue and security title. Each exchange notice requires its own applicable scope. | Issue-level facts can support a dated manual exception when the same filing context establishes class, ticker and venue. Issuer CIK alone cannot resolve a share class. | Admitted exception scope must cover the normalized classification, group identity and evidence reference. | No real exception was imported in this plan. [SEC reuse policy](https://www.sec.gov/about/privacy-information#website) · [SEC ticker association FAQ](https://www.sec.gov/about/webmaster-frequently-asked-questions) · [XBRL guide](https://www.sec.gov/files/edgar/filer-information/specifications/xbrl-guide-2024-07-08.pdf) |
| Expanded Alpaca reference and IEX quotes. Asset identifiers, aliases, stock fields and quote values | The Phase 18 source decision is scoped to its initial stock universe. Expanded requests and internal use were not verified here. | A fresh simulated fill and wider stock display require evidence for the corresponding fields and scope. | Expanded persistence and backup are open. | No credentialed calls or activation. [Phase 18 decision](../18-make-simulated-stock-trades-work/18-SOURCE-DECISION.md) · [Alpaca market data documentation](https://docs.alpaca.markets/docs/about-market-data-api) |

## Coverage evidence

- The prior Phase 19 planning sample reached both official HTTPS directories
  with a matching November 24 footer at 12:11 source time. The earlier v1.4
  research counted 7,101 potential listings after the venue, non-test and
  non-ETF screen. That count predates this execution and does not indicate
  how many listings are common or ordinary shares. No exact live snapshot
  hashes, paired source counts or full classification receipt were retained
  in reviewable planning records. [Phase 19 research](19-RESEARCH.md) ·
  [Earlier v1.4 research](../../research/v1.4/SUMMARY.md)
- The inventory fixture reconciles 5 rows across the two sources. Nasdaq has
  1 included, 1 excluded and 1 duplicate. NYSE has 1 included. The
  out-of-scope venue bucket has 1 excluded. All buckets have zero unresolved
  rows. The two included synthetic issues retain distinct share-class and
  punctuation evidence.
- No same-field public official alternative was established for an exhaustive,
  current NYSE and Nasdaq common-stock directory with stable issue IDs. SEC's
  issuer association and Section 12(b) facts support narrow cross-checks. They
  do not establish a complete current directory or continuous identity for
  every share class. [SEC association file](https://www.sec.gov/file/company-tickers-exchange) ·
  [SEC coverage FAQ](https://www.sec.gov/about/webmaster-frequently-asked-questions)

## Inventory admission

`python -m app.tasks.stock_catalog_inventory --output candidate.json fixture`
accepts explicit directory, mapping and as-of inputs. Its deterministic
manifest is labelled `fixture`. Live mode requires a dated rights document
whose reviewed field purposes are current and complete. It refuses unknown
scope before any source request, uses a single private cursor for its run,
stages normalized outcomes with their source-pair hashes, and keeps failed
batches out of the candidate. Exit code `2` leaves a reconciled incomplete
candidate for review. Exit code `1` leaves publication unsupported.

The official OpenFIGI anonymous ceiling is 25 mapping requests per minute at
10 jobs each. Birja bounds calls to 20 attempts per rolling minute and 100 per
invocation, including retries. A complete initial classification could require
several invocations and a sample cannot establish completeness. No live
directory or mapping calls ran during Plan 19-01. [OpenFIGI API limits](https://www.openfigi.com/api/documentation)

## Live activation cache

The planned production Redis service uses a persistent append-only log.
Expanded IEX prices would remain in that log until it is rewritten even
after their serving TTL expires. Before live expanded quotes are enabled,
the selected quote scope must cover this disk retention, or the quotes
must use a volatile cache. The disposable checks use a volatile Redis
instance. The encrypted recovery proof concerns PostgreSQL snapshots.
