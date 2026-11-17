---
phase: 12-preserve-existing-investing-under-portfolio-ownership
verified: 2026-11-17T18:50:00Z
status: gaps_found
score: 7/8 consolidated must-haves verified
roadmap_score: 5/5
plan_truths_accounted_for: 56
overrides_applied: 0
source_commit: d9da271b2b21f48f965dd54898a6bb8afcc9088e
reviewed_head: 1945adb0a51e27a1f6499e58c1907ce8589e96dc
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
      provides: Strict source-bound security and recovery graph
    - path: frontend/package-lock.json
      provides: Exact locked dependency graph subject to HIGH audit gate
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
      to: frontend/package-lock.json
      via: npm audit --audit-level=high in complete security sequence
gaps:
  - truth: "The current frozen source satisfies the complete strict security qualification, including npm audit HIGH policy."
    status: failed
    classification: BLOCKER
    reason: "Actual integrated all-security exits1 at npm audit:25 findings,14 HIGH and11 moderate. GHSA-fc5q-39xc-vjpf affects picomatch<=4.0.7; final saved official metadata reports latest4.0.7 and no patched version. Separate later browser/image diagnostics cannot convert the failed complete command into a pass."
    artifacts:
      - path: frontend/package-lock.json
        issue: "Locked picomatch4.0.7 and nested2.3.2 are affected; advisory propagates through14 HIGH package entries."
      - path: deploy/tests/run-portfolio-validation.py
        issue: "Correctly enforces unchanged npm audit HIGH gate; current complete execution fails."
      - path: .planning/phases/12-preserve-existing-investing-under-portfolio-ownership/12-LOCAL-VERIFICATION.md
        issue: "Current qualification remains blocked despite historical whole-security pass and current passing independent diagnostics."
    missing:
      - "A legitimate patched dependency candidate with exact scope, artifact checksums/provenance and separately authorized repair; none exists in the final saved official evidence."
      - "Successful complete strict qualification of the repaired frozen source with unchanged audit, coverage and image policy before phase advancement."
deferred:
  - truth: "Public additional strategy creation, naming/renaming, optional descriptions and comparison overview."
    addressed_in: "Phase13"
    evidence: "Roadmap Phase13 SC1–4 explicitly deliver create/name/description/funding and stable strategy comparison."
  - truth: "Public confirmed terminal deletion and the last-portfolio replacement journey."
    addressed_in: "Phase14"
    evidence: "Roadmap Phase14 SC1/4 deliver deletion confirmation and zero-active overview/Create portfolio."
  - truth: "Full integrated create/rename/description/compare/switch/delete lifecycle acceptance and recovery."
    addressed_in: "Phase15"
    evidence: "Roadmap Phase15 SC1–4 qualify the complete strategy lifecycle; current revision-specific preservation/recovery/security obligations remain here."
---

# Phase12: Preserve Existing Investing Under Portfolio Ownership Verification Report

**Phase Goal:** Existing users can keep investing in their first named portfolio with their actual finances and History preserved, while financial requests and authority are explicitly bound to that portfolio.

**Verified:** 2026-11-17T18:50:00Z  
**Status:** gaps_found — one BLOCKER  
**Re-verification:** No — initial goal verification. The separate 12-LOCAL-VERIFICATION.md is campaign evidence, not an earlier goal report with structured gaps.

