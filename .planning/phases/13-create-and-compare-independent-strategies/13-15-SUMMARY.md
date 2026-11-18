---
phase: 13-create-and-compare-independent-strategies
plan: "15"
subsystem: testing
tags: [coverage, qualification, recovery, source-authentication, restricted-roles]
requires:
  - phase: 13-03
    provides: Exact current0020 bootstrap and schema admission
  - phase: 13-05
    provides: V2 recovery consumer and current/retained smoke selection
  - phase: 13-13
    provides: Integrated management and explicit portfolio navigation
  - phase: 13-14
    provides: Independent newly created strategy accounting evidence
provides:
  - Exact61-module critical inventory retaining every original60 member
  - Explicit required browser journeys with missing/symlink refusal
  - Current0020 and immutable0017 seven-stage same-archive qualification graph
  - Genuine fresh0020 TLS program and measured fresh/upgraded authority parity
  - Explicit current test provisioning without weakening retained migration oracles
affects: [13-16, 13-17, 13-18]
tech-stack:
  added: []
  patterns: [finite revision profiles, authenticated stage finally guards, independent authority fingerprints]
key-files:
  created: [deploy/tests/test-portfolio-validation-contracts.py]
  modified:
    - backend/tests/test_critical_coverage_config.py
    - .github/workflows/ci.yml
    - CLAUDE.md
    - deploy/tests/run-stock-browser.py
    - deploy/tests/test-portfolio-browser-contracts.py
    - deploy/tests/run-portfolio-validation.py
    - deploy/tests/test-db-operations.sh
    - deploy/tests/test-rollback-db-security.sh
    - backend/tests/conftest.py
    - backend/tests/test_migrations.py
    - deploy/tests/ops-fixtures.py
    - deploy/tests/portfolio-smoke.py
    - deploy/tests/test-portfolio-smoke-image.py
    - deploy/tests/test-ci-ops.py
    - deploy/tests/test-dev-bootstrap.py
    - deploy/verify-restore.py
key-decisions:
  - "The final graph packages through the explicit V2 producer; historical V1 packaging and immutable0017 meanings remain unchanged."
  - "Fresh0020 migrates directly from an empty schema and returns measured catalogue/ACL hashes, without resetting into the upgraded fixture."
  - "Partial-schema application refusal is distinct from the migration client's finite supported revision set."
requirements-completed: [PSAFE-07, PFUND-02]
duration: approximately21min
completed: 2026-11-18
---

# Phase 13 Plan 15: Critical Gates and Revision-Aware Qualification Summary

**The qualification tooling requires management coverage and browser journeys, authenticates a V2 current0020/retained recovery graph, and compares actual fresh/upgraded authority instead of accepting omitted stages or stale source.**

## Performance and Task Commits

Approximately21minutes on2026-11-18;2/2 tasks,17 implementation/test/configuration files plus this summary.

- Task1 RED `2f58012`, GREEN `664ef31`: require and enforce the management transport and explicit browser inventory.
- Task2 RED `6ec397f`: reproduce old archive/stage selection, missing failed-stage authentication, missing fresh setup and incomplete command inventory.
- Task2 fixture RED `6bc04a9`: reproduce the stale0017 migration-head expectation and specify exact current authority.
- Task2 retained-writer RED `6143e68`: require the genuine old consumer's successor refusal.
- Required-journey RED `1ecbb45`: expose missing/symlinked specifications before Playwright can silently ignore an unmatched pattern.
- Task2 GREEN `c80eb85`: implement current/retained recovery graph, source guards, genuine fresh TLS program, old-writer refusal and current fixture bootstrap.
- Dev-diagnostic RED `986c51d`, GREEN `e1bdfa5`: retain custom-baseline economic assertions under actual current authority.

All RED commits precede their corresponding implementation. The inventory RED browser command actually failed at the missing strategy journey and missing inventory function. The current head probe actually failed against the installed Alembic head. No artificial application defect or full qualification pass was manufactured.

## Delivered Changes

