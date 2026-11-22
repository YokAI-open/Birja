---
phase: 12-preserve-existing-investing-under-portfolio-ownership
reviewed: 2026-11-17
depth: standard
reviewed_head: 05426f76640f0d15ca27551b723dd07d766b3bb6
files_reviewed: 1
files_reviewed_list:
  - deploy/tests/fixtures/portfolio-recovery-0017.json
coverage: complete_structured_data_integrity
files_unreviewed: 0
fixture_sha256: 41d592c77d311404a20e645ffb9b009468eb82379765435502f5e3fc159f3aec
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 12: Generated Recovery Catalogue Review

## Narrative Findings (AI reviewer)

No additional catalogue-integrity defect was found. This closes the single
generated-fixture coverage remainder in `12-REVIEW-FRONTEND-OPS-REMAINING.md`.
It does **not** close the separately established CR-01 execution defect or
CR-02 cold-image provenance defect, and it does not declare the phase complete.

The reviewed file is a generated, single-line JSON catalogue. It was parsed
and examined as structured data, with complete entry enumeration, source-body
identity checks and independently specified grant comparisons. Its size was
not handled by trusting a truncated raw-file display. This is a data-integrity
review of the entire fixture, not a claim to have repeated a new adversarial
audit of unchanged historical routines merely because their text is copied
into the fixture.

### Complete entry coverage and method

| Section | Entries | Verification performed |
|---|---:|---|
| Relations | 27 | Exact static final-schema table vocabulary; all are ordinary tables, with no extra view/foreign/partition relation |
| Columns | 308 | Exact per-table column sets; types, nullability, defaults and precision/scale examined; money remains NUMERIC and the exact stock midpoint retains its deliberate extra digit |
| Identity descriptors | 308 | Same complete table/column inventory; only the twenty intended bigint identity columns use GENERATED ALWAYS |
| Constraints | 569 | All unique by relation/name and validated: 255 NOT NULL, 184 CHECK, 65 FK, 27 PK, 35 UNIQUE and three deferred trigger constraints; all 255 NOT NULL entries match column nullability |
| Indexes | 117 | Unique names, all valid/ready; portfolio query keys, compound causal keys and retained user-global retry uniqueness checked against migration definitions |
| Sequences | 20 | Exact identity-table set, bigint bounds, increment/cache one, no cycle; all empty-fixture identity states are `(1,false)` |
| Functions | 10 | Every complete embedded body is byte-equal to its authoritative checked-in migration/SQL source; headers, return/OUT declarations, owner, definer mode, search path and effective EXECUTE ACL examined |
| Triggers | 25 | All enabled; root locking, active insertion, immutable financial rows, deferred stock integrity and NULL-or-2 digest-marker triggers match final migration/assets |
| Object owners | 47 | Exactly 27 tables plus twenty sequences, all owned by `birja_migrator` |
| Role attributes/membership | 4/0 | All six recorded elevated/inheritance flags false; no role membership edge |
| Table ACL rows | 81 | Every role/table privilege tuple compared to an independently transcribed final bootstrap policy |
| Column ACL rows | 924 | Every effective role/table/column tuple compared to table inheritance plus the exact narrow column grants |
| Sequence ACL rows | 60 | Every tuple compared to the explicit app/scheduler USAGE allowlists; no SELECT/UPDATE grants |
| Schema CREATE/unsafe ACL | 3/0 | No ordinary-role CREATE and no unsafe public/grantable/foreign-role object ACL |
| Table data projections | 27 | Every fixture projection is explicitly empty with the SHA256 of empty bytes; no populated financial proof is inferred |
| Remaining scalar/state data | All | Revision0017, server metadata, empty financial/state counters, zero invalidity and deliberately NULL predecessor authority sections agree with the selected final manifest format |

The entire schema and authority canonical hashes independently match the
source-owned pins in `deploy/backup-snapshot.py:707` and following:

- Schema: `a5426b54a96f536cdf6e76dd29b897a1b51b2d8ec681d36ddced25ce24b2467e`.
- Authority: `dfbad9886f0426961b93391eeca78bce148202998bc1153b1932fc6012d3ba46`.

Those matches supplement the semantic/source checks below; hash equality alone
was not used to conclude that an independently generated oracle is correct.

### Embedded routine source identity

Every fixture definition has the correct `public` name, exact parameter and
return declaration, PL/pgSQL language and `birja_migrator` owner. The table lists
the SHA256 of the complete body between its dollar quotes, including whitespace.

