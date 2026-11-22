---
phase: 14-end-strategies-safely
plan: "13"
reviewed: 2026-11-19T15:29:08Z
depth: standard
source_commit: 2834a95
review_head: 231ec02149810b443c989b6fb8c337b038573cf5
repair_source_commit: 311d61313da89b25130b7da0f32bb7895829f95f
qualified_repair_commit: ba9bba15860abe7b68d0dcf3321dd1094a2395f9
repair_evidence_commit: e163089
diff_base: e5c5bd9
files_reviewed: 17
files_reviewed_list:
  - frontend/src/lib/portfolioMetadataEvents.ts
  - frontend/src/lib/portfolioMetadataEvents.test.ts
  - frontend/src/hooks/usePortfolioTarget.ts
  - frontend/src/hooks/usePortfolioTarget.test.tsx
  - frontend/src/hooks/usePortfolioOverview.ts
  - frontend/src/hooks/usePortfolioOverview.test.tsx
  - frontend/src/hooks/usePortfolioDeletion.ts
  - frontend/src/hooks/usePortfolioDeletion.test.tsx
  - frontend/src/hooks/portfolioCrypto.test.tsx
  - frontend/src/hooks/portfolioStock.test.tsx
  - frontend/src/components/PortfolioTargetBoundary.tsx
  - frontend/src/components/PortfolioTargetBoundary.test.tsx
  - frontend/src/components/PortfolioSwitcher.tsx
  - frontend/src/components/PortfolioSwitcher.test.tsx
  - frontend/src/pages/TradePage.test.tsx
  - frontend/src/App.test.tsx
  - frontend/src/test/setup.ts
initial_findings:
  critical: 2
  warning: 0
  info: 0
  total: 2
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 14 Plan 13 — Independent Code Review

## Narrative Findings (AI reviewer)

Reviewed the 17-file change set and necessary ownership, identity, recovery-storage,
transport and previous Plan12 exclusion contracts. The initial review found two
deletion-session lifetime defects, preserved below. These findings follow reachable source paths; this reviewer did
not run tests, modify source, access providers or perform runtime operations.
No structural pre-pass was supplied. Automated validation reported by the
executor and future browser/human acceptance do not establish these edge cases.

**Repair re-review:** Both blockers are resolved in311d613, qualified by the
strengthened tests atba9bba1 and recorded ate163089. Reviewed the complete repair
diff, real-marker regressions and summary repair appendix. No blocker or warning
remains in the reviewed scope. This is a source re-review; the reviewer did not
rerun tests or claim browser/human acceptance.

## Critical Issues

### CR-01 — Returning to a retired client retains an obsolete quarantine forever

**Severity:** BLOCKER

**Recheck status:** RESOLVED in311d613; original finding retained below.

**File:** `/home/YokaiExchange/frontend/src/hooks/usePortfolioDeletion.ts:312–319`

**Issue:** Client replacement discards the retired session's recovery handle and
visible state, but preserves its `quarantined` set and `releaseAfterReview`.
Restoration at281–292 subsequently only adds an outstanding persisted attempt;
an empty durable marker does not reconcile old quarantine entries.

Concrete sequence: client A submits root2 and receives an unknown result; client B
mounts for the same owner and restores that original. B explicitly checks it and
receives the definitive `portfolio_confirmation_changed` refusal, resolves the
durable marker, and obtains fresh active root2 metadata. B releases its own
quarantine. After a genuine remount of A, A restores the now-empty marker and
becomes ready, but root2 remains in A's old quarantine. A has no remaining original
to check, and its `releaseAfterReview` was never set by B. Fresh active metadata
cannot release it. Target, switcher and overview therefore keep an active
portfolio inaccessible until identity reset or a full reload.

**Fix:** Reconcile generation-local quarantine when claiming/restoring a new
client generation. Reconstruct unresolved-operation quarantine from the current
owner-bound durable marker and require fresh owned-active proof before releasing
obsolete masks; do not expose a formerly closed root through retired cached
active membership. Preserve serial invalidation of old captures and never release
a still-persisted unknown attempt merely because GET returns active. Add the
A-unknown → B-terminal-refusal/fresh-active-proof → A-remount regression; assert
that a newly captured A target works while the original A handle stays revoked.

### CR-02 — An initially unknown identity resolving signed out skips private cleanup

**Severity:** BLOCKER

**Recheck status:** RESOLVED in311d613; original finding retained below.

**File:** `/home/YokaiExchange/frontend/src/hooks/usePortfolioDeletion.ts:142–153`

**Issue:** A session initialized while `['me']` is absent has `known=false` and
`owner=null`. If the current client's identity request then resolves explicit
`null`, the subscription sets `known=true` at152, but `owner !== session.owner`
is false. The guarded cleanup at167–168 is never reached. The known-null mount
check at322 has already run with `known=false`, and its dependencies do not change.
An existing private deletion marker (including its captured name and original
intent) consequently survives an authoritative signed-out result. Mounting the
same hook after null was already cached does clear it, so cleanup depends on
request timing. The same hole follows identity-cache removal and a subsequent
explicit null result without an intervening nonnull identity.

**Fix:** Distinguish unknown cache absence from the transition to an explicitly
known-null identity even when both map to `owner=null`. On the latter transition,
revoke private session state and clear the marker only under the current-client
guard. Preserve the durable marker for undefined/removed/GC identity and prevent
obsolete-client null events from clearing newer storage. Add regressions with a
preexisting original, initial absent `['me']`, and a later current-client null;
contrast with undefined/GC and obsolete-client null cases.

## Repair Review Evidence

- CR-01: Restoration retains readiness=false while it opens the guarded durable
  lease, cancels the old exact owner-list query, invalidates it without automatic
  refetch, and performs a new owned-list fetch with staleTime0/retryfalse. Owner
  and captured-generation guards surround the awaits and the query function.
  Only freshly present active IDs release former masks; the currently persisted
  original is explicitly excluded from release. Closed/missing old IDs remain
  masked. Retirement clears the old releaseAfterReview so a later detail update
  cannot release another generation's unknown original. Proof failure leaves the
  handle uninitialized/readiness false and offers the existing explicit retry;
  it does not submit DELETE.
- CR-01 regressions exercise terminal refusal, verified closure with warm cached
  active bytes, proof failure/retry, and a different new durable original. They
  assert that the explicit B recovery reaches DELETE and the expected durable
  result, that A stays unavailable while fresh proof is withheld, that only a
  newly captured A target revives, and that old target/confirm captures remain
  inert. Repeated active proof does not release the new unknown original. The
  summary records an isolated pre-repair RED replay after fresh GET, preventing
  stale-list timing from disguising the initial defect.
- CR-02: The subscription now records unknown-to-known-null independently of
  owner equality and enters the same guarded revocation/cleanup path. Current
  explicit null clears the private envelope; unknown absence still preserves it,
  and old-client cleanup remains barred by the current-client binding. The cold
  and removed-identity tests use real persisted originals, hold the identity
  request while asserting preservation, then deliver authenticated refusal/null
  and assert cleanup without any portfolio transport.
- Executor qualification recorded in13-SUMMARY: final frontend58files/1,291tests
  passed in25.60s, focused deletion/target88tests passed in4.01s, and final
  typecheck/lint/format/diff checks passed. These are executor receipts, not a
  separately repeated reviewer test run. The repair adds no backend, storage
  format, transport contract, dependency or runtime change.

---

_Reviewer: independent gsd-code-reviewer; source-only standard review with necessary cross-file tracing._
