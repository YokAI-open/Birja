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
