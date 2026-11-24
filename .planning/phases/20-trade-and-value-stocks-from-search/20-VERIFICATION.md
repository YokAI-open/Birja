---
phase: 20-trade-and-value-stocks-from-search
verified: 2026-11-24T22:55:50Z
status: passed
score: 10/10 must-haves verified
overrides_applied: 0
runtime: c842b9f85490fe0967963fe4f36639ac6fba5c20
deferred:
  - truth: Complete live exchange directory coverage and verify expanded quote access and data rights.
    addressed_in: Phase 21
    evidence: The production out-of-list stock round trip needs the open Phase 19 directory and quote gates and admitted reference, display, financial, action and backup scope.
  - truth: Pass release CI, approve rollout and demonstrate a production buy and sell with live IEX data outside the original 20.
    addressed_in: Phase 21
    evidence: Roadmap criteria 2 and 3 require the release checks and live production flow.
---

# Phase 20 verification

The code and isolated integration evidence support the Phase 20 goal of trading and valuing eligible stocks found through search, with bounded quote and corporate-action work. The result applies to admitted synthetic inputs. The Phase 21 handoff retains the full-suite coverage gates, approved rollout and live acceptance. [Roadmap](../../ROADMAP.md) · [Plan 09](20-09-PLAN.md)

## Observable truths

The first three rows are the roadmap criteria. The remaining rows consolidate the distinct plan must-haves.

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | Users can buy and sell a newly onboarded common stock, see the correct position and cash, and refresh only selected or held stocks. | Verified | Chromium searched for FQZT and bought two shares. The owned API returned cash of $9,791.75, quantity 2 and basis of $208.25. Selling both returned cash of $9,993.75 and no holding. The fixture observed only FQZT provider demand. The quote cycle coalesces selected requests with a paged positive-holding query and reserves the shared account budget before fetching. |
| 2 | Closed stocks show their latest permitted marks and local opening countdown. Missing marks leave valuation visibly incomplete. | Verified | The browser observed an indicated closed session and the $102.00 SQL mark with empty quote cache in both Markets and the owned ticket. Expiring the mark removed the price and kept the opening countdown. Quantity remained an editable draft and no operation was submitted. Portfolio reads scoped marks twice and feeds only valid marks into the completeness calculation. |
| 3 | Ordinary dividends and supported splits apply once to affected active portfolios. Ticker changes, restart and uncertain events preserve identity, balances and History. | Verified | The restricted-role SQL functions bind the original issue and entitlement, fence corrections and record immutable split movements. Action ingestion advances admitted coverage and applies effects through the standard worker. Browser History displayed posted dividend and split effects, and retained the original fill link after ticker reuse. The paired recovery replay reproduced exact cash, holdings and payments and retained original effect identities. |
| 4 | An admitted issue has one permanent financial identity. Conflicting listings and crypto tickers cannot borrow that identity. | Verified | Migration 0026 creates a one-to-one coin binding with a composite reference to the listing and issue. The migrator-only promotion command matches the approved listing and provider scope before changing the current listing on an existing binding. The internal representation is excluded from user holdings and history labels. |
| 5 | New fills recheck exact identity, permission, session, report, quote units and action evidence before commit. | Verified | The owned route requires an active portfolio and signed preview. The service checks the database clock after the portfolio lock and calls the final SQL assertion before commit. The halted and stale browser states displayed no submit controls. The affected backend run also exercised expiry during a tentative fill with rollback. |
| 6 | Repricing needs explicit reconfirmation and receipt recovery replays a committed result without booking another fill. | Verified | Chromium saw a 409 replacement preview, required a second confirmation, discarded the committed response and recovered the same receipt from the owned read-only lookup. The backend tests verified a definitive missing result after preview expiry, preserving cash and trade count. |
| 7 | Action coverage gates the first fill. Unsupported or unresolved actions remain scoped, and frozen portfolios stay unchanged. | Verified | Action authority and cursor records bind exact listing and admission. Posting depends on current coverage and journal origin. The scoped ingest tests exercise first-seen pre-journal events, holds, renewal and replay. SQL tests exercise fractional split refusal and original entitlement after rename. |
| 8 | The UI carries the stable issue across Markets, ticket, Portfolio and History, preserving private ownership and usable layout. | Verified | The stable route is a child of the owned portfolio route. Markets and Portfolio supply the catalog ID, and History links from original catalog event evidence. Chromium exercised keyboard selection, focus on the original receipt, another user's denial, and reflow at 390px and 640px. Native desktop zoom remains unmeasured. |
| 9 | The populated 0025 upgrade preserves legacy books. Runtime and recovery admit only the matching source and roles, and destructive downgrade is refused. | Verified | The pinned companions, exact database admission checks and restricted grants are wired to startup and migration. The retained profile restores with matching 0025 source. The 0026 recovery receipt verifies restricted TLS replay, exact financial values, exclusion of Redis display data and a refused populated downgrade. |
| 10 | Expanded live source rights and release gates remain explicit. | Verified | The Phase 19 verification retains SC-01 and SC-03 live gaps. The Phase 20 plan and validation contract identify the fixture boundary and leave Phase 21 responsible for production activation, live use and CI. |

