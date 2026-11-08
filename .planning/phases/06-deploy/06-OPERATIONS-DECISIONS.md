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
