---
phase: 13-create-and-compare-independent-strategies
plan: "12"
subsystem: ui
tags: [react, accessibility, portfolios, metadata, recovery]
requires:
  - phase: 13-09
    provides: Owner-bound creation recovery and authoritative metadata editor
  - phase: 13-10
    provides: Immutable original order recovery across renames
  - phase: 13-11
    provides: Guarded exact comparison statements and shared stock safety projection
provides:
  - Responsive independent portfolio comparison with exact server values
  - Inline creation with original-intent recovery and captured receipt navigation
  - Authoritative metadata view, edit and clear with explicit stale-draft review
affects: [13-13, 13-16, 13-17, 13-18]
tech-stack:
  added: []
  patterns: [Existing query hooks, Native accessible fields, Owner-session keyed draft lifetime]
key-files:
  created:
    - frontend/src/pages/PortfoliosPage.tsx
    - frontend/src/pages/PortfoliosPage.test.tsx
    - frontend/src/components/PortfolioCreateForm.tsx
    - frontend/src/components/PortfolioCreateForm.test.tsx
    - frontend/src/components/PortfolioMetadataForm.tsx
    - frontend/src/components/PortfolioMetadataForm.test.tsx
  modified:
    - frontend/src/pages/PortfolioPage.tsx
    - frontend/src/pages/PortfolioPage.test.tsx
    - frontend/src/hooks/usePortfolioManagement.ts
    - frontend/src/hooks/usePortfolioManagement.test.tsx
    - frontend/src/components/PortfolioTargetBoundary.tsx
key-decisions:
  - Preserve the approved UI contract and existing design system without dependencies or redesign.
  - Cancel captured financial reads before publishing renamed metadata; refresh discovery before marking unchanged financial views stale without immediate refetch.
  - Ignore receipts that predate a newly opened creation form; navigate only from a newly delivered receipt passing its captured isCurrent guard.
requirements-completed: [PMGT-01, PMGT-02, PMGT-06, PFUND-02, PVIEW-01, PVIEW-02]
duration: 21min
completed: 2026-11-18
---

# Phase 13 Plan 12: Portfolio Management UI Summary

**Exact independent-book comparison and accessible creation/edit forms preserve original recovery, metadata review and guarded financial reads across rename.**

## Performance

- Started: approximately 2026-11-18T11:54:00Z
- Completed: 2026-11-18T12:15:00Z
- Tasks: 2/2
- Source/test files: 10, including the parent-authorized two-file management-hook repair.

## Task Commits

1. Task 1 RED: `07d9834` — specify overview and creation interactions.
2. Task 1 GREEN: `3a2585b` — comparison and inline creation.
3. Task 2 RED: `c41ae2f` — metadata editing and review behavior, plus actual detail integration.
4. Rename/session regression RED: `c6a9d39` — real-hook rename/clear and deferred discovery.
5. Pending financial refresh RED: `e4c6cb2` — deferred old-name response must be aborted before renewal.
6. Authorized repair GREEN: `0d9f9d8` — cancellation, discovery sequencing and guarded stale-only financial invalidation.
7. Creation/feedback refinement: `65c7811` — earlier-receipt refusal, captured replay navigation, linked field errors and presentation.
8. Task 2 GREEN: `fb3e6e7` — metadata view/edit/clear beside preserved financial layout.
9. Overview feedback refinement: `adbc15b` — truthful unavailable-source and refresh status copy.

Both tasks have committed RED before GREEN. The RED imports failed because the new components did not exist; the existing detail test also independently failed because the description was absent. Later real-hook rename testing exposed a financial-query error, and the pending-read regression failed specifically at `oldSignal.aborted === false` before cancellation was added. No tracked file was deleted.

## Implemented Behavior

`PortfoliosPage` consumes `usePortfolioOverview()` directly. It preserves the server's ascending numeric ID order and decimal strings, formatting with existing exact-money and signed-outcome helpers. There is no pooled total, ranking, return arithmetic or per-book fetch loop. The 768px media boundary mounts exactly one semantic table or card list. Each book retains its own starting cash, complete total or incomplete known value, unavailable return, zero-baseline percentage meaning, valuation time, oldest applicable source time and dated-stock-mark label. Missing source time for existing holdings is unavailable rather than described as unnecessary.

Loading, genuine zero-book success, initial error, failed background refresh, refresh pending/completion and the ten-book cap have distinct states. Header creation remains visibly disabled while the list is unknown or full; an original unresolved request can still be reviewed/retried. Closing pending/unknown creation preserves its original hook recovery and leaves an overview notice. Closing restores trigger focus after the enabled trigger has committed.

