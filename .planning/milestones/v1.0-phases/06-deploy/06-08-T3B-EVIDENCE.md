# Plan06-08 task03 T3B — consumer and populated transition evidence

2026-11-08. T3A `b48f80e` remains accepted history; T3B RED is `59819fb`.
T3B implementation and the checks below are ready for the parent's independent
code/security review. This is not Plan08 completion or T3C final acceptance.
No08 SUMMARY, STATE update, publication, provider/production action, private
configuration access, or final recovery artifact was performed.

## Frozen implementation

- All live PostgreSQL/Redis Compose and CI consumers use the exact CGR index
  pins in the checked replacement contract. PostgreSQL explicitly runs its
  entrypoint as70:70 with PGDATA `/var/lib/postgresql/18/docker`; the volume
  mount remains `/var/lib/postgresql`. Running the image's root entrypoint
  would automatically chown an old data directory, so explicit nonroot startup
  is essential. Unconverted UID999 data is rejected. Synthetic tmpfs mounts
  use explicit70:70 or65532:65532 ownership and0750 modes.
- Entrypoints receive only their flags; Redis retains authentication,
  noeviction, AOF and internal networking. Actual native clients, healthchecks,
  process IDs, argv, persistence and authentication denial were exercised.
- Server TLS key/directory group is70, retaining0640/0750 permissions;
  app/scheduler/migrator mounts remain CA-only. Actual TLS negatives passed.
- Retained backend/scheduler/migrator builds use the authenticated retained
  backend Dockerfile with the selected application source context. The backend
  Dockerfile was already mandatory in the retained inventory. The retained
  entrypoint and deployment wrapper now supply its fixed orchestration root.
  The Node base assertion follows the accepted Wolfi toolchain.
- Recovery uses only anonymous, fixed-origin CGR token/manifest URLs, rejects
  redirects, authenticates the exact index/platform/config/layer graph, and
  preserves imported config/platform identity selection, fixed alias and
  pull-never behavior. Registry acquisition alone may expose the index engine
  ID. All exact Compose SHA allowlists are synchronized to
  `6e3a5c1b02d07c785cc69327c0656424af307da7719ed51781ab0d6c5fe3bc9c`.
- The guarded helper runs a bounded read-only collation/index preflight under
  its existing fixed-target validation and operation lock, before privileged
  role SQL. Retained deployment invokes inspection before progressing.
  Unknown/mismatching database or used explicit collation versions, invalid
  public indexes, query errors and unexpected output fail closed. No automatic
  production ownership conversion, REINDEX or catalog refresh was added.
  RUNBOOK documents separately approved clone maintenance, rebuilding indexes
  before refreshing versions, logical recovery and original-engine abort.

## Actual final-source serial results

Logs/status and exact source hashes are retained privately in ignored
`.local/phase-06-handoff/t3b-evidence/`. The final four runners executed
serially after freezing the private tmpfs options and all hash allowlists.

| Runner | Exit | Wall seconds | Measured result |
|---|---:|---:|---|
| `test-db-operations.sh --image-transition` |0|37.494|Populated PostgreSQL physical clone, fresh logical restore and untouched-original abort; Redis AOF clone/restart/abort |
| `test-db-operations.sh --roles` |0|29.322|Populated grants,65 permission denials, actual collation/invalid-index negatives before role creation, services and concurrent0008 |
| `test-db-operations.sh --tls` |0|49.347|App/scheduler/migrator SSL, wrong CA/hostname/plaintext denial, mount isolation, renewal and concurrent0008 |
| `test-db-config.sh` |0|16.426|117 actual focused configuration/connection/service tests |

The transition uses only the fixed `birja-image-transition-test` project,
absolute temporary Compose file, `/dev/null` env, internal network, no ports,
bounded subprocesses and finally cleanup. It rejects existing resources before
entering cleanup. Its fixed original/clone volumes are necessary to preserve
physical data across stopped/recreated engines; no caller volume is accepted.

