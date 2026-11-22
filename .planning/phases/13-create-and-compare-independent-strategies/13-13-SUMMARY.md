---
phase: 13-create-and-compare-independent-strategies
plan: "13"
subsystem: ui
tags: [react, routing, accessibility, portfolios, owner-isolation]
requires:
  - phase: 13-12
    provides: Overview/create/edit UI and metadata-only routed editor lease
  - phase: 13-10
    provides: Strict current-target and narrow original-order recovery guards
provides:
  - Signed-in overview route independent of financial target selection
  - Native portfolio draft selection with guarded explicit detail navigation
  - Safe overview choices from unavailable targets and authenticated Markets
affects: [13-15, 13-16, 13-17, 13-18]
tech-stack:
  added: []
  patterns: [Owner-session-route keyed selection, Existing target-hook metadata subscription]
key-files:
  created:
    - frontend/src/components/PortfolioSwitcher.tsx
    - frontend/src/components/PortfolioSwitcher.test.tsx
  modified:
    - frontend/src/App.tsx
    - frontend/src/App.test.tsx
    - frontend/src/components/PortfolioTargetBoundary.tsx
    - frontend/src/components/PortfolioTargetBoundary.test.tsx
    - frontend/src/pages/MarketsPage.tsx
    - frontend/src/pages/MarketsPage.test.tsx
key-decisions:
  - "Keep selection local until explicit Open passes captured target.isCurrent and navigates only to detail."
  - "Reuse authenticated target discovery and its subscription; add no independent fetch, polling or financial authority."
  - "Preserve the unconditional metadata-only boundary lease and all financial loading/refusal behavior."
requirements-completed: [PMGT-01, PCTX-02, PVIEW-01]
duration: 8min
completed: 2026-11-18
---

# Phase 13 Plan 13: Explicit Portfolio Navigation Summary

**The real Portfolios overview is reachable without a financial target; native draft selection opens only a verified detail ID and preserves original financial intent.**

## Performance and Task Commits

- Started: 2026-11-18T12:37:22Z; completed: approximately 2026-11-18T12:45:10Z.
- Tasks: 2/2. Eight source/test paths changed; existing `PortfolioContext.tsx` was inspected and reused unchanged.
- Task 1 RED: `7bc3f7f` — new selector import fails before implementation; App independently records 11 failures at missing overview/navigation behavior.
- Task 1 GREEN: `ec7f46b` — real overview registration and guarded selector; 39 tests pass with whole frontend types/lint.
- Task 2 RED: `252db04` — six expected failures at missing refusal overview choices and authenticated Markets selector.
- Task 2 GREEN: `01c9da3` — refusal/Markets wiring plus actual routed creation and switch lifecycle integration; final 390 affected tests pass.

Both tasks have RED preceding GREEN. No tracked files were deleted. Parent owns STATE, ROADMAP, REQUIREMENTS and review artifacts; this executor did not edit or stage them. Requirement IDs describe this plan's contribution rather than whole-requirement acceptance.

## Implemented Behavior

`App` mounts the existing real `PortfoliosPage` at `/portfolios` outside `PortfolioTargetBoundary`. The primary tab now says Portfolios and always links there. Markets, Portfolios and History remain the three mobile destinations; Account and safe-area/focus behavior remain intact. Explicit detail/history/crypto/stock routes and sole-root legacy discovery remain unchanged. Multiple legacy choices retain their refusal and offer the overview rather than choosing a root.

`PortfolioSwitcher` uses the existing strict target hook for fetching, parsing, subscription and owner/session revocation. It reads that hook's accepted owner metadata cache without adding another fetch/poll or accepting cached labels as financial authority. Its local draft is keyed by owner, session, pathname and current portfolio ID. A native labeled select exposes the server's bounded ascending immutable ID order as `{name} · #{id}`; changing it or pressing arrow/Escape keys does not navigate or retarget the mounted financial page. Open selected portfolio checks its captured `target.isCurrent()` immediately and navigates only to `/portfolios/{id}`. No symbol, trade ticket, preview or attempt is carried to another root. Browser Back returns to the actual previous route.

The current authoritative name appears separately through the existing escaped, full-wrapping `PortfolioContext`. Names/options use React escaping. An overview link is always present while the signed-in control is mounted. Initial/revalidation loading, error and genuine zero states remain distinct; stale names/options are hidden and Open disabled during unknown/refused authority. A removed choice never selects a replacement. Owner/session change clears the draft and suppresses late old discovery. The existing strict parser supplies the canonical IDs/names, ten-book bound and numeric order.

