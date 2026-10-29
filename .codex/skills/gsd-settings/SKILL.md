---
name: "gsd-settings"
description: "Configure GSD workflow toggles and model profile"
metadata:
  short-description: "Configure GSD workflow toggles and model profile"
---

<codex_skill_adapter>
Read `.codex/GSD-ADAPTER.md` before executing this skill.
Invoke as `$gsd-settings`; text after the invocation is `{{GSD_ARGS}}` (empty when omitted).
Resolve all project paths from the repository root.
</codex_skill_adapter>

<objective>
Interactive configuration of GSD workflow agents and model profile via multi-question prompt.

Routes to the settings workflow which handles:
- Config existence ensuring
- Current settings reading and parsing
- Interactive 5-question prompt (model, research, plan_check, verifier, branching)
- Config merging and writing
- Confirmation display with quick command references
</objective>

<execution_context>
@.codex/get-shit-done/workflows/settings.md
</execution_context>

<process>
Execute end-to-end.
</process>
