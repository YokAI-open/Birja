---
phase: 13-create-and-compare-independent-strategies
plan: "10"
subsystem: frontend
tags: [react, tanstack-query, metadata, idempotency, authorization]
requires:
  - phase: 13-09
    provides: Identity-only metadata events and guarded metadata management
provides:
  - Synchronously revoked name-sensitive financial target authority with authoritative renewal
  - Immutable crypto and stock original labels, roots, keys and execution payloads across rename
  - Captured crypto action guards and original-identity-only late refusal handling
affects: [13-11, 13-12, 13-13, 13-15, 13-16, 13-17]
tech-stack:
  added: []
  patterns: [separate original identity and actionable metadata, captured action entrypoints]
key-files:
  created: []
  modified:
    - frontend/src/hooks/usePortfolioTarget.ts
    - frontend/src/hooks/usePortfolioTarget.test.tsx
    - frontend/src/hooks/useTrade.ts
    - frontend/src/hooks/portfolioCrypto.test.tsx
    - frontend/src/hooks/useStockTrade.ts
    - frontend/src/hooks/portfolioStock.test.tsx
    - frontend/src/hooks/useStockTrade.test.tsx
key-decisions:
  - "Keep isCurrent name-sensitive; expose isOriginalCurrent only for matching original identity and revocation, never as standalone submission or publication authority."
  - "Capture original labels outside immutable transport payloads and require explicit current-target same-original replay."
  - "Guard captured crypto mutation entrypoints before invoking TanStack's stable observer, which otherwise adopts its latest mutation function."
requirements-completed: [PCTX-02]
duration: 12min
completed: 2026-11-18
---

# Phase 13 Plan 10: Independent Original Attempts Summary

**Metadata events revoke old financial authority immediately while frozen crypto and stock originals retain their root, payload, key and captured label for explicit recovery.**

## Performance and Task Commits

- Two of two tasks complete; seven owned source/test files plus this summary.
- Task 1 RED `24a81d7`: target metadata-event authority regression failed as expected; real target/crypto cases were authored before implementation.
- Task 1 GREEN `7f6e1fe`: target renewal and original crypto label; 71 target/crypto cases passed.
- Task 2 RED `e9beddb`: two real-target stock original-label cases failed as expected.
- Task 2 GREEN `2505c13`: frozen stock attempt labels and guarded original replay, plus actual-target negative transitions.
- Additional Task 1 RED `d491b1b` and GREEN `9b867f1`: four failures exposed captured crypto action rebinding; guarded entrypoints resolve them.
- Additional paired RED `43991ec` and GREEN `a511e89`: two failures exposed ignored late unavailable replies after rename; narrow original-identity revocation resolves them.

Parent owns STATE/ROADMAP/REQUIREMENTS and independent review. This executor did not edit or stage those globals. The requirement above records this plan's contribution, not whole-phase acceptance.

## Interfaces and Behavior

`PortfolioTarget.isCurrent()` remains strict: current committed route scope, authenticated owner/session, successful non-invalidated discovery, captured authority revision and the same selected metadata object. Old handles cannot regain authority when a name is changed back. `PortfolioTarget.isOriginalCurrent?()` checks the active original root and owner/session against fresh successful discovery without trusting the captured name. Production targets provide it; the optional type preserves existing explicit test/consumer fixtures. It never independently permits a trade or receipt.

The target subscribes to Plan09's identity-only metadata events. Matching events synchronously advance its authority revision and invalidate/refetch authenticated discovery. No event-supplied labels or owner claims are accepted. During invalidated renewal, status is loading and no target grants financial authority. Failed, malformed or missing metadata does not select another root.

Crypto state now exposes `originalName`; stock exposes `originalName` and a frozen `attempt.portfolioName` alongside the frozen original body. Original labels stay outside API execution payloads. The original root, order, expected price/mid and idempotency key remain unchanged through rename, quote/context refresh and same-root recovery. Existing precision, fee, stock authority/eligibility and reconfirmation rules remain intact.

