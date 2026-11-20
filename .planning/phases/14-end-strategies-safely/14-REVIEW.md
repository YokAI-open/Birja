---
phase: 14-end-strategies-safely
reviewed: 2026-11-20
depth: deep
source_commit: d2e8885b798e00a2932a18524a80d6268f28533c
initial_source_commit: 426435789f8f41dea0b3fe9a4c0852c85b314a46
re_reviewed: 2026-11-20
diff_base: 9527e358bc6953cec7580043703324db194ba396
files_reviewed: 46
files_reviewed_list:
  - backend/alembic/sql/0023_portfolio_closure.sql
  - backend/alembic/versions/0021_portfolio_closure_schema.py
  - backend/alembic/versions/0022_portfolio_closure_provenance.py
  - backend/alembic/versions/0023_portfolio_closure_authority.py
  - backend/app/api/v2/portfolio_management.py
  - backend/app/api/v2/portfolios.py
  - backend/app/api/v2/stock_trades.py
  - backend/app/api/v2/trades.py
  - backend/app/db/dev_bootstrap.py
  - backend/app/db/portfolio_bootstrap.py
  - backend/app/db/portfolio_migrate.py
  - backend/app/db/schema_contract.py
  - backend/app/main.py
  - backend/app/schemas/portfolio_closure.py
  - backend/app/services/corporate_actions.py
  - backend/app/services/dividends.py
  - backend/app/services/event_history.py
  - backend/app/services/history.py
  - backend/app/services/portfolio_closure.py
  - backend/app/services/portfolio_lifecycle.py
  - backend/app/services/portfolios.py
  - backend/app/services/stock_ownership.py
  - backend/app/tasks/dividends.py
  - backend/tests/test_portfolio_closure_critical.py
  - backend/tests/test_stock_quotes.py
  - deploy/backup-snapshot.py
  - deploy/deploy.sh
  - deploy/tests/run-portfolio-campaign.py
  - deploy/tests/run-portfolio-validation.py
  - deploy/tests/test-portfolio-validation-contracts.py
  - deploy/verify-restore.py
  - frontend/src/App.tsx
  - frontend/src/api/client.ts
  - frontend/src/api/portfolioDeletion.ts
  - frontend/src/components/PortfolioDeleteForm.tsx
  - frontend/src/components/PortfolioMetadataForm.tsx
  - frontend/src/components/PortfolioSwitcher.tsx
  - frontend/src/components/PortfolioTargetBoundary.tsx
  - frontend/src/hooks/usePortfolioDeletion.ts
  - frontend/src/hooks/usePortfolioManagement.ts
  - frontend/src/hooks/usePortfolioOverview.ts
  - frontend/src/hooks/usePortfolioTarget.ts
  - frontend/src/lib/portfolioDeletionAttempt.ts
  - frontend/src/lib/portfolioMetadataEvents.ts
  - frontend/src/pages/PortfolioDeletionPage.tsx
  - frontend/src/pages/PortfoliosPage.tsx
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 14: Independent Integrated Code Review

## Narrative Findings (AI reviewer)

This distinct code-review agent reviewed the integrated closure, normal-read,
browser-authority and qualification boundaries from qualified Phase13 source
`9527e358bc6953cec7580043703324db194ba396` to committed source
`426435789f8f41dea0b3fe9a4c0852c85b314a46`. The initial pass found one new
**BLOCKER**; independent re-review at `d2e8885` resolves it, leaving **zero
blockers and zero warnings**. No structural pre-pass
was supplied. This is a code review, separate from the security and UI roles.

The explicit list above records the direct source scope: full new transaction,
transport, hook and runner implementations plus changed hunks and their callers
in retained modules. The broader phase diff has 222 changed paths, including
planning and test artifacts. Prior independent per-plan reports and their
recorded regression evidence supply the complementary historical review; this
report does not claim a fresh line-by-line reread of every retained test or
every unchanged line of the large recovery/administrative-SQL implementations.
Original per-plan findings, repairs, failed attempts and evidence remain in
their original reports and are not renumbered as new findings here.

