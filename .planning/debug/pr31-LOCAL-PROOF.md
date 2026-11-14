# PR31 local CI repair proof

The owner approved exactly dnspython2.9.0→2.9.2 for local installation,
image rebuilds and affected checks. Publication, merge and production remain
separate. The exact reviewed lock SHA256 is
`3eded7f21be30568f5d4fae129f38a11e19484035f60f1477a3f9b2bf30fd2d4`.
Full parsed lock and installed host inventories show one changed package,
zero additions/removals and no other changed distribution/version.

## Original failures and fixes

1. The unrestricted dependency audit reports the WKS parsing advisory against
   dnspython2.9.0. Apply only the exact reviewed2.9.2 wheel/lock.
2. The image inventory predates the independently approved OTEL repair.
   Authenticate exact OTEL and DNS full records separately; retain independently
   computed historical remainder and all eight calendar artifacts. Legacy
   rollback's package boundary uses the same exact approved exceptions.
3. Cold CI verifies the recovery image export before standalone recovery tests
   but never binds the required local alias. Authenticate the export, reject
   wrong existing aliases, import that same archive and bind its fixed verified
   platform/config identity before Compose starts. Recovery CORE stays unchanged.

## Actual checks

| Check | Actual outcome | Private evidence |
|---|---|---|
| Exact upstream WKS regression, cached2.9.0 then installed2.9.2 | RED: missing SyntaxError for finite65536 service; GREEN:1pass0.10s | `/tmp/pr31-dns-wks-red.log`, `/tmp/pr31-dns-wks-green.log` |
| Upstream2.9.2 rdata/tokenizer/resolver |211passed,31network/optional skips,71subtests,0.82s|`/tmp/pr31-dns-upstream.log`|
| Canonical unrestricted `uv run --locked --no-sync pip-audit` |No known vulnerabilities found|`/tmp/pr31-dns-audit.log`|
| Image contract |15tests pass; DNS version/artifact and unrelated changes rejected|`/tmp/pr31-dns-image-green.log`|
| CI and selected contracts |16CI/7selected pass|`/tmp/pr31-dns-ci-green.log`, `/tmp/pr31-dns-selected-green.log`|
| Real retained-installer rollback selftest |Pass; precise DNS/OTEL/calendar mutations rejected; real synthetic Git/launcher routing retained|`/tmp/pr31-dns-rollback-green.log`|
| Lint/format/types |Pass;190formatted files,88typechecked sources|`/tmp/pr31-dns-lint.log`, `/tmp/pr31-dns-format.log`, `/tmp/pr31-dns-types.log`|
| Canonical test-builder/runtime builds |Pass; complete APK/Python inventories differ only in approved DNS patch|`/tmp/pr31-dns-{builder,runtime}-build.log`, `/tmp/pr31-dns-image-inventory.json`|
| Actual UID1001/networknone runtime native smoke |WKS upper bound/refusal, email parsing, XNYS/native calendar, dividend/worker/History imports pass|`/tmp/pr31-dns-image-proof.log`|
| Five actual canonical strict image scans |All5pass;0HIGH/CRITICAL including unfixed|`/tmp/pr31-dns-image-reports/`|
| Full backend/47critical coverage |2557passed366.25s;99.87%overall; all47critical modules4565statements/1462branches100%|`/tmp/pr31-dns-backend-full.log`, `/tmp/pr31-dns-critical.log`|
| Canonical rebuilt builder smoke |5passed2.38s against isolated owned PostgreSQL/Redis|`/tmp/pr31-dns-builder-smoke.log`|
| Final owned-resource cleanup |Both birja-test/birja-ops-test have zero containers/networks/volumes|`/tmp/pr31-dns-owned-resources.json`|

Original-source cold startup RED then repaired actual guarded PostgreSQL GREEN
is retained in `/tmp/pr31-ops-cold-before-after.log`. Actual24PostgreSQL recovery
contracts pass122.519s in `/tmp/pr31-ops-postgres.log`, including all four cases
that failed in hosted CI and corruption/unsafe-runtime refusal controls. Owned
cold-probe resources were removed and existing image aliases were preserved.

Independent affected code/security reviews cover the exact source hashes in
`pr31-CODE-REVIEW.md` and `pr31-SECURITY-REVIEW.md`, with zero active findings.
The security review closes all six scoped threats. Exact package provenance and
the absence of independent Sigstore cryptographic verification remain disclosed
in `pr31-DEPENDENCY-REVIEW.md`.

Source-bound final receipt: `/tmp/pr31-dns-receipt.json`, SHA256
`7574eef7b45f92d85cc023235afd5d9bcdce034cf8a87ba3dfcf0613714d180b`.
It binds all five affected source hashes,21raw logs, exact commands, complete
image/native inventories, five strict reports and actual cleanup. Code commit
`a0feb5cabc790ea51afae647026889a1758ba8e4` records the reviewed exact DNS delta;
`d855a0f` records the independently reviewed original image/cold-start fixes.

## Qualification

The earlier Phase11 full/serial recovery evidence remains historical and
source-qualified. This repair changes no financial application/Alembic, retained
CORE, build recipe, authority, frontend or browser bytes. Actual new DNSruntime
qualification covers upstream regressions, backend service effects, native
runtime imports, full native inventories and strict scans. No new complete
serial recovery campaign or hosted CI success is claimed. The same-source cold
image/24PG repair proof remains independently reviewed. No provider/private.env,
production/B2/installed-host-tool/timer action occurred.
