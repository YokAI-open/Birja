---
phase: 12-preserve-existing-investing-under-portfolio-ownership
plan: "11"
subsystem: trading
tags: [stock, portfolio, idempotency, concurrency, authorization, api]
requires:
  - phase: 12-08
    provides: explicit frozen owned-active portfolio resolution
  - phase: 12-10
    provides: user-global crypto retry identity and scoped HTTP pattern
  - phase: 12-12
    provides: paired stock movements and complete owned journals
provides:
  - Explicit-root stock context, quote, account-locked execution and immutable replay
  - Required original portfolio comparison for both stock and crypto retry consumers
  - Actual private scoped stock HTTP routers with string portfolio identity
affects: [12-13, 12-14, 12-15, 12-20, 12-21, 12-24, 12-26, 12-27]
tech-stack:
  added: []
  patterns: [instrument-first owned-root locks, immutable original-root replay, actual-router composition]
key-files:
  created:
    - backend/app/api/v2/stock_trades.py
    - backend/tests/test_portfolio_stock_trading.py
    - backend/tests/test_portfolio_stock_api.py
  modified:
    - backend/app/services/stock_trading.py
    - backend/app/services/trade_idempotency.py
    - backend/app/services/trading.py
    - backend/app/schemas/stock_trades.py
key-decisions:
  - Unavailable portfolios refuse before receipt or market lookup and are rechecked after root lock waits
  - Matching original active receipts replay without current market eligibility; closed portfolios never expose receipts
  - Scoped response identity is transport metadata derived from stored root, without rewriting legacy financial records
requirements-completed: []
requirements-addressed: [PFIN-02, PFIN-03, PSAFE-03]
duration: 13 min
completed: 2026-11-16
---

# Phase 12 Plan 11: Explicit Stock Execution and Gated Retry Ownership

**Owned stock transactions preserve whole-share economics and original receipts while actual scoped HTTP adapters refuse sibling, foreign and unavailable targets.**

## Performance

- Started after Plan12 closeout: 2026-11-16T10:30Z
- Final focused verification and task commits: 2026-11-16T10:43Z
- Tasks: 2/2
- Created/modified task files: 7
- Dependencies, provider operations, production changes and public route registration: none

## Accomplishments

- Stock financial/context/quote/execute paths require OwnedActivePortfolio.
  Exact Account.id/user_id/active predicates and portfolio-scoped holding joins
  replace user-only selection. Instrument gate precedes account lock, and active
  state is rechecked under that lock before a fill or original receipt is used.
  A close committed while an independent request waits prevents the new fill.
- New Trade, StockFillFacts and StockMovementInput carry paired root ownership.
  Final SQL authority receives the same portfolio identity and remains the last
  business SQL statement, after deferred checks, with only commit following.
  Existing whole-share arithmetic, zero fees, source/eligibility/price-change
  checks and immediately reusable per-root cash remain unchanged.
- Global user/key lookup compares original portfolio and canonical order before
  replay. Original active receipts survive current permissions/market denial
  and altered confirmation price; sibling keys conflict and closed targets
  return404 before receipt disclosure. Both crypto and stock consumers now
  supply required portfolio_id; the transitional optional helper default is gone.
- Real independent transactions prove same-root stock/crypto spend/key races,
  duplicate stock requests, sibling same-symbol basis independence, both ordered
  cross-asset key-conflict directions and a restricted birja_app new stock fill.
- Actual v2 quote/fill/context routers reuse existing auth, CSRF, private error
  wrapper and domain mapping. Context, quotes, repricing details and immutable
  receipts contain a string portfolio_id. Extra body target fields are refused.
  New fills return201, original safe retries200, and a synthetic response failure
  after commit is recovered by the original target/key without a second effect.
- HTTP tests compose the actual router objects under final /api/v2/portfolios
  prefixes with real sessions and database services. Production reachability
  is explicitly reserved for15 rather than claimed from test composition.

## Task Commits

