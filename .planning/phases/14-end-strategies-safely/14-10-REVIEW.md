---
phase: 14-end-strategies-safely
plan: "10"
reviewed: 2026-11-19
depth: standard
source_commit: 9b7e8bfa8f2c5a3c86b2240d93af42ee078f5dc6
initial_source_commit: 791f3c62e448a241a5fc112d943a62d57b43b741
diff_base: a3ee222
files_reviewed: 7
files_reviewed_list:
  - backend/app/services/portfolios.py
  - backend/app/services/history.py
  - backend/app/services/event_history.py
  - backend/app/api/v2/trades.py
  - backend/app/api/v2/stock_trades.py
  - backend/tests/test_portfolio_closure_privacy.py
  - backend/tests/test_portfolio_closure_races.py
initial_findings:
  critical: 0
  warning: 1
  info: 0
  total: 1
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 14 Plan 10 — Independent Code Review

## Narrative Findings (AI reviewer)

No proven production BLOCKER was identified in the submitted final-fence
changes. The initial review found one test-reliability WARNING: the retained
stock first-buy race assumed its receipt must win the separate final read race,
while the corresponding crypto assertion was updated for the new contract.
The test-only follow-up at9b7e8bf resolves that warning; its original finding
and resolution are both retained below. No blocker or warning remains.

Reviewed all seven scoped source/test files and their a3ee222→791f3c6 diff,
plus the read-authority inventory and called authorization, session, valuation,
crypto/stock execution, private-route and mixed-History paths. No structural
pre-pass was supplied. This review performed no test/runtime operation or
source change.

## Warnings — original finding retained, now resolved

### WR-01 — Stock first-buy race still requires a scheduling-dependent receipt

**Severity:** WARNING — test reliability.

**Initial file:** `backend/tests/test_portfolio_closure_races.py:220`
at791f3c6.

**Issue:** `test_first_buy_omitted_discovery_retries_entire_public_closure`
correctly observes the original closer waiting behind a genuine first stock
fill and asserts two closure SQL calls after rediscovery. It then unconditionally
requires the buy response to be201. The new stock route performs a separate
owner/active shared-root read after that fill commits. The queued closer can
finish its real40001 whole-transaction retry before this final read obtains
its lock; exact private404 is then the required result even though the fill,
two closure attempts, ledger and terminal global tail are all correct.

Nothing in this test orders the final receipt fence against the retried closer.
The retry's additional awaits make201 common, but do not establish that ordering.
This is the stock counterpart of the crypto assertion already corrected at
lines276–290. The new parameterized stock postcommit privacy test also explicitly
establishes that such a404 is a valid protected result.

**Concrete regression:** In the existing first-buy race, hold the stock API's
`fence_owned_active_portfolios` immediately before its real shared-lock call,
allow the already-queued public closer to complete its actual40001 retry and
commit, then release the final read. The current unconditional201 assertion
fails on the required private404 while `len(calls)==2` and the exact ledger/tail
assertions still pass. Use an event tied to the actual closer completion, not
a sleep or a mocked SQL outcome.

**Fix:** Accept only201 with the exact original stock/root/side/quantity/cash
receipt, or404 with the exact `portfolio_unavailable` body and private no-store/
Vary headers. Preserve the two genuine SQL attempts and every exact cash,
basis, grant, closure-count and terminal-tail assertion. Add the deterministic
postcommit final-fence ordering above to prove the404 branch; retain the separate
read-first/close-first privacy proofs. Do not broaden this to arbitrary errors
or change financial behavior.

**Resolution / independent recheck:** RESOLVED at9b7e8bf. The original race
now accepts only an exact original201 stock receipt or an exact private404
unavailable response with no-store/Vary. Original root/owner/coin, journal
sequence and epoch, fill cause, quantity/basis, global tail, trade price/cash,
grant counts and untouched sibling are independently asserted; normal closed
retry is refused and the frozen financial snapshot stays identical. This is
not a blanket status-code widening.

The new `close_before_final_read=True` variant pauses only the real stock
route's final read seam after genuine fill commit. It waits for the already
queued public closer to complete exactly two real SQL invocations after40001
rediscovery and return200 before releasing the read; the response must then
be404. Actual writer blocking and explicit completion events establish the
ordering without a sleep, mocked closure or invented retry. The existing
read-first stock privacy proof is unchanged and still requires201 while the
real closer waits behind the shared root fence.

Recheck read the actual test-only diff and execution-summary follow-up. Parent
evidence records4 targeted original/forced/read-first cases in27.870s and a
complete38-case affected race/privacy run in238.708s, plus scoped static
checks and owned cleanup. Production source is unchanged by this repair.
The reviewer performed no test/runtime operation or source edit.

## Assessed production boundaries

- Initial owner-active resolution remains unlocked. Final ordered account
  shared locks occur after all stock instrument work, service commits or
  original-replay rollback; no root-before-instrument lock inversion was added.
- The same request AsyncSession retains final shared locks until dependency
  cleanup. Metadata, list and both History projections obtain final authority
  after hydration; new financial routes also fence quote-bearing refusals.
- A final read losing to closure returns the existing private unavailable
  response. A committed fill remains retained when its later receipt is hidden;
  neither the service nor API claims an economic rollback at that point.
- Normal financial routes use owner-active dependencies and root-filtered
  services. Mixed-History original payment hydration includes owner/root
  predicates, cursors bind the root, and retired implicit v1 routes do not
  choose a root or load an original receipt. The sole owned-closed
  acknowledgement remains the separate minimal DELETE contract.
- The privacy tests use real public deletion and actual PostgreSQL waiter
  observation. Both final-fence orderings and populated original-reference/
  cursor matrices have concrete assertions rather than timing-only success.
- No SQL authority, schema, grants, dependency or historical profile changed.
  Source review does not imply whole-suite, coverage, image, encrypted/TLS
  recovery or human acceptance gates have passed; those remain later plans.

## Evidence limits and handoff

The initial combined diagnostic's45passes plus one old crypto assertion failure
are not treated as a fresh complete pass. The executor records the targeted
amendment and separate valuation, role and cursor results; this review did not
rerun them. The known Plan15 historical fixture prerequisite remains unresolved.

Plan13 must preserve the original unknown financial identity if a committed
fill receives private404 after closure, and must not retry it against a
replacement strategy. WR-01 is resolved; later whole-source, critical coverage,
browser and encrypted/TLS qualification obligations remain unchanged.
