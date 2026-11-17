---
phase: 12
slug: preserve-existing-investing-under-portfolio-ownership
status: verified
register_authored_at_plan_time: true
threats_total: 112
threats_closed: 112
threats_open: 0
mitigations_verified: 58
plan_scoped_acceptances: 54
transfers: 0
unregistered_flags: 0
asvs_level: 1
created: 2026-11-17
reviewed_source: d3c603e5a6584d6bba76c16a59496be0b6f4e6d2
qualified_security_source: 1f8d5a4eb500dad879440c2f2ebba892b8b5f65c
qualified_recovery_source: 10121b02db2b2217b868a9bce30c3f77504eadb3
---

# Phase 12 — Declared Threat Mitigation Verification

All **112 plan-authored threats** are accounted for: **58 implemented
mitigations verified, 54 original scoped acceptances documented, zero open**.
This is a declared-mitigation audit, not a new penetration test, complete ASVS
certification, hosted-CI result, release approval or production activation.

Implementation was read-only. This auditor created only this report and did
not run a database test, start a service, read private configuration, install
a dependency, change admissions or commit files. Separate code/UI reviews and
goal verification remain independent gates; this report does not assert that
all functional defects have been ruled out. If the corresponding implementation
changes after this source, recheck affected threat evidence before final sign-off.

## Trust Boundaries

| Boundary | Actual control | Data crossing |
|---|---|---|
| Browser identity to explicit financial root | CurrentUser plus owned active Account resolver; finite path IDs; same404 for unavailable roots | Session identity, root IDs |
| Root to immutable financial causes | Paired composite FKs, root locks, final SQL authority and user-global retry matching | Cash, quantity, basis, fills and original receipts |
| Scheduler/operator to financial state | Private fixed-path routines, narrow roles/columns, exact body/declaration/ACL preflight | Stock effects, dividends/corrections, unit journals |
| Administrative migration to runnable application | Actual authenticated migrator, finite association exception, source pins and staged-runtime refusal | Legacy immutable payloads and final0017 authority |
| Owner/session/root to cached UI | Captured target epochs, scoped queries/hidden guards and unavailable-child masking | Quotes, holdings, cursors, originals and unresolved attempts |
| Archive/retained code/image to restored clone | Exact inventories, pinned complete sources, immutable image bindings and fixed quarantine grants | Encrypted payloads, schema, sequences and restored economics |
| Synthetic proof to human acceptance | Source-bound packet and two distinct explicit owner responses | Named surfaces, zero/many states, native browser zoom |

Per-user authorization is enforced at authenticated HTTP/service entrypoints;
the application database role is not a per-user PostgreSQL RLS identity.
Frontend ownership guards supplement, and never replace, the server resolver.

## Audit Method and Evidence Limits

All28 PLAN threat blocks were parsed, including every mitigate/accept row.
The six explicit SUMMARY threat flags were mapped individually below.
For mitigations, actual code paths, predicates, transaction/lock order, SQL
declarations/grants, restore admission and client publication guards were
inspected. Finding a test name alone was not treated as implementation.

The final existing complete security receipt was read directly:
`/tmp/phase12-27-security-finish-second.result.json` records exit0,
1541.269seconds, no changed source, all five owned projects cleaned, and the
unchanged qualified archive. It corresponds to3108 backend cases, all60
critical modules100%,958 frontend cases,59 browser cases plus the original
deployed-CSP skip, and five strict scans with zero HIGH/CRITICAL. The full
recovery log ends with `same_archive_final_ci=true`, exit0 in2708.086seconds
and no source drift. These results were inspected, not rerun by this auditor.

The recovery archive remains
`5a495a9dc2901cac46bfa82f23ae2daef67323eda05ac08dc44c67272a2b01a4`.
Its original10121b0 qualification is not relabelled as a later HEAD run.
The existing final source-equivalence receipt documents the one unused backend
test-module difference in the broad306-path inventory; packaged CORE/UNITS/
portfolio payload, runtime/migrations/SQL and actual recovery imports remain
unchanged. See12-RECOVERY-PROOF.md and12-LOCAL-VERIFICATION.md.

The fourteen npm MODERATE findings and existing deployed-CSP skip remain
disclosed. The unchanged HIGH/CRITICAL policy was not weakened. No claim of
zero npm findings or deployed CSP verification follows from this audit.
The six deferred Phase7 requirements and consumed manual campaign remain
separate, with stock admissions OFF; no provider/production result is inferred.

## Threat Register

Every row below retains the plan's disposition. CLOSED for an acceptance
means its original scoped rationale is explicitly logged below, not that a
new risk has been silently accepted. Plan links preserve the original complete
mitigation text; evidence anchors point to actual current implementation.

