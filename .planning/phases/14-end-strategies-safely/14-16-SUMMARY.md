---
phase: 14-end-strategies-safely
plan: "16"
subsystem: testing
tags: [postgresql, recovery, coverage, source-integrity, lifecycle]
requires:
  - phase: 14-15
    provides: Strict current0023 and retained0020/0017 recovery authority
provides:
  - 64 critical modules with unchanged strict coverage thresholds
  - Bounded preflight and durable authenticated one-shot qualification supervision
  - Exact legacy0014 migration admission and independently verified bootstrap parity
affects: [14-17, 14-18, 14-19, recovery]
tech-stack:
  added: []
  patterns: [source-bound one-shot receipts, finite legacy authority admission]
key-files:
  created:
    - deploy/tests/run-portfolio-campaign.py
    - .planning/phases/14-end-strategies-safely/14-16-LEGACY-TRANSITION-REVIEW.md
  modified:
    - .github/workflows/ci.yml
    - deploy/tests/run-portfolio-validation.py
    - deploy/tests/portfolio-smoke.py
    - backend/app/db/portfolio_bootstrap.py
    - backend/app/db/portfolio_migrate.py
    - deploy/db/bootstrap-roles.sql
key-decisions:
  - Preserve all61 critical modules and add three closure/lifecycle/schema paths; require exact100% statements/branches and80% overall.
  - Authenticate genuine0014 complete catalogue, object ACLs and defaults before any migration child; retain exact final0023 runtime admission.
  - Preserve failed diagnostic receipts and use a new immutable archive after harness fixes; reserve canonical14 archive for Plan18.
requirements-completed: []
duration: 132min
completed: 2026-11-19
---

# Phase14 Plan16: Exact Qualification Supervision Summary

**Strict closure coverage, durable source/image/archive-bound campaigns, and genuine0014 migration admission now have focused and actual recovery evidence.**

## Performance

- Started after Plan15 handoff at2026-11-19T20:14Z; completed2026-11-19T22:26Z.
- Tasks:2/2. Twenty implementation/provenance files plus this summary changed.
- All work stayed local. No dependency/image-pin changes, provider operations,
  production access, publication, deployment or human acceptance occurred.

## Accomplishments

- CI retains all61 existing critical paths and adds closure/lifecycle services
  and closure schema (64 total). Both current bootstrap/migrator remain critical.
  Statement/branch100% and overall80% thresholds, all existing security gates and
  issue35's exact accepted-risk scope/2026-12-17UTC expiry are unchanged.
- The runner retains all seven ordered stages, complete immutable0020 source
  `9527e358bc6953cec7580043703324db194ba396` and0017 source
  `4b4320b4cc373268a8d598612a563cd5ef199700`, and separate older lanes. Current
  profile isV3/rev0023/deploy-recovery-v4 with31 tables/24 tails. Every current
  restore validates original manifests before grants and exact nonquarantined
  final authority afterward. Cold/fresh/upgraded modes compare all three digests.
- Bounded preflight checks installed tools, exact stripped PATH, current pins,
  fixture tail, and real owned authority/create/admission tests before long work.
  It installs nothing and does not load development/production secret files.
- The one-shot supervisor records PID/startticks, source hashes, original child,
  private logs, elapsed time, exit and cleanup disposition. Status/resume inspect
  the original run; they never launch replacements. Source, archive, imageID or
  alias changes, PID reuse and receipt/path symlinks refuse. Interruptions reap
  the owned process group; borrowed stack authority is checked and never cleaned.
  Atomic fsynced receipt publication prevents partial JSON status reads.
- Source integrity includes tracked and nonignored untracked relevant files,
  additions/renames and ignore configuration. Internal symlink identity is
  hashed without following its target; escapes refuse. Ignored secrets remain
  unread. Missing/changed image bindings refuse without rebuild, retag or RootFS
  equivalence substitution.
- The actual old dev0014→0023 path exposed a real missing finite admission pair.
  Exact prior catalogue/ACL/default authentication now precedes the migration
  child, Python and administrativeSQL accept only the measured inherited pair,
  and ordinary runtime still requires final0023 authority. Historical migrations,
  projections and final fingerprints remain unchanged.

## Task Commits

1. Task1: `7c321d1` — extend critical coverage and current/retained runner contracts.
2. Task2 prerequisite RED: `e37de93` — reproduce genuine14 authority gaps.
3. Task2 prerequisite GREEN: `af8f3e8` — exact legacy authentication and bootstrap parity.
4. Task2: `2642c48` — durable supervisor, bounded preflight and exact recovery graph.
5. Task2 actual-proof fixes: `11e9afc`, `159d6d8` — authenticate only the initial
   prepared14 transport before financial imports; later23 probes use normal admission.
