---
phase: 07-permitted-stock-discovery
plan: "01"
subsystem: database
tags: [postgresql, sqlalchemy, alembic, stock-catalogue, least-privilege]
requires:
  - phase: 06-deploy
    provides: Existing revision0008 identities, financial invariants and explicit runtime roles
provides:
  - Reviewed revision0009 stock schema with conditional runtime grants and guarded downgrade
  - Separate revision0010 twenty-stock SEC-sourced catalogue without provider eligibility
  - Populated upgrade preservation and exact schema/catalogue PostgreSQL regression tests
affects: [07-02, 07-03, 07-04, 07-05, 07-06, 07-08, 07-10]
tech-stack:
  added: []
  patterns:
    - Preserve physical coins and coin_id identities with an additive asset discriminator
    - Migrator-owned bounded calendar evidence; runtime-derived sessions reference generation
    - Explicit new-object grants with role-absent development support
key-files:
  created:
    - backend/app/models/stock.py
    - backend/alembic/versions/0009_stock_discovery_schema.py
    - backend/alembic/versions/0010_seed_stock_catalog.py
    - backend/tests/test_stock_migrations.py
    - backend/tests/test_stock_catalog.py
  modified:
    - backend/app/models/price.py
    - backend/app/models/__init__.py
    - backend/tests/conftest.py
    - backend/tests/test_migrations.py
    - backend/tests/test_seed_coins.py
key-decisions:
  - Keep calendar review/overrides only in bounded admission JSON; sessions have exactly eight derived columns.
  - Enforce ROUND_HALF_EVEN midpoint normalization at eight decimal places, including exact half-unit cases.
  - Retain approved research display names/exchanges with SEC provenance and NULL provider identity/verification.
patterns-established:
  - New mutable discovery fixtures preserve both seeded catalogues.
  - Stock seed and schema rollback independently refuse financial references.
requirements-completed: []
requirements-supported: [STOCK-01, SAFE-01]
duration: approximately 14min
completed: 2026-11-10
---

# Phase 7 Plan 01: Stock Discovery Storage Summary

**Additive crypto/stock identity storage, read-only calendar authority, constrained quotes and twenty unverified SEC-sourced stock catalogue rows.**

## Performance

- Duration: approximately14minutes, including required context loading and real PostgreSQL setup.
- Phase execution start recorded:2026-11-10T13:50:44Z; implementation checks complete:2026-11-10T14:04:40Z.
- Tasks:2/2. Source/test files changed:10; existing Alembic env.py already imports all registered models and needed no edit.

## Accomplishments

- Revision0009 preserves physical coins IDs and all existing financial FKs, adds default crypto discrimination, permits NULL Kraken mapping only for stocks, and replaces symbol uniqueness with asset-class/symbol uniqueness. Existing-table replacement indexes are created concurrently and attached to constraints.
- Four new tables hold stock identity, latest IEX bid/ask/mid provenance, derived regular sessions, and bounded product-specific evidence. Numeric NaN/nonpositive/crossed/incorrect-mid values and impossible sessions are refused. Money remains NUMERIC(20,8); times are timestamptz.
- Calendar authority is exclusively in migrator-owned stock_data_admissions.calendar: exact semantics and generation-changing administrative updates are implemented by later07-05/08 contracts. stock_sessions has no authority-bearing review/override columns and no FK to mutable generation values.
- Revision0009 revokes PUBLIC and existing app/scheduler privileges on only its new tables/sequences before explicit grants. App receives SELECT only; scheduler receives catalogue/admission SELECT, quote/session SELECT/INSERT/UPDATE and session identity-sequence USAGE. Role-absent upgrade creates no production roles. Actual role-positive verified-TLS denial proof remains07-04.
- Revision0010 inserts the exact researched list with generated IDs: AAPL,MSFT,NVDA,AMZN,GOOGL,META,TSLA,AVGO,AMD,COST,JPM,V,JNJ,PG,KO,XOM,CVX,HD,MCD,DIS. First10 NASDAQ; last10 NYSE. Independent source: https://www.sec.gov/files/company_tickers_exchange.json, checked during research2026-11-10. Provider IDs/verification remain NULL; no quote or permission grant is seeded.
- Both downgrade paths lock financial/reference tables and reject stock holdings or fills before deleting discovery rows. Original15crypto IDs/order and populated cash/start/holding/basis/fill/idempotency values compare exactly across upgrade and safe downgrade.

