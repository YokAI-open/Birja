# Plan 26 continuation after browser Task 01

The owner approved **Finish local automated validation** on November16. This
authorizes continued local diagnosis and tested fixes through the remaining
automated gates, including additional repair attempts without asking at each
procedural retry limit. Strict gates, new packages/dependencies, provider and
production operations, publication and owner UI/native zoom remain separate.
This is an internal executor handoff, not a user checkpoint.

## Task 01 diagnosis and scope

The original checkpoint and its failed runs remain in12-26-CHECKPOINT.md.
The approved continuation resolved the remaining failures causally:

1. The lost-response test created a sibling after the application's valid
   owner metadata was cached. Seed both roots before the first financial route;
   Phase13's public creation/cache invalidation is not available in Phase12.
2. Mixed dividend tests deliberately appended uncertain instrument-global
   revisions. A healthy poll correctly cannot clear those persistent holds.
   Finish each synthetic scenario using the existing immutable reviewed
   reconciliation mechanism before another test uses AMD. The retained
   dividend `PROGRAM` bytes are unchanged; only the current browser entrypoint
   changed. No financial guard, SQL authority or application data rule changed.
3. The mobile held-event assertion selected the hidden desktop duplicate. It
   now asserts the actual visible responsive event row.
4. The sibling fixture's `SELECT id::text ... ORDER BY id` sorted the text
   result alias lexically. At IDs9/10, a test consequently navigated back to
   the original root while asserting sibling content. Actual trace proved
   both the original URL and absence of any sibling request. Order by
   `accounts.id` and identify the synthetic sibling explicitly by name.
5. Node-only e2e TypeScript cannot type DOM globals in browser callbacks.
   Use the repository's string-evaluation pattern, without changing compiler
   globals or loosening typing. The e2e/node project typecheck passes.
6. Visual inspection caught a screenshot labeled holdings before its query
   completed. Wait for the actual visible AAPL/BTC trade links before capture.
   Every desktop review state now also gets a640x480 CSS-pixel reflow capture,
   rather than asserting200%-equivalent layout only on the unavailable page.

The 320px crypto card min-width/grid repair was inherited from the original
executor and is covered by actual no-overflow assertions across review states.
No portfolio management route/UI, provider call or production operation added.

## Verification and artifacts

Approved continuation probes, in order: focused4 cases3 passed/1 eligibility
failure; focused2 cases1 passed/1 hidden responsive duplicate; full10 cases9
passed/1 lexical-ID fixture failure; full10 cases10 passed; full10 cases10
passed after Node typing repair. The last visual inspection then found the
premature holdings screenshot, so the final packet is regenerated again with
actual loaded holdings and complete desktop-state equivalent reflow. The first
sandbox socket refusal occurred before a stack existed and was not an
application failure. These retries were explicitly authorized; no gate was
skipped to obtain green results.

Task01 committed: **b71a162** (`test(12-26): qualify owned portfolio browser
journeys`). Final actual run passed **10/10 in2.6 minutes**. Its private stage
logs are `/tmp/birja-phase09-browser-cy0ile3j/`; outer progress/cleanup receipt:
`/tmp/phase12-26-task01-accepted-source.log`. All owned resources were cleaned
and checked absent. No source deletion occurred.

Final packet: `/tmp/birja-phase12-ui-review-task01-accepted-source.zip`.
SHA256: `f3809c1efd3453362a57b1828cd3d517ddc91640bae1713fbb4cc2a5dd9b41df`.
Extracted directory with `index.html` and `manifest.json`:
`/tmp/birja-phase12-ui-review-task01-accepted-source/`.
All102 actual HTML/PNG artifact hashes were verified. All248 source hashes in
the manifest match the committed **b71a162** tree, independently checked via
`git show`. Manifest `git_commit` records the pre-task checkout base b3f7473;
its explicit source inventory binds the actual Task01 bytes, including new
files. Directory/ZIP permissions are0500/0600 and artifact permissions0400.

Actual loaded holdings at320/1280 and640-equivalent reflow images were inspected
with view_image after the run: AAPL/BTC figures, asset labels, long-name
wrapping and controls render correctly. The earlier320/1280 crypto preview
images were also inspected. Native200% and owner UI acceptance remain pending;
the directory name does not claim human acceptance. Older partial/preceding
packets are diagnostic history, not the final review packet.

