# Phase15: Verify Exact Portfolio Recovery and Acceptance — Research

**Researched:** 2026-11-22. **Confidence:** HIGH for the inspected local code;
execution outcomes below are inherited evidence, not newly executed tests.

<user_constraints>
## User Constraints

Source:15-CONTEXT.md. Locked decisions copied verbatim:

- Complete PSAFE-04/05/06 and the four Phase15 roadmap outcomes using isolated
  synthetic data and the existing stack. Keep all financial precision, owner
  isolation, original retry identities and terminal deletion semantics.
- Preserve the implemented screens and design system accepted in Phases12–14.
  Phase14 UI and native browser200% were explicitly accepted on2026-11-22.
  Do not ask for unchanged-screen approval again; new or changed interactions
  need only their affected review and actual human result where appropriate.
- Balance speed and security now and in future milestones, per the owner's
  2026-11-21 preference in CLAUDE.md. Use bounded research and task-scoped checks,
  reuse passing evidence with unchanged relevant inputs, and put nonblocking
  hardening in follow-up debt. Do not reproduce Phase14's long repair campaigns.
- Phase14 is closed:19plans,5/5outcomes,7/7requirements. Its explicit component
  qualification amendments stand. Failed whole commands remain failed, and no
  hosted CI or uninterrupted whole-run pass is invented. Full CI before merge,
  coverage gates and required image policies remain enforced.
- Plan15 must distinguish verified inherited coverage from genuine remaining
  integration gaps. Prefer the smallest executable plan set; no speculative
  abstractions, package changes or broad audit expansion.
- Keep this milestone branch local. Provider operations, Phase7 activation,
  new dependencies/images, push/merge, release and production changes are not
  authorized by planning or execution scope. Issue35 scope/2026-12-17UTC expiry
  stays unchanged. Preserve unrelated untracked.claude/.

### Agent Discretion

Choose bounded synthetic fixtures, exact existing command selectors, evidence
reuse rules, task ordering and a concise operator contract. Identify any
concrete fixture/context fix needed to make supported execution reproducible.
Preserve real database/restore assertions; do not substitute invented results.

### Deferred Ideas

Phase7 live work, deployment/release, paid services, new product surfaces,
nonblocking hardening, portfolio transfers/reset/trash and new asset classes.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Required outcome | Research support |
|---|---|---|
| PSAFE-04 | Exact encrypted active/frozen restore and once-only original retries | Existing31-table/24-tail cold oracle; add explicit restored creation/fill/payment replay, not another ledger design. [VERIFIED: REQUIREMENTS.md; portfolio-closure-recovery-fixture.py; portfolio-smoke.py] |
| PSAFE-05 | Tested migration and supported rollback/refusal without financial loss | Retain genuine0014/0020→0023 migration and original source families; fix cold verifier context and document executable operator matrix. [VERIFIED: portfolio-smoke.py; portfolio-sources.py; RUNBOOK.md] |
| PSAFE-06 | Full protected lifecycle, real accounting/concurrency, required gates/human acceptance | Existing backend/browser cases and accepted12–14 screens provide most coverage; map exact evidence, close post-restore gap, keep full CI before merge. [VERIFIED:14-VERIFICATION.md; existing tests; CLAUDE.md] |
</phase_requirements>

## Summary

Use **four small plans**, not a new feature architecture: (1) make existing
recovery execution reproducible for Phase15, (2) add bounded original-request
replay on the restored current server, (3) qualify the resulting integration
with explicit evidence reuse, and (4) finish the operator/acceptance matrix.
Most lifecycle implementation is already substantive and verified; this is
an integration-evidence phase. [VERIFIED: roadmap Phase15;14-VERIFICATION.md;
code paths inspected below. Plan grouping is a research recommendation.]

The concrete reproducibility problem is still in committed test tooling:
the cold branch imports the checkout verifier, which cannot find the retained
source archive beside itself. Phase14's real installed-verifier correction
exists only in a private driver. Also, the campaign's output is hardcoded to
the preserved Phase14 directory. Fix these two narrow seams before any expensive
run. No historical pin or application/schema change is indicated. [VERIFIED:
portfolio-smoke.py:955,1092; verify-restore.py:970; run-portfolio-validation.py:25;
run-portfolio-campaign.py:33;14-RECOVERY-PROOF.md; private recovery-component-operations.py]

