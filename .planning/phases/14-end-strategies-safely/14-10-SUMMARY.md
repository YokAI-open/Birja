---
phase: 14-end-strategies-safely
plan: "10"
subsystem: private-financial-read-authority
tags: [postgresql, privacy, lifecycle, history, concurrency, portfolios]
requires:
  - phase: 14-09
    provides: Current0023 public closure, canonical bigint identity and real writer races
provides:
  - Final ordered owner-active shared root fences for metadata and both History services
  - Final financial route fences after hydration, execution commit or original replay rollback
  - Exhaustive normal-route and original-reference query authority inventory
  - Real public-DELETE privacy and both-order lock proofs
affects: [14-13, 14-15, 14-16, 14-18, critical-coverage]
tech-stack:
  added: []
  patterns:
    - Final shared root read authority remains held through request-session cleanup
    - Committed economic effects remain retained when a later receipt read loses to closure
key-files:
  created:
    - backend/tests/test_portfolio_closure_privacy.py
    - .planning/phases/14-end-strategies-safely/14-READ-AUTHORITY.md
  modified:
    - backend/app/services/portfolios.py
    - backend/app/services/history.py
    - backend/app/services/event_history.py
    - backend/app/api/v2/trades.py
    - backend/app/api/v2/stock_trades.py
    - backend/tests/test_portfolio_closure_races.py
key-decisions:
  - Keep the initial owner-active resolver unlocked; final root fences follow all stock instrument work.
  - Fence quote-bearing refusals and original receipts as well as successful previews and holdings.
  - Return exact private unavailable after closure even if the economic fill committed earlier.
requirements-completed: []
requirements-progress: [PCTX-03, PSAFE-01, PMGT-04]
duration: 18min measured first-RED-receipt-to-cleanup interval
completed: 2026-11-19
---

# Phase 14 Plan 10: Final Private Read Authority

**Normal portfolio metadata, History, previews, holdings and execution receipts
cannot publish a closed root after their final authority check; real shared locks
keep a later public closer waiting until the authorized response completes.**

## Performance and task commits

First RED receipt completed at2026-11-19T14:17:24UTC. Owned cleanup completed
at14:35:31UTC; resource absence was verified afterward. This interval includes
implementation and diagnostics, not a routine test-latency claim. Both tasks
are complete. Parent retains STATE/ROADMAP/requirements ownership; these three
requirements remain phase-level work in progress.

| Task | Commit | Result |
|---|---|---|
|1 RED|2d98baf|After metadata hydration, real public closure commits; old response exposes the retained name with200 instead of404. Actual9.291s.|
|1 GREEN|39e0599|Ordered final shared owner-active metadata/list and trade/mixed History fences; eight real both-order cases pass.|
|2 RED|2d005ec|After real crypto quote hydration, public closure commits; old response exposes financial data with200 instead of404. Actual9.266s.|
|2 GREEN|106e381|Final crypto/stock route success/refusal fences, original/cursor privacy matrix, both-order financial and existing valuation proofs, approved retained-race assertion amendment.|

Both TDD tasks have separate genuine failing-test commits preceding their fixes.
No app schema, SQL, grants, dependencies, image pins or provider activation changed.

## Proven behavior

- `fence_owned_active_portfolios` selects exact same-owner active IDs in stable
  order with `FOR SHARE`, retaining locks on the request's existing session.
  Metadata/name/description and both History projections acquire this fence only
  after hydration. The initial dependency remains unlocked, preserving stock
  instrument→root order and avoiding a root lock upgrade before later stock work.
- Crypto and stock quote/context/holding, new execution, stored original-key
  receipt replay and quote-bearing reprice refusal all fence their final response.
  A service commit or replay rollback is followed by a new read transaction;
  none of this falsely claims an already committed fill was rolled back.
