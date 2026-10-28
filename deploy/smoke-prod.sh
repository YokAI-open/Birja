#!/usr/bin/env bash
# Automated success-criteria checks for https://birja.nist.one.
#   smoke-prod.sh           checks on the host, through the origin (--resolve to 127.0.0.1)
#   smoke-prod.sh --public  user-facing checks through Cloudflare (no host access needed)
#   smoke-prod.sh --help
# Read-only, except one synthetic failed verify-code request (wrong code, example.com
# account). Prints counts, never addresses, secrets or log lines.
# Deliberately no `set -e`: every check runs and failures are counted.
set -uo pipefail

H=birja.nist.one
ORIGIN_IP=151.243.171.52
APP_DIR=/srv/birja
COMPOSE_FILE=$APP_DIR/docker-compose.prod.yml
ENV_FILE=/etc/birja/prod.env
CERT=/etc/nginx/certs/nist.one/fullchain.pem
REALIP=/etc/nginx/snippets/birja-cloudflare-realip.conf
DEPLOY_LOG=/var/lib/birja/deploys.log
MODE=local

usage() {
  cat <<USAGE
Usage: smoke-prod.sh [--public]
  (no args)  host checks via origin: redirect, TLS, build, headers, docs off,
             ENV=prod, placeholders refused, exposure, client IP, log hygiene,
             price scheduler (one, healthy, kraken), price freshness, prices 401
  --public   user-facing checks through Cloudflare (incl. prices 401 signed out)
  -h, --help this text
Exit 0 only if every check passed.
USAGE
}

case "${1:-}" in
  "") ;;
  --public) MODE=public ;;
  -h|--help) usage; exit 0 ;;
  *) usage >&2; exit 2 ;;
esac

TOTAL=0
FAILED=0
pass() { TOTAL=$((TOTAL + 1)); echo "PASS  $1"; }
fail() { TOTAL=$((TOTAL + 1)); FAILED=$((FAILED + 1)); echo "FAIL  $1"; }
warn() { echo "WARN  $1"; }

if [ "$MODE" = local ]; then
  RESOLVE=(--resolve "$H:443:127.0.0.1" --resolve "$H:80:127.0.0.1")
else
  RESOLVE=()
fi
# One query: active coin count, how many have a price, age in s of the oldest
# price (-1 if none). Run inside the postgres container; prints numbers only.
PRICES_SQL="SELECT count(*), count(p.coin_id), coalesce(floor(extract(epoch FROM now() - min(p.as_of)))::int, -1) FROM coins c LEFT JOIN prices p ON p.coin_id = c.id WHERE c.is_active"

curlq() { curl -sS --max-time 15 "${RESOLVE[@]}" "$@"; }

CT_DIR=$(mktemp -d)
trap 'rm -rf "$CT_DIR"' EXIT

container() { # container <service>
  docker ps -q --filter label=com.docker.compose.project=birja-prod \
    --filter "label=com.docker.compose.service=$1" | head -n1
}

hdr_lower() { tr '[:upper:]' '[:lower:]'; }

check_headers() { # check_headers <label> <url>
  local label=$1 url=$2 h missing=""
  h=$(curlq -o /dev/null -D - "$url" | tr -d '\r' | hdr_lower)
  for want in strict-transport-security content-security-policy x-content-type-options referrer-policy; do
    printf '%s\n' "$h" | grep -q "^$want:" || missing="$missing $want"
  done
  printf '%s\n' "$h" | grep -q "^content-security-policy:.*frame-ancestors 'none'" || missing="$missing csp-frame-ancestors"
  printf '%s\n' "$h" | grep -q '^x-frame-options: *deny' || missing="$missing x-frame-options"
  if printf '%s\n' "$h" | grep -E '^server:' | grep -qE '[0-9]\.[0-9]'; then
    missing="$missing server-version"
  fi
  if [ -z "$missing" ]; then pass "headers on $label"; else fail "headers on $label: missing$missing"; fi
}

first_asset() { # prints the first /assets/*.js path of the index page
  curlq "https://$H/" | grep -oE '/assets/[A-Za-z0-9._-]+\.js' | head -n1
}

health_ok() {
  curlq "https://$H/api/v1/health" \
    | python3 -I -c 'import json,sys; sys.exit(0 if json.load(sys.stdin).get("status")=="ok" else 1)' 2>/dev/null
}

