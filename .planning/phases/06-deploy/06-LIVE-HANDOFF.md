---
phase: 06-deploy
prepared: 2026-11-07
status: blocked-security-gate
execution_authorized: false
---

# Phase06 live handoff

Owner chose **keep the strict gate; finish local validation and prepare the live handoff** on2026-11-07. Local preparation is complete within the audited scope. **This packet authorizes no live operation.** Plan08 task03 still fails the raw HIGH/CRITICAL image gate;09..13 and DEPL-01/02 remain pending. Phase6 is9/15 complete.

## Tested artifact preserved locally

The exact tested recovery archive is retained outside temporary storage at:

`/home/YokaiExchange/.local/phase-06-handoff/recovery.tar`

This directory is mode0700, its files0600, and it is explicitly git-ignored. The archive contains tools/provenance, not a production database backup. No secret or production recovery material was copied into it. It is not an off-server recovery copy; later independent custody remains required. Original temporary evidence paths remain historical.

| Item | Exact binding |
|---|---|
|Archive size|199,669,760bytes|
|Archive SHA256|`cb766040b9eed5eed4dce00400d39c0d8bcb7a02fc4c6d4030c9e6cf6da16814`|
|Separate checksum|`recovery.tar.sha256` in the same directory; independent approved hash must also be retained off-server|
|Reviewed source|`de331fb` verifier correction; independent `06-15-REVIEW.md` has zero active findings|
|Trusted verifier|Separately copied `verify-restore.py`, SHA256 `4a9c485f8e663b2af4132449a15262f24cac661e54e804cbddc740be3fed30ae`; byte-identical to the reviewed source and bundled verifier|
|Inventory|Separate `INVENTORY.json` SHA256 `af964e14957ae15974f29eb1a98c5bcac3d136c616167845ddbb8f0079286a24`;19 payloads plus inventory/checksums, deploy-recovery-v2 profile, quota helper, both units, PG archive and signed-restic provenance|
|PostgreSQL index|`sha256:bd5dfa494a5a259704365813dbfa5fa6b3e69be7348d43b547f540c730478583`|
|Platform manifest|`sha256:e923a22ac074261dd73970c57edf659475bf0497cb9456f17d98ed7cdd3ca913`|
|Config digest|`sha256:8bca9649e52d948114ccc8164b55b7ab26b64e729893e420114bb5c87bf7c7cc`|

The preserved copy's hash, separate checksum and trusted verifier were checked, and the separately copied verifier successfully ran generic `bundle verify` with `--require-profile deploy-recovery-v2` (exit0, `bundle_verified=true`). No install/load/backup occurred. Changing the archive/source/image later invalidates this exact approval candidate and requires affected review/revalidation; never silently rebuild it under the same hash.

## Completed local evidence

- Final exact-artifact supplied recovery73.507s, populated roles31.845s, verifiedTLS57.607s and actualv0.3.1 supplied rollback119.673s: all exit0. Same archive bytes for both supplied runners; authenticated imported image/fixed alias and pulling disabled.
- Final actual-container frontend static build6.353s; Playwright10passed/1expectedproduction-onlyCSPskip/0flaky57.391s. Fake prices, console email and isolated example.com accounts only. No developer.env or actual market/email service used.
- Existing measured backend616/99.80%overall/100%critical and frontend264 tests, audits/builds and focused operational contracts pass. Dates/scope/identities are in LOCAL-GATES/IMAGE-GATES; no repeated-suite claim is made.
- Independent source/security reviews clean; bounded local-readiness audit found no additional concrete implementation/test gap. All five synthetic project labels were confirmed clean at their respective closeouts; no shared images/cache were deleted.

## Required sequence after the security blocker is resolved

