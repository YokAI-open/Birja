---
phase: 14
slug: end-strategies-safely
status: blocked
source_commit: d2e8885b798e00a2932a18524a80d6268f28533c
diff_base: 9527e358bc6953cec7580043703324db194ba396
register_authored_at_plan_time: true
threats_total: 38
threats_closed: 36
threats_open: 2
implementation_defects: 0
qualification_gates_pending: 1
human_gates_pending: 1
unregistered_flags: 0
asvs_level: 1
created: 2026-11-20
---

# Phase 14 — Independent Security Review

The declared threat register remains **OPEN** at reviewed source `d2e8885`.
The original source-inventory defect at `4264357` is resolved by the independent
targeted re-review appended below. Whole-source Plan18 qualification and actual
Plan19 human responses remain pending. This distinct security-agent pass verifies
controls by defensive source tracing; it is separate from the integrated code
and UI reviews and does not claim a test, browser or full campaign execution.

The register contains exactly38 plan-time threats:18 primary rows,18 supply-chain
rows, and the two Plan19 rows. All dispositions are `mitigate`; no new high risk
is accepted or transferred. CLOSED below means the declared implementation
control is present, with the cited behavioral assertions and historical proof
reviewed. It does not turn old bounded runs into final whole-source evidence.

## Scope and trust boundaries

Reviewed project instructions, security skill/workflow/role, current project and
phase context, all19 plan threat models, execution summaries and per-plan repair
history, integrated code finding CR-01, legacy14 transition provenance, and the
final Plan17 packet/evidence disposition. Direct source tracing covered the
new migration/SQL closure authority, service proof, management transport, normal
read fences, lifecycle event handling, migration admission, browser original
transport/storage/generation, source-bound packet verifier, source dispatcher,
restore-before-grant path, selected rollback, campaign runner/supervisor and
unchanged dependency-audit policy. Prior per-plan reports provide complementary
historical evidence; their original findings and failed attempts are preserved.

| Boundary | Data and enforced control |
|---|---|
| Authenticated browser→private API | CurrentUser and CSRF before streamed DELETE parsing; exact original ID/key/name/policy, bounded body/attempts and private minimal responses |
| API→restricted SQL | Narrow app-only definer; repeated owner check, permanent outcomes, sorted stock gates before root and complete service proof before commit |
| Financial writers→closed root | Immutable lifecycle boundaries, existing active-root write checks and strictly forward global stock clocks; no liquidation or hidden closed-book effects |
| Private reads→response | Final owner-active shared fences after hydration/commit/replay; normal closed/foreign/missing refusals and no retained financial recovery endpoint |
| Browser callbacks→current authority | Captured owner/session/operation/generation, durable metadata-only original, synchronous root masking and identity-only advisory events |
| Recovery archive→runtime grants | Exact source/profile/table/identity/authority evidence in no-ACL quarantine before fixed regrant; tested-source compatibility before rollback checkout |
| Source/process/artifact→qualification claim | Exclusive one-shot receipts, exact bindings and repaired no-follow source reads are present; final whole receipts have not yet been produced |

Nominal ASVS level1 follows the workflow default; no explicit project level was
configured. This is declared-threat verification, not comprehensive ASVS
certification. Relevant existing controls correspond to validation/business
logic, authentication/session, authorization, frontend encoding, data protection
and secure communication categories.

## Primary threat register

