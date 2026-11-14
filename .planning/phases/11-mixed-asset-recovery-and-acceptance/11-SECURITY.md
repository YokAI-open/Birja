---
phase: 11-mixed-asset-recovery-and-acceptance
audited: 2026-11-13
status: secured
register_authored_at_plan_time: true
threats_total: 14
threats_closed: 14
threats_open: 0
unregistered_flags: 0
blockers: 0
asvs_version: "5.0.0"
asvs_level: not_configured
---

# Phase 11 security verification

Independent reviewer: `/root/phase11_execute04/security_review`, a separate
gsd-security-auditor agent context from the implementation executor and code
reviewer. Applied the local gsd-secure-phase skill and auditor role. Implementation
was read-only; this report is the only authored file. No commit, package install,
audit rerun, full suite, provider request or production action was performed.

**SECURED for the declared local threat register: 14/14 CLOSED; zero OPEN_THREATS
or HIGH/CRITICAL findings.** Each threat's disposition is `mitigate`; there are
no accept or transfer entries requiring separate disposition documents. This
does not itself complete SAFE-02/03, UI/goal review, hosted CI or rollout.

Reviewed HEAD `6be913cf56e8713d8e48a045dfad91644619215d`; all389 executable/
configuration source hashes match the final `a7f965f` proof map. Plan04 documents
are concurrently owned by other reviewers. No security-enforcement ASVS level or
block_on value is configured in `.planning/config.json`; no level is invented.
The plans explicitly block HIGH/CRITICAL and absent required mitigations.

## Threat verification

Every register row from all four PLAN threat_model blocks was classified before
verification. CLOSED below means the declared mitigation and required local
evidence were found, with the source qualification described below.

| Threat ID | STRIDE category | Disposition | Status | Implementation and observed evidence |
|---|---|---|---|---|
| T-11-01-01 | Tampering/Elevation | mitigate | CLOSED | `deploy/deploy.sh:85` validates immutable SHA/authenticated revision; deploy admission at432 precedes pending marker/checkout/build/start, rollback admission at493 precedes checkout. Current0014 actual refusal marker plus complete unchanged before/after snapshots;17 actual-flow offline cases. |
| T-11-01-02 | Tampering/Repudiation | mitigate | CLOSED | `selected-cutover.py:156` compares canonical financial/schema/authority and19sequence identities, original physical volumes and retained bytes; original stock/dividend receipt replay twice under verified TLS. Actual342.673s current lane includes supported failed-attempt recovery to the tested source. No downgrade/broad grant is used. |
| T-11-01-03 | Disclosure/DoS | mitigate | CLOSED | `selected-cutover.py:34` bounds captured subprocesses at180s with explicit longer bounds where needed; synthetic isolated host/config, private0700evidence directory/0600files at223, owned finally cleanup at988–1010. Actual cleanup markers and independently recorded empty resources. |
| T-11-01-SC | Tampering | mitigate | CLOSED | No Plan01 dependency/image/install change. Locked/pinned retained bytes preserved; final strict audit/image results verified below. Later exact owner-approved lock repair is explicitly qualified, not hidden as an unchanged package. |
| T-11-02-01 | Tampering/Elevation | mitigate | CLOSED | `test-rollback-db-security.sh` invokes legacy and current selected lanes serially with unchanged args.recovery_bundle; `test-ci-ops.py` actual dispatch/mutations reject omission/order/archive replacement/swallowed failures. CI serial graph verifies archive/tool integrity between stages; ci-pass at359 requires backend/frontend/image/e2e/ops and rejects failure/cancel/skip. |
| T-11-02-02 | Repudiation/Disclosure | mitigate | CLOSED | ACCEPTANCE/LOCAL-PROOF separate historical, failed, actual and qualified results. Independent source/artifact/raw snapshot hashing below confirms exact attribution. Public summaries contain synthetic markers/hashes/paths, without copying private financial payload or credentials. |
| T-11-02-SC | Tampering | mitigate | CLOSED | `.github/workflows/ci.yml:53,77,132` retains unrestricted pip-audit, npm high gate and all five actual image scans. `deploy/scan-images.py:181` includes HIGH,CRITICAL and nonzero finding exit, without ignore-unfixed/waiver. Final reports show zero qualifying findings. |
| T-11-03-01 | Tampering/Repudiation | mitigate | CLOSED | `verify-restore.py:780` full manifest/authority verification; retained roundtrip exercises0007–0014, corruption controls, original financial/receipt replay and identity preservation. Raw final-serial log confirms actual stock/dividend replay without second effect; full current0014 snapshots independently match. |
| T-11-03-02 | Elevation/Disclosure | mitigate | CLOSED | `verify-restore.py:951` validates pinned complete function declarations/bodies, role boundary, owners, schema and triggers BEFORE reconstruction; revokes payout EXEC/table mutation/sequence rights from app/scheduler. Clone PUBLIC CONNECT revoked at1020. Actual42501quarantine and fresh/populated verify-full TLS/badCA/hostname/plaintext rejection recorded. `event_history.py:150` filters every union source and subsequent joins by owner; API injects CurrentUserDep and user.id. |
| T-11-03-03 | DoS/Disclosure | mitigate | CLOSED | Existing bounded owned harness/clean environments, private capture and serial execution preserved. CI owns test-stack setup/finally cleanup; selected finally cleans only owned resources and verifies empty lists. Six-project zero-resource receipts include failed attempts, not just successful execution. |
| T-11-03-SC | Tampering | mitigate | CLOSED | Exact approved1.45.2lock repair, unchanged all other package entries, patched unrestricted audit clean, npm high gate passes and all five strict scans clean; native oversized-traceparent refusal and rebuilt image identities bind the repaired runtime. Approval/attestation limits below remain explicit. |
| T-11-04-01 | Repudiation/Tampering | mitigate | CLOSED | This distinct reviewer independently recomputed all389source hashes,23final linked artifacts,113Task1 artifacts, archive/11tar members, full refusal snapshots and raw runtime record equality. Full failed report remains ok:false; no failed full block is relabelled successful. Coordinator must require separate UI/goal disposition before SAFE completion. |
| T-11-04-02 | Disclosure/Elevation | mitigate | CLOSED | Exact owner predicates/auth dependency and clone authority/quarantine traced above, full private receipt modes checked. Product source continuity supports review reuse; this security pass makes no new human/native200% claim. Material-change acceptance remains an explicit UI/goal-review gate, not replaced by6/6contract approval. |
| T-11-04-SC | Tampering | mitigate | CLOSED | All final mapped bytes match; only three rechecked harness files differ from the five-stage map, remaining386files/11retained bytes/runtime/build image identities equal. Strict security evidence remains attributable to those unchanged runtime/build sources. No new install or scan waiver in review. |

