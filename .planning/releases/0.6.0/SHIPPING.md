# Software 0.6.0 shipping receipt

Status: PR36 open; required CI not yet green. No merge, tag, publication or
production write/restart/deployment has occurred. Planning v1.2 audit/archive
remains separate from this owner-authorized software release.

## Authorization and scope

On2026-11-22 the owner authorized PR/full CI, merge/release and production
readiness/deployment. They confirmed Phase7 manual acceptance and applicable
provider display/retention/product-access/limit prerequisites, then explicitly
selected “Deploy portfolios; finish stock activation separately.”

Phase7 OWNER-CLOSURE and07-14SUMMARY preserve attested versus measured evidence.
Missing live stock-status transport remains in DEFERRED; runtime stock gates
remain enforced. No new provider calls or activation are authorized here.
Unrelated untracked.claude work remains untouched.

## PR and CI history

PR36: https://github.com/YokAI-open/Birja/pull/36
Target develop; feature/milestone-v1.2.

- Run45015090662 at8fdff48: stale offline recovery contracts failed; canceled.
- Commit6a6c3ce updates only two test contracts for current phase-aware runner
  output and controlled preflight tools. All110 local CI contracts pass.
- Run45015644389 at6a6c3ce: image passed; frontend had one test callback race;
  superseded/canceled. Commitd6d126d preserves immediate privacy assertion and
  waits for the mocked owner-transition request. All21 affected unit tests and
  formatting pass.
- Run45016186368 atd6d126d: frontend all1330 and image passed. Browser report
  shows92passes,1existing skip and1capture-setup429. Backend reached38% before
  the15-minute job limit canceled it; its partial output has three failures
  and is not a test pass. Operations still running at this receipt's creation.

## Focused repairs under verification

- Browser setup honors the real Retry-After once, with the same idempotency key;
  app quotas and dedicated rate tests stay unchanged. All six affected actual
  isolated capture journeys pass in133.7seconds, with owned cleanup complete.
- Backend checkout fetches full history for qualified0017/0020 source comparisons.
  A shallow checkout omitted those commits.
- Backend job budget120minutes reflects the expanded3691-test suite; the saved
  local passing run took5167.93seconds. Pytest stops at its first failure so a
  subsequent failure has a complete traceback promptly. All existing tests,
  overall80% and critical100% gates remain.
- Two split-clock cases inherited a fixed2026-11-20 payable date while deriving
  ex/record dates from current DB time. They then tested an uncertain event.
  The synthetic payable date now follows its cutoff, and an explicit supported
  classification assertion proves the intended temporal path is exercised.
  No app, SQL, schema, dependency version or recovery payload changes.

Fresh110 workflow-contract tests pass after workflow corrections. All11 cases
in the full affected clock module plus the historical-literal selection pass
in113.56seconds. Ruff lint/format, frontend types/format and diff checks pass.
The failed uncorrected reproduction is retained separately. Final exact
head/run must replace this pending disposition before merge.

Review: separate inline source/diff pass confirms unchanged application gates,
SQL, source identities, dependency graph, original retry keys and strict coverage.
This is not an independent-agent review. No external review command is configured.

## Production read-only preflight

/srv/birja, birja-prod on DE189274 remains source46d24c8/schema0008. All four
services are healthy. Database about8.6MB, free disk about22GB. Live PostgreSQL
18.6 and target pinned18.7 use glibc2.44. Existing selected phase06 PG/Redis
volumes are live and must never be treated as empty. Existing TLS certificate
expires2027-11-10; existing credentials and CA are retained.

The2026-11-22T03:12:41Z nightly backup succeeded. Its snapshot differs from the
last exact restore proof, so a fresh matching backup/restore is required.
Portable backup-recovery-config.json still names an older source; refresh it
from actual protected configuration before the new recovery proof.

Current v4 recovery archivebbbec1af156b594f5093ecef8badf918f8b0a7e039dfdb3e486fb8b58823f47a
verifies; all51 bundled current source payloads match this candidate. Prior
immutable archives/receipts stay preserved. No production tool/config change
has yet been made.

## Prepared next steps

Temporary reviewed release package: /tmp/birja-release-0.6.0-prepared/.
It contains metadata.patch, metadata-review.json, draft release notes and a
read-only original-financial-preservation checker. Parsed third-party Python
and Node graphs are identical; only first-party0.5.0→0.6.0 metadata changes.
Audit-policy hashes follow those exact metadata bytes, while issue35 advisory,
scope and2026-12-17UTC expiry remain unchanged.

Rollout draft: /tmp/birja-0.6.0-rollout-draft.md. Finish required CI, approved
merge/release git-flow, exact tested-source retained tooling, fresh encrypted
B2 backup and isolated restore, guarded0008→0023 migration, original-finance
preservation and origin/public smoke, then post-rollout recovery and custody
export. No old-app downgrade on0023 or restore over newer activity.
