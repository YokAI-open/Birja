# 06-14 focused independent plan check

Current status: PASSED — 0 active blockers or warnings. Initial review: 1 blocker and 1 warning, resolved below. Static review only; no runtime, Docker, provider, private-state or source changes. Reviewed prerequisite 14, scope and 07 handoff against Phase06 goal, DEPL-01/02, operations policy, research/patterns/validation, completed03..06 summaries and existing public lock/recovery/fixture interfaces. SDK plan-structure: valid, three complete tasks, six files. Completed plans remain complete.

Coverage:14 supports DEPL-01 secure rollout through14-01/03→07 and DEPL-02 recovery through14-02/03→08/09/12. Remaining live friend, nightly off-server, CI and role/TLS acceptance remains downstream. Dependencies06→14(wave7)→07(wave8)→08..13(waves9..14) are serial and acyclic. No Phase06 CONTEXT exists; historical domain/manual-deploy/DNS/certificate authority and US$0/latest-only/26h/custody policy are preserved. Architectural responsibilities remain privileged host operations. Research inputs have explicit resolved planning dispositions and later human gates.

| Task | Wave | Automated producer/check | Status |
|---|---|---|---|
|14-01|7|Creates test-deploy-prerequisites.py; --locks|Planned before use|
|14-02|7|Extends --evidence; existing backup/restore safety|Planned before use|
|14-03|7|Extends --fixtures; existing real recovery/roles/TLS|Planned before use|

Nyquist: VALIDATION exists;3/3 tasks have automated checks, no watch flags, no missing producer. Fast suites explicitly require behavioral RED, not missing imports. Long existing integration gates are acknowledged and require measured durations/progress; no claim of execution passes. Scope is within numeric thresholds; no additional split is justified by task/file counts alone.

Positive contracts explicitly cover root-private atomic evidence, failed latest attempts and cleanup invalidation, actual remote exact-snapshot presence, nonfuture/fresh timestamps, source/revision/config/tool/bundle identity, source captured before mutation, immutable same installed recovery artifact, fixed separate clone with unchanged Compose SHA/check_running, private output, budget accounting and ordinary nightly status without a full nightly restore. Existing negative controls must be retained. No new live/secret authority is inferred.

```yaml
issues:
  - plan: "06-14"
    task: 1
    dimension: cross_plan_data_contracts
    severity: blocker
    description: "The shared-lock contract does not select one synthetic inode across its actual callers. configure-db.sh and provision-db-tls.sh use <root>/operation.lock; backup Job.lock uses <root>/state/operation.lock with the current fixture config. Extracting a path-taking verifier preserves this mismatch, so the same inherited deploy lock is rejected by one side and the continuous synthetic rollout cannot prove the required shared serialization."
    fix_hint: "Explicitly normalize the synthetic lock location in14-01 (for example the validated synthetic root/operation.lock derived from config root, retaining the fixed production path). Specify one parent-held FD passing through actual role, TLS, backup and restore/gate callers in one fixture root; verify no recursive acquisition, parent ownership survives, and independently opened contention rejects across all callers. Keep the path closed to caller-selected arbitrary overrides."
  - plan: "06-14"
    task: 3
    dimension: key_links_planned
    severity: warning
    description: "Supplied-archive compatibility is implicit. The current trusted verifier checks exact inventory, checksums, provenance and runtime commands, but a valid pre14 artifact lacks --isolated-clone, durable evidence and recovery-gate. It can pass verification and Docker installation before the new hook discovers the incompatible interfaces."
    fix_hint: "Define an explicit required recovery capability/profile version for new hooks in verify-restore.py package/verify/install; validate it using the transferred trusted verifier before Docker load/install. Add a complete structurally valid older-profile supplied archive negative with zero Docker/install/default-builder calls, plus successful current-profile supplied/default artifact runs. Document old artifact rejection rather than silently replacing it."
```

Revise the BLOCKER before execution and recheck. Both changes fit14's existing file ownership;07 retains orchestration/overlay/rollback-runner ownership. This review does not reopen historical validation task/wave counts or rename completed artifacts.

## Revision 1 — current verdict: VERIFICATION PASSED

Re-read the complete revised14 PLAN/SCOPE and checked both corrections against the unchanged existing interfaces and07 handoff. Current active findings: **0 BLOCKER,0 WARNING**. The issues above are retained as resolved review history, not current execution blockers.

- **BLOCKER resolved:**14's interface,14-01 action/behavior and14-02 done now select validated config-root/operation.lock for every synthetic caller, preserving the fixed production path and forbidding arbitrary override. They require one parent-held FD through actual role/TLS/backup/restore/gate callers, cross-caller independently opened contention, and surviving parent ownership after duplicate closure. This closes the concrete two-inode gap rather than merely sharing a verifier function.
- **WARNING resolved:**14-03 now owns verify-restore.py explicitly and defines authenticated deploy-recovery-v2 inventory plus trusted required_profile/--require-profile checks. Specialized hook and transferred installer must reject missing/unknown/legacy capability profiles before runtime probes, Docker, extraction, installation or archived execution. Generic legacy support remains distinct. A complete valid older artifact negative asserts zero side effects/fallback, and default/current supplied archives must positively exercise the new interfaces.

SDK plan-structure recheck remains valid:3 complete tasks,6 unique files, no structural errors or warnings. The added profile work stays within the existing runtime file inventory and serial task ownership; no new subsystem/dependency, source lifecycle authority or cross-plan ownership conflict is introduced. Earlier findings on requirement coverage, meaningful test producer order, source-before-change binding, immutable same artifact, strict clone safety, ordinary nightly status without full restore, budgets and approval boundaries remain satisfied. No new blocker identified.

```yaml
status: passed
plans_checked: ["06-14"]
active_issues: []
resolved_issues:
  - dimension: cross_plan_data_contracts
    original_severity: blocker
    task: 1
    resolution: "Canonical validated synthetic root lock plus actual cross-caller FD/contention tests; restore/gate extension required in task2."
  - dimension: key_links_planned
    original_severity: warning
    task: 3
    resolution: "Trusted required deploy-recovery-v2 capability checks before side effects, complete legacy negative and current-profile positive interface tests."
```

This is plan approval only. Runtime RED/GREEN results, real integration cleanup, actual provider/live evidence and DEPL completion remain execution work. Only this review record was changed; no source/tests/state/commits or live/private operations were performed.
