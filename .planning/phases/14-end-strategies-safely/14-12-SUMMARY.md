---
phase: 14-end-strategies-safely
plan: "12"
subsystem: ui
tags: [react, tanstack-query, deletion, recovery, session-isolation]
requires:
  - phase: 14-11
    provides: Guarded deletion transport and immutable owner-bound recovery storage
provides:
  - Owner/tab deletion lease with explicit original-intent recovery outside financial routes
  - Synchronous original-root quarantine selectors and metadata-write exclusion
  - Current-operation completion receipts for guarded navigation and announcements
affects: [14-13, 14-14, 14-18, 14-19]
tech-stack:
  added: []
  patterns: [QueryClient-scoped external store, immutable recovery intent, explicit retry]
key-files:
  created:
    - frontend/src/hooks/usePortfolioDeletion.ts
    - frontend/src/hooks/usePortfolioDeletion.test.tsx
  modified:
    - frontend/src/hooks/usePortfolioManagement.ts
    - frontend/src/hooks/usePortfolioManagement.test.tsx
key-decisions:
  - Restore recovery outside the financial Outlet; restoration never sends DELETE.
  - Only an exact closure receipt or durable terminal confirmation-name refusal resolves the original marker.
  - Publish root quarantine synchronously after recovery persistence and before transport; sibling metadata remains independent.
  - Completion consumers must recheck receipt.isCurrent before navigation, focus, or announcements.
requirements-completed: []
requirements-progress: [PMGT-03, PMGT-04, PCTX-03, PSAFE-01]
duration: 16min measured between first RED commit and final source commit
completed: 2026-11-19
---

# Phase 14 Plan 12: Independent deletion recovery Summary

**An owner-bound deletion lease preserves the original uncertain request across financial-route teardown, excludes original metadata writes, and exposes current-operation closure receipts.**

## Accomplishments

- Added idle/review/persisting/submitting/unknown/checking/terminal_refusal/closed state with immutable original ID, key, name and policy capture. Storage readback must succeed before DELETE; TanStack mutation retries are disabled.
- Recovery restoration sends no request. An explicit check resubmits exactly the original intent. Active metadata/list presence, transient refusals, auth errors, malformed acknowledgments and interrupted requests cannot resolve an unknown original.
- Logout/owner changes clear the private lease and abort obsolete work. Route and operation scopes prevent captured callbacks, owner return and route return from acting as a newer context. Known closure remains known if list discovery fails.
- Original-root quarantine is published before the network request. Captured metadata edit/review/save functions consult current quarantine synchronously, while sibling metadata editing stays independent. Pending metadata saves exclude deletion; a rename revokes the prior confirmation even if the name later changes back.

## Task commits and TDD evidence

1. Task 1 RED: `e4c6056` — specify original deletion recovery lifetime; initial missing-hook test failed as expected.
2. Task 1 GREEN: `f2ae102` — implement guarded original deletion lease; 19 focused cases passed in 2.64s.
3. Task 2 RED: `77071c1` — captured metadata save after an unknown deletion failed because it issued PATCH.
4. Task 2 GREEN: `5fa9409` — exclude original metadata edits and guard completion callbacks; final whole-source frontend qualification below passes.

Both tasks have ordered RED/GREEN commits. No tracked files were deleted.

## Verification

Stable tested source: `5fa9409` (the checks ran on its unchanged source immediately before the commit).

| Check | Actual result | Evidence under `/tmp/birja-phase14-plan12/` |
| --- | --- | --- |
| Task 1 RED | Expected missing-hook failure | `task1-red.log` |
| Task 1 GREEN | 19 passed, 2.64s | `task1-green-final.log` |
| Task 2 RED | Expected captured-save exclusion failure | `task2-red.log` |
| Real management + deletion integration | 50 passed, 5.00s before three final callback cases | `task2-green-hooks.log` |
| Deletion transport/storage + deletion/management/target/auth hooks | 152 passed in six files, 4.96s | `affected-final.log` |
| Full frontend unit suite | 1,264 passed in 58 files, 22.58s | `full-unit-final.log` |
| Full frontend TypeScript build | Exit 0 | `typecheck-final.log` |
| Four owned files, scoped ESLint | Exit 0 | `lint-final.log` |
| Four owned files, Prettier check | Exit 0 | `prettier-final.log` |
| Git whitespace and tracked deletion checks | Exit 0; no deletions | Execution terminal evidence |

Meaningful cases include persistence/readback failure before sending, reload/focus without automatic DELETE, duplicate confirmation, exact recovery bodies, durable versus nonterminal refusals, Retry-After without automatic retry, abort/unmount, rename-back revocation, same-owner session replacement, owner and route return, late refusal against a newer review, sibling metadata independence, pending-save exclusion, and owner/route changes during closure-list discovery.