| Threat ID | Category | Component | Disposition | Verification evidence | Status |
|---|---|---|---|---|---|
| T-12-01-01 | Tampering / Information disclosure / Elevation of privilege | `backend/tests/portfolio_fixtures.py` | mitigate | `backend/tests/test_migrations.py:101` rejects alternate test admin/DSN through `ensure_test_stack`; `:119` creates a child-only migrator environment with bounded execution/redaction. `backend/tests/portfolio_fixtures.py:39` checks the actual disposable database/session before destructive reset. [Plan](12-01-PLAN.md:123) | CLOSED |
| T-12-01-02 | Tampering / Information disclosure / Elevation of privilege | `backend/tests/test_portfolio_ownership.py` | mitigate | `backend/tests/portfolio_fixtures.py:106` independently seeds two unequal original books and one global split; `backend/tests/test_portfolio_authority.py:136` and `:239` assert cross-root supersession and closed-root write refusal. [Plan](12-01-PLAN.md:124) | CLOSED |
| T-12-01-03 | Spoofing / Denial of service | `Out-of-scope new mechanism` | accept | Original scoped acceptance AR-T-12-01-03 below; no new acceptance or mitigation waiver. [Plan](12-01-PLAN.md:125) | CLOSED |
| T-12-01-SC | Tampering | `No package boundary created` | accept | Original scoped acceptance AR-T-12-01-SC below; no new acceptance or mitigation waiver. [Plan](12-01-PLAN.md:126) | CLOSED |
| T-12-02-01 | Tampering / Information disclosure / Elevation of privilege | `backend/app/models/user.py` | mitigate | `backend/app/models/user.py:37` pairs Account identity/owner, retains NUMERIC cash/baseline and aware closure metadata; `backend/alembic/versions/0017_portfolio_ownership.py:36` installs the actual required constraints. [Plan](12-02-PLAN.md:102) | CLOSED |
| T-12-02-02 | Tampering / Information disclosure / Elevation of privilege | `backend/app/models/trade.py` | mitigate | `backend/app/models/trade.py:30` binds holdings to root+owner; `:58` pairs trade causes and `:68` keeps user-global idempotency uniqueness. Runtime replay compares portfolio+payload in `backend/app/services/trade_idempotency.py:23`. [Plan](12-02-PLAN.md:103) | CLOSED |
| T-12-02-03 | Spoofing / Denial of service | `Out-of-scope new mechanism` | accept | Original scoped acceptance AR-T-12-02-03 below; no new acceptance or mitigation waiver. [Plan](12-02-PLAN.md:104) | CLOSED |
| T-12-02-SC | Tampering | `No package boundary created` | accept | Original scoped acceptance AR-T-12-02-SC below; no new acceptance or mitigation waiver. [Plan](12-02-PLAN.md:105) | CLOSED |
| T-12-03-01 | Tampering / Information disclosure / Elevation of privilege | `backend/app/models/stock_execution.py` | mitigate | `backend/app/models/stock_execution.py:30` pairs facts to trade/root/coin/owner; `backend/app/models/corporate_action.py:291` pairs owned movements and `:482` pairs terminal closures without adding ownership to the global split application. [Plan](12-03-PLAN.md:110) | CLOSED |
| T-12-03-02 | Tampering / Information disclosure / Elevation of privilege | `backend/app/models/dividend.py` | mitigate | `backend/app/models/dividend.py:41` enforces event+portfolio once-only payment and `:71` binds entitlement identity; same-root supersession is explicit in `backend/app/models/corporate_action.py:416`, decision causes in `dividend.py:146`. [Plan](12-03-PLAN.md:111) | CLOSED |
| T-12-03-03 | Spoofing / Denial of service | `Out-of-scope new mechanism` | accept | Original scoped acceptance AR-T-12-03-03 below; no new acceptance or mitigation waiver. [Plan](12-03-PLAN.md:112) | CLOSED |
| T-12-03-SC | Tampering | `No package boundary created` | accept | Original scoped acceptance AR-T-12-03-SC below; no new acceptance or mitigation waiver. [Plan](12-03-PLAN.md:113) | CLOSED |
| T-12-04-01 | Tampering / Information disclosure / Elevation of privilege | `backend/alembic/versions/0015_portfolio_expansion.py` | mitigate | `backend/alembic/versions/0015_portfolio_expansion.py:31` permits association only for actual session_user birja_migrator, one original account, NULL old association and byte-equal remaining JSON; all other immutable mutations raise. [Plan](12-04-PLAN.md:103) | CLOSED |
| T-12-04-02 | Tampering / Information disclosure / Elevation of privilege | `backend/alembic/versions/0016_portfolio_association.py` | mitigate | `backend/alembic/versions/0016_portfolio_association.py:30` rejects missing/ambiguous/contradictory causes before batches; `:64` commits bounded 500-row batches and checks completion; `:101` refuses downgrade before writes. [Plan](12-04-PLAN.md:104) | CLOSED |
| T-12-04-03 | Spoofing / Denial of service | `Out-of-scope new mechanism` | accept | Original scoped acceptance AR-T-12-04-03 below; no new acceptance or mitigation waiver. [Plan](12-04-PLAN.md:105) | CLOSED |
| T-12-04-SC | Tampering | `No package boundary created` | accept | Original scoped acceptance AR-T-12-04-SC below; no new acceptance or mitigation waiver. [Plan](12-04-PLAN.md:106) | CLOSED |
| T-12-05-01 | Tampering / Information disclosure / Elevation of privilege | `backend/tests/test_portfolio_stock_authority.py` | mitigate | `backend/tests/test_portfolio_stock_authority.py:256`, `:276`, `:325`, `:338` and `:492` directly test forged causes, inactive/foreign roots, global retry conflicts, immutable payloads and scheduler execution denial. [Plan](12-05-PLAN.md:102) | CLOSED |
| T-12-05-02 | Tampering / Information disclosure / Elevation of privilege | `backend/alembic/sql/0017_stock_portfolio.sql` | mitigate | `backend/alembic/sql/0017_stock_portfolio.sql:8`, `:81` and `:258` install fixed-path invoker guards and private/granted signatures. Final authority explicitly compares root/facts/movement at `:143`; schema startup and bootstrap authenticate these routines. [Plan](12-05-PLAN.md:103) | CLOSED |
| T-12-05-03 | Spoofing / Denial of service | `Out-of-scope new mechanism` | accept | Original scoped acceptance AR-T-12-05-03 below; no new acceptance or mitigation waiver. [Plan](12-05-PLAN.md:104) | CLOSED |
| T-12-05-SC | Tampering | `No package boundary created` | accept | Original scoped acceptance AR-T-12-05-SC below; no new acceptance or mitigation waiver. [Plan](12-05-PLAN.md:105) | CLOSED |
| T-12-06-01 | Tampering / Information disclosure / Elevation of privilege | `backend/tests/test_portfolio_dividend_authority.py` | mitigate | `backend/tests/test_portfolio_dividend_authority.py:321`, `:334`, `:354`, `:434` and `:441` assert cross-root, closed unpaid/correction, append-only and private-validator/cash denials under actual roles. [Plan](12-06-PLAN.md:101) | CLOSED |
| T-12-06-02 | Tampering / Information disclosure / Elevation of privilege | `backend/alembic/sql/0017_dividend_portfolio.sql` | mitigate | `backend/alembic/sql/0017_dividend_portfolio.sql:279` derives root from entitlement, takes the instrument gate then active root lock, and scopes original/correction chains to that root; `:444` revokes PUBLIC/private authority and grants only bounded scheduler entrypoints. [Plan](12-06-PLAN.md:102) | CLOSED |
| T-12-06-03 | Spoofing / Denial of service | `Out-of-scope new mechanism` | accept | Original scoped acceptance AR-T-12-06-03 below; no new acceptance or mitigation waiver. [Plan](12-06-PLAN.md:103) | CLOSED |
| T-12-06-SC | Tampering | `No package boundary created` | accept | Original scoped acceptance AR-T-12-06-SC below; no new acceptance or mitigation waiver. [Plan](12-06-PLAN.md:104) | CLOSED |
| T-12-07-01 | Tampering / Information disclosure / Elevation of privilege | `backend/alembic/versions/0017_portfolio_ownership.py` | mitigate | `backend/alembic/versions/0017_portfolio_ownership.py:36` validates root lineage, makes seven owned roots NOT NULL, installs compound causes/immutability and drops the finite association helper. `:79` serializes active writes through the actual locked root; `:515` refuses unsafe downgrade. [Plan](12-07-PLAN.md:111) | CLOSED |
| T-12-07-02 | Tampering / Information disclosure / Elevation of privilege | `backend/app/db/schema_contract.py` | mitigate | `backend/app/db/schema_contract.py:24` accepts only the finite consumer/revision contract, refuses staged0015/16 and malformed/multiple revision state. Actual application startup and health call it at `backend/app/main.py:44` and `:86`. [Plan](12-07-PLAN.md:112) | CLOSED |
| T-12-07-03 | Spoofing / Denial of service | `Out-of-scope new mechanism` | accept | Original scoped acceptance AR-T-12-07-03 below; no new acceptance or mitigation waiver. [Plan](12-07-PLAN.md:113) | CLOSED |
| T-12-07-SC | Tampering | `No package boundary created` | accept | Original scoped acceptance AR-T-12-07-SC below; no new acceptance or mitigation waiver. [Plan](12-07-PLAN.md:114) | CLOSED |
| T-12-08-01 | Tampering / Information disclosure / Elevation of privilege | `backend/app/core/deps.py` | mitigate | `backend/app/core/deps.py:121` combines authenticated CurrentUser with bounded explicit path ID; `backend/app/services/portfolios.py:19` predicates id+user+closed_at and gives the same portfolio_unavailable404 for absent/foreign/closed. [Plan](12-08-PLAN.md:115) | CLOSED |
| T-12-08-02 | Tampering / Information disclosure / Elevation of privilege | `backend/app/services/accounts.py` | mitigate | `backend/app/services/accounts.py:13` grants only the successful new User insert; conflict returns the existing identity without creating a root. `:39` reads identity from User alone, independent of root count. [Plan](12-08-PLAN.md:116) | CLOSED |
| T-12-08-03 | Spoofing / Denial of service | `Out-of-scope new mechanism` | accept | Original scoped acceptance AR-T-12-08-03 below; no new acceptance or mitigation waiver. [Plan](12-08-PLAN.md:117) | CLOSED |
| T-12-08-SC | Tampering | `No package boundary created` | accept | Original scoped acceptance AR-T-12-08-SC below; no new acceptance or mitigation waiver. [Plan](12-08-PLAN.md:118) | CLOSED |
| T-12-09-01 | Tampering / Information disclosure / Elevation of privilege | `backend/app/api/v2/auth.py` | mitigate | `backend/app/api/v2/auth.py:16` uses the existing CSRF/OTP/rate-limit/session services and cookie setter with strict IdentityOut; `backend/app/core/deps.py:46` performs constant-time CSRF comparison. [Plan](12-09-PLAN.md:113) | CLOSED |
| T-12-09-02 | Tampering / Information disclosure / Elevation of privilege | `backend/app/api/v1/auth.py` | mitigate | `backend/app/api/v1/auth.py:83` routes legacy verify directly to409 api_version_required before any OTP/session service, while v2 delegates the same valid code to existing single-use verification. [Plan](12-09-PLAN.md:114) | CLOSED |
| T-12-09-03 | Spoofing / Denial of service | `Out-of-scope new mechanism` | accept | Original scoped acceptance AR-T-12-09-03 below; no new acceptance or mitigation waiver. [Plan](12-09-PLAN.md:115) | CLOSED |
| T-12-09-SC | Tampering | `No package boundary created` | accept | Original scoped acceptance AR-T-12-09-SC below; no new acceptance or mitigation waiver. [Plan](12-09-PLAN.md:116) | CLOSED |
| T-12-10-01 | Tampering / Information disclosure / Elevation of privilege | `backend/app/services/trading.py` | mitigate | `backend/app/services/trading.py:274` locks exact active account before holdings, finds user-global key, compares original root/payload and rolls back refusals; the unique-key race rechecks the original root at `:375`. [Plan](12-10-PLAN.md:113) | CLOSED |
| T-12-10-02 | Tampering / Information disclosure / Elevation of privilege | `backend/app/api/v2/trades.py` | mitigate | `backend/app/api/v2/trades.py:42` and `:61` require OwnedActivePortfolioDep and verify_csrf. PrivateRoute supplies no-store/error privacy, and service active-root rechecks occur before receipt reads. [Plan](12-10-PLAN.md:114) | CLOSED |
| T-12-10-03 | Spoofing / Denial of service | `Out-of-scope new mechanism` | accept | Original scoped acceptance AR-T-12-10-03 below; no new acceptance or mitigation waiver. [Plan](12-10-PLAN.md:115) | CLOSED |
| T-12-10-SC | Tampering | `No package boundary created` | accept | Original scoped acceptance AR-T-12-10-SC below; no new acceptance or mitigation waiver. [Plan](12-10-PLAN.md:116) | CLOSED |
| T-12-11-01 | Tampering / Information disclosure / Elevation of privilege | `backend/app/services/stock_trading.py` | mitigate | `backend/app/services/stock_trading.py:361` acquires instrument gate before exact active root lock, replays only matching immutable causes, and ends new execution with SQL authority validation at `:473` before commit. [Plan](12-11-PLAN.md:111) | CLOSED |
| T-12-11-02 | Tampering / Information disclosure / Elevation of privilege | `backend/app/api/v2/stock_trades.py` | mitigate | `backend/app/api/v2/stock_trades.py:18` and `:34` take the path-derived owned root, not a body target. `backend/app/services/stock_trading.py:284` joins root-bound immutable facts/movement and permits matching active-root replay before current market checks. [Plan](12-11-PLAN.md:112) | CLOSED |
| T-12-11-03 | Spoofing / Denial of service | `Out-of-scope new mechanism` | accept | Original scoped acceptance AR-T-12-11-03 below; no new acceptance or mitigation waiver. [Plan](12-11-PLAN.md:113) | CLOSED |
| T-12-11-SC | Tampering | `No package boundary created` | accept | Original scoped acceptance AR-T-12-11-SC below; no new acceptance or mitigation waiver. [Plan](12-11-PLAN.md:114) | CLOSED |
| T-12-12-01 | Tampering / Information disclosure / Elevation of privilege | `backend/app/services/stock_ownership.py` | mitigate | `backend/app/services/stock_ownership.py:536` validates every closure against actual root/owner/time/sequence/epoch. `:632` dispatches legacy NULL versus explicit2 without rewriting old bytes; unsupported or ambiguous digests refuse, and `:760` rejects postclosure reconstruction. [Plan](12-12-PLAN.md:109) | CLOSED |
| T-12-12-02 | Tampering / Information disclosure / Elevation of privilege | `backend/app/services/corporate_actions.py` | mitigate | `backend/app/services/corporate_actions.py:557` takes instrument then deterministic root/holding locks, re-reads active roots after waits and excludes frozen siblings. New global applications explicitly use version2 at `:685`, with per-root movement causes at `:693`. [Plan](12-12-PLAN.md:110) | CLOSED |
| T-12-12-03 | Spoofing / Denial of service | `Out-of-scope new mechanism` | accept | Original scoped acceptance AR-T-12-12-03 below; no new acceptance or mitigation waiver. [Plan](12-12-PLAN.md:111) | CLOSED |
| T-12-12-SC | Tampering | `No package boundary created` | accept | Original scoped acceptance AR-T-12-12-SC below; no new acceptance or mitigation waiver. [Plan](12-12-PLAN.md:112) | CLOSED |
| T-12-13-01 | Tampering / Information disclosure / Elevation of privilege | `backend/app/services/corporate_actions.py` | mitigate | `backend/app/services/corporate_actions.py:874` collects and reconstructs candidates per active root, not user; `:1020` selects same-root predecessor and `:1054` persists root+owner in the entitlement. Compound supersession FK also enforces lineage. [Plan](12-13-PLAN.md:110) | CLOSED |
| T-12-13-02 | Tampering / Information disclosure / Elevation of privilege | `backend/app/services/dividends.py` | mitigate | `backend/app/tasks/dividends.py:32` and `:48` select active root-bound VERIFIED/ANCHORS work and deduplicate same-root versions; `backend/app/services/dividends.py:45` verifies cause/root, then SQL locks/rechecks active roots and once-only original/correction identities. [Plan](12-13-PLAN.md:111) | CLOSED |
| T-12-13-03 | Spoofing / Denial of service | `Out-of-scope new mechanism` | accept | Original scoped acceptance AR-T-12-13-03 below; no new acceptance or mitigation waiver. [Plan](12-13-PLAN.md:112) | CLOSED |
| T-12-13-SC | Tampering | `No package boundary created` | accept | Original scoped acceptance AR-T-12-13-SC below; no new acceptance or mitigation waiver. [Plan](12-13-PLAN.md:113) | CLOSED |
| T-12-14-01 | Tampering / Information disclosure / Elevation of privilege | `backend/app/services/portfolio.py` | mitigate | `backend/app/services/portfolio.py:49` executes a single statement rooted at exact Account id+owner+active state, joins only that root's holdings/facts and values against its actual stored baseline. Missing root refuses rather than pooling. [Plan](12-14-PLAN.md:113) | CLOSED |
| T-12-14-02 | Tampering / Information disclosure / Elevation of privilege | `backend/app/services/history.py` | mitigate | `backend/app/services/history.py:43` and `:118` bind versioned cursors and trade selection to the requested root; `backend/app/services/event_history.py:165` scopes every union, hydration and original join to owner+root, including off-page correction originals. [Plan](12-14-PLAN.md:114) | CLOSED |
| T-12-14-03 | Spoofing / Denial of service | `Out-of-scope new mechanism` | accept | Original scoped acceptance AR-T-12-14-03 below; no new acceptance or mitigation waiver. [Plan](12-14-PLAN.md:115) | CLOSED |
| T-12-14-SC | Tampering | `No package boundary created` | accept | Original scoped acceptance AR-T-12-14-SC below; no new acceptance or mitigation waiver. [Plan](12-14-PLAN.md:116) | CLOSED |
| T-12-15-01 | Tampering / Information disclosure / Elevation of privilege | `backend/app/api/v2/portfolios.py` | mitigate | `backend/app/api/v2/portfolios.py:12` exposes authenticated metadata plus owned-active detail; `backend/app/api/v2/history.py:36` and `:52` require the same owned root and bounded, validated cursor/limit adapters. [Plan](12-15-PLAN.md:117) | CLOSED |
| T-12-15-02 | Tampering / Information disclosure / Elevation of privilege | `backend/app/api/v2/router.py` | mitigate | `backend/app/api/v2/router.py:10` composes the actual v2 routers; `backend/app/main.py:100` mounts both versions. `backend/app/api/v1/legacy_finance.py:11` refuses every listed old finance route after auth/CSRF and before service lookup. [Plan](12-15-PLAN.md:118) | CLOSED |
| T-12-15-03 | Spoofing / Denial of service | `Out-of-scope new mechanism` | accept | Original scoped acceptance AR-T-12-15-03 below; no new acceptance or mitigation waiver. [Plan](12-15-PLAN.md:119) | CLOSED |
| T-12-15-SC | Tampering | `No package boundary created` | accept | Original scoped acceptance AR-T-12-15-SC below; no new acceptance or mitigation waiver. [Plan](12-15-PLAN.md:120) | CLOSED |
| T-12-16-01 | Tampering / Information disclosure / Elevation of privilege | `deploy/db/bootstrap-roles.sql` | mitigate | `backend/app/db/portfolio_bootstrap.py:7` authenticates actual role attributes/membership, relation owners, fixed function body/declaration/OUT/search_path/ACL and trigger inventory. `:127` and `deploy/db/bootstrap-roles.sql:399` constrain app cash/holding columns and deny scheduler cash/lifecycle writes. [Plan](12-16-PLAN.md:113) | CLOSED |
| T-12-16-02 | Tampering / Information disclosure / Elevation of privilege | `deploy/configure-db.sh` | mitigate | `backend/app/db/portfolio_migrate.py:38`, `:47`, `:114` pin source hashes, actual restricted session identity/schema/objects and finite revision before bounded migration/final validation. `deploy/configure-db.sh:79` and `:127` require the explicit operation and stopped writers; `deploy/deploy.sh:457` admits source/schema before checkout. [Plan](12-16-PLAN.md:114) | CLOSED |
| T-12-16-03 | Spoofing / Denial of service | `Out-of-scope new mechanism` | accept | Original scoped acceptance AR-T-12-16-03 below; no new acceptance or mitigation waiver. [Plan](12-16-PLAN.md:115) | CLOSED |
| T-12-16-SC | Tampering | `No package boundary created` | accept | Original scoped acceptance AR-T-12-16-SC below; no new acceptance or mitigation waiver. [Plan](12-16-PLAN.md:116) | CLOSED |
| T-12-17-01 | Tampering / Information disclosure / Elevation of privilege | `deploy/backup-snapshot.py` | mitigate | `deploy/backup-snapshot.py:380`, `:416`, `:538`, `:788` and `:827` define exact revision-specific identity/schema/financial/root/marker projections and independently pinned authority fingerprints. Intermediate revisions cannot enter a runnable archive. [Plan](12-17-PLAN.md:114) | CLOSED |
| T-12-17-02 | Tampering / Information disclosure / Elevation of privilege | `deploy/verify-restore.py` | mitigate | `deploy/verify-restore.py:1064` authenticates the complete no-ACL schema/authority fingerprint, checks exactly ten trusted signatures, revokes PUBLIC/runtime EXECUTE before fixed grants and retains economic quarantine. `:848` compares exact data/schema/identity/root projections after restore. [Plan](12-17-PLAN.md:115) | CLOSED |
| T-12-17-03 | Spoofing / Denial of service | `Out-of-scope new mechanism` | accept | Original scoped acceptance AR-T-12-17-03 below; no new acceptance or mitigation waiver. [Plan](12-17-PLAN.md:116) | CLOSED |
| T-12-17-SC | Tampering | `No package boundary created` | accept | Original scoped acceptance AR-T-12-17-SC below; no new acceptance or mitigation waiver. [Plan](12-17-PLAN.md:117) | CLOSED |
| T-12-18-01 | Tampering / Information disclosure / Elevation of privilege | `deploy/tests/portfolio-execution-fixture.py` | mitigate | `deploy/tests/portfolio-execution-fixture.py:34` validates independent exact money/units/terminal oracles, `:74` creates a private immutable before snapshot and `:83` requires its unchanged external hash for comparison. [Plan](12-18-PLAN.md:114) | CLOSED |
| T-12-18-02 | Tampering / Information disclosure / Elevation of privilege | `deploy/tests/ops-fixtures.py` | mitigate | `deploy/tests/portfolio-sources.py:43`, `:87`, `:102`, `:169`, `:177` and `:186` pin the complete retained matrix, revision-before-import, program blob/tree, archive and image content/Config/RootFS. `deploy/tests/ops-fixtures.py` dispatches those authenticated consumers, without current-code substitution into retained lanes. [Plan](12-18-PLAN.md:115) | CLOSED |
| T-12-18-03 | Spoofing / Denial of service | `Out-of-scope new mechanism` | accept | Original scoped acceptance AR-T-12-18-03 below; no new acceptance or mitigation waiver. [Plan](12-18-PLAN.md:116) | CLOSED |
| T-12-18-SC | Tampering | `No package boundary created` | accept | Original scoped acceptance AR-T-12-18-SC below; no new acceptance or mitigation waiver. [Plan](12-18-PLAN.md:117) | CLOSED |
| T-12-19-01 | Tampering / Information disclosure / Elevation of privilege | `frontend/src/api/auth.ts` | mitigate | `frontend/src/api/auth.ts:6` accepts exactly email-only identity and never falls back to cash-bearing v1. `frontend/src/hooks/useMe.ts:13` advances the identity epoch and removes private caches while retaining only the exact public prices query. [Plan](12-19-PLAN.md:113) | CLOSED |
| T-12-19-02 | Tampering / Information disclosure / Elevation of privilege | `frontend/src/api/portfolios.ts` | mitigate | `frontend/src/api/portfolios.ts:14` validates bounded ordered canonical string IDs and names; `frontend/src/hooks/usePortfolioTarget.ts:58` captures owner/session/route scope and rejects late metadata. Zero/many discovery produces safe states, never a financial target. [Plan](12-19-PLAN.md:114) | CLOSED |
| T-12-19-03 | Spoofing / Denial of service | `Out-of-scope new mechanism` | accept | Original scoped acceptance AR-T-12-19-03 below; no new acceptance or mitigation waiver. [Plan](12-19-PLAN.md:115) | CLOSED |
| T-12-19-SC | Tampering | `No package boundary created` | accept | Original scoped acceptance AR-T-12-19-SC below; no new acceptance or mitigation waiver. [Plan](12-19-PLAN.md:116) | CLOSED |
| T-12-20-01 | Tampering / Information disclosure / Elevation of privilege | `frontend/src/api/trades.ts` | mitigate | `frontend/src/api/trades.ts:135`, `:169`, `:189` and `:235` build explicit root URLs, validate order/attempt and require returned quote/fill/holding identity to match the requested root and order. Stock adapters mirror this at `frontend/src/api/stockTrades.ts:613`. [Plan](12-20-PLAN.md:116) | CLOSED |
| T-12-20-02 | Tampering / Information disclosure / Elevation of privilege | `frontend/src/api/portfolio.ts` | mitigate | `frontend/src/api/portfolio.ts:272`, `frontend/src/api/history.ts:96` and `frontend/src/api/eventHistory.ts:295` require canonical explicit roots, same-root cursors and validated original-reference structures; unavailable/legacy responses throw rather than returning cached finance. [Plan](12-20-PLAN.md:117) | CLOSED |
| T-12-20-03 | Spoofing / Denial of service | `Out-of-scope new mechanism` | accept | Original scoped acceptance AR-T-12-20-03 below; no new acceptance or mitigation waiver. [Plan](12-20-PLAN.md:118) | CLOSED |
| T-12-20-SC | Tampering | `No package boundary created` | accept | Original scoped acceptance AR-T-12-20-SC below; no new acceptance or mitigation waiver. [Plan](12-20-PLAN.md:119) | CLOSED |
| T-12-21-01 | Tampering / Information disclosure / Elevation of privilege | `frontend/src/hooks/useQuote.ts` | mitigate | `frontend/src/hooks/useQuote.ts:20` captures owner/root/session and current-target authority; `:66` checks it before and after requests. `frontend/src/hooks/useTrade.ts:41` partitions state and freezes original attempts, refuses alternate payloads, suppresses stale publication and prevents unresolved reset. [Plan](12-21-PLAN.md:113) | CLOSED |
| T-12-21-02 | Tampering / Information disclosure / Elevation of privilege | `frontend/src/hooks/useStockTrade.ts` | mitigate | `frontend/src/hooks/useStockTrade.ts:615` resolves only its frozen original root/key/payload; `:718` captures original authority before execution and `:743` retries only the saved unknown attempt. Current scope gates all publication, and target loss cannot rebind the attempt. [Plan](12-21-PLAN.md:114) | CLOSED |
| T-12-21-03 | Spoofing / Denial of service | `Out-of-scope new mechanism` | accept | Original scoped acceptance AR-T-12-21-03 below; no new acceptance or mitigation waiver. [Plan](12-21-PLAN.md:115) | CLOSED |
| T-12-21-SC | Tampering | `No package boundary created` | accept | Original scoped acceptance AR-T-12-21-SC below; no new acceptance or mitigation waiver. [Plan](12-21-PLAN.md:116) | CLOSED |
| T-12-22-01 | Tampering / Information disclosure / Elevation of privilege | `frontend/src/hooks/usePortfolio.ts` | mitigate | `frontend/src/hooks/usePortfolio.ts:33` partitions hidden guards by client/owner/root/session, clears on identity change and checks current scope before/after fetch at `:275`. Returned projection is hidden when ownership or accepted authority is unavailable at `:393`. [Plan](12-22-PLAN.md:110) | CLOSED |
| T-12-22-02 | Tampering / Information disclosure / Elevation of privilege | `frontend/src/hooks/useHistory.ts` | mitigate | `frontend/src/hooks/useHistory.ts:9` partitions query/cursor by owner/root/epoch and rejects stale results/actions; `frontend/src/hooks/useEventHistory.ts:45` does the same for mixed pages, seen sets and original details. Pages key detail/focus lifetimes by the same captured root/session. [Plan](12-22-PLAN.md:111) | CLOSED |
| T-12-22-03 | Spoofing / Denial of service | `Out-of-scope new mechanism` | accept | Original scoped acceptance AR-T-12-22-03 below; no new acceptance or mitigation waiver. [Plan](12-22-PLAN.md:112) | CLOSED |
| T-12-22-SC | Tampering | `No package boundary created` | accept | Original scoped acceptance AR-T-12-22-SC below; no new acceptance or mitigation waiver. [Plan](12-22-PLAN.md:113) | CLOSED |
| T-12-23-01 | Tampering / Information disclosure / Elevation of privilege | `frontend/src/components/PortfolioContext.tsx` | mitigate | `frontend/src/components/PortfolioContext.tsx:2` uses React-escaped wrapping text. `frontend/src/components/PortfolioTargetBoundary.tsx:9` mounts financial children only for ready explicit target and replaces unavailable/zero/many views with nonfinancial safe states. [Plan](12-23-PLAN.md:112) | CLOSED |
| T-12-23-02 | Tampering / Information disclosure / Elevation of privilege | `frontend/src/App.tsx` | mitigate | `frontend/src/App.tsx:67` uses sole-root discovery only to replace-navigate into explicit links; `:136` wraps financial routes in PortfolioTargetBoundary. Account remains identity-only and current-owner/root navigation is derived through usePortfolioTarget. [Plan](12-23-PLAN.md:113) | CLOSED |
| T-12-23-03 | Spoofing / Denial of service | `Out-of-scope new mechanism` | accept | Original scoped acceptance AR-T-12-23-03 below; no new acceptance or mitigation waiver. [Plan](12-23-PLAN.md:114) | CLOSED |
| T-12-23-SC | Tampering | `No package boundary created` | accept | Original scoped acceptance AR-T-12-23-SC below; no new acceptance or mitigation waiver. [Plan](12-23-PLAN.md:115) | CLOSED |
| T-12-24-01 | Tampering / Information disclosure / Elevation of privilege | `frontend/src/pages/TradePage.tsx` | mitigate | `frontend/src/pages/TradePage.tsx:473` captures the verified Outlet target in a root/session-keyed child; quote/confirmation/receipt and Portfolio links use that original root, with hook-level frozen unknown attempts and unavailable masking. [Plan](12-24-PLAN.md:110) | CLOSED |
| T-12-24-02 | Tampering / Information disclosure / Elevation of privilege | `frontend/src/pages/StockTradePage.tsx` | mitigate | `frontend/src/pages/StockTradePage.tsx:369` keys the view by owner/root/session/symbol, captures original portfolio label and uses it through quote/attempt/receipt at `:269`; current-target loss removes actionable children via the boundary. [Plan](12-24-PLAN.md:111) | CLOSED |
| T-12-24-03 | Spoofing / Denial of service | `Out-of-scope new mechanism` | accept | Original scoped acceptance AR-T-12-24-03 below; no new acceptance or mitigation waiver. [Plan](12-24-PLAN.md:112) | CLOSED |
| T-12-24-SC | Tampering | `No package boundary created` | accept | Original scoped acceptance AR-T-12-24-SC below; no new acceptance or mitigation waiver. [Plan](12-24-PLAN.md:113) | CLOSED |
| T-12-25-01 | Tampering / Information disclosure / Elevation of privilege | `frontend/src/pages/PortfolioPage.tsx` | mitigate | `frontend/src/pages/PortfolioPage.tsx:16` reads the verified Outlet target and passes it to usePortfolio; scoped holding trade links and actual stored-baseline/incomplete semantics remain. No sibling or pooled summary is introduced. [Plan](12-25-PLAN.md:113) | CLOSED |
| T-12-25-02 | Tampering / Information disclosure / Elevation of privilege | `frontend/src/pages/HistoryPage.tsx` | mitigate | `frontend/src/pages/HistoryPage.tsx:36` keys root/session detail state and `:59` scopes DOM IDs/focus. Its mixed History hook and client require the same root/cursor; original details are embedded only from server-owned projections. [Plan](12-25-PLAN.md:114) | CLOSED |
| T-12-25-03 | Spoofing / Denial of service | `Out-of-scope new mechanism` | accept | Original scoped acceptance AR-T-12-25-03 below; no new acceptance or mitigation waiver. [Plan](12-25-PLAN.md:115) | CLOSED |
| T-12-25-SC | Tampering | `No package boundary created` | accept | Original scoped acceptance AR-T-12-25-SC below; no new acceptance or mitigation waiver. [Plan](12-25-PLAN.md:116) | CLOSED |
| T-12-26-01 | Tampering / Information disclosure / Elevation of privilege | `frontend/e2e/portfolio-ownership.spec.ts` | mitigate | `deploy/tests/run-stock-browser.py:72` requires a new private synthetic review path; `:139` strips provider/production/Compose defaults, uses its own temporary fake/console environment and isolated project. Full no-retry browser journeys and exact owned cleanup are explicit at `:274`. [Plan](12-26-PLAN.md:115) | CLOSED |
| T-12-26-02 | Tampering / Information disclosure / Elevation of privilege | `.github/workflows/ci.yml` | mitigate | `.github/workflows/ci.yml` retains the complete lint/type/coverage/audit/browser/build/image/ops graph; `deploy/tests/run-portfolio-validation.py:44` reads the exact CI critical command and `:97` authenticates current/archive/retained/image identities around every serial recovery stage. Mutation regressions are explicit in `deploy/tests/test-ci-ops.py:951`. [Plan](12-26-PLAN.md:116) | CLOSED |
| T-12-26-03 | Spoofing / Denial of service | `Out-of-scope new mechanism` | accept | Original scoped acceptance AR-T-12-26-03 below; no new acceptance or mitigation waiver. [Plan](12-26-PLAN.md:117) | CLOSED |
| T-12-26-SC | Tampering | `Locked build/audit image graph` | mitigate | `.github/workflows/ci.yml:122` pins datastore/scanner images; `deploy/scan-images.py:84` requires immutable IDs and `:178` scans HIGH,CRITICAL with nonzero failure, including unfixed; actual complete final receipt has five successful reports. [Plan](12-26-PLAN.md:118) | CLOSED |
| T-12-27-01 | Tampering / Repudiation | `.planning/phases/12-preserve-existing-investing-under-portfolio-ownership/12-LOCAL-VERIFICATION.md` | mitigate | `deploy/tests/run-portfolio-validation.py:44` and `:70` execute the actual unchanged gates and fail on nonzero results, with exclusive stack cleanup. The inspected `/tmp/phase12-27-security-finish-second.result.json` is exit0, no source change, and retained atomic results/coverage/scans support 12-LOCAL-VERIFICATION.md. [Plan](12-27-PLAN.md:108) | CLOSED |
| T-12-27-02 | Tampering / Repudiation | `.planning/phases/12-preserve-existing-investing-under-portfolio-ownership/12-RECOVERY-PROOF.md` | mitigate | `deploy/tests/run-portfolio-validation.py:97`, `:126`, `:136` and `deploy/tests/portfolio-smoke.py:158` enforce one archive, source/image reauthentication, real encrypted source-destroyed cold restore and TLS parity. The inspected full recovery log ends same_archive_final_ci=true with exit0 and no source drift. [Plan](12-27-PLAN.md:109) | CLOSED |
| T-12-27-03 | Spoofing / Denial of service | `Out-of-scope new mechanism` | accept | Original scoped acceptance AR-T-12-27-03 below; no new acceptance or mitigation waiver. [Plan](12-27-PLAN.md:110) | CLOSED |
| T-12-27-SC | Tampering | `Locked build/audit image graph` | mitigate | `deploy/tests/run-portfolio-validation.py:44` includes both audits and all five actual images; `:85` uses check=True, while `deploy/scan-images.py:218` rejects any HIGH/CRITICAL finding. Actual final whole-run receipt is exit0. [Plan](12-27-PLAN.md:111) | CLOSED |
| T-12-28-01 | Tampering / Repudiation | `.planning/phases/12-preserve-existing-investing-under-portfolio-ownership/12-HUMAN-UAT.md` | mitigate | `12-HUMAN-UAT.md:13` and `:47` record the exact owner UI response approved against combined ZIP c87cb4a3; Plan28 preserves artifact/source hashes and explicit response, without substituting prior approvals or automation. [Plan](12-28-PLAN.md:106) | CLOSED |
| T-12-28-02 | Tampering / Repudiation | `.planning/phases/12-preserve-existing-investing-under-portfolio-ownership/12-HUMAN-UAT.md` | mitigate | `12-HUMAN-UAT.md:65` records the independent Yes—native 200% passed response to the actual desktop Zoom-menu question; browser remains unspecified. Immutable capture-time false flags remain unchanged and do not claim automated native zoom. [Plan](12-28-PLAN.md:107) | CLOSED |
| T-12-28-03 | Spoofing / Denial of service | `Out-of-scope new mechanism` | accept | Original scoped acceptance AR-T-12-28-03 below; no new acceptance or mitigation waiver. [Plan](12-28-PLAN.md:108) | CLOSED |
| T-12-28-SC | Tampering | `No package boundary created` | accept | Original scoped acceptance AR-T-12-28-SC below; no new acceptance or mitigation waiver. [Plan](12-28-PLAN.md:109) | CLOSED |

