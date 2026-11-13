---
phase: pr31-ci-failures
reviewed: 2026-11-14
depth: standard
files_reviewed: 3
files_reviewed_list:
  - deploy/tests/check-recovery-image.py
  - deploy/tests/test-image-contracts.py
  - deploy/tests/test-ci-ops.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# PR31 affected code review

Independent reviewer: `/root/pr31_debug/code_review`. Implementation was read-only;
comparison base was `95912e0`. No Docker workload, installation or network action
was started during review.

## Narrative Findings (AI reviewer)

No actionable BLOCKER or WARNING found in the three reviewed files.

Traced the CI prerequisite through unchanged `verify_saved_image`,
`verify_image_provenance`, `bind_recovery_image`, `loaded_recovery_image` and
`image_inspect`. The helper verifies the exported archive before importing it,
rejects an existing alias with an incorrect config/platform identity before load
or bind, rewinds the same authenticated temporary file, then binds only the
unchanged fixed config/platform identities. Registry verification does not
substitute for the Compose alias. CI invokes this prerequisite before recovery
fixtures. Recovery CORE remains unchanged in the reviewed diff.

Independently recomputed the historical `e728855` package inventory with only
`opentelemetry-api` removed: SHA256
`8b0f58d9199b3dad2d27d9b398d33cc578b8a819307a3838dfc1cb32934991f1`.
It matches the revised all-other-entry assertion. The separately authenticated
complete OTEL1.45.2 record and the eight exact calendar additions retain separate
assertions; this is not an unrestricted inventory refresh. Mutation tests reject
unapproved OTEL version/artifact and unrelated dnspython/FastAPI changes.

## Independent checks and limits

- `python3 deploy/tests/test-image-contracts.py`: 15 passed, 0.595s.
- `python3 deploy/tests/test-ci-ops.py`: 16 passed, 0.483s.
- `git diff --check`: passed.
- Read `/tmp/pr31-ops-cold.log`: owned missing-alias startup reports `No such
  image`, followed by successful authenticated import/bind, actual PostgreSQL
  healthy startup, unchanged running-image guard and owned cleanup. This was
  reviewed evidence; the reviewer did not independently repeat Docker execution.

Reviewed file SHA256 values:

| File | SHA256 |
|---|---|
| deploy/tests/check-recovery-image.py | ecc9896db6b4b2f2141e6f686d25aff38fe0e2988ff019f70879c0a7894c5c9a |
| deploy/tests/test-image-contracts.py | 0824f0dcac34c71c2f836ea67b32f568fe62071ded80a02b82a81faf3eb9a787 |
| deploy/tests/test-ci-ops.py | 4f8239d8f1dc281521350e284a81924a170163062223eb8420eaf5b6162384bf |

The pending dnspython2.9.2 lock/install/exception is outside this reviewed byte
scope. A subsequent DNS exception or lock change requires a delta review.
This report does not claim hosted CI success or authorize publication.