## Architectural Responsibility Map

| Capability | Owner | Rationale |
|---|---|---|
| Recovery source selection/output ownership | Existing Python fixture/runner | Owns selected archive, installed tools, source/image/process receipts. [VERIFIED: run-portfolio-validation.py; run-portfolio-campaign.py] |
| Financial retry/terminal semantics | Existing backend services and PostgreSQL | Test actual restricted services; do not reproduce rules in the driver. [VERIFIED: portfolio_closure.py; trading.py; portfolios.py; dividends.py] |
| Exact restored state | Producer/consumer plus independent fixture oracle | Compare31tables/24tails before replay or runtime regrant. [VERIFIED: verify-restore.py; portfolio-closure-recovery-fixture.py:98,589] |
| Visible lifecycle/acceptance | Existing React/browser specs | No new screens are necessary for the three requirements. [VERIFIED: requirements; portfolio-strategies/ownership/deletion specs] |

## Project Constraints (from AGENTS.md)

- Read shared CLAUDE rules and project/phase state; preserve existing history,
  research, checkpoints, reviews, verification and summaries. Use GSD plus its
  adapter; do not treat old STATE pointers as implementation evidence.
- Keep shared rules in CLAUDE.md, Codex adaptations in AGENTS.md; preserve the
  existing design system and use ui-ux-pro-max if UI actually changes.
- Follow session delegation limits; absent delegation, retain sequential roles.
- No push/merge without explicit owner approval; no deployment inferred from
  examples, yolo flags or commit_docs.
- Defensive work stays repository-focused, with static/pure/existing isolated
  checks and plain-language findings; no unnecessary active demonstrations.
- No broad skill/config migration; keep Claude setup and unrelated work intact.

[VERIFIED: AGENTS.md read in this research; CLAUDE.md adds Decimal/string JSON,
real isolated DB tests, no production/dev test stack,80%overall/100%critical,
and proportionate-verification/evidence-reuse requirements.]

## Standard Stack and Environment Availability

Reuse installed/locked dependencies; **no installation or upgrade is proposed**.
Package-legitimacy installation/audit is therefore not applicable. Registry
currency was not queried, and these are lock versions, not latest-version claims.
[VERIFIED: backend/uv.lock; frontend/package.json;15-CONTEXT.md]

| Existing component | Verified value | Source |
|---|---|---|
| Backend runtime | Python3.14.9 in backend/.venv | Read-only version command |
| FastAPI / SQLAlchemy / asyncpg |0.162.0 /2.0.55 /0.32.0 | backend/uv.lock |
| pytest / pytest-asyncio |9.1.1 /1.4.1 | backend/uv.lock |
| Frontend / browser | React19.3.1 / Playwright1.64.1 | frontend/package.json |
| Host tooling | Node24.22.1, uv0.13.5, Docker29.2.1 | Read-only version commands |
| Approved restic |0.19.1, Go1.26.4, linux/amd64 | /tmp/birja-test-tools/restic-0.19.1/restic version |
| Host Python |3.12.3; backend interpreter remains3.14.9 | Read-only version commands |

All table entries are [VERIFIED: listed local source/version command]. No service
was started or probed, Docker daemon access was not exercised, and no credentials
or live configuration were read. Context7 CLI was not found; no library API or
external-standard decision needed new documentation lookup. [VERIFIED: command
outputs in this research; scope restriction from parent task]

## Remaining Work Versus Inherited Evidence

