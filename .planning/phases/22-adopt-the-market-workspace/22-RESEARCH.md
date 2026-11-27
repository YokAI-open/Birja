# Phase 22 — Markets workspace research

**Researched:** 2026-11-26
**Baseline:** v0.8.1 integration source at `81a930e`.
**Confidence:** High for verified local implementation and fixture paths.

<user_constraints>

## User Constraints

- **D-01 — Navigation.** Keep the fox asset, Birja wordmark, Markets,
  Portfolios, History and the labelled account door on one row. Use the
  current Inter, warm surfaces, dark action and fox focus treatment.
  Markets has a semantic heading, visually hidden. Use one owned
  portfolio selector where context exists.
- **D-02 — Discovery.** Use the prototype's US stocks first tab, with the
  original 20 stocks on empty search. Stock search reaches the verified
  catalog with one field. Crypto remains its own tab with independent
  filtering, pricing and availability. The catalog retains its bounded,
  stable listing identities, share classes and truthful fallback states.
- **D-03 — Workspace.** Show the selected asset next to the list on desktop
  and in a reachable detail section on mobile. Use one row control per
  asset and preserve list and search access when browsing detail. The
  selected quote uses its existing display rules. Its action preserves the
  active portfolio and the instrument.
- **D-04 — Closed market.** Use the actual server-provided next regular
  opening for a minute countdown. Show the last permitted price when
  present with `Market closed` and `Opens in …`. The trade route may show
  details. Execution readiness still requires the existing live conditions.
- **D-05 — Prototype scope.** Use the prototype for layout and interactions.
  Phase 22 renders current market data with real app states. The chart,
  range controls and past-period/day-change calculations belong to Phase
  23. Portfolio trends belong to Phase 24. The trade, History and sign-in
  page refactor belongs to Phase 25. Demo scenario controls and synthetic
  app state are prototype fixtures.

</user_constraints>

## Existing paths to reuse

- `MarketsPage.tsx` already combines `useStocks`, `usePrices` and
  `useStockCatalogSearch`. Layout, default tab and the location of controls
  change. Keep the 250ms stock-search debounce, IME handling, ready-empty
  state, last valid catalog results on refresh errors and curated fallback
  only when catalog search is unavailable. Empty search continues to read
  the curated universe through `useStocks`. The price search data stays
  separate from curated results even with overlapping ticker names.
- `useSelectedCatalogPrice` keys requests by authenticated scope and exact
  listing ID/version. `catalogDisplay` enforces expiry, identity and
  regular-session marks. Selecting a result starts its existing bounded
  request. Search itself never fetches every result's price. A changed
  listing keeps the explicit reselection/refetch behavior.
- `App.tsx` keeps an `openedId` in the mounted `SignedIn` identity and
  derives an explicit current target through `usePortfolioTarget`. The
  shared `PortfolioSwitcher` currently navigates to a portfolio. Give it
  an opt-in in-place selection behavior for Markets, with a matching
  accessible description. Existing callers keep navigation. Before using
  the scoped route, distinguish a ready target from a pending or revoked
  explicit choice. Legacy chooser links are only for no explicit choice.
  Remounting for a new identity clears selection. A selected listing keeps
  its ID through a portfolio switch and direct navigation.
- The three current route forms are `/trade/:symbol`, `/trade/stocks/:symbol`
  and `/trade/catalog/:catalogId`, optionally under
  `/portfolios/:portfolioId`. Reuse their present authorization boundaries.
  Portfolio switching changes route context only and never sets execution
  authority.
- `MarketOpening.tsx` formats a positive minute duration from
  `next_open_at`. Preserve the server instant as the time element's
  `dateTime`. Use the existing browser-local time formatter for an
  accessible description and existing closed mark metadata. Curated quotes
  refresh through the current stock hook. Catalog uses `catalogDisplay`.
  The countdown expiring prompts the existing refresh path. It cannot
  promote an old quote to executable. The backend already tests the
  regular session, weekend, holiday, early close and DST.
- `AppShell` already loads responsive fox assets and shared nav. Adapt
  its current row spacing if mobile needs it. `markets.css` and existing
  tokens define the selected row, focus and panel. Phase 22 needs current
  prices only. The approved mock chart, Day percentage and scenario chooser
  have no Phase 22 data contracts.

## Validation Architecture

- Quick component suites: `MarketsPage.test.tsx`, `App.test.tsx`,
  `PortfolioSwitcher.test.tsx`, `StockCatalogTradePage.test.tsx` and
  `useStocks.test.tsx`. Cover selection keys, partial state, slow or stale
  responses, explicit portfolio refusal, keyboard access and mark expiry.
- The current initial tab is Crypto. Audit Markets entry in the app and
  e2e tests. Known assumptions occur in `App.test.tsx`,
  `MarketsPage.test.tsx` and browser specs for markets, trade, stock-catalog,
  portfolio-history, portfolio-ownership and portfolio-strategies. Set
  Crypto explicitly in those journeys and keep existing finance assertions.
- `python3 deploy/tests/run-stock-browser.py --suite catalog` runs the
  stock-catalog spec with isolated seeded catalog support.
  `--suite stocks` runs stock-trades. Only `--suite all` covers the
  Markets, crypto trade and History cases in the same owned harness.
  The broad browser pass belongs after the final source change. Test input
  uses synthetic fixtures and console email. Existing date-aware fixture
  windows must apply to ordinary runtime tests. Use Playwright clock or
  component fake timers for explicit calendar scenarios.
