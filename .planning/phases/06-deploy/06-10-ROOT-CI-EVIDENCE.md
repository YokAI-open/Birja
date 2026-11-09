# Plan 10 privileged synthetic CI correction — 2026-11-09

Actual CI `42585485295` at approved/pushed `57b8774` passed image, backend,
frontend and e2e; ops failed during offline prerequisites. The two errors were
the actual TLS caller in lock reuse/contention tests. `provision-db-tls.sh`
requires effective UID 0 and root-owned synthetic directories before locking;
the GitHub runner is unprivileged. Later real TLS fixtures also require root
for `chown(0,70)` and actual provisioning. These guards remain unchanged.

## Local changes and TDD

- RED `b1dd6dd`: five-test CI suite fails on missing explicit root execution;
  fixture regression fails on missing exact-checkout source Git helper.
- GREEN `0637b48`: use `sudo --` only for the prerequisite suite and serial
  real synthetic image-transition/recovery/roles/TLS/old-image scripts. Host
  uv/db-config contracts retain the prepared runner environment. Existing
  required producers, isolation guards and fixed-project cleanup remain.
- Add fixture-only `source_git` with command-scoped
  `-c safe.directory=<resolved checkout>` and explicit `-C <checkout>`.
  Route original-checkout reads in ops/rollback fixtures through it. Private
  root-owned fake-host Git operations and production helpers remain unchanged.
  No wildcard trust, checkout ownership/mode change or global Git config.

## Concrete ownership and privilege proof

Temporary script `/tmp/birja-ci-root-git-proof.py` created two disposable Git
repositories owned by UID/GID 1001:1002, then ran Git as root with the actual
fixture environment (`HOME=/tmp`, fixed PATH/LANG). Plain Git rejected dubious
ownership. The exact checkout exception and actual `source_git` helper passed;
the unrelated repository remained rejected. No global config was modified.

The same proof invoked the unchanged actual TLS script only inside a private
`/tmp/birja-backup-test-*` directory: real nonroot invocation was rejected;
root create/check passed with server-key owner 0:70 and mode 0640. All temporary
repositories, keys and directories were removed by bounded context cleanup.
Output contained only public booleans and the expected key ownership/mode:

```text
root_caller_runner_owned_checkout_denied=true exact_command_scope_allowed=true unrelated_checkout_denied=true global_config_mutations=0
actual_synthetic_tls_nonroot_denied=true root_provision_check_passed=true key_owner=0:70 key_mode=0640 production_paths_touched=0
```

The combined actual proof completed in 1.679 seconds.

## Validation and remaining integration proof

- `python3 deploy/tests/test-ci-ops.py`: 5 passed, 0.002 seconds.
- `python3 deploy/tests/test-deploy-prerequisites.py`: 18 passed, 7.918 seconds,
  including both actual TLS lock callers and the new source-read assertion.
- Ruff lint/format passes for modified CI/prerequisite tests. Fixture lint
  passes with only existing S102/PLW1510 excluded; baseline `57b8774` confirms
  the same three findings (one S102, two PLW1510). Full fixture format already
  fails at baseline; the new helper independently passes formatting.
- `bash -n deploy/tests/test-rollback-db-security.sh` and `git diff --check`
  passed. Neither task commit deletes files.

The parent task retains independent review and one serial integration proof:
run the exact new root CI commands for `test-db-operations.sh --image-transition`,
`test-db-operations.sh --all`, and `test-rollback-db-security.sh` against only
their fixed synthetic projects. No full application or image gates were
repeated; GitHub already passed those at the prior approved head. Current-head
GitHub ops success is still unproven and publication needs fresh approval.

No production TLS/backup/recovery payload, installed archive, timer, B2 or
production resource was changed. No remote write or new phase completion was
performed. Parent planning edits and the preexisting `.claude/` remain intact.


## Root-fixture correction ready for publication —2026-11-09

Independent06-10-ROOT-CI-REVIEW reports0BLOCKER/0WARNING and independently reran
5CI/18prerequisite tests. Actual private owner/TLS proof and focused source
checks pass; production root/owner/mode guards remain unchanged.

One serial local run of the exact CI synthetic producers as actual UID0 passed:
image-transition38.695s; --all recovery/roles/TLS151.225s; actualold rollback
106.876s, all exit0. Current source0637b48df9d88bbda7ad0141029febde30a296ad
remained unchanged during those runs. Final label queries confirm0containers/
networks/volumes across birja-ops-test, birja-restore-check,
birja-image-transition-test and birja-rollback-test. Immediate command/result/
elapsed logs are retained in ignored pr-preparation/root-ci-* records.
No production/provider/installed recovery/timer change or new image scan.

Actual GitHub image artifact for previous approved57b8774/run42585485295 was
downloaded and checked: all5targets reportok=true/exit0/qualifyingfindings0.
Backend/frontend/browser also passed that actualrun. Only ops/ci-pass failed
the newly corrected root setup. Current root-fix head has not run on GitHub
and is not approved to push yet. Do not call the required aggregate green.

Prepare exact next3commit candidate (RED/GREEN/evidence) for explicit follow-up
push. The owner may authorize this update only, or reviewed/tested CI/test-only
follow-up corrections plus their planning records until required CI succeeds,
with all gates intact. No application/runtime/image/recovery/production change,
merge or deployment authority is inferred.09calendar proof stays deferred and
10/15 plans complete; no09/10SUMMARY/DEPL advancement.
