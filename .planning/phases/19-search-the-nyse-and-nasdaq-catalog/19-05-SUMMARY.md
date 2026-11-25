---
phase: 19-search-the-nyse-and-nasdaq-catalog
plan: "05"
completed: 2026-11-24
requirements-addressed: [SC-02, SC-03, SC-04]
requirements-completed: []
---

# Phase 19 selected quotes and owned trade entry

`POST /api/v2/stock-catalog/{catalog_id}/quote` requires authentication,
CSRF and an exact string `listing_version`. It rechecks source rights,
active identity, mapping, USD share-unit evidence and market hours before
queuing and after the bounded wait. The reply carries the checked listing,
session and next opening, a price or a precise reason. Display prices use
decimal strings and include IEX source time and the earliest display cutoff.

`GET /api/v2/portfolios/{portfolio_id}/stock-catalog/{catalog_id}/trade-context`
checks an active portfolio owned by the caller. It reads permitted cached
prices and returns `read_only: true`. New catalog entries carry separate
identities and cannot enter the curated execution path.

Redis holds selected demand and prices. Pending work is capped at 64 per
account, lasts at most ten seconds and waits at most seven seconds on the
API. The scheduler handles up to eight matching selections within the
admitted request cap, shares the provider account window and rechecks
current authority before each attempt and cache write. A price is fresh for
less than 120 seconds in session. A closed market can display a cached mark
for up to ten minutes within effective permissions.

- The final quote-core run passed 55 PostgreSQL and Redis cases. The stock
  worker, scheduler and provider suite passed 110 cases with mocked HTTP.
- The API and curated portfolio-stock suite passed 32 cases, including
  authentication, CSRF, expiry, wrong portfolio, retired or rebound listing,
  no expanded orders, market reopening and Redis loss. A final integrated
  rerun passed all 21 selected worker and API cases after the cutoff changes.
- Existing curated quote parsing, budget and scheduler behavior passed
  focused regressions. Ruff and strict mypy passed on the changed source.
- Expanded IEX display and mapping were tested with synthetic authority.
  Live source qualification remains open in the [source decision](19-SOURCE-DECISION.md).
