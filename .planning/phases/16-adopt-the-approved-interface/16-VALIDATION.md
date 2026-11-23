---
phase: 16
slug: adopt-the-approved-interface
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-11-23
---

# Phase 16 Validation Strategy

| Plan | Requirements | Evidence |
|---|---|---|
| 16-01 | UI-01 to UI-07 | Type check, lint, Vitest and isolated browser checks. Keep existing financial assertions. |
| 16-02 | QA-01 | Responsive browser captures, keyboard and enlarged-text checks, and owner acceptance. |

Run focused tests after local repairs and the full suite at the integration
checkpoint. A route probe with simulated API responses only establishes
presentation behavior. Run actual financial and session journeys with the
disposable stack. Capture any failed check and its eventual resolution.