## Artifact and data-flow checks

The GSD artifact query passed all 18 declared artifacts. The literal key-link checker reported no matches for the 16 indirect links. I traced the links through imports, service calls, SQL companion loads, and test dispatch.

| Plans | Verified wiring and source data |
|---|---|
| 01–03 | The `promote-instrument` CLI calls the promotion service. Migration 0026 reads the pinned financial, execution and action SQL. The migration and role admission paths use the actual schema and grant fingerprints for 0026 and retained 0025. |
| 04–05 | The scheduler dispatches the bounded catalog quote cycle. The selected queue and active holdings query produce candidates, while the admitted report, provider budget and current listing govern the refresh. The action worker loads scoped coverage and passes the exact authority into action application and dividend entitlement derivation. The dividend service invokes the catalog-aware SQL routine. |
| 06 | The mounted v2 router binds the owned portfolio and accepts preview, confirm and original receipt requests. Both closed-market routes use the SQL mark service independently of the Redis quote cache. The order service uses the same financial ledger and the final catalog assertion. |
| 07 | Portfolio assembles positive holdings, cash and basis from the owned root, compares the two bounded catalog snapshots, and passes unknown marks to the completeness calculation. History joins retained fills or action revisions and projects original labels and IDs. |
| 08 | The ticket uses the catalog-specific hook for typed preview, confirmation and receipt lookup, sharing authorization and time checks with `useStockTrade`. Portfolio holding links resolve to the same owned ticket. History consumes the typed event API through `useEventHistory` and keeps the catalog ID in the link. |
| 09 | `run-stock-browser.py` dispatches the catalog spec to the guarded isolated stack. The paired restic script calls the snapshot and restore test dispatcher for each source profile, which imports the actual backup and restore modules and matches the restored inventory. |

## Requirement disposition

| Requirement | Plans | Status | Evidence |
|---|---|---|---|
| SL-01 | 01–04, 06, 08–09 | Verified on fixtures | Stable owned buy and sell, cash reconciliation, gated replay and selected/held quote budgeting. |
| SL-02 | 04, 06–09 | Verified on fixtures | Permitted closed marks and opening countdown in both price views with empty Redis. Mark expiry removes the price without enabling a fill. |
| SL-03 | 01–03, 05, 07–09 | Verified on fixtures | Scoped dividends, split and correction with immutable event records and an exact cold replay. |
| SL-04 | 01–09 | Verified on fixtures | Exact mixed valuation and cash/basis continuity, truthful incomplete values, private History and stable labels after symbol reuse and restore. |

All four Phase 20 requirements occur in the plan frontmatter. The changed runtime had no stub on the verified paths and no unresolved blocker marker.

## Test and release evidence

- Independently ran the browser runner help, recovery shell syntax check and 19 portable recovery contract tests. All passed. No standalone verification probes were declared.
- Read the final guarded Chromium results and recomputed the wrapper receipt SHA-256 `ea88f552288d23635b4841142b8b0b9222c54dd3d4785796cc864032cf42439e`. All seven browser journeys passed, the before/after source inventory matched, and the disposable resources were removed.
- Read the paired encrypted TLS receipt and recomputed SHA-256 `2f3dd58d8248482aa5367d53e2778ba4243d4bbc24af5ed257a0f4ffa70b54da`. Both revisions reported exact financial, identity and invariant equality. The successor round trip preserved immutable fills, dividends, corrections and splits through cold replay.
- The final five-suite backend slice passed all 63 tests. It recorded 55.17% whole-app coverage and exited nonzero on the inherited whole-suite threshold. The 80% overall and 100% critical full-suite release gates remain open for Phase 21. The separate scoped review closed all seven findings. [Plan 09 summary](20-09-SUMMARY.md) · [Code review](20-REVIEW.md)
- Before activation, Phase 21 still needs complete admitted directory coverage, expanded IEX and action rights, measured quotas and the production Redis retention decision. The PostgreSQL archive excludes Redis display data. These checks address the open Phase 19 live requirements and precede the production out-of-list buy and sell. [Phase 19 verification](../19-search-the-nyse-and-nasdaq-catalog/19-VERIFICATION.md)
