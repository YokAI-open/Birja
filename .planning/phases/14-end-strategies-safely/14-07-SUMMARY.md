---
phase: 14-end-strategies-safely
plan: "07"
subsystem: private-closure-api
tags: [fastapi, csrf, idempotency, identity, portfolio-closure]
requires:
  - phase: 14-03
    provides: Complete same-transaction closure proof and permanent original outcomes
  - phase: 14-04
    provides: Exact current0023 admission and restricted runtime grants
provides:
  - Authenticated bounded canonical DELETE with minimal private acknowledgement
  - Durable original refusal and safe response-loss/cancellation recovery through public HTTP
  - Actual delete-last OTP/refresh/zero-state and explicit replacement grant evidence
  - Private schema-admission refusal headers before management route execution
affects: [14-08, 14-09, 14-10, 14-11, 14-15, 14-16, 14-17, 14-18]
tech-stack:
  added: []
  patterns:
    - Dedicated strict DELETE parser preserves canonical immutable review context
    - Minimal acknowledgement follows complete commit/proof; ambiguous transport never claims rollback
key-files:
  created:
    - backend/app/schemas/portfolio_closure.py
    - backend/tests/test_portfolio_closure_api.py
    - backend/tests/test_portfolio_closure_identity.py
  modified:
    - backend/app/api/v2/portfolio_management.py
    - backend/app/api/v2/portfolios.py
    - backend/app/services/portfolio_closure.py
    - backend/app/main.py
key-decisions:
  - Confirmation name must already be canonical; deletion never silently normalizes the reviewed original.
  - SQL name-refusal is committed before409; original-body conflict remains a distinct409.
  - Global schema-write refusal keeps its existing status/body/admission rules and gains PRIVATE plus Retry-After5.
requirements-completed: []
requirements-progress: [PMGT-03, PMGT-04, PMGT-05, PSAFE-01]
duration: 15.5min measured first-RED-to-cleanup-receipt interval
completed: 2026-11-19
---

# Phase 14 Plan 07: Private Original Deletion API Summary

**Public authenticated deletion freezes the reviewed owned strategy, preserves
immutable original outcomes after response loss, and leaves a zero-portfolio
user signed in without an automatic grant.**

## Performance and task commits

| Task | Commit | Actual evidence |
|---|---|---|
|1 RED|ad060ea|Real current0023 restricted app reaches missing DELETE405;7.53s|
|1 GREEN|0f970f8|Nine complete public API cases pass57.80s; scoped five-source-module mypy passes|
|2 test-only completion|a1dc80f|Clean50-case current/transport run82.33s and two additional postcommit variants13.03s|

First RED was2026-11-19T11:45:23UTC; cleanup/evidence receipt was recorded at
12:00:53UTC. The15.5-minute interval includes implementation and bounded
diagnostics; it is not a promised feedback latency. Parent owns STATE/ROADMAP;
no whole requirement is completed here.

## Implemented behavior

- `DELETE /api/v2/portfolios/{portfolio_id}` uses server CurrentUser and CSRF
  dependencies before reading the streamed body. Canonical bounded path IDs,
  strict canonical UUIDv4/name and fixed policy, forbidden extra/duplicate keys,
  UTF-8/JSON errors, media checks and8192-byte actual-stream bound prevent a
  caller from supplying ownership, money or closure boundary evidence. A
  dedicated `PortfolioClosure` parser leaves the metadata PATCH parser intact.
- Deletion-only owner/IP attempt buckets reuse existing bounded30/min and
  60/min settings/TTL primitives. Rotating request keys or owners cannot evade
  the relevant limits. The independent durable SQL200-outcome/day quota still
  permits original outcomes and owned-closed acknowledgements before quota.
- The thin route captures owner/root/key/name/policy in immutable `ClosureIntent`
  and invokes the actual proven service.200 contains exactly string
  `portfolio_id` and `state:"closed"`, including original/fresh owned-closed
  acknowledgement. No retained name, cash, position, closure time or replay
  distinction is returned. Foreign/missing are the same private404.
- `close_owned_portfolio` maps only named original-body409, missing404 and
  quota429 dispositions; operational DB/proof refusals are private503 with
  Retry-After5. A returned durable `confirmation_changed` outcome has already
  committed before the name-review409 is exposed. Arbitrary500 response
  failures use the existing private original-request recovery copy without
  exception details. No complete-proof check or transaction boundary is skipped.
- Actual public HTTP tests exercise crypto buy→delete with a real holding,
  conserved cash/quantity/basis and one unchanged fill; no liquidation or
  transfer is manufactured. Old original fill execution then refuses404.
- Real committed500/503 failures and actual client-task cancellation after the
  service commit retain the original root/key. Replaying that original succeeds
  without another outcome or grant. A same-name replacement has a different ID;
  neither closure key nor original creation key can target/resurrect it.
- Actual later concurrent calls replay a permanent name refusal after rename
  back; a fresh reviewed key can close once under concurrent duplicate calls.
  Foreign callers cannot acknowledge a closed original.
