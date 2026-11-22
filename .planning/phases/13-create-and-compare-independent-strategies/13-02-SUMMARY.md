---
phase: 13-create-and-compare-independent-strategies
plan: "02"
subsystem: database
tags: [postgresql, alembic, portfolios, funding, idempotency, authentication]
requires:
  - phase: 13-01
    provides: Canonical private metadata helpers and permanent creation/initialization provenance
provides:
  - Source-hashed0020 fixed-grant creation, initialization and metadata authority
  - Owner-serialized permanent replay, active cap and durable UTC-day new-grant quota
  - Genuine signup winner invokes initialization inside the caller transaction
affects: [13-03, 13-04, 13-05, 13-06, 13-14, 13-17]
tech-stack:
  added: []
  patterns: [narrow definer entrypoints, owner then account locking, explicit revision restricted-role tests]
key-files:
  created:
    - backend/alembic/versions/0020_portfolio_management_authority.py
    - backend/alembic/sql/0020_portfolio_management.sql
    - backend/tests/test_portfolio_management_authority.py
    - backend/tests/test_portfolio_funding.py
  modified:
    - backend/app/services/accounts.py
    - backend/tests/test_portfolio_identity.py
key-decisions:
  - "Successful permanent owner/key/canonical-payload lookup precedes all mutable cap, active-name and daily-quota checks."
  - "Creation returns current metadata and original identity; a closed original refuses permanently, with no replacement grant."
  - "Only100 successful new explicit grants per owner per UTC day consume the durable budget; initial onboarding and successful replay do not."
  - "Initialization returns the existing latched root or NULL for legacy empty provenance; it refuses unlatched identities already holding books."
  - "Use genuine restricted app login in explicit0020 fixtures; final current-source admission and complete grants remain Plan03."
patterns-established:
  - "Management functions lock owner then target, with function-local2s lock_timeout, and never acquire stock instrument locks."
  - "Signup unique-email winner calls initialize_portfolio with bound parameters and never commits inside accounts service."
requirements-completed: [PMGT-01, PMGT-02, PMGT-06, PFUND-01, PFUND-02]
duration: 12min
completed: 2026-11-18
---

# Phase 13 Plan 02: Serialized Grants and Onboarding Summary

**Permanent creation replay and narrow owner-locked authority grant exactly10000 per new strategy, while returning sign-in never refills empty identities.**

## Performance

- **Duration:** approximately12min,2026-11-18 08:02–08:15UTC
- **Tasks:**2/2
- **Implementation/test files:**6, plus this summary
- **Focused verification:**18 authority cases passed in57.47s; the two subsequently strengthened authority cases passed in9.75s;17 funding/identity cases passed in52.50s.

## Accomplishments

-0020 installs exactly three public management entrypoints, owned by `birja_migrator`, SECURITY DEFINER with fixed `search_path=pg_catalog,public,pg_temp` and function-local `lock_timeout=2s`. PUBLIC and scheduler execution are revoked; app receives exact execution privileges. Ordinary account INSERT and account-sequence usage are revoked. No users UPDATE, ordinary metadata UPDATE, or provenance mutation grant is introduced. Private0019 canonicalizers remain private.
- Creation locks the user row, canonicalizes name/description with the existing SQL authority and consults permanent journal evidence before mutable active-count/name/quota checks. Matching active replay returns the original root/creation IDs and current metadata without money. Changed original payload conflicts; closed original is permanently unavailable even after name reuse. New intent checks fewer than10 active roots, canonical active-name uniqueness and fewer than100 successful new explicit grants in the current UTC day. Root, fixed10000 baseline/cash and immutable journal commit atomically.
- Initialization locks the user and returns the existing latch result without granting again, including after root closure. Legacy provenance returns NULL. Absent-latch initialization requires an empty identity and inserts `My portfolio`, empty description, fixed10000 cash/baseline, initial journal and initial latch together. An unlatched identity already holding books refuses rather than inventing onboarding provenance.
- Metadata authority locks user then owned active target, validates explicit field-presence flags and updates only name/key/description. Missing fields remain unchanged; empty descriptions clear normally. Cross-owner/closed targets refuse; baseline, identity, closure and financial rows remain outside this entrypoint.
- `get_or_create_user` preserves the unique-email INSERT winner and caller-owned transaction. Only that winner calls bound `SELECT public.initialize_portfolio(:user_id)`. Returning lookup never initializes or repairs books; no helper commit or active-count inference is added. Public `STARTING_CASH` stays for existing test imports, while SQL owns actual grant amounts.

## Task Commits

1. **Task1 RED:** `8de4190` — Specify restricted portfolio grant authority. Actual PostgreSQL missing-function failure before implementation.
2. **Task1 GREEN:** `5eb78f1` — Install serialized portfolio grant authority.18 cases pass, plus strengthened scheduler/source-refusal cases.
3. **Task2 RED:** `a1cdf1c` — Specify atomic once-only onboarding funding. Actual restricted-role42501 proves old direct account INSERT cannot work under0020.
4. **Task2 GREEN:** `a8e8efe` — Initialize new identities through grant authority.17 funding/identity cases pass.

## Verification

Using existing Python3.14 venv and a stripped synthetic environment from `backend/`:

`env -i PATH="$PATH" HOME=/tmp ENV=test PRICE_SOURCE=fake EMAIL_BACKEND=console .venv/bin/python -m pytest tests/test_portfolio_management_authority.py -x --tb=short`

