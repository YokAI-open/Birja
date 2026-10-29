---
name: "gsd-secure-phase"
description: "Retroactively verify threat mitigations for a completed phase"
metadata:
  short-description: "Retroactively verify threat mitigations for a completed phase"
---

<codex_skill_adapter>
Read `.codex/GSD-ADAPTER.md` before executing this skill.
Invoke as `$gsd-secure-phase`; text after the invocation is `{{GSD_ARGS}}` (empty when omitted).
Resolve all project paths from the repository root.
</codex_skill_adapter>

<objective>
Verify threat mitigations for a completed phase. Three states:
- (A) SECURITY.md exists — audit and verify mitigations
- (B) No SECURITY.md, PLAN.md with threat model exists — run from artifacts
- (C) Phase not executed — exit with guidance

Output: updated SECURITY.md.
</objective>

<execution_context>
@.codex/get-shit-done/workflows/secure-phase.md
</execution_context>

<context>
Phase: {{GSD_ARGS}} — optional, defaults to last completed phase.
</context>

<process>
Execute end-to-end.
Preserve all workflow gates.
</process>
