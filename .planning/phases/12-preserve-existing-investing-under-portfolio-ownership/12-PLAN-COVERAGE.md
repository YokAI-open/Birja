# Phase12 Multi-Source Coverage and Reachability Audit

Planning only:28 plans,56 tasks,18 waves. Revision1 completed; independent recheck pending. Seven primary requirements retain their approved mappings and all occur in nonempty plan frontmatter.

## Goal and Requirements

| Source | Required outcome | Plans/tasks | Status |
|---|---|---|---|
| GOAL | Preserve existing investing under explicit named ownership |01–28 coordinated delivery | COVERED |
| PFUND-03 | Actual legacy cash/baseline/quantities/basis/immutable ids,payloads,digests; no grant |01–07;08-02;12–14;17–18;27 | COVERED |
| PFIN-02 | Owned active target and unchanged crypto/stock execution |08;10–13;15;20–21;23–24 | COVERED |
| PFIN-03 | Global retry compares original root+payload; active original replay |10–11;21;24;26–27 | COVERED |
| PCTX-01 | Visible name on ticket,confirmation,receipt,holdings,History |19;23–25;26/28 | COVERED |
| PVIEW-03 | Scoped private mixed History/cursor/original arms |14-02;15;20-02;22-02;25-02 | COVERED |
| PSAFE-02 | Zero/one/many identity; no read grant; old requests refuse |08–09;15;19/23;26 | COVERED |
| PSAFE-03 | Restricted roles/TLS/compound causes/exact recovery |03–07;16–18;26–27 | COVERED |

The five roadmap success outcomes map respectively to preservation/no grant; explicit trading/retries; named private financial surfaces; identity/legacy refusal; restricted fresh/upgraded SQL/TLS/recovery.

## Context Decisions

CONTEXT uses named bullets, not numbered D-IDs. Preserve the actual decisions without inventing historical identifiers.

| Locked item | Coverage |
|---|---|
| Research/UI first and existing design system | Approved research/UI consumed23–28 |
| Actual finances retained in My portfolio; no regrant |01–08 |
| Explicit active target; no alternate selection |08/10–15/19–25 |
| Unchanged fees,freshness,eligibility,incomplete value,History |10–14/20–25/27 full regression |
| Identity zero/one/many; reads/sign-in cannot recreate |08–09/19/23/26 |
| Restricted SQL,TLS,exact money,immutability |02–07/16–18/27 |
| Per-runnable-revision recovery and explicit refusal |04/07/16–18/27 |
| Terminal freeze including earned unpaid dividends and later corrections |03 closure metadata,06/12–13 frozen fixture proof |
| Ten active independent grants later; names/optional empty description/overview Phase13; deletion Phase14 | No public management route or control; prerequisite root shape/freeze included |
| Keep local; no provider,production,install,publish,branch switch | All plan boundaries/SC threats |

## Research Mechanisms

| Mechanism or constraint | Concrete owner | Status |
|---|---|---|
| Responsibility map:SQL relational authority; services explicit owned transaction; browser untrusted |03–08/10–15/19–25 | COVERED |
| accounts.id root; compound owner/cause tuples; global instrument evidence |02–03/05–07/12–14 | COVERED |
| Actual-migrator-only finite NULL association; every other column unchanged |04-01/02;01 authored cases;07 actual final SQL | COVERED |
| Final0017 closes bypass, required tuples, no broad ordinary grants |07/16 | COVERED |
| Intermediate0015/16 explicitly migration-only runtime/bootstrap/backup/restore |07/16/17/27 | COVERED |
| Resumable migrator-to-final path avoids intermediate bootstrap deadlock |16-02/27 | COVERED |
| Immutable static versioned SQL companions, old migrations unchanged |05/06 loaded07;17 exact inventories | COVERED |
| Old binary/unsafe downgrade refuses before writes |04/07/16/18/27 | COVERED |
| Every writer including raw VERIFIED/ANCHORS,entitlement supersession,correction/payment |10–13 plus05/06 SQL | COVERED |
| Global journal ordering; versioned old split digest interpretation; closed terminal unit epochs |03/12 | COVERED |
| Identity-only real v2 API; legacy verify before OTP consumption |08–09/15/19 | COVERED |
| Global retry-key uniqueness plus root/payload; active original replay before market gate |10–11/21/24 | COVERED |
| Root/version cursor and all union/hydration/original references |14/20/22/25 | COVERED |
| Query keys and hidden cache WeakMaps/epochs/seen/pending ownership |19/21–22 | COVERED |
| Existing packages only; strict audits/five actual image scans | SC threats;26–27 | COVERED |
| Exact current/retained schema/function/role inventories; one source/archive serial proof |16–18/26–27 | COVERED |
| Independent fixture oracles and all existing regressions |01/05/06/domain tests and27 | COVERED |