One initial Task 2 integration run exposed a synchronous render-notification loop and was interrupted; its replacement completed in 1.43s. No failed or interrupted run is counted as passing evidence. All owned Vitest processes have finished. Tests clean up mounted hooks, QueryClients, session storage, timers and mocks. No DB, browser server, container, provider, production or package resources were created. Existing unrelated `.claude/` remains untouched.

## Plan 13 boundary handoff

Import these concrete exports from `@/hooks/usePortfolioDeletion`:

```ts
usePortfolioDeletion(portfolioId?: string, options?: {
  route?: string;
  onClosed?: (receipt: PortfolioDeletionCompletion) => void;
})
subscribePortfolioDeletion(client: QueryClient, changed: () => void)
portfolioDeletionRevision(client: QueryClient)
portfolioDeletionAuthorityReady(client: QueryClient, owner: string)
isPortfolioDeletionQuarantined(client: QueryClient, owner: string, id: string)
```

Mount the hook's owner/tab lifetime **outside the financial Outlet**. Subscribe to the revision with `useSyncExternalStore`; snapshots are primitive monotonically incrementing versions. Wait for `portfolioDeletionAuthorityReady` before granting private financial authority after authentication/reload. A storage restoration error leaves readiness false and the hook exposes `retryRecoveryStorage()` for explicit recovery. The storage marker contains metadata only and grants no server authority.

Use `isPortfolioDeletionQuarantined` for the exact owner/root to mask original financial data, previews and actions immediately on confirmed submission, including during submitting/checking/unknown. The signal is synchronous before transport. Do not block sibling reads/trading or creation recovery merely because another root has an unresolved deletion. Boundary/cache integration is Plan 13's remaining work; this plan does not claim it is wired yet.

Known closure retains quarantine for its original root. A durable confirmation-name refusal resolves the marker, invalidates old metadata, and retains quarantine until a fresh usable owned metadata response arrives. An unknown result never releases quarantine from a GET/list response.

## Plan 14 UI handoff

The hook returns `ready`, `deletion`, `canConfirm`, `canCheck`, `reviewDeletion(metadata)`, `cancelReview()`, `confirmDeletion()`, `checkDeletionResult()` and `retryRecoveryStorage()`. Methods must be invoked from the current rendered context. `deletion` contains phase, review, attempt, reviewRequired, sanitized error, retryAt and optional receipt. Metadata-only recovery may use the captured original ID/name; it must not revive financial data.

`reviewDeletion` checks a fresh owned metadata cache entry and no pending/uncertain metadata operation; it returns whether review opened. Review is separate from submission. Confirmation captures the exact immutable review, persists it, then sends. `checkDeletionResult` is an explicit click and respects Retry-After; no focus/reload/timer automatic DELETE is implemented. A second deletion cannot replace an unresolved original.

`PortfolioDeletionCompletion` carries `{ portfolioId, confirmationName, isCurrent }`. Check `isCurrent()` immediately before every deferred navigation/focus/announcement. The hook only invokes `onClosed` while current; callbacks must retain the guard across their own asynchronous work. A list discovery error can coexist with known closed state and must not offer a new original deletion.

`usePortfolioManagement` additionally exposes `metadataBlocked`; original edit/review/save methods enforce the same quarantine even through captured handlers. Siblings remain independent. Creation recovery uses its existing separate key and unchanged state machine.

## Decisions and deviations

