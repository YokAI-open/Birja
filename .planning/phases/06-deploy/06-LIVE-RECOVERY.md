---
phase: 06-deploy
plan: "09"
status: replacement-tested-awaiting-install-decision
updated: 2026-11-08
installation_complete: true
remote_restore_complete: false
calendar_trigger_verified: false
---

# Plan09 recovery installation and remaining setup

The owner explicitly approved Plan09 backup setup and verification on DE189274,
bound to archive SHA256
`83f4f5151807b67072d99e13a89c6b5f90617d54b7a8261c55931705d6f5044d`.
This authorizes the prepared recovery tools/configuration, bounded encrypted B2
backup and isolated restore, then timer activation after successful restore.
App restart, deployment, database-role/TLS/schema/engine changes, publication
and private record inspection remain outside scope. Approval persists; do not
request it again merely because credential/setup work crosses turns.

## Observed installation

The preserved packet passed the trusted verifier's required
`deploy-recovery-v2` profile before installation. `bundle install` then exited0,
created the immutable release and three launchers, and loaded only the
authenticated PostgreSQL recovery image. Engine/platform manifest
`4401cf2919e749cd77b634a72e4a677c1a1afc12baddb21faf28df326162472e`,
config `91c89cf7f1f18cc4d96fcb5b9e2438108569c1dfcd5aa7286f9cad7d75742ed4`,
linux/amd64; fixed verified alias, no registry fallback.

- Immutable root: `/var/lib/birja/recovery/releases/<archive-SHA>`;
  `/var/lib/birja/recovery/current` resolves to that exact root.
- All20 installed inventory/payload hashes match checksums from the exact
  approved archive. Inventory SHA256 remains
  `55069a4ecca727f85f8f55f33f3e4dc9b9e7887a1ff60841b0aa14a7b45d15ea`.
- `/usr/local/sbin/birja-backup`, `birja-backup-status`, `birja-restore-check`
  are root-owned0700 and route to the retained recovery root.
- `/usr/local/bin/restic` links to the immutable `tools/restic`; binary SHA256
  `20d4142678d0d95ec11a4759def1b73fd9190abc9ca19e4b62d067c0b387e639`
  and actual `restic 0.19.1` version pass.
- `/var/lib/birja/backup` is root-owned0700. Four empty credential files and
  one generated backup password were created as root-owned0600 under the
  existing root-owned0700 `/etc/birja`. No existing secret was overwritten;
  no generated password or credential value was displayed.
- Backup JSON/controls have not been activated. No B2 request, repository
  initialization, real backup, restore or unit installation/enable occurred.
  No production service restart or application/database change occurred.

One verification-script attempt assumed the public inventory's files field
was a mapping; it is a list. It stopped before that attempt made any mutation.
The corrected script authenticated installed checksum bytes against the exact
archive and rehashed all20 files successfully. No source or artifact changed.

## Continue with the existing bucket

**Do not create another bucket.** Keep exact `Birja-backup`, endpoint
`s3.eu-central-003.backblazeb2.com`, repository prefix `prod`.

In the Backblaze web console:

1. Open the existing bucket. Confirm it is private and Object Lock is off.
   Set its lifecycle to keep only the last file version; do not add a rule
   that deletes current files after a number of days. This controls obsolete
   object versions, while Birja keeps one verified completed backup.
2. In Caps & Alerts, check the existing limits first. The owner reports no
   credit card/payment method and cannot edit this page. Do not require adding
   a card or assert that limits were edited. Ask for only the displayed cap
   amounts/free-only status and verify whether existing controls satisfy the
   agreed $0 policy. Existing verified zero caps do not need editing. Unknown
   defaults/no payment method alone do not establish every billing control;
   leave remote work/timer inactive until resolved. If an available control
   needs changing, use $0 with uncapped options cleared; changes can take10min.
   Daily owner checks and exclusive writes still apply. Caps are not a
   universal zero-bill guarantee.
