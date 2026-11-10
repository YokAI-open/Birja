---
phase: 6
slug: deploy
status: completed
nyquist_compliant: true
wave_0_complete: true
created: 2026-10-30
---

# Phase 6 — Validation Strategy

## Final execution reconciliation —2026-11-10

Final evidence: initial real B2 exact restore and genuine calendar invocation
correlation pass; nightly snapshot was rotated under approved one-copy retention,
with current exact restore/presence proven separately. Released source/back-merge
CI all six jobs green (42787743632/42791351766);616backend/100%critical,264frontend,
actual trading/portfolio/history browser flows, strict five-image scans and real
recovery/role/TLS/old-app rollback gates pass. Latest browser10pass/no retries /
1expectedskip; previous health retry remains historical.

Actual approved Plan12 source46d24c8/revision0008 rollout pass: candidate-only
conversion/collation5index comparisons,3restricted roles/9migrator-owned tables,
app+scheduler verified SSL sessions,41origin/9public smoke,3exact B2 recoveries,
original fingerprints equal and isolated cleanup. Required focused checks:
backup25tests51.218s, restore-safety4tests1.371s, CI9tests0.419s. Outage365.719s;
this is recorded elapsed time, not a future SLA. Owner now explicitly confirms
both Gmail and Outlook complete recipient flows. No extra broad test rerun needed
because source and accepted CI artifacts did not change during live execution.

Source/code/security reviews and bounded maintenance/rollout/calendar reviews
have no active blockers/warnings. Separate06-VERIFICATION passed4/4criteria and35/35merged truths with no
blockers/warnings; this strategy file does not self-certify the phase. Older entries below are dated
history, not pending operations to repeat. No raw private evidence is published.

## Earlier execution reconciliation

Execution reconciliation2026-11-08: plans01..08,14,15 complete (10/15).
The owner-authorized safer-image replacement passed independent source review
and final T3C acceptance: all five actual fresh raw scans0HIGH/0CRITICAL,
full616/264 suites, native/build/audit/browser checks and one exact recovery
archive83f4f515... through serial recovery/roles/TLS/actualoldrollback pass.
All six synthetic projects are clean. Historical Plan15 vendor failures remain
below as dated history. Plan09 real off-server recovery/calendar timer, actual
current-head remote CI and all later live/friend acceptance remain pending.
No phase/DEPL completion or provider/production/publication authority is implied.

## Test Infrastructure

Reuse pytest/asyncio, Vitest, Playwright and existing offline shell tests.
The research proposes new backup/restore/role/TLS operational runners and
an isolated PostgreSQL 18 fixture; producer tasks must create them before
their commands are referenced as executable checks. No production or dev
database is a test target. No real identity or email automation.

Quick feedback: run the produced offline restore-safety/backup checks first,
before PostgreSQL setup, settings fixture lifecycle or old-image builds.
The 06-03 restore-safety producer includes real packaging/manifest/path and
installation guard tests; these assert behavior with zero Docker calls on
rejection, rather than source-text or syntax-only checks. Target under 30
seconds for this first feedback; actual duration is pending and must be
measured, never presumed. Record fast-check time, fixture/image setup time
and complete integration time separately, including cold-cache runs. A fast
pass cannot replace complete real PG18 recovery/role/TLS/old-image proof.
The 06-03-02 and 06-07-02 runner producers define optional
`--recovery-bundle <archive>`; omission uses their existing build-produced
default, while supplied input must replay the exact verified archive without
repackaging or fallback. Each runner's `--self-test-recovery-bundle-inputs`
provides fast option/path/hash/manifest/provenance/dependency-closure negatives
with zero Docker/install/download calls. 06-08 invokes these established
interfaces on the final tested-unit artifact: old-host installation and full
backup/retrieval/restore, then unchanged launchers/hash before/after hardening,
with no target feature checkout. Static planning does not establish a pass.
Long gates run serially with bounded progress reporting; exceeding the
target is recorded honestly and does not weaken critical integration.

## Per-Task Verification Map

Reconciled:36 tasks in15 sequential waves (14 at wave7;15 at wave9;08 at
wave10;09..13 at waves11..15). Status is actual coverage as of2026-11-08;
measured local results are distinct from unavailable live/remote evidence.

