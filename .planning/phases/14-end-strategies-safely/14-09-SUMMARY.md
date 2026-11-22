---
phase: 14-end-strategies-safely
plan: "09"
subsystem: stock-continuity-and-public-concurrency
tags: [postgresql, lifecycle, bigint, concurrency, recovery, portfolio-closure]
requires:
  - phase: 14-08
    provides: Current public closure and frozen financial-event boundaries
  - phase: 14-11
    provides: Original-identity browser recovery and bigint contract observation
provides:
  - Public multi-stock/sold-out closure with immutable historical evidence and active sibling continuity
  - Actual blocked-PID financial, split, management and creation commit-order proofs
  - Canonical PostgreSQL bigint closure identity and exactly rebound current0023 authority
affects: [14-10, 14-12, 14-15, 14-16, 14-18, critical-coverage]
tech-stack:
  added: []
  patterns:
    - Actual PostgreSQL soft blocker chains establish queued request order
    - Current authority hashes are measured from authenticated source-created databases
key-files:
  created:
    - backend/tests/test_portfolio_closure_races.py
    - .planning/phases/14-end-strategies-safely/14-09-BINDINGS.json
  modified:
    - backend/tests/portfolio_closure_fixtures.py
    - backend/tests/test_portfolio_closure_stocks.py
    - backend/tests/test_portfolio_splits.py
    - backend/tests/test_portfolio_closure_api.py
    - backend/app/services/portfolio_closure.py
    - backend/alembic/sql/0023_portfolio_closure.sql
    - backend/alembic/versions/0023_portfolio_closure_authority.py
    - backend/app/db/portfolio_bootstrap.py
    - backend/app/db/portfolio_migrate.py
    - deploy/backup-snapshot.py
    - deploy/verify-restore.py
    - deploy/db/bootstrap-roles.sql
    - deploy/deploy.sh
    - deploy/tests/fixtures/portfolio-recovery-0023.json
key-decisions:
  - Preserve the existing canonical bigint-string client contract through PostgreSQL maximum bigint.
  - Keep same-date split alias and historical ordering guards; qualify distinct chronological fixtures instead.
  - Preserve qualified0017/0020 profiles and archives; repin only authenticated current0023 authority.
requirements-completed: []
requirements-progress: [PMGT-03, PMGT-04, PMGT-05, PFIN-05, PFIN-06]
duration: 30min measured first-RED-receipt-to-cleanup interval
completed: 2026-11-19
---

# Phase 14 Plan 09: Stock Continuity and Public Commit Orders

**Publicly deleted strategies retain exact stock evidence while active siblings
continue accounting; real lock races preserve captured roots, grants, fills and
terminal outcomes, including canonical bigint identities.**

## Commits

| Scope | Commit | Evidence |
|---|---|---|
|Prerequisite RED|ed9d932|Public creation above2^53 succeeds but public DELETE returns503; actual9.407s failing receipt|
|Prerequisite GREEN|5d0558b|Minimal Python/SQL bigint correction and exact measured current0023 producer/consumer/deploy binding updates|
|Task1|03af1f2|Public stock continuity and current0023 retained split fixture;13 closure-stock and12 split cases verified separately|
|Task2|119533f|11 real race cases plus strengthened literal global tails; final21-case race/identity/dividend overlap run passes|

First RED receipt:2026-11-19T12:54:07UTC. Owned cleanup completed around13:24UTC.
This measured interval includes implementation and diagnostics, not a routine
feedback-latency promise. Parent owns STATE/ROADMAP; no whole requirement is
marked complete by this plan.

## Proven behavior

- All target roots are publicly created. Historical stock openings are declared
  synthetic fixture prehistory under actual instrument gates. Selling out and
  deletion use the actual authenticated production HTTP paths and restricted
  database role. No privileged close shortcut creates acceptance evidence.
- Multi-instrument roots retain exact global tails, including sold-out stock
  and a zero-position owner. The independent expected tails are6 and2. Frozen
  reconstruction retains its closure epoch while an active sibling and another
  owner receive a subsequent split, conserve basis40/30, and retain historical
  dividend eligibility4/3. Root-only snapshots preserve original fills, facts,
  grants, causal rows and closure evidence as shared global objects advance.
- A separate current0023 public-closure case proves two successive distinct-day
  split epochs, active quantity4→8→16 with basis40, once-only applications and
  byte/value-identical closed holdings and causes. Existing corrupt-lineage
  rollback and single-financial-instrument guards remain enforced.
- Closed market sessions, a stale quote and expired/unknown action status do not
  prevent a valid closure. Closure requires valid lineage, without introducing
  a fresh-price or live-provider prerequisite.
