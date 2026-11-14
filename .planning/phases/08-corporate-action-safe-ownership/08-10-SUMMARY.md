---
phase: 08-corporate-action-safe-ownership
plan: "10"
subsystem: frontend
tags: [typescript, tanstack-query, corporate-actions, authorization, expiry]
requires:
  - phase: 08-09
    provides: Bounded action-safe discovery and explicit public action/valuation facts
provides:
  - Exact additive action/valuation validation before authenticated cache publication
  - Authentication-scoped stock epoch and exact server-observation high-water guards
  - Conservative nearest-deadline cache purging using full RTT and monotonic elapsed time
affects: [08-11, 08-12, 09-stock-trading]
tech-stack:
  added: []
  patterns: [strict-stock-response-coherence, monotonic-authority-reduction, nearest-deadline-purge]
key-files:
  created: []
  modified: [frontend/src/api/stocks.ts, frontend/src/api/stocks.test.ts, frontend/src/hooks/useStocks.ts, frontend/src/hooks/useStocks.test.tsx, frontend/src/components/StockSection.test.tsx]
key-decisions:
  - Generic epoch-zero redaction always reduces authority while internal epoch/server-time high-water marks survive.
  - Current responses require strictly newer exact server observations; identical snapshots never restart elapsed authority.
  - Browser precision rounds server authority time up and source/deadline time down; timeout only removes authority.
requirements-completed: []
requirements-addressed: [ACT-02, ACT-03]
duration: 32min
completed: 2026-11-11
---

# Phase 8 Plan 10: Strict Client Epochs and Deadline Expiry Summary

**Stock responses require coherent action, quote and session facts; authenticated cache guards prevent stale replies and repeated snapshots from restoring expired prices.**

## Scope and behavior

Both tasks are implemented in five existing frontend source/test files. No new
package, lockfile, backend, database, production, provider, credential, B2, host
timer, deployment or publication changes were made. The existing Phase7 campaign
was not accessed. Stock execution remains false; no new controls, financial
effects or History were introduced. Phase7 live acceptance remains deferred and
its existing UI acceptance is preserved.

The parser requires exact public keys, twenty distinct identities, string money,
IEX attribution, fixed action/reason and valuation combinations, nonnegative safe
epochs, valid UTC civil timestamps and coherent source-event/collection/server
ordering. Nanosecond comparisons preserve fractions beyond Date.parse precision.
Numeric disclosures require compatible known sessions and reasons; recent means
an open regular session and source age strictly below120seconds. Explicit dated
stale/closed marks remain distinguishable from recent quotes. Unknown, held,
permission-denied and malformed envelopes cannot invent current valuation.
Requests preserve AbortSignal, the shared authenticated retry path, no-store and
the measured full transport interval.

Projection uses monotonic elapsed time and full RTT once. Server time rounds up,
source-event/deadline times down, so sub-millisecond precision can expire early
but never late. The nearest disclosure/calendar/action/session/quote-age deadline
purges cached and rendered values at equality, before the independent one-second
display tick or30second network poll. Query updates reschedule the bounded timer;
focus/visibility catch-up handles throttled background timers. Consumed deadlines
are removed and unmount clears listeners/timers. Timers never establish safety.
Original quote timestamps, integer source ages and transport evidence stay in
cache so projection never adds RTT twice.

QueryClient-scoped raw instrument epoch/time, approved admission generation,
monotonic clock and latest sanitized snapshot high-waters survive polling, same-user refresh
and hook lifecycle changes. Actual email/null authentication transitions reset
the maps; existing private-query cleanup/cancellation and owner guards remain.
Incoming current actions require sufficient epoch and a strictly newer exact
server observation. A separate internal monotonic upper-clock high-water also
survives late generic redactions; its conservative elapsed offset preserves
independent admission/calendar/session authority without changing original measured
transport or public timestamps. Identical current replies retain the original cache/transport anchor
instead of restarting authority before or after a local deadline. Generic lower
epoch0 or held responses may always reduce authority; internal maxima remain to
reject later unsafe replays. A genuinely newer valid resolution can recover.

## Task commits and behavioral TDD

1. Task08-10-01 RED `bfe950e`:17 malformed action cases were accepted incorrectly.
   GREEN `52374a7`: required typed action/valuation authority, exact keys and
   explicit fixtures;37parser tests plus scoped types/lint passed.
2. Task08-10-02 RED `dae28b0`: monitor equality, generic-redaction/older healthy
   replay and sub-millisecond quote expiry failed. GREEN `9b8a46e`: monotonic
   projection, deadlines and epoch guards;55focused tests passed.