3. In Application Keys, reuse an existing matching key if securely held, or
   create `birja-backup-writer`: Read and Write, bucket `Birja-backup`, file
   prefix `prod/`. If offered, allow listing bucket names for S3 compatibility.
   Never put a master key or account-wide write key on this VDS.
4. Create/reuse `birja-backup-inventory`: Read Only, all buckets, no prefix.
   Its required capabilities include `listBuckets`, `listFiles`,
   `readBucketRetentions`, with no non-read/list capability. The automatic
   preflight will validate actual authorization before accepting the key.
   If the UI key fails this requirement, stop and revise only its scoped
   capabilities; do not substitute a master/account-wide write key.

Save the key ID and application key privately into the prepared files below,
one plain value per file, with no quotes or variable assignments. Use your
remote editor's Open File command with the absolute path. Do not paste values
in chat, terminal command arguments or repository `.env` files.

| Value | Root-only destination |
|---|---|
| Writer keyID | `/etc/birja/b2-s3-key-id` |
| Writer applicationKey | `/etc/birja/b2-s3-key` |
| Inventory keyID | `/etc/birja/b2-inventory-key-id` |
| Inventory applicationKey | `/etc/birja/b2-inventory-key` |

Keep both access credentials and the generated `/etc/birja/restic-password`
in your off-server password manager. Open/copy the password privately; never
send it here. Keep required production config/DB/CA recovery material under
the previously approved independent custody policy too.

When finished, report only that the settings, four files and independent
password custody are ready, plus the observed caps/check time and whether other
account writers are stopped during backup. No credentials or screenshots
containing secrets are needed.

Primary setup references checked2026-11-08:

