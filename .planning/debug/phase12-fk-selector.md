---
status: verifying
trigger: Phase12 accepted-risk full qualification metadata constraint selection failure
created: 2026-11-17
updated: 2026-11-17
---

## Symptoms

Expected: all ownership constraints checked deterministically with no weakened assertions.
Actual: full3114-test run at e4c0a9f had3113pass/1failure in test_model_metadata_dividend_decisions_cannot_cross_root_causal_chains.
Evidence: /tmp/phase12-accepted-security-e4c0a9f.{log,source.json,result.json}; actual command failed and cleaned all6owned projects. Recovery did not start.
Failure: for payment_id, next(fk for fk in an unordered constraint set if field in fk.column_keys) chose previous_application_id FK, which also contains payment_id. Historical whole run passed at d9da271; no model/schema change in this audit-only diff.

## Current Focus

reasoning_checkpoint:
  hypothesis: The payment_id containment selector picks one of three distinct valid constraints depending on set iteration order.
  confirming_evidence:
    - Actual full-run traceback selected previous_application_id's composite FK for payment_id.
    - Controlled permutations of the actual matching constraint objects produce all three names; the named payment FK has the exact expected ordered tuple.
  falsification_test: Named payment constraint missing, duplicated or with incorrect ordered columns/ownership would make the same assertions fail rather than selecting an unrelated FK.
  fix_rationale: Select each unique documented constraint by stable name, independently assert its complete ordered source tuple and referred owner columns.
  blind_spots: Full qualification remains required after the local focused proof; no actual schema/runtime change is proposed.
Next: parent performs independent review of the test-only diff, commits it and reruns full security/recovery qualification. Private proof and successful focused log: /tmp/phase12-fk-selector-proof.py and /tmp/phase12-fk-selector-targeted.log.

## Evidence

- Controlled permutations of the three actual payment_id-containing constraints yield fk_dividend_decision_application_owner, fk_dividend_decision_payment_owner and fk_dividend_decision_previous_owner. Thus the original selector is ambiguous independently of the database or fixture state.
- The actual uniquely named payment constraint's tuple is payment_id,event_id,portfolio_id,user_id,coin_id, matching the existing assertion. No model/schema change is required.
- Fixed test passes all six permutations of the three overlapping actual constraints plus reversed complete order. Five negative mutations are refused: missing named constraint, duplicate name, wrong source order, omitted source portfolio ownership and wrong referred portfolio ownership. Only built-in synthetic wrappers around actual metadata were used; the application metadata was not changed.
- Actual isolated pytest of the complete test_portfolio_authority.py file passed11/11 in2.57seconds. The explicit synthetic test stack was started fresh and removed in finally; command exit0 and cleanup recorded in /tmp/phase12-fk-selector-targeted.log.
- Ruff check and format-check of the changed test file pass; git diff-check passes. No model, migration, financial/runtime, package, lock or audit-policy change was made.

## Resolution

root_cause: Unordered first containment match selects one of three distinct causal foreign keys because payment_id occurs in each.
fix: Map the four existing expected tuples to their exact documented FK names, require exactly one matching constraint, and retain full ordered local and referred portfolio/user assertions.
verification: Controlled ordering and five negative mutation cases pass; actual complete focused authority file11/11passes in2.57seconds, Ruff/format/diff-check pass and owned test stack cleaned. Full qualification remains required afterward; this record does not mark the phase complete.
files_changed: [backend/tests/test_portfolio_authority.py]

## Boundaries

Only backend/tests/test_portfolio_authority.py and this debug record may change. No model/schema/financial rules, packages, lock, CI/audit gate or production changes. Preserve failed full receipt and require fresh full qualification after reviewed repair.