The implemented preservation slice satisfies all five functional roadmap criteria in isolated proof. Phase12 cannot close or advance to Phase13 because its mandatory current security qualification fails. Task counts, accepted UI, source review closure, historical audit success and passing separate diagnostics do not change that result.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Implementation and independent proof evidence |
|---|---|---|---|
| 1 | An existing user opens their first named portfolio with exactly the prior cash, stored starting-cash baseline, holdings, basis, fills, event History and retry identities; no migration grant or reset occurs. | VERIFIED | 0015 adds metadata/lineage;0016 associates seven owned tables by their unique original account in bounded NULL-only batches. It does not rewrite cash/baseline/fills/global split digests.0017 validates required compound ownership. accounts.get_or_create_user grants only after a genuinely new User insert; get_me cannot grant. Current migration/preservation suites and same-archive independent before/after economic projections pass. |
| 2 | The user sees the target portfolio name on tickets, confirmations, receipts and holding details, and can complete the existing crypto/stock preview, fill and original-receipt retry flows under unchanged execution rules; omitted, ambiguous or unavailable targets never select another portfolio. | VERIFIED | OwnedActivePortfolioDep verifies path ID+authenticated owner+active state. Both trade services recheck/lock the root; retry lookup remains user-global and compares original root and payload. Client validators reject mismatched identities. Boundary mounts financial children only for a ready target; pages/receipt/holding details carry its name. Actual full browser diagnostic and backend/frontend regressions pass; owner accepted the render-equivalent packet. |
| 3 | The user reads only the chosen portfolio's mixed paginated History and original-event details; identities, references and cursors cannot retrieve another portfolio's financial records. | VERIFIED | history.py trade2 and event_history.py mixed3 decode expected portfolio ID; queries and original hydration constrain user+root. Deterministic seek ends in unique source identity. Client cursor validation and owner/root/session hooks prevent old pages/detail publication. Actual scoped service/API/cursor/frontend/browser cases pass. |
| 4 | OTP sign-in, session refresh and sign-out work independently of zero, one or many financial portfolios in isolated fixtures; legacy financial requests cannot bypass explicit targeting or choose an ambiguous portfolio. | VERIFIED | get_me selects User.email alone; v2 identity is mounted in real create_app. v1 verify refuses before OTP consume; v1 financial handlers use authenticated409 portfolio_required and state-changing routes retain CSRF. Browser discovery distinguishes zero/one/many without financial fallback. Full current auth/session and route tests pass. |
| 5 | The same investing journeys work on fresh and populated upgraded databases through restricted verified-TLS roles, with original financial payloads, immutable evidence and matching ownership constraints preserved; ordinary roles cannot gain broader mutation rights. | VERIFIED | Actual0017 migration, narrow column grants, trigger/compound-FK authority and fixed routine fingerprints are wired to restricted bootstrap/admission. Full recovery runs fresh+upgraded TLS consumers, role denials, exact financial payloads and authority parity. Unsafe source/schema/intermediate states and broadened roles refuse. |
| 6 | Current0017 and retained recovery complete against one source-bound immutable archive with exact financial and authority parity. | VERIFIED | Current complete seven-stage recovery receipt exits0,2697.424s; same_archive_final_ci=true and retained0007–0014 proofs. Recomputed archive SHA94365aff…03eb; raw log/source receipt hashes match. Actual declared-runtime source-destroyed cold restore is included; a separate cold-first51.501s result also passes. |
| 7 | Owner UI and genuine native200% acceptance are explicit and apply to unchanged render inputs. | VERIFIED | HUMAN-UAT records separate “approved” and “Yes—native 200% passed”. Packet SHA c87cb4a3…d55f and all125render inputs remain unchanged. Broad inventory is245/249, with four backend authority/pin changes; no recapture or249/249claim is made. Browser name was not supplied and is not invented. |
| 8 | The current frozen source satisfies complete strict security qualification, including npm audit HIGH policy. | FAILED — BLOCKER | Complete current all-security exits1 after actual npm audit detects14HIGH/11moderate. Saved official advisory/registry refresh18:37:28Z has latest4.0.7, affected<=4.0.7 and first_patched_version=null. No override, waiver or patched candidate exists. |

**Score:** 7/8 consolidated must-haves verified; functional roadmap contract5/5. No UNCERTAIN truth or pending human decision remains.

### Scope and Disconfirmation

Three plausible failure paths were checked: (1) association silently grants/resets finances, (2) global retry keys or stale browser state cross roots, and (3) apparently wired recovery uses a workstation-only image or broadened restored authority. The concrete migrations, root/payload checks, guarded query state, declared-runtime factory and raw exact-recovery receipts disprove those failure hypotheses for the current preservation slice.

A real partial outcome remains: functional behavior is proven while mandatory security qualification is incomplete. The passing offline browser contracts use injected command results; they prove harness guards, not real browser investing. Actual browser evidence comes separately from the full60-collected run. Likewise, SDK schema-drift=false identified no supported ORM and is not schema-equivalence evidence; actual Alembic fresh/upgraded/model/catalogue/TLS proofs supply that evidence. Codebase-drift EPERM is nonblocking and supplies no correctness proof.

CR-01 was checked against actual integrated SQL: the no-dividend-obligation exception requires complete cutoff coverage, no target pre-cutoff trades/movements and matching previous quantity/basis, with coalesce(false) for incomplete evidence. It does not exempt splits, historical owners or held/revised authority. Its regression negatives explicitly observe final SQL authority and assert rollback rather than passing on an earlier refusal. CR-02's actual build_current_runtime uses a complete committed Git archive, verifies context before/after the declared Dockerfile runtime build, refuses dirty/changed source and binds/rechecks immutable image Config/RootFS. Current full backend/recovery receipts include the integrated repairs.

## Required Artifacts and Plan Truth Coverage

