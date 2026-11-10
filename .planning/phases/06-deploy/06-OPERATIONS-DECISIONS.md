# Phase 06 — Operations decisions and authority

Updated: 2026-11-02. Non-secret execution ledger for plan 06-01.
Status: Plan 06-01 complete (3/3 tasks); approved isolated local restic acquisition verified. Production authority and live evidence remain pending.
User selected Backblaze B2 free tier (US$0 paid usage), operating defaults, recovery custody/checking and latest-only rotation. The supplied destination is recorded below; actual account/bucket controls and all production operations remain unverified and separately gated. Historical pending entries below describe earlier checkpoints, not the current authority.

## Branch preparation — completed

- Starting branch: `develop`.
- `git pull --ff-only`: succeeded; already up to date.
- Updated base SHA: `8a76a68cf54f46fb0267c9d97f0da91d91b117e1`.
- Created implementation branch: `feature/phase-06-deploy`.
- Verification: expected branch, `develop` ancestry and `git diff --check`
  passed before the task commit.
- Existing edits to PROJECT.md, ROADMAP.md and STATE.md, all untracked
  Phase 06 planning artifacts and unrelated `.claude/` were preserved.
  Only this ledger is included in the branch-preparation task commit;
  the orchestrator owns the separate planning/state commit.

## Checkpoint 06-01-02 — owner choices recorded

Approved values below combine the owner's explicit answers. They do not
prove account availability, credentials, quotas or successful recovery.

| Input | Proposal or required answer | Approved value |
|---|---|---|
| Storage backend | Backblaze B2 through S3-compatible API | Approved: Backblaze B2 free tier |
| Destination | Owner-supplied B2 bucket and S3 endpoint; prefix as proposed | Approved: bucket `Birja-backup` (exact case), endpoint `s3.eu-central-003.backblazeb2.com`, prefix `prod`; endpoint identifies `eu-central-003`; account identity/access uninspected |
| Spending limit | Free allowances only | Approved: US$0 paid usage; no automatic paid upgrade or silent overage |
| Maximum data loss | Nightly logical-dump recovery window | Approved: maximum 26 hours; missed backup must be escalated, not treated as meeting target |
| Recovery time | Target, to be measured by recovery rehearsal | Approved: 4 hours |
| Schedule | Nightly UTC with bounded jitter | Approved: 03:00 UTC plus up to 15 minutes jitter |
| Freshness | Maximum successful remote-backup age | Approved: 26 hours; report stale/missing/failure as failure |
| Retention | Single recovery point after successful replacement | Latest explicit instruction supersedes 7 daily/4 weekly/3 monthly: keep one verified completed Birja backup |
| Deletion/pruning | Scoped rolling replacement | Approved policy: remove previous Birja backup only after new off-server upload and verification succeed; preserve old copy on any failure; actual provider actions remain gated; no deletion performed |
| Recovery custody | Independent recovery access | Approved: owner off-server password manager for backup password and storage recovery access |
| Encrypted config recovery | Required service configuration | Approved: include required configuration in encrypted recovery material; no plaintext or secrets in evidence |
| Role/CA custody | Independent recovery access | Approved: owner off-server password manager for database credentials and CA recovery material |
| Missed-night response | Owner checks and responds | Approved: owner daily status checks and handles failures; no messages to others authorized |

Supply secret values only through agreed root-only files, never chat,
committed documentation, command arguments or public evidence.

## Checkpoint 06-01-03 — local acquisition verified

The research's ASSUMED acquisition provenance is resolved for the exact
local executable below by explicit owner approval, expected-key signature
verification and matching artifact checksum. No install or download was
performed in Task 06-01-01. Host installation authority must be obtained
separately from local tooling approval.

## Authority boundaries

The current instruction authorizes local execution preparation and scoped
task commits. It does not authorize provisioning/spending, processing real
production data, remote uploads/retrievals, timer activation, database-role
or TLS changes, service restarts, pushes, PRs, merges, releases or deployment.
Later plans retain their explicit approval checkpoints. Historical release
approvals do not transfer to this phase.

Historical Phase 02.1 constraints remain: `birja.nist.one`, separate
`nist.one` untouched, manual deployment without CI SSH credentials,
Cloudflare Full (strict), manual DNS/certificate renewal without API token,
and no automated Cloudflare, real-IP or firewall changes. D-08 supersedes
the older token instructions.

## Resume

All three tasks are complete. Continue with 06-02 using the verified local
executable explicitly in test PATH, checking its hash/version again if
the ephemeral /tmp path changes. Do not repeat branch creation or policy
selection. No application changes, services or live operations occurred.

## Explicit response — 2026-11-02

User selected “Help me choose a provider” and “Use these defaults” in the
operating-policy questions. The approved values above reproduce that
proposal; this is not approval of a provider, budget, credential storage
location, installation, remote backup or production action.

## Acquisition record prepared independently; approval pending

Local platform read: Linux x86_64. `restic` is not installed.
Proposed pin: official restic 0.19.1 Linux amd64 compressed binary,
`restic_0.19.1_linux_amd64.bz2`, from the official v0.19.1 release:
https://github.com/restic/restic/releases/tag/v0.19.1

Official installation verification reference, checked 2026-11-02:
https://restic.readthedocs.io/en/stable/020_installation.html
Verify SHA256SUMS.asc against SHA256SUMS using the expected maintainer key
fingerprint CF8F18F2844575973F79D4E191A6868BD3F7A907, then the downloaded
compressed artifact checksum before extracting/executing it. Record the
actual checksum/signature result during acquisition; none has been fetched,
verified or installed yet. A signed release tag alone is not binary proof.

Proposed local tooling path: /tmp/birja-test-tools/restic-0.19.1/restic,
explicitly selected in test PATH; no system package or global PATH change.
Host installation would have its own named path and later scoped approval.
Policy checkpoint 06-01-02 is still active; preparing this public acquisition
record does not approve or complete checkpoint 06-01-03.

## Provider recommendation — pending owner choice

Compared official Cloudflare R2 pricing/authentication and Backblaze B2
pricing/restic guidance on 2026-11-02. Recommend R2 Standard using the S3
interface, a private EU-jurisdiction bucket `birja-backups`, prefix `prod`.
Provider/account availability and the destination are not assumed.

R2 Standard includes 10 GB-month, one million Class A operations and ten
million Class B operations monthly; direct egress is free. Standard storage
beyond free allowance is USD0.015/GB-month; request charges also apply. Free
usage is shared with any other account usage. Actual backup volume is not
known or inspected. No claim that usage will be free or budget hard-capped.

Proposed budget: USD5/month requiring review before exceeding it; an
alternative is free allowances only. Both are pending explicit choice.
Storage provisioning, credentials and production uploads remain gated.
No Cloudflare DNS, certificate or zone token is needed for this proposal;
use only S3 object access scoped to the selected private bucket later.

Official sources:
- https://developers.cloudflare.com/r2/pricing/
- https://developers.cloudflare.com/r2/api/tokens/
- https://www.backblaze.com/cloud-storage/transaction-pricing
- https://help.backblaze.com/hc/en-us/articles/4403944998811-Quickstart-Guide-for-Restic-and-Backblaze-B2-Cloud-Storage

Exact account/endpoint and bucket provisioning remain pending. Proposed
custody is the owner's off-server password manager with encrypted recovery
of required configuration/role/CA material; proposed missed-night response
is owner daily review and immediate handling of stale/failed status. These
additional choices were asked explicitly and have not been inferred.

## Owner clarification — provider system backups, 2026-11-02

User reports the VDS provider backs up the whole system and asks whether
that can satisfy the requirement. Provider/service documentation and backup
properties are unknown. R2/provider selection and spending are NOT approved.
Assess the existing service before selecting or buying additional storage.
Required evidence remains off-VDS nightly recovery, PostgreSQL consistency,
retention/access/custody, and a successful isolated restore. A full-system
backup is not assumed either adequate or inadequate solely from its name.

