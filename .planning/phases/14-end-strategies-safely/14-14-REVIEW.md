---
phase: 14-end-strategies-safely
plan: "14"
reviewed: 2026-11-19T16:25:26Z
depth: standard
source_commit: d66554b54df52b5b9417b48b88889b49e81e7954
review_head: 873037e073df4d20b31de73484aabd7b36a45f4d
diff_base: 407f4df
repair_source_commit: ee28364b8983c2ea8db55c3691238c3c94502733
repair_evidence_commit: 3af3cbc
initial_files_reviewed: 12
files_reviewed: 14
files_reviewed_list:
  - frontend/src/components/PortfolioDeleteForm.tsx
  - frontend/src/components/PortfolioDeleteForm.test.tsx
  - frontend/src/components/PortfolioMetadataForm.tsx
  - frontend/src/components/PortfolioMetadataForm.test.tsx
  - frontend/src/pages/PortfolioDeletionPage.tsx
  - frontend/src/pages/PortfolioDeletionPage.test.tsx
  - frontend/src/pages/PortfoliosPage.tsx
  - frontend/src/pages/PortfoliosPage.test.tsx
  - frontend/src/pages/PortfolioPage.tsx
  - frontend/src/pages/PortfolioPage.test.tsx
  - frontend/src/App.tsx
  - frontend/src/App.test.tsx
  - frontend/src/components/PortfolioTargetBoundary.tsx
  - frontend/src/components/PortfolioTargetBoundary.test.tsx
initial_findings:
  critical: 0
  warning: 3
  info: 0
  total: 3
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 14 Plan 14 — Independent Code Review

## Narrative Findings (AI reviewer)

Reviewed the complete twelve-file source/test scope and its diff, tracing the
deletion, metadata, target and unavailable-boundary calls against the repaired
Plan12/13 contracts. Three reachable UI robustness/accessibility defects remain.
No financial integrity or authorization bypass was identified in this scope.
No structural pre-pass was supplied.

**Repair re-review:** All three warnings are resolved inee28364, with execution
evidence recorded at3af3cbc. Original findings, submitted-source provenance and
initial counts are preserved below. The final review scope includes the two
explicitly authorized boundary presentation files. No blocker or warning
remains after source/diff re-review; this is not a reviewer test execution.

## Warnings

### WR-01 — Failed metadata proof after a terminal refusal hides its recovery action

**Severity:** WARNING

**Recheck status:** RESOLVED inee28364; original finding retained below.

**File:** `/home/YokaiExchange/frontend/src/components/PortfolioDeleteForm.tsx:115`

**Related call paths:** `frontend/src/components/PortfolioMetadataForm.tsx:28–30`;
`frontend/src/hooks/usePortfolioDeletion.ts:515–525`;
`frontend/src/hooks/usePortfolioTarget.ts:265–266`.

**Issue:** On a durable `portfolio_confirmation_changed` refusal, the hook clears
the original attempt and keeps the root quarantined until a fresh successful
owned-active metadata response. The persistent host receives `available=false`
throughout this interval. If that metadata request fails, this early return
hides the terminal-refusal message and its `Review latest portfolio` action.
The editor, which otherwise supplies metadata-error retry, is also unmounted
while unavailable. Target status stays `unavailable` because quarantine takes
precedence over query errors, so the normal boundary offers no retry either.

The owner sees a generic unavailable portfolio after a known noncommit refusal,
without the promised fresh same-ID review or explicit metadata-proof retry.
The overview also has no original-request link because the attempt is already
resolved. A focus event or route departure/remount might eventually recover it;
neither is a discoverable error action on the current page. Financial masking
must remain in force, but should not hide safe metadata recovery.

**Reproduction:** Open named review on `/portfolios/1`; return the exact terminal
409 from DELETE; fail the following `/portfolios/1/metadata` read. Keep the owned
list reporting root1 active. Assert that no financial subtree revives, but a
visible same-ID metadata retry remains and can recover the new name without
another DELETE. The current form returns null in that state. Existing rename
tests always let this read succeed and do not exercise this interleaving.

**Fix:** Render a current-owner/root terminal-refusal recovery surface before
the generic unavailable early return. Give it an explicit guarded
`refreshMetadata` action and metadata-loading/error state while preserving
quarantine, immutable terminal resolution and absence of financial content.
Do not release quarantine based on the active list or resend DELETE. Cover
failure and successful explicit retry through the real App route.

### WR-02 — Valid detail URLs with a trailing slash lose management and their h1

**Severity:** WARNING

**Recheck status:** RESOLVED inee28364; original finding retained below.

**File:** `/home/YokaiExchange/frontend/src/App.tsx:36`

**Related source:** `frontend/src/App.tsx:48–65`;
`frontend/src/pages/PortfolioPage.tsx:33–36`.

**Issue:** React Router's index route accepts `/portfolios/1/`, but `detail`
requires literal equality with `/portfolios/1`. On the trailing-slash URL the
financial index still renders while the relocated primary heading and the
entire metadata/deletion host are omitted. Users can view the portfolio but
cannot edit or delete it, and the route has no h1 for the shell's heading-focus
behavior. This is a regression introduced by moving those controls out of the
financial page and gating them with a narrower URL predicate than the router.

**Reproduction:** Open the actual App at `/portfolios/1/` with successful current
identity, membership, metadata and financial responses. The financial statement
mounts, but `Portfolio`, `Edit portfolio` and `Delete portfolio…` are absent.
Existing routed fixtures exclusively use the exact canonical no-slash path.

