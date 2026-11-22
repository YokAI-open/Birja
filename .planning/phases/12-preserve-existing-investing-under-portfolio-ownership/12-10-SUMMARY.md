---
phase: 12-preserve-existing-investing-under-portfolio-ownership
plan: "10"
subsystem: trading
tags: [crypto, portfolio, idempotency, concurrency, authorization, api]
requires:
  - phase: 12-07
    provides: actual0017 owned constraints and restricted financial guards
  - phase: 12-08
    provides: frozen explicit owned-active resolver
  - phase: 12-09
    provides: versioned identity and actual-router test composition
provides:
  - Explicit-root crypto quote, holding and account-locked execution
  - User-global retry comparison against original portfolio and order payload
  - Actual private v2 crypto routers and string-ID quote/receipt/context responses
affects: [12-11, 12-15, 12-20, 12-21, 12-24, 12-26, 12-27]
tech-stack:
  added: []
  patterns: [paired active-root recheck, original-root retry, private actual-router composition]
key-files:
  created:
    - backend/app/api/v2/trades.py
    - backend/tests/test_portfolio_crypto.py
    - backend/tests/test_portfolio_crypto_api.py
  modified:
    - backend/app/services/trading.py
    - backend/app/services/trade_idempotency.py
    - backend/app/schemas/trades.py
key-decisions:
  - Every crypto service requires OwnedActivePortfolio and rechecks owner/active state; no user-only account fallback
  - User-global keys compare original portfolio and payload before any new market check
  - Scoped transport adds portfolio identity without changing stored original economic fields
requirements-completed: []
requirements-addressed: [PFIN-02, PFIN-03]
duration: 10 min
completed: 2026-11-16
---

# Phase 12 Plan 10: Explicit Crypto Execution and Retry Ownership

**Explicit active-root transactions preserve crypto economics and immutable retries while private v2 adapters identify the original portfolio on every financial response.**

## Performance

- Started: 2026-11-16T09:58Z
- Focused verification complete: 2026-11-16T10:07Z
- Tasks: 2/2
- Files created/modified: 6
- Dependencies, provider calls, production changes and route deployment: none

## Accomplishments

- Quote, execution and holding reads require a frozen OwnedActivePortfolio.
  Services independently select exact Account.id/user_id/closed_at; execution
  rechecks it under FOR UPDATE before looking up any original receipt. Account
  then portfolio/coin holding locks retain the existing transaction ordering.
- Every new holding and trade persists paired root ownership. Existing Decimal
  trade planning, spread, fee, basis and preview/repricing rules are retained.
  Real sessions prove same-root overspend refusal, sibling independence,
  same-key one-effect execution and user-global cross-root race conflicts.
- Replay uses the original stored root and canonical payload before current
  market gates, never a current sibling balance. Closed or foreign targets
  return unavailable even if a stale resolved object or original key is reused.
- Actual v2 routes implement scoped quote/fill/holding endpoints. The existing
  PrivateRoute wrapper protects success, validation, refusal and unexpected
  error responses with no-store/Vary and sanitized response-loss semantics.
  New fills return201 and original retries200; all scoped portfolio IDs and
  monetary transport are strings. Stored trade rows remain byte/value equal
  across replay; portfolio context is transport metadata, not a payload rewrite.
- The API tests include the actual routers in an isolated create_app composition,
  with real OTP/session/CSRF and database services. Production registration is
  deliberately not claimed before15.

## Task Commits

| Task | Commit | Result |
|---|---|---|
| 12-10-01 | 661d8a9 | Explicit-root crypto service and user-global original-root replay |
| 12-10-02 | 60e21e6 | Actual private scoped crypto adapters and string-ID responses |

## Verification

- `pytest tests/test_portfolio_crypto.py -q`:23 passed at task01; final24 pass
  after the restricted birja_app new-holding path was added.
- `pytest tests/test_portfolio_crypto_api.py -q`:20 passed. Covers correct root,
  private foreign/closed/unknown404, malformed422, CSRF403, unauthenticated401,
  original-root409 conflicts, repricing, stale-price replay, no target fallback,
  and sanitized500 after commit followed by one-effect original retry.
- Final combined assigned service/API and unchanged arithmetic run:44 assigned
  cases plus47 existing trade_math cases passed. The additionally selected old
  trading_schema family had16 fixture failures described below; combined
  command result was91 passed/16 failed, not an overall pass.
- Ruff passes all six changed Python files; focused mypy passes all four
  changed source modules; git diff --check passes.
- Existing uv environment reused with `--no-sync`; writable /tmp uv cache and
  scoped escalation used for guarded localhost PostgreSQL55432/Redis56379.
  Initial sandbox-only socket denial was not a feature result. No installation
  or dependency resolution change occurred.

## Deviations from Plan

1. **[Rule2 — Required negative proof] Reuse existing private response wrapper.**
   Crypto v1 protected only success responses. The actual v2 adapter reuses
   stock PrivateRoute for private validation/refusal/unknown-error behavior;
   the synthetic response-failure-after-commit test proves original retry.
2. **[Rule3 — Transitional shared consumer] Optional shared retry root argument.**
   require_same_order accepts optional portfolio_id solely to retain the old
   stock consumer's signature until11. Every new crypto replay always supplies
   the required original root. Plan11 must make the stock call root-aware and
   can remove the transitional default once all consumers are explicit.

## Deferred Issues and Next Plan Readiness

- The optional retained trading_schema family inserts holdings/trades without
  portfolio_id. It now fails16 cases at0017 NOT NULL rather than its intended
  old constraints. This predates10's service adaptation;27 must associate those
  synthetic fixtures explicitly and preserve all existing negative assertions.
  Recorded in deferred-items.md. No SQL constraint was weakened to pass them.
- Old v1 crypto handlers still call user_id-only service signatures. Plan15
  owns deterministic unscoped409 portfolio_required before any service call;
  no compatibility fallback was added. Full application mypy/backend suite is
  not claimed before those scheduled composition/fixture changes.
- Plan15 must register the actual crypto router under /api/v2 and remove this
  module's redundant test-only registration, then verify production inventory
  and rerun the HTTP cases through production create_app.
- Stock explicit execution remains11; journals12, dividends13, private valuation/
  History14, deployment/recovery16–18 and browser integration19–28 remain pending.
  Verified TLS, full coverage/security/images, exact cold restore and both owner
  UI/native200% checks remain phase gates. All requirements remain unchecked.
- No provider, production, new package, publication or branch switch occurred;
  six Phase7 deferred outcomes and unrelated .claude/ remain unchanged.

## Known Stubs

None. Actual services/routers are implemented. Production registration and
legacy refusal are explicit later composition obligations, not mock handlers.

## Self-Check: PASSED

All six task outputs exist and commits661d8a9/60e21e6 are on
feature/milestone-v1.2. Both assigned behavior gates pass, no tracked files were
deleted, no dependencies changed and no skipped financial assertions added.
