---
name: "gsd-explore"
description: "Socratic ideation and idea routing — think through ideas before committing to plans"
metadata:
  short-description: "Socratic ideation and idea routing — think through ideas before committing to plans"
---

<codex_skill_adapter>
Read `.codex/GSD-ADAPTER.md` before executing this skill.
Invoke as `$gsd-explore`; text after the invocation is `{{GSD_ARGS}}` (empty when omitted).
Resolve all project paths from the repository root.
</codex_skill_adapter>

<objective>
Open-ended Socratic ideation session. Guides the developer through exploring an idea via
probing questions, optionally spawns research, then routes outputs to the appropriate GSD
artifacts (notes, todos, seeds, research questions, requirements, or new phases).

Accepts an optional topic argument: `$gsd-explore authentication strategy`
</objective>

<execution_context>
@.codex/get-shit-done/workflows/explore.md
</execution_context>

<process>
Execute end-to-end.
</process>
