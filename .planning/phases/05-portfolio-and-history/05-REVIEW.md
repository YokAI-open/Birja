---
phase: 05-portfolio-and-history
reviewed: 2026-10-30T13:21:52Z
initial_reviewed: 2026-10-30T08:03:38Z
reviewed_commit: e2764d1
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
  critical: 0
  warning: 0
  info: 0
  total: 0
resolved_findings: [CR-01, CR-02]
status: clean
---

# Phase 5: Code Review Report

**Reviewed:** 2026-10-30T13:21:52Z; initial review 2026-10-30T08:03:38Z
**Depth:** standard  
**Files Reviewed:** 50  
**Status:** clean (both original findings resolved)

## Narrative Findings (AI reviewer)

## Summary

The initial review covered the explicit 50-file summary-derived scope and found two reproducible defects. A focused independent re-review of `a4e9f2c..e2764d1`, the fix evidence and implicated source/tests confirms both are resolved. No new defect was found in those changes. Active finding counts are zero; the original findings and their evidence remain below as resolved history. This code-review result does not close remote CI, browser execution or human acceptance gates.

## Re-review Evidence

- Read the complete six-file fix diff, `05-REVIEW-FIX.md`, the cancellation helper and its tests, auth mutation callers/tests, identity hook/client guards, mounted App regression and affected browser selector/component. The original 50-file scope above is preserved; this pass did not repeat the whole review.
- Independently ran `npm run test -- --run src/lib/privateQueries.test.ts src/hooks/useAuthMutations.test.tsx src/api/client.test.ts src/App.test.tsx`: **50 passed in four files, 3.32 seconds**. The deferred identity cases assert an aborted identity signal before publication, unchanged identity during delayed cleanup, the same query object and observer, and no overwrite after late A or 401 results. The App regression verifies A's account content does not return after logout.
- Independently evaluated the installed Playwright injected text engine with the exact selector on the synthetic status-span/paragraph fragment: **one paragraph matched**, with the separate polite status retained. The component remains unchanged in the fix diff. This is a selector probe, not browser execution.
- The executor's separate full-frontend result (**258 tests** and lint/types/format) and **11 discovered e2e tests** are recorded in `05-REVIEW-FIX.md`; they were not rerun or represented as independent execution here.

## Resolved Critical Issues

### CR-01: Cancel the pending identity read before publishing logout or sign-in

**Classification:** BLOCKER  
**Resolution status:** RESOLVED at `8266da5`; independently re-reviewed at `e2764d1`.
**File:** `/home/YokaiExchange/frontend/src/lib/privateQueries.ts:5-9`  
**Related:** `/home/YokaiExchange/frontend/src/hooks/useAuthMutations.ts:13-15`, `/home/YokaiExchange/frontend/src/hooks/useAuthMutations.ts:24-28`

**Original issue:** The same non-`me` predicate was used for cancellation and removal. Keeping the observed `me` query object is necessary, but leaving its active request alive permitted a pre-transition response to overwrite the identity published by either mutation. A background `/me` request could authenticate as A before logout, then deliver its JSON after logout succeeded. The helper did not abort it; `setQueryData(["me"], null)` did not cancel it. The late response reinstalled A, remounted the signed-in shell and could display A's email and cached account cash after sign-out. An outstanding unauthenticated identity read could similarly overwrite successful verification with null. The original mutation regressions deferred portfolio/history requests, but never a `me` request.

**Reproduction/evidence:** Ran a synthetic, database-free probe with the installed TanStack Query implementation: seed A; start deferred `fetchQuery(["me"])` consuming its signal; execute the helper's cancel/remove predicates; publish null; resolve the deferred A read. Output was `After logout publication: null`, followed by `After delayed pre-logout read: {"email":"a@example.test","cash_usd":"8123.45"}`. This proves the overwrite without accessing any actual identity or balance.

**Fix:** Cancel identity reads as well as other private reads, while retaining only the identity query object during removal. For example, await `queryClient.cancelQueries()` and then remove queries with `queryKey[0] !== "me"`; only afterward publish the mutation's identity. Cancellation does not remove its observer. Add regressions that hold a real `useMe` request pending across logout and verification, then resolve it after publication and assert that identity, account content and observer attachment remain correct.

**Verified resolution:** `privateQueries.ts:10` now awaits unfiltered `cancelQueries()` and only removal retains the non-`me` predicate. Both mutation callers await this helper before publication. Tests added in RED commit `e567bc1` and made GREEN by `8266da5` exercise late A after logout, late A after verification, and late unauthenticated 401 after verification, while retaining the identity query object and observer. All focused tests passed during independent re-review.

### CR-02: Disambiguate the cash-only Playwright message locator

**Classification:** BLOCKER  
**Resolution status:** RESOLVED at `1167b4e`; independently re-reviewed at `e2764d1`.
**File:** `/home/YokaiExchange/frontend/e2e/portfolio-history.spec.ts:194`  
**Related:** `/home/YokaiExchange/frontend/src/components/PortfolioFreshness.tsx:43-57`

**Original issue:** `getByText("No market prices needed")` used substring matching and resolved to two elements after the cash-only portfolio loaded: the status span containing `No market prices needed.` and the visible paragraph containing `No market prices needed`. The `sr-only` class does not exclude an element from text matching. Playwright's strict `toBeVisible()` assertion therefore failed at selector resolution, blocking the e2e job and aggregate CI gate. The later liquidation assertion already used `exact: true`; this earlier assertion did not. The existing RTL assertion passed because its text matching defaults differ from Playwright's.

**Reproduction/evidence:** Evaluated the installed Playwright injected selector engine against a synthetic jsdom fragment containing those exact two rendered nodes. The generated substring selector `internal:text="No market prices needed"i` returned **2** matches: the status span and the visible paragraph. No browser, running service or real-email flow was used. Full Playwright execution remains pending CI; discovery is not a pass.

**Fix:** Use `page.getByText("No market prices needed", { exact: true })`, matching the later assertion, or scope explicitly to the visible paragraph within the total-value region. Preserve the live-region announcement. Execute the corrected spec in the permitted ephemeral fake-price/console-email CI environment before claiming the browser gate passes.

**Verified resolution:** `portfolio-history.spec.ts:194-196` now uses `exact: true`, asserts exactly one match, then asserts visibility. RED commit `ac9341f` adds uniqueness coverage; GREEN commit `1167b4e` disambiguates the selector. The independent installed-engine probe finds one paragraph and the unchanged component still supplies its atomic polite live region. Full browser execution remains pending.

## Review Boundaries

No structural pre-pass was supplied. This reviewer changed only this review artifact. The initial pass used static analysis and two synthetic Node probes; the focused re-review additionally ran the four frontend regression files and an exact-selector synthetic Node probe as recorded above. No backend suite, browser, database, secrets or development/production accounts were accessed. Actual browser rendering, remote CI and fresh human acceptance remain separate pending gates.

---

_Reviewer: gsd-code-reviewer_  
_Depth: standard_
