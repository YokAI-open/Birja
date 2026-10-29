---
name: "gsd-validate-phase"
description: "Retroactively audit and fill Nyquist validation gaps for a completed phase"
metadata:
  short-description: "Retroactively audit and fill Nyquist validation gaps for a completed phase"
---

<codex_skill_adapter>
Read `.codex/GSD-ADAPTER.md` before executing this skill.
Invoke as `$gsd-validate-phase`; text after the invocation is `{{GSD_ARGS}}` (empty when omitted).
Resolve all project paths from the repository root.
</codex_skill_adapter>

<objective>
Audit Nyquist validation coverage for a completed phase. Three states:
- (A) VALIDATION.md exists — audit and fill gaps
- (B) No VALIDATION.md, SUMMARY.md exists — reconstruct from artifacts
- (C) Phase not executed — exit with guidance

Output: updated VALIDATION.md + generated test files.
</objective>

<execution_context>
@.codex/get-shit-done/workflows/validate-phase.md
</execution_context>

<context>
Phase: {{GSD_ARGS}} — optional, defaults to last completed phase.
</context>

<process>
Execute end-to-end.
Preserve all workflow gates.
</process>
