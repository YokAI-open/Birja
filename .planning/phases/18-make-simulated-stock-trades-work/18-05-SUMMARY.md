---
phase: 18
plan: "05"
requirements-completed: [SX-02, SX-03, SX-04]
completed: 2026-11-24
---

# Phase 18 Plan 05 summary

The [live receipt](18-LIVE-RECEIPT.md) records an isolated AAPL buy at the
live IEX ask and sale at the bid. Cash, positions and History matched the
receipts, both retries returned their originals, and a BTC control used the
same virtual cash. The official halt report and quote were collected through
the app's normal scheduler paths. The coverage limits remain documented.

Recovery carries 0024 in payload 4 and profile `deploy-recovery-v5`. Local
encrypted recovery restored exact 0023 and 0024 data and authenticated the
app and scheduler over TLS. All three original receipts replayed unchanged,
including the pre-upgrade receipt. The prior reader code matched the retained
release. The restored report kept its expired deadline. An attempted schema
downgrade refused and preserved the 0024 candidate. The full stock recovery
contract suite passed all 26 tests.

The retained 0023 cold lane passed on the installed v5 archive and replayed
the original financial requests after an encrypted restore with the source
database removed. The local archive SHA-256 was
`3b2bde5265b31351872ef896a6fa8f455dbec90fe952e490ad7c5b3de82edc85`.
The initial same-archive rollback also exercised TLS rejection cases and an
actual prior application image against a retained 0008 database. A second
selected rollback lane preserved the original volume fingerprints and restored
using the same installed archive.

The full 0007–0014 historical operations command reached its local process
time limit in the 0014 lane. The log shows success through retained 0013 and
successful 0014 backup and restore launcher exits. This interrupted run is
not a passing result for the complete historical matrix. The separate rollback
command passed both retained 0008 lanes. Its final 0014 lane reached the
pre-cutover encrypted restore and verified-TLS startup before the local
runner stopped the candidate deploy at its time limit. The harness removed
its owned fixtures.

The Phase 18 recovery evidence is the directly affected 0023 and 0024 proofs,
the passing stock recovery contracts and the two completed rollback lanes.
The historical runs remain partial. [Runbook](../../../deploy/RUNBOOK.md)
Full release CI, production cutover and activation remain Phase 21.
