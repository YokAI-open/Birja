---
phase: 10-dividend-cash-and-event-history
status: secured_implemented_pending_human
reviewed: 2026-11-13
review_mode: independent-agent
initial_reviewed_head: f47af659e579f60015a740cbbafbf03b345ad837
reviewed_head: 48d970c262c7f52bb5692d38db0748e5169cf389
diff_base: 5925b52
register_authored_at_plan_time: true
asvs_level: 1
asvs_scope: targeted-controls-only
block_on: open
threats_total: 72
threats_closed: 70
threats_open: 0
threats_pending_human: 2
unregistered_flags: 0
accepted_phase10_risks: 0
---

# Phase 10 security mitigation audit

**SECURED for implemented technical scope; HUMAN_NEEDED for phase completion.**
No absent implementation mitigation was found. All 72 declared IDs are mapped
below: 70 are fully verified and two retain explicit Plan 18 human completion
pending. `threats_open: 0` counts absent code mitigations; it does not mean 72
fully completed threats, owner acceptance, native 200% verification or permission
to advance the phase. The two pending entries are neither accepted risks nor
fabricated CLOSED outcomes.

Independent security-auditor source/evidence pass, separate from the coordinator
and independent code review. Implementation files were read-only. This auditor
started no stack, changed no source and reran no long gate. Local Python checks
independently recomputed all four migration function-body hashes against the
producer constants and all 384 then-current source hashes plus 12 sealed artifact
hashes in the retained integrity receipt; all matched. Behavioral outcomes below
are attributed to the coordinator's actual logs and read test assertions, not to
new execution by this auditor. No product-wide ASVS certification is claimed.

## Scope and trust boundaries

Inputs: AGENTS/CLAUDE, GSD adapter, security role/skill/workflow/ui-brand,
PROJECT/REQUIREMENTS/ROADMAP/STATE, all 18 PLAN threat blocks and task actions,
01–16 SUMMARY threat sections (including case-varied headings), C01–C06/C03a/C05a,
16-SUMMARY, LOCAL-PROOF, IMAGE-REPAIR-REVIEW, Plan 17/18, current HUMAN-UAT and
independent REVIEW. Actual owning SQL, service, worker, endpoint, schema, client,
hook, UI, dev helper, Compose/CI and producer/restore code and adversarial tests
were inspected; summaries alone are not closure evidence.

| Boundary | Untrusted/changing input | Verified controlling location |
| --- | --- | --- |
| Scheduler → financial SQL | Retained work IDs/fingerprints, changing rights/revision/status | `0014_dividend_accounting.py:134`, `:374`, `:479`; exact retained rows derive owner and cash |
| SQL → cash + History | Duplicate work, concurrent spend, held/revised target | Migration `:392`, `:411`, `:448`, `:473`, `:523`; immutable ledgers and single transaction |
| Session → mixed History | Forged auth/cursor/foreign original | `core/deps.py:90`; `services/event_history.py:77`, `:150`, `:274`; route `api/v1/event_history.py:26` |
| API → browser | Malformed money/lineage, old owner or old same-owner session results | `api/eventHistory.ts:63`, `:296`; `hooks/useEventHistory.ts:15`, `:58` |
| Source/archive → restored clone | Corrupt function/schema/ACL/rows/sequence state | `backup-snapshot.py:124`, `:202`, `:241`; `verify-restore.py:931`, `:951`, `:1038` |
| Explicit local administrator → dev definer rights | Wrong target, unsafe role/membership/object owner | `app/db/dev_bootstrap.py:11`, `:77`; fixed grants after provenance checks only |
| Build inputs → images | Unapproved package drift, known HIGH/CRITICAL | Locked dependencies, exact approved Node repair, CI strict five-image gate; evidence S below |
| Review evidence → owner answers | Historical captures or old acceptance mislabeled current | Current `10-HUMAN-UAT.md` explicitly pending; Plan 18 blocking human tasks |

ASVS L1 and `block_on: open` are the supplied audit scope/strict implementation
gate. `.planning/config.json` has no explicit security override; no setting was
silently changed. Every plan disposition is **mitigate**; there are no Phase 10
accept or transfer entries to substitute for implementation proof.

## Concrete evidence keys

These keys are used by the individual threat rows. Each connects owning code to
actual negative/expected-value assertions and recorded execution.