## Accepted Risks Log — Original Plan Scope Only

These54 entries were authored in the approved execution plans. They do not
accept a discovered security defect. Their rationale is limited to the absence
of a new mechanism/package boundary in that plan, while existing mechanisms
and final gates remain required. No acceptance here closes an independent code
review blocker or admits live market data.

The no-new-package premise is corroborated by a diff from the first Phase12
source parent `e14fa20753a008bab52afbe04c8f735faf5f9fd2`: neither lockfile,
dependency manifest nor package declaration changed. Existing authentication,
rate controls and bounded cycles remain implemented; final audited gates are
covered by T-12-26-SC/T-12-27-SC. Evidence/checkpoint plans introduce no runtime
queue or endpoint.

| Risk ID | Threat reference | Original rationale | Authority / date |
|---|---|---|---|
| AR-T-12-01-03 | T-12-01-03 | Not applicable to a new authentication/queue mechanism: This plan introduces no authentication algorithm or unbounded external queue; existing OTP/session/rate-limit/timeouts remain unchanged and are regression-tested in27. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-01-SC | T-12-01-SC | No install/add/upgrade or new registry input in this plan; supply-chain gates belong12-26-02/12-27-01, not an invented runtime guard here. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-02-03 | T-12-02-03 | Not applicable to a new authentication/queue mechanism: This plan introduces no authentication algorithm or unbounded external queue; existing OTP/session/rate-limit/timeouts remain unchanged and are regression-tested in27. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-02-SC | T-12-02-SC | No install/add/upgrade or new registry input in this plan; supply-chain gates belong12-26-02/12-27-01, not an invented runtime guard here. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-03-03 | T-12-03-03 | Not applicable to a new authentication/queue mechanism: This plan introduces no authentication algorithm or unbounded external queue; existing OTP/session/rate-limit/timeouts remain unchanged and are regression-tested in27. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-03-SC | T-12-03-SC | No install/add/upgrade or new registry input in this plan; supply-chain gates belong12-26-02/12-27-01, not an invented runtime guard here. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-04-03 | T-12-04-03 | Not applicable to a new authentication/queue mechanism: This plan introduces no authentication algorithm or unbounded external queue; existing OTP/session/rate-limit/timeouts remain unchanged and are regression-tested in27. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-04-SC | T-12-04-SC | No install/add/upgrade or new registry input in this plan; supply-chain gates belong12-26-02/12-27-01, not an invented runtime guard here. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-05-03 | T-12-05-03 | Not applicable to a new authentication/queue mechanism: This plan introduces no authentication algorithm or unbounded external queue; existing OTP/session/rate-limit/timeouts remain unchanged and are regression-tested in27. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-05-SC | T-12-05-SC | No install/add/upgrade or new registry input in this plan; supply-chain gates belong12-26-02/12-27-01, not an invented runtime guard here. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-06-03 | T-12-06-03 | Not applicable to a new authentication/queue mechanism: This plan introduces no authentication algorithm or unbounded external queue; existing OTP/session/rate-limit/timeouts remain unchanged and are regression-tested in27. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-06-SC | T-12-06-SC | No install/add/upgrade or new registry input in this plan; supply-chain gates belong12-26-02/12-27-01, not an invented runtime guard here. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-07-03 | T-12-07-03 | Not applicable to a new authentication/queue mechanism: This plan introduces no authentication algorithm or unbounded external queue; existing OTP/session/rate-limit/timeouts remain unchanged and are regression-tested in27. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-07-SC | T-12-07-SC | No install/add/upgrade or new registry input in this plan; supply-chain gates belong12-26-02/12-27-01, not an invented runtime guard here. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-08-03 | T-12-08-03 | Not applicable to a new authentication/queue mechanism: This plan introduces no authentication algorithm or unbounded external queue; existing OTP/session/rate-limit/timeouts remain unchanged and are regression-tested in27. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-08-SC | T-12-08-SC | No install/add/upgrade or new registry input in this plan; supply-chain gates belong12-26-02/12-27-01, not an invented runtime guard here. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-09-03 | T-12-09-03 | Not applicable to a new authentication/queue mechanism: This plan introduces no authentication algorithm or unbounded external queue; existing OTP/session/rate-limit/timeouts remain unchanged and are regression-tested in27. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-09-SC | T-12-09-SC | No install/add/upgrade or new registry input in this plan; supply-chain gates belong12-26-02/12-27-01, not an invented runtime guard here. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-10-03 | T-12-10-03 | Not applicable to a new authentication/queue mechanism: This plan introduces no authentication algorithm or unbounded external queue; existing OTP/session/rate-limit/timeouts remain unchanged and are regression-tested in27. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-10-SC | T-12-10-SC | No install/add/upgrade or new registry input in this plan; supply-chain gates belong12-26-02/12-27-01, not an invented runtime guard here. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-11-03 | T-12-11-03 | Not applicable to a new authentication/queue mechanism: This plan introduces no authentication algorithm or unbounded external queue; existing OTP/session/rate-limit/timeouts remain unchanged and are regression-tested in27. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-11-SC | T-12-11-SC | No install/add/upgrade or new registry input in this plan; supply-chain gates belong12-26-02/12-27-01, not an invented runtime guard here. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-12-03 | T-12-12-03 | Not applicable to a new authentication/queue mechanism: This plan introduces no authentication algorithm or unbounded external queue; existing OTP/session/rate-limit/timeouts remain unchanged and are regression-tested in27. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-12-SC | T-12-12-SC | No install/add/upgrade or new registry input in this plan; supply-chain gates belong12-26-02/12-27-01, not an invented runtime guard here. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-13-03 | T-12-13-03 | Not applicable to a new authentication/queue mechanism: This plan introduces no authentication algorithm or unbounded external queue; existing OTP/session/rate-limit/timeouts remain unchanged and are regression-tested in27. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-13-SC | T-12-13-SC | No install/add/upgrade or new registry input in this plan; supply-chain gates belong12-26-02/12-27-01, not an invented runtime guard here. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-14-03 | T-12-14-03 | Not applicable to a new authentication/queue mechanism: This plan introduces no authentication algorithm or unbounded external queue; existing OTP/session/rate-limit/timeouts remain unchanged and are regression-tested in27. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-14-SC | T-12-14-SC | No install/add/upgrade or new registry input in this plan; supply-chain gates belong12-26-02/12-27-01, not an invented runtime guard here. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-15-03 | T-12-15-03 | Not applicable to a new authentication/queue mechanism: This plan introduces no authentication algorithm or unbounded external queue; existing OTP/session/rate-limit/timeouts remain unchanged and are regression-tested in27. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-15-SC | T-12-15-SC | No install/add/upgrade or new registry input in this plan; supply-chain gates belong12-26-02/12-27-01, not an invented runtime guard here. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-16-03 | T-12-16-03 | Not applicable to a new authentication/queue mechanism: This plan introduces no authentication algorithm or unbounded external queue; existing OTP/session/rate-limit/timeouts remain unchanged and are regression-tested in27. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-16-SC | T-12-16-SC | No install/add/upgrade or new registry input in this plan; supply-chain gates belong12-26-02/12-27-01, not an invented runtime guard here. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-17-03 | T-12-17-03 | Not applicable to a new authentication/queue mechanism: This plan introduces no authentication algorithm or unbounded external queue; existing OTP/session/rate-limit/timeouts remain unchanged and are regression-tested in27. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-17-SC | T-12-17-SC | No install/add/upgrade or new registry input in this plan; supply-chain gates belong12-26-02/12-27-01, not an invented runtime guard here. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-18-03 | T-12-18-03 | Not applicable to a new authentication/queue mechanism: This plan introduces no authentication algorithm or unbounded external queue; existing OTP/session/rate-limit/timeouts remain unchanged and are regression-tested in27. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-18-SC | T-12-18-SC | No install/add/upgrade or new registry input in this plan; supply-chain gates belong12-26-02/12-27-01, not an invented runtime guard here. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-19-03 | T-12-19-03 | Not applicable to a new authentication/queue mechanism: This plan introduces no authentication algorithm or unbounded external queue; existing OTP/session/rate-limit/timeouts remain unchanged and are regression-tested in27. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-19-SC | T-12-19-SC | No install/add/upgrade or new registry input in this plan; supply-chain gates belong12-26-02/12-27-01, not an invented runtime guard here. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-20-03 | T-12-20-03 | Not applicable to a new authentication/queue mechanism: This plan introduces no authentication algorithm or unbounded external queue; existing OTP/session/rate-limit/timeouts remain unchanged and are regression-tested in27. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-20-SC | T-12-20-SC | No install/add/upgrade or new registry input in this plan; supply-chain gates belong12-26-02/12-27-01, not an invented runtime guard here. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-21-03 | T-12-21-03 | Not applicable to a new authentication/queue mechanism: This plan introduces no authentication algorithm or unbounded external queue; existing OTP/session/rate-limit/timeouts remain unchanged and are regression-tested in27. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-21-SC | T-12-21-SC | No install/add/upgrade or new registry input in this plan; supply-chain gates belong12-26-02/12-27-01, not an invented runtime guard here. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-22-03 | T-12-22-03 | Not applicable to a new authentication/queue mechanism: This plan introduces no authentication algorithm or unbounded external queue; existing OTP/session/rate-limit/timeouts remain unchanged and are regression-tested in27. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-22-SC | T-12-22-SC | No install/add/upgrade or new registry input in this plan; supply-chain gates belong12-26-02/12-27-01, not an invented runtime guard here. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-23-03 | T-12-23-03 | Not applicable to a new authentication/queue mechanism: This plan introduces no authentication algorithm or unbounded external queue; existing OTP/session/rate-limit/timeouts remain unchanged and are regression-tested in27. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-23-SC | T-12-23-SC | No install/add/upgrade or new registry input in this plan; supply-chain gates belong12-26-02/12-27-01, not an invented runtime guard here. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-24-03 | T-12-24-03 | Not applicable to a new authentication/queue mechanism: This plan introduces no authentication algorithm or unbounded external queue; existing OTP/session/rate-limit/timeouts remain unchanged and are regression-tested in27. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-24-SC | T-12-24-SC | No install/add/upgrade or new registry input in this plan; supply-chain gates belong12-26-02/12-27-01, not an invented runtime guard here. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-25-03 | T-12-25-03 | Not applicable to a new authentication/queue mechanism: This plan introduces no authentication algorithm or unbounded external queue; existing OTP/session/rate-limit/timeouts remain unchanged and are regression-tested in27. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-25-SC | T-12-25-SC | No install/add/upgrade or new registry input in this plan; supply-chain gates belong12-26-02/12-27-01, not an invented runtime guard here. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-26-03 | T-12-26-03 | Not applicable to a new authentication/queue mechanism: This plan introduces no authentication algorithm or unbounded external queue; existing OTP/session/rate-limit/timeouts remain unchanged and are regression-tested in27. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-27-03 | T-12-27-03 | Not applicable to a new authentication/queue mechanism: Evidence/checkpoint plan introduces no runtime endpoint or queue; availability/authentication controls remain implementation obligations in08–26. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-28-03 | T-12-28-03 | Not applicable to a new authentication/queue mechanism: Evidence/checkpoint plan introduces no runtime endpoint or queue; availability/authentication controls remain implementation obligations in08–26. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |
| AR-T-12-28-SC | T-12-28-SC | No install/add/upgrade or new registry input in this plan; supply-chain gates belong12-26-02/12-27-01, not an invented runtime guard here. | Plan-authored disposition; approved Phase12 execution,2026-11-16; verified scope2026-11-17 |