Crypto `mutate` and `mutateAsync` check their captured target before calling the stable mutation observer. Obsolete `mutate` handles do nothing; obsolete `mutateAsync` handles reject before transport. Current actions still use the mutation's strict target checks and exact-original comparison. Stock exposes guarded action closures rather than its mutation observer and retains those checks.

Late fills from an obsolete label or departed root cannot publish or navigate. Their unresolved original stays in the original owner/root/session cache where allowed. A late authenticated 404/unavailable or 401 after a same-root rename may only revoke matching original authority/session through the narrow guard. Root switches, different owners and changed sessions fail that guard; no sibling authority is revoked by the original response. Known unavailable roots hide finance and recovery actions, retain hidden original uncertainty where applicable, and never allocate a replacement key or portfolio. Metadata renewal, returning to a root and market reopening submit nothing automatically.

## Verification

- Final source `a511e89`: **138 passing tests** across `usePortfolioTarget.test.tsx`, `portfolioCrypto.test.tsx`, `portfolioStock.test.tsx`, and `useStockTrade.test.tsx` in 3.65s.
- Actual target-hook/API-boundary tests cover pending/lost-response rename, renewed-label stale actions, owner/logout/root/removal late responses, immutable original switch/back, stock closed-market same-body replay, late unavailable replies and suppressed private projections/callbacks.
- Earlier source `2505c13`: **517 passing tests in 18 suites** in 15.24s, covering the four target/trade suites plus management hooks, History/valuation, crypto/stock clients, client/auth, management/overview parsers, metadata events, both trade pages and the target boundary. This broader receipt predates the final narrow late-refusal repair; it is not represented as a rerun on the final source.
- Full frontend `npm run typecheck` and `npm run lint` pass on final source. Seven-file Prettier and `git diff --check` pass. No tracked deletions, dependency/pin changes, provider calls or database operations.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Captured crypto actions adopted renewed observer authority.**
- Found during expanded Task 1 real-target tests: the stable TanStack mutation observer uses its latest mutation function, allowing an old public action to submit under a new label/root/owner despite mutation-function checks.
- Added a captured entrypoint check before invoking the observer; preserved current-target explicit original retry and callback guards.
- Files: `useTrade.ts`, `portfolioCrypto.test.tsx`; RED `d491b1b`, GREEN `9b867f1`.

**2. [Rule 2 - Missing Critical] Late same-root refusals did not revoke renewed metadata authority.**
- Found during final Task 1/2 negative verification: strict old-name checks suppressed late unavailable responses after rename along with fills.
- Use original identity solely for 404/401 revocation; all submissions and fill publication retain strict actionable checks.
- Files: both trade hooks and both portfolio trade test suites; RED `43991ec`, GREEN `a511e89`; both regression cases pass.

Both corrections stay within the seven assigned files and the planned target/original authority boundary. No architectural change or package installation was required.

## Issues Encountered

Git metadata is read-only under the default sandbox. Authorized local commits succeeded through reviewed filesystem escalation. No authentication gate or external setup was required.

## Next Phase Readiness and Limits

Consumers can use captured `originalName` / stock `attempt.portfolioName` when presenting recovered order labels; they must continue checking captured `isCurrent()` before receipts/navigation and never substitute `isOriginalCurrent()` as action authority. Original financial recovery remains in memory; only creation recovery is persisted by Plan09.

Parent independent review and later whole-phase coverage/security/browser/recovery qualification remain required. No full frontend coverage, browser/native200%, whole-phase completion, live stock activation, push, merge or deployment is claimed. Preserve issue35's existing exact accepted-risk policy through 2026-12-17T00:00:00Z, the Python 20261111 pin and Phase7 admissions OFF.

## Self-Check: PASSED

All seven modified files exist and all eight listed task/repair commits exist in local history. Modified implementation files contain no placeholder/TODO/FIXME stubs. No new network endpoint, authentication mechanism, filesystem access or schema trust boundary was introduced beyond the plan's registered event/target boundary.
