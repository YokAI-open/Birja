---
phase: 19-search-the-nyse-and-nasdaq-catalog
plan: "04"
completed: 2026-11-24
requirements-addressed: [SC-01, SC-02, SC-04]
requirements-completed: []
---

# Phase 19 local catalog search and details

Authenticated `GET /api/v1/stock-catalog/search?q=` searches the current
admitted generation, returning up to 20 entries and `has_more`. Exact ticker
ranks ahead of exact verified alias, followed by ticker or alias prefix,
company prefix and company substring. Ranking and tie breaks run in
PostgreSQL with literal input and a 21-row lookahead. The response carries
`state`, `generation_id` and `published_at`, distinguishing an empty match
set from a catalog that cannot be used.

`GET /api/v1/stock-catalog/{catalog_id}` resolves the current admitted
listing for the original stable ID, including retirement and review. Both
routes return canonical string IDs and listing versions, with private
no-store responses and zero provider traffic or price-cache dependency.
Effective field permissions suppress expired or revoked display. The
existing curated stock route remains independent.

- All 61 focused search, catalog API and curated API tests passed with real
  PostgreSQL. Ruff and strict mypy passed on the changed source.
- A focused run passed 38 portfolio closure cases. The retained 0023 SQL
  fixtures stay historical, and the associated HTTP fixtures now upgrade
  to the exact current head and install its grants before app startup.
  The 13 affected lifecycle, split, dividend and schema authority reruns
  passed. Broader release validation remains Phase 21 evidence.
- The live exchange inventory and expanded provider rights remain open as
  recorded in the [source decision](19-SOURCE-DECISION.md).
