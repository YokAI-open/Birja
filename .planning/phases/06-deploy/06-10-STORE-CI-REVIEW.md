---
phase: 06-deploy
reviewed: 2026-11-09T12:37:19Z
depth: standard
diff_base: 58c4258
review_head: 57974aa
files_reviewed: 3
files_reviewed_list:
  - .github/workflows/ci.yml
  - deploy/tests/check-recovery-image.py
  - deploy/tests/test-ci-ops.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Plan 06-10: CI Image Store Review

## Narrative Findings (AI reviewer)

No BLOCKER or WARNING findings in the bounded three-file diff
`58c4258..57974aa`.

The daemon configuration change (`.github/workflows/ci.yml:231`) reads and
merges the existing JSON, preserving unrelated top-level settings and nested
features while enabling only `containerd-snapshotter`. It occurs on the
disposable ops runner before the existing restart, first explicit image pull
and fixture build. Invalid existing JSON or incompatible feature types fail
the step rather than silently discarding configuration. The workflow contains
no production or remote-host daemon operation.

The configuration and driver-status check match [Docker's containerd store
instructions](https://docs.docker.com/engine/storage/containerd/), which explain
that upgrading an existing engine retains the classic store until explicitly
enabled. The store switch precedes this job's fixture resources; the existing
fixed-project cleanup remains after them.

The new preflight (`deploy/tests/check-recovery-image.py:20`) requires the
containerd driver, saves only the unchanged pinned linux/amd64 recovery image
using `/usr/bin/docker` and the fixed recovery environment, authenticates the
registry manifests and invokes the unchanged strict saved-image verifier.
Its private anonymous temporary file closes on success or failure. Save has
an explicit timeout; driver, registry and verification failures propagate to
the required CI job. No fallback, suppression, alternate image or relaxed
identity/archive policy was added.

The regression (`deploy/tests/test-ci-ops.py:68`) executes the extracted merge
against absent and populated temporary configuration, checks preserved
settings/features and ordering, rejects the classic store before export or
registry access, and verifies the export command and strict-verifier inputs.
Existing required producers, aggregate gates and isolation remain unchanged.

## Validation and limits

- Independently reran `python3 deploy/tests/test-ci-ops.py`: 7 passed.
- Scoped `git diff --check 58c4258..57974aa`: passed.
- Read the full new preflight and changed workflow/test sections, and traced
  the unchanged saved-image verification and identity boundaries.

The parent supplied actual run `42617492782`'s successful setup, offline checks
and transition followed by rejection at the classic archive membership guard,
plus a separate successful actual containerd export/verification proof.
The failed raw archive is unavailable, so this review does not claim its
specific extra or missing members were established. Focused test success
messages use mocked Docker/registry boundaries and are not an actual export.
This reviewer did not restart Docker or repeat integration, app or scanner
gates. Corrective-head hosted CI success remains pending.

Only this review artifact was written. No source, production/runtime,
recovery code, image pin or remote state was changed; unrelated `.claude/`
and parent-owned work were preserved. No merge or deployment authority is
implied.
