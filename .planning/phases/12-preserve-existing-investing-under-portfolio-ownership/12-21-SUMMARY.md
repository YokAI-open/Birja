---
phase: 12-preserve-existing-investing-under-portfolio-ownership
plan: "21"
subsystem: trading
tags: [portfolio, browser, cache, idempotency, authorization, race-isolation]
requires:
  - phase: 12-19
    provides: frozen explicit portfolio target with captured lifecycle authority
  - phase: 12-20
    provides: required original-root financial clients and immutable attempt types
provides:
  - Owner/root/session-scoped crypto previews, holdings and persisted original attempts
  - Root-partitioned stock context authority, previews, receipts and recovery state
  - Hidden unknown originals with same-root recovery and stale-callback refusal
affects: [12-22, 12-23, 12-24, 12-25, 12-26, 12-27]
tech-stack:
  added: []
  patterns: [captured financial scope, root-keyed authority guards, immutable original recovery]
key-files:
  created:
    - frontend/src/hooks/portfolioCrypto.test.tsx
    - frontend/src/hooks/portfolioStock.test.tsx
  modified:
    - frontend/src/hooks/useQuote.ts
    - frontend/src/hooks/useHolding.ts
    - frontend/src/hooks/useTrade.ts
    - frontend/src/hooks/useStockTrade.ts
key-decisions:
  - Require a current PortfolioTarget at every hook and check its captured session before transport or publication
  - Keep unknown originals in owner/root/session state while suppressing their financial projection on another or unavailable target
  - Partition stock continuity, safety, clock and restriction guards by root as well as symbol
  - Server-unavailable responses remove authority and require fresh metadata instead of permitting recovery on an unavailable target
requirements-completed: []
requirements-addressed: [PFIN-02, PFIN-03]
duration: 16 min
completed: 2026-11-16
---

# Phase 12 Plan 21: Trade Hook Cache and Unknown-Attempt Isolation

**Captured owner/root/session authority isolates previews, fills and recovery attempts while preserving stock market guards and immutable original retries.**

## Performance

- Started: 2026-11-16T13:36Z
- Focused gates complete: 2026-11-16T13:53Z
- Tasks: 2/2
- Files created/modified: 6
- Packages, backend authority, visual controls and production resources changed: none

## Accomplishments

- Crypto quote and holding keys contain owner, portfolio and lifecycle identity;
  previews never borrow previous-root placeholder data. Every request checks its
  captured target before transport and after response, checks query-object
  identity, and honors cancellation even if the underlying transport completes.
  Errors or unavailable refetches do not display an earlier financial projection.
- The shared financial scope captures the existing session epoch and removes
  private crypto state on owner changes. Server-unavailable responses revoke the
  captured target and remove only its metadata entry; fresh metadata is required
  to resolve authority again. No alternate root is selected.
- Crypto mutation state is persisted by owner/root/session/symbol. It saves a
  deeply frozen original order, expected mid and idempotency key before sending.
  Duplicate pending submissions and different unknown attempts fail before
  transport. Unknown attempts cannot be abandoned by reset; same-root recovery
  retains the original key and payload. Late results and caller callbacks cannot
  publish into a new target or resurrect removed owner caches.
- Stock state, context queries, mutation keys and hidden ContextGuard maps now
  include portfolio identity. Existing safety generations, monotone observed
  clocks, continuity, restriction serials and quote expiry remain in force.
  No restriction, cash value or executable mapping is borrowed from a sibling.
- Stock attempts include frozen portfolio_id. Target loss during a fill hides
  the result but retains an unknown original for later recovery on the same
  active root. Market closure still permits original active receipt recovery;
  an unavailable portfolio does not. Leaving a preview invalidates it while
  retaining quantity for another explicit preview. A same-root reprice still
  requires a second confirmation.
- Successful fills invalidate only that owner/root's financial views plus
  shared market queries. No pooled balance, identity-cash fallback or optional
  request target was introduced.

## Task Commits

| Task | Commit | Result |
|---|---|---|
|12-21-01|cd9d311|Scoped crypto reads, immutable original attempts and stale-result guards|
|12-21-02|e03f271|Root-partitioned stock authority/state and original-target recovery|

