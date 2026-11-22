---
phase: 12-preserve-existing-investing-under-portfolio-ownership
plan: "15"
subsystem: api
tags: [portfolio, authorization, identity, history, compatibility, production-composition]
requires:
  - phase: 12-08
    provides: explicit owned-active resolver and metadata-only discovery
  - phase: 12-09
    provides: identity-only versioned auth and pre-consumption legacy refusal
  - phase: 12-10
    provides: owned crypto services and actual scoped routers
  - phase: 12-11
    provides: owned stock execution, receipt replay and actual scoped routers
  - phase: 12-14
    provides: root-bound valuation and trade2/mixed3 History consumers
provides:
  - Actual production create_app composition for all scoped identity and financial routes
  - Private active metadata discovery, actual-baseline statements and both History adapters
  - Central authenticated legacy409 refusal before financial services or receipt lookup
  - Preserved retained API/security/economic assertions using explicit target URLs
affects: [12-17, 12-19, 12-20, 12-23, 12-26, 12-27]
tech-stack:
  added: []
  patterns: [explicit root HTTP adapters, central legacy refusal, production router inventory]
key-files:
  created:
    - backend/app/api/v2/portfolios.py
    - backend/app/api/v2/history.py
    - backend/app/api/v1/legacy_finance.py
    - backend/tests/test_portfolio_routes.py
  modified:
    - backend/app/api/v2/router.py
    - backend/app/api/v1/router.py
    - backend/app/api/v1/trades.py
    - backend/app/api/v1/stock_trades.py
    - backend/app/api/v1/portfolio.py
    - backend/app/api/v1/history.py
    - backend/app/api/v1/event_history.py
    - backend/app/main.py
    - backend/tests/conftest.py
    - backend/tests/helpers.py
    - backend/tests/test_portfolio_identity_api.py
    - backend/tests/test_portfolio_crypto_api.py
    - backend/tests/test_portfolio_stock_api.py
    - backend/tests/test_ratelimit.py
    - backend/tests/test_trades_api.py
    - backend/tests/test_stock_trades_api.py
    - backend/tests/test_portfolio_api.py
    - backend/tests/test_history_api.py
    - backend/tests/test_history_service.py
    - backend/tests/stock_action_fixtures.py
    - backend/tests/test_accounts.py
key-decisions:
  - Mount actual routers in create_app and remove all temporary test-only v2 registrations
  - Retire implicit finance with one authenticated/CSRF-protected adapter, never a fallback root
  - Keep shared stock PrivateRoute/domain error helpers but remove obsolete financial handlers
  - Select a single initial root explicitly in retained test call sites; multi-root tests retain captured IDs
requirements-completed: []
requirements-addressed: [PSAFE-02, PVIEW-03, PFIN-02, PCTX-01]
duration: 20 min
completed: 2026-11-16
---

# Phase 12 Plan 15: Metadata Discovery and Final Scoped Route Wiring

**Production composition now exposes only explicitly owned portfolio finance, while legacy requests refuse before account selection, execution or receipt disclosure.**

## Accomplishments

- GET /api/v2/portfolios returns only active owned string IDs and names in
  stable ID order, including an empty array without recreating or funding a
  portfolio. No creation, rename, description, deletion or pooled totals exist.
- Scoped statement, /history and /event-history adapters pass the verified
  OwnedActivePortfolio to existing consumers. Exact stored baseline and money
  strings, bounded limits, trade2/mixed3 cursors, private unavailable responses,
  embedded originals and no-store/Vary headers are preserved.
- create_app mounts the actual v2 router containing identity, metadata,
  crypto, stock and financial reads. Conftest, dedicated identity/crypto/stock
  tests and the custom rate-limit app no longer register test-only routers.
  Earlier API suites now measure production registration rather than masking it.
- A central nine-operation legacy adapter preserves authentication and POST
  CSRF, returning exactly409 portfolio_required before any financial service.
  It covers old crypto quote/fill/holding, stock quote/fill/context, portfolio,
  trade History and mixed History. Slash redirects reach the same refusal;
  unsupported methods do not expose another handler. Old cash-bearing identity
  remains409 api_version_required before OTP consumption, and v1 market,
  health and auth lifecycle endpoints remain registered.
- Obsolete v1 financial implementations are removed. The old read/crypto
  modules re-export only the refusal router; stock's retained private response
  and error helpers no longer contain unscoped business handlers. Complete
  app typing now passes, closing the followed-import failures from11/14.
- Actual route inventory is exact: twelve v2 operations, no management or
  unscoped v2 financial fallback. No-effect legacy tests monkeypatch financial
  services to fail if called, compare account rows and reject guessed body
  targets. Real correction HTTP proves that an off-page original belongs to
  its root, sibling cursor reuse fails and a foreign root remains unavailable.

## Task Commits

