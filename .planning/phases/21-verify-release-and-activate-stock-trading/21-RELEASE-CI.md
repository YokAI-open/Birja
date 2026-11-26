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

## Corrective release PR

The owner approved publishing fixture correction `58a90b3fe44b46e360b3c36a4098af9774ad6882`,
opening its [PR #48](https://github.com/YokAI-open/Birja/pull/48), merging
that exact head into main only after all six checks pass, and monitoring
the resulting main run. The PR has the checked main base `4c839f5`.
[Run 45636439110](https://github.com/YokAI-open/Birja/actions/runs/45636439110)
tests the approved corrective head.

The corrective PR's frontend, image, browser and seven-stage recovery
jobs passed. The hosted recovery log confirms exact retained `0012` rows,
schema and sequences through the repaired scenario. The same archive also
passed retained `0025`, cold encrypted `0026` on a fresh server, and exact
data before and after the first write boundary. GitHub uploaded that
PR archive. Its SHA-256 is
`a32f8c92f66eff8b081538fc4989e282c5da2e2c5320cf9008b315bb34efde5d`.

Both the original main run and corrective PR backend jobs failed
`test_catalog_renewed_review_rechecks_retained_event_id`. Each stopped
after one test failure and 2,526 passes. The local PostgreSQL reproduction
showed the mocked dividend opening fell before the catalog journal origin,
so the app correctly omitted the event from the new empty book. Renewal had
no retained ID to recheck. The corrective test records today's process date
with ex, record and payable dates at the next verified session opening.
It retains the exact known-ID recheck and reconciliation assertions.
All 60 tests in the monitoring module passed on disposable PostgreSQL and
Redis, Ruff lint and formatting passed, and independent review found
no blockers. The full PR suite and resulting main CI remain required.

The owner approved pushing `1024e95261f5e2c9608a60f820e4c73a869fce99`
to PR #48, merging that exact commit after all six required checks pass,
and monitoring the resulting main run. The branch was updated at that
commit with [run 45647160066](https://github.com/YokAI-open/Birja/actions/runs/45647160066)
on the new head.

All six jobs passed, including the full browser and recovery campaigns.
The backend passed 3,941 tests, 94.41% overall coverage, 100% critical
coverage and the dependency audit. GitHub reported PR #48 clean and
mergeable against the checked main base.

## Corrective main merge

PR #48 merged under the owner's exact-head approval at 16:38:42 UTC on
2026-11-25 as `0f4a42f4dfec657314d2feaab1c5a539c69518b8`. Its parents
are `4c839f5642f60771a5a376f2956bd7c8ab28aca9` and
`1024e95261f5e2c9608a60f820e4c73a869fce99`. The merge tree
`0eb379b4240d0a28918dffcab0825f12c2c555e7` equals the tested PR tree.
[Main run 45656126522](https://github.com/YokAI-open/Birja/actions/runs/45656126522)
tests the actual corrective main commit on the push event.

Attempt 1 passed frontend, image and browser. Its recovery job passed the
retained restores, cold encrypted `0026`, role and TLS stages, then
exceeded the 180-second launcher timeout during the selected cutover.
That command completed in about 71 seconds in the successful exact-tree
PR run. The failed main attempt staged no tooling artifact. The existing
timeout and all recovery assertions remain in force for the same-commit
failed-job retry.
[Attempt 1 recovery job](https://github.com/YokAI-open/Birja/actions/runs/45656126522/job/139353159962)

Attempt 1 backend passed 3,941 tests with 94.41% overall and 100% critical
coverage. The Python dependency audit passed. Its aggregate failed
because of the cutover timeout. GitHub started
[attempt 2](https://github.com/YokAI-open/Birja/actions/runs/45656126522/attempts/2)
with failed jobs only on the unchanged main SHA. Backend, frontend, image
and browser checks carried forward from the completed attempt.

## Verified main recovery artifact

Attempt 2 passed the full seven-stage recovery campaign on
`0f4a42f4dfec657314d2feaab1c5a539c69518b8`. The retained `0012` and
`0025` restores matched their source. A fresh server recovered the cold
encrypted `0026` state. The predecessor reopened its original state
before writes. The candidate reopened exact `0026` state and receipts after
writes, and the predecessor refused that schema. The aggregate passed.
[Successful main run](https://github.com/YokAI-open/Birja/actions/runs/45656126522/attempts/2)

GitHub artifact `15050407948` was downloaded by ID and verified against
transport SHA-256
`09ab62715e12a3f2958c313da1438bbbf7bf1cc303138b7dab7c05553509edc5`.
The private local archive is
`/tmp/birja-backup-test-main-45656126522.zhA4RL/recovery.tar.gz`.
Its strict archive SHA-256
`a32f8c92f66eff8b081538fc4989e282c5da2e2c5320cf9008b315bb34efde5d`
matches the hosted recovery log. The trusted verifier confirmed the
complete 75-file inventory, `deploy-recovery-v7`, payload version 6,
schema `0026`, and the payload files against the exact main source.
The receipt SHA-256 is
`075b1ee0c782e4eb6e02d7b3ad3db6fb9f085246728d4fdcb120975ebd93caaf`.

The receipt records success for image transition, retained roundtrip,
cold `0026`, roles, upgraded TLS, fresh TLS and selected rollback. Its
tested main tree is `0eb379b4240d0a28918dffcab0825f12c2c555e7`.
The application tree is `93638e56ad2a02b79dccdae53c26280e5df9b7a8`.
The main backend build context SHA-256 is
`10c217992ee16ce168c0197fdaa634d1b5d7804101f83cfcbe2bbef9ca497e25`.
The authenticated recovery campaign records candidate image
`sha256:2fe59a837539c2472d09e4a138529b950223f0d9a355cc80d81c8f04f6de53c7`,
config SHA-256
`5e6609732b9e960d7798be8151ec5548b8fed6c3444956d6cedcc1298283b2c8`,
and root filesystem SHA-256
`c5ba0e94dfb65aab15b1c86015fbeb275fd6eb1f071e13ae8bc5110af318fe1d`.

The checked main commit is ready for the `v0.8.0` tag and GitHub release
once the owner approves publication. Plan 21-05 also requires the release
back-merge.

## Published release

The owner requested publication and deployment. GitHub published
`v0.8.0` at 19:28:33 UTC on 2026-11-25. The peeled remote tag is the
verified main commit `0f4a42f4dfec657314d2feaab1c5a539c69518b8`.
The release uses the reviewed notes from that commit.
[GitHub release](https://github.com/YokAI-open/Birja/releases/tag/v0.8.0)

The exact release commit is the proposed `release-0.8.0-backmerge`
head into checked `develop` base
`e1b79566c38f75254827961216c67c390ce94d68`. The back-merge awaits
approval and the six hosted checks. Production rollout has its own
scope and prerequisites.
