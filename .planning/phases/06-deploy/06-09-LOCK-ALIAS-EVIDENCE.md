---
phase: 06-deploy
plan: "09"
status: replacement-reviewed-tested-exact-install-decision-pending
source_commit: 0e47c50
red_commit: ae16a95
tested: 2026-11-09
---

# Fixed production lock and the Ubuntu system alias

This is a bounded Rule 3 correction within ongoing Plan 09. The coordinating
operator supplied the diagnosis: the validated private configuration loads,
but `Job.lock()` rejects `/var/lock/birja-deploy.lock` because Ubuntu's
root-owned `/var/lock` alias resolves it to `/run/lock/birja-deploy.lock`.
The existing root-owned regular lock has mode `0644`. No live inspection
was performed to reproduce that diagnosis during this source correction.

The operator also reports the explicitly approved `548bc494...` replacement
is installed/current and protected configuration is created. Earlier
installation-pending notes are historical. This fix has not changed that
installed release. The new replacement packet and replays are recorded below. No provider operation,
production backup/restore, timer activation or application operation was run.

## Bounded change and security reasoning

Only the exact `/var/lock/birja-deploy.lock` production spelling may depart
from canonical equality, and only when its resolved destination is exactly
`/run/lock/birja-deploy.lock`. The alias itself must be root-owned, a symlink,
and target exactly `/run/lock` or its standard relative spelling `../run/lock`.
`/`, `/var` and `/run` must be real root-owned directories with no group/other
write access. `/run/lock` must be a real root-owned directory; group/other
write access requires its sticky bit, preventing other users from removing
the root-owned lock. Trusted root changes remain outside this local-user
threat boundary. Arbitrary aliases and synthetic noncanonical paths still
fail closed; existing canonical-path behavior is preserved.

The open uses the canonical target with `O_NOFOLLOW`. It does not rename,
unlink, truncate, replace or chmod the shared production lock. The expected
production owner remains UID 0 after canonicalization. Regular-file,
non-writable mode, same-inode `lstat`/`fstat`, nonblocking exclusive `flock`,
inherited exclusive-lock proof in `fdinfo`, and duplicate-close preservation
of the parent's lock remain enforced. The canonical inode is the same one
used by callers opening the fixed `/var/lock` spelling.

## Regression and checks

The regression models only fixed system-path metadata and routes the canonical
open into a private temporary file. Open/flock/inheritance/fdinfo and contention
are real kernel operations. It never opens the real production lock. The happy
path accepts the existing `0644` mode, contends on a second independent open,
reuses an inherited exclusive descriptor, and proves closing the duplicate
leaves the parent's lock held. Negative cases cover wrong resolved target,
alias ownership/target, unsafe parent ownership/writes/symlink, missing sticky
protection, final symlink, unsafe file mode/ownership and synthetic aliases.
Existing real subprocess tests retain coverage of all five shared callers,
wrong inode, unheld/shared/closed descriptors and parent-lock preservation.

| Check | Actual result | Seconds |
|---|---|---:|
| RED lock contracts before source fix | 8 run, exactly 1 expected canonical-guard error | 5.743 |
| GREEN focused lock contracts | 8 passed | 5.532 |
| Full `test-deploy-prerequisites.py` | 18 passed | 8.040 |
| Full `test-backup.sh` | 25 passed | 50.050 |
| Full `test-restore-safety.sh` | 4 passed | 1.451 |
| Ruff check and format check on both changed Python files | Passed | <1 |
| `git diff --check` | Passed | <1 |

The first implementation check identified a fixture inconsistency: its unsafe
mode mutation changed `lstat` metadata while leaving `fstat` metadata safe.
The fixture now models the same unsafe mode on both views of that inode.
No production guard was weakened to accommodate that test.

## Commits and continuation

- `ae16a95`: `test(06-09): Cover trusted system lock alias` (RED).
- `0e47c50`: `fix(06-09): Accept the trusted Ubuntu lock alias` (GREEN).

Independent review and exact-artifact preparation/replays are complete; only
the new checksum-specific installation decision remains. Offline contracts do not establish live backup,
recovery or calendar-timer acceptance. Plan 09/DEPL-02 remain incomplete;
no STATE, ROADMAP, requirement or plan-summary updates belong to this correction.
Unrelated untracked `.claude/` remains untouched. No push or merge occurred.

Self-check: PASSED: both source/test files and this evidence exist, both
referenced commits exist, and neither source commit deletes tracked files.

## Independent review and exact replacement packet

Focused independent06-09-LOCK-ALIAS-REVIEW reports0BLOCKER/0WARNING, with
8independent lock tests passing5.787s. Read-only host metadata confirms all
new alias/directory/file guards pass on DE189274; no live lock was opened or
changed by that metadata check.

Private preserved packet:
`.local/phase-06-handoff/candidate-lock-alias/`

| Binding | Value |
|---|---|
| Archive SHA256 |`d5fe2059b3e984ffcd0dff6b1763dd5a97deddb0be638ca23e49381d35a54401`|
| Archive size |152,156,160bytes|
| Inventory SHA256 |`55069a4ecca727f85f8f55f33f3e4dc9b9e7887a1ff60841b0aa14a7b45d15ea`|
| Trusted verifier SHA256 |`c3fed604fbf14ad9c3df0e43b00874d7761223391eb55c7cb0c45a8cde98b4de`|
| Packet SHA256SUMS hash |`768668792ceaba3db66a000138d491b3b954b1fe5e2e8d8dfbea08cbc42f3225`|

Archive names and every member were compared against approved/installed548...
Only deploy/backup-snapshot.py and embedded SHA256SUMS differ. PostgreSQL image,
restic binary/provenance, verifier, units and every other payload are identical.
No changed application image/dependency/schema; unaffected app/browser/scans
were not repeated. One package took5.232s; generic verification0.767s and copied
standalone verification0.767s passed. Private packet is0700/files0600 and ignored.

| Serial check | Exit | Seconds |
|---|---:|---:|
| Supplied recovery |0|66.973|
| Populated roles |0|30.711|
| Verified TLS |0|51.936|
| Actualv0.3.1 supplied rollback |0|104.093|

All runners checked the same unchanged archive before/after. Recovery and actual
old rollback used explicit --recovery-bundle; roles/TLS used existing bounded
synthetic runners. Immediate command exits/times and logs are retained under
ignored plan09-evidence/lockalias-*. All3fixed projects have0containers/networks/
volumes. Exact productionv0.3.1 source and all4approved running container IDs
remain unchanged. An initial metadata check guessed names for two services;
its false result is retained, and the corrected direct-ID check passes for all4.
No production service change was made to satisfy that check.

## Remaining exact-install checkpoint

Installed548... remains immutable/current. Plan09task02 requires “only the scope
and exact final recovery archive SHA approved by06-09-01”. Present this new
reviewed/tested checksum for supplemental installation approval; no repeated
request for already approved09scope, keys, caps or custody. Trusted install will
create releases/<newSHA>, switch current/stable launchers, verify payloads and
atomically repoint restic to the identical signed binary. Existing private
controls/config must be validated/reused, never overwritten by a setup script
that assumes absence. Then continue fresh inventory/headroom and the approved
backup/retrieval/fixed isolated restore, timer only after actual restore passes.
No actual upload/backup/restore/timer/app deployment has occurred. No09SUMMARY,
DEPL acceptance or whole-phase completion;10/15 plans remain complete.
