# Phase12 — exact Wolfi Python security patch review

**Reviewed:** 2026-11-17. **Disposition:** concrete local patch is available;
owner authorization is required before installation/build. No package was
installed and no repository source, lock or image was changed by this review.

## User constraints

[VERIFIED: owner decision and12-EXCEPTION-CONTEXT.md] Issue35 accepts only
the picomatch advisory. It does not waive this separate Python finding.
Plan31 excludes package installation without a concrete approved repair.
Keep all unrelated audit/image/coverage/recovery gates and existing source
history. No production, provider operation, publication or deployment follows.

## Exact proposed change

[VERIFIED: backend/Dockerfile] Change the shared python-base pins:

| Package | Current | Proposed |
|---|---|---|
|python-3.14|3.14.10_git20261104-r0|3.14.10_git20261111-r0|
|python-3.14-base|3.14.10_git20261104-r0|3.14.10_git20261111-r0|
|python-3.14-runtime, exact transitive|3.14.10_git20261104-r0|3.14.10_git20261111-r0|

[VERIFIED: source] The only planned source edits are the two pin values in
backend/Dockerfile and their matching assertions at
deploy/tests/test-image-contracts.py:422–423. The existing Wolfi base digest,
uv version, npm/Node image and Python/npm manifests/lockfiles stay unchanged.
Both runtime and test-builder inherit the repaired shared interpreter family.

## Finding and applicability

[VERIFIED: actual retained Trivy reports] The actual complete qualification at
f97b2d9 failed final image scans with CVE-2026-119170 in all three Python
package entries in both runtime and builder. Reports advertise the exact fixed
version above, corroborated by the official current Wolfi index and SecDB.
Original reports remain at
/tmp/phase12-accepted-retry1-image-reports-f97b2d9/{runtime,builder}.json.

