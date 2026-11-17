---
phase: 12-preserve-existing-investing-under-portfolio-ownership
verified: 2026-11-17T23:03:54.102Z
status: passed
score: 8/8 consolidated must-haves verified
roadmap_score: 5/5
requirements_verified: 7/7
plan_truths_accounted_for: 59
overrides_applied: 1
source_commit: 4b4320b4cc373268a8d598612a563cd5ef199700
reviewed_head: f2c48f0537b5123d1278721fc14cd3e09d29ef9e
overrides:
  - must_have: "The current frozen source satisfies the complete strict security qualification, including npm audit HIGH policy."
    reason: "The owner explicitly accepted only GHSA-fc5q-39xc-vjpf/CVE-2026-112366 and requested issue35 plus continued development. Raw findings remain visible; exact identity/hash/path/expiry controls reject unrelated HIGH, all critical and invalid evidence. Actual complete security and fresh recovery pass under this documented policy."
    accepted_by: project owner
    accepted_at: "2026-11-17"
    acceptance_time_precision: date
accepted_risks:
  - advisory: GHSA-fc5q-39xc-vjpf
    cve: CVE-2026-112366
    issue: https://github.com/YokAI-open/Birja/issues/35
    expires: "2026-12-17T00:00:00Z"
    status: unresolved_owner_accepted
    scope: "Reviewed frontend manifest/lock and exact Node tooling npm picomatch4.0.4 identity/path/source only; no other HIGH/critical exception."
re_verification:
  previous_status: gaps_found
  previous_score: 7/8
  gaps_closed:
    - "Common security qualification gap: explicit owner advisory acceptance, fail-closed shared npm/image controls, separately approved Python repair, actual complete current security and fresh source-bound recovery."
  gaps_remaining: []
  regressions: []
must_haves:
  truths:
    - "Existing user finances, baseline, holdings, basis, fills, History and retry identities survive first-portfolio association without grant or reset."
    - "Named explicit-target crypto/stock investing and original receipt recovery work without fallback or changed execution rules."
    - "Mixed paginated History, originals, references and cursors disclose only the chosen portfolio."
    - "Identity and session lifecycle work with zero/one/many portfolios and legacy finance cannot bypass explicit targeting."
    - "Fresh/upgraded investing retains restricted verified-TLS roles, immutable evidence and matching ownership constraints."
    - "Current0017 and retained recovery complete against one source-bound immutable archive with exact financial and authority parity."
    - "Owner UI and genuine native200% acceptance are explicit and apply to unchanged render inputs."
    - "The current frozen source satisfies the complete strict security qualification, including npm audit HIGH policy."
  artifacts:
    - path: backend/alembic/versions/0017_portfolio_ownership.py
      provides: Final owned financial schema and narrow authority
    - path: backend/app/api/v2/router.py
      provides: Production explicit portfolio routes
    - path: frontend/src/components/PortfolioTargetBoundary.tsx
      provides: Verified target before financial children
    - path: deploy/tests/run-portfolio-validation.py
      provides: Actual source-bound complete security and recovery graph
    - path: deploy/audit-frontend.mjs
      provides: Fail-closed exact accepted-advisory audit policy and raw findings
    - path: deploy/scan-images.py
      provides: Immutable five-image scans with exact accepted Node tooling finding
  key_links:
    - from: backend/app/main.py
      to: backend/app/api/v2/router.py
      via: Production include_router at /api/v2
    - from: backend/app/core/deps.py
      to: backend/app/services/portfolios.py
      via: CurrentUser and explicit active root resolver
    - from: frontend/src/App.tsx
      to: frontend/src/components/PortfolioTargetBoundary.tsx
      via: Scoped routes and verified Outlet context
    - from: deploy/tests/run-portfolio-validation.py
      to: deploy/audit-frontend.mjs
      via: Same node ../deploy/audit-frontend.mjs command as frontend CI
deferred:
  - truth: "Public creation, naming/renaming, optional editable/empty descriptions and comparison overview."
    addressed_in: Phase13
    evidence: "Roadmap Phase13 success criteria explicitly deliver independently funded strategy management/comparison."
  - truth: "Public confirmed terminal deletion, including holdings or the final portfolio."
    addressed_in: Phase14
    evidence: "Roadmap Phase14 delivers deletion confirmation, freeze and zero-active Create portfolio journey."
  - truth: "Full integrated management/deletion lifecycle acceptance and recovery."
    addressed_in: Phase15
    evidence: "Roadmap Phase15 qualifies create/name/description/compare/switch/delete; current revision recovery is verified here."
