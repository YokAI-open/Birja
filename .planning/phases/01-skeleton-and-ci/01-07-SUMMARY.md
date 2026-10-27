---
phase: 01-skeleton-and-ci
plan: 07
subsystem: ci
tags: [github-actions, ci-pass, branch-protection, docs]
requires: [01-06]
provides:
  - "GitHub Actions workflow with backend, frontend, image, e2e and aggregate ci-pass jobs"
  - "Branch protection on develop and main requiring ci-pass (strict)"
  - "CLAUDE.md Common commands and README 'Run locally' matching the real commands"
affects: [all later phases]
key-files:
  created:
    - .github/workflows/ci.yml
    - README.md
  modified:
    - CLAUDE.md
    - .planning/PROJECT.md
key-decisions:
  - "D-01 resolved as option-public: repo YokAI-open/YokaiExchange made public, ci-pass required on develop and main"
duration: 40min
completed: 2026-10-26
---

# Phase 1 Plan 07: CI, docs and merge enforcement Summary

**Every PR into `develop`/`main` runs lint, types, tests, the image smoke test and the Playwright e2e test. A red `ci-pass` now blocks the merge.**

## Tasks

| # | Task | Commit | Result |
|---|------|--------|--------|
| 1 | CI workflow with aggregate `ci-pass` | 4f680b9 | actionlint 1.7.7 clean. Every job's commands passed when run locally: backend 17 tests at 96.7%, pip-audit clean. Image test-builder smoke: 5 passed. Frontend 100% coverage, npm audit 0 high. e2e: 1 passed |
| 2 | CLAUDE.md Common commands + README "Run locally" | 8408fc5 | Commands match what the CI and local runs actually use. The D-02 sentence is kept |
| 3 | D-01 decision + push/PR (checkpoint:decision) | 29764a8 (CI fix) | User chose **make repo public** and **push + PR into develop**. Details below |

## Task 3 outcome

1. Pushed `feature/phase-01-skeleton-and-ci` and opened PR #2 into `develop`: https://github.com/YokAI-open/YokaiExchange/pull/2
2. Scanned the git history for secrets. No `.env` or key files were ever committed. The only password-like values are placeholders (`change-me-dev-only`) and the throwaway test-stack password `test`, which is bound to 127.0.0.1. No tokens or private keys turned up.
3. After the user's second explicit confirmation, ran `gh repo edit --visibility public`. Visibility is now `PUBLIC`.
4. The first CI run on GitHub was red. Fixed in 29764a8 (see Deviations). The second run went green: backend, frontend, image, e2e and ci-pass all passed.
5. Applied protection to `develop` and `main`: `required_status_checks.contexts: ["ci-pass"]`, `strict: true`, `enforce_admins: false`. Read back and verified on both branches. PR #2 `mergeStateStatus` is `CLEAN`.

**FOUND-02 merge blocking: PASS.** GitHub enforces it, not just convention.

## Deviations from Plan

**1. [Rule 1 - Bug] `astral-sh/setup-uv@v10` does not exist**
- **Found during:** first GitHub run
- **Issue:** setup-uv publishes only full version tags, with no moving `v10` major tag. RESEARCH.md had assumed one.
- **Fix:** pinned `astral-sh/setup-uv@v10.3.2` (the latest release). The other actions' major tags (checkout v7, setup-node v7, upload-artifact v7, setup-buildx v4, build-push v7) were checked against the GitHub API and all exist.

**2. [Rule 1 - Bug] e2e `npm ci` failed with EACCES on the runner**
- **Issue:** the job started `docker compose up` before `npm ci`. The dev override's anonymous `/app/node_modules` volume made Docker create `frontend/node_modules` on the host as root, so the runner user (non-root) could not write to it. This never showed up locally because the local shell runs as root.
- **Fix:** in the e2e job, setup-node, `npm ci` and the Playwright browser install now run before the stack starts. A comment in the workflow explains why.

## Not done

- No throwaway PR with a deliberate lint error was opened to watch `ci-pass` go red. Blocking is shown by the protection settings (required check `ci-pass`, strict). The first, genuinely red run on PR #2 also proved that `ci-pass` fails when any job fails.

## Self-Check: PASSED
