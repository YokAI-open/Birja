---
phase: 25-finish-the-trading-flows-and-verify-the-integrated-app
reviewed: 2026-11-26
depth: standard
base_commit: 16f7763
reviewed_through: 8fc6ba8ec4f935f4ce18ec29f9800474c14161a7
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 25 code review

Independent static reviews covered the new backend History read and cursor
contract, the CI timing changes, the application frontend, and the guarded
browser fixtures. The backend and CI review found no blockers or warnings.
It traced the active owner fence, strict filters before ordered seek,
legacy cursor compatibility, and the exact seven-stage recovery receipt.
The frontend and browser reviews found the items below. All were rechecked
on the corresponding repairs.

| Finding | Resolution and targeted evidence |
|---|---|
| Curated stock repricing silently replaced the active preview. | `183ffab` provides a persistent live status for preview readiness and replacement. The stock tests retain renewed explicit confirmation and original-result recovery. |
| A rounded stock execution price could hide a real change or differ from the value displayed in History. | `183ffab` uses the same exact decimal stock formatter in previews, replacements, fills and History. The sub-cent reprice and matching receipt and History assertions passed. Cash and fees use cents. |
| A failed curated draft preview fell back to the empty-quantity prompt. | `183ffab` displays one retryable alert with the requested quantity retained. The original-order result check still handles ambiguous submission. |
| A pending OTP request could drop the focused button, and successful resend could leave focus away from the cleared code. | `1755c2b` keeps the controls focusable, preserves duplicate-request guards and moves focus to the cleared code only from the active resend control. All 22 sign-in cases in the affected replay passed. |
| Browser assertions used the catalog label for the curated and crypto portfolio choosers. A root-only zoom probe left fixed-size text unchanged. | `9d3c6cb` uses the actual accessible names, checks one chooser, measures doubled computed text sizes and verifies keyboard reach at 320px. The comparison packet omits codes and traces. |
| The actual History page placed refresh below the chooser and used separate cards. | `f99b1eb` aligns the chooser and refresh and adopts the approved divided list. All 61 focused History tests passed, with the existing filtering, ownership, disclosures and pagination preserved. |
| The integrated test uncovered a catalog fixture fixed to 0027 and overlapping dividend batches in one disposable database. A retained assertion still expected the previous holdings heading. | `9d3c6cb` checks the actual 0028 fixture revision. `aec88bc` uses a separate bounded real dividend case with an explicit short page and preserves the 28-payment test. The mixed holdings case asserts current ticker headings, exact cash and the same owned trade destination. |
| The retained split held a stock used by a later trade case in the shared synthetic book. | `729f216` moves the retained dividend, correction and split journey to KO. The financial totals, original links, uniqueness and pagination assertions still run. |
| The focused History retry could move below the viewport when an append failed. | `0087e99` reveals the same active retry control while preserving its focus and scope. Changing filters or portfolios cancels the old intent. The 63 focused History checks and the real clipped-retry browser regression passed. |

The corrected stock checks passed 113 affected cases. The final static
recheck through `aec88bc` confirmed the four initial frontend resolutions,
the chooser and CSS text checks, preserved financial assertions and the
narrow History presentation change. [Validation](25-VALIDATION.md)

The final independent recheck covered `729f216` and `0087e99`. It verified the
retained KO payment and split assertions, the guarded synthetic fixture scope
and the focus and scope checks before scrolling. The complete frontend run
passed 1,441 tests and the guarded Chromium replay passed all 18 cases.
[Browser receipt](25-BROWSER-RECEIPT.md)

## Hosted browser follow-up

Independent review covered `622459e..8fc6ba8` after the first full hosted
browser job failed. The live and chart locators address separate status
containers. The portfolio checks retain exact cash and exclude the stale
total after expiry, and the layout checks measure the approved 44px
chooser and user interaction at each existing width. The catalog test
waits for the destination chooser's accessible description. The runtime
change is one CSS declaration that wraps the company name on narrow
screens. All 113 runnable cases passed. [Corrective candidate](25-CANDIDATE.md)
