---
phase: 13-create-and-compare-independent-strategies
plan: "09"
subsystem: frontend
tags: [react, tanstack-query, session-storage, idempotency, metadata]
requires:
  - phase: 13-08
    provides: Strict raw-original creation and metadata clients
provides:
  - One bounded opaque-owner-bound original creation recovery record before POST
  - Captured owner/session/root guards for receipts and metadata mutations
  - Identity-only cross-tab invalidation with authoritative metadata review
affects: [13-10, 13-11, 13-12, 13-13, 13-15, 13-16, 13-17]
tech-stack:
  added: []
  patterns: [captured lifecycle receipts, frozen session recovery, advisory identity-only events]
key-files:
  created:
    - frontend/src/lib/portfolioCreationAttempt.ts
    - frontend/src/lib/portfolioCreationAttempt.test.ts
    - frontend/src/hooks/usePortfolioManagement.ts
    - frontend/src/hooks/usePortfolioManagement.test.tsx
    - frontend/src/lib/portfolioMetadataEvents.ts
    - frontend/src/lib/portfolioMetadataEvents.test.ts
  modified: []
key-decisions:
  - "Derive an opaque owner binding from a random same-tab lifecycle nonce and authenticated identity in memory; never persist email or authentication material."
  - "Cross-tab source scopes are random emitter nonces, not owner authority: messages only invalidate an already selected root for a current-owner authoritative GET."
  - "Creation receipts carry the original captured isCurrent guard; consumers must check it before navigation or announcements and must not fabricate a new epoch."
requirements-completed: [PMGT-01, PMGT-02, PMGT-06, PFUND-02, PCTX-02]
duration: 15min
completed: 2026-11-18
---

# Phase 13 Plan 09: Refresh Recovery and Metadata Coherence Summary

**Frozen raw creation originals survive same-tab refresh for explicit same-key retry, while identity-only metadata changes preserve drafts for authoritative review.**

## Performance and Task Commits

- Two of two tasks complete; six source/test files and this summary.
- Task 1 RED `5767b6a`: both recovery suites failed on absent implementation imports.
- Task 1 GREEN `673c00a`: original persistence, explicit recovery and owner/session guards; 15 focused cases passed with full frontend typecheck and changed-source lint.
- Task 2 RED `edaf875`: metadata suites failed on the absent events module.
- Task 2 GREEN `9386cdf`: authoritative metadata editing and identity-only invalidation; final new suites pass 29 cases.
- Final 10-suite affected regression passes **184 tests** in 3.33s, including creation storage/hooks/events, strict management/overview clients, target guards, auth clients/mutations, private query clearing and existing crypto trade originals.
- Full frontend `npm run typecheck`, changed-six-file ESLint, Prettier and `git diff --check` pass. No tracked file deletions.

Parent owns STATE/ROADMAP/REQUIREMENTS and independent review. This executor did not edit or stage those files. Requirement IDs above record this plan's contribution rather than whole-requirement acceptance.

## Creation Recovery Contract

`portfolioCreationAttempt.ts` exports `CREATION_STORAGE_KEY`, `openCreationRecovery(owner, isCurrent?)`, `clearCreationRecovery()` and `CreationRecovery`. The opened recovery exposes `attempt`, `persist(input)` and `resolve()`.

One strict versioned envelope contains only a random lifecycle UUID nonce, SHA-256 opaque owner binding and at most one original UUIDv4/name/description request. The email is used transiently to compare authenticated ownership and is never persisted. No tokens, financial values, receipts, URLs, logs or localStorage are involved. The envelope is limited to 16000 characters; exact keys, UUIDs, binding encoding, raw Unicode names/descriptions and payload bounds are checked on read and write. Corrupt/oversized storage blocks new creation rather than discarding an uncertain original. Concurrent openers serialize so one cannot overwrite another observer's outstanding original. A record from another authenticated owner is removed before a new lifecycle is opened. This metadata never authorizes a request: actual server authentication remains authoritative.

`persist` freezes original **raw** strings, verifies the current lifecycle and reads back successful persistence before POST. Equivalent normalized names cannot change the original. Storage failure blocks transport and leaves recovery safe. Mount, focus, login, navigation and count/name changes never submit or allocate a replacement key. A fresh client with identity initially loading preserves the record until authoritative identity resolves; a matching owner restores phase `unknown` for explicit Retry only.

