---
phase: 13-create-and-compare-independent-strategies
plan: "11"
subsystem: frontend
tags: [tanstack-query, portfolio-overview, valuation, owner-isolation, history]
requires:
  - phase: 13-10
    provides: Strict current target authority and narrow immutable-original recovery
  - phase: 13-08
    provides: Strict nineteen-field bounded comparison transport
provides:
  - Owner/session-scoped overview query with per-book stock safety and expiry projection
  - Accepted original-root fill and attributable event comparison invalidation
  - Common comparison snapshot preservation and late creation continuation revocation
affects: [13-12, 13-13, 13-15, 13-16, 13-17, 13-18]
tech-stack:
  added: []
  patterns: [shared safety projector, separate detail and overview snapshot lanes, captured lifecycle invalidation]
key-files:
  created:
    - frontend/src/hooks/usePortfolioOverview.ts
    - frontend/src/hooks/usePortfolioOverview.test.tsx
  modified:
    - frontend/src/hooks/usePortfolio.ts
    - frontend/src/hooks/useTrade.ts
    - frontend/src/hooks/useStockTrade.ts
    - frontend/src/hooks/useEventHistory.ts
    - frontend/src/hooks/useHistory.ts
    - frontend/src/hooks/portfolioHistory.test.tsx
    - frontend/src/hooks/portfolioCrypto.test.tsx
    - frontend/src/hooks/portfolioStock.test.tsx
    - frontend/src/hooks/usePortfolioManagement.ts
    - frontend/src/hooks/usePortfolioManagement.test.tsx
key-decisions:
  - "Share owner/root/session stock proof and monotonic clock knowledge across views while partitioning only latest financial snapshots by detail/overview lane."
  - "Refuse a backwards comparison response atomically instead of mixing retained per-book valuation instants."
  - "Recheck creation's captured session after awaited discovery invalidation before refreshing overview."
requirements-completed: [PCTX-02, PVIEW-01, PVIEW-02]
duration: 12min
completed: 2026-11-18
---

# Phase 13 Plan 11: Guarded Comparison Reads and Financial Refresh Summary

**One owner/session comparison query now retains exact independent statements, suppresses unsafe stock values per book, and refreshes after accepted original-root fills and attributable events.**

## Performance and Task Commits

- Approximately 11:31–11:43 UTC on 2026-11-18; two of two tasks complete.
- Twelve source/test files changed, plus this summary. Existing `portfolioValuation.test.tsx` was read and verified without unnecessary edits.
- Task 1 RED `a88c092`: the missing overview hook fails import resolution before implementation.
- Task 1 GREEN `339f4b7`: guarded query and shared safety projector; 31 initial overview/valuation cases, frontend typing and scoped lint pass.
- Task 2 RED `7e6ddbd`: three expected failures expose missing comparison refresh after accepted real-target crypto fills, stock fills and new events.
- Additional RED `8c2761c`: paired actual detail/overview hooks expose mixed statement timestamps; two actual deferred discovery refreshes expose old creation continuation after owner change or logout/return.
- Additional RED `b9ef316`: a backwards overview response adding a sibling incorrectly succeeds and mixes retained statement times.
- Snapshot GREEN `c3fdfed`: separate snapshot lanes and atomic backwards-response refusal.
- Creation continuation GREEN `d8b999b`: post-await session check before overview invalidation.
- Task 2 GREEN `3167bdf`: correct owner/session overview refresh, repeated authority checks and retained History isolation.

Both tasks have committed RED before GREEN. No tracked file was deleted. Parent owns STATE, ROADMAP, REQUIREMENTS and independent review; this executor did not edit or stage them. The requirement IDs record this plan's contribution, not whole-requirement acceptance.

## Overview Contract for Plan 12

`usePortfolioOverview()` returns the normal TanStack query status/error/loading fields, guarded `data`, and a captured `refetch(options?)`. Its key is exactly `["portfolioOverview", ownerEmail, eventHistorySessionEpoch]`. It uses the strict Plan 08 `/api/v2/portfolios/overview` client and one request for zero through ten active books. It never derives financial authority from discovery or identity cash.

`data` is undefined while no current owner/session is authorized or initial loading/failure has no accepted response. A valid empty response remains `[]`. Initial malformed data remains an error rather than an empty success. Accepted rows retain stable server order, exact decimal strings, custom stored baselines, incomplete/known-value semantics, original source evidence and common `valued_at`. No JavaScript money calculations, pooled total, ranking or fabricated percentage is introduced. Internal transport timing accompanies the validated statement solely for safety projection.

