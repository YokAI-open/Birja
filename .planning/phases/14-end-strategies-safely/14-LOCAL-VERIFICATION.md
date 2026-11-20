# Phase 14 — Local qualification

Plan18 is **incomplete**. Whole-security R1 failed; final recovery has not
started. All results below are local; no hosted CI, publication,
deployment or human acceptance is inferred.

Execution began2026-11-20T08:03Z on `feature/milestone-v1.2`, initial
HEAD `426435789f8f41dea0b3fe9a4c0852c85b314a46`. SDK initialization confirms
17/19 plans have summaries; Plans18/19 remain incomplete. All seven whole
Phase14 requirements remain pending. The parent owns shared STATE/ROADMAP and
requirements; this executor does not advance them.

## Independent reviews

Distinct code, security and UI role passes are required before qualification.
The configured collaboration limit permits one reviewer at a time in this
session, so the roles run sequentially. No DB/browser campaign or source edits
run while reviewers are active. Existing per-plan findings and their repair
history remain in their original reports.

The initial independent code pass identified a Plan16 source-inventory blocker:
`security_sources` checked links only at the final path component and could
follow a linked ancestor while reading cached source paths. The parent has
authorized a narrow descriptor-relative no-follow repair in the runner and
meaningful controlled temporary-directory regressions, after all review passes
return. Finding disposition and final independent re-review belong in
`14-REVIEW.md`; no passing security campaign is claimed before that repair.

### Source-integrity repair and independent disposition

RED `407a6c0` reproduces the missing directory/root/open-race refusals with
controlled temporary trees. GREEN `d2e8885` opens every root/ancestor directory
and ordinary file with no-follow descriptors, validates regular-file identity,
and rechecks parent/root/ignore metadata. Safe in-root leaf links bind link
metadata without reading target bytes. A replacement after opening the parent
reads only the original descriptor's controlled bytes, then refuses the changed
pathname. No real outside source or credential is read by these regressions.

Final frozen tests:33 runner/supervisor contracts pass8.250s and94 CI operations
contracts pass23.865s; scoped Ruff F/E9 and whitespace checks pass.22 image/source
contracts passed5.684s before the final target-directory metadata recheck; image
binding code was unchanged. An earlier CI run passed94 in24.352s but overlaps
the last edit and is retained as diagnostic history, not the final frozen run.
Logs are `/tmp/birja-phase14-campaign-plan18-repair/{source-red,source-frozen,ci-frozen,image-final}.log`.

Independent code re-review resolves CR-01 atd2e8885 with0 blockers/0 warnings.
Independent security re-review closes T-14-16;36/38 threats are closed, with
only actual whole Plan18 qualification and separate actual Plan19 outcomes
pending. Independent UI review scores24/24 with0 blockers/0 warnings, inspecting
ten actual R5 PNGs and verifying365 source hashes and419 artifact hashes.
Original findings and all earlier evidence remain preserved in their reports.

Strict current-source/artifact/exact ZIP verification returns
`CURRENT SOURCE AND ARTIFACTS VERIFIED` after the repair. Current ZIP remains
`372c94808a6741f410522f1559221d5d2b71b02aefaa95ebe417a15911bffdfe`.
Phase13 recovery/UI, Plan15 R4, Plan16 R3 and historical R1/R3 UI archive hashes
match their original recorded values. Canonical Phase14 recovery directory is
absent before qualification. Both human acceptance flags remain false.

## Required qualification order

1. Resolve independent review findings and commit reviewed nonplanning inputs.
2. Verify the current Phase14 UI packet and preserved prior archives.
3. Run actual bounded preflight and one complete uninterrupted all-security
   child through the one-shot supervisor with an exclusive private receipt path.
4. Only after whole security passes, run one fresh uninterrupted seven-stage
   recovery at the same source and exact canonical archive.
5. Verify unchanged source, exact image/archive bindings, owned cleanup and
   current UI evidence again; record actual commands, hashes, times and counts.

The literal children remain:

```text
python3 deploy/tests/run-portfolio-validation.py --suite all-security
python3 deploy/tests/run-portfolio-validation.py --suite recovery
```

Earlier bounded or partitioned proofs are supplemental evidence only. Actual
owner UI acceptance and genuine desktop native200% remain separate Plan19 gates.

## Whole security R1 — failed, preserved

Frozen candidate: `5e0803ab088da61a8c2818c99441c021c12b3d93`, including reviewed
source-integrity repair `d2e8885`. The literal standalone preflight passed:

