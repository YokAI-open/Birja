---
name: "gsd-help"
description: "Show available GSD commands and usage guide"
metadata:
  short-description: "Show available GSD commands and usage guide"
---

<codex_skill_adapter>
Read `.codex/GSD-ADAPTER.md` before executing this skill.
Invoke as `$gsd-help`; text after the invocation is `{{GSD_ARGS}}` (empty when omitted).
Resolve all project paths from the repository root.
</codex_skill_adapter>

<objective>
Display the complete GSD command reference.

Output ONLY the reference content below. Do NOT add:
- Project-specific analysis
- Git status or file context
- Next-step suggestions
- Any commentary beyond the reference
</objective>

<execution_context>
@.codex/get-shit-done/workflows/help.md
</execution_context>

<process>
Execute end-to-end.
Display the reference content directly — no additions or modifications.
</process>
