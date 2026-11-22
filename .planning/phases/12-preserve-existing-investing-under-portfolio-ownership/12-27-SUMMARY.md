---
phase: 12-preserve-existing-investing-under-portfolio-ownership
plan: "27"
subsystem: testing
tags: [postgresql, portfolio-ownership, coverage, recovery, tls, playwright, image-scans]
requires:
  - phase: 12-26
    provides: actual ownership browser journeys and strict security/recovery graph
provides:
  - Complete source-frozen security qualification with3108backend/958frontend cases and60critical modules100%
  - Actual seven-stage same-archive encrypted recovery, cold restore, authority/TLS parity and rollback/refusal
  - Current owner packet including named financial surfaces and capture-only zero/multiple states
affects: [12-28, 13, 15]
tech-stack:
  added: []
  patterns: [complete-run qualification, exact executable-input equivalence, deterministic session fixtures]
key-files:
  created:
    - .planning/phases/12-preserve-existing-investing-under-portfolio-ownership/12-LOCAL-VERIFICATION.md
    - .planning/phases/12-preserve-existing-investing-under-portfolio-ownership/12-HUMAN-UAT.md
  modified:
    - .planning/phases/12-preserve-existing-investing-under-portfolio-ownership/12-RECOVERY-PROOF.md
    - backend/tests/test_portfolio_entitlements.py
key-decisions:
  - Require actual complete command success; never combine failed/focused pieces into a whole-run pass
  - Retain original recovery source identity and authenticate unchanged packaged/runtime inputs after unrelated test-only changes
  - Use completed reviewed sessions and explicit ordering for historical dividend fixtures across exchange clock boundaries
  - Keep owner UI and genuine native200% acceptance separate and blocking
requirements-completed: []
requirements-addressed: [PFUND-03, PFIN-02, PFIN-03, PCTX-01, PVIEW-03, PSAFE-02, PSAFE-03]
duration: 23h20m elapsed across sessions including interruptions; final security25m41s and recovery45m08s
completed: 2026-11-17
---

# Phase 12 Plan 27: Complete Local Security and Recovery Qualification

**The complete security graph and one-archive seven-stage recovery pass, with
current source-bound owner review prepared and both human checks still pending.**

## Performance and Task Commits

The repair ledger begins atf1c33f9,2026-11-16T16:43:53Z. Final qualification
records were completed2026-11-17T16:03Z, approximately23h20 elapsed including
interruptions and bounded continuations. This is not focused-operation latency.
Both tasks are complete; owner Plan28 and phase reviews are not.

| Task | Actual completion |
|---|---|
| 12-27-01 complete financial/browser/security gates |11773a9 records the actual complete all-security pass at1f8d5a4, plus current owner packet and pending human checks |
| 12-27-02 one-archive serial recovery |0394bff records the actual complete seven-stage pass at10121b0;11773a9 adds final executable-input equivalence/current packet references |

Owning-plan fixes are committed individually throughout the detailed
12-27-AUTOMATED-CONTINUATION.md ledger, rather than hidden in evidence commits.
The final test-only repair is1f8d5a4. Earlier historical/failed/focused receipts
remain preserved and are not relabelled as final successes.

## Verified Outcomes

- Actual unchanged `run-portfolio-validation.py --suite all-security` passes
  exit0 in1541.269seconds at1f8d5a4/tree795b50b, zero source changes during
  execution.3108backend cases pass; branch-inclusive overall coverage99.8537%,
  all60critical modules100% with zero missing/partial branches. Ruff227files,
  mypy101sources and Python audit pass.
- Full frontend44files/958tests, lint, types, whole formatting and production
  build pass; statements97.50%/branches94.65%. npm's existing high/critical
  gate passes with14MODERATE findings disclosed. All60browser cases execute:
  59pass/1original deployed-CSPskip, no added filtering/skip/retry. Actual declared
  Dockerfile builds, pinned pulls, container smoke5/5 and all five immutable-ID
  scans pass with0HIGH/CRITICAL, including unfixed vulnerabilities.
- Actual `--suite recovery` passes all seven stages in2708.086seconds at10121b0
  under one exclusively packaged archive5a495a9dc2901cac46bfa82f23ae2daef67323eda05ac08dc44c67272a2b01a4.
  Retained0007–0014 encrypted roundtrips, source-destroyed current0017 cold
  restore, restricted-role parity, upgraded/fresh verified TLS and real selected
  rollback/refusal all pass. Final archive/source/image guards and authority
  equality pass, not an assembly of focused results.
- Final read-only authentication retains that original recovery qualification.
  Of306 broad inventory paths, only the unused backend entitlement test differs.
  Packaged CORE/UNITS/portfolio payload, runtime, migrations, SQL, Dockerfiles,
  locks and actual recovery imports remain unchanged. The existing archive and
  image content/Config/RootFS bindings remain intact; no repackage/new-HEAD run
  is invented.
