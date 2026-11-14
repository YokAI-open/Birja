---
scope: pr31-ci-failures
reviewed: 2026-11-14
reviewer: /root/pr31_debug/security_review
status: secured
threats_closed: 6
threats_open: 0
unregistered_flags: 0
---

# PR31 affected security review

Independent security review of the three-file diff against `95912e0`.
Implementation remained read-only. No Docker workload, package installation,
network operation, publication or production action occurred during this review.
This is bounded engineering verification, not an ASVS certification claim.

## Threat verification

All six assigned threats have disposition **mitigate**. No BLOCKER or WARNING
was found in this reviewed scope.

| Threat | Result | Concrete verification |
|---|---|---|
| T1 authenticated import and binding | CLOSED | `check-recovery-image.py:40` calls unchanged `verify_saved_image` before `docker image load` at55 and binding at63; rewinds the same private temporary file. `verify-restore.py:147` authenticates pinned index/manifest/config plus linux/amd64 linkage. Its232 archive validator rejects duplicate/traversal/non-file members, tagged or additional roots, unapproved blobs and changed layers before import. Regression at `test-image-contracts.py:40` verifies failed archive validation never reaches load/bind. |
| T2 reject wrong preexisting alias | CLOSED | Helper43–50 inspects the alias and invokes unchanged `loaded_recovery_image` before loading. `verify-restore.py:295` accepts only exact config/platform identities for that alias, with exact OS/architecture. `bind_recovery_image:311` selects only authenticated identities and rechecks the bound alias. Wrong-alias regression raises before either load or bind. |
| T3 exact approved package boundary | CLOSED | `test-image-contracts.py:418` checks eight approved calendar full records separately; OTEL1.45.2 version and complete-record hash are pinned separately at451. Independently recomputed historical `e728855` inventory excluding only root/OTEL: `8b0f58d9199b3dad2d27d9b398d33cc578b8a819307a3838dfc1cb32934991f1`, exactly the revised other-entry assertion. Negative controls reject OTEL version/artifact and unrelated dnspython version/FastAPI artifact changes. No blanket inventory refresh. |
| T4 preserve gates and retained authority | CLOSED | Diff changes only helper and two contract files. `deploy/verify-restore.py`, all retained CORE/authority, workflow, build recipes and lock are unchanged. Workflow53 retains unrestricted `uv run pip-audit`; scanner invocation remains the five actual images. Independent16 CI checks pass, including strict image-policy and gate-omission/failure mutations. Helper remains before the standalone PostgreSQL fixture in workflow246/306. No waiver or production recovery change. |
| T5 owned cold reproduction cleanup | CLOSED | Reviewed `/tmp/pr31-ops-cold-before-after.log`: original helper reports strict verification success yet unique `birja-recovery-postgres:pr31-owned-cold-probe` is missing; actual Compose fails `No such image`. Patched authenticated import/bind starts healthy PostgreSQL and unchanged running-image guard reports exact platform42c334e9…/config4ee05252…. Cleanup removes only the named synthetic project container/network and synthetic alias. No retained alias deletion appears. This verifies retained evidence; no independent live Docker inspection is claimed. |
| T6 pending DNS boundary and provenance honesty | CLOSED for current scope | `backend/uv.lock` remains original SHA256 `5622e840e9a8312f930523cd1bedb9830e9ce5679d9aa77d7c1696784eb317c8`; no DNS exception or lock delta is present. `pr31-DEPENDENCY-REVIEW.md` explicitly requests approval before project lock/install and distinguishes parsed publishing attestations from independent cryptographic trust/log verification. Current review does not approve installation or resolve the vulnerable dependency. Any approved later lock/exception needs a delta review. |

## Independent checks and byte scope

- `python3 deploy/tests/test-image-contracts.py`:15 passed,0.699s.
- `python3 deploy/tests/test-ci-ops.py`:16 passed,0.553s.
- Historical all-other full-record digest independently recomputed and matches.
- Read actual before/after cold-start evidence; no Docker rerun competing with
  the investigator's real PostgreSQL suite.

| Reviewed source | SHA256 |
|---|---|
| deploy/tests/check-recovery-image.py | ecc9896db6b4b2f2141e6f686d25aff38fe0e2988ff019f70879c0a7894c5c9a |
| deploy/tests/test-image-contracts.py | 0824f0dcac34c71c2f836ea67b32f568fe62071ded80a02b82a81faf3eb9a787 |
| deploy/tests/test-ci-ops.py | 4f8239d8f1dc281521350e284a81924a170163062223eb8420eaf5b6162384bf |

## Limits and unregistered flags

No unregistered surface was found: importing an authenticated local export and
binding its pinned alias are covered by T1–T2. Unrestricted audit currently still
fails the independently reported dnspython advisory; this report does not mark
that dependency fixed, claim hosted CI success, or authorize publication. Exact
DNS installation/lock changes remain approval-pending and outside these hashes.
Publishing attestation crypto verification and production/provider acceptance
are not established by this review.

