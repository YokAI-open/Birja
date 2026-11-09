#!/usr/bin/env bash
# The supported host entrypoint is /usr/local/sbin/birja-deploy. Install only
# after the separately approved host rollout and the exact source has passed
# test-rollback-db-security.sh (default AND supplied archive), all five offline
# regressions and review. --tested-source records that explicit attestation.
# The legacy checkout launcher is deliberately outside the sparse source set.
set -Eeuo pipefail
umask 077
exec python3 - "${BASH_SOURCE[0]}" "$@" <<'PY'
import fcntl
import hashlib
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True


def require(ok):
    if not ok:
        raise ValueError('guard')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def call(argv):
    r = subprocess.run(argv, capture_output=True, timeout=120, check=False)
    require(r.returncode == 0)
    return r.stdout.decode().strip()


def private(path, directory=False):
    require(path.is_absolute() and path == path.resolve())
    for p in [path, *path.parents]: require(not p.is_symlink())
    s = path.stat()
    require(s.st_uid == 0 and not s.st_mode & 0o022)
    require(stat.S_ISDIR(s.st_mode) if directory else stat.S_ISREG(s.st_mode))


def verify(release):
    private(release, True)
    require(re.fullmatch('[0-9a-f]{64}', release.name))
    manifest = release / 'MANIFEST.json'
    private(manifest)
    require(digest(manifest) == release.name)
    values = json.loads(manifest.read_text())
    require(set(values) == {'files','tested_source','profile'})
    require(values['profile'] == 'retained-deploy-v1')
    require(re.fullmatch('[0-9a-f]{40}', values['tested_source']))
    required = {'deploy/deploy.sh','deploy/deploy-entrypoint.sh','deploy/db-security.compose.yml',
                'deploy/db/pg_hba.conf','docker-compose.prod.yml',
                'deploy/check-nginx-config.sh','deploy/install-nginx.sh',
                'backend/Dockerfile','backend/uv.lock','backend/pyproject.toml',
                'frontend/Dockerfile'}
    require(required <= values['files'].keys())
    for name, sha in values['files'].items():
        require(not name.startswith('/') and '..' not in Path(name).parts)
        path = release/name
        private(path)
        require(digest(path) == sha)
    require({str(p.relative_to(release)) for p in release.rglob('*') if p.is_file()} == set(values['files']) | {'MANIFEST.json'})
    return values