All28 PLAN frontmatters were parsed:56 truths,142 artifact references (131 unique existing paths),54 key-link declarations and112 plan threat rows. All28 SDK verify.artifacts calls return all_passed=true. Existence/SDK results alone are not the substantive or wiring verdict: the source/data-flow tables below and actual suites/receipts establish behavior. Tests are wired through the collected full backend/frontend/CI/browser suites; static SQL through0017 fixed checksum consumption; operational artifacts through declared runner stages; acceptance docs through immutable source/packet evidence.

Each pair below records the two exact plan truths in order. VERIFIED for Plan27's truthful-stop clause means the failure is faithfully preserved; it does **not** satisfy must-have8 or represent a successful audit.

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
| 12-27 | 1. All complete suites/audits/scans actually pass for same frozen source or execution stops with truthful failures; focused latency not falsely claimed.<br>2. Real current and retained isolated recovery proof passed for one exact source/archive, complete sanitized receipt and review packet ready; no production/provider work. | VERIFIED / VERIFIED | Truthful failed security stop is recorded, not called a pass; whole current seven-stage recovery and separate diagnostic have authenticated receipts. |
| 12-28 | 1. Owner explicitly accepts changed synthetic UI for recorded source; absence or ambiguous response is not approval.<br>2. Owner's genuine native200% pass recorded for same source, deferred/live and future-phase boundaries retained. | VERIFIED / VERIFIED | Explicit owner approved and separate Yes—native200%passed; unchanged125render inputs, immutable packet and documented245/249broad match. |

### Artifact Inventory

All paths below pass existence/substance checks and participate in the stated proof chain. Local qualification documentation is substantive and truthful, but its **successful-qualification outcome is FAILED**. No artifact is a substitute for that missing outcome.

