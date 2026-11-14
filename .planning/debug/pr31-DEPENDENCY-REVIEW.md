# PR31 exact dnspython repair review

Status: owner explicitly approved the exact patch and local continuation on
2026-11-14. The exact reviewed lock was applied and locked uv sync changed only
dnspython2.9.0→2.9.2; all other installed package names/versions match.

The [official advisory](https://github.com/rthalley/dnspython/security/advisories/GHSA-vvf4-9x63-8xvv)
identifies CVE-2026-128089, High/CVSS3.1 7.5, affecting versions below2.9.2.
An attacker-controlled WKS zone-record text service number can cause excessive
allocation and CPU. The fix bounds service numbers to0–65535 and bitmaps to8192
bytes, and replaces repeated byte appends with bounded extension. This is an
availability issue; exploitability in this application is not established.
Runtime origin is pydantic[email] → email-validator → dnspython.

[Official PyPI metadata](https://pypi.org/pypi/dnspython/2.9.2/json) links the
established rthalley/dnspython repository. Python>=3.11 supports the project's3.14;
ISC license. The default wheel has no required dependencies; optional extras are
not enabled by this resolution. Both artifacts are not yanked, uploaded2026-11-03:

| Artifact | Size | SHA256 |
|---|---:|---|
| dnspython-2.9.2-py3-none-any.whl |360455|af15f7d385a6ae2fb35a796fde2138004c8c42c7389090e2addc83e3b3340fd8|
| dnspython-2.9.2.tar.gz |455484|8d4d39a513e649d634004ce4d39ade2352efcea472a0247535a5c2d18a9d7ba9|

Downloaded bytes match metadata hashes. Wheel ZIP paths and METADATA were
inspected without executing package code. The [official tag comparison](https://github.com/rthalley/dnspython/compare/v2.9.0...v2.9.2)
contains additional parser/resolver correctness changes, not solely WKS; the
complete comparison is retained. WKS source was inspected in the downloaded wheel
and comparison. Tagv2.9.2 resolves854bedd6d641cb42785d26ca674ed2c0f20131e0;
the WKS fix commit is388db14ee9923288f6e73f86e482c77706e59d73.

PyPI has_sig=false (no detached legacy signature). Both PyPI integrity endpoints
return publishing attestations. Their retained envelopes identify the exact
artifact digest and GitHub publish workflow at refsv2.9.2, the same commit, and
GitHub Actions OIDC issuer. This is inspected provenance data; no independent
Sigstore trust-root/transparency-log cryptographic verification is claimed.

A temporary copy ran `uv lock --upgrade-package dnspython==2.9.2 --no-build
--no-python-downloads`. Parsed full package records prove exactly one changed
entry, zero additions/removals, unchanged project manifest and other entries.

- Existing lock SHA256:5622e840e9a8312f930523cd1bedb9830e9ce5679d9aa77d7c1696784eb317c8.
- Prospective lock SHA256:3eded7f21be30568f5d4fae129f38a11e19484035f60f1477a3f9b2bf30fd2d4.
- Exact diff SHA256:2b728829716340bd378306ce1b79a4f1ce6b74dbc7076577e767f5934579f284.
- Public review artifacts, command output, full comparison, provenance and receipt:
  `/tmp/birja-pr31-package-review/` (prospective lock under `prospective/uv.lock`).

The received approval is limited to applying that exact prospective lock, installing
the exact wheel locally via locked uv, rebuilding affected local images and
running affected audit/security/tests. No other package, provider, production,
installed host tool, publication, push or merge is included. The unrestricted
audit and strict including-unfixed image gates remain enforced.