## Critical Issues

### CR-01: Source inventory follows an escaping ancestor directory link

**Original classification:** BLOCKER. **Disposition:** RESOLVED by independent
re-review at `d2e8885`; original source-trace finding is preserved below.

**Owning implementation plan:** 14-16; relevant integrated threats T-14-16 and
T-14-18. **File:** `deploy/tests/run-portfolio-validation.py:181`, specifically
the path classification and read at lines 197–203.

**Issue:** `security_sources()` asks Git for cached paths and nonignored
additions, then checks `path.is_symlink()` only on each final inventory entry.
For a cached path such as `backend/app/main.py`, replacing an ancestor directory
with a link leaves the final entry itself a regular file: `is_symlink()` is
false, while `is_file()` and `read_bytes()` follow the ancestor. The code reaches
the file read without checking ancestor components or resolved containment.
Git's cached inventory still supplies the descendant pathname even when its
directory was replaced.

Consequently an outside-checkout target is read and hashed as an apparent local
source input, contrary to the function's explicit no-escaping-source-read
contract. A substituted outside tree with identical file bytes can also leave
the snapshot unchanged because ancestor identities/link metadata are absent.
The leaf-link refusal does not cover this case. The checks are also separate
pathname operations, so checking containment alone before a later ordinary
read would retain a link-swap window.

The supervisor's `source_snapshot()` calls this function before launch and
`verify_integrity()` calls it throughout both campaigns. Thus the defect lies
in the final qualification trust boundary, even though no current production
request or actual outside-source read is alleged. This is a newly identified
gap in the current Phase14 source guard, not a relabelling of Plan17's already
resolved packet-input traversal findings.

**Existing regression gap:**
`deploy/tests/test-portfolio-validation-contracts.py:229` tests a direct leaf
link to an outside file, internal leaf-link changes, additions, rename and
ignored credentials. It does not test a linked inventory ancestor, a linked
root or a component replacement between classification and read.

**Concrete fix:** Open the checkout root and walk each inventory parent using
descriptor-relative `O_DIRECTORY | O_NOFOLLOW` opens, rejecting linked parents
before reading a descendant. Read ordinary files through `O_NOFOLLOW` file
descriptors and validate regular-file type with `fstat`; retain the existing
explicit policy for safe leaf-link metadata without reading its target.
Apply equivalent protection to included ignore metadata and ensure the Git
inventory cannot cause an escaping path to be read first. The already reviewed
Plan17 descriptor traversal is a local implementation analog; no dependency
or architectural change is required.

Add synthetic regression cases for escaping and in-root linked ancestors,
linked roots, leaf-link swaps and component replacement, asserting refusal
before any target read and preserving normal tracked/nonignored additions and
ignored-secret exclusions. Run the affected runner/supervisor contracts,
independently review the repair, then freeze the repaired committed source
before the fresh complete security and recovery commands. No whole campaign
has started in this review pass, so no prior final whole receipt is invalidated.

**Proof method:** Direct source/call-chain tracing only. Per the executor's
serial-lane instruction, this reviewer ran no tests, DB, browser, exploit
demonstration or disposable source mutation. The parent was notified before
any source changes were proposed.

## Other Integrated Boundaries Assessed

- **Closure and permanent originals:** The private DELETE route authenticates
  identity/CSRF before bounded streamed parsing. SQL serializes the owner,
  resolves permanent key/body outcomes before mutable state/quota, acquires
  sorted historical instrument gates before root locking, and restarts whole
  discovery on changed instrument membership. The Python service creates its
  transaction-bound proof only after the SQL result, verifies complete retained
  lifecycle/stock evidence, and commits before returning terminal success or
  named refusal. Cancellation and unknown commit transport do not establish
  rollback. The PostgreSQL bigint bound is retained.
