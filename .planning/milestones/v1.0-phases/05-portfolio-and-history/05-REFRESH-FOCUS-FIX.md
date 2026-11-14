# Phase 5 refresh focus correction

CI run `41065518861` failed the actual financial flow twice at
`portfolio-history.spec.ts:269`: Refresh portfolio was inactive after refetch.
The four responsive browser cases passed. Only the failing assertion context
was inspected; no service logs, OTPs or account data were used.

## Cause and correction

The page made its focused refresh button natively disabled during fetching.
An offline Chromium DOM-only probe confirmed that toggling native disabled
loses focus, whereas toggling aria-disabled retains it. JSDOM preserved focus
on disabled buttons, allowing the earlier component focus tests to pass.

Portfolio and History refresh now use aria-disabled with the established
disabled opacity/cursor styling. The shared handler refuses activation while
fetching; `cancelRefetch: false` also coalesces activation before a React
pending render rather than restarting an existing request. This follows
[MDN's aria-disabled guidance](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Attributes/aria-disabled):
focusability is retained and JavaScript suppresses the unavailable action.
The installed TanStack query-core implementation was inspected for the
cancelRefetch behavior; Context7 tools and CLI were unavailable.

Initial and background retry controls use the same guarded handler. When a
focused retry disappears into loading or successful recovery, its ref callback
moves focus to the persistent refresh control without scrolling. It does not
move focus when the user has already navigated elsewhere. Background retry
remains focusable and visibly unavailable during its request.

Shared Button, pagination, financial logic, e2e assertions and shared planning
metadata are unchanged. Pagination's separate native-disabled/final-focus
behavior was preserved under the assigned scope; this report does not claim
real-browser append/end-focus verification.

## Verification

- RED commit `311c00f`: six expected failures and 31 passing tests. Deferred
  requests expose the native-disabled refresh contract and missing retry
  focus handling, rather than relying only on JSDOM's activeElement behavior.
- GREEN focused pages: **39 passed**, covering pending semantics, retained
  values, mouse/Enter/Space duplicate suppression, initial/background retry,
  successful focus transfer and no focus theft after the user tabs away.
- Full frontend once: **264 passed in 24 files**, 16.03 seconds;
  statements 99.06%, branches 97.57%, functions 100%, lines 99.83%.
- ESLint, TypeScript, changed-file Prettier, production build and
  `git diff --check` passed. Build: 2199 modules, JS 381.91 kB /119.42 kB gzip.
- Offline Chromium probe: nativeDisabledRetainsFocus=false,
  ariaDisabledRetainsFocus=true. Initial sandbox launch was blocked; scoped
  escalation succeeded. No app, authentication or network was accessed.
- No backend rerun, rebuild of running services, dev/prod browser access,
  push, PR action, merge or deployment. Root owns the next CI run and review.

## Deviations and remaining evidence

Rule 1 bug fix: use semantic pending disablement to fulfill the existing
manual-refresh focus contract. Retry removal received focused recovery
handling because otherwise successful retry drops focus to the document.
No new dependencies, trust boundary, endpoint, schema, known stub or tracked
file deletion was introduced. Actual full-flow Chromium verification remains
pending CI; the offline probe proves the DOM cause, not the complete flow.

## Self-Check: PASSED

Both changed page/test pairs and this report exist. The RED commit resolves.
The final GREEN commit contains only these scoped files and this report.
Root's four pending UAT/review/release documents and unrelated `.claude/`
files were preserved.