A failed refresh keeps still-authorized permitted values with `isError`/`error` observable for the UI's required failure notice. Each stock holding independently passes the exact existing detail projector, including quote deadlines, admissions, unit/safety epochs, sequence/hash continuity, external stock/context restrictions and monotonic clock bounds. Expiry clears unsafe basis/mark/value/return fields without calculating replacement totals; other books remain usable. Re-fetching the same raw old statement cannot renew proof. Overview has one display interval and one nearest-proof deadline timer for the whole collection, plus one 30-second owner-wide query refresh; there are no per-book provider polls/jobs.

`usePortfolio.ts` exports `TimedPortfolio`, `portfolioGuardFor(client, owner, root, session)`, and `projectPortfolio(client, guard, statement, view = "detail")`. One guard shares proof versions, hashes, provider identity, continuity/sequence, restriction floors and conservative clock across both views of that owner/root/session. Only `guard.latest.detail` and `guard.latest.overview` are separate financial statements. The overview passes `view = "overview"`; a newer detail response therefore cannot replace only one comparison row. Accepted detail/overview cache changes trigger reprojection in both directions without network invalidation or a notification loop. A returned comparison older than a retained overview book refuses as a whole, preserving the previous authorized collection with an error. Equal-time restriction reductions remain irreversible until newer permitted evidence.

Owner loss synchronously clears private queries and revokes hidden guard state. Query-object identity, abort, captured owner/session and mounted scope prevent late responses, stale manual refresh and old401 from publishing into a new lifecycle. Focus, visibility, cache safety changes, render and bounded timers reapply safety. Identity-only metadata events invalidate authoritative owner discovery and this exact overview under current authentication; messages supply neither labels nor ownership authority.

## Financial and History Coherence

Accepted crypto/stock fills invalidate the original root's existing detail/holding/quote/History/context queries and exact current owner/session overview. Each invalidation rechecks captured current authority. Stock list invalidation is now owner-scoped; the owner-independent global crypto price query remains shared. Narrow original-recovery authority still cannot publish a receipt or independently invalidate finance. Stable crypto mutation entrypoint behavior, same-root rename originals, original labels, unknown retries and late404/401 revocation remain covered by retained real-target regressions.

Newly observed attributable event IDs invalidate detail, stock context and exact owner/session overview after cancelling pre-event reads. Seen sets remain owner/root/session scoped. A repeated page does not trigger a refresh loop; delayed cancellation after session loss cannot invalidate the replacement lifecycle. Trade-only and mixed History retain explicit-root queries, root-bound opaque cursors, same-root append error/retry and embedded original details. Switching, unavailable originals, stale actions and late replies continue to mask prior finances and details.

Creation/metadata hooks retain their existing authoritative discovery/overview/root invalidations. The creation continuation now rechecks its captured session after awaited discovery refetch, closing a reproduced same-owner relogin race before the following overview invalidation.

## Verification Evidence

Only existing Node 24.22.1/frontend dependencies were used. No DB resources, provider requests, browser, private environment, package install or production operation ran.

```text
cd frontend
npm run test -- src/hooks/usePortfolioOverview.test.tsx src/hooks/portfolioValuation.test.tsx
  Initial GREEN: 31 pass; final affected run includes 19 overview + 14 valuation cases.
npm run test -- src/hooks/portfolioCrypto.test.tsx src/hooks/portfolioStock.test.tsx \
  src/hooks/portfolioHistory.test.tsx
  Final affected run includes all 71 passing cases in these three suites.
npm run test -- <26 named affected API/auth/parser, target/management/financial-hook,
  Portfolio/History/crypto/stock trade page and App suites>
  26 files, 755 tests pass; duration 15.61s.
npm run typecheck
  PASS: whole frontend tsc -b.
npm run lint
  PASS: whole frontend ESLint.
./node_modules/.bin/prettier --check <all twelve changed source/test files>
  PASS.
git diff --check
  PASS.
```

The final 26-suite command contains `usePortfolioOverview`, `portfolioValuation`, `portfolioCrypto`, `portfolioStock`, `portfolioHistory`, `usePortfolioManagement`, `usePortfolioTarget`, `usePortfolio`, `useTrade`, `useStockTrade`, `useEventHistory`, `useHistory`; API `portfolioOverview`, `portfolioManagement`, `portfolioReads`, `portfolioTrades`, `portfolio`, `stockTrades`, `eventHistory`, `client`, `auth`; pages `PortfolioPage`, `HistoryPage`, `TradePage`, `StockTradePage`; and `App`. No full frontend/backend/phase qualification is claimed.

## Deviations from Plan

