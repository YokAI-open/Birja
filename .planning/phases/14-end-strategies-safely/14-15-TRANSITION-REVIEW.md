# Plan15: authenticated closure migration transition

Status: locally verified; independent parent review remains pending. No release,
deployment or whole-phase acceptance is claimed. Parent authorized this runtime and
current-source pin amendment after the real TLS upgrade refused.

## Observed failure

Starting from actual0020 runtime grants, migration0023 produces a correct
catalogue but a distinct intermediate object ACL. Python and administrative SQL
preflights previously rejected it before the required explicit final bootstrap.
The older upgraded fixture had never installed0020 runtime grants, so it did not
exercise this state. No old grants were removed to make the proof pass.

Measurements used private synthetic PostgreSQL over verified TLS, exact frozen
runtime images from source2522ecc78687246997b6943815b23a73315a05f6, and separately
authenticated qualified0020 literals. Private receipts are under
`/tmp/birja-phase14-plan15/upgrade-delta.json`, `upgrade-initial.stdout` and
`upgrade-partials.stdout`; these contain metadata, not real user rows or keys.

## Finite measured states

| Revision | Exact catalogue SHA256 |
|---|---|
|0020|535cacb140a3a1753b5cf27e2eadcb80bc272a9b12772defd3936a3edc6c2209|
|0021|748dc0f3a3a1eb63a3168cb7a21198d6ac3a59135f35d0700772b79394bed3b4|
|0022|1e24357696abc34020f4fc2ce67f9ca327c7eed48477a5a484a7d2a9d4789b46|
|0023|59aeeee9428fac73f96143cc8afdd77e3b6a8f81b30ed37b752666579d69a66e|

The prior20/21/22 entry recognizer permits exactly initial authority
`3358f6b32d6211d60c93516488ee5c6e7434c775c812c2fe0841b5011fe74a06` or
qualified runtime authority
`041a948470f9692628da43b35263a47bf58f4815310a0793d5eec099fa64c87e`,
paired with either PostgreSQL's built-in implicit global function default
`3c6c72d38f50b3150f0c849954fa0842a0711cfcbda15936e470bc648d436ebe` or
private defaults
`4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`.
Explicit nonowner future-default grants refuse independently, as do role,
ownership, schema and catalogue mismatches. This supports initial/resume states
without an arbitrary ACL fallback. Older7–19 retained behavior remains unchanged.

After real runtime20 grants and migration23, the measured object ACL is
`f900b495d58d21eb1eaa04eac9445b1212810f751c254fb4c13e31b54c77f425`.
The exact difference from final authority consists of four missing SELECTs:
both `birja_app` and `birja_scheduler` need SELECT on
`portfolio_lifecycle_closures` and `portfolio_closure_intents`.
Adding only those four metadata rows independently recomputes the existing final
ACL hash. The same two measured default states occur with this exact transition
ACL. Any partial read grant, missing final read, extra grant or unsafe future
default is outside the finite entry profiles and must refuse without repair.

## Controls preserved

- `require_migrator` authenticates exact prior catalogue/ACL/defaults and existing
  identity/role/configuration rules before Alembic is spawned. Every20/21/22
  entry is explicit; ordinary runtime still refuses21/22.
- The new23 state permits explicit bootstrap only. `require_schema` still
  requires final ACL
  `71896f41a9310ada0af0961b78e78f5364654f1513c11bf9310c250ad545f748`
  and private defaults
  `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`.
- Existing generic20/17 literal values, all migration bytes, authority SQL SHA
  `59577ba16c9e9ea9740c2cb0d171b7006931bb6b1b9e5d0408c9a6f673f7c920`,
  catalogue and financial/schema authority fingerprints stay unchanged.
- Current producer/consumer source maps and selected deployment source checks
  gain the same explicit current migrator pin. Retained source identities stay
  fixed at9527e35 and4b4320b.

## Verification required before completion

Real initial/runtime/resume tests cover both default variants. Drift tests for
every20/21/22 entry must refuse before child creation and preserve evidence.
Python and independent SQL must refuse every partial or missing lifecycle read,
extra grants and unsafe defaults without changing31-table/24-tail evidence.
Current source pins, producer/consumer contracts, exact fresh/upgraded TLS and
encrypted cold restore must be rechecked on newly committed source and a new
private archive. Earlier archive/proof receipts remain intact.

The earlier3538-case backend evidence is explicitly partitioned diagnostic
evidence. A fresh uninterrupted final whole-security run remains Plan18 work.

## Repair checkpoint

The final frozen migration/admission group passes121 real/unit cases in628.67s.
Both changed runtime modules have100% statements and branches:119 statements,
34 branches, zero misses. Scoped mypy/Ruff/format and both source-pin validators
pass; all63 offline deployment compatibility cases and46 offline producer,
consumer and image/source contracts pass. The current23 source now explicitly
pins `portfolio_migrate.py` as well as bootstrap authority.

Current source SHA256s at this checkpoint:

- bootstrap: `504e6995f446cf5de97010fa15262988b660b0013bfc14d873a9c98bd946bd80`
- migrator: `dabc03a7bbcf7efd74824472e6f35ad399cd43a966792aeac065806ce774aa3e`
- administrative SQL: `3166dfa1def5ab13c37f975bd0f766fb40aa280d615fc20939af5dc7ee7f8ac9`

The deliberately committed unsafe-default negative initially exposed a test
cleanup omission; its exact inverse is now applied only after asserting that
the real migration refused before child creation and preserved all evidence.
All four20/21/22/23 unsafe-default cases then passed with cleanup. No runtime
normalization or gate weakening was added for this test failure.

Repair commit352f650 passes fresh TLS20.70s, genuine runtime-granted20→23
TLS15.84s and source-destroyed encrypted cold recovery55.30s, using new private
archive58e225255e0e69279be0a7c86c40be4a55aac82aa63c93a4c388bf6fdb6e1ef4.
Every31-table/24-tail oracle comparison and exact final authority check passes;
the immutable old20 writer refuses before effects. All receipts report unchanged
source. Earlier archives/proofs remain intact and are not relabelled.