| Threat | Category / severity | Disposition | Status | Concrete control and proof location |
|---|---|---|---|---|
| T-14-01 | Tampering/Elevation high | mitigate | CLOSED | `0021_portfolio_closure_schema.py:20` deferred lineage and immutable evidence; `0022_portfolio_closure_provenance.py:25` same-connection complete preflight before retained-boundary backfill; migration negatives in `test_portfolio_closure_migrations.py:106,134,159,252` |
| T-14-02 | Tampering/Repudiation/DoS high | mitigate | CLOSED | `0023_portfolio_closure.sql:4` fixed-path definer, owner non-key lock, replay before quota, finite sorted stock gates, root-locked set recheck and derived terminal clock; `portfolio_closure.py:70` three whole-transaction attempts; authority tests at86,117,143,295,400,451 |
| T-14-03 | Tampering/DoS high | mitigate | CLOSED | `stock_ownership.py:593` transaction-bound private proof, exact instrument membership/actual held gates, retained confirmation-name equality and complete per-instrument core; original single-gate wrapper retained; SQL terminal triggers and service clock checks574; corruption/context/clock tests in closure stocks/clocks modules |
| T-14-04 | Elevation/Tampering high | mitigate | CLOSED | Explicit `PREFLIGHT_0023_SQL` and `GRANTS_0023_SQL` in Python bootstrap and independent `deploy/db/bootstrap-roles.sql`; `portfolio_migrate.py:80` role/inventory/supplemental/catalogue/ACL/default checks before child creation184; admission tests133,287,328,346,448,483,509,545 |
| T-14-05 | Tampering/Information disclosure high | mitigate | CLOSED | `portfolio-sources.py:31,80,106` fixed complete20/17 archives and authentication before import; explicit V3 producer inventory/manifest in `backup-snapshot.py`;31-table/24-tail independent fixture in `portfolio-closure-recovery-fixture.py`; producer/oracle/identity omission contracts retained |
| T-14-06 | Elevation/Tampering high | mitigate | CLOSED | `verify-restore.py:1330` compares complete original evidence in quarantine before fixed grants1370 and rechecks final evidence; `restored:1377` requires manifest for23; `deploy.sh:92,110,553` authenticates selected compatible source before checkout; consumer corruption and rollback refusal contracts retained |
| T-14-07 | Spoofing/Elevation/Disclosure/Repudiation high | mitigate | CLOSED | `api/v2/portfolios.py:165` CurrentUser/CSRF dependencies precede `read_closure_body`; management parser bounds8192 actual bytes and duplicate keys; `portfolio_closure.py:38` narrow private dispositions after service commit; actual identity response-loss/503/cancellation/zero tests38,79,101,163 |
| T-14-08 | Tampering/Repudiation/DoS high | mitigate | CLOSED | `portfolio_lifecycle.py:22` one read-only cause/revision interpretation, no future-event×closed-root work; `dividends.py:69` rejects closed selected causes, retained SQL remains authoritative after locks; worker active selectors38,55; actual both-order job/held-negative/sibling assertions in events tests148,213,298,354 |
| T-14-09 | Tampering/DoS high | mitigate | CLOSED | Existing actual instrument/root SQL authorities plus exact captured ID, bounded attempts/timeouts and original durable outcomes; race tests32,105,186,355,415,450,496 observe blocking PIDs and exact frozen/sibling results; canonical bigint correction preserves PostgreSQL identity range |
| T-14-10 | Elevation/Information disclosure high | mitigate | CLOSED | `portfolios.py:55` final ordered owner-active FOR SHARE fence, metadata/list calls51,174; both History services and crypto/stock response success/refusal routes call final fences after work; `14-READ-AUTHORITY.md` query inventory; privacy tests81,115,210,239,279,315,359,432 |
| T-14-11 | Tampering/Disclosure/DoS high | mitigate | CLOSED | `portfolioDeletion.ts:43,85` exact frozen original and minimal matching receipt, finite sanitized errors, only durable409 terminal; `portfolioDeletionAttempt.ts:22,69,116,131`16000-byte owner-bound storage, readback-before-send, one original and guarded resolution; no stored finances/credentials/receipt |
| T-14-12 | Spoofing/Tampering/Disclosure high | mitigate | CLOSED | `usePortfolioDeletion.ts:251` captured scope and ownerCurrent, `perform:459` persist then quarantine before mutation, explicit checking and `retry:false`; metadata readiness/exact-root review exclusion239; original lease outside financial Outlet; actual stored-marker/context regressions retained |
| T-14-13 | Disclosure/Elevation high | mitigate | CLOSED | Deletion hook serial retirement348, restoration fresh owned list292 and current-original exclusion; target/overview/switcher accepted projections consume readiness/quarantine; `portfolioMetadataEvents.ts:10` finite identity-only advisory shape; stale callbacks cannot restore accepted finance or financial original retries |
| T-14-14 | Tampering/Disclosure/Spoofing high | mitigate | CLOSED | `PortfolioDeleteForm.tsx` renders reviewed name as React text, separate Cancel/final control and metadata-only unknown/refusal; current completion guard36; `App.tsx` host outside financial Outlet/static authenticated recovery; no name/key in recovery URL; routed refusal/trailing-slash/heading regressions retained |
| T-14-15 | Elevation/Tampering/DoS high | mitigate | CLOSED | Migrator finite14/20/21/22 prior catalogue/ACL/default+supplement before Alembic; bootstrap-only inherited pair, unchanged final authority; `test-db-config.sh:31` borrowed stack labels/image/ports/health authentication and owns_stack cleanup distinction; genuine fresh/upgraded/cold authority evidence remains supplemental to18 |
| T-14-16 | Tampering/Repudiation/DoS high | mitigate | CLOSED — CR-01 resolved | Private claim-once supervisor268, gated recorded preflight292, original process identity/reaping and honest forced-finalizer status are present. `source_directory` and `source_bytes` now use no-follow descriptors for root/parents/leaves and identity/reopen checks; targeted independent re-review below resolves the original source-read defect |
| T-14-17 | Information disclosure/Tampering high | mitigate | CLOSED | Actual public lifecycle journeys in deletion spec177–530; guarded READ ONLY synthetic oracle; packet no-follow descriptors79–139, finite static SVG, complete TrustedPolicyPrefix464 and exact artifact/ZIP checks; both human flags must remain false295–296; original packet review findings independently resolved in17 report |
| T-14-18 | Tampering/Repudiation/Elevation high | mitigate | **OPEN — PENDING_PLAN18** | Runner/supervisor require source/archive/image guards and one complete child; original CR-01 is resolved. Uninterrupted whole-security and fresh seven-stage same-archive receipts at final reviewed source are absent. Historical partitions/bounded TLS/cold runs cannot close this row |
| T-14-19 | Repudiation/Tampering high | mitigate | **OPEN — PENDING_PLAN19** | Verifier refuses forged acceptance flags; actual new owner UI response and distinct genuine native200 response have not occurred. This is the later human gate, not a new runtime defect or a waived Plan18 test |
| T-14-19-PII | Information disclosure high | mitigate | CLOSED | Synthetic read-only packet, script/form/network restrictions, sanitised traces and false human flags; no actual account/credential payload supplied by packet generation; native/owner results remain unclaimed |