| Plan | Required artifact paths | Level3 disposition |
|---|---|---|
| 12-01 | `backend/tests/portfolio_fixtures.py`<br>`backend/tests/test_portfolio_migrations.py`<br>`backend/tests/test_portfolio_ownership.py`<br>`backend/tests/test_portfolio_authority.py`<br>`backend/tests/conftest.py`<br>`backend/tests/test_migrations.py`<br>`backend/tests/test_stock_migrations.py` | WIRED; implementation/proof consumer mapped above |
| 12-02 | `backend/app/models/user.py`<br>`backend/tests/test_portfolio_ownership.py`<br>`backend/app/models/trade.py` | WIRED; implementation/proof consumer mapped above |
| 12-03 | `backend/app/models/stock_execution.py`<br>`backend/app/models/corporate_action.py`<br>`backend/tests/test_portfolio_ownership.py`<br>`backend/app/models/dividend.py`<br>`backend/tests/test_portfolio_authority.py` | WIRED; implementation/proof consumer mapped above |
| 12-04 | `backend/alembic/versions/0015_portfolio_expansion.py`<br>`backend/tests/test_portfolio_migrations.py`<br>`backend/alembic/versions/0016_portfolio_association.py` | WIRED; implementation/proof consumer mapped above |
| 12-05 | `backend/tests/test_portfolio_stock_authority.py`<br>`backend/alembic/sql/0017_stock_portfolio.sql` | WIRED; implementation/proof consumer mapped above |
| 12-06 | `backend/tests/test_portfolio_dividend_authority.py`<br>`backend/alembic/sql/0017_dividend_portfolio.sql` | WIRED; implementation/proof consumer mapped above |
| 12-07 | `backend/alembic/versions/0017_portfolio_ownership.py`<br>`backend/tests/test_portfolio_migrations.py`<br>`backend/app/db/schema_contract.py`<br>`backend/app/main.py`<br>`backend/tests/test_portfolio_schema_admission.py` | WIRED; implementation/proof consumer mapped above |
| 12-08 | `backend/app/core/deps.py`<br>`backend/app/schemas/auth.py`<br>`backend/app/schemas/portfolios.py`<br>`backend/tests/test_portfolio_ownership.py`<br>`backend/app/services/accounts.py`<br>`backend/app/services/auth.py`<br>`backend/tests/test_portfolio_identity.py` | WIRED; implementation/proof consumer mapped above |
| 12-09 | `backend/app/api/v2/auth.py`<br>`backend/app/api/v2/me.py`<br>`backend/app/api/v2/router.py`<br>`backend/tests/test_portfolio_identity_api.py`<br>`backend/app/api/v1/auth.py`<br>`backend/app/api/v1/me.py` | WIRED; implementation/proof consumer mapped above |
| 12-10 | `backend/app/services/trading.py`<br>`backend/app/services/trade_idempotency.py`<br>`backend/tests/test_portfolio_crypto.py`<br>`backend/app/api/v2/trades.py`<br>`backend/app/schemas/trades.py`<br>`backend/tests/test_portfolio_crypto_api.py` | WIRED; implementation/proof consumer mapped above |
| 12-11 | `backend/app/services/stock_trading.py`<br>`backend/tests/test_portfolio_stock_trading.py`<br>`backend/app/api/v2/stock_trades.py`<br>`backend/app/schemas/stock_trades.py`<br>`backend/tests/test_portfolio_stock_api.py` | WIRED; implementation/proof consumer mapped above |
| 12-12 | `backend/app/services/stock_ownership.py`<br>`backend/tests/test_portfolio_stock_ownership.py`<br>`backend/app/services/corporate_actions.py`<br>`backend/tests/test_portfolio_splits.py` | WIRED; implementation/proof consumer mapped above |
| 12-13 | `backend/app/services/corporate_actions.py`<br>`backend/tests/test_portfolio_entitlements.py`<br>`backend/app/services/dividends.py`<br>`backend/app/tasks/dividends.py`<br>`backend/tests/test_portfolio_dividends.py` | WIRED; implementation/proof consumer mapped above |
| 12-14 | `backend/app/services/portfolio.py`<br>`backend/app/schemas/portfolio.py`<br>`backend/tests/test_portfolio_valuation.py`<br>`backend/app/services/history.py`<br>`backend/app/services/event_history.py`<br>`backend/tests/test_portfolio_scoped_history.py` | WIRED; implementation/proof consumer mapped above |
| 12-15 | `backend/app/api/v2/portfolios.py`<br>`backend/app/api/v2/history.py`<br>`backend/tests/test_portfolio_routes.py`<br>`backend/app/api/v2/router.py`<br>`backend/app/api/v1/router.py`<br>`backend/app/main.py` | WIRED; implementation/proof consumer mapped above |
| 12-16 | `deploy/db/bootstrap-roles.sql`<br>`backend/app/db/dev_bootstrap.py`<br>`deploy/tests/test-dev-bootstrap.py`<br>`deploy/configure-db.sh`<br>`deploy/deploy.sh`<br>`deploy/tests/test-portfolio-migration-runner.py` | WIRED; implementation/proof consumer mapped above |
| 12-17 | `deploy/backup-snapshot.py`<br>`deploy/backup-manifest.sql`<br>`deploy/tests/test-portfolio-recovery-contracts.py`<br>`deploy/verify-restore.py`<br>`deploy/restore-check.sh`<br>`deploy/backup.sh` | WIRED; implementation/proof consumer mapped above |
| 12-18 | `deploy/tests/portfolio-execution-fixture.py`<br>`deploy/tests/ops-fixtures.py`<br>`deploy/tests/selected-cutover.py`<br>`deploy/tests/test-ci-ops.py`<br>`deploy/tests/test-portfolio-fixture-contracts.py`<br>`deploy/tests/portfolio-retained-sources.json` | WIRED; implementation/proof consumer mapped above |
| 12-19 | `frontend/src/api/auth.ts`<br>`frontend/src/hooks/useMe.ts`<br>`frontend/src/api/auth.test.ts`<br>`frontend/src/api/portfolios.ts`<br>`frontend/src/hooks/usePortfolioTarget.ts`<br>`frontend/src/hooks/usePortfolioTarget.test.tsx` | WIRED; implementation/proof consumer mapped above |
| 12-20 | `frontend/src/api/trades.ts`<br>`frontend/src/api/stockTrades.ts`<br>`frontend/src/api/portfolioTrades.test.ts`<br>`frontend/src/api/portfolio.ts`<br>`frontend/src/api/history.ts`<br>`frontend/src/api/eventHistory.ts`<br>`frontend/src/api/portfolioReads.test.ts` | WIRED; implementation/proof consumer mapped above |
| 12-21 | `frontend/src/hooks/useQuote.ts`<br>`frontend/src/hooks/useHolding.ts`<br>`frontend/src/hooks/useTrade.ts`<br>`frontend/src/hooks/portfolioCrypto.test.tsx`<br>`frontend/src/hooks/useStockTrade.ts`<br>`frontend/src/hooks/portfolioStock.test.tsx` | WIRED; implementation/proof consumer mapped above |
| 12-22 | `frontend/src/hooks/usePortfolio.ts`<br>`frontend/src/hooks/portfolioValuation.test.tsx`<br>`frontend/src/hooks/useHistory.ts`<br>`frontend/src/hooks/useEventHistory.ts`<br>`frontend/src/hooks/portfolioHistory.test.tsx` | WIRED; implementation/proof consumer mapped above |
| 12-23 | `frontend/src/components/PortfolioContext.tsx`<br>`frontend/src/components/PortfolioTargetBoundary.tsx`<br>`frontend/src/components/PortfolioTargetBoundary.test.tsx`<br>`frontend/src/App.tsx`<br>`frontend/src/pages/AccountPage.tsx`<br>`frontend/src/App.test.tsx` | WIRED; implementation/proof consumer mapped above |
| 12-24 | `frontend/src/pages/TradePage.tsx`<br>`frontend/src/pages/TradePage.test.tsx`<br>`frontend/src/pages/StockTradePage.tsx`<br>`frontend/src/components/StockTradeReceipt.tsx`<br>`frontend/src/pages/StockTradePage.test.tsx` | WIRED; implementation/proof consumer mapped above |
| 12-25 | `frontend/src/pages/PortfolioPage.tsx`<br>`frontend/src/components/PortfolioHoldings.tsx`<br>`frontend/src/pages/PortfolioPage.test.tsx`<br>`frontend/src/pages/HistoryPage.tsx`<br>`frontend/src/components/HistoryEventDetails.tsx`<br>`frontend/src/pages/HistoryPage.test.tsx` | WIRED; implementation/proof consumer mapped above |
| 12-26 | `frontend/e2e/portfolio-ownership.spec.ts`<br>`deploy/tests/run-stock-browser.py`<br>`deploy/tests/test-portfolio-browser-contracts.py`<br>`.github/workflows/ci.yml`<br>`deploy/tests/test-ci-ops.py`<br>`deploy/recovery-bundle.sh`<br>`deploy/tests/run-portfolio-validation.py` | WIRED; implementation/proof consumer mapped above |
| 12-27 | `.planning/phases/12-preserve-existing-investing-under-portfolio-ownership/12-LOCAL-VERIFICATION.md`<br>`.planning/phases/12-preserve-existing-investing-under-portfolio-ownership/12-RECOVERY-PROOF.md`<br>`.planning/phases/12-preserve-existing-investing-under-portfolio-ownership/12-HUMAN-UAT.md` | WIRED evidence; security acceptance BLOCKED |
| 12-28 | `.planning/phases/12-preserve-existing-investing-under-portfolio-ownership/12-HUMAN-UAT.md` | WIRED; implementation/proof consumer mapped above |

