# Phase9 local proof

## Current disposition

Plans01–14 complete locally. Final coverage/CI mirror, actual restricted TLS
and recovered-service consumers, backend/security/image/audit/review gates all
pass. Plan15 actual new-UI owner acceptance/native200% remains pending. No
production/provider/B2/timer/publication operation is authorized or performed.

## Final evidence (authoritative; 2026-11-12)

Owner review ZIP:/tmp/birja-phase09-ui-review.zip,4931242bytes, SHA256
0368d66604f8b33ad35294f9c18c7a9837d0f91dd79e3a765c5879d671e816b2.
Source969c301; MANIFEST.json records25actual screenshots/five read-only pages
and their assets. Current UI source hashes and archive CORE/unit equality are
verified. Final cleanup proof:/tmp/birja-phase09-owned-cleanup-final.json.

| Gate | Actual result | Log/artifact |
| --- | --- | --- |
| Backend on patched18.7 |2086passed85warnings239.75s;99.86%overall | /tmp/birja-phase09-final-backend-pg187.log |
| Exact39critical modules |3904statements1242branches100%,zero missing | /tmp/birja-phase09-final-critical-pg187.log |
| Frontend |590tests33files;98.41%statements94.40%branches; full lint/types/Prettier/build pass | /tmp/birja-phase09-final-frontend-reviewed.log; final-browser-source-{lint,types}.log; final-frontend-build.log |
| Dependency audits | pip-audit none; npm audithigh exits0,2low13moderate dev advisories remain | /tmp/birja-phase09-final-{pipaudit,npmaudit}.log |
| Strict five-image scan | All5zeroHIGH/CRITICAL, includingunfixed; patched18.7/libxslt-r7 | /tmp/birja-phase09-patched-scans/status.json |
| Full real browser |45pass1expectedCSPskip,retries0,234.6s | /tmp/birja-phase09-browser-69b6wynx/browser-all.log |
| Final changed stock browser |14pass97.5s,25PNGs,5script-free DOM/CSS/font files | /tmp/birja-phase09-browser-2kg93fsb/browser-stocks.log |
| Offline review integrity |5pages1440/375/640,actualAAPL/BTC,zero script/form/iframe/link elements or external HTTP requests | /tmp/birja-phase09-offline-ui-check.log |
| Compatible archive all lanes |812.835s; retained0007–0013,roles,bothTLS all pass | /tmp/birja-phase09-final-retained-all.log |
| Exact retained rows/schema/identities |378.151s; unchanged source; original receipt3429b3b986e78525a6da0cc866f36034a801d82cd8b768cd59ed71f402f1b81a matches restore | same log |
| Restricted roles |63denials and12input/lock refusals; fresh/upgraded parity | same log |
| Populated / fresh TLS |115.005s /114.264s; actual quote/execute/replay/context/portfolio/status/split/cutoff/crypto consumers | same log |
| Physical image transition |38.802s; copied candidate, logical restore, original fingerprint/abort preserved | /tmp/birja-phase09-final-image-transition.log |
| Actual retained cutover/rollback |357.031s; old18.6 pre-start and new18.7 post-start recovery with exact supplied archive, recreated services and old-app rollback, original fingerprints unchanged | /tmp/birja-phase09-final-rollback-security.log |
| Standalone SQL contracts |13tests49.886s,zero skips; explicit legacy/accounting/resolution revisions | /tmp/birja-phase09-final-stock-sql-contracts.log |
| Nonroot native test-builder |5pass1.51s; actual PG/Redis,read-only,user1001 | /tmp/birja-phase09-final-native-builder.log |
| Network-free runtime | UID1001/nativeXNYS calendar/actual stock imports/exact Decimal Buymax pass | /tmp/birja-phase09-final-runtime-smoke.log |
| Operational/static contracts |26backup,13image,10CI; restore/config/bindings/deploy/smoke/nginx contracts and full backend static pass | final offline logs; dump-compat-green-full.log |