User explicitly approved the proposed recovery/checking policy: off-server
password-manager custody for backup/storage/database/CA recovery material,
encrypted recovery of required configuration, and personal daily backup
status review and handling of failures. No secret values were supplied or
read; no actual configuration was backed up or installed.

Task 06-01-02 remains pending provider/service assessment and an explicit
chosen destination/budget if additional storage is needed. Provider choice
may require a focused plan revision rather than proceeding with R2/restic
assumptions. Acquisition checkpoint 06-01-03 remains unapproved.

## HOSTKEY documentation assessment — 2026-11-02

Owner supplied:
https://hostkey.ru/documentation/controlpanel/server_card/backup/
Read the official page (updated 2026-10-29), without signing into the panel,
requesting backup downloads or accessing any actual private backup.

Documented capabilities: configurable days/time for full VM backup; backup
downloads via S3 storage credentials; tar.gz export; original-server restore
requires stopping the server. Total backup storage quota is 50 GB and new
backups stop at the quota. The page says exported files cannot be restored
or used to create a new server through Invapi. It does not document
PostgreSQL-consistent snapshot/WAL coordination, physical storage failure
domain, encryption guarantees, or actual owner schedule/usage/retention.
Do not infer these properties from the full-system description.

Recommend assessing/reusing this paid/existing service before adding R2.
A candidate adaptation is a nightly consistent PostgreSQL logical dump
included in provider backups, and an actual retrieval plus isolated database
restore drill. A dump remaining only on the VDS is not off-server evidence;
the provider archive must contain it and its independent recovery must be
proven. Need validate export format/extraction path and availability of
recovery without overwriting the live server before accepting this approach.

Asked owner whether all-day scheduling is enabled, its time/timezone and
current 50 GB usage. No R2 spending/provider selection or HOSTKEY changes
are approved. Reviewed restic/S3 plans remain unchanged pending a concrete
owner-selected adaptation and focused verification; do not install tools
or assume the old backend contract still applies.

## Free-tier alternatives requested — 2026-11-02

User does not want the HOSTKEY backup approach and asks for possible free
options. Do not continue HOSTKEY schedule/usage collection as a prerequisite.
No paid storage budget or provider selection has been approved.

Checked official current sources: Backblaze B2 includes the first 10 GB
storage free; download egress is free up to 3x average monthly storage, then
billable. Its documented caps/alerts can limit categories of daily spend;
no unlimited-cost configuration is authorized. R2 Standard includes 10
GB-month plus request allowances and free direct egress; it requires R2
subscription checkout and over-allowance usage is billable. Neither is an
unlimited free storage commitment. Recommend B2 free allowances for further
owner selection, with retained archive size and restore/download limits
measured before claiming it fits the policy. Still use the planned S3 API
and client-side encryption; no additional application dependency needed.

Sources checked 2026-11-02:
- https://www.backblaze.com/cloud-storage/pricing
- https://www.backblaze.com/docs/en/cloud-storage-data-caps-and-alerts
- https://developers.cloudflare.com/r2/pricing/
- https://developers.cloudflare.com/r2/get-started/

Provider/account creation, destination, free-only enforcement and acquisition
checkpoint remain pending. No external account, storage, credential or
production operation was performed.

## Latest-only rotation instruction — 2026-11-02

User asked to create the new backup and remove the previous one. This is
an explicit retention change superseding the earlier multi-version keep
policy and disabled-pruning default. Implement one completed, verified
Birja recovery point at rest, using create-before-delete rotation:

1. Produce a consistent new archive and complete its off-server upload.
2. Verify the exact new snapshot/archive integrity and expected contents.
3. Only then remove the previous Birja snapshot and safely reclaim unused
   repository data. Restrict operations to this dedicated backup set; never
   remove unrelated snapshots, keys, repositories or live database state.
4. Any dump/upload/verification failure preserves the previous backup.
   Missing or ambiguous snapshot identity fails closed; do not delete first
   to make space. Serialize backup and prune operations and check repository
   integrity afterward. Initial recovery proof remains mandatory.

Two snapshots and temporary upload/repacking data may briefly coexist;
free-space/budget planning must include this headroom. One recovery point
cannot recover an error already present in that newest backup. This
tradeoff is explained to the owner; no older history is promised.

Official restic supports latest-only snapshot retention plus pruning:
https://restic.readthedocs.io/en/stable/060_forget.html
This is a policy/implementation instruction, not evidence that a new backup
exists or a previous backup was deleted. Provider selection, installation
and scoped production operations remain separately pending.

## Resource-limit optimization requirement — 2026-11-02

User explicitly requires backup logic to account for limits and be
optimized. Treat this as an execution acceptance requirement, preserving
the chosen latest-only/create-before-delete policy and pending provider.

- Back up the PostgreSQL logical archive and the minimum required recovery
  configuration. Exclude Docker images/build caches, application logs,
  dependency trees and rebuildable Redis/cache data. Do not broaden access
  or omit financial/session database state to save space.
- Measure archive/repository size, run time, CPU/memory pressure, uploaded
  and downloaded bytes and request counts using synthetic fixtures first.
  Do not guess real production size, compression ratio or dedup savings.
- Use standard compression/deduplication supported by the reviewed tools;
  benchmark their combination instead of blindly double-compressing data.
  Reuse uploaded content when supported; avoid redundant archive creation,
  repeated uploads and unnecessary storage/list/check requests.
- Serialize backup/verification/prune, with bounded retries/backoff and
  timeouts; schedule off-peak. Exceeding a resource or free-tier allowance
  fails visibly and preserves the previous verified snapshot. Never
  silently delete first, skip verification or switch to paid usage.
- Budget for temporary coexistence of old/new snapshots, local staging,
  upload/repack overhead and provider-specific request/download limits.
  Count all retained versions, incomplete objects and repository overhead,
  not only the logical database size. Handle quota/partial-upload failures
  without claiming success or destroying the recovery point.
- Distinguish routine new-backup integrity checks from full retrieval/
  recovery drills; do not introduce needless repeated full downloads that
  exhaust free egress. Initial real off-server retrieval/isolated restore
  remains mandatory, and later drill frequency must fit the chosen budget.
  Define the exact routine assurance before pruning; never label an
  unexecuted recovery drill as passed.
- Tests must cover quota exhaustion, insufficient replacement headroom,
  failed/partial uploads, interrupted cleanup, concurrent runs and bounded
  retry/request behavior. Record measured costs and pass/fail privately
  without rows, individual balances or secret values.

No specific provider, numerical resource ceilings or paid spend is inferred.
At implementation, reconcile these requirements into the owning backup,
restore, scheduling and validation tasks with focused regression evidence.
No runtime/source change, installation, backup or deletion occurred here.

## Provider selection — Backblaze B2 free tier, 2026-11-02

User explicitly selected “Backblaze B2’s free tier”. Destination provider is
now approved; do not ask that choice again. No paid allowance is approved.
Actual account region, private bucket name and S3 endpoint must come from
the owner's provisioned bucket. Do not fabricate an account or endpoint.
Recommend EU region if available; bucket names are globally unique. Do not
create a public bucket or enable Object Lock, which conflicts with the
requested rolling deletion. No provider account/bucket has been created by
the assistant, no keys supplied, and no remote repository initialized.

Use the S3 API: official restic documentation recommends it over its native
B2 backend due to native-library error handling. B2's default retained file
versions can defeat repository pruning and consume free storage. For this
dedicated restic bucket, use the documented 'Keep only the last version of
the file' lifecycle; hidden versions are then deleted after one day. Never
configure age-based deletion of currently referenced restic objects. This
is provider object-version cleanup, separate from keeping one verified
application snapshot. Include hidden versions, unfinished uploads and
transient two-snapshot/repack space in quota calculations. Surface cleanup
lag and free-limit failure; do not silently pay or delete the only copy.

