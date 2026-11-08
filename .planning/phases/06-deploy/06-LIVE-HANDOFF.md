---
phase: 06-deploy
prepared: 2026-11-08
status: ready-for-scoped-live-preparation
execution_authorized: false
---

# Phase06 live handoff

The owner authorized safer alternative images while retaining the strict raw
HIGH/CRITICAL gate and local-only scope. Plan08 is now complete after independent
source review and full final acceptance on2026-11-08. Phase6 is10/15 complete;
Plans09..13 and DEPL-01/02 remain pending. **This packet authorizes no live
operation, private configuration access, transfer, publication or deployment.**

## Tested artifact preserved locally

The exact tested recovery archive is retained outside temporary storage at:

`/home/YokaiExchange/.local/phase-06-handoff/candidate-cgr/recovery.tar`

This directory is mode0700, its files0600, and it is explicitly git-ignored. The archive contains tools/provenance, not a production database backup. No secret or production recovery material was copied into it. It is not an off-server recovery copy; later independent custody remains required. Original temporary evidence paths remain historical.

| Item | Exact binding |
|---|---|
|Archive size|152,156,160bytes|
|Archive SHA256|`83f4f5151807b67072d99e13a89c6b5f90617d54b7a8261c55931705d6f5044d`|
|Separate checksum|`recovery.tar.sha256` in the same directory; independent approved hash must also be retained off-server|
|Reviewed source|`e40f688` replacement source; independent `06-08-IMAGE-REPLACEMENT-REVIEW.md` has zero active findings; final evidence `10b5241`|
|Trusted verifier|Separately copied `verify-restore.py`, SHA256 `c3fed604fbf14ad9c3df0e43b00874d7761223391eb55c7cb0c45a8cde98b4de`; byte-identical to the reviewed source and bundled verifier|
|Inventory|Separate `INVENTORY.json` SHA256 `55069a4ecca727f85f8f55f33f3e4dc9b9e7887a1ff60841b0aa14a7b45d15ea`;19 payloads plus inventory/checksums, deploy-recovery-v2 profile, quota helper, both units, PG archive and signed-restic provenance|
|PostgreSQL index|`sha256:f131db66371391e404c80cef7dd40f31b1b54eb264a6cb032925d9a3859f93f4`|
|Platform manifest|`sha256:4401cf2919e749cd77b634a72e4a677c1a1afc12baddb21faf28df326162472e`|
|Config digest|`sha256:91c89cf7f1f18cc4d96fcb5b9e2438108569c1dfcd5aa7286f9cad7d75742ed4`|

The preserved copy's hash, separate checksum and trusted verifier were checked, and the separately copied verifier successfully ran generic `bundle verify` with `--require-profile deploy-recovery-v2` (exit0, `bundle_verified=true`). No install/load/backup occurred. Changing the archive/source/image later invalidates this exact approval candidate and requires affected review/revalidation; never silently rebuild it under the same hash.

## Completed local evidence

- Fresh five-target unchanged scanner returned0 in29.325s; each actual final
  runtime/test-builder/Node/PostgreSQL/Redis raw report has0HIGH/0CRITICAL,
  including unfixed findings. DB updated2026-11-08T06:39:21Z. No exception,
  ignores/VEX, vendor-file/metadata deletion or security-policy change.
- Backend616 passed,99.80%overall/100%critical; actual frontend264 with audits,
  lint/types/format/build passed. Default host pip-audit is retained and passed;
  npm has13moderate/2low and0HIGH/0CRITICAL.
- Actual unfiltered browser10passed/1expectedproduction-CSPskip,57.406s,
  retries0; fake prices, console email and isolated example.com accounts only.
  The retained list output and passed last-run record verify execution; a
  private report filename collision lost detailed JSON, recorded honestly.
- Same exact supplied artifact: recovery65.167s, roles30.099s with65 denials,
  TLS49.578s and actualv0.3.1rollback102.263s, all exit0. Retained source-independent
  launchers, authenticated imported image/fixed alias/pull-never, private
  invariants and transport negatives passed.
- Populated PostgreSQL/Redis image transition37.064s, clone-only UID conversion,
  actual collation drift/reindex-before-refresh, logical recovery and untouched
  original abort passed. Independent22-path replacement source review is clean.
  Actual old application build uses immutable archived dependency files.
- All six synthetic project labels have zero containers/networks/volumes.
  T3C's166-file evidence manifest SHA256 is
  `6a95813377aa41c9d6daa12beb7404df2a8b2b22c60c09c4b4dc6aacb81e3dad`.
  Exact current evidence is `06-08-T3C-EVIDENCE.md`/IMAGE-GATES/LOCAL-GATES.

The historical Debian/cb766040... packet at the parent handoff directory is
untouched. It is not the current candidate. Use only the candidate-cgr packet
and independently recorded new hash above for later scoped approval.

