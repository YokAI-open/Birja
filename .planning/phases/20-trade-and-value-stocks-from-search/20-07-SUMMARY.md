---
phase: 20-trade-and-value-stocks-from-search
plan: "07"
subsystem: portfolio-history
tags: [catalog, valuation, holdings, history]
requires:
  - phase: 20-06
    provides: Stable catalog orders, marks and retained receipts
provides:
  - Exact owned catalog marks in detail and overview
  - Stable and original-label catalog History
affects: [20-08, 20-09]
requirements-addressed: [SL-02, SL-03, SL-04]
requirements-completed: []
---

# Phase 20 Plan 07 Summary

Portfolio detail and overview share the same owned read. Only positive catalog holdings in the selected roots participate in the bounded query. The second statement rechecks ownership and current listing, session, unit, scope and action evidence. A stale or inconsistent mark leaves quantity and basis visible and preserves known cash and priced values. Incomplete totals omit return and allocation percentages. A holding has its stable catalog ID and its current permitted exchange and market label. A restricted holding uses a generic label.

History reads its catalog identity from original fill and action records. A newly reused symbol cannot change the retained market label or route an old receipt to another issue. Dividend corrections retain the stable ID and reference of the original payment. Split quantity and basis stay attached to the original event. Catalog symbols use the full directory grammar. Legacy events omit the optional catalog key.

## Verification

- Six History cases passed in 30.80 seconds on disposable PostgreSQL and Redis. The new cases covered catalog buy and sell labels after actual ticker reuse, original correction lineage, exact split quantity and basis, optional legacy wire behavior, and owner/portfolio paging. Existing curated mixed-event and payment History checks also passed.
- Six portfolio cases passed in 58.25 seconds. New cases covered a closed mark and incomplete scope, changing price or units during the read, and rename and reuse with private root checks. The two- and ten-root cases verified two statements on the existing path. The existing single-mark case also passed.
- The affected race case passed again in 10.54 seconds after the recheck captured a changed calendar session and action journal origin.
- Ruff, formatting, mypy and diff checks passed for the changed source. All market and action inputs were synthetic.