CI, CLAUDE and the independently asserted critical tuple agree on61 modules: all original60 plus `app/api/v2/portfolio_management.py`. Overall80 and critical100 with branch coverage remain unchanged. Existing normalization, financial, authorization and shared valuation modules remain covered by their original entries.

The browser runner explicitly lists all11 retained specs and the new `portfolio-strategies.spec.ts`; the portfolios selector includes both ownership and strategies. Every required spec must be a real non-symlink file before stack creation. Plan16 owns the new strategy spec: its absence currently blocks real full/portfolio browser execution intentionally. Contract doubles validate commands and failure cleanup; they are not browser receipts.

The security command graph retains complete backend/frontend tests, overall/critical coverage, raw dependency audits, browser execution, builds, in-image smoke and all five exact image scan policies. Existing offline operations gates, real recovery contracts and ordinary dev-bootstrap qualification remain explicit commands. The environment strips provider/private Compose inputs, supplies fake prices/console email and disables uv synchronization/downloads. Source hashes are checked before and after commands, including failed commands, and owned test-stack cleanup remains in finally. New browser/validation contracts are included in the existing CI contract loader.

Recovery uses a new exclusive `/tmp/birja-phase13-proof/recovery.tar.gz`, the explicit `backup-snapshot.bundle_package_v2` producer and required deploy-recovery-v3 profile. Historical V1 packaging is unchanged. The exact consumer CLI admits only the two named v2/v3 profiles. Seven serial stages are image-transition; retained-roundtrip, including real cold immutable0017 recovery; current0020-cold; roles; upgraded TLS; fresh TLS; selected rollback/refusal. Retained0007–0014 recovery and every legacy role/TLS/rollback check remain present. Current stages use the selected archive and complete fixed0017 source, never a HEAD overlay.

Every stage authenticates the same archive/current producer-consumer/CORE/unit/V2 source/retained payload bytes and recorded image ID/Config/RootFS, including after a stage throws. Current sources are frozen separately from immutable retained payloads. The status receipt starts false and becomes true only after every stage and authority-parity check succeeds. Interrupted or failed operations cannot emit the final same-archive success line.

The new fresh TLS program migrates an actually empty schema directly to0020, installs the canonical grants, opens real restricted app/scheduler TLS connections, checks admission and privileges, creates/replays one original10000 grant, and returns measured catalogue/ACL hashes. The existing upgraded management fixture retains its complete pre-backup table/sequence oracle. Fresh and upgraded hashes must agree. Current smoke also runs the actual authenticated0017 image/consumer against the actual0020 server and requires refusal, with immutable state comparison afterward. Existing cold source destruction, independent server, encryption, quarantined restoration and before-backup oracle machinery is retained. These generated/runtime paths are implemented and contract-checked here; their actual image/TLS/encryption execution remains Plan17.

## Focused Verification

All DB-bearing commands ran serially against owned project `birja-p13-15`, using cached pinned images, existing Python3.14 and a stripped synthetic environment.

```text
cd backend
env -i PATH="$PATH" HOME=/tmp UV_OFFLINE=1 UV_NO_SYNC=1 \
  PRICE_SOURCE=fake EMAIL_BACKEND=console .venv/bin/python -m pytest \
  tests/test_migrations.py tests/test_critical_coverage_config.py -x -q
11 passed in27.41s

New pytest process against the existing current0020 fixture:
test_migrations.py::test_current_fixture_installs_exact_restricted_authority
1 passed in1.65s

python3 deploy/tests/test-ci-ops.py
58 passed in58.356s at final implementation source
  Includes all retained CI/source/image/command contracts plus:
  browser8; successor validation7; smoke image/source/fresh/refusal12.

python3 deploy/tests/test-portfolio-management-recovery.py   8 passed,9.242s
python3 deploy/tests/test-portfolio-recovery-contracts.py   11 passed,0.403s
python3 deploy/tests/test-portfolio-fixture-contracts.py    8 passed,1.502s
python3 deploy/tests/test-portfolio-migration-runner.py     6 passed,1.947s
bash deploy/tests/test-rollback-db-security.sh \
  --self-test-recovery-bundle-inputs                       PASS, no Docker/install
```

