# Phase 8 local execution proof

Incremental actual evidence, not phase completion or live activation.

## Wave 1: Plans 01 and 03

Plan 01 adds constrained accounting schema 0011 and restricted grants; Plan 03
adds product-specific action admission and exact economic/safety rules.
Individual RED/GREEN commits and scoped results are in their summaries.

Independent early review found and resolved three schema blockers: alias
observations could not share an economic revision; movement causes lacked
user/instrument/unit correspondence; interrupted concurrent index creation broke
migration retries. Actual failing regressions and corrective commits are
recorded in 08-01-SUMMARY.md. Final independent schema review is clean.

The first full integration run exposed 22 failures (1089 passed): 20 stock API
constructor failures after the new local unit column, plus two historical test
expectations for the predecessor downgrade guard. The API now explicitly maps
provider-contract fields and suppresses nonzero-unit amounts until the full
unit-aware path is implemented. Seed downgrade tests exercise actual 0010.
Independent affected-scope review is clean. No earlier failure was ignored.

Final Wave 1 gate:

- Backend compileall: pass.
- Full guarded isolated backend suite: **1115 passed, 77 warnings, 54.26s**.
- Overall coverage: **99.71%**, existing 80% threshold unchanged.
- Expanded 23 critical modules: **1388 statements / 374 branches, 100%**.
- Saved full output: `/tmp/birja-phase08-wave1-backend-fixed.log`.
- Earlier failed output: `/tmp/birja-phase08-wave1-backend.log`.
- No source change followed this successful gate before the next plan.

The isolated birja-test PostgreSQL/Redis services remain healthy for subsequent
execution. No production services, provider requests or installed tools were
changed. Phase 7's live review remains owner-deferred; its frozen source hashes
are stale after authorized Plan 03 changes and must not be silently refreshed.
The scheduled check retains its fail-closed hash guard and has not been modified.

## Plan 02: exact0011 recovery and restricted TLS

Both tasks passed. Independent review found a pre-dump sequence snapshot race:
PostgreSQL sequences are not MVCC, so a correct concurrent dump could disagree
with its manifest. Actual encrypted retained-archive regression reproduced it.
The correction extracts exact allowlisted SEQUENCE SET values from the actual
dump with strict parsing, bounded output and cumulative timeouts. Final review
of this correction and the operations fixtures is clean.

- Same retained archive SHA256:
  `eb271dfc8fe524230b12c698586298ad29ecdf74aacb66d4555c646aaecea690`.
- Exact encrypted recovery 0007/0008/0009/0010/0011: pass, 263.968s.
- Real concurrent-nextval0011 restore, nine accounting-row corruption classes,
  all seventeen identity-state corruptions and duplicate-application refusal:
  pass.
- Actual roles/grant parity: pass, 150.169s, including 63 legacy denials.
- Populated0010→0011 verified-TLS lane without grant repair: pass, 99.296s.
- Fresh0011 verified-TLS/parity lane: pass, 93.225s.
- CA/hostname/plaintext, mount isolation, renewal and real calendar/append/deny
  consumers: pass in both applicable lanes.
- Final real canonical suite: 7 passed, 47.652s; populated downgrade refusal:
  1 passed, 0.44s.
- Backup tests: 25 passed, 53.24s; restore-safety: 6 passed, 1.32s.
- Full serial log: `/tmp/phase08-02-all.log`; earlier actual sequence RED:
  `/tmp/phase08-02-sequence-red.log`.
- Owned birja-ops-test containers, networks and volumes: empty after teardown.

Exact commands, source/image identities, predecessor hashes and RED/GREEN
commits are recorded in 08-02-SUMMARY.md. No new package or privileged production
operation was needed. Existing birja-test services remain available for later
local tests. This completes one of the two Wave 2 plans, not the entire wave.

## Wave 2: Plans 02 and 04

Plan 04 implements current REST discovery, known-ID rechecks and finite mutation
replay with fixed distinct REST/stream hosts, exact parsing and a shared cycle
budget. Official source identities and protocol deviations are recorded in
08-04-SUMMARY.md. No private provider request was performed.

