# Phase12 — accepted picomatch risk

**Owner decision (2026-11-17):** “can you create an issue in gh for the future about this and continue without fixing it?”

**Follow-up:** https://github.com/YokAI-open/Birja/issues/35. Read-back verified
issue35 is OPEN with title “Follow up on deferred picomatch security advisory
GHSA-fc5q-39xc-vjpf”. No internal exposure or exploit details were published in
that issue. This record documents accepted unresolved risk, not remediation.

## Exact scope and expiry

- Only HIGH advisory GHSA-fc5q-39xc-vjpf / CVE-2026-112366, reported on
  picomatch with affected range<=4.0.7, is accepted.
- Current locked instances remain4.0.7 and nested2.3.2; neither was replaced.
- Manifest SHA256:73cd4f25fb329d7d0711321ee56dd9f07b25426eb9ddb69f3491396c2ccbdb59.
- Lock SHA256:1461d4f89e875a5b915278e9d39ba413608fa4ff816fab6be6b21e280db5475b.
- Review expires at2026-12-17T00:00:00Z; reassess sooner on a maintained fix,
  dependency graph change, new finding or changed exposure.

## Exposure assessment and safeguards

The dependency is used by frontend development/build/test tools. Production
serves compiled static frontend files through nginx. No ordinary application
user-input path into this matcher has been identified; this is not a complete
exploitability proof. Keep development tooling and glob/config inputs trusted.
The known vulnerability remains capable of excessive CPU use for crafted
patterns. The rejected fork and previous no_candidate reports stay historical;
they do not become approved package candidates under this acceptance.

The CI/local audit checker runs the full npm audit with development dependencies
included and prints its complete raw report. It labels this finding
accepted-risk and references issue35. Critical findings, other HIGH advisories
(including another one on picomatch), changed locked inputs, expired approval,
transport/timeout failures, malformed reports and broken/unrooted cause graphs
are blocking. Inherited HIGH entries qualify only when they reach the exact
allowed advisory and no other HIGH cause exists. Moderate reporting retains
the existing audit-level policy; it is not erased. There is no package-wide
ignore, omit-dev option or command-line override of the exception.

## Qualification boundary

The same advisory also appears in the Node tooling image's npm-bundled
picomatch4.0.4, exact path
usr/local/lib/node_modules/npm/node_modules/tinyglobby/node_modules/picomatch/package.json.
The image checker alignment applies the SAME accepted CVE/GHSA only to that
exact Node target/path/version, current frontend Dockerfile hash and existing
expiry. Raw findings remain visible with separate accepted/blocking counts;
no other target/advisory or critical severity is excepted.17image contracts
and independent review0/0 pass. This does not accept CVE-2026-119170 in Python.

CI and the complete local security runner invoke the same Node-only helper.
No dependency install, manifest/lock alteration, financial/runtime authority
change, provider operation or production/publication action is authorized here.
The validation runner is itself in PORTFOLIO_PAYLOAD_V1: changing its audit
command requires Plan31's fresh complete one-archive seven-stage recovery.
Previous recovery and failed audit receipts must remain unchanged.

Both owner UI/native200% checks and completed01–28 remain accepted. Phase7
live requirements remain separately deferred. Plan29 risk disposition does not
close Phase12 or any requirement before reviewed implementation, actual current
qualification and independent final verification.
