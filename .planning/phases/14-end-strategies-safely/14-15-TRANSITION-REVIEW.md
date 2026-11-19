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

## CR-01 supplemental migration-entry repair

Independent review at24f716f proved that a disabled-RLS policy could evade the
immutable prior catalogue projection and permit Alembic to mutate the schema
before final admission refused. RED commit4ac8d54 reproduces the bypass against
genuine0020,0021 and0022; all three fail before the repair. The original review
finding remains unchanged for independent re-review.

The current migration entry now runs an additional read-only inventory before
any child. It refuses public policies, rewrite rules, RLS flags, nonordinary
relation kinds, nonpermanent storage, inheritance, and unexpected public types,
collations, conversions, operators, operator classes/families, extended statistics
or extensions. Expected table row/array types are recognized by their actual
catalogue identities and owners, rather than name patterns. Unknown objects are
never dropped or normalized. Existing finite catalogue/ACL/effective-default,
role, configuration and source authentication remains mandatory afterward.

The eight immutable prior/current SQL exports, migration bytes and final
catalogue/ACL/default fingerprints are unchanged. This is a current-entry
supplement; retained0020/0017 authorities are not rewritten. Current producer,
consumer and deployment source pins bind the revised bootstrap and migrator.

The regression matrix covers17 distinct object/storage drift families across
all three prior revisions. Each case first verifies its genuine baseline is
admitted, commits the hostile change, then checks both direct admission and the
actual migration entry refuse before child creation. Revision, both catalogue
projections, all retained rows and sequence tails stay byte-equivalent, and the
hostile object remains present. Package-free foreign/extension fixtures use
only the owned disposable database; their own cleanup follows preservation
assertions. Twelve legitimate initial/runtime and builtin/private-default
initial/resume paths passed separately before the complete relevant group.

CR-01 GREEN commit`ed4f96f5e6f44baee46243f78185243d14689f87` passes172
relevant migration/admission tests in922.17s (durable receipt923.664s), with100%
coverage of both changed runtime modules:124 statements and34 branches, zero
misses. All source bytes remained unchanged during the run. Scoped Ruff/format
and mypy pass;46 offline producer/consumer/image contracts and63 deployment
compatibility cases pass. The complete relevant group includes the51 new drift
cases, legitimate prior initial/resume paths, exact final bootstrap parity,
current runtime refusals and retained literal equality.

Current source SHA256s after CR-01:

- bootstrap:`7ef1a76af2284f065b17dc0baffa7c6e4c7f6a879e9ea72dbab54b9943b74f50`
- migrator:`02747095a00d6543f4156e0f9be025da4186eafa2e8412fae3b239fdd24af8de`
- administrative SQL remains:`3166dfa1def5ab13c37f975bd0f766fb40aa280d615fc20939af5dc7ee7f8ac9`

New private R4 archive SHA256 is
`161b8fa08eedd025b2100328e642d0928927561c6604e8d5839f3ca5130a3d9e`,
packaged from that exact committed source with authenticated current image/source
bindings. Real fresh restricted-TLS proof passes19.831s; genuine runtime-granted
0020→0023 TLS passes15.707s; encrypted source-destroyed cold recovery passes53.765s.
All three return unchanged catalogue59aeeee…/ACL71896f…/private-default4f53…;
source-manifest validation precedes regrant and full31-table/24-tail immutable
before-oracle equality passes. Each receipt records source_unchanged=true.

Private `cr01-cleanup.json` confirms all four owned projects have zero remaining
containers/networks/volumes. `cr01-archive-integrity.json` rechecks R1–R4 and the
protected Phase13 archive; canonical Phase14 proof remains absent. Previous
historical0020/0017 evidence and archive bytes are retained, not relabelled as
new-source proof. The expected backend collection is now3623 cases; the earlier
partitioned evidence remains supplemental and Plan18 still owes uninterrupted
whole-suite/security and seven-stage same-archive proof at final source.

Independent CR-01 re-review remains the parent's next gate; this executor's
passing checks do not replace that review.
