---
name: "gsd-pause-work"
description: "Create context handoff when pausing work mid-phase"
metadata:
  short-description: "Create context handoff when pausing work mid-phase"
---

<codex_skill_adapter>
Read `.codex/GSD-ADAPTER.md` before executing this skill.
Invoke as `$gsd-pause-work`; text after the invocation is `{{GSD_ARGS}}` (empty when omitted).
Resolve all project paths from the repository root.
</codex_skill_adapter>

<objective>
Create `.continue-here.md` handoff file to preserve complete work state across sessions.

Routes to the pause-work workflow which handles:
- Current phase detection from recent files
- Complete state gathering (position, completed work, remaining work, decisions, blockers)
- Handoff file creation with all context sections
- Git commit as WIP
- Resume instructions
</objective>

<execution_context>
@.codex/get-shit-done/workflows/pause-work.md
</execution_context>

<context>
State and phase progress are gathered in-workflow with targeted reads.
</context>

<process>
If `--report` is in {{GSD_ARGS}}:
Read and execute `.codex/get-shit-done/workflows/session-report.md` end-to-end.

**Follow the pause-work workflow**.

The workflow handles all logic including:
1. Phase directory detection
2. State gathering with user clarifications
3. Handoff file writing with timestamp
4. Git commit
5. Confirmation with resume instructions
</process>
