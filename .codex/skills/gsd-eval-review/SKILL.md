---
name: "gsd-eval-review"
description: "Audit an executed AI phase's evaluation coverage and produce an EVAL-REVIEW.md remediation plan."
metadata:
  short-description: "Audit an executed AI phase's evaluation coverage and produce an EVAL-REVIEW.md remediation plan."
---

<codex_skill_adapter>
Read `.codex/GSD-ADAPTER.md` before executing this skill.
Invoke as `$gsd-eval-review`; text after the invocation is `{{GSD_ARGS}}` (empty when omitted).
Resolve all project paths from the repository root.
</codex_skill_adapter>

<objective>
Conduct a retroactive evaluation coverage audit of a completed AI phase.
Checks whether the evaluation strategy from AI-SPEC.md was implemented.
Produces EVAL-REVIEW.md with score, verdict, gaps, and remediation plan.
</objective>

<execution_context>
@.codex/get-shit-done/workflows/eval-review.md
@.codex/get-shit-done/references/ai-evals.md
</execution_context>

<context>
Phase: {{GSD_ARGS}} — optional, defaults to last completed phase.
</context>

<process>
Execute end-to-end.
Preserve all workflow gates.
</process>
