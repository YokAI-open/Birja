---
phase: 06-deploy
plan: "11"
status: main-merged-tag-release-backmerge-rollout-pending
prepared: 2026-11-09T08:01:06Z
implementation_head: 945791115c0bd88fd0cf62835aca3e03c395659f
base: 5ebf62b33b190aaf04a48b107a222e906fbf4c99
nightly_observation: owner-deferred-pending
publication_authorized: true
prior_publication_authorized_head: 77dcd44e852a079d4541c78f724717a0dd13afba
ci_head: 945791115c0bd88fd0cf62835aca3e03c395659f
ci_run: 42787743632
ci_status: success-all-six-browser-health-retry-retained
---

## Main merge completed —2026-11-10

Owner explicitly selected “Approve main merge” for PR27 head
945791115c0bd88fd0cf62835aca3e03c395659f. Before merging, GitHub readback
confirmed exact head, main base, OPEN/MERGEABLE/CLEAN and all six checks SUCCESS.
`gh pr merge --merge --match-head-commit` completed successfully at
2026-11-10T09:24:42Z. PR27 is MERGED; resulting main commit is
46d24c8591de2207cf219429aac0768962bed4c3.
GitHub commit readback verified both parents: previous main0107706617b8bbf9c1a069f3e3ccc9c53b9ab2f7
and approved release945791115c0bd88fd0cf62835aca3e03c395659f.

Only main merge was authorized/performed. No tag, GitHub release, back-merge,
production inspection, restart or deployment occurred. Keep the release branch
and local planning closeout9f4bf5f plus this record for the next approved
integration. Phase remains12/15;09/12/13 and DEPL-01/02 remain incomplete.
Next publication candidate: v0.4.0 at the resulting main SHA, using prepared
release notes; requires separate explicit tag/release authorization. Back-merge
push/PR and its eventual green-CI merge require their own scope decisions.
Production still needs measured preflight, final retained MANIFEST, fresh
recovery proof and an approved maintenance window. Nightly observation remains
owner-deferred.

## Accepted current release checkpoint —2026-11-10

Published945791115c0bd88fd0cf62835aca3e03c395659f / actual42787743632 has
all six required jobs green. Plan11 SUMMARY records verified code/ops, explicit
authorizations and retained browser health retry. PR27 OPEN/MERGEABLE/CLEAN;
main base0107706617b8bbf9c1a069f3e3ccc9c53b9ab2f7. No merge performed.

Current CI scope is fulfilled. Plan12 requires separate explicit main merge
approval and Create-a-merge-commit after rechecking exact head and green CI.
Tag/GitHub release, back-merge and production rollout remain separate.
Local planning closeout can be carried through next approved integration;
keep CI-proven published9457911 unchanged for the merge decision.
No09SUMMARY/DEPL completion or calendar proof is inferred. Production preflight
values/window and resulting main SHA/MANIFEST remain future scoped inputs.

## Bounded CI completion —2026-11-10

Owner approved38eb25c plus reviewed/tested CI/test/planning follow-ups until CI
passes. Actual42785059635 confirmed the Git fix and four other green jobs,
but operations failed missing Bake read consent for the retained Dockerfile.
Reviewed d7f0cf5 pins CI-only Compose5.7.0 with exact version assertion, no
wildcard/bypass.9contracts and full supplied-archive local proof257.676s pass.
Publish under existing authority and require new actual CI. No production tool
change, main merge/tag/deployment,11SUMMARY or DEPL advancement yet.

## Approved publication and actual CI —2026-11-10

Owner approved all18 commits through77dcd44e852a079d4541c78f724717a0dd13afba.
Nonforce push and PR27 update succeeded; remote PR head is exactly77dcd44.
Run42782054013 completed with backend/frontend/image/e2e SUCCESS and ops /
ci-pass FAILURE. Actual backend616/critical100%, frontend264, browser10pass /
1expectedCSPskip/no retry; all5raw image reports hashverify with0HIGH/CRITICAL.

