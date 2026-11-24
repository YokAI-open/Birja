---
phase: 20-trade-and-value-stocks-from-search
plan: "08"
subsystem: frontend
tags: [catalog, trade-ticket, markets, portfolio, history]
requires:
  - phase: 20-07
    provides: Exact owned catalog trades, valuation and History responses
provides:
  - Catalog orders and replay in the approved stock ticket
  - Stable catalog links and permitted prices in the existing views
affects: [20-09]
requirements-addressed: [SL-01, SL-02, SL-03, SL-04]
requirements-completed: []
---

# Phase 20 Plan 08 Summary

The catalog ticket uses the approved Birja controls and receipt. Cash appears once. Repricing requires a new review. Temporary closure and holds preserve quantity and clear the expired preview. Original attempts remain tied to their owner, portfolio, catalog identity, listing and retry key. The shared request client opts into typed repricing and stock receipt status only for the catalog confirmation route.

Markets links to the same stable issue from Trade and View details. The closed panel shows the permitted price and countdown and keeps the source time available to assistive technology. Portfolio follows the stable catalog link and retains known values when a mark becomes invalid. Expanded History links use the original catalog ID for trades and action records, including corrections.

## Verification

- 17 catalog ticket tests passed. The selected curated ticket, receipt, decoder and hook suites passed 158 cases.
- 89 Markets, Portfolio, client and valuation cases passed. They covered quote expiry, same-ticker stock/crypto links and retained closed prices. The History decoder and page passed 97 cases, including the stable event link and nested payment identity.
- Frontend typecheck and production build passed. Vite reported a 583.47 kB minified application chunk. ESLint, Prettier and diff checks passed for touched files.
- The real browser and 200% equivalent viewport checks are part of Plan 09. These component tests did not exercise native browser zoom.
