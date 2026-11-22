# Birja 0.6.0 rollout draft

Owner authorization: publish PR/full CI, merge/release and deploy portfolios;
stock activation remains a separate engineering follow-up. No milestone archival.

## Measured source and host

- Source PR #36 into develop; exact final release/main SHA must be recorded after CI.
- Production /srv/birja, birja-prod on DE189274; live source46d24c8, schema0008.
- Existing selected PostgreSQL and Redis volumes remain the same. Never treat
  phase06 candidates as empty. No volume removal, ownership repair or downgrade.
- Live PostgreSQL18.6; target pinned image reports18.7. Both use glibc2.44.
  Live database collation2.44; about8.6MB database and22GB free disk.
- Existing role secrets and database CA/server certificate retained (expires2027-11-10).

## Sequence

1. All six PR36 jobs pass; merge commit into develop. Prepare release-0.6.0
   with first-party version metadata and release notes. Keep third-party graphs
   byte-equivalent in substance; refresh only audit-policy file bindings after
   explicit metadata-only comparison, preserving issue35 scope and expiry.
2. All six release-PR jobs pass before main merge. Verify tested tree, publish
   v0.6.0 and GitHub release. Back-merge through a green PR into develop.
3. Prepare exact released-source retained tooling and validate the v4 recovery
   archive. Preserve prior immutable tools and current service identities.
   Stage protected configuration; retain the old deploy manifest and add the
   new one (below the existing20-file cap). Portable recovery JSON will mirror
   actual configuration; backup release stays actual live46d24c8 until success.
4. Verify stock collection/actions remain disabled; no provider activation or
   credential changes. Current installed read-only compatibility inspector
   passes. Candidate inspection safely refuses old PG image/HBA identities.
5. Under one shared maintenance lock, stop writers and capture original financial
   preservation receipt. Install the exact released retained deploy tooling and
   verified v4 recovery archive; synchronize protected backup configuration.
   These host preparations do not modify database records. With actual old
   PG18.6/schema0008 still running, perform a fresh encrypted B2 backup and
   exact isolated full restore through the new independent tools.
   Then use existing birja-deploy --start-selected-datastores. Its startup
   admission binds that exact completed restore before transitioning only the
   already selected live volumes to reviewed PG18.7/new immutable HBA directory.
   Do not copy, replace, chown or remove volumes. Database revision stays0008;
   glibc/collation2.44 is unchanged. Check compatibility after startup.
   Live0008 lacks birja_action_operator. Now use reviewed configure-db
   --production --apply --approved-operation populated-role-transition to
   preprovision the fixed NOLOGIN/NOINHERIT role, with existing stored runtime
   and migrator credentials. No manual grants, schema repair or new secret.
   After role/security transition, take and exactly restore a fresh0008 backup
   with final roles/config/tool binding before any application migration.
   Preserve private receipts. Existing $0/headroom/one-verified-copy policy stays.
6. Deploy using the authenticated retained launcher at the exact released SHA.
   Build before cutover; stop writers during the guarded0008-to0023 migration.
   No direct table changes, role shortcuts or grant repair. If a guard fails,
   preserve diagnostics and stop before further mutation.
7. Confirm healthy backend/single scheduler, verified-TLS restricted roles,
   schema0023, preserved original funding/ownership/financial counts, origin
   and public smoke. Do not create fake production users or spend real user
   virtual balances for testing. Owner can perform final interactive acceptance.
8. After success, synchronize protected backup release to actual deploy log,
   take and exactly restore the post-rollout backup; refresh the encrypted
   off-server recovery export using existing custody policy.

## Failure boundary

Before migration, existing stopped old application containers can restart
against unchanged0008 only after reviewed source/image/TLS compatibility and
original financial checks; preserve their exact identities during preparation. After0023, the old0008 application is
incompatible and automatic downgrade is forbidden. Preserve the database and
private failure evidence; use only tested compatible code/fix-forward, or a
separately reviewed exact restore with explicit data-loss disposition. Never
restore an old snapshot over newer user activity merely to make rollback pass.

## Remaining records

Record exact CI run/head/tree, main/tag, installed manifest and recovery archive,
snapshot IDs, measured restore timing, schema/image identities, smoke results
and actual production outcome. Historical synthetic/failed evidence stays intact.
