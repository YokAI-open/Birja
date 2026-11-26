# Requirements — Birja v1.5 Market Charts and Workspace Redesign

Scope follows the [approved prototype](ui-reviews/v1.5/README.md).

## Markets workspace

- [x] **WS-01** — Navigation retains the existing Birja branding, one row of Markets, Portfolios and History, the door control and a single portfolio selector where needed. Users can reach the primary controls with a keyboard and on narrow screens.
- [x] **WS-02** — An empty US stocks search lists the original 20 stocks. Searching by ticker or name still reaches the supported NYSE and Nasdaq catalog. Crypto remains independently browsable.
- [x] **WS-03** — Selecting a row updates its price, market state, and trade entry beside the list on desktop and in a reachable detail section on mobile. The order opens for the selected portfolio and actual instrument.
- [x] **WS-04** — A closed stock keeps its last verified display price if one exists. It shows `Market closed` and a countdown to the actual next regular session, while the existing order rules prevent execution.

## Market charts

The completed checks in this section verify local behavior. Live price
history depends on CHART-04.

- [x] **CHART-01** — Users can view actual historical stock and crypto prices for the selected instrument in `1D`, `1W`, and `1M` ranges. `1W` opens by default, and the series identifies its source and time basis.
- [x] **CHART-02** — The chart and equivalent text communicate dates, prices and a comparable period change. Daily and period change figures appear only when sufficient comparable data exist. Equity sessions, gaps, asset identity and split treatment do not produce fictitious prices or returns.
- [x] **CHART-03** — When history is sparse, delayed or unreachable, chart states describe the available coverage. The current quote, search, and eligible trading still work independently.
- [ ] **CHART-04** — Requests for historical data stay within measured free-tier budgets, respect applicable source scope, and are bounded and shared across common reads. Candidate sources are qualified on representative crypto, featured stock and out-of-list symbols.

## Portfolio trends and workspace

- [ ] **TREND-01** — Fully clickable strategy cards show the name, optional description, cash, total and return under the existing valuation rules. The final `New portfolio` card opens creation and the supported zero-portfolio and limit states still work.
- [ ] **TREND-02** — Each active portfolio can display a sparkline and an accessible summary of its own recorded daily value. Missing valuations produce visible gaps and portfolios without enough observations show their current figures.
- [ ] **TREND-03** — Durable snapshots use exact existing valuation and the original starting cash, remain private, survive restart and restore, and do not duplicate a capture or collect new points after confirmed closure.
- [ ] **TREND-04** — A selected portfolio groups the switcher, Edit, Update with age, and Remove above current value, profit and cash/stock/crypto allocation. Users can filter and sort holdings and open their trade tickets.

## Trade, History, sign-in and acceptance

- [ ] **FLOW-01** — The stock and crypto tickets retain cash, holdings, current execution context, preview and receipt in the approved layout. Existing stock quantity and crypto dollar/quantity inputs, fees, repricing and exact receipt recovery continue to work without duplicating the portfolio name.
- [ ] **FLOW-02** — In the selected portfolio, users can filter History by activity and asset type, expand an event, and page through results with stable ordering. Existing financial event types and correction details remain accessible.
- [ ] **FLOW-03** — Users can request and enter a real email OTP and sign out via the door control, with accessible loading, validation and failure handling.
- [ ] **FLOW-04** — Code review and required CI cover the integrated screens, real API chart contracts, representative synthetic full-stack trading and portfolio flows, and snapshot migration and recovery. The integrated app matches the approved prototype at desktop and mobile widths.

## Scope boundaries

Chart data is display-only. Existing source eligibility, quote freshness, trade
rules, portfolio ownership, grants and ledger behavior remain authoritative.
Daily portfolio history starts when capture is enabled. Historical reconstruction
before rollout, paid data, brokerage integration, new asset classes and new
order types are outside this milestone.

## Traceability

| Requirement | Phase | Status |
|---|---:|---|
| WS-01 | 22 | Complete |
| WS-02 | 22 | Complete |
| WS-03 | 22 | Complete |
| WS-04 | 22 | Complete |
| CHART-01 | 23 | Verified locally |
| CHART-02 | 23 | Verified locally |
| CHART-03 | 23 | Verified locally |
| CHART-04 | 23 | Live qualification pending |
| TREND-01 | 24 | Pending |
| TREND-02 | 24 | Pending |
| TREND-03 | 24 | Pending |
| TREND-04 | 24 | Pending |
| FLOW-01 | 25 | Pending |
| FLOW-02 | 25 | Pending |
| FLOW-03 | 25 | Pending |
| FLOW-04 | 25 | Pending |
