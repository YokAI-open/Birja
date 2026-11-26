# Roadmap — Birja

## Milestones

- [x] **v1.0 Birja MVP** · [Roadmap](milestones/v1.0-ROADMAP.md)
- [x] **v1.1 US Stock Trading** · Closed with accepted live gaps. [Roadmap](milestones/v1.1-ROADMAP.md)
- [x] **v1.2 Multiple Strategy Portfolios** · [Roadmap](milestones/v1.2-ROADMAP.md)
- [x] **v1.3 Birja Interface Redesign** · [Roadmap](milestones/v1.3-ROADMAP.md) · [Audit](v1.3-MILESTONE-AUDIT.md)
- [ ] **v1.4 Searchable Stock Trading** · Previous milestone. [Closeout handoff](milestones/v1.4-OPEN-HANDOFF.md)
- [ ] **v1.5 Market Charts and Workspace Redesign** · Phases 22 and 24 are complete. [Approved prototype](ui-reviews/v1.5/README.md)

## Phases

- [x] **Phase 22: Adopt the market workspace** (completed 2026-11-26)
- [ ] **Phase 23: Show historical market prices**
- [x] **Phase 24: Compare portfolio performance** (completed 2026-11-26)
- [ ] **Phase 25: Finish the trading flows and verify the integrated app**

### Phase 22: Adopt the market workspace

**Goal:** Browse and select stocks or crypto in the approved layout using the working market and trade APIs.

**Requirements:** WS-01, WS-02, WS-03, WS-04

**Success Criteria** (what must be TRUE):

1. The logo, navigation and account door fit on one row at desktop and phone sizes. Keyboard navigation reaches market tabs, search, portfolio selection and the selected asset.
2. The default stock list shows the original 20. Searching a name or symbol beyond the 20 uses the full catalog. Selecting a stock or crypto opens the correct detail and order context.
3. Stocks retain verified closing prices and show the next-session countdown during ordinary closures and early-close or holiday cases. Crypto remains available while stock orders remain gated by existing checks.

**Plans:** 3/3 plans complete

- [x] 22-01 — Adopt the header and Markets discovery layout.
- [x] 22-02 — Bind portfolio selection, quote detail and the reopening countdown.
- [x] 22-03 — Verify the real app in the isolated browser stack.

[UI contract](phases/22-adopt-the-market-workspace/22-UI-SPEC.md) · [Validation strategy](phases/22-adopt-the-market-workspace/22-VALIDATION.md) · [Verification](phases/22-adopt-the-market-workspace/22-VERIFICATION.md)

### Phase 23: Show historical market prices

**Goal:** Give the selected stock or coin a trustworthy price chart.

**Depends on:** Phase 22

**Requirements:** CHART-01, CHART-02, CHART-03, CHART-04

**Success Criteria** (what must be TRUE):

1. A user can switch among `1D`, `1W` and `1M` price series for a coin, a featured stock and an out-of-list stock. The chart and text alternative report the same points, period and source.
2. Closed sessions and missing points stay distinguishable from observed prices. Partial history or provider failure leaves current prices, search and eligible order entry usable.
3. Historical requests use qualified coverage and a measured, bounded free-tier fetch/cache policy. Market orders still use the existing current-quote path.
4. The running app matches the approved Markets reference on ticker tiles, spacing, chart controls and action placement across four matched desktop and mobile captures. Real-data and attribution differences are recorded.

**Plans:** 4/4 plans executed and verified locally

- [x] 23-01 — Qualify source candidates and define actual time-series data contracts.
- [x] 23-02 — Serve selected histories through bounded API and scheduler work.
- [x] 23-03 — Render charts and match the approved Markets layout.
- [x] 23-04 — Verify independent trading behavior and compare actual-app and ZIP captures.

Live Kraken and IEX history qualification remains open under CHART-04.

[Research](phases/23-show-historical-market-prices/23-RESEARCH.md) · [UI contract](phases/23-show-historical-market-prices/23-UI-SPEC.md) · [Verification](phases/23-show-historical-market-prices/23-VERIFICATION.md)

### Phase 24: Compare portfolio performance

**Goal:** Show each strategy's current allocation and actual value trend without changing its accounting.

**Depends on:** Phase 22

**Requirements:** TREND-01, TREND-02, TREND-03, TREND-04

**Success Criteria** (what must be TRUE):

1. Portfolio cards open the chosen strategy and show the correct current figures and its own sparkline when available. Creating, editing, switching and removing portfolios preserves the existing funding and closure behavior.
2. The portfolio page puts the selector and actions above value and allocation, followed by sortable, filterable holdings. Incomplete valuations stay explicit.
3. Daily snapshots agree with authoritative values, preserve missing data, never cross portfolio boundaries, and survive restart and encrypted restore. Capture retries and closures preserve the same historical record.

**Plans:** 8/8 plans complete across 6 waves

