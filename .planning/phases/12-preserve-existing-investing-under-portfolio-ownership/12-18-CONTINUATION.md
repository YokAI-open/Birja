---
phase: 12
plan: "18"
status: resolved
completed_tasks: 2
next_task: 12-21
updated: 2026-11-16
---

# Plan18 continuation — runtime smoke and retained binding incomplete

**Historical checkpoint, resolved by approved continuation on2026-11-16.**
Task02 is committed at a613193 and verified results at12-18-SUMMARY.md
(ddcb166). The fixture omitted checked_at; adding synthetic observation evidence
made unchanged SQL authority and the actual owned TLS smoke pass. Source/archive/
image bindings and immutable selected refs are complete. The original checkpoint
below is preserved as history, not current status; full serial recovery remains27.

Do not mark18 complete or trust code presence as recovery proof. Task01 is
committed; Task02 changes below are uncommitted and its real smoke fails.
No completion SUMMARY was created. Requirements stay unchecked and plan count
remains18/28 (Plan19 completed before18 by dependency order).

## Completed task

12-18-01 commit **24d9ea9** creates the independent current fixture command and
offline command/mutation contracts. `python3 deploy/tests/test-portfolio-fixture-contracts.py`
passes5 methods with independent cash/baseline/quantity/basis, ~190 evidence
mutations, marker/global cause, sequence, cursor/hash/path/overwrite negatives.
Generated runtime programs compile; offline injection is not a runtime proof.
There are subsequent uncommitted fixture corrections from actual smoke probes.

## Exact current failure

Command (requires local Docker socket, no cloud/production/default configs):

```
python3 deploy/tests/ops-fixtures.py --portfolio-fixture-smoke
```

Full latest synthetic-only log: `/tmp/phase12-18-smoke.log`.
The last run completed actual0014 seed, authenticated0015/16→0017 upgrade,
restricted scheduler split and restricted app crypto execution/replay. It then
failed at generated `current()` line150:

```
payments.append(await process_dividend(db,**target))
  app/services/dividends.py:104 -> _invoke
  app/services/dividends.py:86 -> raise DividendRefused(code) from None
app.services.dividends.DividendRefused: Dividend work is unavailable.
```

The domain exception intentionally hides its code in `str(exc)`; `.code` was
not emitted by this run, so the exact refusal reason is **not yet diagnosed**.
Do not invent the reason or relax authority. Inspect the synthetic entitlement,
source/session/action-health and current-unit evidence, then obtain the safe
domain code if necessary. Application code was not altered in this plan.

The fixture uses genuine legacy NULL marker evidence inserted under actual
Alembic0014, then migrates to0017. It never disables a live guard or fabricates
final DDL. New application version2 writes happen under the final insert guard.

## Probe/repair budget

1. Declared Dockerfile build with `--network=none` could not fetch its Wolfi
   package index. No package version was changed, downloaded or installed.
2. Initial synthetic TLS root prefix did not match existing provisioning guard;
   changed to `/tmp/birja-backup-test-portfolio-*`, retaining guard unchanged.
3. Initial fixture economic key was a readable label, violating UUID shape;
   changed synthetic key to deterministic UUID5.
4. Calendar/reference synthetic admissions inherited action retention quota;
   changed only those non-action fixture quotas to86400. This gets past empty
   session selection. Current run reaches the dividend refusal above.

The executor stopped further fixes after recognizing its exhausted attempt
budget. Parent should diagnose deliberately, not repeat the same command blindly.

## Smoke image deviation and ownership

Parent authorized a bounded **smoke-only** current-source image from cached
immutable runtime
`sha256:e5c153f11416842a3cbd7f34c1fe9c7d3f4dec35df8478fd22fbf023d1737aec`.
The installed distribution set and versions exactly equal the offline locked
runtime export, with no extras. The image contains complete frozen tracked
current app/Alembic (including SQL/DB modules), copied in a new no-install image,
with source label and exact Config/RootFS binding before use. Cached base was
not retagged. This does **not** qualify declared Dockerfile rebuild or scans;
Plan27 still owns them. Builder uses exact local base content ID via legacy
Docker builder so no registry/package lookup occurs.

