---
phase: 10-dividend-cash-and-event-history
plan: "05"
subsystem: testing
tags: [postgresql, dividends, restricted-sql, tls, recovery]
requires:
  - phase: 10-02
    provides: Restricted dividend SQL accounting authority
  - phase: 10-04
    provides: Exact0014 recovery authority and quarantined clone validation
provides:
  - Genuine restricted scheduler dividend SQL and observed account-wait races
  - Exact source/clone financial fingerprints without restored financial execution
  - Fresh0014 and populated0013-to0014 verified TLS accounting proof
affects: [10-06, 10-07, 10-10, phase-verification]
tech-stack:
  added: []
  patterns: [synthetic external evidence with actual SQL effects, immutable clone read verification]
key-files:
  created: [deploy/tests/dividend-execution-fixture.py]
  modified: [deploy/tests/ops-fixtures.py, deploy/tests/test-db-operations.sh, deploy/tests/test-restore-safety.sh]
key-decisions:
  - Reserve AMD independently of the older resolution/stock fixtures and run TLS dividend setup after their consumers.
  - Prove0013 entitlement survival in the focused source/clone and retained successor paths; TLS creates its dividend cases after migration.
  - Restored app and scheduler execution stays quarantined; verify immutable saved rows instead of granting financial execution for replay.
requirements-completed: []
requirements-supported: [DIV-03, DIV-04, DIV-05]
duration: 36min measured-proof-window
completed: 2026-11-13
---

# Phase10 Plan05: Genuine dividend SQL, recovery and TLS proof

**Restricted scheduler SQL credits originals and linked corrections exactly once, including sold historical ownership, uncertain terms and real shared-cash deficits; restored accounting remains immutable and quarantined.**

## Accomplishments

- Added a network-free AMD fixture whose external announcements, permissions,
  calendar evidence, opening ownership and reviewed reconciliation are explicitly
  synthetic. Successful payments and adjustments always call the actual four-argument
  `apply_stock_dividend` as the restricted scheduler; unknown-term decisions call
  the actual `record_stock_dividend_hold`. There is no administrative cash UPDATE
  or mocked successful financial result.
- Actual producer-shaped ordinary revisions retain `verified_cutoff=NULL`.
  Production entitlement derivation uses the reviewed package calendar for historical
  cutoffs and consistent opening/fill journal rows. Only the current day has an
  explicitly synthetic open session, following the established runtime fixture;
  historical eligibility never uses an invented opening-time fallback.
- Proved original credit/replay, positive and negative A→B→A corrections,
  verified no-change, and a genuine zero original from zero historical ownership
  with a positive declared rate. The fixture asserts exactly two original rows
  and nine linked decision rows after duplicate invocations.
- The real app stock service sells all AMD shares after the historical cutoff;
  the due original still credits the earlier eligible quantity. The real crypto
  service spends shared cash, a negative dividend correction is held unaffordable,
  and a real crypto sale funds one linked successful successor. No financial
  balance is manufactured to make these cases pass.
- Paid A→cancelled B has no latest verified entitlement. One deduplicated hold
  applies zero cash while desired total, proposed delta and entitlement remain
  NULL. Full-history reviewed reconciliation permits one supported successor;
  the complete original payment row and original replay remain unchanged.
- `pg_blocking_pids` proves the scheduler is genuinely blocked behind an Account
  row lock. Rights and current revision changes before releasing that lock each
  cause SQL22023 with an identical financial fingerprint. Restored verified
  authority then permits one application and duplicate replay. The probe is bounded
  and adds no monitoring privilege.
- App execution of both dividend entry points is denied. Both runtime roles
  are denied private helper execution, immutable table mutation, migration role
  escalation, DDL and function replacement; scheduler direct cash UPDATE is denied.
- Added complete0014 retained dispatch, source/fresh role authority parity and
  source/restored financial fingerprints. Clones receive CONNECT only for the
  verification clients: app/scheduler financial functions and cash mutation remain
  denied, and exact manifest/fingerprint equality holds before and after probes.

## Verification

| Proof | Actual result | Evidence |
|---|---|---|
| Final AMD0013 entitlement→restricted0014 migration→actual SQL→direct dump/restore clone | PASS36.512s; exact predecessor entitlement hash, financial equality and unchanged quarantined clone | `/tmp/birja-phase10-05-source-clone-final.log` |
| Restricted source roles, populated/fresh authority parity | PASS192.187s segment,63 denied operations; its following TLS invocation failed on a fixture date collision and is not claimed as a green combined run | `/tmp/birja-phase10-05-roles-final.log` |
| Final populated0013→0014 TLS lane | PASS136.777s | `/tmp/birja-phase10-05-tls-amd.log` |
| Final fresh0014 TLS lane | PASS133.869s; exact action/execution/dividend authority parity with populated lane | Same paired TLS log |
| Restore safety | 6/6 PASS1.402s | `/tmp/birja-phase10-05-safety-final.log` |
| Python wrapper and embedded program | Compile and scoped Ruff F PASS | Final local commands |
| Shell syntax and whitespace | PASS | `bash -n`, `git diff --check` |

Both TLS lanes preserve every earlier action, ownership, reviewed resolution,
calendar, execution and actual stock/crypto service consumer. They execute actual
dividend originals/corrections/holds and account-wait races over verified TLS,
then actually reject bad CA, wrong hostname and plaintext access. Existing service
credential/mount isolation, internal network and renewal proofs also pass.
Fresh TLS provisions canonical roles before the restricted migration chain;
populated TLS upgrades0013 with its real legacy account/trade data. Dividend
setup follows the older consumers in both TLS lanes. Pre-existing entitlement
survival is specifically proved in the focused lane and wired into retained0014,
not claimed to be the TLS setup.