Free-policy verification must cover storage, download and request budgets,
provider caps where supported, and no event-notification or other paid
features. Do not present caps as a universal hard billing guarantee. Avoid
attaching a payment method if the owner's free-account path allows it.
Owner must verify the actual account controls; no account access occurred.

Exact account setup references checked 2026-11-02:
- https://www.backblaze.com/docs/cloud-storage-create-and-manage-buckets
- https://www.backblaze.com/docs/cloud-storage-integrate-restic-with-backblaze-b2
- https://www.backblaze.com/docs/cloud-storage-lifecycle-rules
- https://www.backblaze.com/docs/en/cloud-storage-data-caps-and-alerts
- https://restic.readthedocs.io/en/stable/030_preparing_a_new_repo.html#backblaze-b2

Asked only for the non-secret bucket name/S3 endpoint, or 'not created'.
Separately presented the exact prepared restic 0.19.1 Linux amd64 official
artifact and signature/checksum verification for isolated local installation
at /tmp/birja-test-tools/restic-0.19.1/restic. No global package/PATH or
production service changes proposed. Local install approval is still
pending, and never transfers to the later production installation gate.

## Exact destination and local acquisition approval — 2026-11-02

Owner supplied bucket `Birja-backup` and endpoint
`s3.eu-central-003.backblazeb2.com`. Preserve the bucket's exact case; use
the proposed prefix `prod`. The selected non-secret restic destination is
`s3:https://s3.eu-central-003.backblazeb2.com/Birja-backup/prod`.
This is the selected address, not a connectivity test or permission to
read credentials, list objects, initialize a repository or upload data.
No bucket privacy, Object Lock state, lifecycle/version cleanup, quota,
free-tier caps or recovery access has been verified. Validate these under
later scoped authority; do not silently lowercase, substitute or provision
a different bucket if a backend rejects this address.

Owner explicitly approved the prepared official restic 0.19.1 Linux amd64
artifact `restic_0.19.1_linux_amd64.bz2` for isolated local testing at
`/tmp/birja-test-tools/restic-0.19.1/restic`, after signed SHA256 verification
against expected key `CF8F18F2844575973F79D4E191A6868BD3F7A907`.
Public artifact download and scoped local git commits are authorized.
No global package/PATH, service or production installation is authorized.
Production acquisition/install, private source/config/credential reads,
real backups, provider actions, timers, push/PR/merge/release and deploy
remain pending their separate checkpoints.

Task 06-01-02 policy acceptance is complete. Quota safety is a required
implementation and later live preflight condition: US$0 paid usage,
temporary old/new coexistence and repacking headroom, hidden versions and
unfinished objects, bounded requests/retries and download budget. Routine
verification must fit that budget; initial actual off-server retrieval and
isolated restore remain mandatory. These are requirements, not measured
production resource ceilings or proof that free allowances suffice.

## Verified local acquisition result — 2026-11-02

Re-read official installation and pinned release documentation independently
before execution:
- https://restic.readthedocs.io/en/stable/020_installation.html
- https://github.com/restic/restic/releases/tag/v0.19.1

Downloaded only the approved executable archive plus verification material
over HTTPS, following HTTPS-only redirects:
- https://github.com/restic/restic/releases/download/v0.19.1/restic_0.19.1_linux_amd64.bz2
- https://github.com/restic/restic/releases/download/v0.19.1/SHA256SUMS
- https://github.com/restic/restic/releases/download/v0.19.1/SHA256SUMS.asc
- https://restic.net/gpg-key-alex.asc (linked by the official installation page)

Used an isolated GPG home under the approved tooling directory; no user
keyring, credentials or storage configuration was read. The public key
bundle includes an old revoked key; only the explicitly expected primary
fingerprint was accepted. `gpg --no-autostart --batch --status-fd 1 --verify`
returned exit 0, GOODSIG and VALIDSIG for
`CF8F18F2844575973F79D4E191A6868BD3F7A907`. Signature timestamp:
2026-07-05 07:59:26 UTC. GPG's undefined web-of-trust warning is expected
for an isolated keyring; identity was pinned to the independently checked
official fingerprint, not inferred from a UID or short key ID.

The signed checksum file contained exactly one matching archive entry.
SHA-256 matched before decompression or execution:
`f415415624dcc452f2a02b8c33641791a8c6d6d3b65bbb3543fcf9a25151585c`.
Compressed size: 10,107,515 bytes. Extracted binary size: 30,941,346 bytes;
binary SHA-256:
`20d4142678d0d95ec11a4759def1b73fd9190abc9ca19e4b62d067c0b387e639`.
These hashes identify public tool artifacts, not private database content.

Installed at `/tmp/birja-test-tools/restic-0.19.1/restic` with mode 0700;
tooling directory and GPG home mode 0700. The only binary invocation was
`version`, exit 0: `restic 0.19.1 compiled with go1.26.4 on linux/amd64`.
Use the exact path or a per-command test PATH; no global PATH/package or
service change occurred. No repository was initialized, no backups made,
and no provider request or production data/config access occurred.

Sandbox DNS initially blocked public GitHub download; the approved scoped
network escalation succeeded. GPG import initially tried an unavailable
agent socket; public verification with `--no-autostart` succeeded without
starting a service. These environment restrictions did not weaken either
verification gate. The ephemeral tooling may disappear; repeat signature,
checksum and version verification before reacquisition or replacement.

## B2 observability checkpoint — 2026-11-06

Plan08 has no source changes as of2c8f3fa. Its executor was interrupted by
a usage limit during official-document research. The owner said continue.
Official docs describe console-managed caps, up-to10minute propagation and
no ClassDcap. No documented API was found for live cap settings or remaining
account billing/download counters. Do not invent that API or mark a manual
value as a current automatic observation.

A concrete design revision is PENDING OWNER ANSWER: preserve US$0 paid
usage policy, owner verifies $0 console caps at setup, bounded automatic
actual storage/version/unfinished/headroom checks and bounded transfer work,
owner daily status handling. Console controls are owner-attested facts,
not machine-verified billing proof; no universal hard-zero guarantee.
No paid use, provider access or live activation is approved by the question.
The alternative is to leave scheduled production backup disabled pending
stronger observable provider controls. Elapsed time is not approval.

Independent CI/local checks may continue while this scoped answer is pending.
Do not implement a permanent always-failing preflight and call it a usable
nightly backup. Task08-01/final artifact readiness remain pending.

Sources checked2026-11-06:
- https://www.backblaze.com/docs/cloud-storage-create-and-manage-caps-and-alerts
- https://www.backblaze.com/docs/cloud-storage-data-caps-and-alerts
- https://www.backblaze.com/cloud-storage/pricing

## Owner-approved B2 controls revision — 2026-11-06

Owner answered: “Use console caps and automatic checks (Recommended)”.
The practical policy above is APPROVED for implementation: US$0 budget,
owner-verified $0 console caps during setup, automatic actual storage and
replacement-headroom checks, bounded transfers and daily owner status checks.
No universal hard-zero billing guarantee is claimed or required as an API
proof. Distinguish owner-attested controls from current measured inventory;
never fabricate remaining account billing/download counters. The previous
requirement to fetch console-only controls/remaining counters automatically
is superseded. Unknown inventory or inadequate headroom still fails before
upload/deletion; retain previous copy. No provider/account/production action
is authorized by this design answer. Actual setup verification remains09.

## Owner direction — 2026-11-07: continue locally

