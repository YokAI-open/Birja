# Phase12 — approved local Python image patch

**Status:** approved pin repair, targeted checks and local builds complete.
Independent review passed0blockers/0warnings; actual full Plan31 qualification remains pending.

The owner approved3.14.10_git20261104-r0→3.14.10_git20261111-r0 for the
shared Python family. Only two pins in backend/Dockerfile and their two
matching test-image-contracts.py assertions changed. The base image, uv,
Node/npm, Python/npm manifests and locks remain unchanged.

## Actual validation

- 17image contracts passed in0.662s.
- 37CI contracts passed in7.677s; git diff --check passes.
- Actual declared test-builder and runtime Docker builds exit0, using normal
authenticated APK resolution without --upgrade/--allow-untrusted.
- The committed backend/.dockerignore excludes .env/.env.*, host virtualenv,
caches and coverage from the build context.
- Both actual interpreters run as UID1001 under a read-only filesystem,
network none, all capabilities dropped and no-new-privileges. Python reports
3.14.10 built November11; OpenSSL4.0.3 and SHA256 smoke checks pass. Observed
default FIPS mode is0; this does not claim an exercised FIPS-mode regression.
- Runtime Config.User remains app. Builder configuration remains the original
root tooling image; its interpreter smoke also ran explicitly as1001.

| Target | Actual engine image ID |
|---|---|
|test-builder|sha256:5e5527fb8ced77259d5eab0a47c7a1d14b549c2b460f8b3b084d51a0c8ee7553|
|runtime|sha256:6a692a98fa979d6a24261b8426b53e9423053e1a4dc3e5faf6122d0b2744d2a7|

These are precommit local repair builds, not a final-source qualification.

## Complete package closure

Prior scanned runtime98c60b5b14be62527ede5d83f473353785a308cd5116f7dc12b5c3d5304a0018
and builder68fb7993af7ff8ac6e352d2527d158d2de12bb2cc42470a24cfa0a116a13d307
have identical36-package APK inventories, including control checksums.
Both new inventories still contain36packages, with no additions/removals.
Exactly three approved family and eleven previously disclosed native versions
changed; no unexpected package/version was adopted.

| Package | Before | After |
|---|---|---|
|python-3.14, python-3.14-base, python-3.14-runtime|3.14.10_git20261104-r0|3.14.10_git20261111-r0|
|py3-pip-wheel|26.2.2-r2|26.2.2-r3|
|libbz2-1|1.0.8-r30|1.0.8-r31|
|libffi|3.8.0-r2|3.8.1-r0|
|gdbm|1.26-r9|1.26-r10|
|xz|5.8.4-r1|5.8.4-r2|
|libstdc++|16.2.0-r3|16.2.0-r4|
|ncurses, ncurses-terminfo-base|6.6.20261107-r0|6.6.20261114-r0|
|readline|8.3-r3|8.3-r4|
|libuuid|2.42.4-r2|2.42.4-r3|
|libzstd1|1.5.7-r13|1.5.7-r14|

Every changed installed control checksum matches its exact record in the
already authenticated official APKINDEX. Every unchanged package retains its
original version/control checksum. Read-only clean-base simulation resolved
this same closure. libexpat1/mpdecimal/sqlite-libs remain unchanged.

## Evidence and limits

Private0700/0600 directory /tmp/birja-phase12-python-repair/ contains both
build logs, before/after raw inventories, read-only interpreter checks,
inspection.log, inspect-repair.py and complete result.json. The result binds
image identities, all14changes, control checksums, source/lock and log hashes.

result.json SHA256:
3f713442ccaba0b63914d69d5eaa4e9f67250dae895363f5b861c59505e83d69.
Both new raw inventories SHA256:
2406a68147a1e428f39763e67179d868d6ddb433f3fdcb1f8baaf4edacbab019.

No actual vulnerability rescan or financial/browser/TLS/recovery campaign ran
in this task. Independent12-PYTHON-REPAIR-REVIEW.md passed before freezing source for
complete security and fresh same-archive seven-stage recovery. The separate
picomatch acceptance remains visible. No source financial rules, global
planning state, requirement, production service or publication changed.
No repository commit was made by this executor.