- Adapter:123 tests; adapter/rules/admission combined:298 passed,3.91s.
- Adapter504statements/220branches:100%; scoped lint/format/types pass.
- Independent review at4d1b327:0blockers/0warnings.
- Full guarded isolated backend integration: **1238 passed,77 warnings,53.86s**.
- Overall coverage: **99.76%**; expanded24critical modules1892statements /
  594branches: **100%**. Existing thresholds were not reduced.
- Backend compileall:pass.
- Full receipt:`/tmp/birja-phase08-wave2-backend.log`.

Wave 2 is complete; four of thirteen Phase 8 plans are executed. Next is the
ownership journal and historical cutoff reconstruction in Plan 05. Phase 7
live acceptance and Phase 8 activation remain separate pending gates.

## Proven recovery contract for subsequent consumers

Plan 02 has proved exact revision-selected recovery and actual restricted
TLS populated upgrade/fresh parity for 0011. Its canonical contract includes observations.event_id,
split_applications.coin_id, causal composite keys and the concurrent trade index.
Privileged bootstrap preprovisions the NOLOGIN operator role; restricted migrator
privileges must not be expanded to CREATEROLE. No requirement or entire phase is
marked complete by the infrastructure/rules evidence above.

## Wave 3: Plan 05

Instrument-serialized ownership and exclusive-cutoff reconstruction are complete.
Independent review reproduced two bugs; exact-boundary fills now hold and new
causes explicitly hold at full transaction ID>=2**32 before xmin interpretation.
Stored replay and reconstruction remain supported. Re-review:0active findings.

- Focused ownership/migration/crypto regressions:207passed19.41s.
- Ownership203statements/94branches:100%; scoped lint/format/types pass.
- Actual roles/fresh parity155.530s and populated/freshTLS102.727/99.435s pass.
- Final corrected-source TLS service consumer:pass100.850s. Owned ops resources
  cleaned. Minimum scheduler six-column immutable trade read preserves denials.
- Full guarded isolated backend integration:**1322passed,77warnings,64.19s**.
- Overallcoverage:**99.78%**;25critical modules2095statements/688branches:**100%**.
- Backend compileall:pass. Receipt:`/tmp/birja-phase08-wave3-backend.log`.

Exact0011 ACL/source identities and RED/GREEN evidence are in08-05-SUMMARY.md.
The canonical producer/row/schema contract is unchanged; earlier encrypted
recovery proof is retained, while affected ACL/TLS consumers were re-proved.
Five of thirteen plans are complete. Next08-06 handles durable revisions,
once-only splits and historical entitlements without stock execution or cash.

## Wave 4: Plan 06

Immutable event revisions, once-only all-owner splits and historical dividend
snapshots are complete. Source repeats append audit without duplicate economics;
uncertain/late/changed applied terms hold. Entitlements preserve sold-out owners,
explicit units and immutable replacement lineage without cash or History writes.

Independent review found three blockers, reproduced and fixed: final monitor/
reviewed-calendar expiry, later split effects past a held earlier boundary, and
trusted account/server scope propagation. Re-review of frozen source SHA256
`649d9e35416315ae2268264142b97059105ef3530b14310fb3f41142ef435317`
has0active findings.

- Focused accounting/ownership/rules:**234passed,20warnings,22.43s**.
- Accounting312statements/116branches:**100%**; scoped lint/format/types pass.
- Actual PostgreSQL races observe blocking in both freeze/fill orders; final
  authority revocation and elapsed monitor/calendar deadlines roll back effects.
- Split retry/concurrency, all-owner fractional/overflow refusal, zero owners,
  first-owner fault rollback and five split/dividend boundary orderings pass.
- Full guarded isolated backend:**1398passed,73warnings,75.35s**.
- Overallcoverage:**99.80%**;26critical modules2407statements/804branches:**100%**.
- Compileall:pass. Receipt:`/tmp/birja-phase08-wave4-backend.log`.

No schema, grant, canonical recovery or dependency change was needed. Six of
thirteen plans are complete; next08-07 implements durable complete catch-up and
independent disabled-by-default action scheduling. External gates remain pending.

