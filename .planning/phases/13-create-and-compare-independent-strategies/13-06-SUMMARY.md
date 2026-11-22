---
phase: 13-create-and-compare-independent-strategies
plan: "06"
subsystem: api
tags: [fastapi, pydantic, portfolios, idempotency, csrf, restricted-roles]
requires:
  - phase: 13-05
    provides: Reviewed current0020 authority, exact admission/grants and recovery contracts
provides:
  - Strict bounded private create, metadata PATCH and metadata detail APIs on actual production routers
  - Permanent SQL-canonical creation replay with service-owned commit and rollback
  - Real session/CSRF, restricted-role, resource-bound, race and financial preservation proofs
affects: [13-07, 13-08, 13-09, 13-14, 13-15, 13-17]
tech-stack:
  added: []
  patterns: [bounded manual JSON after authentication, private management route wrapper, narrow SQL transactions]
key-files:
  created:
    - backend/app/api/v2/portfolio_management.py
    - backend/tests/test_portfolio_management_api.py
    - backend/tests/test_portfolio_creation.py
    - backend/tests/test_portfolio_metadata.py
  modified:
    - backend/app/schemas/portfolios.py
    - backend/app/core/config.py
    - backend/app/services/portfolios.py
    - backend/app/api/v2/portfolios.py
key-decisions:
  - "Retain reviewed immutable SQL100 successful new explicit grants/UTC-day, with30/minute owner and60/minute IP attempt bounds; parent clarified contradictory planner-discretion20/day wording in f55b416."
  - "Authenticate actual session and verify CSRF before manually reading bounded streamed JSON; canonical payload persistence and name equivalence remain SQL-owned."
  - "Keep GET portfolio summaries exactly id/name; new metadata detail and mutation responses contain exactly id/name/description."
requirements-completed: [PMGT-01, PMGT-02, PMGT-06, PFUND-01, PFUND-02, PSAFE-07]
duration: 15min
completed: 2026-11-18
---

# Phase 13 Plan 06: Private Creation and Metadata APIs Summary

**Actual authenticated portfolio routes create fixed10000 strategies once per original intent, safely replay after response loss, and edit metadata without changing financial or History evidence.**

## Performance

- Execution approximately09:36–09:51UTC on2026-11-18;2/2 tasks,8 implementation/test files.
- Final focused run:50passed in49.98s, comprising36 boundary/schema/settings/Redis cases,11 creation/service/statement cases and3 metadata cases.
- Four affected management modules reach100% statement and branch coverage:213 statements,44 branches, zero missed or partial branches. This is a scoped result, not the complete backend/security campaign.
- Changed8-file Ruff lint/format and strict mypy for all5 modified/new source modules pass; `git diff --check` passes.

## Task Commits

1. **Task1 RED:** `998b551` — Specify strict management transport. Actual failure: missing PortfolioCreate before implementation.
2. **Task1 GREEN:** `e7ef737` — Bound private management transport.36 focused cases pass in1.21s.
3. **Task2 RED:** `d4711e4` — Specify funded creation and metadata API. Actual production POST returned405 before implementation; real restricted current-schema fixture admitted successfully.
4. **Task2 GREEN:** `29effb1` — Expose funded portfolio management. Final50-case focused verification passes.

Both task RED commits precede their GREEN commits. No tracked file deletion occurred.

## Delivered Behavior

- POST `/api/v2/portfolios` requires an actual unrevoked cookie session, CSRF and exactly one lowercase UUIDv4 Idempotency-Key. New grants return201 and canonical original retries200. Private metadata GET `/api/v2/portfolios/{id}/metadata` and PATCH `/api/v2/portfolios/{id}` return exactly string id/name/description. The existing discovery GET remains exactly ordered id/name summaries, and the existing explicit statement retains its original financial shape and stored baseline.
- Create accepts only name and optional empty-default description. PATCH requires at least one present field; explicit null and owner/cash/baseline/unknown fields fail. Names reject raw C0/C1/surrogates before explicit Unicode White_Space trim, then use NFC1–60 scalar validation. Descriptions preserve whitespace, normalize CRLF/CR to LF, allow TAB/LF and enforce0–1000 normalized scalars. SQL exclusively decides casefold collisions and immutable persisted canonical intent.
- Owner/session and CSRF checks run before body consumption. Manual UTF-8 JSON parsing rejects duplicate fields, malformed/non-object payloads and unsupported media. Stream accumulation stops at8192bytes, including chunked and deceptive Content-Length inputs; exactly8192bytes remains accepted. Rejections use stable private errors without reflecting submitted inputs.
- Create attempts use existing transactional Redis TTL primitives, with30/minute owner and60/minute normalized-IP default ceilings and settings that cannot raise those maxima. Replays and rejected attempts consume these limits. Existing serialized SQL separately enforces100 successful new explicit grants/UTC-day; initial grants and replay do not consume that quota. Redis failure refuses before creation. Rejected keys never add durable journal records.
- Bound SQL calls invoke only `create_portfolio` and `update_portfolio_metadata`. Services commit the result and roll back recognized and unknown database failures. Known name/key/cap conflicts map409, unavailable roots404, SQL-invalid intent422, durable quota429 with UTC-day Retry-After, and lock/transaction availability failures503. Unknown results remain private and explicitly direct the caller to retry the original request.
- No application users lock, journal read privilege, metadata/account INSERT privilege, new helper, schema/migration change or fallback root was introduced. Actual production `create_app` mounts every endpoint through the existing owned portfolio module; integration tests contain no temporary router registrations.

