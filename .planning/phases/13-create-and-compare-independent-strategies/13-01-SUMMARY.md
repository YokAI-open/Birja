---
phase: 13-create-and-compare-independent-strategies
plan: "01"
subsystem: database
tags: [postgresql, alembic, unicode, portfolios, provenance]
requires:
  - phase: 12-preserve-existing-investing-under-portfolio-ownership
    provides: Qualified source4b4320b, immutable0017 owned financial lineage
provides:
  - Additive0018 metadata and permanent owner-bound creation/initialization models
  - Resumable0019 all-existing-user legacy latch without invented grants
  - Authoritative Unicode metadata and concurrent active-owner name uniqueness
affects: [13-02, 13-03, 13-04, 13-05, 13-06]
tech-stack:
  added: []
  patterns: [migration-only expansion and backfill, bounded committed batches, private SQL canonicalizers]
key-files:
  created:
    - backend/app/models/portfolio_creation.py
    - backend/alembic/versions/0018_portfolio_management_expansion.py
    - backend/alembic/versions/0019_portfolio_management_backfill.py
    - backend/alembic/sql/0019_portfolio_metadata.sql
    - backend/tests/test_portfolio_management_migrations.py
  modified:
    - backend/app/models/user.py
    - backend/app/models/__init__.py
key-decisions:
  - "Legacy initializations have origin legacy and NULL root/creation references; no historical grant is invented, including zero-book users."
  - "Creation evidence uses UUID keys, version1 canonical_payload JSONB, fixed Decimal10000 amount and paired owner/root lineage; initialization links the original initial creation."
  - "Metadata and baseline validation runs through a private SECURITY DEFINER trigger, keeping canonical helpers private without breaking ordinary cash updates."
  - "Use PostgreSQL's actual pg_catalog.pg_unicode_fast collation identifier; PG_UNICODE_FAST is its locale, not a quoted catalogue name."
patterns-established:
  - "Migration-only closed-root key association compares every other old/new row field, then restores the exact0017 financial trigger and drops the temporary helper."
  - "Concurrent index recovery rebuilds only the exact migration-owned invalid index; incompatible definitions refuse."
requirements-completed: [PMGT-02, PMGT-06, PFUND-01, PFUND-02, PSAFE-07]
duration: 15min
completed: 2026-11-18
---

# Phase 13 Plan 01: Canonical Metadata and Durable Provenance Summary

**All legacy identities receive a grant-free initialization latch while exact financial rows survive Unicode metadata backfill and active-owner name enforcement.**

## Performance

- **Duration:** approximately15min, 2026-11-18 07:44–07:59UTC
- **Tasks:** 2/2
- **Implementation/test files:** 7, plus this summary
- **Final acceptance run:** 14passed in37.28s

## Accomplishments

-0018 adds empty-default descriptions, nullable expansion keys, permanent creation bindings and explicit legacy/initial initialization provenance. Bigint identities, UTC times, NUMERIC(20,8), fixed10000 amount, payload version/shape, paired owner FKs, real lookup indexes and append-only triggers protect evidence. No cascading deletion is introduced.
-0019 preflights every existing name before any durable backfill, refusing noncanonical or duplicate active names without renaming. Every existing user receives legacy provenance, including zero-account and closed-only identities. Creation journals remain empty; no financial grant or replacement root is fabricated.
- Batches commit at most500 rows. A test interrupts after the first500 of507 users, observes that committed state independently, resumes and proves exact old-row equality. Closed roots receive only their missing canonical key; all other fields must match. Completion restores `portfolio_root_immutable` to original `check_portfolio_financial_write()` and drops `associate_portfolio_metadata_only()`.
- SQL owns explicit White_Space trim, raw C0/C1 rejection, NFC display,1–60 scalar bounds, full Unicode casefold/NFC key and deterministic C uniqueness per active owner. Descriptions preserve whitespace, normalize CRLF/CR to LF, permit TAB/LF and enforce0–1000 scalars. Private SQL triggers reject forged keys, noncanonical payloads and baseline mutations.
- Actual failed `CREATE UNIQUE INDEX CONCURRENTLY` leaves an invalid index; rerun rebuilds that exact owned object. A different preexisting definition refuses instead of being dropped.

## Task Commits

1. **Task1 RED:** `14aa73b` — Add expansion and provenance migration contracts; actual missing-model failure.
2. **Task1 GREEN:** `d76d5a8` — Add owner-bound creation and initialization provenance;4passed in6.63s.
3. **Task2 RED:** `0cc6333` — Specify canonical metadata and resumable legacy backfill; actual missing0019 failure with retained financial fixtures.
4. **Task2 GREEN:** `82c9214` — Backfill legacy provenance and canonical portfolio metadata; final14passed in37.28s.

## Verification

The isolated harness explicitly migrates0014/0017/0018/0019; it does not request `migrated`, current-app lifespan or partial-schema admission. The existing shared0017 fixture and admission code remain unchanged. Source0017 explicitly refuses0019. Both new downgrade functions refuse before writes, retaining provenance and financial evidence.

Final command, from `backend/`, using the existing Python3.14 venv and stripped synthetic environment:

