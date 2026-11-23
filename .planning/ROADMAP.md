# Roadmap: Birja

## Milestones

- [x] **v1.0 Birja MVP** — shipped 2026-11-10 as software v0.4.0; [archive](milestones/v1.0-ROADMAP.md).
- [x] **v1.1 US Stock Trading** — closed 2026-11-14 with accepted live gaps: 63/64 plans, 130/132 tasks, 20/26 requirements locally satisfied; [archive](milestones/v1.1-ROADMAP.md).
- [x] **v1.2 Multiple Strategy Portfolios** — shipped as software v0.6.2, 28/28 requirements, 72/72 plans. [Archive](milestones/v1.2-ROADMAP.md) · [Audit](milestones/v1.2-MILESTONE-AUDIT.md).

- [ ] **v1.3 Birja Interface Redesign** — owner-approved on 2026-11-23.

## Phases

- [ ] **Phase 16: Adopt the Approved Interface**
- [ ] **Phase 17: Verify Full-Stack Behavior and Prepare Release**

## Phase Details

### Phase 16: Adopt the Approved Interface

**Goal:** Turn the approved working-tree redesign into a verified implementation on the existing Birja APIs.

**Requirements:** UI-01, UI-02, UI-03, UI-04, UI-05, UI-06, UI-07, QA-01

**Plans:** 2 plans

- [ ] 16-01 — Adopt and integrate the approved redesign (wave 1).
- [ ] 16-02 — Verify the integrated UI and capture owner acceptance (wave 2).

**Success criteria:**

1. The shared header, door control, Markets and trade tickets match the approved style and retain existing quote, order and session behavior.
2. Portfolio and History cards, switching, management and recovery identify and affect the correct active portfolio and preserve authoritative data.
3. Keyboard, responsive and enlarged-text checks cover the main flows and their loading, unavailable, error and empty states. The owner can review the release candidate.

### Phase 17: Verify Full-Stack Behavior and Prepare Release

**Goal:** Qualify the redesigned app end to end and produce a reviewed release candidate.

**Depends on:** Phase 16

**Requirements:** QA-02, QA-03

**Success criteria:**

1. Code review, frontend and backend checks, and isolated browser journeys verify session, portfolio ownership, real trade economics, deletion and History. Necessary fixes are reviewed and retested.
2. A milestone audit ties each requirement to observed evidence. The review records any approved follow-up.
3. The release candidate passes required PR CI once publishing is approved. Merge, release and deployment follow their established approval gates.

## Progress

| Phase | Milestone | Status |
|---|---|---|
| 16. Adopt the Approved Interface | v1.3 | Planned |
| 17. Verify Full-Stack Behavior and Prepare Release | v1.3 | Depends on Phase 16 |

All 10 requirements are assigned once in [REQUIREMENTS.md](REQUIREMENTS.md).
The [deferred register](DEFERRED.md) retains the separate stock activation work.