**18passed in57.47s.** Fixed funding/canonical journal, matching/conflicting replay after rename, permanent closed refusal after name reuse,8-session same-key race,6-session tenth-slot race, canonical name race/other-owner name reuse,9 invalid input cases without durable rows, owned/closed metadata and field presence, ordinary INSERT/metadata/baseline/closure/users UPDATE denial, private helper denial, immutable provenance, forged amount overload refusal, preserved ordinary cash UPDATE,100-new-grant quota and replay ordering, definer catalogue and bounded owner lock waits all pass.

The final two authority tests were then strengthened to deny scheduler execution of **all three** entrypoints and execute an actual wrong-source-hash migration refusal with unchanged function definition. Their focused command passed **2cases in9.75s**, also retaining before-write downgrade refusal and evidence preservation. There was no subsequent authority implementation change.

`env -i PATH="$PATH" HOME=/tmp ENV=test PRICE_SOURCE=fake EMAIL_BACKEND=console .venv/bin/python -m pytest tests/test_portfolio_funding.py tests/test_portfolio_identity.py -x --tb=short`

**17passed in52.50s.** Tests cover initial root/journal/latch, explicit additional grants, closure/empty returning identity,8 concurrent email winners, signup rollback and independent visibility, legacy empty latch,8 concurrent initializer calls, malformed initialization, zero/one/many/closed custom legacy books, OTP single use, refresh/logout and new OTP signup. Every normal service call uses an authenticated restricted app connection; legacy fixtures use a separate migrator connection.

Five changed Python files pass Ruff lint/format; `mypy app/services/accounts.py` and `git diff --check` pass. Prior0015–0019 Python and0017/0019 SQL bytes are unchanged against the Plan01 handoff commit028e5ad. No full backend suite, coverage gate, application admission, TLS/recovery/security campaign or browser acceptance pass is claimed.

## SQL and API Handoff

- SQL asset SHA256: `ff97c417260fd9ed80f70c3a51ddfe32837b9b41c803bfcce4e7f37bc33be9d2`, checked before any migration SQL writes. Existing immutable0017 parser splits the source asset;0015–0019 are untouched.
- `create_portfolio(bigint,uuid,text,text)` inputs: `p_user,p_key,p_name,p_description`. Returns TABLE`(portfolio_id bigint,name text,description text,creation_id bigint,replayed boolean)`.
- `initialize_portfolio(bigint)` input `p_user`; returns bigint original initial root or NULL for legacy latch. Intended caller is solely the unique-email INSERT winner.
- `update_portfolio_metadata(bigint,bigint,text,text,boolean,boolean)` inputs `p_user,p_portfolio,p_name,p_description,p_has_name,p_has_description`. Returns TABLE`(portfolio_id bigint,name text,description text)`.
- Domain SQLSTATE/message pairs:22023 invalid input;P0002 `portfolio_unavailable` or `initialization_unavailable`;23505 `creation_key_conflict` or `name_taken`;23514 `portfolio_limit`;P0001 `creation_quota`;55P03 bounded lock timeout. Future service/API mapping must use private bounded errors and preserve unknown-outcome original keys.
- Authenticated owner IDs must come from server authentication, never a browser owner field, caller GUC or SET ROLE. App role is a service identity able to act for its authenticated users; the DB does not pretend it authenticates an end user.
- Current app/schema/source admission and complete bootstrap/recovery grant inventories remain **Plan03–05**. The explicit0020 test harness grants only necessary existing service rights and executes new migration-owned authority; it never starts a partial-schema application or loosens existing0017 admission. Staged tests tear down only their guarded disposable schema. Later whole-suite qualification must account for staged-fixture lifecycle rather than infer readiness from these tests.

## Deviations from Plan

None. Identity fixtures were adapted locally within their owned file, as the plan explicitly permits: explicit0020 restricted app sessions plus migrator-only legacy setup replace the old broad fixture. No cross-owned fixture or admission edit was needed.

During GREEN verification one test helper mistakenly selected the nonexistent-function SQLSTATE for a denied forged journal INSERT because both SQL strings ended with`,20000)`. Selecting by the actual function-call prefix corrected the expectation; PostgreSQL correctly denied the write throughout. No production authority repair was required.

## Resource and Publication Boundaries

Only owned `birja-p13-02` PostgreSQL/Redis resources ran with pinned cached images, stripped synthetic environment, fake prices and console email. Scoped escalation allowed local Docker/test sockets and task commits. Exact project labels were checked before teardown; final container/network/volume queries for the project return empty. No private.env, provider request, install, dependency/lock/pin change, production inspection, push, merge or deployment occurred. The branch remains local `feature/milestone-v1.2`.

Issue35's exact accepted artifact/path/version/target policy and2026-12-17T00:00:00Z expiry remain unchanged, as does the approved Python image pin20261111. No new waiver is introduced. Public deletion/freeze activation remains Phase14.

## Next Plan Readiness

Ready for parent independent review, then13-03 exact current admission/grants. The assigned requirements above record plan coverage, not whole-phase completion. Parent retains exclusive ownership of STATE/ROADMAP/REQUIREMENTS updates; this executor did not modify or stage them. Unrelated `.claude/` is preserved.

## Self-Check: PASSED

All six declared implementation/test files exist. All four task commits exist, with RED before GREEN for each task. Focused verification and static checks pass; immutable prior migration bytes match the handoff. No implementation stubs or unplanned trust surfaces were found. Owned disposable resources are removed. Shared planning state remains parent-owned.
