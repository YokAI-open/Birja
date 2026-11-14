---
phase: 11-mixed-asset-recovery-and-acceptance
reviewed: 2026-11-13T19:46:00Z
depth: deep
files_reviewed: 8
files_reviewed_list:
  - deploy/deploy.sh
  - deploy/tests/selected-cutover.py
  - deploy/tests/test-deploy-compatibility.sh
  - deploy/tests/test-selected-cutover-contracts.py
  - deploy/tests/test-rollback-db-security.sh
  - deploy/tests/test-ci-ops.py
  - deploy/tests/test-stock-recovery-contracts.py
  - .github/workflows/ci.yml
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 11: Code Review Report

Independent reviewer: `/root/phase11_execute04/code_review`, a separate
gsd-code-reviewer agent context from the implementation executor. Read-only
source review; this report is the only authored file. No commit or deployment.

## Narrative Findings (AI reviewer)

**Passed within the stated scope: zero BLOCKER and zero WARNING findings.**
Reviewed the eight changed deployment/CI/test sources and traced their retained
entrypoint, recovery-gate, fixture, canonical verification and rollback callers.
Tests were assessed for reliability of their asserted behavior. Planning evidence
and the approved single-package lock repair were supporting context, not a new
application-wide audit. No structural pre-pass was provided.

The source under review is HEAD `6be913cf56e8713d8e48a045dfad91644619215d`;
executable bytes match the final `a7f965fe27bf3da6172f3110245ff31c3627fa12`
campaign map. Independent local hashing found all 389 source/config files match
the final receipt. Relevant application, migration, retained CORE/unit and build
bytes did not change during the qualified recovery rerun.

## Traced behaviors

| Area | Review result |
|---|---|
| Admission ordering | `deploy/deploy.sh:85` validates full lowercase commit SHA and authenticated revision; at0014 only the retained manifest's tested source passes. `do_deploy:416` resolves the actual commit before admission, pending-marker creation, checkout, builds, migrations or writer startup. Fetching a mutable ref does not grant compatibility. |
| Rollback selection | `do_rollback:477` derives failed-attempt state from the existing pending marker/HEAD and replayed successful log. Admission precedes checkout/build/start. Normal old-source rollback on0014 refuses; the pending path returns to the last good tested source. Existing immutable compatibility-set restriction remains. |
| Actual current0014 | `selected-cutover.py:156` verifies current HEAD/revision, full canonical state and all19 dumped sequence identities. It requires exactly PG18.6→18.7 metadata transition while preserving every remaining canonical field. Two owner-clone replays preserve receipts and financial state; actual restricted runtime denials remain42501. |
| Refusal oracle | `selected-cutover.py:131` requires the specific compatibility refusal and compares complete before/after state: financial/schema/authority/identities, original physical fingerprints, HEAD, web link, log, pending marker, containers and runtime image records. An unrelated command failure cannot produce the success marker. |
| Runtime identity | `canonical_runtime_images:118` preserves every field, unknown fields and duplicate rows; only object-key and outer record order are canonicalized. Offline mutations reject changed IDs, tags, metadata, fields and multiplicity. |
| Archive and legacy lane | Both selected callables forward the same authenticated archive. Runner order remains old-image → legacy selected0008 → current selected0014, propagating failures. The existing0008 application downgrade assertions remain distinct and intact. |
| CI and standalone PG | The required ops job provisions and finally removes its isolated test stack. Safe NOLOGIN source-owner setup creates only an absent role; a real transactional regression proves existing unsafe roles are not repaired. Mandatory coverage/audit/image/aggregate dependencies remain. |
| Bounds and cleanup | Child fixture/launcher calls retain explicit bounds. Actual scenario finally cleans owned Compose resources and four owned volumes and checks empty resource listings. Failure-path contract executes the real finally body. Final actual logs and independently retained cleanup receipts report empty owned resources. |

## Independently checked evidence

The reviewer read the private raw logs/reports and recomputed receipt, artifact,
source, archive and tar-member hashes locally. No raw financial/private payload
is copied here.

