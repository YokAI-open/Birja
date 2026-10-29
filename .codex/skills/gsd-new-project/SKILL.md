---
name: "gsd-new-project"
description: "Initialize a new project with deep context gathering and PROJECT.md"
metadata:
  short-description: "Initialize a new project with deep context gathering and PROJECT.md"
---

<codex_skill_adapter>
Read `.codex/GSD-ADAPTER.md` before executing this skill.
Invoke as `$gsd-new-project`; text after the invocation is `{{GSD_ARGS}}` (empty when omitted).
Resolve all project paths from the repository root.
</codex_skill_adapter>

<runtime_note>
**Copilot (VS Code):** Use `vscode_askquestions` wherever this workflow calls `AskUserQuestion`. They are equivalent — `vscode_askquestions` is the VS Code Copilot implementation of the same interactive question API.
</runtime_note>

<context>
**Flags:**
- `--auto` — Automatic mode. After config questions, runs research → requirements → roadmap without further interaction. Expects idea document via @ reference.
</context>

<objective>
Initialize a new project through unified flow: questioning → research (optional) → requirements → roadmap.

**Creates:**
- `.planning/PROJECT.md` — project context
- `.planning/config.json` — workflow preferences
- `.planning/research/` — domain research (optional)
- `.planning/REQUIREMENTS.md` — scoped requirements
- `.planning/ROADMAP.md` — phase structure
- `.planning/STATE.md` — project memory

**After this command:** Run `$gsd-plan-phase 1` to start execution.
</objective>

<execution_context>
@.codex/get-shit-done/workflows/new-project.md
@.codex/get-shit-done/references/questioning.md
@.codex/get-shit-done/references/ui-brand.md
@.codex/get-shit-done/templates/project.md
@.codex/get-shit-done/templates/requirements.md
</execution_context>

<process>
Execute end-to-end.
Preserve all workflow gates (validation, approvals, commits, routing).
</process>