## Approved DNS delta security review

After the parent relayed explicit owner approval, independently reviewed the
three-file DNS delta against `0dd227e`. This section supersedes the earlier
approval-pending scope statements for the exact DNS repair only. The original
helper/cold-start review remains attributed to its original hashes.

All six assigned DNS-delta threats have disposition **mitigate** and are
**CLOSED**; zero BLOCKERs, WARNINGs or unregistered flags.

| Threat | Actual verification |
|---|---|
| D1 exact approved resolution/install | Independently parsed complete before/after lock: identical top-level metadata, identical package-name sets, exactly one changed record (`dnspython`). Current lock equals approved SHA256 `3eded7f21be30568f5d4fae129f38a11e19484035f60f1477a3f9b2bf30fd2d4`. Downloaded wheel equals approved SHA256 `af15f7d385a6ae2fb35a796fde2138004c8c42c7389090e2addc83e3b3340fd8`. Compared165 installed wheel files byte-for-byte with this wheel: zero mismatches; installer-generated RECORD excluded. `/tmp/pr31-dns-sync.log` records exactly one uninstall/install,2.9.0→2.9.2. |
| D2 preserve historical other records/calendar | Independently recomputed `e728855` records excluding root, OTEL and DNS: SHA256 `e7415d7142069e6bca45afd4d37cd758a1d7c83ddd401a678b1b054c9b7b9509`, matching `test-image-contracts.py`. Exact eight-calendar full-record hash remains unchanged. Full DNS new-record hash independently equals `4ad11523a6d2c2d0989a1eb5dd28d6edfa8c86170728ffc04ca47e1b173d3f79`; its version is exactly2.9.2. Mutation checks reject changed DNS version and wheel hash, OTEL drift and unrelated FastAPI artifact changes. |
| D3 exact legacy boundary | `test-rollback-db-security.sh:89` authenticates complete old DNS2.9.0 record hash `94eaf4580a2e9ddcebeb20c972343bd5ba85647b9d292423921c9652fc3eac21` and exact new record above; preserves prior exact OTEL/calendar exceptions and direct equality for every remaining record. No general old/new version range. Actual self-test rejects DNS version/artifact mutations, unrelated package drift and OTEL/calendar mutations. |
| D4 preserve audit/image/recovery gates | Delta does not touch workflow, scanner, audit arguments, Dockerfiles or recovery dispatch/gates. `/tmp/pr31-dns-audit.log` states unrestricted audit found no known vulnerabilities; reviewed installed-content equality separately. Audit/image qualification is distinct from source review; full image builds/scans remain investigator-owned running evidence and are not promoted to passed here. |
| D5 retain CORE/financial/schema/auth | Diff names against0dd227e contain only lock, the image contract, legacy contract and debug/code-review artifacts. No retained CORE/producer/restore/authority, application financial/authentication, Alembic or schema change. Legacy delta only extends exact artifact comparison and negative controls. |
| D6 disclose provenance and scope | Exact approval is recorded in debug Evidence and matches the applied lock/wheel. Dependency review retains original prospective review and accurately states publishing attestations were parsed, without claiming independent Sigstore trust-root/log cryptographic verification. No permission for push/merge/production/provider follows from this local approval. |

Independent bounded checks:

- `python3 deploy/tests/test-image-contracts.py`:15 passed,0.702s.
- `bash deploy/tests/test-rollback-db-security.sh --self-test-retained-install`:
  passed; offline synthetic installed-launcher behavior and exact artifact
  mutation controls execute without Docker.
- Independently parsed full locks, recomputed historical/old/new DNS digests,
  authenticated exact wheel bytes and compared165 installed files.
- Read `/tmp/pr31-dns-upstream.log`:211passed/31skipped/71subtests; this is
  reviewed investigator evidence, not a second execution by this reviewer.
- Read `/tmp/pr31-dns-wks-red.log` and `pr31-dns-wks-green.log`: official
  `test_wks_bounds` fails against old2.9.0 because an out-of-range service fails
  to raise `SyntaxError`, then passes against installed2.9.2 in0.10s. The
  bounded65536 probe supplies actual advisory-specific RED/GREEN evidence.
- No Docker workload, installation, network operation, commit or source edit
  was performed by this reviewer.

| DNS delta reviewed source | SHA256 |
|---|---|
| backend/uv.lock | 3eded7f21be30568f5d4fae129f38a11e19484035f60f1477a3f9b2bf30fd2d4 |
| deploy/tests/test-image-contracts.py | b7bef3ec796930a939d92c4d36601a8ad5463a50e68fd5e5cc2ad7e3920f3a68 |
| deploy/tests/test-rollback-db-security.sh | 7d506a4973016c874fd706ff9e119902b68f6bfd9b00782ea1309924631893e3 |

