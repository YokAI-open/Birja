#!/usr/bin/env bash
# Synthetic only. The selected recovery artifact is installed once and retained.
set -Eeuo pipefail
umask 077
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec python3 - "$ROOT" "$@" <<'PY'
import argparse
import copy
import importlib.util
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location('fixtures', ROOT / 'deploy/tests/ops-fixtures.py')
f = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)
r = f.r


def options(argv):
    p = argparse.ArgumentParser()
    p.add_argument('--recovery-bundle')
    p.add_argument('--self-test-recovery-bundle-inputs', action='store_true')
    a = p.parse_args(argv)
    assert argv.count('--recovery-bundle') <= 1
    assert argv.count('--self-test-recovery-bundle-inputs') <= 1
    assert not (a.self_test_recovery_bundle_inputs and a.recovery_bundle is not None)
    if a.recovery_bundle is not None:
        assert a.recovery_bundle
        archive = r.synthetic_path(a.recovery_bundle)
        sha = r.private(str(archive) + '.sha256').read_text().strip()
        r.bundle_verify(archive, sha, required_profile='deploy-recovery-v2')
    return a


def run(argv, data=None, env=None, ok=True):
    result = subprocess.run(argv, input=data, env=env or r.ENV, capture_output=True, timeout=180)
    assert (result.returncode == 0) == ok, 'rollback check failed; diagnostics=redacted'
    return result


PROBE = '''
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import Settings
async def main():
 s=Settings()
 e=create_async_engine(s.database_url)
 async with e.connect() as c:
  assert (await c.execute(text('SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()'))).scalar_one(), 'old_runtime_verified_tls=false'
  assert (await c.execute(text('SELECT current_user'))).scalar_one() in {'birja_app','birja_scheduler','birja_migrator'}
 await e.dispose()
asyncio.run(main())
'''


