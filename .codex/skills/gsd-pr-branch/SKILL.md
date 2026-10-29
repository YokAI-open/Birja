---
name: "gsd-pr-branch"
description: "Create a clean PR branch by filtering out .planning/ commits — ready for code review"
metadata:
  short-description: "Create a clean PR branch by filtering out .planning/ commits — ready for code review"
---

<codex_skill_adapter>
Read `.codex/GSD-ADAPTER.md` before executing this skill.
Invoke as `$gsd-pr-branch`; text after the invocation is `{{GSD_ARGS}}` (empty when omitted).
Resolve all project paths from the repository root.
</codex_skill_adapter>

<objective>
Create a clean branch suitable for pull requests by filtering out .planning/ commits
from the current branch. Reviewers see only code changes, not GSD planning artifacts.

This solves the problem of PR diffs being cluttered with PLAN.md, SUMMARY.md, STATE.md
changes that are irrelevant to code review.
</objective>

<execution_context>
@.codex/get-shit-done/workflows/pr-branch.md
</execution_context>

<process>
Execute end-to-end.
</process>
