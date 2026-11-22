---
phase: 13-create-and-compare-independent-strategies
plan: "12"
reviewed: 2026-11-18T12:35:12Z
initial_reviewed: 2026-11-18T12:19:12Z
depth: standard
diff_base: 37e62ef
diff_head: 3266b5c
initial_diff_head: 2f290ba
repair_diff_base: 2f290ba
second_repair_diff_base: 0605225
files_reviewed: 11
files_reviewed_list:
  - frontend/src/components/PortfolioCreateForm.tsx
  - frontend/src/components/PortfolioCreateForm.test.tsx
  - frontend/src/components/PortfolioMetadataForm.tsx
  - frontend/src/components/PortfolioMetadataForm.test.tsx
  - frontend/src/pages/PortfoliosPage.tsx
  - frontend/src/pages/PortfoliosPage.test.tsx
  - frontend/src/pages/PortfolioPage.tsx
  - frontend/src/pages/PortfolioPage.test.tsx
  - frontend/src/hooks/usePortfolioManagement.ts
  - frontend/src/hooks/usePortfolioManagement.test.tsx
  - frontend/src/components/PortfolioTargetBoundary.tsx
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
resolved_findings:
  critical: 2
  total: 2
status: clean
---

# Phase 13 Plan 12: Code Review Report

**Depth:** standard with critical owner/session/editor lifecycle tracing  
**Files reviewed:** 11 cumulative  
**Status:** clean — both blockers resolved

## Summary

Initial review covered the ten source/test files in `37e62ef..2f290ba`. Re-review covered all four repair source/test files in `2f290ba..0605225` and both source/test files in the second bounded repair `0605225..3266b5c`. Both CR-01 and CR-02 are resolved. No remaining concrete BLOCKER or WARNING was established in these focused repair ranges. Original findings are preserved as resolved history.

## Narrative Findings (AI reviewer)

## Second Repair Disposition

**CR-02 — Resolved by `b2018e4`.** Each save now installs an immutable operation token in its editor and originating scope. Before aborting its controllers, scope cleanup checks that the exact operation is still pending under the exact retained owner/root/session/route lease. It clears pending, revokes the operation, preserves the draft, increments revision and requires both authoritative metadata renewal and explicit review. True departure does not retain the editor. The remounted authenticated metadata GET clears awaitingFetch; it does not clear reviewRequired or automatically retry PATCH.

Every asynchronous response/catch/publication continuation checks its operation identity in addition to the existing authority guards. An old abort rejection or ignored-abort response cannot publish success, update metadata, or clear a replacement save's pending state. Editing revokes the previous token, completion revokes its own token, and finally removes it from the originating scope set. No financial guard, boundary rendering or network entrypoint changed in this second repair.

Four real routed cases inspect abort-aware rejection, ignored-abort late response, logout cleanup, and an explicitly reviewed replacement PATCH kept pending while the original response arrives. They preserve the retained draft/latest authoritative metadata, usable Review/Discard, review-blocked Save and no obsolete success or automatic retry. The summary records actual RED `16b433d`, GREEN `b2018e4`, 99 focused cases and 388 affected cases plus static checks; those sources and execution receipts were inspected without rerunning tests. `git diff --check 0605225..3266b5c` passed.

## Second Critical Issue — Resolved History

### CR-02: BLOCKER — A pending PATCH survives revalidation as a permanently pending editor

**Disposition:** Resolved by `b2018e4`; original severity and first-repair source evidence retained below.

**File:** `/home/YokaiExchange/frontend/src/hooks/usePortfolioManagement.ts:170-171`  
**Related lines:** scope cleanup at 322-324; save sets pending at 482, exits on inactive scope at 485 and 530; returned metadataPending at 553.

**Issue:** The new lease preserves the complete Editor through temporary Outlet unmount, including `pending: true`. If a same-root cross-tab event or explicit discovery refresh occurs while PATCH is still pending, the boundary unmounts the form. Management cleanup revokes its scope and aborts the PATCH controller. Both success and error handlers then return on `!current()` without clearing pending. The lease's loading transition only adds revision/reviewRequired. A fresh metadata GET after remount clears awaitingFetch but never pending. The form therefore remains in Saving changes forever: Review, Save and Discard are all disabled. This occurs whether transport rejects on abort or ignores abort and later delivers a response.

