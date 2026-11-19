---
phase: 14-end-strategies-safely
plan: "16"
reviewed: 2026-11-19
depth: deep
source_commit: 6eaf391
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
  critical: 1
  warning: 1
  info: 0
  total: 2
status: issues_found
---

# Phase14 Plan16 — Independent Code Review

## Narrative Findings (AI reviewer)

One **BLOCKER** and one **WARNING** remain in the new durable supervisor.
The exact19-file4c52d7a→6eaf391 scope was reviewed through the runtime,
administrative SQL, recovery transports, CI and negative test call chains.
No structural pre-pass was supplied. Pending Plans17–19 and final whole
qualification are not treated as defects in this plan.

## Critical Issues

### CR-01: Interrupting preflight leaves its descendants outside the supervisor's reaper

**Classification:** BLOCKER.

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

**Classification:** WARNING.

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
