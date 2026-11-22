---
phase: 14-end-strategies-safely
plan: "16"
reviewed: 2026-11-19
depth: deep
source_commit: d39775a
initial_source_commit: 6eaf391
re_reviewed: 2026-11-19T22:47:50Z
repair_diff_base: ec0965c
diff_base: 4c52d7a
files_reviewed: 19
files_reviewed_list:
  - .github/workflows/ci.yml
  - CLAUDE.md
  - backend/app/db/portfolio_bootstrap.py
  - backend/app/db/portfolio_migrate.py
  - backend/tests/test_critical_coverage_config.py
  - backend/tests/test_portfolio_closure_admission.py
  - backend/tests/test_portfolio_migrate.py
  - deploy/backup-snapshot.py
  - deploy/db/bootstrap-roles.sql
  - deploy/deploy.sh
  - deploy/tests/portfolio-smoke.py
  - deploy/tests/run-portfolio-campaign.py
  - deploy/tests/run-portfolio-validation.py
  - deploy/tests/test-ci-ops.py
  - deploy/tests/test-db-config.sh
  - deploy/tests/test-dev-bootstrap.py
  - deploy/tests/test-portfolio-smoke-image.py
  - deploy/tests/test-portfolio-validation-contracts.py
  - deploy/verify-restore.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase14 Plan16 — Independent Code Review

## Narrative Findings (AI reviewer)

The initial review found one **BLOCKER** and one **WARNING** in the new durable
supervisor. Both are now **RESOLVED** by independent re-review at `d39775a`;
there are **0 remaining blockers and 0 warnings**. Original findings and proofs
are preserved below, followed by the repair disposition.
The exact19-file4c52d7a→6eaf391 scope was reviewed through the runtime,
administrative SQL, recovery transports, CI and negative test call chains.
No structural pre-pass was supplied. Pending Plans17–19 and final whole
qualification are not treated as defects in this plan.

## Critical Issues

### CR-01: Interrupting preflight leaves its descendants outside the supervisor's reaper

**Original classification:** BLOCKER. **Disposition: RESOLVED** at `d39775a`.

**Files:** `deploy/tests/run-portfolio-campaign.py:231`,
`deploy/tests/run-portfolio-campaign.py:284`;
`deploy/tests/run-portfolio-validation.py:105`.

**Issue:** The supervisor executes `runner.preflight()` synchronously before
it creates or records `child`. The real preflight launches `bash
deploy/tests/test-db-config.sh`, which launches Python, Compose and pytest.
Only the later long-command child has a recorded PID/startticks, a separate
process group and the bounded SIGINT/reap path.

If SIGTERM arrives during the real fixture preflight, the handler raises
`KeyboardInterrupt` through `subprocess.run`. Its direct subprocess can be
killed while descendants remain alive. The exception boundary sees
`child is None`, publishes a terminal `interrupted` receipt with
`cleanup=long-command-not-started`, and returns without signalling or waiting
for those descendants. It also loses their identities. The configuration
script may consequently continue DB tests and hold disposable resources after
the original supervisor has declared the run interrupted; the script's own
`finally` is not a replacement for process-group supervision. A subsequent
validation lane can overlap this unrecorded work. This violates the planned
interruption/owned-cleanup guarantee during a normal supported launch phase.

**Independent bounded proof:** Parent explicitly authorized a private stdlib
stub proof with no DB, network, installation or qualification command. The
actual `worker()` ran a preflight `subprocess.run` shell-equivalent wrapper
with a child, then received SIGTERM. Observed:

```text
worker_return=1
state=interrupted
cleanup_claim=long-command-not-started
preflight_child_identity_unrecorded=true
preflight_child_still_alive=true
preflight_finally_missing=true
```

The reviewer then explicitly sent SIGINT to the owned descendant and waited
for its termination; its finally marker appeared only after that manual
cleanup. No owned descendant remains. The private reproducible proof is
`/tmp/birja-backup-test-r16-supervisor-review-proof.py`.