Actual old Debian PostgreSQL18.6 data owner999/glibc2.41 was populated with
complete application schema, buy/sell/idempotency/session state, and an indexed
explicit en_US locale containing accented/non-Latin values. The old volume was
stopped and fingerprinted. A readonly mount proved new nonroot startup rejects
unconverted data. Only its selected clone was copied/converted to owner70.
The new PostgreSQL18.6/glibc2.44 reported **actual collation drift=true**.
REINDEX preceded both explicit-collation and database REFRESH operations.
Indexed ordering/lookups, complete canonical rows/schema/money/revision and
the existing FK/index/identity/invariant verifier passed. The distro suffix
in `server_version` is excluded from equality, matching the existing verifier;
both actual servers are separately checked as18.6. A fresh logical restore
also matched. The original fingerprint stayed unchanged until restarting its
original Debian engine; original data, locale versions, ordering and UID999
then matched. No old engine reused the rewritten clone.

Old Redis8.8.4 UID999 AOF bytes were likewise cloned read-only, converted only
on the selected clone to65532, and consumed by the pinned Redis8.10.3 candidate.
Native unauthenticated requests failed, authenticated TTL-bearing data and
noeviction/AOF settings matched, and stop/restart preserved the test key.
Original bytes remained unchanged before the original Debian Redis restarted
and read the same key. All actual service ports remained unpublished.

The real role fixture independently rejected synthetic database and used
explicit-collation mismatches, missing versions, and a genuinely invalid
concurrent index before any role was created. PostgreSQL refuses REFRESH from
an intentionally NULL version; only that synthetic negative fixture restores
the deliberately removed value from the actual-version function, after
REINDEX. The production helper remains read-only.

## Retained old-source and provenance proof

Actual immutable v0.3.1 source `0107706617b8bbf9c1a069f3e3ccc9c53b9ab2f7`
built with the reviewed current backend and frontend Dockerfiles in18.751s.
Archived pyproject/uv.lock/package-lock bytes were checked against git archive/
git show and remained unchanged after the builds. All resolved non-project
distribution records, including versions and artifacts, match the current
lock; runtime and non-audit dev requirements remain equal. Whole-file equality
between old and regrouped current project metadata is deliberately replaced.
Actual old runtime runs as1001, has34 production distributions, imports the
native clients, and contains none of pip-audit/pip-api/pip. Actual old frontend
static build passed with the retained toolchain. Logs and original lock hashes
are in `old-*-build.log`, `old-frontend-consumer.log`, `old-build-proof.json`.
The actual retained installer/repeated rollback-routing contract also passed.
Full supplied-artifact old-application rollback remains T3C after review.

Canonical anonymous CGR bytes verified against the exact saved Docker export:
index `f131db66...`, platform `4401cf29...`, config `91c89cf7...`.
Export SHA256 `534822b6b348a5597d65b1a76cb5a194148d40347bd1e820789ade4bb3f711a2`.
Cold import exposed the authenticated platform engine and bound only the fixed
verified-config alias. Registry index/platform bytes and full identities are
retained in `cgr-export-proof.json`; the temporary121MB export was then removed.
No final recovery bundle was packaged or replayed.

## Other verification and retained failures

Final focused contracts: image13, prerequisites15, CI4, safety4 passed.
Existing shell contracts passed14/18/8/11/7 (58 total). Backup25 passed during
T3B, including actual local encrypted restic rotation, before the final mount
option/hash-only normalization. Syntax and `git diff --check` passed. No
unchanged T3A raw scan or full application suite was repeated.

Earlier failures are preserved distinctly: distro version suffix equality;
inspection of a deliberately stopped original without `ps -a`; initial Redis
root-owned tmpfs denying AOF; and the ownership-refusal probe missing ordinary
synthetic init variables. Each was corrected in the affected fixture/consumer.
Pre-final tmpfs logs are labelled separately from final logs. Final source
hashes were rechecked unchanged after all four serial runners.

Zero containers/networks/volumes were verified for `birja-image-transition-test`,
`birja-ops-test`, `birja-restore-check` and `birja-test`. Evidence inventory
SHA256 `a86f1163c2bbca393889dda1632b57373836efb5a62dfde7cc8d80ce240da351`
authenticates all retained files. Parent STATE and unrelated `.claude/` were
preserved. No known stub or unplanned external trust boundary was introduced.

Next boundary: independent parent-arranged code/security review, then T3C's
fresh five-image raw gate, full suites/browser and one final supplied recovery
artifact/actual-old rollback. Historical `cb766040...` remains history only.
