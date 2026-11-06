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
import shlex
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
    assert sum(arg=='--recovery-bundle' or arg.startswith('--recovery-bundle=') for arg in argv) <= 1
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
    assert (result.returncode == 0) == ok, 'rollback check failed step=' + Path(argv[0]).name + ' exit=' + str(result.returncode) + '; diagnostics=redacted'
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
  assert (await c.execute(text('SELECT NOT (rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls) FROM pg_roles WHERE rolname=current_user'))).scalar_one()
 await e.dispose()
asyncio.run(main())
'''


def orchestration_self_test():
    # Exercise the actual installer and repeated launchers in a private fake
    # host. Only fixed production path literals are relocated; no host checkout
    # config, services, credentials or security decisions are substituted.
    with tempfile.TemporaryDirectory(prefix='birja-backup-test-') as tmp:
        root = Path(tmp)
        root.chmod(0o700)
        app = root/'app'
        app.mkdir(mode=0o700)
        replacements = {'/srv/birja':str(app), '/var/lib/birja/ops':str(root/'ops'),
                        '/usr/local/sbin/birja-deploy':str(root/'bin/birja-deploy'),
                        '/var/lock/birja-deploy.lock':str(root/'operation.lock'),
                        '/var/www/birja':str(root/'web'), '/var/lib/birja':str(root/'state')}
        def relocated(text):
            for a,b in replacements.items(): text = text.replace(a,b)
            return text
        names = ['deploy/deploy.sh','deploy/deploy-entrypoint.sh','deploy/db-security.compose.yml',
                 'deploy/db/pg_hba.conf','docker-compose.prod.yml',
                 'deploy/smoke-prod.sh','deploy/configure-db.sh','deploy/provision-db-tls.sh',
                 'deploy/backup-snapshot.py','deploy/db/bootstrap-roles.sql',
                 'backend/Dockerfile','backend/uv.lock','backend/pyproject.toml','frontend/Dockerfile']
        for name in names:
            dest=app/name
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_text(relocated((ROOT/name).read_text()))
            dest.chmod(0o700 if name.endswith('.sh') else 0o600)
        for name in ['check-nginx-config.sh','install-nginx.sh','cloudflare-ips.sh']:
            p=app/'deploy'/name
            p.write_text('#!/bin/bash\nexit 0\n')
            p.chmod(0o700)
        (root/'bin').mkdir(mode=0o700)
        helper=root/'state/recovery/current/deploy/backup-snapshot.py'
        helper.parent.mkdir(mode=0o700,parents=True)
        helper.write_bytes((ROOT/'deploy/backup-snapshot.py').read_bytes())
        def git(*args):
            result = subprocess.run(['git','-C',str(app),*args],env=r.ENV,capture_output=True)
            assert result.returncode == 0, result.stderr.decode()
            return result.stdout.decode().strip()
        git('init','-b','main')
        git('config','user.email','synthetic@example.invalid')
        git('config','user.name','Synthetic')
        git('add',*names,'deploy/check-nginx-config.sh','deploy/install-nginx.sh','deploy/cloudflare-ips.sh')
        git('commit','-m','Synthetic current source')
        current=git('rev-parse','HEAD')
        git('checkout','-b','old')
        (app/'deploy/deploy.sh').write_text('#!/bin/bash\necho unsafe-old-launcher\nexit 99\n')
        git('add','deploy/deploy.sh')
        git('commit','-m','Synthetic old launcher')
        git('tag','v0.3.1')
        old=git('rev-parse','HEAD')
        git('checkout','main')
        run(['bash','-c','exec 9>"$1"; flock -n 9; BIRJA_BACKUP_LOCK_FD=9 bash "$2" --install --approved-operation install-retained-deploy --tested-source "$3"; ! flock -n "$1" true',
            '_',str(root/'operation.lock'),str(app/'deploy/deploy-entrypoint.sh'),current])
        launcher=root/'bin/birja-deploy'
        legacy=app/'deploy/deploy.sh'
        release=(root/'ops/current').resolve()
        retained={p:r.digest(p) for p in release.rglob('*') if p.is_file()}
        def checkout(ref):
            result=subprocess.run(['bash','-c','. "$1"; exec 9>"$LOCK"; flock -n 9; checkout_source "$2"; ! flock -n "$LOCK" true','_',str(release/'deploy/deploy.sh'),ref],env={**r.ENV,'BIRJA_RETAINED_DIR':str(release)},capture_output=True)
            assert result.returncode == 0, result.stderr.decode() + repr(git('status','--porcelain'))
        # git checkout must preserve the managed legacy entrypoint, with a clean
        # status, even at the ref whose tracked launcher is insecure.
        for ref in ['v0.3.1','main','v0.3.1']:
            checkout(ref)
            assert git('status','--porcelain') in ['', 'M deploy/deploy.sh']
            for entry in [launcher,legacy]:
                assert b'Usage:' in run([str(entry),'--help']).stdout
                run([str(entry)],env={**r.ENV,'DEPLOY_REF':'unsupported-test'},ok=False)
            assert all(r.digest(p)==sha for p,sha in retained.items())
        saved=legacy.read_bytes()
        failure=['bash','-c','. "$1"; exec 9>"$LOCK"; flock -n 9; checkout_source "$2"','_',str(release/'deploy/deploy.sh'),'missing-ref-test']
        run(failure,env={**r.ENV,'BIRJA_RETAINED_DIR':str(release)},ok=False)
        assert legacy.read_bytes() == saved and git('rev-parse','HEAD') == old
        legacy.chmod(0o700)
        legacy.write_bytes(saved+b'# unapproved\n')
        run(failure,env={**r.ENV,'BIRJA_RETAINED_DIR':str(release)},ok=False)
        assert legacy.read_bytes() == saved+b'# unapproved\n'
        legacy.write_bytes(saved)
        legacy.chmod(0o500)
        run(['bash','-c','. "$1"; checkout_source main','_',str(release/'deploy/deploy.sh')],env={**r.ENV,'BIRJA_RETAINED_DIR':str(release)},ok=False)
        assert legacy.read_bytes() == saved and git('rev-parse','HEAD') == old
        # Run retained rollback's real checkout/stack/static/pending behavior;
        # service actions alone are no-ops in this offline Git fixture.
        checkout(current)
        state=root/'state'
        web=root/'web'; (web/'releases/old').mkdir(parents=True)
        (web/'releases/new').mkdir()
        log=state/'deploys.log'
        log.write_text('t '+old+' '+str(web/'releases/old')+' v0.3.1\nt '+current+' '+str(web/'releases/new')+' main\n')
        script='''set -Eeuo pipefail
