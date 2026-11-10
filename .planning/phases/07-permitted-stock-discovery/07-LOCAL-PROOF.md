---
phase: 07-permitted-stock-discovery
status: local-gates-passed
date: 2026-11-10
live_activation: disabled
provider_permission: pending-plan-14
owner_ui_acceptance: pending-plan-14
---

# Phase7 local proof

These are actual isolated synthetic checks, not provider permission or production
acceptance. No push, GitHub run, provider/private API/B2 access, production config
read, host installation, timer change or deployment was performed. Production
remains v0.4.0/source46d24c8/schema0008. Stock execution remains disabled through
Phase8 and live collection defaults off.

## Reviewed source and dependencies

Backend runtime corrections are committed in7fb4bed; UI correction670b221 and
final helper/fixture correction214560b preserve that backend source. Subsequent
compatibility changes are test-fixture-only and committedf6a556e. Independent reports retain original findings and each actual
re-review disposition instead of overwriting the initial failures.

| Input | SHA256 |
|---|---|
| backend/uv.lock | 81c8421f541a5a37966bfe5a87f0e642301911ce5ed345b0c49d37a655f73e69 |
| backend/pyproject.toml | 3071054462750bd4297f973d33d685b15d732ba2e3ee2b380c703dadc9db62fd |
| frontend/package-lock.json | 66a61bfba12247c9e11eed0346c07e221105de6c05d23646900681dc51ed51ae |
| backend/Dockerfile | e7fc0740fdf1423f368d688181e582285f967b30c501a8ce99c73b7951a12cf5 |
| frontend/Dockerfile | bca57d17bdcd1e21bac189ecfb3d6051af5524e2f0f834f9399278265bab5be2 |

Only the eight owner-approved calendar packages were added in07-08. Current
image/legacy compatibility contracts retain the exact original distribution
inventory digest and separately fingerprint the eight additions' complete
version/source/sdist/wheel metadata as
e46b91fbe9b2d6fc9de6f974163816c14714b70b47b7751cd5bbf8bb24fadbd7.
Unsigned source, absent wheel attestation and unverified legitimacy protocol
remain the limitations explicitly accepted at07-07; tests do not replace them.

## Required application gates

| Gate | Actual result |
|---|---|
| Full backend pytest/coverage | 969passed,54.59s;99.68% overall |
| All original15 plus new6 critical modules | 1221statements/304branches,100%; no omitted paths or lowered threshold |
| Backend Ruff lint/format and mypy | Pass;124formatted files,60source files typed |
| pip-audit | No known vulnerabilities |
| Full frontend Vitest | 310passed across28files,20.90s |
| Frontend coverage | Statements97.77%,branches95.59%,functions99.12%,lines98.91% |
| ESLint/types/Prettier | Pass |
| npm audit --audit-level=high | Pass;0HIGH/CRITICAL;2low/13moderate existing development advisories recorded, no force-upgrade |
| Actual full Chromium suite | 20passed90.2s;1expected deployed-site CSP skip because E2E_PROD_URL is absent |
| Nonroot actual hardened test-builder | 158admission/session/API tests passed7.04s |
| Actual runtime, network none/read-only/nonroot | Calendar/NumPy/pandas import and genuine early-close/session decisions passed |
| CI/image offline contracts | 10CI and13image tests passed; six jobs/ci-pass and strict scanner policies preserved |

Backend final receipt:/tmp/birja-phase07-plan13-backend-final2.log; critical
receipt:/tmp/birja-phase07-plan13-critical-final.log; frontend final receipt:
/tmp/birja-phase07-plan13-frontend-final.log. Native test receipt is
/tmp/birja-phase07-plan13-native.log. Upstream pandas3.1 emits deprecation
warnings; nonroot pytest cannot write its source-directory cache. Neither warning
was suppressed or counted as a failed security gate.