The final exact public tool archive is recovery-compatible.tar in
/tmp/birja-backup-test-phase09-final,152309760bytes, SHA256
5eb886d13237bd1376b5af02b23d63b1c9703289cafe8d4a082371f6349c8302.
Every current CORE/unit file is byte-equal to this tested archive. The serial
all-lane adapter calls the exact canonical roundtrip/roles/populated+freshTLS
functions while retaining this archive. The canonical rollback CLI explicitly
receives --recovery-bundle with these same bytes. No reduced assertions or
ignored failures were used. All owned browser/ops/transition/test resources
are cleaned. Earlier interim runs and failures below remain chronological
evidence; the final matrix supersedes their in-progress dispositions.

Distinct inline code/security/UI/goal reports close all implementation blockers;
independence is not claimed. Goal verification16/18 retains the two actual-owner
UI checkpoints. Native200% was observed unsupported in headless automation,
not a pass; offline actual DOM pages make the owner check possible locally.

## Browser proof (Plan13)

Actual isolated Chromium, real email-code auth, cookie/CSRF APIs, financial
services and PostgreSQL/schema0013. Only external calendar DATASET and explicit
rights/status/action/quote inputs are synthetic. Real calendar validation,
advancing DB clock, stock gate, shared account locks, deferred integrity and
final SQL guard remain active. The fixture is an isolated CLI, never an app
route: it refuses without phase09-isolated, dev/console and exact disposable
postgres/birja_e2e DB/user identity, and refuses provider credentials. A negative
guard invocation outside that environment failed before application/DB imports.
One instrument per transaction and new continuity generation per verified test
baseline preserve real service constraints. No runtime application patch or
provider permission is claimed. Guarded synthetic calendar input is mounted
read-only only in the disposable backend launcher; production imports no helper.

The full run/tmp/birja-phase09-browser-0diae03w/browser-final.log passed44tests,
with1expected production-CSP skip and1legacy timing fixture failure. Its500ms
lease could expire during actual page startup; scoped correction gives3seconds
of startup headroom while retaining expiry BEFORE30-second polling and repeated
old-response rejection. Exact125ms equality is separately tested in query cache.
Corrected whole corporate-action file passes11tests47.1s:
/tmp/birja-phase09-browser-qf7aaoq6/browser-actions.log.
Final stock file passes14tests111.5s wrapper:
/tmp/birja-phase09-browser-qf7aaoq6/browser-stock.log.
Together all45applicable browser stories pass,1expected CSP skip, retries0.
No unconditional success or ignored failed assertions.

Stock stories prove real askbuy/bidsell/zero fee, shortcut drafts only, exact
recorded receipt, original shared cash/start, stock sale→crypto buy→stock buy,
combined alphabetical holdings/classes, actual price_changed second click,
committed response loss followed by closed same-key replay200 with exact original
body/receipt, malformed committed success→UNKNOWN→original receipt, closed draft
retention/reopening no auto-fill, real dated closed/halt/uncertain-action marks,
keyboard fractions/status expiry, late actual fill across signout/new-account
without leakage,320/375/768/1024/1440reflow/reduced-motion/64-character valid name,
exact7-column versus card accessibility and no document overflow. Focused
Confirm is explicitly checked above fixed bottom navigation before submission.
Existing actual crypto/auth/portfolio/history and Phase7/8 discovery/action
stories remain in the full run, not replaced by canned financial success.

Native browser Control+Equal five times produced no200% viewport/pixel-ratio
change in this headless runtime. Result is explicitly false;640px supplementary
reflow captures are not native zoom. Owner must verify actual200% in Plan15.
22synthetic-only PNGs are retained under/tmp/birja-phase09-ui-proof/screenshots/,
with SHA256 manifest/tmp/birja-phase09-ui-proof/screenshots.json. Source hashes
are09-UI-SOURCE-HASHES.json. No account email/codes/cookies in screenshots.
Owned browser containers/networks/volumes are checked empty on cleanup; runner
logs retain exact assertions. They do not inspect existing dev/prod resources.