## Required sequence after local acceptance

| Boundary | Concrete prerequisite and scope | Required evidence before proceeding |
|---|---|---|
|08 local acceptance — complete|Reviewed sourcee40f688 and exact final packet above; fresh scans, application/browser/transition and serial supplied-artifact checks pass.|08SUMMARY exists;10/15 plans complete. Future source/image changes require affected review/revalidation, not silent repackaging.|
|09 preparation/approval|Owner confirmed the workspace is on the same VDS. Direct local route on hostname `DE189274`, Linuxamd64/root, replaces SSH/SCP. Metadata-only preflight confirms `/srv/birja` at exact v0.3.1 commit `0107706617b8bbf9c1a069f3e3ccc9c53b9ab2f7`, projectbirja-prod running. Backup JSON/controls, retained recovery, restic path and timer are absent. See concrete scope below.|Owner approval of the displayed host/tool/recovery installation, private config processing, B2 upload/exact retrieval/isolated restore and timer is still pending. No feature checkout or app deployment on production.|
|09 real recovery/timer|Keep source checkout at its actually confirmed prechange release. Install immutable recovery at `/var/lib/birja/recovery/releases/<archive-sha>` and stable `/usr/local/sbin/birja-backup`, `birja-backup-status`, `birja-restore-check`. Source projectbirja-prod, checkout/srv/birja; restore only fixedbirja-restore-check, internal/noports/tmpfs. Source release/schema/runtime facts must be revalidated, not assumed from historicalv0.3.1.|Actual off-server same-snapshot retrieval/full private invariant verification; then an actual calendar-triggered successful snapshot. A manual service run cannot prove nightly operation. No app-role/TLS rollout or deployment in this step.|
|10 feature publication|Separate owner push/PR selection, then approved current-head all-job CI and reviewed recovery evidence.|Current exact-head backend/frontend/image/e2e/ops/ci-pass green; separate feature merge/version-preparation choice. Local browser results do not replace remote CI.|
|11 release preparation|Owner-selected version and approved integration; create release branch only from updated integrated develop, preserving git-flow.|Version-only candidate, scoped release push/PR approval, exact release-head green CI. No invented release version or premature release branch.|
|12 publication/rollout|Individually approved main merge/tag/backmerge/live role+TLS+restart+deploy scope and exact ref/artifact; fresh prechange backup+restore evidence.|Observed live least-privilege/verifiedTLS, origin/public smoke, one scheduler, preserved data/schema, and successful post-rollout recovery through unchanged installed entrypoints. No automatic data restore/downgrade.|
|13 friends/final verification|Consenting Gmail and Outlook friends enter codes privately and perform signup/trade/portfolio/history/session checks at the approved live release.|Both recipient classes pass, genuine nightly+restore/currentCI/liveDB evidence current, then final goal verification. No assistant messages/OTP extraction or local-console substitute.|

## Private setup prerequisites for the later approved operation

Destination stays `s3:https://s3.eu-central-003.backblazeb2.com/Birja-backup/prod`, exact bucket case. BudgetUS$0 paid use. Owner verifies private bucket/ObjectLock/lifecycle and console$0caps; preflight measures actual account/version/unfinished storage/headroom with bounded local transfer/request work. Caps are not a universal zero-bill guarantee. Unknown inventory or inadequate replacement headroom stops before upload/deletion.

Keep exactly one verified completed snapshot: verify replacement before removing prior IDs; preverification failure preserves the old copy. No first-delete-to-free-space action. Recovery26h/four-hour target; nightly03:00UTC+up to15minjitter; owner daily checks. Recheck current free allowances/setup at execution, not by inventing provider remaining counters.

Provision secrets privately into validated root-only JSON `/etc/birja/backup.env` and referenced credential/password/CA files; never source that JSON as shell/systemdEnvironmentFile. The read-only account inventory key and Birja-scoped writer have separate roles. Protect controls/state, independent off-server password-manager custody and minimum encrypted recovery_files as specified in RUNBOOK. Never paste secrets, rows, balances, tokens or private manifests into chat/evidence.

## Production image-transition prerequisite for later Plan12

The safer PostgreSQL18.6 image uses UID/GID70 and glibc2.44, compared with old
Debian UID999/glibc2.41. Explicit PGDATA stays `/var/lib/postgresql/18/docker`
under `/var/lib/postgresql`. Normal startup cannot auto-chown old volumes;
role/deploy preflight rejects collation drift, unknown versions or invalid
indexes before progression. Matching PostgreSQL major alone is insufficient.

Plan09 installs recovery tools only, leaving actual source app/datastore,
credentials, services and schema unchanged. Its fixed isolated restore uses the
verified candidate image. Later Plan12 production engine/role/TLS rollout needs
an explicitly approved stopped-writer outage and selected clone (or fresh
logical restore), untouched original preserved, clone owner70 and affected
index REINDEX **before** collation version refresh. Verify data/index/session/
money/identity invariants before switching. An engine-change abort uses the
untouched old volume and old image; never old libc on rewritten candidate data.
Application rollback retains the reviewed candidate engine/security setup.

