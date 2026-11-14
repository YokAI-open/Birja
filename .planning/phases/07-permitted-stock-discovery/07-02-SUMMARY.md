---
phase: 07-permitted-stock-discovery
plan: "02"
subsystem: trading
tags: [crypto, stock-isolation, postgresql, idempotency]
requires:
  - phase: 07-01
    provides: Additive asset discriminator and separately seeded stock identities
provides:
  - Crypto-only catalogue, latest-price reads and accepted-price writes
  - Unsupported stock holdings remain visible with incomplete portfolio totals
  - Crypto-only preview, execution, replay and holding lookup boundaries
affects: [07-03, 07-09, 07-10, 09-stock-trading]
tech-stack:
  added: []
  patterns:
    - Explicit asset-class predicates before legacy crypto pricing and execution
    - Unsupported holdings retain quantity and basis but receive no crypto mark
key-files:
  created: [backend/tests/test_stock_isolation.py]
  modified:
    - backend/app/services/prices.py
    - backend/app/services/portfolio.py
    - backend/app/services/trading.py
key-decisions:
  - Preserve unsupported held-stock rows as unpriced and inactive rather than omit them from totals.
  - Restrict idempotency lookup to crypto as well as quote and holding lookup.
requirements-completed: []
requirements-supported: [SAFE-01, STOCK-01]
duration: 7min
completed: 2026-11-10
---

# Phase 7 Plan 02: Crypto Boundary Preservation Summary

**Explicit asset discrimination preserves fifteen crypto instruments while refusing stock pricing, trading and replay through legacy endpoints.**

## Performance

- Duration: approximately7minutes, including required context reads and isolated stack setup.
- Started:2026-11-10T14:06Z; validation complete:2026-11-10T14:12:38Z.
- Tasks:2/2; source/test files changed:4. Existing test files remain unchanged because their behavior is retained and the new adverse cases share the owned stock-isolation fixture.

## Accomplishments

- Both catalogue loaders explicitly select crypto before Kraken/fake mapping or latest-price output. A same-symbol stock with NULL Kraken mapping and an injected crypto-table price cannot alter the original fifteen responses.
- Accepted crypto price writes filter their IDs against the crypto catalogue; forged stock IDs produce zero writes. Existing monotonic update and caller-owned transaction semantics remain.
- Portfolio price joins exclude stock marks without discarding the held row. Injected stock holdings retain exact quantity/basis, show unpriced/inactive state, and make aggregate valuation unavailable instead of falsely complete.
- Preview, execution and symbol holdings select only crypto. The internal ID-based held lookup and original-fill replay lookup also constrain asset class. No stock execution switch or new mutation endpoint exists.
- Authenticated HTTP requests for stock buys, sells and holdings return existing404/unknown_coin refusals. Extra forged coin_id fields remain422 under the existing schema. Direct service checks cover active/inactive stock rows, present/absent quotes, valid stock bid/ask injection, fixture holdings, ticker collision and injected stored stock-fill replay.
- Each refusal compares the complete persisted account/holding/trade rows, including starting cash, basis and idempotency fields, before and after. Original crypto fractions, dollar orders, fee/spread, transactions and replay continue to pass.

## Task Commits

1. Task07-02-01 RED: `21483df` — Specify crypto catalogue and valuation isolation.
2. Task07-02-01 GREEN: `fe233ba` — Isolate crypto prices and incomplete stock valuations.
3. Task07-02-02 RED: `bca7065` — Specify stock trade and replay refusal boundaries.
4. Task07-02-02 GREEN: `7b05fe1` — Refuse stocks across legacy crypto trade paths.

## Verification

- Task1 behavioral RED:3failures on stock inclusion, accepted forged ID and falsely complete valuation; no import or missing-file failure.
- Task1 exact slice: `uv run pytest tests/test_prices_service.py tests/test_stock_isolation.py -q` —16passed/0.73s before task2 cases were added.
- Task2 behavioral RED:6failures across stock service/HTTP boundaries and collision; separately injected stock-fill replay failed with DID NOT RAISE before the replay guard.
- Task2 exact slice: `uv run pytest tests/test_stock_isolation.py tests/test_trading_service.py tests/test_trades_api.py -q` —75passed/4.18s.
- Final combined planned slices plus directly affected portfolio/scheduler regressions: `uv run pytest tests/test_prices_service.py tests/test_stock_isolation.py tests/test_trading_service.py tests/test_trades_api.py tests/test_portfolio_service.py tests/test_scheduler.py tests/test_scheduler_loop.py -q` — **137passed/6.97s**.
- Ruff check and format-check on the three modified services and new test module:passed. Mypy on all three services:passed. Whitespace and tracked-file deletion checks:passed.
- Consumer search covered all app Coin/select/coin_id callers. Scheduler uses the guarded loader/writer. History only reads immutable stored fills and does no catalogue selection, mark calculation or execution; it needs no new crypto predicate that could hide financial records.
- No full-backend coverage, frontend, recovery/TLS/image, provider access or phase-completion claim follows from these scoped results. Those remain later plan gates.

## Decisions and Deviations

None outside the approved implementation contract. Existing test modules needed no edits; all new adverse cases live in the explicitly owned test_stock_isolation.py. No dependency, schema or architecture change.

An initial scoped lint run found an unused pytest import before task2's parametrized tests were present; the final module uses it and all final checks pass. This did not weaken any gate or affect application behavior.

## Known Stubs and Threat Review

No new stubs, endpoints, credentials or unplanned trust boundary. The new predicates and adverse HTTP/exact-row assertions implement T-07-04/T-07-05. Dependency lockfiles are unchanged. Missing stock execution and unpriced stock holdings are deliberate Phase7–8 refusal states, not claims of completed stock trading.

## Resources and Cleanup

Only docker-compose.test.yml synthetic PostgreSQL/Redis with tmpfs and guarded test ports were started. They and their test network were removed after verification. No production/dev resource, private configuration, provider request or external upload was accessed. Unrelated .claude/ files were preserved. All commits remain local; publication remains deferred.

## Next Plan Readiness

Ready for07-03 revision-aware recovery contract work. SAFE-01 and STOCK-01 remain pending until whole-phase obligations are verified. Calendar package approval and actual provider permission/access/UI acceptance remain subsequent explicit gates.

## Self-Check: PASSED

The new test artifact exists and all four task hashes are in branch history. Both tasks have behavioral RED→GREEN commits. Final137-test proof, scoped static checks and isolated-stack teardown succeeded; no tracked files were deleted.
