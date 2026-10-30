---
phase: 05-portfolio-and-history
scope: CR-01 and CR-02 from 05-REVIEW.md
completed: 2026-10-30
status: fixes-implemented-awaiting-independent-re-review
---

# Phase 5 Review Fix Evidence

Applied two scoped Rule 1 bug fixes to the existing 05-06/05-07 implementation on `feature/phase-05-portfolio-and-history`, starting at `a4e9f2c`. The original review, completed plan history and shared planning state remain unchanged. This evidence does not close 05-08 or represent human/browser acceptance.

## CR-01: Cancel pending identity reads before publication

- **RED — `e567bc1`:** Extended actual `useMe`/auth mutation regressions with deferred HTTP identity reads across logout (late A), verification (late A), and verification from signed-out state (late 401/null). Extended the mounted App account/logout test with a deferred identity refetch, observer checks and DOM-frame checks. After correcting an initial test harness assumption that the render helper returned its client, the negative control produced **four assertion failures** because the identity signal remained un-aborted; **21 other tests passed**. These are observed assertion failures, not missing-module or harness-error RED evidence.
- **GREEN — `8266da5`:** `clearPrivateQueries` now awaits `cancelQueries()` for every query, then removes only non-`me` queries. Both existing callers publish identity afterward. The same observed identity query object survives, with its observer attached. The helper regression explicitly requires unfiltered cancellation.
- **Behavior:** Deferred cancellation blocks identity publication until cleanup finishes. Resolving old network requests afterward cannot replace mutation-published null/B or restore removed portfolio/history. Failed mutations preserve identity/cache. The mounted App stays signed out without A's email/cash returning; existing mounted A→expired→B portfolio/history tests continue checking immediate private-page boundaries.
- **Focused verification:** `npm run test -- --run src/lib/privateQueries.test.ts src/hooks/useAuthMutations.test.tsx src/api/client.test.ts src/App.test.tsx` — **50 passed in four files**, 3.57 seconds. Full frontend lint, typecheck and changed-file formatting passed before the GREEN commit.

## CR-02: Select the visible cash-only paragraph exactly

- **RED — `ac9341f`:** Added an explicit uniqueness assertion to the existing cash-only browser target. A synthetic jsdom fragment containing the actual status-span and paragraph text was evaluated with the installed Playwright 1.64.1 injected selector engine. The old substring selector returned **two matches**, failing the expected-one assertion. No browser or service was started. This is a selector-level negative control, not an executed Playwright acceptance test.
- **GREEN — `1167b4e`:** Set `exact: true` on that locator, consistent with the later liquidation assertion. The same installed-engine probe then found **one target, the paragraph**, and verified the separate status span retained `aria-live="polite"`. No component/live-region implementation changed.
- **Discovery:** `npm run e2e -- --list` passed, discovering **11 tests in six files**, including the cash-only, responsive and full financial-flow cases. Discovery does not establish browser execution or visibility.

## Final Regression Gate

Run once after both fixes:

- `npm run test -- --coverage` — **258 passed in 24 files**, **17.09 seconds**; statements **99.05%**, branches **97.53%**, functions **100%**, lines **99.82%**.
- `npm run lint`, `npm run typecheck`, `npm run format:check` — all passed across the full frontend.
- `git diff --check` — passed; task commits have no tracked deletions. No package/lockfile change or generated untracked output was introduced. The pre-existing unrelated `.claude/` directory remains untouched.

No backend source changed, so the prior backend suite was not repeated. No database, browser, dev/prod service, environment file, live identity, balance, log, OTP, email or remote operation was accessed. No push, PR, merge, release or deployment occurred. Independent re-review, permitted ephemeral fake-price/console-email browser execution, remote CI and fresh 05-08 human verification remain pending.

## Scope and Threat Review

CR-01 repairs the existing T-05-CACHE identity/cache boundary; CR-02 repairs the T-05-TEST acceptance selector without changing accessibility. No new endpoint, auth mechanism, file-access boundary, schema, dependency or architecture was introduced. The changed production helper has no blocking stub. Shared STATE/ROADMAP/REQUIREMENTS updates and committing this evidence remain the root orchestrator's responsibility.

Context7 tools and the `ctx7` CLI were unavailable. Checked the official TanStack Query [cancellation guide](https://tanstack.com/query/v5/docs/framework/react/guides/query-cancellation) and [QueryClient reference](https://tanstack.com/query/v5/docs/reference/QueryClient); installed-library regressions verify the actual observer/cancellation behavior.

## Self-Check: PASSED

Verified all five focused source/test files and this evidence exist, and all four RED/GREEN commits resolve. No unrelated file was staged. The original review remains available for the independent re-review.
