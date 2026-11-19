---
phase: 13-create-and-compare-independent-strategies
plan: "17"
status: passed
tested_head: 9527e358bc6953cec7580043703324db194ba396
same_archive_final_ci: true
archive_sha256: 6fb79a45ddcb10725b18fc756e71bd555c827a6e61a5a4a0bd2d183096114b92
stages_passed: 7
completed: 2026-11-19
---

# Phase 13 uninterrupted same-archive recovery proof

After the actual complete security command passed, the same durable one-shot
ran the literal complete recovery command at the identical frozen source:

    python3 deploy/tests/run-portfolio-validation.py --suite recovery

The command exited0 after2792.053910s, approximately46m32s. It ran uninterrupted
from2026-11-18T23:17:54.973412Z through2026-11-19T00:04:27.027183Z. This is an
actual seven-stage pass, not a combination of the earlier interrupted diagnostics.

## Immutable campaign evidence

- HEAD9527e358bc6953cec7580043703324db194ba396;
  tree9e2af2ddb10ddd28ce5df71d445a42bb39d170e0.
- New exclusive canonical archive: /tmp/birja-phase13-proof/recovery.tar.gz.
- Archive219289600bytes; SHA256
  6fb79a45ddcb10725b18fc756e71bd555c827a6e61a5a4a0bd2d183096114b92.
- Raw log: /tmp/birja-phase13-plan17-campaign6-20261118-9527e35/recovery.log;
  SHA2561d08f0b14d96e4e2bb8d9fdca6d1afa863653665961a298b40dc8054b327a896.
- recovery-result.json SHA256
  9b9d4e9e5b08d77c61efe1121885701326632cd8686c3a7a33cee0ca37129456.
- Canonical status.json reports ok=true and all seven stages passed-authenticated.
- Final supervisor receipt ok=true,6174.534104s total; HEAD/all1760tracked
  inputs/preserved archives unchanged and all21resource checks empty.
  Its SHA256 is09909cf5b6874c2304b34d6908db90db3408a3778e53612e17b52b1850e8c9b1.

The canonical directory did not exist at preflight and the actual producer created
the new archive. Its deterministic bytes equal the separately preserved diagnostic
archive because bundled runtime bytes are unchanged; no prior archive was copied
or used as the final command's input. Distinct canonical inode700678 versus
diagnostic inode867057 and actual production/creation metadata are preserved in
fresh-archive-identity.json, SHA256
f29f8b955d66555bb100519165318d7597cb983b87c7b349c89b42001f0b749b.

## Actual stage results

| Ordered stage | Result and measured behavior |
|---|---|
| image-transition | PASS: actual pinned image/collation transition and Redis AOF clone/restart, authentication denial/noeviction controls, untouched-original abort |
| retained-roundtrip | PASS: genuine0008–0014exact rows/schema/sequences/source identity, then complete immutable0017 encrypted cold restore with source destroyed, independent before oracle, quarantine and restricted verified TLS |
| current0020-cold | PASS: current V2 exact cold restore after source-server destruction; independent immutable before oracle, quarantine, current restricted TLS and snapshot equality |
| roles | PASS: populated/fresh parity, ownership/dependency/runtime controls, operatorNOLOGIN and immutable audit denials,63denied operations, current0020restrictedTLSsnapshot |
| tls-upgraded | PASS: actual populated retained upgrade, badCA/hostname/plaintext refusals, isolated credential mounts/renewal and current0020restrictedTLSsnapshot |
| tls-fresh | PASS: real fresh retained/current bootstrap and restricted verified-TLS authority; exact authority equals the upgraded result |
| selected-rollback | PASS: same-installed-archive retained cutovers, supported0008old-image rollback,0014replay/quarantine/currentTLS, unsupported-source rollback refusal preserving revision/data and rollback of a failed attempt to its tested source; current0020old-writer refusal/snapshot |

The runner authenticates archive checksum, current CORE/unit/V2 payload bytes,
fixed retained archives, matrix and every immutable image record before/after
each stage, including failure paths. Only after all operations and the exact
fresh/upgraded authority comparison succeed does it replace operation-returned
markers with passed-authenticated and print:

    same_archive_final_ci=true sha256=6fb79a45ddcb10725b18fc756e71bd555c827a6e61a5a4a0bd2d183096114b92

## Exact state and refusal oracles

The current source-owned inventory includes29tables and22identity sequences.
Comparison retains complete rows/schema/exact identity state, independent cash
and baselines, holdings/basis, immutable financial/history/retry lineage, canonical
names/descriptions, creation journal and initialization provenance. Restore does
not rerun grants, reset cash, discard a zero-book latch or substitute a schema.

Both genuine0017 and current0020 cold paths explicitly reported
source_destroyed=true, immutable_before_oracle=true, quarantine=true, followed
by verified restricted-role application comparisons. Additional actual snapshot
projection hashes include0017cd65bb567a76d26e96a079d2fb0dbebbdc765c3072fd25c465c934ee243dc460
and0020cold f3cb01dbaad4aec00ecfa1c6e8034df89bef541531bf6e829db38d4091c9003e.
These are application projections alongside the complete database oracle, not
substitutes for the independent before-backup canonical state.