## Wave 5: Plan 07

Durable fixed-target action catch-up, retained known-ID checks, bounded REST
continuations and replay time-segment resumption are complete. Partial progress
stays reconciling; twenty-stock health publication requires complete evidence
and current scope/generation/unit/epoch/deadline guards. Independent stock loops
share actual request-attempt quotas; actions remain default-OFF.

Five independently found source-continuity/deadline/routing/quota/replay issues
have observed regressions and corrections. Inclusive historical mutation replay
now returns its original immutable observation without changing the later pointer
or safety epoch; changed terms still conflict. Final independent review, including
formatted quota source and scheduler/Compose wiring, has0active findings.

- Final focused suite:**342passed,20warnings,74.26s**.
- Four affected critical modules1155statements/428branches:**100%**.
- Actual bounded REST restart, replay interval bisection and smallest-instant
  capacity-held cases pass. No request/byte/time caps were weakened.
- Ruff12files, mypy6sources, synthetic dev/prod Compose and diff checks pass.
- Full guarded isolated backend:**1461passed,73warnings,126.05s**.
- Overallcoverage:**99.81%**;28critical modules2746statements/896branches:**100%**.
- Compileall:pass. Receipt:`/tmp/birja-phase08-wave5-backend.log`.

Exact source hashes, deviations and task commits are in08-07-SUMMARY.md and its
review. No schema/grant/recovery-contract change was needed. Seven of thirteen
plans are complete; next08-08 adds scoped operator reconciliation and proves0012
plus predecessor exact recovery. No private calls or activation occurred.

## Wave 6: Plan 08

Scoped SQL reconciliation, protected private tooling and exact0012 recovery are
complete. Full action/calendar row digests are bound to the same snapshots Python
validated and rechecked under the shared gate. Exact revision/history/ledger/
unit/epoch expectations constrain immutable decisions. Unsupported financial
repairs stay held. Independent functional/recovery/fixture reviews have0active
findings; actual discovered bugs and test-boundary corrections are recorded in
08-08-SUMMARY.md and08-08-REVIEW.md.

- Final focused authority/private suite:**55passed18.79s**; reconciliation
  121statements/52branches:**100%**; scoped lint/format/types pass.
- Retained archive SHA256:
  `db27d99ba3085c6b93fa4fe4a6ea6bd9be5ea38a89f9e5f3620005de9681b874`.
  Public tool artifact:`/tmp/birja-backup-test-phase08-final/recovery.tar`.
- Actual same-archive encrypted0007–0012 exact recovery/replay:**301.665s**.
  Includes populated accounting/17identities,13authority corruption refusals,
  genuine restricted operator decision replay and split replay without effects.
- Remaining actual role proof:**158.290s**; populated0011→0012 TLS:**105.969s**;
  fresh0012 TLS:**105.810s**. Effective ACL parity, real nonprivileged operator
  consumers, PUBLIC/app/scheduler denials, bad CA/hostname/plaintext, mount
  isolation and renewal pass. No post-upgrade authority repair.
- Source verifier SHA256:
  `1aa4337745716237f228e468da6a09202907fffbdd9621e9913a8a8272c08bf6`.
  Final fixture SHA256:
  `edc0b3ecf4f9e8b71d4533f5bcb8c3cfc319468a42e0ef7222136e43809173fd`.
- Owned ops/restore containers, networks and volumes are cleaned. Logs:
  `/tmp/phase08-08-ops-complete.log`, `/tmp/phase08-08-roles-tls-final.log`.
  The former completed recovery/replay then found a NOLOGIN test-helper error;
  corrected helper was independently reviewed and remaining role/TLS lanes
  passed separately. No claim that an interrupted --all exited successfully.
- First full backend gate:1510passed/6failed146.71s; all failures were stale
  head0011 assertions. Four literal-only corrections preserve financial,
  retry/index and downgrade checks;61migration tests pass8.77s.
