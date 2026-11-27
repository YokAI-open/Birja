# Phase 22: Adopt the market workspace

The owner approved the six-page prototype and requested this phase by
number on 2026-11-26. The decisions below record that reference and the
Phase 22 roadmap. Routine integration details remain with the executor.

## Phase Boundary

Deliver the Markets workspace and the shared navigation needed by it.
Users can browse the original 20 US stocks, search the full supported
catalog, browse crypto independently, see the selected asset and open the
correct portfolio trade route. Preserve the last permitted stock mark and
the actual session countdown. Requirements WS-01 through WS-04 define
acceptance.

## Implementation Decisions

<decisions>

- **D-01:** Navigation. Keep the fox asset, Birja wordmark, Markets,
  Portfolios, History and the labelled account door on one row. Use the
  current Inter, warm surfaces, dark action and fox focus treatment.
  Markets has a semantic heading, visually hidden. Use one owned
  portfolio selector where context exists.
- **D-02:** Discovery. Use the prototype's US stocks first tab, with the
  original 20 stocks on empty search. Stock search reaches the verified
  catalog with one field. Crypto remains its own tab with independent
  filtering, pricing and availability. The catalog retains its bounded,
  stable listing identities, share classes and truthful fallback states.
- **D-03:** Workspace. Show the selected asset next to the list on desktop
  and in a reachable detail section on mobile. Use one row control per
  asset and preserve list and search access when browsing detail. The
  selected quote uses its existing display rules. Its action preserves the
  active portfolio and the instrument.
- **D-04:** Closed market. Use the actual server-provided next regular
  opening for a minute countdown. Show the last permitted price when
  present with `Market closed` and `Opens in …`. The trade route may show
  details. Execution readiness still requires the existing live conditions.
- **D-05:** Prototype scope. Use the prototype for layout and interactions.
  Phase 22 renders current market data with real app states. The chart,
  range controls and past-period/day-change calculations belong to Phase
  23. Portfolio trends belong to Phase 24. The trade, History and sign-in
  page refactor belongs to Phase 25. Demo scenario controls and synthetic
  app state are prototype fixtures.

</decisions>

## Canonical References

- `.planning/ui-reviews/v1.5/README.md` and its pinned `PROTOTYPE.zip`
- `.planning/REQUIREMENTS.md` and `.planning/ROADMAP.md` for Phase 22
- `design-system/birja/MASTER.md` and `design-system/birja/pages/markets.md`
- `frontend/src/pages/MarketsPage.tsx`, `frontend/src/hooks/useStockCatalog.ts`,
  `frontend/src/components/MarketOpening.tsx` and the routes in `frontend/src/App.tsx`
- `.planning/phases/19-search-the-nyse-and-nasdaq-catalog/19-VERIFICATION.md`
- `.planning/phases/20-trade-and-value-stocks-from-search/20-VERIFICATION.md`

## Implementation Discretion

Use the existing responsive primitives, TanStack Query and portfolio
boundary. The exact browser focus handoff, list sizing and route wiring
follow the phase UI contract and research.
