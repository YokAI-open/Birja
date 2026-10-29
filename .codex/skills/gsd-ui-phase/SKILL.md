---
name: "gsd-ui-phase"
description: "Generate UI design contract (UI-SPEC.md) for frontend phases"
metadata:
  short-description: "Generate UI design contract (UI-SPEC.md) for frontend phases"
---

<codex_skill_adapter>
Read `.codex/GSD-ADAPTER.md` before executing this skill.
Invoke as `$gsd-ui-phase`; text after the invocation is `{{GSD_ARGS}}` (empty when omitted).
Resolve all project paths from the repository root.
</codex_skill_adapter>

<objective>
Create a UI design contract (UI-SPEC.md) for a frontend phase.
Orchestrates gsd-ui-researcher and gsd-ui-checker.
Flow: Validate → Research UI → Verify UI-SPEC → Done
</objective>

<execution_context>
@.codex/get-shit-done/workflows/ui-phase.md
@.codex/get-shit-done/references/ui-brand.md
</execution_context>

<context>
Phase number: {{GSD_ARGS}} — optional, auto-detects next unplanned phase if omitted.
</context>

<process>
Execute end-to-end.
Preserve all workflow gates.
</process>
