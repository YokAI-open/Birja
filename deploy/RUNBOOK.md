# Birja production runbook

Production runs at https://birja.nist.one on one host. This file covers deploy, rollback, manual certificate renewal, manual Cloudflare IP refresh and how to undo each host change.

## Overview

Request path: Cloudflare (SSL mode Full strict, D-03) -> host nginx -> 127.0.0.1:18000 -> compose project `birja-prod` (postgres, redis, backend).

Where state lives:

- `/srv/birja`: the prod git checkout (never the dev tree)
- `/etc/birja/prod.env`: prod secrets, root-only, mode 600
- `/var/www/birja`: built frontend releases, served by nginx
- `/var/lib/birja`: deploy history (`deploys.log`)
- `/etc/nginx/certs/nist.one`: the origin certificate
- Docker volumes `birja-prod_pgdata` and `birja-prod_redisdata`

The dev stack (project `birja`) is separate. Never run `-f docker-compose.prod.yml` from the dev tree.

## First-time setup (order matters)

1. Certificate, manual DNS two-step (D-08, no API token):
   `deploy/renew-cert.sh start` prints the `_acme-challenge` TXT record(s). The owner adds them in Cloudflare (DNS only). Then `deploy/renew-cert.sh check --wait`, then `deploy/renew-cert.sh finish`.
2. `deploy/install-nginx.sh` installs the nginx site and a catch-all 443 server (`conf.d/birja-default-tls.conf`, `ssl_reject_handshake on`): a TLS handshake with an unknown or missing SNI fails, so no foreign domain pointed at this origin gets the Birja app. Port 80 keeps the stock `default` site as its `default_server` (it already holds it; a second one would fail `nginx -t`), which serves only the local placeholder page.
3. `deploy/init-prod-env.sh` creates `/etc/birja/prod.env`. Then the owner adds `RESEND_API_KEY`.
4. `git clone https://github.com/YokAI-open/Birja.git /srv/birja`
5. `/srv/birja/deploy/deploy.sh`
6. `/srv/birja/deploy/smoke-prod.sh`
7. The owner adds the DNS record in Cloudflare: Type A, Name `birja`, IPv4 151.243.171.52, Proxy status Proxied (D-08).
8. `/srv/birja/deploy/smoke-prod.sh --public`

## Deploy (one command)

```bash
/srv/birja/deploy/deploy.sh                       # deploys main (D-02, D-05)
DEPLOY_REF=v0.1.0 /srv/birja/deploy/deploy.sh     # a tag, branch or SHA
```

Run as root. The script fetches and checks out the ref, then prepares everything before changing anything live: it builds the backend image, builds the frontend into a new release directory (not yet served) and tests the repo's nginx config offline (`check-nginx-config.sh`). Only when all of that passes does it go live: start postgres and redis, run migrations, start the new backend, switch the `current` link, install the nginx config and run the health check. Finally it records the deploy in `/var/lib/birja/deploys.log`.

The frontend is built from a clean `git archive` copy in a root-only temp dir, in the Node container as uid 1000 with `npm ci --ignore-scripts` (no dependency lifecycle scripts run; none are needed for this lockfile), and only regular files from `dist/` are copied into the release by root. `/srv/birja/frontend` is not written by the build.

A failure during preparation (npm, image build, nginx config) leaves the running backend, schema, served frontend and nginx config untouched; only the checkout has moved, and `--rollback` (or a fixed re-deploy) puts it back.

If the checked-out ref changes `deploy/deploy.sh`, the script logs `deploy.sh changed in <ref>; re-running the new version` and re-runs the new version once for the same commit (still holding the deploy lock), so a release is always deployed with its own deploy logic; tested offline by `deploy/tests/test-reexec.sh`.

If it fails, it prints the failing step and the last redacted backend log lines. Fix the cause and re-run, or roll back.

Releases reach `main` only through `release-*` or `hotfix-*` PRs (git-flow in CLAUDE.md).

## Rollback

```bash
/srv/birja/deploy/deploy.sh --rollback
```

This returns to the release that was live before the current one. It prints the target SHA and release before acting. Migrations are not undone. Phase 6 adds the separately installed recovery tooling described below; actual provider recovery and timer acceptance remain gated until recorded.

How the target is chosen (`/var/lib/birja/deploys.log`, one line per successful deploy or rollback, `time sha release ref`, ref `rollback` for rollbacks):

