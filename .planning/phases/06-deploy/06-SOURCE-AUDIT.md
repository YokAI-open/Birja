# Phase 06 — Multi-source coverage audit

Planning coverage only, 2026-10-30. **0 unplanned source items.** No implementation, tests, installations, live data processing or deployment has occurred. All execution/live results remain pending. No Phase06 CONTEXT exists; user chose continuation without it and research first. No locked decisions were fabricated.

| Source | ID / item | Plan / task | Status | Disposition |
|---|---|---|---|---|
| GOAL | Friends sign up/trade live with safely backed-up data | 06-02..13 | COVERED | Faithful MVP user story in Phase06 ROADMAP section; existing product retained |
| REQ | DEPL-01 public HTTPS/signup/trading | 06-04..08,10..13 | COVERED | Current app released through authorized git-flow, live acceptance |
| REQ | DEPL-02 nightly off-server backup + restore | 06-01..03,08,09,13 | COVERED | Genuine remote recovery and timer evidence mandatory |
| GOAL | SC1 Gmail and Outlook signup/trade | 06-13-01 | COVERED | Owner/friends enter own OTP; provider pass/fail only |
| GOAL | SC2 nightly off-server + successful restore | 06-09-02,13-02 | COVERED | Manual backup cannot count as actual calendar activation |
| GOAL | SC3 existing actual trading Playwright CI | 06-08-02,10-02,11-03,13-02 | COVERED | Existing full browser jobs required, no discovery substitution |
| GOAL | SC4 least-privilege app + DB SSL decision | 06-04..07,12-02 | COVERED | Verified CA/hostname TLS satisfies shared hard security rule |
| CONTEXT | Phase06 CONTEXT absent | 06-01-02; all plan context | N/A | No Phase06 D-XX source or invented decisions |
| CONTEXT | Historical02.1 D-01 domain/separate nist.one | 06-12-02; all plan context | COVERED | Existing birja.nist.one retained; unrelated site untouched |
| CONTEXT | Historical02.1 D-02 manual deploy/no CI keys | 06-07,08,12 | COVERED | No autodeploy or CI production secrets |
| CONTEXT | Historical02.1 D-03 Full(strict) | 06-12-02 | COVERED | Preserve origin HTTPS and edge mode |
| CONTEXT | Historical02.1 D-06 no Cloudflare/IP/firewall automation | 06-08-01,12-02 | COVERED | No new scheduled edge/firewall changes |
| CONTEXT | Historical02.1 D-07/D-08 manual DNS renewal/no API token | 06-08-01,12-02 | COVERED | D-08 supersedes token-related D-04/D-07 parts |
| RESEARCH | Existing few-friends host/Compose/PG18/no major upgrade | 06-02..08 | COVERED | Reuse pins and stack, no platform expansion |
| RESEARCH | Responsibility map: host backup timer, one migrator, one scheduler | 06-06..08 | COVERED | No backup inside web workers/app job scheduler |
| RESEARCH | Provider, endpoint/region/bucket or SFTP, budget | 06-01-02 | COVERED | Future explicit owner decision, recommendation not selection |
| RESEARCH | Recovery window/time, schedule/jitter/freshness | 06-01-02,08-01,09-02 | COVERED | Accept explicit targets; reopen design if PITR required |
| RESEARCH | Retention, deletion policy/provider lifecycle | 06-01-02,08-01 | COVERED | No destructive pruning without selected separate authority |
| RESEARCH | Independently held repository password/config recovery scope | 06-01-02,08-01,09-02 | COVERED | Private custody decision and actual recovery material proof |
| RESEARCH | Missed-night operator response | 06-01-02,08-01,09-02 | COVERED | Status + owner check/escalation; no implicit external messaging |
| RESEARCH | restic [ASSUMED] package legitimacy | 06-01-03,02-02,08-02 | COVERED | Blocking-human official signed artifact/version gate before install |
| RESEARCH | pg_dump -Fc matching PG18, list/checksum/tool/revision metadata | 06-02-02 | COVERED | Standard PG clients, not live PGDATA tar |
| RESEARCH | Held exported snapshot for canonical manifest + dump | 06-02-02,03-02 | COVERED | Concurrent-write test, exact private precision/UTC ordering |
| RESEARCH | Eight app tables + revision, counts/digests/sums privately | 06-02-02,03-02 | COVERED | No private rows/addresses/balances/session/digest output |
| RESEARCH | Sequence MVCC caveat and safe identity progression | 06-03-02,04-01 | COVERED | Generated inserts on clone, no live sequence rewrites |
| RESEARCH | Locked staging/upload/exact retrievable ID/atomic success | 06-02,03 | COVERED | All producer statuses + negative partial/unavailable tests |
| RESEARCH | Stable restic grouping, preserve good snapshot, no custom crypto | 06-02-02,08-01 | COVERED | Restic standard encryption and retention dry-run |
| RESEARCH | Fixed isolated projects/guards before any side effect | 06-03,09-02 | COVERED | Internal network/tmpfs/no ports/app/email/jobs/prod mounts |
| RESEARCH | Hostile dump isolation, no --create/--clean/in-place restore | 06-03-01 | COVERED | No archive-driven source/target selection |
| RESEARCH | Exact retrieved snapshot restore, no prior Alembic upgrade | 06-03-01,09-02 | COVERED | --no-owner --no-acl --role --exit-on-error --single-transaction |
| RESEARCH | Constraints, index validity, money/timestamps, tamper negatives | 06-03-02 | COVERED | Deliberate corruption must fail independently of hashes |
| RESEARCH | Populated0007 ownership/identity transfer, existing grants | 06-04 | COVERED | Exact allowlist, no REASSIGN OWNED/init-only bootstrap |
| RESEARCH | Owner-specific defaults, narrow scheduler/runtime permissions | 06-04 | COVERED | Actual signup/auth/refresh/buy/sell/replay/upsert and denial tests |
| RESEARCH | One-shot restricted migrator, concurrent0008 timeout/recovery | 06-04,06,07,08 | COVERED | No changed merged migrations or automatic downgrade |
| RESEARCH | CA SAN postgres/private keys/expiry/custody | 06-01-02,06-06,08-01 | COVERED | Future custody choice; runtime CA read-only, server key only PG |
| RESEARCH | HBA hostssl/SCRAM/plaintext rejection/real network scope | 06-06 | COVERED | No invented data subnet, no broad trust fallback |
| RESEARCH | Shared SSLContext at all three engines | 06-05,06 | COVERED | Production CA+hostname verification; dev/test explicit |
| RESEARCH | Actual pg_stat_ssl and bad CA/hostname/plaintext failures | 06-06-01,12-02 | COVERED | Real PG18 handshake and live own-session boolean proof |
| RESEARCH | Stable retained rollback adapter, actual v0.3.1 compatibility | 06-07 | COVERED | Wrapper/overlay survive checkout and subsequent invocation |
| RESEARCH | Separate admin/env/runtime/migration secrets; populated passwords | 06-04,06,12 | COVERED | Env edit alone not password provisioning; auth secrets preserved |
| RESEARCH | Shared lock reuse/deploy gate before mutation | 06-02-02,07-02,12-02 | COVERED | Verify held descriptor/inode; no env-only trust/deadlock |
| RESEARCH | Real nightly timer/status/host unit support | 06-08-01,09-02 | COVERED | Confirm installed systemd directives, actual calendar source |
| RESEARCH | Four new ops tests + existing five deploy regressions | 06-02..08 | COVERED | Named producer tasks; real PG18 + old-image test lifecycle |
| RESEARCH | Serial destructive fixtures/finally/absolute fixed cleanup | 06-03..08 | COVERED | Failure-preserving cleanup, no prod fallback |
| RESEARCH | CI ops in aggregate, preserve money/auth/browser/audits/images | 06-08,10,11 | COVERED | Existing jobs retained, actual current-head CI required |
| RESEARCH | Runtime inventory/config/env/OS/artifact transition | 06-01,06,08,09,12 | COVERED | Scoped approved preflight, no planning private state inspection |
| RESEARCH | Separate fresh push/merge/version/tag/deploy authority | 06-10..12 | COVERED | No fixed new version; Phase05 authority cannot transfer |
| RESEARCH | Real friends and no OTP bypass/implicit email | 06-13-01 | COVERED | Human recipient flow only, explicit consent |
| RESEARCH | ASVS5 L1/STRIDE/security and goal review | Every plan;06-08-03,13-02 | COVERED | High blocks; independent review by orchestrator, inline not mislabeled |
| RESEARCH | Environment availability unprobed | 06-01-03,08-03,09-02 | COVERED | Version/runtime/provenance measured at execution, no fabricated passes |
| RESEARCH | Pre-publication recovery tool availability on old host | 06-03-02,08-01,09-01/02 | COVERED | Immutable complete recovery-only artifact, final manifest/hash and approved transfer/verify/install before first backup/push; no feature checkout/app/security rollout |
| RESEARCH | Same installed recovery paths survive hardening | 06-07-02,12-02 | COVERED | Synthetic before/after proof, immutable recovery hash and actual approved post-rollout recovery |
| RESEARCH | All seven mandatory execution inputs | 06-RESEARCH dispositions;06-01/09/10/11/12/13 checkpoints | COVERED | Each planning disposition explicitly RESOLVED; actual owner choices/authority remain pending with fallback replan paths |
| RESEARCH | Catalog-test analog and fast feedback | 06-03..08;06-VALIDATION | COVERED | test_migrations.py catalog/equality/finally pattern only, no destructive fixtures; fast real guards precede full proofs, actual timing pending |

