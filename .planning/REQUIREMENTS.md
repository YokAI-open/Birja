# Requirements — Birja v1.4 Searchable Stock Trading

Defined and approved by the owner on 2026-11-24.

## Working simulated stock trading

- [ ] **SX-01** — A user can preview a whole-share stock order during the regular US session using an on-demand eligible IEX ask for buys or bid for sells. Execution requires a current-session quote whose source timestamp is less than 120 seconds old.
- [ ] **SX-02** — A user sees a specific refusal for closed sessions, exchange-reported halts, or stale or failed market checks. Birja checks recent, complete official halt information, including market-wide halts, without a continuous per-symbol status connection.
- [ ] **SX-03** — A confirmed fill updates only the selected portfolio. Repricing requires reconfirmation. A retry recovers the original receipt without a duplicate fill. Shares, cash and History match the receipt and stock commission remains zero.
- [ ] **SX-04** — The pricing and halt-data combination is qualified with representative live symbols, observed freshness, quotas and applicable use for Birja. Demonstrate a real app buy and sell using live prices in a disposable portfolio while preserving the existing crypto flow.

## Search and new stock onboarding

- [ ] **SC-01** — Users can search all active NYSE and Nasdaq common stocks by ticker or company name, with exact ticker matches first and a clear empty state. Coverage and exclusions can be checked against the refreshed exchange directory.
- [ ] **SC-02** — The catalog handles verified ticker aliases and distinct share classes. A listing change or delisting preserves its historical identity and blocks an ambiguous or inactive instrument from new orders.
- [ ] **SC-03** — A user can select a result beyond the original 20, see its company and exchange, request a price and open a trade in the chosen portfolio. If the price is missing or the instrument requires review, the reason is visible.
- [ ] **SC-04** — Search uses local catalog data and bounded results. Selecting a result fetches only the needed price. A failing or rate-limited price source still allows search and keeps the last verified catalog available.

## Held stocks and corporate actions

- [ ] **SL-01** — An eligible stock found through search can be bought and sold. Quote refresh is shared and bounded for actively selected and held stocks, and scales without polling every listed stock.
- [ ] **SL-02** — Markets and the stock ticket show the latest permitted timestamped price when the market is closed, if a mark exists. Show the local-time opening countdown and disable execution until a fresh in-session quote is available.
- [ ] **SL-03** — The expanded eligible universe retains exactly-once ordinary USD dividends and supported forward splits. Unresolved or unsupported events pause affected symbols without disturbing other holdings and portfolios.
- [ ] **SL-04** — Mixed stock and crypto holdings retain the correct cash, basis, quantities and valuations after new-symbol fills, action processing, ticker changes and restarts. An unpriced holding keeps the portfolio aggregate visibly incomplete.

## Release acceptance

- [ ] **SV-01** — Real-browser acceptance covers accessible search, a ticker beyond the original 20, a simulated buy and sell, and matching cash, holdings and History. It also covers market closed, a reported halt, stale data and crypto availability.
- [ ] **SV-02** — Existing portfolios, ledgers and historical identifiers survive the upgrade. The changed paths pass code review, relevant automated tests and applicable restore and rollback verification.
- [ ] **SV-03** — Required CI passes on the release candidate. After the approved rollout, a designated synthetic production portfolio can find a stock beyond the original 20 and complete a buy and sell with live IEX data during a regular session. The rollout receipt records outcomes and enables rollback using the existing runbook.

## Scope boundaries

Active NYSE and Nasdaq common shares are included, including distinct share
classes. ETFs, ADRs, preferred stock, warrants, OTC instruments, international
exchanges, premarket and after-hours trading, and brokerage orders are outside
the approved scope. The plan targets existing free data access and documented
public sources. Paid feeds and provider outreach remain separate decisions.

## Traceability

| Requirement | Phase | Status |
|---|---:|---|
| SX-01 | 18 | Pending |
| SX-02 | 18 | Pending |
| SX-03 | 18 | Pending |
| SX-04 | 18 | Pending |
| SC-01 | 19 | Pending |
| SC-02 | 19 | Pending |
| SC-03 | 19 | Pending |
| SC-04 | 19 | Pending |
| SL-01 | 20 | Pending |
| SL-02 | 20 | Pending |
| SL-03 | 20 | Pending |
| SL-04 | 20 | Pending |
| SV-01 | 21 | Pending |
| SV-02 | 21 | Pending |
| SV-03 | 21 | Pending |

Coverage is 15 requirements assigned exactly once.
