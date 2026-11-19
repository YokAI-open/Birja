---
phase: 14-end-strategies-safely
plan: "11"
subsystem: browser-deletion-recovery
tags: [typescript, transport, session, immutable-intent, recovery]
requires:
  - phase: 14-07
    provides: Private canonical DELETE and durable original outcomes
provides:
  - Exact canonical immutable deletion intent and minimal receipt transport
  - Opt-in shared JSON transport with current-context checks at every await
  - Bounded owner-bound same-tab original recovery without implicit requests
affects: [14-12, 14-13, 14-14, 14-17, 14-18]
tech-stack:
  added: []
  patterns:
    - A durable terminal result is distinct from a refusal of a later retry
    - Context revocation and cancellation leave the original economic outcome unknown
key-files:
  created:
    - frontend/src/api/portfolioDeletion.ts
    - frontend/src/api/portfolioDeletion.test.ts
    - frontend/src/lib/portfolioDeletionAttempt.ts
    - frontend/src/lib/portfolioDeletionAttempt.test.ts
  modified:
    - frontend/src/api/client.ts
    - frontend/src/api/client.test.ts
key-decisions:
  - deletePortfolio requires the caller's isCurrent guard; immutable target/body capture occurs before any await.
  - Only the durable portfolio_confirmation_changed outcome has terminal=true; a refusal alone never resolves a previous unknown original.
  - Existing apiFetch callers keep their interface; strict guardedJsonRequest is opt-in on the same fetch layer.
requirements-completed: []
requirements-progress: [PMGT-03, PCTX-03, PSAFE-01]
duration: 12min measured first-RED-to-final-test interval
completed: 2026-11-19
---

# Phase 14 Plan 11: Exact Browser Deletion and Durable Original Recovery

**Strict guarded transport and bounded metadata storage preserve the original
reviewed deletion across unknown results without implicit submission or target
replacement.**

## Task commits and measured evidence

| Task | RED | GREEN | Result |
|---|---|---|---|
|1 — strict original transport|1c52fbb|e4c886f|53deletion/shared-client cases pass1.47s; full frontend typing and scoped lint/format pass|
|2 — bounded original recovery|a330a37|9ecca8f|15storage cases pass1.32s; final69focused cases pass1.50s|
|1 follow-up — real admission outage shape|dcee0e3|bd5f9be|Actual schema503 response retains Retry-After5 while discarding its optional message; strict terminal409 shape remains code-only|

The first transport RED at13:33:03UTC fails on the missing transport module,
and storage RED at13:38:11UTC fails on the missing storage module. No existing
passing behavior was manufactured into a failing test. The final complete
frontend run at13:44:04UTC passes1239tests/57files in22.34s at9ecca8f.
The measured first-RED-to-final-test interval is approximately12minutes and
does not include initial mandatory context reading. Parent owns STATE/ROADMAP;
no whole requirement is marked complete.

## Implemented behavior

- Canonical bigint IDs remain strings through the PostgreSQL bigint maximum;
  UUIDv4, NFC reviewed name and policy are exact. Input is copied/frozen before
  CSRF/auth/network/JSON awaits; caller mutation cannot replace target or body.
- Success requires200/application-json and exactly the original string ID plus
  closed state. Wrong ID, extra fields, wrong status/content type or malformed
  JSON remain unknown. Errors retain only allowlisted codes, safe status/wait and
  generic messages. A durable code-only name409 is terminal; original-key
  conflicts, auth/quota refusals and ambiguous5xx do not terminate a previously
  unknown original. Network loss, abort and context revocation are unknown.
- The optional shared `guardedJsonRequest` uses the existing fetch/CSRF/shared
  refresh layer, checks the supplied current-context callback before and after
  each await, and permits only one identical auth-recovery retry after a valid
  not_authenticated response. It never retries transport/5xx failures. Existing
  apiFetch consumers retain their previous interface and behavior.
- Storage uses the separate `birja:portfolio-deletion:v1` key and at most16000
  UTF-8 bytes. A cryptographic random nonce plus opaque owner binding associates
  one tab-local unresolved immutable original. No money, receipt, email or token
  is stored, and no original appears in a URL/log/broadcast. Creation storage is
  untouched. The binding is recovery context, never server authorization.
