# Phase 21 publication and CI

The owner approved publishing `feature/milestone-v1.4` at
`3c1eb42c99b3873bceb596ce39bafeda6dbde3a0` into `develop` and monitoring all
six required jobs, with reviewed and tested CI, fixture and planning fixes
on that feature branch until CI passes. The approved PR base was
`6702b74f93da01f35c97d978902fef277547a161`. [PR #46](https://github.com/YokAI-open/Birja/pull/46)

## First run

[Run 45601104649](https://github.com/YokAI-open/Birja/actions/runs/45601104649)
tested the approved feature head. Frontend and image verification passed.
The E2E job failed a curated closed-market assertion; its report displayed
the correct price and accessible timestamp in the same paragraph. Ops
passed applicable inherited checks through the exact retained `0025`
restore, then the cold `0026` stage stopped on a missing test-shell
dependency. Backend passed all 3,941 tests, measured 94.41% overall and
100% critical coverage, and passed its dependency audit. The aggregate
check failed with the E2E and ops results still red.

Commit `25b0402` fixes the E2E locator to check the visible price and exact
timestamp together and uses portable `grep` for the existing recovery
assertions. The two related Chromium cases, TypeScript, ESLint, Prettier,
176 portable recovery/runner/CI contracts, the paired encrypted
`0025`/`0026` restore and script syntax passed locally. Independent review
found no blocker for the two changes.

The first run completed before publishing the consolidated fixes. Merge
into `develop` requires green checks on the actual feature head and
explicit approval. Release and main artifact identity are pending.

## Follow-up run

[Run 45611951920](https://github.com/YokAI-open/Birja/actions/runs/45611951920)
tests feature head `f3069343bd5d158c43f0653acc3df9fcc0e3bb5d`. Frontend,
image, the full browser suite and ops passed. Hosted recovery logs confirm
the exact retained `0025` restore, encrypted current `0026` on the fresh
restore server, the unchanged original before writes, and exact `0026`
volume/receipt recovery after writes. The old image refused `0026`.
GitHub finalized PR artifact `15023005738` with transport SHA-256
`8eb74557fd40e7a90fb6b172d7338ef7446a09ea1a7fe0550b46a8c17cf23f9b`.
The protected rollout requires the artifact from the eventual successful
`main` run. Backend passed all 3,941 tests in 54:06 with 94.41% overall
and 100% critical coverage. Its audit passed and `ci-pass` succeeded.
GitHub reports PR #46 clean and mergeable at that exact head into the
unchanged `develop` base. The owner merge decision is pending.
