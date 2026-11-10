# Local rollout correction evidence

Updated 2026-11-10. Owner-authorized local work on release-0.4.0; PR27 remains
published at 16623a8. No new push, production deployment or recovery installation.

## Source and review

Initial RED9369351/GREENd876806 implements protected fixed binding, external
candidate routing, actual identity checks and TLS-first limited startup.
Independent initial review closed short/full Docker identity defect through
72756b2/df81abe. Real fixture evidence then required these bounded corrections:

- Legacy and offset-bearing Redis AOF records:3e3c077/39e8dee.
- Retained nonsecret HBA readable by PostgreSQL UID70:b5c7f49/efabec1.
- Explicit Docker containerd pinned index/platform descriptor:ecfd42a/525661e.
- Actual startoffset-only incremental AOF record:e042c9c/9e50f01.
- Final manifest record without newline must still verify its file:
  c3c855d/ce55207; missing, symlinked and wrong-owner references fail.

Independent follow-up source review reports0 active blockers/warnings in
06-12-LOCAL-FINAL-REVIEW. Redis GET, TTL and unauthenticated rejection now run
after force-recreate, current deployment and actual old-app rollback.
The final real fixture and its CI contract are committed at b6b717c.

The proposal's old install-after-start ordering was replaced by final-material
preparation before fresh proof. Follow-up documentation review found an
incorrect guarantee that an old snapshot survives a later isolated-restore
failure. Corrected: upload/repository verification precedes one-copy rotation;
a later restore failure blocks cutover, without an old-snapshot guarantee.
No recovery behavior was changed to resolve that documentation finding.

## Real supplied-archive cutover

Run12 passed:254.099s before final cleanup. Private raw evidence is ignored at
.local/phase-06-handoff/local-rollout-evidence/cutover-12.log. Archive unchanged:
`d5fe2059b3e984ffcd0dff6b1763dd5a97deddb0be638ca23e49381d35a54401`.

| Actual stage | Result |
|---|---|
| Populated old PG0007 and Redis AOF, final protected material, continuous lock | Pass |
| Fresh backup / exact isolated restore before first startup |6.748s /9.350s |
| Real retained TLS-first candidate-only startup, actual0007 equality |11.432s |
| Guarded role setup and forced recreation on selected volumes | Pass |
| Full retained current deployment and separate0008 migration |120.824s |
| Same installed archive backup / exact restore after deploy |8.986s /9.030s |
| Real retained rollback to actual v0.3.1 app with0008 retained |28.419s |
| Same installed archive backup / exact restore after rollback |8.730s /8.983s |
| Redis exact value, positive TTL, NOAUTH after all three milestones | Pass |
| Original stopped volume fingerprints and retained source hashes | Unchanged |
| Owned fixture containers/networks/volumes removed in finally | Pass |

This run used9e50f01 plus the reviewed fixture changes. Final parser hardening
and fixture were subsequently committed; final serial compatibility proof of
b6b717c also passed, as recorded below.

Earlier failures are retained in private run logs, not counted as acceptance.
They exposed real supported-boundary issues above; fixture-only fixes use a
private HOME/TMPDIR and one-pass fixed-path relocation. Production entrypoint
is not given caller-selected paths or a TMPDIR override.

## Final committed serial compatibility — b6b717c

Both producers exited0. Recovery archive bytes and payload remained unchanged.

- `test-db-operations.sh --all`: recovery73.141s, roles32.694s with65 denied
  operations, TLS32.389s including bad CA/hostname/plaintext, credential mount
  isolation and renewal. Default archive SHA equals d5fe2059 above.
- `test-rollback-db-security.sh --recovery-bundle <private-test-copy>`:
  retained installer/legacy checkout and existing actual-old rollback99.487s
  passed, followed by the new full retained cutover239.459s.
- Final cutover: startup10.787s, current deployment110.010s, old-app
  rollback26.169s. Pre-start backup/restore6.773s/9.226s; post-deploy
  8.521s/9.073s; post-rollback8.469s/8.801s. Actual0008, selected identities,
  Redis GET/TTL/NOAUTH, unchanged original fingerprints and retained hashes pass.
- Both fixed synthetic projects are independently confirmed empty after finally
  cleanup. The exact private temporary archive copy was removed. Preserved
  handoff archive remains unchanged.

Private raw logs: compatibility-db-all.log and
compatibility-rollback-supplied-final.log under the ignored evidence directory.
The first supplied-run invocation rejected its repository path before Docker;
its private hash-verified /tmp copy passed the unchanged synthetic-path guard.
No guard was weakened to resolve this test-input error.

## Focused verification

- Final binding13 passed1.536s; prerequisite19 passed9.490s; CI contracts7 passed0.105s.
- Reexec14/14, rollback-target18/18, app-services8/8 pass.
- Actual retained installer / managed legacy checkout self-test passes.
- Backup25 passed50.764s; restore-safety4 passed1.385s, including real local
  encrypted restic rotation with no provider requests.
- New helper, binding contracts and cutover fixture Ruff lint/format, Python
  compile, changed shell syntax and diff whitespace checks pass.
- Full ops-fixtures.py Ruff reports three pre-existing findings (one embedded
  exec and two subprocess check flags); changed functions introduce none.
  An exact Ruff finding comparison against16623a8 confirms the same three
  existing codes/messages. Unrelated broad formatting changes were removed.

## Limits and remaining boundary

The fixture uses synthetic data and fixed owned Docker projects. Host nginx
is replaced by a private TLS origin; real backend health is queried. Fixed
host paths are relocated and launcher children cannot read the source checkout
under Landlock. Existing separate serial TLS tests supply CA/hostname/plaintext
negatives; this is not evidence of current production state.

No app, dependencies, image pins, base Compose, recovery CORE, units, installed
archive or provider settings changed. No production volume names, disk space,
collation scope, source SHA or maintenance window are invented. Local source readiness and final compatibility pass. Updated PR27
publication still requires owner approval and its own exact-head CI; main
merge/tag/back-merge/deployment remain separate. Plan09 nightly observation is
deferred. Phase stays11/15, overall65/69=94%; no09/11SUMMARY or DEPL completion.
