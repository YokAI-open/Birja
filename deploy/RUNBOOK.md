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

Run as root. The script fetches the ref, builds the frontend into a new release, starts the stack, runs migrations, switches the `current` link and records the deploy in `/var/lib/birja/deploys.log`.

If it fails, it prints the failing step and the last redacted backend log lines. Fix the cause and re-run, or roll back.

Releases reach `main` only through `release-*` or `hotfix-*` PRs (git-flow in CLAUDE.md).

## Rollback

```bash
/srv/birja/deploy/deploy.sh --rollback
```

This returns to the release that was live before the current one. It prints the target SHA and release before acting. Migrations are not undone. There are no backups until Phase 6.

How the target is chosen (`/var/lib/birja/deploys.log`, one line per successful deploy or rollback, `time sha release ref`, ref `rollback` for rollbacks):

- The log is replayed as a stack of live releases. A deploy pushes its line. A rollback line pops lines until its own SHA is on top, so a release that was rolled back away from is never picked again; a second rollback goes one further back instead of re-deploying the bad release.
- Normally the target is the newest stack entry below the top with a different SHA, so repeated deploys of the same SHA are skipped (no silent no-op).
- A failed deploy is never logged. While a deploy runs, `/var/lib/birja/deploy.pending` exists; it is removed only when the deploy is recorded. If it is still there (or the checkout's HEAD differs from the top SHA), the last deploy failed, and the target is the top entry itself: the last good release.
- If there is no earlier release with a different SHA, it refuses ("nothing to roll back to").

The selection logic is tested offline by `deploy/tests/test-rollback-target.sh`.

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
