---
phase: 05-portfolio-and-history
status: pr-green-awaiting-separate-merge-approval
updated: 2026-10-30
---

# Phase 5 Remote and Release Decision

Branch: `feature/phase-05-portfolio-and-history`, based on develop.
Target: origin, same feature branch; optional PR into develop.

User approved the Phase 5 dev rebuild, which completed with five healthy
services and Alembic `0008 (head)`. User then approved the supplied real-price
Portfolio/History and responsive/navigation browser checklist.

Local gates: 573 backend tests, 99.90% overall, 100% critical coverage;
258 frontend tests, 99.05% statements; lint/types/format/build, dependency
high gates, image smoke and offline deploy checks passed. Independent
review is clean after both reproduced findings were fixed and re-reviewed.

Push choice: **push and open PR**, explicitly requested by the user as
`push=pr`. Branch pushed with upstream tracking;
[PR #25](https://github.com/YokAI-open/Birja/pull/25) targets develop.
Release intent: **skipped**; no release/deployment requested for Phase 5.
Actual Playwright and remote CI: **passed** at `0595c89`, [run 41066672894](https://github.com/YokAI-open/Birja/actions/runs/41066672894).
All five jobs including ci-pass succeeded. Playwright: 10 passed, one
production-only CSP test intentionally skipped. No failed tests.
Merge approval: **not supplied**. Only the authorized feature push and PR creation were performed.

Previous-phase approval does not authorize these actions. Phase 6 backup,
restore, friend inbox and production database role/SSL work remains separate.

The initial CI run exposed an uncalled string-evaluation function in
responsive assertions; the next run exposed native disabled refresh focus
loss. Both were corrected, regression tested and independently re-reviewed
before the successful run. The browser assertions remain in place.
