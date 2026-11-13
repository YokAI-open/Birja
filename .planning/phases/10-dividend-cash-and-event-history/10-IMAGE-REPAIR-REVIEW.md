# Phase10 exact Node image repair review

Prepared2026-11-13 for explicit owner decision. **No candidate package/image has
been downloaded, installed, pulled or built.** This is read-only official
metadata/provenance review and a proposed patch, not a passed replacement scan.

## Observed blocking finding

Actual strict five-image command exits1. Runtime, builder, PostgreSQL and Redis
have0HIGH/CRITICAL findings; Node has1HIGH, including unfixed findings without
ignore/VEX/waiver. Node report:
`/tmp/birja-phase10-16-image-reports/node.json`, SHA256
`e87d28bc2cdf9cd77f61ce026f44d34b60d3b9cb2e615b52323c32e96f5679f3`.
Requested image`birja-node-toolchain:phase09`, image prefix`bf23aa6774b0`,
saved config`e48ee6f317d450011ead650f051498593a54338b3e41f901e8e4f4481c317c34`.
Scanner Trivy0.76.1, immutable approved scanner pin; DB updated
2026-11-13T12:56:33.451543713Z, next update2026-11-14T12:56:33.451543367Z.

`CVE-2026-123863`: reachable Node HTTP/2 teardown assertion can terminate the
server. Installed Wolfi package`nodejs-24=24.22.2-r2`; reported fixed
`24.22.3-r0`. PublishedNov11/updatedNov12. This remains a blocking gate even
though the current application does not claim an HTTP/2 Node runtime exposure.

## Primary evidence and exact candidate

