---
phase: 14-end-strategies-safely
plan: "11"
reviewed: 2026-11-19
depth: standard
source_commit: ff460939ef5ffa3fb993ff6a1bc70cb68ec83f32
diff_base: ff9de70
files_reviewed: 6
files_reviewed_list:
  - frontend/src/api/portfolioDeletion.ts
  - frontend/src/api/portfolioDeletion.test.ts
  - frontend/src/lib/portfolioDeletionAttempt.ts
  - frontend/src/lib/portfolioDeletionAttempt.test.ts
  - frontend/src/api/client.ts
  - frontend/src/api/client.test.ts
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 14 Plan 11 — Independent Code Review

## Narrative Findings (AI reviewer)

No proven BLOCKER or WARNING identified in the submitted Plan11 changes.
Reviewed all six scoped source/test files and the ff9de70→ff46093 shared-client
diff, with the deletion API/schema, existing creation recovery, canonical
portfolio parser and session/target patterns as call-contract references.
No structural pre-pass was supplied.

This is a source review of transport and recovery primitives. Hook integration,
financial target quarantine, rendered UI, real browser journeys and final
qualification remain downstream; this report does not certify those outcomes.

## Assessed boundaries

- Deletion copies and freezes the exact canonical bigint-string ID, UUIDv4,
  reviewed name and policy before any asynchronous request work. The captured
  path/body cannot follow caller mutation or a later same-name replacement.
- The new transport requires an explicit current-context callback and checks
  context/cancellation around CSRF, authentication recovery, response fetch and
  JSON parsing. It shares the existing fetch/refresh layer rather than adding
  a separate cookie/session implementation. Existing apiFetch callers retain
  their interface and ordinary behavior; the stricter result parser is opt-in.
- Only an exact200 JSON acknowledgement with the original ID and closed state
  yields a receipt. Malformed/wrong-ID/extra-field acknowledgements, transport
  failure, cancellation, stale context and ambiguous server failures remain
  unknown. There is no transport/5xx mutation retry. The one authentication
  recovery retry retains the original path/body and checks its context again.
- Safe error mapping discards arbitrary server detail, retains a bounded safe
  Retry-After value and distinguishes a durable code-only name-refusal409 from
  later request refusal. Only portfolio_confirmation_changed sets terminal;
  original-key conflict, auth, quota and unavailable responses cannot resolve
  a previously unknown original. The actual admission503 optional message is
  discarded without losing the safe status/wait.
- Recovery uses a separate sessionStorage key, strict finite envelope/intent
  shape,16000UTF-8-byte bound and opaque nonce/owner binding. There is no money,
  token, email or receipt in the stored envelope, and no storage operation
  makes an API request. Persistence reads back exact bytes before returning
  the frozen original to a sending caller.
- Openers are serialized; owner/session checks surround digest and storage
  work. Existing nonce/binding and observed-original checks prevent a stale
  handle from persisting over or resolving a different unobserved original.
  Corrupt, oversized, unavailable or failed-readback storage fails closed.
  Creation storage is independent. Logout/owner-change clear is guarded.
- Tests assert actual observable request ordering/counts, original bytes,
  response/error classifications, storage contents, interleaved openers and
  stale epochs. They cover meaningful behavior rather than only execution.

## Evidence and limits

Plan11 records69 focused cases,1239 frontend tests, full typing and scoped
lint/format at unchanged tested source. Those receipts support the handoff;
this reviewer did not rerun tests or perform runtime, DB, provider, package,
publication or production operations. No source file was modified.

Plan12 must supply the mandatory transport guard from its current owner/session/
operation lease, persist the exact intent before sending, and resolve storage
only after a matching receipt or terminal durable result. Generic refused
status alone is insufficient. Rehydration must not submit DELETE. These are
consumer integration obligations, not implemented hook/UI claims here.

The independently recorded backend safe-integer versus PostgreSQL bigint-range
observation remains unresolved for the planned09/10 authority/privacy work.
This client correctly preserves the full canonical bigint-string contract; no
backend acceptance, waiver or remediation is implied by this clean review.

All whole-phase requirements remain pending final integration and verification.