```text
python3 deploy/tests/run-portfolio-validation.py --suite all-security --preflight
python3 deploy/tests/run-portfolio-campaign.py --suite all-security --receipt-dir /tmp/birja-phase14-campaign-security-plan18-r1
```

The original supervisor2000014/startticks2916395351, runID
`88b4e1a94f9f4ccb8869603eaccbc901`, passed its own preflight, then launched
child2002474/startticks2916399426 with literal argv:

```text
/usr/bin/python3 /home/YokaiExchange/deploy/tests/run-portfolio-validation.py --suite all-security
```

The command returned1. The supervisor's terminal elapsed time is **5027.363s**,
started1795163212.4036775 and finished1795168239.7665746. Backend static gates
passed; pytest completed **3651 passed,2 failed,118 warnings in4975.79s**.
Overall coverage reached **99.48%**. This is **not a whole-security pass**.
The separate100% critical command, frontend, browser, audit and image gates
were not reached. Recovery has not started and no canonical14 archive exists.

Both failures are retained `test_stock_quotes.py` cases:
`test_genuine_post_split_event_acquires_local_current_units` and
`test_quote_waiting_for_split_binds_committed_units[True]`. Their collection-time
clock produced one-hour action authority; these tests executed more than an
hour later. Actual SQL correctly refused expired authority. No price, epoch,
lock or freshness assertion is waived.

The same run exposes missing defensive critical branches in the new closure
service, closure ownership proof and final default-ACL admission check. These
need meaningful proof before a fresh whole command. Overall99.48% does not
replace the100% critical gate.

All1802 frozen tracked hashes stayed identical. Independent terminal checks
found no live original supervisor/child group and no containers, networks or
volumes for either `birja-test` or `birja-p14-16-preflight`. Request, claim,
status and log hashes plus exact cleanup inventories are preserved in
`/tmp/birja-phase14-campaign-plan18-repair/r1-terminal-integrity.json`.
Original receipts/logs remain in the exclusive R1 campaign directory. Its
coverage data and JSON were preserved as `r1-backend.coverage` and
`r1-coverage.json` before focused diagnostics. Nothing was overwritten or
presented as passing qualification.

## Authorized repair and focused evidence

Commit **`a21eae3`** contains the parent-authorized three-file repair:

- `test_stock_quotes.py` refreshes scenario time per test. Time-dependent
  parameter values are evaluated inside each case against that fresh time,
  preserving future+1s, stale120s, expiry equality and prior-date semantics.
- `portfolio_closure.py` uses an explicit counter and `while True`, preserving
  exactly three total40001 attempts, rollback before each retry, and one
  attempt for40P01/other database errors. No pragma or exclusion was added.
- `test_portfolio_closure_critical.py` adds real-session input/session/HTTP
  refusals, actual PostgreSQL40001/40P01 fault handling, current transaction/
  isolation/advisory-gate checks, genuine retained-boundary acknowledgement,
  and transactional evidence/default-ACL negatives with rollback and original
  financial/catalogue equality. No execute result or financial payload is
  fabricated. Privileged corruption is confined to the owned test transaction.

Focused R1 selected128 cases:125 passed and three new negative fixtures failed
in599.02s (605.804s receipt). All43 stock-quote cases and existing closure API,
stock, clock and actual first-buy retry regressions passed. Two new corruption
fixtures hit PostgreSQL's pending-trigger ALTER refusal; the final-default
race tried to patch a read-only connection instance method. After the guarded
run ended and cleanup was verified, test-only fixes first validated queued
deferred links and used class-level instrumentation scoped to the exact real
connection. Focused R2 reran only those three cases: **3 passed25.36s**,
31.555s receipt, source unchanged, all owned resources empty.

Independent scoped review found no production blocker and one clock-parameter
warning. That warning was repaired by delaying parameter evaluation; an
independent read-only re-review resolves it with **0 blockers/0 warnings**.
This scoped review does not replace final full-source/security qualification.

Final focused R3 passed **69/69 in203.06s**,209.605s receipt: all24 new critical
tests, all43 quote tests, actual public HTTP closure-quota behavior and the
actual first-buy whole-transaction retry regression. Source stayed unchanged;
all owned containers, networks and volumes are empty. Scoped Ruff, formatting,
service mypy and whitespace checks pass. Raw evidence:
`/tmp/birja-phase14-campaign-plan18-repair/focused-r{1,2,3}.{log,json}`.