Unknown service/network/malformed-success outcomes and creation-key conflicts retain the original UUID/payload. A successful result or definitive refusal clears only the attempt. Refusal allows a later explicitly corrected intent; a closed replay ends `unavailable` without replacement or navigation. Failure to persist resolution keeps safe original recovery. Unmount/root departure aborts the local request and leaves phase `unknown`, permitting same-original retry even if the old fetch never settles; its operation serial prevents that obsolete callback from overwriting a later receipt.

## Hook Interface and Next-Plan Handoff

`usePortfolioManagement(portfolioId?)` is owner-wide for creation and explicit-root scoped for metadata. It returns:

- `ready`, `creation`, `submitCreation({name, description?})`, `retryCreation()`.
- Creation phases `editing | submitting | unknown | resolved | unavailable`, original `attempt`, safe `error`, and optional `receipt: {metadata, isCurrent}`. Actions return handled promises; unknown/refusal state stays observable. **Check the receipt's captured `isCurrent()` before navigation/announcement.** Do not rebuild an epoch from the current session after the callback.
- `metadata`, `metadataError`, `metadataPending`, `draft`, `reviewRequired`.
- `editMetadata(patch)`, `reviewMetadata()`, `discardMetadata()`, `saveMetadata()`, `refreshMetadata()`.

Metadata uses the strict API through TanStack Query/mutations with aborts, no retries, owner/root/session keys and captured query-object guards. Editing accepts a partial name/description patch; an empty description clears it. Failed saves preserve drafts. Ambiguous PATCH performs a same-ID authoritative refetch, sets review required and never automatically retries PATCH. Review remains blocked during a failed/pending authoritative refresh. A cross-tab/focus invalidation while PATCH is in flight increments draft revision, preserving the draft for review instead of applying an obsolete success. Successful mutations invalidate identity summaries, overview and root detail/history label queries; no money calculation or mutation is introduced.

Observed logout, owner change and authentication loss synchronously revoke old captured handles, abort outstanding work, clear creation persistence and cooperate with existing private-query removal. Root change/unmount revokes rendered metadata actions and receipts. Same-root label changes do not reset the creation original or touch existing crypto/stock original-order state. Plan 10 still owns the financial target rename/original-order compatibility integration.

## Cross-Tab Protocol

`portfolioMetadataEvents.ts` exports `metadataEvent(value)`, `subscribeMetadataEvents(changed)` and `broadcastMetadataChange(portfolioId)`. The fixed same-origin BroadcastChannel carries exactly `{scope, portfolioId}` with a bounded UUIDv4 emitter scope and canonical bigint string root. Extra names, descriptions, keys, financial values or other fields refuse. A random source scope suppresses duplicate own-tab channel delivery; local listeners still receive invalidation. Receivers match their already selected explicit root and refetch under their own current authentication. Events never set metadata or confer owner authority. Different per-tab recovery nonces therefore do not prevent useful invalidation. Unsupported channels use the window-focus refetch fallback. Listeners/channels are cleaned up on lifecycle/root departure; stale callbacks also check captured current state before action.

## Deviations from Plan

**1. [Rule 1 - Bug] Strengthened initial-authentication and concurrent recovery lifetimes.**
Found while expanding Task 2 lifecycle tests: treating initial unresolved identity as logout could discard reload recovery; concurrent openers could replace a lifecycle nonce; an aborted original response could arrive after a later retry. Distinguished unknown identity from observed logout, serialized storage opening, and added captured operation serials plus regression cases. Files: creation utility/tests and management hook/tests. Verified in final 29 new /184 affected passing cases. Commit `9386cdf`. Scope and persistence contract unchanged.

## Known Stubs

None. Null/empty states represent real editing, signed-out, unavailable or no-draft states. No mock financial projection, placeholder transport or unwired hook data source was introduced.

## Limits and Next Phase Readiness

No component/browser/native zoom/owner acceptance proof, full frontend coverage, database operation, package/pin update, provider call, production operation, push or merge ran. Parent independent review and final phase security/integration/recovery qualification remain pending. Keep existing issue 35 exact accepted-risk scope and deadline **2026-12-17T00:00:00Z**, Python pin **20261111**, and Phase 7 live stock admissions OFF. This plan changes none of them.

## Self-Check: PASSED

All six declared source/test files and the summary exist. RED/GREEN commits `5767b6a`, `673c00a`, `edaf875`, `9386cdf` exist; both required task commands and the final affected regression pass. No stubs prevent the plan goal. New storage/event boundaries match the plan threat register; no additional network/auth/financial authority surface was introduced.
