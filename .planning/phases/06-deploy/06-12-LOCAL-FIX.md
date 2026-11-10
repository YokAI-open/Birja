# Local rollout fix contract

Scope: existing Plan11 task03 / Plan12 readiness closure, following the owner's
“Prepare local rollout fix” decision. Address only readiness CR-01 (durable
selected-clone routing) and WR-01 (TLS/HBA before PG startup). Design review passed before implementation;
subsequent local source and synthetic proof follow this bounded contract.
No new phase/plan, counter change, publication or live operation is authorized.

Current published PR27 head remains
`16623a8638407eeab27c2879f0a9396764a68e89`, with all required release CI green.
Local planning head at assignment is 16113d1. A later source correction creates
a new candidate requiring its own review, publication choice and exact-head CI.

## Minimal interface

Introduce one protected fixed host JSON file `/etc/birja/datastore-bindings.json`.
It is operator-prepared state, not sourced shell and not a caller option. Missing
bindings fail closed for retained datastore creation; there is no fallback to
implicit project volumes. Exact schema version 1, project `birja-prod`, and
exactly two logical keys, `pgdata` and `redisdata`. Each records:

- original volume name plus measured Docker CreatedAt, driver and scope;
- candidate volume name plus measured Docker CreatedAt, driver and scope.

All four names must be distinct; local driver, local scope, no driver options
or bind-backed aliases. Reject unknown keys, malformed names/metadata and
ambiguous/surprising inspect results. These are proposed fields, not measured
production values. No production names, timestamps or fingerprints are invented.
CreatedAt guards accidental delete/recreate; Docker/root authority is not an
adversarial isolation boundary.

Require a regular root-owned 0600 JSON file beneath trusted root-owned parents,
without symlink traversal. Load/validate it only under the existing operation
lock. The helper accepts neither alternate paths nor volume/project/service
arguments in its production interface. All modifying operations must validate
the inherited held kernel lock; no lock bypass or string-only FD attestation.

New small retained `deploy/datastore-bindings.py` will:

1. Validate this file, inspect every named volume without creating anything,
   and reject missing/duplicated/replaced/unexpected metadata. Before first
   candidate start, prove real existing data through bounded read-only mounts:
   PG fixed `18/docker/PG_VERSION` = 18, nonempty regular global/pg_control,
   expected converted ownership 70; Redis existing multipart AOF manifest/data
   at the reviewed layout with owner 65532. Reject empty data, symlinks and
   unsupported layout. Do not read/print application rows or credentials.
2. Generate a minimal fixed root-private Compose JSON overlay under
   `/var/lib/birja/ops/`, mapping only the two logical volumes to
   `{external: true, name: <validated-existing-candidate>}`. No service,
   network, credential, command, image, arbitrary include or caller override.
   Atomic replacement, no symlink destination, exact protected contents.
   `external: true` plus explicit existence checks prevents implicit creation.
3. Assert that a running selected datastore is the sole container for the
   exact project/service, with expected immutable image/platform, expected
   configured user, no published data ports, approved internal network and
   exactly the expected named-volume mount at PG `/var/lib/postgresql` or
   Redis `/data`. Reject a bind/tmpfs/wrong volume, additional mount at that
   target, replica/foreign project/service, missing container or ambiguity.
   Check actual Docker metadata, not container names alone or user env.

Proposed helper modes are exactly `--check-volumes`, `--write-overlay` and
`--check-running`; none accepts target/path arguments. The retained entrypoint
adds exactly `--start-selected-datastores`, delegated to deploy.sh to check
TLS/HBA, start only PG/Redis via fixed validated orchestration and verify their
running identities. It does not deploy apps or run migrations/role SQL. No
generic Docker wrapper, automatic copying/chown/reindex, bootstrap
fallback, volume creation/removal, recovery, network provider or config editor.

## Consumers and immutable boundary

All retained create/recreate calls, including ordinary deploy and old-app
rollback, must include the same validated fixed overlay, appended to the
immutable base/security overlays. The entrypoint still reconstructs its clean
environment; ambient COMPOSE_FILE/COMPOSE_PROJECT_NAME/DOCKER_HOST, caller
volume flags and arbitrary overlay paths remain ineffective/rejected. Validate
actual mounted identities after `up`/recreate and before migrator/runtime start.
Validate them again before recovery-gate revision SQL and role SQL exec.