The inline creation form uses existing plain-text validation helpers, normalized Unicode scalar description counts and raw validated input strings. It accepts overlong paste without truncation and exposes field errors through labels, `aria-invalid`, described helper/error text and focused linked summaries. Pending/unknown fields are read-only; recovery retry never invents another key. The existing hook persists the intent before POST. Rate waits and storage/refusal/conflict/closed-original feedback preserve the draft or original attempt. Owner/session changes replace local draft state. No optimistic book, cash or grant is rendered.

Only newly delivered receipts can trigger navigation. The form checks the captured `receipt.isCurrent()` immediately before its callback, uses the returned original result ID (including later renamed replays), and ignores a resolved receipt predating this editor. Navigation carries only result ID/replay status for the detail success message; it contains no names, descriptions, financial values or attempt key. Existing shell destination-heading focus remains authoritative.

`PortfolioMetadataForm` renders authoritative escaped name/description, including preserved line breaks and empty-description copy. Edit/save/discard/empty-to-clear use `usePortfolioManagement(portfolioId)` directly. Dirty stale drafts remain distinct from visibly presented latest metadata and require explicit review. Pending metadata freezes fields/actions; duplicate-name and other refusals retain drafts and expose linked summaries. Successful authoritative save closes editing, announces Portfolio updated and restores Edit portfolio focus. The detail page keys local editor lifetime by owner/root/session and keeps its existing financial/holdings layout and exact baseline behavior. Back to Portfolios is a real link. No deletion/reset/freeze action exists.

## Authorized Management-Hook Repair

An actual page test using the real target, management and valuation hooks reproduced a successful rename followed by `Error: Portfolio target changed` in the unchanged owner/root/session financial query. Concurrent discovery and financial invalidation could launch an old target-bound observer while authority was revoked. A second regression retained an already-running old-name financial refresh and independently proved that stale-only invalidation alone did not abort it.

The parent explicitly authorized the narrowly scoped extension to `usePortfolioManagement.ts` and its tests. A successful PATCH now cancels matching portfolio/history/eventHistory reads before publishing metadata. It rechecks captured current authority and editor revision after that await, preserving later cross-tab review. It then publishes metadata, refreshes discovery, and rechecks the captured scope after that await before any following invalidation. Overview refresh remains owner/session guarded. Same-root financial/History queries are marked stale with `refetchType: "none"`, so unchanged finances do not refetch through an obsolete target closure. A committed current observer's later mount, manual refresh or normal interval still fetches under strict authority. No target guard, original retry identity, cursor validation, financial projector or original-order label was weakened.

The real page tests retain readable $10,000 cash/value after rename/clear, verify escaped renamed metadata, verify cancellation despite a deferred transport ignoring abort, release the obsolete reply, and successfully refresh again. Deferred discovery tests cover owner change and logout/return without subsequent old-scope financial invalidation. Existing cross-tab revision/refusal cases remain passing.

## Verification

Existing Node 24.22.1 and installed dependencies only; no installs, database, private environment, provider or browser operation.

- Task 1 command: initial 10 cases, then 16 passing before its GREEN/refinement; final related suites contain 17 cases.
- Task 2 command: 32 passing during initial integration; final metadata/detail suites contain 38 cases.
- Final affected regression: **15 files, 355 tests passed**, 16.38s. It includes all four new/affected management UI suites, management and target hooks, overview/valuation/History/crypto/stock hooks, History/crypto/stock pages and App.
- After the final overview status/source-copy correction: **5 files, 83 tests passed**, 4.83s (the four component/page suites and management hook).
- Whole frontend `npm run typecheck`: passed on final source.
- Whole frontend `npm run lint`: passed on final source.
- Changed-ten-file Prettier check: passed; final overview-only correction formatted with the same installed formatter.
- `git diff --check`: passed. Stub/threat/deletion scan: no tracked deletion, placeholder, TODO/FIXME, HTML interpretation, new data-fetch effect or unmodeled endpoint/storage/schema surface.

The new cross-tab-during-cancellation assertion passed before the additional post-cancellation editor-revision recheck; it is retained coverage, not claimed as a separate demonstrated RED defect. An early deferred discovery test assumed exactly two GETs; the existing metadata broadcast legitimately caused another discovery request, so the test now gates on the deferred stage rather than a fictitious exact request count. The separate real-page and pending-response RED failures remain independently demonstrated.

## Deviations from Plan

**[Rule 1/2 — Correctness] Repair metadata/financial invalidation ordering.** Found during Task 2's actual rename/clear integration. Parent authorized the two additional hook files. Fixed in `0d9f9d8`; demonstrated by committed real-page/pending-read regressions and covered by the final 355-case run. No architecture, library, network endpoint or permission boundary changed.