| Key | Source control and behavioral evidence |
| --- | --- |
| A — storage/lineage | Migration `0014_dividend_accounting.py:92`, `:571`, `:720`, `:989`: immutable UPDATE/DELETE triggers, owner/event/coin/revision/entitlement composite FKs, finite cents/range/state constraints, conditional unknown terms, always-identity BIGINTs, successful-target partial uniqueness and NULL-safe held-status uniqueness. `test_dividend_schema.py:117`, `:126`, `:161`, `:245`, `:285`, `:335`, `:367`, `:399`, `:423` assert cross-link refusal, immutable originals, uncertainty/dedup, genuine runtime write denials and preserved populated 0013 state. Populated downgrade guard precedes DDL at migration `:1006`. |
| B — financial authority | Migration `:134` private authority, `:374` apply and `:479` hold: retained IDs/fingerprints only; fixed owner `birja_migrator`, pinned `pg_catalog,public,pg_temp`, schema-qualified static statements; creating-transaction PUBLIC revocation and scheduler-only entry EXECUTE at `:534`. `test_dividend_authority.py:32`, `:259`, `:335`, `:348` exercises exact bootstrap matrix, original replay, forged identity and temporary shadow tables; declaration-tamper test at `:836` rejects changed OUT types/names/modes. `deploy/db/bootstrap-roles.sql:50` authenticates full identity before grants, `:258` restores only fixed payout ACLs. |
| C — exact money/immutable replay | `services/dividend_rules.py:60` uses bounded Decimal and independent 64-digit HALF_EVEN context. Migration `:411` computes exact quantity × rate and explicit half-even cents; `:448` subtracts original plus only stored applied deltas. Original/successful-target replay at `:396` precedes renewed authority and makes no cash effect. `test_dividend_rules.py` literal tie/range/uncertain vectors; SQL same vectors `test_dividend_authority.py:308`; `test_dividend_payments.py:41`, `:187`, `:271`, `:294`, `:434`; `test_dividend_corrections.py:133`, `:162` prove due historical eligibility, no older fallback, A→B→A, no-change, funded successor and unchanged original/starting grant. |
| D — no-cash uncertainty | Migration `:479` takes existing payment ID/current revision only, derives owner/latest entitlement/status and rechecks current durable rights, revision and final full row snapshot; never updates accounts. NULL target/proposal and applied zero are constrained. Worker `tasks/dividends.py:48` scans paid anchors independently of eligible targets. `test_dividend_corrections.py:30`, `:86`, `:105` asserts missing-current-target hold, dedup, no pre-anchor credit and rights refusal. `test_dividend_scheduler.py:59` proves helper empty → actual worker/restricted SQL → visible owner History hold → repeat unchanged → reviewed applied successor. |
| E — waits/atomicity | Migration `:392`, `:473`, `:493`, `:523`: instrument gate → owner Account FOR UPDATE; all deferred constraints made immediate before final advancing-clock full-row authority comparison; then return/commit. `services/dividends.py:45` owns exactly one transaction, accepts no active caller transaction, binds values and sanitizes SQL errors. `test_dividend_waits.py:143`, `:200`, `:238` observes actual PostgreSQL blocking before revision/rights/hash/cutoff/unit/latest-target/monitor mutations and expiry; both cash and rows roll back. Deferred trigger is test-only synchronization, not a claim of a natural production deferred trigger. `test_dividend_concurrency.py:32`, `:66`, `:117`, `:139`, `:158`, `:194`, `:213` proves duplicate workers, shared stock/crypto spend, response-loss replay, cancellation and invisible uncommitted rows/cash. |
| F — bounded independent work | `tasks/dividends.py:20`, `:72`, `:93`: 50-candidate verified and independent paid-anchor keysets, shared 100/40s cap, interleave/advance-before-attempt, separate wrap and no immediate failed retry; one owner transaction at a time and no network under financial locks. `tasks/scheduler.py:338`, `:363`, `:377` runs independent supervised loop. `test_dividend_scheduler.py:115`, `:220`, `:231`, `:242`, `:259`, `:280`, `:332` asserts 105-owner 50/50/5/wrap, disabled gate, rights refusal, discovery-inclusive timeout, cancellation cleanup and sold entitlement; scheduler-loop tests assert crypto/other loop progress. |
| G — owner-first read | `services/event_history.py:77`, `:150`, `:274`: strict canonical 512-byte v2 cursor; every UNION branch owner-filtered before complete `(recorded_at,kind_rank,source_id)` seek/limit+1; bounded detailed lookup and offpage original owner join. Route `api/v1/event_history.py:26` uses CurrentUserDep, limit 1..100/default25 and fixed no-store errors; no client owner accepted. `test_event_history.py:111`, `:201`, `:243`, `:273`; `test_event_history_api.py:35`, `:43`, `:55`, `:85`, `:144`, `:194`, `:202`, `:244`; cursor hostile matrix tests: foreign owner/forged boundary cannot disclose, all-kind ties remain stable, original remains scoped, read does not credit, Portfolio counts Account.cash once, old /trades v1 remains separate. |
| H — wire validation | `schemas/event_history.py:70` strict/frozen/extra-forbid models and explicit exact target/lineage validators; `api/eventHistory.ts:71` exact keys/bounded BigInt fixed-point strings/chronology/outcome/lineage parser, at most100 unique items. `services/event_history.py:239` exact Fraction normalizes saved1.5:1 to3:2. `test_event_history.py:164` runs actual PostgreSQL page through installed TypeScript parser; frontend `api/eventHistory.test.ts` tests hostile money, tags, dates, IDs, duplicate/unknown keys and held/applied mismatches. No Number/parseFloat cash authority. |
| I — session/cache lifecycle | `hooks/useEventHistory.ts:15`, `:58`, `:82`: synchronous owner-change removal, owner+epoch query keys, query-instance and abort checks, current-session-only401, cancel-before-invalidate authoritative me/Portfolio/stock context, no local cash credit. `useTrade.ts:18` and `useStockTrade.ts:590` invalidate event History after current-session fill. `hooks/useEventHistory.test.tsx:151`, `:173`, `:217`, `:254`, `:265`, `:283`, `:311`, `:356`, `:398`, `:453` checks same-owner relogin, concurrent append, malformed-page retention, late foreign401, pending financial response cancellation and actual trade hooks. |
| J — truthful browser/UI | `HistoryEventDetails.tsx:47`, `:154`, `:194` shows applied versus proposed cash, no-cash holds and bounded original/back navigation through React text; `HistoryPage.tsx:53`, `:89` enforces same-session focus/load-more intent and accepted-page/error retention. Actual `frontend/e2e/dividends-history.spec.ts` with `deploy/tests/run-stock-browser.py`/dividend fixture calls real services/SQL; synthetic external evidence is labeled. Final16 browser log records49 passed,1 expected deployed-CSP skip,305.7s; UI/API/browser CLI bytes unchanged. These viewport/focus results do not prove native200% or human acceptance. |
| K — exact recovery/quarantine | `backup-snapshot.py:124`, `:202`, `:218`, `:241`, `:379`, `:519` pins complete columns/identities, function prosrc hashes, input+OUT types/names/modes, owner/path/security/volatility/ACL, role flags/membership, schema/triggers/column/table/sequence grants. `verify-restore.py:931`, `:951`, `:1038` authenticates independent constants before fixed reconstruction and withholds app/scheduler payout EXECUTE. `test-stock-recovery-contracts.py:269`, `:688`, `:747`, `:767`, `:836` uses genuine pg_dump/restore fresh cluster, real catalog corruption, direct/transitive SET ROLE escape, changed declarations and actual42501 quarantine. No financial success is mocked; read interception in some contract-unit tests is not itself financial execution. Genuine retained/current-service fixture `dividend-execution-fixture.py:304`, `:367` replays saved originals/successful corrections, held/dedup/reconciled work and History/Portfolio with immutable cash/lineage. |
| L — guarded dev authority | `app/db/dev_bootstrap.py:11`, `:77` validates exact ENVdev/asyncpg/host/port/db/user/noquery, actual admin, DB/effective public-schema ownership, head0014,17 fixed relations/owners/kinds, two always-identity dependencies and four function owners/security modes. Within transaction/advisory lock safe NOLOGIN/NOINHERIT flags and no incoming/outgoing memberships precede fixed schema USAGE,15 SELECT,2 INSERT,2 sequence USAGE and UPDATE(cash) grants to migrator only. Unsafe state is refused unchanged. Both Compose commands have prerequisite → migration → explicit after-migrations → server. `test_dev_bootstrap.py:23`, `:82`, `:127`; actual persistent `deploy/tests/test-dev-bootstrap.py:24`, `:72`, `:141` verifies fresh/upgrade financial original/correction/hold/dedup/reconciled worker/History/replay and unsafe flags/membership/object owner. CI builds actual test-builder before running this regression (`ci.yml:281`, `:299`); `test-ci-ops.py:88` rejects omission/order drift. |
| S — locked approved supply chain | No package manifest or uv/npm lock changed across the Phase10 diff. Only approved existing-family Node24.22.3-r0 image repair is adopted; old ICU/libstdc++ versions explicitly pinned, base/npm integrity unchanged (`frontend/Dockerfile:1`). IMAGE-REPAIR-REVIEW records explicit owner approval and authenticated signed-index → compressed-control checksum → PKGINFO datahash → payload/installed-binary chain. APK has no embedded signature; standalone UNTRUSTED diagnostic is preserved and never called successful. First transitive-drift build rejected; accepted26-package delta changes only Node. Final17 actual-recipe backend builds preserve full prior APK/Python inventories; UID1001/network-none/tmpfs native XNYS/dividend/worker/History/helper-hash passes. Five fresh strict scans including unfixed findings have zero HIGH/CRITICAL; source/report details below. pip audit no findings; npm high gate passes with2low/15moderate, not zero all-severity findings. |
| P — truthful pending owner evidence | `10-18-PLAN.md` contains two explicit blocking human checkpoints; current `10-HUMAN-UAT.md` says no answer and both owner results PENDING, separately binds current-source review ZIP and native desktop200% instructions. `10-UI-SOURCE-HASHES.json` distinguishes current bytes from capture bytes; no Phase9 approval substitutes. Technical controls G/H/I/J and immutable A/K are evidenced; actual new-UI/native200% answers remain absent and are not accepted risks. |

