# Phase 8 source coverage audit

Planning audit,2026-11-11. Thirteen focused plans/29 tasks/11 waves.
No08-CONTEXT.md exists; approved requirements and owner instruction to research,
create the existing-system UI contract and plan supply decisions. No D-IDs invented.

| Source | Item | Covered by plans/tasks | Status |
| --- | --- | --- | --- |
| GOAL | Explainable units, basis, historical eligibility and uncertainty preventing unsafe valuation/trading |01–13; actual stock execution stays disabled | COVERED |
| REQ | DIV-01 structured ordinaryUSD announcements, IDs/dates/rates/revisions and rechecks |03-01/02,04-01/02,06-01,07-01,08-02 | COVERED |
| REQ | DIV-02 historical exclusive cutoff including trades/splits, before/after buys/sales |05-01/02,06-03 | COVERED |
| REQ | ACT-01 exact straightforward forward splits/whole shares/basis/immutable fills |03-02,06-02,09-02 | COVERED |
| REQ | ACT-02 unsupported/disputed/fractional actions held, unavailable valuation, audited resolution |06-01,07-01,08-01/02,09–11 | COVERED |
| REQ | ACT-03 once-only/recovery, ordering with fills/entitlements, monitoring loss/recovery |02,05,06,07,08-03,12 | COVERED |
| RESEARCH | Existing stack only, no SDK/package/queue/new worker | All execution rules;07 existing scheduler | COVERED |
| RESEARCH | Current REST process_date inclusive filters/data_quality=all/knownIDs exclusivity/pagination; deprecated paper API forbidden |04-01 | COVERED |
| RESEARCH | Actual optional source fields/currency unknown, ordinary classification and observed/source/economic times distinct |03-02,04,06-01 | COVERED |
| RESEARCH | Finite mutation replay insert/update/delete, inclusive cursor, all-US transport permission, bounded framing/unrelated discard |03-01,04-02,07-01 | COVERED |
| RESEARCH | Missing/empty does not equal cancelled; no guaranteed creation timing/history/latency or green-poll omniscience |04,07,13-02 | COVERED |
| RESEARCH | Distinct action product/purpose/scope/capabilities and durable normalized accounting/DB/backup rights |03-01,12-03,13-02 | COVERED |
| RESEARCH | Native transaction gate, deterministic order, no provider IO under financial locks, post-lock real economic clock |05-01,06,07-01,08-01,09-02 | COVERED |
| RESEARCH | Stable economic identity vs provider alias vs immutable local source revision/observation |01,06-01,08-01/02 | COVERED |
| RESEARCH | Immutable historical ownership/journal baseline/causal sequence, future Phase9 firstfill contract |01,05,06-03 | COVERED |
| RESEARCH | T+1 verified designated ex-date/genuine regular opening/DST; no record-date arithmetic or guessed holiday |03-02,05-02,06-03 | COVERED |
| RESEARCH | Same-boundary split/dividend explicit denomination/order and due-bill ambiguity |03-02,05-02,06-02/03 | COVERED |
| RESEARCH | Exact rational all-owner split, fractional/overflow whole-instrument refusal, unchanged total basis/fills |03-02,06-02 | COVERED |
| RESEARCH | Late effective discovery/revised applied split/changed cutoff/cancellation holds; no inverse/double adjustment |06-01/02/03,08 | COVERED |
| RESEARCH | Durable coveragebaseline/futurehorizon/retainedknownIDs/cursors/partialprogress, completecatchup required for health |07-01 | COVERED |
| RESEARCH | Independent 60s cycle,<=120s lease and finite budgets as internal policy, aggregate accountquota review |04,07,12-01,13-02 | COVERED |
| RESEARCH | Narrow privileged audited reconciliation, current expected generation/revision/epoch, no arbitrary SQL healthy override |01-02,08-01/02 | COVERED |
| RESEARCH | Current committed API authority, safetyepoch/unit epoch separate, post-splitquote invalidation and known boundarydeadline |09-01/02 | COVERED |
| RESEARCH/CODE | New StockQuote.unit_epoch does not break validated-quote column mapping; existing epoch-zero persistence works and nonzero units fail closed until authenticated gate-bound provenance |01-01 compatibility/regressions;09-02 complete unit gate/races | COVERED |
| RESEARCH | Strict frontend safety envelope, authenticated lifecycle, fullRTT, perstock epoch/stale replies and exact deadline purge |10-01/02 | COVERED |
| RESEARCH/UI | Independent action/halt/session/quote/trading states, no new trade/operatorcontrols, safe fixedcopy and timestamp honesty |09–11 | COVERED |
| RESEARCH/UI | Responsive sixcolumn/list, wrap warnings, contextual live region/retryfocus/zoom/reducedmotion |11-01/02; approvedUI-SPEC | COVERED |
| RESEARCH | Additive0011/0012, restrictive quantity-only grants, actual upgrade/fresh TLS parity, guarded financial downgrade |01,02-02,08-01/03 | COVERED |
| RESEARCH | Exact predecessor/new revisions/schema/rows/sequences/functionACL and retained samearchive restore+replay before rollout |02,08-03,12-02/03 | COVERED |
| RESEARCH | Meaningful RED/GREEN, real PG races/failure injection, strict criticalcoverage/audits/images/independentreviews | Every eligible task;12 | COVERED |
| CONTEXT | No artifact; use approved requirements/owner instruction, no fabricated D-IDs | Execution rules in every plan | NOT APPLICABLE |
| OWNER | Phase7 localwork/UI accepted, actual livegate explicitly deferred; continue isolateddevelopment | Every plan;12/13 | COVERED |