Owner requested continued local phase work until completion. This selects
local-only work, not a push/PR/release/provider/production operation. Do not
repeat push questions during this scope. Remaining live checkpoints still
require their concrete evidence and scoped authority; local-only language
does not authorize production-data access, timer activation or live mail.

Final actual-image local browser suite passed10/1expectedCSPskip, with fake
prices, console email, throwaway example.com accounts and separate tmpfs
project. Cleanup verified. Independent LOCAL-READINESS audit found no new
concrete local implementation/test gap; all full live/currentCI criteria
remain unverified. Raw image security findings remain blocking. Security
paths were presented for owner choice; no answer/waiver/base migration is
recorded. Preserve strict policy and existing plans; do not manufacture live
acceptance or automatically start another remediation cycle.

## Owner decision — 2026-11-07: keep strict gate and prepare handoff

Owner answered: “Keep the strict gate; finish local validation and prepare the
live handoff”. This resolves the security-path question: retain strict raw
HIGH/CRITICAL enforcement, no exception/base migration. Local validation and
independent readiness audit are complete. Prepared06-LIVE-HANDOFF.md and
preserved the exact verified recovery archive/checksum/trusted verifier in
ignored.local/phase-06-handoff. No live action or publication is authorized;
09..13 remain gated after08's unresolved vendor findings. Do not re-ask this
policy choice or repeat successful local work without new evidence.

## Owner scope update — safer alternative images

Owner requested “fix it then, maybe another more safe image?”. This authorizes
local alternative-image evaluation and implementation under the same strict
raw HIGH/CRITICAL policy. It supersedes the earlier no-alternate-base scope,
not the live/publication boundaries. Owner separately confirmed existing
DHI authentication; ordinary Docker image operations may use that login,
without reading/printing credential files or helper secrets. Authenticated
DHI Debian candidates were actually scanned and failed; no exception was
created. Public Wolfi/Chainguard candidates measured0H0C; assembled images
and populated compatibility remain execution gates, not assumed passes.

Existing08task03 revised with a checked three-segment replacement contract;
completed01/02/15 history and15-plan count are preserved. No push, provider
or production data/ownership/collation action is authorized.

## Plan09 host route and prepared scope —2026-11-08

Owner answered “same vds” to the access-route question. Route is direct local
execution on DE189274, not SSH/SCP. Metadata-only preflight observed root/Linux
amd64, Docker29.2.1/Compose5.0.0/Python3.12.3/systemd255, source `/srv/birja`
at exactv0.3.1 `0107706617b8bbf9c1a069f3e3ccc9c53b9ab2f7`, projectbirja-prod
backend/scheduler/PG18.6-trixie/Redis8.8.3-trixie running. Backup config/controls,
recovery install, `/usr/local/bin/restic`, launchers and backup timer are absent.
No secret/config contents, logs or private rows were read; no service changed.

LIVE-HANDOFF now displays the exact direct-host operation: archive83f4f515...,
immutable recovery/tools/restic and checked global link, protected JSON/state,
private credential/control setup, bounded B2 backup/exact retrieval/isolated
restore, then nightly timer after success. Actual B2 controls/keys/material/
resource bounds remain unverified. Host-route confirmation alone grants no
installation, private production processing, provider or timer authority.
Explicit Plan09 decision remains pending;10/15 plans complete, no09SUMMARY.
No app-role/TLS/schema/engine/restart/publication/rollout scope is included.

## Explicit Plan09 approval and installed preparation —2026-11-08

Owner answered “Approve Plan09 backup setup and verification” to the exact
DE189274/83f4f515... scope displayed in LIVE-HANDOFF: install recovery/restic,
private config, $0-policy encrypted B2 backup/exact isolated restore, then
nightly timer after successful restore. This supersedes earlier local-only
limits for these named09 actions only; no app deployment/restart/role/TLS/
schema/engine/publication/private-record inspection authority is added.
Approval persists through credential setup and pending nightly observation.

Owner remembers creating the bucket and asks whether another is required.
No: reuse Birja-backup. Actual settings/credentials/caps remain unverified;
no duplication or bucket creation occurred. Installed exact verified artifact,
root/current/three private launchers and authenticated recoveryPG image;
all20payload/inventory hashes pass. Signed retained restic0.19.1 linked at
/usr/local/bin/restic and hash/version checked. Prepared private backup state,
four empty credential files and generated unseen backup password under/etc/birja.
No existing secret overwritten or value exposed. LIVE-RECOVERY records actual
partial installation and privately completed owner setup steps.

Final metadata recheck: source exactv0.3.1 unchanged; original4production
container IDs/states unchanged. No remoteB2/request/init/upload/retrieve,
production backup/restore, timer installation/activation or app restart.
One private installation verification script misread public inventory files
as a mapping and stopped before mutation; corrected exact-checksum parsing
and20file verification passed. No source/artifact correction needed.
Task01complete; task02awaits privatekeys/controls/custody, then actual real
restore/nightly evidence. No09SUMMARY, Phase6 remains10/15.

## No-card account and master-key clarification —2026-11-08

Owner says bucket setup is ready, no credit card is available so cap editing
is disabled, and only the master application key exists. Do not require a
card, recreate the bucket or accept a master key on the server. Existing $0
budget and authorization remain unchanged. The prior instruction to edit caps
is corrected to inspect current limits first; an already verified zero cap
requires no edit. Actual displayed cap/free-only status is requested before
controls attestation; no claim that no payment method alone proves all caps.

Guide now explains two standard web-console keys: Birja-backup/prod/ writer
and all-bucket read-only inventory, privately saved in the four prepared files.
No source/artifact change, provider access/upload, backup or timer action.
Do not bypass console_zero_caps in the installed preflight or attest unknown
facts. Approval persists while this missing setup evidence is resolved.

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

## Plan09 restricted credential authentication gate —2026-11-08

Owner reported keysready; four private files populated/format valid. Actual
B2 authentication rejects writer and inventory pairs with401/bad_auth_token;
independent curl writer check confirms. Four bounded auth-only requests total,
no remote mutation/inventory/backup. Details in LIVE-RECOVERY/private sanitized
plan09-evidence. Stop attempts until owner corrects matched keyID/applicationKey
values; no master key, bucket recreation, scope waiver or new tool is needed.

Owner asked what to write in restic-password: existing random password already
generated during approved setup must remain unchanged and be copied privately
off-server. Custody/exclusive account write readiness remain unconfirmed.
Existing09approval/$0limits persist; no controls attestation/config/timer yet.

## Corrected credentials, custody and replacement candidate —2026-11-09

Both corrected standardkeys authenticate on exactendpoint/sameaccount; writer
Birja-backup/prod/ valid. Owner answered “Saved off-server; no other writers”.
Credential/custody/exclusivewrite gates resolved; no repeatedconfirmationneeded.
Source guard rejected vendorReadOnly shareFiles. Narrow3804ec6 fix recognizes
only that name, no account/storagewrite allowance and no token-issuing API.
Independent focusedreview0findings851bafe;25backup4safetylint/format and four
same-new-archive suppliedreplays pass. See09-READONLY-EVIDENCE for details.

Candidate548bc494e81dbc719d6db0d0c809c49c018bde5c202d5493d73843870c442118
is a concretely reviewed/tested152156160byte replacement. Only helper and its
checksum differ; oldapproved83... remainsinstalled. Because the explicit09
installation named83..., supplemental548... install approval is pending;
existingbackup/restore/timer scope persists. No new approval inferred from
“continue”. No automatic live patch, snapshot, provider write or timer action.

Approvedopaquesource-sizing query measured8574655bytes/PG18/revision0007 and
unchangedexactv0.3.1. Propose32MiBstaging/600s/64MiBdownload/64nativecalls per
operation under observed1GBdaydownload cap, actualheadroom stillneeds fresh
inventory. No actual remaining allowance claim or private data shown.