Persisted Redis AOF similarly needs separately approved selected-clone owner65532
conversion, auth/TTL/noeviction/restart checks and untouched original preservation.
No automatic live chown or deletion of OTP/rate-limit state is permitted. The
complete tested procedure is in RUNBOOK's image/collation transition section;
local rehearsals do not authorize that production maintenance.

## Stop/undo and current next action

Target/host mismatch, invalid provenance, stale source/config/recovery evidence,
unknown inventory, insufficient budget/headroom or failed verification stops the
operation. Never delete prod volumes, auto-restore real data, reset failed status
or broaden target/path guards. Timer disable leaves backup data intact; an
already-running job needs its own diagnosis. App rollback and database restoration
are distinct operations.

**Current next action: approve or revise the concrete Plan09 operation below.**
The access route and host metadata are now known; B2 controls, credentials,
private config, measured resource bounds and actual recovery evidence remain
unverified. No passing local suite needs repetition without changed evidence.

## Concrete Plan09 scope — owner decision pending

Owner confirmed “same vds”. The route is direct local execution, not SSH/SCP.
Read-only administrative preflight on2026-11-08 observed host `DE189274`,
Linuxx86_64/root, Docker29.2.1, Compose5.0.0, Python3.12.3 and systemd255.
`/srv/birja` HEAD is `0107706617b8bbf9c1a069f3e3ccc9c53b9ab2f7`, exactly
v0.3.1. Selected project metadata shows backend/scheduler/PostgreSQL/Redis
running, with source PostgreSQL18.6-trixie and Redis8.8.3-trixie. No container
environment, production config contents, logs or database records were read.
These facts identify the target; they do not grant the live operation below.

Proposed operation, bound to archive SHA256
`83f4f5151807b67072d99e13a89c6b5f90617d54b7a8261c55931705d6f5044d`:

1. Reverify the preserved candidate-cgr packet and trusted verifier, install
   its exact immutable release under `/var/lib/birja/recovery/releases/<SHA>`,
   atomically set recovery/current and three `/usr/local/sbin/birja-*` recovery
   launchers, and load only its authenticated PostgreSQL recovery image.
   Expose its signed restic0.19.1 binary at required `/usr/local/bin/restic`
   through a checked link to the immutable tools/restic; no package upgrades.
2. Create root-only JSON `/etc/birja/backup.env`, controls, explicit credential/
   password references and `/var/lib/birja/backup`. Read required production
   configuration opaquely for setup/encrypted recovery only, never display it.
   Owner independently holds recovery password/access/DB/CA material off-server.
   Use Birja-scoped S3 writer and account-wide read-only inventory key with the
   existing bounded preflight. Owner supplies secrets privately, not in chat.
3. Verify actual B2 private/ObjectLock/lifecycle and owner-attested $0 console
   caps/daily checks/exclusive writes. Measure required source aggregate sizes
   privately; choose bounded work fitting free allowance/headroom and shared
   deadline. Unknown controls or inadequate headroom stop before remote work.
   Repository initialization, if needed, is limited to exact approved B2 prod
   prefix and follows these controls. No paid spend or provider account creation.
4. Take a consistent encrypted production backup from fixed birja-prod only,
   privately compute same-snapshot invariants, upload to the exact approved
   B2 destination, retrieve that exact snapshot using independently held
   recovery material, and restore only fixed `birja-restore-check` with internal
   networking, tmpfs, no ports/email/jobs. Verify all invariants privately and
   remove only that clone/private staging in finally. Publish only sanitized
   status, UTC, snapshot ID and timing, never rows or private data digests.
5. Only after full restore succeeds, install the two verified unit files in
   `/etc/systemd/system`, validate them, reload systemd and enable the timer
   at03:00UTC+up to15minutes jitter. Observe an actual calendar activation and
   remote snapshot before completing09; a manual run is not nightly evidence.
   Latest-only replacement keeps the previous point until new verification;
   deletion/prune stays within explicitly approved Birja rotation scope.

Production app checkout, source database engine/volumes/roles/TLS/schema and
services remain unchanged. No application restart, physical clone transition,
production data restoration, push, PR, merge, release or deployment is included.
Stop on host/source/config/provenance mismatch, credential/controls failure or
insufficient budget. Disable an installed timer to stop future scheduling;
retain completed backup data and diagnose any running job separately. No
production volumes are removed and no database downgrade is an undo mechanism.

All changes above remain **proposed**, not authorized by the host-route answer.
Missing B2 setup/credential material will be resolved privately before any
remote operation. The existing exact artifact/review/replay evidence supplies
the reversible local preparation; no replacement bundle is required.
