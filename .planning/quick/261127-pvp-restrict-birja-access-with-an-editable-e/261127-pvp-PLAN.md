---
phase: quick-261127-pvp
plan: 01
type: execute
wave: 1
depends_on: []
autonomous: true
requirements: [INVITE-FILE, INVITE-REFUSAL, PERSONAL-STOCK]
files_modified:
  - backend/app/core/config.py
  - backend/app/core/deps.py
  - backend/app/services/access_list.py
  - backend/app/services/auth.py
  - backend/app/api/v1/auth.py
  - backend/app/api/v2/auth.py
  - frontend/src/pages/SignInPage.tsx
  - docker-compose.prod.yml
  - deploy/RUNBOOK.md
must_haves:
  truths:
    - A listed address can sign in with the existing email code flow. Other addresses see that registrations are closed, without receiving a code or creating a user.
    - A host-file edit takes effect in the running service, including for the next authenticated request and refresh by a removed address.
    - Birja admits personal Alpaca trading only with an enforced sole-owner audience and valid quotes, action, halt and session checks.
  artifacts:
    - path: backend/app/services/access_list.py
      provides: Shared file reader and normalized membership policy
    - path: deploy/RUNBOOK.md
      provides: Host path, safe operator edit, launch and rollback steps
  key_links:
    - from: docker-compose.prod.yml
      to: backend/app/services/access_list.py
      via: Read-only directory mount and configured access-list file
    - from: backend/app/services/auth.py
      to: backend/app/core/deps.py
      via: Same current list enforced for one-time code and session paths
---

<objective>
Restrict deployed Birja to the operator-maintained list and qualify owner-only simulated equities on the current Alpaca IEX integration. Preserve the existing application design, portfolios, ledger and providers.
</objective>

<context>
@CLAUDE.md
@.planning/PROJECT.md
@.planning/REQUIREMENTS.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/milestones/v1.0-phases/02-authentication/02-CONTEXT.md
@.planning/phases/21-verify-release-and-activate-stock-trading/21-CONTEXT.md
@.planning/phases/21-verify-release-and-activate-stock-trading/21-LIVE-QUALIFICATION.md
@deploy/STOCK-DATA-ADMISSION.md
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Enforce current file membership throughout sign-in</name>
  <files>backend/app/core/config.py, backend/app/services/access_list.py, backend/app/services/auth.py, backend/app/core/deps.py, backend/app/api/v1/auth.py, backend/app/api/v2/auth.py, backend/tests/test_auth_request_code.py, backend/tests/test_auth_verify.py, backend/tests/test_auth_session.py, frontend/src/pages/SignInPage.tsx, frontend/src/pages/SignInPage.test.tsx</files>
  <behavior>Unlisted addresses get the same 403 whether or not an account exists. Removal before code confirmation blocks onboarding. Removal while signed in rejects the old access and refresh token. Edits and atomic file replacement change access without bouncing the app. A missing, unreadable, invalid or empty configured file permits nobody.</behavior>
  <action>Add optional `AUTH_ALLOWED_EMAILS_FILE` to `Settings`. An unset path preserves explicitly unrestricted development and existing test configurations. Read a bounded UTF-8 one-address-per-line file on use so every backend worker sees the current policy and no daemon is needed. Apply the same trim, lowercase and validation as `RequestCodeIn` to the file, making blank lines harmless. Use the shared check before issuing a code and before consuming a code or creating account/session state. Keep CSRF and IP/OTP rate limits. In `get_current_user`, refuse removed addresses with the existing 401 session contract. In `rotate_session`, refuse removed addresses before issuing fresh tokens and clear cookies via existing `InvalidSession`; add a user-email lookup only when the file policy is active. At v1 code request and v2 verification return 403 `registration_closed` with `Cache-Control: no-store`, independent of account existence and with no address in logs or response. Keep the legacy verifier refusal. Read the frontend-design skill and Birja MASTER before mapping that code to “Birja isn’t accepting registrations at the moment.” in the existing `SignInPage` alert. Use synthetic addresses in all tracked artifacts.</action>
  <verify><automated>Run the isolated PostgreSQL/Redis auth request, auth verify, session and CSRF tests. Run the SignInPage Vitest suite and assert registration-closed copy on both affected steps. Verify edit/remove/missing-file cases against one live test app instance, with an active account and a separate OTP recipient.</automated></verify>
  <done>Listed users retain the existing sign-in flow and a disallowed browser or API client cannot obtain or reuse a session. The sign-in form explains refusal without displaying internal details.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Wire host editing and guard the personal Alpaca audience</name>
  <files>docker-compose.prod.yml, deploy/RUNBOOK.md, backend/app/core/config.py, backend/app/core/deps.py, backend/app/api/v1/stocks.py, backend/app/api/v2/stock_catalog.py, backend/app/api/v2/stock_trades.py, backend/app/services/portfolio.py, backend/tests/test_auth_session.py, backend/tests/test_stock_execution_authority.py</files>
  <behavior>The owner can use configured personal stock data with a one-entry list. Adding another listed address still allows ordinary sign-in, while owner-data pricing and new equity trades pause. Removing the extra address restores the audience condition on the next request. Removing or replacing the pinned owner with any other address never satisfies personal mode.</behavior>
  <action>Expose the configured path using the existing production Compose and environment convention. Mount the host directory containing the allowlist read-only so atomic replacements are visible within the container, and keep the real file and owner identity under protected host configuration. Document one email per line, the file's effective path and ownership, behavior when no entry matches, and preflight/read-only rollback confidentiality. Add an opt-in personal-stock setting pinned to the owner account ID and normalized address, which requires the current list to be exactly that address. Enforce the condition at the backend paths that can return current personal prices or authorize a stock order. Audit the featured Markets list, both stock trade routers, selected listing quotes, current portfolio valuations and any native stock-history branch. A single `STOCK_DATA_ENABLED` toggle does not cover every cached disclosure or curated execution path. Reuse a shared request-level policy and existing unavailable states where possible. Confirm background collection respects personal audience where it handles private account data, including held stocks owned by pre-existing accounts. Preserve independent catalog identities, TradingView chart presentation, crypto operations and users' own pre-existing portfolio records. The check adds an audience requirement to current admission and execution authority.</action>
  <verify><automated>Validate production Compose rendering with synthetic values, including the read-only directory. In one test stack, edit the file and check all personal quote, preview and trade paths plus valuation against single-owner, two-address and replaced-owner lists. Confirm crypto access for both allowed accounts.</automated></verify>
  <done>A root-operated file replaces enrollment without redeployment, and list edits cannot widen the audience for personal Alpaca data.</done>
