---
phase: 06-deploy
audited: 2026-11-07
scope: bounded-local-readiness
status: blocked
phase_complete: false
---

# Phase 06 local readiness

Phase 06 remains **9/15 plans complete**. The available local implementation,
compatibility rehearsals and browser checks are complete within the reviewed
scope. **Plan08 task03 is blocked by raw HIGH/CRITICAL image findings.** No
additional concrete local source defect or missing local test was found in
this bounded audit. This is neither final phase verification nor acceptance
of the remaining security findings; DEPL-01/02 remain pending.

This independent pass read the roadmap contract, current plans/evidence and
the affected wiring. It inspected existing sanitized execution JSON/logs and
raw image-report counts rather than treating SUMMARY claims as proof. It ran
no suites, builds, scans, services or external operations. Current source was
not changed; no policy exception or owner decision was inferred.

## Roadmap contract

| Success criterion | Local code and observed evidence | Current truth | Exact missing prerequisite / next boundary |
|---|---|---|---|
| SC1: Gmail and Outlook friends sign up and trade at the public HTTPS site | Existing `frontend/e2e/trade.spec.ts` signs in a synthetic user, previews/buys and sells; the separate actual-server portfolio/history story checks returned financial values. Persisted local browser result has 10 passes, one expected deployed-CSP skip and no failures. | **UNCERTAIN — WARNING:** current-release real inbox/friend evidence unavailable. Local console/fake flows do not prove delivery. | Plan12 approved secure release/rollout, then Plan13 consenting Gmail and Outlook recipients privately complete signup, trade, portfolio/history and session checks; retain only provider class/ref/UTC/pass-fail. No additional local implementation identified. |
| SC2: production data backed up nightly off-server and successfully restored | Timer calls the retained `/usr/local/sbin/birja-backup`; producer invokes bounded quota refresh under the operation lock; recovery verifies authenticated artifact/data identity and freshness. Final supplied archive recovery exited0 in73.507s; same archive old-release rollback exited0 in119.673s. | **UNCERTAIN — WARNING:** synthetic encrypted recovery is proven; actual production off-server restore and calendar-triggered snapshot are unavailable. | Plan08 security gate first; Plan09 scoped provider/host/config/material/transfer/install authority, private setup and exact-archive approval, then real remote retrieval/isolated restore and an actual successful nightly calendar trigger. Manual runs do not close this. No missing local producer identified. |
| SC3: Playwright e2e in CI covers the trading happy path | `.github/workflows/ci.yml` executes unfiltered `npx playwright test`; `ci-pass` requires backend/frontend/image/e2e/ops and rejects failed/cancelled/skipped jobs. Ops calls real serial recovery/roles/TLS/old-image runners. Local browser execution is observed, not just test discovery. | **UNCERTAIN — WARNING:** wiring verified; no actual current Phase06 feature/release CI result is available. | Plans09→10 dependencies and separately approved feature publication/PR; actual exact-head all-job CI including trade and portfolio/history outputs, followed by release-head CI in Plan11. Known strict image failures currently prevent a green aggregate. Local-only authorization supplies no publication authority. |
| SC4: production least-privilege app role and recorded DB SSL decision | `bootstrap-roles.sql` creates non-superuser separate app/scheduler/migrator roles with scoped grants; production Compose routes distinct credentials and CA mounts. Backend, scheduler and Alembic all call `database_connect_args`; its default SSL context verifies CA/hostname and prod rejects missing CA. HBA rejects plaintext. Existing local roles/TLS runs exit0 in31.845s/57.607s; roles log records65 denials. | **UNCERTAIN — WARNING:** local wiring/handshakes verified; current production role/session/SSL evidence unavailable. | Plan12 exact-release and live role/TLS/restart/deploy authority, fresh production recovery gate, private credential/certificate provisioning, observed scoped role/SSL checks and post-rollout recovery. No further local role/TLS implementation identified. |

All four complete live/current-CI truths remain unverified. Absence of live
evidence is not reported as absent implementation. The observed failing image
gate below is a **BLOCKER**, independent of these evidence warnings.

## Six remaining plan boundaries

