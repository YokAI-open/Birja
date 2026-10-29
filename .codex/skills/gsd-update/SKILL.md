---
name: "gsd-update"
description: "Update GSD to latest version with changelog display"
metadata:
  short-description: "Update GSD to latest version with changelog display"
---

<codex_skill_adapter>
Read `.codex/GSD-ADAPTER.md` before executing this skill.
Invoke as `$gsd-update`; text after the invocation is `{{GSD_ARGS}}` (empty when omitted).
Resolve all project paths from the repository root.
</codex_skill_adapter>

<objective>
Check for GSD updates, install if available, and display what changed.

Routes to the update workflow which handles:
- Version detection (local vs global installation)
- npm version checking
- Changelog fetching and display
- User confirmation with clean install warning
- Update execution and cache clearing
- Restart reminder
</objective>

<execution_context>
@.codex/get-shit-done/workflows/update.md
</execution_context>

<flags>
- **--sync**: Sync managed GSD skills across runtime roots so multi-runtime users stay aligned after an update. Runs the sync-skills workflow (--from, --to, --dry-run, --apply flags supported).
- **--reapply**: Reapply local modifications after a GSD update. Uses three-way comparison (pristine baseline, user-modified backup, newly installed version) to merge user customizations back. Runs the reapply-patches workflow.
- **(no flag)**: Standard update — check for new version, show changelog, install.
</flags>

<process>
Parse the first token of {{GSD_ARGS}}:
- If it is `--sync`: strip the flag, execute the sync-skills workflow (passing remaining args for --from/--to/--dry-run/--apply).
- If it is `--reapply`: strip the flag, execute the reapply-patches workflow.
- Otherwise: execute the update workflow end-to-end.

</process>

<execution_context_extended>
@.codex/get-shit-done/workflows/sync-skills.md
@.codex/get-shit-done/workflows/reapply-patches.md
</execution_context_extended>
