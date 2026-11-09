#!/usr/bin/env bash
# Private PostgreSQL TLS lifecycle. No service reload/restart is performed.
# --production --create|--renew requires the exact operation and custody gates.
# --synthetic /tmp/birja-backup-test-* uses the same permissions/crypto policy.
# Leaf: 365 days; CA: 3650 days; --check fails within 30 days of leaf expiry.
# Renew with the SAME independently recovered signing CA, then explicitly
# reload Postgres after verifying the new pair. Copy CA/key + DB credentials
# to the owner's off-server password manager before any production rollout.
# Never mount custody/ into a service or include it in plaintext evidence.
set -Eeuo pipefail
umask 077
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 - "$SCRIPT_DIR" "$@" <<'PY'
import argparse
import importlib.util
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path


def require(value):
    if not value:
        raise ValueError('invalid TLS operation')


def run(args):
    result = subprocess.run(['openssl', *args], capture_output=True, timeout=30,
                            env={'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8'})
    require(result.returncode == 0)
    return result.stdout


def private(path, mode, gid=0, directory=False):
    value = path.lstat()
    require((stat.S_ISDIR(value.st_mode) if directory else stat.S_ISREG(value.st_mode))
            and value.st_uid == 0 and value.st_gid == gid
            and stat.S_IMODE(value.st_mode) == mode)


def check(base, custody):
    private(base, 0o700, directory=True)
    private(custody, 0o700, directory=True)
    private(custody / 'ca.key', 0o600)
    private(base / 'ca.crt', 0o644)
    private(base / 'server', 0o750, 70, directory=True)
    private(base / 'server/server.key', 0o640, 70)
    private(base / 'server/server.crt', 0o644)
    cert = str(base / 'server/server.crt')
    require(b'DNS:postgres' in run(['x509', '-in', cert, '-noout', '-ext', 'subjectAltName']))
    run(['verify', '-CAfile', str(base / 'ca.crt'), '-verify_hostname', 'postgres',
         '-purpose', 'sslserver', cert])
    run(['x509', '-in', cert, '-noout', '-checkend', '2592000'])
    run(['x509', '-in', str(base / 'ca.crt'), '-noout', '-checkend', '31536000'])
    require(run(['x509', '-in', cert, '-pubkey', '-noout']) ==
            run(['pkey', '-in', str(base / 'server/server.key'), '-pubout']))
    require(run(['x509', '-in', str(base / 'ca.crt'), '-pubkey', '-noout']) ==
            run(['pkey', '-in', str(custody / 'ca.key'), '-pubout']))


def main():
    parser = argparse.ArgumentParser()
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument('--production', action='store_true')
    target.add_argument('--synthetic')
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--create', action='store_true')
    action.add_argument('--renew', action='store_true')
    action.add_argument('--check', action='store_true')
    parser.add_argument('--approved-operation')
    parser.add_argument('--approved-custody')
    source = Path(sys.argv[1])
    args = parser.parse_args(sys.argv[2:])
    require(os.geteuid() == 0)
    if args.production:
        require(args.check or args.approved_operation == 'production-db-tls')
        root = Path('/etc/birja')
    else:
        root = Path(args.synthetic)
        require(re.fullmatch(r'/tmp/birja-backup-test-[A-Za-z0-9_-]+', str(root)))
    require(root == root.resolve() and not root.is_symlink())
    private(root, 0o700, directory=True)
    require(args.check or args.approved_custody == 'owner-off-server-password-manager')
    lock = root / 'operation.lock' if args.synthetic else Path('/var/lock/birja-deploy.lock')
    spec = importlib.util.spec_from_file_location('backup', source / 'backup-snapshot.py')
    backup = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True
    spec.loader.exec_module(backup)
    with backup.acquire_operation_lock(lock):
        base, custody = root / 'db-tls', root / 'custody'
        if args.check:
            check(base, custody)
            print('db_tls_valid=true expires_beyond_30_days=true')
            return
        if args.create:
            require(not base.exists() and not base.is_symlink()
                    and not custody.exists() and not custody.is_symlink())
        else:
            # Renewal may run inside the warning window, but never accepts unsafe
            # permissions, changed custody, mismatching keys or an untrusted pair.
            private(base, 0o700, directory=True)
            private(custody, 0o700, directory=True)
            private(custody / 'ca.key', 0o600)
            private(base / 'ca.crt', 0o644)
            private(base / 'server', 0o750, 70, directory=True)
            private(base / 'server/server.key', 0o640, 70)
            private(base / 'server/server.crt', 0o644)
            run(['x509', '-in', str(base / 'ca.crt'), '-noout', '-checkend', '31536000'])
            require(run(['x509', '-in', str(base / 'ca.crt'), '-pubkey', '-noout']) ==
                    run(['pkey', '-in', str(custody / 'ca.key'), '-pubout']))
        stage = Path(tempfile.mkdtemp(prefix='.db-tls-', dir=root))
        try:
            if args.create:
                run(['req', '-x509', '-newkey', 'rsa:3072', '-nodes', '-days', '3650',
                     '-subj', '/CN=Birja database private CA', '-addext', 'basicConstraints=critical,CA:TRUE',
                     '-addext', 'keyUsage=critical,keyCertSign,cRLSign',
                     '-keyout', str(stage / 'ca.key'), '-out', str(stage / 'ca.crt')])
            else:
                shutil.copyfile(custody / 'ca.key', stage / 'ca.key')
                shutil.copyfile(base / 'ca.crt', stage / 'ca.crt')
            run(['req', '-new', '-newkey', 'rsa:3072', '-nodes', '-subj', '/CN=postgres',
                 '-keyout', str(stage / 'server.key'), '-out', str(stage / 'server.csr')])
            (stage / 'extensions').write_text('subjectAltName=DNS:postgres\nbasicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\n')
            run(['x509', '-req', '-in', str(stage / 'server.csr'), '-CA', str(stage / 'ca.crt'),
                 '-CAkey', str(stage / 'ca.key'), '-set_serial', '0x' + secrets.token_hex(16),
                 '-days', '365', '-extfile', str(stage / 'extensions'), '-out', str(stage / 'server.crt')])
            if args.create:
                base.mkdir(mode=0o700)
                custody.mkdir(mode=0o700)
                os.replace(stage / 'ca.key', custody / 'ca.key')
                (custody / 'ca.key').chmod(0o600)
                os.replace(stage / 'ca.crt', base / 'ca.crt')
                (base / 'ca.crt').chmod(0o644)
                (base / 'server').mkdir(mode=0o750)
                (base / 'server').chmod(0o750)
                os.chown(base / 'server', 0, 70)
            (stage / 'server.key').chmod(0o640)
            os.chown(stage / 'server.key', 0, 70)
            (stage / 'server.crt').chmod(0o644)
            # Caller reloads only after this operation succeeds; no live reload here.
            os.replace(stage / 'server.key', base / 'server/server.key')
            os.replace(stage / 'server.crt', base / 'server/server.crt')
            check(base, custody)
            print('db_tls_provisioned=true custody_export_required=true reload_performed=false')
        finally:
            shutil.rmtree(stage)



try:
    main()
except (OSError, ValueError, subprocess.SubprocessError):
    print('db_tls_failed=true diagnostics=redacted', file=sys.stderr)
    sys.exit(1)
PY
