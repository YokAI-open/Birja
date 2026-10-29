---
name: "gsd-resume-work"
description: "Resume work from previous session with full context restoration"
metadata:
  short-description: "Resume work from previous session with full context restoration"
---

<codex_skill_adapter>
Read `.codex/GSD-ADAPTER.md` before executing this skill.
Invoke as `$gsd-resume-work`; text after the invocation is `{{GSD_ARGS}}` (empty when omitted).
Resolve all project paths from the repository root.
</codex_skill_adapter>

<objective>
Restore complete project context and resume work seamlessly from previous session.

Routes to the resume-project workflow which handles:

- STATE.md loading (or reconstruction if missing)
- Checkpoint detection (.continue-here files)
- Incomplete work detection (PLAN without SUMMARY)
- Status presentation
- Context-aware next action routing
  </objective>

<execution_context>
@.codex/get-shit-done/workflows/resume-project.md
</execution_context>

<process>
Execute end-to-end.
</process>