| Concern | Actual existing coverage | Remaining work |
|---|---|---|
| Current exact cold recovery | Real source-destroyed0023cold,67.354s; fixed0020cold50.781s, matching authority triples. | Commit the real verifier-context selection and make it reproducible from a clean checkout. [VERIFIED:14-RECOVERY-PROOF.md; smoke factory] |
| Current oracle inventory | Active root plus4closed roots, zero-active user, same-stock boundaries,31tables/24tails; independent literal finances. | Retain this oracle; no duplicate inventory. [VERIFIED: portfolio-closure-recovery-fixture.py:98–200] |
| Original migrated finances | Genuine0014upgrade checks full old columns/tails, baseline8765 and fractional original holding;0020upgrade compares before snapshot. | Reference/reuse matching migration evidence; do not label a newly seeded10000root as migrated data. [VERIFIED: portfolio-smoke.py:fresh_authority_program; test-portfolio-smoke-image.py:98,114] |
| Once-only AFTER restore | Closure intents explicitly replay through actual service; oracle equality preserves creation/fill/payment records. | Explicitly retry original creation, active original fill and paid dividend on restored server; confirm closed originals cannot resume or redirect. Source seeding is not post-restore replay. [VERIFIED: closure_role_program:460; closure fixture generated program:760] |
| Full user lifecycle | Creation/description/comparison/switching in strategies spec; original migration/targeting in ownership; terminal/zero/recovery/tabs in deletion. | Build one exact requirement→test/evidence matrix and fill only a demonstrated missing assertion. [VERIFIED: three existing specs and14verification] |
| Concurrency/accounting | Actual cross-asset cash and creation/name races; closure/fill/job/create/delete races both orders. | Reuse unchanged-input results; no new concurrency framework. [VERIFIED: test_portfolio_strategy_lifecycle.py:235,255; test_portfolio_closure_races.py] |
| Owner UI/native200 | Actual12/13/14 approvals;14reply2026-11-22, packet strict verification passes. | Reuse accepted unchanged surfaces; request only affected outcomes if actual UI changes. [VERIFIED:14-HUMAN-UAT.md;13/12verifications;15context] |

## Architecture Patterns and Exact Seams

1. **Select the real installed consumer.** `portfolio-smoke.run` already accepts
   `archive`, `archive_sha`, `revision`, `cold`, `fresh_bootstrap`,
   `upgraded_bootstrap` and `upgraded_from`. Its cold branch calls
   `load_recovery()` then `canonical`, `restored(...,manifest=source_manifest)`
   and `verify(...,quarantined=revision!='0023')`. Make that factory use an
   authenticated synthetic installation for archive-backed cold calls, with
   lifetime covering the entire restore. Keep the default checkout consumer
   only where a complete installed package is unnecessary. [VERIFIED:
   deploy/tests/portfolio-smoke.py:616,955,1020,1092]

2. **Reuse the proven installation sequence.** Existing `ops-fixtures.py`
   `installed_recovery(archive_arg=None)` authenticates/installs selected tooling;
   the private Phase14 `installed_verifier()` uses `bundle_verify`,
   `bundle_install(...,required_profile='deploy-recovery-v4')`, imports
   `host/var/lib/birja/recovery/releases/<sha>/deploy/verify-restore.py`, and
   confirms genuine0020source before use. Commit a small context/factory seam;
   do not copy the entire private supervisor or substitute verification results.
   [VERIFIED: ops-fixtures.py:373; private recovery-component-operations.py:26–46]

3. **Use finite Phase15 path selection.** `ARCHIVE` is currently
   `/tmp/birja-phase14-proof/recovery.tar.gz`; recovery preflight rejects its
   existing parent. The supervisor receipt allowlist knows `phase14-campaign-*`
   or `backup-test-*`, and status reads `runner.ARCHIVE`. Add an explicit finite
   phase choice, e.g.14(default)/15, consistently forwarded in request, worker,
   preflight and status; select `/tmp/birja-phase15-proof/recovery.tar.gz` for15
   and preserve existing14/13archives. Never clear the old proof to make a
   preflight pass. Preserve exclusive receipt creation and read-only resume.
   [VERIFIED: run-portfolio-validation.py:25,100,455;
   run-portfolio-campaign.py:33,93,573. Proposed option spelling is a recommendation.]

4. **Extend current restore replay in place.** The current generated fixture
   has create/projection/verify/compare modes and actual app/scheduler clients.
   Closure replay is injected by `closure_role_program`; extend a similarly
   explicit restored-only check using original stored request identities and
   actual existing services. First compare immutable before-oracle, then retry,
   then assert no extra grant/trade/payment and no frozen-root/sibling changes.
   Account for legitimately consumed sequence values during attempted inserts;
   exact restored tails are checked before business replay, never reset them.
   [VERIFIED: portfolio-closure-recovery-fixture.py:694–829;
   portfolio-smoke.py:426–468; existing PostgreSQL identity assertions]

