---
name: "gsd-ship"
description: "Create PR, run review, and prepare for merge after verification passes"
metadata:
  short-description: "Create PR, run review, and prepare for merge after verification passes"
---

<codex_skill_adapter>
Read `.codex/GSD-ADAPTER.md` before executing this skill.
Invoke as `$gsd-ship`; text after the invocation is `{{GSD_ARGS}}` (empty when omitted).
Resolve all project paths from the repository root.
</codex_skill_adapter>

<objective>
Bridge local completion → merged PR. After $gsd-verify-work passes, ship the work: push branch, create PR with auto-generated body, optionally trigger review, and track the merge.

Closes the plan → execute → verify → ship loop.
</objective>

<execution_context>
@.codex/get-shit-done/workflows/ship.md
</execution_context>

Execute the ship workflow from @.codex/get-shit-done/workflows/ship.md end-to-end.
