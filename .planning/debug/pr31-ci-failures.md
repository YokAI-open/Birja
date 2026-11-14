---
status: awaiting_human_verify
trigger: "continue"
created: 2026-11-14
updated: 2026-11-14
---

# PR 31 hosted CI failures

## Current Focus

hypothesis: Image checkout lacks required historical source; the separate frontend refresh test observes React before TanStack Query's scheduled subscriber notification.
next_action: Root publishes the reviewed checkout/History-test fixes, then observes every required job in the new hosted run; no new runtime/backend/recovery campaign is needed for these three workflow/test-only files.
reasoning_checkpoint:
  hypothesis: The History refresh promise resolves before TanStack Query's default setTimeout subscriber batch commits the error result to React, making the immediate observer assertion flaky.
  confirming_evidence:
    - Hosted run43588078025 frontend fails only the immediate isRefetchError assertion;696other tests pass.
    - Unchanged CI=true whole hook file repeated20times reproduces the exact assertion failure in27.21s;20other tests pass.
    - Installed TanStack notifyManager batches subscriber callbacks through defaultScheduler=systemSetTimeoutZero; adjacent append-error tests already wait for observer state.
  falsification_test: Settled refetch result is not an error, or the observer never reaches the expected error with both previously accepted pages intact.
  fix_rationale: Wait for the accepted two-page precondition and observable error notification, while asserting the settled refetch error and unchanged full accepted chain; no application change.
  blind_spots: Same twenty repetitions and all697frontend tests now pass; fresh hosted workflow still needs actual confirmation.

## Symptoms

expected: PR31 required CI passes with existing coverage, security and recovery gates enforced.
actual: backend/image/ops/ci-pass fail at head95912e0; frontend/e2e pass.
errors: pip-audit flags dnspython2.9.0 CVE-2026-128089, fix2.9.2; image exact inventory hash mismatch; four fresh-cluster subtests fail starting Compose with ValueError recovery guard.
timeline: First hosted run43502466097 after completed local Phase11 verification.
reproduction: Inspect /tmp/birja-pr31-failed-ci.log and reproduce affected commands with isolated synthetic fixtures.

## Scope and authorization

Owner subsequently approved publishing the five reviewed commits through ade062b,
refreshing PR31 and finishing CI, including further independently reviewed/tested
workflow/test/planning fixes on the feature branch. Root performs publication;
this debugger does not push or edit the PR. New dependencies/application/runtime/
retained recovery tools, merge and production remain outside this follow-up.

User requested continuing after the CI failure summary: investigate, make local fixes and affected verification. Existing exact dependency approvals do not approve a different package; prepare concrete review before requesting installation approval. No gate waiver, private credentials, provider/production changes, merge or deployment. New push approval remains separate. Preserve unrelated .claude/ and shared-tree work; do not switch branches.

## Evidence

- timestamp: 2026-11-14
  checked: Same CI=true hook file --repeats=19 --retry=0 after test-only observer synchronization, then full frontend coverage.
  found: All21hook tests pass every repetition in29.96s; full36files/697tests pass17.36s,98.37%statements/94.82%branches/98.95%functions/99.1%lines. Scoped ESLint/Prettier and whitespace pass. Logs /tmp/pr31-frontend-repeat-green.log and /tmp/pr31-frontend-coverage-green.log. Exact accepted-chain/error assertions remain, with additional settled-error/four-request assertions.
  implication: Locally verified test-only timing repair; no hook/application/runtime change or weakening of the original History contract. Independent affected code/security reviews have zero findings, including allthree exact source hashes. Code committed08c92e6 for root publication.

- timestamp: 2026-11-14
  checked: Hosted image job132426760647 in run43588078025, then owned depth-one/no-tags local clone and identical fixture after full-history fetch.
  found: Hosted image15pass; CI fixture import fails archiving absentv0.3.1. Local git archive reports not a valid object name, exact fixture fails recovery guard; git fetch --unshallow --tags permits the unchanged fixture. Log /tmp/pr31-shallow-repro.log. New full-history policy fails before workflow repair; image fetch-depth0 plus missing/shallow/late-checkout negative controls gives15image/16CI pass.
  implication: Complete history is a prerequisite before image job's source-dependent isolation contracts; generated-launcher proof and runtime/CORE remain unchanged.
