# Phase 6 production maintenance packet

Status: REVIEWED; explicit production rollout approval pending.
Owner confirmed “Any time now; only Birja writes”. This supplies window/writer
inventory, not deployment approval. New material off-server custody is confirmed.

## Immutable operation scope

- Host DE189274, checkout `/srv/birja`, fixed project `birja-prod`, public
  `https://birja.nist.one`; preserve Cloudflare Full(strict), DNS, firewall and
  manually managed HTTPS origin certificate. No account or global-tool changes.
- Deploy source `46d24c8591de2207cf219429aac0768962bed4c3`, published v0.4.0.
  Source PR27 and back-merge PR28 have six successful checks; latest actual
  CI42791351766 includes real retained cutover/recovery/TLS/old-app rollback.
- Installed retained MANIFEST
  `70e568a8c0f9953926e40de4ed79ec25272b3cdd777e474b3967a09849edb0b2`;
  independent recovery archive remains
  `d5fe2059b3e984ffcd0dff6b1763dd5a97deddb0be638ca23e49381d35a54401`.
- Originals `birja-prod_pgdata` / `birja-prod_redisdata`; candidates
  `birja-prod-phase06-pgdata` / `birja-prod-phase06-redisdata`. Revalidate actual
  protected creation-time/driver/scope records, mount identities, empty/unconsumed
  candidates and sole expected service IDs before acting. Never create a missing
  original or mount a guessed volume. Use bind mounts of inspected existing data
  directories for read/copy/fingerprinting, so Docker cannot create a lost source.
- Recorded live app v0.3.1/010770..., PG18.6/revision0007/locale en_US.utf8
  libc2.41,18valid indexes (5default-collation), Redis8.8.3/AOF/auth/noeviction.
  Revalidate these inputs; unexpected schema/source/writer identities stop work.

## Execution discipline

One continuously held `/var/lock/birja-deploy.lock` covers all bound-material
changes, fresh recovery, stopped copy, candidate startup and deployment.
Use the installed kernel-backed lock validator and inherited descriptors; every
child gets `BIRJA_BACKUP_LOCK_FD` via supported APIs. No nested uncoordinated
Compose runs. Installed deploy launcher converts inherited lock to fd9 itself.
Read JSON/dotenv as validated data, never source/eval it. Secrets stay in protected
files/stdin; no credential argv, environment dumps, raw SQL rows or public logs.
Print stage/exit/boolean outcomes only; private equality evidence stays root0600.
Do not update app source/runtime/images/installed recovery to solve a failure.

## Ordered run sheet and acceptance

1. **Revalidate before outage.** Verify all retained129file hashes and20recovery
   payload hashes, exact launcher bytes and source identity. Check CA/key/hostname
   via retained TLS `--production --check`; check original service image IDs,
   mounts/sole consumers, disk headroom and old images. Preserve current prod.env
   privately and immutable old Compose bytes from010770... plus measured old
   backend/scheduler/PG/Redis image IDs for the pre-writer abort path. No timer
   inspection/change; first-night observation remains owner-deferred.
2. **Stop writers.** Stop only the revalidated existing backend and scheduler
   containers, retain original PostgreSQL/Redis running. Confirm both writers
   stopped and no other application clients; unexpected clients block progress.
   This begins the outage; frontend may load but API requests fail until restart.
3. **Finalize protected recovery material before fresh proof.** Preserve existing
   prod.env values, append/replace only APP_DATABASE_URL, SCHEDULER_DATABASE_URL,
   MIGRATOR_DATABASE_URL, using staged hex credentials with respective
   birja_app/birja_scheduler/birja_migrator roles, database birja, host postgres.
   Never change bootstrap/Resend/JWT/OTP/Redis values. Atomic root0600 replacement,
   validate Compose with `config -q` only. Retained CA mounts enforce verification.
   Build root0600 `/etc/birja/backup-db-tls.tar` from the already-custodied CA,
   signing/server key and certificate files so private_file can bind exact bytes;
   do not regenerate any key/cert. Extend validated backup.env recovery_files
   with prod.env, db-roles.json, datastore-bindings.json, app/scheduler/migrator,
   canonical retained MANIFEST and private TLS tar; retain previous required
   entries, enforce <=20 unique private canonical files. Keep backup release at
   actual old deploy-log SHA010770..., not new checkout. Preserve all repository,
   credential, quota/reserve/freshness/retention settings. Verify protected profile
   through existing parser; capture no values. Leave material unchanged thereafter.
4. **Fresh pre-cutover off-server recovery.** Run unchanged installed
   `/usr/local/sbin/birja-backup` under held lock. It measures B2 account inventory
   and headroom, bounds requests/transfers and follows existing $0/one-verified-copy
   replacement policy. Read only sanitized status/exact resulting snapshot ID.
   Run `/usr/local/sbin/birja-restore-check --snapshot <that-exact-ID> --approved-clone`
   with the same installed payload and lock. Require full retrieval/restore,
   private schema/row/session/money/sequence invariants and strict exact-source /
   revision/config/tool freshness gate. Failed/missing/expired proof stops before
   datastore shutdown or copy. Rotation can remove the earlier snapshot after
   repository verification; isolated-restore failure blocks cutover, it does not
   promise retention of that earlier snapshot. No unrelated deletion/init/unlock.