## Key Link Verification

SDK verify.key-links was run for all28 plans. Its “Target not referenced in source” filename heuristic cannot resolve Python dotted imports, SQL foreign-key references, reverse fixture consumption, cross-layer HTTP URLs or manually recorded evidence links. Those are not accepted as missing implementation without checking the actual mechanism. The following semantic chains cover all54 declared links, including the duplicate Plan01 fixture declaration.

| Plans | From → To | Actual mechanism | Result |
|---|---|---|---|
| 01 | Authenticated fixtures → migrations/authority tests | conftest restricted migration connection and run_test_migration; independent snapshots imported by test consumers | WIRED |
| 02–03 | Models → account/trade/event lineage | Compound ForeignKeyConstraint/unique tuples, not Python source filename strings; actual0017 validates matching SQL | WIRED |
| 04 | 0016 →0015 | down_revision=0015, authenticated finite NULL association guard and batch/resume negatives | WIRED |
| 05–07 | 0017 → static SQL; main → schema_contract | Fixed companion names/SHA pins consumed by upgrade; startup calls final schema admission | WIRED |
| 08–09 | deps/auth → resolver/accounts/session | OwnedActivePortfolio dependency and identity-only get_me; before-consume legacy refusal with actual v2 verification | WIRED |
| 10–11 | v2 trades → services → retry/journal | Required verified portfolio argument, global key lookup/root equality, instrument then root locks and append/final authority | WIRED |
| 12–13 | Actions/workers → journal/entitlement → SQL | Persisted digest/closure interpretation; active-root discovery and bound cause-derived financial routines | WIRED |
| 14–15 | Scoped readers/real application → database services | Actual v2 router registration; root baseline query; private mixed union/original hydration and bound seek cursor | WIRED |
| 16 | Configure/dev startup → final migrator/grants | Fixed runtime inventory and source-pinned authenticated path; actual restricted fresh/upgraded TLS | WIRED |
| 17–18 | Producer/consumer → manifest/projections/source dispatcher | Fixed source catalogue, archive manifest, exact rows/units, retained source loader and declared current runtime | WIRED |
| 19–20 | Browser identity/financial clients → v2 API | v2 email-only identity, owned metadata; explicit encoded root URL plus response/cursor identity checks | WIRED |
| 21–22 | Trade/read hooks → strict clients | Captured owner/root/session query keys, hidden guards, original attempts, same-root page/detail publication | WIRED |
| 23–25 | App/boundary/pages → target/hooks/details | Scoped routes enter verified Outlet; current target passed to hooks/receipts/original details; unavailable states remove children | WIRED |
| 26 | Browser/CI → real journeys/validation | Runner selects ownership spec; CI invokes strict full graph including audit and serial recovery | WIRED |
| 27–28 | Runner receipts → proof/UAT documents | Exact source/archive/packet hashes and explicit owner responses, with current security failure retained | WIRED; successful security qualification FAILED |

