---
phase: 06-deploy
reviewed: 2026-11-09T18:05:06Z
depth: standard
diff_base: 15caac1
review_head: df81abe
files_reviewed: 10
files_reviewed_list:
  - .github/workflows/ci.yml
  - deploy/RUNBOOK.md
  - deploy/configure-db.sh
  - deploy/datastore-bindings.py
  - deploy/deploy-entrypoint.sh
  - deploy/deploy.sh
  - deploy/tests/test-ci-ops.py
  - deploy/tests/test-datastore-bindings.py
  - deploy/tests/test-deploy-prerequisites.py
  - deploy/tests/test-rollback-db-security.sh
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
operational_acceptance: pending_real_isolated_proof
---

# Plan 06-12: Local Source Review

## Narrative Findings (AI reviewer)

**0 active BLOCKER findings; 0 active WARNING findings** in the bounded source
change `15caac1..df81abe`. This review includes the full new binding helper,
retained entrypoint/deploy/role integration, documentation and regression
changes, with call-boundary analysis of the unchanged lock and recovery gate.
It is source acceptance for proceeding to the required isolated proof, not
production readiness or release publication approval.

### Closed finding — shortened Docker container identities

The initial review of `d876806` found a BLOCKER at
`deploy/datastore-bindings.py:237`: `docker ps -aq` returned shortened IDs while
the guard required exact equality with full inspect IDs. A realistic isolated
short/full-ID reproduction rejected an otherwise selected running container.
The original test returned matching service-name strings and missed this.

RED `72756b2` / GREEN `df81abe` adds `--no-trunc` and a realistic regression
with 64-character inspect identities and simulated 12-character ps output when
that option is missing. The targeted corrected regression independently
passes. Exact identity equality remains enforced; this finding is closed.

## Reviewed trust and operation boundaries

- The fixed root-owned private JSON, trusted-parent/no-symlink checks, duplicate
  JSON-key rejection, exact schema and distinct volume names constrain routing.
  Actual volume metadata is inspected, driver options are rejected, and data
  probes bind-mount inspected existing directories read-only. These probes do
  not implicitly create named volumes or mount originals for mutation.
- The protected overlay contains only the two external candidate mappings.
  Existing unexpected overlay contents fail closed. Retained Compose creation
  and recreation use that same fixed overlay; missing external volumes fail.
  Runtime checks verify sole fixed project/service containers, immutable image,
  configured user, running state, exact data/TLS/HBA mounts and internal network.
- The new helper is required by retained manifest verification and installation.
  The entrypoint keeps its fixed clean environment and narrow argument set.
  Inherited locks are validated by the existing kernel-backed implementation;
  role inspection/application checks running identities before SQL execution.
  Docker errors are captured and reported through redacted helper failures.
- First startup resolves the actual circularity: the stopped source cannot
  supply a running revision. The limited mode reads an exact private completed
  restore profile for the selected snapshot and old live-log release, then
  calls the unchanged strict recovery gate with that revision. Only successful
  admission sets `ADMITTED_REVISION`. Candidate data/TLS/HBA checks precede
  startup; actual container identities and actual candidate revision must match
  afterward. No role SQL, migration or app startup is performed by this mode.
  Normal deploy/rollback retain actual running revision and recovery checks.
- Explicit failure returns protect the admission/start functions even when
  Bash invokes them in an error-tested context. Ordinary deploy checks selected
  identities after datastore startup and before migration; app/rollback
  recreation retains the same mapping and rechecks it.

The updated procedure correctly prepares final protected material and takes
fresh exact backup/restore while old datastores remain available with writers
stopped. It then holds the lock across stop/copy/start without changing bound
material. This remains a required maintenance procedure, not measured live
state or a claim that existing backup intrinsically selects candidate volumes.

Recovery CORE, archive and independent backup implementation are unchanged.
Production `source_compose` remains forbidden. Existing exec-only backup can
reach the verified sole candidate under its fixed project/service identity.
The source gate binds approved private `recovery_files`; live TLS key0640 and
CA certificate0644 do not themselves qualify for that list. Documentation now
distinguishes private custody/configuration coverage from actual TLS pair,
hostname and permission validation, without claiming an intrinsic hash binding
for unlisted material.

## Independent validation and limits

- Reproduced the initial shortened-ID rejection without Docker or source edits.
- Corrected realistic running-identity regression at `df81abe`: passed.
- New unchanged-gate admission/material-mutation regression: passed.
- Current CI contracts: 7 passed.
- Changed shell syntax and scoped `git diff --check`: passed.
- Earlier full binding-suite attempt at `d876806`: ten tests passed; its real
  UID-marker fixture could not perform `os.chown` in this review filesystem
  (`EINVAL`). That environment limitation is not treated as a source finding
  or a passing ownership proof. Executor root-suite results remain separate
  evidence; this reviewer did not repeat them with elevated permissions.

The private-file/kernel-lock and extracted admission tests exercise behavior;
the corrected ID fixture now models the Docker formatting boundary. Structural
wiring assertions do not prove actual retained production entrypoint execution.
The required serial populated secure startup/cutover, forced recreation,
actual v0.3.1 app rollback, original preservation and unchanged installed
archive backup/exact restore proof remain pending. No synthetic unit success
is substituted for that operational evidence.

Only this review artifact was written. No implementation, long Docker proof,
live/private access, provider operation, install, commit or remote write was
performed. Existing unstaged procedure/proposal/evidence and `.claude/` were
preserved. PR27's published head and prior green CI are unchanged historical
evidence; an updated candidate still requires review, a publication decision
and exact-head CI. No merge, tag or deployment authority follows from this report.