`env -i PATH="$PATH" HOME=/tmp ENV=test PRICE_SOURCE=fake EMAIL_BACKEND=console .venv/bin/python -m pytest tests/test_portfolio_management_migrations.py -x`

Result: **14passed in37.28s**. Cases cover expansion, crossed-owner FK refusal, fixed amount/NaN refusal, legacy-without-grant shape, safe downgrade refusal, retained0014→0017→0019 complete old-row preservation with holdings/trades/stock/dividend evidence and unequal baselines, zero/closed-only users, fresh migration, Unicode/astral/control/count corpus, owner/closed-name uniqueness, forged metadata/baseline refusal, append-only journals, noncanonical/duplicate legacy refusal, stale SQL checksum refusal, durable interruption/resume and actual concurrent-index failure recovery/object-drift refusal.

Focused six-file Ruff lint/format, three-model mypy and `git diff --check` pass. A direct diff against actual qualified4b4320b confirms0015/0016/0017 Python and both0017 SQL assets unchanged. No whole-suite, coverage, TLS, current0020 authority, recovery or UI acceptance pass is claimed.

## Source and Authority Handoff

- SQL asset SHA256: `a26d4230843f75af9202fce71a771818d0bd7f041777a8a01a0d53a8df7a7c65`, checked before installing helpers or backfill writes.
- Final new private functions: `portfolio_display_name(text)`, `portfolio_name_key(text)`, `portfolio_description(text)`, `check_portfolio_management_metadata()`. All are owned by `birja_migrator`, fixed-search-path and revoked from PUBLIC. The three canonicalizers are immutable SECURITY INVOKER; the trigger validator is SECURITY DEFINER. No ordinary creation/latch access is granted by0018.
- `portfolio_creations`: `id,user_id,creation_key,portfolio_id,origin,payload_version,canonical_payload,amount,created_at`. Permanent owner/key and root uniqueness; origin initial/explicit; version1; JSON object exactly name/description strings; fixed amount10000. Payload/key canonical validation is installed by0019.
- `portfolio_initializations`: `id,user_id,origin,portfolio_id,creation_id,created_at`. One per user; legacy has both references NULL, initial has both required and paired to an initial creation. Both new tables reject UPDATE/DELETE through the existing immutable ledger function.
- Account final metadata validation is trigger-owned rather than helper-calling CHECK expressions: restricted cash writers need no direct canonicalizer EXECUTE. Accounts have non-null C-collated `name_key` after0019 and partial unique `uq_accounts_active_name(user_id,name_key) WHERE closed_at IS NULL`.
- New revisions remain migration-only; writers must stay stopped through0020. Plan02 installs creation/onboarding/metadata entrypoints;03 owns exact runtime/source admission and grants. Full-current/retained source profiles and recovery inventories remain04/05. Default head is intentionally intermediate during this plan; normal app suites must wait for finalization, rather than weakening admission.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule1 - Bug] Corrected the planned quoted collation identifier.** PostgreSQL18.7 rejects `pg_catalog."PG_UNICODE_FAST"`; actual builtin collation is `pg_catalog.pg_unicode_fast`, whose locale is PG_UNICODE_FAST. Official [PostgreSQL18 collation documentation](https://www.postgresql.org/docs/18/collation.html) and the owned test catalogue agree. The intended Unicode full-casefold semantics and independently expected corpus pass unchanged. Fixed in Task2, commit `82c9214`.

**2. [Rule2 - Correctness] Added a narrowly bounded closed-root backfill guard.** Original0017 correctly refuses every closed-root UPDATE. The temporary migration-only guard permits only NULL→canonical key with full equality of every other old/new field and authenticated migrator identity. It is dropped after restoring the exact original trigger; preservation/resume tests pass. No immutable migration or financial function body changed. Fixed in Task2, commit `82c9214`.

No architecture, package, lockfile, image pin or scope changes. The test injection harness required Alembic's actual per-migration transaction setting to exercise committed interruption; production migration commands already use that setting.

## Resource and Publication Boundaries

Only owned `birja-p13-01` disposable PostgreSQL/Redis resources ran, with pinned cached images, synthetic credentials, fake prices and console email. Docker/local-socket/git sandbox restrictions used scoped escalation. Exact project labels were checked before teardown; final container/network/volume queries for that project return empty. No private env, provider call, application activation, push, merge or deployment was performed. Shared STATE/ROADMAP/REQUIREMENTS and unrelated `.claude/` remain parent-owned and untouched by this executor.

Issue35's exact accepted artifact/path/version policy and2026-12-17T00:00:00Z expiry remain unchanged, as does the approved Python image pin20261111. This plan adds no waiver.

## Next Plan Readiness

Ready for parent independent review and13-02. The requirements list above records this plan's assigned coverage; whole requirement completion still depends on downstream API/authority/resource/recovery and final phase proofs. Shared state updates are delegated to the parent under its explicit single-writer ownership instruction.

## Self-Check: PASSED

All seven declared implementation/test files exist. All four recorded task commits exist, with RED before GREEN for each task. Immutable prior migration/SQL bytes match qualified4b4320b. Final tests, scoped static checks and owned-resource cleanup pass. No implementation stubs or unplanned trust surfaces were found; nullable legacy provenance is intentional and tested.