## Independently checked proof and qualification

Final receipt `/tmp/birja-phase11-gates/final-receipt.json` SHA256
`bb90d570e6b2313f7b1fd3fc5d53cf2a6ebe558831b7f0e57a4760d16255f5af`.
Recomputed all linked artifact hashes, all389current source hashes, and the
Task1 receipt's113linked artifact hashes; none differed. Task1 receipt SHA256
`a9ae4672b48c9d848ab8b9e613b59f8d327c99246d89eb68915e8a2aa90608d9`.

Archive `/tmp/birja-backup-test-phase11-final/recovery.tar`:152320000bytes,
SHA256 `1faa8277951d0c2a66ac10ffb8b39b5f85372acdacd10b3b3348126c90052cc1`.
Independently read all11CORE/unit tar members: each equals the receipt digest
and current corresponding source bytes. Runtime image
`sha256:2c91676c9d4408bb7ab7458a6dfef353157aef44dca18a77a9a60fe97dbfb80b`,
builder `sha256:ec7544f9813f558889bb725513b524b12ee3608b93073f1f2811755b9f185856`
and Node `sha256:f2e7cc228ec174d5df1bca0e61050f39b8c3685aa36095459df1b28583971feb`
match Task1 and the subsequent campaign records.

Five actual stages at `fb926d8c9605452f30e18719d239826ab7d5628a`:
image transition39.639s, roundtrip452.729s, roles178.205s, populatedTLS145.445s,
freshTLS145.753s. The970.754s full report remains failed after a subsequent
offline self-test failure: SHA256
`98e7dd2559b2fb73257bb2ac32e6985127e545c0ea3877dc39f4e0479f990122`.
Actual legacy old-image100.375s and selected0008 276.057s are at
`22c44d6e4098a8b0fa768a7d0dc542e82072b92b`; fresh complete current0014
342.673s is at `a7f965fe27bf3da6172f3110245ff31c3627fa12`.

Independent campaign-map comparison found exactly selected-cutover.py,
test-selected-cutover-contracts.py and test-rollback-db-security.sh changed;
all386other sources match. These deltas repair installer expectations/exact
approved package fingerprint and preserve all runtime fields while canonicalizing
JSON order. The affected legacy/current lanes and mutation contracts were rerun.
Unchanged restore/authority/build/runtime proof can therefore be reused under
the explicitly approved qualification. This is **not a fresh successful full CI
block at final source**, nor hosted CI success.

