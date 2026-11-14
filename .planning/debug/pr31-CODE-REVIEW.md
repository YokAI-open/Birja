---
phase: pr31-ci-failures
reviewed: 2026-11-14
depth: standard
files_reviewed: 7
files_reviewed_list:
  - deploy/tests/check-recovery-image.py
  - deploy/tests/test-image-contracts.py
  - deploy/tests/test-ci-ops.py
  - backend/uv.lock
  - deploy/tests/test-rollback-db-security.sh
  - .github/workflows/ci.yml
  - frontend/src/hooks/useEventHistory.test.tsx
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# PR31 affected code review

Independent reviewer: `/root/pr31_debug/code_review`. Implementation was read-only;
comparison base was `95912e0`. No Docker workload, installation or network action
was started during review.

## Narrative Findings (AI reviewer)

No actionable BLOCKER or WARNING found in the three reviewed files.

Traced the CI prerequisite through unchanged `verify_saved_image`,
`verify_image_provenance`, `bind_recovery_image`, `loaded_recovery_image` and
`image_inspect`. The helper verifies the exported archive before importing it,
rejects an existing alias with an incorrect config/platform identity before load
or bind, rewinds the same authenticated temporary file, then binds only the
unchanged fixed config/platform identities. Registry verification does not
substitute for the Compose alias. CI invokes this prerequisite before recovery
fixtures. Recovery CORE remains unchanged in the reviewed diff.

Independently recomputed the historical `e728855` package inventory with only
`opentelemetry-api` removed: SHA256
`8b0f58d9199b3dad2d27d9b398d33cc578b8a819307a3838dfc1cb32934991f1`.
It matches the revised all-other-entry assertion. The separately authenticated
complete OTEL1.45.2 record and the eight exact calendar additions retain separate
assertions; this is not an unrestricted inventory refresh. Mutation tests reject
unapproved OTEL version/artifact and unrelated dnspython/FastAPI changes.

## Independent checks and limits

- `python3 deploy/tests/test-image-contracts.py`: 15 passed, 0.595s.
- `python3 deploy/tests/test-ci-ops.py`: 16 passed, 0.483s.
- `git diff --check`: passed.
- Read `/tmp/pr31-ops-cold.log`: owned missing-alias startup reports `No such
  image`, followed by successful authenticated import/bind, actual PostgreSQL
  healthy startup, unchanged running-image guard and owned cleanup. This was
  reviewed evidence; the reviewer did not independently repeat Docker execution.

Reviewed file SHA256 values:

| File | SHA256 |
|---|---|
| deploy/tests/check-recovery-image.py | ecc9896db6b4b2f2141e6f686d25aff38fe0e2988ff019f70879c0a7894c5c9a |
| deploy/tests/test-image-contracts.py | 0824f0dcac34c71c2f836ea67b32f568fe62071ded80a02b82a81faf3eb9a787 |
| deploy/tests/test-ci-ops.py | 4f8239d8f1dc281521350e284a81924a170163062223eb8420eaf5b6162384bf |

The pending dnspython2.9.2 lock/install/exception is outside this reviewed byte
scope. A subsequent DNS exception or lock change requires a delta review.
This report does not claim hosted CI success or authorize publication.

## Approved DNS delta review

Independently reviewed `backend/uv.lock`, `deploy/tests/test-image-contracts.py`
and `deploy/tests/test-rollback-db-security.sh` against `0dd227e`, after the parent
relayed owner approval of the exact DNS patch. No actionable BLOCKER or WARNING
found. This section supersedes the earlier exclusion of the pending DNS delta;
the earlier three-file review remains attributed to its original hashes.

Parsed full before/after lock data independently: zero package additions or
removals; exactly the complete dnspython record changes. All top-level lock
metadata and every other package record remain equal. The lock matches the
approved SHA256 and its wheel matches the exact approved artifact SHA256
`af15f7d385a6ae2fb35a796fde2138004c8c42c7389090e2addc83e3b3340fd8`.

Independently computed the historical `e728855` inventory with only DNS and OTEL
removed: `e7415d7142069e6bca45afd4d37cd758a1d7c83ddd401a678b1b054c9b7b9509`.
This equals the revised image assertion; the eight calendar records remain
separately authenticated by their unchanged exact hash. Full DNS record hashes
independently match old `94eaf4580a2e9ddcebeb20c972343bd5ba85647b9d292423921c9652fc3eac21`
and new `4ad11523a6d2c2d0989a1eb5dd28d6edfa8c86170728ffc04ca47e1b173d3f79`.
Legacy compatibility authenticates both records, preserves exact OTEL/calendar
exceptions and compares all remaining records directly. No broad refresh or
version range was introduced.

Independent checks:

