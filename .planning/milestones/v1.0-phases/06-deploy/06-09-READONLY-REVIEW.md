---
phase: 06-deploy
plan: "09"
reviewed: 2026-11-09T07:03:54Z
depth: standard
diff_base: b65d538
reviewed_head: 3804ec6
files_reviewed: 3
files_reviewed_list:
  - deploy/backup-quota.py
  - deploy/tests/test-backup.sh
  - deploy/RUNBOOK.md
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 06 Plan09: ReadOnly compatibility review

**Status:** clean within the stated change scope; 0 BLOCKER, 0 WARNING.
**Depth:** standard, focused independent source/security review.

## Narrative Findings (AI reviewer)

No provable new correctness, security or test-reliability defect was found in
`b65d538..3804ec6` across the three listed files. The current scoped source
matches the reviewed commit. Existing resolved full-phase reviews remain
outside this bounded review.

The exact `shareFiles` exception at `deploy/backup-quota.py:183-192` preserves
the required inventory capabilities and unrestricted bucket/prefix checks at
lines178-181. It does not accept arbitrary `share*`, write/delete, governance
bypass or other capability names outside the existing read/list rule.
The inventory traversal still measures versions, unfinished parts and other
buckets; accepting the extra capability does not change its accounting.

The fixed operation allowlist at `deploy/backup-quota.py:56-65` permits only
authorization and four inventory operations. It rejects
`b2_get_download_authorization` and every provider mutation before request
construction and transport. The inventory call chain contains no alternative
download-token creation route. The narrowly scoped writer remains used only
for listing unfinished upload parts in this client.

Backblaze's [primary capability reference](https://www.backblaze.com/docs/cloud-storage-application-key-capabilities),
checked during this review, associates `shareFiles` with creating download
authorization tokens. It grants download delegation, rather than file,
bucket or key writes/deletes. The clarification at `deploy/RUNBOOK.md:207-210`
accurately distinguishes that credential capability from the operations this
inventory client permits.

This is a justified compatibility exception for the supplied standard console
Read Only preset. It is not proof that this credential has the smallest
possible custom API capability set: an account-wide key with `shareFiles`
can delegate account-wide downloads if used outside this client. The runbook
discloses the extra capability, root-only credential handling remains required,
and the client does not exercise it. No account-wide write authority is added.

## Verification

Independently ran:

```bash
bash deploy/tests/test-backup.sh \
  Backup.test_native_inventory_includes_all_versions_parts_and_other_buckets \
  Backup.test_native_transport_rejects_redirect_endpoint_and_bounds
```

Result: **2 passed**, unittest runtime **0.151 seconds**, process exit0.
The synthetic fixtures and HTTP mocks make no provider request and invoke no
real Docker/restic operation in these selected methods.

The positive regression at `deploy/tests/test-backup.sh:159-160` proves the
same exact inventory totals with `shareFiles`; the following HTTP-adapter /
refresh / Job-admission path also runs with that capability present.
Lines182-186 independently reject representative file/bucket/key writes and
deletes, retention writes, governance bypass and an unknown sharing capability.
Lines200-202 prove download authorization and representative mutation operations
raise before the mocked HTTP opener is called. These assertions check observable
admission/transport behavior, beyond merely executing the changed predicate.

## Review limits

This review covers the three-file compatibility diff and its relevant existing
inventory/transport context. It does not repeat the full-phase audit, full
test suite, image scans, builds or artifact replays. Broader passing test/lint
results supplied by the orchestrator were not rerun or treated as independent
proof here. No structural pre-pass was provided.

No live authentication, provider inventory, production data/configuration or
credential read, upload, restore, timer operation or installation was performed.
Reported current key authentication/scope is context from the orchestrator,
not independently observed live evidence. The installed `83f4f515...` recovery
release remains untouched. A clean source review does not establish replacement
archive identity, installation approval, successful recovery or nightly evidence;
the orchestrator retains those separate gates.

Only this review artifact was created; no source/state/history changes or commits
were made by this reviewer.

_Reviewer: independent gsd-code-reviewer agent_