Authenticated Markets uses the same control; public market data and price polling remain unchanged. Selecting a different draft leaves existing trade links on the verified current root until explicit navigation. Zero active roots still permit browsing Markets and Account; they cause no creation or grant. Refusal states now link to the actual overview, where explicit creation already exists. Explicit unavailable/foreign roots never mount financial children or fall back, and original unresolved-order notices retain only their approved current-owner/session/root boolean.

The unconditional `usePortfolioMetadataLifetime(portfolioId, result.status, pathname)` remains before conditional Outlet rendering. No financial guard, target hook, trade hook, metadata hook, original retry authority or create receipt implementation changed. Existing routed regression tests retain same-route draft/success preservation, interrupted pending-save review, and ignored-old-response isolation.

## Verification

Only existing Node 24/frontend dependencies were used; no DB resources, browser, providers, private environment or installs were involved.

```text
Task 1: npm run test -- src/components/PortfolioSwitcher.test.tsx src/App.test.tsx
  39 pass at Task 1 GREEN.
Task 2 initial RED: boundary + Markets suites
  6 expected failures; 26 existing cases pass.
Final affected regression: 17 suites, 390 tests PASS in 15.44s.
  App; PortfolioSwitcher; PortfolioTargetBoundary; MarketsPage;
  usePortfolioManagement; usePortfolioTarget; portfolioCrypto; portfolioStock;
  usePortfolioOverview; portfolioValuation; portfolioHistory; PortfolioPage;
  PortfolioCreateForm; PortfolioMetadataForm; PortfoliosPage; TradePage; StockTradePage.
npm run typecheck                         PASS: whole frontend tsc -b
npm run lint                              PASS: whole frontend ESLint
Prettier --check all nine planned paths    PASS
git diff --check                          PASS
```

New coverage includes zero/one/ten native options and immutable numeric order; escaped long current name; keyboard selection/Escape versus explicit Enter/Open; removed choice; failed discovery refresh; logout and late old-owner discovery; actual App overview with zero/one/many discovery roots; draft selection while the original trade child remains active; detail navigation/Back heading focus; actual current creation receipt to its original ID; no repeated route focus on background metadata renewal; and real pending creation responses after route or owner departure with no late navigation or replacement POST. Financial child probes in App verify routing/target handoff; the affected real page/hook suites verify their respective financial and original-attempt behavior. No browser proof is inferred from jsdom.

## Deviations from Plan

None. Existing `PortfolioContext.tsx` already supplies the required full escaped wrapping current name, so it was reused without cosmetic changes. The selector adds no separate query API or registry/component dependency. Routine test refinements use async observer settlement and table-driven objects so zero/one/many fixtures are exercised correctly.

## Issues Encountered

Git metadata is read-only under the default sandbox. Authorized scoped commits succeeded through reviewed escalation. No auth gate or external setup was required.

## Known Stubs

None. Empty/undefined values represent genuine zero, loading, unavailable or signed-out states. Stub scan found no TODO/FIXME/placeholder or unwired product data source. No new network endpoint, authentication mechanism, file access or schema trust boundary was introduced beyond the planned navigation/target boundary.

## Handoff and Limits

Plan 16 can exercise actual `/portfolios`, inline Create portfolio, explicit detail routes and the labeled native Open portfolio / Open selected portfolio control on both Markets and financial routes. The switcher navigates only to detail and never submits a financial or creation request. Overview creation continues using the existing original-result ID/current callback guards; real App tests cover the route integration without replacing those hooks.

Independent parent review, whole-phase coverage/security/recovery, actual browser journeys and native 200%/owner acceptance remain pending Plans 15–18. No whole phase or whole requirement acceptance is claimed. Keep issue35's exact existing accepted-risk scope/expiry **2026-12-17T00:00:00Z**, Python pin **20261111**, and Phase7 live admissions OFF. No package/manifest/lock/pin/provider/production/push/merge changes. Unrelated `.claude/` remains untouched; keep all commits local on `feature/milestone-v1.2`.

## Self-Check: PASSED

All eight changed source/test paths and this summary exist. All four listed task commits resolve, with RED before GREEN. The nine planned existing/new paths pass formatting; the final 390-case regression and whole frontend types/lint pass. No tracked deletions or generated untracked artifacts were introduced. Parent global planning updates and independent review remain pending.
