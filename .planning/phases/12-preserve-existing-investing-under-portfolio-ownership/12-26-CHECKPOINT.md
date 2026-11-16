# Plan 12-26 repair checkpoint

Status: **incomplete**. Task 01 has no completion commit; task 02 has not
started. Phase progress remains 25/28. This is a repair-budget checkpoint,
not a phase summary or a passing UI acceptance record.

## Actual verification

- `python3 deploy/tests/test-portfolio-browser-contracts.py`: 5 passing
  behavioral guard/artifact contracts, including a fresh repeat at handoff.
  These mocked subprocess contracts are not browser proof.
- A real owned Docker/Chromium migrated-login probe passed. The first full
  ten-case run passed 7/10; a focused diagnostic run passed 2/3. The latest
  expanded full run passed **5/10**, with failures detailed below.
- Latest exact command:
  `python3 deploy/tests/run-stock-browser.py --suite portfolios --review-dir /tmp/birja-phase12-ui-review-plan26-final`.
- Latest browser log:
  `/tmp/birja-phase09-browser-sw9zq3hy/browser-portfolios.log`;
  outer log `/tmp/phase12-26-browser-final.log`.
- The runner's cleanup stage completed after that campaign. A fresh direct
  Docker inspection during handoff was denied by socket permissions, so it
  supplies no additional independent cleanup evidence.
- Actual migrated authentication/reused-browser owner switch, both scoped
  asset fills/receipts, zero/many legacy-entry refusal, and mixed dividend
  correction original-row focus pass in the latest run.

## Remaining failures

1. Lost actual response journey: after committed original-root fill with its
   first response aborted, navigation to the synthetic sibling displays
   `Portfolio unavailable` rather than the sibling label. The fixture currently
   creates that sibling after owner metadata was already cached. Refreshing
   qualified metadata or creating the sibling before the first financial page
   is a diagnosis candidate, not an applied or verified repair.
2. Delayed original-root statement journey: after navigation through Markets,
   a manually dispatched `pushState`/`popstate` changes the URL, but the expected
   sibling view does not reliably mount. A focused run previously passed;
   the full run fails. Inspect actual BrowserRouter navigation and committed
   target activation before attributing this to either product or fixture.
3. All three expanded review journeys reach their real crypto/stock/holdings/
   History snapshots, then the real dividend fixture `seed ... AMD` fails its
   eligible-quantity assertion in `dividend-execution-fixture.py` around line597.
   The earlier mixed AMD journey succeeds. Shared instrument uncertainty or
   ownership-journal state across cases is suspected, not proven. Preserve the
   SQL entitlement authority; do not replace these with invented UI records.

Both navigation failures are `expect(locator).toBeVisible() failed`, locator
`getByText('Sibling strategy', { exact: true }).first()`, timeout5000ms, at
spec lines259 and325. The first actual DOM is `Portfolio unavailable`; the
second retains the original `My portfolio` navigation/loading view. Both first
click the actual Markets link and wait for its heading, then invoke `inApp`
(`pushState` with `usr`, random `key`, incremented `idx`, then `PopStateEvent`).
The URL assertion passes; no request-level causal trace has yet been analyzed,
so request ordering/refetch behavior is not established. Error-context and
trace ZIP paths are recorded in the browser log under `frontend/test-results/`.
All review failures are the actual subprocess command's `AssertionError` at
`assert any(...)` inside dividend entitlement derivation; no eligible-row
reason has yet been printed or verified.

The actual 320px probe previously identified an implicit 380px crypto-ticket
grid column. The current bounded source repair adds `grid-cols-1` and
`min-w-0` to the existing layout. The latest 320px journey advances through
those surfaces without an overflow failure, but the full review journey still
fails at dividend seeding. No completed final manifest/index/ZIP exists.
Partial HTML/PNG files in the review directory are diagnostic artifacts only.
Native 200% zoom and owner UI acceptance remain pending. The final320/1280
captures have not received the required visual inspection.

## Preserved work

Uncommitted task01 changes: `deploy/tests/run-stock-browser.py`,
`deploy/tests/dividend-execution-fixture.py`,
`frontend/e2e/stock-trade-fixture.py`,
`frontend/e2e/portfolio-browser-fixture.py`,
`frontend/e2e/portfolio-ownership.spec.ts`,
`deploy/tests/test-portfolio-browser-contracts.py`, and
`frontend/src/pages/TradePage.tsx`.

The isolated runner uses actual0014-to0017 migration, synthetic restricted-role
setup and actual application pages/API transactions, with fake provider input
at the existing process boundary. Retained dividend `PROGRAM` is unchanged.
Review export strips scripts and embeds actual rendered CSS/fonts; its guard
tests reject source drift, unsafe output paths and nonexclusive output.
The source inventory still needs to bind the current dividend browser fixture
before final evidence regeneration.

No CI/workflow/recovery-bundle/validation-runner task02 changes have been made.
Task02 must preserve all six jobs, the original47 critical modules plus new
ownership/v2/bootstrap/schema-admission modules at100% branch coverage,80%
overall, both dependency audits and all five actual strict unfixed high/critical
image scans. Its fixed archive is
`/tmp/birja-phase12-proof/recovery.tar.gz`; every current/retained/TLS/rollback
stage must authenticate the same archive, retained source inventory and image
identities. The new runner's exact command/order/isolation contracts remain
unimplemented. Existing archive path guards currently expect the older
`birja-backup-test-*` directory and need an explicit bounded adaptation;
current cold recovery must not be substituted by a retained-only roundtrip.
No production, provider, dependency, push, merge or branch action occurred.
Unrelated `.claude/` remains untouched. Do not mark requirements complete.

## Resume boundary

The executor's three-attempt repair limit has been reached. Obtain the required
targeted diagnosis/retry disposition before another repair campaign. Preserve
all five failing tests and strict gates. Once task01 actually passes, regenerate
the entire source-bound packet, visually inspect320/1280 images, commit task01,
then implement task02. Full source/security/cold-recovery qualification remains
Plan27; owner UI/native zoom gates remain Plan28.
