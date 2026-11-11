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
