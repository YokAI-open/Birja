# Phase 1: Skeleton and CI - Context

**Gathered:** 2026-10-26
**Status:** Ready for planning
**Source:** plan-phase questions after research (no discuss-phase run)

<domain>
## Phase Boundary

Walking skeleton: Postgres, Redis, FastAPI backend and React frontend run together via `docker compose up --build`. The page shows a live backend health result fetched through TanStack Query. GitHub Actions checks every PR into `develop`/`main`. Requirements: FOUND-01, FOUND-02.

</domain>

<decisions>
## Implementation Decisions

### CI merge blocking
- **D-01:** One aggregate `ci-pass` job is the single required check. Enforcing it is the phase's final `checkpoint:decision` task, because branch protection returns 403 on the current private repo plan. The user then chooses one of three options: make the repo public, upgrade the plan, or rely on convention. If enforcement becomes possible, the task runs the `gh api` protection command from RESEARCH.md for `main` and `develop`.

### API response serialization
- **D-02:** No `ORJSONResponse` and no `orjson` dependency. Endpoints use `response_model`/return types with FastAPI's default response class. CLAUDE.md was updated to match on 2026-10-26.

### End-to-end test
- **D-03:** Phase 1 includes exactly one Playwright e2e test, `e2e/health.spec.ts`. It runs against the full Compose stack and checks that the health page shows DB and Redis reachable. It runs as its own CI job and feeds `ci-pass`.

### Claude's Discretion
- Exact pinned versions, file layout within the CLAUDE.md structure, health endpoint shape (`/api/v1/health`), and test fixture design all follow RESEARCH.md.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

- `CLAUDE.md`: stack, security, testing, git and data rules
- `.planning/phases/01-skeleton-and-ci/01-RESEARCH.md`: pinned versions, patterns, pitfalls, validation architecture
- `.planning/REQUIREMENTS.md`: FOUND-01, FOUND-02
- `design-system/yokaiexchange/MASTER.md`: colors, fonts and tokens for Tailwind and shadcn

</canonical_refs>

<deferred>
## Deferred Ideas

- No UI-SPEC for this phase. The user skipped it because the only screen is a health page styled from MASTER.md.
- react-router, decimal.js, respx, extra shadcn components, nginx, a prod Dockerfile target and DB role hardening are all deferred to the phases that need them (see RESEARCH.md Scope Flags).

</deferred>

---

*Phase: 01-skeleton-and-ci*
