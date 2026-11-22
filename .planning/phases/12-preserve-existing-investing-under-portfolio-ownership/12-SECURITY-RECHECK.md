---
phase: 12
slug: preserve-existing-investing-under-portfolio-ownership
status: secured_targeted_source_review
register_authored_at_plan_time: true
baseline_threats_total: 112
targeted_threats: 11
targeted_threats_closed: 11
threats_open: 0
unregistered_flags: 0
asvs_level: 1
reviewed_at: 2026-11-17
cr01_candidate: 4c16a30c01e6040c1005fe4067e791d0ec2bc40c
cr02_candidate: 2ef1f58abc376c6b587e936d98e985809a7246f9
integrated_qualification: pending
---

# Phase 12 — Targeted Security Recheck

The two repair candidates preserve the declared mitigations examined below.
This is a source-bound recheck of the changed controls, not a new qualification
of the complete phase or the combined runtime. The 112-entry register, original
54 scoped acceptances and mapped flags remain in `12-SECURITY.md`; this report
does not invent new risk acceptances or relabel its historical test receipts.

CR-01 was inspected at immutable commit
`4c16a30c01e6040c1005fe4067e791d0ec2bc40c`, with supporting source in
`/tmp/sv-12-reviewfix-G1RXLm`. CR-02 was inspected through immutable Git blobs at
`2ef1f58abc376c6b587e936d98e985809a7246f9`. The candidate commits are separate
repair branches. Neither this report nor the existing actual image proof claims
they were already integrated and tested together.

## Threat disposition

All entries below retain their plan-authored **mitigate** disposition. CLOSED
means the declared control is present in the examined candidate code; actual
combined-source security and cold-recovery qualification remains a separate gate.

| Threat ID | Result | Candidate-bound implementation evidence |
|---|---|---|
| T-12-11-01 | CLOSED | CR-01 `backend/app/services/stock_trading.py:361–480` retains instrument gate before active root lock, immutable cause insertion, immediate constraints, final SQL authority as last business SQL and rollback on refusal. Changed `backend/alembic/sql/0017_stock_portfolio.sql:124–151` exempts only proven zero historical dividend obligation. |
| T-12-11-02 | CLOSED | CR-01 leaves the path-derived owned-active API resolver and CSRF wrapper unchanged. The final authority still joins root ID plus user, matches movement/fill root and owner, rejects closed roots and compares exact persisted cash, holdings, basis and expected authority at SQL lines154–189. Retry identity/replay handling is unchanged. |
| T-12-13-01 | CLOSED | CR-01 does not expand entitlement discovery or borrow another owner's snapshot. Its exemption requires no earlier movement or trade for this exact root and instrument and verifies before-quantity and before-basis against this root's preceding journal. Unknown/incomplete history remains blocking. |
| T-12-13-02 | CLOSED | Scheduler selection, active-root predicate, dividend SQL locking, once-only cause identities and narrow financial routine grants are unchanged. No zero entitlement, payment, decision or History entry is inserted to unlock a purchase. Only a final stock execution predicate changes. |
| T-12-18-01 | CLOSED | CR-02 changes the image factory, leaving independent money/unit projections and immutable before-oracle comparison intact. `portfolio-smoke.py:89` calls the declared runtime factory before fixture database construction; child transport reauthenticates immutable image/source/archive before execution. |
| T-12-18-02 | CLOSED | CR-02 `portfolio-smoke.py:27–69` exports one exact committed complete backend tree, verifies its inventory before and after actual Dockerfile runtime build, refuses dirty source/HEAD drift, binds source/app/context/Config/RootFS and reinspects the immutable image ID. `portfolio-sources.py:153–202` supplies the actual complete binding/inventory checks. Retained consumer dispatch is unchanged. |
| T-12-26-02 | CLOSED | CR-02 removes the workstation-only cached dependency image, custom Smoke.Dockerfile and source overlay. Build failure refuses before image adoption; build timeout remains bounded. `test-ci-ops.py:1142` adds six provenance/refusal contracts to its existing unittest gate. Existing security/recovery gates and thresholds are unchanged. |
| T-12-26-SC | CLOSED | No dependency, runtime Dockerfile, scanner policy or base-image pin changes in either repair. Actual declared-runtime construction now precedes the cold fixture; immutable-ID/image scanning obligations remain unchanged and require integrated qualification. |
| T-12-27-01 | CLOSED | Existing serial validation/source authentication and nonzero-failure handling remain unchanged. The repair receipts explicitly distinguish affected checks and the old-source actual image proof from complete final qualification; no new whole-run success is asserted. |
| T-12-27-02 | CLOSED | CR-01 updates exact migration/static SQL/body and recovery authority fingerprints together. CR-02 preserves image/archive verification around children and the existing encrypted source-destroyed cold restore. Complete seven-stage qualification of the combined new source remains pending. |
| T-12-27-SC | CLOSED | Neither repair weakens strict HIGH/CRITICAL gates or changes approved packages. Existing qualified scans remain historical evidence, not scans of these two candidates together. |