---

# Phase12: Preserve Existing Investing Under Portfolio Ownership Verification

**Goal:** Existing users keep investing in their first named portfolio with their actual finances and History preserved, while financial requests and authority are explicitly bound to that portfolio.

**Status:** passed — 8/8 consolidated truths, including one explicit owner-approved security-policy override; functional roadmap5/5 and assigned requirements7/7.

**Re-verification:** Yes. The earlier7/8 report is preserved in Git history at2792536 and its underlying failed receipts remain intact. The owner subsequently requested “can you create an issue in gh for the future about this and continue without fixing it?” This accepts the specific unresolved advisory, not a general security waiver or proof of remediation. Exact acceptance time was not recorded; the override records the known date only.

## Goal Achievement

| # | Observable truth | Verdict | Independently checked evidence |
|---|---|---|---|
|1|Original cash, stored baseline, holdings, basis, fills, History and retry identity survive association without grant/reset.|VERIFIED|0015/16/17 and all application/Alembic source are byte-unchanged from the prior substantive verification. Existing seven-table bounded NULL-only association and immutable legacy/global evidence remain. Current3114 backend and fresh exact recovery pass. accounts.get_or_create_user grants only after successful new User insertion; get_me reads identity only.|
|2|Explicit named-root crypto/stock execution and original receipt recovery preserve rules without fallback.|VERIFIED|Resolver actually queries Account.id+user_id+closed_at; services lock/recheck that root and compare original payload/root on globally found retry keys. Production v2 router is mounted by create_app. Boundary renders financial children only for ready verified target. Current full unit/API/browser and recovery service consumers pass.|
|3|History, originals, references and cursors disclose only the selected root.|VERIFIED|Actual trade/event queries constrain user and portfolio; decoder requires expected root. The unchanged clients/hooks partition root/session/owner and validate response identity. Current complete backend/frontend/browser tests cover private original hydration and seek pagination.|
|4|Identity/session lifecycle works at zero/one/many portfolios; legacy finance cannot bypass targeting.|VERIFIED|v2 identity returns User.email independently of Account; legacy refusal remains authenticated and state-changing CSRF protected. Real router composition and boundary zero/many/unavailable paths are unchanged and covered by the current full suite.|
|5|Fresh/upgraded journeys preserve restricted verified TLS, immutable evidence and ownership authority.|VERIFIED|Fresh and upgraded actual service-consumer TLS lanes pass on the approved patched runtime, including63role denials, immutable accounting, scoped stock/dividend effects, badCA/hostname/plaintext refusals and authority parity. No application/model/schema mutation was introduced by audit/image repairs.|
|6|Current0017 and retained recovery complete from one immutable source-bound archive with exact state/authority.|VERIFIED|Actual full seven-stage recovery exits0,2694.692s, final same_archive_final_ci=true. Independently recomputed new196689920-byte archive SHA d253bc51…26be; declared-runtime source-destroyed cold restore and retained0007–0014 exact oracles pass.|
|7|Both explicit owner UI/native200 acceptances remain applicable.|VERIFIED|HUMAN-UAT records “approved” and separately “Yes—native 200% passed”,2passed/0pending. Owner ZIP independently hashes c87cb4a3…d55f. Frontend and capture runner are byte-unchanged from prior verified render inputs, so no new UI checkpoint is invented.|
|8|Current frozen source satisfies complete strict security qualification, including npm HIGH policy.|PASSED (override)|Owner accepted only the named picomatch advisory via issue35. Shared helper and image classifier retain full findings and reject unrelated HIGH/critical, error/schema/transport, changed hashes/path/version and expired approval. Actual whole all-security exits0,1479.850s. The separate Python advisory is fixed by the separately approved official image patch; it is not waived.|

**Score:**8/8 including1explicit override. No FAILED/BLOCKER or UNCERTAIN/WARNING truth and no pending human item.

### Disconfirmation and source regression

The initial adversarial hypotheses remain disproved: no migration regrant/reset, no root-switch retry/history leak, and no cached-image/broadened-authority substitute for real recovery. This re-verifier checked actual resolver/router/identity/grant code, trade root/lock/retry links, root-bound History predicates and boundary rendering. It also verified that backend/app, backend/alembic, frontend and the capture/browser runner have **no diff from d9da271**. Thus the prior functional data-flow verification is retained by direct source equality, not by trusting task summaries.