- Independent owners with reversed physical stock insertion order close under
  sorted real instrument gates. Exact tails/epochs and immutable duplicate
  acknowledgements are checked; user-row serialization does not mask this case.
- A genuine first public stock buy holds its real instrument/root transaction
  while public deletion discovers an empty stock inventory. The observed root
  wait produces actual40001, exactly two complete closure SQL invocations,
  rediscovery and one committed closure. Cash9898, quantity1, basis102 and one
  grant per original root remain exact.
- Crypto fill-first yields cash9899.50, quantity1 and basis100.50 before closure.
  Stock fill-first is covered by the public first-buy case. Closure-first stock
  and crypto writers queue on the captured original root and return404 after
  deletion; independent sibling trading cannot alter the frozen book.
- Split-first and close-first instrument waits produce respectively frozen
  quantity4 or2, basis20 and closure epoch1 or0. The active sibling receives
  quantity8/basis40 once. Existing dividend/positive-correction real lock-order
  proofs also pass in both orders, with exact financial outcomes.
- Create/delete races at active-cap10 preserve exact grants/counts. Close-first
  permits a fresh case-insensitive name and slot with a different ID,11 retained
  roots/grants totaling110000 and10 active roots. Create-first is refused,
  deletion leaves9 active roots, and the old creation key cannot resurrect its
  deleted original. Rename/delete races retain the original terminal refusal or
  successful close on replay, without substituting current metadata or IDs.
- Every race observes genuine PostgreSQL blocked PIDs, including soft blockers
  behind the first queued request. Async events only pause an actual writer
  after its real lock/work; they do not substitute financial writes or SQL locks.
  Bounded waits, request deadlines and task cleanup prevent abandoned writers.
  The already-qualified public API suite also proves actual lock timeout503 and
  successful original retry under its six-second request deadline.

## Bigint prerequisite and exact authority provenance

The existing client/API contract accepts canonical decimal strings through
9223372036854775807. Python closure validation and its SQL definer incorrectly
capped IDs at9007199254740991. Real RED reproduced public create201/delete503.
Both owner and portfolio IDs now follow the existing bigint contract; PostgreSQL
argument types impose SQL's upper bound and positive/null checks remain intact.
The public tests cover root>2^53, owner+root>2^53, max-bigint root, replay, and
existing negative/zero/noncanonical/out-of-range path refusal without mutation.

Parent explicitly authorized this local prerequisite and the coordinated repair
of the still-unmerged0023 authority. No historical profile or allowlist was
broadened. Exact old→new file SHA256 values for all11 repair files are retained
in `14-09-BINDINGS.json` (before=ed9d932, after=5d0558b).

| Binding | Before | Authenticated measured replacement |
|---|---|---|
|0023 SQL|1da9076cc99e36c2eb264dcf0801e3752d0329c5e7f54fd4a358e7ea8c3c8949|59577ba16c9e9ea9740c2cb0d171b7006931bb6b1b9e5d0408c9a6f673f7c920|
|0023 catalogue|3a7e0dbe6a908890a1e0e493aa025938b8f03dbd84cf5f799ea0a1895dc164ec|59aeeee9428fac73f96143cc8afdd77e3b6a8f81b30ed37b752666579d69a66e|
|Producer normal authority|0d9a2bfef268be0f226e02e7f1329961259fcabe015218cdb6a8149df60195b9|62e3776654a98a62bf605355e209884b32ff1247fec463d6b923f48a76f42492|
|Producer quarantine authority|dac8876fadcf8f8ee73af4ed41fbeb047882a6b8cb2674566edb09be00680a2f|19c82c874e5f6362500ca4b37df367795ffc6db3cc617502b59bd20057dee399|

The catalogue was measured from an authenticated `session_user=birja_migrator`
source-created0023 database. Function-definition SHA256 is
59df3a9c8444bd14bb287c5ad538598a9f8a45cd46f33fb3eb6b01a470269044.
Schema fingerprint64dc79e1add352d2cb53486ff2f1cce86d40e9540ad25a980c6dc07003da7d4e,
initial ACL6dfc328bda8577360c8a2994cd5c1c00bd1cae1cbd542be6c1b3a0f3c4f71d76
and final ACL71896f41a9310ada0af0961b78e78f5364654f1513c11bf9310c250ad545f748
remain unchanged. Exact current source pins, production SQL catalogue expectation,
development0023 manifest fixture and deploy CLOSURE_PINS were updated together.

## Actual verification

Raw synthetic commands/logs/JSON receipts: `/tmp/birja-phase14-plan09/`.
All database work ran serially on exclusively owned `birja-p14-09`, existing
test image, current0023, fake prices and console email, without repository.env.