Routine implementation corrections included restoring focus after a disabled trigger becomes enabled, letting linked error-summary focus run after native autofocus, preserving recovered input after definitive refusal and refusing an old receipt on a new editor mount. These are part of the planned form/focus/recovery requirements rather than new features.

## Known Stubs

None. Empty names/descriptions are real unsubmitted drafts or intentional empty metadata; unavailable values come from guarded hooks. The overview component is complete but its route/shell mounting belongs to Plan 13, as assigned. It is not replaced by mock product data.

## Limits and Handoff

Parent owns STATE, ROADMAP, REQUIREMENTS, UI contracts and independent reviews. None was edited or staged here; requirement IDs above record this plan's implementation contribution, not whole-phase acceptance. Parent must apply shared state updates after this committed summary.

Plan 13 must mount the exported default `PortfoliosPage` at `/portfolios` without a selected-target boundary and integrate navigation/switcher as planned. Creation callback already navigates to the captured returned ID; detail renders its creation/replay status and relies on existing shell h1 focus. Metadata detail card is already mounted beside the existing context. No new registry, design-system file, token, font, palette or dependency was added.

Actual browser multi-width/reflow/keyboard journeys remain Plan 16. Owner UI and actual native desktop 200% zoom acceptance remain Plan 18. This work claims component/hook tests only, not visual acceptance, full coverage/security/recovery qualification or phase completion.

No package/lock/image/Python pin, live provider admission, private `.env`, production, push or merge changed. Preserve issue35's exact accepted-risk expiry **2026-12-17T00:00:00Z**, approved Python pin **20261111**, Phase7 live stock admissions OFF and unrelated `.claude/`. The existing keep-local publication preference remains.

## Self-Check: PASSED

All ten source/test paths and this summary exist. All nine named task/refinement commits resolve and RED precedes GREEN. Final affected/focused and static checks pass; no tracked deletion or new generated untracked artifact was introduced. Only unrelated `.claude/` remains untracked. Independent parent review, global state bookkeeping and later browser/owner acceptance remain pending.

## Independent Review CR-01 Repair

The independent review identified a routed lifetime blocker that the initial immediate-discovery tests did not exercise: discovery invalidation makes the unchanged target boundary unmount its financial Outlet. With the editor query's zero-GC lifetime, a deferred discovery request collected the dirty draft, required review and local successful-save feedback. The parent explicitly authorized the minimal metadata-only boundary extension in addition to the existing Plan 12 hook/form/test files. The parent-owned review remains untouched.

RED `09214df` adds actual `PortfolioTargetBoundary` + `PortfolioPage` + real management/target/query-hook tests. Both dirty cross-tab and focus-plus-explicit-discovery-revalidation cases defer discovery through a 25ms timer turn; they independently fail when the editor fields disappear after the returned authoritative statement. The delayed successful-PATCH case independently fails because Portfolio updated is absent after remount. These are component-level routed tests with controlled HTTP responses, not actual browser or owner acceptance.

The GREEN repair introduces `usePortfolioMetadataLifetime(portfolioId, status, pathname)` in the existing management module. The boundary invokes it before its existing conditional Outlet rendering. Its disabled query observes only the existing metadata editor record; it performs no fetch, broadcast, financial read or financial rendering. `gcTime: 0` is retained. A single route lease is bound to the captured owner/session/root and pathname by token identity. Explicit cleanup removes the editor query on true route/root/session departure; refusal/unavailability/error clears retained editor state. Loading of the same route keeps the observer and marks dirty drafts for review. Metadata is authoritatively fetched by the existing management hook when its form remounts; an accepted response clears only the outstanding-fetch flag and does not remove required review.

Successful-save feedback is one bounded boolean in that same editor record. It is published only after discovery returns and only when the original management scope is still current or the exact captured owner/root/session/route lease remains active. Owner/session checks still run after the await. The form handles a newly delivered or remounted success marker, waits for the actual enabled Edit control and current metadata, restores focus once, then acknowledges the marker. No receipt, financial value, token, browser storage or additional private metadata is retained by the lease. Earlier creation storage and strict original-order guards are unchanged.

The boundary continues to revoke target/action authority synchronously and unmount financial children while discovery is pending. No `isCurrent` check, unavailable-target refusal, stock proof, root-bound History cursor or original-retry guard is relaxed. The earlier cancellation → captured guard → discovery → captured guard → stale-only financial invalidation ordering remains in place. A matching route lease only permits metadata completion bookkeeping across the intended temporary Outlet absence; it cannot authorize a trade, financial projection or sibling route.