Final browser receipt:/tmp/birja-phase07-e2e-7ypm63gm/all-browser.log, with harness
receipt /tmp/birja-phase07-plan13-browser-final2.log. Dedicated project
birja-phase07-e2e-test uses temporary synthetic env, fake crypto, console email,
stock collection off, tmpfs PG/Redis, no production resources and a loopback-only
random frontend port. Cleanup confirms no containers, volumes or networks remain.
The full suite includes the eleven stock journeys, post-success keyboard-focus
assertion, responsive320/375/768/1280, permission expiry/revocation,120second
boundary, unknown/previous-session/early-close/DST and independent crypto flows.

## Actual five-image gate

Current backend runtime/test-builder were rebuilt from the locked source after
the admission corrections. Unchanged Node toolchain and exact pinned datastores
were scanned again. Actual deploy/scan-images.py used pinned Trivy0.76.1,
HIGH/CRITICAL including unfixed, no ignores/VEX/skip/continue-on-error. All five
actual targets exited0 with zero qualifying findings. Evidence is
/tmp/birja-phase07-plan13-scans-final/status.json and its per-image JSON/logs.

| Target | Actual Docker identity | Saved configuration digest |
|---|---|---|
| Runtime | 6f17581c24f9442fb83f5a1fdeeed3741eadf87f660168451bd5550bd81c471f | 14d96e385a8cbdebc6089c0dfd7f64b177112e0117436eb9be14425a0f4273fc |
| Test-builder | 1189c36f9e278b23e2455be753c696a9aa563bdda4b584f086b59f674748a574 | 4f9a96f93c7489274a4b5a41a29c8a6a471857b04d802b1faf0c62b8ee5dc6dc |
| Node | e44078913d853de420bdd91a255281140c0265c93c18f5675e5088416d6ff16e | e48ee6f317d450011ead650f051498593a54338b3e41f901e8e4f4481c317c34 |
| PostgreSQL pinned registry digest | f131db66371391e404c80cef7dd40f31b1b54eb264a6cb032925d9a3859f93f4 | 91c89cf7f1f18cc4d96fcb5b9e2438108569c1dfcd5aa7286f9cad7d75742ed4 |
| Redis pinned registry digest | 26bb2dd4412f902f3decd44fba5dfaef4360d97004d44f6cff7f28d6aba19c48 | 20fd1c1d7997a7bd67b6f607c79b056a7143c5472910b7e586ebcf9a736486e6 |

Each value is SHA256. Docker engine identities and saved image configuration
digests differ under the containerd store; both are retained, not conflated.

## Serial recovery, roles and compatibility

Actual current-source test-db-operations --all passed. Same installed encrypted
recovery archive SHA256155743d84c3ae2d7ed765dc21245d3050e73f15afd30ce90d0abc47cb969bc9a
backs up/retrieves/restores revisions0007/0008/0009/0010. Exact rows/schema/money/
generations/identities compare, generated sequences advance and corruptions are
refused; authority is never renewed or repaired. Full retained recovery portion
took165.932s. Source checkouts/config/credentials/Compose/mount identities stay
unchanged; feature source is denied to retained recovery children.

Roles portion passed65denied operations in71.102s, including original financial,
DDL/membership and new authority/sequence denials. Both populated0008 migrator
upgrade without grant repair and fresh successor bootstrap evaluate persisted
derived rows/current admission through actual app reads, scheduler writes and
migrator-only review updates over verified TLS. They call genuine session_at,
not a copied predicate: forged generation, replacement, expired authoritative
review with fresh rows refuse; matching refresh succeeds without renewing review.
TLS lanes passed56.584s/68.122s with bad CA/hostname/plaintext rejection and
credential/mount isolation. --roles independently passed both lanes too. Receipt:
/tmp/birja-phase07-plan13-all.log and /tmp/birja-phase07-plan13-roles-final.log.

Backup25tests passed56.672s; restore-safety6tests passed1.529s; DB configuration
121tests passed13.30s. These run serially and the DB configuration runner owns
its disposable birja-test stack lifecycle. Final backend/native checks followed
recreation of that isolated stack, never production/dev databases.

Actual image transition passed43.204s: untouched UID999/glibc2.41 originals,
candidate UID70/glibc2.44, actual collation drift, reindex-before-refresh, exact
logical restore and Redis UID65532 AOF/auth/noeviction/restart/TTL. Unrelated
collation probes live in a separate synthetic schema so the strict public schema
allowlist is unchanged. Receipt:/tmp/birja-phase07-plan13-image-transition-final.log.

