---
phase: 06-deploy
reviewed: 2026-11-09T08:35:10Z
depth: standard
diff_base: 57b8774
review_head: 0637b48
files_reviewed: 5
files_reviewed_list:
  - .github/workflows/ci.yml
  - deploy/tests/ops-fixtures.py
  - deploy/tests/test-ci-ops.py
  - deploy/tests/test-deploy-prerequisites.py
  - deploy/tests/test-rollback-db-security.sh
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Plan 06-10: Privileged Synthetic CI Review

## Narrative Findings (AI reviewer)

No BLOCKER or WARNING findings in the bounded five-file diff
`57b8774..0637b48`. Review covered the changed behavior and its fixture,
Git, TLS-provisioner and workflow call boundaries. It does not constitute a
whole-phase audit or passing current-head GitHub CI.

Explicit `sudo --` execution is limited to the prerequisite suite and three
serial synthetic rehearsals (`.github/workflows/ci.yml:262`, `:272`–`:274`).
This supplies the effective root identity required by the unchanged TLS
provisioner and its root-owned private files. The host uv preparation and
db-config consumer remain unprivileged; no environment-preserving sudo was
introduced. The signed restic checks, required aggregate, serial ordering,
fixed synthetic project targets and always-run cleanup remain unchanged.

The fixture-only `source_git` helper (`deploy/tests/ops-fixtures.py:30`) binds
both the trust exception and working directory to `Path(__file__).resolve()`'s
checkout root. Arguments remain a subprocess argument vector, using the
existing fixed fixture environment. All its current callers perform source
reads (`rev-parse`, `archive`, `show`); no wildcard trust, global configuration,
ownership change or checkout mutation is added. Rollback retains the old
source/lock byte comparisons and original-HEAD assertion. Private fake-host
repositories retain their existing root-owned Git operations.

The added contracts check exact privilege invocation and the source helper's
complete command vector. No modified assertion suppresses an existing
failure or changes production guards.

## Validation and limits

- Independently reran `python3 deploy/tests/test-ci-ops.py`: 5 passed.
- Independently reran `python3 deploy/tests/test-deploy-prerequisites.py`:
  18 passed, including both actual TLS lock callers.
- `bash -n deploy/tests/test-rollback-db-security.sh`: passed.
- Scoped `git diff --check 57b8774..0637b48`: passed.
- Read `06-10-ROOT-CI-EVIDENCE.md`, including its recorded runner-owned
  checkout trust and actual nonroot/root synthetic TLS proofs. These separate
  proofs were not rerun by this reviewer.

The supplied actual run `42585485295` finished with image/backend/frontend/e2e
passing and ops failing at the prior head; STATE's running note is stale.
The three serial real synthetic rehearsals at the corrective head and actual
current-head GitHub ops success remain pending. Unchanged baseline lint and
format observations are outside this corrective diff.

Only this review artifact was written. Existing planning edits and `.claude/`
were preserved. No source, recovery payload, archive, timer, production
resource or remote branch was changed. No push, merge, release, deployment
or phase-completion authority follows from this review.
