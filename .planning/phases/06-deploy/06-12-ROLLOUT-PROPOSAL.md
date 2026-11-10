# Release 0.4.0 publication and later rollout proposal

Updated 2026-11-10 for the owner-authorized local routing/startup correction.
Production commands below remain a proposed maintenance sequence requiring
measured preflight inputs and separate approval.

## Current release boundary

PR [27](https://github.com/YokAI-open/Birja/pull/27) publishes exact
`945791115c0bd88fd0cf62835aca3e03c395659f` from release-0.4.0 into main.
[Actual CI42787743632](https://github.com/YokAI-open/Birja/actions/runs/42787743632)
passed all six jobs. Independent source reviews and actual retained cutover /
old-app rollback proof pass. The known health-screen retry is preserved in
RELEASE-CI. Closing planning metadata is local for next approved integration;
PR27 merged approved9457911 into main as `46d24c8591de2207cf219429aac0768962bed4c3`. Prior16623a8/77dcd44/38eb25c
results and corrected failures remain historical evidence.

The unchanged independently installed recovery archive is
`d5fe2059b3e984ffcd0dff6b1763dd5a97deddb0be638ca23e49381d35a54401`.
This identifies recovery, not the future retained deployment MANIFEST.
No app, dependency, image pin, base Compose or recovery CORE changes are
included in the local correction.

| Separate decision | Required scope and evidence | Present authority |
|---|---|---|
| Release publication | Approved9457911 pushed; six actual CI jobs green | Complete |
| Main PR merge | Owner-approved9457911; six green jobs; merge commit `46d24c8591de2207cf219429aac0768962bed4c3` | Complete |
| Tag / GitHub release | v0.4.0 published at46d24c8; annotated remote tag verified | Complete |
| Back-merge PR / merge | PR28 exact6097085; six checks green; approved merge63c9b47 | Complete |
| Production rollout | Measured preflight, retained MANIFEST and maintenance window | Pending |

The owner authorized local correction and bounded reviewed/tested CI follow-ups.
Publication, exact-head CI and owner-approved main merge are complete.
Resulting main SHA is `46d24c8591de2207cf219429aac0768962bed4c3`; v0.4.0 tag/release publication is approved and complete; back-merge is approved and complete as63c9b47; production remains unapproved.
Main merge, tagging and deployment remain separate decisions.

## Recorded target and recovery limits

Target is DE189274, production checkout `/srv/birja`, project `birja-prod`;
existing public edge is birja.nist.one via Cloudflare Full(strict), host nginx,
and backend loopback port 18000. Recorded baseline is v0.3.1 at
`0107706617b8bbf9c1a069f3e3ccc9c53b9ab2f7`, Alembic 0007. This is history,
not a new inspection. Preserve existing manual origin-certificate/DNS/firewall
procedures; no Cloudflare API token or firewall change is proposed.

Last real backup completed Nov 9 at 07:43:40Z (11.817s); exact snapshot
`bed51816831081a195e4b3ef5b39f8f4059cd8feb1b4e51289f9bed05da46194` passed
isolated retrieval/restore at 07:44:22Z (12.211s), with private invariants and
source/config/tool binding. No current freshness or remote existence check
was performed here. Recovery admission uses conservative backup **data time**
and source/configuration binding, not these completion times alone; the accepted
maximum data age is 26 hours and measured recovery target is within four hours.

The enabled timer was recorded awaiting its first genuine activation on Nov 10
at 03:11:32Z. Owner explicitly deferred that observation. No scheduled success
is inferred; Plan09/DEPL-02 remain pending. No timer change is proposed.

## Local routing and startup correction

The original readiness review found missing persistent selected-clone routing
and TLS/HBA startup ordering. The local correction provides a fixed protected
`/etc/birja/datastore-bindings.json`, an external-volume-only retained overlay,
actual sole-container/mount/image/user/network guards, and the limited
`--start-selected-datastores` entrypoint. Deploy, recreation and old-app rollback
consume the same selected candidates. Source reviews and test outcomes are in
06-12-LOCAL-FINAL-REVIEW and 06-12-LOCAL-FIX-EVIDENCE.

Prepare final retained source, TLS/HBA, role/prod/binding and approved recovery
material while old datastores remain available with writers stopped. Then take
a fresh backup/exact isolated restore using unchanged installed tools and the
actual old live deploy-log SHA. Hold the shared lock without bound-material
changes through stop/copy/start. First-start admission authenticates the exact
completed profile through the unchanged recovery gate, then compares actual
candidate revision before role SQL, migrations or writers. Normal deploy and
rollback use the actual running revision.

Production source_compose overrides remain forbidden. Existing recovery_files
can bind canonical root0400 MANIFEST, root0600 bindings and approved private
custody/configuration files. Live server key0640 and CA certificate0644 do not
qualify directly; the TLS checker validates their actual pair/CA/hostname before
startup. Production measurements and custody coverage remain preflight inputs.

## Required preflight bindings before a production decision

Collect only after an explicitly authorized read-only preflight. Keep private
configuration/invariant evidence protected; publish sanitized results only.

| Binding | Required measured value; currently unresolved |
|---|---|
| Source | Final approved main SHA, exact clean checkout/tree, tested-source attestation and retained deployment MANIFEST SHA |
| Containers/images | Exactly one current production PostgreSQL/Redis/backend/scheduler; immutable old image IDs and old rollback availability |
| Original storage | Actual named-volume identities mounted at PG `/var/lib/postgresql` and Redis `/data`; owner/path/state checks and no other writers |
| Candidate storage | Explicit newly approved empty PG/Redis clone names, distinct from originals, and reviewed persistent routing for all retained operations |
| Capacity | Measured source/clone sizes and available local disk for both preserved originals and candidates; B2 bounded headroom/controls via installed tools |
| Data compatibility | Actual PG18 path, extensions/locales, UID and recorded/actual collations; Redis AOF state/auth/TTL/noeviction; private equality baseline |
| Private configuration | Protected prod/role/TLS/recovery identities and root-only paths, independent credential/CA custody confirmed; no values/fingerprints invented here |
| Recovery | Revalidated installed archive/launchers, current completed backup + exact isolated restore bound to actual source/configuration; fresh gate succeeds |
| Maintenance | Owner-approved write outage/window, writer inventory, routing cutover and explicit abort boundary before new writes |

Select containers using fixed `com.docker.compose.project=birja-prod` and
service labels; reject zero/multiple matches. Read only the selected mount,
image and ID fields, never container environment. Runbook volume names are
documentation defaults, not measured selectors for this operation.

## Proposed maintenance order after resolving those bindings

This is a review sequence, not an executable end-to-end run sheet. Placeholders
below require measured, reviewed values before any action. All mutations must
be serialized under `/var/lock/birja-deploy.lock`, with kernel-validated inherited
lock descriptors where the supported helper accepts them. Do not disable locks.

1. Revalidate target, unchanged recovery installation, off-server custody,
   writer inventory and disk/B2 headroom. Under one held operation lock, close
   admissions and stop all app/external writers while old PG/Redis remain up.
2. Select the exact approved clean main source and install retained deployment
   through `deploy-entrypoint.sh --install --approved-operation
   install-retained-deploy --tested-source <approved-main-SHA>`. Record its
   MANIFEST separately. Prepare the measured original/candidate binding records
   for four distinct existing volumes and final prod/role/recovery configuration.
3. Provision/check final TLS/HBA before any candidate start, using retained
   `provision-db-tls.sh --production --create --approved-operation
   production-db-tls --approved-custody owner-off-server-password-manager`
   (existing material uses its reviewed check/renew procedure). Confirm readable
   nonsecret retained HBA, protected server key and actual CA/hostname checks.
4. Verify old sole service/original mount identities read-only. Keep backup
   release equal to actual old live_sha, include approved final private material,
   and invoke installed `birja-backup`, then `birja-restore-check --snapshot
   <exact-64-hex-ID> --approved-clone`. Require full exact restore success after
   all bound changes. Upload and repository verification precede one-copy
   rotation; a later isolated-restore failure blocks cutover and acceptance
   but does not guarantee the previous snapshot remains after rotation.
5. Cleanly stop old datastores, record private stopped fingerprints, and copy
   each original read-only into its approved empty candidate. Convert only
   candidate PG18/docker ownership to70:70 and Redis data to65532:65532.
   Preserve originals and old images. No running physical copy, original chown,
   bound-material changes, or converted-data reuse under old libc.
6. Invoke `/usr/local/sbin/birja-deploy --start-selected-datastores` under the
   inherited held lock. It starts only PG/Redis after strict recovery/TLS/data
   admission and verifies actual selected mounts and admitted revision equality.
   Compare private invariants; inspect collation drift and rebuild approved
   affected indexes BEFORE refreshing collation versions. Verify indexed versus
   sequential results and index validity. Confirm Redis AOF/auth/TTL/noeviction.
   Do not insert synthetic keys in production without separate approval.
7. Inspect/apply roles through retained `configure-db.sh --production --inspect`
   and `--production --apply --approved-operation populated-role-transition`.
   Refresh any invalidated recovery proof using the same installed tools.
   Normal deploy must pass the strict gate against actual source/revision.
8. Deploy using `DEPLOY_REF=<approved-main-SHA> /usr/local/sbin/birja-deploy`.
   The allowlist accepts main, v0.3.1 or tested_source, not v0.4.0. The retained
   orchestrator runs the separate 0007→0008 migrator before app/scheduler startup.
   Verify least-privilege roles, actual TLS and origin/public smoke through
   retained `smoke-prod.sh` and `--public`; print only sanitized results.
9. Set protected backup release identity to actual deployed SHA and take a fresh
   backup/exact isolated restore using the same unchanged independent archive.
   Post-rollout recovery failure leaves acceptance pending. Recheck original
   fingerprints, selected mounts and immutable retained source. Resume admissions
   only at the approved maintenance acceptance point.

## Maintenance duration and undo

No production outage estimate is yet defensible: real volume sizes, copy/disk
throughput, affected collation indexes, index-build contention and artifact
build/cache state have not been measured. Synthetic feature CI observed roughly
34s transition, 63s recovery, 24s roles, 23s TLS and 96s old-image rollback;
the earlier real backup/restore took about 12s each. These are evidence of
operation success, not a promised downtime budget for production.

Before candidate writers resume, engine cutover abort means reselecting the
untouched original PG/Redis volumes with their original pinned Debian images,
UID999 and original collation/AOF state, then verifying the private baseline.
Never mount a converted/reindexed candidate under old libc or chown it back.
After new writes, originals are stale: switching back would discard accepted
writes and requires a separately reviewed data-recovery decision.

Application rollback is different: `/usr/local/sbin/birja-deploy --rollback`
uses the retained secure orchestration with tested actual v0.3.1 app code,
current database engine/TLS roles and reviewed current build instructions.
It leaves 0008 in place and never undoes schema automatically. Its fresh
recovery/config gate must still pass. If migration 0008 leaves an invalid named
index, stop and inspect exactly the runbook's index/revision/definition; any
`DROP INDEX CONCURRENTLY public.ix_trades_user_created_id` repair needs separate
scoped maintenance approval. No wildcard/CASCADE/downgrade or automatic real
restore is an undo method.

## Scope of this preparation

Local source, tests, independent reviews and synthetic evidence are tracked
separately. No production volume/TLS/role/app operation, provider inspection,
updated release push, merge or tag is included. Plan09's first actual nightly
observation remains explicitly deferred; no scheduled success is inferred.
Production approval requires measured preflight bindings and an exact final
source/MANIFEST/window, even after local proof and new release CI pass.
