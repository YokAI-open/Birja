---
name: "gsd-audit-fix"
description: "Autonomous audit-to-fix pipeline — find issues, classify, fix, test, commit"
metadata:
  short-description: "Autonomous audit-to-fix pipeline — find issues, classify, fix, test, commit"
---

<codex_skill_adapter>
Read `.codex/GSD-ADAPTER.md` before executing this skill.
Invoke as `$gsd-audit-fix`; text after the invocation is `{{GSD_ARGS}}` (empty when omitted).
Resolve all project paths from the repository root.
</codex_skill_adapter>

<objective>
Run an audit, classify findings as auto-fixable vs manual-only, then autonomously fix
auto-fixable issues with test verification and atomic commits.

Flags:
- `--max N` — maximum findings to fix (default: 5)
- `--severity high|medium|all` — minimum severity to process (default: medium)
- `--dry-run` — classify findings without fixing (shows classification table)
- `--source <audit>` — which audit to run (default: audit-uat)
</objective>

<execution_context>
@.codex/get-shit-done/workflows/audit-fix.md
</execution_context>

<process>
Execute end-to-end.
</process>
