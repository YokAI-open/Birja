---
phase: 07-permitted-stock-discovery
plan: "13"
subsystem: testing
tags: [coverage, admission, retention, tls, recovery, images, playwright]
requires:
  - phase: 07-12
    provides: Read-only stock UI and independent crypto behavior
provides:
  - Original and stock critical coverage at100% with unchanged six required CI jobs
  - Genuine restricted-TLS persisted calendar consumer proof in both schema lanes
  - Independently reviewed scoped admission, retention deadlines and whole-cycle bounds
  - Actual current-source native/image/recovery/browser and historical rollback evidence
affects: [07-14, Phase8, Phase11]
tech-stack:
  added: []
  patterns: [earliest disclosed retention deadline, trusted scope propagation, explicit historical fixture lanes]
key-files:
  created:
    - .planning/phases/07-permitted-stock-discovery/07-LOCAL-PROOF.md
    - .planning/phases/07-permitted-stock-discovery/07-REVIEW.md
    - .planning/phases/07-permitted-stock-discovery/07-SECURITY.md
    - .planning/phases/07-permitted-stock-discovery/07-UI-REVIEW.md
  modified:
    - .github/workflows/ci.yml
    - CLAUDE.md
    - backend/app/services/alpaca.py
    - backend/app/services/stock_admission.py
    - backend/app/services/stock_sessions.py
    - backend/app/services/stocks.py
    - backend/app/tasks/stock_scheduler.py
    - backend/tests/test_accounts.py
    - backend/tests/test_alpaca.py
    - backend/tests/test_critical_coverage_config.py
    - backend/tests/test_stock_admission.py
    - backend/tests/test_stock_quotes.py
    - backend/tests/test_stock_scheduler.py
    - backend/tests/test_stocks_api.py
    - deploy/RUNBOOK.md
    - deploy/STOCK-DATA-ADMISSION.md
    - deploy/tests/ops-fixtures.py
    - deploy/tests/selected-cutover.py
    - deploy/tests/test-ci-ops.py
    - deploy/tests/test-db-operations.sh
    - deploy/tests/test-image-contracts.py
    - deploy/tests/test-rollback-db-security.sh
    - frontend/e2e/helpers.ts
    - frontend/e2e/stocks.spec.ts
    - frontend/src/components/StockSection.test.tsx
    - frontend/src/components/StockSection.tsx
    - frontend/src/hooks/useStocks.test.tsx
key-decisions:
  - "Existing admission.valid_until conservatively bounds every disclosed retained quote; no API shape change or runtime DELETE privilege."
  - "Historical0008 old-application rollback and current0010 runtime/recovery are distinct explicitly proven lanes."
  - "Actual provider/storage rights and owner UI acceptance remain Plan14 gates; local proof never enables stock execution."
requirements-completed: []
duration: 46min
completed: 2026-11-10
---

# Phase 7 Plan 13: Reviewed local safety gates Summary

**Original and stock critical paths reach100%; current images, exact recovery,
restricted TLS consumers and browser journeys pass after independent fixes.**

## Performance

- Started:2026-11-10T19:37:38Z; completed:2026-11-10T20:23Z.
- Tasks:2/2;27implementation/test/operator files plus owned planning/review records.
- Source remained on feature/v1.1-stock-planning; all commits are local.

## Accomplishments and actual verification

- Preserved six required jobs and ci-pass aggregate, all original15critical
  modules,100%critical/80%overall thresholds, serial ops and strict unfixed image
  policy. Added six stock modules and exact documented-command parity.
- Genuine session_at reads persisted current admission/derived rows through app,
  scheduler and migrator TLS roles in populated0008 upgrade-without-grant-repair
  and fresh successor bootstrap. Forged/replaced generation, expired review with
  fresh rows and authority writes refuse; matching refresh remains permitted.
- Trusted configured account/server now propagates through nested calendar and
  provider checks. Current retention permission and exact collected_at deadline
  govern disclosure; the existing client envelope carries the earliest deadline
  and full transport time is spent before caching. Whole-cycle configured timeout
  cancels both pre-fetch work and post-fetch writes, rolling back partial state.
- Full backend969passed54.59s,99.68%overall. All21critical modules:
  1221statements/304branches at100%. Ruff/format/mypy and pip-audit pass.
- Frontend310passed20.90s;98.91%lines,97.77%statements,95.59%branches.
  Lint/types/format pass. npm high/critical gate passes;2low/13moderate existing
  development advisories remain recorded without force-upgrades.
- Actual full Chromium20passed90.2s without retry;1expected deployed-site CSP
  skip because no production URL is provided. This includes all stock journeys
  and completed-retry keyboard focus. Dedicated e2e resources were cleaned.
- Actual hardened nonroot test-builder158admission/session/API tests pass7.04s;
  actual read-only/network-none/nonroot runtime imports approved native calendar
  dependencies and evaluates early-close bounds correctly.
- All five actual final images pass pinned Trivy0.76.1 HIGH/CRITICAL including
  unfixed with zero qualifying findings; no waiver/ignore/filter change.
- Current --all exact retained encrypted restore0007/0008/0009/0010 passes;
  recovery165.932s, roles65denials71.102s, TLS lanes56.584s/68.122s.
  Backup25tests, restore6tests, DB configuration121tests, CI10/image13contracts pass.
