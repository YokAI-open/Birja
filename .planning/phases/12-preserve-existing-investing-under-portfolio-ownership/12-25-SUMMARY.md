---
phase: 12-preserve-existing-investing-under-portfolio-ownership
plan: "25"
subsystem: ui
tags: [portfolio, history, valuation, authorization, focus, race-isolation]
requires:
  - phase: 12-22
    provides: target-first valuation and private History hooks
  - phase: 12-23
    provides: verified Outlet target and neutral portfolio context
provides:
  - Named owned portfolio statements and root-specific holding links
  - Scoped mixed History, original-detail lifetimes and focus anchors
  - Committed target readiness before warm-cache financial child mounting
affects: [12-26, 12-27, 12-28]
tech-stack:
  added: []
  patterns: [verified Outlet financial context, keyed detail lifetime, committed activation subscription]
key-files:
  created: []
  modified:
    - frontend/src/pages/PortfolioPage.tsx
    - frontend/src/components/PortfolioHoldings.tsx
    - frontend/src/pages/PortfolioPage.test.tsx
    - frontend/src/pages/HistoryPage.tsx
    - frontend/src/components/HistoryEventDetails.tsx
    - frontend/src/pages/HistoryPage.test.tsx
    - frontend/src/components/HistoryEventDetails.test.tsx
    - frontend/src/test/portfolioFixtures.ts
    - frontend/src/hooks/usePortfolioTarget.ts
key-decisions:
  - Read only the verified Outlet target and use it for all financial hooks and trade links
  - Scope original-detail state, DOM references and asynchronous focus to owner/root/session
  - Publish target readiness after committed activation rather than weakening isCurrent or activating in render
requirements-completed: []
requirements-addressed: [PCTX-01, PVIEW-03]
duration: 18 min
completed: 2026-11-16
---

# Phase 12 Plan 25: Scoped Holdings and Mixed History Surfaces

**Named statements, root-specific holdings and private original details preserve the accepted investing views without borrowing another portfolio's identity or financial evidence.**

## Performance

- Focused verification began: 2026-11-16T14:55Z
- Final affected gate completed: 2026-11-16T15:09Z
- Tasks: 2/2
- Files modified: 9
- Dependencies, backend authority and production resources changed: none

## Accomplishments

- PortfolioPage consumes useOutletContext<PortfolioTarget>() and passes it to
  usePortfolio. Statement and holdings regions show the approved neutral
  Portfolio/name text, with full escaped wrapping. Trade links use the same
  explicit root for stock and crypto; there is no selector, pooled value,
  identity cash fallback or new management feature.
- Existing alphabetical combined holdings, desktop table/mobile cards,
  fee-inclusive costs, exact returns, actual stored baseline, three allocation
  bars, dated stock marks and incomplete-value meanings remain intact. A failed
  valuation refresh follows Plan22's suppression of unvalidated projections;
  it never restores earlier cash as an accepted current result.
- HistoryPage consumes the verified target and scopes its local component
  lifetime to owner/root/session. Infinite-query pages already use the scoped
  hook; page announcements and focus intents additionally refuse invalidated
  targets. Approved cash helper copy identifies this portfolio's USD balance.
- Original dividend regions show the same context. Detail state and loaded
  original anchors include root/session identity, preventing a shared global
  event/reference ID from selecting a sibling's original. Target loss/logout
  removes financial content and late append/detail publication. Heading focus
  occurs only for a newly mounted valid original region; a same-root metadata
  refresh cannot steal focus from its existing control.
- Actual warm-cache sibling page tests exposed a readiness ordering issue in
  usePortfolioTarget: ready metadata could mount a financial child before its
  layout-committed scope became active, leaving History's initial query
  permanently disabled. A narrow useSyncExternalStore activation subscription
  now publishes ready only after committed activation. Existing owner/session,
  metadata and isCurrent checks remain unchanged; no authority is activated in
  render and no financial request runs before target validation.

## Task Commits

| Task | Commit | Result |
|---|---|---|
| 12-25-01 | deae175 | Owned statements, context, holdings links and preservation tests |
| 12-25-02 | cb70759 | Scoped History/detail/focus and committed target readiness |

## Verification

- PortfolioPage: **26 passed**. Exact figures/baselines, incomplete semantics,
  stock/crypto presentation, context escaping/wrapping, no-root/foreign refusal,
  same-symbol sibling navigation and delayed/root-loss responses.
- HistoryPage: **25 passed**. Retained chronology, append/error/focus behavior,
  mixed event kinds, scoped originals, cross-root cursor rejection, delayed
  append, root loss, logout and warm-cache sibling identity.
- HistoryEventDetails: **11 passed**, preserving exact saved economics, original
  navigation and focus, including same-root refreshed target objects.
- Required and affected target/read-hook gate: **152 passed** across six files.
- Final bounded App/trade/boundary/read regression: **249 passed** across ten
  files on final source. Commands used existing locked Node24/Vitest tooling.
- All nine changed files pass ESLint and Prettier; git diff --check passes.
- Full frontend typecheck remains failing with **47 errors across11 retained
  API/hook fixture files**, owned by Plan27. No error references a product page,
  changed source or changed test. This is not a full frontend build/test claim.

## Deviations from Plan

1. **[Rule3 - Blocking fixture contract]** Added required portfolio_id/name to
   shared synthetic portfolio fixtures and supplied target metadata to existing
   detail tests. Their old monetary values and negative assertions are retained.
   The old refresh test now asserts Plan22's existing privacy-safe suppression
   and retry behavior. Verified in the assigned page gates; deae175/cb70759.
2. **[Rule1 - Readiness ordering bug]** Added committed activation notification
   to the existing target hook after real sibling History navigation stalled.
   Warm-cache page, target, read-hook, logout, root-loss and late-response gates
   verify it without weakening authorization; cb70759.
3. **[Rule1 - Background focus]** Retained only first valid original-heading
   focus for each DOM node so refreshed same-root metadata does not refocus an
   already-open region. Existing detail focus regression covers new target
   objects while preserving the active Back control; cb70759.

Initial synthetic failures were a61-character metadata name, stale sibling
class totals, and a hardcoded session0 anchor expectation. Fixtures now follow
the strict actual wire/metadata/session contracts; parsers and economics were
not relaxed.

## Known Stubs / External Setup

None. Null rendering for unavailable authority is required privacy behavior.
No provider, cloud, private environment, real rows, package or production service
was accessed. Unrelated .claude/ remains untouched; everything is local.

## Handoff

- Plan26 owns browser/CI/critical-module harness updates and synthetic review
  artifacts. Plans27/28 still own actual browser widths/reflow, encrypted
  same-archive source/image/TLS recovery, strict gates and separate owner UI /
  genuine native200% acceptance. Unit wrapping assertions do not prove those.
- Plan27 must adapt the remaining11 retained fixture files: api/eventHistory,
  history, portfolio, stockTrades and trades tests; hooks/useEventHistory,
  useHistory, usePortfolio, useStockTrade and useTrade tests; and
  test/stockTradeFixtures.ts. Full frontend typing/build remains pending.
- Portfolio and History product pages now have no remaining type errors. Use
  the verified Outlet target; do not reconstruct authority from URL/name data.
- All whole requirements remain unchecked pending final phase verification.
  Phase7's six live requirements and activation guards remain unchanged.

## Self-Check: PASSED

Both task commits exist; all nine modified files exist. Assigned gates and the
249-case affected run pass with changed-file lint/format/type checks. Remaining
full-suite, browser, security, recovery and owner gates are explicit above.