## Verification

- Assigned crypto module: 16 cases pass. Tests cover delayed preview responses,
  root switching, holding/quote unavailable refetch, zero/one/many navigation-only
  discovery, missing targets, frozen unknown payloads, duplicate submission,
  stale callbacks, logout-and-return, wrong receipts and scoped invalidation.
- Assigned stock module: 13 cases pass. Tests cover sibling contexts/hidden
  restrictions, delayed preview, lost response and market-closed recovery,
  root loss during fill, stale confirm, logout/owner switch, wrong receipts,
  second-confirmation repricing, closure interruption, unavailable recovery
  and scoped invalidation. Requests use the real financial clients with fetch
  intercepted at the HTTP boundary; no test-only financial handlers are used.
- Final five-file clients/target/hooks run: 160 cases pass, including both
  assigned modules, portfolioTrades, portfolioReads and usePortfolioTarget.
- All six task files pass ESLint and Prettier; git diff --check passes.
- Full frontend typecheck was run and reports 59 errors across 17 later
  consumer/legacy-fixture files. No error is reported in the six changed/new
  task files. Hooks/pages still using old signatures belong to Plans22–25 and
  retained test fixtures to27. Whole frontend type/build/suite success is not
  claimed and no compatibility shim hides these obligations.

## Deviations from Plan

No scope or output-file deviation. A one-line Task02 correction keeps exported
quoteKey(target,order) exactly equal to the query key used by useQuote, so Plan24
can install a same-root server reprice without an unexported extra epoch suffix.
The target's captured lifecycle and query-owner checks still protect publication.

## Issues Encountered

Initial crypto assertions awaited network completion rather than TanStack's
scheduled observer notification; waitFor now checks the actual visible state.
The initial stock reprice fixture omitted required detail fields and used an
unchanged price, correctly rejected by the existing strict parser. It now supplies
independent previous/new execution and cash deltas, preserving parser authority.
No package, database or permission change was required.

## Interfaces for Following Plans

- useQuote(target:PortfolioTarget|null, order:Order|null) and
  quoteKey(target,order) share the exact owner/root/session/order key. A null
  target or invalidated handle never requests or exposes a preview.
- useHolding(target:PortfolioTarget|null,symbol) requires the captured target.
- useTrade(target:PortfolioTarget|null,symbol) retains the mutation interface
  (order,expectedMid,idempotencyKey) and adds attempt and outcomeUnknown. Plan24
  must recover using attempt.order, attempt.expected_mid and
  attempt.idempotency_key; it must not rebuild an unknown attempt from the new
  quote or current form. reset is intentionally ineffective while submitting or
  unknown. Returned variables/status/financial data are masked on target loss.
- useStockTrade(target:PortfolioTarget|null,routeSymbol) preserves the existing
  draft/preview/confirm/checkResult/tradeAgain interface. The body of attempt
  includes its original portfolio_id. Unknown results remain in that original
  root's state and cannot be checked from a sibling or unavailable target.
- Financial key prefixes are [prefix,owner,portfolioId,...]; stock context uses
  [stockContext,owner,portfolioId,sessionEpoch,symbol]. Later read hooks must use
  the same owner/root prefix so fill invalidations stay scoped. Shared prices
  and stock market evidence remain shared.

## Known Stubs and Carry Forward

None in the delivered hooks. Initial empty states are real idle/unavailable
states, not synthetic financial values. Pages are deliberately migrated in
Plans23–25, and remaining read hooks in22; old fixtures are adapted in27.
No changed UI acceptance, native browser zoom, full coverage/audits/images or
encrypted same-archive campaign is claimed. All whole requirements remain
unchecked; Phase7 live outcomes remain deferred. Changes stay local and
unrelated .claude/ remains untouched.

## Self-Check: PASSED

Both created test modules and both task commits exist. Both assigned gates,
the final160-case regression, changed-file lint/format and diff checks pass.
Later consumer/fixture type errors are recorded without claiming final readiness.
