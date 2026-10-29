---
name: "gsd-verify-work"
description: "Validate built features through conversational UAT"
metadata:
  short-description: "Validate built features through conversational UAT"
---

<codex_skill_adapter>
Read `.codex/GSD-ADAPTER.md` before executing this skill.
Invoke as `$gsd-verify-work`; text after the invocation is `{{GSD_ARGS}}` (empty when omitted).
Resolve all project paths from the repository root.
</codex_skill_adapter>

<objective>
Validate built features through conversational testing with persistent state.

Purpose: Confirm what the agent built actually works from user's perspective. One test at a time, plain text responses, no interrogation. When issues are found, automatically diagnose, plan fixes, and prepare for execution.

Output: {phase_num}-UAT.md tracking all test results. If issues found: diagnosed gaps, verified fix plans ready for $gsd-execute-phase
</objective>

<execution_context>
@.codex/get-shit-done/workflows/verify-work.md
@.codex/get-shit-done/templates/UAT.md
</execution_context>

<context>
Phase: {{GSD_ARGS}} (optional)
- If provided: Test specific phase (e.g., "4")
- If not provided: Check for active sessions or prompt for phase

Context files are resolved inside the workflow (`init verify-work`) and delegated via `<files_to_read>` blocks.
</context>

<process>
Execute end-to-end.
Preserve all workflow gates (session management, test presentation, diagnosis, fix planning, routing).
</process>