## All plan-time threats

Each row preserves the declared category/disposition. Evidence keys above are
exact source/test/log mappings, not inferred closure from a keyword or summary.
PENDING_HUMAN means the technical control exists but future Plan18 acceptance
completion is unverified. It does not hide an absent implementation mitigation.

| Threat ID | STRIDE category | Disposition | Status | Concrete evidence |
| --- | --- | --- | --- | --- |
| T-10-01-01 | Tampering / Elevation | mitigate | CLOSED | C01 financial or privacy boundary; A: composite/FK/immutability/direct-denial tests. |
| T-10-01-02 | Repudiation / Information disclosure | mitigate | CLOSED | Retained event and owner proof; A: saved source/owner identity; K: old rows/identities preserved. |
| T-10-01-03 | Denial of service | mitigate | CLOSED | Queries, loops and tests; A: bounded fields and owner/work indexes; K: rollback-owned SQL. |
| T-10-01-SC | Tampering | mitigate | CLOSED | npm/uv packages and images; S: approved exact patch exception; locked manifests; strict five-image pass. |
| T-10-02-01 | Tampering / Elevation | mitigate | CLOSED | C02/C03 financial or privacy boundary; B+C+D: exact apply/hold signatures and forged/shadow denials. |
| T-10-02-02 | Repudiation / Information disclosure | mitigate | CLOSED | Retained event and owner proof; A+C+D: original replay, applied-only sum and NULL hold lineage. |
| T-10-02-03 | Denial of service | mitigate | CLOSED | Queries, loops and tests; E: one gate→Account; no provider I/O; F: finite runtime work. |
| T-10-02-SC | Tampering | mitigate | CLOSED | npm/uv packages and images; S: approved exact patch exception; locked manifests; strict five-image pass. |
| T-10-03-01 | Tampering / Elevation | mitigate | CLOSED | C02 financial or privacy boundary; C: bounded exact Decimal/HALF_EVEN vectors matched in SQL. |
| T-10-03-02 | Repudiation / Information disclosure | mitigate | CLOSED | Retained event and owner proof; C: desired/proposed/applied distinct; no invented unknown zero. |
| T-10-03-03 | Denial of service | mitigate | CLOSED | Queries, loops and tests; C: constant bounded arithmetic; no query/network loop. |
| T-10-03-SC | Tampering | mitigate | CLOSED | npm/uv packages and images; S: approved exact patch exception; locked manifests; strict five-image pass. |
| T-10-04-01 | Tampering / Elevation | mitigate | CLOSED | C01/C03/C04 financial or privacy boundary; K+B: exact function/schema/ACL metadata; no repair; SET ROLE negatives. |
| T-10-04-02 | Repudiation / Information disclosure | mitigate | CLOSED | Retained event and owner proof; K: complete saved rows,19 sequences and lineage corruption checks. |
| T-10-04-03 | Denial of service | mitigate | CLOSED | Queries, loops and tests; K: fixed26-table/four-function catalog; bounded owned test execution. |
| T-10-04-SC | Tampering | mitigate | CLOSED | npm/uv packages and images; S: approved exact patch exception; locked manifests; strict five-image pass. |
| T-10-05-01 | Tampering / Elevation | mitigate | CLOSED | C03/C04 financial or privacy boundary; B+E+K: genuine restricted SQL/TLS/role denials and quarantine. |
| T-10-05-02 | Repudiation / Information disclosure | mitigate | CLOSED | Retained event and owner proof; C+D+K: actual financial ledger/replay/held successor source=clone. |
| T-10-05-03 | Denial of service | mitigate | CLOSED | Queries, loops and tests; E+K: observed waits, fixed owned projects and finally cleanup. |
| T-10-05-SC | Tampering | mitigate | CLOSED | npm/uv packages and images; S: approved exact patch exception; locked manifests; strict five-image pass. |
| T-10-06-01 | Tampering / Elevation | mitigate | CLOSED | C04 financial or privacy boundary; K: genuine same-archive0007–0014 and both verify-fullTLS lanes. |
| T-10-06-02 | Repudiation / Information disclosure | mitigate | CLOSED | Retained event and owner proof; K: checksum/archive/identity/source equality; corruption refuses. |
| T-10-06-03 | Denial of service | mitigate | CLOSED | Queries, loops and tests; K: bounded serial tooling; cleanup_empty in actual gate report. |
| T-10-06-SC | Tampering | mitigate | CLOSED | npm/uv packages and images; S: approved exact patch exception; locked manifests; strict five-image pass. |
| T-10-07-01 | Tampering / Elevation | mitigate | CLOSED | C01/C02/C03 financial or privacy boundary; B+C+D: actual derived historical target, zero and current hold rights. |
| T-10-07-02 | Repudiation / Information disclosure | mitigate | CLOSED | Retained event and owner proof; A+C: saved immutable original/replay and linked applied successors. |
| T-10-07-03 | Denial of service | mitigate | CLOSED | Queries, loops and tests; E: one transaction; service validates BIGINT/fingerprint bounds. |
| T-10-07-SC | Tampering | mitigate | CLOSED | npm/uv packages and images; S: approved exact patch exception; locked manifests; strict five-image pass. |
| T-10-08-01 | Tampering / Elevation | mitigate | CLOSED | C02/C03 financial or privacy boundary; E: actual concurrent spends/duplicate work and advancing final guards. |
| T-10-08-02 | Repudiation / Information disclosure | mitigate | CLOSED | Retained event and owner proof; A+D+E: no partial rows/cash, unchanged original/held dedup. |
| T-10-08-03 | Denial of service | mitigate | CLOSED | Queries, loops and tests; E: observed blockers, cancellation and test-barrier cleanup. |
| T-10-08-SC | Tampering | mitigate | CLOSED | npm/uv packages and images; S: approved exact patch exception; locked manifests; strict five-image pass. |
| T-10-09-01 | Tampering / Elevation | mitigate | CLOSED | C04 financial or privacy boundary; B+D+F: two independent retained paths; no live escape. |
| T-10-09-02 | Repudiation / Information disclosure | mitigate | CLOSED | Retained event and owner proof; D+F+G: actual worker→SQL→owner History hold and reviewed successor. |
| T-10-09-03 | Denial of service | mitigate | CLOSED | Queries, loops and tests; F:100/40s budget,105-owner fairness/wrap and real-wait timeout. |
| T-10-09-SC | Tampering | mitigate | CLOSED | npm/uv packages and images; S: approved exact patch exception; locked manifests; strict five-image pass. |
| T-10-10-01 | Tampering / Elevation | mitigate | CLOSED | C05 financial or privacy boundary; G: owner per UNION and offpage original; forged cursor tests. |
| T-10-10-02 | Repudiation / Information disclosure | mitigate | CLOSED | Retained event and owner proof; A+G+H: saved values/IDs/lineage and actual wire→parser regression. |
| T-10-10-03 | Denial of service | mitigate | CLOSED | Queries, loops and tests; G+H:512-byte cursor,1..100 limit and bounded lookup. |
| T-10-10-SC | Tampering | mitigate | CLOSED | npm/uv packages and images; S: approved exact patch exception; locked manifests; strict five-image pass. |
| T-10-11-01 | Tampering / Elevation | mitigate | CLOSED | C05 financial or privacy boundary; G: CurrentUserDep/no owner input/forged-session refusal. |
| T-10-11-02 | Repudiation / Information disclosure | mitigate | CLOSED | Retained event and owner proof; G: no-store/fixed errors; private original; legacy untouched. |
| T-10-11-03 | Denial of service | mitigate | CLOSED | Queries, loops and tests; G: bounded request/service values; no external fetch. |
| T-10-11-SC | Tampering | mitigate | CLOSED | npm/uv packages and images; S: approved exact patch exception; locked manifests; strict five-image pass. |
| T-10-12-01 | Tampering / Elevation | mitigate | CLOSED | C05/C06 financial or privacy boundary; H: strict tags/BigInt money/identity/lineage; malformed-page refusal. |
| T-10-12-02 | Repudiation / Information disclosure | mitigate | CLOSED | Retained event and owner proof; H: null uncertainty differs from verified zero; no implied credit. |
| T-10-12-03 | Denial of service | mitigate | CLOSED | Queries, loops and tests; H: bounded decimal/ID/cursor/page validation and abort. |
| T-10-12-SC | Tampering | mitigate | CLOSED | npm/uv packages and images; S: approved exact patch exception; locked manifests; strict five-image pass. |
| T-10-13-01 | Tampering / Elevation | mitigate | CLOSED | C06 financial or privacy boundary; I: owner+epoch+query guards; late result/auth401 negatives. |
| T-10-13-02 | Repudiation / Information disclosure | mitigate | CLOSED | Retained event and owner proof; I+G: immediate old owner removal; no stored finance/optimistic balance. |
| T-10-13-03 | Denial of service | mitigate | CLOSED | Queries, loops and tests; I: retryfalse, one append, cancellation before authoritative reload. |
| T-10-13-SC | Tampering | mitigate | CLOSED | npm/uv packages and images; S: approved exact patch exception; locked manifests; strict five-image pass. |
| T-10-14-01 | Tampering / Elevation | mitigate | CLOSED | C05/C06 financial or privacy boundary; G+H+I+J: scoped validated financial rows and current-owner hiding. |
| T-10-14-02 | Repudiation / Information disclosure | mitigate | CLOSED | Retained event and owner proof; J: exact saved cash/proposal/hold/original text via React escaping. |
| T-10-14-03 | Denial of service | mitigate | CLOSED | Queries, loops and tests; J+I: bounded inline original; one active append; focus/error retention. |
| T-10-14-SC | Tampering | mitigate | CLOSED | npm/uv packages and images; S: approved exact patch exception; locked manifests; strict five-image pass. |
| T-10-15-01 | Tampering / Elevation | mitigate | CLOSED | C04/C06 financial or privacy boundary; J+B+D+G: real auth/SQL/worker financial browser journeys. |
| T-10-15-02 | Repudiation / Information disclosure | mitigate | CLOSED | Retained event and owner proof; J+K: labeled synthetic inputs and retained capture/source evidence. |
| T-10-15-03 | Denial of service | mitigate | CLOSED | Queries, loops and tests; J+F: owned bounded runner, timeouts and cleanup. |
| T-10-15-SC | Tampering | mitigate | CLOSED | npm/uv packages and images; S: approved exact patch exception; locked manifests; strict five-image pass. |
| T-10-16-01 | Tampering / Elevation | mitigate | CLOSED | C04/C06 financial or privacy boundary; K+L+B: exact recovery/role matrix, guarded dev rights and CI gate. |
| T-10-16-02 | Repudiation / Information disclosure | mitigate | CLOSED | Retained event and owner proof; K+J: sealed original ledger/capture/source hashes remain exact. |
| T-10-16-03 | Denial of service | mitigate | CLOSED | Queries, loops and tests; F+K+L: timeout/cleanup and bounded serial CI; observed dev refusals. |
| T-10-16-SC | Tampering | mitigate | CLOSED | npm/uv packages and images; S: approved exact patch exception; locked manifests; strict five-image pass. |
| T-10-17-01 | Tampering / Elevation | mitigate | CLOSED | C01/C02/C03/C04/C05/C06 financial or privacy boundary; A+B+C+D+E+F+G+H+I+K+L: independent owning-code audit. |
| T-10-17-02 | Repudiation / Information disclosure | mitigate | CLOSED | Retained event and owner proof; A+K+P: retained12 artifacts/384 current hashes rechecked; pending honest. |
| T-10-17-03 | Denial of service | mitigate | CLOSED | Queries, loops and tests; F+G+K+L: bounded work/read/dev/tooling; no new runtime query. |
| T-10-17-SC | Tampering | mitigate | CLOSED | npm/uv packages and images; S: approved exact patch exception; locked manifests; strict five-image pass. |
| T-10-18-01 | Tampering / Elevation | mitigate | PENDING_HUMAN | C06 financial or privacy boundary; G+H+I+J technical controls verified; P: actual new-UI/native200% completion pending. |
| T-10-18-02 | Repudiation / Information disclosure | mitigate | PENDING_HUMAN | Retained event and owner proof; A+K+P: immutable/source evidence verified; owner answers expressly absent. |
| T-10-18-03 | Denial of service | mitigate | CLOSED | Queries, loops and tests; F+G+J+L: bounded work/read/inline originals and script-free review packet. |
| T-10-18-SC | Tampering | mitigate | CLOSED | npm/uv packages and images; S: approved exact patch exception; locked manifests; strict five-image pass. |

