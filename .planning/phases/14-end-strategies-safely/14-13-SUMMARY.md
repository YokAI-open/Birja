---
phase: 14-end-strategies-safely
plan: "13"
subsystem: ui
tags: [react, tanstack-query, lifecycle, quarantine, recovery, session-isolation]
requires:
  - phase: 14-12
    provides: Owner-bound deletion recovery, readiness and synchronous original-root quarantine
provides:
  - Identity-only lifecycle advisories with authoritative revalidation
  - Financial target, overview and switcher masking for uncertain or unavailable originals
  - Recovery generation fencing across identity GC and replacement QueryClients
  - Safe removed-control focus and explicit initialization-error recovery
affects: [14-14, 14-15, 14-17, 14-18, 14-19]
tech-stack:
  added: []
  patterns: [Revocable financial authority, advisory lifecycle hints, owner-bound recovery generation]
key-files:
  created: []
  modified:
    - frontend/src/lib/portfolioMetadataEvents.ts
    - frontend/src/lib/portfolioMetadataEvents.test.ts
    - frontend/src/hooks/usePortfolioTarget.ts
    - frontend/src/hooks/usePortfolioTarget.test.tsx
    - frontend/src/hooks/usePortfolioOverview.ts
    - frontend/src/hooks/usePortfolioOverview.test.tsx
    - frontend/src/components/PortfolioTargetBoundary.tsx
    - frontend/src/components/PortfolioTargetBoundary.test.tsx
    - frontend/src/components/PortfolioSwitcher.tsx
    - frontend/src/components/PortfolioSwitcher.test.tsx
    - frontend/src/hooks/usePortfolioDeletion.ts
    - frontend/src/hooks/usePortfolioDeletion.test.tsx
    - frontend/src/hooks/portfolioCrypto.test.tsx
    - frontend/src/hooks/portfolioStock.test.tsx
    - frontend/src/pages/TradePage.test.tsx
    - frontend/src/App.test.tsx
    - frontend/src/test/setup.ts
key-decisions:
  - Lifecycle messages revoke handles but require fresh owned-active server proof; they never establish permanent closed authority.
  - An active discovery response cannot release the original local unknown deletion quarantine.
  - Identity cache absence revokes memory without deleting durable recovery; authenticated logout remains distinct.
  - A genuine replacement client mount retires the prior generation permanently, including same-owner A-to-B-to-A returns.
  - Preserve financial execution-404 attempts privately as unknown while unavailable routes expose only the approved unresolved-order boolean.
requirements-completed: []
requirements-progress: [PCTX-03, PSAFE-01, PFIN-06]
duration: 23min from first RED receipt to qualified source commit
completed: 2026-11-19
---

# Phase 14 Plan 13: Revoked financial authority Summary

**Confirmed deletion masks its original finances before transport; advisory hints require fresh server proof, and uncertain originals survive cache eviction without reviving obsolete financial handles.**

## Accomplishments

- Extended the existing channel with the finite `kind: "lifecycle"` variant. Legacy metadata messages remain accepted; extra names, keys, amounts and claimed closed authority are rejected. Listeners and channels retain explicit cleanup and focus revalidation remains available.
- Publish lifecycle hints after durable original-intent persistence and local quarantine, and after verified closure, under captured owner/session guards. Target handles consult quarantine synchronously before financial transport or publication.
- Initialize deletion recovery outside the financial Outlet. Readiness gates private target discovery, target authority and overview data. Explicit storage retry is available without silently sending DELETE; initialization errors do not become endless loading.
- Mask the financial Outlet, overview row and switcher choice for the exact quarantined root. Generic unavailable routes retain the overview link and only the previously approved original unresolved-order boolean. They expose no retained name, description, amount, receipt or executable retry.
- Fresh authenticated proof can restore a still-active row after a forged or stale advisory. Local unknown quarantine remains independent of active GET/list responses. A late response captured before a lifecycle revision cannot restore authority.
- Preserve independent siblings and explicit navigation. Legacy discovery does not redirect to a sibling merely because another root is masked. A masked final row plus failed refresh is not presented as an authoritative zero count.
- Keep focus reachable when a focused financial control disappears, while preserving focus on a still-connected external control. Existing tokens, typography and layout remain in use; the financial wrapper uses `display: contents`.
- Strengthened existing crypto/stock execution-404 cases: the hidden state retains the original immutable root, key and payload as unknown, while visible attempts/receipts are removed and further submission is blocked. Existing trade-hook classification required no source change.

