---
name: "gsd-extract-learnings"
description: "Extract decisions, lessons, patterns, and surprises from completed phase artifacts"
metadata:
  short-description: "Extract decisions, lessons, patterns, and surprises from completed phase artifacts"
---

<codex_skill_adapter>
Read `.codex/GSD-ADAPTER.md` before executing this skill.
Invoke as `$gsd-extract-learnings`; text after the invocation is `{{GSD_ARGS}}` (empty when omitted).
Resolve all project paths from the repository root.
</codex_skill_adapter>

<objective>
Extract structured learnings from completed phase artifacts (PLAN.md, SUMMARY.md, VERIFICATION.md, UAT.md, STATE.md) into a LEARNINGS.md file that captures decisions, lessons learned, patterns discovered, and surprises encountered.
</objective>

<execution_context>
@.codex/get-shit-done/workflows/extract-learnings.md
</execution_context>

Execute the extract-learnings workflow from @.codex/get-shit-done/workflows/extract-learnings.md end-to-end.
