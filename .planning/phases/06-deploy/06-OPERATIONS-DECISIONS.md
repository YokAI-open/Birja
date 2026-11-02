# Phase 06 — Operations decisions and authority

Updated: 2026-11-02. Non-secret execution ledger for plan 06-01.
Status: Task 06-01-01 complete; awaiting checkpoint 06-01-02.
User approved the operating defaults below; destination, budget and remaining custody/response details are pending.

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

## Checkpoint 06-01-02 — owner choices pending

Recommendations below are proposals from the reviewed plan/research,
not approvals or inferred account availability.

| Input | Proposal or required answer | Approved value |
|---|---|---|
| Storage backend | Recommend owner-provisioned off-server S3-compatible repository; existing independent SFTP storage is an alternative | Pending |
| Destination | Provider/account, endpoint, region and bucket/prefix, or independent SFTP host/path; no credentials in this ledger | Pending |
| Spending limit | Owner chooses currency and maximum recurring cost | Pending |
| Maximum data loss | Nightly logical-dump recovery window | Approved: maximum 26 hours; missed backup must be escalated, not treated as meeting target |
| Recovery time | Target, to be measured by recovery rehearsal | Approved: 4 hours |
| Schedule | Nightly UTC with bounded jitter | Approved: 03:00 UTC plus up to 15 minutes jitter |
| Freshness | Maximum successful remote-backup age | Approved: 26 hours; report stale/missing/failure as failure |
| Retention | Desired keep policy; destructive enforcement separately gated | Approved: 7 daily, 4 weekly, 3 monthly; no automatic pruning yet |
| Deletion/pruning | Separate explicit authority required | Not authorized; disabled |
| Recovery custody | Independent recovery access | Approved requirement: encryption password and recovery credentials kept outside this server; exact private custody route pending |
| Encrypted config recovery | Owner chooses which configuration and recovery material to include separately from the database archive | Pending |
| Role/CA custody | Owner chooses independent recovery custody for database credentials, CA and keys | Pending |
| Missed-night response | Owner chooses operator check frequency, responsible person and escalation; no external notification is implicitly authorized | Pending |

Supply secret values only through agreed root-only files, never chat,
committed documentation, command arguments or public evidence.

## Checkpoint 06-01-03 — acquisition pending

Restic remains the research's proposed executable with installation
provenance marked ASSUMED. Exact platform/version/artifact, official origin,
signed checksum verification and local installation scope must be presented
for explicit approval after the policy checkpoint. No install, download or
existing binary inspection was performed in Task 06-01-01. Host installation
authority must be obtained separately from local tooling approval.

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

Verify the task commit and branch, then resume at 06-01-02 with the owner's
explicit non-secret operating contract. Do not repeat branch creation or
mark plan 06-01 complete. After policy approval, prepare the concrete
acquisition record for 06-01-03 and stop for its separate scoped approval.
No application changes, runtime tests, services or live operations occurred.

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
