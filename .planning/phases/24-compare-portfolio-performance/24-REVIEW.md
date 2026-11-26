---
phase: 24-compare-portfolio-performance
reviewed: 2026-11-26
depth: standard
base_commit: 7bb868f4492dbbc1b277d64a1a0d6f8db73491ca
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 24 code review

Independent reviews covered the 0028 schema and grants, exact daily
capture and private owner API, the selected portfolio and overview,
and encrypted recovery, deployment compatibility and CI staging.
The schema review found no issues with the active-portfolio fence,
migration admission or restricted roles. The scoped reviews and
replays resolved the findings below.

| Finding | Resolution and evidence |
|---|---|
| Loss of portfolio access after Update stranded keyboard focus. | `ce1db01` restores focus to the surviving management target on authority loss. The App regression covers the route and portal transition. |
| Update could pair stock age with an unrelated display timestamp, and the retained deletion test title fell out of the execution filter. | `ce1db01` keeps the displayed age and exact timestamp together and restores discovery of the retained deletion scenario using the current Keep portfolio label. |
| Reviewed catalog mark grants could not persist explicit restrictions on daily aggregate use or backup. | `b6a1eb6` carries both typed restrictions through the actual grant writers. The restricted mark still contributes to current valuation and records a null daily total. |
| Retrying a portfolio trend request could drop keyboard focus. A paused request could look like an empty series. | `545ee39` preserves the focused retry while waiting and restores focus on success. The 57 focused checks include offline and retry regressions. |
| Exact date digests could depend on PostgreSQL DateStyle. | `08a1948` serializes the new UTC date as ISO in the canonical projection. The isolated cold component verified the result on a fresh server. |
| The cold-stage receipt accepted the same read marker before and after restore. It lacked the exact measured predecessor image digest. | `50347df` requires a marker emitted only after the restored owner reads and compares the recorded 0027 image binding during receipt verification. The 45 campaign contracts and 114 CI contract checks passed after the fix. |

The last recovery harness review covered source through `5026e3c`.
The two test-evidence changes above were checked against the reviewed
failure cases. Final browser and recovery evidence is recorded in
[Validation](24-VALIDATION.md).

The first comparison exposed undersized overview card names on phones.
`33f2247` matches the approved 23px at desktop and phone widths using rem
units and retains wrapping. The guarded Chromium cases exercise the title
at both sizes and with enlarged text. `741c337` uses the established
Playwright browser-expression pattern for those test callbacks. The checked
Node project type-checks without changing TypeScript configuration.

The recovery receipt binds the frozen `74e852d` source. The subsequent
browser and typography adjustments leave backend, deployment, CI and
recovery fixture inputs byte-for-byte identical. The local rehearsal
passed in 56m 19s while the backend suite was running. Hosted CI must
confirm the existing 45-minute budget.
