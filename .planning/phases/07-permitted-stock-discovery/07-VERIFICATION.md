---
phase: 07-permitted-stock-discovery
verified: "2026-11-16T16:02:37.806599+00:00"
status: human_needed
score: local implementation and actual20mappings evidenced; partial quote coverage observed; rights/activation/whole-phase acceptance unresolved
reviewer: coordinator verification pass using saved independent reviews and hosted CI
---

# Phase 7 verification — actual measurement recorded; acceptance remains open

No full Phase7 pass is claimed. Plans01–13 are complete; Plan14 now has tasks01/02 performed, with final live acceptance unresolved. Existing UI acceptance is retained. This coordinator update is not a newly independent code/security/UI audit. Nov16 used only the already-approved read-only campaign; no admission import, service/production action, package change, schedule or waiter occurred. The earlier Nov14 audit made no private requests.

## Actual November16 campaign result

The already-approved manual replacement ran2026-11-16 from15:51:29Z to16:00:55Z
(18:51–19:00Moscow). Exactly30attempts:20Paper reference GETs and10IEX quote
batches; no retry, second campaign, background schedule or activation. The
separate single-use claim is consumed and must not be removed/reused.

All20symbols mapped to distinct provider asset UUIDs with expected listings,
active us_equity/tradable observations. Common-stock subtype/USD remain the
separately reviewed catalogue/product bases; absent Asset fields were not
invented. Ten regular-session samples accepted183/200individual quotes, with
reported integer ages0–41seconds (<120). Valid counts were
18,18,18,17,17,17,19,20,19,20. MSFT was rejected as invalid in samples1–6,
META1–7, andGOOGL4–6/9. No raw payload was retained, so the exact reason beyond
adapter invalid is unknown; do not call these stale quotes or infer a provider
outage. All20 were valid in samples8and10. Missing/invalid observations were
retained honestly rather than replaced by zero or a second feed.

Sanitized durable receipt: [07-LIVE-20261116-RESULT.json](07-LIVE-20261116-RESULT.json).
Original private receipt SHA256: `2b3824e471f65ae340aaa37a685c1e3d114172939ff5ed34440202eeb63f659e`.
Precheck/source/helper identities and52offline checks:
[07-MANUAL-20261116-PRECHECK.md](07-MANUAL-20261116-PRECHECK.md).

This supplies actual mappings/account access and observed IEX ages. It does not
independently verify multi-user display/storage/backup rights, action/status
capabilities, continuous twenty-symbol coverage, production compatibility or
owner live-state acceptance. Owner's existing UI acceptance is retained.
Keep all six whole-phase requirements pending and stock admissions disabled.
No extra measurement is authorized by this successful campaign. A follow-up
must have a separately bounded scope; do not reuse the November11 claim or
Nov16 result directory. Phase12 remains at its separate Plan26 repair task.

## Historical November14 verification (preserved)

The following statements describe the prior audit, before the actual Nov16 run.

## Roadmap criteria and requirement disposition

| Criterion | Evidence | Verdict |
|---|---|---|
|1 twenty stable NYSE/Nasdaq stock identities and IEX attribution,STOCK-01/02| Existing reviewed catalogue/discovery/browser and owner acceptance; current hosted e2e passed at ed37d69 | Local implementation/UI evidenced; actual20provider mappings remain unobserved |
|2 source timestamps/minute refresh/strictage/STOCK-03| Current quote adapter/rules/scheduler, previous real isolated tests, full hosted backend/e2e | Local enforcement evidenced; actual IEX account coverage/current-session ages not measured |
|3 product rights/scope/quota/denial and crypto independence,DATA-01| Product-specific denial logic and saved owner attestation; later action capability changes reviewed in their phases | Gate implementation evidenced; no independent provider grant determination, actual live checks and required activation scope unresolved |
|4 regular sessions/holiday/earlyclose/DST,MKT-01| Existing actual calendar consumers/tests; official schedules plus current installed calendar | Local calendar behavior evidenced; old dated campaign not a live pass |
|5 accounts/cash/identities/crypto history/restrictedTLS,SAFE-01| Phase7 compatibility and Phase11 complete recovery; new hosted ops passed exact mixed-asset recovery/TLS/rollback | Local migration/role compatibility evidenced; no production rollout implied |

All six primary Phase7 requirement checkboxes remain pending under the existing
whole-phase acceptance boundary. No local feature was declared broken because
external evidence is absent. Existing initial UI and subsequent Phase8–11 owner
acceptance are retained; no repeat generic UI/nativezoom question is required.
Later phase controls supersede the original staged no-stock-ticket UI; synthetic
stock execution does not establish live provider activation.

## New verification facts

- Known old runner PID/path absent in same-host process checks. Originalclaim
  remains; runner.log0bytes; no result-20261111/receipt.json. Outcome/requestcount
  unknown. Do not infer no calls or success from a missing process/receipt.
- Temporary measurement/runner files exactly match recorded hashes. Only the
  pinned application admission module changed; the old actual runner refuses
  that hash. Current source hashes are recorded below. Old scheduled day/window
  is expired; no additional run was authorized by the original one-shot scope.
- Existing network-free measurement+runner tests:63passed/2failed/4warnings,
  12.21s. Both failures are audited_hash_mismatch before live work. Preserve old
  artifacts and review a fresh source-bound campaign rather than bypass guards.
- Saturday2026-11-14 has no regular session. Installed calendar gives next
  sessionMonday2026-11-16,17:30–00:00Moscow(closeNovember17); official schedules
  corroborate regular hours and no listed November16holiday. Fresh public review
  is still required before actual future collection; current review is dated.
- HostedCI43588776865 at ed37d69 independently passed backend/frontend/image/
  e2e/ops/ci-pass, including actual current0014 and legacy0008 recovery paths.
  Merge78de5bd has the same tested feature source; current local changes are
  documentation receipts. No duplicate full suite/campaign is needed now.

## Current relevant source hashes

- `backend/app/services/alpaca.py`: `41ef322b908cf7e9f1e442c42b732e8252bb3d647a77733376556ab7caf49052`
- `backend/app/services/stock_admission.py`: `ec5ddce4ca362e28547dc42a698b43d90349f23436ec0c6572905c9f6c4fb315`
- `backend/app/services/stock_quote_rules.py`: `298d2d4d246dc4a14d526a164709ef6cc23eb79f5a4319265325390fac713d3f`
- `backend/app/services/stock_sessions.py`: `cc2e2069ff3b50f77bc318fda862f4c55347e50bd4aef7a033c79d0f1a3ffb22`

## Historical November14 continuation proposal

1. Replacement campaign timing/budget approved2026-11-14: “Approve Monday’s
   manual campaign (Recommended)”. Scope:07-LIVE-VERIFICATION-PROPOSAL.md.
   No process scheduled/launched; original oldclaim/run remains preserved.
2. Refresh current source/affected checks/review and public calendar evidence
   within24hours of the actual regular-session campaign. No new package needed.
3. Perform the approved bounded actual reference/quotes measurement and preserve
   sanitized receipt/results; review remaining rights/action/status/retention
   limits honestly. Do not turn an account-access pass into unrestricted rights.
4. Re-run final goal verification only with those results. Keep phase pending,
   collection/execution disabled and milestone unarchived until required truths pass.

Sources checked2026-11-14: [NYSE](https://www.nyse.com/trade/hours-calendars),
[Nasdaq](https://www.nasdaq.com/market-activity/stock-market-holiday-schedule).
Current hostedCI: https://github.com/YokAI-open/Birja/actions/runs/43588776865
