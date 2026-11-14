---
phase: 10-dividend-cash-and-event-history
plan: "13"
subsystem: private-client-history
tags: [tanstack-query, owner-isolation, session-epoch, authoritative-cash]
requires:
  - phase: 10-11
    provides: Authenticated exact mixed History API
  - phase: 10-12
    provides: Strict event parser and bounded cursor transport
provides:
  - Owner/session-epoch infinite History with synchronous private-page removal
  - Accepted-page retention, duplicate-append protection and late-response refusal
  - Owner-safe financial refresh and both existing trade-hook invalidation links
affects: [10-14, 10-15, 10-16, 10-17]
tech-stack:
  added: []
  patterns: [query-client-lifecycle-guard, synchronous-external-store-epoch, cancel-before-invalidate]
key-files:
  created: [frontend/src/hooks/useEventHistory.ts, frontend/src/hooks/useEventHistory.test.tsx]
  modified: [frontend/src/hooks/useStockTrade.ts, frontend/src/hooks/useTrade.ts]
key-decisions:
  - Observe auth epochs synchronously so batched query notifications cannot retain the previous owner's rendered pages.
  - Cancel pending pre-event financial views before invalidating authoritative owner cash, Portfolio and stock context.
  - Capture the crypto mutation's owner lifecycle so late successful replies cannot refresh a replacement session.
requirements-completed: []
requirements-supported: [HIST-03, DIV-04]
duration: approximately11min
completed: 2026-11-13
---

# Phase10 Plan13: Owner-isolated events and authoritative refresh

**Mixed History pages follow the current owner and auth epoch; accepted new
identities refresh server-owned cash and trading views without a client credit.**

## Tasks and commits

1. RED `571076a`: the callable legacy-hook seam made one actual transport call
   while logged out, rather than zero. GREEN `578a9dd`: owner+epoch key, immediate
   purge/hiding, abort and query-identity checks, strict existing parser, one active
   append and retained accepted pages. Fourteen transport tests passed2.21s.
2. RED `e875f32`: an accepted new identity produced none of the required
   authoritative refreshes. GREEN `279307b`: cancel-before-invalidate owner views,
   session-bound crypto completion and scoped stock/event invalidation, retaining
   legacy History invalidation. Existing financial math and wire remain unchanged.

No staged seam remains. The hook is not yet mounted in HistoryPage; Plan14 owns
that declared UI integration. There is no browser storage, optimistic income,
History-derived balance, provider transport, dependency or backend change.

## Actual verification

| Gate | Result |
|---|---|
| Task1 behavioral RED |1 failed; actual request-count assertion, not import failure |
| Final affected hook suites |68 passed/3.35s across new History and existing crypto/stock hooks |
| Complete frontend coverage |681 passed/35files/16.46s |
| Full frontend coverage percentages |98.44 statements;94.88 branches;98.93 functions;99.14 lines |
| New History hook coverage |96.92 statements;94.73 branches;100 functions;98.03 lines |
| Full ESLint / TypeScript / Prettier |Pass |
| Whitespace / stub / deletion scan |Pass; no tracked deletion or remaining staged seam |

Logs: `/tmp/birja-phase10-13-task1-red.log`,
`/tmp/birja-phase10-13-task1-expanded2.log`,
`/tmp/birja-phase10-13-task2-red.log`,
`/tmp/birja-phase10-13-task2-green.log`,
`/tmp/birja-phase10-13-affected.log`,
`/tmp/birja-phase10-wave8-frontend.log`.
Executed existing installed `npm run test -- --coverage`, `npm run lint`,
`npm run typecheck`, `npm run format:check`; no install or lockfile change.
The new file has21 tests. Parent owns the independent backend wave gate.

Tests assert logout/account switch immediate purge, same-owner relogin epoch,
late prior-owner fulfillment/401 refusal, current401 login handling without a
retry loop, server order, duplicate active append, malformed append and later
refresh-page failures preserving accepted pages, initial error and explicit retry.
Actual existing crypto/stock hooks reach the new scoped invalidation while keeping
legacy invalidation. Late crypto success after another owner or same-owner relogin
causes no replacement-session refresh. A paused pre-event Portfolio query is
cancelled; its delayed old cash cannot overwrite the new server result. Another
owner's Portfolio cache stays unchanged and uninvalidated. Auth change during
cancellation suppresses the former owner's deferred invalidations.

These are frontend transport/cache tests, not claims of executing financial SQL.
Actual financial effects are predecessor proofs; no financial success is invented
as backend evidence here. Unknown/held money is never summed or credited locally.

## Deviations and construction corrections

- The initial owner guard purged cache synchronously, but TanStack's batched
  observer notification left a prior rendered snapshot briefly visible in a
  direct auth-transition assertion. A small useSyncExternalStore subscription
  observes the existing cache guard epoch synchronously; React cleans its hook
  subscription on unmount. The per-QueryClient WeakMap guard follows existing
  project lifecycle patterns and adds no window/global listener.
- Corrected test observer waits after asynchronous page notifications, a typed
  mock's unused parameter and an owner-switch fixture's response routing order.
  The first scoped lint run caught that unused parameter before final static
  verification; its correction is included in Task2, and final full lint passes.
  Earlier failed construction logs are not represented as passing gates.
- No ownership extension or architecture/dependency change. Parent retains
  canonical STATE/ROADMAP/requirements and the pending ROADMAP edit untouched.

Context7 MCP and ctx7 CLI were unavailable; no tool was installed. Consulted
official [TanStack infinite queries](https://tanstack.com/query/latest/docs/framework/react/guides/infinite-queries)
and [query cancellation](https://tanstack.com/query/latest/docs/framework/react/guides/query-cancellation)
for the existing installed5.105.0 behavior. No dependency upgrade was inferred.

## Threat results and remaining gates

T-10-13-01/02: owner/epoch/query identity, strict existing parser, synchronous
private-page removal, current-only401 and actual late-response/cache tests pass.
T-10-13-03: bounded server pages, one active append, no retry loop or polling,
retained safe pages and cancellation-before-refresh pass. T-10-13-SC: no package,
lock, image or installation change. No new trust surface or known stub remains.

No backend, DB, Docker, .env/secret, provider, production, B2, timer, installed
tool, push or deployment access occurred. Parent's separately running backend
gate was not touched. UI/browser/recovery/security and real new UI/native200%
acceptance remain later declared plans; prior approvals do not satisfy them.

## Self-Check: PASSED

All4owned implementation/test files exist. Four task commits exist without
deletion. Actual681 full/68 affected tests, complete static checks and whitespace
scan pass. Unrelated `.claude/` and parent planning changes are preserved.