## Supply-chain threat register

All18 rows below retain their authored `mitigate` disposition. The common control
is unchanged locked dependency/image inputs, exact accepted-risk policy S01,
raw audits and five strict image scans in `security_commands()` and CI. Read-only
Git comparison from9527e35 confirms no Phase14 changes to `backend/uv.lock`,
`frontend/package-lock.json`, backend/frontend Dockerfiles,
`deploy/audit-frontend.mjs`, or `deploy/scan-images.py`. No install, lock/image
version change, scanner filter expansion or new risk acceptance occurred in this
audit. Final actual audit/scan results still belong to T-14-18.

| Threat | Category / severity | Disposition | Status | Evidence |
|---|---|---|---|---|
| T-14-01-SC | Supply-chain tampering high | mitigate | CLOSED | S01; unchanged source comparison; strict runner graph |
| T-14-02-SC | Supply-chain tampering high | mitigate | CLOSED | S01; unchanged source comparison; strict runner graph |
| T-14-03-SC | Supply-chain tampering high | mitigate | CLOSED | S01; unchanged source comparison; strict runner graph |
| T-14-04-SC | Supply-chain tampering high | mitigate | CLOSED | S01; unchanged source comparison; strict runner graph |
| T-14-05-SC | Supply-chain tampering high | mitigate | CLOSED | S01; unchanged source comparison; strict runner graph |
| T-14-06-SC | Supply-chain tampering high | mitigate | CLOSED | S01; unchanged source comparison; strict runner graph |
| T-14-07-SC | Supply-chain tampering high | mitigate | CLOSED | S01; unchanged source comparison; strict runner graph |
| T-14-08-SC | Supply-chain tampering high | mitigate | CLOSED | S01; unchanged source comparison; strict runner graph |
| T-14-09-SC | Supply-chain tampering high | mitigate | CLOSED | S01; unchanged source comparison; strict runner graph |
| T-14-10-SC | Supply-chain tampering high | mitigate | CLOSED | S01; unchanged source comparison; strict runner graph |
| T-14-11-SC | Supply-chain tampering high | mitigate | CLOSED | S01; unchanged source comparison; strict runner graph |
| T-14-12-SC | Supply-chain tampering high | mitigate | CLOSED | S01; unchanged source comparison; strict runner graph |
| T-14-13-SC | Supply-chain tampering high | mitigate | CLOSED | S01; unchanged source comparison; strict runner graph |
| T-14-14-SC | Supply-chain tampering high | mitigate | CLOSED | S01; unchanged source comparison; strict runner graph |
| T-14-15-SC | Supply-chain tampering high | mitigate | CLOSED | S01; unchanged source comparison; strict runner graph |
| T-14-16-SC | Supply-chain tampering high | mitigate | CLOSED | S01; unchanged source comparison; strict runner graph |
| T-14-17-SC | Supply-chain tampering high | mitigate | CLOSED | S01; unchanged source comparison; strict runner graph |
| T-14-18-SC | Supply-chain tampering high | mitigate | CLOSED | S01; unchanged source comparison; strict runner graph |