# API docs must not be reachable through nginx. Only /api/ reaches the app,
# so /docs etc. must come back as the SPA's index.html (not Swagger/ReDoc/
# schema JSON), and the /api/ variants must not return 200.
docs_not_exposed() {
  local p body code bad=""
  for p in /docs /redoc /openapi.json; do
    body=$(curlq "https://$H$p")
    if ! grep -q 'id="root"' <<<"$body" || grep -qiE 'swagger-ui|redoc|"openapi"' <<<"$body"; then
      bad="$bad $p"
    fi
  done
  for p in /api/docs /api/redoc /api/openapi.json /api/v1/docs /api/v1/redoc /api/v1/openapi.json; do
    code=$(curlq -o /dev/null -w '%{http_code}' "https://$H$p")
    [ "$code" = 404 ] || bad="$bad $p($code)"
  done
  if [ -z "$bad" ]; then pass "API docs/schema not exposed via nginx"; else fail "API docs/schema check failed:$bad"; fi
}

# D-02: prices need a session
prices_requires_auth() {
  local code
  code=$(curlq -o /dev/null -w '%{http_code}' "https://$H/api/v1/prices")
  if [ "$code" = 401 ]; then pass "GET /api/v1/prices is 401 when signed out"; else fail "GET /api/v1/prices signed out: got $code (want 401)"; fi
}

