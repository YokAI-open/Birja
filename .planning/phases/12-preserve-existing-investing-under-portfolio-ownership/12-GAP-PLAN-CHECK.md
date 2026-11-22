---
phase: 12-preserve-existing-investing-under-portfolio-ownership
mode: gap_closure
status: passed
plans_checked: [12-29, 12-30, 12-31]
revision_checked: 3
blockers: 0
warnings: 0
execution_prerequisite: owner_accepted_exact_advisory_policy_and_fresh_recovery
phase_completion: blocked
---

# Phase12 Gap Plan Check

## Current Verdict — Revision3: VERIFICATION PASSED

The sole revision2 blocker is resolved. Plan31-02 now explicitly requires an
actual fresh complete --suite recovery at the same reviewed frozen source that
passes31-01, because Plan30 modifies the retained PORTFOLIO_PAYLOAD_V1 runner.
Its action requires preserving the prior entire campaign/archive and raw
receipts privately, a new immutable archive through all seven serial stages,
source/image/CORE/UNITS/payload checks, exact financial/TLS authority parity,
final same_archive_final_ci=true and exact-owned cleanup. Its automated command
is the real complete recovery runner; its acceptance criteria require that
actual proof before independent final verification. The exception context now
states the same required fresh-proof boundary.

The narrowed advisory acceptance remains scoped only to issue35, exact artifact
hashes and expiry; no package installation or additional advisory exception is
introduced. All six task contracts and the earlier revision2 non-recovery
checks remain applicable. This bounded recheck found **zero blockers and zero
warnings**; git diff --check passes after EOF whitespace correction.

```yaml
issues: []
```

This is plan verification, not completed execution or a clean npm audit claim.
Phase completion remains pending actual whole security under accepted risk,
new whole recovery and independent goal verification. Only this report was
updated; no implementation tests, network operations or commits were performed.

## Historical Revision2: ISSUES FOUND (Resolved by Revision3)

The November17 owner decision in12-EXCEPTION-CONTEXT.md supersedes the earlier
no-exception requirement **only** for GHSA-fc5q-39xc-vjpf. Issue35 is recorded at
https://github.com/YokAI-open/Birja/issues/35. No dependency installation or
additional package authorization is needed for the revised policy-only work.
Earlier pass sections below describe superseded revisions0/1, not the current
plans. The current review has **one BLOCKER and zero warnings**.

### BLOCKER — Planned runner change necessarily changes packaged recovery input

Plan30 explicitly modifies deploy/tests/run-portfolio-validation.py to use the
new audit helper. That runner is not merely an unretained CI harness:
deploy/verify-restore.py:65 explicitly includes it in PORTFOLIO_PAYLOAD_V1.
The runner's authenticate function compares every CORE, UNITS and
PORTFOLIO_PAYLOAD_V1 member from the archive with current bytes and refuses any
difference. Therefore the planned diff cannot retain the d9da271 whole recovery
as qualification of unchanged recovery payloads. Plan31-02's policy-only reuse
branch is infeasible for this concrete plan set, even though application and
financial runtime bytes can remain unchanged.

**Required revision:** Require an actual fresh complete --suite recovery at the
same frozen source qualified by31-01. Preserve the old owned campaign/archive
and raw receipts under a distinct private path before recreating the exclusive
fixed proof directory; record a new archive SHA and all seven stages with
current/retained/source/image/authority guards and final same_archive_final_ci.
Do not repackage or relabel the old archive. Use the actual complete recovery
command in automated verification; contract tests may supplement it. No new
implementation or production scope is introduced by this required proof.

### Other Revision2 Checks

All six tasks retain concrete nonempty read_first and acceptance_criteria,
files/action/verify/done. The28→29→30→31 waves18–21 remain valid. Plan29
records exact owner risk acceptance, expiry2026-12-17UTC, original manifest and
lock hashes, exposure reassessment and issue35 without claiming remediation.
Plan30 uses Node built-ins and full raw npm audit, forbids omit-dev, constrains
the exact advisory and inherited HIGH graph causes, and requires fail-closed
critical/unrelated HIGH, malformed/network/schema, hash/expiry and unrooted
cycle cases. The existing cyclic report is a positive fixture; cycle-only and
mixed-advisory roots are negative fixtures. Complete output must say accepted
risk, not clean. CI and the local runner consume the same helper and require
independent source/security review before full qualification. These controls
are coherent planning requirements, not a reviewed implementation yet.

Financial/runtime scope, original owner UI/native200 acceptance and Phase7
deferrals remain preserved. All seven Phase12 IDs still have retained
implementation plus final qualification coverage. No broad gate waiver, package
change, provider operation, publication or deployment is authorized.