Current HEAD f2c48f0 differs from tested4b4320b only in four qualification documents. A separate git diff over backend/frontend/deploy/.github/all Compose inputs is empty. The new financial-authority test selector is test-only and preserves complete named/ordered ownership constraints; the approved Python/Docker and scoped audit changes were independently reviewed and exercised by actual fresh recovery.

## Plans, Artifacts and Wiring

All31plan and31summary frontmatters were read. They declare exactly the seven assigned requirement IDs,59plan truths,145artifact references/133unique existing paths,57key links and121threat rows. No required artifact is missing. Original56plan truths retain the prior substantive/wiring verification by unchanged application and SQL source; revised29–31 are additionally verified below. Existence and task counts alone do not establish success.

| Plan | Exact additional truths | Result | Substantive/wiring evidence |
|---|---|---|---|
| 12-01 | 1. Guarded authenticated migrator bootstrap and connection tests pass on existing schema; feature tests collect with independent economics and migration/resume/refusal assertions, without claiming future feature completion.<br>2. All matrix tests collect; no provider or production fixture; pending feature assertions remain visible. | VERIFIED / VERIFIED | Guarded LOGIN/session_user helper and independent legacy snapshots; current full backend migration/authority families pass. |
| 12-02 | 1. Model declares root identity and closed state; original monetary columns unchanged; future multi-root shape is represented without enabling creation.<br>2. Holdings and trades express root lineage with globally unique user retry identity; no old economic payload reshaping. | VERIFIED / VERIFIED | Account retains Numeric(20,8) cash/baseline; model compound owner keys and global retry uniqueness are installed by0017. |
| 12-03 | 1. Owned stock metadata has coherent root tuples; split applications stay global with nullable persisted digest marker, and terminal epochs preserve global state.<br>2. Payment/decision model constraints identify one owned entitled root; independent roots can receive their own effect once. | VERIFIED / VERIFIED | Owned fact/movement/entitlement/payment/decision composite keys; global split marker and closure metadata retained. |
| 12-04 | 1. 0015 adds shape only; actual-migrator-only finite exception has negative SQL proof.<br>2. Each old owned row maps once under authenticated migrator with refusal/resume proof; global applications/NULL markers/digests remain unchanged; unsafe reversal refuses. | VERIFIED / VERIFIED | 0015 finite association guard;0016 OWNED_KEYS seven-table500-row batches, authenticated session_user, NULL-only association and pre-write downgrade refusal. |
| 12-05 | 1. All test_final_sql_* restricted-role scenarios collect without execution or broad-role fixtures; their required green execution belongs12-07-01 after actual0017.<br>2. Static stock asset contracts pass with exact signatures; real restricted-role SQL proof is required in12-07-01. | VERIFIED / VERIFIED | Fixed SHA-pinned0017_stock_portfolio.sql consumed by0017; actual full backend restricted final_sql suites pass. |
| 12-06 | 1. Tests exist before final dividend SQL consumer and cover direct restricted-role forgeries.<br>2. Static dividend asset contracts pass; actual payment/correction/freeze SQL proof is required in12-07-01. | VERIFIED / VERIFIED | Entitlement-derived active-root dividend SQL, narrow EXECUTE and direct-write revocation; actual restricted final_sql families pass. |
| 12-07 | 1. Actual0017 fresh/populated authenticated upgrades and all restricted-role final_sql economic/forgery/freeze checks pass; roots cover owned tables only, global applications retain immutable NULL/2 markers, and no migration bypass remains.<br>2. Intermediate runtime refuses deliberately; final code does not boot on an unsafe schema; no startup auto-migration. | VERIFIED / VERIFIED | 0017 removes association exception, validates compound FKs and installs active-write guards; startup schema admission refuses intermediate revisions. |
| 12-08 | 1. Financial adapters receive a verified explicit root; zero roots still authenticate; foreign/closed indistinguishable.<br>2. Identity works zero/one/many, signup alone grants once, reads and repeated sign-in never grant. | VERIFIED / VERIFIED | resolve_owned_active_portfolio matches id/user/closed_at; get_me reads User only; get_or_create_user grants only on new unique-email insert. |
| 12-09 | 1. Versioned identity is reachable when wired by15 and neither exposes pooled nor fake zero cash.<br>2. Legacy callers get deterministic refusal with valid OTP still usable by versioned client. | VERIFIED / VERIFIED | Production v2 identity composition; v1 verify refuses before OTP consumption; current auth/session families pass. |
| 12-10 | 1. Crypto economics unchanged; explicit root governs all reads/writes and global retry conflict; closed targets never reveal financial receipt.<br>2. Scoped adapters reject invalid target before economic work; all new responses unambiguously identify original portfolio. | VERIFIED / VERIFIED | Explicit OwnedActivePortfolio, account FOR UPDATE, root+owner holdings, global retry lookup and require_same_order root/payload comparison. |
| 12-11 | 1. Stock execution and replay preserve existing gates/economics while restricting every financial path to original active root.<br>2. Stock HTTP has explicit target throughout and existing buy ask/sell bid/freshness rules remain intact. | VERIFIED / VERIFIED | Instrument gate→active-root locking→immutable fill/movement→final authority; CR-01 no-obligation exception fails closed on incomplete history. |
| 12-12 | 1. Persisted NULL legacy and2 new digests validate after reload with unchanged global IDs/digests; terminal holdings stay exact through later sibling splits.<br>2. Active roots apply once, closed holdings/cash/history stay frozen, uncertain actions retain existing suspension semantics. | VERIFIED / VERIFIED | Root journals/closure epochs and persisted NULL-v1/2 dispatch; once-only global split with active-root movement uniqueness. |
| 12-13 | 1. Eligibility source lineage remains exact per root and does not reactivate frozen experiments.<br>2. No hidden user-only worker or SQL invocation; active-root effects once and frozen roots unchanged. | VERIFIED / VERIFIED | Active root VERIFIED/ANCHORS worker discovery, portfolio-scoped entitlements and entitlement-bound SQL; no direct scheduler cash UPDATE. |
| 12-14 | 1. Valuation preserves old outcomes for legacy root and never pools balances/returns.<br>2. Both History implementations prove complete scoped pagination and private original links. | VERIFIED / VERIFIED | Actual stored baseline/root valuation; trade2/mixed3 scoped seek cursors; all event and original joins match owner+root. |
| 12-15 | 1. Discovery is identity-only metadata; every financial read resolves explicit owned active root.<br>2. Only explicit scoped financial routes can execute or disclose; legacy refusal is measured before effect. | VERIFIED / VERIFIED | main.create_app mounts v2; v1 finance is authenticated refusal; private metadata/statement/History routes consume verified root. |
| 12-16 | 1. Restricted production/dev roles agree and cannot mutate portfolio lifecycle or old money evidence.<br>2. Migration-to-final is reachable without weakening intermediate refusal; deployment admission prevents unsafe old-code writes. | VERIFIED / VERIFIED | Exact pinned routine/owner/ACL inventories; authenticated source-pinned final migrator; current fresh/upgraded verified-TLS and role-denial receipts. |
| 12-17 | 1. Final producer recognizes only exact qualified schema and cannot back up an intermediate state as runnable.<br>2. Consumer and wrappers reject mutated schema/data/source and prove exact owned final recovery, without treating staged schemas as supported. | VERIFIED / VERIFIED | Exact source-owned0017 backup/restore catalogue and projections, staged schema refusal, quarantine and negative mutation contracts. |
| 12-18 | 1. Fixture exposes deterministic create/verify/projection commands with no production defaults; meaningful cold comparison is runnable.<br>2. Operational graph has explicit final and retained lanes, verified TLS/roles and serial same-archive source binding. | VERIFIED / VERIFIED | Declared current Dockerfile runtime factory, immutable image/source/archive checks, independent before-oracle, source destruction and separate-server cold receipt. |
| 12-19 | 1. Identity client exposes no cash and existing auth/refresh semantics remain valid.<br>2. Target identity is available before financial queries, zero/many states never choose an arbitrary root. | VERIFIED / VERIFIED | Identity-only v2 client; captured owner/session metadata target; explicit target never falls back and sole legacy discovery navigates first. |
| 12-20 | 1. Trade clients cannot call an unscoped URL or manufacture current-root identity on an old receipt.<br>2. Read clients carry explicit root through every page and original-reference request. | VERIFIED / VERIFIED | Explicit root URLs and strict response IDs; immutable original attempt and portfolio-bound cursor checks in financial clients. |
| 12-21 | 1. Crypto hook cannot spend or display stale root data across navigation/identity changes.<br>2. Stock recovery remains original-target and all existing market/freshness checks retain behavior. | VERIFIED / VERIFIED | Owner/root/session query and hidden state keys; frozen attempts and current-target publication guards; current full frontend/browser regressions. |
| 12-22 | 1. Known value, cash and returns can only originate from current verified target.<br>2. No hidden pagination or detail cache leaks across roots; same-root retry remains deterministic. | VERIFIED / VERIFIED | Target-bound valuation/infinite History, session notification, guarded accepted pages/detail/seen state and same-root append retry. |
| 12-23 | 1. Reusable label/boundary complies with approved UI contract and blocks stale finance.<br>2. Reachable scoped routes and navigation retain portfolio identity; Account remains valid with zero roots. | VERIFIED / VERIFIED | App scoped routes→PortfolioTargetBoundary→verified Outlet; empty/ambiguous/unavailable surfaces mount no finance. |
| 12-24 | 1. Every crypto investment surface unambiguously names its root with unchanged financial behavior.<br>2. Stock confirmation and immutable receipt remain original-target and accessible at responsive widths. | VERIFIED / VERIFIED | Trade pages consume Outlet target; named confirmation/receipt surfaces and frozen original attempt; scoped receipt component links. |
| 12-25 | 1. Existing accepted financial presentation is preserved for one explicitly named root.<br>2. History list, pagination and original detail disclose one active owned portfolio only. | VERIFIED / VERIFIED | PortfolioPage→usePortfolio and HistoryPage→useEventHistory render real scoped responses; detail state root/session lifetime. |
| 12-26 | 1. All new journeys are reachable from isolated target routes; review bundle tied to exact source and synthetic evidence.<br>2. CI graph and retained archive contents enforce ownership/source/security contracts with unchanged strength. | VERIFIED / VERIFIED | Actual browser journeys and strict CI command graph; current browser diagnostic plus independently rerun6 browser/37 CI contracts. |
| 12-27 | 1. All complete suites/audits/scans actually pass for same frozen source or execution stops with truthful failures; focused latency not falsely claimed.<br>2. Real current and retained isolated recovery proof passed for one exact source/archive, complete sanitized receipt and review packet ready; no production/provider work. | VERIFIED / VERIFIED | Historical failed stops remain recorded; new31 actual complete security and fresh seven-stage recovery pass at one frozen source, with the owner-approved advisory disposition. |
| 12-28 | 1. Owner explicitly accepts changed synthetic UI for recorded source; absence or ambiguous response is not approval.<br>2. Owner's genuine native200% pass recorded for same source, deferred/live and future-phase boundaries retained. | VERIFIED / VERIFIED | Explicit owner approved and separate Yes—native200%passed; unchanged125render inputs, immutable packet and documented245/249broad match. |
| 12-29 | The unresolved picomatch advisory has explicit owner acceptance and a bounded follow-up, without claiming a fix. | VERIFIED | Exact owner decision, issue35, immutable lock bindings, expiry and reassessment conditions in12-ACCEPTED-RISK.md. |
| 12-30 | CI and local qualification visibly report only the exact accepted advisory while rejecting unrelated HIGH/critical and invalid evidence. | VERIFIED | Complete Node helper and shared invocation;12 independently rerun audit tests plus source review and actual full campaign. |
| 12-31 | Functional/recovery assurance and complete qualification pass while accurately disclosing accepted unresolved risk. | VERIFIED | Independently hashed actual whole-command exit0 receipts at4b4320b, new source-bound archive and all7 recovery stages. |

