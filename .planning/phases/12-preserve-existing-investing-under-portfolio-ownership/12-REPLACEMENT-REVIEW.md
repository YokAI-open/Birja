---
phase: 12-preserve-existing-investing-under-portfolio-ownership
reviewed: 2026-11-17
depth: deep
files_reviewed: 14
files_reviewed_list:
  - /tmp/birja-phase12-replacement-research/fork-static/index.js
  - /tmp/birja-phase12-replacement-research/fork-static/posix.js
  - /tmp/birja-phase12-replacement-research/fork-static/package.json
  - /tmp/birja-phase12-replacement-research/fork-static/LICENSE
  - /tmp/birja-phase12-replacement-research/fork-static/README.md
  - /tmp/birja-phase12-replacement-research/fork-static/lib/parse.js
  - /tmp/birja-phase12-replacement-research/fork-static/lib/constants.js
  - /tmp/birja-phase12-replacement-research/fork-static/lib/picomatch.js
  - /tmp/birja-phase12-replacement-research/fork-static/lib/scan.js
  - /tmp/birja-phase12-replacement-research/fork-static/lib/utils.js
  - frontend/node_modules/micromatch/index.js
  - frontend/node_modules/micromatch/node_modules/picomatch/lib/utils.js
  - /tmp/birja-phase12-replacement-research/prospective/package.json
  - /tmp/birja-phase12-replacement-research/prospective/package-lock.json
findings:
  critical: 1
  warning: 1
  info: 0
  total: 2
status: issues_found
installation_recommended: false
candidate: "@ryotsu/picomatch@4.0.7-a"
candidate_source: 3ab5a7627d480259e3d9ca67fbc14c125d374f0e
candidate_execution: false
---

# Phase12 replacement preinstallation review

## Narrative Findings (AI reviewer)

**Recommendation: reject this artifact as the security replacement.** Its
single-branch patch is substantive, but a direct two-branch form still reaches
the same nested-unbounded-quantifier problem with default safeguards enabled.
The registry-name change could remove advisory matches without removing this
security defect. Do not install the candidate or ask the owner to approve it
as a reviewed fix on the basis of a future clean npm audit.

This is an independent static source/consumer and artifact review, not an
installed compatibility or complete-security pass. No replacement module,
source test or lifecycle script was executed. The one bounded behavioral
experiment below uses only Node's built-in RegExp and a source-derived literal;
it does not assert that candidate code was run.

## Critical Issues

### CR-01 — BLOCKER: multi-branch repeated wildcard bypasses the safeguard

**File:** `/tmp/birja-phase12-replacement-research/fork-static/lib/parse.js:414`.
Related guards: lines355–421; close emission: lines614–649;
`lib/constants.js:26` and its `extglobChars` plus entry define lazy unrestricted
stars and the outer plus quantifier. `lib/picomatch.js:273` wraps the output
with anchored matching.

**Issue:** The new `analyzeStarBranch` safety check is called only when
`branches.length === 1`. Pattern `+(*a|b)` instead has two nonempty branches.
Neither is a bare wildcard string; `hasRepeatedCharPrefixOverlap` discards
`*a` because it is not a plain branch. `getStarExtglobSequenceChars('*a')`
does not recognize a `*(...)` expression, neither branch has nested repeated
extglob depth, and `sawStarSequence` stays false. The final return is therefore
`{ risky: false }`, without collapse or literalization, under the default
`maxExtglobRecursion: 0`.

Tracing the ordinary tokens and unchanged `plus.close` emits the significant
anchored regex `^(?:(?=.)(?:[^/]*?a|b)+)$`. For an input consisting of repeated
`a` followed by `!`, the outer repetition and inner wildcard can divide the
same run of `a` into exponentially many partitions before the final failure.
This bypass does not disable safeguards or use a nondefault parser option.
Similarly, plain overlapping alternatives such as `+(ab|abab)` are not
covered by the special repeated-single-character-prefix guard; the security
review must not limit itself to the advertised `+(*a)` regression.

**Bounded independent evidence:** Separate fresh Node processes evaluated only
the derived literal above against `"a".repeat(n) + "!"`, with a2second parent
timeout per process and a stripped environment. No require/import of downloaded
code occurred. Results were false at n12/16/20/24, approximately5.30/7.87/71.93/
1108.26ms respectively; n28 exceeded the2second hard limit and its subprocess
was terminated. These measurements support the source-derived exponential
backtracking finding, not a claim of actual candidate execution. The concrete
branch trace is the basis for rejecting the candidate.