```yaml
issues:
  - plan: "12-31"
    task: 2
    dimension: cross_plan_data_contracts
    severity: blocker
    description: "Plan30 changes run-portfolio-validation.py, an exact PORTFOLIO_PAYLOAD_V1 archive member, so Plan31 cannot retain d9da271 recovery through unchanged packaged-input equivalence."
    fix_hint: "Require fresh actual complete --suite recovery at frozen qualified source; preserve prior archive privately and record the new seven-stage same-archive proof."
```

This bounded static revision2 check changed only this report. No implementation
test, package install, network/provider operation or commit was performed.

## Historical Revision0/1 Findings (Superseded)

## VERIFICATION PASSED

The three gap plans form a valid **conditional** repair and qualification
route. This is approval of the plan structure and controls, not evidence of an
available patch, package approval, successful qualification or phase completion.
The saved official evidence still has no patched picomatch release. Plan29
must stop without completion if its bounded refresh finds no eligible candidate;
30 and31 cannot execute before29 succeeds with exact owner authorization.

This independent checker reviewed the new plans against the authoritative
12-VERIFICATION gap, current dependency review, approved requirements/context,
research responsibility map, pattern/validation/UI contracts and accepted owner
responses. Existing01–28 coverage and completed evidence were retained rather
than turned into new implementation work. No application, test, dependency
installation, network, provider or production operation was performed. Only
this report is written; global state and the plans are unchanged by this role.

## Plan and Dependency Summary

| Plan | Tasks | Wave | Precondition | Verdict |
|---|---:|---:|---|---|
|12-29|2|19|Completed28 and existing gap evidence|Valid; real candidate, full graph/artifact review and exact blocking approval; no_candidate halts|
|12-30|2|20|Successful29 and bound approval|Valid; exact manifest/lock install, both affected paths remedied, strict audit and frontend compatibility|
|12-31|2|21|Successful audited/reviewed30|Valid; actual complete all-security then one new complete same-archive recovery and final independent verification|

28 is wave18. The existing28→29→30→31 dependency chain is acyclic and waves
increase correctly. Shared evidence paths have sequential ownership. All three
plans have gap_closure:true, required artifacts/key links and concrete STRIDE
mitigations. Six SDK checks independently passed: frontmatter.validate and
verify.plan-structure for each plan, with no errors or warnings.

## Requirement and Decision Coverage

| Requirement | Preserved implementation plans | New qualification coverage |
|---|---|---|
|PFUND-03|01–04,06–08,12–14,16–18,26–27|31 retains no-grant and exact financial recovery|
|PFIN-02|05,08,10–12,15,20–21,26–27|30 frontend regression;31 complete unchanged execution proof|
|PFIN-03|01,05,10–11,20–21,24,26–27|30 frontend original retry checks;31 full regression|
|PCTX-01|09,14–15,19,22–28|30–31 render/behavior compatibility and honest accepted-packet provenance|
|PVIEW-03|14–15,20,22,25–28|30–31 complete private History regressions|
|PSAFE-02|07–09,15,19,22–23,26–28|31 full identity/authorization regression|
|PSAFE-03|01–07,11–13,16–18,26–27|29–31 common strict dependency/security/recovery qualification|

The plan set claims precisely the seven assigned IDs; no requirement is dropped
or marked complete by planning. The four-source audit correctly distinguishes
its local C01–C10 labels from source decision IDs. Locked money, restricted
roles/TLS, explicit owned targeting, no fallback, original-receipt identity,
freeze-compatible foundation and current-revision recovery obligations remain.
Naming/creation/descriptions/comparison stay in13, public deletion in14, and
full lifecycle acceptance in15. Phase7's six deferred requirements and consumed
manual campaign remain outside this work; stock activation stays gated.

## Dimensions