**Fix:** Make preflight an owned, recorded and separately supervised process
phase, or otherwise route all its spawned processes through the same bounded
group cancellation/reaping mechanism as the long command. Record its PID,
startticks, phase and log before relying on it. On interruption, signal and
reap that exact group before writing the terminal receipt; preserve honest
cleanup disposition if finalizers cannot complete. Add a real nested-child
test that interrupts while preflight is running and checks no descendant
survives, original identities remain auditable, cleanup/finally markers are
observed, and the long command never starts. Keep public status/resume read-only.

## Warnings

### WR-01: Re-entering the internal worker overwrites an already-consumed run receipt

**Original classification:** WARNING. **Disposition: RESOLVED** at `d39775a`.

**Files:** `deploy/tests/run-portfolio-campaign.py:200`,
`deploy/tests/run-portfolio-campaign.py:216`,
`deploy/tests/run-portfolio-campaign.py:362`.

**Issue:** The normal public `--suite` entry correctly refuses an existing
receipt directory, and `--resume` only reads. However, the CLI also exposes
the internal `--worker` path. That path accepts any existing private request,
unconditionally replaces `status.json` with a new supervisor identity and
runs preflight again before trying the exclusive `command.log` creation.
There is no claimed-once launch token or worker ownership check at this boundary.

Replaying it against a completed request therefore destroys the original
terminal status and child identity even though the existing log eventually
prevents another long command. Replaying during an active run can similarly
replace the original status before the second worker refuses. This is a
robustness/evidence-integrity defect in the internal lifecycle boundary,
not a claim that ordinary `--resume` restarts work or that the proof executed
a second long qualification.

**Independent bounded proof:** Using the actual worker and the same private
request, first run a bounded successful child, then invoke the worker again:

```text
preflight_runs=2
before_state=passed
after_state=refused
original_child_identity_lost=true
second_long_command_prevented_by_existing_log=true
```

This used only stdlib local children and the same private proof above. The
first command log remained original. All owned test resources were removed.

**Fix:** Atomically claim each launch request once before writing status or
running preflight, and reject later/concurrent workers without modifying the
original receipt. Bind the claim to the launch request and original process
identity; do not turn a stale claim into an automatic retry. Add completed,
active and concurrent-worker replay tests proving preflight is not rerun,
original status/log/PID/startticks remain unchanged, and no replacement child
starts. Preserve the already-correct public launch/resume behavior.

## Independent Repair Re-review — CR-01 and WR-01 Resolved

**Source and scope:** `ec0965c`→`d39775a`, including RED `286611f`, GREEN
`54c9120` and forced-cleanup disposition `3b2b24d`. The repair changes only
`deploy/tests/run-portfolio-campaign.py`, its existing validation-contract test
file, and the appended Plan16 summary. The original19-file review scope remains
listed above. No application/runtime, administrativeSQL, source-pin, image or
archive bytes change during this repair.

**CR-01:** Preflight now runs in a separately owned session. A ready/work gate
prevents it from starting qualification work before PID, startticks, phase and
private log identity are durably recorded. The parent records the process before
handling deferred cancellation; the long-command assignment boundary receives
the same protection. Cancellation sends SIGINT to the original owned group,
tracks every live group member and reaps the leader before a terminal receipt
is published. The preflight wrapper records cancellation instead of throwing
through `subprocess.run`, so nested direct-child finalizers have time to run.
Unexpected surviving descendants after nominal phase completion also refuse
instead of allowing a pass.

The new real nested-wrapper/grandchild regression checks both finally markers,
absence of live descendants, retained preflight PID/startticks and absence of a
long command. The forced-cancellation regression separately checks bounded
SIGKILL, no live work and an absent finally marker. In that escalation case the
receipt explicitly says `group-killed;finalizers-unconfirmed` and resource
cleanup is `not-attested`; process reaping is not presented as proof that Docker
or other resource finalizers completed. Cleanup failure similarly requires manual
inspection rather than reporting success. These paths address the original
orphan/process-audit defect without widening permissions or adopting caller
resources.