- Final full guarded backend:**1516passed,73warnings,146.72s**,**99.82%** overall.
  All29critical modules2875statements/952branches:**100%**; compileall passes.
  Receipt:`/tmp/birja-phase08-wave6-backend-fixed.log`.

Predecessor selected SQL/contracts remain byte-compatible. Eight of thirteen
plans are complete; next08-09 integrates committed action-safe discovery and
genuinely gate-bound quote units. Whole-phase human/external gates remain pending.

## Wave 7: Plan 09

Action-safe discovery and gate-bound local quote units are complete. The final
bounded READ COMMITTED query projects twenty instruments, exact persistent-hold
and resolution facts, verified units and unresolved event deadlines. Denied,
expired or mismatched authority returns generic epoch0/null times and suppresses
amounts. There are no awaits after the fresh projection clock. One shared SQL
predicate preserves accounting/reconciliation hold semantics.

Quote writes use the exact instrument gate and current post-wait authority,
health and genuine strictly-post-boundary source time. Local units never become
a provider field. Multi-instrument batches explicitly require caller partition;
scheduler writes sorted single-instrument transactions after HTTP without
committing a caller-owned transaction. Verified applications consume stale
boundary hints; unresolved events still cap disclosure.

- Focused API/quote/scheduler/accounting/operator suite:**311passed,28warnings,
  101.00s**; three changed critical services562statements/194branches:**100%**.
- Actual observed advisory waits prove both quote/split orders, permission and
  120second source-age expiry. Applied split/new-unit quote/API recovery and a
  separate pending event cutoff pass. Entire-envelope redaction regressions
  reproduce and correct both calendar denial and generation mismatch.
- Scoped Ruff/format8files,mypy5sources and diff checks pass.
- Independent full and targeted re-review atf6e9d0a:**0active findings**.
- Full guarded isolated backend:**1551passed,73warnings,153.59s**,**99.82%**overall.
  All29critical modules2972statements/978branches:**100%**; compileall passes.
  Receipt:`/tmp/birja-phase08-wave7-backend.log`.

No schema/grant/tooling/dependency change was needed. Nine of thirteen plans
are complete; next08-10 implements client validation, monotonic epoch protection
and exact known-deadline purging. Permission-reducing generic epoch0 responses
must win over cached higher epochs while internal replay high-water is retained.

## Final dependency audit preparation

Actual unchanged-lockfile audits ran during Plan10 on 2026-11-11; these are
dependency results only, not a completed Plan12 or phase gate. `uv run pip-audit`
exited0 with no known vulnerabilities. `npm audit --audit-level=high` exited0:
0HIGH/CRITICAL, with the existing2low/13moderate development advisories retained.
No forced upgrade, dependency, lockfile or gate change was made. Initial sandbox
attempts failed on cache/network access; authorized local audit reruns completed
with ordinary registry access. Receipts:
`/tmp/birja-phase08-final-pipaudit.log` and
`/tmp/birja-phase08-final-npmaudit.log`.

An actual current-source hardened runtime build also passed. The subsequent
container ran as UID1001 with network disabled, read-only root, all capabilities
dropped, no-new-privileges and a bounded16MiB private temporary filesystem.
Genuine calendar imports/early-close decisions, exact3:2 split/basis preservation,
fractional refusal, persistent-hold precedence and exact expiry passed; action,
ownership, reconciliation and monitor modules import from baked source. No
database/provider connection, credentials or production resource was used.
An initial harness needed explicit `/app` import resolution and writable private
temporary space; the corrected smoke exited0. Build/smoke receipts:
`/tmp/birja-phase08-runtime-build.log`,
`/tmp/birja-phase08-runtime-smoke.log`;
replay script:`/tmp/birja-phase08-runtime-smoke.py`.
This runtime smoke is not the later all-five-image vulnerability scan or a
completed Plan12 gate; changed backend source would require affected revalidation.

## Wave8: Plan10 client safety

Strict parser/coherence and exact nearest-deadline purging are complete. Raw
observed action epochs, permission generations and server times are retained
separately from sanitized cached data. Generic redaction can remove prices
without rewinding session/calendar/admission authority. Equal replies cannot
restart elapsed authority; lower generations/epochs cannot recover through
denial, TTL expiry or cache removal/remount. Actual authentication lifecycle
changes alone reset these guards. Public source times and measured RTT remain
intact; an internal monotonic bound only removes authority.