## Data-Flow Trace (Level4)

| Rendered artifact/data | Source chain | Real data and boundary | Status |
|---|---|---|---|
| PortfolioPage cash/baseline/value/holdings | Account/Holding/marks → get_portfolio → v2 portfolios → fetchPortfolio → usePortfolio(target) → page/PortfolioHoldings | Actual owner+active-root query joins holdings by portfolio; calculate_portfolio receives stored starting_cash, not a fixed new baseline. Response validates root/name/monetary strings; hook only exposes current owner/root/session cache. | FLOWING |
| Crypto ticket/preview/receipt | Account/Holding/Trade/prices → trading quote/execute → v2 trades → strict trades client → useQuote/useHolding/useTrade → TradePage | Decimal transaction locks selected account; fills persist root and original key/payload. Page freezes original attempt and names target; late callbacks cannot publish into another root. | FLOWING |
| Stock ticket/context/receipt | Instrument/quote/session/action authority + owned cash/holding → stock_trading + journal + final SQL → v2 stock_trades → strict client/useStockTrade → StockTradePage/StockTradeReceipt | Bid/ask/freshness/permission checks retained; matching root facts/movement and final cash/holding state required. Original root/key/payload preserved during unknown-result recovery. | FLOWING |
| Mixed History and original detail | Owned Trade/Fill/Movement/Payment/Decision → event_history union/original joins → v2 event-history → strict client → useEventHistory(target) → HistoryPage/HistoryEventDetails | Real deterministic root-filtered query and embedded original hydration; cursor carries expected root. Seen sets, pages, details and focus lifetime are scoped; no empty hardcoded child props replace finance. | FLOWING |
| Trade History continuation | Owned Trade → history.list_history → v2 history → strict history client/useHistory | Owner/root predicates and trade2 cursor checked before query; final active-root recheck; continuation publication remains target/session bound. | FLOWING |
| Target label and identity-only Account | User → v2 me; owned active Account IDs/names → metadata API → usePortfolioTarget → boundary/PortfolioContext/pages | Metadata query is real, bounded by supported owned roots and stable ID ordering. Empty/many responses are legitimate states; sole legacy discovery navigates before finance. Account does not synthesize zero cash. | FLOWING |

## Behavioral Spot-Checks

These were independently invoked by this verifier from repository root. They are offline contract checks with injected/fake command runners; no service, database, provider or production operation was started.

| Behavior | Command | Result | Status |
|---|---|---|---|
| Browser harness safety, cleanup and packet contracts | python3 deploy/tests/test-portfolio-browser-contracts.py |6tests,0.241s, exit0 | PASS |
| Exact recovery producer/consumer mutation contracts | python3 deploy/tests/test-portfolio-recovery-contracts.py |10tests,0.576s, equality/invariants/identities=true, exit0 | PASS |
| CI graph, source/image provenance and CR-02 refusal contracts | python3 deploy/tests/test-ci-ops.py |37tests,7.835s, exit0; expected injected failure cases asserted | PASS |

### Probe Execution

No explicit probe-*.sh path occurs in the phase PLAN declarations, and no conventional scripts probe shell path was discovered. No production/default-config helper was invoked. The phase's declared actual runnable qualification commands are recorded below; their original process receipts were inspected and hashed, not rerun or replaced by summaries.

## Current Raw Qualification Evidence

Tested source is d9da271b2b21f48f965dd54898a6bb8afcc9088e. Current HEAD1945adb is documentation-only afterward: git diff d9da271 HEAD -- backend frontend deploy DockerCompose .github is empty. The raw four source/result receipts record unchanged HEAD and zero changed tracked files during their own commands. This verifier recomputed every raw log SHA and source-receipt SHA and all match the corresponding result JSON.

| Actual campaign | Source-bound command/evidence | Result | Status |
|---|---|---|---|
| Cold-first | /tmp/phase12-reviewfix-cold-d9da271.{log,source.json,result.json}; declared-runtime cold lane |51.501s, exit0; source destroyed, separate PostgreSQL/quarantine/TLS | PASS |
| Complete security | python3 deploy/tests/run-portfolio-validation.py --suite all-security; /tmp/phase12-reviewfix-security-d9da271.* |993.346s, exit1 at npm audit. Backend3114PASS, exact60critical modules100% (5020statements/1604branches), overall99.85%; Python audit clean; frontend958PASS/lint/types/format/build passed before failure. | FAILED — BLOCKER |
| Complete recovery | python3 deploy/tests/run-portfolio-validation.py --suite recovery; /tmp/phase12-reviewfix-recovery-d9da271.* |2697.424s, exit0, all7stages; final same_archive_final_ci=true | PASS |
| Separate remaining diagnostic | /tmp/phase12-reviewfix-remaining-d9da271.*; unchanged commands unreached by failed security prefix |594.239s, exit0; whole_security_pass=false. Full60browser collected,59PASS/1original deployed-CSPskip,505.9s;3declared builds/pinned pulls, smoke5/5 and5immutable strict image scans0HIGH/CRITICAL. | PASS diagnostic; not whole-security PASS |

