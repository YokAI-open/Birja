# Phase 21 live-source qualification

Reviewed public documentation on 2026-11-25. The expanded live acquisition
and activation checks are pending. Phase 7's owner attestation and Phase 18's
measured original-20 run support their recorded scope. [Phase 18 evidence](../18-make-simulated-stock-trades-work/18-SOURCE-DECISION.md) · [Phase 19 source decision](../19-search-the-nyse-and-nasdaq-catalog/19-SOURCE-DECISION.md)

## Evidence needed

| Evidence | Public finding | Disposition |
|---|---|---|
| Exchange directories | Nasdaq Trader documents both files. The Symbol Lookup reuse notice names its Nasdaq Listed data. Applying that notice to the exact file and the NYSE subset of `otherlisted.txt` requires evidence for the relevant fields, derived class/aliases, multi-user display and retained catalog/backups. | Full two-venue live inventory and publication pending. [Lookup notice](https://www.nasdaqtrader.com/Trader.aspx?id=symbollookup) · [Directory definitions](https://www.nasdaqtrader.com/Trader.aspx?id=SymbolDirDefs) |
| Classification | OpenFIGI's terms dedicate FIGI identifiers to the public domain. The separate associated descriptions and normalized class evidence need scope for Birja's exact use. SEC issuer filings can corroborate a reviewed class/venue exception, and the SEC ticker associations carry no accuracy or completeness guarantee. | Scope for the full mapping workflow pending. [OpenFIGI terms](https://www.openfigi.com/docs/terms-of-service) · [SEC FAQ](https://www.sec.gov/about/webmaster-frequently-asked-questions) |
| Alpaca assets and IEX | Basic documents access to IEX real-time equity data. The published securities customer agreement has restrictions on reproduction and distribution. The owner attested to the expanded Alpaca scope below. | ORCL asset and quote access verified in the bounded probe. Exact agreement terms and broader live qualification remain pending. [Basic plan](https://docs.alpaca.markets/us/docs/about-market-data-api) · [Published customer agreement, section 30](https://files.alpaca.markets/disclosures/library/AcctAppMarginAndCustAgmt.pdf) |
| Corporate actions and halt reports | Alpaca's REST docs cover incomplete events and disclose variable availability. Nasdaq documents the reported-halt feed and its polling interval. | Verify applicable durable action, report and backup scopes, measured replay and known-ID access, window coverage, timing, and shared quota for the exact cohort. [Alpaca actions](https://docs.alpaca.markets/us/reference/corporateactions-1) · [Nasdaq halt RSS](https://www.nasdaqtrader.com/Trader.aspx?id=TradeHaltRSS) |
| Cache and recovery | Plan 02 passed real restart and storage checks for the pinned volatile Redis candidate. Financial PostgreSQL quote, mark, fill and action data follows its separate admitted retention and exact restore contract. | Use the qualified volatile candidate for transient catalog fields when approved. Actual durable-data rights and authorized host verification remain pending. [Plan 02 evidence](21-02-SUMMARY.md) |

Applicable private agreements or dated source-scope evidence can be reviewed
in the owner's existing private custody. Keep only the reference, exact
fields and purposes, review time and applicable expiry in sanitized receipts.
Public product documentation is sufficient for proposed API mechanics.
The existing written-evidence and admission checks must pass before any
live quote, retained financial fact, or catalog generation is activated.

## Proposed finite measurement

The scope below is an upper-bound proposal. Final approval names the
reviewed rights, exact targets, destination, calendar window and allowable
account limits. These limits count failed attempts. The lower reviewed or
configured limit applies.

- Directory reconciliation uses the guarded `stock_catalog_inventory live`
  command, one private cursor and the existing two allowlisted HTTPS directory
  files. An initial campaign can use at most nine invocations in 60 minutes,
  with two directory GETs per invocation and OpenFIGI at the existing ceiling
  of 10 jobs/request, 20 attempts/minute and 100 attempts/invocation.
  Nine invocations allow at most 900 mapping attempts. This is planning
  headroom against the prior roughly 7,100-row screened candidate, with no
  claim about the current row count. Respect source-pair time bounds and
  stop/resume rules. The publishable result reconciles included, excluded,
  duplicates and unresolved for each venue with zero unresolved. Preserve
  a private incomplete manifest if any bound or source check stops the run.
- Credentialed measurement runs after exact scope and targets are approved
  in a disposable `0026` stack. Use up to two separately listed asset lookups,
  the configured Alpaca data endpoints with `feed=iex`, bounded action REST
  and mutation replay, and the official report. An initial proposal allows
  at most 20 combined asset/quote/action attempts in 15 minutes, plus up to
  three halt reports spaced by at least one minute. Include a selected and
  a held-only quote attempt with no overlapping selected demand, advancing
  original timestamps, shared accounting and valid age below 120 seconds.
  Record the measured limit, reset, latency, cap and incomplete results.
  Stop on lost scope, no session evidence or an exhausted provider response.
  Preserve the exact incomplete reason if the bounded window cannot prove
  the required action coverage. [Operator contract](../../../deploy/STOCK-DATA-ADMISSION.md)
- Verify the actual regular session before requesting a window in Eastern
  time and UTC. November 26 is closed and the November 27 NYSE/Nasdaq
  regular equity session closes at 13:00 ET. Choose the actual campaign time
  later using the verified release and source state. [NYSE hours](https://www.nyse.com/trade/hours-calendars) · [Nasdaq calendar](https://nasdaqtrader.com/Trader.aspx?id=Calendar)

The full Plan 06 campaign remains pending. SC-01 and SC-03 remain open.
The software release is published. The owner-attested Alpaca scope and
the completed one-stock read-only probe are recorded below.

## Owner confirmation and ORCL probe on 2026-11-25

The owner confirmed that the existing Alpaca approval covers the expanded
NYSE/Nasdaq scope, display of IEX prices to signed-in Birja users, and
retention of simulated fill prices and corporate-action records in the
database and encrypted backups. This is an owner attestation dated
2026-11-25. The underlying agreement, its expiry and terms for distinct
directory, classification and halt-report sources were outside that
confirmation.

The owner separately approved one private Alpaca test for `ORCL`, up to
six read requests and ten minutes with a 20:55 UTC cutoff. The probe used
the saved paper-account credentials and completed at 19:36:28 UTC. Oracle
identifies its common stock as NYSE `ORCL`, which is outside Birja's
original 20. [Oracle investor FAQ](https://investor.oracle.com/faq/default.aspx)
· [NYSE regular session](https://www.nyse.com/trade/hours-calendars)

| Check | Result |
|---|---|
| Paper asset lookup | HTTP 200. Alpaca returned the active, tradable NYSE equity. |
| Two latest USD IEX quotes | Both HTTP 200. Birja's released quote validator accepted the bid and ask shape, session and freshness. Source ages were 0.080 and 0.395 seconds, with an advancing source timestamp. |
| Corporate-action REST | HTTP 200 and a valid response envelope for the one-stock seven-day sample. |
| Requests | Four of the six approved reads. |

The probe kept the provider response bodies in memory. Its receipt records
only status, validation results and quote age. No production order, data
activation or account change occurred. Full directory reconciliation,
approval for each non-Alpaca source, held-only scheduler evidence,
complete action and reported-halt coverage, and the production buy/sell
remain pending.
