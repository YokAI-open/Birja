---
phase: 06-deploy
plan: "10"
status: root-fixture-correction-reviewed-serial-integration-passed-publication-pending
prepared: 2026-11-09T08:01:06Z
implementation_head: 9e0d19e94a3a50ed4c055fed3d3b696c0d806dbb
base: 8a76a68cf54f46fb0267c9d97f0da91d91b117e1
nightly_observation: owner-deferred-pending
publication_authorized: true
---

# Feature review and publication checkpoint

## Owner sequencing update —2026-11-09

Owner explicitly said “let's not wait for it, will check it later”. Proceed
with Plan10 review/publication preparation while the first genuine scheduled
backup observation remains deferred. The real encrypted backup, exact isolated
restore/private invariants and installed timer are already proven. Keep09 and
DEPL-02 pending; do not fabricate nightly success or create a completed09SUMMARY.
This instruction changes sequencing only. Actual CI, publication approval,
merge/release/deployment approval, fresh recovery gates before rollout, and
final friend/calendar acceptance are retained. Timer scheduling stays unchanged.
This supersedes the requirement to wait for the first night before preparing10.

## Concrete review target

- Repository: https://github.com/YokAI-open/Birja
- Branch: feature/phase-06-deploy, target develop; no upstream configured.
- Implementation head: `9e0d19e94a3a50ed4c055fed3d3b696c0d806dbb`; base `8a76a68cf54f46fb0267c9d97f0da91d91b117e1`.
-111local commits before this preparation commit;107changed paths,48outside
  planning. Full exact commit list is privately retained at ignored
  .local/phase-06-handoff/pr-preparation/commits.txt.
- Resolve the publication HEAD after this preparation commit and display that
  exact SHA/commit count for the owner's decision. A later documentation
  decision commit does not authorize a different unreviewed source payload.
- Read-only remote preflight confirms develop at the exact base above, main at
 0107706617b8bbf9c1a069f3e3ccc9c53b9ab2f7; feature branch is not published
  and no matching open develop PR exists.
- PR title: Add encrypted recovery and hardened deployment workflow.
- Complete PR body prepared at ignored
  .local/phase-06-handoff/pr-preparation/pr-body.md. Use structured body/file;
  preserve actual newlines. No remote publication occurred.

## Scope and implementation result

Consistent PG18 exported-snapshot dump/private invariant manifest; encrypted
restic/B2 recovery with fresh actual account/version/unfinished inventory,
headroom and bounded local transfers; verified replacement before scoped
latest-only rotation. Immutable recovery installation, fixed isolated clone,
nightly units, honest status and source/config/tool-bound recovery gates.
Least-privilege runtime/migrator roles and verified DB TLS across all engines;
retained deploy/actual-old rollback gates. Pinned safer images and strict image/
operational CI. No new product feature or UI redesign.

## Validation and exact limitations

- Current06-10check:4test-ci-ops tests passed0.002s on9November.
- Last affected source fix:18prerequisite/25backup/4safety tests, lint/format and
  focused independent review0BLOCKER/0WARNING; source0e47c50.
- Latest exactd5fe2059 recovery archive: recovery66.973s/roles30.711s/
  TLS51.936s/actualoldrollback104.093s and copied verification pass; fixed
  synthetic project resources0. Both later source fixes have independent review.
- Full application gates dated8November:616backend99.80%overall/100%critical,
  264frontend, browser10pass/1expectedproduction-onlyCSPskip, audits/builds,
  five raw image scans0HIGH/0CRITICAL. Do not call these fresh PR-head CI.
- Real9November backup11.817s/restore12.211s passed with private invariants,
  exact source/config/tool binding and cleanup. Actual productionv0.3.1 source
  and all4original running IDs unchanged. Timer enabled, first actual trigger
  scheduled10November03:11:32UTC; genuine calendar observation deferred/pending.
- Full branch whitespace check exposed generated planning-document whitespace;
  trailing blanks/EOF spacing were normalized without semantic/history changes.
  No code/image retest needed for these documentation-only edits.
- Untracked.claude/ preserved. No secrets, private configuration, credential files,
  ignored recovery packets or production rows are staged. No remote CI result,
  integration, release, deployment or final DEPL acceptance is claimed.

## Remaining publication gate

CLAUDE.md Pushing says “Never push without asking”. Present the exact prepared
HEAD/branch/commit count plus results, then owner chooses push+developPR,
push-only or notyet. The nightly deferral is not publication authorization.
After approved push, require actual exact-head backend/frontend/image/e2e/ops/
ci-pass green. If push-only, separate PR approval remains required. Merge/version
and production rollout retain their own concrete checkpoints; never use prior
phase approvals. Plan10 has noSUMMARY and Phase6 stays10/15 until its actual
CI/integration tasks complete. Plan09/DEPL-02 remain pending until real calendar
proof is checked later; no09SUMMARY created.


