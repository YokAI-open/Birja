---
name: "gsd-fast"
description: "Execute a trivial task inline — no subagents, no planning overhead"
metadata:
  short-description: "Execute a trivial task inline — no subagents, no planning overhead"
---

<codex_skill_adapter>
Read `.codex/GSD-ADAPTER.md` before executing this skill.
Invoke as `$gsd-fast`; text after the invocation is `{{GSD_ARGS}}` (empty when omitted).
Resolve all project paths from the repository root.
</codex_skill_adapter>

<objective>
Execute a trivial task directly in the current context without spawning subagents
or generating PLAN.md files. For tasks too small to justify planning overhead:
typo fixes, config changes, small refactors, forgotten commits, simple additions.

This is NOT a replacement for $gsd-quick — use $gsd-quick for anything that
needs research, multi-step planning, or verification. $gsd-fast is for tasks
you could describe in one sentence and execute in under 2 minutes.
</objective>

<execution_context>
@.codex/get-shit-done/workflows/fast.md
</execution_context>

<process>
Execute end-to-end.
</process>