### S01 — Existing issue35 accepted-risk scope, unchanged

The existing owner acceptance is
`https://github.com/YokAI-open/Birja/issues/35`, advisory
`https://github.com/advisories/GHSA-fc5q-39xc-vjpf`, through
**2026-12-17T00:00:00Z**. `deploy/audit-frontend.mjs:10` pins manifest SHA256
`73cd4f25fb329d7d0711321ee56dd9f07b25426eb9ddb69f3491396c2ccbdb59` and
lock SHA256 `1461d4f89e875a5b915278e9d39ba413608fa4ff816fab6be6b21e280db5475b`.
The reviewed locked picomatch versions remain4.0.7 and nested2.3.2. Only exact
`node_modules/picomatch` and
`node_modules/micromatch/node_modules/picomatch` HIGH advisory paths qualify;
other HIGH, any CRITICAL, malformed audit data, changed locks/manifests,
unmatched paths, or expiry refuse. Existing risk is retained, not remediated.
No Phase14 threat is newly accepted under this record.

## Original defect and required next evidence

The original finding below is retained as history. Its implementation defect
is resolved by the targeted independent re-review at the end of this report;
the remaining Plan18 and Plan19 evidence requirements still apply.

**CR-01, owning Plan16:** In `run-portfolio-validation.py:197–203`, a cached
descendant such as `backend/app/main.py` can be read through a directory link
although the final entry is not itself a link. This can hash outside-checkout
bytes; equal-byte substitution leaves the snapshot unchanged. It directly
contradicts the claimed source guard. The final leaf-link test in
`test-portfolio-validation-contracts.py:229` does not cover ancestor/root links
or classification/open replacement. This source trace independently confirms
the integrated code report; no outside-data access was performed to prove it.

Required repair: descriptor-relative no-follow root/ancestor traversal before
descendant access, no-follow ordinary-file reads with regular `fstat` checks,
and explicit safe leaf-link metadata handling. Add controlled temporary-tree
ancestor/root/link-swap/equal-byte negatives and ordinary positives. The parent
has scoped this fix; this auditor changes no source. Independent code/security
re-review must confirm its disposition before final campaigns.

After repair, T-14-18 additionally needs literal whole all-security exit0 and
fresh complete seven-stage recovery at one reviewed frozen source, with exact
image/archive/CORE/unit bindings, source-destroyed before-oracle, quarantine,
roles/TLS parity, rollback/refusal, original replay and verified owned cleanup.
Do not combine historical partial receipts. T-14-19 remains separately pending
until the two actual human outcomes; no automated layout or prior approval
closes that gate.

## Flags, audit trail and sign-off

No unregistered summary threat flag was identified. The process/file access
surface maps to T-14-16/18; packet source/file parsing maps to T-14-17/19-PII;
new schema/closure API maps to T-14-01–07. No additional proven implementation
blocker or warning was identified in this scoped threat-control pass.