Final new routed coverage consists of **10 cases**: cross-tab dirty draft retention; focus plus explicit discovery revalidation retention; delayed-save success/focus; no late-save feedback after logout, owner change or logout/return; draft cleanup on logout, root change, same-root History route departure or unavailable target. Tests assert absence of the Cash region during revoked discovery, retained original text plus latest authoritative metadata and review-blocked Save after renewal, successful focus restoration, and no retained old draft/success flag after departure.

Final verification:

- Four focused suites: **95 passed**, 5.87s.
- Sixteen affected suites: **384 passed**, 16.56s, including all 19 existing boundary cases and the earlier financial-read/creation/original-order regressions.
- Whole frontend `npm run typecheck` and `npm run lint`: passed.
- Four changed-file Prettier check and `git diff --check`: passed.
- Four changed source/test files: `usePortfolioManagement.ts`, `PortfolioMetadataForm.tsx`, `PortfolioTargetBoundary.tsx`, `PortfolioPage.test.tsx`. No existing boundary-test fixture adjustment was necessary.

The implementation used the existing session update helper to comply with the repository's React immutability lint rule. The focus test explicitly invalidates discovery alongside the focus event; it does not claim that an ordinary focus event alone always unmounts this boundary. No arbitrary production retention delay or infinite editor cache was added. No new endpoint, fetch effect, storage mechanism, dependency, schema or unmodeled trust surface was introduced.

Plan 13 inherits the pathname-scoped metadata-only boundary lease; it must preserve it while adding navigation/switcher integration. Parent global state, review, later browser/native200/owner acceptance, publication and all original provider/accepted-risk boundaries remain unchanged. Repair work took approximately 8 minutes.

### Repair Self-Check: PASSED

All four changed paths exist, committed RED precedes GREEN, and the final 384-case affected regression and static checks pass. No tracked deletion was introduced. The parent-owned untracked review and unrelated `.claude/` were left untouched. The repaired plan now has eleven source/test paths in its cumulative ownership; the initial ten-file counts above remain the historical initial execution record.

## Independent Review CR-02 Repair

The second independent review found a different ordering: PATCH is still pending when same-root discovery revalidation unmounts the form. The lease correctly retained the editor, but its pending flag survived the controller abort; the inactive old handler returned without clearing it. Review, Save and Discard remained disabled indefinitely. CR-01's successful-PATCH-before-discovery tests could not cover this ordering. The parent explicitly authorized this bounded second repair; its review remains untouched.

RED `16b433d` defers the actual routed page's PATCH before triggering the same-root metadata event and deferred discovery. Abort-aware rejection and a transport that ignores abort both independently fail because the restored Review button is disabled. The separate logout control passes before the repair. A fourth final regression starts a newer explicitly reviewed PATCH before delivering the obsolete first response.

The repair changes only `usePortfolioManagement.ts` and `PortfolioPage.test.tsx`. Each save captures an immutable operation token containing its starting editor revision and exact route lease; the editor and originating scope retain that same token. Scope cleanup, before aborting its controllers, transitions only its matching still-pending operation under the exact captured owner/root/session/path lease to non-pending, review-required and awaiting authoritative metadata. It retains the draft, increments revision, records an unknown/interrupted-save explanation and revokes that operation token. True departure/privacy cleanup is unchanged.

The remounted existing metadata query must successfully obtain authoritative metadata before clearing the outstanding-fetch flag. Review remains required, Save stays blocked until explicit review, and Discard becomes usable. No automatic PATCH retry occurs. Response, catch and post-await completion handling require the exact operation token as well as captured current authority/retained lease. Editing or replacing an operation revokes its earlier token. An old abort rejection or late response can therefore neither publish success nor clear a newer save's pending state. The operation is removed from its scope's active set in `finally`.

Final real routed coverage verifies both abort behaviors, current latest metadata plus the retained draft, enabled Review/Discard with review-blocked Save, exactly one PATCH before explicit action, no obsolete success feedback, successful discard, logout clearing, and an obsolete first reply leaving a second explicit save pending until that second save itself resolves. Existing CR-01 delayed-success focus and all financial/original-order guards remain covered.

- Four focused suites: **99 passed**, 6.52s.
- Sixteen affected suites: **388 passed**, 15.71s.
- Whole frontend typing/lint, two-file Prettier and diff checks: passed.
- No boundary, route, creation storage, provider, dependency, financial guard, global planning state or parent review change. No production, push or merge operation.

### CR-02 Repair Self-Check: PASSED

Both changed paths exist, RED is committed before GREEN and the final 388-case affected regression/static checks pass. No tracked deletion or generated artifact was introduced. Parent-owned review and unrelated `.claude/` remain untouched. Independent re-review remains the parent's next step; browser/native200/owner acceptance and the original publication/accepted-risk boundaries remain pending or unchanged as previously recorded.