. "$1"
exec 9>"$LOCK"
flock -n 9
BIRJA_TESTED_SOURCE=$2
dc() { if [ "$1" = config ]; then printf 'backend\\nscheduler\\n'; fi; }
health_check() { :; }
do_rollback
[ ! -e "$PENDING_MARK" ]
[ "$(live_sha "$DEPLOY_LOG")" = "$3" ]
[ "$(readlink -f "$WEB_ROOT/current")" = "$WEB_ROOT/releases/old" ]
'''
        run(['bash','-c',script,'_',str(release/'deploy/deploy.sh'),current,old],env={**r.ENV,'BIRJA_RETAINED_DIR':str(release)})
        assert git('rev-parse','HEAD') == old
        assert b'Usage:' in run([str(legacy),'--help']).stdout
        assert git('status','--porcelain') in ['', 'M deploy/deploy.sh']
        assert all(r.digest(p)==sha for p,sha in retained.items())
        print('retained_installer_real_git_rollbacks=true repeated_legacy_entrypoints=true immutable_routing=true checkout_failure_restored=true changed_launcher_unheld_lock_rejected=true',flush=True)


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
               'BIRJA_MIGRATOR_CONTEXT': str(ROOT / 'backend'), 'BIRJA_OLD_TLS_SUFFIX': '?ssl=verify-full'}
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
            # Call the retained deploy gate itself against the same installed
            # synthetic recovery. Only fixed host paths/config are relocated.
            gate_text=(ROOT/'deploy/deploy.sh').read_text()
            gate_text=gate_text.replace('/var/lib/birja/recovery/current',str(session.release))
            gate_text=gate_text.replace('[[ "$recovery" =~ ^/var/lib/birja/recovery/releases/[0-9a-f]{64}$ ]]',
                '[ "$recovery" = '+shlex.quote(str(session.release))+' ]')
            gate_text=gate_text.replace('/var/lib/birja/backup/last-success.json',str(root/'state/last-success.json'))
            gate_text=gate_text.replace('recovery-gate \\\n','recovery-gate --synthetic '+shlex.quote(str(session.config_path))+' \\\n')
            gate=root/'deploy-gate.sh'; gate.write_text(gate_text)
            history=root/'gate-deploys.log'; history.write_text('t '+old_sha+' unused main\n')
            gate_dc=['/usr/bin/docker','compose','--env-file','/dev/null','-p','birja-ops-test','-f',str(root/'old/docker-compose.ops-test.yml')]
            # Fixture server's maintenance DB differs from the populated source;
            # match production's POSTGRES_DB=source for the gate's socket query.
            shell='. '+shlex.quote(str(gate))+'; DEPLOY_LOG='+shlex.quote(str(history))+'; dc() { shift 2; '+shlex.join(gate_dc)+' exec -T -e POSTGRES_DB=birja_source_test "$@"; }; exec 9>'+shlex.quote(str(root/'operation.lock'))+'; flock -n 9; recovery_gate'
            f.target(root,['bash','-c',shell])
            evidence=root/'state/restore-last-success.json'
            saved=evidence.read_bytes()
            evidence.unlink()
            f.target(root,['bash','-c',shell],ok=False)
            evidence.write_bytes(saved); evidence.chmod(0o600)
            attempt=root/'state/restore-last-attempt.json'
            prior=attempt.read_bytes()
            data=json.loads(prior); data['ok']=False
            attempt.write_text(json.dumps(data))
            f.target(root,['bash','-c',shell],ok=False)
            attempt.write_bytes(prior)
            state_files=[root/'state'/name for name in ['last-success.json','last-attempt.json','restore-last-success.json','restore-last-attempt.json']]
            original={p:p.read_bytes() for p in state_files}
            for path in state_files:
                data=json.loads(original[path])
                for key in list(data):
                    if key=='epoch' or key.endswith('_epoch'):
                        data[key]-=93601
                        data[key.replace('epoch','utc')]=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(data[key]))
                path.write_text(json.dumps(data))
            f.target(root,['bash','-c',shell],ok=False)
            for path,value in original.items(): path.write_bytes(value)
            f.target(root,['bash','-c',shell])
            print('deploy_exact_recovery_gate=true missing_failed_stale_evidence_rejected=true',flush=True)
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
            # Write through the live container mount namespace: Docker's archive
            # copy does not address this tmpfs. No bytes enter argv or logs.
            def server_file(source,destination):
                assert destination.startswith('/var/lib/postgresql/')
                run(['/usr/bin/docker','exec','-i','-u','0',container,'sh','-c',
                     'umask 077; cat > "$1"; chown 0:999 "$1"; chmod 640 "$1"','_',destination],source.read_bytes())
            server_file(root/'db-tls/server/server.crt','/var/lib/postgresql/server.crt')
            server_file(root/'db-tls/server/server.key','/var/lib/postgresql/server.key')
            hba = root/'pg_hba.conf'
            hba.write_text((ROOT/'deploy/db/pg_hba.conf').read_text())
            hba_path=r.sql(dc0,'SHOW hba_file','birja_source_test').decode().strip()
            assert hba_path.startswith('/var/lib/postgresql/') and hba_path.endswith('/pg_hba.conf')
            server_file(hba,hba_path)
            for query in ["ALTER SYSTEM SET ssl_cert_file='/var/lib/postgresql/server.crt'", "ALTER SYSTEM SET ssl_key_file='/var/lib/postgresql/server.key'", "ALTER SYSTEM SET ssl='on'", "ALTER SYSTEM SET ssl_min_protocol_version='TLSv1.2'"]:
                r.sql(dc0, query, 'birja_source_test')
            r.sql(dc0, 'SELECT pg_reload_conf()', 'birja_source_test')
            def client(service, code, extra=(), ok=True):
                return run(dc+['run','--rm','--no-deps','-T',*extra,'--entrypoint','python',service,'-'], code.encode(), ok=ok)
            run(dc+['run','--rm','--no-deps','-T','migrate'])
            assert r.sql(dc0,'SELECT version_num FROM alembic_version','birja_source_test').strip() == b'0008'
            old_runtime=copy.deepcopy(fixture)
            for service,key in [('backend','APP'),('scheduler','SCHEDULER')]:
                s=fixture['services'][service]
                s['image']='birja-backend-test:phase05-07'
                s['volumes'] += [str(ROOT/'backend/app')+':/app/app:ro']
                s['environment']['DATABASE_URL']=env[key+'_DATABASE_URL']
            file.write_text(json.dumps(fixture))
            current_probe=PROBE.replace('e=create_async_engine(s.database_url)',
                'from app.db.connection import database_connect_args\n e=create_async_engine(s.database_url,connect_args=database_connect_args(s))')
            current_services=f.ROLE_SERVICES.replace('engine=create_async_engine(s.database_url)',
                'from app.db.connection import database_connect_args\n engine=create_async_engine(s.database_url,connect_args=database_connect_args(s))')
            for service in ['backend','scheduler']:
                settings='from app.core.config import SchedulerSettings as Settings' if service=='scheduler' else 'from app.core.config import Settings'
                client(service,current_probe.replace('from app.core.config import Settings',settings))
                client(service,current_services.replace('from app.core.config import Settings',settings))
            f.recovery_roundtrip(session, source_revision='0008', source_release=current_sha)
            print('post_hardening_same_installed_recovery=true current_services_tls=true',flush=True)
            # Roll back only application image/source routing. Source PostgreSQL,
            # schema, limited logins, HBA, CA and installed recovery are retained.
            file.write_text(json.dumps(old_runtime))
            # Old image has no shared connection helper: the overlay alone enforces verify-full.
            for service in ['backend','scheduler']:
                probe=PROBE if service=='backend' else PROBE.replace('from app.core.config import Settings','from app.core.config import SchedulerSettings as Settings')
                client(service, probe)
            services = f.ROLE_SERVICES.replace('restricted-runtime@example.invalid','old-runtime@example.invalid')
            client('scheduler', services.replace('from app.core.config import Settings','from app.core.config import SchedulerSettings as Settings'))
            client('backend', services)
            for extra, marker in [(['-e','PGSSLROOTCERT=/does-not-exist'], b'FileNotFoundError'),
                                  (['-e','DATABASE_URL='+env['APP_DATABASE_URL'].replace('@postgres:', '@birja-ops-test-postgres-1:')+'?ssl=verify-full'], b'Hostname mismatch'),
                                  (['-e','DATABASE_URL='+env['APP_DATABASE_URL']+'?ssl=disable'], b'no encryption')]:
                result = client('backend', PROBE, extra, ok=False)
                assert marker.lower() in result.stderr.lower(), 'specific TLS rejection missing: '+marker.decode()
            # Independently signed CA must fail even though readable and well-formed.
            run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','1','-subj','/CN=wrong-ca','-keyout',str(root/'wrong.key'),'-out',str(root/'wrong.crt')])
            (root/'wrong.crt').chmod(0o644)
            result = client('backend', PROBE, ['-v',str(root/'wrong.crt')+':/run/birja/db-ca.crt:ro'], ok=False)
            assert b'CERTIFICATE_VERIFY_FAILED' in result.stderr
            print('old_image_services_tls=true bad_ca_hostname_plaintext_rejected=true', flush=True)
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
    for bad in [['--recovery-bundle'], ['--recovery-bundle',''], ['--unknown'], ['--self-test-recovery-bundle-inputs']*2, ['--recovery-bundle','a','--recovery-bundle','b'], ['--recovery-bundle=a','--recovery-bundle=b']]:
        try: options(bad)
        except (SystemExit, AssertionError, ValueError, OSError): pass
        else: raise AssertionError('unsafe options accepted')
    print('rollback_input_rejections=true docker_install_fallback_calls=0')
else:
    orchestration_self_test()
    integration(args.recovery_bundle)
PY
