# Phase 21 live-source qualification

Reviewed public documentation on 2026-11-25. The expanded live acquisition
and activation checks are pending. Phase 7's owner attestation and Phase 18's
measured original-20 run support their recorded scope. [Phase 18 evidence](../18-make-simulated-stock-trades-work/18-SOURCE-DECISION.md) · [Phase 19 source decision](../19-search-the-nyse-and-nasdaq-catalog/19-SOURCE-DECISION.md)

## Evidence needed

| Evidence | Public finding | Disposition |
|---|---|---|
| Exchange directories | Nasdaq Trader documents both files. The Symbol Lookup reuse notice names its Nasdaq Listed data. Applying that notice to the exact file and the NYSE subset of `otherlisted.txt` requires evidence for the relevant fields, derived class/aliases, multi-user display and retained catalog/backups. | Full two-venue live inventory and publication pending. [Lookup notice](https://www.nasdaqtrader.com/Trader.aspx?id=symbollookup) · [Directory definitions](https://www.nasdaqtrader.com/Trader.aspx?id=SymbolDirDefs) |
| Classification | FIGI identifiers are dedicated to the public domain. OpenFIGI separately describes the API's associated metadata as available under the MIT license. SEC issuer filings can corroborate a reviewed class or venue exception. | Verify the exact returned mapping and each primary listing before inclusion. [OpenFIGI FAQ](https://www.openfigi.com/about/faq) · [Bloomberg field explanation](https://www.sec.gov/comments/s7-2024-05/s7202405-533215-1528962.pdf) |
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

## Expanded evidence measured on November 25

The owner authorized completing the rollout, bounded live checks and
production acceptance without additional owner checks. This uses the
already attested Alpaca scope and the published reuse scope for the new
reference data. External agreements or paid products remain outside scope.

- The two active Alpaca equity inventories returned 2,885 NYSE and 5,610
  Nasdaq instruments, with unique symbols and provider IDs. Those results
  include other issue types and serve as a provider mapping input.
- The dated NYSE Pillar file, the current CAT intraday report and the
  current Nasdaq Listed directory reconcile a reference cohort of 1,722
  NYSE and 3,237 Nasdaq common/ordinary issue codes. The Nasdaq directory
  excludes OBTC as an ETF, and the issuer filing confirms it is a Bitcoin
  trust issuing beneficial interests. This leaves 4,958 mapping candidates.
  [Pillar specification](https://www.nyse.com/publicdocs/nyse/data/NYSE_Pillar_Equities_Common_Client_Specification_v2.4o.pdf) · [CAT reference data](https://www.catnmsplan.com/reference-data) · [Nasdaq symbol lookup notice](https://www.nasdaqtrader.com/Trader.aspx?id=symbollookup) · [OBTC issuer filing](https://www.sec.gov/Archives/edgar/data/1767057/000149315226051287/form10-q.htm)
- Confirmed that the Nasdaq Listed reuse notice does not expressly include
  Other Exchange Listed. The revised catalog obtains NYSE display names and
  share-class identities from supported OpenFIGI metadata. The official
  comparators supply primary listing and type checks. Catalog publication
  requires exact identity reconciliation and current field permissions.
- At 20:15 UTC four further bounded reads succeeded. Alpaca REST returned
  the ORCL action range and matched a separate known ID. Headers showed a
  limit of 200. The all-US historical corporate-action SSE returned HTTP
  200 with normal EOF and a limit of 20 for a 30-second interval containing
  no frames. The Nasdaq halt report was 5.833 seconds old and had no ORCL
  or market-wide halt. Raw responses and credentials were excluded from
  the receipt. [Alpaca actions](https://docs.alpaca.markets/us/reference/corporateactions-1) · [Alpaca replay](https://docs.alpaca.markets/us/reference/subscribetocorporateactionseventssse) · [Nasdaq halt RSS](https://www.nasdaqtrader.com/Trader.aspx?id=TradeHaltRSS)

The OpenFIGI pass completed all 4,958 jobs in 496 batches. A further
bounded 69-job comparison resolved 20 NYSE class suffixes using exact
Pillar/CQS and OpenFIGI aliases. It resolved seven Nasdaq tier differences
by requiring an exact alternate Nasdaq match and the same composite
share-class identity. The issuer's current SEC filing confirmed EMP is
a mortgage bond. Specific supported fund, partnership, royalty trust and
unit classifications account for the other exclusions. [NYSE symbology](https://www.nyse.com/publicdocs/nyse/data/NYSE_Symbology_Spec.pdf) · [EMP issuer filing](https://www.sec.gov/Archives/edgar/data/71508/000006598426000325/R1.htm)

| Venue | Included | Excluded | Unresolved |
| --- | ---: | ---: | ---: |
| NYSE | 1,682 | 1,196 | 0 |
| Nasdaq | 3,216 | 2,393 | 0 |

The complete private manifest binds the November 25 authoritative
rosters and reference evidence. All 4,898 included symbols matched
Alpaca's exact current primary symbol and venue. Alpaca returned
`tradable=false` for 25 of the included Nasdaq stocks. Keep them searchable
and preserve their execution-state distinction. Provider availability,
market hours and the latest stock-specific evidence still control orders.

The restricted test migrator published all 4,898 listings in an
isolated PostgreSQL database in 2.301 seconds. Replaying the exact
manifest preserved the generation and digest. Under the restricted
application role, ten queries each for `ORCL` and `Oracle` returned the
same listing. `BRK/B` returned `BRK.B` on NYSE. Median times for the
three queries were 62–66 milliseconds.

The matching Alpaca inventories also passed full-size enrollment on a
disposable `0027` database. All 49 reviewed batches visited 4,898 rows
and created 4,853 expanded financial bindings in 339 seconds. The other
45 were the original 20 handled by the curated path and 25 marked
nontradable by Alpaca. Every promoted listing had one current grant for
each of provider identity, execution, mark, reported halts and actions.
The ORCL binding retained the actual inventory capture timestamp. No
production records were changed by these tests.

The catalog financial quote scheduler accepted two real IEX quotes for
NYSE ORCL. With an explicit selection at 20:28 UTC, the restricted
scheduler persisted a source observation aged 0.082 seconds and returned
the selection result as ready. The next cycle used only a synthetic held
position. Its source observation aged 0.288 seconds advanced by 61.194
seconds. Both requests returned HTTP 200, and Redis counted one attempt
in each rolling window. The authenticated requests used the existing
paper account. PostgreSQL, Redis, listing authority and portfolio were
isolated fixtures. Production acceptance and rollout remain open.