### Required Artifact Coverage

The prior initial report's131unique-artifact inventory remains applicable for unchanged implementation. All133current unique required paths exist; the two additional required artifacts are12-ACCEPTED-RISK.md and deploy/audit-frontend.mjs. Changed runtime/test/CI/audit artifacts are substantive and wired, not placeholders.

| Artifact group | Substance and actual consumer | Verdict |
|---|---|---|
|0015/16/17 migrations, fixed SQL and schema admission|Real finite association, owner tuples, active-root SQL guards and staged/runtime refusal; consumed by authenticated bootstrap/migrator and exact catalogue recovery.|VERIFIED|
|Identity/root and financial v2 services/routers|Authenticated explicit-root resolver, transactional financial locks, immutable retry payload and private seek queries; mounted in real app.|VERIFIED|
|Frontend clients/hooks/pages/boundary|Validated target identity and owner/root/session data/cache lifetime feed real financial pages; no financial child before ready metadata.|VERIFIED|
|Backup/restore/catalogue/roles/TLS/runtime factory|One authenticated archive, independent before-oracle, source destruction, fixed retained bytes, Config/RootFS identity and restricted restored authority.|VERIFIED|
|deploy/audit-frontend.mjs and tests|Full raw npm audit, exact advisory/lock/expiry policy; same CI/local invocation and12 meaningful positive/refusal tests.|VERIFIED|
|deploy/scan-images.py and image contracts|All five saved immutable images, fresh DB, exact report/config checks; Node-only specific finding accepted separately; other findings/errors fail.|VERIFIED|
|backend/Dockerfile and matching assertions|Only approved exact Python-family pins changed; complete reviewed36-package/14-change closure and source/artifact review; actual current images rescan with no Python HIGH.|VERIFIED|
|Risk, repair, UAT and qualification records|Explicit owner decisions, exact package/source/receipt hashes and raw result evidence; historical failures remain distinguished.|VERIFIED|

