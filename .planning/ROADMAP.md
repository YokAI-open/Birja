# Roadmap — Birja

## Milestones

- [x] **v1.0 Birja MVP** · [Roadmap](milestones/v1.0-ROADMAP.md)
- [x] **v1.1 US Stock Trading** · Closed with accepted live gaps. [Roadmap](milestones/v1.1-ROADMAP.md)
- [x] **v1.2 Multiple Strategy Portfolios** · [Roadmap](milestones/v1.2-ROADMAP.md)
- [x] **v1.3 Birja Interface Redesign** · Phases 16–17 verified and interface deployed. [Roadmap snapshot](milestones/v1.3-ROADMAP.md) · [Audit](v1.3-MILESTONE-AUDIT.md)
- [ ] **v1.4 Searchable Stock Trading** · Scope and roadmap approved on 2026-11-24.

## Phases

- [ ] **Phase 18: Make simulated stock trades work**
- [ ] **Phase 19: Search the NYSE and Nasdaq catalog**
- [ ] **Phase 20: Trade and value stocks from search**
- [ ] **Phase 21: Verify, release and activate stock trading**

## Phase Details

### Phase 18: Make simulated stock trades work

**Goal:** Complete a real app buy and sell with live market data and the approved simulator eligibility rule.

**Requirements:** SX-01, SX-02, SX-03, SX-04

**Plans:** 5 plans

**Wave 1**
- [x] 18-01 — Qualify IEX and official halt sources.

**Wave 2** (after Wave 1)
- [x] 18-02 — Add reported-halt evidence and the final transactional check.

**Wave 3** (after Wave 2)
- [x] 18-03 — Fetch eligible quotes on demand through the scheduler.

**Wave 4** (after Wave 3)
- [x] 18-04 — Connect the existing trade flow and verify regressions.

**Wave 5** (after Wave 4)
- [ ] 18-05 — Prove recovery and a live isolated stock buy and sell.

Stock execution uses current evidence from the qualified halt and IEX sources.
The simulator runs in a disposable stack for Phase 18 verification.

**Success Criteria**:

1. The approved pricing and halt-data combination supplies usable real data within a measured free-tier request budget and blocks reported individual and market-wide halts and discloses the report coverage limits.
2. An isolated portfolio buys at the eligible IEX ask and sells at the eligible bid. Session closure, stale or unavailable data, and reported halts cause a clear refusal.
3. Repricing requests a fresh confirmation and retry leaves one fill. The selected portfolio and History agree, while crypto continues to work.

### Phase 19: Search the NYSE and Nasdaq catalog

**Goal:** Find and select supported common stocks by name or ticker, including stocks beyond the original 20.

**Depends on:** Phase 18

**Requirements:** SC-01, SC-02, SC-03, SC-04

1. Users can search the loaded catalog with bounded results, see exact ticker matches first and distinguish share classes. A symbol beyond the original 20 opens its own detail and trade entry.
2. A catalog refresh preserves stable identities and historical links. Stale or failed price access leaves name and ticker search available.
3. Selecting a result requests market data on demand and shows the actual quote or a precise eligibility reason.

### Phase 20: Trade and value stocks from search

**Goal:** Extend the working trade and valuation path to eligible catalog results, with bounded price and corporate-action work.

**Depends on:** Phase 19

**Requirements:** SL-01, SL-02, SL-03, SL-04

1. Users can buy and sell a newly onboarded common stock and see its correct position and cash in a mixed portfolio. Refresh calls scale with selected and held stocks.
2. Closed stocks show their latest permitted marks and local opening countdown. Missing marks leave the relevant aggregate visibly incomplete.
3. An ordinary dividend and a supported split apply once to affected active portfolios. Ticker changes, restart and uncertain actions preserve identity, balances and History.

### Phase 21: Verify, release and activate stock trading

**Goal:** Deliver a verified production flow for search, buy and sell.

**Depends on:** Phase 20

**Requirements:** SV-01, SV-02, SV-03

1. Browser acceptance covers an out-of-list stock search, simulated round trip, cash, holdings and History, along with market closure, known halts and stale data.
2. Review, required CI and applicable migration, recovery and rollback checks pass for the release candidate.
3. After the approved rollout, the designated production test portfolio buys and sells an out-of-list stock against real IEX prices. Record safe totals and exact release identity.

## Progress

| Phase | Plans complete | Status |
|---|---|---|
| 18. Make simulated stock trades work | 4/5 | In progress |
| 19. Search the NYSE and Nasdaq catalog | 0/TBD | Not started |
| 20. Trade and value stocks from search | 0/TBD | Not started |
| 21. Verify, release and activate stock trading | 0/TBD | Not started |

All 15 requirements map once in [REQUIREMENTS.md](REQUIREMENTS.md).
[Research](research/v1.4/SUMMARY.md) · [Deferred work](DEFERRED.md)