All smoke resources use project `birja-portfolio-fixture-test`, internal network,
no host ports and tmpfs PostgreSQL. TLS provisioning receives only its private
synthetic root. The failing program is inside try/finally: compose down -v and
label-filtered container/network/volume absence checks ran. No production env,
keys, B2, installed timer/service or real financial rows were read or changed.
The source-bound smoke image may remain as a local build artifact.

## Uncommitted Task02 files

- `deploy/tests/portfolio-execution-fixture.py`: UUID/quota corrections only.
- `deploy/tests/portfolio-retained-sources.json`: fixed reviewed Git/tree/blob/
  Dockerfile/lock/complete archive hashes for v0.5.0, v0.4.0 and v0.3.1.
- `deploy/tests/portfolio-sources.py`: source/schema dispatcher and image/
  Config/RootFS/archive binding helpers; private complete-source image builder.
- `deploy/tests/portfolio-smoke.py`: owned TLS smoke described above.
- `deploy/tests/ops-fixtures.py`: source helper/program dispatch, retained image
  setup and role/TLS client context wiring; new smoke command dispatch.
- `deploy/tests/test-ci-ops.py`: existing dev bootstrap command contract updated
  to actual guarded --migrate sequence; source/schema/blob/commit/image/config/
  RootFS/archive mutation contracts. **18 tests pass.**
- `deploy/verify-restore.py`: optional successor archive field with fixed-hash
  complete retained source payloads. Old archives retain exact old layout.

No Task02 commit exists. No tracked source deletion. Unrelated `.claude/` stays
untouched. No package/lockfile/production change.

## Remaining ordered obligations (not proven)

1. Diagnose actual dividend refusal and complete actual current0017 restricted
   TLS create→exclusive projection→verify→compare smoke. Keep independently
   expected books(25/334/123 cash;9999/1234/7777 baselines;8/4/4 stock units;
   20/30/20 basis) and exact global/owned evidence, not result-derived oracles.
2. Bind every retained child to exact declared revision. Existing call sites
   that verify0014 via runtime_program still need explicit `revision='0014'`;
   defaults are0013. Current0017 consumer must refuse retained revision and
   retained consumer must refuse0017 before app import or writes.
3. Complete retained source/image integration. New builder authenticates full
   pinned v0.5.0 source before image build and records ID/Config/RootFS. Role/TLS
   wiring is drafted but **not exercised**. Pin image use before every child;
   never silently substitute current source or retag mismatched images.
4. Bind retained runtime contexts to the same archived payload/hash throughout
   each stage. Archive now includes fixed complete payloads, but helper currently
   obtains them from authenticated local Git rather than selected archive; wire
   selected archive identity explicitly before child/stage use.
5. `selected-cutover.py` is still unchanged and still creates a synthetic commit
   after overlaying legacy app/source and relocating tooling. Plan18 expressly
   forbids this. Refactor to immutable complete source refs and separately
   authenticated private relocated tooling; do not claim the old harness already
   satisfies the new source identity contract. Preserve distinct0008 legacy/
   old-app rollback lane and0013/14 retained lanes. Exact old Git pins are in
   the reviewed JSON; never rewrite retained programs or current checkout.
6. Strengthen archive/image dispatcher negative contracts where remaining
   wiring changes require them, then rerun prescribed test-ci-ops and fixture
   contracts plus actual smoke. Full encrypted/current+retained same-archive
   TLS/image/rollback serial qualification is Plan27, not completed here.
7. Commit verified Task02, then committed18-SUMMARY with honest results and
   carry-forward, then STATE/ROADMAP19/28 next12-20. Do not mark any whole
   requirement complete merely because this plan's fixture exists.