The actual retained roundtrip rejected9accounting and17exact-identity corruptions,
13resolution-authority corruptions and10execution-recovery corruptions. Restored
original stock receipts replayed with unchanged hashes, mixed portfolio values
and financial quarantine. Held/cancelled/alias/cursor/epoch evidence survived.
No corruption refusal or ACL equality was waived to achieve a restore.

The rollback stage emitted supported0008rollback/original-fingerprint preservation,
selected0014owner-clone replay and app/scheduler42501quarantine, current TLS,
unsupported rollback refusal with revision0014preserved, and failed-attempt
rollback to the tested source. Its two actual cutover deployments passed in
109.850s and110.622s. A new-schema old consumer remained refused before writes;
the final current0020snapshot comparison passed.

## Source and image identities

Immutable0017 is the complete4b4320b4cc373268a8d598612a563cd5ef199700source,
archive361a0fafbb6f1645d7beb9caeadb8bd46c85abc739d957dce7fc439b64eba248,
not an overlay on HEAD. Other retained source is fixed
c2c7af17e2cb225fe196c5dbf843a65022a69e37; legacy0008uses
46d24c8591de2207cf219429aac0768962bed4c3 and0007uses
0107706617b8bbf9c1a069f3e3ccc9c53b9ab2f7. Current0020uses the tested9527e35
Git source and authenticated current authority payload. The real0007source/image
lane is additionally exercised by selected rollback; retained roundtrip revisions
printed explicitly in the log are0008through0014.

| Private first-use record | Actual immutable image ID | Final record SHA256 |
|---|---|---|
| current0017 | sha256:21497b174560e4a942a2146d020239eefb89797286624847b5204df33cd76f7e | 070a8dfa28171a190c5633cd33b9e570b60940cc8cb0872f954aaece5b6b5ade |
| current0020 | sha256:d164e7db8206ebbcf1f5d1a3f03a33b26d71444e2cf648d319c2c580924f8248 | 277538b7432f62ec38b7e64d862225a8805055c0ec4eeeb23a03809ea05b84f6 |
| retained0017-refusal | sha256:21497b174560e4a942a2146d020239eefb89797286624847b5204df33cd76f7e | 070a8dfa28171a190c5633cd33b9e570b60940cc8cb0872f954aaece5b6b5ade |
| retained | sha256:ecf5a9fdf5855c0d612e7affe417ae03965c6d81c66b7b7f35bfadba4890b480 | 7d5d85c2fff090b0cc009ff4610f6d223702c463f36b2a84e73dea1d9b5f2e5d |
| legacy0008 | sha256:4626b944b63c41420a50418bb7cde3171141fef6e1d95ed8b417dcf09d23b609 | 5e0f9decef65fffc6adbc69902cac0c2367924d779efd9686c8b8b00c3b5b637 |
| legacy0007 | sha256:f1d548d02fe08264ff49e4b7fcdba7e148229c77ee8d8b04435cacaf41f7e3c1 | af275c7a43ed587d193b11bc8fab7012e08202a475934dcc08abdd60dfefa6ef |

These records are beside the canonical archive and contain complete source,
context, config and RootFS bindings. Repeated callers reuse the authenticated ID;
missing/changed IDs refuse rather than rebuilding or accepting equivalent bytes.
All records remained valid through final post-stage authentication. The prior
image-rebuild failure is preserved as failed history; it is not concealed by
this successful new campaign.

## Preservation, cleanup and limits

All21container/network/volume checks across the seven owned synthetic projects
are empty. Bound image artifacts remain available for receipt inspection; this
does not mean all Docker images were deleted. The supervisor recorded no cleanup
ownership escape and no mutation of these preserved archives:

- Phase12: /tmp/birja-phase12-proof/recovery.tar.gz,
  SHAd253bc51b876c7d629ee246ee47bd57274a5d9333e71318e11fcef586cff26be.
- Failed campaign4: /tmp/birja-phase13-proof-campaign4-failed-535a5b7/recovery.tar.gz,
  SHA2d182e0b91488138cf4a9bbe96b2a43e35f3f99e785dfb45543f3c76e0318375.
- Earlier diagnostic: /tmp/birja-backup-test-phase13-tail-diagnostic-312d8c9-20261118/recovery.tar.gz,
  SHA6fb79a45ddcb10725b18fc756e71bd555c827a6e61a5a4a0bd2d183096114b92.

This proof uses synthetic data, local encrypted repositories and owned disposable
resources. It authorizes no provider call, production restore/deployment, push or
merge. Existing issue35 and Phase7live debt remain separately tracked. The final
parent goal/security/validation closeout and Phase14deletion/Phase15full lifecycle
acceptance are separate from this Plan17completion record.