## Approved548 replacement installed; trusted lock alias correction —2026-11-09

Owner explicitly approved replacement installation for548bc494e81dbc719d6db0d0c809c49c018bde5c202d5493d73843870c442118.
Trusted immutable bundle install exited0; current/root-only launchers and signed
restic route to that release. Protected controls/static recovery/live backup JSON
were created and load successfully. Existing keys, generated password, source
checkout and services were not replaced; original83...release remains.

Fresh inventory failed at shared lock acquisition, before provider HTTP:
Ubuntu's trusted /var/lock -> /run/lock alias violated canonical equality.
No production lock inode/mode change. Bounded REDae16a95/GREEN0e47c50 supports
only the exact trusted alias and retains directory/owner/mode/inode/O_NOFOLLOW/
exclusive and inherited-flock guards.18prereq25backup4safety/lint pass;
independent review has0BLOCKER/0WARNING. A new exact archive is being replayed
before checksum-specific installation approval under09task02. Do not patch
installed548inplace or re-ask09scope/caps/keys/custody. No actual backup/upload,
restore, timer or app/publication operation occurred. Phase6 remains10/15.


## New lock-alias packet ready for exact installation decision —2026-11-09

Archived5fe2059b3e984ffcd0dff6b1763dd5a97deddb0be638ca23e49381d35a54401 is preserved candidate-lock-alias.
Only snapshot helper/checksum differ from installed548; independent review clean,
18prereq25backup4safety pass. One exact packet recovery66.973s/roles30.711s/
TLS51.936s/actualoldrollback104.093s and copied verification pass;3synthetic
projects0resources, production ref/all4running IDs unchanged. No new live action.
Request only the new exact checksum installation decision required by09task02;
existing named09scope, caps, corrected keys and off-server custody persist.


## Approved replacement, actual recovery and timer —2026-11-09

Owner approved exactd5fe2059b3e984ffcd0dff6b1763dd5a97deddb0be638ca23e49381d35a54401 replacement installation on DE189274.
Trusted immutable install exited0; all20payload/inventory hashes, current,
3root-only launchers and identical signed-restic link pass. Existing protected
configuration was validated/reused. Corrected system lock and actual bounded
B2inventory/headroom pass; initial visible/hidden/unfinished/other account bytes
were0, private bucket/ObjectLock-off/lifecycle policy validated. Empty encrypted
repository initialization succeeded2.634s. No credential value was displayed.

First installed backup completed2026-11-09T07:43:40Z in11.817s,11tool calls;
60,773bytes staged backup data, private staging removed. Exact remote snapshot:
`bed51816831081a195e4b3ef5b39f8f4059cd8feb1b4e51289f9bed05da46194`.
Installed exact-snapshot retrieval/isolated restore passed12.211s, completed
2026-11-09T07:44:22Z. Private table/schema/financial/session/sequence invariants
and source/config/tool-bundle binding pass; installed exact-source recovery gate
also passes. Source remains exactv0.3.1/0107706617b8bbf9c1a069f3e3ccc9c53b9ab2f7,
revision0007. Fixedbirja-restore-check has0containers/networks/volumes and no
private restore staging. No production restore or app operation occurred.

After restore passed, systemd-analyze verify exited0 on both exact retained
units; installed root-owned0644 under /etc/systemd/system, daemon-reload and
only enable--now birja-backup.timer succeeded. Timer enabled/active/waiting,
OnCalendar03:00UTC daily, randomized15m, accuracy1m, persistentyes. Actual next
trigger: **Tue 2026-11-10 03:11:32 UTC**. LastTrigger is empty; backup.service has
no InvocationID/start/exit timestamp. No manual service start occurred. Genuine
calendar-run evidence is PENDING; default service Result=success is not a run.

Installed birja-backup-status exits0. Final checks confirm actualproduction
ref/all4original running container IDs unchanged and fixedclone/staging clean.
Sanitized immediate exit/time/ID metadata in ignored plan09-evidence files:
lockalias-approved-install-inventory.json, repository-init.json,
first-live-backup.json, first-live-restore.json, nightly-timer-install.json,
first-live-final-status.json; unit-verify/operation logs remain private there.
A final bookkeeping attempt to directly parse backup configuration was rejected
by automatic approval review before execution; the accepted replacement uses
only the installed sanitized status interface plus IDs/ref/counts. No direct
configuration read was needed for final health evidence.

All actions stayed within named09authority and previously approved rolling
replacement policy (latest-only instruction explicitly superseded disabled
pruning). No unrelated snapshot/provider/production deletion was performed.
Keep Plan09 pending for actual calendar evidence; no new owner input needed.


## Owner sequencing update —2026-11-09

Owner explicitly said “let's not wait for it, will check it later”. Proceed
with Plan10 review/publication preparation while the first genuine scheduled
backup observation remains deferred. The real encrypted backup, exact isolated
restore/private invariants and installed timer are already proven. Keep09 and
DEPL-02 pending; do not fabricate nightly success or create a completed09SUMMARY.
This instruction changes sequencing only. Actual CI, publication approval,
merge/release/deployment approval, fresh recovery gates before rollout, and
final friend/calendar acceptance are retained. Timer scheduling stays unchanged.
This supersedes the requirement to wait for the first night before preparing10.

Prepared local review package only; user has not selected push/PR/merge/release
or deployment. Earlier no-push/no-pushquestion preference applies to the prior
local-only work; the requested forward work now reaches10's explicit publication
checkpoint after concrete preparation. No remote write is inferred from deferral.


## Exact feature push and PR authorized/executed —2026-11-09

Owner chose “Push and open PR” for exactc085a766a056b017fce1d9d6e2f737541867ae79,
feature/phase-06-deploy,112local commits, targetdevelop. Nonforce feature push
and prepared PR creation both exited0. PR26/head verified; actual CI42583320799
running. No integration/version/release/deployment authority is inferred. New
pushed source commits require an explicit scope-consistent choice; checkpoint
bookkeeping stays local. Nightly observation remains deferred, not passed.


## Actual CI and corrective validation —2026-11-09

CI42583320799 on approved/pushedc085a766 completed FAILURE. Backend616 tests/
99.80%overall/100%critical, frontend264 and browser10passes/1expectedproduction
CSPskip succeeded. Actual trade.spec and complete portfolio-history buy/sell
flow executed. Image/ops/ci-pass failed; no green aggregate claim.

All5original image logs show mkdir/cache/db permission denied and empty reports,
not vulnerability findings. Ops lacked hostuv/locked dependencies required by
test-db-config.sh. REDc5fc244/GREEN7d5d8c2 adds the established setup-uv and
uvpythoninstall/uvsync--locked to ops, and effectiveUID:GID to scanner Docker
runs. Four source/test files,39added lines,11implementation lines. Private
0700cache/0600input and all readonly/capdrop/no-new-privileges/pin/rawseverity
checks remain intact. No suppression or image/application changes.

Independent06-10-CI-FIX-REVIEW reports0BLOCKER/0WARNING;5CI/13image tests pass.
Real nonroot hostUID1001:GID1002 Docker proof reproduces old denial and proves
corrected private access in0.972s. Existing S102/untouched formatting baseline
was reproduced and left unchanged; changed source/sections pass focused checks.
One fresh actual5image scan passed32.416s, every target0HIGH/0CRITICAL,
DBUpdatedAt2026-11-09T06:57:06.372182267Z/DownloadedAt08:17:06.729314674Z.
Original CI logs/artifacts and new raw reports remain ignored/private under
pr-preparation. No recovery archive/replay/install, provider/timer/prod action.