Add the helper to the retained deployment installer inventory and required
manifest membership. Its code must come from verified immutable ops/current,
including while application checkout is actual v0.3.1. Do not import it from
the mutable application checkout or permit modified runtime overlay content
to act as an executable/unbounded Compose authority.

Role and backup helpers are exec-only consumers, as readiness review explains;
they need no independent volume selector. Add the running-identity assertion
to retained role inspection/application before its existing exec. For the
cutover run sheet, perform the same assertion immediately before invoking the
existing installed backup under the shared lock. Prove the unchanged installed
backup's fixed project/service exec reaches the sole verified candidate after
recreation. Backup itself never creates/selects a volume.

**Recovery boundary:** do not modify backup-snapshot.py, verify-restore.py,
backup-quota.py, CORE, units, installed recovery launchers or archive d5fe2059….
Do not add a dependency from independent recovery onto the deployment helper.
The new validation is at the reviewed cutover/deployment caller boundary;
it is not a new claim that the unchanged nightly producer individually enforces
the new binding policy against a Docker-authority adversary. If review requires
an intrinsic per-backup mount guard rather than this fixed exec/cutover proof,
stop and demonstrate that requirement before proposing any CORE/archive change.

## Secure first startup and maintenance order

Fix WR-01 through ordering, not a plaintext bootstrap definition. The following
ordering supersedes the original design's fresh-proof-before-config sequence:

1. Validate target/custody/maintenance authority. Under the shared held lock,
   stop application/external writers, keeping old datastores running. Select
   the exact retained ops source; prepare fixed bindings for already existing
   distinct candidate volumes and all final protected role/prod/recovery
   material. Candidates may still be empty: no start/data probe occurs yet.
2. Invoke that retained source's
   existing `provision-db-tls.sh --production --create --approved-operation
   production-db-tls --approved-custody owner-off-server-password-manager`
   before any candidate PG start (existing state instead requires check/renew
   according to measured evidence). It already supports the held lock and
   does not need a running cluster or perform a service restart.
3. Verify CA/server key/certificate modes, UID0:GID70 server-key access,
   matching/valid trusted pair and hostname, independent CA custody, and exact
   retained HBA bytes/mounts. Use the existing final secure PG definition from
   first start. Missing material, bad modes/HBA or custody stops before start.
4. Verify the sole old PG service/original mount identity read-only immediately
   before unchanged installed backup exec. Take a fresh exact backup/isolated
   restore AFTER all bound material changes. Keep c.release equal to the old
   actual live_sha(deploys.log), not the new checkout. Include the protected
   binding and canonical root0400 retained MANIFEST in recovery_files, plus
   approved private custody/role/prod files compatible with private_file.
   Live server.key0640 and CA certificate0644 do not qualify directly and are
   not intrinsically hash-bound by that list; the existing TLS check validates
   their actual pair/CA/hostname before startup. Production does
   not accept the synthetic-only source_compose override; fixed source exec
   and immutable retained source review supply that orchestration boundary.
   Then stop both datastores and copy only into separately approved candidates.
   Preserve originals/old images, hold the lock continuously, and change no
   bound config/material between this proof and startup. No automatic copy,
   chown, reindex or engine migration belongs in this local helper.
5. First-start admission reads only the protected successful completed-restore
   profile for the exact latest snapshot and actual old source. The UNCHANGED
   recovery-gate then independently authenticates source/revision/config/tools,
   remote snapshot/profile, latest attempts and conservative data age. There
   is no caller revision/fallback or stale-proof exception. Normal deploy and
   rollback still read the actual running revision and selected identities.
   The narrow candidate-start path consumes the validated overlay, validates
   data presence, starts only PG/Redis with final TLS/HBA/noeviction/AOF settings,
   and proves actual mounts/identity. It does **not** call role apply, run
   migrations or start backend/scheduler. After start, require actual candidate
   revision equality with the just-admitted profile before any role/migration
   operation or writers; a mismatch stops with candidate services only.
6. Inspect candidate collations/indexes, perform separately approved affected
   REINDEX before version refresh, and verify private equality/validity. Keep
   configure-db's collation guard intact; then inspect/apply role SQL using
   its existing approved interface. Unknown/unsafe collation state still blocks.
7. Refresh any invalidated recovery/config binding through the same independent
   installed tools. Normal retained deploy must still pass its fresh strict
   gate, role/TLS checks and separate one-shot 0007→0008 migrator before writers
   resume. Old-app rollback retains selected candidates and TLS/least privilege;
   never downgrade 0008 or put converted data under old libc.

