# Phase 12 — Independent plan recheck after revision 1

**Date:** 2026-11-14
**Reviewer:** /root/phase12_plan_recheck1, fresh independent gsd-plan-checker
**Reviewed:** c39ba018d1de51dce0057b78148f334dc316cf24
**Verdict:** ISSUES FOUND — 4 BLOCKER, 0 WARNING, down from 8 findings
**Scope:** 28 plans / 56 tasks / 18 waves; no runtime or implementation proof

## Issues

```yaml
issues:
  - id: P12-C02
    severity: BLOCKER
    dimension: task_completeness
    plan: "12-05, 12-06"
    task: "12-05-02, 12-06-02"
    field: "acceptance_criteria / done / success_criteria"
    evidence:
      - "12-05-PLAN.md:82,86 still require restricted-role stock SQL tests to pass."
      - "12-06-PLAN.md:81,85 still require all payment/correction authority and terminal-freeze proofs to pass."
      - "Both plans run in wave5; their actions explicitly defer real SQL execution to 12-07-01 in wave6."
    description: >-
      The commands and actions were corrected, but mandatory completion criteria
      still require the unavailable final-schema proofs. These plans cannot
      truthfully satisfy their own completion contract before dependent Plan07.
    fix_hint: >-
      Change both tasks' acceptance/done and plan success criteria to static
      asset-contract success plus collected final_sql scenarios. Keep actual
      restricted-role economic/forgery/freeze success exclusively in07-01.

  - id: P12-C06
    severity: BLOCKER
    dimension: cross_plan_data_contracts
    plan: "12-03, 12-04, 12-07, 12-12"
    field: "12-RESEARCH.md R1; migration/model/application contract"
    evidence:
      - "12-RESEARCH.md:399 explicitly includes stock_split_applications among tables gaining portfolio_id."
      - "12-RESEARCH.md:401 requires association through OLD.user_id and the owner's unique original Account."
      - "backend/app/models/corporate_action.py:224-279 defines StockSplitApplication as an instrument-global economic_event_id-unique row, without user_id."
      - "12-12-01/02 retain global application/unit ordering and per-root movement reconstruction."
    description: >-
      The resolved migration contract assigns a single portfolio to an
      instrument-global split application that can affect multiple owners.
      It has no OLD.user_id for the prescribed backfill and cannot truthfully
      receive one owned root. This contradicts the planned global split journal.
    fix_hint: >-
      Keep split applications global and exclude them from root association.
      Specify root ownership on split movements and application+portfolio
      once-only keys, retaining the global application/coin/unit cause FK.
      Reconcile R1, model/migration plans, SQL and recovery inventories. Add a
      legacy split spanning two users and subsequent same-user sibling split
      fixture proving unchanged global application IDs/digests.

  - id: P12-C07
    severity: BLOCKER
    dimension: key_links_planned
    plan: "12-03, 12-04, 12-07, 12-12, 12-17"
    task: "12-12-01"
    field: "Persisted digest-version contract"
    evidence:
      - "12-RESEARCH.md:407 requires owner_digest_version=2 in split evidence's immutable JSON payload."
      - "12-12-PLAN.md:72 explicitly requires that exact JSON contract."
      - "StockSplitApplication currently stores before_digest/after_digest text, with no JSON payload or version field."
      - "Plans03/04/07 allocate no concrete field/table for persisting the required marker."
    description: >-
      New digest interpretation depends on a persisted version marker whose
      storage, migration and immutable authority are not planned. A service-only
      marker cannot survive database reload or exact recovery.
    fix_hint: >-
      Define the actual persisted version representation and assign its model,
      migration, immutable guard, writer, reader and recovery inventory changes.
      For example, add a nullable immutable digest-version column with NULL
      interpreted as legacy v1 and explicit2 on new rows, preserving old digest
      bytes. Test mixed legacy/new applications, unsupported versions and exact
      restored interpretation.

  - id: P12-C08
    severity: BLOCKER
    dimension: dependency_correctness
    plan: "12-01, 12-04, 12-07"
    field: "Actual migration connection and pytest prerequisite"
    evidence:
      - "12-04-PLAN.md:67 and RESEARCH R1 require authenticated session_user=birja_migrator; SET ROLE is explicitly insufficient."
      - "backend/tests/conftest.py:67-89 unconditionally provisions the existing migration owner and upgrades through ordinary test Settings."
      - "backend/tests/test_migrations.py:44-51 creates birja_migrator NOLOGIN and rejects an existing LOGIN migrator."
      - "No plan owns adapting this prerequisite or explicitly supplies a separate authenticated-role fixture lane before04."
    description: >-
      The existing pytest migration setup cannot authenticate as the role now
      required for populated0016 association. Its ordinary connection is
      birja_test, while enabling migrator login conflicts with the unconditional
      test prerequisite. Generic fixture-builder prose leaves this execution
      prerequisite unresolved.
    fix_hint: >-
      Assign an early task to provide a guarded, genuinely authenticated
      birja_migrator migration connection and reconcile the existing prerequisite,
      or specify a fully separate disposable role/TLS harness unaffected by it.
      Add explicit file ownership/dependencies and tests asserting session_user
      for successful association, ordinary/SET ROLE refusal and interrupted
      resume. Do not weaken the production caller predicate.
```

## Prior finding disposition

C01 typed SDK objects, C03 retained compatibility matrix, C04 behavioral fixture
verification, W01 actual wiring, W02 specific threats and W03 per-file analogs
are resolved. C05 has explicit resolved design entries, but their split contract
introduced C06/C07 contradictions. C02 completion wording remains partly unresolved.

## Dimension outcomes and mechanical checks

- Seven primary IDs, owner context, deferred scope, architectural tiers, bounded
  file/task counts, structural DAG/waves, shared outputs, AGENTS/CLAUDE and
  pattern references pass.
- Completion consistency, migration test prerequisites, split ownership and
  persisted version wiring fail as above; overall Nyquist remains unapproved.
- All 28 frontmatter validations, all 28 structure validations and typed-object
  assertions pass. All 56 task commands exactly match VALIDATION. Existing local
  Git independently confirms the retained v0.5.0 pins.
- Keep nyquist_compliant and wave_0_complete false pending approval/execution.
- Strict full coverage/audits/five-image/recovery/roles/TLS and both blocking
  owner checkpoints remain explicit. No execution, edit, commit, provider,
  production, installation or branch operation occurred in this review.

Proceed to bounded revision 2 of at most 3; issue count decreased 8 → 4.
