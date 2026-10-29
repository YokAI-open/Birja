# Working on Birja with Codex

Open this repository in Codex. `AGENTS.md` loads the project agreement and
directs Codex to read `CLAUDE.md`, which remains the shared rules source.
Both assistants use the same `.planning/` history and design system.

## GSD commands

The Codex installation uses the upstream adapter from **Get Shit Done
1.42.3**, matching the existing Claude installation. It includes all 67 GSD
skills and 33 agent roles. Invoke a skill with `$`:

| Claude spelling | Codex spelling | Purpose |
| --- | --- | --- |
| `/gsd:help` | `$gsd-help` | Show the command reference |
| `/gsd:progress` | `$gsd-progress` | Inspect current progress |
| `/gsd:resume-work` | `$gsd-resume-work` | Restore session context |
| `/gsd:discuss-phase 5` | `$gsd-discuss-phase 5` | Capture phase decisions |
| `/gsd:plan-phase 5` | `$gsd-plan-phase 5` | Research, plan, and check a phase |
| `/gsd:execute-phase 4` | `$gsd-execute-phase 4` | Execute remaining phase plans |
| `/gsd:verify-work 4` | `$gsd-verify-work 4` | Check delivered behavior |
| `/gsd:quick ...` | `$gsd-quick ...` | Run a small tracked task |
| `/gsd:pause-work` | `$gsd-pause-work` | Record a handoff |

Start with `$gsd-progress` to inspect the existing project. Do not run
`$gsd-new-project` to resume it. Native Codex clients expose skills through
`/skills` or the `$` selector. If the client has not picked up the new
instructions or skills, start a new Codex session in this repository.

The UI skill is available as `$ui-ux-pro-max`, with its own scripts and data
under `.codex/skills/ui-ux-pro-max/`.

## Layout and runtime

- `AGENTS.md`: Codex entry point; shared rules remain in `CLAUDE.md`.
- `.codex/skills/`: native GSD skills and a portable copy of the project's
  UI skill, excluding Python caches.
- `.agents/skills/`: relative links to those skill folders, for Codex discovery.
- `.codex/get-shit-done/`: upstream workflows, references, templates, and tools.
- `.codex/agents/` and `.codex/config.toml`: upstream agent roles, inheriting
  the user's model selection.
- `.codex/GSD-ADAPTER.md`: tool translation and project-specific runtime rules.
- `.codex/hooks.json`: upstream Codex session-start update check. Claude's
  other hook registrations and status line are not installed into Codex;
  project instructions preserve their applicable workflow checks.

GSD needs Node.js 22+ and the matching `gsd-sdk` CLI on PATH. Both were
available on the migration machine. On another machine, install the pinned
CLI package with `npm install --global get-shit-done-cc@1.42.3`, then check
`gsd-sdk --version`. Installing the CLI package alone does not run a Claude
configuration migration. The Python UI search scripts use the standard
library.

The installation does not change the global Codex model, approval settings,
Claude configuration, application code, or existing planning artifacts.
Agent roles remain subject to the client's available tools and delegation
policy; sequential execution is supported by the adapter. Read-only progress
checks do not authorize execution, pushing, merging, or deployment.

## Validate or refresh

From the repository root:

```bash
python3 scripts/sync-codex-skills.py --check
gsd-sdk --version
gsd-sdk query init.progress
gsd-sdk query phase-plan-index 4
```

The sync check validates skill discovery links, frontmatter names,
execution-context file references, and agent configuration paths. The GSD
queries read the existing planning state without executing phase plans.

After deliberately reinstalling or updating GSD, run:

```bash
# Reinstall the pinned version for this repository only.
npx get-shit-done-cc@1.42.3 --codex --local
python3 scripts/sync-codex-skills.py
python3 scripts/sync-codex-skills.py --check
```

Use a deliberately chosen version for an upgrade, review the resulting diff,
and retain `.codex/GSD-ADAPTER.md`. The sync script makes generated paths
portable, shares the runtime adapter across GSD entry points, and restores
discovery links. It does not download packages or change `.planning/`.
Do not use upstream `--global` examples to update this repository's install.
Commit `.codex/`, `.agents/`, `AGENTS.md`, the sync script, and this guide
together so other checkouts get the same setup. Keep upstream GSD's MIT
license with the vendored files.

Official references: [Codex skills](https://learn.chatgpt.com/docs/build-skills)
and [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md).