- Actual public DELETE after initial resolution/hydration, but before final
  authority, returns exact private404. The opposite order observes actual
  `pg_blocking_pids` while the closer waits behind the reader's root share lock.
  This covers metadata/list, both History services, crypto/stock fill responses
  and the existing overview/detail valuation membership fence.
- Closed, foreign and missing roots produce the same unavailable response across
  normal metadata/detail, trade/mixed History, holdings/context, previews and
  execution/original-key URLs. Responses retain private no-store policy.
- Mixed History embeds only same-owner/root original dividend and correction
  records. Old seek cursors cannot target a sibling; even a forged root-bound
  cursor cannot hydrate an old root's original record through the sibling query.
  Same-name newly created roots have different IDs and cannot use old financial
  idempotency keys to spend replacement cash.
- Retired implicit v1 finance routes return authenticated private409
  `portfolio_required`; they neither choose nor create a root nor expose an old
  receipt. DELETE remains the sole minimal owned-closed lifecycle acknowledgement.
- Existing restricted app/scheduler tests retain direct lifecycle mutation denials
  and the exact app-only closure-function boundary. Scheduler jobs do not serve
  authenticated browser read routes, and their grants were not broadened.

See `14-READ-AUTHORITY.md` for the exact route→service→query inventory and executable
selectors, including already-satisfied paths. No additional original-event endpoint
exists; original references are embedded in root-filtered mixed History hydration.

## Verification evidence

Sanitized command logs, JSON elapsed-time receipts and synthetic test runner are
retained in `/tmp/birja-phase14-plan10/`.

| Receipt | Actual result | Elapsed |
|---|---|---|
|task1-qualified|8 metadata/History both-order cases pass|49.337s|
|task2-green|10 late crypto/stock quote/context/fill/retry/reprice cases pass|63.732s|
|task2-matrix|2 cursor/original/retired-v1 matrix cases pass|16.728s|
|final-privacy|45 pass; the retained crypto race's old unconditional201 assertion fails with the required exact private404|280.736s|
|valuation-roles-retry|4 new overview/detail public-DELETE both-order cases pass; the `-k` selector intentionally reports28 other cases deselected|27.228s|
|role-race-final|Approved crypto postcommit assertion plus app/scheduler authority negatives:6 pass|36.049s|
|history-cursor-regression|28 existing cursor/root/bounds cases pass;15 historical-fixture cases deselected|3.147s|
|final-all-lint|Scoped Ruff passes all changed source/tests|0.039s|
|final-format-check|Seven source/test files already formatted|0.044s|
|mypy|Six service/route modules pass|0.795s|

The final batches cover26 new privacy cases, all existing public closure API and
lock-order race cases, and the selected restricted-authority/cursor regressions.
The single observed retained assertion failure was corrected and specifically
rerun; this summary does not mislabel that initial combined command as green.
No full-suite, coverage, image-scan or recovery qualification is claimed here.

The separately tracked historical creation/dividend fixture still expects0020;
its repair belongs to Plan15. Its15 scoped-History DB cases were not substituted
for current0023 acceptance or reported passing. Current real HTTP tests directly
exercise populated trade/mixed History, original corrections and cursor privacy.

## Deviations and issues

**Parent-approved narrow test amendment:** The real retained
`test_crypto_fill_before_closure_preserves_exact_fill_and_basis` run proved its
economic fill committed, while the queued closer won the later receipt fence.
Parent explicitly added ownership of that one assertion in
`backend/tests/test_portfolio_closure_races.py`. It now permits only exact private404
with no financial fields, or201 with the original root/BTC/buy/quantity/cash
receipt. Every original exact ledger, basis, count and frozen-finance assertion
remains. New deterministic tests separately prove both fence orders. This changes
no financial, authority, security or service gate.

No other scope deviation, dependency installation or authentication gate occurred.
No TODO/stub or new endpoint/trust boundary was introduced. The inventory and tests
implement the existing T-14-10 mitigation without accepting a new threat.

## Resources and preservation

