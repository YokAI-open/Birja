---
phase: 13-create-and-compare-independent-strategies
reviewed: 2026-11-18T18:46:46Z
depth: standard
diff_base: 7125fec
reviewed_head: fa28d8e
files_reviewed: 72
files_reviewed_list:
  - .github/workflows/ci.yml
  - CLAUDE.md
  - backend/alembic/sql/0019_portfolio_metadata.sql
  - backend/alembic/sql/0020_portfolio_management.sql
  - backend/alembic/versions/0018_portfolio_management_expansion.py
  - backend/alembic/versions/0019_portfolio_management_backfill.py
  - backend/alembic/versions/0020_portfolio_management_authority.py
  - backend/app/api/v2/portfolio_management.py
  - backend/app/api/v2/portfolios.py
  - backend/app/core/config.py
  - backend/app/db/dev_bootstrap.py
  - backend/app/db/portfolio_bootstrap.py
  - backend/app/db/portfolio_migrate.py
  - backend/app/db/schema_contract.py
  - backend/app/models/__init__.py
  - backend/app/models/portfolio_creation.py
  - backend/app/models/user.py
  - backend/app/schemas/portfolios.py
  - backend/app/services/accounts.py
  - backend/app/services/portfolio.py
  - backend/app/services/portfolios.py
  - deploy/backup-snapshot.py
  - deploy/db/bootstrap-roles.sql
  - deploy/recovery-bundle.sh
  - deploy/tests/fixtures/portfolio-recovery-0020.json
  - deploy/tests/ops-fixtures.py
  - deploy/tests/portfolio-execution-fixture.py
  - deploy/tests/portfolio-management-recovery-fixture.py
  - deploy/tests/portfolio-retained-sources.json
  - deploy/tests/portfolio-smoke.py
  - deploy/tests/portfolio-sources.py
  - deploy/tests/portfolio-ui-evidence.py
  - deploy/tests/run-portfolio-validation.py
  - deploy/tests/run-stock-browser.py
  - deploy/tests/test-db-operations.sh
  - deploy/tests/test-dev-bootstrap.py
  - deploy/tests/test-rollback-db-security.sh
  - deploy/verify-restore.py
  - frontend/e2e/portfolio-browser-fixture.py
  - frontend/src/App.tsx
  - frontend/src/api/portfolio.ts
  - frontend/src/api/portfolioManagement.ts
  - frontend/src/api/portfolioOverview.ts
  - frontend/src/api/portfolios.ts
  - frontend/src/components/PortfolioCreateForm.tsx
  - frontend/src/components/PortfolioMetadataForm.tsx
  - frontend/src/components/PortfolioSwitcher.tsx
  - frontend/src/components/PortfolioTargetBoundary.tsx
  - frontend/src/hooks/useEventHistory.ts
  - frontend/src/hooks/useHistory.ts
  - frontend/src/hooks/usePortfolio.ts
  - frontend/src/hooks/usePortfolioManagement.ts
  - frontend/src/hooks/usePortfolioOverview.ts
  - frontend/src/hooks/usePortfolioTarget.ts
  - frontend/src/hooks/useStockTrade.ts
  - frontend/src/hooks/useTrade.ts
  - frontend/src/lib/portfolioCreationAttempt.ts
  - frontend/src/lib/portfolioMetadataEvents.ts
  - frontend/src/pages/MarketsPage.tsx
  - frontend/src/pages/PortfolioPage.tsx
  - frontend/src/pages/PortfoliosPage.tsx
  - frontend/src/pages/TradePage.tsx
  - frontend/src/pages/StockTradePage.tsx
  - frontend/src/pages/TradeRenameRecovery.test.tsx
  - backend/tests/test_portfolio_management_grants.py
  - backend/tests/test_portfolio_strategy_events.py
  - backend/tests/test_dev_bootstrap.py
  - deploy/deploy.sh
  - deploy/tests/test-deploy-compatibility.sh
  - deploy/tests/test-deploy-prerequisites.py
  - deploy/tests/test-stock-recovery-contracts.py
  - deploy/tests/test-db-config.sh
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
resolved_findings:
  - CR-01
  - CR-02
  - CR-03
status: clean
---

# Phase 13: Integrated Code Review

## Narrative Findings (AI reviewer)

### CR-01: Retained trade names are not wired into the actual ticket and receipt UI

**Original classification:** BLOCKER — incorrect original-attempt presentation after rename/remount.
**Disposition:** RESOLVED in `6bfb447`, independently re-reviewed after RED `bc4298c`.

**Files:** `frontend/src/hooks/useTrade.ts:175`,
`frontend/src/hooks/useStockTrade.ts:39`; integration callers
`frontend/src/pages/TradePage.tsx:102`, `:254`, `:300` and
`frontend/src/pages/StockTradePage.tsx:45`, `:269`, `:275`.

