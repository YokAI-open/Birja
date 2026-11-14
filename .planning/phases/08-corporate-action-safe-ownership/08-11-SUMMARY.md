---
phase: 08-corporate-action-safe-ownership
plan: "11"
subsystem: frontend
tags: [corporate-actions, accessibility, playwright, responsive]
requires:
  - phase: 08-10
    provides: Strict conservative stock projections and deadline-safe cache
provides:
  - Independent fixed-copy corporate-action status and unavailable valuation
  - Accessible retry feedback and manual recovery focus
  - Isolated responsive Chromium journeys and review screenshots
affects: [08-12, 08-13]
tech-stack:
  added: []
  patterns: [fixed-enum-copy, contextual-announcement, isolated-browser-fixtures]
key-files:
  created: [frontend/src/components/StockActionState.tsx, frontend/src/lib/stockActionCopy.ts, frontend/e2e/stock-actions.spec.ts, frontend/e2e/stock-fixtures.ts]
  modified: [frontend/src/components/StockSection.tsx, frontend/src/components/StockSection.test.tsx, frontend/e2e/stocks.spec.ts]
key-decisions:
  - Action, stock status, session, quote freshness and disabled trading remain independent facts.
  - Local query cache sanitization cannot erase request failure feedback or manual retry focus.
  - CSS zoom and narrow CSS viewport reflow are complementary evidence, not native toolbar zoom claims.
requirements-completed: []
requirements-addressed: [ACT-02, ACT-03]
duration: 39min
completed: 2026-11-11
---

# Phase 8 Plan 11: Accessible Stock Suspensions Summary

**Markets preserves all stock identities and crypto trading while fixed corporate-action warnings hide unsafe stock prices and explain unavailable valuation.**

Both tasks are implemented in seven frontend source/test files. No dependencies,
image versions, backend runtime, schema, privileges, credentials, provider calls,
production services or financial cash/History behavior changed. Stock execution
remains disabled. Phase7 UI acceptance and deferred live review are preserved.

## Task commits and meaningful RED/GREEN

1. Task08-11-01 RED `cce6bdd` requires visible scoped hold copy; GREEN `a09324b`
   adds fixed public reason mapping, independent status labels, semantic permitted
   checked times, contextual announcements and unavailable valuations.
2. Task08-11-02 browser tests `75a6a1d` and stronger RED `8d3b616` reproduce
   error-before-expiry feedback loss and failed keyboard retry focus. GREEN
   `aaab66a` retains failure through local cache sanitization and restores manual
   failed retry focus or the heading after successful recovery. Background updates
   do not move focus. Existing authenticated TanStack fetching remains unchanged.
3. Actual CSS200% cell-overflow RED `80cfb44` detects overlap beyond document
   overflow checks. Diagnostic assertions identify affected cells; narrow Side
   block/wrapping and Recent Badge auto-height/wrapping preserve copy and monetary
   formatting. Final GREEN `0cea8b5` also constrains the quote-time flex item's
   intrinsic minimum width; its original date/time formatting stays unchanged.

## Verification and browser scope

-17 focused RTL tests pass5.56seconds; final scoped typecheck, ESLint and Prettier pass.
  Component coverage before the final class-only change:97.01% statements,
  96.35% branches,94.73% functions,98.41% lines. Log:
  `/tmp/phase08-11-component-final.log`.
- Broad real Chromium run passes21/21 stories in69.4seconds without retries;
  `/tmp/birja-phase08-ui-obqbh0ko/browser-final.log`. Four responsive widths
  320/375/768/1280 preserve20stocks and15crypto links, independent holds, safe
  recovery, exact deadline/source-age expiry and accessible keyboard recovery.
- Actual login/backend/fake-crypto run in isolated synthetic Compose. Frontend
  stock routes provide deterministic layout/time cases; accounting races are
  established by earlier actual PostgreSQL proofs, not these routed fixtures.
- Screenshot paths and precise zoom limitations are in08-11-BROWSER.md. Broad
  screenshots precede the final narrow wrapping classes; focused CSS200% proof
  plus all four ordinary responsive widths pass5/5 in21.5seconds on final source.
  Log `/tmp/birja-phase08-ui-mqq4ss1g/browser-final.log`; final screenshots in its
  `screenshots/` directory. All table cells pass intrinsic overflow checks.
  Parent final full browser gate remains separate.
- Every task-owned stack cleans only `birja-phase08-e2e-test`, with empty owned
  container/network/volume inventories. No existing Phase7 process was touched.
- Intermediate13pass/8fail run exposed fixture coherence and genuine retry bugs;
  subsequent21pass run fixes them. The first CSS zoom run passed weaker checks,
  but visual inspection exposed overlap; strengthened cell geometry failed as
  expected before the final wrapping fix. No failed capture is claimed accepted.

## Deviations from plan

1. **[Rule2 — Required copy module]** Shared pure enum-copy helper lives in
   `stockActionCopy.ts` to satisfy React Fast Refresh exports without duplicating
   the visual and live-region wording.
2. **[Rule2 — Required fixture integration]** Extracted strict shared browser
   fixtures and updated existing stock stories for mandatory action/valuation,
   epoch/session/source-time coherence. No healthy fallback was introduced.
3. **[Rule1 — Retry lifecycle]** Actual cache sanitization clears transient query
   error state; UI retains request feedback across that privacy operation and
   restores keyboard focus after a failed manual retry. Successful background
   fetching clears the feedback without moving focus. A proposed cancellation
   concern was independently reviewed and withdrawn as unreachable in the retained
   authenticated flow; auth teardown removes queries and resets the UI lifecycle.
4. **[Rule1 — CSS zoom overlap]** Side text and fixed nowrap quote badges needed
   wrapping within table cells at CSS200%. Values, source times and copy remain
   unchanged; approved contract explicitly permits warning/badge wrapping.

## Handoff and remaining gates

Parent owns final independent source/visual reviews, full frontend/browser gates,
critical CI file lists,08-LOCAL-PROOF and08-VALIDATION. Owner Phase8 acceptance
remains Plan13; screenshots do not imply acceptance or provider permission.
Whole-phase requirements remain unchecked. No blocking stubs, new auth/network/
file-access boundary or dependency surface was introduced. Threats T-08-11-01/02
retain fixed enum text, price/time suppression and independent safety facts.

## Self-Check: PASSED

All seven changed source/test files and the browser packet exist; task RED/GREEN
commits exist. Scoped checks and actual browser evidence are recorded above.
Final source and metadata hashes are provided to the parent at lane release.
