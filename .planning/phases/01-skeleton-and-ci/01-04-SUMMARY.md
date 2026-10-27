---
phase: 01-skeleton-and-ci
plan: 04
subsystem: frontend
tags: [vite, react, typescript, tailwind, shadcn, vitest, design-tokens]
requires: ["01-01"]
provides:
  - "frontend/ Vite 8 + React 19 + TS 6 app with exact-pinned deps and package-lock.json"
  - "ESLint 10 / Prettier / Vitest 5 with 80% coverage thresholds"
  - "MASTER.md tokens in index.css (light mode only) and Tailwind utilities"
  - "shadcn Card, Badge (success/danger/neutral), Button (44px primary pill)"
affects: [01-05, 01-06, 01-07]
key-files:
  created:
    - frontend/package.json
    - frontend/package-lock.json
    - frontend/vite.config.ts
    - frontend/eslint.config.js
    - frontend/components.json
    - frontend/src/index.css
    - frontend/src/App.tsx
    - frontend/src/App.test.tsx
    - frontend/src/components/ui/card.tsx
    - frontend/src/components/ui/badge.tsx
    - frontend/src/components/ui/button.tsx
  modified: []
key-decisions:
  - "shadcn alias @/* works with paths only (no baseUrl) under TS 6; ignoreDeprecations fallback not needed"
  - "shadcn 4.22.1 requires a preset: used -b radix -p vega (classic set), neutral base"
  - "Shadows defined in plain @theme (not inline) so var(--border) resolves at use site"
requirements-completed: [FOUND-01]
duration: 25min
completed: 2026-10-26
---

# Phase 1 Plan 04: Frontend foundation Summary

**Vite 8 + React 19 + TypeScript 6 frontend on Node 24, with Tailwind 4 driven entirely by MASTER.md tokens and restyled shadcn card/badge/button.**

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | 476193e | Scaffold the Vite React frontend (pinned deps, ESLint/Prettier/Vitest) |
| 2a | aaf57cb | Initialise shadcn with card, badge and button (raw generated output) |
| 2b | 0e0f9cd | Apply the YokaiExchange design tokens |

## Verification

`npm ci`, `npm run lint`, `npm run typecheck`, `npx prettier --check .`, `npm run test -- --coverage` (100% on App.tsx) and `npm run build` all pass on Node 24.22.1. typescript resolves to 6.0.3. No raw hex or oklch in .tsx files or index.css besides MASTER values; no `.dark` block.

## Deviations from Plan

1. **[Rule 3 - Blocking] scaffold differences.** `create-vite` 9.3.1 scaffolds oxlint and a different tsconfig; replaced by hand with the plan's ESLint config and scripts.
2. **[Rule 3 - Blocking] shadcn init prompts for a preset.** Ran `init -t vite -b radix -p vega -y`. Unpinned `^` ranges that shadcn added (class-variance-authority 0.7.1, cn 0.5.0, lucide-react 1.61.0, radix-ui 1.8.1, shadcn 4.22.1, tw-animate-css 1.4.0) were converted to exact versions (covered by approval "shadcn 4.22.1 and the packages it installs"). `cn` is shadcn-ui's own package, used by generated `import { cn } from "cn"`.
3. **Hex case.** Plan acceptance greps `--gain-text: #2E7A2E` (uppercase); Prettier (also a required gate) lowercases hex, so index.css holds `#2e7a2e`. Values are identical to MASTER.md; case-insensitive grep passes.
4. **Version note.** All pinned versions resolved as planned; no substitutions. `@testing-library/dom` comes in as a peer dependency of @testing-library/react.

## Known Stubs

`App.tsx` `<main>` is empty by design until plan 05 adds the health page.

## Self-Check: PASSED

Files and commits 476193e, aaf57cb, 0e0f9cd verified in the worktree.