</task>

<task type="auto">
  <name>Task 3: Diagnose and verify the deployed trade path</name>
  <files>deploy/STOCK-DATA-ADMISSION.md, .planning/quick/261127-pvp-restrict-birja-access-with-an-editable-e/261127-pvp-SUMMARY.md</files>
  <action>Inspect the current app-role decisions and sanitized admission metadata for representative curated stocks and an available listing outside them. Existing flags select Alpaca IEX, but live AAPL, MSFT and NVDA currently return `permission_unavailable`, with noncurrent corporate-action states. Trace the first failed authority predicate, source freshness, calendar/halt scope and corporate-action worker health. Check any known replay fix against actual captured evidence and exact production source before considering it. Reuse and truthfully narrow the supported admission procedure for the verified personal audience. Preserve currency, accounting, status, quote age and expiry checks and keep prior records. For authorized production work preserve release verification, recovery and rollback requirements from the runbook and avoid restoring open stock access by accident. If unresolved evidence or a closed market prevents a genuine round trip, record the failing gate and evidence separately from release/read-only smoke.</action>
  <verify><automated>Run affected backend and frontend integration checks. On the exact deployed release verify public refusal and owner access without logging email or credentials. In an open session verify quote and preview then reconcile a one-share virtual buy and sell, cash, zero remaining position and both History receipts using an isolated portfolio permitted for the sole owner. Preserve the recorded fallback and actual outcome.</automated></verify>
  <done>The deployed private service has a verified stock round trip, or an explicit outstanding reason with the observed decision and the access work separately verified.</done>
</task>

</tasks>

<threat_model>

| Concern | Boundary | Mitigation |
|---|---|---|
| Registration or token replay after removal | Public request to authenticated backend | Check file membership at issuance, confirmation, refresh and every authenticated request. Keep CSRF, OTP and existing session expiry. |
| Missing or malformed file | Host operator to container | Bound reads, reject invalid configured files and mount directory read-only. |
| Display outside personal scope | Host audience list to stock routes and portfolio valuation | Pin the owner and enforce sole-owner condition in addition to the existing market/data checks. |
| Unintended user identification | Public responses and operational output | Use a uniform refusal for all unlisted addresses and keep addresses and provider evidence out of the repository, output and logs. |

</threat_model>

<source_audit>

| Source | Requirement | Task |
|---|---|---|
| User request | Keep current app, make enrollment editable on host, give a clear closed-registration response | 1, 2 |
| User request and parent context | Allow personal Alpaca buy and sell only for the sole owner | 2, 3 |
| Authentication context and project requirements | Preserve OTP, CSRF, non-enumeration, session semantics and funding | 1 |
| Roadmap and Phase 21 | Preserve market rules, crypto and portfolio ownership. Verify live stock behavior directly | 2, 3 |
| Existing production and planning evidence | Trace actual admission and corporate-action failures before activation | 3 |

</source_audit>

<output>
Record verified quick-task results in `.planning/quick/261127-pvp-restrict-birja-access-with-an-editable-e/261127-pvp-SUMMARY.md` and update the quick-task table without changing the roadmap.
</output>