| Audit date | Total | Closed | Open | Detail |
|---|---|---|---|---|
|2026-11-20|38|35|3|Distinct security agent at4264357; one implementation defect affects16/18, final18 evidence and actual19 human gates pending |
|2026-11-20|38|36|2|Same independent security agent atd2e8885; CR-01 resolved/T-14-16 closed, complete18 evidence and actual19 human gates remain pending |

- [x] Every authored threat has an explicit disposition and current status.
- [x] Existing issue35 scope remains unchanged; no new high risk accepted.
- [x] CR-01 mitigation independently reverified atd2e8885.
- [ ] Complete final Plan18 security/recovery evidence verified.
- [ ] Separate actual Plan19 outcomes verified.
- [ ] `threats_open: 0` and final `status: verified`.

Only this report was written. No tests, DB/browser/campaign, active security
demonstration, dependency change, provider/production operation, commit, push,
global planning-state update or unrelated `.claude/` modification occurred.

## Independent targeted CR-01 security re-review — resolved

This follow-up reviewed RED `407a6c0` and committed repair
`d2e8885b798e00a2932a18524a80d6268f28533c`, limited to
`deploy/tests/run-portfolio-validation.py` and its validation-contract tests.
The original aggregate audit, finding and35/38 initial disposition remain
preserved above. No source changes, tests, database, browser or campaign were
performed by this reviewer.

`source_directory()` starts at `/` and opens every root/ancestor component with
descriptor-relative `O_DIRECTORY | O_NOFOLLOW`. Linked root, root ancestor,
source parent and ignore-metadata parent therefore refuse before a descendant
read. Ignore metadata is read with links forbidden before Git enumeration.
Ordinary leaves are classified with no-follow stat, opened with `O_NOFOLLOW |
O_NONBLOCK`, verified by regular-file `fstat` and exact identity comparison,
then read only through that opened descriptor. Identity is rechecked after
reading and the parent pathname is reopened through guarded traversal, so a
parent replacement cannot redirect the read and is rejected afterward. Root
identity and ignore bytes are checked again when inventory finishes.

Safe in-root leaf links contribute only their own `readlink` metadata. Their
finite regular leaf target is inspected without following links and target
parents receive guarded traversal and a reopen identity check; the target's
bytes are never consumed through the link. Existing ordinary positives,
nonignored additions, missing/renamed-source refusal, leaf-link identity changes
and ignored-credential behavior remain covered.

The synthetic regressions address the original control gap: external and
internal linked ancestors even with equal target bytes; root/root-ancestor and
ignore-parent links before Git; leaf replacement at open; and parent replacement
after opening its descriptor. The last case observes the original descriptor
read, explicitly excludes controlled outside bytes, and requires refusal.
These assertions verify the mechanism instead of merely searching for flags.

The read-only raw RED log records four methods/six failing subcases at old
source. Final `source-frozen.log` records33 passing runner/supervisor tests in
8.250s, and `ci-frozen.log` records94 passing CI-ops tests in23.865s.
`image-final.log` records22 passing image/source tests in5.684s before the final
target-parent metadata recheck; that narrower source boundary is retained and
is not presented as a rerun at final bytes. The final33/94 groups ran after
that refinement. These are reviewed recorded results, not tests newly run by
the security auditor. Logs are preserved under
`/tmp/birja-phase14-campaign-plan18-repair/`.

Independent hashing confirms final runner SHA256
`e646fd8e25ca9547142eb2f9e480be3321cdad3ae84ec099d014053c82c8f04b`
and test SHA256
`4dc3836cb535ea8827d139a46a3dae57997f16152956df479adaac264a6f2619`.
The independent code re-review also records zero remaining blockers/warnings.
No additional concrete defect was established by this defensive security
re-review. **CR-01 is resolved; T-14-16 is CLOSED; implementation defects:0.**

**T-14-18 remains OPEN/PENDING_PLAN18** until the actual uninterrupted whole
security and same-source seven-stage same-archive recovery receipts, exact
bindings and owned cleanup are verified. **T-14-19 remains OPEN/PENDING_PLAN19**
until the distinct actual owner UI/native200 responses. Neither later result
is inferred from source repair, focused test logs or this report. Current
register:36 closed/38;2 pending evidence gates; no new accepted high risk.
