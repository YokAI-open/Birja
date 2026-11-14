---
phase: 10-dividend-cash-and-event-history
plan: "06"
reviewed: 2026-11-13
depth: standard
reviewed_head: 513f51d
files_reviewed: 3
files_reviewed_list:
  - deploy/tests/dividend-execution-fixture.py
  - deploy/tests/ops-fixtures.py
  - /tmp/birja-phase10-06-gate.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
gate_status: ready_for_local_consumers
---

# Phase10 Plan06: Independent pre-consumer recovery review

## Narrative Findings (AI reviewer)

**READY FOR LOCAL CONSUMERS.** No material correctness or security finding in
this distinct Task2 pass. This verdict permits subsequent isolated payout and
History implementation against C01–C04; it does not complete Phase10 or activate
live data, production accounting, provider rights or deployment.

Reviewed the new financial fixture and its retained/roles/TLS integration,
canonical all-mode wrapper, completed gate report and sanitized result markers.
Read the Plan02/04/05 summaries, frozen contracts and prior independent
`10-AUTHORITY-REVIEW.md`, `10-RECOVERY-CONTRACT-REVIEW.md` and
`10-PREGRANT-REVIEW.md`. Unchanged authority/recovery implementation retains those
reviews; this is not a claim to have repeated their entire source audit.

The fixture explicitly synthesizes external announcements, admissions, calendar
session evidence, opening ownership and operator reconciliation. It does not
mock successful financial effects: entitlement production is real, original and
correction effects call the restricted scheduler SQL, the historical shares are
sold through the actual stock execution service, and an actual crypto purchase
and sale create and recover the shared-cash deficit. Uncertainty tests first
prove no current eligible entitlement fallback, then use the paid-anchor hold
entry point. Repeated original/decision calls, immutable original bytes, linked
once-only successors, zero original and positive/negative/no-change corrections
are asserted. Real account-lock waits precede authority revocation/revision
changes; blocked calls must raise22023 without changing financial fingerprints.

The restore fixture only fingerprints saved rows and tests restricted42501
denials. It does not grant restored financial execution to fabricate successful
replay. Exact whole-database rows, sequences, financial/authority identities and
source immutability are independently checked by the retained recovery path,
beyond the fixture's narrower cash/ledger fingerprint.

## Exact retained evidence

Independently recomputed archive SHA256 and size, compared all11 CORE/unit files
byte-for-byte between current source and tar members, and matched all6 reported
fixture/bootstrap/migration hashes to current files. Before/after report archive
identities are equal. The report source head is
`d86e759581f6ae73d582587dd4a3eb230f5e69d1`; reviewed head513f51d retains the checked
source identities. Current source/fixture hashes are recorded individually in
the gate report rather than inferred from a later Git head.

| Artifact | Independently checked SHA256 |
| --- | --- |
| `/tmp/birja-backup-test-phase10-preconsumer-fixed/recovery.tar` (152320000bytes) | `1faa8277951d0c2a66ac10ffb8b39b5f85372acdacd10b3b3348126c90052cc1` |
| Current/archived `deploy/verify-restore.py` | `2a9009e4c6332be4d551cd7b1d503edc376ade24f459d0fa6d02595fbfeb4d4e` |
| `deploy/tests/dividend-execution-fixture.py` | `d7d202b714d923626264868eed5f68d2802bde71504496cf87dca7b67e22e7aa` |
| `deploy/tests/ops-fixtures.py` | `9c94238e2c047128729564136cb64fd861176fe5c5fb32c85a8d1b78de7ac022` |
| Fixed wrapper `/tmp/birja-phase10-06-fixed-gate.py` | `9000f5cbe27e27828a8063ca512eaff0470986d5666396eea11c17a83d3302a9` |
| Delegated `/tmp/birja-phase10-06-gate.py` | `f542b035d7156e8c36d39e5223ca405d61ea686d872d1b00114ec9941a0456e7` |
| `/tmp/birja-phase10-06-fixed-all.log` | `28019afa6aa56f83d77f42ae13b100d5814c9d98a62943a1451d891b006a1714` |
| Fixed `gate-report.json` | `c2ab72ce34b3fa7e844788275f7a08a03167d7e969fd8968806426a41f10bdc8` |

