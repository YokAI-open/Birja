---
phase: 08-corporate-action-safe-ownership
plan: "03"
subsystem: accounting
tags: [corporate-actions, permissions, decimal, fractions, calendar]
requires:
  - phase: 07-permitted-stock-discovery
    provides: "Product admission and genuine reviewed regular-session evaluator"
provides:
  - "Independent REST/replay action authority and durable accounting/backup scope"
  - "Frozen normalized action, classification, cutoff and exact all-owner split contracts"
  - "Fail-closed action availability independent of persistent economic holds"
affects: [08-04, 08-05, 08-06, 08-07, 08-08, 08-09]
tech-stack:
  added: []
  patterns: [exact-rational-splits, exclusive-ex-date-open, product-specific-retention]
key-files:
  created:
    - backend/app/services/corporate_action_rules.py
    - backend/app/services/stock_action_rules.py
    - backend/tests/test_corporate_action_rules.py
  modified:
    - backend/app/services/stock_admission.py
    - backend/tests/test_stock_admission.py
key-decisions:
  - "Action permission uses alpaca-corporate-actions and reviewed durable-accounting/backup rights; IEX evidence remains insufficient."
  - "Normalize absent provider facts as nullable values; local verification and economic ordering are explicit inputs, never invented source revisions."
  - "Persistent holds outrank recovered monitoring; known boundaries cap validity and post-split quotes need matching local units and strictly later source time."
requirements-completed: []
requirements-addressed: [DIV-01, DIV-02, ACT-01, ACT-02, ACT-03]
duration: 10 min
completed: 2026-11-11
---

# Phase 8 Plan 03: Exact Action Rules Summary

**Independent action authority, genuine exclusive dividend cutoffs and rational all-owner split plans refuse uncertain economics without changing cash or enabling stock execution.**

## Performance and Accomplishments

- Approximately10minutes, 2026-11-11, completed10:47UTC;2tasks and5source/test files.
- `ProductAdmission` remains call compatible for old products; optional `capability` selects independently reviewed REST/replay authority. Action evidence requires actual normalized provider fields, exact20-symbol REST scope, account/server/audience, finite operational quotas, durable accounting and backup/restore rights with explicit retention mode. All-US replay ingress is separately required whenever replay is admitted. REST-only permission never authorizes replay. Other product IEX limits remain unchanged.
- Frozen `NormalizedAction` separates provider/process/source/observation/economic facts. `ActionClassification`, `CutoffEvidence`, `SplitOwner`, `SplitPlan` and `ActionDecision` are exported typed interfaces. Supported ordinary USD dividends require explicit nonforeign/nonspecial/ordinary facts, verified identity and date semantics. Missing currency, unsupported events, conflicts, cancellation and identity changes do not create guessed effects.
- `dividend_cutoff` derives the actual reviewed ex-date regular opening with `build_sessions`, preserving calendar generation/version and exclusive cutoff. Genuine holidays, DST and shortened sessions are tested. Same-boundary dividends require explicit pre/post-split units and corresponding economic order.
- Forward splits use bounded Decimal-to-Fraction exact ratios. Every owner must have finite whole quantities and finite cent basis within existing schema bounds; one fractional/overflow/duplicate/invalid owner rejects the entire immutable plan. Total basis remains exactly unchanged, including zero-owner applications; no rounding, cash-in-lieu or inverse adjustment exists.
- Safety states retain persistent issuer holds after healthy monitoring, deny stale/unknown/incomplete authority, cap validity at known future boundaries and require exact quote-unit epoch plus strictly post-boundary source time after splits. Execution remains false for every decision.

## Task Commits and TDD Gates

1. Task08-03-01 RED `1af79d6`: an actual behavioral assertion failed because old IEX action evidence was incorrectly admitted. GREEN `f7a31ec`: independent product/capability/storage authority;100tests passed0.50s.
2. Task08-03-02 RED `5dca2bd`: frozen fail-closed typed scaffolds were importable and supported-dividend behavior failed as `uncertain`, rather than an import error. GREEN `f705efb`: complete rules, adversarial fixtures and exact safety decisions.

Both tasks have observed RED and subsequent GREEN commits. The initial typed scaffold functions are fully implemented; no remaining implementation stub is required by this plan.

## Verification Executed

- `uv run pytest tests/test_stock_admission.py tests/test_corporate_action_rules.py --cov=app.services.stock_admission --cov=app.services.corporate_action_rules --cov=app.services.stock_action_rules --cov-branch --cov-report=term-missing --cov-fail-under=100 -q`: **175passed2.06s; all3modules100% statements/branches**,273statements/114branches.
- `uv run pytest tests/test_stock_sessions.py tests/test_stock_quote_rules.py tests/test_stock_admission.py tests/test_corporate_action_rules.py -q -x`: **259passed4.64s**, including genuine calendar and old quote/product behavior.56existing upstream pandas deprecation warnings remain; no dependency change or gate waiver.
- Scoped Ruff check and format check: **5files pass**. `uv run mypy app/services/stock_admission.py app/services/corporate_action_rules.py app/services/stock_action_rules.py`: **3source files pass**. `git diff --check` passes.
- Tests use synthetic evidence and the existing isolated test Redis/PostgreSQL fixtures only; no provider keys, private API, production, timer or B2 access. Sandbox socket restrictions required an authorized isolated-test escalation. No dependency installation.
- Consulted official [Python3.14 Fraction](https://docs.python.org/3.14/library/fractions.html) and [Decimal](https://docs.python.org/3.14/library/decimal.html) references. Exact bounded conversion is used without floating point or approximation.
- Stub/security scan: no TODO/FIXME/placeholder remains; no endpoint, credential discovery, schema or new infrastructure introduced. Existing trust boundaries are covered by T-08-03-01/02.

## Interfaces and Remaining Gates

`classify_action(action)` returns classification plus verified action/ratio only on supported economics. `dividend_cutoff(action, exchange, now, authority, account/server)` returns verified cutoff orNone. `plan_forward_split(action, owners)` returns one all-owner plan or an empty held result. `evaluate_action_state` takes explicit current rights/health/coverage/hold/boundary/unit evidence; it is a pure decision and establishes neither permission nor DB completeness itself. Plans04–09 supply actual bounded adapters, persistence, monitoring and final authority reads.

Whole-phase DIV/ACT requirements remain unchecked until final verification. Wave1 integration remains **pending the separate Plan01 schema-review fixes** (alias observation and causal FK consistency); this plan does not claim those reviewed findings resolved. Full-suite/image/recovery/concurrency and owner/external activation gates remain later plans.

The frozen Phase7 one-shot includes the prior `stock_admission.py` hash. This authorized source change intentionally makes that manifest stale: its unchanged runner must fail closed before private calls at opening. No hash refresh, relaunch, altered process or new campaign is authorized here. Its actual result and any separately reviewed revalidation remain deferred; no measurement success is claimed. Owner UI acceptance and prior Phase7 evidence remain preserved.

## Deviations and Issues

No architectural deviation. Added explicit exact existing cent-basis/quantity bounds and boolean/date checks as required correctness safeguards. The RED commit includes importable fail-closed contract scaffolds solely to observe meaningful behavioral RED before implementation. One added synthetic calendar test initially referenced a local fixture before assignment; corrected ordering, then final100%coverage and regressions pass. SDK metric command's documented positional form returned `phase, plan, and duration required`; scoped metric is recorded directly without inventing a successful SDK result.

## Self-Check: PASSED

All3created files exist; all4task commits are present; final tests, scoped static checks and exact coverage pass. No unrelated edits staged. Nothing pushed or deployed.
