# Phase15 — Full Strategy Lifecycle Acceptance

Local evidence is complete for final independent goal verification. This record
does not mark global requirements complete, publish software or authorize a
production operation. Fresh Phase15 evidence is distinguished from inherited
results below; failed whole commands remain failed.

## Evidence keys and hash bindings

| Key | Actual evidence / source / scope |
|---|---|
| R | Fresh supported current-only R5 at `6d7ee7f`, `/tmp/birja-phase15-campaign-recovery-current-r5/command.log`, SHA256 `b3bd7b162293a4316d566d8178beb4c544c2ceb9325de861279e793ecdd05502`. Actual encrypted source-destroyed cold restore,31/24before-oracle, active original creation/fill/payment, three closed refusals, frozen/sibling/zero state and no sequence change; exit0/135.998s. |
| B | Inherited Phase14 R2 backend/frontend raw `/tmp/birja-phase14-campaign-security-plan18-r2/command.log`, SHA256 `76673da8728efd87b4f6977a24e55c62e57d4b4fd473b1e9174672da0e8bdff5`;3691backend/1330frontend pass, overall99.87%/96.43%,64critical modules100%. Whole R2 remains failed. Relevant277backend/155frontend inputs match. |
| C | Inherited actual lifecycle browser assertions;314relevant inputs match. Composite92prior passes plus corrected History and one retained CSPskip, not a successful whole-browser command. Failed full-R2 receipt SHA256 `28b1a59ce8d39b08c07678ac6c863ab2d3e56aadef7b44c97f22f1a03caca903`; passing `browser-repair-history-final.json` SHA256 `65002310c6c071713d2ecf39d5040f74158721def8548734c7548fed9e7beb96`, both in `/tmp/birja-phase14-campaign-plan18-repair/`. Passing eight real deletion behaviors `/tmp/birja-phase14-plan17/behavior-r2.json` SHA256 `627b406312196963226e7283e1d346d0dea9bb7e0166a2d5c1ca12dba67972c1`. No forced optional replay-branch coverage claimed. |
| D | Inherited source-bound migration/roles/TLS/rollback results at `628f0af`;139authority inputs match. `/tmp/birja-phase14-campaign-recovery-components-plan18-r1/03.log` SHA256 `65b6e4a33f7e6fd2aa4824a3e74be062ce8d98b606ffb27f1c3a0b663edc887c` proves both0014/0020→0023 upgrades and original cash123.45/baseline8765. `05.log` SHA256 `a4c07f175c55ee7433e5321a1f7144ac6f3c46f3e9fee67b8221783ff836f6bf` proves selected rollback/refusal. Other exact cold/roles/fresh hashes are in the reuse manifest. New cold helper execution is R, not re-labelled old direct-login TLS. |
| H | Actual12/13/14owner UI/native200 records and unchanged365R7render inputs. Phase14 owner: “i approve ui and 200 zoom” on2026-11-22. R7ZIP SHA256 `886805a094fad7495ae53539da7ea80d0ddff6c67b1ce0aa0465899a493d32e0`; browser metadata unknown. See15-UI-REVIEW. |
| Q | Fresh five exact image scans HIGH0/CRITICAL0,41.220s; source/image/CORE/archive guards, owned cleanup,9prior artifacts and3failed archives. `/tmp/birja-phase15-plan03/final-integrity.json` SHA256 `5837ba0e774807fbbdea98d36a198a103f25e7d54f96e7749602c00a953aef2f`. Exact current image and authority are in15-RECOVERY-PROOF. |

The explicit input/log/image inventory is
`/tmp/birja-phase15-plan03/reuse.json`, SHA256
`4d9f957d9ec951a7635aa7c436eb68fe83489f486cec57358808aafa923c7210`.
It rechecks28successful security-command logs and six recovery logs, their
actual exit0receipts and relevant source families. See15-EVIDENCE-REUSE for
the scope, repaired-input associations and immutable failed-run history.

## All28 approved requirements

Backend anchors below are under `backend/tests/`; browser anchors are under
`frontend/e2e/`. B/C/D/H are inherited only at the compared input scope; R/Q are
fresh. Paths name substantive assertions, not mere file-existence evidence.