### Strong Analog Map

| Planned responsibility | Closest source to read/copy |
|---|---|
| Installed selected verifier lifetime | ops-fixtures.py:installed_recovery; private installed_verifier above |
| Bounded owned execution and receipts | run-portfolio-campaign.py:start/worker/inspect_status; validation.recovery_operations |
| Current exact data and replay oracle | portfolio-closure-recovery-fixture.py:require_projection/program; smoke.closure_role_program |
| Focused tooling contracts | test-portfolio-smoke-image.py:98,114,396; test-portfolio-validation-contracts.py |
| End-to-end lifecycle acceptance | portfolio-strategies.spec.ts; portfolio-ownership.spec.ts; portfolio-deletion.spec.ts |

All analogs are [VERIFIED: current source inspected]; these suffice without wider
analogy discovery. Suggested modified paths are the existing smoke/runner/campaign
and their contracts, current closure fixture if needed, RUNBOOK and Phase15
evidence. No application, schema, dependency or product-UI file is presently
identified as needing change. [VERIFIED: requirements and inspected gaps]

## Don't Hand-Roll

- Use restic plus the existing producer/consumer and independent oracle, not a
  second backup format or comparison framework.
- Use actual restricted backend services for retries, not replayed success rows.
- Use existing supervisor and source/image/archive guards, not another private
  orchestration framework or mutable-image equivalence fallback.
- Use genuine fixed0020/0017 archives, never repin/overlay current source.

[VERIFIED: existing implementations and locked constraints; these are prescribed
reuse choices, not external product recommendations.]

## Runtime State Inventory

| Category | Scope found / planning consequence |
|---|---|
| Stored data | Synthetic current schema0023, lifecycle/intent/grant journals and31/24oracle; no new schema is proposed. Preserve existing14proof. [VERIFIED: fixture and recovery report] |
| Live service config | Outside authorized research; no live config changes are required by this test-tooling phase. [VERIFIED:15context] |
| OS state | Existing tool paths and owned receipt processes; don't alter registered production timers/services. [VERIFIED: campaign source;15context] |
| Secrets/env | Existing sanitized synthetic environment; never read/use real.env or recovery passwords. [VERIFIED: validation.environment] |
| Artifacts | Preserved14archive plus fixed historical source/image records; Phase15 needs its own absent output/receipt paths. [VERIFIED: runner constants and14proof] |

## Common Pitfalls

- **Wrong resolver context:** current verifier silently lacks adjacent archived
  source, so fixed0020guard correctly refuses. Test real consumer resolution
  without Docker before the long proof. [VERIFIED: actual14failure and source]
- **False replay claim:** unchanged restored rows or replay during seed are not
  actual post-restore retry. Add the bounded restored-only check above.
  [VERIFIED: inspected generated program and role injection]
- **Destroying earlier evidence:** existing Phase14 directory prevents the
  current hardcoded runner from starting. Introduce finite owned paths, not
  deletion/moving of prior proof. [VERIFIED: preflight and preserved archive]
- **Unnecessary invalidation:** smoke/runner are archived payload members;
  modifying them requires a fresh matching archive for their new proof, but
  does not automatically invalidate unchanged backend/frontend/image evidence.
  [VERIFIED: verify-restore.py:PORTFOLIO_PAYLOAD_V1; validation.authenticate]
- **Moving goalposts:** preserve failed whole results, exact source/input reuse
  records and mandatory full CI before merge; do not relabel local component
  evidence as hosted CI. [VERIFIED: CLAUDE;14amendments;15context]

## Validation Architecture

Use existing pytest/Vitest/Playwright and offline unittest contracts; no Wave0
framework installation. [VERIFIED: test files, dependency manifests,15context]