| Boundary | Concrete prerequisite and scope | Required evidence before proceeding |
|---|---|---|
|08 security acceptance|Vendor fixes in actual consumed images, followed by affected tests, exact-image scans and any required archive revalidation. Owner selected no exceptions and no alternate-base migration.|Required strict image scans pass; source review and affected compatibility remain valid. No blanket ignore-unfixed, downgrade or automatic rescan loop.|
|09 preparation/approval|Confirm exact SSH/SCP route, host identity and configuration fingerprints through a separately authorized narrow process. The route is **not verified in this packet**; do not infer it from the website domain. Present exact archive/hash, target allowlists, proposed runtime/tool installation, private config scope and cleanup/undo.|Owner explicitly approves the displayed host/tool/recovery installation, opaque production backup processing, B2 upload/exact retrieval/isolated restore and timer scope. Do not execute from the feature checkout on production.|
|09 real recovery/timer|Keep source checkout at its actually confirmed prechange release. Install immutable recovery at `/var/lib/birja/recovery/releases/<archive-sha>` and stable `/usr/local/sbin/birja-backup`, `birja-backup-status`, `birja-restore-check`. Source projectbirja-prod, checkout/srv/birja; restore only fixedbirja-restore-check, internal/noports/tmpfs. Source release/schema/runtime facts must be revalidated, not assumed from historicalv0.3.1.|Actual off-server same-snapshot retrieval/full private invariant verification; then an actual calendar-triggered successful snapshot. A manual service run cannot prove nightly operation. No app-role/TLS rollout or deployment in this step.|
|10 feature publication|Separate owner push/PR selection, then approved current-head all-job CI and reviewed recovery evidence.|Current exact-head backend/frontend/image/e2e/ops/ci-pass green; separate feature merge/version-preparation choice. Local browser results do not replace remote CI.|
|11 release preparation|Owner-selected version and approved integration; create release branch only from updated integrated develop, preserving git-flow.|Version-only candidate, scoped release push/PR approval, exact release-head green CI. No invented release version or premature release branch.|
|12 publication/rollout|Individually approved main merge/tag/backmerge/live role+TLS+restart+deploy scope and exact ref/artifact; fresh prechange backup+restore evidence.|Observed live least-privilege/verifiedTLS, origin/public smoke, one scheduler, preserved data/schema, and successful post-rollout recovery through unchanged installed entrypoints. No automatic data restore/downgrade.|
|13 friends/final verification|Consenting Gmail and Outlook friends enter codes privately and perform signup/trade/portfolio/history/session checks at the approved live release.|Both recipient classes pass, genuine nightly+restore/currentCI/liveDB evidence current, then final goal verification. No assistant messages/OTP extraction or local-console substitute.|

## Private setup prerequisites for the later approved operation

Destination stays `s3:https://s3.eu-central-003.backblazeb2.com/Birja-backup/prod`, exact bucket case. BudgetUS$0 paid use. Owner verifies private bucket/ObjectLock/lifecycle and console$0caps; preflight measures actual account/version/unfinished storage/headroom with bounded local transfer/request work. Caps are not a universal zero-bill guarantee. Unknown inventory or inadequate replacement headroom stops before upload/deletion.

Keep exactly one verified completed snapshot: verify replacement before removing prior IDs; preverification failure preserves the old copy. No first-delete-to-free-space action. Recovery26h/four-hour target; nightly03:00UTC+up to15minjitter; owner daily checks. Recheck current free allowances/setup at execution, not by inventing provider remaining counters.

Provision secrets privately into validated root-only JSON `/etc/birja/backup.env` and referenced credential/password/CA files; never source that JSON as shell/systemdEnvironmentFile. The read-only account inventory key and Birja-scoped writer have separate roles. Protect controls/state, independent off-server password-manager custody and minimum encrypted recovery_files as specified in RUNBOOK. Never paste secrets, rows, balances, tokens or private manifests into chat/evidence.

## Stop/undo and current next action

Target/host mismatch, invalid provenance, stale source/config/recovery evidence, unknown inventory, exhausted budget/headroom or failing verification stops the operation. Never delete prod volumes, auto-restore real data, reset failed status or broaden target/path guards. Timer disable leaves backup data intact; an already-running job needs its own diagnosis. Reviewed app rollback is distinct from restoring a production database.

**Current next action: retain this packet and wait for a concrete vendor fix that can satisfy08's strict gate.** Do not start09, publish or deploy while blocked. A later instruction must explicitly authorize its displayed external action; this owner answer only keeps strict policy and requests local preparation. No further passing local suite or unchanged-image scan needs repetition without new evidence.
