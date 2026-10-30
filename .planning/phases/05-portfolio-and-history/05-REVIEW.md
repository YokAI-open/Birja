---
phase: 05-portfolio-and-history
reviewed: 2026-10-30T08:03:38Z
depth: standard
files_reviewed: 50
files_reviewed_list:
  - .github/workflows/ci.yml
  - CLAUDE.md
  - backend/alembic/env.py
  - backend/alembic/versions/0008_trade_history_index.py
  - backend/app/api/v1/history.py
  - backend/app/api/v1/portfolio.py
  - backend/app/api/v1/router.py
  - backend/app/models/trade.py
  - backend/app/schemas/history.py
  - backend/app/schemas/portfolio.py
  - backend/app/services/history.py
  - backend/app/services/portfolio.py
  - backend/app/services/portfolio_math.py
  - backend/tests/test_accounts.py
  - backend/tests/test_critical_coverage_config.py
  - backend/tests/test_history_api.py
  - backend/tests/test_history_service.py
  - backend/tests/test_migrations.py
  - backend/tests/test_portfolio_api.py
  - backend/tests/test_portfolio_math.py
  - backend/tests/test_portfolio_service.py
  - backend/tests/test_portfolio_snapshot.py
  - deploy/RUNBOOK.md
  - frontend/e2e/portfolio-history.spec.ts
  - frontend/src/App.test.tsx
  - frontend/src/App.tsx
  - frontend/src/api/client.test.ts
  - frontend/src/api/client.ts
  - frontend/src/api/history.test.ts
  - frontend/src/api/history.ts
  - frontend/src/api/portfolio.test.ts
  - frontend/src/api/portfolio.ts
  - frontend/src/components/PortfolioAllocation.tsx
  - frontend/src/components/PortfolioFreshness.tsx
  - frontend/src/components/PortfolioHoldings.tsx
  - frontend/src/hooks/useAuthMutations.test.tsx
  - frontend/src/hooks/useAuthMutations.ts
  - frontend/src/hooks/useHistory.test.tsx
  - frontend/src/hooks/useHistory.ts
  - frontend/src/hooks/usePortfolio.ts
  - frontend/src/hooks/useTrade.test.tsx
  - frontend/src/hooks/useTrade.ts
  - frontend/src/lib/financialDisplay.test.ts
  - frontend/src/lib/financialDisplay.ts
  - frontend/src/lib/privateQueries.test.ts
  - frontend/src/lib/privateQueries.ts
  - frontend/src/pages/HistoryPage.test.tsx
  - frontend/src/pages/HistoryPage.tsx
  - frontend/src/pages/PortfolioPage.test.tsx
  - frontend/src/pages/PortfolioPage.tsx
findings:
  critical: 2
  warning: 0
  info: 0
  total: 2
status: issues_found
---

# Phase 5: Code Review Report

**Reviewed:** 2026-10-30T08:03:38Z  
**Depth:** standard  
**Files Reviewed:** 50  
**Status:** issues_found

## Narrative Findings (AI reviewer)

## Summary

Reviewed the explicit summary-derived scope, with targeted call tracing through authentication, query cancellation, financial formatting and the database services. Two reproducible defects remain: an identity request can republish a signed-out account, and the cash-only browser test has a deterministic strict-locator failure. Both require correction before advancing the phase.

## Critical Issues

### CR-01: Cancel the pending identity read before publishing logout or sign-in

**Classification:** BLOCKER  
**File:** `/home/YokaiExchange/frontend/src/lib/privateQueries.ts:5-9`  
**Related:** `/home/YokaiExchange/frontend/src/hooks/useAuthMutations.ts:13-15`, `/home/YokaiExchange/frontend/src/hooks/useAuthMutations.ts:24-28`

**Issue:** The same non-`me` predicate is used for cancellation and removal. Keeping the observed `me` query object is necessary, but leaving its active request alive permits a pre-transition response to overwrite the identity published by either mutation. A background `/me` request can authenticate as A before logout, then deliver its JSON after logout succeeds. The helper does not abort it; `setQueryData(["me"], null)` does not cancel it. The late response reinstalls A, remounts the signed-in shell and can display A's email and cached account cash after sign-out. An outstanding unauthenticated identity read can similarly overwrite successful verification with null. The existing mutation regressions defer portfolio/history requests, but never a `me` request.

**Reproduction/evidence:** Ran a synthetic, database-free probe with the installed TanStack Query implementation: seed A; start deferred `fetchQuery(["me"])` consuming its signal; execute the helper's cancel/remove predicates; publish null; resolve the deferred A read. Output was `After logout publication: null`, followed by `After delayed pre-logout read: {"email":"a@example.test","cash_usd":"8123.45"}`. This proves the overwrite without accessing any actual identity or balance.

**Fix:** Cancel identity reads as well as other private reads, while retaining only the identity query object during removal. For example, await `queryClient.cancelQueries()` and then remove queries with `queryKey[0] !== "me"`; only afterward publish the mutation's identity. Cancellation does not remove its observer. Add regressions that hold a real `useMe` request pending across logout and verification, then resolve it after publication and assert that identity, account content and observer attachment remain correct.

### CR-02: Disambiguate the cash-only Playwright message locator

**Classification:** BLOCKER  
**File:** `/home/YokaiExchange/frontend/e2e/portfolio-history.spec.ts:194`  
**Related:** `/home/YokaiExchange/frontend/src/components/PortfolioFreshness.tsx:43-57`

**Issue:** `getByText("No market prices needed")` uses substring matching and resolves to two elements after the cash-only portfolio loads: the status span containing `No market prices needed.` and the visible paragraph containing `No market prices needed`. The `sr-only` class does not exclude an element from text matching. Playwright's strict `toBeVisible()` assertion therefore fails on every execution of this new cash-only case, blocking the e2e job and the aggregate CI gate. The later liquidation assertion already uses `exact: true`; this earlier assertion does not. The existing RTL assertion passes because its text matching defaults differ from Playwright's.

**Reproduction/evidence:** Evaluated the installed Playwright injected selector engine against a synthetic jsdom fragment containing those exact two rendered nodes. The generated substring selector `internal:text="No market prices needed"i` returned **2** matches: the status span and the visible paragraph. No browser, running service or real-email flow was used. Full Playwright execution remains pending CI; discovery is not a pass.

**Fix:** Use `page.getByText("No market prices needed", { exact: true })`, matching the later assertion, or scope explicitly to the visible paragraph within the total-value region. Preserve the live-region announcement. Execute the corrected spec in the permitted ephemeral fake-price/console-email CI environment before claiming the browser gate passes.

## Review Boundaries

No structural pre-pass was supplied. No source, tests, shared tracking, dependency or migration file was changed. This review used static analysis and two narrowly scoped synthetic Node probes; it did not repeat the backend/frontend suites, run a browser, start a database, inspect secrets or access development/production accounts. Earlier reported suite results are not represented as execution evidence from this review. Actual browser rendering, remote CI and fresh human acceptance remain separate pending gates.

---

_Reviewer: gsd-code-reviewer_  
_Depth: standard_
