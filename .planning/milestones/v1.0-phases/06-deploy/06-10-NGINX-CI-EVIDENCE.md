# Nginx CI privilege correction — 2026-11-09

Actual PR26 run42588116337 at995b464 passed backend, frontend, image and e2e.
Ops passed the prior root prerequisite fix and reached the final offline
nginx configuration check. It failed opening /var/log/nginx/access.log as
the unprivileged runner; the existing check script documents its root need.

RED49df53f adds a regression for the privileged invocation; it failed before
the fix. GREENeec70c5 adds only sudo to that CI command. It does not change the
nginx helper or production configuration. The existing throwaway prefix and
EXIT cleanup remain; no nginx start/reload/restart occurs.

Executor verification: five CI contracts, Ruff lint/format and diff checks
passed. The actual root nginx-t check passed and its temporary prefix was
removed. No unchanged DB/app/image rehearsal was repeated.

Independent06-10-NGINX-CI-REVIEW:0 blockers,0 warnings; independently reran five
CI contracts and scoped diff check. Existing required producers and strict
image/security/test gates remain mandatory.

The owner's standing “Publish and finish CI” authorization covers this CI,
test and planning-only correction and feature-branch push/PR-body update.
Actual new-head GitHub CI remains pending until observed. Merge, release,
deployment and production changes are excluded;09 calendar proof is deferred.