### Key Links

| Link | Concrete wiring | Verdict |
|---|---|---|
|create_app→v2 router→owned-active dependency|Actual include_router /api/v2, user/root/active query before financial service.|WIRED|
|Trade/retry→owned account/holding/journal/final SQL|Root+owner predicates, root lock, immutable original identity/payload and final authority.|WIRED|
|History→source rows/original hydration/cursor|User/root constrained unions and deterministic seek; expected portfolio identity in cursors.|WIRED|
|App→boundary→Outlet→hooks/pages|Only ready target mounts children; captured root reaches financial clients and named receipt/details.|WIRED|
|CI and local security→shared audit helper|Both invoke node ../deploy/audit-frontend.mjs and its Node tests from frontend cwd; raw audit and exact expiry/hash controls.|WIRED|
|Actual full runner→immutable image scans/recovery|Complete command sequence, failure propagation, source/archive/image checks and fresh/upgraded parity between seven stages.|WIRED|

## Data-Flow Trace (Level4)

| Rendered artifact/data | Source chain | Real data and boundary | Status |
|---|---|---|---|
| PortfolioPage cash/baseline/value/holdings | Account/Holding/marks → get_portfolio → v2 portfolios → fetchPortfolio → usePortfolio(target) → page/PortfolioHoldings | Actual owner+active-root query joins holdings by portfolio; calculate_portfolio receives stored starting_cash, not a fixed new baseline. Response validates root/name/monetary strings; hook only exposes current owner/root/session cache. | FLOWING |
| Crypto ticket/preview/receipt | Account/Holding/Trade/prices → trading quote/execute → v2 trades → strict trades client → useQuote/useHolding/useTrade → TradePage | Decimal transaction locks selected account; fills persist root and original key/payload. Page freezes original attempt and names target; late callbacks cannot publish into another root. | FLOWING |
| Stock ticket/context/receipt | Instrument/quote/session/action authority + owned cash/holding → stock_trading + journal + final SQL → v2 stock_trades → strict client/useStockTrade → StockTradePage/StockTradeReceipt | Bid/ask/freshness/permission checks retained; matching root facts/movement and final cash/holding state required. Original root/key/payload preserved during unknown-result recovery. | FLOWING |
| Mixed History and original detail | Owned Trade/Fill/Movement/Payment/Decision → event_history union/original joins → v2 event-history → strict client → useEventHistory(target) → HistoryPage/HistoryEventDetails | Real deterministic root-filtered query and embedded original hydration; cursor carries expected root. Seen sets, pages, details and focus lifetime are scoped; no empty hardcoded child props replace finance. | FLOWING |
| Trade History continuation | Owned Trade → history.list_history → v2 history → strict history client/useHistory | Owner/root predicates and trade2 cursor checked before query; final active-root recheck; continuation publication remains target/session bound. | FLOWING |
| Target label and identity-only Account | User → v2 me; owned active Account IDs/names → metadata API → usePortfolioTarget → boundary/PortfolioContext/pages | Metadata query is real, bounded by supported owned roots and stable ID ordering. Empty/many responses are legitimate states; sole legacy discovery navigates before finance. Account does not synthesize zero cash. | FLOWING |