## Implementation Threat Flag Mapping

| Summary flag | Existing threat references | Actual evidence | Result |
|---|---|---|---|
| trigger_definer —12-07 | T-12-07-01, T-12-16-01, T-12-17-02 | `0017_portfolio_ownership.py:79` is fixed-path trigger-only definer; `portfolio_bootstrap.py:37` authenticates its exact declaration/body/owner/ACL; `verify-restore.py:1084` authenticates and quarantines the trusted routine inventory | MAPPED/CLOSED |
| lock_definer —12-12 | T-12-12-02, T-12-16-01, T-12-17-02 | `0017_portfolio_ownership.py:112` takes instrument then ordered root locks without cash writes; PUBLIC revoked and scheduler-only EXECUTE; `portfolio_bootstrap.py:173` and fixed recovery grants carry that boundary | MAPPED/CLOSED |
| migration_child —12-16 | T-12-16-02, T-12-18-02, T-12-27-02 | `portfolio_migrate.py:38/47/114` validates source/actual caller/schema, bounds child execution and redacts failures; selected source/archive/image authentication preserves exact consumers | MAPPED/CLOSED |
| dev_role_setup —12-16 | T-12-16-01, T-12-16-02 | `dev_bootstrap.py:255` requires exact local dev endpoint/admin; `:91` uses fixed object inventory, an ephemeral actual migrator child, login disable/password removal and lock cleanup | MAPPED/CLOSED |
| synthetic_cold_repository —12-26 | T-12-18-01, T-12-26-02, T-12-27-02 | `portfolio-smoke.py:158` verifies the restic binary, encrypts fixed local payload, destroys original inputs/source server, checks/read-verifies restore into a separate cold project and compares the immutable before oracle | MAPPED/CLOSED |
| successor_archive_inventory —12-26 | T-12-17-01, T-12-17-02, T-12-26-02 | `verify-restore.py:495` requires exact optional version1 payload/hash inventory; old layout dispatch remains finite; `:1064` authenticates current schema/no-ACL authority before fixed quarantine grants | MAPPED/CLOSED |

**Unregistered flags:0.** No transfer disposition exists in the plan register.
No threat was omitted merely because it spans later bootstrap/recovery consumers.

## Security Audit Trail

| Audit date | Total | Verified mitigations | Original scoped acceptances | Closed | Open | Run by |
|---|---|---|---|---|---|---|
|2026-11-17|112|58|54|112|0|Independent gsd-security-auditor|

## Sign-Off

- [x] All112 threats retain their original disposition and individually recorded evidence.
- [x] All58 implemented mitigation obligations were inspected in actual code.
- [x] All54 original plan-scoped acceptances are explicitly logged.
- [x] All six SUMMARY flags map to declared threats; zero unregistered flags.
- [x] `threats_open: 0` and `status: verified` reflect this declared-mitigation scope.
- [x] UI acceptance and native200% responses are separate actual owner results,
  not inferred from automation; their immutable capture flags remain untouched.

**Declared-threat verification: verified2026-11-17.** Independent code-review
findings, UI review, schema/regression checks and phase goal verification are
separate gates. Any functional fail-closed discovery issue found by code review
must be resolved through that gate; this audit is not a whole-phase clean-code
claim or permission to publish, deploy, activate stocks or advance a milestone.

