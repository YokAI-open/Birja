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

1. The owner creates `/root/.secrets/cloudflare.env` with the variables `CF_Token=` and `CF_Zone_ID=`. Directory mode 700, file mode 600. The token needs Zone:DNS:Edit and Zone:Zone:Read on nist.one only.
2. `deploy/renew-cert.sh` issues the certificate.
3. `deploy/install-nginx.sh` installs the nginx site.
4. `deploy/init-prod-env.sh` creates `/etc/birja/prod.env`. Then the owner adds `RESEND_API_KEY`.
5. `git clone https://github.com/YokAI-open/Birja.git /srv/birja`
6. `/srv/birja/deploy/deploy.sh`
7. `/srv/birja/deploy/smoke-prod.sh`
8. `/srv/birja/deploy/cloudflare-dns.sh ensure`
9. `/srv/birja/deploy/smoke-prod.sh --public`

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

This redeploys the previous entry of `deploys.log`. Migrations are not undone. There are no backups until Phase 6.

## Certificate renewal (manual, D-07)

Nothing renews automatically. The cert was removed from acme.sh's renewal list and saved Cloudflare credentials were stripped. The existing acme.sh cron line was left unchanged (D-06); it has nothing to renew.

Next certificate expiry: <filled in by 02.1-05>
Renew by (30 days before): <filled in by 02.1-05>

Procedure:

1. Check that `/root/.secrets/cloudflare.env` exists and the token is not revoked. Recreate it if needed.
2. `cd /srv/birja && deploy/renew-cert.sh`
3. `deploy/smoke-prod.sh`
4. Update the two date lines above through a normal feature branch.

Cloudflare error cheat sheet:

- 521: origin refused the connection (nginx down or ufw blocking)
- 525: TLS handshake with the origin failed
- 526: origin certificate invalid or expired

Fallback if ZeroSSL refuses to issue: a Cloudflare Origin CA certificate (see RESEARCH alternatives). That needs a decision from the owner.

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

- DNS record: delete it in the Cloudflare dashboard (DNS, Records, birja), or see the header of `deploy/cloudflare-dns.sh`.
- nginx site: `rm /etc/nginx/sites-enabled/birja.nist.one /etc/nginx/sites-available/birja.nist.one /etc/nginx/snippets/birja-*.conf /etc/nginx/conf.d/birja-zones.conf && nginx -t && systemctl reload nginx`. `systemctl disable --now nginx` also stops serving nist.one, which was brought online by this phase.
- Certificate: `rm -r /etc/nginx/certs/nist.one`. The acme.sh conf rename is reversible by moving `*.nist.one.conf.removed` back to `.conf` in the cert dir (not wanted per D-07).
- Prod env: `rm -r /etc/birja` (only while the stack is down; the Postgres volume keeps the old password).
- Checkout, releases and history: `rm -rf /srv/birja /var/www/birja /var/lib/birja`.
- Prod stack: `docker compose -p birja-prod down` keeps the data; `down -v` destroys it.
- Token: delete `/root/.secrets/cloudflare.env` and revoke the token in Cloudflare (My Profile, API Tokens).

## Out of scope here

Backups (Phase 6), CI auto-deploy (deferred in D-02) and monitoring.