## Approved publication and current CI —2026-11-09

Owner chose “Push and open PR” for exactc085a766a056b017fce1d9d6e2f737541867ae79,
112local commits. Push--set-upstream origin feature/phase-06-deploy withoutforce
exited0. Prepared PR creation exited0; PR26 targetsdevelop:
https://github.com/YokAI-open/Birja/pull/26.
Read-back PR head matches the approved SHA. Actual pull_request CI42583320799
created2026-11-09T08:04:16Z is running:
https://github.com/YokAI-open/Birja/actions/runs/42583320799.
Backend/frontend/image/e2e/ops are in progress; no green result claimed yet.
Publication evidence and exact live job observations are private at ignored
pr-preparation/publication.json, ci-initial.json and ci-current.json.
These local checkpoint edits are not included in the already approved/pushed
head. No new source push, merge, release or deployment is authorized. The first
scheduled backup observation remains deferred by owner.


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


## Corrective publication approved and executed —2026-11-09

Owner chose “Push fixes and check CI” for exact57b8774cc93f26000f3e691421c9fefd0020e375,
three local commits. Nonforce feature push and prepared PR26 description refresh
both exited0. Read-back PR head equals that approved SHA. New actual pull_request
CI42585485295 was created2026-11-09T08:22:34Z:
https://github.com/YokAI-open/Birja/actions/runs/42585485295.
Backend/frontend already pass; image/browser/ops remain in progress at this
observation. No passing aggregate, merge/version/release/deploy authority yet.
Initial CI42583320799 failures remain retained; no claim they passed. Actual
corrective-head result must be inspected. Nightly proof remains owner-deferred.


## Second CI result and reviewed root-fixture correction —2026-11-09

Approved57b8774 push/PR-description refresh succeeded. Actual CI42585485295
completedFAILURE: image/backend/frontend/e2e PASS, ops/ci-pass FAIL. The scanner
cache correction is proven on GitHub; no vulnerability gate exception needed.
Ops reached18prerequisites and failed two actual TLS lock caller tests because
this real provisioner correctly requires root. Later syntheticTLS also chowns
private server keys0:70. Keep these production guards; explicitly use sudo only
for privileged synthetic prerequisites and serial image/recovery/role/TLS/old
rollback CI fixtures. Hostuv/dbconfig checks stay in the prepared runner env.

REDb1dd6dd/GREEN0637b48 implements that bounded5file workflow/test-only change.
Fixture source reads use -c safe.directory=<canonical ROOT> -C ROOT; no wildcard,
global config or shared checkout ownership/mode changes. Actual private repo
proof reproduces root/runner ownership rejection and verifies exact exception
plus unrelatedrepo denial. Actual TLS nonroot denial/rootcreatecheck/key0:70
mode0640 passes.18prereq/5CI tests pass; independent ROOT-CI-REVIEW has0BLOCKER/
0WARNING and reran them. No installed recovery/runtime/image/provider/timer
change. One serial local root integration is in progress; actual new-head CI
and follow-up publication approval remain pending. Firstnight proof deferred.


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


## Bounded CI completion authorization —2026-11-09

Owner selected “Publish and finish CI” for exact995b46426194a4773f24099f6bb17a4048bc34c7
and3reviewed commits. Nonforce push and prepared PR26description refresh exited0.
Standing authorization now covers further independently reviewed/tested fixes
ONLY in feature/phase-06-deploy's .github/workflows/ci.yml, deploy/tests/ and
planning records until required CI succeeds. Preserve existing security/test
checks; no weakening/skipping tests or severity policy. Do not re-ask for pushes
inside this explicit scope. Application/runtime/image/recovery/production code,
merge/release/deployment and force-push are excluded and retain separate gates.
Current actual new-head run is being observed; no green aggregate claim yet.
Nightly proof remains deferred; no plan/requirement completion inferred.

## Reviewed nginx CI privilege correction —2026-11-09

Actual995b464/run42588116337 completed failure: backend/frontend/image/e2e
passed; ops failed only at the final offline nginx check because nginx-t opens
/var/log/nginx/access.log. The existing script explicitly documents root and
uses a disposable config/certificate/prefix, with no install/reload/start.
RED49df53f/GREENeec70c5 changes only the CI invocation to sudo plus regression.
Five CI contracts, Ruff lint/format, scoped diff and actual root nginx check
with temporary cleanup pass. Independent NGINX-CI-REVIEW reports0/0.
Publish under existing bounded CI completion authorization; no new push
question. Required current-head CI remains pending; no merge/deploy authority.
Recorded 2026-11-09T12:20:10Z. Nightly proof remains deferred;10/15 plans unchanged.