| Requirement | Behavioral assertion / implementation test anchor | Evidence |
|---|---|---|
| PMGT-01 | Creation cap, independent identity and freed slot: `test_portfolio_creation.py`; `portfolio-strategies.spec.ts` concurrent tenth-slot/zero replacement | B,C; R preserves identities |
| PMGT-02 | Canonical name, owner uniqueness and rename without finances: `test_portfolio_metadata.py`; strategies metadata/race cases | B,C,H |
| PMGT-03 | Named Cancel sends no DELETE; confirmed closure with holdings stays original: `test_portfolio_closure_api.py`; `portfolio-deletion.spec.ts:177` | B,C,H |
| PMGT-04 | Financial freeze, unpaid/corrected-event dispositions and no liquidation: `test_portfolio_closure_events.py:81,102,298`; closure authority | B,R |
| PMGT-05 | Last deletion preserves signed-in zero identity; no implicit grant: `test_portfolio_closure_identity.py`; ownership/deletion zero cases | B,C,R,H |
| PMGT-06 | Optional description edits/clears preserve immutable finances: `test_portfolio_metadata.py`; strategies create/view/edit/clear case | B,C,H |
| PFUND-01 | Exactly one10000grant/baseline per new root: `test_portfolio_funding.py`; generated current oracle | B,R |
| PFUND-02 | Permanent original creation retry, including deleted original, grants nothing new: `test_portfolio_creation.py`; restored fixture `replay-restored` | B,C,R |
| PFUND-03 | Original migration cash/baseline/holdings/history unchanged, no regrant: `test_portfolio_migrations.py`; `fresh_authority_program` | B,D; distinct8765baseline |
| PFIN-01 | Same-asset siblings keep own cash/quantity/basis: `test_portfolio_strategy_lifecycle.py:172`; complete restored table oracle | B,R |
| PFIN-02 | Explicit active target, unchanged crypto/stock execution rules and stock gates: lifecycle `:172,277`; ownership trade journeys | B,C,R; live stocks remain gated |
| PFIN-03 | Unknown fill retains original target/key/body; original fill replay equals allfields: lifecycle tests and restored active fill103 | B,C,R |
| PFIN-04 | Historical eligibility, once-only per-book dividends/corrections: `test_portfolio_strategy_events.py`; original paid entitlement replay | B,R |
| PFIN-05 | Active same-stock siblings split once with conserved basis while closed book stays frozen: `test_portfolio_closure_stocks.py:31` | B,R preserves frozen ledger |
| PFIN-06 | Real create/delete/trade/job overlap never overspends, duplicates or mutates closed book: `test_portfolio_closure_races.py:105,186,355,415,450,496` | B,C,R |
| PCTX-01 | Correct portfolio name/ID on ticket/receipt/History: frontend route/unit assertions and `portfolio-ownership.spec.ts` | B,C,H |
| PCTX-02 | Switching/late callbacks isolate cache, previews, cursors and original requests: strategies late creation and ownership/deletion stale-order cases | B,C,H |
| PCTX-03 | Stable target links, private unavailable state and explicit overview escape: `test_portfolio_closure_privacy.py`; deletion stale routes | B,C,H,Rclosed refusals |
| PVIEW-01 | Stable own cash/value/return, original baseline, no pooled total: `test_portfolio_overview.py`; strategies overview | B,C,H |
| PVIEW-02 | Shared exact valuation, independent incomplete semantics: overview tests; strategies incomplete/refresh cases | B,C,H |
| PVIEW-03 | Private deterministic portfolio History, original references and scoped cursors: `test_portfolio_scoped_history.py`; ownership/History cases | B,C,H |
| PSAFE-01 | Owner/active final read/write/retry fences: `test_portfolio_closure_privacy.py`; API and stale-route cases | B,C,Rclosed refusals |
| PSAFE-02 | Identity/OTP/refresh/logout independent of zero/one/many roots; legacy target refuses ambiguity: `test_portfolio_identity_api.py`, closure identity tests | B,C,H |
| PSAFE-03 | Exact fresh/upgraded/cold SQL/ACL authority and original-data preservation: `test_portfolio_closure_admission.py`; real TLS parity | B,D,Rauthority equals inherited |
| PSAFE-04 | Exact active/frozen31table24tail restore; real original creation/fill/payment and closed/sibling/zero invariants | R,Q; `portfolio-closure-recovery-fixture.py:replay-restored` |
| PSAFE-05 | Authenticated installed-source consumer, finite preserved outputs, tested version/refusal matrix | D,R,Q;15-01contracts and RUNBOOK support matrix |
| PSAFE-06 | Complete create/edit/clear/compare/switch/trade/History/delete/zero loop, real races, coverage/images/reviews and actual UI | B,C,D,H,R,Q; no new UI |
| PSAFE-07 | Bounded creation cap/requests, isolated financial jobs and shared polling; no expanded backup/activation policy | B,C; existing scheduler/management/resource assertions, unchanged policy inputs |

## Four Phase15 outcomes

| Outcome | Actual evidence |
|---|---|
|1 Exact active/frozen identity/financial/lineage/tails, original migrated data, same-symbol/zero state|R31/24oracle plus Doriginal8765baseline, inherited migration and same-stock assertions; deleted data remains private|
|2 No repeated grant/fill/payment or resumed frozen effects after restore|Rreal original portfolio3/fill4/payment2,3closed refusals, all financial tables/lists equal, sequence_changes empty|
|3 Tested supported migration/recovery/rollback/refusal contract|Dgenuine source families plus Rinstalled consumer/current-only tooling; exact RUNBOOK matrix and guarded output/receipt contracts|
|4 Full protected lifecycle and required local gates|B/Cactual real DB/browser assertions, Hactual accepted unchanged screens, Qfresh exact-image scans, bounded code reviews and all nine validation outcomes|

## Completion boundary

Plan04's documented interfaces match the actual dry-run; diff/reference checks
pass. Independent final phase-goal verification is next and owns the decision
to advance PSAFE-04/05/06 globally. Full required PR CI must pass before merge.
No new complete all-security/browser/seven-stage or hostedCI pass is claimed.
R1–R4and earlier whole failures stay failed; current-only whole7/finalCI flags
remain false. Issue35's original scope/2026-12-17UTC expiry is unchanged; zero
image findings do not mean the accepted dependency advisory was remediated.
Phase7 live requirements, stock activation, publishing, milestone archival and
production changes remain separate. No real account/secret/financial data is used.
