# Phase 06 — Operations decisions and authority

Updated: 2026-11-02. Non-secret execution ledger for plan 06-01.
Status: Task 06-01-01 complete; awaiting checkpoint 06-01-02.
No operating policy has been approved for Phase 6.

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
| Maximum data loss | Owner accepts nightly logical-dump recovery window, including failed nights, or requests revised PITR research | Pending |
| Recovery time | Owner chooses target time to recover service/data | Pending |
| Schedule | Owner chooses nightly UTC time and allowed jitter; research's 02:30 UTC plus up to 5 minutes is only an example | Pending |
| Freshness | Owner chooses maximum successful-backup age before failure/escalation | Pending |
| Retention | Owner chooses keep policy and any provider lifecycle constraints | Pending |
| Deletion/pruning | Separate explicit authority required | Not authorized; disabled |
| Recovery custody | Repository password and provider recovery access must be recoverable outside this host; owner chooses private custody route | Pending |
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