- Actual image transition passes43.204s with collation drift/reindex, logical
  restore, original fingerprints and Redis AOF/auth/restart invariants. Actual
  selected legacy retained cutover/deploy/old rollback passes296.329s. Final
  source-label-corrected legacy TLS/services/recovery lane passes107.422s with
  stable HEADf6a556e. Its v0.4.0 app identity, current tool identity and installed
  recovery archive remain distinct. No old-v0.3.1-on-0010 claim is made.

Exact commands, receipts, lock/image/config/archive identities, failures/retries
and limits are in07-LOCAL-PROOF.md. All fixed ops/restore/transition/e2e projects
have no remaining containers, volumes or networks. The healthy disposable
birja-test stack remains available for the orchestrator; no dev/prod target used.

## Task commits

Task1 meaningful RED/GREEN/corrections:

- bb924b2 — Require stock coverage and genuine TLS consumers (behavioral RED).
- 1db7af1 — Refuse malformed Decimal exponents at HTTP boundary (behavioral RED).
- 70a6791 — Scope/retention/whole-cycle regressions (7actual RED failures).
- 7fb4bed — Extend gates and fix runtime admission, timeout and fixture issues.
- bd2a83f — Loading/focus regressions (2actual RED failures).
- 670b221 — Reserve twenty records, restore retry focus, await browser readiness.
- 214560b — Isolate collation probes and select revisioned recovery contracts.
- f6a556e — Explicit immutable legacy0008 rollback fixture scope/provenance.

Task2:

- ae8b939 — Actual local proof plus independent code/security/UI review records.

## Independent reviews

- Code: initial3blockers/2warnings, all fixed; final bounded re-reviews report
  zero active blockers/warnings, including historical fixture/inventory changes.
- Security: initial retention exposure/cache gaps fixed;47/47unique declared local
  threats/49obligations closed, no accepted waiver. Actual external rights remain
  outside this local audit and pending; this is not full ASVS certification.
- UI: initial22/24 with loading/focus warnings; focused re-review24/24 with no
  active defects. Existing real synthetic screenshots were inspected; no owner
  acceptance or new screenshots were fabricated.

Original reports and corrective dispositions are preserved. Late fixture source
label correction changes only truthful provenance; its exact affected lane was
rerun after the unchanged selected-cutover receipt.

## Deviations from plan

Bounded ownership expansions were reported to and authorized by the orchestrator
before fixes; all stay within Phase7. No architecture, provider, production or
security-gate change occurred.

1. **[Rule1 — Bugs]** Independent review found lost nested configured scope,
   ignored retention disclosure/deadline, whole-cycle budget applied only to HTTP,
   and huge Decimal exponent conversion escaping sanitized refusal. Fixed in
   existing services/scheduler with meaningful adverse-case tests.
2. **[Rule1 — UI]** Twenty-record loading shape and post-retry keyboard position
   violated the contract. Added RED component/browser assertions and bounded fixes.
3. **[Rule3 — Verification blockers]** Stale route allowlist, dated quote authority,
   weekday-only scheduler clocks, current-image historical seeds, pre-calendar
   inventory assertions and public synthetic collation probes blocked real gates.
   Fixtures now use actual historical source/verified dates, retain exact original
   package inventory plus separately fingerprinted additions, and preserve strict
   public recovery contracts. Legacy and successor lanes remain explicit.
4. **[Rule2 — Documentation parity]** CLAUDE.md's common coverage command must
   match CI exactly; updated that command only, retaining shared policy.

## TDD gate compliance

Task1 has meaningful RED→GREEN commits for gate enforcement, runtime refusals
and UI contracts. Task2 is documentary acceptance execution/review: its tdd=true
annotation has no separate documentary RED commit. No import/missing-artifact
failure is counted as a behavioral RED. Phase-wide tdd_mode remainsfalse.

## Issues encountered

- Initial full browser runs exposed sign-in readiness races; the helper now waits
  for actual authenticated Markets UI. An incorrect intermediate /markets URL
  assumption was corrected; final full run passes at the actual root route.
- Interrupted overlapping focused test/preparatory fixture invocations are
  excluded from final evidence. Final backend/ops proofs are serial; final
  corrected identity run kept HEAD stable and cleanup was verified.
- One automatic scope review rejected a combined owned-fixture edit/test action.
  Explicit scope clarification and separate authorized actions resolved it;
  no bypass occurred.
- Upstream pandas deprecation warnings and nonroot pytest source-cache warning
  remain visible; no gate suppression or global package install was used.

## Known stubs and activation limits

No blocking local stubs. Denied/unknown/empty provider outcomes and disabled stock
execution are intentional tested scope. Actual quote/reference/action/status
rights/access,20symbol coverage and observed source freshness, plus official
current calendar evidence and owner UI acceptance remain Plan14 prerequisites.
Storage permission must cover DB/recovery-copy lifetimes or an approved verified
privileged cleanup process must already satisfy deadlines. Display redaction is
not storage cleanup; no DELETE privilege/job or financial-evidence removal added.

## Next plan readiness

07-14 can prepare its sanitized activation packet from reviewed local source,
lock/image/archive identities in07-LOCAL-PROOF.md. Private measurement/provider
actions require the explicit Plan14 checkpoint. No provider contact/signup/terms/
payment, publication, host installation, production migration or deployment is
inferred. All whole-phase requirement checkboxes remain pending until real final
verification; Phase7 is not marked complete here.

## Self-Check: PASSED

All listed created artifacts and recorded commits exist. Actual current-source
application, native runtime, strict scan, exact recovery, restricted TLS, historical
rollback, browser and independent review receipts are recorded. No unexpected
tracked-file deletion, unrelated .claude/ change, push or production action.