## Targeted ASVS L1 control mapping

These are control areas used by the plan, not a full ASVS checklist or versioned
requirement-number certification. STRIDE Tampering/Elevation maps to B/C/E/G/H/L;
Repudiation/Information disclosure maps to A/D/G/I/J/K/P; Denial of service maps
to E/F/G/H/L; supply-chain Tampering maps to S.

| Control area | Concrete verification | Limit |
| --- | --- | --- |
| Input validation and output handling | Bound fingerprints/BIGINT/cursors; strict Pydantic/TS tags/strings/lineage; bound SQL parameters; React escaping (B/G/H/J) | Does not certify all existing product inputs or dependencies |
| Authentication/session lifecycle | Existing verified access/session dependency; owner+epoch/query replacement; late old-session/401 refusal (G/I) | Existing v1 accepted cross-tab follow-up stays separate |
| Access control/least privilege | All entry/detail owner scopes; runtime real42501 negatives; scheduler only fixed SQL EXECUTE; private helpers; dev fixed owner-only rights (B/G/K/L) | Ordinary dev admin is intentionally privileged locally; production bootstrap is separately restricted |
| Financial/business integrity | Exact HALF_EVEN target minus actual applied; immutable owner-bound originals/decisions; gate/account/constraint/final-clock order; atomic rollback and replay (A/C/D/E) | Synthetic admissions do not establish live provider authorization |
| Sensitive data and error/cache handling | no-store, fixed errors/log codes, no browser persisted finance, no raw provider HTML/PII in new output (G/H/I/J) | Existing publication/CSP follow-up is not newly claimed resolved |
| Resource limits |100 candidates/40s,50 per path, bounded cursor/page/detail, timeouts/cancellation/isolated cleanup (E/F/G/L) | No load-capacity or large-scale benchmark claim |
| Recovery authority/configuration | Independent exact prosrc/full declarations/owner/path/ACL/role membership/schema/sequence checks before reconstruction; clone financial quarantine (K) |0014 current-service restore and0008 selected cutover/old-app rollback are distinct |
| Dependencies/build integrity | Locked manifests, explicit approved exact Node repair, no trust waiver, actual-recipe inventories/nonroot native proof and five strict fresh scans (S) | Clean HIGH/CRITICAL threshold does not mean no lower-severity findings |

