---
phase: 05-portfolio-and-history
plan: "02"
subsystem: portfolio
tags: [react, decimal, accessibility, allocation, exact-strings]
requires:
  - phase: 05-01
    provides: Authenticated full portfolio response, strict guards and real query hook
provides:
  - Complete holdings table and mobile cards with fee-inclusive performance
  - Cash-inclusive allocation text and bounded decorative bars
  - Exact signed financial and full local timestamp display helpers
affects: [05-03, 05-07, 05-08]
tech-stack:
  added: []
  patterns: [String-only financial presentation, CSS-switched semantic representations]
key-files:
  created:
    - frontend/src/components/PortfolioHoldings.tsx
    - frontend/src/components/PortfolioAllocation.tsx
    - frontend/src/lib/financialDisplay.ts
    - frontend/src/lib/financialDisplay.test.ts
  modified:
    - frontend/src/pages/PortfolioPage.tsx
    - frontend/src/pages/PortfolioPage.test.tsx
    - backend/tests/test_portfolio_math.py
key-decisions:
  - Preserve calculator implementation; new edge regressions confirm its existing contract.
  - Treat positive raw value rounded to zero dollars separately from an actually zero denominator.
requirements-completed: [PORT-01, PORT-02, PORT-03, PORT-04]
requirements-status: Plan implementation coverage only; global acceptance remains with the phase gates.
duration: 7 min
completed: 2026-10-30
---

# Phase 5 Plan 2: Portfolio Holdings and Allocation Summary

**Exact holding performance in responsive semantic views, with real cash-inclusive allocation and explicit zero/unavailable outcomes.**

## Performance

- **Duration:** Approximately 7 minutes including preparation and verification.
- **Started:** After the 05-01 state sync at 2026-10-30T07:02:53Z; first RED commit at 07:04:54Z.
- **Completed:** 2026-10-30T07:10:06Z verification; summary recorded immediately afterward.
- **Tasks:** 2/2
- **Source/test files changed:** 7

## Accomplishments

- PortfolioPage continues to use the real usePortfolio/apiFetch response. Every holding keeps server order and symbol keys, including inactive coins. Desktop has scoped table headers and a labelled keyboard-focusable scroll region; mobile has ordered cards with labelled fields. Complementary `hidden md:block` / `md:hidden` display rules expose one representation at each breakpoint.
- Holdings show quantity, fee-inclusive average cost, mid, current value, independently signed dollar/percentage unrealized return, allocation and full local price timestamp with exact UTC title/dateTime. Zero-basis positions show $0.00 average, real dollar return, Not applicable and the approved explanation. Missing-price values say Unavailable; inactive holdings have no Trade link. Active links retain the existing route and 44px targets.
- Shared outcome helpers inspect decimal strings and reuse exact-string currency formatting. Positive plus, Unicode minus, neutral zero, separate gain/loss/no-change text and decorative arrows also serve the summary. Rounded neutral percentages remain neutral beside negative dollars. Existing quantity trimming remains unchanged.
- Cash and each actual holding have labelled allocation text and 8px blue bars on muted tracks. Percentage strings are lexically bounded to 0..100 before direct CSS use. Null has no fill, known zero has an empty track, and no ratio or balancing residual is computed in the browser. Positive raw totals rounded to $0.00 retain their known percentages.
- New calculator regressions cover cash-inclusive/raw denominators, differing rounded row sums, 99.99/100.01 allocation sums, HALF_EVEN ties, normalized negative zero, wide products/averages, 1e-8 quantities, zero basis/start/total and the real partial-sale dust basis function.

## Task Commits

1. **Task 1: Show full holding performance on desktop and mobile**
   - RED: `f66c07e` — Cover complete holding performance display.
   - GREEN: `c1204fa` — Show complete holding performance.
2. **Task 2: Explain allocation with real cash and position percentages**
   - RED: `d6557a5` — Cover cash-inclusive allocation and rounding edges.
   - GREEN: `31ab6df` — Explain cash-inclusive portfolio allocation.

## Verification

- **Task 1 RED:** helper suite could not resolve the not-yet-created financialDisplay module; three new holdings/empty-state page tests failed; four existing page tests passed.
- **Task 1 GREEN:** 19 focused display/page tests and 13 existing money formatter tests passed. Frontend lint, TypeScript, changed-file Prettier and diff checks passed before commit.
- **Task 2 RED:** five new allocation page cases failed while seven existing page cases passed. All 12 calculator tests, including seven new regressions, passed against the existing calculator before UI implementation. Those are regression evidence, not claimed calculator RED failures.
- **Final frontend regressions:** financialDisplay, PortfolioPage, money, portfolio API, App, MarketsPage and TradePage — **96 passed in 7 files**. This includes 31 focused display/page tests and malformed/out-of-range CSS percentage assertions.
- **Final backend regressions:** portfolio math/service/API and accounts — **24 passed**, including all 12 calculator tests. Changed backend test file passed Ruff lint and format checks.
- **Final static checks:** frontend ESLint, TypeScript, changed-file Prettier and `git diff --check` passed. Source scan found no financial Number/parseFloat conversion or blocking placeholder/stub. Task commits contain no tracked deletions.
- **Isolation:** only `docker compose --env-file /dev/null -f docker-compose.test.yml` was started; guarded synthetic localhost fixtures were used. Both birja-test containers and network were removed with `down -v`. No real accounts, dev/prod services or secrets were accessed.
- **Pending:** actual browser responsive/accessibility proof at 375/768/1024/1440px belongs to 05-07 and human review to 05-08. Component tests verify complete semantic markup and complementary CSS display rules; jsdom does not prove media-query rendering. Playwright remains CI-only and unexecuted locally. Full phase coverage/security/review/CI gates remain pending.

## Files Created/Modified

- `PortfolioHoldings.tsx` — Shared outcome rendering, complete semantic table/mobile cards, timestamps, inactive state and empty-state navigation.
- `PortfolioAllocation.tsx` — Cash/holding allocation labels, bounded direct CSS widths and zero-total explanation.
- `financialDisplay.ts` and its tests — Exact string signs/outcomes and full local timestamps.
- `PortfolioPage.tsx` and its tests — Integrated real holdings/allocation and summary formatting, retained existing query/error behavior.
- `test_portfolio_math.py` — Explicit raw-rounding, denominator, wide-value and real dust-basis regressions.

## Decisions Made

Followed the approved UI-SPEC and existing design tokens, Inter typography and local overrides; no global restyle or dependency changes. The calculator already satisfies the added financial regressions and was preserved. Shared STATE/ROADMAP/REQUIREMENTS/config updates remain the orchestrator's responsibility. The requirements frontmatter copies this plan's mapped IDs; it does not mark global requirements or Phase 5 complete.

## Deviations from Plan

None in implementation scope. Added defensive CSS-boundary regression assertions and the rounded-zero-total presentation case within the planned test ownership.

## Issues Encountered

- Docker/isolated localhost test access and Git writes used scoped sandbox escalation.
- The cleanup trap initially resolved the compose filename from backend after tests passed. An immediate root-directory `down -v` succeeded and removed the isolated resources; no dev/prod stack was touched.

## User Setup Required

None.

## Next Phase Readiness

Ready for 05-03 freshness/retained-state proofs using these real holding fields and timestamps. History, private-cache integration, final responsive browser proof, review, CI and human UAT remain assigned to later plans. No push, PR, merge, release or deployment occurred.

## Self-Check: PASSED

All seven source/test files exist and all four task commits resolve. No tracked deletion, blocking stub or new endpoint/auth/schema/trust-boundary surface was introduced. Only unrelated `.claude/` files remained untracked before this summary.
