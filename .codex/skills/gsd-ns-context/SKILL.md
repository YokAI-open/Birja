---
name: "gsd-ns-context"
description: "codebase intelligence | map graphify docs learnings"
metadata:
  short-description: "codebase intelligence | map graphify docs learnings"
---

<codex_skill_adapter>
Read `.codex/GSD-ADAPTER.md` before executing this skill.
Invoke as `$gsd-ns-context`; text after the invocation is `{{GSD_ARGS}}` (empty when omitted).
Resolve all project paths from the repository root.
</codex_skill_adapter>

Route to the appropriate codebase-intelligence skill based on the user's intent.
`gsd-scan` and `gsd-intel` were folded into `gsd-map-codebase` flags by #2790.

| User wants | Invoke |
|---|---|
| Map the full codebase structure | gsd-map-codebase |
| Quick lightweight codebase scan | gsd-map-codebase --fast |
| Query mapped intelligence files | gsd-map-codebase --query |
| Generate a knowledge graph | gsd-graphify |
| Update project documentation | gsd-docs-update |
| Extract learnings from a completed phase | gsd-extract-learnings |

Invoke the matched skill directly using the Skill tool.