## Frontend interim evidence

Plan11 full556tests passed,96.42%statement/92.40%branch coverage; full lint/types
passed. Later meaningful boundary tests additionally cover cancellation failure,
foreign receipts, exact expired confirmation, session failure, malformed
financial authority and cutoff bounds. These are not yet claimed as final full
critical coverage; Plan14 remeasures all required gates. See10–12summaries for
actual earlier RED/GREEN, scoped timings and inline review provenance.


## Plan14 final gates in progress — 2026-11-12

Distinct inline source/security/UI/goal role passes are used because delegated
roles lacked filesystem/shell access. This is not independent-agent assurance.
Plan15 owner acceptance and native200% zoom remain pending. No live stock data,
provider/B2/timer, installed recovery archive or production service was touched.

- Full backend:2086passed85warnings263.05s,99.86%overall. Exact39critical
  modules:3904statements1242branches100%,zero missing/partial. Logs
  /tmp/birja-phase09-final-backend-clean.log and final-critical.log. Since then
  PostgreSQL was patched; a complete rerun on18.7 is still required.
- Final frontend:590tests33files18.42s;98.41%statements,94.40%branches,
  98.83%functions,99.12%lines. Critical stockTrades wire parser100%. UI controller
  coverage is not falsely described as100%. Full lint/types/format pass; final
  production build1.13s,453.87kB JS/139.61kB gzip. Logs final-frontend-reviewed
  and final-frontend-build under/tmp/birja-phase09-.
- Full canonical browser driver:45passed,1expected production-CSPskip,retries0,
  234.6seconds on PostgreSQL18.7; /tmp/birja-phase09-browser-69b6wynx/browser-all.log.
  /tmp/birja-phase09-final-browser-driver.log records explicit project identity,
  private synthetic Compose inputs and zero remaining containers/networks/volumes.
- pip-audit: no known vulnerabilities. npm audit --audit-level=high exits0;
  2low13moderate development advisories remain, zeroHIGH/CRITICAL. No audit fix
  or gate exception was used.
- Runtime nonroot/networknone smoke: UID1001, real native XNYS calendar, stock
  service imports and exact Decimal Buymax assertion pass. Actual test-builder
  DB/Redis smoke remains in the serial tail.

### Fresh image finding and local patch

The fresh Trivy0.76.1 database reported CVE-2026-125350 HIGH in old PostgreSQL
libxslt1.1.45-r5, fixed version1.1.45-r6. Old strict status is
/tmp/birja-phase09-final-scans/status.json (overallfalse,onepostgres finding).
Official registry candidate is PostgreSQL18.7/libxslt1.1.45-r7:
https://images.chainguard.dev/directory/image/postgres/versions . This same-major
local remediation is a necessary gate-failure deviation, not a production upgrade.
Source compose/CI pins, recovery registry index/platform/config identities,
embedded Compose checksums and dump version checks move together; retained old
archives and installed tooling are untouched. Sourcec272b3c records the patch.

New indexadbf3d8db097696ed6e997b108b51393786be999c04d543502f8959e1bafa8de,
amd64manifest42c334e9e4d30cf6f99ac6bbc411910d020b02dfb693604887e9cdc9188e3a48,
config4ee05252904571f8901ceb47916108d7da51fc6ecc3edbfa4a161b8b9225051e.
Authenticated recovery Compose SHA256634eabc7c1c3e4235a2d506e7ac1b8417b5cffcca0203df6f4f578f0420ddc91.
New /tmp/birja-phase09-patched-scans/status.json is overalltrue with all five
strict targets zeroHIGH/CRITICAL, includingunfixed, no ignore/VEX waiver.
Database updated2026-11-12T12:59:19Z. Per-image identities/report hashes are there.
Offline image13contracts and CI10contracts pass. Physical copied-candidate and
independent logical restore/untouched-original abort proof passes38.802s;
/tmp/birja-phase09-final-image-transition.log. Its old/new exact server-version
fixture now expects18.6 original versus18.7 candidate, never an arbitrary major.