The management test's real V2 archive assembly uses explicitly mocked external image transport; it is not an actual image/encryption receipt. Three backend changed files pass full Ruff lint/format. Changed deploy Python files parse and pass targeted E9/F63/F7/F82 checks; shell syntax and git diff checks pass. Fresh/current and both retained staged dev programs compile. The actual full dev diagnostic image command was not run. A source-freeze check correctly rejected an intermediate contract run while this executor was still editing; the final58-case run used frozen source and passed.

## Deviations from Plan

**1. [Rule3 — Required fixture and tooling ownership extensions].** Parent explicitly authorized eight additional paths: conftest, test_migrations, ops-fixtures, portfolio-smoke, test-portfolio-smoke-image, test-ci-ops, verify-restore and test-dev-bootstrap. Ordinary current provisioning still expected0017 and omitted final grants; packaging/installation still selected V1/v2; fresh TLS had no genuine current mode. The changes install only the canonical final grants, recognize exact current tables/signatures, preserve retained tests and add the necessary current producer/profile/path/CLI dispatch. No immutable migration, SQL authority, dependency or financial oracle was rewritten. Commits `c80eb85`, `e1bdfa5`.

**2. [Rule1 — Malformed inventory exception].** The retained V1→V2 mutation test exposed a KeyError when the expected map lacked V2 members. An explicit all-required-names check now refuses with ValueError before dictionary access; valid V1/V2 and all exact declaration/checksum/source checks retain their meaning. Commit `c80eb85`.

**3. [Rule3 — Current dev diagnostic assumptions].** The old dev program asserted0017, restored its drift test to0017 and inserted an account as the ordinary app role. It now seeds the same123.45cash/7777baseline synthetic account administratively with canonical metadata and a grant-free legacy latch, then requires actual ordinary INSERT denial before the unchanged app cash+1/124.45 oracle. Existing migrated321.12/8765 and foreign-role/ownership/grant checks remain. Partial0018 application admission must report migration_only and restore0020; the migration client correctly retains its supported partial-revision semantics. This is test setup, not a new grant or baseline rewrite. Commit `e1bdfa5`.

No architectural change, new dependency, source overlay or waiver occurred. Neither deploy.sh nor the management recovery fixture required modification.

## Cleanup, Known Stubs and Handoff

Owned containers/network were removed with exact-project down/volumes cleanup; container/network/volume label queries are empty. The exclusive DB lane is released. No unfinished runtime stub was introduced. The deliberately future Plan16 strategy spec is a declared creation dependency, enforced as a missing-file failure rather than represented as a passing journey.

The preserved Phase12 archive remains SHA256 `d253bc51b876c7d629ee246ee47bd57274a5d9333e71318e11fcef586cff26be`; no Phase13 final archive was created here. All17 code/config/test paths are committed. Unrelated `.claude/` remains untouched. No private environment, provider, production, package/lock/image/Python pin, push, merge or deployment operation occurred. Exact issue35 scope/hash/path/version/targets and expiry2026-12-17T00:00:00Z remain unchanged; Python pin20261111 remains unchanged.

Plan16 still owns real strategy browser authoring and the UI packet. Plan17 owns actual complete all-security, image builds/scans, fresh/upgraded TLS/dev diagnostics, complete retained/current encrypted cold recovery and selected rollback qualification at frozen reviewed source. Focused contract composition here is not that campaign. Parent owns independent review and global STATE/ROADMAP/REQUIREMENTS updates. No whole requirement, phase, UI or native200 acceptance is claimed.

## Self-Check: PASSED

All17 changed implementation/test/configuration paths and this summary exist. All nine listed task commits resolve, with relevant RED commits before GREEN. Final58-case aggregate and focused verification above pass. No tracked deletion or task-generated untracked repository artifact remains. No new production endpoint/auth/schema trust boundary was introduced beyond the plan's synthetic tooling/file-source boundary.
