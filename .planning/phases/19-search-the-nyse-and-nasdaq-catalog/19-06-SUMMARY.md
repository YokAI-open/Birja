---
phase: 19-search-the-nyse-and-nasdaq-catalog
plan: "06"
completed: 2026-11-24
requirements-addressed: [SC-01, SC-02, SC-03, SC-04]
requirements-completed: [SC-02, SC-04]
---

# Phase 19 Markets discovery and portfolio ticket

Markets uses one debounced stock search for ticker, verified alias or
company name. The list shows exchange and share class within the existing
layout. The original curated list stays available. Only an explicit result
selection requests a quote. Late responses are fenced by session, identity
and listing version. If the selected listing disappears, opening a same-ticker
curated result requires an explicit click.

The selected listing keeps its stable ID through the portfolio chooser,
portfolio switches and direct navigation. The owned read-only ticket shows
permitted price, available cash and one explanation. A closed market shows the
permitted cached mark and opening countdown. Orders for newly discovered
listings remain part of Phase 20.

- All four catalog Chromium journeys passed on source `fac7a95` with
  real PostgreSQL, Redis and API routes and a deterministic provider
  transport. They covered keyboard operation, name, alias and ticker search,
  selected-only pricing, a retained closed-market mark, portfolio switching,
  ticker reuse and provider failure.
- The focused six-case run also passed the existing curated stock ask/bid
  and BTC buy/sell journeys. The exact catalog-only rerun covered the final
  same-ticker fallback fix. Chromium checked 390px focus return and 640px
  reflow equivalent to 200% zoom. Native browser zoom remains unmeasured.
- The 12 runner contracts and all 1,356 frontend tests passed, along with
  lint and type checks. The prior stock regression sweep passed 216
  execution, session, halt and market-data cases.
- The code review fixes passed all 119 affected backend cases, 29 focused
  frontend tests and four catalog browser journeys on runtime `cc31da5`.
  [Code review](19-REVIEW.md)
- The live exchange inventory and expanded IEX verification remain open.
  [Source decision](19-SOURCE-DECISION.md)