**Issue:** Both hooks correctly retain the original attempt name, but their actual
page components still render independently stored component-local labels.
`TradePage` initializes `attemptName` from `target.name`; `StockTradePage`
initializes `originalName` the same way. Neither page reads the retained hook
field. Those local values do not survive the real metadata-renewal boundary:
`PortfolioTargetBoundary` removes its financial Outlet while discovery is
invalidated/loading and then mounts it again with the renamed target.

Concrete sequence: submit an order in **Original**, lose or defer its response,
rename that portfolio to **Renamed** in another tab, and let authenticated
metadata renewal complete. The original request remains in the hook cache with
its original ID/key/payload/name, but the remounted page initializes its local
label as **Renamed**. Both the unresolved original attempt and its subsequent
explicit-replay receipt therefore show the new name. A previously filled
cached receipt has the same remount problem. This defeats the planned distinction
between the current page label and the frozen original-attempt label. It does
not demonstrate cash duplication, cross-owner disclosure or request retargeting;
the defect is the incorrect financial-context label.

**Fix:** Use `trade.originalName` for crypto pending/unknown/filled presentation,
and `t.originalName` (or the attempt's frozen `portfolioName`) for stock original
attempts and receipts. Retain the current/local preview name only for an
unsubmitted preview. The page header can continue showing the current
authenticated name; clear the original label only through the existing explicit
new-order transition. Do not rewrite the original request or weaken target guards.

**Required regression:** A routed component/browser test for each asset should
submit a pending/lost original, perform a real rename/discovery invalidation
that removes and remounts the financial Outlet, assert a current **Renamed**
page context alongside an **Original** unresolved-attempt context, then check
the original result with byte-identical ID/key/payload and assert an **Original**
receipt. Include revisiting an already filled receipt after rename. Existing
`portfolioCrypto.test.tsx` / `portfolioStock.test.tsx` hook tests assert the
retained name but do not render these page-local consumers, so they cannot
detect this integration failure.

**Resolution review:** The crypto consumer now takes its unresolved-attempt and
receipt labels from `trade.originalName`; the stock consumer uses
`t.originalName` for an original attempt/receipt and keeps separate local
`previewName` only for an unsubmitted quote. Both current page contexts remain
bound to the newly authenticated name. The existing hook state retains the
original name through late-result recovery and filled receipts, then its
explicit new-order transition clears it. No request payload, target guard,
idempotency key, money calculation or authority check changed.

`TradeRenameRecovery.test.tsx` renders the actual pages under the actual
`PortfolioTargetBoundary`, rather than mocking their hook-returned name. Its
six cases cover crypto/stock crossed with lost, pending and already-filled
outcomes. Each forces discovery loading, asserts removal/remount of the
financial page, checks the current renamed context and frozen original context,
checks byte-identical replay requests where applicable, checks the receipt's
portfolio link, and verifies Trade again clears the original name and quantity.
The case structure and assertions address the failure described above. The
executor reports all six failed before the consumer repair and passed after it;
138 affected cases, typecheck and lint also passed. This reviewer inspected the
actual diff, test and hook/caller lifecycle; it did not rerun those commands.
No remaining or newly introduced defect was demonstrated in this repair.

### CR-02: Management owner locks invert the dividend user foreign-key lock

**Original classification:** BLOCKER — concurrent metadata/creation replay and
dividend processing can deadlock or encounter a lock-timeout refusal.
**Disposition:** RESOLVED in `99166d9`, independently reviewed after deterministic
RED `203815f`. Original trace and fixture review are preserved in
`13-17-FIXTURE-REVIEW.md`.

**Runtime source:** `backend/alembic/sql/0020_portfolio_management.sql:16`,
`:63`, `:96`. All three owner-row locks now use `FOR NO KEY UPDATE`, retaining
mutual serialization among management operations while allowing the dividend
ledger FK's `KEY SHARE`. The account lock, authenticated owner predicate,
canonicalization, cap/quota ordering, permanent owner/key binding, grant amount,
transactions, timeout and row checks are unchanged. The fix does not alter
retained0017 dividend SQL or historical0015–17/0019 migrations.

**Binding review:** Independently compared all1172 measured catalogue records
before/after: reversing only the exact `WHERE u.id=p_user FOR NO KEY UPDATE;`
line in the three routine definitions makes the entire record multiset equal.
The measured ACL is unchanged at
`041a948470f9692628da43b35263a47bf58f4815310a0793d5eec099fa64c87e`.
The current catalogue becomes
`535cacb140a3a1753b5cf27e2eadcb80bc272a9b12772defd3936a3edc6c2209`.
The producer, production bootstrap, migration runner, restore source guards and
current recovery fixture all bind the corresponding current hashes; no matching
predicate, source guard, historical literal or privilege check was removed.
The stored0020 specimen's only JSON changes are that catalogue hash and the
same three function definitions; finances, table digests, identity tails,
constraints, owners and ACLs remain exact.

Recomputed the current authority hash from the specimen as
`0192d3a7222af2a91930d34b7089ef93371e849bc32f911cacc8383fd5ac5ebf`;
independently projecting the six quarantined financial/management routine ACL
revocations yields
`d6486b31f5609a6fdbeadaf4eeb7d9f0b4eaabe1de0566e646d85080a939fa26`;
projecting no-ACL tables/columns/sequences and default PUBLIC function EXECUTE
yields `e88cb1971126447232f872c3b93fe18454ef58094becdcecd4d9066af44e3cfe`.
These match the repaired constants; schema and ACL fingerprints stay unchanged.
This validates the intended new definition, not an arbitrary repin of a failing
financial or permission oracle.

**Regression review:** The observed-blocking-PID case now covers metadata and
original creation replay, requiring both successful200, the same root ID,
cash10000.50 and exactly two original creation records. Restricted-grant tests
also exercise initialize/create/rename after reapplying the unchanged ACL
profile. Existing cap, canonical intent and replay tests remain in scope.
Inspected the receipt and verified its committed source and log hashes:
70 focused tests passed363.48s, the two overlap cases passed12.71s, and four
offline contract groups passed8+11+8+6. No new issue was demonstrated. These
commands were run by the executor, not rerun by this reviewer. They do not
replace final full-suite/image/browser/TLS/encrypted-recovery qualification.

### CR-03: Deployment source predicate pins the wrong immutable migration bytes

**Original classification:** BLOCKER — the genuine supported portfolio source
is refused before rollout because its marker hash cannot match the stale pin.
**Disposition:** RESOLVED at `74ee5ea`, following genuine positive and negative
source fixtures in `0e55743`.

**File:** `deploy/deploy.sh:89`. The one-line repair replaces stale
`df84ca54126423c9de52821906c93a79b3251983a2a9b032da939419b9ee7ee9`
with the actual immutable0017 migration marker hash
`92cff0699a40b0b8f5f4d66bc56a39a2ef88e3184860d86d6957607a3413f32b`.
Independently hashed both the current file and the complete retained
`4b4320b4cc373268a8d598612a563cd5ef199700` Git object's migration bytes; both
match the repaired pin and the existing `portfolio_migrate.py` source map.
No migration bytes, schema/profile fingerprint, source predicate structure,
finite revision set, tested-source equality check or rollback branch changed.
This repairs the pin to unchanged reviewed bytes; it does not bless modified
historical migration contents or introduce a permissive fallback.

The47-case compatibility matrix now creates distinct real Git commits for
legacy-only source, correct immutable portfolio marker and corrupted marker.
It calls the real source predicate rather than stubbing it. Refusals require
the exact incompatibility marker, no simulated deployment calls and unchanged
deployment/pending records. Correct portfolio-upgrade lanes assert writer-stop
before the inherited-lock configure-db call and restart afterwards. Runtime
rollback remains separate: supported legacy runtime examples pass,0014/0017
need the existing pending approval state,0020 remains refused, and malformed,
missing, unsupported and corrupted marker cases remain refused even when the
corrupted commit is the declared tested source. The changed old deploy-v0.3.1
expectations follow the existing portfolio-upgrade source gate; explicit legacy
runtime rollback positives preserve that separate behavior.

Source/test review finds CR-03 resolved with no new defect. No compatibility or
database command was run by this reviewer;47 is the inspected matrix's case
count and the executor's reported focused outcome. Campaign3 remains failed at
compatibility despite earlier passing backend/critical/frontend/browser stages.
The in-progress diagnostic tail and final complete security/same-archive proof
remain separate pending evidence. `deploy.sh` is outside UI render inputs;
this delta changes no UI and does not require render recapture.

## Review Scope and Limits

The deployment source-pin/compatibility follow-up reviewed two additional
paths at `74ee5ea`, bringing the exact cumulative listed scope to69 files.
Other concurrently changing diagnostic fixtures are not covered by this head.

Initial explicit runtime/config/tool scope: 61 paths, changes relative to
`7125fec`, at `255c4a0` (runtime bytes last changed at `8cdd175`). This is a
standard change-oriented integration review using source/diffs and surrounding
callers, not a fresh requalification of all historical unchanged implementation.
The two initially unchanged trade-page consumers were followed to establish CR-01;
the follow-up explicitly reviewed their repair plus the new routed regression
file at `6bfb447`. CR-02 follow-up reviewed the eleven-file delta
`203815f..99166d9`, including two strengthened test files added to this cumulative
list, bringing its exact scope to66. The separate35-file fixture review is
retained in `13-17-FIXTURE-REVIEW.md`; those paths are not silently claimed as
another full runtime review here.
The separate 51 changed test paths have per-plan review records; this report
does not claim another comprehensive review of every test. Fallow was disabled
and no structural substrate was supplied.

The pass traced SQL canonical intent and permanent owner/key replay ordering,
onboarding latches and fixed grants, service-bound ownership/CSRF/body bounds,
metadata route leases and unknown-result handling, target/session cache guards,
detail/overview proof sharing, retained/current source and schema binding,
versioned recovery inventory completeness and quarantine, and final security/
same-archive campaign guards. No additional demonstrated issue is reported in
those paths. Prior clean per-plan reviews are evidence of their narrower passes,
not a reason to disregard the combined consumer defect above.

This review ran no database/browser/security/recovery campaign and changed no
source or tests. Plan17 actual final-source qualification remains mandatory.
The previously owner-accepted issue35 picomatch advisory, its narrow checks and
2026-12-17 expiry are retained; no remediation or expanded exception is claimed.
Owner UI/native200 acceptance is a separate human result; the source repair and
its regression evidence resolve CR-01. Changed render inputs require refreshed
source-bound evidence before final qualification. No provider, production,
dependency or publication operation occurred.

_Reviewer: independent gsd-code-reviewer; no commit created._

## Subsequent Test-Only Review — 5dc6c45

Reviewed the23-line public bootstrap wrong-ACL regression. It keeps the real
final authorizer and requires its refusal after canonical preflight/grants,
the exact ACL query, transaction-exit ValueError and connection close. Driver
I/O is mocked using the existing test protocol; no real rollback is claimed
from this unit test. Existing real-driver coverage is retained. No new defect
or oracle weakening found. This adds one explicitly reviewed test path to the
cumulative list (67files); the35-file fixture record remains separately bound.
Verified the focused receipt's committed source and raw-log hashes:
48pass2.84s, module116statements/56branches100%. This reviewer ran no tests.
The prior whole campaign failed at critical coverage and is not relabelled
successful; remaining full security/image/browser/recovery outcomes are pending.
See `13-17-FIXTURE-REVIEW.md` for detailed disposition and measurement limits.

## Security Tail Fixture Review — 531cf48

**Disposition: clean, no new findings.** Independently reviewed the three-file
test-only commit: `test-deploy-prerequisites.py`, `test-dev-bootstrap.py` and
`test-stock-recovery-contracts.py`. The first two add controlled environment
isolation with an explicit ambient-DATABASE_URL refusal and assert the actual
current bootstrap refusal reasons without replacing the authorizer or accepting
repair of unsafe roles/objects. Historical PostgreSQL probes now own a separate
database and select0014 explicitly for their two dividend contracts, preserving
the original financial, catalogue, tamper and fresh-clone assertions.

The historical fixture refuses an existing identity before replacing its saved
state, authenticates the disposable source database/session, drops only the
database it created and newly introduced allowlisted roles, and compares the
original current database's independent dump plus role/membership snapshot after
cleanup. A new preexisting-database negative verifies refusal without mutation.
No current0020 downgrade or historic schema/authority redefinition is introduced.
`test-dev-bootstrap.py` was already in this cumulative list; the two additional
paths bring the exact cumulative scope to71. See the separate fixture report for
the source-bound follow-up details; its original35-file hash remains historical.

This pass ran no tests, database, browser or scan command. The active worker owns
the serial diagnostic lane. The previous whole campaign3 remains failed, and
tail diagnostic success cannot substitute for complete final-source security
and same-archive recovery qualification. No source/runtime/dependency or UI
input changed in this reviewed test-only commit.

## Borrowed Configuration Stack Review — fa28d8e

**Disposition: clean, no new findings.** Reviewed the complete changed wrapper
and its invoked six backend test modules/fixture context. The wrapper now
distinguishes a stack it creates from a complete campaign stack it borrows.
Before using an existing stack it requires exactly the expected two services,
fixed project/configuration/workdir labels, healthy running state, exact pinned
image reference and resolved local image ID, expected loopback port bindings and
test-network membership. A partial, foreign or unhealthy borrowed stack fails
before pytest and has neither an up operation nor cleanup ownership.

The standalone branch alone executes up and down; it also validates the resulting
stack before testing. The finally clause checks the captured ownership flag,
including failure paths, so borrowed containers are not removed after a failed
test or validation. All six existing test modules, argument boundaries, checks,
return-code propagation and timeouts remain. This avoids deleting the current
database needed by later historical probes without weakening the existing136
configuration/health/scheduler assertions. This adds the72nd cumulative path.

This source review ran no tests or Docker command. Executor standalone and
ordered borrowed-stack diagnostics are separate measured evidence, not a full
security pass. Whole final-source security and same-archive recovery remain
pending. No runtime, dependency or UI input changed in this commit.