def integration(archive_arg):
    started = time.monotonic()
    # This exact locally available ref is required; never fetch or change host HEAD.
    old_sha = r.call(['git', 'rev-parse', '--verify', 'v0.3.1^{commit}']).decode().strip()
    current_sha = r.call(['git', 'rev-parse', 'HEAD']).decode().strip()
    original_head = current_sha
    dc0 = r.compose()
    with f.installed_recovery(archive_arg) as session:
        root = session.root
        old = root / 'old/app'
        # Actual old application source, using byte-identical locked dependencies.
        assert (old / 'backend/uv.lock').read_bytes() == (ROOT / 'backend/uv.lock').read_bytes()
        assert (old / 'backend/pyproject.toml').read_bytes() == (ROOT / 'backend/pyproject.toml').read_bytes()
        (old / 'backend/Rollback.Dockerfile').write_text(
            'FROM birja-backend-test:phase05-07\nCOPY --chown=app:app app /app/app\nCOPY --chown=app:app alembic /app/alembic\nCOPY --chown=app:app alembic.ini /app/alembic.ini\n')
        run(['/usr/bin/docker', 'build', '--network=none', '--pull=false', '-f', str(old / 'backend/Rollback.Dockerfile'), '-t', 'birja-rollback-test:v0.3.1', str(old / 'backend')])
        env = {**r.ENV, 'POSTGRES_USER': r.BOOT, 'POSTGRES_PASSWORD': 'synthetic-ops-only',
               'POSTGRES_DB': 'birja_source_test', 'REDIS_PASSWORD': 'synthetic-redis-only',
               'OTP_HMAC_SECRET': 'synthetic-only-otp-secret-00000000000000',
               'JWT_SECRET': 'synthetic-only-jwt-secret-00000000000000',
               'RESEND_API_KEY': 'synthetic-unused', 'EMAIL_FROM': 'test@example.invalid',
               'BIRJA_APP_DIR': str(old), 'BIRJA_OPS_DIR': str(ROOT),
               'BIRJA_MIGRATOR_CONTEXT': str(ROOT / 'backend')}
        for role, char in [('APP', 'a'), ('SCHEDULER', 'b'), ('MIGRATOR', 'c')]:
            env[role + '_DATABASE_URL'] = 'postgresql+asyncpg://birja_' + role.lower() + ':' + char * 64 + '@postgres:5432/birja_source_test'
        try:
            run(dc0 + ['up', '-d', '--wait'])
            r.sql(dc0, 'CREATE DATABASE birja_source_test;', 'birja_ops_test')
            seed = ['/usr/bin/docker', 'run', '--rm', '-i', '--network', 'birja-ops-test_isolated']
            seedenv = {'ENV': 'test', 'DATABASE_URL': 'postgresql+asyncpg://' + r.BOOT + ':synthetic-ops-only@postgres:5432/birja_source_test',
                       'REDIS_URL': 'redis://localhost/0', 'OTP_HMAC_SECRET': env['OTP_HMAC_SECRET'], 'JWT_SECRET': env['JWT_SECRET'], 'EMAIL_BACKEND': 'console'}
            for k, v in seedenv.items(): seed += ['-e', k + '=' + v]
            seed += ['--entrypoint', 'python', 'birja-rollback-test:v0.3.1', '-']
            run(seed, f.SEED.encode())
            if not (ROOT / 'deploy/db-security.compose.yml').exists():
                # Meaningful RED: actual old engine connects, but its session is plaintext.
                probe = PROBE.replace("in {'birja_app','birja_scheduler','birja_migrator'}", "== '" + r.BOOT + "'")
                result = subprocess.run(seed, input=probe.encode(), capture_output=True, env=r.ENV, timeout=30)
                assert result.returncode == 0, 'real_old_image_verified_tls=false plaintext_session=true'
            f.recovery_roundtrip(session, source_revision='0007', source_release=old_sha)
            print('pre_hardening_same_installed_recovery=true', flush=True)
            for role, char in [('app','a'), ('scheduler','b'), ('migrator','c')]:
                (root / role).write_text(char * 64)
                (root / role).chmod(0o600)
            roles = root / 'roles.json'
            roles.write_text(json.dumps({'project':'birja-ops-test','db_name':'birja_source_test','bootstrap':r.BOOT,'password_files':{x:str(root/x) for x in ['app','scheduler','migrator']}}))
            roles.chmod(0o600)
            run(['bash', str(ROOT/'deploy/configure-db.sh'), '--synthetic', str(roles), '--apply', '--approved-operation', 'populated-role-transition'])
            run(['bash', str(ROOT/'deploy/provision-db-tls.sh'), '--synthetic', str(root), '--create', '--approved-custody', 'owner-off-server-password-manager'])
            prod = json.loads(run(['/usr/bin/docker','compose','--env-file','/dev/null','-f',str(ROOT/'docker-compose.prod.yml'),'-f',str(ROOT/'deploy/db-security.compose.yml'),'--profile','migrate','config','--format','json'], env=env).stdout)
            fixture = {'name':'birja-ops-test','services':{},'networks':{'isolated':{'internal':True}}}
            for name, source in prod['services'].items():
                s = copy.deepcopy(source)
                for key in ['build','ports','restart','logging','profiles','depends_on','volumes','networks']: s.pop(key, None)
                s.update(networks=['isolated'], mem_limit='512m', cpus=2, pids_limit=128)
                if name == 'postgres':
                    s['networks'] = {'isolated':{'aliases':['wrong-host']}}
                    s['environment'] = {'POSTGRES_USER':r.BOOT,'POSTGRES_PASSWORD':'synthetic-ops-only','POSTGRES_DB':'birja_ops_test'}
                    # Keep the same already populated tmpfs container; enable TLS in place below.
                    s['tmpfs'] = ['/var/lib/postgresql:size=268435456']
                    s['command'] = ['postgres','-c','statement_timeout=30000','-c','idle_in_transaction_session_timeout=30000']
                elif name == 'redis': s['tmpfs'] = ['/data:size=16777216']
                else:
                    s['image'] = 'birja-rollback-test:v0.3.1' if name != 'migrate' else 'birja-backend-test:phase05-07'
                    s['volumes'] = [str(root/'db-tls/ca.crt')+':/run/birja/db-ca.crt:ro']
                    if name == 'migrate':
                        s['volumes'] += [str(ROOT/'backend/app')+':/app/app:ro',str(ROOT/'backend/alembic')+':/app/alembic:ro']
                    else: s['command'] = ['sleep','infinity']
                fixture['services'][name] = s
            file = root/'rollback-compose.json'
            file.write_text(json.dumps(fixture))
            dc = ['/usr/bin/docker','compose','--env-file','/dev/null','-p','birja-ops-test','-f',str(file)]
            # TLS files enter only the source server; same container/data survive the transition.
            container = r.call(dc0+['ps','-q','postgres']).decode().strip()
            run(['/usr/bin/docker','cp',str(root/'db-tls/server/server.crt'),container+':/var/lib/postgresql/server.crt'])
            run(['/usr/bin/docker','cp',str(root/'db-tls/server/server.key'),container+':/var/lib/postgresql/server.key'])
            run(['/usr/bin/docker','exec','-u','0',container,'chown','postgres:postgres','/var/lib/postgresql/server.crt','/var/lib/postgresql/server.key'])
            hba = root/'pg_hba.conf'
            hba.write_text((ROOT/'deploy/db/pg_hba.conf').read_text())
            run(['/usr/bin/docker','cp',str(hba),container+':/var/lib/postgresql/18/docker/pg_hba.conf'])
            for query in ["ALTER SYSTEM SET ssl_cert_file='/var/lib/postgresql/server.crt'", "ALTER SYSTEM SET ssl_key_file='/var/lib/postgresql/server.key'", "ALTER SYSTEM SET ssl='on'", "ALTER SYSTEM SET ssl_min_protocol_version='TLSv1.2'"]:
                r.sql(dc0, query, 'birja_source_test')
            r.sql(dc0, 'SELECT pg_reload_conf()', 'birja_source_test')
            def client(service, code, extra=(), ok=True):
                return run(dc+['run','--rm','--no-deps','-T',*extra,'--entrypoint','python',service,'-'], code.encode(), ok=ok)
            run(dc+['run','--rm','--no-deps','-T','migrate'])
            assert r.sql(dc0,'SELECT version_num FROM alembic_version','birja_source_test').strip() == b'0008'
            # Old image has no shared connection helper: the overlay alone enforces verify-full.
            for service in ['backend','scheduler']:
                client(service, PROBE)
            services = f.ROLE_SERVICES
            client('scheduler', services)
            client('backend', services)
            for extra, marker in [(['-e','PGSSLROOTCERT=/does-not-exist'], b'root certificate'),
                                  (['-e','DATABASE_URL='+env['APP_DATABASE_URL'].replace('@postgres:', '@wrong-host:')+'?ssl=verify-full'], b'Hostname mismatch'),
                                  (['-e','DATABASE_URL='+env['APP_DATABASE_URL']+'?ssl=disable'], b'no encryption')]:
                result = client('backend', PROBE, extra, ok=False)
                assert marker.lower() in result.stderr.lower(), 'specific TLS rejection missing'
            # Independently signed CA must fail even though readable and well-formed.
            run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','1','-subj','/CN=wrong-ca','-keyout',str(root/'wrong.key'),'-out',str(root/'wrong.crt')])
            (root/'wrong.crt').chmod(0o644)
            result = client('backend', PROBE, ['-v',str(root/'wrong.crt')+':/run/birja/db-ca.crt:ro'], ok=False)
            assert b'CERTIFICATE_VERIFY_FAILED' in result.stderr
            f.recovery_roundtrip(session, source_revision='0008', source_release=current_sha)
            print('post_hardening_same_installed_recovery=true old_image_services_tls=true bad_ca_hostname_plaintext_rejected=true', flush=True)
            f.recovery_roundtrip(session, source_revision='0008', source_release=old_sha)
            assert r.call(['git','rev-parse','HEAD']).decode().strip() == original_head
            print('old_image_rollback_same_installed_recovery=true revision_0008_preserved=true', flush=True)
            print('rollback_integration_seconds=%.3f' % (time.monotonic()-started), flush=True)
        finally:
            run(dc0+['down','-v','--remove-orphans'])
            clone = r.compose('birja-restore-check')
            run(clone+['down','-v','--remove-orphans'])
            assert not r.call(dc0+['ps','-q']).strip()
            assert not r.call(clone+['ps','-q']).strip()


args = options(sys.argv[2:])
if args.self_test_recovery_bundle_inputs:
    f.input_self_test()
    for bad in [['--recovery-bundle'], ['--recovery-bundle',''], ['--unknown'], ['--self-test-recovery-bundle-inputs']*2, ['--recovery-bundle','a','--recovery-bundle','b']]:
        try: options(bad)
        except (SystemExit, AssertionError, ValueError, OSError): pass
        else: raise AssertionError('unsafe options accepted')
    print('rollback_input_rejections=true docker_install_fallback_calls=0')
else:
    integration(args.recovery_bundle)
PY