**WR-01:** An fsynced `O_EXCL` claim consumes the original request before status
publication or preflight. It binds request bytes, runID and original supervisor
PID/startticks. A second worker, including a stale or concurrent replay, returns
before changing original status/logs or running preflight. The claim remains
consumed after the original process exits; it is not a restart lease. Claim and
request identity are checked before phases, during the long command and by
status/resume. The completed, concurrent and stale-replay tests assert one
preflight, original receipt/log preservation, matching claim/status identities,
one original child and refusal of request/identity mutation. The public
launch-existing-directory refusal and read-only resume behavior remain intact.

**Evidence assessed independently:** The final log records28 runner/supervisor
tests in8.189s,22 image/source contracts in5.385s and88 CI contracts in23.050s,
all OK. Source tracing confirms the original archive/source/image guards and
finite prior migration authority are retained. The real detached preflight
receipt is passed with `preflight_exit_code=0`, final exit0 and matching original
claim/status identity. Its reported139-case preflight/41.947s diagnostic used
the measured GREEN source; later changes only refine disposition/tests. It is
not relabelled as a whole security/recovery qualification at the later commit.

The reviewer did not rerun those suites or another DB/TLS campaign. The original
bounded reproduction is retained above; this re-review inspected the repair,
new behavioral assertions and recorded outputs. No additional proven defect
was found. Plan17 browser work, Plan18 uninterrupted whole qualification and
Plan19 owner/native200 acceptance remain required.

## Other Assessed Boundaries

- Current14 authentication checks the complete measured catalogue, ACL/default
  pair, authenticated migrator and supplemental object inventory before Alembic.
  The inherited14 post-migration ACL is bootstrap-only; ordinary runtime still
  requires the unchanged final0023 ACL/private defaults. Python/adminSQL pair
  logic agrees. Historical projections and migration files are unchanged.
- Independently calculated current producer/consumer pins match bootstrap,
  migrator and administrative SQL bytes; deployment pins agree. Retained0020
  and final0023 catalogue/ACL constants compare unchanged to the diff base.
- The prepared14 diagnostic flag is forwarded only by the initial creation
  transport. It verifies source and complete prior authority before financial
  imports; later23 probes use their ordinary gate. The before-oracle keeps all
  genuine14 columns and tails and explicitly checks baseline, holdings,
  initialization origin and absence of another starting grant.
- CI retains all61 old critical modules plus three closure paths (64). Strict
  coverage, audits, browser/image gates and issue35 scope are retained. The
  finite command-failure source double leaves separate actual file-mutation
  and source-guard checks in place.
- Current profile/version/revision and all seven stage families are explicit;
  complete fixed0020/0017 images remain separate. Source/CORE/unit/archive and
  exact image-ID/alias guards refuse substitution rather than rebuild/retag.
  Missing/malformed authority triples cannot pass by equal empty results.
- The recovery archive directory is absent at start and atomically acquired
  by the runner. Supervisor artifact observation begins only when its packaged
  archive/status exists; subsequent snapshots freeze existing archive/image
  identities while allowing legitimate new stage bindings. Source scope covers
  relevant tracked/nonignored additions and ignore metadata without reading
  ignored secrets or following escaping source links.
- Exact canonical14 synthetic-path allowance preserves older paths. Borrowed
  configuration stacks are authenticated and retain caller cleanup ownership.
  Private directories, logs and atomic JSON publication have restrictive modes.

## Evidence and Limits

Reviewed receipts for the202-case100%-coverage group,139-case preflight,
82-case CI ops block, R3 fresh/14/20/cold proofs and ordinary-dev fixture all
exist and record exit0/source_unchanged. The reviewer traced their assertions,
but independently executed only the bounded supervisor proofs documented above;
no duplicate backend, DB, browser, image scan or whole recovery run was started.

Final whole3653-backend/security qualification and uninterrupted seven-stage
same-archive proof remain Plan18 work. Browser integration and separate owner
UI/native200 acceptance remain Plans17/19. This report grants no publication,
provider or production authorization.