The original publication approval namedc085a766. Prepare the exact corrective
candidate after the evidence commit, then request its follow-up push/PR-body
update before publishing. Actual corrective-head GitHub CI remains pending;
no merge/release/deploy approval.09nightly proof remains owner-deferred and
10/15plans remain complete. No09/10SUMMARY or DEPL completion.


## Corrective publication approved and executed —2026-11-09

Owner chose “Push fixes and check CI” for exact57b8774cc93f26000f3e691421c9fefd0020e375,
three local commits. Nonforce feature push and prepared PR26 description refresh
both exited0. Read-back PR head equals that approved SHA. New actual pull_request
CI42585485295 was created2026-11-09T08:22:34Z:
https://github.com/YokAI-open/Birja/actions/runs/42585485295.
Backend/frontend already pass; image/browser/ops remain in progress at this
observation. No passing aggregate, merge/version/release/deploy authority yet.
Initial CI42583320799 failures remain retained; no claim they passed. Actual
corrective-head result must be inspected. Nightly proof remains owner-deferred.


## Second CI result and reviewed root-fixture correction —2026-11-09

Approved57b8774 push/PR-description refresh succeeded. Actual CI42585485295
completedFAILURE: image/backend/frontend/e2e PASS, ops/ci-pass FAIL. The scanner
cache correction is proven on GitHub; no vulnerability gate exception needed.
Ops reached18prerequisites and failed two actual TLS lock caller tests because
this real provisioner correctly requires root. Later syntheticTLS also chowns
private server keys0:70. Keep these production guards; explicitly use sudo only
for privileged synthetic prerequisites and serial image/recovery/role/TLS/old
rollback CI fixtures. Hostuv/dbconfig checks stay in the prepared runner env.

REDb1dd6dd/GREEN0637b48 implements that bounded5file workflow/test-only change.
Fixture source reads use -c safe.directory=<canonical ROOT> -C ROOT; no wildcard,
global config or shared checkout ownership/mode changes. Actual private repo
proof reproduces root/runner ownership rejection and verifies exact exception
plus unrelatedrepo denial. Actual TLS nonroot denial/rootcreatecheck/key0:70
mode0640 passes.18prereq/5CI tests pass; independent ROOT-CI-REVIEW has0BLOCKER/
0WARNING and reran them. No installed recovery/runtime/image/provider/timer
change. One serial local root integration is in progress; actual new-head CI
and follow-up publication approval remain pending. Firstnight proof deferred.


## Root-fixture correction ready for publication —2026-11-09

Independent06-10-ROOT-CI-REVIEW reports0BLOCKER/0WARNING and independently reran
5CI/18prerequisite tests. Actual private owner/TLS proof and focused source
checks pass; production root/owner/mode guards remain unchanged.

One serial local run of the exact CI synthetic producers as actual UID0 passed:
image-transition38.695s; --all recovery/roles/TLS151.225s; actualold rollback
106.876s, all exit0. Current source0637b48df9d88bbda7ad0141029febde30a296ad
remained unchanged during those runs. Final label queries confirm0containers/
networks/volumes across birja-ops-test, birja-restore-check,
birja-image-transition-test and birja-rollback-test. Immediate command/result/
elapsed logs are retained in ignored pr-preparation/root-ci-* records.
No production/provider/installed recovery/timer change or new image scan.

Actual GitHub image artifact for previous approved57b8774/run42585485295 was
downloaded and checked: all5targets reportok=true/exit0/qualifyingfindings0.
Backend/frontend/browser also passed that actualrun. Only ops/ci-pass failed
the newly corrected root setup. Current root-fix head has not run on GitHub
and is not approved to push yet. Do not call the required aggregate green.

Prepare exact next3commit candidate (RED/GREEN/evidence) for explicit follow-up
push. The owner may authorize this update only, or reviewed/tested CI/test-only
follow-up corrections plus their planning records until required CI succeeds,
with all gates intact. No application/runtime/image/recovery/production change,
merge or deployment authority is inferred.09calendar proof stays deferred and
10/15 plans complete; no09/10SUMMARY/DEPL advancement.


## Bounded CI completion authorization —2026-11-09

Owner selected “Publish and finish CI” for exact995b46426194a4773f24099f6bb17a4048bc34c7
and3reviewed commits. Nonforce push and prepared PR26description refresh exited0.
Standing authorization now covers further independently reviewed/tested fixes
ONLY in feature/phase-06-deploy's .github/workflows/ci.yml, deploy/tests/ and
planning records until required CI succeeds. Preserve existing security/test
checks; no weakening/skipping tests or severity policy. Do not re-ask for pushes
inside this explicit scope. Application/runtime/image/recovery/production code,
merge/release/deployment and force-push are excluded and retain separate gates.
Current actual new-head run is being observed; no green aggregate claim yet.
Nightly proof remains deferred; no plan/requirement completion inferred.

## Reviewed nginx CI privilege correction —2026-11-09

Actual995b464/run42588116337 completed failure: backend/frontend/image/e2e
passed; ops failed only at the final offline nginx check because nginx-t opens
/var/log/nginx/access.log. The existing script explicitly documents root and
uses a disposable config/certificate/prefix, with no install/reload/start.
RED49df53f/GREENeec70c5 changes only the CI invocation to sudo plus regression.
Five CI contracts, Ruff lint/format, scoped diff and actual root nginx check
with temporary cleanup pass. Independent NGINX-CI-REVIEW reports0/0.
Publish under existing bounded CI completion authorization; no new push
question. Required current-head CI remains pending; no merge/deploy authority.
Recorded 2026-11-09T12:20:10Z. Nightly proof remains deferred;10/15 plans unchanged.


## Reviewed Docker runner capability correction —2026-11-09

Actual1bbaa69/run42616168904 passed backend/frontend/image/e2e and every
offline ops check including nginx. Populated image-transition passed30.200s.
Recovery package preparation then failed its pinned Docker image inspection.
Exact runner20261101.360 has Docker28.0.4/API1.48; image inspect --platform
requires API1.49+. Local29.2.1 supports the existing command.

RED8d3466f/GREENf5ad5cc pins matching29.2.1 CE/client packages from Docker's
official signed apt repo in the disposable ops runner, before fixture work.
The clean-root /usr/bin/docker/default socket preflight pulls the unchanged
pinned image and verifies platform inspection. Six CI contracts, focused Ruff/
diff and read-only old-API rejection/new-API command+identity-guard proof pass.
Independent DOCKER-CI-REVIEW reports0 blockers/0 warnings. VDS Docker/service,
recovery source, image pins and installed archive remain unchanged.

Publish under existing bounded CI completion authority; actual new-head
hosted setup/required CI remain pending. Merge/deployment and deferred nightly
proof retain their distinct gates. Phase10/15 unchanged.


## Reviewed CI image-store alignment —2026-11-09

Actual58c4258/run42617492782 passed Docker29.2.1 setup/platform inspection,
offline ops, app/browser/image jobs and populated transition33.549s.
Recovery packaging then rejected classic archive membership at unchanged
verify_saved_image line280. Runner inspection exposed the config identity;
Docker documents that upgrades retain the classic store. Raw failed archive
members are unavailable; do not claim their exact difference was captured.

REDb44f381/GREEN57974aa preserves existing daemon JSON/features while enabling
containerd only on the disposable ops runner, before restart/pull/build. New
test-only preflight checks the driver, saves the unchanged pinned public PG
image, authenticates registry provenance and invokes the original strict
archive verifier with anonymous temporary-file cleanup and bounded save.
Seven CI contracts, Ruff/format/diff and actual local containerd export+
unchanged verifier4.929s pass. Independent STORE-CI-REVIEW reports0/0.

Publish under existing bounded CI completion authority. Actual runner replay
remains pending; no VDS daemon change, recovery code/image pin/installed bundle
change or new production action. Merge/deployment and deferred nightly proof
remain separate; phase10/15 unchanged.


