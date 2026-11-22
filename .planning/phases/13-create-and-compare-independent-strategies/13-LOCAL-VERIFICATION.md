---
phase: 13-create-and-compare-independent-strategies
plan: "17"
status: passed
tested_head: 9527e358bc6953cec7580043703324db194ba396
tested_tree: 9e2af2ddb10ddd28ce5df71d445a42bb39d170e0
completed: 2026-11-19
whole_security: true
critical_modules: 61
critical_coverage: 100
---

# Phase 13 complete local security qualification

The actual complete all-security command passed at one frozen, independently
reviewed source. This record does not assemble earlier partial runs into a pass.
The subsequent uninterrupted seven-stage recovery also passed at the same HEAD;
see [13-RECOVERY-PROOF.md](13-RECOVERY-PROOF.md).

## Actual complete command

    python3 deploy/tests/run-portfolio-validation.py --suite all-security

- Tested HEAD: 9527e358bc6953cec7580043703324db194ba396.
- Tested tree: 9e2af2ddb10ddd28ce5df71d445a42bb39d170e0.
- Branch: feature/milestone-v1.2; all work remains local.
- Started: 2026-11-18T22:21:37.467836Z.
- Finished: 2026-11-18T23:17:50.514156Z.
- Exit: 0; elapsed 3373.046358s, approximately56m13s.
- Private campaign directory:
  /tmp/birja-phase13-plan17-campaign6-20261118-9527e35/.
- Raw log: all-security.log, SHA256
  9ee807da3bcc03f8d062a2da9c46b80df5cf8b84fa4becafc61d9e085a3e56bb.
- Command result: all-security-result.json, SHA256
  a4eba725ebbcd73c64c92f0ee7612960e3053527f56f53c99eb6eb550fcc843e.

The one-shot supervisor ran the literal whole command, then ran whole recovery
only after its successful exit. It used a new private directory, saved PID/start
identity and no recurring schedule. It survived tool-turn boundaries without
restarting or omitting tests. No other database/browser/ops campaign ran alongside
it. The supervisor itself was private test orchestration, not a repository change.

## Measured results

| Gate | Actual result |
|---|---|
| Backend Ruff, formatting and mypy | PASS |
| Full backend pytest | 3343 passed,114 warnings;2202.23s |
| Overall backend coverage | 99.8599767% combined statement/branch coverage;80% gate retained |
| Critical backend coverage | All61modules:5287statements and1668branches, zero misses;100% gate retained |
| Python dependency audit | No known vulnerabilities found |
| Frontend lint, types, formatting and build | PASS |
| Full frontend tests | 55suites,1194tests PASS |
| Frontend coverage | 96.63% statements,93.92% branches;80% gate retained |
| Actual unfiltered browser suite | 79passed,1existing deployed-CSPskip;714.7s |
| Browser inventory | All12explicit specifications, including20new portfolio cases |
| Image builds and runtime smoke | PASS |
| Declared image/CI/browser/validation contracts | PASS |
| Backup, deployment compatibility and remaining infrastructure tail | PASS in the whole command's declared order |
| Real historical PostgreSQL contracts | PASS, including pre-existing-database refusal and preserved current database/roles |
| Real fresh/upgraded development bootstrap | PASS, exact tamper refusals and owned cleanup |
| Five immutable image policies | All PASS, zero blocking findings |

The actual CI critical include list is read by the runner from the reviewed
.github/workflows/ci.yml rather than maintained as a smaller duplicate. Its
SHA256 is 5a5bfdee7ca2f6249203fe9c4b96bd3d4104fa4d56773cfae4a87eec4d8c4787.
This includes the new portfolio-management API and the existing financial,
authorization, login/session, stock-action and recovery-admission critical paths.

The exported backend-coverage.json has SHA256
5c2441dcbf02422101cba37e568632b36598e68f31081442521628bbc60b85aa;
the untouched coverage database is preserved as backend.coverage. The114backend
warnings and frontend test warnings remain visible in the raw logs; none was
hidden through a skip, xfail or weaker gate.