- Persist validates and reads back exact bytes before returning the frozen
  original to a sending caller. Corruption, byte overflow, quota/read-only/readback
  failure and a different pending original fail closed. Concurrent opens are
  serialized; stale owners/epochs cannot persist or resolve newer state. A stale
  observer cannot erase a subsequently replaced original. Opening/reading a
  marker performs no network request; recovery stays explicit.

## Verification and evidence limits

Raw receipts: `/tmp/birja-phase14-plan11/`, with final tested source hashes and
commit identities in `receipt.json`.

| Check | Actual result |
|---|---|
|Transport/shared-client focused group|53passed1.47s|
|Storage focused group|15passed1.32s|
|Affected creation/management/session transport group|139passed4.87s before the final outage/mandatory-guard strengthening|
|Final three-file focused group|69passed1.50s|
|Final whole frontend unit suite|1239passed/57files22.34s|
|Full frontend typecheck|`npm run typecheck` exits0|
|Scoped ESLint/Prettier|All6source/test files pass|
|Diff/stub/ownership checks|No whitespace errors, TODO/FIXME/placeholder stubs or unexpected tracked deletion|

Final tests ran with source unchanged; all six source/test files match9ecca8f.
No DB/browser/provider/production operation, package installation or cloud
access occurred. No processes/resources remain owned by this plan. The
unrelated `.claude/` directory is preserved. These unit results do not establish
new implemented UI acceptance or native200%zoom; hooks/UI and actual browser
qualification remain downstream.

## Deviations from Plan

**[Rule2 — prerequisite] Opt-in guarded shared fetch transport.** Existing
apiFetch hides response content type/error shape and does not accept a
current-context callback around its internal CSRF/auth awaits. A wrapper in the
four planned files could not enforce the required boundary. Parent authorized
the narrow prerequisite in client.ts/client.test.ts. Existing caller interfaces
remain unchanged; the full frontend suite proves affected regressions.

**[Rule1 — strict-parser correction] Preserve a real service outage wait.** The
actual global schema-admission503 includes a safe optional message slot. The
first strict parser discarded its status/wait along with the body. A RED/GREEN
regression now admits that slot only for auth/service errors, discards its
contents and retains bounded retry evidence;409 terminal outcomes remain exact.

Full typing caught one closure-narrowing error during implementation; capturing
the narrowed detail object fixed it before GREEN. No package or architecture
change, exception expansion or new security waiver was introduced.

## Hook 12 / downstream interface handoff

- `deletePortfolio(intent, signalOrUndefined, isCurrent)` requires the captured
  owner/session/operation guard. It returns frozen `{portfolioId,state:"closed"}`
  or a safe `PortfolioDeletionError`. Do not discard an earlier unknown original
  on `outcome === "refused"`; only the receipt or `terminal === true` supplies a
  definitive original outcome. All markers/actions still need the hook's lease.
- `openDeletionRecovery(owner,isCurrent)` returns a metadata-only handle. Its
  `attempt` getter may throw when stale or corrupt. Synchronous `persist(intent)`
  returns the frozen exact original only after storage readback. Call it before
  sending. `resolve()` checks the observed original and must only follow a
  definitive original result. `clearDeletionRecovery(isCurrent)` is guarded
  logout/owner-change cleanup; it never sends a request.
- New marker names and body fields must remain separate from creation and
  financial original attempts. Hook12 owns pending/unknown root quarantine,
  explicit recovery, no auto-mutation and sibling independence; Plan13 owns
  lifecycle invalidation and Plan14 owns the new surfaces.

## Deferred observation — not accepted or waived

While checking the server contract, `backend/app/services/portfolio_closure.py`
was observed to reject owner/root IDs above9007199254740991, whereas the strict
API/browser ID contracts permit PostgreSQL bigint strings through9223372036854775807.
Parent was notified and instructed this remain an unresolved09/10authority/privacy
follow-up unless existing schema bounds explain it. No backend file was changed
here; the browser retains the full canonical bigint-string contract. This is
not an acceptance, waiver or claim that the mismatch is fixed.

## Self-Check: PASSED

All four new files and two authorized prerequisite files exist. All six task/repair
commits exist; source matches the final tested9ecca8f. Full/frontend focused tests,
typing, scoped lint/format and diff checks pass. No stub, pending task or new
human checkpoint remains within11. Parent must independently review before
continuing; whole Phase14 requirements and later qualification remain pending.