| Task | Commit | Outcome |
|---|---|---|
|12-15-01|aaf5c8e|Metadata/read adapters and23 actual-router preservation/privacy cases|
|12-15-02|51e2f13|Production mount, explicit legacy refusal and retained API adaptations|

## Verification

Only existing locked tools and the guarded disposable test stack were used.
No package install, provider call or production operation occurred.

| Check | Result |
|---|---|
| Task01 prescribed metadata/History/valuation filter |23 passed in4.31s|
| Initial prescribed four production API suites |103 passed in12.99s|
| Added actual correction/original HTTP proof |1 passed; exact real cash records and private roots|
| Retained crypto/valuation/trade-History plus auth/session/rate-limit run |111 passed|
| Retained stock HTTP plus account contract affected rerun |35 passed|
| Final combined production read/identity/crypto/stock APIs, retained crypto/stock/valuation/History APIs, auth request/session/verify, rate limits and accounts |259 passed in28.87s|
| Whole-backend mypy app |Success,101 source files|
| Ruff app and all changed tests |Pass|
| Ruff format check |115 files already formatted|
| git diff --check |Pass|

The final four API families comprise53 read/refusal/inventory cases,11 identity,
20 crypto and20 stock cases; all use real production composition. The final
259-case run includes retained regression families, not an entire backend run.
Two nonblocking warnings remain: the existing synthetic bad-key JWT warning
and the reused disposable dividend seed's transaction-deassociation warning.
No security/economic assertion is skipped, xfailed or replaced with a stub.

## Deviations from Plan

1. **[Rule2 — compatibility correctness]** Removed stale business handlers in
   the four v1 finance modules and stock handler module, in addition to changing
   their parent router. Otherwise complete app typing still sees obsolete
   user_id calls and separately importing an old router could retain an unsafe
   path. Only explicit refusal re-exports/private helpers remain.
2. **[Rule3 — production reachability proof]** Removed temporary registrations
   from shared and dedicated test fixtures and the rate-limit custom app.
   This is required by09/10/11's handoff and prevents test-only reachability.
3. **[Rule1/3 — retained fixture contract]** Retained API call sites now select
   their single initial test portfolio explicitly through real metadata, then
   call a captured scoped URL. The helper asserts exactly one active root and
   never rewrites requests or supplies an application default; multi-root tests
   use their explicitly captured IDs. Synthetic holding/fill records now carry
   paired root IDs and cursor boundaries carry the current root.
4. **[Rule1 — valid immutable test evidence]** The retained matched-split
   receipt test now supplies explicit digest version2, canonical actual journal
   digests and the movement root. Its synthetic split is held in a real external
   transaction shared with actual HTTP sessions, then rolled back before old
   cleanup. Globally immutable triggers remain enabled; no deletion exception
   or grant broadening was introduced. Original fill replay and new-order
   refusal assertions remain intact.
5. **[Rule1 — approved uniqueness change]** Replaced the obsolete account test
   expecting user-only uniqueness with a seeded-sibling/no-repeated-onboarding
   grant assertion, reflecting the explicitly approved0017 foundation. This
   does not introduce public multi-portfolio creation or a second grant.

Initial fixture corrections included active-only closure setup, separate
metadata/resolver queries versus the single financial valuation snapshot, and
the journal tail rather than action-event counter for the split boundary.
The old teardown's attempted immutable split deletion was refused as intended;
its disposable contamination was discarded using the existing guarded schema
fixture before the final passing runs. Runtime guards were never weakened.

## Known Stubs

None. Legacy financial refusal is intentional compatibility behavior; browser
consumers and full source-frozen recovery are separately planned tasks.

## Carry Forward

- Plan27 must adapt the older test_event_history_api.py module: collection
  currently fails because its static HistoryCursor construction omits the now
  required portfolio_id. Its retained dividend fixture also assumes ownership
  of old role setup. This was reported, not skipped or counted as passing;
  broad retained mixed-fixture integration remains27. Scoped private originals
  are proven through the new real HTTP test and the existing14 service suite.
- Plans19/20/23–25 must consume the actual metadata and scoped routes. All
  new financial endpoint paths are under /api/v2/portfolios/{portfolio_id}.
  Request-code, csrf, refresh/logout and refresh-cookie path stay at v1.
- Plan26's critical-path inventory must follow the live v2/central refusal
  modules rather than removed v1 handler implementations.
- No live activation, deployment, whole backend coverage, strict audit/image,
  rebuilt-image TLS/cold recovery, browser journey or human UI/native200%
  result is claimed here. All28 requirements remain unchecked and Phase7's
  six live outcomes remain separately deferred.

## Self-Check: PASSED

Both task commits and all four created files exist; no tracked file was deleted.
The final affected259-case run, full app typing and changed-file formatting/lint
pass. Unrelated .claude/ remains untouched. All commits remain local.