| Routine | Authoritative source | Complete body SHA256 |
|---|---|---|
| apply_stock_action_resolution | `backend/alembic/versions/0012_stock_action_resolution.py` literal | `692bc69bb4c4045aa9b65c8c2dee00fc00cf684763076a6c08e91e4609d2ce4d` |
| apply_stock_dividend | `backend/alembic/sql/0017_dividend_portfolio.sql` | `e9b7686f3b17b5a1df89e351d01c8244a610de03346f847f5ad8c7a3d20ef99e` |
| assert_stock_execution_current | `backend/alembic/sql/0017_stock_portfolio.sql` | `d3da8748084a3458b63ef1a51435b8decc28b1bac8b522fbefd746d62555f907` |
| check_portfolio_financial_write | `backend/alembic/versions/0017_portfolio_ownership.py` literal | `606f8a858caf900d9e20239a2dd49575a84976a77ab73289458b51e4aad9125c` |
| check_stock_fill_integrity | `backend/alembic/sql/0017_stock_portfolio.sql` | `55c8f44882c787923bb9f1ac2e6e26fc2493d7eced19c48d40560e5f042b290b` |
| check_stock_split_digest_version | `backend/alembic/sql/0017_stock_portfolio.sql` | `bea15354f486b6df5fe7d3d2687c98ae5b98082aebb350cf83b12fc0b3ee833d` |
| lock_stock_portfolio_roots | `backend/alembic/versions/0017_portfolio_ownership.py` literal | `ccd98d6b645d315b9a4b308a2dd28d7727b8a15565b36a9b83cce7a3ad4809c9` |
| record_stock_dividend_hold | `backend/alembic/sql/0017_dividend_portfolio.sql` | `cbab7352d3964e2ed79d88748cbd6c6428ba0c29bc8652fc2a3ba79d96b6612d` |
| reject_stock_dividend_mutation | `backend/alembic/sql/0017_dividend_portfolio.sql` | `bbb7ec48f270806ecc4273ce5fb5996c26d2c7a84c8edb9c47de20a9c09016d7` |
| stock_dividend_authority | `backend/alembic/sql/0017_dividend_portfolio.sql` | `a3085991a1d8397bb446f47aabf285b6c3f97d5bf45ea72e7982ab360d34ed12` |

The source-body matches also agree with the finite body checks in
`backend/app/db/portfolio_bootstrap.py`. The two payout routines retain the
declared `payment_id`, `decision_id`, `outcome` TABLE outputs. Their shape is
not inferred solely from input argument identities.

There is no hidden PUBLIC EXECUTE or grant option. Effective non-owner EXECUTE
is limited to operator/resolution, app/final execution assertion, and scheduler/
payout, hold and lock-only helpers. Trigger routines and the inner dividend
authority have no ordinary direct executor. SECURITY DEFINER is present only
on resolution, payout, hold, root-write and root-lock routines. Search paths are
the reviewed fixed paths; the retained resolution body remains byte-identical
to its preceding migration rather than being rewritten by this fixture.

The copied execution body includes the already reported CR-01 predicate. A
faithful oracle can copy a product defect; this review confirms fidelity and
does not claim that matching the old body closes CR-01. After its repair, the
new execution body, bootstrap/source pins and affected authority catalogue
hashes must be reconciled and independently rechecked.

### Schema and privilege semantics

The seven owned financial tables have required `portfolio_id` columns and
compound `(portfolio_id,user_id)` root references. Fill/movement trade links,
entitlement supersession and payment/decision chains retain their complete
portfolio/owner/event/revision causal keys. Global split applications have
neither `portfolio_id` nor `user_id`; `owner_digest_version` is nullable
SMALLINT with no default and a NULL-or-2 check. Owned split movements use the
per-application/per-portfolio uniqueness key. The root `user_id` uniqueness
was removed, while the existing `(user_id,idempotency_key)` fill key remains.
Terminal closure rows retain their root/owner/stock identity and immutable
closure sequence/epoch constraints.

All 924 column permissions were compared to the independently read final
bootstrap policy, not copied into expectations from the fixture. The only
column-level additions to inherited table permissions are:

- app cash UPDATE on accounts, and quantity/cost-basis UPDATE on holdings;
- scheduler quantity UPDATE on holdings and current-revision UPDATE on events;
- operator SELECT on the five declared coin catalogue columns.

There is no whole-table account/holding UPDATE, ordinary financial DELETE,
TRUNCATE, REFERENCES, TRIGGER or MAINTAIN grant. The scheduler has no direct
cash UPDATE or payment/decision INSERT. The source catalogue's narrow economic
EXECUTE grants are distinct from cold quarantine: `restore_portfolio_authority`
authenticates the fixed no-ACL catalogue, revokes PUBLIC/ordinary EXECUTE on
all ten authenticated signatures, applies the fixed grants and then removes
payout/hold/root-lock execution. That source/quarantine distinction is preserved
by the separately pinned authority hashes and the contract consumers.

### Oracle independence and limits

The fixture is a static reference consumed by the offline recovery contracts;
the producer does not generate its expectations from the database it is about
to authorize. Fixed source inventory, static hashes and migration-owned SQL
remain separate from the observed manifest. Existing mutation contracts cover
omitted/extra fields and schema objects, marker shape, routines, owner/ACL,
trigger and root/cause corruption. The empty financial projections are useful
for those catalogue contracts only; the populated independent execution books
and actual encrypted restore campaign provide the economic proof.

No tests, DB commands, Docker processes, network/provider operations, source
edits or commits were performed for this pass. Inspection used JSON/AST
parsing, complete routine-body byte comparisons, complete finite permission
matrix comparisons, schema-entry enumeration and reading the authoritative
migration/bootstrap/consumer code. The main checkout remained at the recorded
head and the reviewed fixture hash stayed unchanged.
