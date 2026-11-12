# Plan09-07 review

Distinct inline review, not an independent agent review (agents lacked tools).
Scope: stock execution refinement, two-instrument fixture, actual financial
contention/waits, ownership/corporate-action consumers and final0013guard.

Resolved actual RED050bfa0: unchanged selected ask with a changed bid unnecessarily
refused after immutable Trade insertion. One full rollback/rebuild retains
current bid/ask/mid metadata without rewriting an immutable record. Bound is two
attempts total, same economic key/body, fresh permissions/cash/locks each time.
Only a quote metadata signal can rebuild; no deadlock/timeout/constraint or
permission retries hide a lock-cycle bug. A changed selected price renews preview.

Confirmed real independent sessions and observed PG blockers, <=10parallel
requests, exact count/balance/basis/journal assertions, deterministic holder
locks and no additional starting grant. No financial/DB/clock authority mocks.
Explicit test-only barriers and injected XID guard input are accurately disclosed.
Actual split processor serializes with first fill, and final guard has no later
business await. Complete role/recovery/API/browser/security gates remain later.

No open blocker/high. Final248tests63.39s;185statements/42branches100%; scoped
Ruff/format/Mypy pass. No provider, production, publication or deployment change.
