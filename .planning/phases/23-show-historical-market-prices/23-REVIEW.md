---
phase: 23-show-historical-market-prices
reviewed: 2026-11-26
depth: standard
base: 3670ac4
backend_review_head: f0c76a3
frontend_review_head: 6d61c49
rechecked_through: 775c435
files_reviewed: 26
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 23 code review

Independent standard reviews covered the history API, provider adapters,
cache and scheduler, both Compose entry points, the history client, chart
and Markets integration, and their focused tests. The display path keeps
current-price and order authority independent. The API binds history to the
active identity and range, and the scheduler rechecks evidence before fetch
and publication.

## Resolved findings

| Finding | Resolution and replay |
|---|---|
| The existing critical scheduler coverage gate required tests for the new configured entry point. | `8de0390` exercises history disabled, Kraken and IEX, plus ticker observation, private client and cache wiring. All 130 coverage cases passed. `scheduler.py` and `stock_scheduler.py` reached 100% line and branch coverage. |
| A relative Redis expiry could extend permitted storage after a write delay. The API could return a result that expired during its authority recheck. | `3889b3a` publishes with the exact absolute deadline and rechecks that deadline before returning the series. The real-Redis replay verifies the deadline and refusal when it passes during the read. |
| Slow history jobs could monopolize the queue. Kraken ticker priority could drift after a late wake-up. | `3889b3a` clears the exact failed demand and tracks the fixed ticker cadence conservatively. The replay verifies another job can proceed and a late ticker does not create false headroom. |
| The concurrent demand test could cross a clock bucket. Unexpected history errors used order-recovery wording. | `3889b3a` fixes the test clock and gives the route a chart-specific private response. Existing stock route behavior remains covered at 100%. |
| A slow shared session refresh could outlive the chart deadline. The decoder accepted normalized invalid dates or non-UTC offsets. | `87b8c36` bounds a chart caller's wait, preserves shared refresh, and uses the existing canonical UTC validator. Focused tests cover both paths. |
| A 1D equity chart could describe a prior regular session as the past day. Flat prices could repeat axis labels. Retrying could leave a keyboard user without focus. | `87b8c36` shows the regular session and the actual latest interval time, increases axis precision when labels repeat, and restores focus to the selected range. The chart tests cover the session date and retry focus. |
| Full-page captures exposed blank scrolling below the desktop workspace. | `775c435` contains visually hidden row text within the list's scroll region. The final isolated browser run verifies that all three 1440 × 1000 desktop captures have no extra document scroll. |

All 335 planned backend regression tests passed before the review fixes.
The affected review replay passed 85 backend tests, with 100% line and branch
coverage of the touched stock route, and mypy and Ruff passed. The reviewed
chart repair passed 57 focused client tests, scoped lint and app type checking.
The browser replay used the final CSS and passed all 11 cases.

## Live qualification

Record the distinction between measured account-wide and history-only limits
before enabling history. The ready chart includes its actual latest interval
time. Check any source-specific browser display or retention condition as
part of live qualification. The current local results do not establish a
live source scope. [Source qualification](23-SOURCE-QUALIFICATION.md)