## Dependency / producer audit

13 sequential waves, one plan per wave, 30 tasks. Each plan depends on its immediate predecessor; file overlap and shared destructive fixtures intentionally serialize. Every automatic command refers to an existing runner or a runner produced in the same task's RED phase / an earlier plan. First execution task prepares the feature branch before source mutation/commits. Planning remains uncommitted on develop under the parent assignment.

- 06-02-01 produces test-backup.sh; 06-02-02 produces all backup commands.
- 06-03-01 produces restore-safety and real ops lifecycle; 06-03-02 adds real fixture cases plus recovery-bundle.sh and old-checkout-only populated0007 installation proof. Verifier uses stdlib+included PG18 client, no feature/app dependencies.
- 06-04-01 adds --roles; 06-04-02 implements role administration.
- 06-05-01 produces test-db-config.sh plus focused pytest; 06-05-02 wires all engines.
- 06-06-01 adds --tls/--all; 06-06-02 delivers matching production routing.
- 06-07-01 produces actual old-image regression; 06-07-02 delivers retained orchestrator and same-installed-recovery proof after hardening. Five existing regression files allow import/call-site edits only; substantive changes require a separate serial plan and ownership revision.
- 06-08-01 reuses the 06-03 producer for final tested-unit bundle and repeats installation rehearsal; 06-09-01 approves its exact SHA/transfer/install, 06-09-02 installs before first live backup and before 06-10 publication. Recovery root /var/lib/birja/recovery is separate from retained deployment root /var/lib/birja/ops.
- 06-08-02 produces CI contract test and required ops job.
- Final-artifact replay interface: 06-03-02 owns test-db-operations.sh --backup-restore [--recovery-bundle <archive>]; 06-07-02 owns test-rollback-db-security.sh [--recovery-bundle <archive>]. Omission retains build-produced defaults; supplied canonical safe regular non-symlink synthetic archives require independent expected hash, manifest/provenance/dependency-closure verification and no repackaging or fallback. Both producers add fast runner-input negatives before full real proofs. 06-08 only invokes these interfaces on the exact final archive, with old-host installation/backup/retrieval/restore and unchanged installed hash/launchers before/after hardening, without target feature checkout.
- Later operations must have explicit approvals and produce evidence; offline checks alone cannot satisfy live acceptance.

## Exclusions

Existing deferred product features, managed infrastructure/Terraform, continuous PITR unless owner rejects nightly recovery window, additional queue/notification services, UI redesign and CI autodeploy are not introduced. This is scope fidelity, not silent deferral of an in-phase decision. Operational policy choices remain required checkpoints.

## Pre-mortem controls

1. False recovery proof: retrieve exact remote snapshot and compare private same-snapshot state; deliberate corruption must fail.
2. Unsafe downgrade/role rollout: prove populated PG18 grants + real old-image TLS adapter before live changes; reject unsupported refs.
3. Approval or evidence leakage: per-boundary current authority; no historical approval inheritance or manual-run nightly substitute.