## Verification Evidence

The final command used the existing Python3.14.9 environment, an explicitly stripped environment and the owned disposable test stack:

```text
env -i PATH="$PATH" HOME=/tmp UV_OFFLINE=1 backend/.venv/bin/python -m pytest \
  --rootdir=backend backend/tests/test_portfolio_creation.py \
  backend/tests/test_portfolio_metadata.py backend/tests/test_portfolio_management_api.py \
  -x -q --cov=app.api.v2.portfolio_management --cov=app.services.portfolios \
  --cov=app.schemas.portfolios --cov=app.api.v2.portfolios \
  --cov-branch --cov-fail-under=100
```

- Cookie/CSRF precede malformed or oversized bodies; missing/revoked sessions401 and bad CSRF403, with private headers. Malformed shapes, controls, nulls, authority fields, media, UUID casing/version/length and canonical path bounds refuse without roots or journal growth.
- Independently concurrent same-key requests create exactly one grant; distinct-key races permit only the tenth active root. SQL Unicode tests cover NFC equivalents, sharp-s casefold, sigma/final-sigma,60/61 astral name limits, active owner collisions and same-name reuse by another owner.
- Original canonical key/payload replays after rename and active-cap exhaustion; changed intent conflicts. Closed original replay404 does not bind to a replacement reusing its name. A real committed service result followed by an injected response failure returns private500, and the original retry recovers200 without another grant.
-100 real successful explicit grants, with99 closed fixtures, yield a durable quota429 for a new intent and200 for the original replay. Monetary evidence remains exactly100 journal rows and1000000 granted.
- A real competing owner lock triggers the SQL2-second lock timeout, private503, complete rollback and later successful original-key retry. Direct restricted-service calls prove actual22023 rollback and unknown42501 rollback/rethrow on both helpers; owned EXECUTE grants are restored afterward. These direct negative service probes do not claim API admission while grants are intentionally revoked.
- Metadata description view/edit/clear, exact1000/1001 astral limits, preserved markup text, rename conflict, foreign/closed/unknown404 privacy, CSRF and invalid paths pass. Before/after byte comparisons include nonempty actual BTC holdings and trade History, cash/baseline, immutable original canonical journal and other financial ledgers. Stock ledgers are empty in this fixture; active stock/split/dividend scenarios remain Plan14.
- Existing statement GET reads the created root and original10000.00 cash/baseline and refuses the foreign owner. No DELETE/freeze public endpoint exists.

## Deviations from Plan

**1. Planner quota contradiction resolved without authority changes.** Initial Plan06/COVERAGE said20 new grants/day while prior research and the implemented, reviewed0020 SQL said100. The parent confirmed these were planner-discretion resource values, corrected Plan06/COVERAGE and recorded the decision in `f55b416`. Implementation retains durable100/day and exact existing grants. No Redis-only daily funding quota or new privilege was added.

**2. [Rule3 - Blocking] Explicit current-schema test harness.** The retained ordinary migration-owner fixture still enumerates0017, and current ordinary admin runtime grants are intentionally not finalized until Plan15. The owned tests reuse the prior explicit authority migration harness, apply source-owned current `GRANTS_SQL` to the exact disposable database, authenticate a real birja_app login, and enter actual production lifespan/admission. Shared conftest, inventories and admission were not weakened or edited. Committed in `29effb1` with the Task2 proof.

Routine test corrections addressed async collection syntax and the existing two-decimal statement transport expectation. The first nested-router composition was replaced by the existing portfolio router's management route class before GREEN. No remaining product defect or scope expansion was established.

## Cleanup and Limits

- Owned Compose project `birja-p13-06` used only cached pinned PostgreSQL/Redis images, guarded55432/56379 ports and disposable tmpfs. App fixtures explicitly use fake prices and console email. Its containers and network were removed; exact Compose project label queries for containers/networks/volumes return empty.
- No package, lockfile, image/Python pin, immutable0015–0020 migration, private environment, provider, production, deployment, push or merge operation occurred. Unrelated `.claude/` is preserved. Issue35's existing exact accepted risk/deadline2026-12-17T00:00:00Z and Phase7 OFF remain unchanged.
- Stub scan found only intentional empty metadata defaults, the JSON duplicate-field accumulator and existing unrelated config defaults; no unfinished implementation stub prevents this plan's goal. New network surfaces are the planned authenticated management routes; no additional unmodeled trust boundary was introduced.
- Parent owns independent review plus STATE/ROADMAP/REQUIREMENTS updates. Requirement IDs above record this plan's contribution, not whole-requirement acceptance. Plan15/17 still own complete inventories, whole suites/security and encrypted/TLS/image qualification. Browser/UI/native200 acceptance remains later work. This summary makes no phase-completion or full-campaign claim.

## Self-Check: PASSED

All8 listed source/test paths and this summary exist; all4 task commits resolve. RED precedes GREEN for both tasks. Scoped verification, source typing/lint/format and cleanup pass. Only unrelated `.claude/` remains untracked.
