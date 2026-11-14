## Reviewed Docker runner capability correction —2026-11-09

Actual1bbaa69/run42616168904 passed backend/frontend/image/e2e and every
offline ops check including nginx. Populated image-transition passed30.200s.
Recovery package preparation then failed its pinned Docker image inspection.
Exact runner20261101.360 has Docker28.0.4/API1.48; image inspect --platform
requires API1.49+. Local29.2.1 supports the existing command.

RED8d3466f/GREENf5ad5cc pins matching29.2.1 CE/client packages from Docker's
official signed apt repo in the disposable ops runner, before fixture work.
The clean-root /usr/bin/docker/default socket preflight pulls the unchanged
pinned image and verifies platform inspection. Six CI contracts, focused Ruff/
diff and read-only old-API rejection/new-API command+identity-guard proof pass.
Independent DOCKER-CI-REVIEW reports0 blockers/0 warnings. VDS Docker/service,
recovery source, image pins and installed archive remain unchanged.

Publish under existing bounded CI completion authority; actual new-head
hosted setup/required CI remain pending. Merge/deployment and deferred nightly
proof retain their distinct gates. Phase10/15 unchanged.
