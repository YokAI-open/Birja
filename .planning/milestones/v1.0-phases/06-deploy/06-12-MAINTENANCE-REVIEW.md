---
phase: 06-deploy
reviewed: 2026-11-10T10:28:49Z
depth: standard
review_type: bounded-maintenance-packet
source: 46d24c8591de2207cf219429aac0768962bed4c3
retained_manifest: 70e568a8c0f9953926e40de4ed79ec25272b3cdd777e474b3967a09849edb0b2
recovery_archive: d5fe2059b3e984ffcd0dff6b1763dd5a97deddb0be638ca23e49381d35a54401
files_reviewed: 1
files_reviewed_list:
  - .planning/phases/06-deploy/06-12-MAINTENANCE.md
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
rollout_authority: pending_explicit_owner_approval
---

# Plan12 maintenance packet review

## Narrative Findings (AI reviewer)

No active BLOCKER or WARNING findings in the bounded maintenance packet.
The sequence is consistent with the reviewed retained interfaces, Plan12 and
recorded host preparation. The owner's confirmed immediate window, sole Birja
writer inventory and off-server custody are correctly distinguished from
deployment approval.

### Scope, source and lock boundaries

The packet binds the proposed work to one host/project, released main source,
retained deployment MANIFEST, unchanged independent recovery archive and four
explicit original/candidate volumes. Actual metadata, mounts, sole consumers,
images, compatibility and empty candidates must be revalidated; historical
measurements do not substitute for these execution guards.

The continuous operation lock and inherited descriptors match the existing
kernel-backed validator and supported entrypoints. The retained deploy launcher
adopts that lock before executing the clean environment with fd9. No arbitrary
Compose source, recovery override, executable config, wildcard target or
security-gate bypass is proposed.

### Recovery and candidate mutation ordering

Writers stop while old datastores remain available. Final protected role URLs,
private TLS archive, bindings, retained MANIFEST and recovery-file membership
are prepared before the fresh backup/exact isolated restore. The old actual
deploy-log SHA remains the recovery source identity until successful deployment.
The packet accurately states that repository verification precedes rotation,
and a later isolated-restore failure cannot promise retention of the preceding
snapshot.

Shutdown, stopped fingerprints and read-only original copying follow successful
proof. Ownership conversion, REINDEX and subsequent collation version refresh
are confined to candidates. The narrow startup admits completed exact proof,
verifies selected candidate identities and requires revision0007 equality before
role SQL, migration or application writers. Unknown collation/index state stops
the sequence; it is not silently refreshed or repaired.

Role inspection/application follows compatibility maintenance. The final packet
explicitly requires a second fresh backup/exact restore after role transition
and before normal deployment, preserving the actual old live release identity.
Normal deployment retains strict recovery admission and the separate0008 migrator. Post-rollout
recovery uses the same installed independent tools against final configuration,
source and revision; failure leaves acceptance pending. Refreshing the private
off-server configuration export is explicitly included.

### Failure and write boundary

Before original shutdown, recovery/preparation failure can restore configuration
and restart only the verified old writer containers. Before candidate application
startup, the stated abort uses untouched originals with measured old images and
original configuration, without converting candidate data back to old libc.

The packet treats application startup as potential accepted writes immediately,
including startup followed by failed health checks. After that boundary it
prohibits automatic original-volume fallback. Secure application rollback keeps
current candidates, roles, TLS and schema0008 and still requires fresh recovery
admission. It does not authorize automatic schema downgrade, real-data restore,
invalid-index repair or image/tool changes to work around failure.

## Review limits and remaining checkpoint

This was a read-only packet and call-boundary review using project instructions,
Plan12, recorded host preparation and the relevant retained deployment, recovery,
quota, binding, role and previously reviewed synthetic-proof source. No production
configuration/provider access, commands, tests, implementation changes, commits
or publication were performed. Exact live identities, capacity, image availability,
fingerprints and recovery freshness were not independently measured here.

The packet is ready to present for explicit approval of its exact maintenance,
recovery, copy, candidate collation/roles, restart/deployment, smoke and final
recovery scope, including its abort boundary. A clean packet review supplies no
rollout authority. Nightly observation, Plan13 friend acceptance and whole-phase
completion remain separate outstanding evidence.