Ops passed transition34.841s, recovery58.758s, roles22.158s/65denials,
TLS21.576s and prior actual-old rollback94.821s. New selected-cutover fixture
failed at the real retained first-start launcher: private app “is not a git
checkout”. Owned fixture cleanup passed. No successful current-head CI or
Plan11 completion is inferred.

RED7d3f8a4 / GREENc343f6b isolates Git system configuration only in the
synthetic generated launcher, with a regression reproducing denied host config
under Landlock. Real Git rev-parse and local config pass afterward, while a
missing .git still fails. Independent review clean; affected full supplied-
archive proof passed246.010s including deployment, rollback, three restores
and unchanged originals/cleanup. No production/runtime/image/CORE changes.
Actual runner confirmation needs a separately approved correction push;77dcd44
approval did not cover later commits. No11SUMMARY, merge/tag or deployment.

## Local rollout correction —2026-11-10

Owner approved local correction before merge. Protected persistent candidate
routing, TLS-first startup and actual running-identity guards are implemented;
independent source review has no open findings. Source/fixtureb6b717c includes
strict observed Redis manifest formats, final-record file checks, nonsecret
HBA readability and pinned containerd platform identity.

Real supplied-archive run12 passed254.099s with current0008 deployment, actual
v0.3.1 rollback, Redis persistence/authentication, unchanged originals and three
same-archive backup/exact restore stages. Final committed serial compatibility
passed, including full retained cutover239.459s; results recorded in
06-12-LOCAL-FIX-EVIDENCE. The revised proposal prepares all
bound material before fresh first-start recovery proof; live preflight values
remain unmeasured and require separate approval.

PR27 still publishes16623a8. Its existing CI is historical for that head only.
The local candidate requires a new push decision and new actual CI before
main merge. No main merge/tag/back-merge/deploy authority is implied; no
11SUMMARY/DEPL advancement until current candidate requirements pass.

## Published release CI and rollout readiness decision —2026-11-09

Owner explicitly selected “Push and open main PR” for16623a8638407eeab27c2879f0a9396764a68e89.
Nonforce release-0.4.0 push and PR27 into main succeeded:
https://github.com/YokAI-open/Birja/pull/27.
Actual release CI42622430042 completedSUCCESS at that exacthead; all six
backend/frontend/image/e2e/ops/ci-pass checks green. No mainmerge/tag/release/
backmerge/deployment authority was granted or exercised.

Backend616/99.80%overall/100%critical; frontend264. Actual trading/portfolio/
history flows passed. Browserattempt1:9passed,1health-screen first-attempt
timeout then successonretry,1expectedproductionCSPskip. Targeted same-head
browser+aggregate rerunattempt2:10passed,1expectedskip,0retries,aggregatepass.
Initial flaky result retained, not erased or called fixed by a clean rerun.
Five raw image reports hashverify and each0HIGH/CRITICAL; original strictgate
unchanged. Ops populatedtransition34.239s/recovery59.159s/roles21.387s+65denials/
TLS21.221s/actualoldrollback89.555s pass; mandatorycleanup succeeded.

Plan11releaseCI requirement is proven. Subsequent source-only rolloutreadiness
review found CR-01: productionCompose/deploy/rollback lack protected persistent
selection of new datastore clone volumes while preserving originals. WR-01:
candidate startup requires TLS/HBA material before startup; proposal revised
to make this explicit, actual bootstrap/material state still unmeasured.
Role/backup exec helpers need verified solecandidate identity/mountmapping,
not necessarily separatevolume selectors. See06-12-READINESS-REVIEW and revised
ROLLOUT-PROPOSAL. No highfinding waived, no executableliveproposal is ready.

