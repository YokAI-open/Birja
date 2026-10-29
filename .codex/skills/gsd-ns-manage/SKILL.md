---
name: "gsd-ns-manage"
description: "config workspace | workstreams thread update ship inbox"
metadata:
  short-description: "config workspace | workstreams thread update ship inbox"
---

<codex_skill_adapter>
Read `.codex/GSD-ADAPTER.md` before executing this skill.
Invoke as `$gsd-ns-manage`; text after the invocation is `{{GSD_ARGS}}` (empty when omitted).
Resolve all project paths from the repository root.
</codex_skill_adapter>

Route to the appropriate management skill based on the user's intent.
`gsd-config` (settings + advanced + integrations + profile) and `gsd-workspace`
(new + list + remove) are post-#2790 consolidated entries.

| User wants | Invoke |
|---|---|
| Configure GSD settings (basic / advanced / integrations / profile) | gsd-config |
| Manage workspaces (create / list / remove) | gsd-workspace |
| Manage parallel workstreams | gsd-workstreams |
| Continue work in a fresh context thread | gsd-thread |
| Pause current work | gsd-pause-work |
| Resume paused work | gsd-resume-work |
| Update the GSD installation | gsd-update |
| Ship completed work | gsd-ship |
| Process inbox items | gsd-inbox |
| Create a clean PR branch | gsd-pr-branch |
| Undo the last GSD action | gsd-undo |

Invoke the matched skill directly using the Skill tool.
