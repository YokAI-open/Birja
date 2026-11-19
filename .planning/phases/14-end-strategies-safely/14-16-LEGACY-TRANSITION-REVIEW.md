# Plan16 — Exact legacy14 migration-entry and bootstrap repair

## Actual failure and scope

The existing required dev financial diagnostic upgrades a populated0014 database.
After adapting it to current0023, its fresh lane first exposed a fixture bind-mount
permission problem: a private root-owned checkout file replaced readable image
source. The fixture now resets backend/scheduler volumes and uses the complete
selected image; no host permissions or runtime policy were changed.

The corrected fresh lane passed. The genuine legacy14 lane then reached0023 but
failed the strict final preflight with `unexpected closure privileges`. A private
owned diagnostic measured the exact prior and post-migration states below. The
old migration entry had only finite object/role checks for14, not an exact
catalogue/ACL/default recognizer before Alembic. Moving this test's starting
revision to20 would have hidden the existing promised compatibility behavior.

Parent explicitly authorized a current-only14 entry recognizer, finite inherited
bootstrap pair, independent administrative-SQL parity, coordinated current source
pins and real regression/recovery checks. No dependency, image pin, historical
migration/profile, provider, production or publication operation is included.

## Measured source-owned states

The actual dev role-creation order is reproduced: migrate trusted source to14
before app/scheduler principals are provisioned, then provision their restricted
identities. Test-only role removal happens only while the owned disposable schema
is empty. It is not a runtime grant repair or an acceptance fallback.

| Boundary | Complete catalogue | Object ACL |
|---|---|---|
|Genuine14 restricted migration entry|`5dac40c397dc206186f940befc95e353352bd806f3cc3167c165095211b8ee91`|`2363d5540c0ce80684e3d8135f088a32994477b4b43fc58541530cddcc74231d`|
|Inherited14 after source migrations to23, before final grants|`59aeeee9428fac73f96143cc8afdd77e3b6a8f81b30ed37b752666579d69a66e`|`8f48c68571268efe53c84883faa9f3de4c676721acc2d003be10cae58df1dc06`|

Both boundaries were measured with exactly these effective-default variants:

- Builtin implicit PUBLIC function execution:
  `3c6c72d38f50b3150f0c849954fa0842a0711cfcbda15936e470bc648d436ebe`.
- Private owner-only defaults:
  `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`.

Explicit unsafe non-owner future-default grants still refuse. The current-only
entry uses the complete current catalogue projection against actual14; it does
not rewrite the frozen historical14 projection. Existing supplemental inventory,
source, identity, ownership, role and configuration checks remain mandatory.
Unrecognized prior states refuse before child creation and are not normalized.

The inherited post14 pair is accepted only by explicit bootstrap. Ordinary
runtime still requires the unchanged final object ACL
`71896f41a9310ada0af0961b78e78f5364654f1513c11bf9310c250ad545f748`
and private defaults above. Python and independent administrative SQL have the
same finite bootstrap pair. Existing GRANTS23 is applied only after validation.

## Source and regression evidence

RED commit `e37de93` reproduces two rejected legitimate14 transitions and the
prior14 index drift that formerly reached a migration child:3 expected failures
in18.49s,19.916s receipt, unchanged source. Both real default variants measured the
same prior/post object ACLs. Bounded GREEN passed7 cases in36.50s.

The final frozen relevant group passed202 tests in1070.95s,1072.525s receipt.
Both changed runtime modules have100% statement/branch coverage:133 statements,
36 branches, zero misses. Source hashes stayed unchanged. The existing runpy
entrypoint warning remains unrelated and unchanged.

New cases cover all17 omitted-object/storage families on14, full prior
catalogue/ACL/default/missing/extra-grant refusals before a child, and both
inherited14 defaults. Each negative preserves original financial rows, identity
tails, version, catalogue, ACL/defaults and the hostile object until after the
assertion. Existing20/21/22 cases keep the same assertions. Post14 Python/SQL
parity tests cover every partial lifecycle read, every missing final read,
extra grants and unsafe future defaults; ordinary runtime refuses until final
grants and all31-table/24-tail evidence is preserved during explicit bootstrap.

Current source SHA256s at this checkpoint:

- bootstrap: `fa17d8546265f8e7eccb23838a8989b0b905a342a0d3e7b8eebf725c31c3bbc6`
- migrator: `bfc2990eca9e70993b228b7ca52ab7c47fb17610719944779ad97b94dd57cd17`
- administrative SQL: `e981467f2cbf565140eb78b318b06b201f8007e95d563fe162d70663c47691bb`

Producer/consumer/deployment pins are coordinated. Historical exports, migration
bytes, final catalogue/ACL/default fingerprints and qualified source identities
are unchanged. Raw synthetic PID/start-tick/log/source receipts remain under
`/tmp/birja-phase14-plan16/`; failed diagnostics are not passing qualifications.

## New-source actual proof

At source `159d6d87049d65463314b50ead94cde1bddda82b`, the new private R3
archive `/tmp/birja-backup-test-p14-16-proof-r3/recovery.tar` has SHA256
`7a698a7667efc0c3ff6b7545dabd89e969d6f4d9adcd5fde5d93b9f5a19aceff`.
Its immutable backend image is
`sha256:859be689c5d4077cd91aaff34f62e51b7b00c8d6e2163bf3aa0d9c672f796a33`.
The same archive passed genuine14 upgrade (20.257s), empty-schema fresh
(15.884s), genuine20 upgrade (15.690s), and encrypted cold restoration (53.390s).
All four returned the unchanged final catalogue/object/default triple above;
each receipt records unchanged source. Their durable private evidence is
`/tmp/birja-phase14-plan16/proof-r3-{package,upgrade14,fresh,upgrade20,cold}.json`
and corresponding logs. Cold recovery verifies original manifest evidence
before grants and final nonquarantined23 authority afterward.

The actual ordinary-dev fresh and populated14 paths also passed against that
immutable image: 19.043s and22.109s,42.726s total, unchanged source. This covers
exact money/baseline preservation, repeated initialization without a grant,
and unsafe role/membership/object refusal. Every owned resource was removed.
Receipt: `/tmp/birja-phase14-plan16/dev-r3.json`.

R1 andR2 failed diagnostic archives/receipts remain preserved. Their harness
errors were an empty-schema pre-import gate on deliberately prepared14, then
passing that prepared flag to a subsequent final23 probe. The fix permits only
the explicit initial current14 upgrade transport, verifies source and complete
restricted-migrator14 authority before financial imports, and keeps later23
probes on ordinary admission. Unsupported sources/modes refuse; an additional
offline regression asserts the flag occurs only on the initial transport.
No runtime/pin changes followed the202-test runtime qualification.

## Remaining validation

Final Plan18 whole security/backend coverage and uninterrupted seven-stage
same-archive proof remain mandatory at its final source. These bounded proofs
are not that whole qualification. Independent parent review, Plan17 browser
integration and Plan19 owner UI/native200 acceptance remain separate.
