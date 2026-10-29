---
phase: 04-trading
reviewed: 2026-10-29T09:02:07Z
depth: standard
files_reviewed: 46
files_reviewed_list:
  - .github/workflows/ci.yml
  - CLAUDE.md
  - backend/alembic/versions/0006_holdings_and_trades.py
  - backend/alembic/versions/0007_accounts_cash_cents.py
  - backend/app/api/v1/router.py
  - backend/app/api/v1/trades.py
  - backend/app/core/config.py
  - backend/app/models/__init__.py
  - backend/app/models/trade.py
  - backend/app/models/user.py
  - backend/app/schemas/trades.py
  - backend/app/services/trade_math.py
  - backend/app/services/trading.py
  - backend/pyproject.toml
  - backend/tests/conftest.py
  - backend/tests/helpers.py
  - backend/tests/test_accounts.py
  - backend/tests/test_config_trading.py
  - backend/tests/test_migrations.py
  - backend/tests/test_trade_math.py
  - backend/tests/test_trades_api.py
  - backend/tests/test_trading_concurrency.py
  - backend/tests/test_trading_schema.py
  - backend/tests/test_trading_service.py
  - deploy/RUNBOOK.md
  - deploy/smoke-prod.sh
  - deploy/tests/test-smoke-trading.sh
  - frontend/e2e/trade.spec.ts
  - frontend/package.json
  - frontend/src/App.test.tsx
  - frontend/src/App.tsx
  - frontend/src/api/client.test.ts
  - frontend/src/api/client.ts
  - frontend/src/api/trades.test.ts
  - frontend/src/api/trades.ts
  - frontend/src/hooks/useDebouncedValue.test.ts
  - frontend/src/hooks/useDebouncedValue.ts
  - frontend/src/hooks/useHolding.ts
  - frontend/src/hooks/useQuote.ts
  - frontend/src/hooks/useTrade.ts
  - frontend/src/lib/money.test.ts
  - frontend/src/lib/money.ts
  - frontend/src/pages/MarketsPage.test.tsx
  - frontend/src/pages/MarketsPage.tsx
  - frontend/src/pages/TradePage.test.tsx
  - frontend/src/pages/TradePage.tsx
findings:
  critical: 1
  warning: 0
  info: 0
  total: 1
status: issues_found
---

# Phase 4: Code Review Report

**Reviewed:** 2026-10-29T09:02:07Z
**Depth:** standard
**Files reviewed:** 46, scoped from phase-summary key-files fields
**Status:** issues_found

## Summary

Reviewed every scoped file, tracing trade validation, decimal rounding,
cost basis, transaction locking, idempotency replay, API serialization,
frontend preview/confirmation, authentication boundaries and deployment
smoke checks. One execution-time freshness defect violates TRADE-05 when
a request waits for an account lock near the 120-second price-age limit.

Accepted v1 choices (including the fee-inclusive dollar amount, minimum
fee, whole-position dust exemption, stateless quote and lack of a trade
rate limit) are not findings. No additional proven defects were found at
this review depth. Fallow was disabled; no structural findings were supplied.

## Narrative Findings (AI reviewer)

### CR-01: Refresh the clock after acquiring the account lock

**Classification:** BLOCKER

**File:** `backend/app/services/trading.py:240` and `:261`

**Requirement:** TRADE-05; Phase 4 D-03 requires a trade to use a Live price
younger than 120 seconds at execution.

**Issue:** `execute()` assigns `now = now or datetime.now(UTC)` before its
first await, including the account `SELECT ... FOR UPDATE` at lines 244-250.
After that lock is acquired, `_require_fresh` at line 261 still receives the
time captured before the wait. A request that began while a price was
119 seconds old can wait two seconds on another transaction, then pass the
freshness check with an age of 119 and fill at an actual price age of 121.
The ordinary 30-second database statement timeout does not prevent this
two-second boundary crossing. This also applies to query/connection delay
between capturing the clock and loading the price.

The account lock correctly prevents overspending; the defect is that time
spent obtaining it is excluded from the stale-price decision. A stopped or
delayed scheduler is exactly when this boundary matters, so the trading
service must enforce it even if a client submitted while its badge was Live.

**Evidence:** Control-flow inspection proves the frozen timestamp spans
the awaited account lock and price read. The existing stale execution test
in `backend/tests/test_trading_service.py:361` supplies a fixed `now` and a
price already 130 seconds old, so it does not test a price becoming stale
while the transaction waits. Concurrency tests keep prices only five
seconds old and do not cross the freshness boundary.

**Fix:** Preserve the optional injected clock value for deterministic tests,
but sample the real clock when enforcing freshness after the account lock
and price load, rather than eagerly replacing `now` at method entry:

```python
# Keep `now` as None until the time-dependent check.
coin, price = await _load_coin_price(db, order.symbol)
age = _require_fresh(coin.symbol, price.as_of, now or datetime.now(UTC), settings)
```

Apply the same late-clock approach to `quote()` so a slow price read cannot
return an incorrectly fresh age. Keep replay lookup before freshness checks;
an already committed trade must remain replayable even with stale prices.

**Regression:** On the isolated real-Postgres test stack, hold the user's
account row lock in one session, start a new `execute()` in another session
without supplying `now`, advance a controlled clock from price age 119 to
121 while the second session waits, then release the first lock. Assert
`stale_price`, unchanged cash/holding and zero new trades. Add a control
that stays below 120 seconds and fills, and retain the stale-price replay
test. No production or dev trading is needed to reproduce this.

## Review limits and validation

- Source and tests were read at standard depth; supporting auth/query
  helpers were traced as needed.
- This review did not modify source, run containers, call application
  endpoints, access secret env files, execute trades or change git state.
- Prior suite/CI/smoke results in phase summaries were treated as recorded
  evidence, not a substitute for examining the uncovered lock-wait case.
- Findings are based on code and explicit execution ordering; the proposed
  real-Postgres regression was not run during this read-only review.

_Reviewer: Codex gsd-code-reviewer_