**Fix:** Identify the detail index using the router's route-matching semantics
(an end-matched detail pattern or index-owned route context), or normalize the
URL with a safe replace redirect before rendering. Preserve the canonical
decoded portfolio-ID validation, absence of management on History/trade
children, and exact route lifetime invalidation. Add a real routed
trailing-slash regression asserting one primary heading and both management
actions.

### WR-03 — Pending and unknown detail pages put their h2 before the page h1

**Severity:** WARNING

**Recheck status:** RESOLVED inee28364; original finding retained below.

**File:** `/home/YokaiExchange/frontend/src/App.tsx:48–66`

**Related source:** `frontend/src/components/PortfolioDeleteForm.tsx:130–137`;
`frontend/src/components/PortfolioTargetBoundary.tsx:131–138`.

**Issue:** The relocated primary h1 exists only while the target is ready.
Submitting deletion intentionally makes that target unavailable while keeping
the deletion host mounted. The host then emits `Deleting portfolio…` or
`Deletion result unconfirmed` as h2, followed later by the boundary's
`Portfolio unavailable` h1. The same reversed outline occurs when restoring
an unknown original directly on its detail URL. The new pending/recovery
section is consequently outside the heading hierarchy of the page it explains.
This is a semantic accessibility defect, not a claim that an automated browser
or a specific WCAG criterion has failed.

**Reproduction:** Hold DELETE pending after confirming on `/portfolios/1`, then
reject it as transport-unknown. In both states inspect routed headings in DOM
order: the first is the deletion h2 and the later one is the boundary h1.
The static `/portfolios/deletion` route already has the correct h1-first order.

**Fix:** Give the detail layout ownership of exactly one appropriate generic
page h1 before its metadata/recovery sections across ready and unavailable
states, coordinating the boundary heading so it does not duplicate that h1.
Alternatively place the unavailable primary heading before the retained
metadata-only region without remounting the deletion operation. Keep cached
closed names/finances hidden and preserve current-only focus behavior. Add
routed pending, unknown and restored-unknown assertions for h1-first order and
exactly one h1, using the real page rather than its existing extra-h1 probe.

## Evidence and scope limits

The source preserves explicit own-button confirmation, escaped captured names,
pre-submit Cancel/Escape, durable-original replay, metadata exclusion at hook
level, current receipt navigation, authenticated static recovery and accepted
overview projections. These inspected paths do not negate the findings above.

The executor records1,321 full frontend and128 affected passing tests plus
type/lint/format qualification at the submitted source. This reviewer performed
source review only: no tests, browser, services, database, provider, package,
production or publication operation. The only created file is this review.
Actual browser/reflow evidence remains Plan17, whole qualification Plan18, and
separate human UI/native200 outcomes Plan19. No phase requirement is completed
by this report. Unrelated `.claude/` content remains untouched.

## Repair source re-review — all three warnings resolved

- **WR-01:** The form captures the validated review's original ID as well as a
  persisted attempt. Before its generic unavailable return, it now permits a
  same-root terminal-refusal recovery surface. Its text is generic and exposes
  no cached name, description or financial content. The only recovery action
  invokes the existing current-scope `refreshMetadata` for that original ID;
  metadata failure/loading is explicit, and the financial editor remains
  unmounted. Fresh successful metadata remains the hook's only release proof.
  The real App/actual PortfolioPage regression observes initial failed proof,
  another explicitly failed metadata retry with focused error and no finance,
  and a subsequent successful retry. DELETE count remains one through those
  reads and through opening the newly named review; only intentional final
  confirmation sends the second DELETE, to the original ID. No hook, transport
  or quarantine rule was relaxed.
- **WR-02:** The detail predicate now uses React Router's end-matched pattern
  while retaining canonical portfolio-ID validation. Canonical and
  trailing-slash actual-page tests exercise management availability, Cancel
  focus/restore, pending submission and unknown recovery. Complementary nested
  History/crypto/stock cases assert no management host. The unavailable
  trailing-slash case receives stale private metadata but renders none of it.
- **WR-03:** The detail layout owns one stable generic h1 ahead of its
  persistent management host, including loading and unavailable states. The
  optional boundary `primaryHeading` ref suppresses its duplicate heading and
  directs existing initial-refusal/removed-control focus to the supplied node.
  The default remains its own h1 when no external ref is supplied. Actual-page
  tests assert first-heading h1 order and exactly one h1 in pending, unknown
  and restored-unknown states; the original financial probe's extra h1 is
  explicitly bypassed for these assertions. A separate boundary regression
  checks private refusal focus through the external ref, and existing default
  boundary/privacy tests remain intact.

Reviewed the complete production repair diff, new actual-page and boundary
tests, unchanged lifetime guards and summary repair appendix. No additional
source defect was found. The executor records genuine REDfcce369, the corrected
canonical-readiness RED receipt, and qualified GREENee28364:1,330frontend tests
in24.76s,146affected in10.27s, plus whole typecheck/lint/format. Those are executor
receipts, not independently repeated runs. No source, test, service, database,
provider, package, production or publication operation was performed by this
reviewer; only this artifact was updated. Later whole-source/browser/human
gates and all seven pending whole requirements remain unchanged.

---

_Reviewer: independent gsd-code-reviewer; standard source review._