| Dimension | Finding |
|---|---|
|Requirement coverage|PASS: all seven IDs retained in original work and31;29/30 focus common qualification|
|Task completeness|PASS: every task has concrete files/action/verify/done; explicit approval checkpoint is nonautonomous and blocking|
|Dependency correctness|PASS:28→29→30→31 with waves18→19→20→21|
|Key links|PASS: lock graph→candidate review→hash-bound approval→exact install→actual complete runner evidence|
|Scope sanity|PASS: two tasks per plan, three declared paths each; no app/schema/toolchain migration bundled|
|Verification derivation|PASS: complete security outcome and exact finances/recovery, not a count of performed tasks|
|Context compliance/reduction|PASS: existing decisions and accepted UI/native200 retained; no feature scope reduction|
|Architectural tiers|PASS: dependency repair stays frontend manifest/lock; recovery remains existing deploy proof tooling; no financial authority moves|
|Nyquist|PASS: existing validation plus gap coverage supplement; every task includes automated evidence; full frontend/security/recovery are explicit long-proof exceptions|
|Cross-plan contracts|PASS: ready/base/prospective/review hashes and exact approval bind29→30; frozen repaired source binds30→31|
|AGENTS/CLAUDE compliance|PASS: existing npm/locks, strict audits, serial isolated DB/TLS, exact money, local-only publication boundary preserved|
|Research resolution|PASS: original design questions resolved; absent external patched artifact is explicit gated prerequisite, not a guessed implementation answer|
|Pattern compliance|PASS: existing runner/qualification and immutable evidence patterns reused; no new product files needing different analogs|

## Command and Acceptance Checks

Static manifest inspection confirms lint, typecheck, format:check, test and
build scripts exist. In particular, format:check is prettier --check .; its use
does not invent a missing script. test is vitest run, so the coverage command
does not enter watch mode. npm ci and package-lock-only preparation disable
lifecycle scripts and audit side effects until their explicitly planned gates;
any genuinely needed lifecycle execution requires exact prior review/approval.

Actual run-portfolio-validation.py supports --suite all-security and --suite
recovery. The former derives the exact critical coverage command from CI,
includes full npm audit with dev dependencies, complete browser execution and
five actual strict image scans, and uses a stripped synthetic environment.
The latter creates an exclusive fixed directory and the one uncompressed USTAR
archive, authenticates source/archive/image identities between seven serial
stages and requires final TLS authority parity. Plan31 preserves old evidence
before creating that new directory; it does not invent an --archive option.

No guessed fixed version, audit-level reduction, omitted tooling, force fix,
unreviewed override/fork or automatic major downgrade is authorized. Both
currently affected lock paths must be absent or genuinely fixed, including
compatible parent constraints. A merely higher version is insufficient. A
replacement/major migration is an explicit replan boundary.

Current failed complete all-security remains FAILED. Separate browser/image
diagnostics cannot be assembled into a whole-run pass. Existing owner UI and
native200 responses remain accepted; a changed dependency graph must be
disclosed and assessed without falsely claiming unchanged build inputs or
automatically demanding duplicate acceptance.

## Structured Issues

```yaml
issues: []
```

## Revision1 — Deep-Work Task Contracts

Rechecked the planner's six added per-task read_first and acceptance_criteria
blocks against the already reviewed actions and verification commands. All six
tasks have both nonempty fields. Required reads name the actual policy, input,
producer or prior-task evidence for that task; future receipts/summaries are
consumed only after their dependency creates them, and existing evidence is
read before append. The criteria specify observable outcomes rather than
restating task completion:

| Task | Required-read boundary | Measurable acceptance |
|---|---|---|
|29-01|Rules, authoritative gap, saved dependency/research evidence and current manifest/lock|Unchanged base hashes; structured ready/no_candidate; exact candidate/hash/zero-affected-path fields; no_candidate stops before checkpoint|
|29-02|Rules, produced candidate/review and research addendum|Ready receipt, presented hashes and exact explicit owner approval; refusal/missing response/hash drift blocks30|
|30-01|29 summary, review, candidate, research and current manifests|Exact approved prospective hashes installed; real ci/tree/audit exits0; every affected path remedied and unrelated bytes unchanged|
|30-02|Repair/review, accepted human evidence, manifests, actual CI/runner|All full frontend checks exit0 at unchanged inventory/thresholds, independent review clean and policy hashes unchanged|
|31-01|Successful30 evidence, existing qualification/UAT and actual CI/runner|Actual complete all-security exits0 with equal source/lock hashes, full required gates and raw receipts/cleanup; no assembled partial pass|
|31-02|Actual security receipt, prior recovery/review/goal evidence and recovery consumers|Prior31-01 pass; actual complete recovery exits0 with one unchanged new archive, seven stages/parity/final marker and cleanup; independent goal review before closure|

Revision1 changes neither the reviewed action/verify behavior nor conditional
scope, waves or approval authority. No new blocker or warning was found.
Deep-work task-contract compliance: **6/6**. This bounded recheck performed no
source/package mutation, implementation test, network operation or commit.

Planning can be recorded as checked. Execution is conditional on a legitimate
candidate and exact approval; phase status remains blocked and all requirements
stay pending until actual qualification and independent goal verification pass.
