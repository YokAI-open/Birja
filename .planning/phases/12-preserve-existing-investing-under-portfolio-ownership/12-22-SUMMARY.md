---
phase: 12-preserve-existing-investing-under-portfolio-ownership
plan: "22"
subsystem: accounting
tags: [portfolio, browser, history, valuation, cache, authorization, race-isolation]
requires:
  - phase: 12-19
    provides: explicit owned target handles and lifecycle authority
  - phase: 12-20
    provides: required-root financial clients and bound trade2/mixed3 cursors
  - phase: 12-21
    provides: captured financial scope and unavailable-root revocation
provides:
  - Root/session-partitioned valuation projections and hidden stock restriction guards
  - Explicit private trade and mixed History query/page/cursor ownership
  - Scoped event seen sets and stale append/refetch/detail refusal
  - Immediate session invalidation without recapturing old target authority
affects: [12-23, 12-24, 12-25, 12-26, 12-27]
tech-stack:
  added: []
  patterns: [captured read authority, root-partitioned projection, session external-store subscription]
key-files:
  created:
    - frontend/src/hooks/portfolioValuation.test.tsx
    - frontend/src/hooks/portfolioHistory.test.tsx
  modified:
    - frontend/src/hooks/usePortfolio.ts
    - frontend/src/hooks/useHistory.ts
    - frontend/src/hooks/useEventHistory.ts
key-decisions:
  - Require PortfolioTarget first and partition query keys plus hidden projections and seen state by owner/root/session
  - Subscribe to session changes for immediate masking but retain the authority captured by the original target
  - Preserve accepted immutable History pages for same-root append errors; unavailable roots revoke authority and expose no pages
  - Invalidate only the event's owner/root financial views; identity is no longer a financial cash projection
requirements-completed: []
requirements-addressed: [PVIEW-03, PCTX-01, PSAFE-02]
duration: 14 min
completed: 2026-11-16
---

# Phase 12 Plan 22: Valuation and History Hook Isolation

**Captured portfolio authority partitions financial projections, opaque continuations and embedded originals while preserving exact valuation and same-root History recovery.**

## Performance

- Started: 2026-11-16T13:56Z
- Focused gates complete: 2026-11-16T14:10Z
- Tasks: 2/2
- Files created/modified: 5
- Dependencies, backend authority, page controls and production resources changed: none

## Accomplishments

- usePortfolio requires a captured target and uses owner/root/session query keys.
  Its WeakMap now holds separate projection/monotone authority/clock maps per
  root. Equal symbols and coin IDs in a sibling cannot replace cash, stored
  baseline, returns or retained stock restrictions. Stock-context restrictions
  use the exact owner/root/session/symbol key; global market evidence remains
  shared. Cache values with a different returned portfolio ID are suppressed.
- Every read verifies the captured target before transport and after response,
  checks cancellation and query-object identity, and never carries previous-root
  placeholder data. Unavailable404 removes only that metadata root and revokes
  its captured authority; fresh metadata is required before finance resumes.
  Failed valuation refreshes hide earlier statements instead of presenting old
  cash or return as a new success. Existing stock expiry reductions and incomplete
  known-value/allocation rules remain unchanged; no subtotal is recalculated.
- Both History hooks require the same explicit target. Query/page/cursor chains
  are owner/root/session-scoped, and every late initial/append response must still
  belong to its original query and target. Stale manual refetch/fetchNextPage
  actions reject before transport. Simultaneous next-page requests retain the
  existing cancelRefetch:false behavior. Same-root append errors retain accepted
  immutable pages and permit retry using their original cursor.
- Mixed History's seen-event sets are partitioned by root as well as owner and
  session. Even identical global event IDs in sibling portfolios produce only
  their own financial invalidations. Pending cancellation/invalidation checks
  its captured scope again before acting. It no longer invalidates identity as
  a cash projection; portfolio and stock-context invalidations include the root.
- Original dividend details stay inside the validated immutable page. Loaded
  originals disappear before a sibling page is available, and late detail/page
  hydration cannot publish into another target. There is no separate unscoped
  original-reference cache or client-side financial recomputation.