## CR-01 predicate and authority checks

The only executable SQL change is in the calculation of `pending_boundary`.
The new exception applies to `supported_dividend` only. It requires all four
coverage bounds to span the verified cutoff: `journal_start_at`, `complete_from`,
`coverage_start`, and `covered_until`. It requires no pre-cutoff root/instrument
movement and no other pre-cutoff root/instrument trade. Current movement
`before_quantity` must equal the preceding root/instrument journal sum and
`before_basis` must equal its last preceding basis, with zero only when no such
prior journal exists. `coalesce(...,false)` keeps NULL/unknown coverage closed.
Historical owners and every unapplied split therefore retain their pending
boundary; the later final-authority refusal still enforces that boundary.

No change occurs to instrument/root lock ordering, caller/user identity,
active-root validation, immutable economics, source admission, quote freshness,
market sessions, supported-action holds or exact financial comparisons.
The two changed bootstrap files replace only the expected routine body digest;
their grants, declared signatures/OUT metadata, definer checks and ACL checks
are unchanged. Migration and migrator source pins change consistently.

Independent read-only blob hashing reproduced:

| Artifact | SHA256 |
|---|---|
| Static stock SQL | `3dc967baccb425ba26f73bb2fab66b7947aff73f5454ea2f85e03a6e0aa5e08b` |
| Final routine body | `dd923d5797c95072163bd59918a95935849e9acc7af884b406706dcedfa7c158` |
| Migration0017 | `92cff0699a40b0b8f5f4d66bc56a39a2ef88e3184860d86d6957607a3413f32b` |
| Canonical source authority | `617fcabb4fe6d24f0cd0c306680f759f5d9dc21d970e7ed8919c8913980a9696` |

A recursive comparison of old/new `portfolio-recovery-0017.json` found exactly
one changed leaf: `portfolio_authority.functions[2].definition`, the expected
routine. Roles, grants, ACLs, declarations, financial oracle, other routines and
schema are unchanged. Quarantine/no-ACL pins are updated in the same fixed
source-owned profile; the inspected actual logical-restore receipt exercises
their admission and grant reconstruction. No live catalogue is trusted as its
own expected fingerprint.

The six new regression cases use actual restricted `birja_app` execution after
another owner's genuine scheduler-derived dividend payment. They check other
owners, sibling roots and later-created roots, repeated buys and immutable
replay, unchanged original-owner state and absence of fabricated payments.
Historical-owner and incomplete-coverage refusal cases explicitly observe a
call to final SQL authority and require unchanged economics after rollback.
Closed roots remain404. These assertions were inspected, not rerun here.

## CR-02 provenance checks

`build_current_runtime` obtains the full backend archive from one captured commit
and uses its actual Dockerfile `runtime` target. It has no previous-image lookup,
fallback dependency base or runtime source overlay. Complete extracted inventory
checks surround the build. Tracked dirty backend files or changed HEAD refuse;
untracked files cannot enter the committed archive. Build and inspect failures
refuse rather than adopting an old image. The result captures all Config and
RootFS bytes and reinspects the content ID immediately. Every child transport
again checks that ID, captured commit, backend cleanliness and archive binding.

Six offline contract assertions cover actual dispatch to the factory, exact
declared build context, dirty source, failed build, HEAD/context mutation and
revision/RootFS substitution. They are loaded by the existing CI unittest gate.

## Inspected receipts and limits

- CR-01 `12-REVIEW-FIX.md` and `/tmp/phase12-cr01-green-final.log`: six cases
  pass; `/tmp/phase12-cr01-affected-first.log` records106 affected cases.
  `/tmp/phase12-cr01-recovery-logical.log` ends with actual mixed0017 logical
  restore, marker refusal, reader interpretation and equality passing, plus
  the ten offline recovery contracts described in the repair receipt.
- CR-02 `/tmp/phase12-cr02-REVIEW-FIX.md` and
  `/tmp/phase12-cr02-ci-contracts.log`:37 cases pass, including six new contracts.
  `/tmp/phase12-cr02-image-proof.json` records an actual declared-runtime build,
  UID1001,123 matching packaged files and immutable image
  `sha256:8063a60795d194ac41971e51b49b24535a95152bd52c92a990175f0d767d89c9`.
  Its backend source is **`05426f76640f0d15ca27551b723dd07d766b3bb6`**, before
  CR-01 integration. It is evidence for the factory, not a new-source cold restore.

No tests, services, database processes, provider calls, private configuration,
dependencies or production operations were invoked by this recheck. Only this
report was written. No new unregistered threat flag is introduced by the bounded
repairs; both map to the existing threat register above. No new risk acceptance
is added. **The combined source still needs its affected actual security/image
and cold-recovery qualification before final phase claims.** Existing Phase7
live gates and separate owner UI/native200% acceptance remain unchanged.