| Plan | Already complete locally | Required prerequisite and unfinished result | Actionable local work now |
|---|---|---|---|
| 08 — scheduling, CI, local gates | Tasks01/02; full measured616 backend/264 frontend suites, audits/builds, offline ops, final exact-artifact replays, actual local browser suite; source/security reviews have zero active findings. | Task03 strict image acceptance fails. Raw final reports: runtime49H, builder54H, PostgreSQL91H/2C, Redis48H, Node48H. Available bounded fixes were delivered by15; required test-tool/vendor rows remain and no waiver exists. | Keep failure/policy decision explicit. No proved local bug remains. Do not rescan unchanged images, repeat passing suites, add research plans or weaken policy. A specific vendor fix or separately reviewed owner security resolution is needed before targeted implementation/revalidation. No08 SUMMARY. |
| 09 — live recovery/timer | Verified final archive, stable launchers, synthetic old-host recovery and usable procedures. | Completed08; explicit exact-artifact host/provider/opaque production-read/backup/retrieval/isolated-restore/unit scope, private controls and independently held recovery material. Must then observe real restore plus actual nightly trigger; preserve unchanged v0.3.1 app until later rollout. | None without new security resolution and live authority. Do not fabricate `06-LIVE-RECOVERY.md` acceptance. |
| 10 — feature publication/integration | Concrete local code/evidence/reviews are available. | Completed09; separately selected push/PR scope; actual approved-head all-job CI; separately approved feature merge and owner-selected release version/preparation. | Preserve local-only preference; no push question/action now. Actual CI cannot be manufactured locally. |
| 11 — release candidate | Existing version metadata and release process already defined. | Approved integration/version and completed10; candidate from updated develop; scoped version-only preparation, separate release push/PR authority and actual release-head CI. | No release/version choice exists for this phase. Do not invent one or create a release branch early. |
| 12 — secure production rollout | Local retained installer, final recovery and actualv0.3.1 rollback proof complete. | Completed11; individually scoped merge/tag/backmerge/rollout choices, exact artifact/ref and fresh real recovery. Actual production non-owner/TLS deployment, origin/public smoke and unchanged installed-entrypoint post-rollout recovery must pass. | No additional local rollout/rollback implementation identified. Keep all production actions pending. |
| 13 — friend acceptance/final verification | Local trading/portfolio/history behavior observed; criteria and final evidence links are explicit in the plan. | Completed12; Gmail and Outlook recipient acceptance, real timer/restore, current CI and live role/SSL evidence; final goal verification only afterward. | Keep final `06-VERIFICATION.md`,13 SUMMARY and requirement/phase completion pending. This audit closes only stale local-readiness accounting. |

## Evidence independently inspected

- `/tmp/birja-e2e-local-bigoocoe/playwright.json`: start
  `2026-11-07T16:27:34.098Z`, expected10/skipped1/unexpected0/flaky0,
  errors empty. The four responsive cases use routed fixture data; the
  separate cash-only and buy→portfolio→history→sell cases use actual local
  server responses. Neither kind proves real inbox delivery or remote CI.
- `/tmp/birja-plan15-fixed-package.json`: package/verify exit0,199,669,760bytes,
  archive SHA256 `cb766040b9eed5eed4dce00400d39c0d8bcb7a02fc4c6d4030c9e6cf6da16814`.
  `/tmp/birja-plan15-replay.json` binds both supplied runners to that archive,
  records all four successful commands/times and four successful cleanup
  commands. Sanitized supplied-recovery/roles/TLS/old-rollback logs confirm
  feature-checkout denial, populated transfer,65 permission denials, transport
  negatives and preserved0008 across actual old-image rollback.
- `/tmp/birja-plan15-final-image-reports/{runtime,builder,postgres,redis}.json`
  and `/tmp/birja-plan15-final-node-0t6brzg7/node.json`: parsed actual
  vulnerability arrays reproduce the blocking counts above. The final Node
  report is used for its rebuilt identity. Dated2026-11-06 reports remain
  evidence of failure; this audit performs no fresh scan or fixability claim.
- Source links inspected: `.github/workflows/ci.yml`, `deploy/scan-images.py`,
  `deploy/systemd/birja-backup.{service,timer}`, `deploy/backup.sh`,
  `deploy/backup-snapshot.py` quota refresh and final authorization-time
  recheck, `deploy/verify-restore.py`, `deploy/db/bootstrap-roles.sql`,
  `deploy/db/pg_hba.conf`, `docker-compose.prod.yml`,
  `backend/app/db/connection.py` and its three engine consumers, and actual
  browser story assertions. Prior source reviews `06-REVIEW.md` and
  `06-15-REVIEW.md` close source findings only, not image/live acceptance.

No private configuration, `.env`, `.aws`, production/provider endpoint,
real authentication/email/trade or publication operation was accessed.
The report and current validation tables are the only owned edits; unrelated
work is preserved. Temporary logs are supporting local artifacts, not a
durable substitute for the later approved current-evidence checkpoints.

## Owner selection after audit — 2026-11-07

Owner chose keepstrict/finishlocal/preparehandoff. `06-LIVE-HANDOFF.md` now
records the exact artifact and future gates. No exception, base migration or
live action is approved. This later policy note does not alter the audit's
observed local results or the blocked overall acceptance.