# ---------------------------------------------------------------- public mode
if [ "$MODE" = public ]; then
  A=$(curl -sS --max-time 15 -H 'accept: application/dns-json' \
    "https://1.1.1.1/dns-query?name=$H&type=A" \
    | python3 -I -c 'import json,sys
d=json.load(sys.stdin)
print(" ".join(a["data"] for a in d.get("Answer",[]) if a.get("type")==1))' 2>/dev/null)
  if [ -z "$A" ]; then
    fail "DNS: no A answer for $H"
  elif printf '%s\n' "$A" | tr ' ' '\n' | grep -qx "$ORIGIN_IP"; then
    fail "DNS: A record exposes the origin IP (not proxied)"
  else
    pass "DNS: proxied (origin IP not in answer)"
  fi

  CODE=$(curl -sS --max-time 15 -o /dev/null -D "$CT_DIR/h" -w '%{http_code}' "https://$H/")
  if [ "$CODE" = 200 ] && grep -qi '^cf-ray:' "$CT_DIR/h"; then
    pass "https / returns 200 via Cloudflare with valid chain"
  else
    fail "https /: status $CODE or no cf-ray header"
  fi

  CODE=$(curl -sS --max-time 15 -o /dev/null -w '%{http_code}' "http://$H/")
  if [ "$CODE" = 301 ] || [ "$CODE" = 308 ]; then pass "http redirects ($CODE)"; else fail "http redirect: got $CODE"; fi

  check_headers "/" "https://$H/"
  if health_ok; then pass "health ok"; else fail "health not ok"; fi

  docs_not_exposed
  prices_requires_auth

  if [ "$FAILED" -eq 0 ]; then echo "SMOKE OK ($TOTAL checks)"; exit 0; fi
  echo "SMOKE FAILED ($FAILED of $TOTAL)"; exit 1
fi

# ----------------------------------------------------------------- local mode
[ "$(id -u)" -eq 0 ] || { echo "must run as root (or use --public)" >&2; exit 1; }

# 1. SC1 redirect
LOC=$(curlq -o /dev/null -D - "http://$H/x?y=1" | tr -d '\r' | awk 'tolower($1)=="location:"{print $2}')
CODE=$(curlq -o /dev/null -w '%{http_code}' "http://$H/x?y=1")
if [ "$CODE" = 301 ] && [ "$LOC" = "https://$H/x?y=1" ]; then pass "http -> https 301 keeps path and query"; else fail "redirect: status $CODE"; fi

# 2. SC1 TLS
TLS=$(openssl s_client -connect 127.0.0.1:443 -servername "$H" -verify_return_error -verify_hostname "$H" </dev/null 2>&1)
if printf '%s\n' "$TLS" | grep -q 'Verify return code: 0'; then pass "TLS chain verifies"; else fail "TLS chain does not verify"; fi
if openssl x509 -in "$CERT" -noout -ext subjectAltName 2>/dev/null | grep -q '\*\.nist\.one'; then
  pass "cert SAN contains *.nist.one"
else
  fail "cert SAN lacks *.nist.one"
fi
tls_ok() { openssl s_client -connect 127.0.0.1:443 -servername "$1" </dev/null >/dev/null 2>&1; }
if tls_ok evil.example; then
  fail "unknown SNI completes the TLS handshake (catch-all 443 missing)"
else
  pass "unknown SNI is rejected at the TLS handshake"
fi
for sni in "$H" nist.one; do
  if tls_ok "$sni"; then pass "TLS handshake for $sni"; else fail "TLS handshake for $sni failed"; fi
done
if openssl x509 -in "$CERT" -noout -checkend $((30 * 86400)) >/dev/null; then
  pass "cert valid for more than 30 days"
elif openssl x509 -in "$CERT" -noout -checkend 0 >/dev/null; then
  warn "cert expires in under 30 days: renew (RUNBOOK, D-07)"
else
  fail "cert is expired"
fi

# 3. SC1 prod build
BODY=$(curlq -D "$CT_DIR/h" "https://$H/")
if grep -qi '^content-type: *text/html' "$CT_DIR/h" && printf '%s' "$BODY" | grep -q 'id="root"'; then
  pass "/ serves the built index.html"
else
  fail "/ is not the built index.html"
fi
ASSET=$(first_asset)
if [ -z "$ASSET" ]; then
  fail "no /assets/*.js referenced from index.html"
else
  curlq -o /dev/null -D "$CT_DIR/a" -H 'Accept-Encoding: gzip' "https://$H$ASSET"
  A_CODE=$(head -n1 "$CT_DIR/a" | awk '{print $2}')
  if [ "$A_CODE" = 200 ] && grep -qi '^cache-control:.*immutable' "$CT_DIR/a" \
     && grep -qi '^content-encoding: *gzip' "$CT_DIR/a"; then
    pass "asset is 200, immutable, gzip"
  else
    fail "asset: status $A_CODE or missing immutable/gzip"
  fi
fi
CODE=$(curlq -o /dev/null -w '%{http_code}' "https://$H/assets/does-not-exist.js")
if [ "$CODE" = 404 ]; then pass "missing asset is 404"; else fail "missing asset returned $CODE"; fi

# 4. SC1 headers
check_headers "/" "https://$H/"
if [ -n "$ASSET" ]; then check_headers "asset" "https://$H$ASSET"; else fail "headers on asset: no asset"; fi
check_headers "/api/v1/health" "https://$H/api/v1/health"

# 5. SC2 health
if health_ok; then pass "health status ok"; else fail "health status not ok"; fi

# 6. SC2 docs off
for p in /docs /redoc /openapi.json; do
  CODE=$(curl -sS --max-time 15 -o /dev/null -w '%{http_code}' "http://127.0.0.1:18000$p")
  if [ "$CODE" = 404 ]; then pass "$p is 404 on the app"; else fail "$p returned $CODE"; fi
done

docs_not_exposed

# 7. SC2 ENV
BACKEND=$(container backend)
REDIS=$(container redis)
POSTGRES=$(container postgres)
if [ -z "$BACKEND" ]; then
  fail "backend container not running"
elif [ "$(docker exec "$BACKEND" printenv ENV 2>/dev/null)" = prod ]; then
  pass "ENV=prod in backend"
else
  fail "ENV is not prod in backend"
fi

# 8. SC2 placeholders refused. The positive control proves the command itself
# runs (image, env file, compose, imports); the refusal must be the specific
# validation error, not any failure. Output is matched, never printed.
settings_run() {
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm --no-deps "$@" backend \
    python -c "from app.core.config import Settings; Settings()" 2>&1
}
if ! settings_run >/dev/null; then
  fail "placeholder check: Settings() fails even with the real env (compose/docker/config error)"
else
  OUT=$(settings_run -e OTP_HMAC_SECRET=change-me-placeholder-0123456789abcdefghij)
  RC=$?
  if [ "$RC" -ne 0 ] && grep -q 'ValidationError' <<<"$OUT" \
     && grep -q 'otp_hmac_secret is still a placeholder' <<<"$OUT"; then
    pass "placeholder secret refused"
  elif [ "$RC" -eq 0 ]; then
    fail "placeholder secret was accepted"
  else
    fail "placeholder check failed for another reason (exit $RC)"
  fi
  unset OUT
fi

# 9. SC2 exposure
BAD=""
WARNP=""
while read -r addr; do
  port=${addr##*:}
  host=${addr%:*}
  case "$host" in 127.*|"[::1]") continue ;; esac
  case "$port" in
    22|80|443) ;;
    4200) WARNP="$WARNP $port" ;;
    *) BAD="$BAD $port" ;;
  esac
