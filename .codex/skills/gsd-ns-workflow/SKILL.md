---
name: "gsd-ns-workflow"
description: "workflow | discuss plan execute verify phase progress"
metadata:
  short-description: "workflow | discuss plan execute verify phase progress"
---

<codex_skill_adapter>
Read `.codex/GSD-ADAPTER.md` before executing this skill.
Invoke as `$gsd-ns-workflow`; text after the invocation is `{{GSD_ARGS}}` (empty when omitted).
Resolve all project paths from the repository root.
</codex_skill_adapter>

Route to the appropriate phase-pipeline skill based on the user's intent.
Sub-skill names below are post-#2790 consolidated targets — `gsd-phase`
absorbs the former add/insert/remove/edit-phase commands and `gsd-progress`
absorbs the former next/do commands.

| User wants | Invoke |
|---|---|
| Gather context before planning | gsd-discuss-phase |
| Clarify what a phase delivers | gsd-spec-phase |
| Create a PLAN.md | gsd-plan-phase |
| Execute plans in a phase | gsd-execute-phase |
| Verify built features through UAT | gsd-verify-work |
| Add / insert / remove / edit a phase | gsd-phase |
| Advance to the next logical step | gsd-progress |
| Offload planning to the ultraplan cloud | gsd-ultraplan-phase |
| Cross-AI plan review convergence loop | gsd-plan-review-convergence |

Invoke the matched skill directly using the Skill tool.