The full current backend/frontend and browser results cover retained earlier auth/trading/stock/action/dividend/History families, satisfying the regression check without another full-suite run. The original deployed-CSP skip is disclosed; local proof is not deployed-CSP acceptance or Phase7 live stock approval.

| Receipt | Independently matched raw log SHA256 |
|---|---|
| cold | ccdc57e5945c19ca9438659b8c7aad69614c243f40f406ffde4480043ad85154 |
| security | 2c7e4bc2416dfe5e8b5483fc06781cdec1c11b2bdc44d0d3d65cefc25aad9be4 |
| recovery | bb0d57233c55da8517da95ebd8f9647ae31860f76f1d65c086bacfe3a8c774bb |
| remaining | ddb3c1ac30a754158a7a55a22e730605e03557dc0cf221db9deef720504e663b |

All four result receipts report zero containers/networks/volumes across all six exact owned projects. No pipeline was started by this verifier.

### Exact Recovery Provenance

One fresh archive /tmp/birja-phase12-proof/recovery.tar.gz is196689920bytes. Its independently recomputed SHA256 is **94365aff1bbf8558bcc1481a19c10afea8c571801d54cf3ae3b79156f4af03eb**. Whole recovery covers image transition, retained0007–0014 encrypted roundtrips, current0017 declared-runtime cold restore, restricted roles, upgraded TLS, fresh TLS and selected rollback/refusal. Current/retained/source/image/CORE/unit guards and fresh/upgraded authority parity are enforced between stages. The old archive/proof is retained separately; current evidence does not relabel an older run.

### Dependency Qualification Gap

Raw /tmp/phase12-reviewfix-npm-audit-d9da271.json reports25findings:14HIGH/11moderate. The single new picomatch advisory propagates through14HIGH package entries; these are not14independent direct vulnerabilities. Current lock entries are4.0.7 and nested2.3.2. The saved official final refresh at2026-11-17T18:37:28.517088Z still reports affected<=4.0.7, latest4.0.7 and no patched version.

