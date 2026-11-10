# Accepted published release CI —2026-11-10

[PR27](https://github.com/YokAI-open/Birja/pull/27) is OPEN into main at exact
`945791115c0bd88fd0cf62835aca3e03c395659f`.
[Run42787743632](https://github.com/YokAI-open/Birja/actions/runs/42787743632)
completed SUCCESS: backend/frontend/image/e2e/ops/ci-pass all green.
GitHub reports MERGEABLE/CLEAN against main0107706617b8bbf9c1a069f3e3ccc9c53b9ab2f7.
No merge/tag/deployment occurred. Closing planning metadata stays local for
next approved integration; it does not change this verified published head.

Backend616/critical100%, frontend264, five raw reports hash/config-ID verified
and each0HIGH/CRITICAL. Browser9passed +1flaky health test passed on retry,
1expectedproductionCSPskip. Preserve the known retry; no claimed flake fix.
Actual ops transition35.842s/recovery58.140s/roles18.595s+65denials/TLS20.069s/
existing old-app rollback85.653s/new retained selected cutover206.439s pass.
Real secure startup, forced recreation,0008, actualv0.3.1 app rollback, Redis
state/authentication, untouched original fingerprints and same installed
pre/post backup/exact restore all pass. Mandatory fixture cleanup succeeded.
The CI-only Git and precise Compose consent corrections are confirmed on the
actual runner. Independent reviews and full supplied d5fe2059 proof retained.

Public job metadata/logs and raw reports are preserved in ignored private
pr-preparation/release-compose-pin-* evidence. Prior failures below remain
historical; final accepted source and outcomes above supersede pending text.
Plan11 complete;09nightly remains deferred; no DEPL/whole-phase completion.

# Current CI tooling correction —2026-11-10

Published38eb25c/run42785059635 passed backend616/critical100%, frontend264,
browser10/1expectedskip/no retry, and five hash-verified raw0HIGH/CRITICAL
reports. Ops confirmed the Git fix: real retained secure startup9.693s,
role apply and forced recreation passed. Full deployment then failed at the
backend Bake build because its retained Dockerfile is outside app context
and lacked explicit filesystem consent. Cleanup passed; aggregate failed.

## Reviewed precise-consent tooling pin

REDb31f3dd/GREENd7f0cf5 pins only the disposable ops runner's
Docker-signed-apt docker-compose-plugin=5.7.0-1~ubuntu.24.04~noble. A clean-root
actual version gate precedes fixtures. Nine CI contracts passed0.363s,
focused Ruff/format/diff pass, and independent source review is clean in
06-11-CI-COMPOSE-REVIEW. No Bake bypass, wildcard grant, recovery/runtime/image
or production tool change is introduced.

[Official Compose5.7.0 source](https://raw.githubusercontent.com/docker/compose/v5.7.0/pkg/compose/build_bake.go)
includes the resolved Dockerfile in localBuildPaths and emits precise fs.read
consent. Its official apt package exists with SHA256
61dd23ec4d0f6e4a99ef841f2ea2c0dc9cbada2c6ad99ffbd4f980ae957cc691.
For local testing only, official release binary SHA256
7758048ad38e580f22559603312874fec8bb638d021a9e64182385fc17cc12a2
and checksum-file digest were verified against publisher release metadata.
The verified plugin was copied only into the temporary fixture HOME; actual
launcher plugin5.7.0 was asserted. Host Compose5.0.0/Buildx0.30.1 were unchanged.
This temporary wrapper did not modify fixture source or production launchers.

The complete supplied d5fe2059 archive proof atd7f0cf5 passed257.676s:
real retained TLS-first startup, full backend/frontend deployment/0008, actual
v0.3.1 app rollback, three exact restores, Redis GET/TTL/NOAUTH, original
fingerprints and retained source hashes all pass. Finally cleanup completed.
Private raw log: local-rollout-evidence/cutover-compose-570.log.

Owner explicitly authorized further reviewed/tested CI/test/planning follow-ups
until CI passes. Publish this in-scope correction without re-asking, then
require actual new-head CI. No main merge/tag/back-merge/deployment or Plan11 /
DEPL completion is implied. Earlier evidence below remains historical.

# Current release CI and reviewed fixture correction —2026-11-10

Owner approved publishing18 commits through
`77dcd44e852a079d4541c78f724717a0dd13afba`; nonforce push and PR27 update
succeeded. [Actual run42782054013](https://github.com/YokAI-open/Birja/actions/runs/42782054013)
completed with backend/frontend/image/e2e SUCCESS and ops/ci-pass FAILURE.

- Backend616 tests passed; critical-path coverage100%; dependency audit passed.
- Frontend264 tests passed; lint/types/format/audit passed.
- Browser10 passed, one expected production-only CSP skip, no retries.
- Five downloaded raw image reports match their recorded SHA256 and config
  identities; every report has0HIGH/0CRITICAL. Strict policy unchanged.
- Ops transition34.841s, recovery58.758s, roles22.158s/65denials,
  TLS21.576s and existing actual-old rollback94.821s passed. New fixture then
  rejected its private Git checkout at candidate first-start; finally cleanup
  and the separate cleanup step passed. Aggregate correctly failed.

## Bounded correction, not yet published

RED7d3f8a4 / GREENc343f6b changes only selected-cutover.py/test-ci-ops.py.
The generated synthetic launcher now sets GIT_CONFIG_NOSYSTEM=1 alongside its
private TMPDIR. Production entrypoint, app/runtime, image pins, dependencies,
recovery CORE/archive and Landlock allowlist are unchanged. Repository ownership
checks remain active; no wildcard safe.directory is introduced.

The regression executes the actual generated clean environment under Landlock.
Denied synthetic host system config reproduces real Git rev-parse exit128;
with isolation it passes and reads the repository-local marker. Removing.git
still rejects. Eight CI contracts passed0.321s; focused Ruff/format/diff pass.
Independent review is clean, including an independent regression rerun; see
06-11-CI-GIT-REVIEW. [Git documents system-config isolation](https://git-scm.com/docs/git-config#Documentation/git-config.txt-GITCONFIGNOSYSTEM).
The original runner masks Git stderr, so this reproduces a compatible failure
mechanism; only new actual CI can confirm the correction there.

The complete affected supplied-archive proof atc343f6b passed246.010s:
TLS-first startup11.230s, current deploy/0008 116.441s, actual v0.3.1 rollback
26.218s. Pre-start backup/restore6.635s/9.023s, post-deploy8.619s/8.498s,
post-rollback8.432s/8.821s. Redis GET/TTL/NOAUTH, selected mounts, unchanged
original fingerprints and retained hashes pass. All use unchanged archive
`d5fe2059b3e984ffcd0dff6b1763dd5a97deddb0be638ca23e49381d35a54401`.
Cleanup completed. Private raw log: local-rollout-evidence/cutover-git-isolation.log.

The correction requires a new publication decision;77dcd44 approval covered
only that exact candidate. No merge/tag/deployment, Plan11 summary or DEPL
completion. Phase11/15,65/69=94%;09 calendar observation stays owner-deferred.

## Prior published release evidence (historical)

## Published release CI and rollout readiness decision —2026-11-09

Owner explicitly selected “Push and open main PR” for16623a8638407eeab27c2879f0a9396764a68e89.
Nonforce release-0.4.0 push and PR27 into main succeeded:
https://github.com/YokAI-open/Birja/pull/27.
Actual release CI42622430042 completedSUCCESS at that exacthead; all six
backend/frontend/image/e2e/ops/ci-pass checks green. No mainmerge/tag/release/
backmerge/deployment authority was granted or exercised.

Backend616/99.80%overall/100%critical; frontend264. Actual trading/portfolio/
history flows passed. Browserattempt1:9passed,1health-screen first-attempt
timeout then successonretry,1expectedproductionCSPskip. Targeted same-head
browser+aggregate rerunattempt2:10passed,1expectedskip,0retries,aggregatepass.
Initial flaky result retained, not erased or called fixed by a clean rerun.
Five raw image reports hashverify and each0HIGH/CRITICAL; original strictgate
unchanged. Ops populatedtransition34.239s/recovery59.159s/roles21.387s+65denials/
TLS21.221s/actualoldrollback89.555s pass; mandatorycleanup succeeded.

Plan11releaseCI requirement is proven. Subsequent source-only rolloutreadiness
review found CR-01: productionCompose/deploy/rollback lack protected persistent
selection of new datastore clone volumes while preserving originals. WR-01:
candidate startup requires TLS/HBA material before startup; proposal revised
to make this explicit, actual bootstrap/material state still unmeasured.
Role/backup exec helpers need verified solecandidate identity/mountmapping,
not necessarily separatevolume selectors. See06-12-READINESS-REVIEW and revised
ROLLOUT-PROPOSAL. No highfinding waived, no executableliveproposal is ready.

Next scope decision: prepare/test/independently review a protected clonebinding
and concrete TLS startup procedure locally before changing the release, or
consider publishing currentrelease without any deployment. Recommend fixfirst.
Any changedreleasehead needs a new concrete reviewedpushchoice and ownCI;
current166approval does not authorize unreviewedsourcepublication.
Keep PR27open/unmerged; do not request productionapproval against placeholders.
11SUMMARY remains pending readiness disposition;phase11/15,65/69=94%.
09nightlyproof still owner-deferred; no09SUMMARY/DEPLadvance.