3. Review/regression RED `8909646`: contradictory quote/session/source facts and
   two equal-time post-expiry reanchor cases failed. RED `cd08a43` additionally
   records pre-expiry transport reanchoring and coherent changed-time fixtures.
   GREEN `a289b40` fixes both independent findings. Strictly newer current server
   observations prevent elapsed-time resetting even before a deadline is reached.

## Verification

- Final focused Vitest with V8 coverage: **144passed,5.15seconds**.
  Command: `npm run test -- src/api/stocks.test.ts src/hooks/useStocks.test.tsx --coverage --coverage.include=src/api/stocks.ts --coverage.include=src/hooks/useStocks.ts`.
- Parser: **100% statements, branches, functions and lines**. Hook:98.24%
  statements,94.47%branches,100%functions,99.36%lines. Combined263/266statements,
  398/410branches,53/53functions,236/237lines. Remaining hook gaps are defensive
  synchronous post-abort checks, null defaults and an unknown-session projection
  branch whose numeric envelope the strict parser rejects. No synthetic mocks or
  coverage exclusions were added to claim unreachable guards passed.
- Behavioral cases include119.999→120source age, exact125ms timer/cache expiry,
  full40ms RTT at a60ms local boundary, simultaneous deadlines and rescheduling,
  no zero-delay timer loop, focus catch-up, unmount cleanup, newer holds,
  equal-time/older/sub-millisecond replies, generic epoch0 redaction, same-user
  refresh, legitimate newer recovery, logout/login, cancellation and private cache.
- `npm run typecheck`, scoped ESLint and Prettier over all five changed files
  pass. Final focused log: `/tmp/phase08-10-final.log`.
- Independent review and complete affected-ordering re-review of frozen runtime
  `7473df3` report **0active findings**. CR01/CR02 regression/fix evidence is
  above; root owns its report and the pending final Wave8 full frontend gates.

## Deviations from plan

1. **[Rule2 — Required fixture integration]** StockSection's existing typed test
   fixture now explicitly provides action/valuation authority. No component runtime
   or visual behavior changed; Plan11 owns UI implementation.
2. **[Rule1 — Review bug]** Added full quote/session/reason/source-time coherence
   after independent CR01. Changed-server test fixtures now retain exact ages so
   ordering regressions reach the intended cache guards rather than malformed
   response rejection.
3. **[Rule1 — Review bug]** CR02 and executor regressions exposed authority
   reanchoring for identical snapshots, including before expiry. Strict exact
   server observation ordering prevents current replies from reanchoring.
4. Follow-up CR02 RED `3f4b477`: equal/older generic epoch0 redaction could still
   rewind independent closed-session metadata. GREEN `89c1322` retains the
   independent monotonic upper-clock/elapsed offset across all snapshots; generic
   redaction stays accepted and both cached/rendered sessions remain closed.
5. RED `6e20eeb`→GREEN `edfc623`: late generic envelopes could categorically restore
   revoked admission/calendar facts despite a preserved clock. A retained sanitized
   snapshot now merges only action reductions/quote removal, including after cache
   removal/remount; independent authority and original transport stay intact.
6. RED `bb6df5a`→GREEN `44d1fff`: merging public redactions must retain raw incoming
   higher held epochs and observation times, and new unavailable admission must
   retain its actual time instead of comparing null generation as an old approval.
   Separate raw observation maxima survive public merge decisions.
7. RED `724d71a`→GREEN `9242068`: approved generation5→generic denial→generation4
   could restore a lower permission generation. Independent approved-generation
   high-water now survives denial and query remount; actual auth alone resets it.
8. RED `54aa17b`→GREEN `7473df3`: full arrival RTT could erase higher epoch or
   permission-generation facts before first cache insertion. Both accepted paths
   now observe raw maxima after ordering checks and before local redaction;
   only sanitized cache observations replace the retained public snapshot.

## Next plan handoff

Plan11 consumes required `item.action` and `valuation_reason` without a healthy
fallback. Unknown/reconciling/suspended facts retain catalogue identity while
unsafe numbers remain unavailable. Use original checked/source times and fixed
reason enums only. No trading or History controls belong to Phase8. Parent owns
full frontend/browser/cross-stack proof and new Phase8 human acceptance; provider
activation and whole-phase requirements remain pending.

## Stubs and threat review

No blocking stubs, new endpoints, authentication mechanisms, file access patterns
or dependency surfaces. Threats T-08-10-01/02 retain exact validation, monotonic
cache ordering, full-RTT expiry and authenticated lifecycle regressions. Local
fixtures do not establish provider rights or live success.

## Self-Check: PASSED

All five changed source/test paths exist, all17 task/regression commits recorded above exist,
focused tests and scoped static checks pass. Whole-phase requirements remain
unchecked; independent re-review is clean and final root Wave8 proof remains
explicitly separate.
