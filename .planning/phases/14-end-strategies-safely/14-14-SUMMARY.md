---
phase: 14-end-strategies-safely
plan: "14"
subsystem: ui
tags: [react, deletion, recovery, accessibility, session-isolation]
requires:
  - phase: 14-13
    provides: Accepted financial projections, quarantine, owner/tab recovery and generation fences
provides:
  - Named inline irreversible deletion review with safe Cancel focus
  - Persistent metadata-only deletion host outside the financial Outlet
  - Authenticated static original-request recovery and overview navigation
  - Routed last-portfolio, stale-context and metadata-lifetime regression coverage
affects: [14-15, 14-17, 14-18, 14-19]
tech-stack:
  added: []
  patterns: [Persistent deletion host with revocable editor child, explicit original recovery]
key-files:
  created:
    - frontend/src/components/PortfolioDeleteForm.tsx
    - frontend/src/components/PortfolioDeleteForm.test.tsx
    - frontend/src/pages/PortfolioDeletionPage.tsx
    - frontend/src/pages/PortfolioDeletionPage.test.tsx
  modified:
    - frontend/src/components/PortfolioMetadataForm.tsx
    - frontend/src/components/PortfolioMetadataForm.test.tsx
    - frontend/src/pages/PortfoliosPage.tsx
    - frontend/src/pages/PortfoliosPage.test.tsx
    - frontend/src/App.tsx
    - frontend/src/App.test.tsx
    - frontend/src/pages/PortfolioPage.tsx
    - frontend/src/pages/PortfolioPage.test.tsx
key-decisions:
  - Keep the deletion operation mounted through automatic quarantine while retaining the metadata editor's existing revocation and PATCH-abort lifetime.
  - Recovery is a static authenticated owner/tab route; names and intent keys never enter its URL.
  - Only receipt.isCurrent may initiate completion navigation; confirmed closure never selects or funds a replacement portfolio.
requirements-completed: []
requirements-progress: [PMGT-03, PMGT-04, PMGT-05, PCTX-03, PSAFE-01]
duration: 17min from first RED receipt through committed-source qualification
completed: 2026-11-19
---

# Phase 14 Plan 14: Named deletion and original recovery Summary

**An explicit named deletion review survives financial quarantine, preserves the immutable original request, and returns confirmed closure to a signed-in overview without selecting or funding another strategy.**

## Accomplishments

- Added an escaped canonical-name review with the exact freeze, unpaid/future dividend/split/correction, retained-record, no-sale, no-transfer and no-undo consequences. The last-portfolio notice uses accepted active membership only.
- The disclosure only opens review. Cancel receives initial focus; Cancel/Escape send nothing and restore the disclosure. Final deletion requires its own button activation. Metadata editing/drafts and deletion review exclude each other without discarding drafts.
- Preserved the reviewed name across invalidation and required fresh same-ID review after a rename. Pending/unknown states retain only validated original metadata, explain that leaving does not cancel, and offer explicit original-result checking with the hook's server wait boundary. No automatic DELETE was added.
- Added one busy/polite announcement or unknown alert, user-error focus, removed-control fallback, full-name wrapping, existing semantic tokens, minimum 44px controls, 8px action gaps and content-driven confirmation padding. No dialog, package, font, registry, image or design-system replacement was introduced.
- Mounted `/portfolios/deletion` before dynamic portfolio routes, authenticated and outside the financial Outlet. A direct URL without a marker offers private overview navigation; restoration never sends a mutation. A durable rename refusal links to fresh metadata for its original ID.
- Added an overview recovery notice/link, a brief generic current-completion acknowledgement, uncertain-membership count/capacity handling, authoritative empty/Create behavior and post-ack error handling. Known closure navigates to `/portfolios`, never an implicit sibling. Markets, Account and Sign out remain available.
- Real App tests cover confirm → financial quarantine → known closure/unknown recovery, reload without automatic DELETE, pre-submit Escape, metadata exclusion, rename refusal, storage retry, last-book Back, remaining sibling, same-name replacement, and late results after navigation/logout/same-owner new session/replacement owner.

## Task commits and TDD evidence

| Task | Commit | Result |
|---|---|---|
| 1 RED | `bce1d7e` | New form is missing and existing metadata editing ignores deletion review exclusion. |
| 1 GREEN | `cf3e9ad` | Named review/recovery component and metadata exclusion; 20 focused tests pass in 2.44s. |
| 2 RED | `065f44a` | Static recovery is missing, routed deletion cannot occur, and uncertain membership is reported as zero. |
| 2 GREEN | `d66554b` | Persistent operation host, authenticated recovery, guarded overview navigation and retained regressions pass. |

Both tasks have ordered RED/GREEN commits. All task commits are local on `feature/milestone-v1.2`.