## Precise continuation gate — Plan18 remains incomplete

The returned-row guard at `portfolio_closure.py:107` remains a critical-coverage
scope decision. Authenticated immutable0023 SQL returns the submitted root,
finite outcome and PostgreSQL boolean; valid calls cannot exercise its invalid
branch. No fake execute result, invented database outcome or coverage waiver
was used. The parent was asked before any additional protected-source change.

Recommended concrete scope: extract this existing validation into a private
pure validator, invoked unconditionally on the real SQL row before proof or
commit. Pure argument tests can exercise invalid ID/outcome/replay types while
existing real-SQL tests verify production wiring. This preserves the defensive
guard and avoids modifying database authority. **It is proposed, not approved
or implemented.** The parent execution thread became unavailable before that
additional scope decision was delivered.

After the decision: implement only approved scope, verify meaningful affected
tests and all64 critical paths, obtain independent re-review, and freeze the
final committed source. The backend service edit changes a render input, so
the exact R5 UI packet must remain preserved and new current-source evidence
must be generated/verified through the accepted capture tool and190 offline
layouts. Do not forge provenance or inherit human acceptance. Then run a new
exclusive complete all-security command; only after it exits0 run fresh
seven-stage recovery at the same frozen source and one exact new archive.

Actual current packet verification after commit `a21eae3` refuses with
`ValueError: Source drift`, as expected. Log:
`/tmp/birja-phase14-campaign-plan18-repair/current-ui-after-repair.log`.
R5 ZIP remains exactly
`372c94808a6741f410522f1559221d5d2b71b02aefaa95ebe417a15911bffdfe`;
canonical recovery directory remains absent. This refusal is not a new packet
or acceptance result.

No whole task, requirement, recovery, owner UI or native200 result is complete.
No Plan18 SUMMARY is created because it would misrepresent disk progress to
the SDK. Shared STATE/ROADMAP/requirements remain parent-owned. Existing issue35,
dependencies/image pins, historical migrations/profiles, prior archives,
production/provider state and unrelated `.claude/` are preserved. Nothing was
pushed, merged or deployed. No test lane remains active.

## Resumed approved validation repair

The parent resumed execution and explicitly approved the proposed private pure
validator. Updated `AGENTS.md` defensive-review instructions at`fb39f0f` were
read; review and verification stay focused on fixes, ordinary validation and
existing isolated integration checks.

Commit **`48aec5b`** extracts the exact existing returned-field predicates and
error into `_validate_closure_result`. The service calls it unconditionally on
actual SQL fields before proof or commit. The SQL, authority, rollback and
three-attempt40001 retry policy are unchanged. Nine ordinary argument cases
cover the two finite outcomes, replay booleans, original-ID mismatch and invalid
field values without replacing database results.

Focused R4 passes **91/91 in297.16s**,303.956s receipt: the prior69 cases,
nine pure validator cases and13 retained closure API cases. Current closure
service coverage is **63 statements/18 branches,100%/100%**, zero exclusions.
A source-bound diagnostic gap audit also identified two developer-bootstrap
refusal branches. Four ordinary unsupported-revision argument cases and a real
owned-transaction final-default check were added in the same critical test file;
all driver query results remain real. Focused R5 passes **6/6 in6.59s**,
12.839s receipt, including the existing positive final-SQL authorization check.
Both runs retain unchanged-source and empty owned-resource receipts.

The final diagnostic coverage-gap audit covers all64 critical files with no
remaining statement/branch gaps. It is explicitly `qualification:false`: only
unchanged source may use preservedR1 plus focused evidence, and the edited
closure service uses fresh focused evidence. It does not relabel failedR1 or
replace the required fresh literal whole-command and critical gates.
Evidence: `/tmp/birja-phase14-campaign-plan18-repair/`:
`focused-r{4,5}.{log,json}`, corresponding coverage JSON and
`pre-r2-coverage-gap-audit-final.json`.

Ordinary independent code review accepts the final scoped repair with
**0 blockers/0 warnings**, preserving original history in`14-REVIEW.md`.
Scoped Ruff/format/mypy and whitespace checks pass. Final source is committed;
the next step is preserving R5 and generating genuine current-source UI
evidence before freezing and starting a new whole security run. The earlier
scope-decision checkpoint is resolved; whole qualification remains pending.