| Task(s) | Requirement | Verification / producer | Status |
|---|---|---|---|
| 06-01-01 | Both | Existing git branch/base/diff checks before source mutations | complete locally;01 |
| 06-01-02,03 | Both | Explicit operating-policy and blocking-human provenance decisions | choices/provenance complete; live scope remains separate |
| 06-02-01,02 | DEPL-02 | test-backup.sh and backup/status/snapshot/manifest; RED then GREEN | implemented/tested locally; latest25 backup methods recorded in IMAGE-GATES |
| 06-03-01 | DEPL-02 | test-restore-safety.sh and actual test-db-operations.sh lifecycle | implemented/tested; final4 safety methods pass |
| 06-03-02 | DEPL-02 | recovery-bundle.sh/ops-fixtures.py; guards, encrypted recovery and old-checkout-only install | complete locally; final83f4f515... supplied recovery exit0/65.167s |
| 06-04-01,02 | DEPL-01/SC4 | real --roles runner; populated0007->0008 and denials | complete locally; latest exit0/30.099s,65 denied operations |
| 06-05-01,02 | DEPL-01/SC4 | test-db-config.sh and focused connection/config tests | implemented;117 focused tests pass; shared policy wired to3 engines |
| 06-06-01,02 | DEPL-01/SC4 | real --tls/--all runner; handshake/credential negatives | complete locally; latest TLS exit0/49.578s |
| 06-07-01,02 | DEPL-01/SC4 | actual old-image rollback; same installed recovery before/after hardening | complete locally; final same-artifact rollback exit0/102.263s; per-task RED omission retained in07 history |
| 06-08-01 | Both/SC2 | timer/status, final bundle and old-host install rehearsal with tested units | implemented/tested locally; final artifact acceptance in IMAGE-GATES; no live timer |
| 06-08-02 | Both/SC3 | test-ci-ops.py and required ops job; prior backup/safety | implemented/tested locally; CI wiring verified; actual Phase06 CI pending |
| 06-08-03 | Both | full suites/image/audit/coverage, serial ops/rollback, separate reviews | complete locally: five raw scans0HIGH/0CRITICAL, full suites/reviews and10-pass browser;08SUMMARY exists |
| 06-09-01 | DEPL-02 | Explicit scoped host/backup/private-manifest/retrieval/timer approval | approved2026-11-08 for DE189274/exact83f4f515...; no app rollout |
| 06-09-02 | DEPL-02/SC2 | Approved exact recovery artifact/hash verification/install on unchanged v0.3.1, then real remote restore/calendar activation | original tools installed/20filehashes pass; keys/custody valid; reviewed548bc494 replacement install decision, real restore/night pending |
| 06-10-01,03 | Both | Explicit feature push/merge/version-preparation choices | pending human |
| 06-10-02 | DEPL-01/SC3 | Prior CI contract + actual feature-head all-job/browser/ops CI | pending remote |
| 06-11-01 | DEPL-01 | Git diff + prior CI/backup/safety; selected-version candidate gates | pending approved integration/version; no release candidate authorized |
| 06-11-02 | DEPL-01 | Explicit release push/PR approval | pending human |
| 06-11-03 | DEPL-01/SC3 | Prior CI contract + actual release-head all-job CI | pending remote |
| 06-12-01 | Both | Individually scoped release/tag/backmerge/live approval | pending human |
| 06-12-02 | Both/SC4 | Prior quick tests + approved recovery recheck, live SSL/roles and smoke | pending live |
| 06-13-01 | DEPL-01/SC1 | Owner/friends Gmail + Outlook signup/trade/portfolio/history | pending human |
| 06-13-02 | Both/all4SC | Prior CI contract/diff + independent/separate exact-evidence goal verification | pending |

### Current capability coverage (original research producers now exist)

| Capability | Requirement | Secure behavior | Proposed command / producer | Status |
|---|---|---|---|---|
| Backup failures and scheduling | DEPL-02 | No false success/overlap; fresh remote snapshot evidence | `bash deploy/tests/test-backup.sh` | local/synthetic pass; actual provider/nightly evidence pending09 |
| Restore guard | DEPL-02 | Reject unsafe target/corrupt artifact before Docker | `bash deploy/tests/test-restore-safety.sh` | final4 methods pass; supplied-input negatives also pass |
| Real encrypted recovery | DEPL-02 | Exact snapshot restores financial/session/schema invariants privately | `bash deploy/tests/test-db-operations.sh --backup-restore --recovery-bundle <final>` | synthetic actualPG/restic pass65.167s; production remote restore pending09 |
| Role/TLS transition | DEPL-01, SC4 | Runtime denials, migrator success, verified TLS/plaintext rejection | real `--roles` / `--tls`, focused settings tests | local pass30.099s/49.578s; production pending12 |
| Old-ref rollback | DEPL-01, SC4 | actualv0.3.1 preserves restricted roles/verified TLS | `bash deploy/tests/test-rollback-db-security.sh --recovery-bundle <final>` | final same-artifact pass102.263s |
| Trading story | DEPL-01, SC3 | fake/console real-server happy paths execute | actual local Playwright plus required unfiltered CI invocation | local10 pass/1 expected deployed-CSP skip; current Phase06 CI pending10/11 |
| Regression | Both | Money/auth/portfolio/history/deployment checks preserved | CI-equivalent application/ops/image gates |616 backend/264 frontend, audits and operations pass; five raw images0HIGH/0CRITICAL; reviews clean |

