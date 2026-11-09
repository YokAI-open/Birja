---
phase: 06-deploy
plan: "09"
status: replacement-tested-installation-pending
source_commit: 3804ec6
review_commit: 851bafe
tested: 2026-11-09
---

# B2 Read Only compatibility: reviewed replacement

Both corrected restricted key pairs authenticated on2026-11-08 with the exact
region/same account. Writer restrictions match Birja-backup/prod/. The supplied
standard console Read Only inventory preset includes shareFiles, so the old
guard rejected a key created exactly according to the setup instructions.

RED3280a6c reproduces that rejection. GREEN3804ec6 recognizes only the exact
shareFiles name in addition to the existing read/list capabilities. It still
rejects writes/deletes, governance bypass and unknown sharing permissions.
The fixed native client cannot invoke download-token creation or mutations.
Backblaze documents shareFiles as download delegation; the account-wide key
retains that extra authority outside this client. No account-wide write
capability is accepted. This distinction is explicit in the runbook/review.

Independent focused source/security review851bafe reports0BLOCKER/0WARNING,
two independent synthetic tests passed0.151s. Full25backup contracts passed
50.269s;4restore-safety passed1.520s; Ruff/checkformat/whitespace passed.
The interrupted earlier test process had no completion record and was not
counted as passing; the complete recorded rerun supplies these results.

## Exact replacement packet

Private preserved path:
`.local/phase-06-handoff/candidate-b2-readonly/recovery.tar`

| Binding | Value |
|---|---|
| Archive size |152,156,160bytes|
| SHA256 |`548bc494e81dbc719d6db0d0c809c49c018bde5c202d5493d73843870c442118`|
| Separate inventory SHA256 |`55069a4ecca727f85f8f55f33f3e4dc9b9e7887a1ff60841b0aa14a7b45d15ea`|
| Trusted verifier SHA256 |`c3fed604fbf14ad9c3df0e43b00874d7761223391eb55c7cb0c45a8cde98b4de`|
| Packet SHA256SUMS hash |`e9c03329b3689c822e0b9c262c6d60c361e12d46ba52e80f27c23feedb8b45be`|

One package created5.533s; generic verification0.768s and copied packet
standalone verification0.764s passed. Both archives have exactly the same member
names. Only deploy/backup-quota.py and its entry in embedded SHA256SUMS differ
from installed83f4f515...; PostgreSQL image archive, signed restic binary,
verifier, units and other payloads are byte-identical. No image, application
source, lock, dependency, role/TLS or schema changed; unaffected full app/browser/
image gates were not repeated. Historical original packet remains preserved.

## One exact artifact, serial supplied replays

| Check | Exit | Seconds |
|---|---:|---:|
| Supplied recovery |0|67.437|
| Populated roles |0|31.076|
| Verified TLS |0|51.252|
| Actualv0.3.1 supplied rollback |0|102.176|

All commands verified the same unchanged548bc494... archive before and after.
The actual existing integration runners used their fixed synthetic projects,
no target feature-checkout fallback or production data. Fresh label queries
confirmed0containers/networks/volumes for birja-ops-test, birja-restore-check
and birja-rollback-test. Logs/immediate exits/times and packet/delta bindings
are retained under ignored `.local/phase-06-handoff/plan09-evidence/`, names
readonly-fix-* and readonly-replacement-*. No raw credentials are included.

## Live preparation and next boundary

Owner explicitly confirmed off-server password/key custody and no other B2
writers. Existing screenshot caps/$0budget persist. Approved read-only source
setup check confirmed exact unchangedv0.3.1, PostgreSQL18, revision0007 and
database size8,574,655bytes, with no private rows/secrets displayed.
Propose32MiB max_stage_bytes,600s whole-operation timeout,64MiB local download
budget/64native requests per operation. These are conservative local ceilings,
not measured remaining provider allowances. Fresh actual bucket/version/parts/
account headroom and normal control validation must still pass before upload.

The installed release remains83f4f515... and must not be edited in place.
The owner approved09installation specifically for that checksum. Present the
reviewed548bc494... replacement for supplemental exact-artifact installation
approval. This is not a re-request of existing backup/restore/timer scope.
After approval, use the trusted verifier/immutable installer, check payloads/
launchers and update the restic link to the same signed binary in the new root.
Then continue the already approved real inventory/backup/isolated restore and
timer-after-success flow. No B2 upload, real backup/restore, timer activation,
app restart or publication occurred during this fix. Plan09 and DEPL remain
pending; Phase6 stays10/15.

Self-check: PASSED for source/review/tests, exact packet/replays and cleanup.
