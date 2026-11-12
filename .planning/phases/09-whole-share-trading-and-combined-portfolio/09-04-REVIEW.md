# Plan09-04 recovery review

Reviewed on2026-11-12 in a separate sequential pass by the executing agent.
Both attempted review/execution agents reported unavailable filesystem/shell
tools and performed no review. This is an inline review, not independent proof.

Scope:0013 producer/restore dispatch, manifest SQL, immutable function/trigger/
owner/ACL fingerprints, retained-tool fixtures, runtime-role and verified-TLS
consumers. Earlier0007–0012 contracts remain fixed. No installed production
tool, real database, B2 repository or provider was accessed.

## Findings

- R04-01, resolved in603e43a: receipt canonical rows used coin_id as their
  ordering key. Several fills of the same stock could produce nondeterministic
  equality hashes. Meaningful generated-SQL regression5a59aa0 failed before
  the correction and passes afterward.0013 now uses unique trade_id; earlier
  revision SQL remains unchanged. The isolated execution fixture now seeds
  two distinct receipts for one stock to exercise the actual retained path.
- Fixture compatibility: the0013 scenario creates all five admissions, so the
  historical next-identity probe cannot insert another reference admission.
  Its already-verified quarantined clone now frees that unique product slot
  before the insertion; the sequence itself is untouched. No source writes or
  runtime grant expansion is needed.
- R04-02: the synthetic journal lacked its historical baseline and allocated
  a noncontiguous initial sequence. The added actual ownership-service check
  in e17ef25 demonstrated `OwnershipHeld: missing_baseline`. The fixture now
  preserves a complete initial baseline and allocates contiguous tail values;
  the service must accept both source and restored histories before the
  fixture can report success. This is test-data repair, with no runtime
  implementation or recovery-tool contract change. Resolved in e8d3bb2; short real-service GREEN and the final canonical retained/roles/both-TLS run pass.

## Review conclusions and limits

Fixed invoker bodies are authenticated against reviewed independent constants,
not accepted from manifest self-hashes. Clone reconstruction grants only the
fixed new table/function rights after authentication; old financial tables
remain quarantined. Explicit fixture CONNECT grants occur after restore checks.
Named immutable-trigger bypasses are restricted to privileged synthetic setup
and cleanup, with restoration in the same transaction. Runtime denials and
cross-row integrity remain active during the behavior under test.

Synthetic duplicate SQL uses an explicit unused identity so conflict checking
cannot silently advance a sequence. It tests database duplicate rejection,
not an implemented execution service: actual service replay, final-wait races
and retained restricted-service consumers remain Plans06/07/14 obligations.

No remaining source finding was identified in this pass. The final corrected canonical --all run passes. Its actual timings and archive
identity are recorded in09-04-SUMMARY.md and09-LOCAL-PROOF.md; this review itself
is not a substitute for that execution evidence.
