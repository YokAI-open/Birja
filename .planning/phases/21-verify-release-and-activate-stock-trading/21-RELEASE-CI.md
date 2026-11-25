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
GitHub reported PR #46 clean and mergeable at that exact head into the
unchanged `develop` base.

## Develop merge and release preparation

The owner approved merging the green feature head and preparing the
release locally. PR #46 merged at 13:16:48 UTC on 2026-11-25 as
`e1b79566c38f75254827961216c67c390ce94d68`. Both the feature head and the
merge have tree `1df6b476c62eab9b7f9ed1f768ab558a8b314167`. The merge has
the checked base and approved feature as its two parents. The verified
`main` head `07d3aa5c627b5ba550aa2d11baa13e2becaf3aa9` is an ancestor.

The local `release-0.8.0` branch starts at that merge and carries forward
the saved CI evidence. Version 0.8.0 is the next minor version after
`v0.7.1` for the catalog and trading feature. The backend and frontend
manifests and locks differ only in their root application version. The
frontend audit fingerprints match those new files and the existing issue
35 advisory, scope and expiry are preserved. The offline uv lock check,
frontend audit tests, lint, typecheck, build and diff checks passed.
Successful exact-main CI and release publication remain pending.

## Release PR

The owner approved pushing the local release head and opening its PR into
`main`, with reviewed CI, fixture and planning fixes on the release branch
through the check run. [PR #47](https://github.com/YokAI-open/Birja/pull/47)
tests release head `84511f0864799d5a058129644a89a7ce37f88bdc` against
`main` base `07d3aa5c627b5ba550aa2d11baa13e2becaf3aa9`.
[Run 45623598560](https://github.com/YokAI-open/Birja/actions/runs/45623598560)
The frontend, image, full browser and ops jobs passed. The recovery
campaign restored the exact retained `0025` and cold encrypted `0026` on a
fresh server. It preserved the original volume and ledger before writes
and recovered exact `0026` candidate data and receipts after writes. The
predecessor refused `0026`. PR artifact `15029749173` has transport SHA-256
`efb0dfd5ad9abdedf78abdadd0bdc6aaf1cd5d3dbb406fdc7d2a85c52d85a2c6`.
The artifact must be replaced by the verified artifact from the eventual
successful `main` run for protected rollout.

Backend passed 3,941 tests with 94.41% overall coverage and 100% critical
coverage. Its dependency audit passed. All six jobs, including `ci-pass`,
completed successfully on the exact release head. GitHub reports PR #47
open, clean and mergeable into the verified `main` base. The next
checkpoint is explicit owner approval for the main merge commit.

## Main merge

The owner approved the merge of the checked release head. PR #47 merged
at 14:23:00 UTC on 2026-11-25 as
`4c839f5642f60771a5a376f2956bd7c8ab28aca9`, with parents
`07d3aa5c627b5ba550aa2d11baa13e2becaf3aa9` and
`84511f0864799d5a058129644a89a7ce37f88bdc`. The merge tree
`ede70d1f0320f6efd7907a7ec35463453dca3a7b` matches the reviewed release.
[Main run 45633446612](https://github.com/YokAI-open/Birja/actions/runs/45633446612)
tests the actual main merge commit on the push event.

The [main recovery job](https://github.com/YokAI-open/Birja/actions/runs/45633446612/job/139272499837)
failed in the retained `0012` corporate-action scenario. After the November
25 session opened, the next opening was November 27. The older fixture
already held a session row for that date under calendar generation 3. Its
scenario expected generation 8 and kept the existing row untouched.
PostgreSQL correctly rejected the mismatched calendar in the resolution
function. No release artifact was staged by this run.

The fixture refreshes the selected session under the scenario's active
calendar while retaining its primary key. There are no runtime or
migration changes. The isolated retained-source PostgreSQL replay
reproduced the same rejection on the prior fixture, then passed resolution
and split application with the patched fixture. It confirmed November 27
at 14:30 UTC, a stable row ID and new generation 8. All 44 recovery-runner
contracts and 113 ops CI contracts passed. Independent focused review
found no blockers. The full campaign remains required on the corrective PR
and its resulting main commit.
