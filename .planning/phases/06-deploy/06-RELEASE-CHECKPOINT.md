---
phase: 06-deploy
plan: "10"
status: local-review-ready-awaiting-publication-choice
prepared: 2026-11-09T08:01:06Z
implementation_head: 9e0d19e94a3a50ed4c055fed3d3b696c0d806dbb
base: 8a76a68cf54f46fb0267c9d97f0da91d91b117e1
nightly_observation: owner-deferred-pending
publication_authorized: false
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