6. Task2 final regression: `8e1b150` — assert that sole prepared14 call-site boundary.

## Verification

| Evidence | Actual result |
|---|---|
| Critical-path configuration |3 assertions passed;64 modules |
| Bounded real preflight |139 passed34.11s;41.108s receipt, unchanged source |
| Legacy14 RED |3 expected failures18.49s;19.916s receipt |
| Bounded legacy14 GREEN |7 passed36.50s |
| Relevant real backend group |202 passed1070.95s;1072.525s receipt, unchanged source |
| Changed runtime critical coverage |133 statements/36 branches;100%/100%, zero misses |
| Final CI ops contracts |82 passed22.694s;22.900s receipt, unchanged source |
| Final runner/supervisor contracts |23 passed6.718s |
| Final image/source contracts |22 passed5.712s |
| New-archive genuine14 TLS upgrade |Passed20.257s |
| Same-archive fresh TLS |Passed15.884s |
| Same-archive genuine20 TLS upgrade |Passed15.690s |
| Same-archive encrypted cold restore |Passed53.390s |
| Actual dev fresh/14 upgrade |Passed19.043s/22.109s;42.726s total, unchanged source |
| Static checks |Scoped Ruff/format/mypy, shell syntax and diff checks passed |

The202 cases include prior14 missing/extra/unsafe objects, grants and default
drift, source mismatch and before-child refusal without financial/schema/ACL
mutation; both legitimate default variants; post14 administrativeSQL/Python
parity and refusal of partial lifecycle reads, extra grants and unsafe defaults.
Existing staged15/16 behavior and financial/role refusals remain represented.
The final backend suite is expected to contain3653 tests after30 new cases;
**no whole3653-test or whole-security pass is claimed here**.

A real detached20-second synthetic supervisor lifetime probe survived launcher
exit and a separate status/resume call with the same PID/startticks and runID,
then exited0 without replacement. It was explicitly NOT_QUALIFICATION; current
offline contracts additionally cover source mutation/addition/link, malformed
authority digest vectors, image changes, PID reuse and atomic receipt behavior.

R3 actual proof source: `159d6d87049d65463314b50ead94cde1bddda82b`.
Archive: `/tmp/birja-backup-test-p14-16-proof-r3/recovery.tar`.
SHA256: `7a698a7667efc0c3ff6b7545dabd89e969d6f4d9adcd5fde5d93b9f5a19aceff`.
All four actual recovery modes return identical final catalogue/object/default
digests and unchanged-source receipts. The later8e1b150 commit changes only a
test; runtime, harness and archive-qualified source bytes remain unchanged.
Full private receipts/logs are under `/tmp/birja-phase14-plan16/`.

## Deviations from Plan

1. **[Rule3 — Blocking fixture issue]** Complete authenticated backend/scheduler
   images replace unreadable root-owned host bind overlays in the dev test.
   This fixes a real PermissionError without weakening image equality checks.
   Additional harness files test-ci-ops.py, test-dev-bootstrap.py and the finite
   owned preflight project recognizer in test-db-config.sh were explicitly scoped.
2. **[Rule1 — Migration authority bug]** Parent authorized the concrete legacy14
   repair after measured evidence: bootstrap.py, portfolio_migrate.py, matching
   administrativeSQL, two backend regression files, coordinated backup/restore/
   deploy pins, and transition provenance. RED preceded GREEN. No historical
   authority asset or generic fallback changed. See the transition review.
3. **[Rule3 — Synthetic restore guard]** verify-restore.py allows only the exact
   canonical14 archive path in addition to existing scoped synthetic paths.
4. **[Rule1 — Actual diagnostic admission]** R1/R2 proofs exposed empty-schema
   and repeated-transport assumptions. Fixed only the explicit current14
   diagnostic branch, with source/full authority authentication before imports
   and later final23 probes unchanged. Failed archives and receipts remain.

An early CIops run failed because tracked source changed while its genuine
source guard was active. A frozen rerun passed; it is not reported as an
application defect or a passing earlier campaign. No test/security gate was waived.

## Cleanup and Preserved Evidence

Owned preflight/backend/TLS/cold/dev resources were cleaned; real dev output ends
`all_owned_dev_financial_resources_clean=true`. TLS/cold containers and volumes
were independently checked absent. Borrowed resources were untouched.
Phase13 archive SHA remains
`6fb79a45ddcb10725b18fc756e71bd555c827a6e61a5a4a0bd2d183096114b92`;
Plan15 R4 remains
`161b8fa08eedd025b2100328e642d0928927561c6604e8d5839f3ca5130a3d9e`.
R1–R3 diagnostics are preserved. Canonical `/tmp/birja-phase14-proof` remains
absent and reserved for final18. Preexisting untracked `.claude/` is untouched.

