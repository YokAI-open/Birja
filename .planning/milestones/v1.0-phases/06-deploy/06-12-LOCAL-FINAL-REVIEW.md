---
phase: 06-deploy
reviewed: 2026-11-10T08:05:00Z
depth: standard
diff_base: df81abe
review_head: ce552076618c7cf183e19a0d41e8a4c565bca12b
working_tree_included: true
files_reviewed: 7
files_reviewed_list:
  - deploy/datastore-bindings.py
  - deploy/deploy-entrypoint.sh
  - deploy/tests/test-datastore-bindings.py
  - deploy/tests/test-rollback-db-security.sh
  - deploy/tests/ops-fixtures.py
  - deploy/tests/test-ci-ops.py
  - deploy/tests/selected-cutover.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
operational_acceptance: pending_real_isolated_proof
---

# Local rollout follow-up source review

## Narrative Findings (AI reviewer)

No active BLOCKER or WARNING findings in the bounded follow-up changes since
df81abe, including the working tree corrections inspected during this review.
This supplements the earlier source review; it does not authorize publication,
deployment, production access or changes to the independent recovery archive.

The later Redis parser accepts only the observed six-field legacy, eight-field
open incremental and ten-field incremental records, with fixed labels, safe
filenames and numeric offsets. The containerd alternative requires the pinned
index identity and the actual approved linux/amd64 child descriptor; it does
not accept arbitrary image identities. Public read permissions apply only to
the retained HBA directory and nonsecret HBA file. The installer still verifies
retained bytes and rejects writable files.

The synthetic proof invokes actual retained deployment and rollback interfaces,
uses separate original and candidate volumes, retains real lock inheritance,
and runs launcher children under the existing Landlock boundary. Its temporary
host and nginx substitutions are explicit fixture limitations. CI's existing
serial rollback producer now invokes this proof with the same recovery bundle
argument; the CI contract asserts that inclusion.

### Closed WARNING: Unterminated final manifest record bypassed file checks

At deploy/datastore-bindings.py:35, plain `while read` skipped the last record
when its terminating newline was absent. The preceding awk validation still
accepted that row, so a missing, symlinked or incorrectly owned referenced file
could escape the data guard. The reviewed correction processes a nonempty
partial final read with `|| test -n "$kind"`. The new regression covers missing,
symlinked, wrong-owner and valid final referenced files without a newline.
RED c3c855d / GREEN ce55207 preserve this regression and correction. The root
agent reports all 13 focused binding tests passing in 1.449 seconds; this
reviewer inspected the source and did not independently rerun that suite.

### Closed WARNING: Redis persistence proof stopped before deploy and rollback

The initial selected-cutover fixture checked Redis GET and TTL only after its
explicit force-recreate. It did not verify that state after current deployment
or actual old application rollback. The reviewed shared `check_redis_state()`
now asserts the exact sentinel value, positive TTL and unauthenticated NOAUTH
rejection after all three milestones.

## Validation limits

This reviewer performed source and call-boundary analysis only. No Docker
tests, private configuration reads, production operations or publication were
performed. The root agent is separately running the serial real proof and
regressions. Those results must be recorded before operational acceptance; this
artifact does not claim that an in-progress proof passed. Later source changes
require review of their delta.