- [Node official November security release](https://nodejs.org/en/blog/vulnerability/november-2026-security-releases)
  names this CVE and links the24.22.3 release. Locally fetched HTML SHA256
  `e5860b0809369acc0792fc48b7aaa92e661042ece93828c49a869af0801872c2`.
- [Wolfi official security metadata](https://packages.wolfi.dev/os/security.json)
  lists`CVE-2026-123863` and`GHSA-cwc7-c9hg-jq89` fixed in
  `nodejs-24/24.22.3-r0`. Metadata SHA256
  `c3ea73e0319cef363cc62c0773e7e7631bffaeb2095dbb6353e9299e36689f79`.
- [Configured Chainguard repository index](https://apk.cgr.dev/chainguard/x86_64/APKINDEX.tar.gz)
  SHA256`50bdba70c1a930725b136c11b37935a216a1efbdc8dea94a21b6fcd263784b0e`
  contains exact package`nodejs-24`,version`24.22.3-r0`,arch`x86_64`,MIT,
  maintainer`wolfi`,source commit`24bffb2e65978a9684050b88de007975a5f974b3`.
  Compressed size29814375; installed size85255790. Signed APK control checksum
  `Q1SFY3HxJWkbkcFkujs8uEetvBZuc=`. This is the APK index's control checksum,
  **not** a fabricated whole-package SHA256.
- Independent [Wolfi repository index](https://packages.wolfi.dev/os/x86_64/APKINDEX.tar.gz)
  SHA256`52ac2bbd2be920ea08fa08f3e4b5d0dbe9795bf343495e2b857500c974721c71`
  has the identical candidate stanza/control checksum/source commit.
  Candidate versus current package dependency declarations are identical;
  `cmd:node` and`nodejs` provider versions change to24.22.3-r0.
- HEAD for the exact Wolfi APK returns200,size29814375,Last-Modified
  Nov11at21:38:51GMT. HEAD from the configured Chainguard APK endpoint returns303
  with matching`x-chainguard-control-hash`; its ephemeral delivery URL is omitted.
  No APK payload was downloaded. Later24.22.3-r1/r2 also exist; this proposal
  deliberately selects only the exact minimal fix stated by official secfixes.

## Signed index and APK trust chain

The already approved Node image's`/etc/apk/repositories` is
`https://apk.cgr.dev/chainguard`. It retains the three Chainguard RSA public keys
and`wolfi-signing.rsa.pub`. The configured index has three RSA256 signature
members matching those existing Chainguard key names. Wolfi index has its
RSA256 Wolfi signature. Network-free, read-only`apk verify` of both downloaded
index files uses that existing trust store without`--allow-untrusted`; both
exit0 and print`0 - OK`. Verify logs and public-key hashes are retained under
`/tmp/birja-phase10-16-image-repair-review/`.

Existing trusted Wolfi public key SHA256:
`f0031424cf46f7db780ce63a45f0fd6aa6f85f601e6bb3b7a91fe3d4d5b7d2cc`.
Configured repository trusted key SHA256 values:
`fc774d8f9ffd8f2986eeda888c5358d08bab80fdb251a2e4e8236f82cbf241c8`,
`d91e3de0257c8762512695edbe35c7fb910ea5e11ff1cd54051e1ee50c10a0ec`,
`d53f265d056f818ca6fc2284798f46c4f046c7ffbaef152acb36362fbc9d12d9`.

After approval, ordinary APK verification must authenticate the actual package
signature/control checksum and payload when resolving the exact pin from this
configured repository. Whole-APK SHA256, actual resolved transitive package
versions, successful build/runtime behavior and a clean strict image scan remain
**unverified** until then. Signed repository metadata proves publisher-chain
availability, not a complete reproducible-build or upstream source audit.

## Proposed scoped patch — not applied

```diff
--- a/frontend/Dockerfile
+++ b/frontend/Dockerfile
@@
-RUN apk add --no-cache nodejs-24=24.22.2-r2 \
+RUN apk add --no-cache nodejs-24=24.22.3-r0 \
--- a/deploy/tests/test-image-contracts.py
+++ b/deploy/tests/test-image-contracts.py
@@
-        self.assertIn("nodejs-24=24.22.2-r2", frontend)
+        self.assertIn("nodejs-24=24.22.3-r0", frontend)
```

Keep the existing base digest, npm11.21.2 integrity check, application lockfiles,
Node24 family, backend/datastore/scanner pins and no-waiver security threshold.
Scope for approval: the two files above plus this review and Plan16 evidence;
download/install only this existing-family exact approved package through APK's
existing signed repository, rebuild local toolchain/dev images, run image
contracts, all five strict scans, applicable full frontend/build/browser checks
and final source/image/archive verification. No host tool upgrade, new package
name, npm/uv lock change, production tool/deploy/push or provider action.
If dependency resolution or further findings require another package/version,
stop and report the concrete extension rather than silently widening scope.

## Approval source — exact rules and interpretation

CLAUDE.md requires: **“pinned image versions + scans (`trivy`)”** and
**“committed lockfiles (`uv.lock`, `package-lock.json`); regular
`pip-audit`/`npm audit`, run in CI.”** It does **not** contain a universal
explicit-owner-approval rule for every package version update; none is invented.

Plan10-16 threat register T-10-16-SC states: **“No new package/install/lockfile
change; reuse reviewed locked stack. Any later addition requires legitimacy
audit and blocking approval before install; never waive strict final image
gate.”** The current executor assignment additionally expressly forbids
package/image changes and directs a separately audited repair when observed.
That explicit authorization boundary is why approval is required here.

[Executor checkpoint rule](../../../.codex/agents/gsd-executor.md) says:
**“If checkpoint has `gate="blocking-human"` OR its purpose indicates package
legitimacy verification ... do not auto-approve. STOP and return
checkpoint_return_format for explicit human confirmation.”** This controls an
actual package-legitimacy gate; it is not misrepresented as a general rule in
the execute-phase skill. Owner approval must explicitly authorize the concrete
scope above; auto mode, a clean index signature or a fixed-version suggestion
does not grant that authorization. Unaffected local verification can continue.

Status: **review ready; candidate installation/build remains awaiting explicit
owner approval; strict image gate remains FAILED.**