- **Financial freeze and chronology:** Closed causal interpretation is
  read-only and separate from financial authority. Existing writer SQL remains
  responsible for its post-lock active checks. Global stock movement/application
  clocks inspect an already-held gate and reject equal/backward terminal time;
  the financial one-instrument marker is not cleared by closure proof.
- **Private final reads:** Initial target resolution remains unlocked to
  preserve instrument-before-root ordering. Normal metadata, History and
  crypto/stock quote/receipt returns obtain final ordered owner-active shared
  locks after hydration or financial service completion. A committed fill may
  therefore return private unavailable after a concurrent closure; the browser
  retains its original unknown attempt and exposes only the approved boolean
  at the unavailable boundary.
- **Browser generations and quarantine:** Durable immutable owner/tab originals
  are stored before send. Root quarantine is synchronous before transport;
  active list presence cannot resolve the current original. Route/session,
  operation and provider generations guard late callbacks. Former-generation
  masks are released only from fresh owned-active membership, while a new
  different unresolved original remains masked. Terminal named refusal and
  exact receipt are the only durable resolution paths. Completion navigation
  rechecks its current receipt; no implicit sibling or automatic DELETE is
  introduced.
- **Management lifetime:** The metadata/deletion host remains outside the
  financial Outlet. Draft/pending metadata and named deletion review exclude
  one another. Private unavailable routes hide ordinary metadata/finance;
  explicit same-ID metadata recovery after terminal refusal remains available.
  The static recovery route contains no original name/key in its URL.
- **Admission and recovery:** Current14 and20/21/22 migration-entry recognizers
  authenticate the finite catalogue/ACL/default state and supplemental objects
  before Alembic child creation. Current23 runtime admission requires final
  authority. Retained0020/0017 sources stay fixed and separate from current
  imports. Current restore requires the original manifest, compares financial,
  schema, lifecycle and identity evidence before regrant, permits only finite
  no-ACL normalization, then rechecks exact authority. Incompatible old-app
  rollback refuses before switching or state changes.
- **One-shot process receipts:** Launch uses a private exclusive directory and
  an irreversible fsynced request claim before preflight/status writes.
  Preflight has its own gated, recorded session. Both preflight and command
  cancellation reap owned process groups; forced termination explicitly leaves
  finalizers/resource cleanup unconfirmed. Status/resume inspect original
  identities and never launch replacements. All seven recovery stages run in
  order with source/archive/image guards before/after, and all three current
  authority triples must match.

## Historical Review and Qualification Limits

The review used the existing Phase14 interfaces, coverage/threat register,
implementation summaries and per-plan independent findings, including the
Plan16 genuine14 transition and supervisor repairs and the final Plan17 packet
disposition. Those artifacts retain their original scope and limitations.
In particular, the earlier diagnostic backend partitions, bounded TLS/cold
checks,139-case preflight and Plan17 captures are not an uninterrupted final
security or same-archive recovery pass.

No whole qualification result is asserted here. Plan18 still requires fresh
literal complete commands at the final reviewed source, actual strict coverage,
audit/image/browser results and independently checked owned cleanup. Plan19's
actual owner UI acceptance and native browser-menu200% result remain pending;
neither can be inferred from automated screenshots or this review.

Only this report was written. No source, package, lockfile, image version,
provider, production, Git commit, global state or unrelated `.claude/` content
was modified by this reviewer. No publication authorization is granted.

## Independent CR-01 Repair Re-review — Resolved

The same distinct code-review agent reviewed RED `407a6c0` and GREEN
`d2e8885b798e00a2932a18524a80d6268f28533c`, limited to the qualification runner
and its existing validation-contract tests. The original aggregate scope and
finding above remain intact. This follow-up did not rerun tests, start a DB,
browser or qualification campaign, or change source.

