---
name: "gsd-stats"
description: "Display project statistics — phases, plans, requirements, git metrics, and timeline"
metadata:
  short-description: "Display project statistics — phases, plans, requirements, git metrics, and timeline"
---

<codex_skill_adapter>
Read `.codex/GSD-ADAPTER.md` before executing this skill.
Invoke as `$gsd-stats`; text after the invocation is `{{GSD_ARGS}}` (empty when omitted).
Resolve all project paths from the repository root.
</codex_skill_adapter>

<objective>
Display comprehensive project statistics including phase progress, plan execution metrics, requirements completion, git history stats, and project timeline.
</objective>

<execution_context>
@.codex/get-shit-done/workflows/stats.md
</execution_context>

<process>
Execute end-to-end.
</process>