done < <(ss -ltnH | awk '{print $4}')
if [ -z "$BAD" ]; then pass "only 22/80/443 public"; else fail "unexpected public ports:$BAD"; fi
[ -n "$WARNP" ] && warn "pre-existing public port(s):$WARNP (ufw-firewalled)"

PORTS=$(docker ps --filter label=com.docker.compose.project=birja-prod --format '{{.Names}} {{.Ports}}')
PUB=$(printf '%s\n' "$PORTS" | grep -E '[0-9]->' || true)
if [ "$(printf '%s\n' "$PUB" | grep -c .)" = 1 ] && printf '%s\n' "$PUB" | grep -q 'backend.*127\.0\.0\.1:18000->8000/tcp' \
   && ! printf '%s\n' "$PUB" | grep -q '0\.0\.0\.0\|\[::\]'; then
  pass "only backend publishes 127.0.0.1:18000->8000"
else
  fail "published ports differ from expected"
fi
for c in "$POSTGRES" "$REDIS"; do
  [ -n "$c" ] || { fail "postgres/redis container missing"; continue; }
  NETS=$(docker inspect -f '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}' "$c")
  if [ "$NETS" = "birja-prod_data " ]; then pass "data container only on birja-prod_data"; else fail "data container on unexpected networks"; fi
done

# 10. SC2 client IP
rcli() { docker exec "$REDIS" sh -c 'REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli --no-auth-warning "$@"' _ "$@"; }
JAR="$CT_DIR/jar"
curlq -c "$JAR" -o /dev/null "https://$H/api/v1/auth/csrf"
CSRF=$(awk '$6=="bj_csrf"{print $7}' "$JAR")
curlq -b "$JAR" -o /dev/null -X POST "https://$H/api/v1/auth/verify-code" \
  -H 'Content-Type: application/json' -H "X-CSRF-Token: $CSRF" \
  -H 'CF-Connecting-IP: 1.2.3.4' -H 'X-Forwarded-For: 1.2.3.4' \
  -d '{"email":"smoke-check@example.com","code":"000000"}'
if [ -z "$REDIS" ]; then
  fail "redis container missing"