## Function identity and final authority checks

The auditor independently extracted all four prosrc bodies from migration SQL
and recomputed SHA256; each equals `backup-snapshot.py`'s independent constants.

| Function | Prosrc SHA256 | Privilege boundary |
| --- | --- | --- |
| `apply_stock_dividend(bigint,bigint,text,text)` | `4fa0589f573067ee7a870addce0e303a79152ee47cb7c857632104c9d5bd0507` | SECURITY DEFINER; migrator owner; scheduler EXECUTE only |
| `record_stock_dividend_hold(bigint,text)` | `68b31d48ee5036cd962770b6a0be7d29a50a3d9e8a7f709faf728344d6c6072b` | SECURITY DEFINER; migrator owner; scheduler EXECUTE only; no account UPDATE |
| `stock_dividend_authority(bigint,bigint,text,text,boolean,jsonb)` | `7861fec1e2552603ad9d5b8c9d314572dee859fa0f6d2e2247812e793e121d23` | Private invoker; not granted to scheduler/app/PUBLIC |
| `reject_stock_dividend_mutation()` | `1ed29a1005ee6925f954852f4aec69abf2f4865a3a6a0b7cab53391c4cc5c2fa` | Private invoker immutable trigger; migrator owner |

The apply TABLE output is exactly payment_id BIGINT, decision_id BIGINT,
outcome TEXT, with four input and three TABLE argument modes. Hold has two
inputs and the same three outputs. Recovery checks full argument names/modes/
types, not just input regprocedure or body. The expected search_path is exactly
`pg_catalog, public, pg_temp`; language plpgsql, volatile, no defaults/support/
leakproof/strict changes. Full body/identity checks are shared with bootstrap
preflight; source/clone catalog tampering tests fail before reconstruction.