Next scope decision: prepare/test/independently review a protected clonebinding
and concrete TLS startup procedure locally before changing the release, or
consider publishing currentrelease without any deployment. Recommend fixfirst.
Any changedreleasehead needs a new concrete reviewedpushchoice and ownCI;
current166approval does not authorize unreviewedsourcepublication.
Keep PR27open/unmerged; do not request productionapproval against placeholders.
11SUMMARY remains pending readiness disposition;phase11/15,65/69=94%.
09nightlyproof still owner-deferred; no09SUMMARY/DEPLadvance.

## Local release0.4.0 ready for publication choice —2026-11-09

Branch release-0.4.0 was created from updateddevelop5ebf62b after approvedPR26
merge. Carries final featurecloseout0e0a6eb and reviewed versioncommit
524080f5414b71de336239c008c3ddcecaefd3dc. BothPhase5/6merge ancestors verified.
Four files/five versionvalues0.3.1->0.4.0 only; parsed complete metadata
normalization and74backend/638frontend inventory hashes prove all dependency
records/artifacts unchanged. No source/image/recovery/runtime change.

Local7CI/25backup/4restore-safety tests, uvlockedofflinesync/check, frontend
lint/types/metadataformat/build passed. Independent06-11-LOCAL-REVIEW0blockers/
0warnings independently verified full metadata equality, ancestry and lock.
No repeated fullapp/DB/browser/image runs; actualrelease-head CI must stillrun.
Fresh featureCI42618704350 remains evidence only for unchangedimplementation.

Last recorded installed recovery archive is d5fe2059...; actualB2backup at
07:43:40Z and exactisolatedrestore at07:44:22Z on09November passed. Freshness
has not been rechecked in this local release task and must be rechecked before
any approved rollout. First genuine nightly observation remainsowner-deferred.
No provider/private/production action or archive rebuild occurred.

Task11-01 complete;11-02 awaits explicit publication choice. Resolve exact
publicationHEAD after this planningcommit; show three local releasecommits
(closeout,versions,evidence), target origin/release-0.4.0 and mainPR. Prepared
PRbody/title are ignored/private. Owner approval sofar covers localprep only,
not releasepush/mainPR/mainmerge/tag/backmerge/deployment. No11SUMMARY yet.

## Current green CI and integration decision —2026-11-09

PR26 https://github.com/YokAI-open/Birja/pull/26 remains OPEN/MERGEABLE into
develop at exact a7d5dcb01d40a916c9cbf9d6ff51525c70c50833.
Actual run42618704350 completedSUCCESS:
https://github.com/YokAI-open/Birja/actions/runs/42618704350.
All six required jobs backend/frontend/image/e2e/ops/ci-pass passed; no required
job skipped. Job logs and raw public reports are preserved in ignored
pr-preparation/passed-ci-* and final-image-reports.

Backend616pass/99.80% overall/100% critical; frontend264pass. Browser10pass,
one expected csp.spec production-only skip because E2E_PROD_URL is absent.
Actual trade.spec buy/sell and full buy->portfolio->history->whole-sell pass,
including375/768/1024/1440 widths. Five raw runtime/builder/Node/Postgres/Redis
reports hash-match successful status records and each contain0HIGH/CRITICAL.
No ignores/waivers or severity changes.

Ops proves pinned29.2.1/clean-root containerd export through unchanged strict
verification. Populated transition34.051s, encrypted recovery62.533s, roles
24.112s/65permission denials, TLS23.141s and actualold rollback96.232s pass.
Old checkout/credentials/Compose/revision unchanged; missing/failed/stale
evidence and bad CA/hostname/plaintext reject; immutable routing/lock and0008
preservation pass. Mandatory cleanup succeeded. No VDS daemon/recovery change.

06-10-02 complete. Next06-10-03 requires explicit Create-a-merge-commit into
develop and separately selects release preparation/version. Suggested0.4.0
is a proposal only; not selected. No merge/release/deploy authority inferred.
Production remains reportedv0.3.1. Exact installed recovery d5fe2059... and
actualB2backup/restore remain dated09November. First genuine nightly observation
is owner-deferred;09/DEPL-02 pending. Phase10/15; no09/10SUMMARY/completion.

