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
