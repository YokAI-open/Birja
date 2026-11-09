# Release 0.4.0 publication and later rollout proposal

Prepared 2026-11-09 from source and recorded evidence only. No command below
was executed. This document does not grant authority or claim release CI passed.

## Current release boundary

PR [27](https://github.com/YokAI-open/Birja/pull/27) targets main from
release-0.4.0 at exact `16623a8638407eeab27c2879f0a9396764a68e89`.
Actual release CI [42622430042](https://github.com/YokAI-open/Birja/actions/runs/42622430042)
is being monitored separately by the parent; its result must be recorded before
publication approval. Prior feature CI is not a substitute. Current authority
covers release branch push, main PR creation and CI inspection only.

The release contains approved Phase 5 and Phase 6 integration. Since the
reviewed recovery payload, changes are limited to CI/tests, planning and project
version metadata; no changed recovery payload or new image pin is proposed.
The independently installed recovery archive remains
`d5fe2059b3e984ffcd0dff6b1763dd5a97deddb0be638ca23e49381d35a54401`.
This is the **recovery** archive identity, not an already installed/approved
retained deployment bundle identity. The latter must be recorded separately
from the final selected source and its MANIFEST.json.

| Separate decision | Concrete scope and prerequisite | Present authority |
|---|---|---|
| Merge release PR27 | Recheck exact head above, all six required jobs green and independent review; Create a merge commit into main | Not granted |
| Tag v0.4.0 | Bind the tag to the resulting verified main merge SHA, record tag object and target; present SHA again if owner wants exact resulting-SHA approval | Not granted |
| Publish GitHub release | Separately review notes/assets and whether a GitHub release is desired; tagging alone is not that publication | Not granted |
| Release back-merge PR | Propose release-0.4.0 into develop, recheck exact source/target; any additional branch push requires its own scope | Not granted |
| Back-merge PR merge | Wait for that PR's own exact-head green CI and applicable explicit approval; use a merge commit | Not granted |
| Production rollout | Requires the missing routing/preflight decisions below, then a distinct concrete approval | Not ready for approval |

Publication can be approved separately after release CI succeeds. The main
merge, tag/publication and back-merge do not authorize any live operation.
The final main SHA and tag do not exist yet; do not fabricate them or accept
a different release PR head without renewed review.

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

## Independent readiness review

06-12-READINESS-REVIEW confirms one rollout blocker (persistent clone-volume
routing) and one startup-order warning. This remains a non-executable draft.
Role and installed backup helpers use compose exec, so they need a proven sole
candidate container/mount identity rather than independent volume selectors.
The warning is made explicit below: TLS/HBA prerequisites must exist before
candidate PostgreSQL startup. No implementation or live fix is claimed.

## Production blocker: selected-clone routing

`docker-compose.prod.yml` declares pgdata/redisdata without configurable
external names. The retained helper fixes its Compose paths and project;
`deploy-entrypoint.sh` does not accept a caller-selected Compose file/volume
override. `configure-db.sh` independently uses its retained base Compose too.
Therefore new clone names cannot presently be substituted through a supported
retained deployment interface while preserving the untouched originals.

Do not invent a volume-selector flag, rely on COMPOSE_FILE/ambient environment,
silently patch an immutable bundle, delete/reuse the original volume names, or
let a later `compose up` reattach originals after manually starting clones.
The runbook supplies the maintenance policy and synthetic clone rehearsal;
it does not supply this missing production routing mechanism.

Before requesting production approval, choose and independently review an
explicit protected volume binding consumed by retained deploy/rollback service
creation. Prove the sole candidate container and its actual mounts before role
SQL or installed backup exec operations. A separately specified logical-restore/
cutover alternative would still need persistent routing and a preserved original. Any implementation/test/artifact
change is new work requiring its own scope. This proposal makes no such change.

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

1. Revalidate target, immutable recovery installation and independent custody.
   Use installed `/usr/local/sbin/birja-backup-status`; if recovery is stale or
   mismatched, obtain/perform the scoped fresh backup and exact retrieval/restore
   before maintenance. Supported interfaces are `/usr/local/sbin/birja-backup`
   and `/usr/local/sbin/birja-restore-check --snapshot <exact-64-hex-ID>
   --approved-clone`. Only fixed isolated birja-restore-check is a restore target;
   never restore directly over production. Preserve a completed point on failure.
2. Close admissions and stop **all** writers. For the recorded old production
   orchestration, the runbook's explicit Compose path/env/project can stop
   backend and scheduler; confirm no external writers. Then cleanly stop
   postgres and redis before the physical copies. Record the stopped-source
   baseline privately and preserve both original volumes plus old pinned images.
   Do not perform the copy against a running PostgreSQL cluster or active AOF.
3. Create only the explicitly approved new empty volumes. Reuse the tested
   filesystem-copy shape: `docker run --rm --network none --read-only` with
   original mounted `/original,readonly`, candidate mounted `/clone`, and the
   exact pinned reviewed PostgreSQL image as the filesystem tool. The tested
   shell operations are `cp -a /original/. /clone/ && chown -R 70:70
   /clone/18/docker` for PG and `cp -a /original/. /clone/ && chown -R
   65532:65532 /clone` for Redis. Bind those mount sources only to the measured
   originals and approved candidates; never recursively chown an original.
   This is not authorization to run the synthetic fixture against real data.
4. Before candidate PostgreSQL startup, bind the selected retained helper
   source and validate/provision its required TLS server/key/HBA mounts under
   the exact lock/custody gates. If a distinct maintenance bootstrap is needed,
   specify and independently review it; no ambient plaintext override. This
   prerequisite cannot be postponed until role SQL in step 6. Actual existing
   TLS state is unmeasured.
   Start only candidate datastores through the newly reviewed routing. PG uses
   the pinned PG18.6/glibc2.44 image as 70:70, with PGDATA at
   `/var/lib/postgresql/18/docker`. Compare exact private data/schema/session/
   financial/sequence invariants with the stopped source. Inspect actual used
   collation drift; rebuild affected indexes with reviewed REINDEX maintenance
   **before** any `ALTER COLLATION ... REFRESH VERSION` or database collation
   refresh. The synthetic `REINDEX DATABASE birja_source_test` is not a command
   for production; select production database/index scope after inspection.
   Verify locale-sensitive indexed results against sequential results and all
   index validity flags. Do not merely refresh catalog version strings.
5. Verify Redis candidate owner 65532, authenticated reload and restart, AOF,
   noeviction and retained TTL behavior. An unauthenticated request must fail.
   Do not discard OTP/rate-limit state or insert synthetic keys into production
   without separately approving that exact check. Both original volumes remain
   stopped and unchanged after their recorded baseline.
6. Apply role SQL after collation/index checks, against the **selected
   candidate** only. Final TLS/HBA startup prerequisites must already have been
   satisfied before step 4; complete final mount/verification checks here. Existing exact helper interfaces are retained
   `configure-db.sh --production --inspect`, then `--production --apply
   --approved-operation populated-role-transition`, and `provision-db-tls.sh
   --production --create --approved-operation production-db-tls
   --approved-custody owner-off-server-password-manager` (use renew/check only
   if actual existing state calls for it). Resolve source routing and custody
   first. The TLS helper does not restart PostgreSQL. Mount server material
   only into PostgreSQL, CA only into clients; verify hostname/CA, local HBA and
   expiry, and owner off-server signing-CA/credential custody before restart.
7. Select the approved clean source and install the retained deployment bundle
   with `/srv/birja/deploy/deploy-entrypoint.sh --install --approved-operation
   install-retained-deploy --tested-source <approved-main-SHA>`. Its precondition
   is that exact clean `/srv/birja` HEAD; review the source-selection procedure
   under the shared lock before doing so. Record the resulting deployment
   MANIFEST identity separately; leave recovery/current at d5fe2059… unchanged.
   The installer changes managed sparse checkout/launcher routing, not database
   volume selection; it does not resolve the blocker above.
8. After config/security/custody transitions, regenerate any recovery binding
   invalidated by those transitions, using the same installed independent
   backup/restore tools. Never patch evidence. Require the strict pre-deploy
   recovery gate to pass for actual current source/revision/configuration.
   Proposed deploy interface is `DEPLOY_REF=<approved-main-SHA>
   /usr/local/sbin/birja-deploy`, with that SHA installed as tested_source.
   The current allowlist accepts main, v0.3.1 or tested_source, **not v0.4.0**;
   do not propose the latter as DEPLOY_REF without a separately reviewed change.
9. The retained deploy performs the separate one-shot migrator and 0007→0008,
   then starts backend and exactly one scheduler and swaps the frontend/nginx.
   Runtime app/scheduler are non-owner least-privilege roles; the migrator is
   a separate DDL login. Verify actual role/catalog/pg_stat_ssl booleans and
   origin/public smoke using `/var/lib/birja/ops/current/deploy/smoke-prod.sh`
   and its `--public` mode. Do not print rows, credentials or service logs.
10. Synchronize protected backup JSON release identity to the actually deployed
    full SHA, preserving the independently retained recovery tool hash. Use
    the **same** installed birja-backup and birja-restore-check for a fresh
    post-rollout backup/exact isolated restore. Verify tool identities and
    socket-based source access still work independently of hardened app logins.
    Post-rollout recovery failure leaves acceptance pending; neither old proof
    nor a successful HTTP smoke replaces this evidence.

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

Only this proposal was written. No live/private/network inspection, replay,
source edit, branch operation, commit or remote write occurred. Evidence comes
from 06-12-PLAN, RUNBOOK's retained operations/image-collation/recovery sections,
current retained deployment/role/TLS code, synthetic transition source and
06-LIVE-HANDOFF/06-LIVE-RECOVERY records. Parent-owned state and .claude/ remain
untouched. Release publication can advance through its own approvals after
actual CI; production approval must wait for the routing gap and measured
preflight bindings to become concrete.
