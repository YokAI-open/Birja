# 06-14 prerequisite scope

This additional serial plan answers the explicit scope gate in06-07-02. It does not reopen completed06-01..06-06. Current evidence: configure-db.sh independently flocks at line74; provision-db-tls.sh does likewise at87; backup Job.lock already has inherited-FD support but needs consistent inode/ownership checks; verify-restore.py restore at641 verifies recovery without durable evidence; roundtrip owns a complete source lifecycle and cannot be reused across hardening unchanged.

Ownership: four existing runtime files, existing ops-fixtures.py and one dedicated stdlib test file. Three serial tasks, approximately40–50% executor context; estimated350–500 changed lines, an estimate rather than a hard cap. No new runtime framework/helper dependency, package installation, Compose-file rewrite, product feature or migration. If implementation requires another subsystem, return its bounded files/contracts estimate before expanding ownership.

| Task | Required inputs | Produces | Consumer |
|---|---|---|---|
|14-01| Existing shared lock path, inherited descriptor and guarded synthetic root | One canonical config-root/operation.lock across synthetic callers; validated acquire_operation_lock; parent-safe duplicate lifetime; fast --locks test producer | Both role/TLS helpers, backup/restore and06-07 retained orchestrator |
|14-02| Exact remote snapshot, private validated config, installed artifact identity, successful full isolated restore | Atomic restore attempt/success, strict explicit recovery-gate, fixed synthetic separate clone |06-07 prechange gate,06-09/12 actual recovery and rollout evidence |
|14-03| Trusted exact archive+separate expected SHA, required deploy-recovery-v2 profile, caller-owned fixed populated source | Pre-side-effect capability check, install-once session and repeated backup/recovery hooks |06-07 before hardening/after roles+TLS+0008/after actual old-image rollback;06-08 final supplied artifact replay |

Lock normalization is explicit: Job.lock currently selects root/state/operation.lock, whereas role/TLS select root/operation.lock. All synthetic callers must use the latter, derived only from the guarded config root; production retains its fixed shared path. One parent-held FD must pass actual role, TLS, backup, restore and gate callers; independently opened attempts cross-contend on the same inode and duplicate closure preserves parent ownership. No arbitrary lock path override is introduced.

Supplied artifact compatibility is explicit: authentic pre14 recovery artifacts lack the new evidence, gate and separate-clone interfaces. Generic verification may still accept their legacy profile, but these specialized hooks require deploy-recovery-v2 through the transferred trusted verifier before runtime/Docker/load/extraction/install/exec. Inventory profile is authenticated by exact archive SHA and checksums, then positive tests prove its interfaces. A complete valid older-profile negative must produce zero Docker/install/packaging/default-builder calls; reject rather than silently rebuild. Both default new packaging and exact supplied current-profile artifacts have positive recovery coverage. This uses existing verify-restore.py ownership.

The source and restore clone must differ during hardening: existing check_running deliberately refuses TLS source mounts. A guarded synthetic --isolated-clone selects only birja-restore-check using the unchanged reviewed recovery Compose. Keep its no-mount isolation; caller retains birja-ops-test. This is a test lifecycle contract, not permission for arbitrary target selection.

Routine status and explicit rollout assurance differ. Ordinary nightly backups retain bounded upload/metadata verification and latest-only replacement; no nightly full restore is required. An explicit rollout selects a snapshot at most26h old, verifies it still exists remotely and requires matching completed full-restore evidence. A newer nightly snapshot can leave ordinary status healthy while the next rollout waits for an explicit restore of its selected fresh snapshot. No retention expansion or historical recovery promise is introduced.

Identity rules: bundle bytes remain immutable throughout the fixture; source schema/release and config are captured per recovery attempt. Bind evidence to the prechange source rather than the future candidate ref, so valid0007 recovery can gate its0008 transition. Changed actual source/config/recovery material requires another backup+restore through the same installed artifact. Exclude volatile quota observation timestamps/counters from stable config identity while revalidating current budgets. Do not accept caller-supplied digest strings as proof, rewrite earlier evidence to match changes or silently substitute another artifact.

## Multi-source coverage audit

This is an additive audit for the prerequisite; the unchanged06-SOURCE-AUDIT and existing plans retain all other Phase06 scope.

| Source | Item | Plan/task | Status / disposition |
|---|---|---|---|
| GOAL | Friends sign up/trade on the live site with safe backups |14-01..03 →07,09,12,13| COVERED: prerequisite enables secure rollout; live acceptance remains in existing plans |
| REQ | DEPL-01 secure deployed operation and rollback |14-01,14-03 →07,12,13| COVERED |
| REQ | DEPL-02 nightly off-server backup and tested restore |14-02,14-03 →08,09,12| COVERED; synthetic proof does not complete requirement |
| RESEARCH | Backup-first, exact retrievable recovery point, no optimistic success |14-02| COVERED |
| RESEARCH | Isolated restricted restore and private equality/financial/schema verification |14-02,14-03| COVERED; existing complete assertions preserved |
| RESEARCH | Role/TLS rollout and rollback preserve trust; shared lock |14-01,14-03 →07| COVERED; one canonical synthetic inode and cross-caller parent-held FD proof |
| RESEARCH | Independent recovery artifact, checksum/provenance/dependency closure |14-02,14-03| COVERED; adjacent existing modules only; specialized capability profile checked before side effects |
| RESEARCH | Remaining systemd/CI/provider/release/live friend work | Existing08..13 | COVERED by unchanged downstream ownership |
| CONTEXT | Phase06 CONTEXT/D-IDs | None exists | Excluded: no fictional decisions |
| CONTEXT | Historical02.1 D-01/02/03/06/07/08 |14 context/authority boundaries; existing downstream plans| COVERED; no domain/TLS/DNS/firewall/deploy-policy changes |
| OPERATIONS | B2 US$0, latest-only verified replacement,26h, custody and resource policy |14-02; existing08/09/12| COVERED; no new retention/full-nightly-download requirement |
| SCOPE GATE |06-07-02 wider prerequisite changes need separate serial ownership |14-01..03| COVERED;07 retains its deploy/entrypoint/overlay/smoke/rollback files |

No prerequisite item is deferred or silently dropped. Actual retained wrapper integration and three-stage real old-image acceptance belong to06-07; final units/artifact packaging and CI to06-08; provider/private/live actions retain their explicit existing checkpoints. No production read, provider request, test execution, tool acquisition, branch switch, commit, push, PR, merge or deployment was performed in this planning assignment.
