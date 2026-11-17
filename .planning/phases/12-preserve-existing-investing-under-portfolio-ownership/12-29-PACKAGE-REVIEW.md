# Plan12-29 — bounded candidate review

**Disposition:** `no_candidate`; Plan29 remains incomplete before Task02.
**Observed:** 2026-11-17T19:43:24.125695+00:00.
**Reviewed source:** `8291b8377cbc0a0fcb2fdcc55a0550ce6fcc8336`.

The [official reviewed advisory](https://github.com/advisories/GHSA-fc5q-39xc-vjpf)
still reports HIGH CVE-2026-112366, affected picomatch `<=4.0.7`, with
`first_patched_version=null`. The [official registry](https://registry.npmjs.org/picomatch)
still reports latest `4.0.7`; every version in its published-version inventory
is within that affected range. There is no eligible artifact to resolve, review
for installation or present for exact owner approval. No prospective lock or
candidate checksum has been invented.

## Current locked scope

| Lock path | Version | Finding |
|---|---|---|
| `node_modules/picomatch` |4.0.7|Affected|
| `node_modules/micromatch/node_modules/picomatch` |2.3.2|Affected|

All current lock entries and picomatch dependency fields were inspected locally.
Direct parent constraints are `@dotenvx/dotenvx ^4.0.4`, `fdir` peer `^3 || ^4`,
`micromatch ^2.3.1`, `tinyglobby ^4.0.4`, `vite ^4.0.7` and `vitest ^4.0.7`.
Both installed lock paths therefore remain unresolved. A root-only upgrade
would not establish repair of micromatch's nested major2 dependency. No parent
upgrade, override, fork, major toolchain migration or automatic Vitest downgrade
has been selected or attempted.

Unchanged `frontend/package.json` SHA256:
`73cd4f25fb329d7d0711321ee56dd9f07b25426eb9ddb69f3491396c2ccbdb59`.
Unchanged `frontend/package-lock.json` SHA256:
`1461d4f89e875a5b915278e9d39ba413608fa4ff816fab6be6b21e280db5475b`.

## Bounded refresh and raw evidence

The first sandbox-only attempt failed DNS for both public URLs before HTTP.
The exact two requests then succeeded with permitted read-only network
escalation, each using20second timeouts and8MiB response bounds. There was one
successful official metadata refresh, no repeating schedule and no retry after
the successful result. This transport retry is disclosed rather than claiming
the failed DNS attempt established upstream package status.

| Evidence | Private raw path | SHA256 |
|---|---|---|
|Successful source/metadata receipt|`/tmp/birja-phase12-29-metadata-yvcwquan/refresh-receipt.json`|`8232b5c0696d3cb4c6b4cce2b7e05c8192997c72dc6d2d884fd033126b3ebae1`|
|Official advisory HTTP200|`/tmp/birja-phase12-29-metadata-yvcwquan/advisory.json`|`cc99706e61047047b6690db94abb98b5940d007196775c12902c0f79d8aedbd5`|
|Official registry HTTP200|`/tmp/birja-phase12-29-metadata-yvcwquan/registry.json`|`9a8e64f1208fef4d18c27f48267e00c639b65743484cf3f5e788d018195b6fbb`|
|Initial failed transport receipt|`/tmp/birja-phase12-29-metadata-5orpuk0w/refresh-receipt.json`|`f153341fdca87542aa82d1b92265a33ca947eb1175fdc3e9f69810d6c6890c55`|

The successful metadata hashes exactly match the previous saved official
evidence. Registry metadata includes signatures for the existing affected
4.0.7 artifact; they were not independently verified and are not a patched
candidate. No replacement tarball was downloaded or executed. Replacement
provenance/signature verification is inapplicable while no replacement exists.

## Acceptance and stopping boundary

The receipt parses as `no_candidate`, the project manifest/lock hashes remain
unchanged, and Task01's disposition check can pass without proving a fix.
There is no request for generic package approval: Task02 is not reached.
No completion SUMMARY is created, and Plans30/31 cannot start. The actual
complete security attempt remains failed; separate prior diagnostics remain
separate. Phase12, its seven primary requirements and all28 milestone
requirement checkboxes remain pending. Both owner UI/native200% outcomes stay
accepted; Phase7's consumed campaign and live activation gates remain separate.

No package installation, prospective package resolution, npm audit, application
test campaign, source/lock/image change, service or provider operation, push,
merge or production change occurred. Historical research remains unchanged
because no new candidate legitimacy addendum is justified. The next necessary
prerequisite is an actual legitimate published patched artifact, followed by
complete graph/artifact review and exact approval under this plan. Do not repeat
unchanged tests or refresh metadata on a background schedule.
