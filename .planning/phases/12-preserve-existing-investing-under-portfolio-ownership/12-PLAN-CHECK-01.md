# Phase 12 — Independent plan check 1

**Date:** 2026-11-14
**Reviewer:** /root/phase12_plan_check, independent gsd-plan-checker
**Reviewed source:** plans d3614a6, tracked pattern input a829ae9
**Verdict:** ISSUES FOUND — 5 BLOCKER, 3 WARNING; revision required
**Scope:** 28 plans, 56 tasks, 18 waves; no execution or runtime test claims

All 28 SDK structure checks pass, the listed dependency graph is acyclic and
same-wave files are disjoint. Those checks do not resolve these findings.

## Issues

```yaml
issues:
  - id: P12-C01
    plan: "12-01 through 12-28"
    dimension: verification_derivation
    severity: BLOCKER
    field: must_haves.artifacts / must_haves.key_links
    description: >-
      The installed SDK does not parse the inline flow-object lists into objects.
      For example, frontmatter.get for 12-15 returns artifact strings
      "{path:backend/app/api/v2/portfolios.py" and "provides:...}" separately.
      key_links is similarly fragmented. Structure verification reports valid
      despite this invalid downstream contract.
    fix_hint: >-
      Rewrite these fields as block-style YAML mappings. Query every plan with
      the installed SDK and assert artifacts contain path/provides objects and
      key_links contain from/to/via objects.

  - id: P12-C02
    plan: "12-02, 12-03; affected downstream verification sequencing"
    dimension: dependency_correctness
    severity: BLOCKER
    task: "12-03-02"
    file: "12-03-PLAN.md:73"
    description: >-
      Wave 3 requires cross-root entitlement/payment/supersession tuples to be
      rejected by final-schema fixtures, but final compound constraints are
      created only by 12-07 in wave 6. Model declarations cannot change PostgreSQL.
      Existing tests/conftest.py upgrades the actual Alembic head, which remains
      0014 before 12-04. Similar early database expectations occur in 12-02-02.
      The plan therefore cannot meet its required green verification in order.
    fix_hint: >-
      Keep early checks explicitly limited to model metadata. Assign real SQL
      negative assertions to a concrete task after 12-07, and list their exact
      commands there. Do not duplicate the final schema through manual test DDL
      or use skipped assertions. Also specify test-router composition for API
      checks preceding the actual router mount in 12-15.

  - id: P12-C03
    plan: "12-18"
    dimension: cross_plan_data_contracts
    severity: BLOCKER
    task: "12-18-01 / 12-18-02"
    file: "12-18-PLAN.md:75"
    description: >-
      Retained-schema proof lacks an application-source compatibility mechanism.
      Existing ops-fixtures.py successor_roundtrips executes current-source
      stock-runtime-fixture programs on 0013/0014 and dividend programs on 0014.
      Those programs import the models/services that earlier plans make
      portfolio-required. Leaving old calls fails new signatures; adding
      portfolio arguments still queries columns absent from retained schemas.
      Merely promising to preserve historical lanes does not resolve this.
    fix_hint: >-
      Specify explicit current0017 versus retained-schema dispatch, with compatible
      retained application/proof source pinned and authenticated. Name the
      fixture entrypoints and source/schema matrix. Add negative contracts
      rejecting current portfolio consumers against old schemas and any silent
      upgrade or changed-source substitution. Preserve the same-archive,
      exact-row, role/TLS and rollback proofs.

  - id: P12-C04
    plan: "12-18"
    dimension: nyquist_compliance
    severity: BLOCKER
    task: "12-18-01"
    file: "12-18-PLAN.md:61"
    description: >-
      The sole automated command is portfolio-execution-fixture.py --help.
      Help output cannot verify the task's independent economic oracle,
      immutable snapshots, comparison behavior or runnable cold comparison.
      A broken fixture can pass this check unchanged.
    fix_hint: >-
      Create and run behavioral fixture-contract tests that exercise its command
      modes and reject independently mutated economics, lineage and snapshots.
      Assign an actual isolated fixture smoke invocation to the appropriate
      ready harness. Keep the complete real cold restore in 12-27.

  - id: P12-C05
    plan: null
    dimension: research_resolution
    severity: BLOCKER
    file: "12-RESEARCH.md:393"
    description: >-
      The Open Questions / Implementation Proofs section has neither a RESOLVED
      section marker nor resolved individual entries. It still says to finalize
      object/function definitions and the finite-owner predicate, and to define
      response/status schemas. Dimension 11 explicitly blocks unresolved
      research questions.
    fix_hint: >-
      Resolve remaining design choices and record their concrete contracts and
      owning plans. Mark resolved questions explicitly. Separate genuinely
      pending execution proofs into a validation-obligations section without
      claiming those proofs have run.

  - id: P12-W01
    plan: "12-02 through 12-28"
    dimension: key_links_planned
    severity: WARNING
    field: must_haves.key_links
    description: >-
      Links such as "12-15 tasks -> 12-14 outputs via explicit dependency and
      verified interface contracts" repeat the dependency graph rather than
      identify functional wiring. They do not describe actual artifact calls,
      router mounting, composite FKs, cursor transport or fixture invocation.
    fix_hint: >-
      Replace placeholder links with actual source/destination files and the
      call, constraint, route registration or transport contract connecting
      them. Reference the implementing task and behavioral proof.

  - id: P12-W02
    plan: "12-01 through 12-28"
    dimension: threat_mitigation_specificity
    severity: WARNING
    field: threat_model
    description: >-
      The repeated threat tables use generic Tasks1/2 mitigation prose and
      "where applicable" tests. Concrete security work exists in several task
      actions, but the register does not map each threat to its actual control
      and negative proof. The validation table repeats those generic IDs.
    fix_hint: >-
      Map each applicable threat to a named boundary, implementing task/control
      and exact negative test or harness mode. Mark irrelevant categories
      explicitly instead of implying every plan implements all three controls.

  - id: P12-W03
    plan: "12-23 and other new-file plans"
    dimension: pattern_compliance
    severity: WARNING
    task: "12-23-01"
    file: "12-23-PLAN.md:57"
    description: >-
      New-file actions do not consistently reference their mapped analogs.
      For example PortfolioContext is mapped to StockAttribution.tsx in
      PATTERNS.md, but task 12-23-01 names only UI-SPEC and generic existing
      patterns. A blanket context reference to PATTERNS.md does not satisfy
      the per-file analog check.
    fix_hint: >-
      Add the relevant analog files and retained pattern to each affected action
      or read_first block. For novel mechanisms, explicitly reference the
      relevant research section and required new proof.
```

## Dimension outcomes

- Requirement coverage, bounded plan/task/file scope, structural DAG/waves and
  same-wave ownership pass; all seven primary IDs have substantive coverage.
- Task fields exist, but executable order/proof are blocked by C02/C04.
- Artifact contract/verification derivation fail C01; key links warn W01.
- Nyquist fails C02/C04 despite syntactically continuous automated tags and
  a complete task map; collection-only precursor checks cannot become runtime proof.
- Cross-plan retained-source compatibility fails C03; research resolution fails C05.
- Context fidelity, architectural tiers, AGENTS/CLAUDE scope and no unauthorized
  reduction pass. API v2 is a legitimate versioned compatibility contract.
- Threat specificity warns W02; per-file pattern references warn W03.
- Final planned gates retain strict coverage, audits, five-image scans, serial
  source/archive binding, roles/TLS and both blocking owner checkpoints.

Return to a fresh planner revision, then independently recheck. The reviewer
performed no runtime suites, Docker/provider operations, installations, edits,
commits or branch changes. Runtime and owner acceptance remain unperformed.