- timestamp: 2026-11-14
  checked: Hosted frontend failure and unchanged CI=true hook file with --repeats=19 --retry=0.
  found: Same immediate isRefetchError false assertion reproduced in27.21s;20other hook tests pass. Installed TanStack notifyManager subscriber notifications use systemSetTimeoutZero, so awaiting the query promise alone does not await its React observer batch. Log /tmp/pr31-frontend-repeat-red.log.
  implication: Synchronize this test with the accepted two-page precondition and observable error, retaining exact accepted-history assertions and testing settled refetch error plus allfourHTTPcalls.

- timestamp: 2026-11-14
  checked: Final affected backend, critical coverage, rebuilt native images, canonical builder smoke, five strict scans, reviews and owned cleanup.
  found:2557backend pass366.25s/99.87%;47critical4565statements/1462branches100%;builder5pass2.38s. ExactAPK/Python inventories differ onlyDNSpatch; nonroot networknone WKS/email/calendar/dividend imports pass. All5actual strict scans0HIGH/CRITICAL includingunfixed. Independent code/security delta0findings,6/6threatsclosed. Owned birja-test/birja-ops-test containers/networks/volumes allzero.
  implication: Complete affected local repair is verified, code committed as a0feb5c; publication/hostedCI confirmation remains separate. Final21log/source/image/command/cleanup receipt /tmp/pr31-dns-receipt.json SHA7574eef7b45f92d85cc023235afd5d9bcdce034cf8a87ba3dfcf0613714d180b.

- timestamp: 2026-11-14
  checked: Exact reviewed lock application, locked uv sync and installed inventory; canonical pip-audit.
  found: Lock SHA3eded7f21be30568f5d4fae129f38a11e19484035f60f1477a3f9b2bf30fd2d4 applied. Exactly one uninstall/install dnspython2.9.0→2.9.2; every other installed version unchanged. Unrestricted audit reports No known vulnerabilities found.
  implication: Original dependency audit failure has a verified exact local repair without additional package drift.
- timestamp: 2026-11-14
  checked: Exact upstream2.9.2 test_wks_bounds using prior cached2.9.0 then installed2.9.2, finite65536 input only.
  found: Prior2.9.0 fails SyntaxError not raised;2.9.2 same test passes. Upstream rdata/tokenizer/resolver211passed,31network/optional skips,71subtests in0.82s. Logs /tmp/pr31-dns-wks-red.log,/tmp/pr31-dns-wks-green.log,/tmp/pr31-dns-upstream.log.
  implication: Advisory mechanism is directly reproduced and fixed without unbounded resource input or network calls.
- timestamp: 2026-11-14
  checked: Exact DNS image/legacy contract boundaries before and after scoped exceptions.
  found: Pre-exception image15test and retained-installer contracts reject the approved DNS change; exact complete DNS entry plus historical remainder permit it. Image15,CI16,selected7 and actual retained-installer selftest pass; DNS version/artifact and unrelated changes still reject.
  implication: Only independently approved full package records depart from historical inventory; all eight calendar artifacts remain authenticated.

- timestamp: 2026-11-14
  checked: Parent relayed explicit owner decision Approve patch and continue locally; exact prospective lock and complete record comparison revalidated.
  found: Owner approves only dnspython2.9.0→2.9.2, exact wheel af15f7d385a6ae2fb35a796fde2138004c8c42c7389090e2addc83e3b3340fd8 and lock3eded7f21be30568f5d4fae129f38a11e19484035f60f1477a3f9b2bf30fd2d4, local install/rebuild/affected checks. Only that package record differs; no added/removed packages.
  implication: Exact approved local repair may proceed; publication/production remain unauthorized.

- timestamp: 2026-11-14
  checked: Official dnspython advisory, artifacts, provenance and temporary uv resolution
  found: Exact review ready in pr31-DEPENDENCY-REVIEW.md; only dnspython entry changes in temporary lock, no project mutation/install.
  implication: Parent can request exact package approval while unaffected fixes continue.
- timestamp: 2026-11-14
  checked: Local image contracts and historical e728855 lock
  found:13tests reproduce one exact hosted failure; only changed preexisting full package record is approved OTEL1.45.2.
  implication: Preserve historical inventory except exact independently authenticated OTEL record.
