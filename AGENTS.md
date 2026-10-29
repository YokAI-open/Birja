# Codex project instructions

## Shared project rules

Read `CLAUDE.md` in full before planning, implementation, or review. It remains
the shared source of project rules for both assistants, including MVP scope,
architecture, commands, git-flow, money precision, security, migrations, and
test requirements. Its filename does not limit those rules to Claude.
Keep shared rules there; keep Codex-specific adaptations in this file.

Before planning or building, also read `.planning/PROJECT.md`,
`.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, and `.planning/STATE.md`.
Read the relevant phase's context, plans, and summaries. Use those artifacts
and the code to establish progress; old session pointers in STATE.md can be
stale. Continue the existing project rather than initializing a new one.

## Get Shit Done (GSD)

GSD is the project's established development workflow. Use the relevant GSD
skill for phase planning, execution, verification, progress, and substantial
tracked work. Small maintenance edits can be handled directly.

- Skills are discoverable through `.agents/skills/`; their maintained copies
  live in `.codex/skills/`.
- Before using a GSD workflow, read `.codex/GSD-ADAPTER.md` and the selected
  skill's `SKILL.md`. Load only the workflow references needed for that task.
- Codex invocation is `$gsd-progress`, `$gsd-plan-phase 5`,
  `$gsd-execute-phase 4`, etc. Treat historical `/gsd:...` and `/gsd-...`
  spellings as aliases for the corresponding `$gsd-...` skill.
- Preserve `.planning/` as the shared state between Claude and Codex. Do not
  reset it, rewrite completed history, or advance phases merely to migrate
  the assistant setup.
- Preserve research, plan checks, dependency ordering, checkpoints, reviews,
  verification, and summaries. Use available tools as described in the
  adapter; do not invent Claude-only tools or bypass checkpoints.
- GSD's `yolo` mode, `autonomous` plan flags, and `commit_docs` setting do
  not override project rules, existing authorization, or runtime permissions.
  In particular, retain the explicit approval requirements for pushing and
  merging in `CLAUDE.md`. A deployment example is not deployment permission.
- Follow the session's delegation rules. If agents are unavailable or
  delegation is not authorized, execute the required roles sequentially in
  the current agent and retain their review and verification steps.

## UI work

For interface design, components, accessibility, responsive behavior, and
visual review, read `.agents/skills/ui-ux-pro-max/SKILL.md`. Use its local
search scripts and the existing `design-system/` documents. Preserve the
project's established design system rather than replacing it during setup.

## Setup maintenance

See `docs/CODEX.md` for invocation examples, prerequisites, validation, and
updates. Run `python3 scripts/sync-codex-skills.py --check` to validate local
discovery. Keep the Claude configuration intact when maintaining Codex.
