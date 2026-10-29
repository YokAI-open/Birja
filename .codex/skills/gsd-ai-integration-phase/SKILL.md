---
name: "gsd-ai-integration-phase"
description: "Generate an AI-SPEC.md design contract for phases that involve building AI systems."
metadata:
  short-description: "Generate an AI-SPEC.md design contract for phases that involve building AI systems."
---

<codex_skill_adapter>
Read `.codex/GSD-ADAPTER.md` before executing this skill.
Invoke as `$gsd-ai-integration-phase`; text after the invocation is `{{GSD_ARGS}}` (empty when omitted).
Resolve all project paths from the repository root.
</codex_skill_adapter>

<objective>
Create an AI design contract (AI-SPEC.md) for a phase involving AI system development.
Orchestrates gsd-framework-selector → gsd-ai-researcher → gsd-domain-researcher → gsd-eval-planner.
Flow: Select Framework → Research Docs → Research Domain → Design Eval Strategy → Done
</objective>

<execution_context>
@.codex/get-shit-done/workflows/ai-integration-phase.md
@.codex/get-shit-done/references/ai-frameworks.md
@.codex/get-shit-done/references/ai-evals.md
</execution_context>

<context>
Phase number: {{GSD_ARGS}} — optional, auto-detects next unplanned phase if omitted.
</context>

<process>
Execute end-to-end.
Preserve all workflow gates.
</process>
