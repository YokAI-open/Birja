---
name: "gsd-thread"
description: "Manage persistent context threads for cross-session work"
metadata:
  short-description: "Manage persistent context threads for cross-session work"
---

<codex_skill_adapter>
Read `.codex/GSD-ADAPTER.md` before executing this skill.
Invoke as `$gsd-thread`; text after the invocation is `{{GSD_ARGS}}` (empty when omitted).
Resolve all project paths from the repository root.
</codex_skill_adapter>

<objective>
Create, list, close, or resume persistent context threads. Threads are lightweight
cross-session knowledge stores for work that spans multiple sessions but
doesn't belong to any specific phase.
</objective>

<execution_context>
@.codex/get-shit-done/workflows/thread.md
</execution_context>

<process>
Execute end-to-end.
</process>
