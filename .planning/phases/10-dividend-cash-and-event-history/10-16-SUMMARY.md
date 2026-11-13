---
phase: 10-dividend-cash-and-event-history
plan: "16"
subsystem: local-ci-and-recovery-verification
tags: [critical-coverage, dev-bootstrap, signed-apk-index, retained-restore, tls, quarantine]
requires:
  - phase: 10-15
    provides: Actual financial browser journeys and connected mixed History UI
  - phase: 10-06
    provides: Reviewed0014 authority and exact retained-tool compatibility
provides:
  - Complete47-module critical CI/docs contract with statement and branch coverage
  - Explicit fail-closed local dev migration-owner prerequisite
  - Owner-approved exact Node security repair with unchanged other packages
  - Current0014 service replay/History and complete same-archive local gates
affects: [10-17, 10-18, 11]
tech-stack:
  added: []
  patterns: [explicit-dev-only-owner-bootstrap, authenticated-index-control-payload-chain, one-archive-all-recovery-stages]
key-files:
  created:
    - backend/app/db/dev_bootstrap.py
    - backend/tests/test_dev_bootstrap.py
    - .planning/phases/10-dividend-cash-and-event-history/10-IMAGE-REPAIR-REVIEW.md
  modified:
    - .github/workflows/ci.yml
    - CLAUDE.md
    - backend/tests/test_critical_coverage_config.py
    - docker-compose.yml
    - docker-compose.override.yml
    - deploy/tests/dividend-execution-fixture.py
    - deploy/tests/stock-runtime-fixture.py
    - deploy/tests/ops-fixtures.py
    - deploy/tests/test-ci-ops.py
    - deploy/tests/test-deploy-prerequisites.py
    - deploy/tests/test-image-contracts.py
    - frontend/Dockerfile
    - .planning/phases/10-dividend-cash-and-event-history/10-LOCAL-PROOF.md
key-decisions:
  - Keep0014 authority/migrations immutable; dev prerequisite creates only an absent safe canonical owner and never repairs unsafe roles.
  - Apply only the explicitly approved Node24.22.3-r0 update; pin existing transitive versions so no other package changes.
  - Authenticate unsigned CAS APK through the existing signed index, exact control checksum and linked payload SHA256 without trust bypass.
  - Keep actual legacy0008 selected cutover/old-app rollback distinct from current0014 retained-service replay proof.
requirements-completed: []
requirements-supported: [DIV-03, DIV-04, DIV-05, HIST-03]
duration: approximately90min; final serial proof1391.017s
completed: 2026-11-13
---

# Phase10 Plan16: Complete Local Gates and Exact Recovery

**All47critical modules reach100% statements/branches; real current0014 replay,
fresh/upgraded TLS and one-archive recovery pass after an approved exact Node fix.**

## Tasks and commits

1. CI/docs/regression and necessary dev startup prerequisite: RED`11f9649`,
   GREEN`5e0b066`, bounded waits`cb75e56`, same-archive CI`127231b`.
2. Current-service fixtures`fe6a38b`, prerequisite test-fixture repair`45ab970`,
   approved Node repair`6d95d19`, actual0013/0014 consumer fix`7196d5f`, final
   measured evidence`895a408`. This summary is committed separately.

All commits are local on`feature/v1.1-stock-planning`; no tracked deletion.
Parent owns canonical STATE/ROADMAP/requirements updates. All four whole
requirements remain unchecked until the remaining goal/review/human gates.

## Actual verification