[CITED: https://github.com/python/cpython/issues/160923] The upstream defect
is a Python3.14.10 hashlib FIPS-property regression. The upstream3.14 fix is
[merged PR160984](https://github.com/python/cpython/pull/160984), November6.
[VERIFIED: actual report description] Only OpenSSL FIPS-mode users are
described as affected. No Birja FIPS-use evidence was established in this
review; that limits the exposure assessment but does not invent another
exception to the retained image policy. An official fixed package is available.

## Official package identity and integrity

[VERIFIED: official repository download] The three exact x86_64 artifacts
exist at https://packages.wolfi.dev/os/x86_64/ and match these whole-archive
SHA256 values:

| APK | Bytes | SHA256 |
|---|---:|---|
|python-3.14-3.14.10_git20261111-r0.apk|39130|3705d78308f435bf3974b1fd85818cf48a98d6d09446c1d914f1e8f8f0ecc537|
|python-3.14-base-3.14.10_git20261111-r0.apk|13093293|af4e39d237eba3107c4b2347ae9710c0a682805a9805bfb143d7908bc98862bf|
|python-3.14-runtime-3.14.10_git20261111-r0.apk|39454|4bbce9760758830a14f4f9113eda1eeabdfd4bf19a03e5ddaeb5871c1f5868ca|

[VERIFIED: current official APKINDEX] The signed index SHA256 is
3c4eb7df6a14ee81431a4a9a99b381b0224794846ada3370ca457e14430b00d1.
All three records identify maintainer wolfi, origin python-3.14, PSF-2.0,
x86_64 and recipe commit2283fc0b206ee1f8c592ed0633b432fa86f5a9c3.
The first depends exactly on the runtime package, which depends exactly on
the base package at the same version. Base native-library dependencies remain
ordinary Wolfi shared-library constraints, not a new Python ABI family.

[VERIFIED: existing trusted APK tool, network-disabled read-only container]
The actual installed runtime engine image
sha256:98c60b5b14be62527ede5d83f473353785a308cd5116f7dc12b5c3d5304a0018
contains wolfi-signing.rsa.pub. Its existing apk verify reports the official
APKINDEX signature OK. The downloaded APKs have no individual .SIGN member,
so standalone apk verify reports UNTRUSTED for them; do not describe them as
individually signed. Their first compressed control-member SHA1 values match
the authenticated index Q1 checksums, and each authenticated .PKGINFO datahash
matches SHA256 of its full compressed data stream. The complete chain verified
here is signed index → control checksum → data checksum. No candidate Python
or package lifecycle code executed.

[VERIFIED: Wolfi SecDB] Official security.json SHA256
b3a2225e54ca53c2596ce6f301bcb9de163ec954277afc5f22d23e464a59f268
lists CVE-2026-119170 and related identifiers as fixed in
3.14.10_git20261111-r0 for origin python-3.14.

## Resolution-only evidence and limits

[VERIFIED: offline read-only simulation] Using that exact existing runtime
image, the signed local official index, --no-network/--no-cache,
--repositories-file /dev/null and add --simulate with the two exact new pins
resolves **only the three Python-family upgrades** against the currently
qualified installed image. No files or package database were changed.

[VERIFIED: separate conservative simulation] Adding --upgrade also elects
eleven unrelated native/pip-wheel upgrades: py3-pip-wheel26.2.2-r3,
libbz2-1:1.0.8-r31, libffi3.8.1-r0, gdbm1.26-r10, xz5.8.4-r2,
libstdc++16.2.0-r4, ncurses-terminfo-base/ncurses6.6.20261114-r0,
readline8.3-r4, libuuid2.42.4-r3 and libzstd1:1.5.7-r14.
Do not add --upgrade to the Dockerfile or pretend that broader simulation is
the minimal repair. A clean rebuild starts from the pinned base rather than
the installed runtime; its native transitive resolution may differ. Capture
the actual resulting complete package inventory/diff and refuse unexpected
unreviewed changes before final qualification. This review does not claim a
frozen full clean-build transitive closure or successful rebuilt scan.

[ASSUMED / provenance limitation] The index's recipe commit is recorded, but
the exact corresponding GitHub recipe URL returned404 in this bounded lookup.
The source recipe bytes/commit signature were therefore not independently
verified. Official signed index identity and SecDB are verified as above.
No new legitimacy checker was installed; npm/PyPI-name checks would not verify
these APK ecosystem artifacts and were not misapplied.

## Local approval and validation scope

Request approval for the exact two source pin updates, matching image-contract
assertions, isolated local rebuilds and affected rechecks. Show the three
artifacts/checksums and clean-build transitive limitation. No blanket security
waiver or production change is proposed. Preserve the separate picomatch
accepted-risk treatment and issue35.

After approval, verify the exact family package inventory in rebuilt images,
run image contracts, affected container smoke/financial/TLS consumers and fresh
image scans. The updated interpreter is a runtime-image change, so Plan31's
source-bound complete security and fresh same-archive seven-stage recovery
remain required. Do not close the phase from a simulated resolution.

## Private evidence

[VERIFIED: local artifacts] All retained downloads and parsed metadata are in
/tmp/birja-phase12-python-package-review/: APKINDEX.tar.gz, the three APKs,
review.json, security.json, security-family.json,
index-checksum-verification.json and data-integrity.json. Observation time is
2026-11-17T21:24:55.197490Z. Only this report and private static evidence were
written; no repository source/lock/state, package/image or service changed.

## Subsequent owner approval and local execution

The owner explicitly approved this exact reviewed Python-family patch and
isolated local builds/rechecks. That approval was relayed to the executor
before applying the two pins. The resulting clean-build closure consists
of the three proposed Python packages and exactly the eleven already
disclosed native versions, with no unexpected package/version.
See12-PYTHON-REPAIR.md for complete before/after inventories, authenticated
control-checksum comparisons, actual image IDs and read-only interpreter
checks. This addendum does not relabel the original preinstallation review
as an installation proof or claim final scan/recovery qualification.