## Task Commits

1. Task07-01-01 RED: `c7a9aae` — Specify additive stock schema invariants.
2. Task07-01-01 GREEN: `f201d8a` — Add constrained stock discovery storage.
3. Task07-01-02 RED: `cd83c7c` — Specify twenty-stock seed and rollback safeguards.
4. Task07-01-02 GREEN: `623ad2e` — Seed twenty unverified stock identities separately.

Both RED tests failed on missing observable behavior, not import/missing-file failures: existing coins lacked the discriminator, and the stock catalogue returned zero rows instead of twenty.

## Verification

- `cd backend && uv run pytest tests/test_stock_migrations.py tests/test_migrations.py -q`:37passed/3.05s at task1, including ORM-to-migration parity and actual populated0008→0009 preservation.
- Final `cd backend && uv run pytest tests/test_stock_catalog.py tests/test_stock_migrations.py tests/test_seed_coins.py tests/test_migrations.py -q`: **49passed/3.89s** after synthetic discovery fixture cleanup was added.
- Ruff check and format-check on all10modified source/test files:passed.
- `cd backend && uv run mypy app/models/price.py app/models/stock.py`:passed,2source files.
- Actual reviewed Alembic autogeneration ran against isolated birja-test at0008 before manual constraint/grant/downgrade review. Old migrations remain unchanged. Existing env.py registration suffices; no redundant configuration edit.
- No claim of full backend/API/CI, privileged-role/TLS, backup/restore, provider access or live acceptance: those are subsequent plan gates.

## Decisions and Deviations

No architectural or scope deviation. JSON evidence size/type bounds belong to the schema; exact product/calendar semantic validation and the administration procedure remain07-05/08. Missing evidence denies access; schema defaults alone do not establish permission.

During test development, Infinity was correctly refused by PostgreSQL NUMERIC precision before CHECK evaluation(SQLSTATE22003); the test now accepts only that exact overflow or CHECK23514. After adding0010, the schema guard fixture explicitly enters0009 first so it proves0009 independently rather than being intercepted by the seed guard. Neither correction weakens runtime behavior.

The stock midpoint CHECK explicitly follows project ROUND_HALF_EVEN rather than PostgreSQL's default half-away rounding; exact half-unit acceptance tests cover both even outcomes.

## Known Stubs and External Gates

None preventing this storage plan. NULL provider IDs and empty/denied admissions are deliberate unverified states, not fabricated live eligibility. No API/provider/scheduler/UI behavior is implemented by this plan. STOCK-01/SAFE-01 remain unchecked until their full phase-level discovery/recovery/role obligations are verified.

## Resources and Cleanup

Only authorized synthetic birja-test PostgreSQL/Redis containers were started from docker-compose.test.yml. No dev/production service, configuration, volume or provider was accessed. Synthetic test rows are rolled back or explicitly deleted; catalogue tests restore head0010 after guarded migration exercises. The isolated stack is stopped after this plan with tmpfs removed; no retained volume or external upload. No global package, new dependency, production role or key was installed/read.

## Next Plan Readiness

07-02 must apply the planned explicit crypto predicates and narrow nullable Kraken mappings in legacy loaders/trade paths before broad API/scheduler regressions. 07-03 evolves exact recovery contracts for these tables/columns/sequences;07-04 proves actual restricted-role TLS grants without repairing0009. No stock execution, phase completion, push, PR, deployment or external permission follows from these local commits.

## Self-Check: PASSED

All five created source/test artifacts exist; all four task commit hashes appear in current branch history. Final scoped49-test proof, lint/format/type checks and whitespace checks passed. No tracked-file deletion occurred. Isolated containers/network were removed successfully.