- timestamp: 2026-11-14
  checked: Actual Docker cold startup using unique owned alias/project, unchanged Compose constraints and check_running guard
  found: Missing synthetic alias produces No such image with pull_policy never; helper verifies export before import/binding, then actual isolated PostgreSQL startup and check_running pass. Existing tags untouched; owned resources removed. Log /tmp/pr31-ops-cold.log.
  implication: Cold-run prerequisite failure reproduced and corrected without changing retained CORE or selecting unverified image.
- timestamp: 2026-11-14
  checked: python3 deploy/tests/test-image-contracts.py; python3 deploy/tests/test-ci-ops.py
  found:15image contracts pass0.604s, including unapproved OTEL version/artifact, unrelated version/artifact, invalid archive and wrong existing alias negative controls;16CI contracts pass0.450s after adjacent mock updated for load/bind. Original13test RED is retained /tmp/pr31-image-red.log.
  implication: Exact artifact/inventory security remains enforced and CI preflight still precedes builds.
- timestamp: 2026-11-14
  checked: Original95912e0 preflight on unique synthetic cold alias, followed by actual same Compose before/after startup
  found: Original strict preflight passes yet alias remains missing; Compose refuses No such image. Patched helper then gives actual guarded PG GREEN. Log /tmp/pr31-ops-cold-before-after.log. Existing aliases preserved, owned tag/network/container cleaned.
  implication: Original-source behavior directly confirms missing prerequisite, rather than inferring it from warm host success.
- timestamp: 2026-11-14
  checked: sudo python3 /tmp/pr31-real-pg.py (actual affected24test PostgreSQL recovery suite)
  found:24tests pass122.519s, including all four original fresh-cluster subtests and function/schema/unsafe-runtime refusal controls. Log /tmp/pr31-ops-postgres.log. Owned birja-test/birja-ops-test containers and cold network absent after cleanup.
  implication: CI cold image initialization fix preserves actual0014 restore, role/quarantine/identity assertions without CORE changes.

- CI run: https://github.com/YokAI-open/Birja/actions/runs/43502466097
- Log: /tmp/birja-pr31-failed-ci.log
- Local accepted prior proof: .planning/phases/11-mixed-asset-recovery-and-acceptance/11-VERIFICATION.md

## Eliminated

None yet.

## Resolution

root_cause: Original stale OTEL inventory, missing authenticated recovery alias and vulnerable dnspython are fixed; subsequent hosted run43588078025 exposes image checkout missing historicalv0.3.1 and an immediate React-observer assertion before TanStack's scheduled notification.
fix: Preserve exact approved DNS/OTEL records and authenticated cold image startup; add full-history image checkout before real fixture contracts and synchronize only the History test with accepted pages/error notification, retaining all original data/error assertions.
verification: Prior exact dependency/backend/image/PG qualification remains source-bound and historical. Follow-up actual shallow-clone fixture RED/GREEN,15image/16CI and missing/shallow/late-checkout negatives pass; frontend exact failure reproduced with20whole-file repetitions, repaired repetitions and697tests/coverage pass. Hosted all-job success remains pending root publication/execution; no duplicate runtime/CORE campaign claimed.
files_changed: [backend/uv.lock, deploy/tests/test-image-contracts.py, deploy/tests/check-recovery-image.py, deploy/tests/test-ci-ops.py, deploy/tests/test-rollback-db-security.sh, .github/workflows/ci.yml, frontend/src/hooks/useEventHistory.test.tsx]
commit: d855a0f and a0feb5c published;08c92e6 reviewed/tested workflow/test follow-up prepared for root publication.

## Specialist Review

specialist_hint: python/general. Mapped python-expert-best-practices-code-review
and engineering:debug skills are not available locally; none invoked. Independent
affected code/security reviews are complete with no active findings, as recorded below.

Independent code review: pr31-CODE-REVIEW.md, no active findings. Independent
security review: pr31-SECURITY-REVIEW.md,6/6closed, no active findings. Both
reviewed the original three source paths and the exact subsequent DNS lock/image/
legacy-contract delta. Owner-approved installation and all affected checks pass.
