# Phase11 exact dependency repair

The mandatory unrestricted `uv run pip-audit` initially failed on the existing
runtime transitive `opentelemetry-api==1.45.1`, CVE-2026-126360 /
GHSA-mf5v-w3w3-f6cg. Five strict HIGH/CRITICAL image scans passed at that point;
they do not supersede the failing unrestricted dependency audit.

The [upstream advisory](https://github.com/open-telemetry/opentelemetry-python/security/advisories/GHSA-mf5v-w3w3-f6cg)
rates the issue Moderate, CVSS3.1 5.3: an oversized malformed traceparent carrier
retaining a newline can cause excessive parsing CPU. Exposure depends on the
application's carrier/instrumentation; actual exploitability here is not claimed.
The advisory does not demonstrate data disclosure, modification or code execution.
The [official patch release](https://github.com/open-telemetry/opentelemetry-python/releases/tag/v1.45.2)
identifies the512character limit. Runtime dependency origin is pinned
FastAPI0.162.0 → opentelemetry-api, recorded in backend/uv.lock. This is not
merely a development-tool dependency.

## Exact review and approval

The owner explicitly selected **“Approve patch and continue locally
(Recommended)”** for only opentelemetry-api1.45.1→1.45.2, the reviewed wheel
hash below, unchanged other dependencies/manifests, local locked installation,
image rebuilds and affected verification. Production, installed host tools,
providers, B2, timers and publication remain excluded. Missing wheel signature
and attestation were disclosed before approval. Approval was relayed by the
orchestrator during this execution; no broader package authorization is inferred.

[Official PyPI metadata](https://pypi.org/pypi/opentelemetry-api/1.45.2/json)
identifies organization opentelemetry and the same upstream repository; Python
>=3.10 includes3.14 and the sole dependency remains typing-extensions>=4.5.0.
The wheel is not yanked, uploaded2026-10-29T17:29:06.955093Z:

- `opentelemetry_api-1.45.2-py3-none-any.whl`,60335bytes.
- SHA256 `2cbd737377e710ee740d261c94e93fa0f08e6d037c18f17513cc0a2d94479a34`.
- Downloaded bytes match PyPI; ZIP paths, METADATA and propagation source were
  inspected without executing the downloaded archive before approval.
- PyPI `has_sig=false`; exact wheel provenance endpoint returned404. GitHub's
  verified release-commit signature does not independently bind this wheel.

A temporary no-build/no-Python-download `uv lock --upgrade-package
opentelemetry-api==1.45.2` proved exactly one changed full package entry and zero
added/removed packages. `pyproject.toml`, all other lock entries and existing
package constraints remain unchanged. The exact approved prospective lock was
applied; `uv sync --locked --no-build --no-python-downloads` reported one package
uninstalled/installed,1.45.1→1.45.2. No alternative package was substituted.

## Retained review receipts

Private review directory `/tmp/birja-phase11-package-review` retains official
metadata, inspected wheel/source, provenance404, resolution command/log and the
concrete prospective lock diff. These are public package artifacts, not account
or provider credentials.

| Artifact | SHA256 |
|---|---|
| Original repository lock |81c8421f541a5a37966bfe5a87f0e642301911ce5ed345b0c49d37a655f73e69|
| Approved replacement lock |5622e840e9a8312f930523cd1bedb9830e9ce5679d9aa77d7c1696784eb317c8|
| REVIEW.md |91f0b46d19762e59da535709046d7ca58146cc9cf7f2b3b0e61b008bc7f0f9b6|
| receipt.json |7d9f54c50524877f6b5bb17362dd48acef2448a52fee891067ed119246f447f8|
| prospective-lock.diff |38eff451fd0bae110e9a7f28fc4d493d489e5f4b4874ba41b782c4262911614c|

The patched mandatory pip-audit reports no known vulnerabilities. Final-source
coverage, package inventory delta, native/image/browser/dev and recovery outcomes
belong to11-LOCAL-PROOF.md. Earlier prepatch passes retain their earlier package
and image identities and are not relabelled as patched execution.