`source_directory()` opens the absolute root path component by component with
descriptor-relative `O_DIRECTORY | O_NOFOLLOW`. Consequently linked roots,
root ancestors and inventory parent components refuse before a descendant read.
`source_bytes()` classifies the leaf without following links, opens regular
source leaves through `O_NOFOLLOW`, compares descriptor identity with the
classified object, checks regular-file type, reads only that descriptor and
checks identity again afterward. A replaced parent cannot redirect that already
opened descriptor; a subsequent guarded parent reopen also refuses replacement.
The function uses nonblocking open before type validation, avoiding a FIFO wait.

Permitted leaf links supply only their own `readlink` metadata to the hash.
Their target must remain inside the root and have an ordinary-file leaf under
guarded parent traversal; target bytes are never read through the link. The
target parent is reopened and compared before accepting its metadata. Ignore
metadata uses the same reader with leaf links forbidden, and its ancestors are
checked before Git enumeration. The root and ignore contents are checked again
at inventory completion. Existing nonignored additions, leaf-link metadata
binding and ignored-credential exclusions remain present.

The new behavioral regressions cover external and in-root linked parents with
equal target bytes, linked roots/root ancestors before Git, linked ignore
parents before Git, a leaf replaced just before open and a parent replaced
after its descriptor was opened. The last case observes only original source
bytes, explicitly excludes the controlled outside bytes and requires refusal.
These assertions address the actual failure mechanism rather than merely
checking for flag strings. The historical direct-leaf/addition/rename/ignored
credential tests remain intact.

The independently read RED log records four test methods with six failing
subcases at the old source. The final runner/supervisor log records **33 tests
passing in8.250s** and the matching CI-ops log records **94 tests passing
in23.865s**. The image/source log records **22 tests passing in5.684s** before
the final target-directory metadata recheck; no image-binding code changed in
that last refinement, and the final33/94 groups ran at the final bytes. These
are assessed recorded results, not tests independently executed by this reviewer.
Receipts remain under `/tmp/birja-phase14-campaign-plan18-repair/` as
`source-red.log`, `source-frozen.log`, `ci-frozen.log` and `image-final.log`.

This reviewer independently hashed the final files, confirming runner SHA256
`e646fd8e25ca9547142eb2f9e480be3321cdad3ae84ec099d014053c82c8f04b`
and contract-test SHA256
`4dc3836cb535ea8827d139a46a3dae57997f16152956df479adaac264a6f2619`.
No additional concrete defect was established in this scoped re-review.
**CR-01 is resolved; zero remaining blockers and zero warnings.**

Fresh uninterrupted whole security and seven-stage same-archive recovery remain
Plan18 gates at this repaired reviewed source. Current packet verification and
Plan19's actual owner/native200 acceptance remain separate; this disposition
does not claim those outcomes or a hosted CI pass. Only this report changed.

## Final Scoped Repair Review — Coverage and Fresh Test Clocks

This independent follow-up follows the updated defensive-review instructions
in `AGENTS.md` at `fb39f0f`. Scope is the approved Plan18 repair in
`backend/app/services/portfolio_closure.py`,
`backend/tests/test_portfolio_closure_critical.py` and
`backend/tests/test_stock_quotes.py`, including the final working-tree change
after `a21eae3`. The final source commit remains the executor's next step.
The reviewed file hashes are:

- Closure service: `ef21a9be97efdda0989e55cede877ea624ae654f0bdc74984ea118c76703e025`.
- Critical tests: `b2ff646d3e92893ea6f9c156f470ad331ce9f6d707b8728cb695dab747d7433b`.
- Quote tests: `0dfe30ecf6e0bec40d6862f831bab1778b242be9521e711bc5f0fa2d8e6f10cc`.

**Disposition: zero concrete correctness blockers and zero remaining warnings
in this scoped repair.** Original findings and their dispositions above remain
preserved. This review used static analysis and read the recorded isolated
verification; it ran no tests, DB operations, browser or demonstrations.

The loop refactor keeps the same maximum of three total attempts. Only
SQLSTATE40001 can continue, after rollback and counter advancement; other DB
errors, including40P01, leave after the first attempt. The `finally` cleanup
still runs on each attempt. The former unreachable terminal statement is
removed without adding an unlimited retry path.

