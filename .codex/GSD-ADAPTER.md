# GSD runtime adapter for Birja

Use this adapter with the upstream Codex GSD skills, workflows, and agent
roles. It supplies the repository's tool translations; follow the actual
session tool schemas and higher-priority instructions when they differ from
examples in upstream documents.

## Context and invocation

- Work from the repository root. Read `AGENTS.md` and the shared rules in
  `CLAUDE.md`, then the selected skill and its required references.
- Resolve `.codex/`, `.planning/`, and other project-relative paths from the
  repo root, even when the shell or current file is in a subdirectory.
- Treat `@path` and `<files_to_read>` as instructions to read those files;
  Codex does not automatically expand Claude's `@` imports. Do not assume
  that mentioning a file loaded it. Read required inputs before editing.
- `$gsd-name arguments` selects `.codex/skills/gsd-name/SKILL.md`.
  The text after the skill invocation is `{{GSD_ARGS}}` (formerly
  `$ARGUMENTS`); it is empty if omitted. Only literal supplied flags are
  active. Translate historical `/gsd:name` and `/gsd-name` to `$gsd-name`.
- Preserve existing plan paths and references to `CLAUDE.md`. They refer to
  real shared rules, not obsolete files to rename or remove.

## Tools

| Upstream notation | Codex behavior |
| --- | --- |
| `Read`, `Glob`, `Grep` | Read files and search with the available shell tools (`rg`, `rg --files`, `sed`, etc.). |
| `Write`, `Edit`, `MultiEdit` | Use the available patch/file editing tools. |
| `Bash` | Use `exec_command` (directly or through `functions.exec`, as exposed). Honor sandbox approvals. |
| `WebSearch`, `WebFetch`, Context7 | Use an available documentation connector or web search/fetch; prefer primary documentation. Do not assume MCP servers are configured. |
| `TodoWrite` | Use an available planning tool or a concise working checklist; persist GSD state in its existing artifacts. |
| `AskUserQuestion` | Use an available user-input tool under its current mode restrictions. See below. |
| `Task`, `Agent`, `SendMessage`, `TaskOutput` | Use available collaboration tools only when permitted; otherwise execute the roles inline. |

For user questions, prefer `request_user_input_async` when available.
In clients exposing a synchronous `request_user_input`, use it only in the
modes and for the question types its schema supports. If neither is
available, ask in the conversation and wait when an answer is required.
Do not invent an answer to a scope decision, approval, or verification
checkpoint. Reuse preferences and approvals already given in the session;
resolve routine implementation choices directly when authorized. An
`--auto` flag is not consent to a push, merge, deployment, or other action
requiring separate authorization.

Some clients expose `spawn_agent(agent_type=..., message=...)` and
`wait`/`close_agent`; others expose `collaboration.spawn_agent` with
`task_name`, `message`, and `fork_turns`, plus `wait_agent` and
`send_message`. Use the actual exposed schema. For the latter form, read
the relevant `.codex/agents/gsd-<role>.md` and pass its instructions and the
necessary file paths explicitly; custom TOML role names are not a
`task_name` registration API. Preserve required input-reading blocks and
structured output markers. Inherit the selected model unless an applicable
instruction or explicit user choice specifies an override.

When delegation is not permitted or available, perform research, planning,
plan checking, execution, review, and verification as separate sequential
passes in the current agent. Retain dependency ordering and checkpoints.
Do not claim that an inline pass was an independent agent review. A request
for worktree isolation requires an actual separately prepared worktree;
`spawn_agent` alone does not provide it. Never change the main worktree's
branch while another worker may be using it.

## SDK and state

Use the installed `gsd-sdk query ...` interface. The matching CLI is
**1.42.3**, and `gsd-sdk --version` checks it. Do not silently download a
different release when a command is missing. The bundled
`.codex/get-shit-done/bin/gsd-tools.cjs` is an upstream legacy compatibility
CLI; use it only for commands it actually supports, not as a universal
replacement for SDK-only queries.

The shared `.planning/config.json` remains usable by Claude. Do not change
its runtime to Codex merely to change assistants. If SDK results contain
Claude model tiers (`opus`, `sonnet`, `haiku`), interpret them as upstream
profile metadata; do not send them as Codex model IDs. The installed Codex
agent roles inherit the user's model choice.

Preserve research, plan verification, summaries, UAT checkpoints, code
review, Nyquist validation, and state updates specified by the workflow.
The project's push and merge gates still apply in GSD `yolo` mode. Check
current authorization before creating commits, and scope any commits to
the actual task. Do not stage unrelated work with `git add .`.

Before executing a plan, compare its summary and recorded commits with
the working tree to avoid repeating completed tasks. Resolve stale session
pointers using the roadmap, plans, summaries, and implementation evidence;
report contradictions rather than blindly restarting Phase 1. This setup
migration itself must not execute pending plans or mark phases complete.

## Hooks and updates

Only the upstream Codex session-start update check is registered. Claude's
tool-use hooks and status line are not equivalent Codex hooks. Their
applicable intent is retained through these instructions: read before
editing, follow the selected workflow, respect phase boundaries, verify
changes, preserve checkpoints, and record a handoff before losing context.
Do not claim that automatic hook enforcement exists where it does not.

Keep updates scoped to this repository's `.codex/` installation. Use the
local reinstall procedure in `docs/CODEX.md` and run
`python3 scripts/sync-codex-skills.py` afterward. Upstream examples using
`--global` do not apply to this project installation. Review an upgrade's
diff before relying on changed behavior. Never modify the Claude install
as a side effect of a Codex update.