These CLI modes are implemented locally; production use requires separate approval.
Fixed-path relocation exists only in synthetic tests; production has no
arbitrary project/Compose/source/target arguments.

## Bounded files

- New deploy/datastore-bindings.py; deploy/deploy-entrypoint.sh (retained
  inventory/verification); deploy/deploy.sh (all fixed orchestration and
  initial candidate-only start); deploy/configure-db.sh (pre-exec identity).
- Prefer generated volume-only overlay, leaving docker-compose.prod.yml and
  db-security.compose.yml unchanged; change them only if an evidenced blocker
  requires it and report that before expansion.
- deploy/RUNBOOK.md and 06-12-ROLLOUT-PROPOSAL.md: selected fixed binding,
  pre-start TLS sequence and still-unmeasured production preflight inputs.
- Focused deploy/tests contract file, existing test-deploy-prerequisites.py,
  test-rollback-db-security.sh and ops-fixtures.py as needed for production-
  interface and actual cutover proof. Update CI producer list only if the new
  focused test is separate; preserve every current gate.
- No app/frontend/dependency/image/CORE changes, new phase plan or installed
  host files. No production values may be copied into tests.

## RED, GREEN and acceptance proof

First RED commit: real argument construction rejects absent/unsafe binding and
shows current recreation selecting implicit originals; prove startup presently
does not ensure TLS/HBA prerequisites. Use private fake-host path relocation
and existing Landlock pattern, retaining the actual entrypoint/environment/
manifest/kernel-lock logic. No mocked security success or skipped checks.

Negative matrix: missing/unsafe/symlink JSON and parents; extra/missing keys;
original=candidate or cross-alias; missing/recreated/driver-option volume;
empty/unsupported/wrong-owner candidate data; external-volume deletion between
validation and create; forged overlay; manifest/helper tampering; caller env
override; missing/unheld/wrong-inode lock; zero/multiple/wrong project/service
container; wrong actual mount/image/user/port/network; missing or invalid TLS/
HBA material. Assert no unrelated Docker/SQL/start/original-write on rejection.

GREEN commit: smallest helper plus fixed consumer wiring and startup ordering.
Retain redaction, exact-source installer rules, env scrubbing and all existing
guards. Focused tests must execute the JSON/argv/guard behavior, not mirror
implementation strings alone; no unrelated refactor or compatibility fallback.

One serial real isolated proof extends the existing fixed synthetic fixture:
create populated original/candidate PG and Redis data; preserve original
fingerprints privately; convert only candidates; create real TLS material
before secure candidate PG startup. Through the real retained interface,
verify candidate mounts, correct collation maintenance/roles, 0008 migration,
TLS-positive and bad CA/hostname/plaintext negatives. Force service recreate,
deploy then actual v0.3.1 app rollback and prove every resulting datastore
still mounts the selected candidates; observe persistence of stored test data
and Redis AOF/TTL/auth state. Run unchanged installed recovery backup/exact
isolated restore against the sole selected source before and after, using the
same provided independent archive. Retained source controls must survive old
application checkout and Landlock denies reliance on the feature checkout.

Verify originals remain unchanged and usable with original engines before any
candidate writes; verify the reviewed abort route does not reuse candidate
data under old libc. After accepted new writes, original-volume fallback is
not lossless and requires a separate recovery decision. Clean only fixture-
owned resources in finally; no shared parallel datastore tests or prod access.

Run affected focused lint/format/contracts and required backup/safety tests;
then this one bounded real proof. Do not repeat unrelated app suites/scans or
rebuild/install recovery without changed scope. Independently review the final
source and evidence before any updated release push request. Real production
names, capacity, freshness, custody, final main SHA and outage window remain
future authorized preflight inputs, not facts supplied by this local work.

## Review checkpoint

Original design checkpoint passed before implementation. Source reviews and
current operational evidence are recorded separately in LOCAL-FINAL-REVIEW
and LOCAL-FIX-EVIDENCE. The fixed JSON/runtime overlay trust boundary,
candidate-start interface, backup exec-only boundary and fixture ownership
remain within that reviewed scope. Any demand
for CORE changes or general routing/bootstrap infrastructure stops for a newly
bounded decision rather than silently expanding this contract.