- Final receipt `/tmp/birja-phase11-gates/final-receipt.json`, SHA256
  `bb90d570e6b2313f7b1fd3fc5d53cf2a6ebe558831b7f0e57a4760d16255f5af`:
  every linked artifact hash matches; all389 current source hashes match.
- Same archive `/tmp/birja-backup-test-phase11-final/recovery.tar`,152320000bytes,
  SHA256 `1faa8277951d0c2a66ac10ffb8b39b5f85372acdacd10b3b3348126c90052cc1`:
  size/hash/private checksum sidecar match; all11 retained CORE/unit tar members
  equal current files and their pinned digests.
- Full refusal evidence directory
  `/tmp/birja-backup-test-selected0014-evidence-p487c9dv`: both complete snapshots
  hash to `b5c4d146f2af9b56f8ce8b25079ad834cda01a53ea9824f46e28ea76f50490be`.
  They contain26 canonical tables,19 sequence identities, schema and dividend,
  execution and resolution authority, plus all operational snapshot fields.
  All four files are0600; the directory is0700.
- Raw runtime before/after hashes respectively
  `b30c2017cd43532acf1e4f71eda24972e1d1a6009efd06aa42c6c1dd553872bb` and
  `d645e0868878d98b5b3d401c652c1959383ee410c04450b535544d2e3be4c902` differ.
  Independent parsing confirms identical complete records with multiplicity,
  and both canonical results bind exactly to their saved full snapshot.
  The earlier failed run's payload was not retained: its cause remains unproven.
- Current0014 log SHA256
  `8b57f962b7cd13db8e8952b3938ccd8b285b97d362fb5bcd446acb3bb21d85d4`
  and report SHA256
  `d6ad5c0973260385dfbaeffb5d365f14e27f92d501cb690bd48da394bcf8c770`
  bind actual342.673s success, two replay passes, intended refusal, failed-attempt
  recovery and cleanup. Legacy log SHA256
  `2f40f4a02de2f33887911726701a3de7356ac9ad07fcf691df69379194360a95`
  contains actual old-image100.375s and selected0008 276.057s successful markers.
- Executor's fresh Plan04 short checks are independently hash-checked through
  `/tmp/birja-phase11-04-offline/receipt.json`, SHA256
  `d6c27240f771c0234b0e9ff6fc6d595908559792da97b8dec6503fcdfb6233c4`:
  diff check,17 deploy cases,7 selected tests and16 CI tests pass,1.247s receipt
  total. This reviewer did not duplicate those unchanged commands.

## Source qualification and limits

Five actual stages ran at `fb926d8c9605452f30e18719d239826ab7d5628a`:
image transition39.639s, encrypted0007–0014 roundtrip452.729s, roles178.205s,
populated TLS145.445s and fresh TLS145.753s. The original serial report remains
`ok:false` after its later offline-installer failure; its SHA256 is
`98e7dd2559b2fb73257bb2ac32e6985127e545c0ea3877dc39f4e0479f990122`.
Actual legacy success is at `22c44d6e4098a8b0fa768a7d0dc542e82072b92b` and
actual complete current0014 success is at `a7f965f`. Git and source-map comparison
independently confirms only selected-cutover.py, its offline contracts and the
rollback test harness differ from the five-stage source. All386 other mapped
files and all11 retained bytes match. Those changes affect the rechecked lanes;
they do not invalidate unchanged producer/restore/authority/runtime/build proof.
The same archive and recorded image identities are retained. Reuse is therefore
qualified evidence, not a newly successful full CI block at final source.

This is a local code-review pass. It does not claim hosted CI success, live
provider permission/access/freshness, production/B2 recovery, deployment or a
historical old application running on0014. Supported0014 rollback is recovery
to the tested source; historical application downgrade is proven only at0008.
SAFE-02/03 final disposition belongs to the separate security/UI/goal reviews
and coordinator. No unchanged expensive gate was rerun for this review.
