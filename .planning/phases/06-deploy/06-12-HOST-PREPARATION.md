# Approved host preparation — 2026-11-10

Status: COMPLETE for the approved preparation scope; rollout pending.

Owner selected “Approve host preparation” for the exact source, manifest,
private material and two empty candidate volumes documented in06-12-PREFLIGHT.
Executed the guarded preparation under the installed shared operation lock,
including kernel-validated inherited lock handling by the reviewed installers.
No errors; no scope expansion or replacement artifact was required.

## Actual prepared state

- `/srv/birja` selected released main
  `46d24c8591de2207cf219429aac0768962bed4c3` (v0.4.0). The live application
  containers continue running their previous v0.3.1 images; source selection
  does not claim application deployment.
- Installed `/usr/local/sbin/birja-deploy` and supported legacy launcher with
  immutable retained tooling. Actual MANIFEST SHA256 equals approved
  `70e568a8c0f9953926e40de4ed79ec25272b3cdd777e474b3967a09849edb0b2`;
  all129retained file hashes verified. Installation uses the reviewed sparse
  checkout/launcher mechanism; do not overwrite it with an old deploy script.
- Private CA/server certificate created through reviewed provisioner; CA trust,
  postgres hostname, key/certificate matching and expiry beyond30days pass.
  No PostgreSQL reload/restart was performed; live TLS remains unchanged.
- New random256-bit hex credentials staged separately for app/scheduler/migrator;
  format/root0600 checks pass. db-roles.json is root0600 with fixed project,
  database, bootstrap role and staged file references. No SQL roles applied.
- Created only `birja-prod-phase06-pgdata` and
  `birja-prod-phase06-redisdata`; both empty and unused. Original volumes are
  preserved. Root0600 datastore-bindings.json records original/candidate names,
  actual creation timestamps and local driver/scope. No copy, conversion,
  original chown, reindex, migration, routing cutover or container recreation.
- All four original live IDs/images/mounts match before/after and remain
  healthy. Existing prod.env inode/size/mtime/ctime match before/after; no
  credential values were displayed. Installed independent recovery remains
  exactd5fe2059 archive. No backup/restore, provider or timer access occurred.

## Post-verification

Separate postcheck revalidated exact retained MANIFEST, generated credential
format/permissions, role config, actual routing identities and empty/unconsumed
candidate directories. Repeated reviewed TLS --check succeeded.
Private sanitized result is retained at
`.local/phase-06-handoff/production-preflight/host-preparation-result.json`;
the guarded execution script is also private/ignored. No new application code
or dependency/image change; the released source already has actual green CI.

## Required off-server custody before rollout

Copy these existing files privately into the off-server password manager as
secure attachments/entries; preserve exact bytes and filenames. Do not invent
replacement values and do not send contents in chat:

- `/etc/birja/app`, `/etc/birja/scheduler`, `/etc/birja/migrator`:
  newly generated database credentials (staged, not applied).
- Entire `/etc/birja/custody/` and `/etc/birja/db-tls/` directories:
  CA signing key, CA certificate and server certificate/key.
- `/etc/birja/db-roles.json` and `/etc/birja/datastore-bindings.json`:
  recovery configuration and volume identity mapping.

Existing B2/restic custody remains confirmed from Plan09; this request covers
only newly generated role/TLS/routing material. Off-server custody is not yet
confirmed for it. Production rollout remains unapproved. After confirmation,
prepare the exact maintenance/recovery/collation/cutover/deploy scope and ask
for its separate checkpoint. No production restart follows from “saved”.

Phase12/15;09/12/13 and DEPL-01/02 remain pending. No12SUMMARY or phase completion
is claimed. First scheduled-backup observation remains explicitly deferred.

## Owner-requested single off-server archive —2026-11-10

Owner requested one archive including production env. Created private ignored
`offserver-export/birja-offserver-recovery-20261110T100419Z.tar.gz.gpg`
(130,286,280bytes), encrypted AES256 through GnuPG using the existing separately
custodied restic password. Includes all18files under/etc/birja, current HTTPS
certificate/key, authenticated independent recovery archive, retained MANIFEST,
runbook and recovery instructions/checksums.25members total.
Full decrypt/MDC and every archived member hash verified; root0600 archive in
root0700directory. No secret values printed. Archive SHA256:
`3888fb71b23e7985cb5273ce1b9b033e98853b1250a5f9b022778285db90fe79`.
The archive is configuration/tool custody, not a database backup; actual data
remains in encrypted B2. No production configuration/service change or provider
access. Owner must download/save it off-server and retain the existing restic
password independently; off-server custody confirmation is still pending.

## Owner-requested 7z replacement —2026-11-10

Owner requested 7z format. Created private root0600 ignored
`offserver-export/birja-offserver-recovery-20261110T100419Z.7z`
(127,260,957bytes), AES256 with encrypted headers using the same existing
restic password. Contains all25members from the verified GPG export; only
README instructions and its internal checksum changed for7-Zip. Full private
extraction and all25file hashes passed, including original source checksums
before conversion; opening without password rejected. Plaintext temporary
staging removed. No production/service/config/provider changes.
SHA256:`4b67c3fec44a3fd8ce85c30cf22a4b022f4a214e33ccb8d308a9ed56886f9584`.
Isolated temporary py7zr1.1.4 used; no project/global package changes.
Use this7z for owner download; earlier encrypted GPG copy remains private.
Off-server custody confirmation remains pending.

## Off-server custody confirmed —2026-11-10

After downloading/opening instructions for the requested encrypted7z archive,
owner replied “ok, done, i saved it”. Record custody of the new recovery material
as confirmed; the existing restic password/B2 custody was already confirmed.
No secret values were shared. Archive identity remains
4b67c3fec44a3fd8ce85c30cf22a4b022f4a214e33ccb8d308a9ed56886f9584.
Do not ask the owner to repeat this custody step. Confirmation authorizes no
service restart, role/data transition, backup/restore or deployment.

Next: finalize a concrete maintenance run sheet bound to main46d24c8 and retained
MANIFEST70e568a8, approved candidate volumes and installed recoveryd5fe2059.
Obtain a maintenance window/writer inventory and explicit rollout approval.
Fresh bounded B2 recovery proof, candidate-only copy/collation maintenance,
role/TLS/migration/deploy, smoke and post-rollout recovery remain pending.
Phase12/15;09/12/13 and DEPL-01/02 remain incomplete; nightly observation deferred.