### Remaining serial proof

All configured offline operational contracts passed. Initial retained run reached
actual source stock execution, shared cash, split and cutoff plus every historical
revision through0013; the new restored scheduler fixture incorrectly expected a
write against quarantined stock metadata. Actual42501 denial exposed that fixture
error. Corrected fixture requires actual app financial denial AND actual scheduler
stock denial, while owner-only original-receipt replay/context/portfolio and
manifest/identities remain exact. No grant was repaired or broadened. Final same
archive replay, populated/fresh verified TLS, rollback and SQL tail remain in
progress; do not claim those gates yet. Existing public tool archive is
/tmp/birja-backup-test-phase09-final/recovery.tar, SHA256
0f818cd27fedaeec0a5545d5df73a5920b02ba2d90bdcc3418c7e068d44e2c4f.
Wrapper/tmp/birja-phase09-final-ops.py calls canonical bundle/roundtrip/roles/TLS
lanes serially, verifies that exact retained archive on rerun, and installs nothing.

Retained replay now passes379.164s,152309760archive bytes with that SAME SHA256.
Every0007–0013 revision preserves exact rows/schema/identities and source. Actual
restored original receipt SHA256c58fe79842fc60970294128e46c8ee9531271fef12c53489b5468f2c6c71413b
matches source, mixed portfolio matches, app/scheduler quarantine stays intact.
A subsequent identity-insert probe initially collided with the now complete
calendar; it now chooses MAX(session_date)+1 without touching sequence state or
weakening uniqueness/check constraints. Final entire retained replay passes,
not merely a targeted consumer. Restricted role and both TLS lanes continue.

Final restricted roles pass161.010s:63denials,12input/lock refusals, fresh/upgraded
ACL parity, actual auth/crypto/runtime/calendar consumers. Populated0012→0013
TLS passes115.596s including actual stock quote/execute/replay/context/portfolio,
real split/exclusive cutoff and immediate crypto cashreuse. Bad CA/hostname and
plaintext, credential/mount isolation and certificate renewal all pass. Fresh
TLS and final rollback/SQL/native/backend/browser artifact tail remain pending.

### Preserved old-source backup compatibility

The prior full0f818archive completed allretained/roles/TLS in811.581s, but the
separate real selected-volume rollout exposed that a pre-upgrade18.6 source
pg_dump was rejected by the newly exact18.7 producer guard. This is an actual
source compatibility finding, not a permission exception. Behavioral RED
6cd3c59 additionally catches prefix18.70 accepted incorrectly. FIX03a2ec3
uses a full-match allowlist for reviewed18.6/18.7 including Debian suffix,
rejecting other minors/majors/lookalikes before upload. Full26backup contracts
pass57.775s; /tmp/birja-phase09-dump-compat-green-full.log.

Replacement local public archive is recovery-compatible.tar in the same private
/tmp/birja-backup-test-phase09-final directory,152309760bytes, SHA256
5eb886d13237bd1376b5af02b23d63b1c9703289cafe8d4a082371f6349c8302.
Independent tar-member hash comparison confirms ONLY backup-snapshot.py,
INVENTORY.json andSHA256SUMS differ from0f818: images, restic, schema authority,
roles, TLS and other recovery sources are byte-identical. Nonetheless the final
complete serial replay is repeated on these exact bytes; rollback now receives
--recovery-bundle with this exact archive explicitly, including selected-volume
old-source pre-start and new-source post-start proofs. Production and installed
archives are unchanged. Final compatible-archive gates are still running.