## Independent Behavioral Spot-Checks and Probes

| Behavior | Actual verifier command/result | Verdict |
|---|---|---|
|Exact accepted audit plus unrelated HIGH/critical/schema/graph/error/hash/expiry refusal|node deploy/tests/test-frontend-audit.mjs;12pass/0skip,114ms, exit0. No network audit invoked by this check.|PASS|
|Image identity, raw finding retention, exact exception and operational/mixed/unknown refusal|python3 deploy/tests/test-image-contracts.py;17pass,0.699s, exit0. Injected Docker/scanner contracts only; no service started.|PASS|
|Functional source remains the previously verified implementation|git diff d9da271 HEAD -- backend/app backend/alembic frontend deploy/tests/run-stock-browser.py; empty.|PASS|
|Final source equals the actually qualified runtime/tooling source|git diff4b4320b HEAD over backend/frontend/deploy/.github/Compose; empty.|PASS|

Prior initial-verifier offline browser6/recovery10/CI37contract results remain historical supporting evidence, not newly invoked by this verifier. No explicit probe-*.sh is declared by the31plans, and no conventional probe path was identified. Actual full campaigns below were verified from their raw process evidence; no full suite, service, provider or production operation was started during this verification.

## Independently Verified Actual Qualification

Both actual commands ran at frozen4b4320b4cc373268a8d598612a563cd5ef199700. This verifier parsed their raw result/source receipts, recomputed every log/source SHA below, checked unchanged before/after HEAD, empty tracked-drift lists and zero containers/networks/volumes for all six exact-owned projects. These are two successful complete commands, not an assembly of separate diagnostics.

