# Phase 23 — Show historical market prices

The user approved the v1.5 browser ZIP and called out the visual differences
in the Phase 22 captures. They requested Phase 23 planning after agreeing to
include the remaining Markets refinements with the chart work.

<decisions>

- **D-01:** Show real line charts for the selected cryptocurrency, original
  stock or catalog listing. Offer 1D, 1W and 1M, with 1W selected on entry.
  Include one concise source/time basis label and equivalent readable values.
- **D-02:** Treat history as display data. Distinguish missing bars, closed
  sessions, delayed or unavailable history and split-adjusted prices. Compute
  daily/period change only from comparable observations. Keep current quotes,
  closure, countdown, search and authorized trading independent.
- **D-03:** Qualify Alpaca IEX equity bars and Kraken USD OHLC as the initial
  free-source candidates. Reuse existing identities and scheduler. Limit
  requests, cache time and history storage to evidence for the actual source.
  Keep exact source coverage and permission as a separate execution outcome.
- **D-04:** Use the approved ZIP as the Markets visual target. Restore the
  compact ticker tiles, list/quote spacing, chart framing, period buttons and
  right-aligned trade action. Keep the normal one-row header, existing focus
  and reflow, single portfolio chooser, and necessary provider attribution.
- **D-05:** Compare actual-app and ZIP renders side by side on desktop and
  mobile. Include open stock, closed stock, catalog and crypto and record
  permitted differences caused by real data states. Preserve Phase 22 tests.

</decisions>

## Scope

CHART-01 through CHART-04 and the outstanding Markets fidelity. Portfolio
sparklines and portfolio value history belong to Phase 24. Other page
layouts, launch and release CI remain in their respective phases.

## References

- [Approved ZIP](../../ui-reviews/v1.5/README.md)
- [Phase 22 verification](../22-adopt-the-market-workspace/22-VERIFICATION.md)
- [Requirements](../../REQUIREMENTS.md)
- [Roadmap](../../ROADMAP.md)
- [Design system](../../../design-system/birja/MASTER.md)
