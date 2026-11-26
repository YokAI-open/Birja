---
phase: 25-finish-the-trading-flows-and-verify-the-integrated-app
plan: "03"
subsystem: auth
tags: [react, sign-in, accessibility, focus, vitest]
requires:
  - phase: 22-adopt-the-market-workspace
    provides: Shared Birja header and signed-in navigation
provides:
  - Centered email-code forms with focus transfer, input labels and paste support
  - Single pending door sign-out with focus returned after success
affects: [25-01, 25-05]
tech-stack:
  added: []
  patterns: [Scoped sign-in stylesheet, Mutation-backed form focus]
key-files:
  created: [frontend/src/pages/signInWorkspace.css]
  modified: [frontend/src/pages/SignInPage.tsx, frontend/src/pages/SignInPage.test.tsx, frontend/src/App.tsx, frontend/src/App.test.tsx]
key-decisions:
  - Keep the session mutations as the source of pending, error and completion state
  - Restore focus to the email field when a confirmed sign-out presents the form
requirements-completed: [FLOW-03]
duration: 6min
completed: 2026-11-26
---

# Phase 25 Plan 03 — Email-code sign-in

The centered email and code forms and the shared header door use the
existing request, verification and sign-out mutations.

## Delivery

- Adopted the approved 415px panel width and retained the 52px fields from
  the UI contract. The initial panel leads with the email field and Send
  code. The code panel retains the delivery hint and resend actions.
- Moved focus to the mounted field when requesting a code, returning to
  email or finishing sign-out. Both fields support autofill. The code field
  supports paste and preserves numeric input.
- Guarded actions during pending mutations, including repeat submissions
  within the same event batch. A successful resend clears the old code.
  Existing sanitized feedback, session-cache handling and scoped navigation
  remain in use.

| Task | Commit | Verification |
|---|---|---|
| 25-03-01 · Centered email and code forms | `9885c03` | 41 targeted sign-in, auth mutation and client tests passed. |
| 25-03-02 · Accessible door and sign-out | `baad312` | 97 App, sign-in and auth mutation tests passed. Project TypeScript and scoped ESLint and Prettier passed. |

The task window ran from 19:23:21 to 19:29:44 UTC on 2026-11-26.
Both tasks changed five files in total. The Vite production bundle built
successfully and reported a chunk-size warning.

## Local visual measurements

Chromium rendered the production bundle with an intercepted signed-out
response and the approved local prototype at matching sizes. All other
network origins were blocked. Plan 25-05 supplies real generated-code
browser coverage through the application API.

| Viewport | App panel origin and width | Prototype panel origin and width | App and prototype email field widths |
|---|---|---|---|
| 1440 × 1000 | x512.5, y209, 415px | x512.5, y207, 415px | 341px and 339px |
| 390 × 1000 | x16, y116.3, 358px | x16, y115.3, 358px | 316px and 316px |

The live field is 52px high at both widths, compared with the prototype's
44px. The signed-out panel is 16px shorter on desktop and 12.5px shorter
on mobile. The approved live panel uses a concise form with working
controls and the current signed-out navigation. At 320px with 200% CSS
text enlargement, the document width remained 320px and the input remained
usable at 214px wide.

## Self-Check: PASSED

Both task commits and the stylesheet exist. The scoped diff passes its
whitespace checks. The auth transport and session hooks use their existing
files, with guarded browser integration scheduled in Plan 25-05.