## Verification

Qualified source: **`d66554b54df52b5b9417b48b88889b49e81e7954`**.

- Final whole frontend: **60 files / 1,321 tests passed in 27.60 seconds**, exit 0. Receipt: `/tmp/birja-phase14-plan14/full-qualified.log`.
- Final affected component/page/App selector: **6 files / 128 tests passed in 8.13 seconds**, exit 0. Receipt: `affected-final.log` in the same directory. All 43 retained PortfolioPage cases are included.
- Whole frontend typecheck, lint and formatting: exit 0. Receipts: `typecheck-qualified.log`, `lint-qualified.log`, `format-qualified.log`.
- `git diff --check` passes. The production-file stub/XSS scan found no TODO/FIXME/placeholder/dangerous HTML rendering. No tracked files were deleted.
- `/tmp/birja-phase14-plan14/source-bindings.json` binds all 12 changed source/test files by SHA256 to the qualified commit. Test logs contain synthetic identities and data only.

All Vitest and static processes completed. Test cleanup disposes QueryClients and clears synthetic storage/cookies/globals; no browser, database, service, container or provider was started. No dev/production `.env` was read. Existing unrelated `.claude/` remains untouched. Global STATE, ROADMAP and requirements remain parent-owned and unchanged by this executor.

## Deviations from Plan

1. **[Rule 2 — Required lifetime prerequisite] Relocate the existing metadata host.** Source inspection showed that PortfolioMetadataForm lived inside PortfolioPage's revocable financial Outlet. Submitting deletion there would unmount the operation during its own quarantine. Parent explicitly authorized the exact additional `PortfolioPage.tsx` and `PortfolioPage.test.tsx` files. The actual App `PortfolioRoute` now owns the persistent deletion host on the detail index only; primary h1 precedes management sections. Trade/History do not acquire a duplicate form. The retained page router imports this actual host rather than testing a divergent reconstruction. Included in `d66554b`.
2. **[Rule 1 — Retained editor lifetime] Separate persistent recovery from revocable editing.** The first whole-suite run had 18 retained fixture failures after relocation; updating the fixture to the actual host exposed seven genuine PATCH-abort/save-focus/owner-reset regressions. Keeping the entire editor mounted changed its established lifetime. An internal editor child now mounts only with active target authority, while the outer deletion lease survives quarantine. Owner/session generation keys reset local UI. All existing assertions remain, and all 43 retained cases pass. Included in `d66554b`; no hook contract changed.

The initial new App fixture also used the wrong metadata endpoint, and its first rename refusal included a `message` field forbidden by the strict 409 schema. Fixtures were corrected to `/metadata` and the actual code-only response; production transport gates were preserved. Focus assertions now target the real relocated primary h1 rather than a mock financial probe's heading. Lint caught effect-driven acknowledgement state; initialization now uses the route's initial state and the effect only consumes history state.

No dependency, lock, image, backend, recovery-tool, provider, production or publication changes occurred. Issue35 and strict phase qualification gates remain unchanged.

## Plan 17 capture and integration handoff

Use the actual `PortfolioRoute` host and current App router for the isolated browser journeys. Do not place deletion back inside the financial Outlet. Keep the outer metadata/deletion observer mounted through automatic quarantine, but let real route/owner/session departure retire its hook scope. The internal metadata editor must still unmount during revoked discovery so pending PATCH/draft review semantics remain intact.

Required actual captures remain: collapsed/review/Cancel; 60-codepoint Unicode/unbroken/markup-looking names and 1000-codepoint descriptions; last-book review; submitting; unknown/reloaded unknown; Retry-After; rename and operational refusal; known overview with sibling; true empty; post-ack discovery error; stale unavailable with/without original-order boolean; uncertain-stock deletion; cross-tab deletion during an original trade. Measure 320/375/768/1024/1280/1440px, control geometry, keyboard/focus, reduced motion and announcement behavior against the source-bound packet. This plan's jsdom tests do not prove rendered geometry or real SQL atomicity.

Plan15 backend fixture integration, Plan17 real full-stack browser/captures, Plan18 whole-source security/exact same-archive recovery, and Plan19 actual owner UI plus native browser 200% acceptance remain required. No previous phase's owner acceptance is inherited. No whole requirement is completed by this summary.

## Known Stubs

None. The recovery-only page intentionally has no metadata editor/refetch action; its terminal-refusal action navigates to fresh normal metadata for the original ID. Loading, empty and private-unavailable states are genuine safety states, not mock financial output.

## Self-Check: PASSED

All 12 listed source/test files and this summary exist. All four task commits resolve. The source bindings match the committed files, no tracked deletion occurred, all verification processes finished, and the only unrelated working-tree item is the preserved `.claude/` directory.
