# Phase12 — Picomatch replacement research

**Researched:** 2026-11-17. **Final status:** `no_safe_candidate` after independent
review rejected the concrete fork. The original candidate investigation below
is retained as history, not a current installation recommendation. No
installation or complete-security pass occurred.
**Confidence:** HIGH for source/registry integrity and static dependency facts;
MEDIUM for patch suitability; compatibility and actual qualification unverified.

## User Constraints

[VERIFIED: conversation] The owner now requests “replace this dependency then.”
This permits investigating a replacement rather than waiting for the original
maintainer, while preserving strict audits, existing behavior and prior work.
It does not fabricate exact package legitimacy approval, a successful audit or
production/publication authorization. Original context decisions remain in
12-CONTEXT.md; names/descriptions/creation are Phase13, deletion Phase14, and
Phase7 live activation remains deferred. Both UI/native200 checks remain accepted.

## Recommendation

**Superseded by independent review:** Do not install the fork below or seek
approval to install it as a security fix. See the final disposition at the end
and12-REPLACEMENT-REVIEW.md. Its default multi-branch safeguard remains bypassable.

[CITED: https://github.com/ryotsu-kankichi/secured-picomatch] Review the published
security fork **@ryotsu/picomatch 4.0.7-a**, then, only if independent source/security
review and the exact owner checkpoint pass, replace both original instances using
the exact private prospective manifest/lock below. This is a concrete candidate,
not a claim that a mature, widely maintained replacement has been established.

[VERIFIED: official npm metadata and local static comparison] Its runtime patch
changes the vulnerable repeated-extglob parser; this is not merely renaming an
affected artifact to hide from npm audit. All ten published files exactly match
source commit `3ab5a7627d480259e3d9ca67fbc14c125d374f0e`. The package has no runtime
dependencies and no installation lifecycle scripts. It is nevertheless a new,
single-maintainer fork, and must not be called upstream-approved or risk-free.

## Project Constraints (from AGENTS.md)

[VERIFIED: AGENTS.md and CLAUDE.md] Keep the existing project and GSD state;
retain plan checking, reviews, exact approval checkpoints and verification.
Use committed npm locks; do not bypass HIGH audits, image scans or coverage.
Preserve financial Decimal/NUMERIC behavior, isolated serial DB/TLS proofs and
unchanged scope. No source/private environment/provider/production operation is
needed for this investigation. Keep the feature branch local; do not push/merge.

## Current dependency and API facts

[VERIFIED: frontend/package-lock.json and installed source] Root picomatch4.0.7
is used by Vite8.3.5, Vitest5.0.5, tinyglobby0.2.17, fdir6.5.0 and dotenvx1.75.1.
Micromatch4.0.8 uses nested picomatch2.3.2 through fast-glob3.3.3, shadcn4.22.1,
@shadcn/registry and @ts-morph/common. Typescript-estree also uses tinyglobby.
Removing Vite/Vitest alone therefore cannot remove every affected path.

| Consumer | Required surface | Static evidence |
|---|---|---|
|Vite|callable matcher, scan returning base, makeRe returning RegExp|dist/node/chunks/node.js:1952,28064,32551|
|Vitest|callable matcher and isMatch, dot/include/exclude semantics|dist/chunks/cli-api.De07GUeT.js:6433 and index.1TqnEahn.js:6645|
|tinyglobby|callable matcher, scan.parts, isGlob, negated|dist/index.mjs:82,123,217|
|fdir/dotenvx|callable matcher and include/ignore semantics|fdir/dist/index.cjs:461; dotenvx/src/lib/services/*.js|
|micromatch|private picomatch/lib/utils; callback onResult; matcher.state and returnObject; parse/scan/makeRe|micromatch/index.js:6,49,368,392,408,428|

[VERIFIED: installed source] Shadcn cannot simply be removed as an unused CLI:
frontend/src/index.css imports `shadcn/tailwind.css`. A removal route must preserve
that actual CSS source/license/build behavior. There are44 frontend unit-test
files and958 last-qualified tests, plus the full browser/recovery graph.

## Alternatives considered

| Candidate | Primary-source finding | Disposition |
|---|---|---|
|minimatch|Different matcher API; no compatible picomatch scan/state/private-utils contract established. Its name in the existing tree does not confer compatibility.|Do not alias directly or write a partial adapter to evade audit.|
|zeromatch|Official README explicitly lacks onMatch/onIgnore/onResult and makeRe returns a string, not RegExp; native prebuild/source fallback adds platform tooling.|Reject as a drop-in for the actual consumers.|
|upstream PR194|Official PR is open and explicitly says +(*a) remains exponential and outside its fix scope.|Not a CVE fix artifact.|
|replace Vite/Vitest/shadcn toolchain|Typescript-estree/tinyglobby remains another path; existing plugins,44 test files, config, Docker/dev/browser/CI contracts would require a separate migration.|Not a bounded substitute for the dependency fix. No complete verified replacement graph is claimed.|
|@ryotsu/picomatch4.0.7-a|Maintainer repository and published artifact explicitly contain targeted CVE parser changes; source/API files can be reviewed completely.|Candidate; exact approval and compatibility/security tests required.|

Sources: [zeromatch](https://github.com/orielhaim/zeromatch#compatibility),
[upstream PR194](https://github.com/micromatch/picomatch/pull/194),
[fork source](https://github.com/ryotsu-kankichi/secured-picomatch).

## Exact candidate and legitimacy audit

[VERIFIED: registry/source/cryptographic local checks] Package `@ryotsu/picomatch`
version4.0.7-a was published2026-10-29T07:07:43.070Z. Registry package creation is
2026-10-29T06:56:21.026Z. The single npm maintainer and declared contributor map to
the named GitHub fork. This is source/package identity continuity, not evidence of
an established maintainer reputation or upstream endorsement.

| Check | Result |
|---|---|
|Tarball|https://registry.npmjs.org/@ryotsu/picomatch/-/picomatch-4.0.7-a.tgz|
|SHA256|`7ec4864687a913bac593294c455c0b134e16d9db71fba9637342cd999b278a22`|
|SRI|`sha512-JroBFEmaejC7szGSfqOhF1QZHLKvX2wTA1+fWyfkpy3BjzdQKNPLKa2FtgeKVUDy5/UPUNkXEeCHJ5ZRBMLTVA==`|
|Registry signatures|Both ECDSA signatures verify with the matching official npm public key over name@version:integrity. This verifies registry integrity, not patch correctness.|
|Source binding|All10 published file bytes match exact GitHub commit3ab5a7627d480259e3d9ca67fbc14c125d374f0e. Commit is unsigned.|
|Provenance|Official npm SLSA payload binds the same tarball SHA512, commit, repository, refs/tags/4.0.7-a and publish.yml workflow. Full Sigstore certificate/log trust verification was NOT performed.|
|Lifecycle/runtime deps|No install/preinstall/postinstall/prepare hook in published scripts; no runtime dependencies. Development lint/Mocha/nyc scripts exist but were not run.|
|Installed slopcheck scan|Read-only scan returned SUS, not SLOP: FRESH_PACKAGE19days and LOW_DOWNLOADS637. No package install occurred.|
|Disposition|[ASSUMED] Candidate legitimacy/ongoing maintenance is not fully established; flagged source/security review and exact owner approval remain mandatory.|

No slopcheck installation was attempted. The already installed tool was invoked
only as `slopcheck scan --pkg npm @ryotsu/picomatch --json`; its install subcommand
was deliberately not used. A SUS result is disclosed rather than suppressed.

## Complete static source delta

[VERIFIED: all ten tar members compared] Six files are byte-identical to installed
upstream4.0.7: index.js, posix.js, LICENSE, lib/picomatch.js, lib/scan.js and
lib/utils.js. Changed files: package.json, README.md, lib/parse.js, lib/constants.js.
The complete958-line diff is mostly README replacement; full runtime changes are
available at the raw path below, not just the security claim.

[VERIFIED: static code] The targeted parser adds analyzeStarBranch, checks
single-branch wildcard extglobs, removes redundant outer quantifiers when its
analyzer judges collapse safe, and literalizes unsupported risky forms. Examples
in the source regression cover +(*a), *(a*), +(*), nested @ forms and complex
fallbacks. Existing maxExtglobRecursion:false deliberately disables the safeguard;
do not enable that option in consumers. Capture substrings can change.

[VERIFIED: static diff] The fork also contains three non-CVE behavior changes
compared to published upstream4.0.7: globstar matches newline via [\\s\\S], POSIX
bracket negation handling changes, and `**.js` fast-path handling changes; a
POSIX punctuation-class backslash correction changes constants.js. These must
be reviewed/tested as real scope, not presented as a security-only one-line fix.

[VERIFIED: v2/v4 utils comparison] Micromatch's older private utils contract is a
specific risk: v4 isWindows no longer takes its options argument. Utils used by
micromatch (isObject/isWindows/toPosixSlashes) still exist, and the other required
matcher callbacks/state methods remain, but static existence is not behavioral
compatibility. Test micromatch.capture Windows-option behavior explicitly; do
not claim cross-platform equivalence from Linux unit success alone.

## Prospective replacement — private files only

[VERIFIED: local npm resolution] The exact prepared manifest preserves all
existing direct versions and adds two override entries: global picomatch and
micromatch→picomatch both resolve to `npm:@ryotsu/picomatch@4.0.7-a`. npm11.19.1
resolved the copied lock with `--package-lock-only --ignore-scripts --no-audit
--no-fund`. No node_modules directory exists in the disposable directory, no
package code ran and no project file changed.

Private prospective files:
`/tmp/birja-phase12-replacement-research/prospective/package.json` and
`/tmp/birja-phase12-replacement-research/prospective/package-lock.json`.

| Binding | SHA256 |
|---|---|
|Base manifest|`73cd4f25fb329d7d0711321ee56dd9f07b25426eb9ddb69f3491396c2ccbdb59`|
|Base lock|`1461d4f89e875a5b915278e9d39ba413608fa4ff816fab6be6b21e280db5475b`|
|Prospective manifest|`7927bb09c2afc21160aa3964a890480eb67ce1edf62283c69b6bc3625dda57ed`|
|Prospective lock|`8994a5f4123a3f82715b603e1fd41ca9375e594ad146718235b35419b029d0a7`|

[VERIFIED: complete lock diff] Rootpicomatch identity/SRI changes to the fork and
nested affected2.3.2 is removed/deduplicated. All other existing package entries
retain exact bytes. npm also adds six optional inBundle inventory entries under
the already locked @tailwindcss/oxide-wasm32-wasi: @emnapi/core1.11.1,
@emnapi/runtime1.11.1, @emnapi/wasi-threads1.2.2, @napi-rs/wasm-runtime1.1.4,
@tybys/wasm-util0.10.2 and tslib2.8.1. These incidental entries are included in
the proposed diff and need review; no full-graph clean audit is claimed.

[VERIFIED: resolver behavior] Initial lock-only resolution retained the stale
nested2.3.2 entry, and package-lock-only npm ls correctly failed ELSPROBLEMS.
Adding the explicit micromatch override alone did not remove it. In the private
copy only, removing that stale lock node and rerunning the official resolver
produced the final graph; no fabricated version/integrity was written.
`npm ls picomatch --all --package-lock-only --json` now exits0 and all consumers
resolve the fork. This is graph validation, not installed compatibility.

## Validation Architecture

[VERIFIED: existing plan/runner/config] Before installation, obtain independent
source/security review of the entire delta, including the recent-maintainer
warning, unrelated runtime changes and major2→4 compatibility. If accepted,
present exact manifest/lock/tarball/source bindings and request explicit package
approval; do not automatically reuse the prior nonexistent-upstream-patch plan.
Plans29/30 must be revised to admit the now requested concrete replacement.

After approval: install only exact locked files with scripts disabled; test
targeted ReDoS cases in subprocesses with hard timeouts, root/nested consumer
resolution, scan.parts/base, makeRe RegExp, onResult/state/returnObject and
micromatch private utils/capture semantics. Test affected dotfiles/brackets/
newlines/fastpaths and actual configured include/exclude glob lists. A green
alias-based npm audit alone cannot establish security because the fork has a
different advisory identity. Preserve the source regression and adverse cases.

Then run unchanged frontend lint/types/format/958-test coverage/build, strict
full npm audit and independent repair review. The actual complete all-security
and fresh same-archive serial recovery must subsequently pass at the frozen
replacement source, retaining existing coverage/image/TLS/authority/refusal
gates. Separate old diagnostics are not a whole-run pass. Meaningful rendered
regression requires actual review; a lock change alone does not erase accepted
UI/native200 outcomes. All seven Phase12 requirements remain pending meanwhile.

## Runtime State Inventory and environment

[VERIFIED: scoped source] No stored financial data/schema, secrets/env names,
OS registration or live service configuration needs a change for an npm alias.
Production was not inspected. Existing local node_modules/build artifacts and
future Docker builds do require exact reinstallation/rebuild after approval;
old package caches do not prove adoption. Node24.22.1/npm11.19.1 and slopcheck
were available. Context7/ctx7 CLI was unavailable; official source and registry
were used. No tool was installed.

## Sources and private evidence

- [Fork official repository](https://github.com/ryotsu-kankichi/secured-picomatch)
- [Exact source commit](https://github.com/ryotsu-kankichi/secured-picomatch/commit/3ab5a7627d480259e3d9ca67fbc14c125d374f0e)
- [Official scoped registry](https://registry.npmjs.org/@ryotsu%2fpicomatch)
- [Official provenance](https://registry.npmjs.org/-/npm/v1/attestations/@ryotsu%2fpicomatch@4.0.7-a)
- [npm public signing keys](https://registry.npmjs.org/-/npm/v1/keys)
- [zeromatch compatibility](https://github.com/orielhaim/zeromatch#compatibility)
- [upstream PR194](https://github.com/micromatch/picomatch/pull/194)

[VERIFIED: local artifacts] All raw evidence lives under
`/tmp/birja-phase12-replacement-research/`: ryotsu-metadata.json,
ryotsu-4.0.7-a.tgz, ryotsu-source-3ab5a762.tar.gz, ryotsu-attestation.json,
ryotsu-commit.json, npm-signing-keys.json, source-binding.json,
fork-upstream.diff, fork-static/, upstream-regression-source.js.txt,
prospective-delta.json and prospective/. `inventory-sha256.json` records every
private artifact hash. The downloaded source/tarball was inspected statically
only; no replacement code or test campaign executed. No commits were made.

## Assumptions and remaining decisions

1. [ASSUMED] New fork maintainer legitimacy and continuing maintenance are not
   fully established. SUS warning and incomplete Sigstore trust verification
   require honest independent review and explicit owner acceptance.
2. [ASSUMED] The actual consumer graph remains compatible, especially old
   micromatch/capture/Windows behavior. Must be demonstrated after approval.
3. [ASSUMED] The parser change safely addresses all targeted attack forms;
   static review supports a plausible fix, not an independent security proof.

Research supplies a concrete replacement packet. It does not mark Plan29 or
Phase12 complete, authorize installation, waive a gate, or start Phase13.

## Final independent-review disposition and bounded follow-up

**Current recommendation: do not apply the rejected prospective lock.**
[VERIFIED: 12-REPLACEMENT-REVIEW.md] Independent preinstallation review rejects
@ryotsu/picomatch4.0.7-a with one blocker and one warning. The new branch analyzer
runs only for one branch; `+(*a|b)` still derives an ambiguous nested-quantifier
regex with default safeguards enabled. The review's separate built-in-RegExp
experiment exceeded its2second process limit at28repeated characters. Candidate
module code itself was not executed. The major2→4 private Windows capture
contract warning is separately retained. Authentic artifact signatures do not
establish a correct security patch.

[VERIFIED: bounded official-source follow-up] One final sweep examined the
upstream issue-linked proposed fixes, limited to two credible source candidates,
without another advisory/registry refresh, download, install, code execution,
audit or test campaign:

| Candidate | Primary evidence | Disposition |
|---|---|---|
|Upstream PR237, seeibt/picomatch|[Open PR237](https://github.com/micromatch/picomatch/pull/237) explicitly limits its rewrite to a single branch with a top-level star; no maintained published artifact/backport identified.|Not an eligible replacement; does not establish a remedy for the demonstrated multi-branch bypass.|
|Upstream PR238, rborlone/picomatch|[Open PR238](https://github.com/micromatch/picomatch/pull/238) adds a leading-quantifier per-branch guard, but explicitly retains `+(a*)` patterns and documents an unhandled nested-group/trailing-content limitation. Author states they are not an upstream maintainer; merge/release is pending.|No eligible maintained published artifact; its own documented scope does not establish complete safety. Do not adopt an unmerged branch as an approved fix.|

[CITED: https://github.com/micromatch/picomatch/issues/234] The official issue
still records proposed fixes awaiting maintainer review/release. This follow-up
did not identify another defensible, maintained drop-in artifact. This is a
bounded search conclusion, not proof that no alternative could ever exist.
Previously assessed zeromatch remains API-incompatible with actual consumers;
minimatch remains unsuitable for a direct alias. The rejected private packet
and its integrity inventory are preserved unchanged for audit.

The next defensible paths are a properly maintained reviewed fix when available,
or an explicitly scoped frontend-toolchain migration that removes all affected
consumers while preserving tests/build/CSS behavior. The latter is broader than
substituting a leaf package and needs its own concrete architecture decision,
dependency review and checked plans; it has not been silently authorized or
implemented here. Do not manufacture a local parser/fork or clean audit identity
to claim success. Phase12 remains blocked; no completed work, owner acceptance
or deferred Phase7 result changes.