This supersedes older publication/CI-pending entries. Final local tracking
edits stay unpushed so greenPRhead remains exacta7d5dcb. Preserve/carry edits
through any approved integration/release; never discard or publish silently.


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


## Reviewed Docker runner capability correction —2026-11-09

Actual1bbaa69/run42616168904 passed backend/frontend/image/e2e and every
offline ops check including nginx. Populated image-transition passed30.200s.
Recovery package preparation then failed its pinned Docker image inspection.
Exact runner20261101.360 has Docker28.0.4/API1.48; image inspect --platform
requires API1.49+. Local29.2.1 supports the existing command.

RED8d3466f/GREENf5ad5cc pins matching29.2.1 CE/client packages from Docker's
official signed apt repo in the disposable ops runner, before fixture work.
The clean-root /usr/bin/docker/default socket preflight pulls the unchanged
pinned image and verifies platform inspection. Six CI contracts, focused Ruff/
diff and read-only old-API rejection/new-API command+identity-guard proof pass.
Independent DOCKER-CI-REVIEW reports0 blockers/0 warnings. VDS Docker/service,
recovery source, image pins and installed archive remain unchanged.

Publish under existing bounded CI completion authority; actual new-head
hosted setup/required CI remain pending. Merge/deployment and deferred nightly
proof retain their distinct gates. Phase10/15 unchanged.


## Reviewed CI image-store alignment —2026-11-09

Actual58c4258/run42617492782 passed Docker29.2.1 setup/platform inspection,
offline ops, app/browser/image jobs and populated transition33.549s.
Recovery packaging then rejected classic archive membership at unchanged
verify_saved_image line280. Runner inspection exposed the config identity;
Docker documents that upgrades retain the classic store. Raw failed archive
members are unavailable; do not claim their exact difference was captured.

REDb44f381/GREEN57974aa preserves existing daemon JSON/features while enabling
containerd only on the disposable ops runner, before restart/pull/build. New
test-only preflight checks the driver, saves the unchanged pinned public PG
image, authenticates registry provenance and invokes the original strict
archive verifier with anonymous temporary-file cleanup and bounded save.
Seven CI contracts, Ruff/format/diff and actual local containerd export+
unchanged verifier4.929s pass. Independent STORE-CI-REVIEW reports0/0.

Publish under existing bounded CI completion authority. Actual runner replay
remains pending; no VDS daemon change, recovery code/image pin/installed bundle
change or new production action. Merge/deployment and deferred nightly proof
remain separate; phase10/15 unchanged.


## Approved feature integration and release preparation —2026-11-09

Owner selected “Merge and prepare0.4.0” for exact green PR26/a7d5dcb.
All six exact-head checks reverified before gh pr merge --merge
--match-head-commit. PR26 is now MERGED into develop as 5ebf62b33b190aaf04a48b107a222e906fbf4c99,
at 2026-11-09T12:53:43Z. Explicit permission covers this feature integration and
local release-0.4.0 preparation only. Release push/main PR, merge/tag/backmerge
and production rollout remain separate unapproved gates.

Preserve local final CI records/Plan10closeout through updateddevelop into
releasebranch. Plan10complete; Plan11task01 prepares four version metadata
files using locked tools, no dependency or application changes. Keep actual
nightlyproof deferred and09/DEPL-02 pending.


## Local rollout correction authorized —2026-11-09

Owner selected “Prepare local rollout fix”. Prepare a protected persistent
clone-volume binding and concrete TLS-before-startup procedure, with meaningful
synthetic cutover/rollback/negative tests and independent review. This permits
local source/test/documentation work on release-0.4.0; no updated releasepush,
mainmerge/tag/backmerge, VDS/private/provider operation, archive installation
or production service/volume change. Existing16623a8 PR27 stays unchanged.
Retain the accepted image/security/recovery gates and installed independent
recovery payload. No new phase plans/counter reset; scoped closure of the
confirmed readiness findings is part of pending11-03/12preparation.
