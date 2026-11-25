# Phase 21 production preflight proposal

The owner requested publication and deployment. GitHub published v0.8.0.
The approved Phase 21 rollout combines the 0026 upgrade with live stock
admission. Expanded exchange coverage, account scope for IEX data and
durable use, and out-of-list quote and corporate-action proof remain open.
This proposal requests a separate decision to prepare a deployment with
stock trading and live stock collection paused. Preparation and a paused
deployment leave the live requirements and Phase 21 acceptance open.
[Live-source qualification](21-LIVE-QUALIFICATION.md)

## Selected release

| Item | Identity |
|---|---|
| Production target | DE189274, `/srv/birja`, project `birja-prod` |
| Last recorded running source and schema | `07d3aa5c627b5ba550aa2d11baa13e2becaf3aa9`, `0023` |
| Published release | `v0.8.0` at `0f4a42f4dfec657314d2feaab1c5a539c69518b8` |
| Released tree | `0eb379b4240d0a28918dffcab0825f12c2c555e7` |
| Expected retained deploy manifest | SHA-256 `672b8680b3d8649a7b3bd4eb56a2aecb618591456f2ba3e685c38ed2de4b55f1` |
| Recovery profile and archive | `deploy-recovery-v7`, payload 6, `0026`, SHA-256 `a32f8c92f66eff8b081538fc4989e282c5da2e2c5320cf9008b315bb34efde5d` |

The expected retained manifest was computed from the 350 tracked files
selected by the released installer. The same commit's six passing checks
and seven-stage recovery receipt are recorded in the
[release CI record](21-RELEASE-CI.md). Shell syntax passed for the installer,
deployment launcher and smoke script.

## Read-only host scope

Once approved, verify the host and deployment log before reading fixed
container image, mount and health metadata. Check PostgreSQL schema,
restricted role and TLS metadata, stock flag states, current retained
tool and binding identities, local disk headroom, and local backup and
restore receipts and inventory count. Record sanitized results. Use
local protected metadata for this step, with live backup-service
measurements reserved for the approved backup and recovery scope.
App, Git and system configuration writes, writer stops, volume operations,
provider access, backup and restore require later authorization.

## Proposed paused-stock cutover

Use the existing protected tooling and fresh exact encrypted restore
gates with the actual predecessor. Keep `STOCK_DATA_ENABLED=false` and
`STOCK_ACTIONS_ENABLED=false`. Proceed only after verifying the mounted
source and available distinct candidate. Under the shared operation lock,
fence the writers, verify the final predecessor snapshot and restore,
and copy and migrate the approved candidate to `0026`. Preserve the
predecessor data and tooling. Run origin and public smoke, confirm crypto
and stock refusal, then take and verify a fresh encrypted 0026 backup in
the approved isolated clone. Confirm off-server custody with the owner.

Before the first candidate writer, the measured original 0023 release and
volumes can be reopened after the rollback checks. After the first writer,
preserve 0026 data and use tested 0026-compatible recovery. The exact
maintenance window, volume selection, capacity, live recovery evidence and
rollback route must be bound to the actual host before asking for cutover
approval. [Production runbook](../../../deploy/RUNBOOK.md)

Phase 21 Plans 06, 08 and 09 retain the live catalog and trading
requirements. Their proofs stay pending until live qualification and
activation are complete.