**1. [Rule 3 - Blocking regression expectation] Extend two existing root-isolation assertions.** New required owner/session comparison invalidations necessarily failed blanket root-only expectations in `portfolioCrypto.test.tsx` and `portfolioStock.test.tsx`. Parent explicitly authorized both minimal extensions. Each allows only exact current-owner/session overview invalidation; sibling detail/history and other owner/session invalidations remain excluded. Committed in `3167bdf`.

**2. [Rule 1 - Bug] Revoke creation continuation after awaited discovery refresh.** Existing Plan 09 creation could await a GET across logout/return and then invalidate the replacement session's overview. Parent explicitly authorized `usePortfolioManagement.ts` and its test extension. Two real deferred discovery regressions fail in `8c2761c`; the single captured-session recheck and passing tests are committed in `d8b999b`.

**3. [Rule 1 - Bug] Separate snapshot retention and refuse backwards comparison responses.** Implementation review exposed shared latest-detail data replacing only one comparison row, and per-book fallback mixing an older collection with accepted data. Real paired-hook and backwards-response regressions failed before repair. `c3fdfed` retains shared safety semantics with independent snapshot lanes and refuses backwards collections atomically. No financial math/parser or target authority was weakened.

## Issues Encountered

Git index writes require sandbox escalation in this environment; the authorized scoped commits succeeded. An initial test fixture used a stock action state outside the real union and was corrected to `reconciling`. Lint required the repository's existing WeakSet scope activation pattern rather than mutating a memoized object. Query replacement testing uses a separate unresolved replacement request so it tests the discarded original rather than accepting a legitimate new query reply.

## Known Stubs

None. Null/undefined/empty values represent actual unavailable, expired, signed-out, loading or zero-book states. Stub scan found no TODO/FIXME/placeholder or unwired product data source in changed source files. No new network endpoint, authentication path, storage mechanism or schema trust boundary was added beyond this plan's modeled private overview/cache surface.

## Limits and Next Work

Plan 12 can consume the guarded overview directly and must display its truthful initial/refresh/error/incomplete states, timestamps and exact server values. Components, browser/native200 acceptance, full critical coverage/security/recovery and final goal verification remain later plans/parent review. STATE/ROADMAP/REQUIREMENTS remain parent-owned.

No package, manifest, lockfile, image/Python pin, live provider admission, private `.env`, production, push or merge changed. Keep issue35's exact existing accepted-risk scope and expiry **2026-12-17T00:00:00Z**, Python pin **20261111**, and Phase7 live stock admissions OFF. Unrelated `.claude/` remains untouched.

## Self-Check: PASSED

All twelve changed source/test paths and this summary exist. All eight task/refinement commits resolve, RED precedes corresponding GREEN, the final 755-case affected regression and whole frontend lint/type checks pass. No tracked deletions or generated untracked artifacts were introduced; unrelated `.claude/` is preserved. Independent parent review and global state updates remain pending.

## Independent Review CR-01 Repair

The initial independent review identified a blocking regression: separating whole guards by view also separated monotonic stock safety knowledge. An actual detail response with unavailable/unsafe units left its older overview mark visible; an actual overview restriction did not promptly reach detail. The earlier stockContext-injection test could not detect that path. The original report is parent-owned and remains unchanged.

RED `dd5c69f` adds two paired real-hook regressions. Each first accepts safe detail/overview data, then delivers a newer actual unsafe response through one financial endpoint. Both fail at the opposite view's still-visible basis/mark assertion. They also require separate financial times, unaffected sibling books, no revival by older/equal safe responses, no stockContext/stocks injection and bounded exact fetch counts.

GREEN `9f07f23` keys the guard only by owner/root/session, sharing all monotonic proof/restriction and clock evidence. It partitions only latest financial statements by view. Detail now subscribes to accepted overview cache updates, complementing overview's existing detail subscription; local cache reprojection is reduction-only and does not refetch. A root-unavailable detail response clears only its financial lane rather than erasing shared safety knowledge. Its next deadline also uses the conservative shared clock. Overview's atomic backwards-response refusal and common statement timestamp remain intact.

Ten additional paired actual-response cases independently exercise detail→overview and overview→detail unit epoch, safety epoch, same-generation admission hash, status sequence and advancing-clock knowledge. All 45 overview/valuation cases pass, including all prior owner/session, backwards/time and sibling-isolation assertions. The affected 26-suite regression passes **767 tests**; whole frontend typing/lint and changed-three-file Prettier/ESLint checks pass. No components, endpoints, storage, dependencies, backend, providers or global planning files changed. This is a Rule 1/2 repair within the existing T-13-11-01 proof boundary; no new feature or permission boundary was added.

### Repair Self-Check: PASSED

The three source/test files exist; RED `dd5c69f` precedes GREEN `9f07f23`. All original execution/publication/accepted-risk limits remain. Parent independent recheck and global state updates remain pending.
