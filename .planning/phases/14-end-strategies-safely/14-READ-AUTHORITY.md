# Phase 14 — Normal Read and Original-Reference Authority

Current implementation inventory for Plan10. A completed row is supported by
actual source and the indicated real PostgreSQL/public-DELETE tests. This is
not a whole-phase verification, production observation or new endpoint.

## Linearization and lock order

Initial `OwnedActivePortfolioDep` / `resolve_owned_active_portfolio` establishes
the captured owner and ID without a root lock. It cannot authorize a late
financial response by itself. `fence_owned_active_portfolios` is a **final**
ordered `Account FOR SHARE` owner/active check: no later instrument work may
follow it. Read locks remain on the same request transaction until `get_db`
closes its session after response processing. No upfront account share lock is
introduced before stock instrument gates. Shared root locks taken after a
financial commit/replay rollback are a new read transaction, not a claim that
the prior economic commit was rolled back.

If closure commits before the final fence, normal response is private404
`portfolio_unavailable`. If the final fence wins, the closer waits for that
read transaction; its already-authorized response can complete first. Neither
server nor browser can retract bytes delivered before closure.

The retained `test_crypto_fill_before_closure_preserves_exact_fill_and_basis`
case now distinguishes the economic commit from its later response: a queued
closer may win after the fill commits, requiring exact private404 with no
receipt. A read-first result must still carry the original root/BTC/buy/quantity
and exact resulting cash; all original ledger, basis and frozen-state assertions
remain. This narrow test-file amendment was approved by the parent executor
after the real regression returned the required private404. Deterministic tests
separately establish both fence orders; this scheduling case does not replace them.

## Route → service → query inventory

| Normal surface | Route / service / authoritative query | Final authority and proof |
|---|---|---|
| Identity discovery | GET `/api/v2/portfolios` → `list_active_portfolios` → owner/active IDs and names, ID order | Final ordered same-owner active-ID share fence; late hydration closure refuses, read-first blocks actual public closer. `test_metadata_late_read_cannot_publish_closed_identity`, `test_metadata_final_fence_holds_closer_until_response`. Empty discovery creates/grants nothing. |
| Named metadata | GET `/{id}/metadata` → `get_portfolio_metadata` → exact owner/active ID/name/description | Same final fence and both-order tests above. No name/description returned after closed final fence. |
| Overview / statement / holdings valuation | GET `/overview`, `/{id}` → `load_portfolio_snapshots` / `get_portfolio` → owner-filtered bounded snapshot + final ordered shared active-membership query | Existing final shared lock includes selected roots and current membership; no new early lock. `test_valuation_final_membership_with_public_closure` exercises both public-DELETE orders for overview and detail; direct-ID privacy is covered by the cursor/original matrix. Exact value math is preserved. |
| Trade History | GET `/{id}/history` → `list_history` → root/owner-filtered seek join `(created_at,id)` | Initial unlocked lifecycle check, bounded root-bound cursor, then final `validate_portfolio_read(final=True)`; same session share locks through response. `test_history_final_fence_holds_closer_until_response`, `test_history_close_before_final_read_refuses_hydrated_data`. |
| Mixed History / original payment details | GET `/{id}/event-history` → `list_event_history` → owner/root-filtered union then bounded per-kind hydration | Same final shared lifecycle fence. Every embedded original payment join includes owner+root, and seek cursor binds expected root. There is no independent `/event/{id}` original endpoint. Both-order History tests plus Task2 cursor/original privacy matrix cover this surface. |
| Crypto preview / holding | POST `/{id}/trades/quote`, GET `/{id}/holdings/{symbol}` → trading quote/holding service | Initial captured owner/active resolver and service account check; final route fence after value hydration, including quote-bearing reprice refusals. Task2 late-response and private-read matrix. |
| Crypto execution / original receipt retry | POST `/{id}/trades` → `trading.execute` → root UPDATE before original-key lookup; new fill commits, original replay rolls back read transaction | Final route owner/active share fence after service commit/rollback and before receipt/refusal projection. A committed fill remains retained if closure wins the later read race; no normal closed receipt access or replacement spend. Task2 real postcommit/original-retry overlap. |
| Stock preview / context | POST `/{id}/stock-trades/quote`, GET `/{id}/stock-trades/{symbol}/context` → stock quote/context evidence services | Final route share fence after all evidence awaits, never before instrument work. Task2 root-bound context/preview and close-overlap cases. |
| Stock execution / original receipt retry | POST `/{id}/stock-trades` → stock execute → original instrument gate then exact account UPDATE; final authority/proof and commit or replay rollback | Final route share fence after service returns, including quote-bearing price-change refusals; no later instrument acquisition. Task2 stored receipt/close/foreign-original tests. |
| Legacy implicit finance | `/api/v1/trades`, `/holdings/{symbol}`, `/portfolio`, `/history`, stock equivalents → `legacy_finance.portfolio_required` | Existing authenticated private409 `portfolio_required`; POST also requires CSRF. It never reads a receipt, chooses a root, creates one or invokes finance. Task2 retired-route assertions. |

## Narrow lifecycle acknowledgement

DELETE `/api/v2/portfolios/{id}` is the sole minimal owned-closed acknowledgement:
the complete same-transaction closure proof precedes its exact ID/state receipt.
It exposes no retained name, money, History or original execution receipt. This
does not weaken any normal read/retry owner-active check. No trash/restore/export
or normal closed-book detail endpoint is added.

## Executable evidence and remaining integration

All selectors below are in `tests/test_portfolio_closure_privacy.py`, with real
restricted `birja_app` HTTP sessions and real PostgreSQL/public DELETE:

- `metadata_late_read`, `metadata_final_fence`: identity discovery/metadata,
  both orderings, including post-hydration closure and an observed waiting closer.
- `history_close_before_final_read`, `history_final_fence`: trade/mixed History,
  both orderings and an observed waiting closer.
- `valuation_final_membership`: overview/detail, both orderings, existing final
  membership lock retained until response cleanup.
- `late_financial_read_or_original_receipt`: crypto/stock quote, holding/context,
  new fill, original-key retry and quote-bearing reprice refusal after closure.
- `financial_final_fence`: crypto/stock committed-fill response wins, actual
  closer blocked until the request session releases its root share lock.
- `cursor_original_retry`: original dividend/correction details, owner/root-bound
  seek cursors, guessed IDs, original execution keys and same-name new roots.
- `retired_finance`: every retired implicit financial route refuses without
  selecting or creating a replacement root.

Scheduler jobs are a separate restricted trust boundary: they do not serve
normal authenticated HTTP or original-receipt URLs. Existing authority/admission
tests exercise both app/scheduler mutation denials and the app-only exact closure
signature; no scheduler grant is broadened for these final browser-read fences.
Whole critical coverage, browser proof and encrypted/TLS qualification remain
Plans16–18; this inventory is not evidence that those gates passed.