Inventory profile is `deploy-recovery-v2`, revisions0007–0014. Approved retained
restic0.19.1 SHA256 is
`20d4142678d0d95ec11a4759def1b73fd9190abc9ca19e4b62d067c0b387e639`.
PostgreSQL18.7 amd64 inventory identities: registry index
`adbf3d8db097696ed6e997b108b51393786be999c04d543502f8959e1bafa8de`,
platform manifest `42c334e9e4d30cf6f99ac6bbc411910d020b02dfb693604887e9cdc9188e3a48`,
image config `4ee05252904571f8901ceb47916108d7da51fc6ecc3edbfa4a161b8b9225051e`.
These are recorded tool provenance, not a new image-security certification.

## Actual gate and scope attribution

Executed by Task1:
`python3 /tmp/birja-phase10-06-fixed-gate.py > /tmp/birja-phase10-06-fixed-all.log 2>&1`.
Inspection confirms the canonical all-mode callable sequence: retained
`roundtrip(archive)`, `roles()`, populated `tls()`, fresh
`tls(fresh_bootstrap=True)`, asserting equal authority results. Literal CLI
`--all` was not used because it cannot receive an external retained archive.
The exact archive is installed in the retained recovery stage; roles/TLS use
the checked current source/scripts, not a claimed archive-installed runtime.

| Completed stage | Seconds | Evidence |
| --- | ---: | --- |
| Retained0007–0014 |503.681|Exact encrypted retrieval/restore, installed fresh0014, legacy/current rows and identities, corruption controls, clone quarantine|
| Restricted roles |210.330|63 denials, fresh/populated authority parity, actual dividend SQL effects|
| Populated verified TLS |163.830|Older consumers plus new SQL effects/races, TLS negatives and isolation|
| Fresh verified TLS |162.172|Fresh0014 authority parity, same real consumer/SQL coverage|

Total1047.402seconds. Full SQL contracts separately passed23/23 with zero skips
in125.294seconds; reviewed fresh pregrant recheck passed2/2 in30.884seconds.
Retained dividend source/clone ledger fingerprint is
`7f06d31ab8315914b282b6d04e0c1c0f5d3f5b84362b721372c2287a5697dfb8`.
Both TLS result markers occur in the inspected final log; their independently
created datasets correctly have different ledger fingerprints.

The original failed archive remains at
`/tmp/birja-backup-test-phase10-preconsumer/recovery.tar`, independently rehashed
as `637516d8ccd487ef2c45ccba395782cba035d21d737abdca2827ffa9a9e7bbc5`.
Its report remains failed:0007–0013 passed;0014 exposed absent operator metadata
during pregrant canonical lookup, before roles/TLS. It is not passing evidence.
The separately reviewed64f7795 fix uses a role-free pregrant structure check;
exact trusted function/schema checks and later full canonical verification remain
required. The replacement archive and full sequence above supersede that failure.

## Threat mapping and limits

| Threat | Scoped disposition/evidence |
| --- | --- |
| T-10-06-01 | Mitigated for C03/C04 boundary: narrow scheduler calls, real42501 denials, immutable owner-bound lineage, role isolation, genuine advancing-authority waits, corruption rejection and clone quarantine. |
| T-10-06-02 | Mitigated for retained evidence: exact original/decision rows and sequences, fixed archive/source/tool hashes, source unchanged and explicit synthetic evidence attribution. |
| T-10-06-03 | Bounded isolated review/execution: sequential stages, observed bounded wait probes and cleanup receipts; no provider I/O or production financial locks. Future application/query bounds remain subject to consumer review. |
| T-10-06-SC | Existing reviewed tool/image provenance retained; this review installed no package, changed no lock or image, and waives no later strict security gate. |

Gate report records zero owned ops/restore containers, volumes and networks;
Task1 also records stopping the empty `birja-test` stack. After the default
sandbox socket denial, an approved read-only metadata recheck independently
confirmed zero containers, volumes and networks for each exact project label:
`birja-test`, `birja-ops-test` and `birja-restore-check`. No other project's
metadata was queried. Whitespace validation passed.
No long database proof was repeated, no source/state was changed, and no provider,
B2, production, timer or installed-tool operation was performed by this review.

The future Plan07 payout service and Plan10 History API are absent by design.
Their integration, user isolation, final exact-archive consumer replay, UI/UAT,
frontend and strict image gates remain later work. This scoped review is not
blanket ASVS certification, provider permission verification or live acceptance.