## Current green CI and integration decision —2026-11-09

PR26 https://github.com/YokAI-open/Birja/pull/26 remains OPEN/MERGEABLE into
develop at exact a7d5dcb01d40a916c9cbf9d6ff51525c70c50833.
Actual run42618704350 completedSUCCESS:
https://github.com/YokAI-open/Birja/actions/runs/42618704350.
All six required jobs backend/frontend/image/e2e/ops/ci-pass passed; no required
job skipped. Job logs and raw public reports are preserved in ignored
pr-preparation/passed-ci-* and final-image-reports.

Backend616pass/99.80% overall/100% critical; frontend264pass. Browser10pass,
one expected csp.spec production-only skip because E2E_PROD_URL is absent.
Actual trade.spec buy/sell and full buy->portfolio->history->whole-sell pass,
including375/768/1024/1440 widths. Five raw runtime/builder/Node/Postgres/Redis
reports hash-match successful status records and each contain0HIGH/CRITICAL.
No ignores/waivers or severity changes.

Ops proves pinned29.2.1/clean-root containerd export through unchanged strict
verification. Populated transition34.051s, encrypted recovery62.533s, roles
24.112s/65permission denials, TLS23.141s and actualold rollback96.232s pass.
Old checkout/credentials/Compose/revision unchanged; missing/failed/stale
evidence and bad CA/hostname/plaintext reject; immutable routing/lock and0008
preservation pass. Mandatory cleanup succeeded. No VDS daemon/recovery change.

06-10-02 complete. Next06-10-03 requires explicit Create-a-merge-commit into
develop and separately selects release preparation/version. Suggested0.4.0
is a proposal only; not selected. No merge/release/deploy authority inferred.
Production remains reportedv0.3.1. Exact installed recovery d5fe2059... and
actualB2backup/restore remain dated09November. First genuine nightly observation
is owner-deferred;09/DEPL-02 pending. Phase10/15; no09/10SUMMARY/completion.

This supersedes older publication/CI-pending entries. Final local tracking
edits stay unpushed so greenPRhead remains exacta7d5dcb. Preserve/carry edits
through any approved integration/release; never discard or publish silently.


## Approved feature integration and release preparation —2026-11-09

Owner selected “Merge and prepare0.4.0” for exact green PR26/a7d5dcb.
All six exact-head checks reverified before gh pr merge --merge
--match-head-commit. PR26 is now MERGED into develop as 5ebf62b33b190aaf04a48b107a222e906fbf4c99,
at 2026-11-09T12:53:43Z. Explicit permission covers this feature integration and
local release-0.4.0 preparation only. Release push/main PR, merge/tag/backmerge
and production rollout remain separate unapproved gates.

Preserve local final CI records/Plan10closeout through updateddevelop into
releasebranch. Plan10complete; Plan11task01 prepares four version metadata
files using locked tools, no dependency or application changes. Keep actual
nightlyproof deferred and09/DEPL-02 pending.


## Local release0.4.0 ready for publication choice —2026-11-09

Branch release-0.4.0 was created from updateddevelop5ebf62b after approvedPR26
merge. Carries final featurecloseout0e0a6eb and reviewed versioncommit
524080f5414b71de336239c008c3ddcecaefd3dc. BothPhase5/6merge ancestors verified.
Four files/five versionvalues0.3.1->0.4.0 only; parsed complete metadata
normalization and74backend/638frontend inventory hashes prove all dependency
records/artifacts unchanged. No source/image/recovery/runtime change.

Local7CI/25backup/4restore-safety tests, uvlockedofflinesync/check, frontend
lint/types/metadataformat/build passed. Independent06-11-LOCAL-REVIEW0blockers/
0warnings independently verified full metadata equality, ancestry and lock.
No repeated fullapp/DB/browser/image runs; actualrelease-head CI must stillrun.
Fresh featureCI42618704350 remains evidence only for unchangedimplementation.

Last recorded installed recovery archive is d5fe2059...; actualB2backup at
07:43:40Z and exactisolatedrestore at07:44:22Z on09November passed. Freshness
has not been rechecked in this local release task and must be rechecked before
any approved rollout. First genuine nightly observation remainsowner-deferred.
No provider/private/production action or archive rebuild occurred.

Task11-01 complete;11-02 awaits explicit publication choice. Resolve exact
publicationHEAD after this planningcommit; show three local releasecommits
(closeout,versions,evidence), target origin/release-0.4.0 and mainPR. Prepared
PRbody/title are ignored/private. Owner approval sofar covers localprep only,
not releasepush/mainPR/mainmerge/tag/backmerge/deployment. No11SUMMARY yet.


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


## Local rollout correction authorized —2026-11-09

Owner selected “Prepare local rollout fix”. Prepare a protected persistent
clone-volume binding and concrete TLS-before-startup procedure, with meaningful
synthetic cutover/rollback/negative tests and independent review. This permits
local source/test/documentation work on release-0.4.0; no updated releasepush,
mainmerge/tag/backmerge, VDS/private/provider operation, archive installation
or production service/volume change. Existing16623a8 PR27 stays unchanged.
Retain the accepted image/security/recovery gates and installed independent
recovery payload. No new phase plans/counter reset; scoped closure of the
confirmed readiness findings is part of pending11-03/12preparation.

## Local rollout correction verification —2026-11-10

The owner's “Prepare local rollout fix” scope was executed locally on
release-0.4.0. Protected persistent selected-volume routing, exact running
identity checks and TLS-before-first-start are implemented; initial and
follow-up independent source reviews have no open findings. Real supplied
archive cutover run12 passed, including current0008 deploy, actual v0.3.1
app rollback, Redis state/authentication, unchanged originals and pre/post
exact restores. Final committed compatibility evidence is recorded separately
in06-12-LOCAL-FIX-EVIDENCE; this entry does not replace those results.

PR27 still publishes16623a8; refreshed Git/PR metadata confirms OPEN into main.
Preparing/reviewing/testing local fixes does not extend the earlier exact-head
push approval. Updated release publication requires the next concrete candidate
choice. Main merge, tagging, back-merge and deployment remain separate.
No production preflight, private configuration read, volume/role/TLS/app change,
provider operation, timer change or recovery installation occurred in this scope.
Plan09 actual scheduled-run observation stays owner-deferred; counters11/15.


## Approved77dcd44 publication and CI correction —2026-11-10

Owner selected “Push fixes and check CI” for all18 commits through77dcd44.
Nonforce publication/PR27 update completed; actualCI42782054013 had four jobs
green, ops fixture-checkout failure and aggregate failure, successful cleanup.
No main merge/tag/deployment occurred. Reviewed local7d3f8a4/c343f6b isolates
synthetic Git system config without changing production/runtime/security
policy.8contracts and full same-archive cutover246.010s pass; see RELEASE-CI.
New publication authority remains pending; previous approval named77dcd44.
No nightly observation, phase/DEPL acceptance or source-image rescan inferred.


## Approved bounded CI completion —2026-11-10

Owner selected “Publish and finish CI” for three commits through
38eb25ca2457cb05299e08ef668ffebd5bd6551d. This explicitly permits further
independently reviewed/tested CI workflow, test and planning fixes on the
release branch until required CI passes. Existing test/security/recovery gates
remain enforced. App/runtime/image/recovery/production changes, merge and
deployment are excluded. Do not re-ask to publish follow-ups within this scope;
a source or operational expansion still needs its own concrete decision.

Approved38eb25c push/PR27 update completed. ActualCI42785059635 is running.
No merge/tag/back-merge/deployment occurred. Preserve77dcd44's failed ops run
as history; do not label corrected runner behavior proven until the new run.


## In-scope precise Compose consent correction —2026-11-10

