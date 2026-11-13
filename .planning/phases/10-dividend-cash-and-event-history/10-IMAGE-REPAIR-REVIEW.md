# Phase10 exact Node image repair review

Initially prepared2026-11-13 for explicit owner decision. **At initial review,
no candidate package/image had been downloaded, installed, pulled or built.**
The original read-only review follows; later sections separately record actual
owner approval, package authentication, observed build failures and corrections.

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

Status at preparation: **review ready; candidate installation/build awaiting
explicit owner approval; strict image gate FAILED.**

## Owner approval and actual payload authentication

On2026-11-13 the owner selected **“Approve security patch and continue locally
(Recommended)”** for the exact scope above. The parent relayed that explicit
approval before any APK payload retrieval, installation or candidate build.
This does not authorize a different version, base/npm/lock change or trust bypass.

The exact approved APK was then retrieved from the configured repository:
SHA256`40d88fe87af9d59007fca8698286edbcabe3864bcf525a64fa42a930b7cc35fc`,
29814375bytes. It has **no embedded package signature**, so standalone
`apk verify <file>` reports`UNTRUSTED`; that diagnostic remains preserved.
No keys were added and no`--allow-untrusted` or other bypass was used.

The normal repository chain was independently authenticated instead:

1. Existing trusted APK keys verify the signed configured repository index.
2. The unsigned APK has two gzip members, as described by the publisher's
   [APK expansion documentation](https://pkg.go.dev/github.com/chainguard-dev/go-apk/pkg/expandapk).
   SHA1 of the17945-byte compressed control member is exactly the authenticated
   index checksum`Q1SFY3HxJWkbkcFkujs8uEetvBZuc=`. Its SHA256 is
   `e2564e3a45407207d701b596f6fa545f3e1083ab6ff2097fa782d365443958b1`.
3. The authenticated`.PKGINFO` names the exact approved package/version/arch/
   source commit. Its`datahash` equals SHA256 of the entire29796430-byte
   compressed payload member:
   `1ae40321c10c19202c25624d726a0b73c310aa1bdf4c44ccd1bf1f10081413f9`.
   Both links are asserted by the independently retained
   `verify-candidate.py`; receipt`candidate-authentication.json` is alongside it.
4. Default trusted-repository`apk add --simulate --no-cache` resolves exactly
   one upgrade: Node24.22.2-r2→24.22.3-r0;26packages remain. This simulation
   installs nothing and uses no relaxed trust setting.

The installed APK-tools2.14.13 source URL was unavailable(404); no claim of
reviewing that exact implementation is made. Primary format documentation,
the actual cryptographic byte comparisons and default repository verification
establish the chain; the standalone embedded-signature result is not relabelled
as successful. Full build inventory comparison and all-five strict rescans
remain the required next evidence, with failures retained.

### Fresh-build inventory guard caught additional revisions

The first approved exact-Node build completed, but inventory comparison against
the previously accepted26-package toolchain rejected the result. Fresh resolution
also changed`icu79-data-full`and`libicu79`79.1-r1→r2, and
`libstdc++`16.2.0-r2→r3. Existing-image simulation had planned only Node; it did
not model fresh-base transitive selection. The image is **not accepted**, and
its build/inventory failure remain recorded. Base/npm/application locks did not
change. A proposed guard is to pin those three already accepted old versions
explicitly, so only Node changes. All three old versions remain present in the
authenticated configured index. No approval of their newer revisions is inferred.

Parent confirmed that explicitly constraining those three **already accepted
versions** preserves the owner's exact approved scope; it adopts no new package
family or extra version. The amended actual Dockerfile keeps the approved Node
pin and adds`icu79-data-full=79.1-r1 libicu79=79.1-r1 libstdc++=16.2.0-r2`.
Its image contract requires all four exact pins. A separate fresh-base simulation
must pass before rebuilding; final inventory must differ only in Node.

The upstream APK-tools [v2 format manual](https://man.archlinux.org/man/apk-v2.5.en)
documents the authenticated control metadata's SHA256 datahash link. This is a
mirror of the upstream manual, not a claim to have inspected unavailable2.14.13
source. The publisher's separate expansion documentation explicitly distinguishes
two-member unsigned packages from three-member signed packages.

### Corrected build preserves the exact accepted package inventory

Fresh pinned-base simulation passed with the three old transitive versions.
The corrected default-trust build then passed the complete26-package comparison:
**only**`nodejs-24-24.22.2-r2`is removed and`nodejs-24-24.22.3-r0`is added.
Receipt`accepted-package-delta.json`; old failed delta and build are separately
retained as`unaccepted-first-build-*`and`birja-phase10-16-node-security-build.log`.
Corrected local tag`birja-node-toolchain:phase10-final` has image ID
`7344f1b05de0e77f4156a04b73098bfbad78c81a2480efdc6645070b14e2a4db`,
config`c1bad00ce93f18db31302718481fb9732ffdf4c059e2ad2d844582aa54a9103b`.
The original base digest and npm11.21.2 integrity pin remain unchanged.
All13image contracts pass0.383s, including the four exact package-pin guards.
This build/inventory result does not replace the required all-five strict scan.

CI's expanded serial recovery job allows45minutes rather than30: the measured
predecessor retained/roles/TLS gate alone took1047.402s, plus selected rollback,
image transition, actual SQL contracts and tool preparation. The larger bounded
job budget preserves every stage; no gate is skipped to fit the old timeout.
