---
phase: 04-trading
plan: 10
status: passed
updated: 2026-10-29
release_tag: v0.3.0
release_sha: 6425dad1b9c5718eb969688cbe3e2b0ac7cd3224
---

# Release 0.3 checkpoint

All release tasks are complete. The user replied `appoved` to the final
live-browser check; the post-check production trade count was 2 (from 0).
See 04-10-SUMMARY.md. Final code review, hotfix and goal verification are
tracked by the phase closeout; this document preserves the v0.3.0 evidence.

## Authorization

The user chose `push-pr, release-now`, then answered `yes, do it all` after
reviewing the prepared release. The assistant stated that this covered
remaining release pushes, PRs, merge commits after green CI, tag publication,
back-merge and production deployment. Final browser verification remained
the user's checkpoint. No further permission is needed for these already
authorized actions.

## Git-flow evidence

- PR #19 merged into develop as `5dc514d` after green CI.
- `release-0.3` was cut from updated develop; `22ff0d5` changes only the four
  project version files to 0.3.0, with no dependency changes.
- Planning closeout commits were carried onto the release because PR #19
  merged before they were created.
- [Release PR #20](https://github.com/YokAI-open/Birja/pull/20) targets main.
  `b605079` merges production hotfix ancestry without changing files.
- [CI run 40843969400](https://github.com/YokAI-open/Birja/actions/runs/40843969400)
  passed backend, frontend, image, e2e and ci-pass.
- The assistant merged #20 with a merge commit under the user's blanket
  authorization: `6425dad1b9c5718eb969688cbe3e2b0ac7cd3224`.
- Annotated tag `v0.3.0` was published on that main merge commit.
- `0388183` carries the tagged main merge back into release-0.3 without
  changing files so the tag is an ancestor of develop too.
- [Back-merge PR #21](https://github.com/YokAI-open/Birja/pull/21) passed all
  five checks in [run 40844466345](https://github.com/YokAI-open/Birja/actions/runs/40844466345)
  and merged as `130dfb6a2498f4763795923918e4f377197179ab`. Read-only GitHub
  state showed it already merged when the assistant reached that step.
- Verified the published tag resolves to the main merge SHA and is an
  ancestor of both origin/main and origin/develop.

## Local release validation

- Backend: 476 tests; 99.89% overall coverage; critical-path list 100%.
- Frontend: 161 tests; 98.88% statements and 99.76% lines.
- Backend lint, format and mypy passed; frontend lint, types and build passed.
- Both lockfiles were checked to change only project version entries.
- The isolated test stack was removed after the checks.

## Production evidence

- Read-only sub-cent cash compliance count was 0 immediately before deploy.
- `/srv/birja/deploy/deploy.sh` ran once, exited 0, and printed
  `Deploy complete: main`.
- Migrations 0005 -> 0006 -> 0007 applied successfully.
- Backend and scheduler reported healthy. All 15 active coins were priced;
  the oldest price was 28 seconds old during origin smoke verification.
- `/srv/birja/deploy/smoke-prod.sh`: `SMOKE OK (38 checks)`.
- `/srv/birja/deploy/smoke-prod.sh --public`: `SMOKE OK (9 checks)`.
- Both smoke modes verified holdings/BTC returns 401 and trades/quote
  returns 403 when signed out.
- Deployment log and production checkout both match the tag SHA:
  `6425dad1b9c5718eb969688cbe3e2b0ac7cd3224`.
- Recorded deploy entry:
  `2026-10-29T08:50:10Z 6425dad1b9c5718eb969688cbe3e2b0ac7cd3224 /var/www/birja/releases/6425dad-20261029T084949Z main`.
- Production trade count before the user's live check: 0; after approval: 2.
- No secrets, recipient addresses, login codes or individual balances were
  read or recorded. Smoke scripts perform only their defined synthetic
  rejection checks; the assistant placed no trades or sign-in requests.

## Completed manual checkpoint

1. User opens https://birja.nist.one and signs in with an emailed code.
2. Markets -> Trade BTC: confirm Live price; buy $10.00, with fee $0.02 and
   exact cash change -$10.00. Check the fill and resulting balance.
3. Sell the entire displayed holding quantity and check the proceeds.
4. Confirm a signed-out private window shows the sign-in screen.
5. After the user says approved, record only the aggregate production trade
   count again and finish 04-10-SUMMARY.md using this evidence.
6. Preserve code review, regression/goal verification and phase-closeout
   steps from execute-phase before marking Phase 4 complete. Local checkpoint
   commits after back-merge still need inclusion in develop via PR; never
   commit directly to main/develop.

The manual checkpoint is complete and approval is recorded in the summary.
Do not repeat the v0.3.0 deployment or republish its tag. The reviewed
stale-price correction is being released separately as v0.3.1.
