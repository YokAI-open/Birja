---
phase: 06-deploy
reviewed: 2026-11-09T13:31:12Z
review_type: bounded_design_check
contract: .planning/phases/06-deploy/06-12-LOCAL-FIX.md
verdict: PASS
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
implementation_verified: false
---

# Local Rollout Fix Contract Check

## Narrative Findings (AI reviewer)

**PASS — 0 blockers, 0 warnings in the design contract.** The proposed bounded
mechanism addresses readiness CR-01 and WR-01 without requiring a general
routing framework or a recovery CORE/archive change. Implementation and its
evidence still require independent review; the existing source findings are
not closed by this design-only result.

The fixed root-owned JSON binds exactly the two logical volumes to distinct
existing candidates, with originals separately recorded. Protected parent/file
checks, exact schema, local-volume metadata, nonempty converted-data checks,
kernel-validated operation lock and external-only generated overlay provide
the required boundary. The overlay changes only volume names, and every
retained create/recreate path must use it. The contract also requires actual
post-start mount/image/user/network identity checks and rejects missing or
recreated volumes and forged overlays; it supplies no original-write operation.

The proposed narrow `--start-selected-datastores` entrypoint is sufficient for
first secure startup without invoking the existing full-deploy role inspection
prematurely. The retained inventory and manifest must cover its helper, while
the existing clean environment and fixed paths continue to reject ambient
Compose/Docker routing. This fits the actual entrypoint argument gate and
environment construction at `deploy/deploy-entrypoint.sh:158–183`.

WR-01 is addressed by provisioning/checking TLS and retained HBA before that
first candidate start, using the final secure PostgreSQL definition. The
existing provisioner works without a running cluster and consumes the held
lock through `backup.acquire_operation_lock`; that helper already validates
inherited descriptors from the environment. Collation/index maintenance then
precedes the unchanged guarded role inspection/apply and final migration.
No plaintext bootstrap or weakened collation preflight is needed.

The exec-only boundary is correct: the role helper and installed backup do
not create/select volumes. A sole fixed project/service candidate with verified
mounts can satisfy their current Compose exec interface. The contract places
the new assertion before role/deploy operations and immediately before the
explicit cutover backup under the shared lock. It appropriately avoids claiming
that unchanged nightly backup intrinsically enforces a new binding policy
against an actor with Docker authority. This review finds no demonstrated need
to alter independent recovery code, CORE, launchers, units or archive d5fe2059….

The required serial proof is appropriately concrete: real populated candidates,
secure initial startup, unchanged originals, collation/role/migration checks,
forced recreation, actual v0.3.1 app rollback retaining candidate mounts,
Redis AOF/TTL/auth persistence and unchanged installed backup/exact restore
before and after. Negative cases cover the trust and operation boundaries;
fake-host relocation retains actual entrypoint/manifest/lock behavior rather
than mocking security success. Original-engine abort remains restricted to
the pre-accepted-write boundary.

## Scope and remaining gates

Only the contract, prior readiness findings and narrow existing source
interfaces were inspected. No tests, implementation, replay, live/private
access, commit or remote operation occurred. Only this check artifact was
written; parent records and `.claude/` were preserved.

Proceed only with the owner-authorized local implementation and specified
focused evidence. Updated source still needs independent review, a separately
reviewable release candidate, its publication choice and exact-head CI.
Production identities, bindings, custody, capacity, freshness and outage remain
future measured inputs requiring their own authorized preflight and rollout
decision. This design pass grants no publication, merge or deployment authority.