- [Application keys](https://www.backblaze.com/docs/cloud-storage-application-keys)
- [Object Lock key permissions](https://www.backblaze.com/blog/digging-deeper-into-object-lock/)
- [Lifecycle rules](https://www.backblaze.com/docs/en/cloud-storage-lifecycle-rules)
- [Caps and alerts setup](https://www.backblaze.com/docs/en/cloud-storage-create-and-manage-caps-and-alerts)

## Remaining execution

After private setup, validate credentials opaquely and measure actual inventory,
source sizing and conservative operation budgets. Do not fabricate controls,
quota or completed recovery evidence. Create protected JSON using the installed
validated contract. Initialize only the exact approved repository if needed;
then perform encrypted same-snapshot backup, exact off-server retrieval and
fixed internal/tmpfs `birja-restore-check` invariant verification and cleanup.

Only afterward install/verify/enable the approved03:00UTC+15min timer. Record
an actual calendar activation, successful service result and remote snapshot;
manual service execution does not satisfy nightly acceptance. Return a pending
checkpoint between nights instead of blocking a tool for hours.

Plan09 remains incomplete. No09 SUMMARY or DEPL-02 acceptance yet; Phase6 stays
10/15. Actual snapshot ID/UTC/restore result and calendar evidence remain absent.

## Owner setup clarification —2026-11-08

Owner reports bucket settings are ready, cannot edit caps without a credit
card, and currently has only the master application key. No card/payment method
is available or approved. Do not recreate the bucket, request master credentials,
mark restricted keys supplied, or attest console_zero_caps without actual
confirmation. B2 signup permits starting without a card; precise no-card
account cap/default/paid-overage behavior is not established by generic signup
wording. Current task is to obtain displayed cap amounts/free-only status and
privately provision two standard restricted keys through the web console.
Source controls/installed artifact remain unchanged; no provider call/upload,
backup or timer activation occurred for this clarification. Existing Plan09
approval persists.

## Existing caps verified from owner-provided screen —2026-11-08

Screenshot received/reviewed at2026-11-08T10:43:46UTC shows:

- Daily storage cap: $0.00,10GB; displayed usage0bytes/$0.00.
- Daily download bandwidth cap: $0.00,1GB; displayed usage0bytes/$0.00.
- Daily ClassB transactions:2500 maximum; displayed usage0.
- Daily ClassC transactions:2500 maximum; displayed usage7.

This is owner-provided console evidence, not an API observation or remaining
allowance counter. No card/cap edit is required for these existing controls;
no claim is made about an unseen category or universal zero-bill enforcement.
Keep agreed automatic actual-storage/headroom and bounded-transfer checks,
$0budget/daily owner checks and fail-closed behavior. The1GB/day displayed
allowance constrains actual later local download-budget sizing; do not use
the code's4GB maximum as available provider allowance.

Metadata-only keyfile check: all four prepared /etc/birja keyfiles are still
empty, regular/root-owned0600. No contents were read. Next action is to create
and privately save the two restricted standard key pairs and complete independent
password custody; do not re-ask the cap amounts or existing09approval. No B2
request, private source read, backup/restore or timer activation occurred.

## Restricted keys supplied; authentication gate —2026-11-08

Owner said “keys ready”. All four root-owned0600 keyfiles are populated;
opaque checks confirm plain distinct single-line values, no quotes/assignments/
whitespace, plausible hexadecimal IDs, and separate values for each pair.
No credential value/hash or token was printed or retained in public evidence.

Installed exact quota helper made one bounded writer authorization request:
HTTP401 at epoch1794134947, before bucket inventory. A diagnostic classified
both writer and inventory responses as401/bad_auth_token (two requests), and
one independent installed-curl writer cross-check also returned401/bad_auth_token.
Four total authentication-only requests; no upload/delete/init/backup/restore.
Private sanitized records are in ignored plan09-evidence/key-inventory-preflight,
key-authorization-diagnostic and curl-auth-diagnostic JSON files. No retry loop.
The key pair rejection is not attributed to a confirmed source defect.

Owner asks what to write in restic-password. It already contains an agent-generated
private random encryption password from approved setup; retain it and copy it
privately into the off-server password manager. It is separate from both B2
credentials. Actual off-server copying and no-other-writers readiness are not
yet confirmed. Do not rotate/overwrite the password or expose its value.

Resume when the owner privately corrects the keyID/applicationKey pairings
(recreate only restricted keys if original secret was lost), confirms password/
key custody and exclusive writes, then revalidate scopes/inventory. No second
approval for the already named09 scope, no cap edit or bucket recreation.
Protected JSON/controls remain inactive; timer absent,10/15 plans complete.

## Corrected key retry —2026-11-08

Owner disclosed that secret files had contained key names, then requested retry.
Fresh writer authentication is still401/unauthorized; independent inventory
key authentication now succeeds with expected region/all-bucket/no-prefix scope.
Two requests, no bucket inventory/remote mutation/backup. Sanitized retry reports
are retained under ignored plan09-evidence with epochs1794135413/1794135441.
Next owner action is to recheck/update BOTH writer keyID and applicationKey from
the same creation result. Existing encryption password/custody guidance persists.

Inventory authorization success is not full preflight acceptance. Its standard
web-console ReadOnly capability set includes shareFiles; installed controls
currently require every capability to begin read/list and will reject that
extra permission. Keep this concrete compatibility/least-privilege question
open: obtain a minimally scoped key or review a justified source correction;
never filter/misreport authorization capabilities, silently bypass the guard
or modify the installed exact approved archive. No source changes made now.
Prior pair-wide auth failure is superseded only for inventory authentication.

## Current checkpoint —2026-11-09

Both corrected pairs authenticate; ownerconfirmed actual off-server custody
and nootherwriters. Those prior gates are closed. Narrow standardReadOnly
compatibility fix3804ec6 reviewed0active851bafe;25backup/4safety pass. New
548bc494e81dbc719d6db0d0c809c49c018bde5c202d5493d73843870c442118 archive
passed suppliedrecovery67.437s/roles31.076s/TLS51.252s/actualoldrollback102.176s,
copiedgenericverify and0threeprojectresources. Only helper/checksum payload
changed. Installed83...untouched; supplemental exactchecksum installation
decision pending. Fullbindings/source/limits are in06-09-READONLY-EVIDENCE.
Read-onlysource measurement8574655bytes,PG18/revision0007/exactv0.3.1; no
private rows/secrets displayed. No B2upload/realbackup/restore/timer yet.
Earlier authentication/custody pending entries are historical, superseded here.
