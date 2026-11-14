## Reviewed CI image-store alignment —2026-11-09

Actual58c4258/run42617492782 passed Docker29.2.1 setup/platform inspection,
offline ops, app/browser/image jobs and populated transition33.549s.
Recovery packaging then rejected classic archive membership at unchanged
verify_saved_image line280. Runner inspection exposed the config identity;
Docker documents that upgrades retain the classic store. Raw failed archive
members are unavailable; do not claim their exact difference was captured.

REDb44f381/GREEN57974aa preserves existing daemon JSON/features while enabling
containerd only on the disposable ops runner, before restart/pull/build. New
test-only preflight checks the driver, saves the unchanged pinned public PG
image, authenticates registry provenance and invokes the original strict
archive verifier with anonymous temporary-file cleanup and bounded save.
Seven CI contracts, Ruff/format/diff and actual local containerd export+
unchanged verifier4.929s pass. Independent STORE-CI-REVIEW reports0/0.

Publish under existing bounded CI completion authority. Actual runner replay
remains pending; no VDS daemon change, recovery code/image pin/installed bundle
change or new production action. Merge/deployment and deferred nightly proof
remain separate; phase10/15 unchanged.
