#!/usr/bin/env bash
# Explicit privileged operation, never an application startup hook.
# Inspect: --synthetic /tmp/birja-backup-test-*/roles.json --inspect
# Apply additionally requires --apply --approved-operation populated-role-transition.
# Production: --production (fixed /etc/birja/db-roles.json), only after the
# separately approved off-server recovery gate. No production read by tests.
set -Eeuo pipefail
umask 077
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 - "$SCRIPT_DIR" "$@" <<'PY'
import fcntl
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path


def require(ok):
    if not ok:
        raise ValueError("guard")


def private(path):
    p = Path(path)
    require(p.is_absolute() and p.resolve() == p)
    s = p.lstat()
    require(stat.S_ISREG(s.st_mode) and s.st_uid == os.geteuid() and s.st_mode & 0o077 == 0)
    return p


def main():
    source = Path(sys.argv[1])
    args = sys.argv[2:]
    require(len(args) >= 2)
    synthetic = args[0] == "--synthetic"
    if synthetic:
        p = private(args[1])
        require(re.fullmatch(r"/tmp/birja-backup-test-[A-Za-z0-9_-]+/roles\.json", str(p)))
        rest = args[2:]
        root = p.parent
        require(root.stat().st_mode & 0o077 == 0)
    else:
        require(args[0] == "--production" and os.geteuid() == 0)
        p = private("/etc/birja/db-roles.json")
        rest = args[1:]
        root = Path("/etc/birja")
    apply = rest == ["--apply", "--approved-operation", "populated-role-transition"]
    require(apply or rest == ["--inspect"])
    c = json.loads(p.read_text())
    require(set(c) == {"project", "db_name", "bootstrap", "password_files"})
    require((c["project"], c["db_name"], c["bootstrap"]) ==
            (("birja-ops-test", "birja_source_test", "birja_ops_bootstrap") if synthetic else
             ("birja-prod", "birja", "birja")))
    require(set(c["password_files"]) == {"app", "scheduler", "migrator"})
    # Source/config are never sourced or evaluated. Secrets go to psql stdin,
    # constrained hex plus psql literal binding, never argv/environment/logs.
    values = {"apply": "true" if apply else "false", "bootstrap": c["bootstrap"], "db_name": c["db_name"]}
    for role, path in c["password_files"].items():
        require(Path(path).parent == root and Path(path).name == role)
        if apply:
            password = private(path).read_text().strip()
            require(re.fullmatch(r"[0-9a-f]{64}", password))
            values[role + "_password"] = password
    compose = source.parent / "docker-compose.ops-test.yml" if synthetic else Path("/srv/birja/docker-compose.prod.yml")
    require(compose.is_file() and not compose.is_symlink())
    if synthetic:
        require(hashlib.sha256(compose.read_bytes()).hexdigest() == "91af78e11963a7a8f944e1807b310193e1ea1da676b74beab2e667b5e841c7f0")
    env_file = "/dev/null" if synthetic else "/etc/birja/prod.env"
    dc = ["/usr/bin/docker", "compose", "--env-file", env_file, "-p", c["project"], "-f", str(compose)]
    lock = root / "operation.lock" if synthetic else Path("/var/lock/birja-deploy.lock")
    fd = os.open(lock, os.O_CREAT | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as held:
        require(os.fstat(held.fileno()).st_uid == os.geteuid())
        require(os.fstat(held.fileno()).st_mode & 0o077 == 0)
        fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
        prefix = "".join("\\set " + k + " '" + v + "'\n" for k, v in values.items())
        sql = prefix + (source / "db/bootstrap-roles.sql").read_text()
        result = subprocess.run(dc + ["exec", "-T", "postgres", "psql", "-XqAt", "-v", "ON_ERROR_STOP=1", "-U", c["bootstrap"], "-d", c["db_name"]],
                                input=sql.encode(), capture_output=True, timeout=150, check=False,
                                env={"PATH": "/usr/bin:/bin", "HOME": "/tmp", "LANG": "C.UTF-8"})
        require(result.returncode == 0)
    print("db_roles_preflight=true mode=" + ("apply" if apply else "inspect") + " tables=9 owners=migrator runtime=app,scheduler secrets_printed=false")


try:
    main()
except (ValueError, OSError, KeyError, TypeError, subprocess.TimeoutExpired):
    print("db_roles_failed=true diagnostics=redacted", file=sys.stderr)
    sys.exit(1)
PY