The final helper compares the entire loaded event/revision/entitlement/action/
instrument/coin/session/admission/historical-quantity/sequence/uncertainty
snapshot and evaluates advancing DB clock. This covers same-generation row
changes and rights/calendar expiry after real waits. Apply and hold both flush
constraints before this final check. Service result construction makes no
subsequent business query; transaction commit follows. Immutable successful
replay intentionally precedes renewed authority, performs no payment, and
returns the saved result when current rights have expired.

Hold revalidates current action/calendar/reference durable accounting/storage/
display admissions and expected revision even with no current eligible target.
It needs an actual paid anchor and uncertainty, cannot introduce arbitrary owner
or target, and writes applied0 with unknown amount. No-target work is discoverable
without the eligible-entitlement helper; pre-anchor uncertainty publishes no
Dividend. Test assertions exercise those distinctions and later reviewed
reconciliation rather than interpreting cancellation as a zero reversal.

## Additional implementation surface and flags

All 01–16 SUMMARY threat-related sections were checked; only16 declares a
literal `threat_flag`. Its heading is `Threat flags and limits`, so an exact
case-sensitive `## Threat Flags` search alone would have missed it.

| Flag/surface | Register mapping | Result |
| --- | --- | --- |
| `privileged-dev-database-access` (`10-16-SUMMARY.md:177`) | T-10-16-01/03/SC and T-10-17-01/03/SC; concrete L/S above | Mapped informational surface, independently verified after CR-01 repair. It is not ignored because disabled stock flags can make startup health pass. |
| New private SQL helper/hold entry | T-10-02-01/02 and T-10-04-01/02 | Both exact retained authorities verified; no app/PUBLIC helper execution |
| Current-source review export | T-10-15-02/03, T-10-17-02 and pending T-10-18-01/02 | Presentation evidence and current/capture identities stay distinct; no inferred acceptance |
| Approved Node image repair | All SC IDs, principally T-10-16-SC | Approved exception, preserved failed diagnostic/builds and strict fresh scans; no lock drift |

