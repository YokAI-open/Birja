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
  No application service, schema, dependency version or recovery payload changes.

Fresh110 workflow-contract tests pass after workflow corrections. All11 cases
in the full affected clock module plus the historical-literal selection pass
in113.56seconds. Ruff lint/format, frontend types/format and diff checks pass.
The failed uncorrected reproduction is retained separately. Final exact
head/run must replace this pending disposition before merge.

Review: separate inline source/diff pass confirms unchanged application gates,
migration SQL, source identities, dependency graph, original retry keys and strict coverage.
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

## Rollout smoke compatibility correction

Readiness review found the retained crypto freshness query counted newly seeded
active stock symbols as crypto, despite deferred stock activation. It now filters
crypto explicitly, with a JSON-field fallback for genuine0008 rows that have no
asset_class column. This preserves crypto's priced-count/age requirements; stock
activation remains separate. No data, grant, migration or runtime service changes.

Four real isolated PostgreSQL cases pass:retained0008-shaped/mixed rows, fully
priced/missing crypto. An old stock mark and an unpriced stock do not affect
crypto; missing crypto still reduces the priced count. All18 existing offline
smoke port/auth cases, Bash syntax, Ruff and diff checks pass. Test stack cleanup
completed. These are read-only smoke semantics, not production acceptance.

Run45018036764 at77f1a57 began after the earlier four repair commits; frontend
passed, remaining checks were still running before this correction was published.
Its eventual canceled/failed outcome must not be called a fullCI pass.

## Related fixed-date fixture closure

Static caller review found the same expired payable-date inheritance in two
remaining portfolio split helpers. The active-sibling case reproduced the
failure locally (no supported split applied); this was not a production bug.
Their synthetic payable dates now follow their actual database clock, preserving
all financial assertions and deliberate uncertain/reverse cases. All14 affected
split and legacy-journal reload cases pass in114.21seconds; Ruff/diff checks
pass and the owned test stack is removed. App/SQL/recovery payloads are unchanged.

Atf47889e, run45018262873 has successful frontend, image and full browser jobs.
Actual browser-all exit0 took672.0seconds and owned cleanup passed. Backend and
operations were still running when these final test-only fixes were prepared;
no whole-CI pass is claimed. These component receipts remain valid for their
unchanged inputs, while the final head still requires all six green checks.

## Measured production transition prerequisite

The old installed configure-db --production --inspect passes for live0008.
Running the candidate inspector directly safely refuses existing old image/HBA
bindings. Read-only role query also confirms birja_action_operator is absent.
No grants, database rows, services or installed tools were changed.

The concrete rollout draft now uses existing guarded --start-selected-datastores
after a fresh exact new-tool0008 backup/restore, keeping the same selected
volumes. This moves PG18.6→18.7 and the immutable HBA binding, then the reviewed
populated-role bootstrap preprovisions the fixed NOLOGIN operator role using
existing credentials. Fresh final0008 backup/restore follows that security
transition before migration; post-rollout0023 recovery follows deployment.
No new role password, CA, manual grant repair, volume copy or downgrade is
introduced. Current source release stays actual old live46d24c8 until rollout
succeeds. Exact final source/manifest binding and all six CI checks remain pending.

## Query-replacement test scheduling repair

Run45019889211 atd7e3f66 exposed one frontend unit race:overview replacement
could occur before the first deferred request had started, so resolving it
legitimately answered the new query. The test now waits for the original
request, asserts its cache identity, proves a second request/new cache entry,
then delivers the old reply and still requires no published data. Application
response-handling logic is unchanged.

Both affected overview/owner-boundary files pass56cases. A fresh full frontend
qualification passes all1330tests/60files in31.89seconds, with96.46%statements
and94.01%branches; formatting and diff checks pass. The prior failed hosted
run remains failed/superseded. Required CI must pass at the new exact head.

## Parallel draft release preparation

Feature candidate92a8956 is under run45020330811; latest observed frontend,
image and full browser jobs pass, with backend/ops still running. Its full
1330-test frontend result is also locally qualified.

Release worktree was created from freshly pulled develop26d2011 and locally
merged reviewed feature92a8956 with--no-ff. This changes no protected branch.
Preparing a draft main PR now lets both required full CI graphs execute in
parallel on separate hosted runners. Main merge remains held until featurePR36
is green and merged, and the release head independently passes all six checks.

Version0.6.0 changes only root project metadata. METADATA-REVIEW.json proves
parsed Python/Node third-party graphs identical; prospective uv lock --check
--offline passes83packages. Exact Node audit bindings follow those changed
metadata bytes; advisory scope and expiry remain unchanged. UI/runtime/migration
programs remain identical to the reviewed feature. No new human UI gate.

Staged independent release asset birja-recovery-0.6.0.tar is exactly244357120bytes,
SHA256bbbec1af156b594f5093ecef8badf918f8b0a7e039dfdb3e486fb8b58823f47a,
and all51 current payloads match. It contains public recovery tooling and
source profiles, with configuration/credentials separately in encrypted custody.
Publish/verify that asset with the software release before production transition
to provide an off-server exact independent recovery toolchain.

Release-preparation review re-parsed actual candidate TOML/JSON against feature
92a8956 and proves every third-party entry identical. Policy JS differs only
in its two file-hash constants. Actual uv lock --check --offline passes83
packages; direct audit contract execution passes all12cases; Prettier/diff
checks pass. All51 archive payloads still match, and application, migration,
frontend runtime/E2E and deployment/smoke sources are byte-identical to feature.
This is a separate inline review pass, not an independent-agent review.

## Retain the exact fully tested distribution artifact

Feature run45020330811 at92a8956 completed its entire serial recovery job
successfully in39m27s. Its actual same_archive_final_ci=true archive is
41839607250c74d83ce80fdbf2d78ebefd50d8acb763c734b2ba90b26dc6de62.
The workflow did not upload that generated archive, so it cannot be retrieved
from the completed ephemeral runner. Backend qualification remains in progress.

Release workflow collection is therefore added after successful whole recovery:
copy only its fixed canonical archive and SHA to a runner-owned private staging
directory, verify the copied bytes, then upload exactly those two tooling files.
Missing/modified data fails the collection and ops job. All seven stages, image/
coverage gates and the45-minute ops bound remain unchanged. No production data
or configuration is collected. Current feature qualification is untouched.

Earlier localbbbe archive remains the separately qualified Phase15current proof;
it must not be substituted for the final full-CI distribution archive. The
previous staged copy is preserved under the temporary local-qualified folder.
Publish/install only the subsequently downloaded and verified successful release
CI artifact. The release notes defer its exact checksum to the actual sidecar
and receipt, avoiding a guessed identity or another metadata-only CI restart.

ROLLOUT-DRAFT.md records the measured existing image/role prerequisites and
guarded sequence. Exact final main/manifest/CI artifact identities must be bound
after the release gates pass; no production write is claimed.

Collector verification passes all111 CI contracts in27.55seconds, including
matching/modified/missing archive behavior. A first worktree-local contract run
failed because its mocked preexisting-stack branch called a real source snapshot
that deliberately expects an ordinary.git directory. That branch now uses the
same fixed source double as its existing failure matrix, so it actually tests
the intended owned-stack refusal. Runtime source guards remain unchanged and
independently covered. The failed first run remains recorded, not relabeled.
Separate inline diff review confirms unchanged full recovery invocation, exact
two-file upload scope, copied-byte verification and strict failure propagation.
