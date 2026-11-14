---
phase: 06-deploy
reviewed: 2026-11-09T13:12:47Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - .planning/phases/06-deploy/06-12-ROLLOUT-PROPOSAL.md
  - docker-compose.prod.yml
  - deploy/db-security.compose.yml
  - deploy/deploy-entrypoint.sh
  - deploy/deploy.sh
  - deploy/configure-db.sh
  - deploy/provision-db-tls.sh
  - deploy/backup-snapshot.py
  - deploy/RUNBOOK.md
findings:
  critical: 1
  warning: 1
  info: 0
  total: 2
status: issues_found
rollout_readiness: not_ready
release_publication: separate_gate
---

# Plan 06-12: Bounded Rollout Readiness Review

## Narrative Findings (AI reviewer)

Production rollout is not ready for an executable approval proposal. The
selected-clone routing gap is confirmed, with the helper nuance below. This
does not invalidate the reviewed release candidate or prevent separate release
publication decisions after exact-head CI and the required owner approval.

### CR-01 — BLOCKER: Retained datastore creation cannot select preserved-clone volumes

**Files:** `/home/YokaiExchange/docker-compose.prod.yml:14`, `:53`, `:74`;
`/home/YokaiExchange/deploy/deploy.sh:56`, `:391`;
`/home/YokaiExchange/deploy/deploy-entrypoint.sh:158`, `:164`.

**Issue:** Production Compose declares implicit project volumes `pgdata` and
`redisdata`; service mounts use those exact logical names. The retained deploy
passes only its immutable base and security overlay to project `birja-prod`.
The overlay has no datastore volume changes. Its entrypoint accepts no
volume/Compose selector and reconstructs a fixed environment without ambient
Compose overrides. A later retained `compose up ... postgres redis` therefore
has no supported way to use separately named candidate volumes while keeping
the original named volumes untouched. Manually starting a candidate under a
different mapping does not establish persistence across deploy or rollback.
The runbook requires preserved originals and selected clones at lines 376–395
but supplies no corresponding production selection interface.

**Minimal required mechanism:** Independently review one durable, protected
binding from the two logical datastore volumes to the explicitly approved
existing candidate names, consumed by every retained command that can create
or recreate these services, including rollback. Validate fixed project/service,
distinct original/candidate identities, no implicit empty-volume creation and
actual mounted volume identities before transitions. Keep bindings outside
untrusted caller overrides and preserve immutable bundle verification. A
separately specified logical-restore/cutover alternative is also possible;
it still needs an explicit persistent binding and untouched-original abort.
No implementation or new plan is proposed by this review.

**Helper nuance:** The proposal overstates the need for independent volume
selectors in the current role and backup helpers. `configure-db.sh:98–119`
uses its fixed Compose definition only for `exec ... postgres`; production
backup similarly constructs `compose ... exec -T postgres` at
`backup-snapshot.py:554–570`. They do not create/recreate a datastore or choose
its backing volume. They can reach the selected candidate if it is the sole
container under the required project/service identity. The reviewed cutover
must prove that container identity and mount mapping before SQL or backup;
the absence of helper volume flags alone is not an additional creation-routing
defect or proof that the installed recovery bundle must change.

### WR-01 — WARNING: Candidate startup precedes its unresolved TLS prerequisites

**Files:** `/home/YokaiExchange/.planning/phases/06-deploy/06-12-ROLLOUT-PROPOSAL.md:131`,
`:146`; `/home/YokaiExchange/docker-compose.prod.yml:43`, `:54`.

**Issue:** Proposal step 4 starts candidate PostgreSQL; step 6 provisions TLS
and describes mounting its server material. Current production Compose already
enables SSL and requires the server certificate/key/HBA mounts at startup.
No measured existing TLS installation or distinct candidate bootstrap
definition is supplied. The new routing mechanism alone does not resolve
these startup prerequisites. In the absent-material case the candidate cannot
start under the current final Compose, so the stated sequence cannot yet
become a run sheet.

**Fix:** Before requesting rollout approval, bind the selected retained helper
source and validate/provision the required TLS/HBA material before candidate
startup, or explicitly review an isolated maintenance bootstrap definition
and its transition to the final secure definition. Keep role SQL after the
collation/index checks, preserve the exact lock/custody gates, and verify final
mounted files and secure startup before writers resume. Do not infer that TLS
currently exists or introduce an ambient plaintext override.

## Confirmed boundaries and unresolved measurements

The proposal correctly separates the recovery archive from the retained
deployment MANIFEST, preserves original volumes/images for a pre-write abort,
orders reindexing before collation version refresh, and distinguishes engine
abort from application rollback after accepted writes. The exact-source
installer and deploy ref shapes match their source allowlists; `v0.4.0` is
not currently an accepted deploy ref. Existing inherited-lock validation reads
`BIRJA_BACKUP_LOCK_FD` from the environment, so the stated shared-lock approach
does not itself require bypassing or disabling locks.

Actual production volume names/mounts, selected candidate names, TLS state,
capacity, engine/collation/AOF state, current backup freshness, final main SHA,
retained deployment MANIFEST and outage duration remain unmeasured here.
Documented defaults and historical snapshots are not measured selectors.
Resolve the routing and startup interfaces before collecting an authorized
bounded production preflight or presenting executable maintenance commands.

This was source/document inspection only. No tests, replays, live/private
reads, network calls, source edits, branch operations, commits or publication
were performed. Only this artifact was written; the proposal and unrelated
`.claude/` were preserved. Release PR27 publication/CI inspection remains its
own authorized boundary; main merge, tag, back-merge and deployment authority
were not inferred.