| Task | Commit | Result |
|---|---|---|
| 12-11-01 | 1984101 | Explicit-root stock execution, required shared retry root and real transaction proofs |
| 12-11-02 | 791e8f8 | Actual scoped stock HTTP, string-ID contracts and response-loss/repricing proofs |

## Verification

Locked existing uv environment reused with --no-sync and temporary UV cache.
Only guarded disposable localhost PostgreSQL55432/Redis56379 were accessed.

| Check | Result |
|---|---|
| Assigned stock service suite | 23 passed at task01; final25 pass including both cross-asset key directions |
| Assigned actual-router stock API suite | 20 passed |
| Shared crypto service regression | 24 passed |
| Unchanged stock arithmetic regression | 89 passed |
| Final combined focused run | 158 passed in13.72s |
| Ruff check/format, all seven task files | PASS |
| Explicit changed-source mypy --follow-imports=silent, five source modules | PASS |
| git diff --check | PASS |

Default mypy following the reused v1 private wrapper reports three obsolete
user_id keyword calls in api/v1/stock_trades.py. Those handlers are the explicit
Plan15 unscoped-refusal consumers; no ignore annotations or runtime fallback
were added. A whole-application type/backend-suite success is not claimed.

Initial test setup encountered the sandbox socket boundary and was rerun with
scoped local-test access. One fixture intentionally committed closure of a book
with holdings, then inherited teardown correctly refused deleting those frozen
holdings. The corrected local-transition probe rolls closure back after actual
service refusal; separate committed closed-root scenarios and the independent
close-while-waiting transaction cover persisted refusal. The disposable schema
was reset through its existing guarded reset_disposable_schema helper after
failed cleanup. No production guard, trigger or grant was weakened or disabled.

## Deviations from Plan

1. **[Rule2 — Finish transitional shared retry boundary]** Required portfolio_id
   in trade_idempotency.require_same_order and updated the crypto wrong-asset
   refusal caller. Plan10 documented this exact handoff to11. Both ordered
   cross-asset conflicts and the24-case crypto regression pass.
2. **[Rule2 — Serialize historical replay lifecycle]** Historical stock replay
   obtains its retained instrument gate and rechecks active root under lock
   before returning financial data. Wrong-asset keys conflict before attempting
   a stock gate for a crypto instrument; no current catalogue or market admission
   is required to replay a valid stock receipt.

No new schema, dependencies, provider operations or unexpected threat surface.
All scoped endpoints and paired-root authority are covered by the planned
threat mitigations; both task behavioral commands pass.

## Known Stubs

None in the implemented stock service/HTTP path. Production registration,
retained unscoped retirement and browser client adaptation are explicit later
plan obligations, not handlers returning fabricated data.

## Carry Forward

- Plan15 must mount actual v2 stock routers in production create_app, remove
  this module's test-only registration, and prove route inventory/HTTP behavior.
  It must retire v1 stock calls to deterministic409 portfolio_required before
  financial service invocation; that also resolves the three pending imported
  v1 type errors. No implicit-root compatibility adapter is permitted.
- Plans20/21/24 must consume string portfolio_id on stock context/quote/fill and
  nested replacement previews, retaining original attempt target through retries.
- Plan13 must derive stock entitlements by portfolio;14 owns scoped valuation
  and private mixed History. Neither is completed by these execution proofs.
- Retained user-only service callers/fixtures and old stock contract builders
  need explicit-root adaptation during domain/full-suite integration in27.
  No retained whole-suite pass is claimed; security, verified TLS, exact cold
  recovery, browser coverage and both owner UI checks remain phase gates.
- All milestone requirements remain unchecked. Phase7 deferred live outcomes,
  gated admissions, local-publication preference and unrelated .claude/ remain
  unchanged. Ready for12-13 by approved wave order.

## Self-Check: PASSED

All seven task files exist and commits1984101/791e8f8 are on
feature/milestone-v1.2. Both assigned suites and the focused158-case regression
pass; no tracked file deletion, package change or skipped financial assertion
was introduced. The three pending v1 type errors are explicitly recorded above.