- Image contracts: 15 passed, 0.627s, including DNS version/artifact mutation
  rejection alongside existing OTEL and unrelated-artifact controls.
- `bash deploy/tests/test-rollback-db-security.sh --self-test-retained-install`:
  passed; actual positive full-record comparison and DNS/OTEL/calendar/unrelated
  mutation rejections run before isolated synthetic installer/checkout checks.
- Shell syntax and `git diff --check`: passed.
- An initial abbreviated `--self-test` invocation was rejected as ambiguous by
  argparse; it exercised no integration workload. The explicit command above
  succeeded. No Docker, installation or network action was performed by reviewer.

Reviewed DNS-delta file SHA256 values:

| File | SHA256 |
|---|---|
| backend/uv.lock | 3eded7f21be30568f5d4fae129f38a11e19484035f60f1477a3f9b2bf30fd2d4 |
| deploy/tests/test-image-contracts.py | b7bef3ec796930a939d92c4d36601a8ad5463a50e68fd5e5cc2ad7e3920f3a68 |
| deploy/tests/test-rollback-db-security.sh | 7d506a4973016c874fd706ff9e119902b68f6bfd9b00782ea1309924631893e3 |

This bounded source review does not replace application/audit/image execution
qualification and does not claim hosted CI success or publication authorization.

## Full-history checkout delta review

Independently reviewed `.github/workflows/ci.yml` and
`deploy/tests/test-ci-ops.py` against `ade062b`. No actionable BLOCKER or WARNING
found. The workflow delta adds only `fetch-depth: 0` to image-job checkout, before
the actual offline contracts. Build targets, immutable images, five-image scan,
failure handling, smoke checks, evidence upload, cleanup and required aggregate
are unchanged.

Traced the actual fixture import: `FixtureGitIsolation` imports selected-cutover,
which imports ops-fixtures; its historical seed calls `git archive v0.3.1` at
module load. Read `/tmp/pr31-shallow-repro.log`: one owned depth-one/no-tags clone
lacks that object and the unchanged actual fixture fails at this archive call;
fetching full history and tags into the same clone makes that fixture pass.
This is causal executable evidence beyond the new workflow text assertion. The
reviewer inspected the retained reproduction and independently executed the
actual fixture within the complete CI-contract suite, without repeating the clone.

Independent bounded checks:

- `python3 deploy/tests/test-ci-ops.py`: 16 passed, 0.477s, including actual
  generated-launcher isolation and depth-one/missing-history/late-checkout
  mutations.
- Loaded the new policy and supplied the original `ade062b` image-job text:
  rejected with `image fixture contracts require full Git history first`.
- `python3 deploy/tests/test-image-contracts.py`: 15 passed, 0.670s.
- `git diff --check`: passed.

Reviewed checkout-delta SHA256 values:

| File | SHA256 |
|---|---|
| .github/workflows/ci.yml | a02b0ce7fef757afd362bafad9e78b3d691513a32bd15f8c0ebedcf53294172a |
| deploy/tests/test-ci-ops.py | 978fea16619806d7effcb10a8319b83402e8621589497ce7b0a942c6d60c4cb2 |

No Docker/backend/image build or package installation was performed in this
review. Frontend test changes are outside this delta. Hosted success remains a
separate observation after publication.

## Frontend test synchronization delta review

Independently reviewed only `frontend/src/hooks/useEventHistory.test.tsx` against
`ade062b`, using the unchanged hook and installed query notification scheduler as
context. No actionable BLOCKER or WARNING found. Reviewed SHA256:
`0b908857522f6a82cfefafa4593e4a536ae3e25e2698faa7bb8eafa3684bd4a5`.

The added waits synchronize two observable states: the accepted two-page chain
before refresh, and React's refetch-error subscriber state after the failed
refresh. Installed TanStack `notifyManager` schedules/batches notifications via
`systemSetTimeoutZero`; resolving `refetch()` alone need not synchronously render
the subscriber. The test now separately requires the settled refetch result to
report an error, then awaits that same error in the hook. It retains the literal
whole-chain `["dividend:3", "dividend:2"]` oracle and adds exactly four History
HTTP calls, so a partial refreshed `["dividend:4"]`, lost accepted page or skipped
second refresh request still fails. No timeout expansion, retry, production hook,
money expectation, owner-isolation or privacy check changes were introduced.

Read `/tmp/pr31-frontend-repeat-red.log`, which reproduces the original immediate
subscriber assertion failure in the unchanged 20-run file. Independently ran
`CI=true npm run test -- src/hooks/useEventHistory.test.tsx -t 'retains the whole accepted page chain if a later refresh page is malformed'`:
one target passed, twenty unrelated tests filtered out, 1.50s. This bounded target
run is distinct from the executor's full/repeated suites. `git diff --check`
passed. Direct scoped diff confirms no change to the hook or History API source.