Legacy0008 selected retained deployment/rollback passed296.329s, including actual
force recreation, old application rollback, exact same-archive pre/post recovery,
original volume fingerprints and immutable retained tooling; cleanup completed.
Receipt:/tmp/birja-phase07-plan13-rollback-final.log. Its explicit fixture
separation uses immutable v0.4.0 app/Alembic for the0008 lane and actual v0.3.1
rollback with current retained tooling. Successor0010 runtime/recovery is proven
by --all/native, never by running old v0.3.1 on0010. The first legacy TLS/services
lane also passed; its final source-label-only rerun binds the mounted app to
v0.4.0 while separately checking original ROOTHEAD/tool/archive identities.
That corrected first lane passed107.422s with HEADf6a556e stable throughout;
receipt:/tmp/birja-phase07-plan13-legacy-label-final.log. Its actual source label
is46d24c8591de2207cf219429aac0768962bed4c3, distinct from the current tool source
and recovery archive. Two pre-start/interrupted preparatory attempts are excluded
from this final serial receipt; final fixed-project cleanup was verified empty.

## Independent review and corrected failures

07-REVIEW.md preserves three initial blockers and two test-reliability warnings,
all corrected and independently re-reviewed: trusted configured scope reaches
every nested calendar/provider check; current retention is required and exact
collected_at retention cutoff shortens the existing client deadline; configured
budget bounds the entire cycle including post-fetch write rollback; quote fixture
uses real UTC and scheduler fixture selects a verified XNYS date, including
holiday/weekend regressions. A separate HTTP-boundary regression also fixes huge
Decimal exponent conversion escaping the sanitized adapter error.

07-SECURITY.md retains initial retention exposure/cache gaps and corrective
re-review:47/47 unique local mitigation IDs closed,49plan obligations verified.
This is declared-mitigation verification, not full ASVS certification or actual
provider acceptance. 07-UI-REVIEW.md preserves initial22/24 and current24/24:
twenty detailed loading records reserve space; successful retry focuses the stock
heading after its button disappears. Actual prior synthetic screenshots were
inspected; no new screenshots or owner acceptance were fabricated.

Real failing receipts are retained: initial stale route allowlist/critical list;
numeric exponent regression; seven independent-review RED cases; two UI RED
cases; historical seed incompatibility after rebuilding current image; legacy
inventory assertions predating approved calendar additions; unrelated probe
rejected by strict recovery schema. The isolated browser harness first needed
Redis tmpfs ownership; two earlier full runs found sign-in readiness races. The
helper now waits for the actual authenticated Markets heading before callers
navigate. An incorrect intermediate /markets URL assumption was corrected to
the actual root route. Final full browser run passed without retry.

One overlapping focused/full backend invocation was interrupted and excluded
from final evidence; final969test and native runs were serial. One auto-review
scope rejection for the owned synthetic transition fixture was resolved by
explicit scope clarification and separate edit/test actions; no bypass occurred.

## Concrete activation handoff (Plan14, not satisfied here)

Review actual access, audience/account/server/feed, collection/display/derived/
retention rights, fields, attribution, quotas and expiry separately for each
product. Selecting IEX or owning credentials establishes no multi-user permission.
Confirm storage rights cover actual DB and encrypted recovery-copy lifetimes, or
an explicitly approved and verified privileged cleanup process already satisfies
every storage deadline. Display redaction alone does not establish storage rights;
no DELETE privilege/service or financial evidence deletion was added.

Only after the explicit Plan14 checkpoint may bounded private verification measure
all20symbol identities, real quote source times/freshness, correct scope/quota and
calendar/status/action access. Missing evidence keeps stocks disabled. Record
sanitized booleans/counts/generation/times; never keys, raw terms/provider payloads
or user data. Owner UI acceptance remains separate. Source changes require
affected proof/re-review. Production tooling installation/custody/migration and
deployment remain later separately approved work; local plans do not authorize them.
