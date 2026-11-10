---
phase: 06-deploy
reviewed: 2026-11-09T08:15:50Z
depth: standard
diff_base: c085a766a056b017fce1d9d6e2f737541867ae79
review_head: 7d5d8c2
files_reviewed: 4
files_reviewed_list:
  - .github/workflows/ci.yml
  - deploy/scan-images.py
  - deploy/tests/test-ci-ops.py
  - deploy/tests/test-image-contracts.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Plan 06-10: Bounded CI Fix Review

## Narrative Findings (AI reviewer)

No BLOCKER or WARNING findings in the four-file change from `c085a766` to
`7d5d8c2`. This is a bounded independent correctness/security review of the
CI fixes, not a whole-phase audit or proof of passing current-head GitHub CI.

The ops job prepares uv, Python and the locked backend environment before
the operational contracts (`.github/workflows/ci.yml:220`). Tracing
`deploy/tests/test-db-config.sh:23` confirms its host consumer uses
`uv run --locked --no-sync` from the same backend directory. The new sync
retains the existing default dev and audit groups. The added contract checks
prerequisite ordering and rejects dependency-group exclusions.

The scanner's `--user` argument (`deploy/scan-images.py:59`) uses the effective
host UID/GID, matching ownership of its private temporary directory, cache
and exported input. It preserves the read-only root and input mount, dropped
capabilities, no-new-privileges, immutable scanner pin and explicit cache path.
The raw HIGH/CRITICAL policy, inclusion of unfixed findings, identity checks,
error handling and required aggregate job are unchanged. Regression assertions
exercise nonroot identity `1001:1002`, private modes and preserved isolation
across the existing success and failure cases.

## Validation and limits

- Independently reran `python3 deploy/tests/test-ci-ops.py`: 5 passed.
- Independently reran `python3 deploy/tests/test-image-contracts.py`: 13 passed.
- Scoped `git diff --check c085a766..7d5d8c2`: passed.
- Read `06-10-CI-FIX-EVIDENCE.md`, including its recorded real nonroot Docker
  permission proof. That proof was not rerun during this review and does not
  establish a completed vulnerability scan.

Actual run `42583320799` failed at the approved/pushed baseline, per supplied
failure evidence; STATE's earlier running status is stale. Fresh five-image
scan results and actual GitHub CI at the corrective head remain pending.
Unchanged baseline lint/format observations are outside this corrective diff.

Only this review artifact was written. No source, recovery bundle, operational
state, timer, production resource or remote branch was changed. No push,
merge, release or deployment authority is implied by this clean review.