The private `_validate_closure_result` helper contains the exact existing
returned-field predicates and error. Its call is unconditional on the actual
SQL row fields, before complete closure proof or commit. There is no new
accepted result shape, skipped validation or change to transaction handling.
Its ordinary argument tests cover valid finite outcomes and booleans, target
inequality, unsupported outcome and invalid boolean arguments. The service
path still consumes real SQL results in the existing integration tests.

The real-session guard, bounded server-error retry, retained acknowledgement
and rollback checks remain in the new critical file. The additional unsupported
revision cases are pure validation tests. The final-default timing check reads
through the real driver and verifies rollback restores the original authority
and catalogue. No returned database row is replaced by a fabricated result.
No schema, SQL authority, ACL source, fingerprint, lockfile or image pin is
changed by this repair.

The intermediate quote-test warning **WR-02 — collection-time timestamp
parameters outlive a refreshed test clock — is RESOLVED**. The autouse fixture
refreshes each scenario's wall clock, and all time-dependent parameter values
are now evaluated inside the test against that refreshed clock. Future+1s,
stale120s, exact expiry and prior-date cases therefore retain their intended
meaning after a long collection-to-execution delay. Other module parameter
sites contain no collection-time timestamp values. This preserves the refusal
assertions instead of letting an unrelated stale-time refusal satisfy them.

Recorded evidence assessed under
`/tmp/birja-phase14-campaign-plan18-repair/`:

- `focused-r3.log/json`:69 tests passed in203.06s,209.605s receipt; the existing
  critical/quote repairs and actual quota/first-buy regression complements.
- `focused-r4.log/json`:91 tests passed in297.16s,303.956s receipt. The current
  closure service has63 statements and18 branches,100% coverage with zero
  missing statements/branches; no exclusions were added.
- `focused-r5.log/json`:six bootstrap checks passed in6.59s,12.839s receipt.
- Both final R4/R5 receipts record exit0, unchanged source and empty owned
  container/network/volume inventories.

`pre-r2-coverage-gap-audit-final.json` describes64 critical modules and explicitly
sets `qualification:false`. Its current-service entry uses fresh repair evidence;
unchanged modules retain provenance from R1 plus focused diagnostics. This is
a useful diagnostic of remaining gaps, **not a composite qualification pass**.
The failed R1 whole command remains failed historical evidence.

Fresh uninterrupted all-security, its literal whole critical gate, the complete
seven-stage same-archive recovery, current UI packet verification and Plan19's
actual owner/native200 outcomes remain pending. Neither this scoped approval
nor the focused coverage measurements complete those gates. Only this report
was edited; no source change, commit or global-state update was made here.

## Scoped Current-Service Binding Review — Two Entries

**Zero blockers and zero warnings.** The reviewed working-tree diff on
`7a29129` changes exactly two SHA256 values: the current closure-service entry
in `deploy/backup-snapshot.py` and its matching current entry in
`deploy/verify-restore.py`. Both now equal
`ef21a9be97efdda0989e55cede877ea624ae654f0bdc74984ea118c76703e025`.
This reviewer independently hashed the working-tree service and its accepted
`48aec5b` version; both match that value. The update therefore binds the already
reviewed service repair rather than accepting an unrelated source.

The source-validation loops, required member names, current profile, legacy
bindings, SQL/schema/ACL fingerprints, dependency and image pins remain
unchanged. The preflight's earlier refusal of the stale binding remains valid
failed-history evidence, not a passing long-command result. The recorded four
offline contract logs contain12 fixture,19 recovery,9 package/retained and22
image/source tests passing,62 total; this reviewer read those outputs and did
not independently execute them. Neither changed file is a render input.

Only this report was appended. No source, commit, browser, DB or test operation
was performed by this pass. Whole R2 has not launched; fresh complete security,
same-archive recovery and actual human acceptance remain pending.
