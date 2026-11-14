---
phase: 10-dividend-cash-and-event-history
plan: "14"
subsystem: mixed-history-ui
tags: [responsive-history, immutable-lineage, exact-money, keyboard-focus]
requires:
  - phase: 10-13
    provides: Owner/session-isolated infinite events and authoritative financial refresh
  - phase: 10-11
    provides: Authenticated exact mixed History wire
provides:
  - Typed trade, dividend, split and correction details with truthful applied cash
  - Loaded-original anchors and bounded offpage-original keyboard navigation
  - Five-column desktop History and equivalent mobile event cards
affects: [10-15, 10-16, 10-17, 10-18]
tech-stack:
  added: []
  patterns: [saved-event-rendering, stable-original-anchors, retained-page-recovery]
key-files:
  created:
    - frontend/src/components/HistoryEventDetails.tsx
    - frontend/src/components/HistoryEventDetails.test.tsx
  modified:
    - frontend/src/pages/HistoryPage.tsx
    - frontend/src/pages/HistoryPage.test.tsx
    - frontend/src/App.test.tsx
key-decisions:
  - Preserve exact significant rate strings and calendar dates without client financial arithmetic.
  - Held proposals never replace the actual no-cash headline or mutate an original payment.
  - Use layout-specific stable IDs and getElementById for original navigation, with a stable mount-focus callback.
requirements-completed: []
requirements-supported: [HIST-03, DIV-03, DIV-05]
duration: approximately14min
completed: 2026-11-13
---

# Phase10 Plan14: Truthful responsive mixed History

**Owner-isolated History renders saved event economics and actual cash separately
from held proposals, with immutable original details and keyboard-safe paging.**

## Tasks and commits

1. RED `7ac2d5e`: callable empty renderer lacked the expected no-cash uncertainty
   explanation;1 failed/1.54s, not an import failure. GREEN `2f52733`: all typed
   event details, exact rates/dates, actual versus proposed cash and original
   navigation;11 component tests and scoped ESLint/TypeScript pass.
2. RED `a7c21c0`: existing trade-only page lacked Account activity;1 failed/
   13 deselected/2.71s. GREEN `36a1642`: owner hook integration, approved five
   columns at lg, equivalent mobile cards, safe paging/recovery and integration
   fixture correction. All code and tests are committed; no staged seam remains.

## Actual verification

| Gate | Result |
|---|---|
| Final component/page gate |27 passed/3.54s |
| App plus component/page integration |47 passed/3.64s |
| Final full frontend coverage |695 passed/36 files/16.11s |
| Full coverage |98.40% statements;94.89% branches;98.95% functions;99.09% lines |
| Full ESLint / TypeScript / Prettier |Pass |
| Whitespace / stub / deletion scan |Pass; no tracked deletion or staged seam |

Used installed `npm run test -- --coverage`, `npm run lint`,
`npm run typecheck` and `npm run format:check`; no install or lock change.
Logs: `/tmp/birja-phase10-14-task1-red.log`,
`/tmp/birja-phase10-14-task1-expanded.log`,
`/tmp/birja-phase10-14-task2-red.log`,
`/tmp/birja-phase10-14-task2-final.log`,
`/tmp/birja-phase10-14-integration-fixed.log` and
`/tmp/birja-phase10-wave9-frontend-fixed.log`.

Assertions preserve existing append/error/refresh/retry/final-button focus
behavior, strict cursorv2 transport and server order. Mixed-kind page tests check
the exact five headers, stable public identities, stock/crypto labels, tiny rate,
long names, held no-cash explanation, loaded-original focus and immediate removal
of an expanded offpage original on logout. Component tests cover all outcomes,
positive/negative/zero cash, separate proposals, conserved split basis, stock IEX
attribution, nullable source-date copy, exact dates/UTC titles and escaped text.
Stable original-heading callbacks prevent background rerender focus theft.

No financial values are reconstructed, multiplied or credited in the browser.
Native time formatting applies only to instants; calendar dates stay unchanged.
Both responsive DOM layouts have distinct anchor prefixes and CSS exposes one
at a time. This jsdom proof does **not** establish actual viewport reflow, visual
quality, native200% zoom or browser focus visibility; Plans15/18 retain those gates.

## Deviations and construction corrections

Parent authorized only the necessary App.test.tsx integration-fixture extension.
The first full run had694 passes/one failure/16.06s because its transport routed
legacy `/trades` but not new `/history`, so the new owner's pending read never
started. It now routes both, seeds exact mixed-owner cache data alongside legacy
cache, and preserves all passive-expiry, late-response and frame-privacy assertions.
Failed log `/tmp/birja-phase10-wave9-frontend.log` remains preserved.

Construction corrections: direct component rerender is used for mount-focus
stability rather than replacing the test's provider tree; authenticated page
fixtures supply strict mixed fields/canonical boundary cursors and count their
own History spy instead of the auth transport wrapper. An old `total` field in
two sell fixtures was replaced by exact `cash_delta`; existing parser guards
remained intact. Formatting after the final focus change was corrected before
the final full gate. No application authority or contract changed.

Read the approved UI contract and existing MASTER. Local UI skill search for
focus-not-obscured returned the enhanced focus-visibility guidance, without an
AAA compliance claim; existing tokens/44px controls/mobile-first layout remain.
Context7/ctx7 were unavailable; no tool installed. Consulted official
[React19.3 DOM-ref/focus guidance](https://react.dev/learn/manipulating-the-dom-with-refs).

## Threat results and remaining gates

T-10-14-01/02 mitigated locally: strict validated typed sources, owner hook,
escaped metadata, stable original identity and truthful no-cash/immutable details.
T-10-14-03: bounded supplied original, no page scan or financial action, guarded
one-page append and retained accepted pages. T-10-14-SC: no dependency/package/
image changes. No unplanned route, admin/payment surface or known stub remains.

No backend/DB/Docker, .env/secrets, provider, production, B2, timer, installed
tool, publication or deployment access occurred. Parent owns canonical planning
state and requirement completion. Actual browser/source-hash review bundle15,
final gates16, reviews17 and real owner new-UI/native200% acceptance18 remain.

## Self-Check: PASSED

All5 owned implementation/test files and this summary exist; four RED/GREEN
task commits exist without deletion. Actual695 full tests,47 integration tests,
full static gates and whitespace checks pass. Unrelated `.claude/` is preserved.