## Task commits and TDD evidence

| Commit | Evidence or result |
|---|---|
| `31de6e8` | Task 1 RED: finite lifecycle event rejected; initial deletion fixture also failed. |
| `8618113` | Corrected fixture and advisory recovery regression. A corrected replay against original target source proves unknown deletion incorrectly returns to ready after active discovery. |
| `d6851c9` | Task 1 GREEN: readiness/quarantine, lifecycle publication and accepted switcher projection. |
| `eac0484` | Task 2 RED: original overview row remains visible and removed financial control loses safe focus. |
| `8b6da15` | RED: identity-query removal erases a real persisted unknown marker. |
| `3799a81` | RED: obsolete client logout erases a newer client's original marker. |
| `c0795ff` | Initial lifetime repair: distinguish metadata GC from logout and guard persistent cleanup. |
| `e36b8a2` | Valid independent recovery/trade UUID fixtures preserve exact original-key assertions. |
| `18ae64f` | Stronger RED keeps the obsolete hook mounted; scope changes must not reclaim persistence. |
| `81bfebd` | RED: an obsolete client's recovery authority remains active after replacement. |
| `4a9c105` | RED: failed initialization reports pending and hides explicit recovery behind loading. |
| `2834a95` | Task 2/final GREEN: all masking, generation, explicit retry and retained execution-original checks pass. |

Both plan tasks have ordered RED/GREEN evidence. The first deletion fixture initially lost unobserved metadata to its `gcTime: 0`; corrected setup writes metadata immediately before review. The corrected original-source replay is recorded separately rather than claiming the initial fixture failure proved the authority bug.

## Verification

Qualified source: `2834a95e927518a1639b6d0e740b3af959e4d60f`.

- Whole frontend: **58 files / 1,285 tests passed**, **26.20 seconds**, exit 0. Receipt: `/tmp/birja-phase14-plan13/stable-full.log`.
- Whole frontend typecheck, lint and format check: all exit 0. Formatting receipt: `/tmp/birja-phase14-plan13/stable-format.log`; typecheck/lint outputs were returned by the same successful command.
- Focused generation/boundary/overview/deletion selector: 135 tests passed in 3.38 seconds before the final storage-error assertions; the complete final suite includes those later assertions.
- App/overview storage-error and readiness checks: 72 tests passed in 5.30 seconds.
- Protocol, switcher and retained crypto/stock execution originals: 55 tests passed in the focused run and are included in the final whole suite.
- `git diff --check` passes; source scan found no TODO/FIXME/placeholder stubs in modified production files. No tracked files were deleted.

All Vitest invocations completed; no service, browser or container was started. Existing cleanup disposes query clients, listeners and channels. Test receipts remain under `/tmp/birja-phase14-plan13/`. The unrelated pre-existing `.claude/` directory is preserved.

## Deviations from Plan

### Authorized correctness prerequisites

