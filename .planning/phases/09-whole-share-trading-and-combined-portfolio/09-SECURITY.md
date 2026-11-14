---
phase: 09-whole-share-trading-and-combined-portfolio
status: passed
threats_total: 76
threats_closed: 76
threats_open: 0
review_mode: sequential-inline
asvs_level: 1
register_authored_at_plan_time: true
reviewed: 2026-11-12
---

# Phase 9 security mitigation audit

Distinct inline security pass under gsd-secure-phase; not independent-agent assurance.
Scope is the plan-time STRIDE register, actual owning code and behavioral tests.
This records implementation checks, not a full product ASVS certification.
Existing deferred live rights/status/continuity are not granted by synthetic tests.

## Register mapping

| Threat | Category | Disposition | Status | Actual mitigation and evidence |
| --- | --- | --- | --- | --- |
| T-09-01-A | Elevation / Spoofing | mitigate | CLOSED | CurrentUserDep/verify_csrf and owner-only lookup; no client user_id; gate/account lock order and final advancing-DB-clock authority. Actual cross-user/API/wait/cancel tests; no prod status transport/fake activation. |
| T-09-01-D | Denial of service | mitigate | CLOSED | Positive12-digit input, bounded20-stock evidence/session limits, DB timeouts, one clean metadata rebuild only, finite status cycle timeout; fixed owned isolated runners with resource refusal and cleanup. |
| T-09-01-I | Information disclosure | mitigate | CLOSED | PrivateRoute no-store including errors; logger types only; fixed safe messages. Owner/lifecycle/query/generation/hash guards, full-RTT deadlines; browser late-account actual-fill assertion; no browser persisted finance or bearer tokens. |
| T-09-01-R | Repudiation | mitigate | CLOSED | Immutable trade/facts/journal receipts, user-scoped global key, original wire replay; no receipt rewrite after close/split. Source/archive/test hashes recorded. Owner acceptance remains pending rather than synthesized. |
| T-09-01-V | Tampering | mitigate | CLOSED | schemas/stock_trades.py rejects extra inputs/coercion; stock_trade_math exact Decimal; API/client strict strings and identities. SQL constraints/final invoker guard. Full backend critical statement/branch100%; client stockTrades parser100%. |
| T-09-02-A | Elevation / Spoofing | mitigate | CLOSED | CurrentUserDep/verify_csrf and owner-only lookup; no client user_id; gate/account lock order and final advancing-DB-clock authority. Actual cross-user/API/wait/cancel tests; no prod status transport/fake activation. |
| T-09-02-D | Denial of service | mitigate | CLOSED | Positive12-digit input, bounded20-stock evidence/session limits, DB timeouts, one clean metadata rebuild only, finite status cycle timeout; fixed owned isolated runners with resource refusal and cleanup. |
| T-09-02-I | Information disclosure | mitigate | CLOSED | PrivateRoute no-store including errors; logger types only; fixed safe messages. Owner/lifecycle/query/generation/hash guards, full-RTT deadlines; browser late-account actual-fill assertion; no browser persisted finance or bearer tokens. |
| T-09-02-R | Repudiation | mitigate | CLOSED | Immutable trade/facts/journal receipts, user-scoped global key, original wire replay; no receipt rewrite after close/split. Source/archive/test hashes recorded. Owner acceptance remains pending rather than synthesized. |
| T-09-02-V | Tampering | mitigate | CLOSED | schemas/stock_trades.py rejects extra inputs/coercion; stock_trade_math exact Decimal; API/client strict strings and identities. SQL constraints/final invoker guard. Full backend critical statement/branch100%; client stockTrades parser100%. |
| T-09-03-A | Elevation / Spoofing | mitigate | CLOSED | CurrentUserDep/verify_csrf and owner-only lookup; no client user_id; gate/account lock order and final advancing-DB-clock authority. Actual cross-user/API/wait/cancel tests; no prod status transport/fake activation. |
| T-09-03-D | Denial of service | mitigate | CLOSED | Positive12-digit input, bounded20-stock evidence/session limits, DB timeouts, one clean metadata rebuild only, finite status cycle timeout; fixed owned isolated runners with resource refusal and cleanup. |
| T-09-03-I | Information disclosure | mitigate | CLOSED | PrivateRoute no-store including errors; logger types only; fixed safe messages. Owner/lifecycle/query/generation/hash guards, full-RTT deadlines; browser late-account actual-fill assertion; no browser persisted finance or bearer tokens. |
| T-09-03-R | Repudiation | mitigate | CLOSED | Immutable trade/facts/journal receipts, user-scoped global key, original wire replay; no receipt rewrite after close/split. Source/archive/test hashes recorded. Owner acceptance remains pending rather than synthesized. |
| T-09-03-V | Tampering | mitigate | CLOSED | schemas/stock_trades.py rejects extra inputs/coercion; stock_trade_math exact Decimal; API/client strict strings and identities. SQL constraints/final invoker guard. Full backend critical statement/branch100%; client stockTrades parser100%. |
| T-09-04-A | Elevation / Spoofing | mitigate | CLOSED | CurrentUserDep/verify_csrf and owner-only lookup; no client user_id; gate/account lock order and final advancing-DB-clock authority. Actual cross-user/API/wait/cancel tests; no prod status transport/fake activation. |
| T-09-04-D | Denial of service | mitigate | CLOSED | Positive12-digit input, bounded20-stock evidence/session limits, DB timeouts, one clean metadata rebuild only, finite status cycle timeout; fixed owned isolated runners with resource refusal and cleanup. |
| T-09-04-I | Information disclosure | mitigate | CLOSED | PrivateRoute no-store including errors; logger types only; fixed safe messages. Owner/lifecycle/query/generation/hash guards, full-RTT deadlines; browser late-account actual-fill assertion; no browser persisted finance or bearer tokens. |
| T-09-04-R | Repudiation | mitigate | CLOSED | Immutable trade/facts/journal receipts, user-scoped global key, original wire replay; no receipt rewrite after close/split. Source/archive/test hashes recorded. Owner acceptance remains pending rather than synthesized. |
| T-09-04-V | Tampering | mitigate | CLOSED | schemas/stock_trades.py rejects extra inputs/coercion; stock_trade_math exact Decimal; API/client strict strings and identities. SQL constraints/final invoker guard. Full backend critical statement/branch100%; client stockTrades parser100%. |
| T-09-05-A | Elevation / Spoofing | mitigate | CLOSED | CurrentUserDep/verify_csrf and owner-only lookup; no client user_id; gate/account lock order and final advancing-DB-clock authority. Actual cross-user/API/wait/cancel tests; no prod status transport/fake activation. |
| T-09-05-D | Denial of service | mitigate | CLOSED | Positive12-digit input, bounded20-stock evidence/session limits, DB timeouts, one clean metadata rebuild only, finite status cycle timeout; fixed owned isolated runners with resource refusal and cleanup. |
| T-09-05-I | Information disclosure | mitigate | CLOSED | PrivateRoute no-store including errors; logger types only; fixed safe messages. Owner/lifecycle/query/generation/hash guards, full-RTT deadlines; browser late-account actual-fill assertion; no browser persisted finance or bearer tokens. |
| T-09-05-R | Repudiation | mitigate | CLOSED | Immutable trade/facts/journal receipts, user-scoped global key, original wire replay; no receipt rewrite after close/split. Source/archive/test hashes recorded. Owner acceptance remains pending rather than synthesized. |
| T-09-05-V | Tampering | mitigate | CLOSED | schemas/stock_trades.py rejects extra inputs/coercion; stock_trade_math exact Decimal; API/client strict strings and identities. SQL constraints/final invoker guard. Full backend critical statement/branch100%; client stockTrades parser100%. |
| T-09-06-A | Elevation / Spoofing | mitigate | CLOSED | CurrentUserDep/verify_csrf and owner-only lookup; no client user_id; gate/account lock order and final advancing-DB-clock authority. Actual cross-user/API/wait/cancel tests; no prod status transport/fake activation. |
| T-09-06-D | Denial of service | mitigate | CLOSED | Positive12-digit input, bounded20-stock evidence/session limits, DB timeouts, one clean metadata rebuild only, finite status cycle timeout; fixed owned isolated runners with resource refusal and cleanup. |
| T-09-06-I | Information disclosure | mitigate | CLOSED | PrivateRoute no-store including errors; logger types only; fixed safe messages. Owner/lifecycle/query/generation/hash guards, full-RTT deadlines; browser late-account actual-fill assertion; no browser persisted finance or bearer tokens. |
| T-09-06-R | Repudiation | mitigate | CLOSED | Immutable trade/facts/journal receipts, user-scoped global key, original wire replay; no receipt rewrite after close/split. Source/archive/test hashes recorded. Owner acceptance remains pending rather than synthesized. |
| T-09-06-V | Tampering | mitigate | CLOSED | schemas/stock_trades.py rejects extra inputs/coercion; stock_trade_math exact Decimal; API/client strict strings and identities. SQL constraints/final invoker guard. Full backend critical statement/branch100%; client stockTrades parser100%. |
| T-09-07-A | Elevation / Spoofing | mitigate | CLOSED | CurrentUserDep/verify_csrf and owner-only lookup; no client user_id; gate/account lock order and final advancing-DB-clock authority. Actual cross-user/API/wait/cancel tests; no prod status transport/fake activation. |
| T-09-07-D | Denial of service | mitigate | CLOSED | Positive12-digit input, bounded20-stock evidence/session limits, DB timeouts, one clean metadata rebuild only, finite status cycle timeout; fixed owned isolated runners with resource refusal and cleanup. |
| T-09-07-I | Information disclosure | mitigate | CLOSED | PrivateRoute no-store including errors; logger types only; fixed safe messages. Owner/lifecycle/query/generation/hash guards, full-RTT deadlines; browser late-account actual-fill assertion; no browser persisted finance or bearer tokens. |
| T-09-07-R | Repudiation | mitigate | CLOSED | Immutable trade/facts/journal receipts, user-scoped global key, original wire replay; no receipt rewrite after close/split. Source/archive/test hashes recorded. Owner acceptance remains pending rather than synthesized. |
| T-09-07-V | Tampering | mitigate | CLOSED | schemas/stock_trades.py rejects extra inputs/coercion; stock_trade_math exact Decimal; API/client strict strings and identities. SQL constraints/final invoker guard. Full backend critical statement/branch100%; client stockTrades parser100%. |
| T-09-08-A | Elevation / Spoofing | mitigate | CLOSED | CurrentUserDep/verify_csrf and owner-only lookup; no client user_id; gate/account lock order and final advancing-DB-clock authority. Actual cross-user/API/wait/cancel tests; no prod status transport/fake activation. |
| T-09-08-D | Denial of service | mitigate | CLOSED | Positive12-digit input, bounded20-stock evidence/session limits, DB timeouts, one clean metadata rebuild only, finite status cycle timeout; fixed owned isolated runners with resource refusal and cleanup. |
| T-09-08-I | Information disclosure | mitigate | CLOSED | PrivateRoute no-store including errors; logger types only; fixed safe messages. Owner/lifecycle/query/generation/hash guards, full-RTT deadlines; browser late-account actual-fill assertion; no browser persisted finance or bearer tokens. |
| T-09-08-R | Repudiation | mitigate | CLOSED | Immutable trade/facts/journal receipts, user-scoped global key, original wire replay; no receipt rewrite after close/split. Source/archive/test hashes recorded. Owner acceptance remains pending rather than synthesized. |
| T-09-08-V | Tampering | mitigate | CLOSED | schemas/stock_trades.py rejects extra inputs/coercion; stock_trade_math exact Decimal; API/client strict strings and identities. SQL constraints/final invoker guard. Full backend critical statement/branch100%; client stockTrades parser100%. |
| T-09-09-A | Elevation / Spoofing | mitigate | CLOSED | CurrentUserDep/verify_csrf and owner-only lookup; no client user_id; gate/account lock order and final advancing-DB-clock authority. Actual cross-user/API/wait/cancel tests; no prod status transport/fake activation. |
| T-09-09-D | Denial of service | mitigate | CLOSED | Positive12-digit input, bounded20-stock evidence/session limits, DB timeouts, one clean metadata rebuild only, finite status cycle timeout; fixed owned isolated runners with resource refusal and cleanup. |
| T-09-09-I | Information disclosure | mitigate | CLOSED | PrivateRoute no-store including errors; logger types only; fixed safe messages. Owner/lifecycle/query/generation/hash guards, full-RTT deadlines; browser late-account actual-fill assertion; no browser persisted finance or bearer tokens. |
| T-09-09-R | Repudiation | mitigate | CLOSED | Immutable trade/facts/journal receipts, user-scoped global key, original wire replay; no receipt rewrite after close/split. Source/archive/test hashes recorded. Owner acceptance remains pending rather than synthesized. |
| T-09-09-V | Tampering | mitigate | CLOSED | schemas/stock_trades.py rejects extra inputs/coercion; stock_trade_math exact Decimal; API/client strict strings and identities. SQL constraints/final invoker guard. Full backend critical statement/branch100%; client stockTrades parser100%. |
| T-09-10-A | Spoofing/Elevation | mitigate | CLOSED | CurrentUserDep/verify_csrf and owner-only lookup; no client user_id; gate/account lock order and final advancing-DB-clock authority. Actual cross-user/API/wait/cancel tests; no prod status transport/fake activation. |
| T-09-10-D | Denial of service | mitigate | CLOSED | Positive12-digit input, bounded20-stock evidence/session limits, DB timeouts, one clean metadata rebuild only, finite status cycle timeout; fixed owned isolated runners with resource refusal and cleanup. |
| T-09-10-I | Information disclosure | mitigate | CLOSED | PrivateRoute no-store including errors; logger types only; fixed safe messages. Owner/lifecycle/query/generation/hash guards, full-RTT deadlines; browser late-account actual-fill assertion; no browser persisted finance or bearer tokens. |
| T-09-10-R | Repudiation | mitigate | CLOSED | Immutable trade/facts/journal receipts, user-scoped global key, original wire replay; no receipt rewrite after close/split. Source/archive/test hashes recorded. Owner acceptance remains pending rather than synthesized. |
| T-09-10-V | Tampering | mitigate | CLOSED | schemas/stock_trades.py rejects extra inputs/coercion; stock_trade_math exact Decimal; API/client strict strings and identities. SQL constraints/final invoker guard. Full backend critical statement/branch100%; client stockTrades parser100%. |
| T-09-11-A | Spoofing/Elevation | mitigate | CLOSED | CurrentUserDep/verify_csrf and owner-only lookup; no client user_id; gate/account lock order and final advancing-DB-clock authority. Actual cross-user/API/wait/cancel tests; no prod status transport/fake activation. |
| T-09-11-D | Denial of service | mitigate | CLOSED | Positive12-digit input, bounded20-stock evidence/session limits, DB timeouts, one clean metadata rebuild only, finite status cycle timeout; fixed owned isolated runners with resource refusal and cleanup. |
| T-09-11-I | Information disclosure | mitigate | CLOSED | PrivateRoute no-store including errors; logger types only; fixed safe messages. Owner/lifecycle/query/generation/hash guards, full-RTT deadlines; browser late-account actual-fill assertion; no browser persisted finance or bearer tokens. |
| T-09-11-R | Repudiation | mitigate | CLOSED | Immutable trade/facts/journal receipts, user-scoped global key, original wire replay; no receipt rewrite after close/split. Source/archive/test hashes recorded. Owner acceptance remains pending rather than synthesized. |
| T-09-11-V | Tampering | mitigate | CLOSED | schemas/stock_trades.py rejects extra inputs/coercion; stock_trade_math exact Decimal; API/client strict strings and identities. SQL constraints/final invoker guard. Full backend critical statement/branch100%; client stockTrades parser100%. |
| T-09-12-A | Spoofing/Elevation | mitigate | CLOSED | CurrentUserDep/verify_csrf and owner-only lookup; no client user_id; gate/account lock order and final advancing-DB-clock authority. Actual cross-user/API/wait/cancel tests; no prod status transport/fake activation. |
| T-09-12-D | Denial of service | mitigate | CLOSED | Positive12-digit input, bounded20-stock evidence/session limits, DB timeouts, one clean metadata rebuild only, finite status cycle timeout; fixed owned isolated runners with resource refusal and cleanup. |
| T-09-12-I | Information disclosure | mitigate | CLOSED | PrivateRoute no-store including errors; logger types only; fixed safe messages. Owner/lifecycle/query/generation/hash guards, full-RTT deadlines; browser late-account actual-fill assertion; no browser persisted finance or bearer tokens. |
| T-09-12-R | Repudiation | mitigate | CLOSED | Immutable trade/facts/journal receipts, user-scoped global key, original wire replay; no receipt rewrite after close/split. Source/archive/test hashes recorded. Owner acceptance remains pending rather than synthesized. |
| T-09-12-V | Tampering | mitigate | CLOSED | schemas/stock_trades.py rejects extra inputs/coercion; stock_trade_math exact Decimal; API/client strict strings and identities. SQL constraints/final invoker guard. Full backend critical statement/branch100%; client stockTrades parser100%. |
| T-09-13-A | Spoofing/Elevation | mitigate | CLOSED | CurrentUserDep/verify_csrf and owner-only lookup; no client user_id; gate/account lock order and final advancing-DB-clock authority. Actual cross-user/API/wait/cancel tests; no prod status transport/fake activation. |
| T-09-13-D | Denial of service | mitigate | CLOSED | Positive12-digit input, bounded20-stock evidence/session limits, DB timeouts, one clean metadata rebuild only, finite status cycle timeout; fixed owned isolated runners with resource refusal and cleanup. |
| T-09-13-I | Information disclosure | mitigate | CLOSED | PrivateRoute no-store including errors; logger types only; fixed safe messages. Owner/lifecycle/query/generation/hash guards, full-RTT deadlines; browser late-account actual-fill assertion; no browser persisted finance or bearer tokens. |
| T-09-13-R | Repudiation | mitigate | CLOSED | Immutable trade/facts/journal receipts, user-scoped global key, original wire replay; no receipt rewrite after close/split. Source/archive/test hashes recorded. Owner acceptance remains pending rather than synthesized. |
| T-09-13-V | Tampering | mitigate | CLOSED | schemas/stock_trades.py rejects extra inputs/coercion; stock_trade_math exact Decimal; API/client strict strings and identities. SQL constraints/final invoker guard. Full backend critical statement/branch100%; client stockTrades parser100%. |
| T-09-14-A | Spoofing/Elevation | mitigate | CLOSED | CurrentUserDep/verify_csrf and owner-only lookup; no client user_id; gate/account lock order and final advancing-DB-clock authority. Actual cross-user/API/wait/cancel tests; no prod status transport/fake activation. |
| T-09-14-D | Denial of service | mitigate | CLOSED | Positive12-digit input, bounded20-stock evidence/session limits, DB timeouts, one clean metadata rebuild only, finite status cycle timeout; fixed owned isolated runners with resource refusal and cleanup. |
| T-09-14-I | Information disclosure | mitigate | CLOSED | PrivateRoute no-store including errors; logger types only; fixed safe messages. Owner/lifecycle/query/generation/hash guards, full-RTT deadlines; browser late-account actual-fill assertion; no browser persisted finance or bearer tokens. |
| T-09-14-R | Repudiation | mitigate | CLOSED | Immutable trade/facts/journal receipts, user-scoped global key, original wire replay; no receipt rewrite after close/split. Source/archive/test hashes recorded. Owner acceptance remains pending rather than synthesized. |
| T-09-14-V | Tampering | mitigate | CLOSED | schemas/stock_trades.py rejects extra inputs/coercion; stock_trade_math exact Decimal; API/client strict strings and identities. SQL constraints/final invoker guard. Full backend critical statement/branch100%; client stockTrades parser100%. |
| T-09-15-A | Spoofing/Elevation | mitigate | CLOSED | CurrentUserDep/verify_csrf and owner-only lookup; no client user_id; gate/account lock order and final advancing-DB-clock authority. Actual cross-user/API/wait/cancel tests; no prod status transport/fake activation. |
| T-09-15-D | Denial of service | mitigate | CLOSED | Positive12-digit input, bounded20-stock evidence/session limits, DB timeouts, one clean metadata rebuild only, finite status cycle timeout; fixed owned isolated runners with resource refusal and cleanup. |
| T-09-15-I | Information disclosure | mitigate | CLOSED | PrivateRoute no-store including errors; logger types only; fixed safe messages. Owner/lifecycle/query/generation/hash guards, full-RTT deadlines; browser late-account actual-fill assertion; no browser persisted finance or bearer tokens. |
| T-09-15-R | Repudiation | mitigate | CLOSED | Immutable trade/facts/journal receipts, user-scoped global key, original wire replay; no receipt rewrite after close/split. Source/archive/test hashes recorded. Owner acceptance remains pending rather than synthesized. |
| T-09-15-V | Tampering | mitigate | CLOSED | schemas/stock_trades.py rejects extra inputs/coercion; stock_trade_math exact Decimal; API/client strict strings and identities. SQL constraints/final invoker guard. Full backend critical statement/branch100%; client stockTrades parser100%. |
| T-09-SC | Tampering | mitigate | CLOSED | Locked dependencies unchanged. Official registry image pin updated after observed HIGH; five-image strict scan has zero qualifying findings. Recovery index/platform/config/Compose authenticated together. No registry block or provider calls. |