**Wave 1**

- [x] 24-01 — [Add the daily value schema and narrow capture authority](phases/24-compare-portfolio-performance/24-01-PLAN.md).
- [x] 24-02 — [Build the selected portfolio toolbar, allocation and holdings](phases/24-compare-portfolio-performance/24-02-PLAN.md).

**Wave 2**

- [x] 24-03 — [Verify fresh and upgraded 0028 database paths](phases/24-compare-portfolio-performance/24-03-PLAN.md).

**Wave 3**

- [x] 24-04 — [Capture daily valuations and serve private 30-day trends](phases/24-compare-portfolio-performance/24-04-PLAN.md).

**Wave 4**

- [x] 24-05 — [Build portfolio overview cards and sparklines](phases/24-compare-portfolio-performance/24-05-PLAN.md).
- [x] 24-06 — [Extend encrypted backup and restore to daily values](phases/24-compare-portfolio-performance/24-06-PLAN.md).

**Wave 5**

- [x] 24-07 — [Wire predecessor compatibility and successor recovery into CI](phases/24-compare-portfolio-performance/24-07-PLAN.md).

**Wave 6**

- [x] 24-08 — [Verify the running views, finance behavior and encrypted recovery](phases/24-compare-portfolio-performance/24-08-PLAN.md).

[Research](phases/24-compare-portfolio-performance/24-RESEARCH.md) · [UI contract](phases/24-compare-portfolio-performance/24-UI-SPEC.md) · [Validation](phases/24-compare-portfolio-performance/24-VALIDATION.md) · [Verification](phases/24-compare-portfolio-performance/24-VERIFICATION.md)

### Phase 25: Finish the trading flows and verify the integrated app

**Goal:** Bring the approved trade, History and sign-in layouts into the live application code and qualify the release candidate.

**Depends on:** Phases 22, 23 and 24

**Requirements:** FLOW-01, FLOW-02, FLOW-03, FLOW-04

**Success Criteria** (what must be TRUE):

1. The stock and crypto tickets show cash and the actual preview. Repricing and uncertain submission recover correctly, and the trade receipt reconciles against the chosen portfolio and History.
2. Users can filter, expand and page through History and go through the real email-code and sign-out flows.
3. Real-browser checks cover desktop and mobile reflow, chart states and the main financial journeys against an isolated stack. Review, release CI and applicable snapshot recovery gates pass on the candidate.

**Plans:** 7 plans across 4 waves

**Wave 1**

- [x] 25-02 — [Filter private mixed History before pagination](phases/25-finish-the-trading-flows-and-verify-the-integrated-app/25-02-PLAN.md).
- [x] 25-03 — [Adopt the sign-in layout and verify the email-code flow](phases/25-finish-the-trading-flows-and-verify-the-integrated-app/25-03-PLAN.md).
- [x] 25-06 — [Adjust CI recovery timing within the UTC fixture window](phases/25-finish-the-trading-flows-and-verify-the-integrated-app/25-06-PLAN.md).

**Wave 2** · Depends on 25-02 and 25-03

- [x] 25-01 — [Adopt the crypto, curated-stock and catalog trade layouts](phases/25-finish-the-trading-flows-and-verify-the-integrated-app/25-01-PLAN.md).
- [x] 25-04 — [Connect the History toolbar, disclosures and paging](phases/25-finish-the-trading-flows-and-verify-the-integrated-app/25-04-PLAN.md).

**Wave 3** · Depends on 25-01 and 25-04

- [ ] 25-05 — [Verify real app flows and compare with the approved prototype](phases/25-finish-the-trading-flows-and-verify-the-integrated-app/25-05-PLAN.md).

**Wave 4** · Depends on 25-05 and 25-06

- [ ] 25-07 — [Review the local candidate and qualify it in authorized hosted CI](phases/25-finish-the-trading-flows-and-verify-the-integrated-app/25-07-PLAN.md).

[Research](phases/25-finish-the-trading-flows-and-verify-the-integrated-app/25-RESEARCH.md) · [UI contract](phases/25-finish-the-trading-flows-and-verify-the-integrated-app/25-UI-SPEC.md) · [Validation](phases/25-finish-the-trading-flows-and-verify-the-integrated-app/25-VALIDATION.md)

## Progress

| Phase | Plans complete | Status |
|---|---|---|
| 22. Adopt the market workspace | 3/3 | Complete 2026-11-26 |
| 23. Show historical market prices | 4/4 | Local checks passed. Live qualification pending. |
| 24. Compare portfolio performance | 8/8 | Complete 2026-11-26 |
| 25. Finish the trading flows and verify the integrated app | 5/7 | Executing wave 3 |

All 16 requirements map once in [REQUIREMENTS.md](REQUIREMENTS.md).
[Research](research/v1.5/SUMMARY.md) · [Design reference](ui-reviews/v1.5/README.md)