## Dependency graph and ownership

| Wave | Plans | Needs | Creates |
| --- | --- | --- | --- |
|1|01,03| Existing0010/schema and pure admission/calendar patterns | Constrained0011 + epoch-zero quote-writer compatibility/nonzero refusal + pure exact action/permission contracts |
|2|02,04|01 for02;03 for04| Exact0011 recovery/TLS + bounded current provider adapters |
|3|05|02,03| Instrument serialization and causal historical ownership |
|4|06|04,05| Immutable revisions, once-only splits and entitlements |
|5|07|06| Complete durable catch-up/monitor health, disabled loop |
|6|08|07| Narrow0012 operator function/CLI and exact recovery/TLS |
|7|09|08| Current committed safe API/unit quote provenance |
|8|10|09| Strict monotonic deadline-bound client |
|9|11|10| Responsive safe Markets UI/browser evidence |
|10|12|11| Actual full local gates and concrete acceptance packet |
|11|13|12| Owner newUI acceptance/external disposition checkpoints |

Same-wave01/03 and02/04 have disjoint files_modified. Later overlapping files
have transitive dependency edges and later waves. All13plans have requirements,
must-haves/keylinks and explicit STRIDE mitigations with automated verification.
29tasks each have exact files/read_first/action/verify/done; eligible tasks carry
TDD behavioral expectations. Plans06/08/12 each have3tasks, others2, preserving
cohesive executor scope without merging distinct financial/provider/UI contexts.
Plan01 owns stock_quotes.py/test_stock_quotes.py only for schema-adjacent explicit
column compatibility and zero-unit guards. Plan03 does not modify these files.
Plan09 later extends them with authentic instrument-gated unit provenance and
two-session quote/split races; its existing dependency chain preserves ownership.

## Explicit exclusions, not gaps

Post-planning CLI gap analysis checked all 26 milestone requirements against
this phase's plans: the five Phase 8 requirements are covered. The other 21
belong to Phases 7, 9, 10 and 11 per approved traceability; their absence from
Phase 8 plans is intentional, not a dropped Phase 8 requirement. No CONTEXT.md
exists, so there is no separate decision-ID coverage set.

Actual stock fills/combined portfolio/status execution integration belong to9;
cash payments/corrections/public event History belong to10; final integrated
mixed-asset acceptance belongs to11. Feature-local recovery/concurrency tests
are included now. Real settlement delays, fractional cash-in-lieu, guessed
liquidation, reverse/merger automation, new provider grants/payment/deployment
are excluded by approved scope. Unsupported genuine financial repairs remain
held for separately reviewed scoped repair, never arbitrary operatoroverride.

## Reachability and planning risks

- Scheduler enabled only through explicit settings plus current distinct rights;
  local synthetic fixtures demonstrate all phase behaviors with defaults off.
- Operator CLI calls only its narrowly granted0012 function; no public route.
  Function and0012 recovery proof precede runtime calls.
- Future Phase9 stockfill must acquire instrument before account/holding and
  append economic journal in the same transaction from its first actualfill.
- API final committed action authority reaches strict client and StockSection
  on existing /markets; known boundaries expire in querycache before polling.
- The main failure risks are guessed continuity, wrong economic units/time and
  broadened privilege. Completecoverage holds, exactjournal/race tests and real
  SQLSTATE/TLS/functionACL proofs address each before activation.
- All requested local behaviors have plans. External action account rights,
  replay/latency and Phase7 live evidence remain explicit gates; nothing here
  claims those passed. No implementation/testing or activation occurred.