| Actual command | Exit/time | Contents | Verdict |
|---|---|---|---|
|python3 deploy/tests/run-portfolio-validation.py --suite all-security|0;1479.8497948981822s|Backend3114/60critical modules100%(5020statements/1604branches), clean Python audit, frontend958/lint/types/format/build, audit12, browser59pass/1originaldeployed-CSPskip501.4s, builds/smoke5 and all5image policies.|PASS under explicit accepted risk|
|python3 deploy/tests/run-portfolio-validation.py --suite recovery|0;2694.6917584463954s|Image transition, retained0007–0014 exact encrypted roundtrips, current0017 declared-runtime source-destroyed cold restore, roles, upgradedTLS, freshTLS and selected rollback/refusal; final same_archive_final_ci=true.|PASS|

| Receipt | Raw log SHA256 | Source-receipt SHA256 |
|---|---|---|
|/tmp/phase12-accepted-retry2-security-4b4320b.*|ace8a8e70cc2b80234ad2261ed5e60166e64854873acc43bef660d45dc0c1f62|05485ef32941148f0c78dc0f31114c9d5c20ce5c50978d80954b3cb3f4a58619|
|/tmp/phase12-accepted-retry2-recovery-4b4320b.*|9bf74942a3aaef89c346c2485e867bdfb3338b064241ddcfc2b66b60c7788b24|f1686473ba3bbaa3665394dfe567fae5208f5219ba9a852cbb6fec0d82603d08|

### Actual image findings and identity evidence

The five preserved reports at /tmp/phase12-accepted-retry2-image-reports-4b4320b/ independently match their status.json report hashes and exported config/report ImageIDs. Aggregate ok=true and each target ok=true. Trivy0.76.1 uses the pinned scanner; DB UpdatedAt2026-11-17T19:04:24Z, DownloadedAt22:08:05Z and NextUpdate2026-11-18T19:04:24Z were fresh for the run.

| Target | Raw HIGH/CRITICAL | Accepted | Blocking |
|---|---:|---:|---:|
|runtime|0|0|0|
|builder|0|0|0|
|postgres|0|0|0|
|redis|0|0|0|
|node|1|1 exact picomatch finding|0|

Node raw row remains CVE-2026-112366, picomatch4.0.4 at usr/local/lib/node_modules/npm/node_modules/tinyglobby/node_modules/picomatch/package.json. The exact node target, vendor advisory, version/path, frontend Dockerfile hash and UTC expiry are required. No critical or unrelated HIGH is accepted. npm raw14HIGH/11moderate remain visible as accepted risk; the HIGH package entries propagate one advisory, not14independent vulnerabilities. The moderate policy remains unchanged.

The previously found Python CVE-2026-119170 is absent from both rebuilt runtime/builder scans after the separately approved official Python patch. Its source-provenance/unsigned-individual-APK limitations remain in12-PYTHON-PACKAGE-REVIEW.md; authenticated signed-index/control/data integrity and complete package closure were independently reviewed. No claim of a zero-vulnerability graph or upstream picomatch remediation is made.

### Exact recovery provenance and preserved history

The new uncompressed strict USTAR file /tmp/birja-phase12-proof/recovery.tar.gz is196689920bytes and independently hashes:
**d253bc51b876c7d629ee246ee47bd57274a5d9333e71318e11fcef586cff26be**.
Every stage authenticates current/retained/source/image/CORE/unit/payload bindings; final fresh/upgraded authority comparison passed.