- Session external-store subscriptions immediately mask accepted read data on
  identity changes, even before the parent route rerenders. Subscription updates
  do not recapture the original target's authority after logout and return.

## Task Commits

| Task | Commit | Result |
|---|---|---|
|12-22-01|85a5a8a|Owned valuation queries, per-root hidden projection and expiry guards|
|12-22-02|020c79a|Scoped private History state and immediate captured-session masking|

## Verification

- Assigned valuation module: 14 cases pass. Coverage includes missing targets,
  same-symbol siblings with unequal baselines, delayed root responses, logout
  and return, unavailable/failed refreshes, metadata revocation, root loss during
  refresh, same-root expiry, crossed-cache bodies and sibling hidden guards.
- Assigned History module: 24 cases pass. Both real request clients run with
  fetch intercepted at the HTTP boundary: opaque trade2/mixed3 continuations,
  order and retry, initial/append races, stale callbacks, owner changes, unavailable
  targets, wrong-root cursors, event seen sets and actual embedded original details.
  A positive same-root correction/original page is accepted before testing its
  suppression during a target switch; malformed fixtures cannot stand in for
  private-detail isolation.
- Final seven-file read/trade/client/target regression passes198 cases:
  portfolioValuation, portfolioHistory, portfolioCrypto, portfolioStock,
  portfolioTrades, portfolioReads and usePortfolioTarget.
- All five task files pass ESLint and Prettier. git diff --check passes.
- Full frontend typecheck was run and reports61 errors across18 later consumer
  and retained-fixture files. No error is in this plan's changed source or new
  tests. Plans23–25 must supply targets to pages;27 owns old API/hook/page fixture
  adaptations. No whole frontend type/build/suite success is claimed and no
  optional target or synthetic cash compatibility shim was introduced.

## Interfaces for Following Plans

- usePortfolio(target:PortfolioTarget|null), useHistory(target) and
  useEventHistory(target) all require explicit captured authority. Null or revoked
  targets do not query or expose financial data. Hooks should be called normally
  with null when their target boundary is unavailable.
- Read keys are [portfolio,owner,portfolioId,session],
  [history,owner,portfolioId,session] and
  [eventHistory,owner,portfolioId,session]. Existing scoped fill invalidation
  prefixes [prefix,owner,portfolioId] match those keys.
- Both History hooks keep normal TanStack infinite-query data and flags, plus
  guarded refetch/fetchNextPage methods. Same-root append failures expose accepted
  pages for the existing error/retry UI; unavailable portfolios expose none.
- eventHistorySession(client) retains its existing {email,epoch} interface for
  trade hooks. Plan25 must key visible expanded original details to the target,
  following the accepted UI contract; no page/component change is part of22.

## Deviations from Plan

**[Rule2 — Missing critical observer notification]** A new cached-owner-change
probe showed that valuation's timer/cache reduction subscription alone did not
rerender accepted data immediately when identity changed. The shared session
external-store subscription now notifies all three read hooks. Authority remains
memoized to the original target rather than being recaptured by an old handle
after logout/return. The failing probe and all affected trade hooks now pass.
This bounded Task02 correction also touches the Task01 valuation files; no new
file or architectural boundary was introduced.

## Known Stubs and Carry Forward

None in the delivered hooks. Null-target/empty History states are actual idle or
unavailable states, not invented financial data. Pages and visible details are
intentionally integrated in23–25; old unscoped test fixtures are adapted in27.
Human UI/native zoom, full frontend coverage/build/browser, strict audits/images
and complete encrypted same-archive recovery remain pending. Whole requirements
stay unchecked, and Phase7 live outcomes remain separately deferred. All work
remains local; unrelated.claude/ stays untouched.

## Self-Check: PASSED

Both new test modules and task commits85a5a8a/020c79a exist. The assigned38-case
read-hook and combined198-case regression pass, as do changed lint/format and
diff checks. Full frontend typing obligations are recorded without concealing
them or claiming the whole phase is ready.