**Unregistered flags: none after the explicit mappings above.** No warning is
being used to waive a missing control. This is a targeted audit of declared
mitigations and identified implementation surfaces, not a blind vulnerability
scan. No additional implementation blocker was proved.

## CR-01 and actual affected evidence

Independent code review originally found ordinary dev `birja` owned the tables
while the new definer ran as an empty `birja_migrator`. Source inspection agrees:
without object rights its reads fail even if the caller is a superuser.
`/tmp/birja-phase10-17-dev-repro.log:39`, `:43`, `:123`, `:127` records both fresh
and0013-upgrade actual42501 at `stock_action_events`, with unchanged cash/rows.
The persistent RED at `dd2ba3a` fails in the actual service's first original
payment (`dev-financial-red.log:65`); it predates the new CLI option and is not
a manufactured missing-flag test.

Fix `f47af65` grants only the needed fixed underlying object rights to the safe
definer owner after migration and provenance checks (L). It adds no scheduler
cash/table writes, role memberships, superuser flag or authority migration/body
change. Both advertised Compose startup paths and persistent CI regression are
wired. GREEN log `dev-financial-green.log:44`, `:153`, `:237`, `:346`, `:371`
records actual fresh19.287s/upgrade21.117s, original/correction/uncertain hold/
dedup/reconciled worker/History/replay, exact cash10004 and starting10000,
one unchanged original/three decisions. Unsafe CREATEROLE, incoming membership
and foreign object owner are refused without repair. Expected refusal
tracebacks in that GREEN log are asserted outcomes, not unresolved failures.
The independent affected code re-review closes CR-01 with zero active findings.

| Gate read by this auditor | Actual result and scope |
| --- | --- |
| New dev financial regression | Fresh19.287s + upgrade21.117s; owned resources clean; source/test assertions read (L) |
| Final affected backend | `/tmp/birja-phase10-17-backend-full.log`:2557passed/324.80s,99.87% overall; `/tmp/birja-phase10-17-critical.log`:47 critical modules,4565 statements/1462 branches,100%,0missing/partial |
| Backend static checks | Coordinator records full Ruff,190format and Mypy88 pass; no new code was changed by this audit |
| Actual current-recipe builder/runtime | `image-proof-final.log` and `image-native-inventory.json`: complete APK/Python inventories unchanged; UID1001/native XNYS/dividend/worker/History/helper SHA passes; network-none and bounded tmpfs harness inspected |
| Five new strict scans | `/tmp/birja-phase10-17-image-reports/status.json`:oktrue; runtime21.923s,builder8.233s,PostgreSQL6.342s,Redis1.829s,Node3.886s; all0qualifying HIGH/CRITICAL including unfixed |
| Current image identities | Runtime`06de74e4dea8b56c8b24ee8f164f69adf18e09547af9ffc3fcddd96dd3dcf657`; builder`b4a366829d51ce1c206f2b8aa077e42e30f6c886808a432624ded26409d268d3`; unchanged approved Node`7344f1b05de0e77f4156a04b73098bfbad78c81a2480efdc6645070b14e2a4db` |
| Preserved initial image diagnostics | Initial network-none build cache miss/APK failure and first native harness missing tmp are superseded by actual-recipe/safe-harness passes; no package/version/lock change is inferred from those failures |
| Reused browser/frontend | Final16 actual49pass/1expected deployed-CSPskip305.7s;697frontend tests plus static/build. UI/API/browser CLI bytes unchanged; no new browser run claimed at f47af65 |
| Reused final same-archive proof | All six stages passed1391.017s; archive SHA256`1faa8277951d0c2a66ac10ffb8b39b5f85372acdacd10b3b3348126c90052cc1`; exact current0014 restore/service replay/History/Portfolio/quarantine; actual selected cutover/old-app rollback at0008 |
| Independent integrity recheck | All12old sealed artifacts and384current source hashes in `/tmp/birja-phase10-17-retained-source-integrity.json` recomputed equal. Receipt confirms11retained CORE/unit bytes equal current/archive;378/384 final16 sources unchanged, six dev/CI/Compose sources changed plus new dev regression. Financial SQL, production bootstrap, services/worker/History and retained producer/consumer bytes unchanged |