## Remaining Integration Gates

Parent independent review follows this handoff. Plan17 browser integration,
Plan18 final whole-backend/security and uninterrupted seven-stage qualification
at one final source/archive, and Plan19 separate owner UI/native200 acceptance
remain required. No whole requirement/global planning status is advanced by
this summary. Phase7 deferred/live provider activation remains deferred.

## Known Stubs

None introduced. Stub and threat-surface inspection found no new unresolved
application behavior; the new private file/process supervisor boundary is
covered by the plan's tampering/repudiation/DoS threat controls.

## Self-Check: PASSED

All listed implementation/provenance files and seven task/fix commits exist;
actual R3 receipts are passed and source unchanged. Global state updates are
owned by the parent orchestrator and were intentionally not performed here.

## Independent Review Repairs: CR-01 and WR-01

The independent review at `ec0965c` found two genuine supervisor defects:
interrupting synchronous preflight could leave an unrecorded descendant alive,
and replaying the internal worker could overwrite original status and rerun
preflight even though exclusive command.log prevented a second long command.
The original findings remain unchanged in14-16-REVIEW.md; this implementation
record does not substitute for independent re-review.

**RED:** `286611f` adds actual stdlib-process regressions. Both findings reproduce
in0.579s: nested preflight work remains alive at terminal publication, and a
completed worker replay runs preflight twice. The test explicitly cleans the
old implementation's leaked synthetic descendant afterward. RED log:
`/tmp/birja-phase14-plan16/supervisor-repair-red.log`.

**GREEN:** `54c9120` makes preflight a separate owned session, gated until its
PID/startticks/phase/private log are durable. Cancellation signals the original
group and waits for every live descendant before terminal publication; a reused
identity refuses signalling. The preflight wrapper avoids throwing through
subprocess.run on group cancellation, allowing its direct child's shell/Compose
finalizers to finish. The real nested regression checks both wrapper and
grandchild finalizers, no live descendant, retained preflight identity, and no
long command. Long-child interruption also checks prompt cancellation/nonzero
exit rather than merely waiting for a normal child to finish.

An atomic O_EXCL claim consumes the private request before status/preflight.
The claim binds immutable request bytes, runID and original PID/startticks and
is fsynced before work. Completed, active, concurrent and stale replays refuse
without changing original logs/status/identities or rerunning preflight. Claim
identity/request mutation negatives refuse, and status/resume remain read-only.

**Honest escalation:** `3b2b24d` retains a group-killed/finalizers-unconfirmed
disposition after bounded SIGKILL escalation, with resource cleanup explicitly
not attested. Its actual bounded forced-preflight case proves the finally marker
is absent, all work is gone, and no long command started. Process reaping is
never presented as evidence of successful resource finalization.

Final focused results:28 runner/supervisor cases passed8.189s;22 image/source
cases passed5.385s;88 CI ops cases passed23.050s. The CI block discovers the
new contract cases. Scoped Ruff/format and git diff checks pass. Raw logs remain
under `/tmp/birja-phase14-plan16/supervisor-repair-{final,image,ci}.log`.
The last disposition-only change was followed by the28-case runner block;
image/CI results are from54c9120's unchanged source/image guard implementation.
The existing202-case runtime qualification and R3 TLS/archive proofs were not
rerun because no runtime, administrativeSQL, pin, fixture image or archive bytes
changed during this review repair.

**Actual detached mechanism check:** At54c9120, the real139-case preflight ran
under the new supervisor and passed33.26s; the whole bounded diagnostic took
41.947s. Separate tool calls observed the same supervisor1114247/startticks
2912888888 and preflight1114250/startticks2912888932 while active and after
completion. The retained claim matches the terminal original identity;
preflight_exit_code=0. Only a NOT_QUALIFICATION print followed preflight;
no long security/recovery campaign ran. Private receipt directory:
`/tmp/birja-backup-test-p14-16-repair-preflight`. Its owned containers, volumes
and network were independently checked absent. Later disposition/test changes
do not change the measured preflight process mechanism; the receipt preserves
its original source rather than claiming a rerun at the later commit.

No runtime/ACL/pin changes, package installation, provider/production access,
new archive, publication, global state updates or human acceptance occurred.
Original review findings remain open pending parent independent re-review.
Self-check confirms286611f,54c9120,3b2b24d and their files/evidence exist;
preexisting untracked.claude remains untouched.
