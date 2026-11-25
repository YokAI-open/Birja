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