Run42785059635 confirmed Git isolation but exposed Bake's missing explicit
read consent for retained Dockerfile outside app context. The owner-approved
CI completion scope covers REDb31f3dd/GREENd7f0cf5: ephemeral ops runner only
pins Compose5.7.0 from Docker's signed apt repository and verifies clean-root
actual version before fixtures. Independent review clean,9contracts pass,
full same-archive local proof with verified private5.7.0 passed257.676s and
cleanup. No global bypass/wildcard, production plugin update, app/runtime /
image/recovery change. Publish/follow CI under existing scope, no repeated
approval request. Merge/deployment stay separate;09nightly stays deferred.


## Plan11 final CI acceptance —2026-11-10

Bounded CI authority fulfilled: published9457911/run42787743632 all six jobs
SUCCESS. Git and precise Compose Dockerfile-consent corrections pass actual
runner cutover206.439s/rollback/recovery/cleanup; independent reviews clean.
Health-screen retry remains reported, not declared fixed. Plan11 complete,
phase12/15,66/69=96%; DEPL-01/02 and09nightly are incomplete.

No main merge/tag/GitHub release/back-merge/deployment is authorized by CI
completion. Present separate Plan12 choice for exact published9457911 merge
into main. Planning closeout remains locally committed for next approved
integration, preserving the verified published source. Do not delete local
release branch before carrying it. Production measurements/window remain
future scoped preflight; no private/provider/production operation occurred.

## Main merge completed —2026-11-10

Owner explicitly selected “Approve main merge” for PR27 head
945791115c0bd88fd0cf62835aca3e03c395659f. Before merging, GitHub readback
confirmed exact head, main base, OPEN/MERGEABLE/CLEAN and all six checks SUCCESS.
`gh pr merge --merge --match-head-commit` completed successfully at
2026-11-10T09:24:42Z. PR27 is MERGED; resulting main commit is
46d24c8591de2207cf219429aac0768962bed4c3.
GitHub commit readback verified both parents: previous main0107706617b8bbf9c1a069f3e3ccc9c53b9ab2f7
and approved release945791115c0bd88fd0cf62835aca3e03c395659f.

Only main merge was authorized/performed. No tag, GitHub release, back-merge,
production inspection, restart or deployment occurred. Keep the release branch
and local planning closeout9f4bf5f plus this record for the next approved
integration. Phase remains12/15;09/12/13 and DEPL-01/02 remain incomplete.
Next publication candidate: v0.4.0 at the resulting main SHA, using prepared
release notes; requires separate explicit tag/release authorization. Back-merge
push/PR and its eventual green-CI merge require their own scope decisions.
Production still needs measured preflight, final retained MANIFEST, fresh
recovery proof and an approved maintenance window. Nightly observation remains
owner-deferred.

## Release publication completed —2026-11-10

Owner explicitly selected “Publish v0.4.0 release” at main commit
46d24c8591de2207cf219429aac0768962bed4c3 using the prepared release notes.
Rechecked main SHA and no existing v0.4.0 tag/release before publication.
Created annotated tag v0.4.0 (tag object
bb64990ba6be425e66e0a560cbd6a6d3589e4a79), pushed only that tag, and published
https://github.com/YokAI-open/Birja/releases/tag/v0.4.0
at2026-11-10T09:29:02Z. GitHub readback confirms public/non-draft/non-prerelease;
remote peeled tag matches the approved main SHA exactly.

No back-merge push/PR/merge or production operation was authorized/performed.
Local planning commits remain preserved on release-0.4.0 for the next approved
integration. Next: request release-branch push and PR into develop, inspect its
own exact-head CI, then request merge approval. Keep the branch until both
integration and its planning records are preserved. Phase12/15 and pending
09/12/13, DEPL-01/02 remain unchanged; nightly observation is still deferred.

## Back-merge PR ready —2026-11-10

Owner approved pushing release-0.4.0 through
6097085e9d5ca897bed7ec76aeee7b61071509e8 (three local planning commits),
opening the PR into develop and checking CI. Nonforce push and PR creation
succeeded. PR28 https://github.com/YokAI-open/Birja/pull/28 is OPEN,
MERGEABLE/CLEAN at that exact head, base develop.
Actual CI https://github.com/YokAI-open/Birja/actions/runs/42791351766
completed SUCCESS: backend/frontend/image/e2e/ops/ci-pass all six green.
Public logs confirm backend616 passed, frontend264 passed, browser10 passed
without retries and1expected skip. Real recovery/TLS/old-image rollback and
finally cleanup passed. Previous release-run health retry remains historical;
this passing run does not claim a source fix for that flake.

Merge remains unapproved: require separate exact-head Create-a-merge-commit
approval under CLAUDE.md. This local receipt stays unpushed so the proven PR
head remains6097085; preserve it before deleting the local release branch.
No additional code changes, production reads or deployment. Phase12/15 and
09/12/13, DEPL-01/02 remain pending; nightly observation remains deferred.

## Back-merge completed —2026-11-10

Owner selected “Approve back-merge into develop” for PR28 exact
6097085e9d5ca897bed7ec76aeee7b61071509e8. Immediately rechecked base develop,
OPEN/MERGEABLE/CLEAN, matching head and all six current checks SUCCESS.
Merge-commit operation succeeded2026-11-10T09:44:22Z. PR28 is MERGED as
63c9b479209aaa180fc1f41314a367dd79fab2f8. GitHub commit readback verified
parents5ebf62b33b190aaf04a48b107a222e906fbf4c99 and approved6097085.

Release publication and develop integration are complete. Main/tag v0.4.0 stays
46d24c8591de2207cf219429aac0768962bed4c3. Local CI receipt51c7b8d and this
merge record remain preserved on the release branch; do not delete that branch
until they are carried into subsequent authorized integration. No further push
is inferred from this merge approval.

Next is the explicit read-only production preflight in ROLLOUT-PROPOSAL:
fixed birja-prod container mount/image identities, volume/disk sizes, installed
recovery integrity and sanitized PG/Redis compatibility/catalog checks. Private
values remain private; no container environment/raw rows/logs, provider access,
backup/restore, timer inspection, writes/restarts or deployment are included.
Preflight requires its own checkpoint answer before access. Actual nightly
observation remains owner-deferred. Phase12/15;09/12/13 and DEPL-01/02 pending.

## Read-only preflight completed —2026-11-10

Owner approved exact fixed-host/project read-only scope. Actual results and
concrete next preparation proposal are in06-12-PREFLIGHT.md. Baseline remains
clean010770/0007 with original volumes/services unchanged. Recovery integrity
passed; disk capacity is ample. PG TLS/roles and retained deploy/routing are
not provisioned; five indexes use default collation. No provider/timer access,
backup/restore, production file write, service or database mutation occurred.
No new authority follows from successful preflight. Next checkpoint is the
exact host-preparation scope and expected MANIFEST in that report. Phase stays
12/15 with09/12/13 and DEPL-01/02 incomplete; nightly observation deferred.

## Approved host preparation completed —2026-11-10

Owner approved the exact preparation scope in06-12-PREFLIGHT. Execution and
separate postchecks succeeded; see06-12-HOST-PREPARATION for measured results
and off-server custody paths. Actual retained MANIFEST70e568a8/all129files
matches released main46d24c8. TLS and staged role credentials created; two
approved empty unused candidate volumes and protected routing records exist.
Live container IDs/images/mounts remain identical and healthy; prod.env metadata
and independent recovery unchanged. No live data/role/TLS/service transition,
backup/restore, provider/timer operation or deployment occurred.

Next: save only the NEW material off-server and confirm custody, then prepare
the separate exact maintenance/rollout decision. Custody confirmation alone is
not production restart/deploy approval. Phase12/15;09/12/13 and DEPL pending.

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
