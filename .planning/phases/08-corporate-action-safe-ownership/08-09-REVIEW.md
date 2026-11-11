---
phase: 08-corporate-action-safe-ownership
reviewed: 2026-11-11T15:37:35Z
depth: deep
review_head: f6e9d0a
review_source: frozen-runtime
files_reviewed: 7
files_reviewed_list:
  - backend/app/services/stocks.py
  - backend/app/schemas/stocks.py
  - backend/app/services/corporate_actions.py
  - backend/tests/test_stocks_api.py
  - backend/app/services/stock_quotes.py
  - backend/app/tasks/stock_scheduler.py
  - backend/tests/test_stock_quotes.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Plan08-09 Task1: Stock Action Projection Review

## Narrative Findings (AI reviewer)

### Final CR-01 re-review at `f6e9d0a`

**Zero active BLOCKER/WARNING findings in the reviewed Plan09 runtime scope.**
CR-01 is fully resolved: current actions generation mismatch returns the default
unknown envelope before any persisted epoch/check time is projected; applicable
calendar authority/deadline failures likewise return generic epoch0/null times.
Denied action purposes and missing/malformed facts retain their existing generic
fallback. The quote remains absent while all catalogue identities survive.

stocks.py SHA-256 is
`12c2bf3dfe16fa5446342adebe4b5ccae9f858b8a4260258c38b418f973e3fdc`.
Previously reviewed quote-writer/scheduler/shared-predicate source identities
are unchanged. The executor's regression/coverage work and parent's pending
Wave7 integration are separate verification evidence; no reviewer tests or
database operations were performed. Source review is clear for that integration.

### Full runtime freeze review after `3833fc5`

Task2 quote persistence and scheduler partitioning were additionally reviewed.
The calendar portion of CR-01 is fixed: action facts are generic when applicable
calendar purpose checks/deadline fail. The actions-generation portion remains
active: the code still changes a local rights boolean and then emits epoch/time,
rather than returning the generic envelope immediately.

No additional concrete BLOCKER/WARNING was found in the scoped Task2 code.
The writer takes the shared instrument gate, rereads quotes authority, assigns
only local current units, revalidates source age after waits and conditions the
write on current full permission/mapping/units. Nonzero units require exact
current applied boundary, source time strictly after it, current monitor health,
no unresolved holds/changed applied revision and no due unapplied split. The
conflict update retains source-time monotonicity and never lowers stored units.
The scheduler finishes provider HTTP before entering sorted one-instrument
caller-owned transactions and checks permission/lease before commit. No source
epoch is fabricated, and unrelated safety epochs do not relabel quote units.

Canonical unresolved boundaries continue to bound API validity independently
when an exact applied current-unit boundary consumes a stale cached marker.
The API retains final bounded READ COMMITTED authority and no await after its
fresh evaluation clock. Full operational proof and ongoing coverage runs are
executor work, not claimed here; the reviewer ran no tests or database calls.

Frozen working-tree runtime SHA-256 identities:

- stocks.py: `e63b7725cbc513f225ea622e1ba76c322285ab6b8f756c049a32da37e7e03405`
- schemas/stocks.py: `d1d7244d0ab562a51c7d697e1bc7b17b3c2562426eff807d22e139e93be1dfa0`
- corporate_actions.py: `6be8f49158009d9b1e9c927ec8d88813770085ff51f25d1a43d8ab5f0fdccfc3`
- stock_quotes.py: `0aeee6f1982802c1960c9cc7a83c5181507e9e4950c544c15ba74904f0f2d7e6`
- tasks/stock_scheduler.py: `5c9b255122f4b85ec7c15c5d1f42a458aba8882d2f6bdbe5e53be99dc7b194e2`

Reviewed the frozen Task1 API envelope, final committed authority query and
shared persistent-hold SQL predicate at `3833fc5`. Task2 quote-writer/scheduler
implementation remains in progress and is deliberately excluded. Review was
source-only: no tests, database/provider calls, runtime/source edits or commits.
Reported executor test results are not reviewer-executed evidence.

The SQL predicate preserves current-revision and exact held-history identity,
allows routine identical observations, and invalidates resolution applicability
after new material missing/uncertain observations. Bounded129-ID history refuses
oversized histories; casts are CASE guarded. Final API authority reads precede
the fresh clock, with no subsequent await; catalogue identities and disabled
execution remain separate from price disclosure.

Frozen SHA-256 identities:

- stocks.py: `c6cc1bef3f1271044bde75ccd515b0af8887f8e3ac88a2f44e4fcceae3a1a5a0`
- schemas/stocks.py: `d1d7244d0ab562a51c7d697e1bc7b17b3c2562426eff807d22e139e93be1dfa0`
- corporate_actions.py: `6be8f49158009d9b1e9c927ec8d88813770085ff51f25d1a43d8ab5f0fdccfc3`
- test_stocks_api.py: `aae56438ad24e8259d34ccc64f225859b20c4d26a7756742f9fdbcafd0a47882`

### CR-01 — BLOCKER, RESOLVED: Unavailable derived authority still discloses old action timestamps and epoch

**File:** `/home/YokaiExchange/backend/app/services/stocks.py:192`

**Also affected:** `_action_projection` output construction near lines224–229.

**Issue:** Early generic redaction occurs only when the initial actions-purpose
checks fail. When final calendar authority is revoked/missing/expired,
`session.valid_until` is None: evaluation returns unknown and suppresses prices,
but the projection still returns the persisted action epoch and checked_at.
Likewise an actions admission generation change sets `rights=False` only after
the early return; old-generation epoch/check time are still disclosed. These
facts were derived using authority that is now unavailable, contrary to the
plan's generic-unavailability/null-time boundary. Unknown monitor health with
otherwise current rights can expose a dated check legitimately; revoked or
unmatched authority cannot authorize that disclosure.

**Fix:** Complete current-generation actions and applicable calendar authority
checks before projecting any derived state metadata. Return the default generic
StockActionOut (epoch0, null checked_at/valid_until) when those checks fail,
retaining all20 catalogue identities and numeric/source-time suppression. Add
same-request calendar revocation/review-expiry and action-generation-change
regressions that assert the entire generic action envelope, not quote absence
alone. Keep normal closed-session behavior distinct from unknown calendar
authority.