Runner guard contracts:6 tests pass, including provider env removal, owned
resource refusal/cleanup, unsafe mount/provider/port refusal, source-drift and
exclusive inert review exports, and current dividend fixture source binding.
Retained dividend `PROGRAM` byte-equality against HEAD passes.
`frontend/node_modules/.bin/tsc -p frontend/tsconfig.node.json --noEmit` passes.
Full frontend typecheck retains exactly47 pre-existing legacy API/test fixture
signature failures across11 files intended for Plan27; do not claim it passes.

## Task 02 remains unimplemented

No Task02 CI/recovery/runner source has been edited. Read the full12-26 plan,
12-18/17/16 summaries and their real producer/consumer implementations before
editing. Task01 has not completed the whole plan: do not create a completed
26SUMMARY or advance the phase counter until Task02 actually finishes.

- Extend the existing six CI jobs, keeping every original47 critical module
  and adding the new ownership/v2/bootstrap/admission paths at100% branch
  coverage. Keep80% overall, Python/npm audits, and all five actual strict
  unfixed HIGH/CRITICAL image scans. Existing `test-ci-ops.py` has20 contracts
  against the old exact inline recovery graph; update its behavioral/mutation
  contracts to enforce the actual replacement graph rather than deleting gates.
- Create `deploy/tests/run-portfolio-validation.py --suite all-security` and
  `--suite recovery`. The security command graph must invoke the exact checked
  in CI coverage lists, frontend lint/typecheck/coverage, full browser suite,
  both audits and all five actual image commands. Add dry-run exact-order,
  failure-propagation and isolation tests. No new install/upgrade is authorized.
- Use fixed archive `/tmp/birja-phase12-proof/recovery.tar.gz`. Existing
  `verify-restore.synthetic_path` only accepts `/tmp/birja-backup-test-*`.
  Add an explicit bounded exception for the new owned proof directory, with
  private owner/mode/symlink/exclusivity guards; do not widen production defaults.
- `verify-restore.py` already packages and verifies complete fixed-hash
  retained source payloads from `portfolio-sources.py`. Preserve backwards
  compatibility of old immutable archives. Add authenticated successor
  inventory for migration0015/16/17 and both static0017 SQL files, bootstrap
  source and ownership proof tooling; current `CORE` lacks these. Do not
  silently change old archives' required inventory semantics.
- Authenticate the outer archive, current source bytes,
  `portfolio-retained-sources.json`, inner fixed source hashes and recorded
  image Config/RootFS/content IDs before every lane. Existing source helpers
  bind complete immutable v0.5.0/v0.4.0/v0.3.1 and reject changed/reforged
  preexisting image bindings. No rebuilt archive, synthetic Git commit,
  application overlay or retagged source/image authority is acceptable.
- Existing `ops-fixtures.successor_roundtrips` ends at0014. Its roundtrip
  proves retained0007–0014, not current0017. `portfolio-smoke.py` only seeds,
  projects/verifies and compares the live current0017 source using verified
  TLS and restricted roles. **A genuine encrypted cold0017 restore lane is
  still needed**, with the independent pre-backup immutable oracle compared
  after restore, final current application interpretation, original NULL/new2
  digest markers, frozen journal and fixed authority quarantine preserved.
  Do not claim that the retained loop or live source comparison proves this.
- Preserve role/TLS fresh/upgraded parity, selected old-source cutover and
  rollback using that same checksum-pinned archive. Installed restoration
  revokes PUBLIC EXECUTE from exactly10 trusted signatures before quarantine
  grants; preserve Plan17's exact source/current authority contracts.
- Plan26 verifies the graph and its focused contracts. Actual full backend,
  frontend, strict scans and complete source/security/cold-recovery campaign
  qualification belong to Plan27. Plan28 owns owner UI/native200% acceptance.

## Shared checkout boundaries

Keep all work local on `feature/milestone-v1.2`. Do not stage unrelated
`.claude/` or parent Phase7 docs. No branch change, private configuration,
provider/production operation, dependency change or publication.

Parent finished Phase7's already-authorized November16 campaign while this
executor ran. Preserve the current STATE note: campaign consumed, result in
`07-LIVE-20261116-REVIEW.md`; six whole requirements still pending, stock
admissions remain OFF, and no rerun/schedule/fallback is authorized. The live
four-file fence is released, but those modules need no browser-harness edits.

At final closeout, preserve Plan27 legacy typing debt and human gates. Do not
mark whole requirements complete from this harness. Normalize narrow counters
after SDK updates if they overwrite the current phase status/progress format.