**Impact:** The proposed dependency still compiles a small attacker-controlled
glob into a pathological regex. This is the same relevant denial-of-service
class being remediated, not a general speed/style concern. Birja's arbitrary
public-request reachability has not been established; its build/test tooling
graph is the reviewed exposure. That uncertainty does not satisfy the strict
security replacement requirement.

**Fix:** Do not adopt this exact artifact. Require a maintained published
replacement that rejects or safely compiles all ambiguous quantified branches,
including multi-branch wildcard and overlapping-literal forms. Any future
candidate needs source review plus subprocess-bounded adversarial regressions
for `+(*a|b)`, `*(*a|b)`, `+(ab|abab)`, the original single-branch forms and
matching-semantics controls before qualification. Do not locally alter this
fork, rename it again or use an advisory-identity change as the fix.

## Warnings

### WR-01 — WARNING: global override changes micromatch's Windows capture contract

**File:** `/tmp/birja-phase12-replacement-research/fork-static/lib/utils.js:17`.
Consumer: `frontend/node_modules/micromatch/index.js:366`.
Prior implementation:
`frontend/node_modules/micromatch/node_modules/picomatch/lib/utils.js:32`.

**Issue:** The proposed override replaces micromatch's picomatch2.3.2 with a
major4-derived implementation. Micromatch calls private `utils.isWindows(options)`
to decide whether to normalize backslashes before its capture regex executes.
The old utility honors explicit `options.windows`; the fork's unchanged major4
utility takes no argument and reads only the host platform. On a non-Windows
host, `micromatch.capture('**', 'a\\b', { windows: true })` no longer normalizes
its capture input to `a/b`. Conversely, explicitly disabling Windows mode on a
Windows host no longer controls this normalization. Public method existence
does not prove the old private contract is preserved.

**Fix:** Do not describe this override as fully API-compatible. A future
acceptable replacement must retain the old consumer contract or use a
compatible parent package. Add explicit cross-platform option/capture tests
without relying on the host OS, and qualify the actual configured glob
consumers. This warning is independent of the security blocker above; actual
application breakage from this capture API was not established.

## Artifact and source integrity checks

Independent read-only checks confirmed all22 entries in the research artifact
inventory, exact tarball SHA256
`7ec4864687a913bac593294c455c0b134e16d9db71fba9637342cd999b278a22`,
and equality of all ten published file bytes with both the extracted static
files and source commit archive3ab5a762. Both advertised registry ECDSA
signatures cryptographically verify over the exact package/version/integrity
using the saved matching npm public key. No trust in the patch follows merely
from those signatures. Full Sigstore trust-chain verification remains unperformed;
the source commit is unsigned and the new single-maintainer/low-usage warning
is retained. No unexpected runtime dependency, installation hook, network call,
eval or secret/file exfiltration path was identified in the reviewed runtime
delta. This is not a claim of established publisher reputation.

The complete prospective lock comparison independently confirms: one changed
root identity/SRI, removal of nested affected2.3.2, six added optional bundled
Tailwind WASM inventory entries, and byte-equivalent retained package entries.
The exact prospective manifest/lock hashes are respectively
`7927bb09c2afc21160aa3964a890480eb67ce1edf62283c69b6bc3625dda57ed` and
`8994a5f4123a3f82715b603e1fd41ca9375e594ad146718235b35419b029d0a7`.
Graph removal of the original package identities does not resolve CR-01.

## Disposition and limits

The project manifest/lock, installation, application source, global planning
state, accepted UI/native200 results and production remain untouched by this
review. No audit or financial/browser/recovery campaign ran. The parent must
record the rejected candidate and choose another remedy; neither Plan29 nor
Phase12 is complete. An exact package-approval request for this artifact would
be premature while the demonstrated security defect remains.

Primary source under review:
https://github.com/ryotsu-kankichi/secured-picomatch/commit/3ab5a7627d480259e3d9ca67fbc14c125d374f0e

_Reviewer: independent gsd-code-reviewer agent; source-only preinstallation scope._
