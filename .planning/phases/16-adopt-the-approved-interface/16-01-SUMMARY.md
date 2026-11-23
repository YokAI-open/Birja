---
phase: 16-adopt-the-approved-interface
plan: "01"
requirements-completed: [UI-01, UI-02, UI-03, UI-04, UI-05, UI-06, UI-07]
status: complete
completed: 2026-11-23
---

# Plan 16-01 — Adopt and Integrate the Interface

The owner-approved design is implemented for the branded shell, Markets,
Portfolios, selected portfolio, both trade tickets, History and sign-in.
The existing API, auth and finance paths remain authoritative. The stock
restriction notice, editor focus and responsive fixes from review are in
the implemented UI.

The application tree is pinned at ef60a64. The follow-up commits through
abe4976 change three affected browser specs. Lint, format, typecheck and
build pass, and 1,332 frontend tests pass with 97.56% line coverage.

The complete isolated browser run at ef60a64 produced 85 passes, eight
failures and one expected deployed-only CSP skip. The eight cases failed
on test locators or navigation adapted for the new interface. The rerun at
equivalent application input and corrected specs passed all 16 selected
journeys, including the eight failed cases. Matching test names and the
scoped git diff establish 93 distinct passing scenarios across the runs.
The initial whole-run verdict remains failed. Both owned stacks were cleaned.

Receipts:

- Full browser: `/tmp/birja-phase09-browser-700n9c8w/browser-all.log`
- Corrected browser: `/tmp/birja-phase09-browser-f7qiz8pr/browser-all.log`
- Frontend: `/tmp/birja-v13-frontend-ef60a64-final.log`
