---
name: "gsd-inbox"
description: "Triage and review open GitHub issues and PRs against project templates and contribution guidelines."
metadata:
  short-description: "Triage and review open GitHub issues and PRs against project templates and contribution guidelines."
---

<codex_skill_adapter>
Read `.codex/GSD-ADAPTER.md` before executing this skill.
Invoke as `$gsd-inbox`; text after the invocation is `{{GSD_ARGS}}` (empty when omitted).
Resolve all project paths from the repository root.
</codex_skill_adapter>

<objective>
One-command triage of the project's GitHub inbox. Fetches all open issues and PRs,
reviews each against the corresponding template requirements (feature, enhancement,
bug, chore, fix PR, enhancement PR, feature PR), reports completeness and compliance,
and optionally applies labels or closes non-compliant submissions.

**Flow:** Detect repo → Fetch open issues + PRs → Classify each by type → Review against template → Report findings → Optionally act (label, comment, close)
</objective>

<execution_context>
@.codex/get-shit-done/workflows/inbox.md
</execution_context>

<context>
**Flags:**
- `--issues` — Review only issues (skip PRs)
- `--prs` — Review only PRs (skip issues)
- `--label` — Auto-apply recommended labels after review
- `--close-incomplete` — Close issues/PRs that fail template compliance (with comment explaining why)
- `--repo owner/repo` — Override auto-detected repository (defaults to current git remote)
</context>

<process>
Execute end-to-end.
Parse flags from arguments and pass to workflow.
</process>