The previous full archive/directory is separately retained at /tmp/birja-phase12-proof-d9da271-preserved-before-4b4320b/. Its196689920-byte archive independently still hashes94365aff1bbf8558bcc1481a19c10afea8c571801d54cf3ae3b79156f4af03eb. Historical d9da271 audit failure, e4c0a9f metadata-selector failure and f97b2d9 image failure remain failures, not rewritten passes. The current successful proof uses a new archive and actual commands.

## Requirements Coverage

The31plans declare exactly the seven Phase12IDs mapped in REQUIREMENTS.md. No assigned requirement is orphaned. The global checkboxes are still pending at verification time because this agent does not mutate them; implementation is now verified and ready for the parent's completion step.

| Requirement | Verdict | Supporting preserved implementation and current proof |
|---|---|---|
|PFUND-03|SATISFIED|Bounded finite migration, actual prior baseline/cash/quantities/economic bytes, no regrant onboarding and current exact same-archive recovery.|
|PFIN-02|SATISFIED|Explicit active resolver, root locks/final SQL, unchanged fee/freshness/eligibility rules and real current API/browser/TLS consumers.|
|PFIN-03|SATISFIED|Original root+payload/global retry comparison, immutable receipt replay, concurrent once-only effects and unavailable-root refusal.|
|PCTX-01|SATISFIED|Real names from metadata through verified target, ticket/confirmation/receipt/holding/History; accepted render-equivalent UI.|
|PVIEW-03|SATISFIED|Owner/root constrained mixed union, original hydration, root-bound seek/cursors and root/session publication guards.|
|PSAFE-02|SATISFIED|User-only identity/session, zero/one/many metadata states, no recreation/regrant reads and authenticated legacy refusal.|
|PSAFE-03|SATISFIED|Actual fresh/upgraded restrictedTLS/grants, immutable ownership catalogue, exact migration/current recovery and approved policy-qualified supply-chain checks.|

## Anti-Patterns, Security Disposition and Human Checks

No unreferenced TBD/FIXME/XXX marker occurs in the133required artifacts or changed runtime/test/CI source. Ready-state gating, empty metadata, session defaults and injected negative contracts are intentional, not hollow financial UI. Prior source security112threat entries and11targeted CR rechecks remain; new plans add9threat rows with an explicit accepted-advisory disposition. Source review is not substituted for the actual current qualification.

**No BLOCKER or WARNING remains.** Known nonblocking limits are the explicitly accepted picomatch advisory until the review deadline, the original deployed-CSP skip, recorded backend warnings/moderate advisories and disclosed package provenance limits. These do not imply live stock acceptance or a production/hosted-CI result.

**Human verification required:** None pending. Owner UI and genuine native200% were separately explicitly accepted. The immutable ZIP independently hashes c87cb4a3eb3feb52c42a37aa60ff69cce66d2ac8e2637847e6a977af1714d55f. All frontend/capture render inputs are unchanged since the prior verified125input equivalence; broad249entry equality is not newly claimed. Capture-time native200=false flags and unspecified browser name remain unaltered; later actual human acceptance is recorded separately.

## Deferred Items and Completion Boundary

| Item | Owner | Evidence and boundary |
|---|---|---|
|Additional funded creation/name/rename/optional editable or empty description/overview|Phase13|Explicit roadmap management and comparison outcomes; preservation foundation does not expose them prematurely.|
|Public confirmed terminal deletion and zero-active replacement journey|Phase14|Explicit deletion/freeze/last-portfolio outcomes; underlying terminal safety fixtures are already verified here.|
|Complete public management/deletion lifecycle recovery and acceptance|Phase15|Explicit final integration scope; current revision qualification was completed here, not postponed.|
|STOCK-01/02/03, DATA-01, MKT-01, SAFE-01 live verification|Separate deferred Phase7|November16manual campaign consumed; requirements remain unverified, admissionsOFF, no07-14summary fabricated.|

The Phase12 goal is achieved locally under the owner's one documented advisory override. Phase13 may be planned after the parent records completion. This is not milestone completion, stock activation, hosted CI, publication or deployment.

Only this report was written by the independent re-verifier. No global state, requirement checkbox, phase-completion SDK mutation, source change, dependency installation, commit, service or network/provider/production operation was performed.

_Verified: 2026-11-17T23:03:54.102Z_
_Verifier: independent gsd-verifier agent, re-verification of prior7/8 gap._

