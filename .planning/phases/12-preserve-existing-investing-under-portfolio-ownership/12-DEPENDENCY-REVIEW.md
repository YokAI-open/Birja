# Phase 12 strict npm audit blocker — 2026-11-17

Frozen source: `d9da271b2b21f48f965dd54898a6bb8afcc9088e`. This is a dependency investigation, not approval or an installation. No manifest, lock, package, gate or source change has been made.

The actual complete `all-security` attempt reached `npm audit --audit-level=high` and failed with 25 findings: 14 high and 11 moderate. Backend 3,114 tests, exact critical 100% coverage, Python audit and frontend 958 tests/build passed before this failure. Browser and five image scans were not reached in that complete attempt. Its immutable failed receipt is `/tmp/phase12-reviewfix-security-d9da271.result.json`; full audit JSON is `/tmp/phase12-reviewfix-npm-audit-d9da271.json` (SHA256 `471ad05e25c3ac71efd8a0fc04e0eb7b5e0f201b2f80720d232cc7101daa6fa1`).

## Primary evidence and available remedy

[GitHub reviewed advisory GHSA-fc5q-39xc-vjpf](https://github.com/advisories/GHSA-fc5q-39xc-vjpf), reviewed/updated November 17, identifies CVE-2026-112366: crafted repeated extglob patterns can cause regular-expression denial of service. Affected versions are `<=4.0.7`; patched versions: **none**. The audit propagates this one advisory through 14 high package entries; those entries are not 14 independent new direct vulnerabilities.

[Official npm registry](https://registry.npmjs.org/picomatch) metadata, captured read-only at `2026-11-17T17:42:05.402346Z`, reports latest **4.0.7**, modified `2026-08-24T14:36:23.879Z`. Saved metadata: `/tmp/phase12-reviewfix-picomatch-registry.json`, SHA256 `62815a1e548ff21e8fdd6da8a2c47b9e31112aad65f7cb64f192c3f96ad1c246`.

There is **no published patched candidate identified** and therefore no truthful prospective fixed lock diff, new artifact checksum or candidate provenance to approve. Existing npm integrity values below describe current affected artifacts only. No tarball was installed or executed during this investigation; signature/provenance verification of a replacement is inapplicable until a replacement exists.

The audit's automatic `fixAvailable` proposes a semver-major Vitest downgrade to 3.1.4. It is not evidence that picomatch is fixed, and is outside authorized scope. Do not run `npm audit fix --force`, install a downgrade/override, weaken the HIGH gate, or claim this failed campaign passed.

## Exact current artifacts and dependency scope

| Installed lock path | Version | npm integrity |
|---|---|---|
| `node_modules/picomatch` | 4.0.7 | `sha512-qcJu88Q2IWqJsDD529JKMdwGm/dvInW4HvQnRwiH9JtihJvzGOscDtHE3x1pBKeUOTysQ8kVmLnJ2kJu7yhcGA==` |
| `node_modules/micromatch/node_modules/picomatch` | 2.3.2 | `sha512-V7+vQEJ06Z+c5tSye8S+nHUfI51xoXIXjHQ99cQtKUkQqqO1kO/KCJUfZXuB47h/YBlDhah2H3hdUGXn8ie0oA==` |

Resolved tarballs: `https://registry.npmjs.org/picomatch/-/picomatch-4.0.7.tgz` and `https://registry.npmjs.org/picomatch/-/picomatch-2.3.2.tgz`.

The saved actual `npm ls picomatch minimatch --all --json` tree is `/tmp/phase12-reviewfix-glob-tree.json`. Current paths include Vite 8.3.5 and Vitest 5.0.5 through tinyglobby 0.2.17/fdir, plus micromatch 4.0.8 through fast-glob 3.3.3 and shadcn 4.22.1/@shadcn/registry/@ts-morph/common. `@dotenvx/dotenvx` also reaches the shared picomatch via fdir. This is build/test/tooling dependency exposure; it does not establish that an arbitrary public Birja request reaches the vulnerable parser, nor does that uncertainty waive the strict audit gate.

`frontend/package.json` SHA256: `73cd4f25fb329d7d0711321ee56dd9f07b25426eb9ddb69f3491396c2ccbdb59`.

`frontend/package-lock.json` SHA256: `1461d4f89e875a5b915278e9d39ba413608fa4ff816fab6be6b21e280db5475b`.

`git diff HEAD -- frontend/package.json frontend/package-lock.json` is empty. Existing moderate advisory groups remain recorded by the audit, including Hono, its Node adapter and minimatch; no unapproved remediation is bundled into this review.

## Disposition

Keep the strict gate failing truthfully. Continue unaffected same-source recovery verification. A future dependency repair requires a concrete legitimate patched artifact and exact scope/checksums/provenance review plus separate owner authorization; this document authorizes none. No production/provider/publication operations are involved.

## Final metadata refresh

At2026-11-17T18:37:28.517088Z, the single final read-only official refresh still reports latest4.0.7, affected<=4.0.7 and first_patched_version=null. Advisory updated_at remains2026-11-17T15:56:44Z,26seconds after the historical complete security pass finished15:56:18Z. No new candidate or audit retry was justified.

Saved summary: `/tmp/phase12-reviewfix-picomatch-refresh-summary.json`.
Official advisory JSON SHA256: `cc99706e61047047b6690db94abb98b5940d007196775c12902c0f79d8aedbd5`.
Official registry JSON SHA256: `9a8e64f1208fef4d18c27f48267e00c639b65743484cf3f5e788d018195b6fbb`.
The separate remaining diagnostic subsequently passed full browser59/1originalskip, declared builds, smoke5/5 and five strict image scans0HIGH/CRITICAL. That does not change the failed complete npm audit or constitute whole-security success. Phase12 remains blocked; no requirement checkbox or phase advanced.

