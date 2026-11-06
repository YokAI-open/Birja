# 06-15 focused independent plan check

Current verdict: **ISSUES FOUND — 1 BLOCKER,0 WARNING**. Static review only: no source/test/runtime/private/provider actions or commits. Only this new record was written.

Reviewed full15 PLAN/SCOPE, IMAGE-RESEARCH including authorized candidate validation,08 PLAN, LOCAL-GATES, source REVIEW/FIX through clean c8e23fd disposition,07/14 summaries, actual Dockerfiles/Compose/deploy Node consumer, recovery producer/verifier and prerequisite/ops/rollback/CI contracts. SDK plan-structure is valid:3 complete tasks,16 owned files. Root's added backup-snapshot.py/configure-db.sh ownership closes both exact Compose-hash consumer updates found by rg.

## Findings

```yaml
issues:
  - plan: "06-15"
    task: 1
    dimension: key_links_planned
    severity: blocker
    description: "The new recovery Compose registry-index pin is not explicitly connected to the image actually loaded from the independent archive. Task01 authenticates registry/config identities and changes inspect/save to the immutable registry reference, while task03 replays on the already-pulled Docker host. Verifying saved config bytes and then inspecting the loaded config ID does not establish that subsequent Compose startup can resolve its registry-index reference from that archive alone. Existing registry/cache state or an implicit pull can hide missing recovery dependency closure."
    fix_hint: "Keep production registry-index pins, but explicitly define a trusted registry-index/platform-manifest/config-ID mapping authenticated before effects. Recovery clone execution must select the verified loaded config ID (or an equally verified local mapping) with pull disabled, and assert the actual running container image ID/platform matches it. Add behavioral tests that reject registry-resolution/pull fallback after install and actual supplied-artifact execution checks proving the resolved image is the verified loaded config, rather than using pre-existing RepoDigest availability. Use the owned verifier/ops Compose/new image tests as needed; do not delete shared images, clear global caches or require a new privileged daemon. Record the mapping and proof in IMAGE-GATES."
```

This is a bounded archive→loaded image→actual clone wiring gap, not a request for another image subsystem or a claim that every Docker implementation necessarily loses digest metadata. The current acceptance does not distinguish an archive-complete recovery from one borrowing already-cached registry resolution.

## Checks that pass

- **Requirement coverage:** DEPL-01/02 appear in frontmatter and map to secure deploy/recovery prerequisites; existing08..13 retain nightly provider/timer/actual CI/live friend outcomes.15 deliberately delivers measured fixes/enforcement/evidence, leaves requirements-completed empty and08/09 blocked on remaining HIGH/CRITICAL. This is explicit residual blocking, not silent user-scope reduction.
- **Dependencies/ownership:**07/14→15 wave9→08 wave10→09..13 waves11..15 is valid/serial;08 tasks01/02 history is preserved. All actual image-pin and exact Compose-hash source consumers found by the bounded rg are owned. Current ops/rollback fixtures dynamically use verifier constants; old v0.3.1 source and unchanged locks remain compared while its actual image builds from selected current test-builder.
- **Task completeness/producer order:** Three tasks have Files/Action/Verify/Done.15-01 creates image-contract tests before use;15-02 extends them to invoke the actual scanner producer through fake command boundaries and mutation-tests required CI wiring. Behavioral RED is required, not missing imports or source-text assertions alone.
- **Scope:**16 paths are above the raw file-count heuristic, but most are mechanical pin/hash updates. Substantive work is bounded to existing image/provenance logic, legitimate complete-tool cleanup, one stdlib scanner producer/tests and evidence. Three serial tasks and declared45–50% context do not justify a split solely from file count. Optional npm work must fit owned consumers or remain blocked; no new framework is authorized.
- **Image integrity/tool cleanup:** Same-major trixie/glibc, PG18 layout/UID999, non-root runtime, uv pin and application locks are preserved. Entire unused pip/ensurepip distributions may be removed only after working locked builder/runtime proof; no SBOM-only deletion/vendor patch/library stripping. Optional npm requires actual official complete same-major artifact/provenance and independent review, otherwise findings remain blocked.
- **Scanner/CI:** Five exact actual targets, loaded/tagged built stages, pinned scanner, isolated archive/cache mounts, strict HIGH/CRITICAL including unfixed, JSON/DB/scanner/export/inspect errors, continued collection with overall failure, always-uploaded evidence and unchanged image→ci-pass dependency are explicit. Any changed consumed Node toolchain must itself be scanned. No blanket ignore, VEX, fail-open or waiver mechanism is included.
- **Verification derivation:** Task03 requires actual affected builds/runtime/migration/Redis/frontend/audits, complete supplied recovery/roles/TLS/actual-old rollback on one finalized artifact after c8e23fd, final cleanup, actual fresh raw scans and independent bounded code/security review. Prior clean scans/builds/full-suite counts and older archives cannot substitute. Raw expected scan failure is recorded distinctly from successful enforcement tests and blocks08/live advancement.
- **Context/tier/project compliance:** No Phase06 CONTEXT/D-IDs invented; research places distro/tool fixes in image/build pipeline and scan policy in CI. Operations-ledger US$0/26h/latest-only/custody and all later approval gates remain unchanged. No new application feature/migration or app dependency manager is introduced.
- **Research resolution:** Candidate questions were measured by the authorized follow-up; remaining unavailable vendor fixes/dispositions are explicitly preserved as downstream acceptance blockers, not fabricated resolutions.15's bounded objective is achievable without claiming those resolved.