5. **Stop/copy only after proof.** Cleanly stop only originals' selected PG/Redis
   containers (do not remove volumes). Record private full stopped-file fingerprints.
   Assert candidates still empty/unused; copy each original bind-mounted readonly
   into its distinct candidate, then change only copied PG owner to70:70 and copied
   Redis owner to65532:65532. Use pinned already-authenticated helper image, no
   registry fallback; validate fixed PG18 path and Redis AOF manifest. Originals
   and old images remain untouched; verify stopped fingerprints after copying.
6. **Secure candidates and compatibility, no app writers.** Invoke supported
   `/usr/local/sbin/birja-deploy --start-selected-datastores`, inheriting held lock.
   It requires fresh completed proof, exact candidate/TLS/HBA routing, starts only
   PG/Redis, and compares actual revision with admitted0007. Revalidate selected
   sole mounts/images/users/internal ports. Privately compare baseline table,
   session, financial and generated-identity invariants against restored/source
   evidence, without displaying data. Verify Redis AOF/auth/noeviction and existing
   TTL semantics, adding no key. Compare candidate locale/extension versions and
   index validity. Scope authorizes `REINDEX DATABASE birja` on candidate only,
   BEFORE `ALTER DATABASE birja REFRESH COLLATION VERSION`; no explicit versioned
   collations were used at preflight. If this changes, stop for review. Privately
   compare indexed versus sequential results for actual default-collation indexes,
   and repeat data/constraint/index checks. No original chown/reindex/refresh.
7. **Apply candidate roles.** Run retained configure-db.sh `--production --inspect`
   then `--production --apply --approved-operation populated-role-transition`.
   Only after compatibility passes, apply fixed9table ownership/privileges and
   staged passwords through the reviewed helper. Confirm runtime non-owner,
   NOSUPERUSER/NOCREATEDB/NOCREATEROLE and independent migrator grants. Take a second fresh
   exact backup/restore after role transition and before normal deploy;
   preserve old live release identity until successful deploy updates its history.
8. **Deploy and cross writer boundary.** Recheck exact recovery admission and run
   `DEPLOY_REF=46d24c8591de2207cf219429aac0768962bed4c3 /usr/local/sbin/birja-deploy`.
   Retained orchestration uses protected candidate overlay/current build recipes,
   separate one-shot0007→0008 migrator, and starts backend plus exactly1scheduler.
   Treat app startup as potentially accepting new writes immediately, even before
   health succeeds; after this point NEVER switch to originals automatically.
   Existing nginx becomes available as app returns; no separate traffic gate or
   synthetic live trade is introduced. Inspect sanitized role/TLS session metadata,
   origin and public smoke, actual deployed SHA/static release and revision0008.
9. **Post-rollout recovery and acceptance.** Once live deploy log records exact
   approved SHA, atomically synchronize backup release to that actual SHA. Using
   unchanged installed backup/restore entrypoints, perform another fresh bounded
   off-server backup/exact isolated restore under final config and revision0008.
   Revalidate installed hashes, source socket access with hardened roles, selected
   mounts, unchanged stopped originals, and cleanup of isolated restore resources.
   Failed post-rollout recovery keeps Plan12 acceptance pending; no rollback to
   stale originals or claims of whole-phase completion. Refresh the owner's private
   config export after final material changes before closing recovery custody.

## Downtime, timeouts and failure actions

Owner allows outage now. No production duration promise: volumes total~66.2MiB,
~63GiB free, but network/build/copy throughput is unmeasured. Synthetic complete
cutover took206.439s in final release CI; actual pre-rollout may take longer.
Use existing per-operation backup/build/health/migration timeouts. Record elapsed
outage at execution; do not weaken gates to meet a guessed duration.

Before original shutdown: if preparation/recovery fails, stop with sanitized
stage. Restore original env/config if needed and restart only the already
verified old writer containers; datastore originals stay unchanged.

After original shutdown but BEFORE new application writers: candidate failure
allows abort by stopping/removing only candidate-bound service containers (no
volumes), restoring original prod.env/source/old Compose with measured immutable
old image IDs and original volume identities, checking private original baseline,
then restarting old services. Do not mount converted candidates under old libc.
Any identity mismatch or uncertain write boundary stops for owner decision.

AFTER app startup: originals are stale even if no writes were observed. Preserve
candidates. Reviewed `/usr/local/sbin/birja-deploy --rollback` is the only normal
app rollback route: actual old app with current secure candidates/roles/TLS and
fresh recovery, schema0008 retained. No automatic schema downgrade, database
restore, invalid-index drop, wildcard/CASCADE, destructive volume cleanup, billing
policy change or new dependency/image change. Such repair requires its own scope.

## Remaining decisions

- Independent06-12-MAINTENANCE-REVIEW passed with0blockers/0warnings.
- Owner already confirmed custody and immediate window/only Birja writers.
- Ask explicit approval for this exact maintenance/recovery/copy/collation/roles /
  restart/deploy/smoke/post-recovery scope, including the explained abort boundary.
- This packet does not close09/DEPL-02 nightly observation, Plan13 friend acceptance
  or Phase6. No new release publication/push/merge authority is included.