## Historical planning strategy — sampling and Wave 0

Every automatic task needs an executable automated check or a dependency
on its named test producer. Record intended RED before behavior changes;
do not count missing fixture errors as behavioral regressions. Do not run
destructive database/migration fixtures concurrently. Always tear down
only the fixed isolated project in finally; never production as fallback.

No three consecutive automatic tasks may lack feedback. Full gates pass
before push/review; actual CI and separate approval precede merge.

## Manual-Only Verification

- Choose external storage, cost limits, retention, recovery targets, key
  custody and nightly schedule; supply credentials privately at execution.
- Approve scoped production backup/download/isolated restore, privilege/TLS
  rollout and production deployment only after concrete rehearsal evidence.
- Prove an actual nightly off-server snapshot and a successful retrieval/
  isolated restore; record IDs, times and pass/fail, never private rows.
- Friend/owner performs Gmail and Outlook inbox/sign-up/trade checks after
  an authorized release. No messages are sent by the assistant implicitly.
- Record push/PR, merge and release/deploy choices separately.

## Validation Sign-Off

- [x] Final task map and missing-file producers reconciled with plans.
- [x] Automatic task coverage and feedback continuity verified in planning.
- [x] Isolated integration/rollback and cleanup contracts concrete.
- [x] Human/live prerequisites explicit; no production authority inferred.
- [x] Planning compliance reviewed separately from execution results.

Historical planning approval: independent recheck passed2026-11-02 with zero
active blockers/warnings. At that approval all implementation, runtime tests,
Wave0 producers and live evidence were pending. That historical statement is
not current execution status; current coverage appears above. No final live
validation sign-off has occurred.

## Additive prerequisite14 validation

Independent check06-14-PLAN-CHECK passed after resolving lock-path and capability-profile findings.

| Task | Automated producer | Actual status |
|---|---|---|
|06-14-01|python3 deploy/tests/test-deploy-prerequisites.py --locks|passed;14SUMMARY|
|06-14-02|same producer --evidence plus backup/restore-safety|passed;14SUMMARY|
|06-14-03|same producer --fixtures plus serial recovery/roles/TLS|passed;14SUMMARY|

14 runtime checks passed and are measured in14SUMMARY; live acceptance remains pending.

## Additive image prerequisite15

Independent15 plan checkpassed afterofflineimage-referenceclosure revision.
Three tasks: immutableactualconsumerpins/provenance with newimage-contract
producer; strictfive-targetscanner/CI; affectedbuild/runtimeandfinalexact
artifactproof/residualscanrecord.16pathsowned, testproducerscreatedbeforeuse.
Actual bounded15runtime acceptance is complete: final cb766040... artifact
passed recovery/roles/TLS/actual-old rollback, with persisted exit0 evidence.
Independent source/security review and focused rechecks have zero active
findings. Actual raw five-target scans remain FAILED with vendor
HIGH/CRITICAL findings; bounded15completion does not complete08task03.
No waiver or live advance. See `06-IMAGE-GATES.md` for current identities,
commands/times and historical resolved packaging failure.

## Plan08 safer-image final acceptance —2026-11-08

Checked task03 replacement contract executed T3A→T3B→independent source review→T3C.
All22 reviewed source paths remain unchanged sincee40f688. Final scanner exit0
29.325s, DBUpdatedAt2026-11-08T06:39:21Z; five actual targets0HIGH/0CRITICAL.
No waiver/ignore/VEX/vendor-file masking or weakened critical-path list.
PGUID70/glibc2.44 and RedisUID65532 clone transitions/untouched abort pass37.064s.
New preserved152156160byte archive83f4f515... passed recovery65.167s,
roles30.099s/TLS49.578s/actualoldrollback102.263s and copied genericverification.
Backend616/99.80%/critical100; frontend264; actual browser10pass1expectedskip
57.406s; native/offline/build/hostaudits/operationalcontracts pass. Two extra
private harness/reporting failures are honestly retained in T3C-EVIDENCE.
Sixfixedprojects0resources. This completes08 only, not actual remoteCI/live
requirements;09..13 remain pending under local-only authorization.