- Exclusive `birja-p14-10` PostgreSQL/Redis stack used synthetic test credentials,
  fake prices and console email; no `.env`, dev/prod data or provider calls.
- `docker compose --env-file /dev/null -p birja-p14-10 -f docker-compose.test.yml
  down -v` removed both owned containers and network. Label-filtered container,
  network and volume checks returned no objects afterward. No other stack changed.
- No tracked files were deleted. Unrelated untracked `.claude/` was preserved.
- Historical migration/profile/lock/image/deploy SQL paths are unchanged from
  a3ee222. The retained Phase13 recovery archive remains SHA256
  `6fb79a45ddcb10725b18fc756e71bd555c827a6e61a5a4a0bd2d183096114b92`.

## Handoff

Plan13 may consume these exact private404 responses: a stale original receipt
must not reopen a closed strategy or retarget a same-name replacement. A committed
fill remains retained even when its later response is unavailable; the UI must
not describe that as a failed financial rollback or retry it against another root.
Already delivered bytes cannot be retracted by a later closure.

Plan15 retains historical fixture integration; Plans16–18 retain critical coverage,
whole-source/security and same-archive/TLS recovery gates. Plan19 retains owner
UI/native200% acceptance. No push, merge, deployment or live provider operation
was performed or newly authorized.

## Self-Check: PASSED

All created artifacts and all four task commits were verified present. Scoped
diff checks pass; no tracked deletion or unresolved owned change remains outside
this summary. Parent-owned planning state is intentionally unchanged.

## WR-01 review follow-up — stock first-buy response ordering

The independent `14-10-REVIEW.md` warning remains preserved as originally
written. Parent authorized a test-only follow-up in
`test_portfolio_closure_races.py`; no production source change was required.

The original first-buy omission case now accepts only an original201 receipt
with exact root/coin/AAPL/buy/IEX identity and independent bid100, ask102,
midpoint101, quantity1, execution/notional102, zero fee, cash10000→9898 and
holdings0→1; or exact private404 `portfolio_unavailable` with no receipt/quote
fields and no-store/Vary headers. It still observes the real original closer
blocked behind the stock writer and requires exactly two actual closure SQL
invocations after the genuine whole-transaction40001 retry.

A second deterministic variant pauses the stock route immediately before its
final shared read, after the real fill commits. It waits for the actual public
closer to complete both attempts and return200 before releasing the final read,
then requires404. Events and observed PostgreSQL blockers establish the ordering;
there is no mocked financial outcome, fabricated SQL retry or timing sleep.

Both variants independently verify the stored journal's original root/owner/coin,
sequence1/epoch0, fill cause, quantity0→1 and basis0→102, global tail1, retained
trade/execution/cash, two grants totaling20000, exact original book and untouched
sibling. A subsequent normal closed trade is refused and the complete frozen
financial snapshot remains identical. The existing stock read-first privacy test
remains unchanged and still requires201 while the actual closer is blocked.

Targeted original/forced cases and the unchanged crypto/stock read-first tests
passed4 cases in27.870s. The final full affected race/privacy run then passed
all38 cases in238.708s (236.60s pytest time), including the additional independent
stored journal/frozen-state assertions. Scoped Ruff passed in0.040s; the unchanged
stock route's mypy contract passed in0.446s; final test format check passed
in0.048s. Actual receipts/logs are `/tmp/birja-phase14-plan10/wr01-*.json` and
matching `.log` files. Both owned test containers and their network were removed
again with the same explicit project-scoped cleanup command. No app/runtime,
dependency, authority, provider, production or parent planning-state change occurred.

**Plan13 financial uncertainty handoff:** Execution404 may follow a committed
fill whose later receipt became private. If the receipt cannot be verified,
preserve the original immutable attempt identity, original portfolio ID, request
body/idempotency key and unresolved-outcome state; never discard that uncertainty,
assert an economic rollback, or retry the attempt against a replacement root.
A preview404 alone does not imply an unknown economic execution outcome.