def install(source, args):
    require(len(args) == 5 and args[:3] == ['--install','--approved-operation','install-retained-deploy'] and args[3] == '--tested-source')
    tested = args[4]
    require(re.fullmatch('[0-9a-f]{40}', tested))
    require(source == Path('/srv/birja/deploy/deploy-entrypoint.sh'))
    require(call(['git','-C','/srv/birja','rev-parse','HEAD']) == tested)
    require(not call(['git','-C','/srv/birja','status','--porcelain']))
    inherited = os.environ.get('BIRJA_BACKUP_LOCK_FD')
    if inherited is not None:
        helper = Path('/var/lib/birja/recovery/current').resolve()/'deploy/backup-snapshot.py'
        private(helper)
        spec = importlib.util.spec_from_file_location('backup_lock', helper)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        held = module.acquire_operation_lock(Path('/var/lock/birja-deploy.lock'), inherited)
    else:
        fd = os.open('/var/lock/birja-deploy.lock', os.O_CREAT|os.O_WRONLY|os.O_NOFOLLOW, 0o600)
        lock = os.fstat(fd)
        require(stat.S_ISREG(lock.st_mode) and lock.st_uid == 0 and not lock.st_mode & 0o022)
        fcntl.flock(fd, fcntl.LOCK_EX|fcntl.LOCK_NB)
    base = Path('/var/lib/birja/ops')
    base.mkdir(mode=0o700, parents=True, exist_ok=True)
    private(base, True)
    releases = base/'releases'
    releases.mkdir(mode=0o700, exist_ok=True)
    private(releases, True)
    names = ['deploy/deploy.sh','deploy/deploy-entrypoint.sh','deploy/db-security.compose.yml',
             'docker-compose.prod.yml','deploy/db/pg_hba.conf',
             'deploy/check-nginx-config.sh','deploy/install-nginx.sh',
             'deploy/cloudflare-ips.sh','deploy/smoke-prod.sh',
             'deploy/configure-db.sh','deploy/provision-db-tls.sh',
             'deploy/backup-snapshot.py','deploy/db/bootstrap-roles.sql',
             'frontend/Dockerfile']
    names += call(['git','-C','/srv/birja','ls-files','deploy/nginx']).splitlines()
    names += call(['git','-C','/srv/birja','ls-files','backend']).splitlines()
    with tempfile.TemporaryDirectory(prefix='stage-', dir=base) as tmp:
        stage = Path(tmp)
        for name in names:
            original = Path('/srv/birja')/name
            private(original)
            dest = stage/name
            dest.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            shutil.copyfile(original, dest)
            dest.chmod(0o500 if name.endswith('.sh') else 0o400)
        manifest = {'profile':'retained-deploy-v1','tested_source':tested,'files':{n:digest(stage/n) for n in sorted(names)}}
        (stage/'MANIFEST.json').write_text(json.dumps(manifest, sort_keys=True, separators=(',',':')))
        (stage/'MANIFEST.json').chmod(0o400)
        sha = digest(stage/'MANIFEST.json')
        release = releases/sha
        if not release.exists(): shutil.copytree(stage, release)
        verify(release)
    # Own only source selection, leaving the supported legacy launcher present
    # across checkout of a tag that contains an obsolete privileged deploy.sh.
    call(['git','-C','/srv/birja','sparse-checkout','set','--no-cone','/*','!/deploy/'])
    deploy = Path('/srv/birja/deploy')
    deploy.mkdir(mode=0o755, exist_ok=True)
    exclude = Path('/srv/birja/.git/info/exclude')
    require(exclude.parent.is_dir() and not exclude.is_symlink())
    with exclude.open('a') as out: out.write('\n/deploy/\n')
    legacy = deploy/'deploy.sh'
    require(not legacy.is_symlink())
    legacy.write_text('#!/bin/bash\nexec /usr/local/sbin/birja-deploy "$@"\n')
    legacy.chmod(0o500)
    launcher = Path('/usr/local/sbin/birja-deploy')
    require(not launcher.is_symlink())
    temp = launcher.with_name('birja-deploy.tmp')
    require(not temp.exists() and not temp.is_symlink())
    temp.write_text('#!/bin/bash\nexec /var/lib/birja/ops/current/deploy/deploy-entrypoint.sh "$@"\n')
    temp.chmod(0o500)
    os.replace(temp, launcher)
    switch = base/'current.tmp'
    require(not switch.exists() and not switch.is_symlink())
    switch.symlink_to(release)
    os.replace(switch, base/'current')
    print('retained_deploy_installed=true tested_source_attested=true')


def main():
    require(os.geteuid() == 0)
    source = Path(sys.argv[1]).resolve()
    args = sys.argv[2:]
    if args and args[0] == '--install':
        install(source, args)
        return
    require(args in [[], ['--rollback'], ['--help'], ['-h']])
    release = source.parent.parent
    require(release.parent == Path('/var/lib/birja/ops/releases'))
    verify(release)
    require(Path('/var/lib/birja/ops/current').resolve() == release)
    require(os.environ.get('DEPLOY_REF','main') in {'main','v0.3.1',verify(release)['tested_source']})
    # No caller-controlled bundle/Compose/service routing. Only the supported
    # ref is retained from the environment; deploy.sh applies its allowlist.
    env = {'PATH':'/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin','HOME':'/root','LANG':'C.UTF-8',
           'BIRJA_RETAINED_DIR':str(release),'BIRJA_OPS_DIR':str(release),'BIRJA_APP_DIR':'/srv/birja',
           'BIRJA_MIGRATOR_CONTEXT':str(release/'backend')}
    if 'DEPLOY_REF' in os.environ: env['DEPLOY_REF'] = os.environ['DEPLOY_REF']
    if args not in [['--help'], ['-h']]:
        recovery = Path('/var/lib/birja/recovery/current').resolve()
        require(recovery.parent == Path('/var/lib/birja/recovery/releases'))
        require(re.fullmatch('[0-9a-f]{64}', recovery.name))
        helper = recovery/'deploy/backup-snapshot.py'
        private(helper)
        spec = importlib.util.spec_from_file_location('backup_lock', helper)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        held = module.acquire_operation_lock(Path('/var/lock/birja-deploy.lock'))
        os.dup2(held.fileno(), 9, inheritable=True)
        env['BIRJA_RETAINED_LOCK'] = '1'
        env['BIRJA_BACKUP_LOCK_FD'] = '9'
    os.execve('/bin/bash', ['bash', str(release/'deploy/deploy.sh'), *args], env)


try:
    main()
except (ValueError, OSError, KeyError, TypeError, subprocess.TimeoutExpired):
    print('retained_deploy_failed=true diagnostics=redacted', file=sys.stderr)
    sys.exit(1)
PY