- Final focused suite144tests5.15s; parser100%allmetrics. Hook defensive coverage
  is reported honestly in08-10-SUMMARY.md; no artificial exclusions or gate change.
- Independent complete re-review at7473df3:0active findings. Both original
  blockers and each actual additional ordering regression are preserved in
  08-10-REVIEW.md with final source hashes.
- Full frontend419tests/28files pass15.96s:98.84%statements,97.09%branches,
  99.6%functions,99.53%lines. Full ESLint/typecheck/Prettier/build pass.
  Receipts:`/tmp/birja-phase08-wave8-frontend-final.log` and matching
  `wave8-lint-final`, `wave8-types-final`, `wave8-format-final`,
  `wave8-build-final` logs under `/tmp/birja-phase08-`.
- An earlier409test/fullstatic pass at89c1322 was superseded by the final run
  after real review-driven source corrections, not counted as final evidence.

Ten of thirteen plans and eight of eleven waves are complete. Next08-11 renders
and proves the approved responsive safety states. Requirements, human acceptance
and distinct external activation remain pending; stock execution stays disabled.

## Final retained recovery and restricted-TLS proof

While Plan11 performed isolated frontend/browser work, the unchanged backend,
schema and recovery tooling completed a fresh serial run of the exact `--all`
lanes. Actual command:`python3 /tmp/birja-phase08-plan12-ops.py`; the reviewed
wrapper calls `bundle_package(archive)`, `roundtrip(archive)`, `roles()` and
`assert tls()==tls(fresh_bootstrap=True)` from the current ops fixture, retaining
the same public archive rather than deleting it. Runner SHA256:
`9f32ad29ad3370eeeb95a24c8f99b6049db41b7a6e2d9515ee9f6549f8c9ad7e`.
The runner exited0, with `final_all_lanes=true`, on2026-11-11. No source changes
were made to produce a pass; frontend changes cannot affect these backend lanes.

| Actual lane | Result and measured time |
| --- | --- |
| Same retained encrypted0007–0012 restore | Exact rows/schema/sequences/identities and nonempty action state;315.978s |
| Accounting/authority corruption and replay | Refused corruptions; retained cancellation/alias/cursors/epochs; genuine operator/split replay passed within roundtrip |
| Restricted roles and upgrade/fresh parity |63denied operations, immutable audit/quantity-only scheduler/operator NOLOGIN checks;160.138s |
| Populated0011→0012 verified TLS | Actual app ownership/accounting, scheduler and narrow operator consumers;111.679s |
| Fresh0012 verified TLS | Same effective ACLs and genuine consumers;108.760s |

Both TLS lanes reject bad CA/hostname/plaintext, preserve credential mount
isolation and exercise renewal. No post-upgrade grant repair or source authority
renewal occurred. Fixed `birja-ops-test` containers, networks and volumes are
empty after finally cleanup; the separate UI project was not touched.

Retained archive:`/tmp/birja-backup-test-phase08-plan12/recovery.tar`,152186880bytes,
SHA256`db27d99ba3085c6b93fa4fe4a6ea6bd9be5ea38a89f9e5f3620005de9681b874`.
Receipt:`/tmp/birja-phase08-plan12-ops.log`. Current verifier SHA256
`1aa4337745716237f228e468da6a09202907fffbdd9621e9913a8a8272c08bf6`;
ops-fixture SHA256
`edc0b3ecf4f9e8b71d4533f5bcb8c3cfc319468a42e0ef7222136e43809173fd`.
This closes these final local operation lanes, not UI acceptance, the remaining
CI/image/security gates, provider permission or production rollout.

Independent source security review of Plans01–09 is also complete:
34/34 backend mitigations verified,0open blockers/unregistered warnings. See
08-SECURITY.md for exact scope/hashes and explicit legacy ASVS4.0.3 mapping.
It does not claim pending UI/final verification/external gates are passed.
