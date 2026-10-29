---
name: "gsd-cleanup"
description: "Archive accumulated phase directories from completed milestones"
metadata:
  short-description: "Archive accumulated phase directories from completed milestones"
---

<codex_skill_adapter>
Read `.codex/GSD-ADAPTER.md` before executing this skill.
Invoke as `$gsd-cleanup`; text after the invocation is `{{GSD_ARGS}}` (empty when omitted).
Resolve all project paths from the repository root.
</codex_skill_adapter>

<objective>
Archive phase directories from completed milestones into `.planning/milestones/v{X.Y}-phases/`.

Use when `.planning/phases/` has accumulated directories from past milestones.
</objective>

<execution_context>
@.codex/get-shit-done/workflows/cleanup.md
</execution_context>

<process>
Execute end-to-end.
Identify completed milestones, show a dry-run summary, and archive on confirmation.
</process>