Primary evidence: [GitHub reviewed advisory](https://github.com/advisories/GHSA-fc5q-39xc-vjpf) and [official registry metadata](https://registry.npmjs.org/picomatch), captured and hashed in12-DEPENDENCY-REVIEW.md. No fresh network lookup or audit loop was performed. Final saved advisory SHA cc99706e61047047b6690db94abb98b5940d007196775c12902c0f79d8aedbd5; registry SHA9a8e64f1208fef4d18c27f48267e00c639b65743484cf3f5e788d018195b6fbb. Audit JSON SHA471ad05e25c3ac71efd8a0fc04e0eb7b5e0f201b2f80720d232cc7101daa6fa1.

The historical whole-security run finished15:56:18Z; advisory metadata updated15:56:44Z. Historical success cannot establish current gate success. The exposure is in the build/test/tooling dependency graph; public-request exploitability is not inferred, and does not waive the owner’s strict HIGH policy. The suggested semver-major Vitest downgrade is not evidence of a patched picomatch. No package installation, force fix, downgrade, override or waiver is authorized or applied. There is no concrete patched candidate to approve; retain the gate.

## Requirements Coverage

All plans declare only the exact seven primary Phase12 IDs. REQUIREMENTS.md assigns the same seven to Phase12, so there are no orphaned Phase12 IDs. All remain unchecked: local functional verification does not close a requirement while the mandatory phase qualification is blocked.

| Requirement | Source plans | Local implementation status | Closure status/evidence |
|---|---|---|---|
| PFUND-03 — preserve original finances/no migration grant |01–04,06–08,12–14,16–18,26–27 | VERIFIED | BLOCKED closure by common qualification gap; migration economics, no-regrant onboarding, exact same-archive recovery verified. |
| PFIN-02 — explicit active crypto/stock execution, unchanged rules |05,08,10–12,15,20–21,26–27 | VERIFIED | BLOCKED closure; resolver, transactions, final SQL, scoped clients/hooks and actual browser execution verified. |
| PFIN-03 — original-root/payload uncertain retry, once-only fill |01,05,10–11,20–21,24,26–27 | VERIFIED | BLOCKED closure; global retry conflict, immutable active-root replay and unavailable-root refusal verified. |
| PCTX-01 — visible portfolio name on financial surfaces |09,14–15,19,22–28 | VERIFIED | BLOCKED closure; source-rendered names, strict root clients, accepted UI/native200% verified. |
| PVIEW-03 — private root History/originals/cursors |14–15,20,22,25–28 | VERIFIED | BLOCKED closure; complete scoped union/seek/original detail and cache isolation verified. |
| PSAFE-02 — zero/one/many identity/session and legacy refusal |07–09,15,19,22–23,26–28 | VERIFIED | BLOCKED closure; identity-only auth, OTP preservation, session lifecycle and explicit route composition verified. |
| PSAFE-03 — restricted TLS, immutable evidence, exact migration ownership |01–07,11–13,16–18,26–27 | VERIFIED | BLOCKED closure; actual fresh/upgraded TLS, restricted SQL/role denial, immutable catalogue/projection parity and current recovery verified. |

## Anti-Patterns and Threat Coverage

The232 canonical reviewed paths were checked for unreferenced TBD/FIXME/XXX debt markers; none were found. The131 required unique artifacts also have no such unreferenced marker. Empty metadata/no-portfolio states, signed-out boundary return null, initial query state and injected negative contract failures are intentional and do not form hollow financial rendering. Actual database→API→client→hook→page chains are traced above.

| Finding | Severity | Impact |
|---|---|---|
| Current npm audit HIGH finding in exact locked tooling graph | BLOCKER | Mandatory qualification fails; phase must not advance. |
| Existing1deployed-CSP browser skip and disclosed backend warnings/moderate advisories | Info | No new skip or weakened gate; not evidence of live/deployed acceptance. |
| SDK key-link filename heuristic false-negatives | Info | Resolved by actual semantic calls, SQL constraints and receipts, not by assuming existence means wiring. |

The112 authored threat entries and baseline/targeted security reports were considered by boundary: authenticated owned root, immutable financial causes, active/terminal journal semantics, limited SQL authority, stale browser state, exact source/image/archive admission and supply-chain gates. Source control closure in12-SECURITY.md and the11targeted CR rechecks does not erase the newly failed supply-chain qualification. No current security HIGH obligation is deferred to Phase15 and no new risk acceptance is invented.

## Human Verification Required

None pending. Both explicit Plan28 checks are accepted in12-HUMAN-UAT.md. The two human-check blocks are those existing owner UI/native200% checks, not additional tasks.

The immutable combined packet has SHA c87cb4a3eb3feb52c42a37aa60ff69cce66d2ac8e2637847e6a977af1714d55f. All125frontend/capture inputs are unchanged;245/249broad hashes match, and the four backend SQL/migration/bootstrap pin changes are disclosed. Render equivalence preserves owner acceptance without claiming a new capture, changing capture-time native200=false metadata, or fabricating a browser name. Human acceptance is separately recorded true in UAT.

## Deferred Items

| Item | Owner | Specific roadmap evidence |
|---|---|---|
| Public additional funded creation, name/rename, optional descriptions, overview comparison | Phase13 | SC1–4 create/manage funded strategies and compare a stable overview. |
| Public terminal deletion/confirmation and last-portfolio replacement | Phase14 | SC1/4 user deletion and zero-active overview/Create action. Existing terminal safety fixtures remain required here and pass. |
| Complete integrated management/deletion lifecycle recovery/acceptance | Phase15 | SC1–4 qualify the full create/rename/description/compare/switch/delete lifecycle. Current revision recovery and strict qualification are not deferred. |
| STOCK-01/02/03, DATA-01, MKT-01, SAFE-01 live stock acceptance | Separately deferred Phase7 campaign | Existing November16 manual campaign is CONSUMED. No activation/provider/network operation or repeat is part of this verification. |

## Gaps Summary

One shared external dependency qualification gap blocks closure. Functional ownership/preservation, current/retained exact recovery, source code/security/UI repair checks and both owner checks are supported by code and raw receipts. The current complete security process nonetheless fails the retained strict HIGH policy. Separate later browser/build/smoke/image passes are diagnostic evidence only.

Keep Phase12 and all seven primary requirement closures pending; Phase13 must not start. A legitimate published patched artifact and separately authorized exact repair followed by complete strict qualification are required. No patched candidate exists in the saved final official evidence, so another unchanged audit loop or fabricated candidate/approval would not resolve the gap.

This verifier wrote only this report, made no source changes or commits, and did not mutate SDK state, requirement checkboxes, phase completion, services, dependencies, providers or production.

---

_Verified: 2026-11-17T18:50:00Z_  
_Verifier: independent gsd-verifier agent_

