---
phase: 15-verify-exact-portfolio-recovery-and-acceptance
verified: 2026-11-22
status: passed
score: 4/4 roadmap outcomes verified
supporting_plan_truths: 12/12
requirements_satisfied: [PSAFE-04, PSAFE-05, PSAFE-06]
overrides_applied: 0
verification_scope: local implementation and source-bound component qualification
---

# Phase15 — Independent Goal Verification

**Goal:** Users and the operator can rely on the full strategy lifecycle after
migration, recovery and supported rollback/refusal, with privacy and once-only
financial effects preserved.

**Passed locally:4/4 outcomes,3/3 assigned requirements.** Verification inspected
actual source, service assertions, original raw receipts and independently
recomputed hashes; summaries and artifact existence were not treated as proof
of behavior. All four plans are complete. No new human verification is needed:
accepted screens and their relevant inputs are unchanged.

## Observable outcomes

| # | Roadmap contract | Status | Evidence |
|---|---|---|---|
|1|Exact encrypted restore preserves active/frozen identities, owners, closure, baselines, cash, holdings, lineage and sequences, including original migrated data, same-symbol and zero-active cases; deleted books stay private.|VERIFIED|`portfolio-smoke.py:963` authenticates/installs the matching consumer, creates an encrypted restic snapshot, destroys the source stack, verifies restored payload hashes and restores on a new server. `portfolio-closure-recovery-fixture.py:require_projection/project` requires31tables/24identity tails and the independent economic oracle. R5 raw log confirms source destruction and immutable comparison. Unchanged migration/authority evidence separately verifies original cash123.45/baseline8765; it is not mislabeled the new10000baseline fixture. Existing private-read tests and restored closed refusals keep deleted finances unavailable.|
|2|Restored original creation, fill and event retries cannot repeat grants/trades/payments, cross targets or restart frozen activity.|VERIFIED|`replay_restored` at fixture:657 calls real `create_portfolio`, crypto `execute` and `process_dividend` using retained original keys/payloads/fingerprints. It checks original portfolio3/fill4/payment2, all fill fields, three closed-target refusals, unchanged active/zero lists and all31table contents. Exact sequences compare before retry; later values cannot regress or be reset. R5 reports all assertions passed and `sequence_changes={}`.|
|3|The documented migration and supported rollback/refusal contract rejects incompatible old applications/schemas without merging roots, moving money or discarding evidence.|VERIFIED|RUNBOOK:660–732 records genuine current0023, qualified0020/0017, retained0007–0014 and actual0014/0020→0023 upgrade/selected-refusal scopes. Existing source-family dispatch/manifest and authority checks remain substantive. Six inherited recovery logs have matching successful receipts and unchanged139-input authority/migration scope; actual current authority matches all inherited triples. The installed-consumer fix uses authentic bundled sources rather than historical repinning. Finite campaign selection preserves prior outputs and original request identity.|
|4|The full real isolated accounting/concurrency and protected browser lifecycle, original-data/privacy coverage, human UI and required local coverage/security/image gates are satisfied.|VERIFIED|Actual backend lifecycle/race assertions and browser create/edit/clear/compare/switch/trade/History/delete/zero cases remain unchanged at277backend/155frontend/314browser input scopes. Original logs retain3691backend,1330frontend and64critical modules100% results. Five fresh exact image reports have HIGH0/CRITICAL0. All28acceptance rows map to concrete assertions/raw evidence. Actual owner UI/native200 responses are retained at365identical render inputs. Full required hosted CI remains a separate pre-merge gate.|

## Supporting plan truths and artifacts

All12 supporting plan truths are verified; none reduces the roadmap contract.
SDK `verify.artifacts` independently passes12/12 artifact declarations across
the four plans, supplemented by the substantive/wiring checks below.

| Plan | Three supporting truths | Status |
|---|---|---|
|01|Authenticated installed-consumer lifetime; finite exclusive Phase15 outputs; complete recovery graph retained with distinct current-only claims.|VERIFIED|
|02|Real original creation/fill/payment replay; closed/sibling/zero invariants; complete exact pre-replay data/tail comparison.|VERIFIED|
|03|Fresh matching encrypted current proof; qualified unchanged-input reuse; exact image/archive/source/cleanup identities without whole-CI claims.|VERIFIED|
|04|Tested operator matrix; full private lifecycle evidence; complete local evidence with provider/release/production boundaries preserved.|VERIFIED|

## Key links and real data flow

| From → To | Substantive wiring | Status |
|---|---|---|
|Campaign → validation runner|Original `qualification_phase`/suite/archive are persisted and forwarded; absent legacy phase remains14. Status/resume inspect the original run.|WIRED|
|Full/current selection → operations|`execute_recovery` selects all seven stages only for full recovery; current-only selects `current0023-cold` and leaves whole/final-CI flags false.|WIRED|
|Cold smoke → authenticated installed consumer|`installed_recovery_verifier` verifies/installs the selected v4 archive and loads its actual adjacent-source consumer for the complete cold context.|WIRED|
|Encrypted restore → exact oracle → original services|Cold branch performs installed verifier checks and original compare, then invokes `replay-restored` only for current0023 on `birja_restore_test` with the required original snapshot SHA.|WIRED|
|Restricted session → real services → before/after projection|Actual TLS is observed before attenuation on the same connection; finite SET ROLE/commit precedes nonprivileged identity checks and bound AsyncSession. Services never run at bootstrap current_user. Finally resets the role. Real database projections supply the result.|FLOWING|
|RUNBOOK/acceptance → assertions/receipts|Support matrix and all28unique requirement rows reference real source families, tests, current/inherited logs and scope; no orphaned requirement or invented test path was found.|WIRED|

