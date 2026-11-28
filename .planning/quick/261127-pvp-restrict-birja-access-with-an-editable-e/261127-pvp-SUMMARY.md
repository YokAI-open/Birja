---
phase: quick-261127-pvp
plan: 01
status: partial
subsystem: auth
tags: [registration, allowlist, sessions, equities]
requirements-completed: [INVITE-FILE, INVITE-REFUSAL]
---

# Editable access and personal stock data

Birja checks an operator-owned email file for sign-in and session authorization. Personal Alpaca data requires the pinned owner account and its sole email in the current file.

## Local changes

- `28e5b66` and `afbfe54` cover and enforce the file policy for OTP requests, code confirmation, access tokens and refresh. Rejected addresses see the existing sign-in alert with registration-closed copy.
- `2f4a1f9`, `fa2947d` and `e8472ec` cover and enforce the personal stock audience for quotes, preview and confirmation, portfolio marks and the quote and action scheduler paths. An invited account still has access to crypto and its existing records. The account ID allows scheduler valuation without a grant to read user email from the database. The pinned email checks the one-entry file in both backend and scheduler.
- The Compose services share a read-only directory mount. A file replacement becomes visible on the next relevant read without a service restart. The production file path and rollout and recovery instructions are in `deploy/RUNBOOK.md`.

## Verification

- The new auth and stock tests each failed against their respective pre-implementation source at the missing authorization check.
- The isolated stack verified owner sign-in, quote, preview, simulated stock purchase and valuation. Editing the file immediately refused the stock quote, chart and order paths and hid its current mark. A newly invited user could still sign in and reach crypto prices. Restoring the sole owner allowed a simulated sale and left a zero position.
- All 331 tests in the affected backend selection passed. The coverage command's full-application 80% floor was unmet by the targeted selection, with 48.95% measured across the application. The final focused equity privacy regression passed separately after adding the sale and chart assertions.
- Python Ruff and mypy, frontend typecheck, frontend lint, the production frontend build and the 24 SignInPage tests passed. Synthetic Compose rendering passed with both default and private configurations. Vite reported a chunk-size warning during the successful build.

- All 188 targeted Alpaca action parser and scheduler tests passed on the integrated candidate, including both replay envelopes and current-window expiry. Ruff, formatting and mypy also passed for those changes.

## Production follow-up

The source changes are based on production commit `5d4e5b0`. On November 27 the requested one-entry file was created at `/etc/birja/access/allowed-emails.txt` under restricted host permissions. The existing owner account was confirmed by a read-only query. The running services still use the prior release and its configuration.

The deployed backend and scheduler have the IEX quote source enabled. The scheduler also has corporate actions enabled. At 17:31 UTC, the running application reported an open market and rejected AAPL, MSFT and NVDA with `permission_unavailable`. A second read-only check identified missing durable accounting, retention and backup scope for `calendar`, `quotes`, `reference` and `status`. ORCL was searchable and reported `market_closed` at 18:00 UTC. The requested privacy change does not change these records.

The exact production snapshot also predates a tested Alpaca replay repair. Commit `4d06ada` accepts both observed event envelopes and preserves a valid matching action window through transient replay failures. Financial, action, quote freshness and halt requirements remain enforced. Microsoft and NVIDIA have separate corporate-action holds, which remain subject to reconciliation.

Release the file-backed access candidate through a hotfix PR. Before activating the intended site, set both pinned owner values and the mounted allowlist in protected production configuration. Confirm that an unlisted address is refused and that a removed address cannot reuse an old session. Only then qualify the exact personal data scope and apply the existing admission procedures. Verify a buy and a sell in the requested owner's isolated portfolio during an open session, including an eligible listing beyond the original 20. The hosted CI, rollout, live scope and production round trip are pending.

## Self-Check

Local unit and integration artifacts are tracked in the five source and test commits. This planning record and the quick-task table are left to the orchestrator.