This verdict covers the exact source/artifact delta. Backend coverage and fresh
image qualification remain separate actual gates. Hosted CI success,
publication and production acceptance are not claimed.

## Image checkout-history security delta

Independently reviewed `.github/workflows/ci.yml` and
`deploy/tests/test-ci-ops.py` against `ade062b`. All four scoped threats below
have disposition **mitigate** and are **CLOSED**, with zero BLOCKERs, WARNINGs
or unregistered flags. This review is limited to these two exact files; any
parallel frontend test changes are outside its scope.

| Threat | Actual verification |
|---|---|
| C1 retain real Git-isolation proof | Workflow image checkout now requests `fetch-depth: 0` before contracts. The actual `FixtureGitIsolation.test_generated_launcher_git_ignores_denied_host_config` remains unchanged: denied host Git config fails, generated launcher's actual environment block reads only fixture-local config, hidden `.git` fails, and production source is asserted not to contain `GIT_CONFIG_NOSYSTEM`. No skip, fixture mock or weakened assertion is introduced. Independently executed the16test CI suite including this fixture. |
| C2 reject missing/late history prerequisite | `image_policy` now requires the full-history checkout before the actual CI-contract command. Mutation controls reject depth1, removed `with`/history configuration and checkout moved after contracts. Independently invoked revised policy against the complete original `ade062b` workflow: rejected with `image fixture contracts require full Git history first`. |
| C3 preserve gates and credentials/ref trust | The only workflow delta is two configuration lines under image job's unchanged `actions/checkout@v7`. No action version, token permissions, credential persistence, checkout repository/ref, event type, build input, audit/strict including-unfixed five-image scan, failure propagation or aggregate requirement changes. Full-history fetching makes the already referenced historical source available; it does not add a new source or bypass the existing source/identity guards. Existing ops checkout already uses full history. |
| C4 preserve runtime/CORE and bounded evidence | Neither reviewed file changes product/runtime/financial/auth/schema/retained CORE. Reviewed `/tmp/pr31-shallow-repro.log`: owned local depth1/no-tags clone lacks `v0.3.1`, and unchanged actual fixture fails importing `git archive v0.3.1`; fetching history/tags into that same clone makes the identical fixture pass. It still proves denied-host-config and missing-repository failures. This is reviewed raw evidence, not an independently repeated clone; no Docker, package install, network or production operation was performed by this reviewer. |

Independent checks:16CI tests passed0.531s;15image tests passed0.665s;
original-workflow negative rejected; `git diff --check` passed.

| Reviewed checkout delta source | SHA256 |
|---|---|
| .github/workflows/ci.yml | a02b0ce7fef757afd362bafad9e78b3d691513a32bd15f8c0ebedcf53294172a |
| deploy/tests/test-ci-ops.py | 978fea16619806d7effcb10a8319b83402e8621589497ce7b0a942c6d60c4cb2 |

Fresh hosted CI outcome remains separate. This review authorizes no publication,
merge, production or provider action and does not broaden the earlier exact
dependency approval.

## History refresh-test synchronization security delta

Read the additional test-only diff in
`frontend/src/hooks/useEventHistory.test.tsx`; no implementation change was
made. Two scoped threats, disposition **mitigate**, are **CLOSED** with zero
BLOCKERs, WARNINGs or unregistered flags:

- **F1 preserve privacy/error/data assertions:** the test waits for the two
  accepted pages before starting refetch, asserts the settled query result is a
  refetch error, awaits the observer's matching error state, and requires
  exactly four History HTTP calls. The literal retained chain
  `["dividend:3", "dividend:2"]` assertion is unchanged, rejecting replacement
  by the refreshed partial chain. Auth-owner/epoch isolation,401 handling,
  other malformed/append tests and exact monetary fixtures remain unchanged.
  Read the unchanged hook to confirm its owner/epoch/query identity checks and
  refusal of malformed data remain intact; no production source is edited.
- **F2 preserve failure visibility and timing bounds:** only observer
  synchronization uses existing default `waitFor`; no arbitrary sleep, timeout
  increase, retry, skip, catch-and-ignore or permitted failure is introduced.
  The extra direct settled-result assertion prevents waiting alone from
  masking a successful refresh. Reviewed `/tmp/pr31-frontend-repeat-red.log`:
  full-file repeats19/retry0 reproduces the original false observer error flag
  after promise settlement. The fix addresses asynchronous notification, not
  the protected error/data contract. Repeated GREEN evidence is recorded in
  `/tmp/pr31-frontend-repeat-green.log`; full frontend verification remains
  separately owned by the investigator.

Frontend test SHA256:
`0b908857522f6a82cfefafa4593e4a536ae3e25e2698faa7bb8eafa3684bd4a5`.
The final three-file security delta scope consists of this test plus checkout
workflow `a02b0ce7…172a` and CI test `978fea16…4cb2` above. No competing
frontend suite, Docker, install or publication action was run by this reviewer.