- Delete-last preserves `/me` and repeated empty discovery/overview. A new
  browser actually obtains an OTP via the synthetic outbox, verifies it,
  refreshes its session and remains at zero. Only explicit creation returns a
  new ID and its once-only$10,000 grant; logout still revokes the session.

## Actual verification

Raw receipts: `/tmp/birja-phase14-plan07/`; source/log hashes, commands and
resource identities are captured in `receipt.json`.

| Check | Actual result |
|---|---|
|Task1 RED|Missing DELETE405;7.53s, `task1-red.log`|
|Initial minimal commit/replay GREEN|1passed7.29s, `task1-green-initial.log`|
|Task1 complete matrix|9passed57.80s, `task1-full2.log`|
|Initial completed identity/recovery matrix|4passed25.74s, `task2-green2.log`|
|Clean complete current API/identity/transport group|50passed82.33s, `final-current.log`|
|Additional test-only committed503/client cancellation variants|2passed13.03s, `postcommit-variants.log`|
|Scoped Ruff/check/format|All7 touched Python paths pass;7 already formatted|
|Scoped mypy|All5 touched source modules pass|
|Historical migration/SQL bytes|No change from9bd8f13, including all existing0021–23 assets|
|Owned cleanup|Allbirja-p14-07 containers/networks/volumes removed; project-label queries empty|

The clean50-case command covers10new API cases,4new identity cases and36
existing transport cases, including parameterized metadata boundary tests. The
two added postcommit tests ran afterward; runtime source did not change. These
are distinct receipts, not a claim of a new combined52-case command or any
whole-phase CI/security/recovery qualification. The first hash-capture attempt
had a receipt-only cwd-prefix error; unchanged files were captured immediately
after launch and compared afterward. No runtime bytes changed during the runs.

## Deviations and corrected diagnostics

1. **Rule2 — private pre-route schema refusal.** A real corrupted retained-name
   test reached `main.py` write admission before ManagementRoute. Its existing
   schema503 had neither PRIVATE headers nor Retry-After. With parent agreement,
   added only those headers, preserving status/body and every admission check.
   The real DELETE regression now proves the earlier refusal is private. Include
   main.py explicitly in independent review and later coverage assessment.
2. The private HTTP disposition adapter in `portfolio_closure.py` was needed by
   Task1's route and therefore landed with Task1 rather than waiting for Task2.
   It wraps the existing transaction/proof service without changing its core.
3. Test fixtures initially used the inherited SQL harness's reserved `.test`
   email domain, which actual OTP validation rejects. They now use unique
   `example.com` fixture addresses and a local OutboxSender; no real email is
   sent. A fresh browser must use its actual rotated CSRF cookie rather than
   the initial synthetic token. Neither correction changed auth/CSRF validation.
4. One added IP-limit test initially lacked its pytest import. That diagnostic
   failed after6cases and is retained, not reported as passing. The corrected
   current command is the clean final receipt.

## Deferred integration prerequisite — Plan15

The combined command that also included `test_portfolio_creation.py` passed50
cases then failed its first old fixture before the test body:
`management_api` uses the explicitly historical0020 authority, while current
app admission correctly requires0023. Receipt `final-affected2.log` records
50passed/1error87.13s; it is **not** a successful full command. The exact
Plan15 handoff is in `deferred-items.md`. No admission widening, fixture skip,
current-over-historical overlay or new waiver was introduced. Full phase
qualification must resolve that prerequisite before its complete suite.

## TDD gate compliance

Task1 has real missing-route REDad060ea followed by GREEN0f970f8. Task2 is
behavioral verification of the transaction/identity semantics already delivered
in prior plans and Task1; its first two scenarios passed immediately. Fixture
email/CSRF failures are not relabelled as feature RED. Task2 is an explicit
test-only commit; no manufactured failing runtime behavior or additional
feature RED is claimed.

## Remaining handoff

- Plans08/09/10 must integrate closed-event policy, lifecycle races and every
  normal read/original-reference final fence; public DELETE is now available
  for their fixtures. Initial service-only recovery acceptance is insufficient
  as the final public lifecycle proof;09/17 must exercise the API.
- Frontend11–14 must preserve the exact canonical original body/status contract,
  metadata-only recovery and unknown500/503/cancellation semantics. Active GET
  alone cannot cancel an unresolved original or authorize a new target/body.
- Plan15 must adapt the retained creation API fixture explicitly;16 adds new
  critical paths without removing61 originals, and18 runs whole gates.
- UI/native200 acceptance, encrypted same-archive cold/TLS/rollback proof and
  independent phase-goal verification remain pending. No provider/production,
  dependency, publication, user UI approval or live-stock activation occurred.

No blocking runtime stub remains in Plan07's scoped API. No authentication or
package gate occurred. Financial records are retained rather than purged.

## Self-Check: PASSED

All created source/test files exist; task commitsad060ea/0f970f8/a1dc80f are
present. Clean current and focused postcommit receipts pass, source pins match
within the stated limits, old Alembic assets are unchanged, scoped static checks
pass and owned resources are removed. The unresolved Plan15 fixture prerequisite
and later whole-phase gates are explicitly retained, not marked complete.
