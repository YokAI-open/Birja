# Production preflight — 2026-11-10

Owner explicitly approved read-only checks on DE189274, `/srv/birja`, fixed
project `birja-prod`. All checks below actually ran and returned success.
No provider/timer access, backups/restores, role/schema/configuration changes,
service restart, image pull, volume creation or deployment occurred.

## Measured source and services

- Production checkout is clean, exact `0107706617b8bbf9c1a069f3e3ccc9c53b9ab2f7`
  (v0.3.1). Exactly one running/healthy PostgreSQL, Redis, backend and scheduler.
- Original volumes: `birja-prod_pgdata` mounted at `/var/lib/postgresql`;
  `birja-prod_redisdata` at `/data`. Each has exactly its sole expected container
  consumer. This does not establish absence of external application writers.
- Original PG image `postgres:18.6-trixie`, local ID
  `sha256:edb0c08dc33befd0262ab3b5cf1c4f3f8cfd8b09e88c05b45adee29d6761ddb6`.
- Original Redis image `redis:8.8.3-trixie`, local ID
  `sha256:418e397fd48d66e450af13baab123397f2d2580b07ef310c3a5dbe96c3d731f1`.
- Old backend image is present, local ID
  `sha256:e90ba1d89d772f7a05ecab99784689b2efd03d1f6e1bf2bcef0e31170abe5122`.
  All three inspected images are linux/amd64. Availability is not a new live
  rollback proof; the actual old-app rollback passed the synthetic CI gate.

## Capacity and compatibility

- Host free: 67,662,368,768 bytes (about63GiB) at measurement. Original physical
  PG volume66,555,904 bytes; Redis2,904,064 bytes. About66.2MiB combined;
  enough measured disk for preserved originals and a second copy, with ample
  headroom. This is not a throughput/outage benchmark or B2 quota check.
- PG18.6, PGDATA `/var/lib/postgresql/18/docker`, directory owner999:0, mode0700.
  Process postgres UID999. Database size8,574,655 bytes, Alembic0007.
- Locale provider libc, en_US.utf8, recorded/actual version2.41 match. Only
  plpgsql1.0 extension.18public indexes,0invalid/unready;5indexes use default
  collation,0use explicit versioned collations. The selected hardened image
  changes libc: candidate collation checks/reindex-before-refresh remain
  required. No catalog version refresh or index write occurred here.
- PG SSL is off. Existing `birja` role is superuser/createdb/createrole; planned
  non-owner runtime roles do not exist. These are current transition inputs,
  not completed least-privilege/TLS acceptance.
- Redis8.8.3, authentication required, appendonly=yes/AOF enabled, last AOF
  write statusok, no rewrite in progress, noeviction. AOF size2,878,847 bytes.
  Redis directory999:999 mode0755. Bounded first SCAN page returned no keys;
  no TTL sample was available and no global key/TTL conclusion is inferred.
  No key names, values or credentials were printed; no synthetic key was added.

## Recovery and configuration

- Preserved approved archive authenticated as
  `d5fe2059b3e984ffcd0dff6b1763dd5a97deddb0be638ca23e49381d35a54401`.
  Installed current points to its exact release; SHA256SUMS bytes and all20
  payload/inventory hashes match. All three root0700 launcher contents match
  the reviewed installer exactly. Restic resolves to the same approved tool.
- `/etc/birja/prod.env` exists, root0600, regular nonsymlink; values not read.
  db-roles.json, datastore-bindings.json and db-tls CA/server files are absent.
  `/var/lib/birja/ops/current` is absent: retained deploy is not installed.
- No current backup freshness, remote existence/headroom, private invariants,
  certificate custody or first-night evidence is inferred. Those checks remain
  gated as documented in LIVE-RECOVERY and ROLLOUT-PROPOSAL.

## Concrete next preparation scope — not yet authorized

Use final main `46d24c8591de2207cf219429aac0768962bed4c3` (published v0.4.0).
Computed the retained installer's exact deterministic129-file MANIFEST locally
from this immutable git tree; expected SHA256:
`70e568a8c0f9953926e40de4ed79ec25272b3cdd777e474b3967a09849edb0b2`.
The JSON is private at production-preflight/expected-retained-MANIFEST.json.
This is an expected artifact identity, not a claim of installation.

Proposed single preparation authorization:

1. Under the supported shared operation lock, fetch/select that exact clean
   production source and install the reviewed retained deploy entrypoint. Check
   its resulting MANIFEST equals the above hash. Preserve the old deploy SHA,
   original volumes and images; do not invoke deploy or start services.
2. Generate private DB TLS CA/server material with the reviewed provisioner;
   prepare root-only app/scheduler/migrator credential files and db-roles.json.
   Do not apply SQL roles or modify existing prod.env yet. Keep new secrets out
   of output and provide file paths for off-server custody before rollout.
3. Create only new empty volumes `birja-prod-phase06-pgdata` and
   `birja-prod-phase06-redisdata`, after rejecting existing names, and prepare
   root0600 routing identity records referencing these and measured originals.
   No copying, ownership conversion, container recreation or volume removal.

This preparation changes host files/empty volumes and production source
selection; it does not restart the running services. It requires explicit
approval. After preparation and off-server custody confirmation, prepare the
final maintenance/outage decision: writer stop, final prod/recovery bindings,
fresh bounded B2 backup/exact restore, clone/collation/security transition,
0007→0008 deploy, smoke and post-rollout same-tool recovery. None is authorized
by read-only preflight or the proposed preparation scope. Do not promise an
outage duration from synthetic timing. Nightly observation remains deferred.
