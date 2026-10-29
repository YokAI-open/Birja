---
name: "gsd-ns-project"
description: "project lifecycle | milestones audits summary"
metadata:
  short-description: "project lifecycle | milestones audits summary"
---

<codex_skill_adapter>
Read `.codex/GSD-ADAPTER.md` before executing this skill.
Invoke as `$gsd-ns-project`; text after the invocation is `{{GSD_ARGS}}` (empty when omitted).
Resolve all project paths from the repository root.
</codex_skill_adapter>

Route to the appropriate project / milestone skill based on the user's intent.
`gsd-plan-milestone-gaps` was deleted by #2790 — gap planning now happens
inline as part of `gsd-audit-milestone`'s output.

| User wants | Invoke |
|---|---|
| Start a new project | gsd-new-project |
| Create a new milestone | gsd-new-milestone |
| Complete the current milestone | gsd-complete-milestone |
| Audit a milestone for issues | gsd-audit-milestone |
| Summarize milestone status | gsd-milestone-summary |

Invoke the matched skill directly using the Skill tool.