1. **[Rule 2 — Missing integration] Publish from the producer and filter direct switcher consumption.** The eight planned files alone could not notify other tabs when no target hook was mounted, and PortfolioSwitcher read raw metadata independently. Parent authorized the exact deletion producer hook and switcher source/test changes. The producer sends only identity hints; the switcher now consumes accepted target metadata.
2. **[Rule 1 — Recovery lifetime] Preserve unknown markers across identity GC and obsolete clients.** Query removal returned undefined identity and was interpreted as logout, deleting durable recovery. An obsolete client's later events could also clear or reopen the newer client's envelope. Parent authorized this narrow existing-hook repair. Undefined identity revokes memory only; current authenticated logout clears persistence. A weak current-client binding is claimed on genuine mount, prior operations and serials are retired, and generation guards prevent A-to-B-to-A resurrection. Real stored-marker regressions cover GC/restore without automatic DELETE, obsolete null/non-null events, current logout and captured original callbacks.
3. **[Rule 3 — Test environment] Use actual existing Node WebCrypto.** Central readiness now exercises real SubtleCrypto, which jsdom omits. Parent authorized `src/test/setup.ts`; no production fallback or package was added. TradePage's invalid `key-N` UUID mock was replaced with valid deterministic trade UUIDs and a separately initialized genuine recovery nonce. App's deferred metadata fixture now waits for initialization before releasing its resolver, retaining the no-financial-child-before-discovery assertion.
4. **[Rule 1 — Error state] Expose initialization errors as errors.** Overview initially returned both pending and error after storage failure, preventing its existing error/retry UI from appearing. A real storage exception/retry regression precedes the boolean-state correction.

No package, lockfile, image, provider, database, production or publication operation was part of this plan. Existing security gates and issue35 scope remain intact.

## Plan 14 handoff

- `usePortfolioTarget` and `usePortfolioOverview` mount the owner-only deletion lease outside financial content. Metadata-only deletion recovery UI must also stay outside the financial Outlet; do not reintroduce a dependency on financial target readiness.
- `usePortfolioTarget(...).portfolios` is the accepted lifecycle-filtered identity list. Do not restore switcher labels/options from raw `['portfolios', owner]` cache values. Uncertain filtering never establishes empty-account or implicit sibling authority.
- `usePortfolioOverview(...).membershipUncertain` flags a hinted/masked root or unresolved original. A fully masked uncertain overview returns undefined data rather than a misleading empty array. Use this flag when presenting pending membership/counts; visible remaining rows keep their independent values.
- Storage initialization errors expose explicit guarded retry. These retries restore the metadata lease only and never submit DELETE. The original-intent recovery controls remain the deletion hook's explicit methods.
- `portfolioDeletionAuthorityGeneration(client)` is a readonly captured-generation fence, not financial authority. Readiness still requires the current mounted client, matching owner and restored recovery. Existing captured functions/receipts remain permanently invalid after their generation retires.
- Preserve Plan 12's `isPortfolioDeletionMetadataBlocked` versus financial quarantine distinction: opening a named pre-submit review does not revoke trading; durable confirmed submission does.
- Completion consumers must still check `receipt.isCurrent()` immediately before every navigation, focus or announcement. No automatic original DELETE or trade retry is introduced.
- Execution `404 portfolio_unavailable` can follow a committed fill. Preserve the original financial attempt privately as unknown; the unavailable boundary exposes only its existence. Preview-404 remains a separate noneconomic path.

## Remaining qualification

Plan 14/15 product UI and integration, Plan 17 actual browser journeys, Plan 18 complete security/recovery qualification and Plan 19 owner UI/native200 acceptance remain separate. This summary does not mark global requirements complete or claim human/browser acceptance. Parent owns STATE/ROADMAP/requirements updates and independent review; this executor stops after Plan 13.

## Known Stubs

None. Generic unavailable/error/loading states are intentional safety states, not simulated financial data.

## Self-Check: PASSED

The summary and all 17 modified source/test files exist. All 12 recorded source/test commits resolve as Git commits. The qualified source is committed; the working tree contains only this summary and the pre-existing unrelated `.claude/`. No global planning state was changed by this executor.

## Independent-review blocker repairs — CR-01 and CR-02

Completed locally on 2026-11-19 after reading the complete parent-owned `14-13-REVIEW.md`. The original review and finding history remain intact for independent re-review.

### CR-01 — Reconcile former masks against the current durable original