else
  LOOP=$(rcli EXISTS sim:rl:ver:ip:127.0.0.1 | tr -d '\r')
  SPOOF=$(rcli EXISTS sim:rl:ver:ip:1.2.3.4 | tr -d '\r')
  if [ "$LOOP" = 1 ] && [ "$SPOOF" = 0 ]; then
    pass "spoofed client-IP headers ignored from non-Cloudflare peer"
  else
    fail "client-IP bucket wrong (loopback=$LOOP spoofed=$SPOOF)"
  fi
  CLASSES=$(rcli --scan --pattern 'sim:rl:*:ip:*' | tr -d '\r' \
    | python3 -I -c '
import ipaddress, re, sys
cf = []
try:
    for line in open("'"$REALIP"'"):
        m = re.match(r"\s*set_real_ip_from\s+([0-9a-fA-F:./]+);", line)
        if m:
            cf.append(ipaddress.ip_network(m.group(1), strict=False))
except OSError:
    pass
dock = ipaddress.ip_network("172.29.50.0/24")
counts = {"loopback": 0, "docker-bridge": 0, "cloudflare": 0, "other-public": 0}
for key in sys.stdin.read().split():
    raw = key.rsplit(":ip:", 1)[-1]
    try:
        addr = ipaddress.ip_interface(raw).ip
    except ValueError:
        continue
    if addr.is_loopback:
        counts["loopback"] += 1
    elif addr.version == 4 and addr in dock:
        counts["docker-bridge"] += 1
    elif any(addr.version == n.version and addr in n for n in cf):
        counts["cloudflare"] += 1
    else:
        counts["other-public"] += 1
print(counts["loopback"], counts["docker-bridge"], counts["cloudflare"], counts["other-public"])
' 2>/dev/null)
  set -- $CLASSES
  echo "INFO  rate-limit buckets: loopback=${1:-?} docker-bridge=${2:-?} cloudflare=${3:-?} other-public=${4:-?}"
  if [ "${2:-x}" = 0 ] && [ "${3:-x}" = 0 ]; then
    pass "no buckets on docker gateway or Cloudflare addresses"
  else
    fail "buckets found on docker gateway or Cloudflare addresses"
  fi
fi

# 11. Log hygiene
if [ -n "$BACKEND" ]; then
  N=$(docker logs "$BACKEND" 2>&1 | grep -cE 'DEV EMAIL|code=[0-9]{6}|re_[A-Za-z0-9_]{16,}')
  if [ "$N" = 0 ]; then pass "no codes or keys in backend logs (count 0)"; else fail "backend logs contain $N suspicious lines"; fi
fi

# 12. Prices (Phase 3)
SCHED_IDS=$(docker ps -q --filter label=com.docker.compose.project=birja-prod \
  --filter label=com.docker.compose.service=scheduler --filter status=running)
SCHED_N=$(printf '%s' "$SCHED_IDS" | grep -c .)
if [ "$SCHED_N" = 1 ]; then
  pass "exactly one scheduler running"
  SCHED=$SCHED_IDS
  HS=$(docker inspect -f '{{.State.Health.Status}}' "$SCHED" 2>/dev/null)
  if [ "$HS" = healthy ]; then pass "scheduler healthy"; else fail "scheduler health is '${HS:-unknown}'"; fi
  if [ "$(docker exec "$SCHED" printenv ENV 2>/dev/null)" = prod ] \
     && [ "$(docker exec "$SCHED" printenv PRICE_SOURCE 2>/dev/null)" = kraken ]; then
    pass "scheduler runs ENV=prod PRICE_SOURCE=kraken"
  else
    fail "scheduler ENV/PRICE_SOURCE is not prod/kraken"
  fi
  SNETS=$(docker inspect -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}' "$SCHED" | tr ' ' '\n' | grep . | sort | tr '\n' ' ')
  if [ "$SNETS" = "birja-prod_app birja-prod_data " ]; then pass "scheduler only on app+data networks"; else fail "scheduler networks: $SNETS"; fi
  SPORTS=$(docker ps --filter "id=$SCHED" --format '{{.Ports}}')
  if [ -z "$SPORTS" ]; then pass "scheduler publishes no ports"; else fail "scheduler publishes ports"; fi
  N=$(docker logs "$SCHED" 2>&1 | grep -cE 'DEV EMAIL|code=[0-9]{6}|re_[A-Za-z0-9_]{16,}')
  if [ "$N" = 0 ]; then pass "no codes or keys in scheduler logs (count 0)"; else fail "scheduler logs contain $N suspicious lines"; fi
else
  fail "scheduler count is $SCHED_N (want exactly 1)"
fi
PG=$(container postgres)
if [ -n "$PG" ]; then
  read -r ACTIVE PRICED OLDEST < <(docker exec "$PG" sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tA -F" " -c "$1"' _ "$PRICES_SQL" 2>/dev/null)
  if [[ "${ACTIVE:-}" =~ ^[0-9]+$ && "${PRICED:-}" =~ ^[0-9]+$ && "${OLDEST:-}" =~ ^-?[0-9]+$ ]] \
     && [ "$ACTIVE" -ge 10 ] && [ "$PRICED" = "$ACTIVE" ] && [ "$OLDEST" -ge 0 ] && [ "$OLDEST" -le 300 ]; then
    pass "all $ACTIVE active coins priced, oldest ${OLDEST}s"
  else
    fail "price freshness: active=${ACTIVE:-?} priced=${PRICED:-?} oldest=${OLDEST:-?}s (need >=10 active, all priced, <=300s)"
  fi
else
  fail "postgres container not found for price check"
fi
prices_requires_auth

# 13. Deploy record
if [ -f "$DEPLOY_LOG" ]; then
  LAST=$(tail -n1 "$DEPLOY_LOG" | awk '{print $2}')
  HEAD_SHA=$(git -C "$APP_DIR" rev-parse HEAD 2>/dev/null)
  if [ -n "$LAST" ] && [ "$LAST" = "$HEAD_SHA" ]; then pass "deploy log matches checkout HEAD"; else fail "deploy log SHA differs from checkout HEAD"; fi
else
  fail "deploy log missing"
fi

if [ "$FAILED" -eq 0 ]; then echo "SMOKE OK ($TOTAL checks)"; exit 0; fi
echo "SMOKE FAILED ($FAILED of $TOTAL)"
exit 1