| Requirement | Existing focused command / map | New bounded proof |
|---|---|---|
| PSAFE-04 | `python3 deploy/tests/test-portfolio-fixture-contracts.py`; `python3 deploy/tests/test-portfolio-management-recovery.py` (offline default) | Actual encrypted current cold restore with restored original-request replay; tests for correct installed context. [VERIFIED: source; new proof proposed] |
| PSAFE-05 | `python3 deploy/tests/test-portfolio-smoke-image.py`; `bash deploy/tests/test-deploy-compatibility.sh`; `bash deploy/tests/test-rollback-db-security.sh --self-test-retained-install` | Reproducible phase15selector, genuine retained consumer and documented supported/refused matrix. [VERIFIED: existing runbook/contracts] |
| PSAFE-06 | `python3 deploy/tests/test-portfolio-browser-contracts.py`; real backend `tests/test_portfolio_strategy_lifecycle.py tests/test_portfolio_closure_races.py`; browser `--suite portfolios` | Exact full lifecycle coverage matrix using inherited passing evidence plus affected checks, no duplicate screens. [VERIFIED: runner/tests; recommendation] |

**Per edit:** affected offline contract group and lint/type check only.
**Before expensive work:** clean committed inputs, genuine installed-context
check, exact selected owned paths, available existing tools/images and cleanup.
**Final integration:** one fresh Phase15archive if archived fixture inputs changed;
execute affected current restore/replay and reproducibility checks once. Reuse
unchanged legacy/roles/TLS/browser/backend evidence by explicit input/hash scope.
Keep the existing whole graph executable for required PR CI; any broader rerun
must have a concrete invalidation or deliberate integration/release reason.
Do not promise a sub30second real restore. Measured Phase14current cold67.354s
and full component2266.665s are history, not deadlines. [VERIFIED: CLAUDE;
14-RECOVERY-PROOF.md; existing runner. Sampling policy is the owner-constrained recommendation.]

**Wave0 gaps:** only tooling-context/Phase15-output contracts and the explicit
post-restore retry assertion; no infrastructure installation or product work.
Use existing tests, adding a small test file only if the existing contract group
cannot express the seam. [VERIFIED: code inspection; recommended task boundary]

## Security Domain

Keep current authentication/session/owner checks, synthetic-only inputs,
authenticated archive provenance, restricted roles, verified TLS and immutable
financial records. Narrow checks to wrong source selection, lost original retry
identity or incorrect target scope; no new active demonstrations, threat-surface
expansion or ASVS certification claim. Existing38-entry Phase14 review and issue35
disposition remain unchanged. [VERIFIED: AGENTS; CLAUDE;14-SECURITY.md;15context]

## Recommended Plan Boundaries

1. **Reproducible tooling:** installed verifier context plus finite15paths and
   focused contracts; no schema/application changes.
2. **Restored original retries:** minimal actual-service replay/checks and
   independent frozen/sibling/grant/payment assertions.
3. **Integrated proof:** fresh matching archive/current proof once, exact reuse
   matrix, affected protected journeys only, reviews and cleanup receipts.
4. **Operator/acceptance:** tested support/refusal matrix, 28-requirement lifecycle
   evidence map and final independent goal verification; inherited human outcomes
   remain valid for unchanged surfaces. No publication or milestone archival.

These are recommendations derived from the verified seams above, not executed
tasks or approved implementation changes.

## Assumptions Log and Open Questions

No training-based capability/package assumption is needed. Exact CLI option
spelling and bounded test helper placement remain planner discretion; inspect
the actual original creation/fill/payment records when implementing the replay
check. Whether an additional active crypto fill must be seeded is not yet
determined; preserve an independently specified economic oracle if added.
[VERIFIED: current fixture inspected; explicitly unresolved implementation detail]

No new owner scope decision, credentials or provider permission is needed to
plan the three existing requirements. Full hosted CI has not been run by this
research and remains required before merging. [VERIFIED:15context; CLAUDE]

## Sources and Confidence

Primary sources are the repository paths and exact private historical driver
cited inline, read on2026-11-22. Code/lock/version observations are HIGH
confidence; observed prior timings/outcomes are attributed to14proof and its
independent verification rather than fresh execution. The private driver is
an implementation analog, not a new committed supported interface.
No new external facts, packages, web recommendations or standards were used.
No tests, services, Docker operations, provider calls or production inspection
were run during this research. Only15-RESEARCH.md was written.