Current0014 raw log SHA256
`8b57f962b7cd13db8e8952b3938ccd8b285b97d362fb5bcd446acb3bb21d85d4`
contains actual current cutover, twice owner-clone replay/42501, intended old-source
refusal, tested-source failed-attempt recovery and cleanup. Report SHA256
`d6ad5c0973260385dfbaeffb5d365f14e27f92d501cb690bd48da394bcf8c770`.
Historical application downgrade is exercised at0008 only;0014 rollback means
recovery to the retained tested source.

Private directory `/tmp/birja-backup-test-selected0014-evidence-p487c9dv` is0700;
all four files are0600. Both full snapshots independently hash to
`b5c4d146f2af9b56f8ce8b25079ad834cda01a53ea9824f46e28ea76f50490be`.
They preserve financial/schema/authority/identities, physical originals, HEAD,
web link, log, pending state, containers and complete runtime records. Raw runtime
hashes differ (`b30c2017cd43532acf1e4f71eda24972e1d1a6009efd06aa42c6c1dd553872bb`
and `d645e0868878d98b5b3d401c652c1959383ee410c04450b535544d2e3be4c902`),
but independent parsing confirms every field and row multiplicity equal. Only
outer row/key ordering is canonicalized. Earlier failed payload was not retained;
its historical failure cause remains unproven and is not asserted resolved by
diagnosis. Fresh complete proof and field/multiplicity mutation regressions are
the evidence used here.

Fresh Plan04 short-check receipt SHA256
`d6c27240f771c0234b0e9ff6fc6d595908559792da97b8dec6503fcdfb6233c4`
was independently hash-checked with all four logs: diff check,17deploy cases,
7selected and16CI tests pass in1.247s. Unchanged commands were not repeated.

## Dependency and image boundary

`backend/uv.lock` SHA256
`5622e840e9a8312f930523cd1bedb9830e9ce5679d9aa77d7c1696784eb317c8`.
Independent parsed comparison to48d970c finds exactly one full package entry
changed: opentelemetry-api1.45.1→1.45.2. The wheel hash is precisely owner-approved
`2cbd737377e710ee740d261c94e93fa0f08e6d037c18f17513cc0a2d94479a34`.
See11-DEPENDENCY-REVIEW: official metadata/download inspected before approval;
wheel signature unavailable and provenance endpoint404. A verified GitHub release
signature does not bind the wheel. No attestation is claimed; this disclosed
provenance limit is not silently converted into a new accepted application risk.

Read patched raw pip-audit result: no known vulnerabilities. Npm high gate passes
with2low/15moderate retained findings, not zero total vulnerabilities. Independently
parsed builder/runtime/Postgres/Redis/Node patched raw Trivy reports: zero
HIGH/CRITICAL in each, including unfixed. Status digest
`61f35169b8e7bd64808bf89e4dc6008c2d96c2b326905a1447bd365ec37aa5bb`.
No broader package re-audit or external advisory lookup was performed in review.

## Scoped ASVS5 mapping and flags

Mapping follows11-RESEARCH's5.0.0 names: V2 Validation and Business Logic;
V3 Web Frontend Security; V4 API and Web Service; V6 Authentication;
V7 Session Management; V8 Authorization; V11 Cryptography; V12 Secure
Communication; V13 Configuration; V14 Data Protection; V15 Secure Coding and
Architecture; V16 Security Logging and Error Handling. Checked the applicable
restore/encryption, TLS, owner/auth/session preservation, fail-closed deployment,
immutable financial replay, restricted configuration and evidence paths above.
This is scoped engineering verification, not blanket ASVS certification.

No SUMMARY has a literal `## Threat Flags` section; Plans01/02 instead document
Threat Outcomes, and Plan03 records the package repair/harness corrections.
These map to existing SC, evidence and host/runtime threats. No unregistered
implementation attack surface was identified within the bounded changed paths;
absence of a flags section was not treated as complete evidence by itself.

Accepted risks log: no new accepted threats or transfers. Existing W01–W08 debt,
the deployed-CSP-only browser skip, SAFE-01/provider rights/access/freshness,
production/B2/installed tools/timers/publication remain separately scoped.
This audit grants no rollout, push, merge or deployment permission. Separate
UI/goal reviews and coordinator own final phase/requirement disposition.
