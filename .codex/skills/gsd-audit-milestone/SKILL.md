---
name: "gsd-audit-milestone"
description: "Audit milestone completion against original intent before archiving"
metadata:
  short-description: "Audit milestone completion against original intent before archiving"
---

<codex_skill_adapter>
Read `.codex/GSD-ADAPTER.md` before executing this skill.
Invoke as `$gsd-audit-milestone`; text after the invocation is `{{GSD_ARGS}}` (empty when omitted).
Resolve all project paths from the repository root.
</codex_skill_adapter>

<objective>
Verify milestone achieved its definition of done. Check requirements coverage, cross-phase integration, and end-to-end flows.

**This command IS the orchestrator.** Reads existing VERIFICATION.md files (phases already verified during execute-phase), aggregates tech debt and deferred gaps, then spawns integration checker for cross-phase wiring.
</objective>

<execution_context>
@.codex/get-shit-done/workflows/audit-milestone.md
</execution_context>

<context>
Version: {{GSD_ARGS}} (optional — defaults to current milestone)

Core planning files are resolved in-workflow (`init milestone-op`) and loaded only as needed.

**Completed Work:**
Glob: .planning/phases/*/*-SUMMARY.md
Glob: .planning/phases/*/*-VERIFICATION.md
</context>

<process>
Execute end-to-end.
Preserve all workflow gates (scope determination, verification reading, integration check, requirements coverage, routing).
</process>