| Gate | Measured result |
|---|---|
| Full backend |2550passed,93existing warnings,294.73s;99.87%overall|
| Actual47critical list |4545statements/1452branches,0missing/partial,100%|
| Full backend static |Ruff;190formatted files;Mypy88sources pass|
| Bootstrap focused |25combined cases0.71s;helper24statements/10branches100%|
| Ordinary fresh/0013dev startup |20.531s/22.567s;safe owner,idempotency,actual unsafe-flag/membership refusal;cleaned|
| Host frontend |697tests/36files16.15s;98.37%statements94.82%branches;static/build pass|
| Repaired-image frontend |697tests/36files31.40s;UID1000,networknone;lint/types/format/build pass(build1.00s)|
| Current full browser |49passed/one expected deployed-CSPskip305.7s;cold build99.2s separate|
| Locked dependency audits |pip:none2.841s;npm high-threshold exit0/3.103s,2low15moderate,no HIGH/CRITICAL|
| All five strict images |0HIGH/CRITICAL including unfixed;runtime15.251s,builder7.167s,PG5.560s,Redis1.609s,Node3.702s|
| Native runtime |UID1001,networknone,XNYS/calendar,dividend/worker/History imports and exact target pass|
| Actual full SQL contracts |23/23,111.574s,zero skips|
| Current dividend source/clone |35.224s;cycle-first original/held/dedup/reconciled publication,successful replay,exact cash/quarantine|
| Actual stock0013/0014 consumers |41.322s;same receipt digest,exact canonical state,current0014History,quarantine|
| Offline contracts |image13,CI12,backup26,restore6,DBconfig136,prerequisites20,datastores13,reexec14,rollback18,app8,ports11,trade7;nginx config pass|

Full commands, individual timings and logs are in`10-LOCAL-PROOF.md`. Existing
locked environments were reused; no npm/uv lock change or host tool upgrade.
The owner-approved Node package exception is documented separately below.

## Final same-archive proof

Actual command:`python3 /tmp/birja-phase10-16-final-gate.py`.
It calls canonical roundtrip(explicit_archive),roles(),both TLS lanes with equal
authority results,image_transition(),then the actual selected rollback script
with`--recovery-bundle`using that same archive. **Literal CLI`--all`was not run.**

| Completed stage | Seconds |
|---|---:|
| Retained0007–0014 |458.785|
| Restricted roles |183.898|
| Populated verify-fullTLS |147.413|
| Fresh verify-fullTLS |160.010|
| Physical image transition |39.011|
| Selected cutover/recreate/old-app rollback |395.051|

Total1391.017s includes orchestration/integrity checks. **Selected cutover and
actual old-app rollback are proven at0008.** No old-runtime-on0014 or selected
0014candidate-cutover claim is made. Current0014 proof is the genuine retained
clone/current-service replay, mixed History/Portfolio and financial quarantine.
Plan17 must assess this exact scope; Phase11 rollout remains separate.

Archive`/tmp/birja-backup-test-phase10-final/recovery.tar`,152320000bytes,
SHA256`1faa8277951d0c2a66ac10ffb8b39b5f85372acdacd10b3b3348126c90052cc1`.
Current11CORE/unit files reproduce the pre-consumer archive byte-for-byte; this
is a newly executed final current-service proof, not reuse of an earlier pass.
Report`/tmp/birja-backup-test-phase10-final/gate-report.json`, SHA256
`0114bbd04e61756afd47fda9246eb333102d059af799c2e1db0efeadd471f972`.
Log`/tmp/birja-phase10-16-final-same-archive.log`, SHA256
`a06b495303d4a23c93aadcda97f89d688d72c0185d3b84e445f55413622dd344`.

All384final source hashes and all three accepted built image IDs match before/
after; every stage checks source/archive/CORE bytes. Independent final receipt
`/tmp/birja-phase10-16-final-integrity.json` seals all artifact hashes and confirms
zero containers/networks/volumes across all six exclusively owned test projects.
No unrelated dev/prod resources were changed. Financial authority, schema,
migrations, bootstrap grants and producer/consumer contracts are unchanged.

Retained0014 actually replays originals and every successful correction/no-change
through current services, reads mixed History/Portfolio with unchanged cash,
proves paidA→heldB dedup/reconciled successor, and retains app/scheduler42501
denials. Existing function ownership permits owner replay; **no EXEC grant is
added**. The extra current0014 stock callback proves private trade/split History
with the same saved original receipt. Both SQL authorities and immutable lineage
remain covered by exact canonical verification and corruption controls.

## Security repair and deviations