## Applicable ASVS L1 controls

| Area from plan | Evidence |
| --- | --- |
| V2 input validation | Strict whole quantity, positive fixed-point price, extra=forbid; no amount/user/authority supplied by browser; malformed-response tests. |
| V4 API/business logic | Thin routes, immutable key identity, ask/bid exact accounting, deferred SQL invariants and final authority; original receipt replay, actual lock/expiry/split tests. |
| V7 session lifecycle | Existing HttpOnly cookie auth/CSRF preserved; owner cache/auth version replacement and late-response checks; signout/new-user browser assertion. |
| V8 authorization | Current user from dependency, owner-scoped trade/portfolio queries, invoker rights and restricted role denials, migrations grant no financial repair in quarantined clones. |
| V1 frontend handling | React escaping; no new HTML injection or web storage; exact parsers, safe fixed copy, labels and conservative stale-value suppression. |

All76plan-time mitigations are verified locally, with no open implementation
threat or applicable ASVSL1 failure. The image advisory is remediated by the
reviewed18.7 pin, not accepted or ignored. Final all-five strict scans show zero
HIGH/CRITICAL; same compatible archive5eb886d1 passes retained recovery, both
restricted verified-TLS lanes and actual old/new selected-volume rollback.
Backend2086/39critical modules100%, frontend590 and all applicable browser
stories pass. Final stock14also validate script-free, form-free, same-origin
font-only offline export; its generated files make zero external HTTP requests.

T-09-15-R is closed as a mitigation check: the explicit human gate and truthful
pending record prevent forged acceptance. The actual owner answers remain
pending in15; this security pass does not satisfy those feature checkpoints.
No new provider agreement, production setting, installed archive or timer changed.
There are no unregistered security flags: image remediation maps toT-09-SC;
synthetic read-only review exports map toT-09-13-I/R andT-09-15-I/R.