The parent approved affected gates after the dev-only repair; the unchanged
23-minute same-archive proof was not repeated. New image IDs and helper bytes
must not be presented as if all six stages ran again against them. The receipt
preserves both accepted old stage identities and the actual new affected
validation. This reuse is adequate for Phase10's schema/current-service recovery
obligations because none of those authorities or retained bytes changed.
It does not establish selected0014 cutover or public rollout; Phase11's separate
rollout/acceptance remains outstanding. No installed production tool, timer,
B2/provider access, secret/.env, deployment, push, PR or merge is authorized.

## Accepted risks and pending human completion

No Phase10 threat was accepted or transferred. Existing explicitly accepted
v1 W01–W08 and Phase7/8 live/provider/publication deferrals remain in their
original logs; they are not new acceptance of missing Phase10 implementation.
The Node HIGH was repaired and rescanned, not accepted or waived.

| Threat | Verified technical mitigation | Completion evidence still required |
| --- | --- | --- |
| T-10-18-01 | Owner-only validated/escaped cash and correction UI; bounded original; actual privacy/financial/browser assertions | Explicit owner acceptance of the current hash-bound new mixed History/held/correction interface and native zoom task outcome |
| T-10-18-02 | Immutable original/source identity; exact artifact hashes; current HUMAN-UAT truthfully pending with no fabricated answer | Real Plan18 owner answers bound to reviewed source, including genuine desktop native200% readability/reachability/no overlap/no horizontal page overflow |

These two remain **PENDING_HUMAN**, not fully CLOSED and not accepted risk.
The remaining Plan18 resource and supply-chain mitigations are already present
and explicitly mapped. No current technical gap is disguised as a future human
choice. Silence, old Phase9 approval, CSS zoom/device scale and viewport-width
tests cannot satisfy either future checkpoint.

## Audit trail and sign-off

| Date | Registered | Fully verified | Absent implementation mitigation | Human completion pending | Auditor |
| --- | ---: | ---: | ---: | ---: | --- |
|2026-11-13|72|70|0|2|Independent gsd-security-auditor agent, current source f47af65 |

Technical mitigation status: **SECURED**. Overall phase status:
**HUMAN_NEEDED**; complete Plan18 only from actual answers. This report does not
mark any phase/requirement complete or advance shared project state.


## Affected security recheck — UI focus repair at 48d970c

This independent affected pass inspected the complete three-file diff
`f47af65..48d970c` and the owning focus callback. It changes end-of-list focus
from `node.focus({ preventScroll: true })` to normal `node.focus()`, corrects
four gap classes and makes displayed cash medium weight. The exact existing
owner/session-epoch/intent and active-element checks still precede focus;
no query/auth/cash parsing or mutation behavior changes. The browser test adds
actual focused bounding-box checks against the viewport and mobile navigation
at320/375/768/1024/1440. No new network, auth, monetary authority or unregistered
trust boundary appears. Evidence J is extended; I/G/H/B/K remain unchanged.
No additional implementation mitigation gap is found.

UX-01 was a real required accessibility finding: the end message received
focus while its bottom was at3616px in a900px viewport. The actual RED
`db19cf5` is retained in
`/tmp/birja-phase09-browser-nnh4g3e4/browser-dividends.log`; normal focus scrolling
in `48d970c` resolves that targeted behavior. The coordinator's GREEN
`/tmp/birja-phase10-17-ui-focus-green.log` records one actual browser test passing
in40.2s, all five viewport/navigation bounds plus retry focus, and owned cleanup.
Reported affected component/page29tests4.15s, fullfrontend697tests16.42s and
static/build checks pass. The separate independent code re-review is clean.
This auditor did not rerun those tests or start a browser/stack.

At this recheck boundary the one full current-source browser run is **running**,
with385sources frozen in
`/tmp/birja-phase10-17-final-browser-frozen-sources.json`; no completed receipt
or final full-browser outcome is claimed here. The earlier packet with SHA
`482f3ec3f763d273416cfe8ec80a8dd6f94c0e6624a3c5d7812a46a4eb409862`
is now historical pre-focus evidence, safely preserved as
`/tmp/birja-phase10-ui-review-before-focus17*`. A refreshed packet must be
attributed to the actual new passing captures after that run. This report does
not call the earlier packet final/current or infer native200% acceptance.

No backend/SQL authority, production bootstrap, retained CORE byte, package,
lockfile or image-version change occurred in this three-file diff. Prior
backend2557/47critical100%, native/inventory and five strict scans remain
applicable; retained same-archive reuse retains its original source/image scope.
The original four-body/384-source/12-artifact integrity verification above
remains attributed to f47af65, not retroactively relabeled48d970c.

Counts remain72registered,70fully verified,0absent implementation mitigations
and2PENDING_HUMAN (T-10-18-01/02). Technical status remains SECURED; overall
phase and owner UI/native200% acceptance remain HUMAN_NEEDED.
