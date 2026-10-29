---
name: "gsd-audit-uat"
description: "Cross-phase audit of all outstanding UAT and verification items"
metadata:
  short-description: "Cross-phase audit of all outstanding UAT and verification items"
---

<codex_skill_adapter>
Read `.codex/GSD-ADAPTER.md` before executing this skill.
Invoke as `$gsd-audit-uat`; text after the invocation is `{{GSD_ARGS}}` (empty when omitted).
Resolve all project paths from the repository root.
</codex_skill_adapter>

<objective>
Scan all phases for pending, skipped, blocked, and human_needed UAT items. Cross-reference against codebase to detect stale documentation. Produce prioritized human test plan.
</objective>

<execution_context>
@.codex/get-shit-done/workflows/audit-uat.md
</execution_context>

<context>
Core planning files are loaded in-workflow via CLI.

**Scope:**
Glob: .planning/phases/*/*-UAT.md
Glob: .planning/phases/*/*-VERIFICATION.md
</context>