The replay adapter truthfully reports `owned-login-set-role`; restored runtime
groups stay NOLOGIN. The migrator is the independent read-only economic oracle.
This is not a newly performed direct runtime-login TLS test. That unchanged
authority/transport coverage is inherited separately.

## Independent raw-evidence checks

- Parsed R5 original status: terminal `passed`, exit0, preflight exit0,
  phase15/suite`recovery-current`,135.998s. Independently rehashed all six bound
  request/claim/status/preflight/command files and read actual retry markers.
- Independently verified canonical archive SHA256
  `bbbec1af156b594f5093ecef8badf918f8b0a7e039dfdb3e486fb8b58823f47a`,
  inode943204/device64512/244357120bytes against the terminal binding.
- Recomputed every current input hash in the277/155/314/139/10reuse groups;
  compared groups remain unchanged. Independently rehashed28successful security
  logs, six recovery logs and the original backend/frontend command log.
- Rehashed all five fresh scan reports and counted raw findings: HIGH0 and
  CRITICAL0 for each. The new runtime is exact
  `sha256:dacbd2c31e69610d179638999281bd91b5d3d1d0ad897473371ab1eda0f961b7`.
- Compared new authority against all five inherited current role/cold/TLS/
  rollback triples; catalogue/object/default ACL values match exactly.
- Independently rehashed all nine prior archive/UI artifacts and checked their
  inode/device/size identities. Final integrity attests original process groups
  and all six exact owned projects empty; no new service operation was run here.
- Verified all365actual current render hashes against the accepted R7 manifest
  and the actual Phase14 owner reply “i approve ui and 200 zoom” on2026-11-22.
  Prior phase records supply the unchanged remaining surfaces; no new approval
  is inferred from capture flags or silence.
- Compared the acceptance table with approved requirements:28unique matching
  IDs; Phase15 claims exactly PSAFE-04/05/06. Checked representative actual
  financial arithmetic, real-lock race and browser metadata/switch/History
  assertions rather than relying on test names alone.

Private evidence roots are `/tmp/birja-phase15-campaign-recovery-current-r5/`
and `/tmp/birja-phase15-plan03/`. The exact scope/hash inventory remains in
`reuse.json` and `final-integrity.json`; this report does not duplicate it.

## Behavioral spot-checks and probes

| Read-only command/check | Actual result |
|---|---|
|`python3 deploy/tests/run-portfolio-validation.py --phase 15 --suite recovery-current --dry-run`|Exit0; Phase15 canonical archive and only current0023-cold.|
|`python3 deploy/tests/run-portfolio-validation.py --suite recovery --dry-run`|Exit0; default Phase14 archive and all seven original stages.|
|SDK `verify.artifacts` on all four plans|All12artifact declarations pass.|
|Source/raw-receipt/hash inspections above|Pass; no new database, browser, image scan or service run.|

No conventional `scripts/**/probe-*.sh` was discovered. Declared current/full
entrypoints were inspected through their safe dry-runs; the actual long proof
is the independently authenticated R5 receipt, not the dry-run output.
No blocking unreferenced debt marker, product stub or disconnected data path
was found in the modified implementation scope.

## Requirements

| ID | Status | Evidence |
|---|---|---|
|PSAFE-04|SATISFIED|Exact encrypted current restore plus actual original-request/frozen/sibling/zero checks; inherited original migrated-data and identity evidence.|
|PSAFE-05|SATISFIED|Authentic installed-source consumer, supported finite runner, tested inherited upgrade/rollback/refusal families and precise operator matrix.|
|PSAFE-06|SATISFIED|Full lifecycle assertion map, actual real-DB/browser/concurrency evidence at unchanged inputs, required local coverage/images/reviews and actual unchanged-screen approvals.|

## Disconfirmation and limits

Source seeding and compiled contracts alone would not establish post-restore
replay; this report uses the actual R5 service execution and before/after
assertions. Old TLS results do not claim execution of the changed replay helper.
The new cold fixture's10000baseline does not replace the distinct original8765
migration check. These possible false-positive interpretations were checked
against source and raw logs; no assigned local requirement remains partial.

R1–R4 and earlier whole-run failures remain failed. Current-only
`whole7=false`/`same_archive_final_ci=false` are preserved. No new full
all-security/browser/seven-stage or hosted-CI pass is claimed; required full CI
must pass before merge. Issue35's original scope/2026-12-17UTC expiry is unchanged;
zero image findings are not dependency remediation. Phase7 live obligations,
provider activation, publication, milestone archival and production remain
separate. No verification override or new risk acceptance was applied.