Engineering refinement:portfolio_stock_closures records owned root+coin closed_at,closing_sequence,unit_epoch. Migration-authority synthetic fixtures seed it; generic runtime roles cannot mutate lifecycle. Closed-root reconstruction uses its own cutoff while active siblings advance global epochs. Public closure transaction belongs Phase14. New split digest interpretation is versioned; old saved bytes unchanged.

## UI Contract

| UI-SPEC item | Owner | Status |
|---|---|---|
| Existing spacing/type/color/tokens/components; neutral Portfolio and wrapping plain-text name |23 context/boundary;24–25;26 | COVERED |
| Scoped URLs/nav; sole-root discovery only before existing intent |19/23/26 | COVERED |
| Context ticket/confirmation/reprice/original receipt/holdings/History/detail |24–25 | COVERED |
| No selector/management controls; Account identity no cash |23; all exclusions | COVERED |
| Exact approved loading/unavailable/ambiguous copy and financial suppression |19/23/24–25 | COVERED |
| Original attempt scope; no fallback; market-close original active replay |21/24 | COVERED |
|320/768/1280,long escaped names,focus/aria-live,responsive reflow |23–26 | COVERED |
| Source-bound read-only synthetic packet plus blocking UI/native200% owner check |26–28 | COVERED |
| Registry safety; no new UI/package dependency | Existing components;SC threats | COVERED |

## Reachability and Dependency Audit

Legacy root reaches named ownership by0015→0016→0017. New User creates sole My portfolio through existing atomic onboarding; reads never create roots. Zero/many/terminal roots are reachable only in isolated migrator fixtures01/18 until later management phases. Versioned routes mount15; request-code/refresh/logout retain existing paths. Browser routes/nav23 and pages24–25 require target boundary. Original receipt recovery and original event details remain same-root. Intermediate schema reaches final by16 migrator lane even while ordinary bootstrap/recovery refuses.27 source-bound proof consumes final and retained lanes. No same-wave file overlap:shared modifications have explicit dependencies.12 stock journal interfaces precede11 stock service despite numeric naming.28 owner checkpoints follow27 proof.

## Exclusions and Unperformed Proofs

Phase7 STOCK-01/02/03,DATA-01,MKT-01,SAFE-01 remain separately deferred/unverified and original manual campaign untouched; stock gates stay off. Phase13 create/name/rename/optional empty description/overview and ten-root funded controls,Phase14 delete/empty-management remain future features. No provider agreement/payment,production access/deployment,package change,push/merge or branch change.

Revision1 resolution is recorded in12-PLAN-REVISION-01.md; added source/schema/image/proof matrix is owned18, real fixture mode/oracle negatives18-01 and actual isolated smoke18-02.02/03 metadata and05/06 static precursor checks defer real SQL negatives to07-01 after Alembic0017. Pre15 API checks compose the actual declared routers in isolated test apps;15-02 verifies production mounting. All new mechanisms remain required; no source item was removed.

Static SDK/schema/task/DAG/reference checks establish plan shape only. Real Wave0,SQL/TLS/cold recovery,strict audits/five image scans and owner changed-UI/native zoom remain unperformed. Independent checker follows. Nothing marks Phase12 executed or runtime verified.

