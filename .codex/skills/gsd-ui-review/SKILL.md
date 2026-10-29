---
name: "gsd-ui-review"
description: "Retroactive 6-pillar visual audit of implemented frontend code"
metadata:
  short-description: "Retroactive 6-pillar visual audit of implemented frontend code"
---

<codex_skill_adapter>
Read `.codex/GSD-ADAPTER.md` before executing this skill.
Invoke as `$gsd-ui-review`; text after the invocation is `{{GSD_ARGS}}` (empty when omitted).
Resolve all project paths from the repository root.
</codex_skill_adapter>

<objective>
Conduct a retroactive 6-pillar visual audit. Produces UI-REVIEW.md with
graded assessment (1-4 per pillar). Works on any project.
Output: {phase_num}-UI-REVIEW.md
</objective>

<execution_context>
@.codex/get-shit-done/workflows/ui-review.md
@.codex/get-shit-done/references/ui-brand.md
</execution_context>

<context>
Phase: {{GSD_ARGS}} — optional, defaults to last completed phase.
</context>

<process>
Execute end-to-end.
Preserve all workflow gates.
</process>
