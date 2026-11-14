---
phase: 06-deploy
reviewed: 2026-11-09T12:18:56Z
depth: standard
diff_base: 995b464
review_head: eec70c5
files_reviewed: 2
files_reviewed_list:
  - .github/workflows/ci.yml
  - deploy/tests/test-ci-ops.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Plan 06-10: Nginx CI Privilege Review

## Narrative Findings (AI reviewer)

No BLOCKER or WARNING findings in the bounded two-file diff
`995b464..eec70c5`.

The workflow change (`.github/workflows/ci.yml:268`) grants root execution
only to the existing `deploy/check-nginx-config.sh` invocation. Its documented
root requirement matches nginx's opening of the configured log path during
`nginx -t`. Tracing the unchanged script confirms it copies repository config
into a fresh temporary prefix, generates a disposable certificate, invokes
the configuration test and removes the prefix through an EXIT trap. It does
not install config or start/reload nginx. No environment-preserving sudo,
input interpolation or broader privilege change was introduced.

The check remains mandatory in the ops job under `set -Eeuo pipefail`;
failure still blocks subsequent commands and the required aggregate. Existing
backend/frontend/image/browser gates, host uv setup, serial fixture execution
and always-run fixed-project cleanup remain unchanged.

The added regression (`deploy/tests/test-ci-ops.py:111`) requires the exact
anchored privileged invocation in the ops job. It would reject the previous
unprivileged line and introduces no suppression of existing assertions.

## Validation and limits

- Independently reran `python3 deploy/tests/test-ci-ops.py`: 5 passed.
- Scoped `git diff --check 995b464..eec70c5`: passed.
- Read both changed files and the unchanged nginx test script and config
  references to assess the command's scope and error propagation.

The parent supplied the actual CI failure at `42588116337` and executor's
successful root nginx test/cleanup proof. This reviewer did not repeat that
root execution, Docker rehearsals, application suites or image scans. Actual
current-head GitHub success remains a separate pending gate.

Only this review artifact was written. Parent planning edits and `.claude/`
were preserved; no source, app/runtime, recovery, production or remote state
was changed. This review grants no merge or deployment authority.
