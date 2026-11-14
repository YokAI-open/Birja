# Plan 10 bounded CI runner fixes — 2026-11-09

Actual CI run `42583320799` at approved/pushed source
`c085a766a056b017fce1d9d6e2f737541867ae79` failed its image and ops jobs;
backend, frontend and e2e succeeded. This records local corrective work only.
It does not claim passing current-head GitHub CI or complete Plan 10.

## Observed failures and corrections

- Ops: `test-db-config.sh` invokes host `uv run --locked --no-sync pytest`,
  but the ops job did not install uv or prepare the host backend environment.
  Add the existing `astral-sh/setup-uv@v10.3.2` setup and backend
  `uv python install` / `uv sync --locked` before the operational contracts.
  Default dev/audit dependency groups and existing checks remain intact.
- Images: all five public scanner logs reported `mkdir /cache/db: permission
  denied`, with empty reports. These were scanner failures, not vulnerability
  results. Private cache mode 0700 and archive mode 0600 belong to the host
  caller; container root with all capabilities dropped cannot access them on
  a nonroot runner. Add `--user <effective UID>:<effective GID>` to the existing
  isolated scanner invocation. Preserve the pinned scanner, read-only root,
  read-only input mount, capability drop, no-new-privileges and strict raw
  HIGH/CRITICAL checks including unfixed findings. No suppression or mode
  relaxation was added; original failure evidence remains available.

The exact ops fixtures also use Docker/Compose, Python stdlib, OpenSSL, standard
Ubuntu utilities, and the already configured verified restic binary. The
identified missing prerequisite is the host uv/backend environment; no broader
host installation changes were made.

## TDD and local validation

- RED `c5fc244`: CI contract failed for absent setup-uv; image contract failed
  its expected clean case without a caller-identity scanner invocation.
  Regressions mock effective UID/GID `1001:1002` and assert private modes,
  read-only archive mount, isolation flags, severity and absence of
  `--ignore-unfixed` across the existing scan failure cases.
- GREEN `7d5d8c2`: minimal workflow and scanner source fixes.
- `python3 deploy/tests/test-ci-ops.py`: 5 passed, 0.002 seconds.
- `python3 deploy/tests/test-image-contracts.py`: 13 passed, 0.439 seconds.
- Ruff lint passes for scanner and CI contracts; image contracts pass with
  only preexisting S102 excluded. Baseline `c085a766` independently reproduces
  that unchanged S102 finding at image-contracts line 91.
- Ruff format passes for scanner, CI contracts and the entire modified
  `Scans` class. Full image-contract file format check fails on existing
  untouched sections; baseline `c085a766` independently reproduces that result.
  Those unrelated sections were left unchanged.
- `git diff --check`: passed. Neither task commit deletes files.

## Actual nonroot Docker permission proof

The approved pinned scanner already existed locally:
`aquasec/trivy@sha256:2e6c00d711ab4ae41d8a30c2c1fd3bd3b62704c177bb120f95012e939edfb3df`.
The temporary proof `/tmp/birja-ci-runner-permission-proof.py` ran as a real
nonroot host process using `setpriv` with UID/GID `1001:1002` and Docker socket
group access. It imported the actual corrected `isolated()` function and used
only private disposable public fixtures and the pinned scanner's shell:

1. Prior container-root invocation with all other isolation flags identical
   failed to create `/cache/db` with permission denied.
2. Corrected caller-identity invocation verified container UID/GID, read the
   mode-0600 read-only input, and created/wrote `/cache/db` successfully.
3. Cache/work directories remained mode 0700 and the input remained mode 0600.
   Temporary fixture cleanup completed; runtime was 0.972 seconds.

Output was limited to:
`nonroot_host_uid_gid=1001:1002 previous_root_capdrop_denied=true caller_identity_read_write=true private_modes_preserved=true`.
This proves bind-mount permissions with real Docker, not a fresh vulnerability
scan. Full actual five-image scans and independent review remain with the
parent task before requesting publication approval.

## Boundaries retained

No remote write, merge, release, deployment, production access, backup timer
change, recovery installation change or recovery archive rebuild occurred.
The installed `d5fe2059` recovery payload is unaffected by these CI-only files.
The owner-deferred first calendar backup observation, Plan 09, DEPL-02 and
whole-phase acceptance remain pending. Other working-tree edits and the
preexisting untracked `.claude/` directory were preserved.


## Actual CI and corrective validation —2026-11-09

CI42583320799 on approved/pushedc085a766 completed FAILURE. Backend616 tests/
99.80%overall/100%critical, frontend264 and browser10passes/1expectedproduction
CSPskip succeeded. Actual trade.spec and complete portfolio-history buy/sell
flow executed. Image/ops/ci-pass failed; no green aggregate claim.

All5original image logs show mkdir/cache/db permission denied and empty reports,
not vulnerability findings. Ops lacked hostuv/locked dependencies required by
test-db-config.sh. REDc5fc244/GREEN7d5d8c2 adds the established setup-uv and
uvpythoninstall/uvsync--locked to ops, and effectiveUID:GID to scanner Docker
runs. Four source/test files,39added lines,11implementation lines. Private
0700cache/0600input and all readonly/capdrop/no-new-privileges/pin/rawseverity
checks remain intact. No suppression or image/application changes.

Independent06-10-CI-FIX-REVIEW reports0BLOCKER/0WARNING;5CI/13image tests pass.
Real nonroot hostUID1001:GID1002 Docker proof reproduces old denial and proves
corrected private access in0.972s. Existing S102/untouched formatting baseline
was reproduced and left unchanged; changed source/sections pass focused checks.
One fresh actual5image scan passed32.416s, every target0HIGH/0CRITICAL,
DBUpdatedAt2026-11-09T06:57:06.372182267Z/DownloadedAt08:17:06.729314674Z.
Original CI logs/artifacts and new raw reports remain ignored/private under
pr-preparation. No recovery archive/replay/install, provider/timer/prod action.

The original publication approval namedc085a766. Prepare the exact corrective
candidate after the evidence commit, then request its follow-up push/PR-body
update before publishing. Actual corrective-head GitHub CI remains pending;
no merge/release/deploy approval.09nightly proof remains owner-deferred and
10/15plans remain complete. No09/10SUMMARY or DEPL completion.