The real browser evidence is at /tmp/birja-phase09-browser-2xnkf52g/. The one skip
is the retained deployed-CSP test, not a new Phase13 scenario. Browser success
does not establish live market-data permission or production stock activation.
The existing browser runner's disposable dev-administrator database connection
is not claimed as restricted-role proof; actual restricted role/TLS checks are
separate gates, including the seven-stage recovery.

## Raw audits and accepted advisory scope

The raw npm report contains14moderate findings and0HIGH/CRITICAL; the unchanged
policy reported no-blocking-findings. Python audit is clean. No package, lockfile,
image pin or waiver changed in this qualification run.

The fresh five-image report has zero qualifying, accepted and blocking findings
for every target. This differs from earlier diagnostic Node results. No dependency
was repaired here and no remediation or closure of issue35 is claimed. The
owner's existing exact artifact/path/version/source/expiry risk record remains
tracked until2026-12-17T00:00:00Z; it was not expanded or needed by these final
image results. Raw earlier findings and failed/diagnostic scans remain preserved.

Scanner: Trivy0.76.1 at immutable reference
aquasec/trivy@sha256:2e6c00d711ab4ae41d8a30c2c1fd3bd3b62704c177bb120f95012e939edfb3df.
Final database UpdatedAt2026-11-18T19:07:09.82030288Z,
DownloadedAt2026-11-18T23:17:26.137638567Z. No unpinned scanner or stale substituted
report qualifies a target. The complete report directory is preserved privately
as image-reports/ in the campaign directory; status.json SHA256 is
3fab16f9bcd63e6c4f4fd024e05f89fff8727d60058e18311e09462b63ebd418.

| Target | Actual immutable engine ID | Raw report SHA256 |
|---|---|---|
| Runtime | sha256:5d8ad2d0c4e6de300697ead971f6b4c258ba3d3831ec2da262fc060045c7fd2f | c65c1715d16ea9b942fa1b673bce5d632c4190d9631382b422611df4db8522e1 |
| Builder | sha256:c74437a99c78e5ac3405ab77375eb985aab579ea8dc9e6f545b00786379d6957 | 566e3c259d5ad9b1ae9b2f15f2e44b8258248c147dd9af1e20fa94e21367cca0 |
| PostgreSQL | sha256:adbf3d8db097696ed6e997b108b51393786be999c04d543502f8959e1bafa8de | c41cb320c695985035bed6adebb59978f23308e05df3c371d392627ef9deccfe |
| Redis | sha256:26bb2dd4412f902f3decd44fba5dfaef4360d97004d44f6cff7f28d6aba19c48 | 2d7b328f7d24c847a829e3c7954bc873a31ecb889a09297ea13292dfca1c564a |
| Node toolchain | sha256:53a4d2b147636a26206d5633b6604049c280de13a1cbe61dfb0fc25ba48683a0 | cbc983eed56748e95df6e0f05ed0526d3b115f44cd4cf38a667d800f46c0106d |

Each row's qualifying/accepted/blocking counts are0/0/0. Full config digests,
registry descriptors, report and exported-image checksums are in the preserved
status/report files; mutable tag names do not replace these identities.

## Frozen source and render association

The supervisor captured and compared all1760tracked inputs, recording regular
file hashes and literal symlink targets. HEAD, tree and every captured input
stayed unchanged throughout both whole commands. source-receipt.json SHA256:
f87c577da55dafaf5cc8b2d5231b0ebb0ae7c0d4c9f8877f3a9c9688bdf0127a.
The final successful supervisor receipt also preserves this outcome:
receipt.json SHA25609909cf5b6874c2304b34d6908db90db3408a3778e53612e17b52b1850e8c9b1.

Selected runtime bindings from that full source receipt:

| Input | SHA256 |
|---|---|
| backend/Dockerfile | 6abf11d09a0154f419c38ee8c23c07a3d05e82fa1e12111d7b33fef8398f5ff3 |
| backend/uv.lock | 201c4282ebf3d0025e092b3ab688516769197f16d5631cef997c88926dc09133 |
| backend/alembic/sql/0020_portfolio_management.sql | 9fe1fd5706df5ac319f7a70dcfe73a437f0886ba7e4a827758fa8c414106963d |
| backend/app/db/portfolio_bootstrap.py | b2f3326a7b19392491c7133fcc9cc34816dcf5b29360a1fc9fdd44ec68ec117c |
| backend/app/db/portfolio_migrate.py | 2e1ee5a8b5f7f489eea1ac45c8df56c8ed6b8f1276e59503f7a13eab9c6d890d |
| deploy/deploy.sh | 4cf88e62ea1c8cb42da3233ee9f2deacf02a1d50f282e0c4b26bc3754109b995 |
| deploy/tests/portfolio-smoke.py | c0b694291279401c60310f67dceecf88071718a71724d2a8864c1ec68caffd8e |
| deploy/tests/run-portfolio-validation.py | 63eb3e7cbfd7ec9c1fbcd9e693c4c9711b08a7f570385e8ed4dacf13bf31db7d |
| frontend/package.json | 73cd4f25fb329d7d0711321ee56dd9f07b25426eb9ddb69f3491396c2ccbdb59 |
| frontend/package-lock.json | 1461d4f89e875a5b915278e9d39ba413608fa4ff816fab6be6b21e280db5475b |

The unchanged source-bound UI packet remains
/tmp/birja-phase13-ui-review.zip, SHA256
724607e83592bd1bda5e86a0b92217478aba93b53127b7cdf5f2d04f0142c361.
Its340-input digest is e082f97d9aaa758fa17a6060877328ed6f6dd39c31f2d66942c00bb7dba47a47.
The actual offline current-source/artifact verifier passed at the final source;
ui-final-source-verify.log SHA256
4f2dc3ef3db70e5adb5d8a3521e9ab4345973a2c788dd005022ba0347208afd8.
This preserves the separately recorded owner UI/native200responses in13-UAT;
it does not rewrite automated capture flags or invent another human response.

## Prior attempts, environment and scope

Earlier failed campaigns remain failed. Reviewed repairs and their RED/GREEN
evidence are retained in13-REVIEW,13-17-FIXTURE-REVIEW and13-SECURITY. The prior
complete535a5b7security pass and failed image-guard recovery are historical;
subsequent four-stage diagnostics do not form this final seven-stage result.

Campaign5 at this same source failed because the private supervisor PATH omitted
/usr/sbin and could not find existing nginx. That was an avoidable orchestration
error, not an application fix or missing-package waiver. Its failed log/coverage/
cleanup receipt remains at /tmp/birja-phase13-plan17-campaign5-20261118-9527e35/.
Campaign6 corrected only private orchestration, validated all existing executable
bindings, and ran actual nginx -t plus recovery/runtime/restic provenance checks
under the exact corrected child environment before the complete rerun.
executable-preflight.json SHA256:
978be4397b23128217371b36b60507c6c1e692132a807f58192aa99581b6c7f4.
No new tools were installed; jq is neither installed nor referenced as a required
command by this source, and recovery explicitly has no jq dependency.

The successful run uses stripped synthetic settings, fake prices, console email,
existing Node24/uv/pinned images and owned disposable resources. All21fixed
container/network/volume checks across seven test projects are empty after both
commands; generated image reports were preserved outside the repository.
There was no provider operation, private .env access, production change, push,
merge or deployment. This is local qualification, not a hosted CI result.
Phase7live requirements, public deletion/freeze Phase14 and final lifecycle
acceptance Phase15 remain outside this proof's completion claim. Global Phase13
completion remains the parent's independent verification decision.