| Receipt / command scope | Actual result | Wall/test seconds |
|---|---|---|
|bigint-red|Expected failure: public DELETE503 after valid create201|9.407/7.60|
|bigint-green2|3 real bigint HTTP cases pass|21.291/19.53|
|admission|7 fresh/upgraded SQL/Python parity, closed-evidence, quarantine and historical-literal cases pass|36.075/34.73|
|bigint-qualified: closure API + portfolio migrator + closure migrations|62 pass, one retained runpy warning|240.448/238.59|
|producer-proof2|Actual producer/fixture,24 identity tails and authority/tail corruption refusals pass|7.665|
|logical-restore|Source database destroyed;31 tables,24 tails,4 pregrant tamper refusals, exact oracle/identities/replay outcomes pass|28.241|
|Offline portfolio-recovery-contracts.py|17 unittest cases pass|4.197 test|
|Offline portfolio-management-recovery.py|9 retained contract cases pass|15.650 test|
|task1|13 closure-stock cases pass before retained split fixture setup error; not a complete combined-suite pass|109.243/107.56|
|splits|All12 affected retained split cases pass on current0023|77.347/75.70|
|management|4 actual management overlap cases pass|27.925/26.24|
|task2-qualified|All11 new races,6 original identity cases and4 actual dividend/correction overlap cases pass together|133.568/131.74|
|terminal-tails|Final literal expected global-tail strengthening passes|9.954/8.30|
|Scoped Ruff, format check, mypy service, git diff --check|Pass|See individual receipts|

Source-owned producer/logical-consumer proof bodies were loaded from the actual
recovery test source. A private launcher verified the owned Docker project label
and changed only hardcoded project/artifact names05/06→09; production producer,
consumer, fixtures and checks remained real. Source SHA and exact replacements
are recorded in `proof-source-producer.json` and `proof-source-consumer.json`.
The logical restore is explicitly neither encrypted nor verified-TLS proof.
No combined whole-phase, image scan, cold encrypted recovery or live acceptance
claim is made here; those qualification gates remain later plans.

## Deviations and diagnostics

1. **[Rule1 - Bug, explicitly parent-authorized] Bigint contract repair.** Real
   public RED isolated Python's cap, then actual SQL reproduced the same cap.
   Minimal bounds and exactly measured current authority/source bindings were
   repaired in5d0558b. Historical0015–0020 SQL/migrations and qualified0017/0020
   fixture/profile assets are unchanged; git comparison confirms no edits.
2. **[Rule3 - Blocking fixture] Owned retained split fixture used old0020.** Its
   adapter now uses the existing current0023 public API fixture, real public
   empty-root close and instrument gate before declared opening history. The
   original tests still exercise actual SQL/scheduler arithmetic and refusals.
3. Initial new action fixtures correctly hit ordering and suspected same-date
   alias guards. Sold-out current fills now precede a measured current-time split;
   two-epoch acceptance uses distinct historical event dates on the separate
   no-current-fill scenario. No guard, clock or alias acceptance was weakened.
4. Initial observation seams/assumptions were corrected to the execution path's
   actual account lock and actual soft blocking PID chain. Failed attempts remain
   retained as failed receipts; they are not counted as successful qualification.

## Cleanup and handoff

- Owned Compose project09 was removed with `down -v`; label-filtered container,
  volume and network inventories are empty. No other project was stopped.
- Qualified Phase13 `/tmp/birja-phase13-proof/recovery.tar.gz` remains unchanged:
  SHA2566fb79a45ddcb10725b18fc756e71bd555c827a6e61a5a4a0bd2d183096114b92.
  All retained source archives were preserved. No new canonical Phase14 recovery
  archive was published by this plan.
- Parent independently reviews this expanded authority/binding scope before12.
  Plan10 privacy audit should retain the canonical bigint range. Plan15 still
  owns the known unowned `test_portfolio_creation.py` old0020/current-admission
  fixture mismatch; this plan neither fixes nor waives it.
- Plan16/18 must bind and qualify the final complete current source, encrypted
  same-archive/TLS recovery, critical coverage, whole suites and strict security
  gates. Issue35 scope/expiry is unchanged; no package or image changed.
- No new UI is introduced, no owner acceptance is synthesized, no provider or
  production operation occurred, and nothing was pushed or merged.
- No implementation stubs or new unmodeled network/auth/schema trust surface
  were introduced. Requirements remain progressing until integrated evidence.

## Self-Check: PASSED

All owned created/modified files exist; REDed9d932, GREEN5d0558b, Task103af1f2
and Task2119533f exist in git. Exact source-binding records match committed files.
Only the pre-existing untracked.claude directory is outside this plan's changes.
