---
phase: 14-end-strategies-safely
plan: "12"
reviewed: 2026-11-19
depth: standard
source_commit: ff76617
initial_source_commit: 88875238c969d0200982a2f63d5714543283265a
repair_source_commit: 302a9de
diff_base: ab3e0e7
files_reviewed: 4
files_reviewed_list:
  - frontend/src/hooks/usePortfolioDeletion.ts
  - frontend/src/hooks/usePortfolioDeletion.test.tsx
  - frontend/src/hooks/usePortfolioManagement.ts
  - frontend/src/hooks/usePortfolioManagement.test.tsx
initial_findings:
  critical: 2
  warning: 0
  info: 0
  total: 2
intermediate_findings:
  source_commit: cb3a0fd
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

# Phase 14 Plan 12 — Independent Code Review

## Narrative Findings (AI reviewer)

Two BLOCKER findings affect the original portfolio's metadata exclusion.
Reviewed all four scoped files and their changes, with Plan11 transport/storage,
identity/target helpers and the prescriptive UI/interface contracts as call-path
references. No structural pre-pass was supplied. This review does not count
future Plan13/14 rendering as already implemented.

The original findings below are preserved. Re-review of302a9de/cb3a0fd resolves
both production blockers. The final test-only recheck atff76617 resolves the
subsequent regression reliability warning; no blocker or warning remains.

## Critical Issues

### CR-01 — Metadata writes are enabled before recovery has been established

**Severity:** BLOCKER

**Recheck status:** RESOLVED in302a9de; original finding retained below.

**File:** `frontend/src/hooks/usePortfolioManagement.ts:209–212`

`metadataWritable()` checks only `isPortfolioDeletionQuarantined`. A new deletion
session has an empty quarantine and a null recovery handle; `restore()` fills
quarantine only after the asynchronous owner-binding/storage check succeeds
(`usePortfolioDeletion.ts:243–261`). During that check, or permanently after a
storage restoration error, `portfolioDeletionAuthorityReady` is false but
`metadataWritable()` remains true. An owned metadata response/draft can therefore
produce a PATCH for the persisted unresolved original before the hook has proved
that it is safe. `metadataBlocked` also reports false in this state.

The guarded sending methods consult the same incomplete predicate at
`usePortfolioManagement.ts:502–508`, `518–525` and `532–545`, so a disabled future
button alone would not protect already captured metadata handlers. This is a
gap in the submitted hook's fail-closed/exclusion boundary, not a request to
implement the later financial Outlet or UI now. The storage helper's synchronous
persist-before-DELETE guarantee does not cover this earlier rehydration period.

**Concrete regression:** Seed a valid owner-bound deletion marker containing root2
and usable root2 metadata, then defer the recovery-binding digest before mounting
the deletion and management hooks. While deletion authority readiness is false,
invoke edit/review/save, including a captured save handler. No PATCH may occur.
Repeat with failed/corrupt recovery storage; management must stay blocked until
safe initialization succeeds. After initialization, an unrelated active root
must become writable while the unresolved original remains blocked.

**Fix:** Include owner/session deletion recovery readiness in the management
write gate and arrange initialization for the management consumers. Keep this
an action-level guard and expose the same blocked state to UI consumers. Do not
merely add a later presentation condition or infer an absent original from a
failed storage read. Preserve unrelated sibling metadata availability once the
owner-bound recovery state is known.

### CR-02 — Named deletion review and unsaved metadata are not mutually exclusive

**Severity:** BLOCKER

**Recheck status:** RESOLVED in302a9de; original finding retained below.

**Files:** `frontend/src/hooks/usePortfolioDeletion.ts:100–107,313–341`;
`frontend/src/hooks/usePortfolioManagement.ts:209–212`

The UI contract's Placement rule3 explicitly forbids simultaneous metadata
editing and deletion review: a draft must be finished/discarded before deletion,
and opening named deletion review must block metadata editing until Cancel or
resolution. `metadataBusy()` only inspects `pending` and `awaitingFetch`; it
ignores an existing `draft` and `reviewRequired`. Consequently `reviewDeletion`
can open and `confirmDeletion` can send while unsaved metadata still exists.
The current test `usePortfolioManagement.test.tsx:623–628` demonstrates this
path by creating a draft, entering deletion review and successfully reaching an
unknown submitted deletion.

In the reverse direction, opening deletion review does not add quarantine,
which correctly belongs to submission. However, `metadataWritable()` has no
separate review-exclusion predicate. A current or captured metadata edit handler
can modify the same root while its named confirmation remains open. A
description-only draft does not change the authoritative cached name, so
`canConfirm` can remain true and deletion can proceed over that unsaved work.
Existing pending-save exclusion only starts after PATCH is launched; it does
not implement the required draft/review boundary.

**Concrete regressions:**

- Create an unsaved name or description draft, then call `reviewDeletion`; it
  must refuse without dropping that draft or sending DELETE. Cover an existing
  `reviewRequired`/uncertain metadata editor as well.
- Open named deletion review without a draft, then invoke captured metadata
  edit/review/save handlers. They must not change its editor state or send PATCH.
  Cancel must release metadata editing without sending DELETE.