Final recorded financial fingerprints:

- Source/clone AMD ledger: `662abb0caaff9069c2761a2298fd19fc99f216928a01d7b16b074936e4291610`.
- Unchanged0013 predecessor entitlements: `3505d5de390b8193fd9127bc20a3f4c66f6a54b86f075bb06c4f0d84590c4cc4`.
- Populated TLS AMD ledger: `1915b4465bbac99b77407a51b44d709bc39062b9110b122430a5612d437c7f65`.
- Fresh TLS AMD ledger: `545bdce8fc80bef8deb1fbc6e10d1114aae71d2e532bcee0b0efa8ca596a584c`.

Saved evidence integrity:

- Source/clone log SHA256: `a3f8c109d30f085596714a7f1a2dc0c97c3e873289f1186cbea3fcc580f88e54`.
- Paired TLS log SHA256: `d54370b357201750df97f3547dc0c7ebaa65d487a186c721fb307c1595428ca7`.
- Roles-segment log SHA256: `808afc3898d89010fe76ff6fa1fa6beea49e5a9a752e7774c90b0eb9437d9450`.
- Restore-safety log SHA256: `23a60a7ce6d2775de3502e8c292e66595d844cb5a169f4c41c68c2a7d4cccdfc`.
- Fixture source SHA256: `d7d202b714d923626264868eed5f68d2802bde71504496cf87dca7b67e22e7aa`.
- Ops driver SHA256: `9c94238e2c047128729564136cb64fd861176fe5c5fb32c85a8d1b78de7ac022`.

The focused clone proof uses genuine `pg_dump --no-owner --no-acl` and the actual
restorer, without a restic archive transport. Full retained same-archive `--all`
is implemented in dispatch but **has not run in this plan** and remains mandatory
Plan06 work. No archive hash or full retained success is invented. Application
source and images did not change; no new backend/frontend coverage percentage or
fresh image scan is claimed here. Final phase gates remain mandatory.

## Commits

1. `f481694` — test(10-05): prove restricted dividend accounting and retained replay.
2. `fdd1c2a` — test(10-05): verify fresh and upgraded dividend TLS parity.

## Deviations and observed failures

Fixture-only compatibility fixes, within the planned test ownership:

- Existing current-head0013 assertions and the execution-authority validator's
  implicit0013 default failed against0014. Use the actual revision and preserve
  full authority validation. Initial integration failures remain in
  `/tmp/birja-phase10-05-roles-red.log` and `roles-first.log`.
- Initial synthetic event identity violated the existing UUID constraint;
  corrected the fixture identity. A zero declared rate was correctly held as
  unverified; replaced that invalid assumption with real zero historical ownership
  and a positive rate. No runtime gate was weakened.
- Restricted roles cannot inspect another role's detailed `pg_stat_activity`
  wait metadata. Replaced that observation with actual public blocker-graph checks;
  added no monitoring grant.
- Full calendar fixtures exposed hardcoded session-day collisions in existing
  ACL/identity probes. Use unused dates and returned IDs while preserving exact
  identity advancement. An initial missing explicit SQL alias was reproduced by
  a read-only query on owned PostgreSQL and corrected. Failed TLS logs are retained
  as `/tmp/birja-phase10-05-tls.log`, `tls-final.log`, and `tls-final2.log`.
- The older resolution scenario owns NVDA. Its real authority refused conflicting
  new setup. Reserve AMD and initialize it after all older TLS consumers;
  `/tmp/birja-phase10-05-tls-final2.log` records the failed collision, and final
  paired evidence records every old consumer passing. Refresh synthetic quote
  and action observations before the stock sale so long setup cannot stale them.
- The current schema-contract inventory test still named0013; update its exact
  revision list through0014, preserve reading old inventories without contract
  metadata, and reject an incomplete current inventory.

These are observed development/integration failures, not separately committed
TDD RED gates. The plan is `type: execute` and adds proof fixtures; no successful
financial effect was simulated. No production/runtime defect was repaired here.

## Threat and scope results

T-10-05-01/02: actual constrained SQL, role denials, immutable original/linked
history, real wait races and clone financial quarantine pass. T-10-05-03:
fixed test projects, bounded clients/race loops and serial finally-cleanup pass.
T-10-05-SC: no package/install/lockfile/image changes. Both ops and TLS projects
are cleaned up. No `.env`, provider access, private credentials, B2, timer,
installed production tool, deployment or publication action occurred.

Stub scan: none. Synthetic external/review/calendar inputs are deliberate test
evidence, not placeholders for successful financial operations. No new product
endpoint, authentication path, schema or production trust boundary was introduced.

Requirements DIV-03/04/05 are supported by these proof artifacts, not marked
complete: retained Plan06, application consumers, History and final phase
verification remain downstream. Existing live/provider deferrals remain intact.
Canonical STATE/ROADMAP/requirement updates are owned by the parent orchestrator.

## Self-Check: PASSED

All four planned test files and this summary exist. Commits `f481694` and
`fdd1c2a` exist; neither deletes tracked files. Final source hashes match the
recorded evidence. Docker confirms no remaining ops-project containers, volumes
or networks. Only the unrelated `.claude/` directory remains untracked and is
preserved. The measured fixture window is09:22:54–09:58:28UTC; this excludes
earlier reading/setup rather than inventing a total agent start time.