- Current owner ZIPc87cb4a3 contains the preserved102-artifact full-browser
  packet935963b1 and12-artifact zero/multiple capture-only supplement86d073b1.
  Both share249current covered source hashes, explicit original render commits
  and private capture/renderer hashes. Loaded mobile/desktop states were
  inspected; native200% and owner UI acceptance remain false/pending.

Exact commands, source/tree/time/coverage and immutable image IDs are in
12-LOCAL-VERIFICATION.md. Recovery timings/oracles and source binding are in
12-RECOVERY-PROOF.md. No hosted CI or production outcome is claimed.

## Deviations from Plan

The plan explicitly required retained consumer reconciliation. Necessary repairs
remained in their owning plans, with unchanged security/economic assertions:

1. **[Rules1/3 — Explicit-root fixtures]** Retained API, service, cursor, hook,
   browser and immutable-row setup/cleanup now use actual owned roots and exact
   current or genuine retained schemas. Combined runs exposed accidentally
   coincident user/root IDs and historical helpers importing current columns.
   Independent retained SQL/financial oracles and actual restricted authority
   remain. See the complete per-commit continuation ledger.
2. **[Rules1/2 — Actual runtime refusals]**3b88c35 preserves only the exact public
   crypto-price query across identity changes; private caches still purge.
   775abf4 validates final function OUT argument declarations as well as bodies/
   owners/ACLs. Behavioral negatives and affected full gates qualify both fixes.
3. **[Rule2 — Critical behavioral coverage]** Added meaningful real refusal and
   process-boundary cases for bootstrap/migrator cleanup, schema admission,
   ownership/history/receipt and zero-owner effects. All original47critical
   paths remain alongside13new ones; no threshold, exclusion or pragma changed.
4. **[Rules1/3 — Retained recovery harness]**5d9ae72/59e29b6 remove redundant
   private source overlays from nonroot images;777fc10 retains authenticated
   image IDs in direct Compose calls;487483b uses authenticated historical
   deploy control for historical lanes.10121b0 isolates same-archive campaign
   image aliases while preserving missing-binding/content/Config/RootFS guards.
   Regressions fail before/pass after; actual complete recovery qualifies them.
5. **[Rule1 — Deterministic clock premises]**e61f89b forces a real quote refresh,
   requires actual409/no-money-change then explicit reconfirmation, loses only
   a real201 fill and replays200 with the original payload/key.1f8d5a4 selects
   a genuinely completed dividend session, preserving a later split after the
   historical cutoff.18deterministic exchange clock cases and61real financial
   cases pass, followed by the complete3108/60-browser final run.
6. **[Rule3 — Review completeness and tool interruption]** A unified browser
   session ended143 without a result; its102partial artifacts were preserved,
   exact resources cleaned and a new full run passed. Private detached wrappers
   retain atomic results and guarded cleanup without changing commands/gates.
   After whole security success, the unchanged guarded renderer created a
   capture-only zero/multiple companion; no test-suite success is fabricated
   from those screenshots and no tracked test changed merely to capture them.

No new dependency, runtime endpoint, provider operation, production tool/config
change, force-push or deployment was introduced. Necessary prior source changes
are qualified by the final actual gates rather than accepted on focused counts.

## Known Stubs and Remaining Checks

No required runtime stub remains for this preservation slice. Create/name/rename/
description/overview management remain Phase13; public deletion remains Phase14.
The SSH destination placeholder in owner instructions is an intentional user-
specific connection value, not a product stub.

Both Plan28 checks remain blocking: explicit acceptance of changed named
surfaces/safety states and genuine desktop browser Zoom menu200%. The current
packet is `/tmp/birja-phase12-ui-review-owner-1f8d5a4.zip`:
c87cb4a3eb3feb52c42a37aa60ff69cce66d2ac8e2637847e6a977af1714d55f.
Extract and open top-level index.html.12-HUMAN-UAT.md preserves both pending
responses; no silence or past phase acceptance is reused.

Final phase code/security/UI reviews and goal verification still follow
execution. All28requirements remain unchecked until the appropriate verified
phase outcomes. No advancement to13 or Phase12 completion is authorized here.
Phase7's consumed November16 campaign, six pending requirements and OFF stock
admissions remain unchanged. Work stays local onfeature/milestone-v1.2.

## Self-Check: PASSED

Both complete command results, named source commits, task-record commits,
three qualification/UAT files and all review archives exist. All source and
artifact hashes are verified, exact owned test resources are zero and no
test/migration child remains. Only unrelated.claude/ is untracked. No tracked
file was unexpectedly deleted; actual owner/native200% responses remain pending.