- Confirm that another root's draft and metadata editing remain independent.

**Fix:** Treat unresolved/drafted metadata as busy when entering/confirming
deletion, and expose an exact-owner/root metadata-only exclusion for open
deletion review. Consume that predicate in all management edit/review/save gates.
Do not misuse financial quarantine for pre-submit review, and do not silently
discard the draft. Update the existing exclusion test to avoid using the
forbidden draft-plus-deletion setup as a successful scenario.

## Other assessed boundaries and evidence limits

- The store is QueryClient-scoped and preserves an immutable original outside
  a financial route lifetime. Persistence precedes transport; restoration does
  not submit a mutation. Only a matching receipt or durable terminal refusal
  resolves the stored original.
- Operation/route/owner guards suppress obsolete responses and completion
  callbacks; active GET/list data cannot resolve an unknown request. A failed
  discovery can coexist with known closure. Metadata rename-back revokes a
  review and captured handlers recheck post-submit quarantine.
- The exact Plan13 selectors and Plan14 receipt/guard contract are documented;
  their later rendering/cache integration is not credited or flagged here.
- The executor records1264frontend and152affected passing tests. The two missing
  interleavings above are not established by those passing counts. This reviewer
  did not rerun tests or perform runtime, DB, provider, package or production
  operations. No source file or parent-owned artifact was changed.
- All whole-phase requirements remain pending. Human UI/native200 acceptance
  and final whole-source qualification remain later required gates.

## Re-review of the production repair

The new `isPortfolioDeletionMetadataBlocked` combines owner-bound initialization
readiness, exact-root open review and post-submit quarantine. Management action
guards and its public blocked state consume this predicate. Management also
mounts the existing owner-only deletion lifetime, so direct consumers initialize
without relying on future UI wiring; there is no hook-import recursion because
the deletion hook does not import the management hook. Explicit current-scope
storage retry and error surfaces are provided.

The busy predicate now includes non-null drafts and unresolved review state.
Both review entry and captured confirmation recheck it. Metadata edit/review/save
handlers are blocked during named deletion review; Cancel releases that
metadata-only exclusion without adding financial quarantine. Ready siblings
remain independent. The previous contradictory draft-plus-deletion test is
corrected, and the new draft/review/captured-handler and corrupt-storage tests
cover the repaired boundaries. Existing terminal-only resolution, owner/route
guards and primitive external-store snapshots remain intact. No new production
blocker was identified in the repair diff.

Executor evidence records six initial RED failures,160affected cases and1272full
frontend passes at unchanged repair source, with typing/static checks. This
reviewer did not rerun those tests. The following test warning limits the claimed
coverage of the *pending-digest* interleaving specifically.

## Warnings

### WR-01 — The deferred-digest regression can block creation instead of deletion

**Severity:** WARNING

**Recheck status:** RESOLVED atff76617; original warning retained below.

**File:** `frontend/src/hooks/usePortfolioManagement.test.tsx:717–749`

The cold-recovery test defers `webcrypto.subtle.digest`'s first call globally.
The repaired management hook starts both deletion and creation recovery. Deletion
opening is serialized through `opening.then(...)`, whereas creation recovery
starts its digest directly from its layout effect. Creation can therefore consume
the one-shot deferred mock while deletion rehydration completes normally.
`entered === true` proves only that some digest was held. The test never asserts
`portfolioDeletionAuthorityReady(...) === false` before invoking the captured
metadata handlers. It can pass using the already-restored root quarantine and
fail to exercise CR-01's pending-initialization window.

**Fix:** Read the seeded deletion envelope's nonce and defer only the binding
digest whose encoded input belongs to that nonce. Explicitly assert deletion
authority readiness is false before and after invoking the captured handlers,
then release the gate and assert readiness becomes true while the restored
original remains blocked and the sibling is writable. Keep the corrupt-storage
variant and do not modify production behavior to satisfy this test.

This is a regression reliability issue, not a remaining production readiness
guard defect. No source/runtime/test operation was performed by the reviewer.

## Final test-only recheck — WR-01 resolved

The final diff selects the binding digest by the exact nonce from the seeded
deletion envelope and its owner, instead of deferring the first global hash.
Creation recovery therefore proceeds independently. The test explicitly observes
entry into that selected digest, then proves deletion readiness is false and
original-root quarantine is empty before and after captured edit/review/save
actions. No PATCH or editor mutation occurs in that actual initialization window.

After releasing the gate it asserts readiness, restored unknown original/root,
post-restoration quarantine, no automatic DELETE and independent sibling editing.
The corrupt-storage/safe explicit retry variant is retained. These assertions now
distinguish readiness exclusion from an already-restored quarantine and directly
cover the original missing interleaving.

Only the test and its summary changed after the production repair. Recorded
qualification is2focused cases1.86s,61complete hook cases5.64s and passing
typing/scoped lint/format. The earlier1272frontend/160affected qualification
remains evidence for unchanged production source, not a claimed full rerun at
this test-only head. This reviewer performed source/diff review only, with no
test/runtime/source operation. Original findings and review chronology remain
preserved. Final remaining findings:0BLOCKER,0WARNING.