## Nyquist

VALIDATION exists; existing config enables Nyquist. Every task has automated commands, no watch mode or missing producer. Wave9 sampling is3/3. Task03's short automated list is supplemented by mandatory actual build/scan/serial integration actions and measurable done criteria; those cannot be skipped because short contracts pass. New meaningful verification is planned in the created module before invocation. Existing long integrations/scans have bounded time/progress and elapsed-evidence requirements. Parent owns additive validation-map metadata.

Revise the one BLOCKER, then recheck. This record does not authorize image execution/acquisition, source mutation, publication or any provider/production action.

## Revision 1 — current verdict: VERIFICATION PASSED

Re-read the full revised15 PLAN/SCOPE and rechecked the changed recovery execution contract against existing verifier/fixture/CI call shapes. **Current active findings:0 BLOCKER,0 WARNING.** The original issue above is resolved history.

The revised interface,15-01 action/behavior/done,15-03 offline_closure/done and scope now specify the entire missing chain: authenticate retained index/platform bytes and their descriptor links to the selected config digest, hash saved config bytes before effects, load that exact image, resolve fixed recovery Compose by config ID with pull_policy:never and explicit --pull never, and verify actual running Image ID/platform. Production/dev/test retain registry pins; no caller-selected image, interpolation or extra Compose override is introduced. All three exact Compose-hash consumers remain owned.

Import-only tests exercise the actual installed resolution/start consumer through a fake Docker boundary with only the verified imported config ID present, registry reference/RepoDigests absent and zero pull attempts. Missing/wrong IDs, forged mapping and fallback fail. Actual same-final-artifact recovery/rollback additionally assert resolved Compose and running image identity with pulling disabled. Thus success no longer depends on warm registry cache or on Docker load restoring RepoDigests. No shared cache deletion, new privileged daemon or new subsystem is needed.

SDK structure recheck passes with3 complete tasks and unchanged16-file ownership. No new blocker arises from this explicit recovery-only config-ID exception. Previous coverage, serial dependency/ownership, strict five-target scanner/CI, legitimate complete-tool cleanup, actual old-source/lock compatibility, retained final-artifact replay, independent review and honest residual vendor-blocker findings remain satisfied. Known HIGH/CRITICAL still block08/09 and neither deployment requirement is completed by15.

```yaml
status: passed
plans_checked: ["06-15"]
active_issues: []
resolved_issues:
  - dimension: key_links_planned
    original_severity: blocker
    task: 1
    resolution: "Authenticated index/platform/config/saved-byte chain; fixed imported config-ID recovery with pull disabled; import-only zero-fallback consumer tests and actual installed/running image identity assertions in task3."
```

Plan approval only; source implementation, behavioral RED/GREEN, actual builds/scans/replays/cleanup and separate final code/security review remain mandatory execution work. Only this check record was updated; no source/tests/state/runtime/private/provider actions or commits.
