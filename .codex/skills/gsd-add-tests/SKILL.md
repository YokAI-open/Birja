---
name: "gsd-add-tests"
description: "Generate tests for a completed phase based on UAT criteria and implementation"
metadata:
  short-description: "Generate tests for a completed phase based on UAT criteria and implementation"
---

<codex_skill_adapter>
Read `.codex/GSD-ADAPTER.md` before executing this skill.
Invoke as `$gsd-add-tests`; text after the invocation is `{{GSD_ARGS}}` (empty when omitted).
Resolve all project paths from the repository root.
</codex_skill_adapter>

<objective>
Generate unit and E2E tests for a completed phase, using its SUMMARY.md, CONTEXT.md, and VERIFICATION.md as specifications.

Analyzes implementation files, classifies them into TDD (unit), E2E (browser), or Skip categories, presents a test plan for user approval, then generates tests following RED-GREEN conventions.

Output: Test files committed with message `test(phase-{N}): add unit and E2E tests from add-tests command`
</objective>

<execution_context>
@.codex/get-shit-done/workflows/add-tests.md
</execution_context>

<context>
Phase: {{GSD_ARGS}}

@.planning/STATE.md
@.planning/ROADMAP.md
</context>

<process>
Execute end-to-end.
Preserve all workflow gates (classification approval, test plan approval, RED-GREEN verification, gap reporting).
</process>