- Followed the planned architecture and existing QueryClient-scoped session patterns; no new package, network endpoint or shared global service was introduced.
- **[Rule 1 — Bug]** Actual management integration revealed that QueryCache observer-options notifications could feed external-store rerenders back into the editor. The deletion listener now reacts only to actual query updates/removals; the concrete integration regression and full suite pass. This stayed within the four owned files.
- API behavior was checked against official [TanStack mutation documentation](https://tanstack.com/query/v5/docs/framework/react/reference/useMutation) and [React external-store documentation](https://react.dev/reference/react/useSyncExternalStore), alongside installed source and retained project patterns.
- Parent orchestrator owns STATE/ROADMAP/requirement updates; this executor deliberately leaves those files untouched. Requirement IDs above describe this plan's contributions, not phase-wide acceptance.

## Remaining gates

Plan 13 must integrate actual financial quarantine/cache boundaries; Plan 14 must build the accepted UI contract on these hooks. Independent review, whole-source recovery/security qualification (18), and real human UI/native 200% acceptance (19) remain later gates. No human acceptance, live provider activation, push, merge or deployment is claimed.

No blocking stubs or new threat surface outside the plan's authenticated-browser/recovery-storage boundary were found.

## Self-Check: PASSED

All four source/test files exist; all four task commit hashes exist; source is committed and unchanged after passing checks. Only this summary and the pre-existing unrelated `.claude/` were untracked before the summary commit.

## Independent review repair — CR-01 and CR-02

The original review at `14-12-REVIEW.md` identified two valid blockers in the initial source: metadata writes were allowed before recovery initialization, and draft/editing state was not mutually exclusive with named deletion review. Its findings remain preserved as the original review record. The earlier passing test counts did not prove these interleavings.

- **RED `bfc94ba`:** six deterministic cases failed: deferred recovery digest and corrupt recovery storage with a direct management consumer, open named review versus captured metadata handlers, unsaved name and description drafts, and unresolved metadata review state. Log: `/tmp/birja-phase14-plan12/review-red.log` (six failures, 1.93s).
- **GREEN `302a9de`:** metadata actions now require known owner-bound recovery and no exact-root deletion review/quarantine. Management itself mounts the existing owner-only deletion hook lease, so direct consumers initialize and subscribe without depending on future UI placement. No new store, package, network endpoint, or file was needed.
- `metadataBusy` now includes non-null drafts and `reviewRequired`, as well as pending/uncertain saves. Both entering deletion and captured confirmation recheck it. Named pre-submit review blocks original metadata editing separately from financial quarantine; Cancel releases that exclusion. A terminal original refusal releases metadata only after fresh same-root authority arrives. Sibling editing remains available after recovery readiness, including following a restored unknown original.
- Corrected the earlier contradictory successful test that created an unsaved draft before confirming deletion. Pending-save coverage now begins metadata saving first and proves deletion refusal until reconciliation. Error-response fixtures now include the actual JSON content type required by the guarded transport; a terminal-refusal test initially lacked it and was corrected without changing production parsing.
- Captured edit/review/save calls are refused during pending/corrupt recovery and named deletion review. Additional coverage exercises a draft appearing after captured confirmation, safe Cancel, explicit recovery retry after a synthetic storage repair, fresh metadata after terminal refusal, and recovered original/sibling isolation. Existing owner/route-return and obsolete callback cases still pass.

### Updated exports and consumer contract

New exact-root export from `@/hooks/usePortfolioDeletion`:

```ts
isPortfolioDeletionMetadataBlocked(client: QueryClient, owner: string, id: string): boolean
```

It returns true until recovery is ready, during this root's named review, or while this root is quarantined. Use it for metadata editing only; do not use it to quarantine pre-submit financial content. Existing Plan 13 financial readiness/quarantine exports are unchanged.

`usePortfolioManagement` now also returns `deletionRecoveryError` and `retryDeletionRecovery()`. The latter is an explicit current-management-scope guarded storage retry, never a DELETE. Existing `metadataBlocked` and all edit/review/save action guards consume the stronger predicate. Legitimate direct management consumers initialize automatically and become writable after successful safe recovery; a recovery error remains fail-closed and has an explicit retry surface.

### Repair qualification

Tested source is `302a9de`; no source changes followed these checks:

| Check | Actual result | Log under `/tmp/birja-phase14-plan12/` |
| --- | --- | --- |
| Management/deletion hooks before final explicit retry/sibling assertions | 61 passed, 5.42s | `review-green-hooks-final.log` |
| Transport/storage/management/deletion/target/auth affected set | 160 passed in six files, 5.92s | `review-affected-final.log` |
| Full frontend suite including final retry and restored-sibling assertions | 1,272 passed in 58 files, 24.79s | `review-full-unit-final.log` |
| Full frontend typecheck | Exit 0 | `review-typecheck-final.log` |
| Scoped ESLint / Prettier | Exit 0 / all matched files formatted | `review-lint-final.log`, `review-prettier-final.log` |
| Whitespace / tracked deletion checks | Clean / no tracked deletions | Execution terminal evidence |

The initial repair run's two draft-observer assertions required waiting for TanStack observer notification; those test assertions were corrected before the final runs. All owned test processes completed and standard hook/storage/mock cleanup ran. No DB/provider/production operations, installations, publication or gate changes occurred. Parent-owned requirement progress fields remain preserved; whole-phase requirements are not marked complete. Independent re-review of both original findings is still required before the next wave.

### Repair self-check: PASSED

RED/GREEN commits and all four owned source/test files exist. The original review and parent planning files remain untouched; only the authorized summary append accompanies source repair evidence.
