---
phase: 01-skeleton-and-ci
plan: 01
subsystem: toolchain
tags: [git-flow, uv, node, supply-chain]
requires: []
provides:
  - "Branch feature/phase-01-skeleton-and-ci from origin/develop"
  - "uv 0.13.5 and Node v24.22.1 / npm 11.19.1 on PATH"
  - "User-approved Phase 1 package and image list"
affects: [01-02, 01-03, 01-04, 01-05, 01-06, 01-07]
key-files:
  created: []
  modified: []
key-decisions:
  - "uv and Node 24 installed at user level (astral.sh installer, nvm) and symlinked into /usr/local/bin so non-interactive shells see them"
duration: 5min
completed: 2026-10-26
---

# Phase 1 Plan 01: Branch, toolchain and package gate Summary

**Phase 1 runs on `feature/phase-01-skeleton-and-ci`, the host has uv and Node 24, and the user approved the full package list.**

## Tasks

| # | Task | Result |
|---|------|--------|
| 1 | Create feature branch from up-to-date develop | Done. `develop` was already up to date with origin, and the branch was created from it. Planning docs committed as `9b0c44e` |
| 2 | Install uv and Node 24 (checkpoint:human-action) | Done by Claude at the user's request. uv 0.13.5 via the official astral.sh installer (`~/.local/bin`). Node v24.22.1 via nvm v0.40.3 (`~/.nvm`), set as the nvm default |
| 3 | Package legitimacy (checkpoint:human-verify, blocking-human) | User replied **Approved** with no removals |

## Approved package set

The list in 01-01-PLAN.md Task 3 was approved unchanged:
- **Backend (PyPI):** fastapi 0.162.0, uvicorn[standard] 0.54.0, sqlalchemy[asyncio] >=2.0.55,<2.1, asyncpg 0.32.0, alembic 1.20.1, pydantic 2.14.1, pydantic-settings 2.16.1, redis 8.1.0. Dev: pytest 9.1.1, pytest-asyncio 1.4.1, pytest-cov 7.1.0, httpx 0.28.1, ruff 0.17.2, mypy 2.4.0, pip-audit.
- **Frontend (npm):** react/react-dom 19.3.1, vite 8.3.5, @vitejs/plugin-react 6.1.2, typescript ~6.0.3, @tanstack/react-query 5.105.0, tailwindcss and @tailwindcss/vite 4.3.3, shadcn 4.22.1 and the packages it installs, @fontsource-variable/inter 5.3.0, vitest and @vitest/coverage-v8 5.0.5, jsdom 30.1.3, @testing-library/react 16.3.3, @testing-library/jest-dom 7.0.1, @testing-library/user-event 14.x, @playwright/test 1.64.1, eslint 10.13.0, @eslint/js 10.0.1, typescript-eslint 8.72.0, eslint-plugin-react-hooks 7.1.1, eslint-plugin-react-refresh 0.5.7, globals 17.13.0, prettier 3.9.10, @types/node ^24, @types/react and @types/react-dom.
- **Images:** postgres:18.6-trixie, redis:8.8.3-trixie, python:3.14.9-slim-trixie, node:24.22.1-trixie-slim, ghcr.io/astral-sh/uv:0.13.5.

## Deviations from Plan

**1. [Rule 3 - Blocking] Symlinked uv and Node 24 into /usr/local/bin**
- **Found during:** Task 2
- **Issue:** The agent tool shells are non-interactive and don't source `~/.bashrc`, so the nvm Node and `~/.local/bin/uv` weren't on their PATH, and `/usr/bin/node` (v18) still won.
- **Fix:** Created symlinks `/usr/local/bin/{node,npm,npx,corepack}` → `~/.nvm/versions/node/v24.22.1/bin/*` and `/usr/local/bin/{uv,uvx}` → `~/.local/bin/*`. `/usr/local/bin` comes before `/usr/bin` on PATH. To undo, delete those six links.
- **Verification:** `uv --version` → 0.13.5, `node --version` → v24.22.1, `npm --version` → 11.19.1 in a fresh tool shell.

## Notes

- The uncommitted `.gitignore` change (`__pycache__/`, `*.pyc`) and the untracked `.claude/` existed before this phase and were left alone. Plan 01-02 edits `.gitignore` anyway.

## Self-Check: PASSED
