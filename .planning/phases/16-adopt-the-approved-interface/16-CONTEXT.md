# Phase 16 Context

**Gathered:** 2026-11-23

## Locked owner decisions

- Use the accepted warm light Birja theme and the supplied fox mark and logo. Brand and primary navigation share one row. Keep labels only where they help users act or interpret the data.
- Use real portfolio names, whole-card links and a final New portfolio card. Name is required and description can be empty. Hide explanatory valuation sections from the overview.
- Place the chooser, Edit, Remove and Update/freshness in one portfolio toolbar. Show overall performance, cash/crypto/stock allocation, and holding cards with filters and sort. Keep named, explicit deletion confirmation and retry.
- History uses expandable chronological cards, one chooser and Update. Remove the Account page and use an icon-only door for sign-in and sign-out. Retain signed-in system status at `/health`.
- Keep existing order, valuation and account rules. Check both frontend and backend. Any backend changes should fix demonstrated integration defects. Keep live stock activation separate.

## Starting point

The owner approved the visual direction from earlier local previews. The redesign
is already present as uncommitted workspace changes on the v0.6.2 runtime base.
The phase adopts and validates those changes, fills proven gaps and records the
result. Earlier mocked browser checks and 1,331 frontend unit tests passed, at
the pre-milestone source. The integrated full-stack proof is separate.

## References

- `design-system/birja/MASTER.md` and `design-system/birja/pages/markets.md`
- `.planning/REQUIREMENTS.md` and `.planning/DEFERRED.md`
- `.planning/milestones/v1.2-MILESTONE-AUDIT.md`
- `frontend/src/App.tsx` and the approved page changes
