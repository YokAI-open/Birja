---
phase: 12-preserve-existing-investing-under-portfolio-ownership
plan: "23"
subsystem: ui
tags: [portfolio, navigation, identity, authorization, accessibility]
requires:
  - phase: 12-19
    provides: explicit target metadata and opt-in navigation-only legacy discovery
  - phase: 12-20
    provides: required-root browser financial transport
  - phase: 12-22
    provides: captured target-first private read hooks for later page consumers
provides:
  - Neutral fully wrapping portfolio name context and safe financial-child boundary
  - Actual explicit resource routes and owner-local target-preserving navigation
  - Identity-only Account without invented cash or root-dependent onboarding
  - Safe sole-root legacy entry replacement and zero/many/unavailable refusal
affects: [12-24, 12-25, 12-26, 12-27, 12-28]
tech-stack:
  added: []
  patterns: [verified Outlet target context, owner-keyed navigation lifetime, refusal before financial child mount]
key-files:
  created:
    - frontend/src/components/PortfolioContext.tsx
    - frontend/src/components/PortfolioTargetBoundary.tsx
    - frontend/src/components/PortfolioTargetBoundary.test.tsx
  modified:
    - frontend/src/App.tsx
    - frontend/src/App.test.tsx
    - frontend/src/pages/AccountPage.tsx
    - frontend/src/pages/MarketsPage.tsx
    - frontend/src/components/StockSection.tsx
    - frontend/src/components/StockSection.test.tsx
key-decisions:
  - Pass the verified PortfolioTarget through React Router Outlet context; financial pages24/25 consume it explicitly
  - Keep navigation memory inside the mounted signed-in identity; explicit routes always take priority over remembered navigation
  - Legacy routes opt into sole-root discovery only before financial children mount; zero/many never choose or create a root
  - Account renders identity/session actions only; public market facts remain browseable without financial authority
requirements-completed: []
requirements-addressed: [PCTX-01, PSAFE-02]
duration: 15 min
completed: 2026-11-16
---

# Phase 12 Plan 23: Scoped Navigation and Accessible Target Boundary

**Explicit owned-resource routes and a metadata boundary suppress unavailable finance while preserving identity-only Account and target-bound market navigation.**

## Performance

- Started: 2026-11-16T14:12Z
- Focused verification and task commits complete: 2026-11-16T14:26Z
- Tasks: 2/2
- Files created/modified: 9
- Packages, backend endpoints, provider admission and production resources changed: none

## Accomplishments

- PortfolioContext renders a semantic Portfolio/name pair using neutral existing
  tokens and safe React text. All60 allowed characters wrap naturally with
  min-width:0 and overflow-wrap:anywhere; no dropdown, ellipsis, badge, repeated
  live region, description or management control was introduced.
- PortfolioTargetBoundary consumes actual usePortfolioTarget. Loading never
  mounts finance; malformed, absent, ambiguous, empty and unavailable states use
  approved copy. Errors retry only the captured metadata query. Initial refusal
  focuses its heading; later background loss announces without heading focus
  theft. A revoked target removes all child financial regions.
- App registers /portfolios/:portfolioId and its history, crypto and stock trade
  children. Ready boundaries render Outlet with the actual PortfolioTarget as
  context. Legacy /portfolio, /history and both trade entries explicitly opt into
  discovery and replace-navigate only for exactly one active owned root before
  mounting any financial child. Explicit unavailable links never fall back.
- Navigation retains the same verified ID through Markets, Portfolio, History
  and trade links. Its remembered navigation belongs only to the current mounted
  signed-in identity, which is keyed by owner; account/session replacement cannot
  reuse another identity's selection. An explicit unavailable route masks that
  memory. Metadata does not grant execution authority.
- Account retains Email, Sign out, error handling and health view, removing its
  old user-wide Cash block. Zero roots do not trigger metadata discovery on
  Account, synthesize cash, create a portfolio or repeat a grant.
- Public market prices and stock facts remain globally shared. When a verified
  root is known, crypto and both desktop/mobile stock trade links carry its
  encoded ID; otherwise they enter the safe legacy resolver without finance.

## Task Commits

| Task | Commit | Result |
|---|---|---|
| 12-23-01 | 86b8041 | Context/boundary and15 focused cases |
| 12-23-02 | 391a802 | Explicit routes, identity-only Account and scoped navigation |

## Verification

- Assigned boundary command:15 tests pass.
- Assigned App command:31 tests pass against real App, target hook, metadata
  transport, boundary, Account and auth lifecycle. Financial child probes are
  explicit stand-ins for pages owned by24/25, not proof of those future pages.
- Combined App/boundary/StockSection/MarketsPage regression:75 tests pass.
  This includes actual crypto market links and both stock layouts, heading/Back
  focus, metadata401 sign-in, sign-out CSRF, late identity cancellation, owner
  changes, root loss, malformed IDs, zero/many discovery and private refusal.
- Changed-file ESLint, Prettier and git diff checks pass.
- Full frontend typecheck was run and still fails on downstream target-first
  financial pages24/25 and retained test fixtures27. It reports no errors in
  this plan's changed/new files; Account's cash_usd consumer is removed. Whole
  frontend build/type/coverage success is not claimed.
- Unit assertions prove wrapping styles, text escaping and semantics only.
  Actual320px/multi-width browser reflow, genuine native200% zoom and owner
  acceptance remain26–28; JSDOM results are not layout/zoom evidence.

## Deviations from Plan

### Auto-fixed blocking wiring

**1. [Rule3 - Blocking] Carry root into existing public market navigation**

The declared App files alone could not preserve a verified root through crypto
and stock row links. MarketsPage and StockSection now accept optional navigation
metadata and form encoded scoped links when it exists. This is not an optional
financial-client target: absent navigation metadata still enters the resolver,
and no financial fetch executes. One StockSection regression verifies both
desktop/mobile links. These three extra files were committed with task02.

### Test corrections

Two initial boundary failures came from Vitest it.each spreading array rows;
table objects now preserve the intended metadata array. One App owner-switch
assertion now waits for TanStack observer notification before inspecting the new
owner's rendered nav. Scope/privacy assertions remain intact; runtime guards
were not weakened. Existing App tests were updated to email-only identity and
explicit-route contracts, with pending financial page work isolated as probes.

## Integration Contract for24/25

- Within scoped financial pages call useOutletContext<PortfolioTarget>() from
  react-router, then pass that captured target to21/22 financial hooks.
- Use PortfolioContext name={target.name} after the existing h1 and before the
  financial cards, and repeat it for independent preview/receipt/detail regions
  as UI-SPEC requires. Boundary itself does not add a competing financial label.
- Root-specific destination prefix is /portfolios/${target.portfolioId}. Never
  derive authority from a remembered display name or use unscoped receipt links.
- Real current financial pages have not yet been adapted to target-first hooks;
 24/25 are required before running the integrated UI. No placeholder business
  handler, compatibility cash value or default target was added here.

## Residual Gates and Scope

Plans24/25 page wiring,26 browser/CI graph,27 complete suites/security/images/
same-archive recovery and28 owner/native-zoom acceptance remain pending. No
whole requirement is marked complete from these component/wiring tests.
Six Phase7 live outcomes stay deferred; stock admissions remain gated. No push,
merge, new dependency, provider operation or production inspection/change occurred.
Unrelated untracked .claude/ remains untouched.

## Self-Check: PASSED

All three new component/test files exist; both task commits are present. Actual
source contains no placeholder financial data, new management controls or raw
HTML rendering. Output ownership and remaining gates were checked before closeout.