- **Observed blocking HIGH, explicit approval:** strict scan failed Node on
  `CVE-2026-123863`in24.22.2-r2. Owner selected“Approve security patch and continue
  locally(Recommended)”for exact24.22.3-r0. Official Node/Wolfi metadata and
  signed configured index were reviewed before candidate retrieval/build.
- **Actual APK chain:** no embedded signature; standalone`apk verify`therefore
  says`UNTRUSTED`, preserved honestly. Existing keys authenticate the repository
  index; exact compressed control checksum matches it and authenticated PKGINFO
  datahash matches the whole compressed payload SHA256. Default repository
  verification is used without new keys/allow-untrusted/waiver. Installed Node
  binary matches authenticated payload. See`10-IMAGE-REPAIR-REVIEW.md`.
- **Rejected first build:** fresh resolution also updated ICU/libstdc++ revisions.
  Inventory guard rejected it. Explicit pins retain the three already accepted
  versions; corrected26-package inventory changes **only Node**. Base/npm/locks
  unchanged. Old failed scan, standalone diagnostic, first build and delta remain.
- **[Rule3] Dev prerequisite:** ordinary startup lacked the canonical owner.
  Explicit dev-only bootstrap validates target/env/actual admin before writes,
  creates only an absent safe owner, and refuses unsafe roles without repair.
  Actual idempotency exposed asyncpg Record iteration; fixed with driver-shaped
  regression and real fresh/0013 startup/unsafe-role proof,100%critical coverage.
- **[Rule3] Stale prerequisite fixture:** existing19-test suite had6missing-table
  manifest errors. Authorized test-only change derives the complete legacy
  contract from the producer; real restore validation still rejects omitted
  tables/columns and invalid cash.20tests pass8.232s; validator unmodified.
- **[Rule1] Ops-only compatibility:** real0013 replay exposed absent dividend
  tables in the new History assertion. Explicit0014guard and mandatory0014
  callback preserve all old0013 behavior. Actual both-revision proof and final
  retained run pass. Source hash changes after the browser are limited to
  ops-fixtures,stock-runtime-fixture,test-ci-ops; all other381 hashes unchanged.
- Initial probe private-file refusal and noexec frontend harness failure ran no
  corresponding consumer/tests; corrected isolated harnesses pass. Missing
  `/usr/bin/time`did not run audits; Bash timing then recorded genuine audit
  passes. Earlier fixture settings/PID-observer mistakes are retained in failed
  logs; ordinary paths use services and original raw-SQL PID wait proof remains.

## Threat flags and limits

| Flag | File | Mitigation/proof |
|---|---|---|
| threat_flag: privileged-dev-database-access |backend/app/db/dev_bootstrap.py|Exact dev target/admin guard,constant safe role,all unsafe flags/memberships refused,no repair,timeout bounds,100%critical and actual disposable startup|

T-10-16-01/02/03/SC local controls pass through real constrained SQL, immutable
lineage/owner History/cash assertions, exact restore/corruption/quarantine,
bounded isolated cleanup and actual approved supply-chain repair. No blanket
certification or independent Plan17 review is claimed. No known blocking stubs;
synthetic external evidence and intercepted infrastructure fixtures are labelled.

## Remaining gates

Ready for Plan17 code/security/UI/goal review. Refresh its review packet using
current captures`/tmp/birja-phase09-browser-8w6nln0e`and separately sealed browser/
operations manifests. The previous ZIP is historical; it was not regenerated or
newly source-validated here. Plan18 actual new-UI/native200%owner acceptance and
deferred live/provider/publication gates remain pending. No push,PR,merge,
deployment,B2,timer,installed production-tool or provider action occurred.

## Self-Check: PASSED

Created files and all nine listed task/evidence commits exist. Six-stage report
is passed with complete owned cleanup and identical before/after archive/source/
image identities. All five strict reports have zero qualifying findings. No
tracked deletion or blocking stub; unrelated`.claude/`is preserved. Canonical
state/requirements are deliberately left to the parent orchestrator.