**Fix:** Explicitly transition an interrupted save retained by the exact current owner/root/session/route lease into a non-pending, review-required unknown outcome, retain its draft, and require authoritative metadata renewal before allowing review/save. Do not let a departed root/session's callback mutate the next editor, publish an old response as success, or automatically retry PATCH. Ensure an old operation cannot later clear a newer operation's pending flag. Add a real `PortfolioTargetBoundary` + page + hook regression that defers PATCH first, triggers same-root discovery revalidation, waits through Outlet unmount, releases discovery/current metadata and rejects or releases the obsolete PATCH. Assert draft retained, latest metadata shown, no success from the obsolete reply, and Review/Discard usable with Save blocked until explicit review. Existing new delayed-success tests defer discovery only after PATCH has already resolved and cannot detect this ordering.

## Repair Disposition

**CR-01 — Resolved by `fd7cf13`.** The boundary now observes only the disabled editor query before its unchanged conditional Outlet rendering. Zero GC remains, but an active owner/root/session/pathname lease keeps the record observed across temporary loading and explicitly removes or clears it on true departure/refusal. Dirty loading marks required review; remounted management fetches authoritative metadata. Guarded one-shot success state survives deferred post-PATCH discovery and is consumed after restoring the real Edit control. No financial child or action authority is retained under loading, no extra network query is introduced, and original target/trade/proof guards remain unchanged.

The three actual routed RED failures (`09214df`) and ten routed repair cases address dirty cross-tab/focus-plus-revalidation, delayed-save announcement/focus, departure/unavailability and owner/session refusal. Their sources and the summary's 95-focused/384-affected execution receipts were inspected, not rerun. CR-02 is a different ordering not covered by those cases.

## Initial Critical Issue — Resolved History

### CR-01: BLOCKER — Target revalidation unmounts and discards the dirty metadata editor

**Disposition:** Resolved by `fd7cf13`; original source evidence and severity retained below.

**File:** `/home/YokaiExchange/frontend/src/pages/PortfolioPage.tsx:55-58`  
**Related paths:** `/home/YokaiExchange/frontend/src/hooks/usePortfolioManagement.ts:128-133`, `/home/YokaiExchange/frontend/src/hooks/usePortfolioTarget.ts:151-156,210-215`, `/home/YokaiExchange/frontend/src/components/PortfolioTargetBoundary.tsx:54-60`.

**Issue:** The newly integrated metadata editor is inside the financial target boundary. A same-root metadata event synchronously invalidates discovery. While that authenticated discovery GET remains pending, `usePortfolioTarget` returns `loading` and the boundary replaces its Outlet with a loading card. This unmounts `PortfolioPage` and the editor. Its dirty draft/review state is held exclusively in an editor query configured with `gcTime: 0`; once the inactive-query collection timer runs, the draft is removed. A later successful discovery mounts a fresh editor with `emptyEditor()`. The user's text and required stale-draft review are gone.

Concrete ordering: open real detail, edit name/description, receive another tab's same-root event, defer `/api/v2/portfolios` through at least one timer turn, then release authoritative discovery. The page must retain the original draft and require review against the newly fetched metadata; current code instead destroys the editor during that wait. Window-focus discovery refresh has the same lifetime problem. The successful PATCH path also broadcasts at `usePortfolioManagement.ts:437` and awaits discovery, so delayed discovery can destroy its local success announcement/focus state before the form observes completion.

The component stale-draft test mocks the hook, and the real-hook event tests mount without `PortfolioTargetBoundary`. The actual detail rename tests resolve discovery immediately. They do not exercise this deferred boundary transition.

**Fix:** Preserve owner/root/session-scoped metadata editor state across temporary discovery revalidation, while continuing to revoke financial/action authority synchronously. Keep that state outside the disappearing Outlet or give it an explicit session-bound lifetime and cleanup on true route/root/owner/session departure; a short arbitrary GC delay is insufficient. Preserve successful-save feedback/focus through the same transition. Do not weaken target `isCurrent`, retain a financial child under invalid authority, or persist private drafts across logout. Add a real routed detail regression with actual management/target hooks, a dirty draft, a same-root cross-tab event, deferred discovery long enough for zero-GC collection, and final assertions for retained draft/latest metadata/review-blocked Save. Add a deferred successful-PATCH discovery case asserting success feedback and restored Edit focus, plus owner/session-change refusal controls.

## Review Limits

Independent source review only; no tests, browser/runtime operations, dependencies, providers, private environment access, source edits or commits were performed. Only this review artifact was written. The recorded component/hook execution receipts were inspected, not rerun. Plan 13 routing/switcher, Plan 16 browser journeys and Plan 18 owner/native 200% acceptance remain pending and are not credited here. Existing original-order guards, separate financial snapshots/shared safety proof, retained recovery and accepted-risk boundaries remain outside any proposed weakening.

---

_Reviewer: gsd-code-reviewer_  
_Depth: standard_