- The log is replayed as a stack of live releases. A deploy pushes its line. A rollback line pops lines until its own SHA is on top, so a release that was rolled back away from is never picked again; a second rollback goes one further back instead of re-deploying the bad release.
- Normally the target is the newest stack entry below the top with a different SHA, so repeated deploys of the same SHA are skipped (no silent no-op).
- A failed deploy is never logged. While a deploy runs, `/var/lib/birja/deploy.pending` exists; it is removed only when the deploy is recorded. If it is still there (or the checkout's HEAD differs from the top SHA), the last deploy failed, and the target is the top entry itself: the last good release.
- If there is no earlier release with a different SHA, it refuses ("nothing to roll back to").

The selection logic is tested offline by `deploy/tests/test-rollback-target.sh`.

What it does: checks out the target SHA, rebuilds the backend image, reuses the target's frontend release (or rebuilds it if pruned), tests that release's nginx config offline, restarts the backend, switches `current`, and reinstalls the nginx config from the rolled-back release with its own `install-nginx.sh` (so its CSP and limits match its frontend; birja-* files that release does not know, such as `birja-default-tls.conf`, stay installed). The health check passes only if the API is healthy and nginx serves exactly that release's `index.html` (it names the hashed assets), for deploys and rollbacks alike.

## Certificate renewal (manual, D-07, D-08)

There is no API token. The cert stays in acme.sh's list in manual DNS mode, and renewal is a two-step run by hand. The existing acme.sh cron line is unchanged (D-06); in manual mode it cannot renew this cert and only logs a failure (its output goes to /dev/null).

Next certificate expiry: 2027-01-25
Renew by (30 days before): 2026-12-26

The CA is Let's Encrypt (ECC, `*.nist.one` + `nist.one`, 90 days). On 2026-10-27 ZeroSSL's ACME endpoint returned 502, so the CA was switched to Let's Encrypt and the cert was issued by hand in manual DNS mode; `renew-cert.sh` uses the same commands with `--server letsencrypt`. The first Let's Encrypt cert was installed directly with `acme.sh --install-cert` (no pending file existed).

Procedure:

1. `cd /srv/birja && deploy/renew-cert.sh start` (run once; it prints the TXT name and value(s)).
   If it says "no challenge needed" (Let's Encrypt reused valid authorizations and issued at once), skip steps 2, 3 and 6 and run `finish` directly: without a pending file it only installs the issued cert and prints the dates.
2. In the Cloudflare dashboard (nist.one, DNS, Records) add each `_acme-challenge` TXT record, Proxy status DNS only, TTL Auto. With two values there are two records with the same name.
3. `deploy/renew-cert.sh check --wait`
4. `deploy/renew-cert.sh finish`
5. `deploy/smoke-prod.sh`
6. Delete the TXT records in the dashboard.
7. Update the two date lines above through a normal feature branch.

Cloudflare error cheat sheet:

- 521: origin refused the connection (nginx down or ufw blocking)
- 525: TLS handshake with the origin failed
- 526: origin certificate invalid or expired

Fallback if Let's Encrypt refuses to issue: a Cloudflare Origin CA certificate (see RESEARCH alternatives). That needs a decision from the owner.

## Cloudflare IP ranges (manual, D-06)

```bash
/srv/birja/deploy/cloudflare-ips.sh
```

This regenerates the nginx real-IP snippet and reloads nginx. There is no cron. The script warns if ufw lacks a Cloudflare range. Changing ufw is the owner's manual decision; ufw is never automated.

## Logs and checks

```bash
docker compose -f /srv/birja/docker-compose.prod.yml --env-file /etc/birja/prod.env logs --tail 100 backend
/srv/birja/deploy/smoke-prod.sh            # on the host
/srv/birja/deploy/smoke-prod.sh --public   # through Cloudflare
```

Never run `compose config` without `-q`, never read container env with `docker inspect`, and never paste logs that contain addresses into public places.

## Prices scheduler

One container (`scheduler`) polls Kraken every 60 s and writes the latest mid
price per active coin. If it stops, prices age and the UI shows them as Stale
(after 300 s). Never scale it; `deploy.sh` starts exactly one, after migrations.

```bash
docker compose -p birja-prod logs --tail 100 scheduler
docker compose -p birja-prod ps scheduler
```

All prices stale together:

- Kraken rejects the batch (look for "Unknown asset pair"): one delisted pair
  freezes the whole batch. Fix with a new migration that sets `is_active = false`
  for that coin, never a manual DB edit.
- No egress to Kraken. Check (the image has no curl; prints 200 when it works):
  `docker compose -p birja-prod exec scheduler python -c "import urllib.request; print(urllib.request.urlopen('https://api.kraken.com/0/public/Time', timeout=10).status)"`

`smoke-prod.sh` checks: exactly one healthy scheduler with ENV=prod and
PRICE_SOURCE=kraken, every active coin priced within 300 s, no codes/keys in its
logs, and `/api/v1/prices` returns 401 when signed out.

Rollback to v0.1.x removes the scheduler (that release has no prices page).

## Phase 6 retained operations and authority

These are setup/recovery instructions for the later explicitly approved host
operation. Local synthetic rehearsals do not establish live backups, enable
timers, authorize a deployment, or satisfy DEPL-01/02. Do not run a destructive
restore against production. The accepted recovery target is at most 26 hours
of data loss and a measured restore within 4 hours; the owner checks daily.

The deployment installer is `deploy/deploy-entrypoint.sh --install
--approved-operation install-retained-deploy --tested-source <exact-tested-SHA>`.
It needs a clean, reviewed exact source and separate live approval. It retains
helpers under `/var/lib/birja/ops/current/deploy/` and installs
`/usr/local/sbin/birja-deploy`. `/srv/birja/deploy/deploy.sh` becomes the sole
managed launcher exception: its exact validated bytes may differ from Git's
tracked file across old/new release checkouts. Managed sparse checkout excludes
the remaining deploy tree. Never broaden the dirty-check exception or overwrite
this launcher from an old checkout. Use retained helpers, including smoke,
instead of `/srv/birja/deploy/` paths after installation. The independent
recovery artifact lives under `/var/lib/birja/recovery/current/`; installing a
deployment bundle does not replace or refresh it.

After a successful deploy/rollback, synchronize backup JSON `release` to the
actual deployed full commit before the next backup. Recreate completed backup
and exact full-restore evidence after source/config/security/custody changes.
The strict prechange gate binds the prior source, configuration, tools and
recovery bundle; never edit evidence to make a candidate deployment pass.

## B2 free policy and preflight setup

Destination is exactly `s3:https://s3.eu-central-003.backblazeb2.com/Birja-backup/prod`.
Keep the bucket private, Object Lock off, with one whole-bucket lifecycle rule:
`fileNamePrefix=""`, `daysFromHidingToDeleting=1`, uploading-to-hiding and
unfinished-cancellation unset/null. This preserves current referenced restic
objects. Hidden versions still consume space during cleanup lag. Keep this
dedicated repository free of foreign snapshots. No payment/paid usage is
authorized. Console caps are not a universal zero-bill guarantee: changes can
take 10 minutes, and Class D transactions cannot be capped. The owner verifies
all available spend caps at $0 in the console, checks account usage/caps daily,
and stops the timer if the controls or available free allowances change.

`/etc/birja/backup.env` is mode 0600 root-owned **JSON**, never shell input or
systemd EnvironmentFile. Use the exact validated CONFIG_KEYS in
`backup-snapshot.py`; set freshness to 93600, timeout at most 3600, resource
ceilings measured in the later real-data rehearsal, and approved host identity.
Password and bucket-scoped S3 key values live only in referenced root-only
files. The automatic preflight updates its `quota` atomically under the same
operation lock immediately before backup; never hand-edit measurements to
bypass rejection. It counts actual visible/hidden versions, unfinished upload
parts and other account storage, includes old/new/repack/wire overhead reserves,
and refuses unknown, excessive, stale or insufficient inventory before upload
or deletion. Inventory errors publish a failed latest attempt and preserve the
last completed recovery point. The native HTTPS API has no redirects/proxies,
128-call/120-second inventory ceilings, 2 MB responses and bounded pagination.

Create `/etc/birja/backup-controls.json` as root mode 0600 after verifying setup.
It has exactly these fields (supply actual measured/setup values privately):

- `format`: 1; `verified_at`: actual console verification epoch, at least 600
  seconds old before execution, renewed within 31 days.
- `console_zero_caps`, `daily_owner_checks`, `exclusive_account_writes`: true
  only after owner confirmation. Other account writers must not run during
  backup; all-account inventory is measured but cannot prevent concurrent use.
- `inventory_key_id_file`, `inventory_key_file`: root-only paths under
  `/etc/birja` for an account-wide **read-only** inventory application key,
  with `listBuckets`, `listFiles`, `readBucketRetentions`, no bucket/prefix
  restrictions and no file/bucket/key write/delete capabilities.
- `local_request_budget`: 1000..10000; `local_download_budget_bytes`: at least
  max_stage_bytes and at most 4 GB. Size these conservatively with the owner's
  current free-egress knowledge before setup/restore; they are local work
  ceilings, **not** automatically measured provider remaining allowances.

Native `b2_list_parts` requires `writeFiles`. Only when unfinished Birja
`prod/` uploads exist does preflight reuse the existing Birja bucket-scoped
writer for this read operation; its auth response must match the same account,
endpoint, bucket and allowed prefix. It never calls a provider mutation API.
Unfinished uploads elsewhere fail closed because the read-only inventory key
cannot fully measure their parts. Owner resolves those separately; never grant
account-wide writes to make this check pass. Keys cannot configure billing
caps. Include controls and required credential/password/CA configuration among
the explicit minimal encrypted `recovery_files`; retain independent custody.

The preflight stores historical compatibility fields `request_remaining` and
`download_remaining_bytes` as these local budgets. Their names do not mean
remaining B2 account allowance. Restic uses two connections, bounded retries,
1 MiB/s directional rate limits and a whole-job timeout. Exact HTTP request
totals/wire bytes are not measured by subprocess counts or packed payload size.
The conservative storage reserve includes twice the rate-times-timeout plus
staging/repack reserve without assumed dedup savings. If headroom is inadequate,
reduce measured work, wait for provider version cleanup or stop; never delete
the only completed backup first or silently authorize paid capacity.

Official interfaces checked 2026-11-06:
[authorization](https://www.backblaze.com/apidocs/b2-authorize-account),
[buckets](https://www.backblaze.com/apidocs/b2-list-buckets),
[versions](https://www.backblaze.com/apidocs/b2-list-file-versions),
[unfinished uploads](https://www.backblaze.com/apidocs/b2-list-unfinished-large-files),
[parts](https://www.backblaze.com/apidocs/b2-list-parts),
[lifecycle](https://www.backblaze.com/docs/cloud-storage-lifecycle-rules),
[caps](https://www.backblaze.com/docs/cloud-storage-data-caps-and-alerts).

## Install and operate the nightly schedule (later approved setup)

Build with `bash deploy/recovery-bundle.sh package --output
/tmp/birja-backup-test-<private-directory>/recovery.tar --include-units`.
Carry its independently recorded SHA256 and reviewed verifier off-server.
The exact mandatory inventory includes quota helper, both units, signed restic
provenance, image identity and SHA256SUMS. Verify with `bundle verify --archive
<archive> --sha <SHA256> --require-profile deploy-recovery-v2` before install;
then `bundle install` with the same exact arguments after host approval.
Do not execute archive scripts to verify themselves. Review the trusted
verifier against the recorded source before use.

The installer creates `/usr/local/sbin/birja-backup`, `birja-backup-status`,
`birja-restore-check`. The backup launcher invokes retained quota preflight
then locked backup; it works while the application checkout is v0.3.1 or
absent. It never depends on the deployment bundle. Prepare private state
`/var/lib/birja/backup`, protected JSON/credential files and local tool paths
before enabling. Install the verified unit files mode 0644 in
`/etc/systemd/system/`, run `systemd-analyze verify` against them, then
`systemctl daemon-reload` and `systemctl enable --now birja-backup.timer`.
These are later host actions, not actions performed by local tests.

Schedule: 03:00 UTC daily, up to 15 minutes randomized delay, persistent missed
trigger catch-up. `Type=oneshot` has no RemainAfterExit. Filesystem write access
is limited to backup config/state/lock; Docker socket and network access are
required. Docker still represents host authority; unit hardening is not an
isolation boundary against Docker. MemoryMax=768M/CPUQuota=200%, job timeout
65 minutes, private umask, low I/O priority; validate suitability on the host.

For verification use `systemctl list-timers --all birja-backup.timer` and
`systemctl show birja-backup.timer -p LastTriggerUSec -p NextElapseUSecRealtime`;
then `systemctl show birja-backup.service -p Result -p ExecMainStatus
-p ExecMainStartTimestamp` and `/usr/local/sbin/birja-backup-status`.
Preserve original failed Result/ExecMainStatus before any manual retry.
`systemctl start birja-backup.service` tests a manual run; it cannot count as
actual scheduled-trigger evidence. Match timer LastTrigger, service invocation
and remote completed snapshot for acceptance. Exit failure/missing/stale
status is an escalation to the owner the same day; do not reset failure or
claim an older success satisfies a failed latest attempt. Disable future
runs with `systemctl disable --now birja-backup.timer`; this does not cancel
an already-running service. Diagnose before deciding whether to stop that job.
No notification service or messages to others are configured.

Latest-only rotation is already owner-selected: upload a new exact snapshot,
verify its files/private manifest/structural integrity, then forget only
enumerated prior Birja IDs and prune with zero data repacking, under the shared
lock. Failures preserve the old point until new verification. Routine structural
checks are not full restore proof. For separately approved manual maintenance,
first inspect `restic forget --dry-run <exact-prior-IDs>` with the same protected
credential environment and exact repository; never wildcard or use an unscoped
retention rule. Only after exact-new verification, scope review and authority
run `forget <exact-prior-IDs>`, `prune --max-repack-size 0` and `check`, under
the operation lock. Do not run these maintenance commands in parallel with
backup/deploy/restore, and do not run them merely to make space for replacement.

## Independent recovery and secure rollback

Retrieve the encrypted exact snapshot ID with independent storage access and
the backup password from the owner's off-server password manager. Recover the
tested recovery artifact/verifier and its separately recorded SHA first, verify
the complete immutable inventory/provenance, install on an approved recovery
host, and recreate protected JSON/credentials from independent custody.
Do not paste configuration, rows, tokens, private manifests or content hashes
into chat/logs. The recovery password must not exist only on the failed VDS.

Run `/usr/local/sbin/birja-restore-check --snapshot <exact-64-hex-ID>
--approved-clone` for the fixed isolated `birja-restore-check` target. Consult
the actual guarded CLI if it rejects an option; do not add an arbitrary DB URL
or use `latest`. It downloads that exact snapshot, checks archive SHA and full
private canonical manifest, restores into isolated PostgreSQL 18 tmpfs with no
host ports, verifies all rows/money/schema/FKs/indexes/sequences privately, and
tears down the clone before publishing completed evidence. Historical auth
sessions stay inside the clone and are never served to users. Record only
sanitized counts/booleans/snapshot ID/timing; private evidence stays root-only.
The real-data clone must be explicitly approved; synthetic tests cannot grant
that authority. Re-provision DB app/migrator passwords, CA/server key material
and required grants/mounts using the reviewed retained role/TLS procedures;
an application DB dump alone does not recreate cluster roles or independent
credential custody. Never use a bootstrap superuser for app/scheduler runtime.

For current/old release rollback use `/usr/local/sbin/birja-deploy --rollback`
with exact fresh prechange recovery evidence. The retained orchestrator keeps
the role/TLS overlay and separate migrator even for actual v0.3.1. Never switch
back to the old release's unchecked deployment script or downgrade 0008.
If concurrent index migration 0008 stops with an invalid index, stop rollout,
preserve failure and completed backup, inspect the exact invalid concurrent
index through approved maintenance, and follow its reviewed recovery procedure
before retry. Do not automatically downgrade or drop arbitrary objects; a
schema-changing repair needs a reviewed migration and scoped approval.

For this specific interrupted 0008, have the approved migrator inspect
`pg_index.indisvalid`, `pg_index.indisready`, `pg_get_indexdef(indexrelid)` and
the current `alembic_version` for
`to_regclass('public.ix_trades_user_created_id')`. The expected index is
nonunique on `public.trades (user_id, created_at, id)` and the source revision
is 0007 until 0008 completes. If and only if that exact invalid partial index
is confirmed, retain the private inspection and request scoped maintenance
authority for standalone `DROP INDEX CONCURRENTLY public.ix_trades_user_created_id`.
Run it outside a transaction with the migrator, then retry the unchanged
reviewed `alembic upgrade head` through the retained migration path. Verify
revision 0008 and both index flags true before starting candidate services.
A valid index, different definition/revision, missing ownership, or unrelated
object stops this recipe for review; never use CASCADE, automatic downgrade,
an app superuser, or a wildcard drop.

Certificate dates above are recorded history, not fresh expiry evidence.
Owner checks actual origin/DB certificate expiry daily alongside backup status,
renews before the recorded deadline, and repeats trusted TLS verification.
Origin renewal stays the manual DNS procedure above (no Cloudflare token).
DB renewal uses the retained provision helper and documented least-privilege
mount/restart sequence only after approval; replace CA/recovery custody and
perform new recovery evidence when identities/configuration change.

## Trading (release 0.3)

What changes in prod:

- Two migrations run on backend start through the normal deploy: 0006 (tables `holdings` and `trades`) and 0007 (`ck_accounts_cash_cents`, a CHECK that cash has at most two decimals; it refuses to apply if any account already has sub-cent cash).
- No new services, ports or env vars. Trade settings use the code defaults (spread 0.25%, fee 0.25%, minimum fee $0.01, minimum order $1.00; D-01/D-04/D-06) and can be overridden only through prod.env if ever needed.

Before deploying, run the read-only compliance count. It must print 0:

```bash
docker exec "$(docker ps -q --filter label=com.docker.compose.project=birja-prod --filter label=com.docker.compose.service=postgres)" sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tA -c "select count(*) from accounts where cash <> round(cash, 2)"'
```

Rollback: `deploy.sh --rollback` to 0.2.x leaves the new tables and the CHECK in place (migrations are not undone, see Rollback). 0.2.x code never writes cash, so it runs unchanged. Trades made on 0.3 stay in the database.

Checks: `smoke-prod.sh` (both modes) now asserts the trade endpoints refuse signed-out callers: `GET /api/v1/holdings/BTC` is 401 and `POST /api/v1/trades/quote` is 401 or 403. A 404 there means the release is not deployed. To see activity without PII, count only (same `docker exec` as above):

```bash
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tA -c "select count(*), max(created_at) from trades"
```

Never print emails or balances per user.

## History index (migration 0008)

0008 adds only `public.ix_trades_user_created_id`, a non-unique B-tree on
`trades (user_id, created_at, id)`, for the existing user-scoped history seek.
Upgrade and downgrade use `CONCURRENTLY` outside transactions; Alembic uses
one transaction per migration online and offline. Earlier revisions can
therefore remain committed if a later revision fails. No data is rewritten.
Normal application rollback leaves the index in place; an explicitly approved
schema downgrade to 0007 removes only this index and preserves fills.

A failed concurrent build can leave an invalid named index even while the
Alembic revision remains 0007. Before retrying, inspect revision state and
only the named index, using the deployment's approved database connection:

```sql
SELECT version_num FROM alembic_version;
SELECT i.indisvalid, i.indisready, pg_get_indexdef(i.indexrelid)
FROM pg_index i
WHERE i.indexrelid = to_regclass('public.ix_trades_user_created_id');
```

The successful definition must be exactly a non-unique B-tree on
`public.trades (user_id, created_at, id)`, with both flags true. If the named
index exists but is invalid, first establish that no build is still running
(inspect `pg_stat_progress_create_index`), review the failure and definition,
and obtain approval for recovery. Only the failed new index may be removed:

```sql
DROP INDEX CONCURRENTLY public.ix_trades_user_created_id;
```

Run that statement outside a transaction, then rerun the normal Alembic
upgrade to head and inspect both validity flags and the definition again.
If the index is valid but revision state is behind, or its definition differs,
stop for review before modifying it. Never silently stamp head, use
`IF NOT EXISTS` to hide an invalid/mismatched index, drop another index, or
rewrite trades to recover. These instructions authorize no production action.

## Undo (every host change in phase 02.1)

- DNS record: delete the birja record in the Cloudflare dashboard (DNS, Records).
- nginx site: `rm /etc/nginx/sites-enabled/birja.nist.one /etc/nginx/sites-available/birja.nist.one /etc/nginx/snippets/birja-*.conf /etc/nginx/conf.d/birja-zones.conf /etc/nginx/conf.d/birja-default-tls.conf && nginx -t && systemctl reload nginx`. `systemctl disable --now nginx` also stops serving nist.one, which was brought online by this phase.
- Certificate: `rm -r /etc/nginx/certs/nist.one`.
- Prod env: `rm -r /etc/birja` (only while the stack is down; the Postgres volume keeps the old password).
- Checkout, releases and history: `rm -rf /srv/birja /var/www/birja /var/lib/birja`.
- Prod stack: `docker compose -p birja-prod down` keeps the data; `down -v` destroys it.
- TXT challenge records: delete the `_acme-challenge` records in the dashboard after issuance.

## Out of scope here

Backups (Phase 6), CI auto-deploy (deferred in D-02) and monitoring.