A retired client's old quarantine is now reconciled before its restored generation receives financial readiness. The current owner-bound durable attempt remains quarantined regardless of active GET/list results. Other former masks require a forced fresh authenticated owned list: cancel any old list request, invalidate its cache, then use the existing QueryClient `fetchQuery` with retries disabled. Owner/generation guards apply before and after every await and inside the query function. Only IDs present in that fresh active list can release former masks. Missing/closed roots remain masked, including while old cached membership is still present.

Retirement also discards `releaseAfterReview`, which belongs to the retired generation. This prevents an obsolete terminal-review release from resolving a newer unknown original. A failed proof read keeps readiness false and masks intact; explicit recovery retry obtains metadata proof without sending DELETE.

Real-marker regressions cover:

- A unknown → B exact durable `portfolio_confirmation_changed` refusal and fresh detail metadata → A returning with an empty marker; A obtains a new ready target only after fresh list proof, while the original target and confirmation stay revoked.
- B verified closure → A returning with its old active list; no target becomes available before or after the fresh closed/missing proof.
- B resolves A's first original and starts a **different** unknown original; returning A releases the former active root while the new original stays masked even when repeated fresh lists include it as active.
- A proof-read failure and explicit retry; the original mask persists through failure, and neither initialization nor retry submits DELETE.

The additional metadata proof GET is part of restoration only when former masks exist outside the current durable original. Consumers must retain the readiness gate while it runs. It is not provider access, mutation authority, proof from a broadcast, or automatic deletion recovery.

### CR-02 — Clean up authenticated null after unknown identity

The session now detects an unknown-to-known-null transition even when both identities map to `owner: null`. Current authenticated sign-out revokes private memory and clears persistent recovery under the existing current-client guard. Undefined/removed identity still revokes memory without erasing the durable original; obsolete clients still cannot clear or reopen a newer lease.

Two real stored-marker cases exercise cold undefined identity and identity-cache removal after restoration. Both preserve the marker while identity remains unknown, then resolve an actual bounded authentication-refusal flow to null and verify current-client cleanup. Existing GC, obsolete-client null/non-null, current logout and generation-return cases remain passing.

### Repair commits and qualification

- `c56beaf` — genuine RED regressions for both blockers. The valid terminal/closure fixtures use application/json, and B's explicit original check is asserted to reach transport and its durable result.
- `311d613` — production GREEN repair in the existing deletion hook plus the cold/removed, closure, retry and different-original complements.
- `ba9bba1` — strengthen the ordinary stale-list refresh path. An isolated source replay of pre-repair `231ec02` fails after fresh active proof: both empty-marker and different-original cases leave A unavailable. The verified-closed complement remains unavailable as required.

Qualified repair tree: **`ba9bba15860abe7b68d0dcf3321dd1094a2395f9`**; production repair: `311d61313da89b25130b7da0f32bb7895829f95f`.

- Final whole frontend: **58 files / 1,291 tests passed in 25.60 seconds**, exit 0.
- Final whole frontend typecheck, lint and formatting: all exit 0. `git diff --check` also passes.
- Deletion/target complements: 88 tests passed in 4.01 seconds before the last strengthened stale-list assertion; the complete final suite includes that assertion.
- Earlier focused deletion/target/overview/management/boundary/switcher/protocol/storage/API group: 231 tests passed in 6.25 seconds before the different-original complement; the final suite includes the complement.
- Receipts: `/tmp/birja-phase14-plan13-repair/full-final.log`, `format-final.log`, `blockers-red.log`, `all-complements.log` and `old-source-fresh-proof-red.log`.

The old-source replay used a synthetic source-only copy under `/tmp` and the already installed Node modules; it did not alter the working source or install packages. All test invocations completed. No database, browser, provider, production or publication operation was performed. Only the existing deletion hook, its tests, target tests and this summary changed during repair. Global planning state and requirements remain parent-owned; independent re-review is still required before Plans 14/15 proceed.

### Repair Self-Check: PASSED

All three repaired source/test files and this summary exist. All three repair commits resolve. No tracked files were deleted. The parent-owned untracked review and pre-existing `.claude/` directory are preserved.
