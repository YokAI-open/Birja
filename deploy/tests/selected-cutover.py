#!/usr/bin/env python3
"""Serial private retained-launcher proof; only fixed synthetic Docker projects."""

import fcntl
import hashlib
import http.server
import importlib.util
import io
import json
import os
import re
import shutil
import ssl
import subprocess
import tarfile
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "fixtures", ROOT / "deploy/tests/ops-fixtures.py"
)
f = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)
r = f.r
PROJECT = "birja-ops-test"
PG_OLD = "postgres:18.6-trixie@sha256:bd5dfa494a5a259704365813dbfa5fa6b3e69be7348d43b547f540c730478583"
REDIS_OLD = "redis:8.8.4-trixie@sha256:a008e2cb5579f3616b29bd9e9913a25f16ec09ae2f56ddab524664663b581228"
REDIS_NEW = "cgr.dev/chainguard/redis@sha256:26bb2dd4412f902f3decd44fba5dfaef4360d97004d44f6cff7f28d6aba19c48"


def call(argv, data=None, ok=True, timeout=180, env=None):
    started = time.monotonic()
    result = subprocess.run(
        argv,
        input=data,
        capture_output=True,
        timeout=timeout,
        env=env or r.ENV,
        check=False,
    )
    print(
        f"cutover_command={Path(argv[0]).name} seconds={time.monotonic() - started:.3f} exit={result.returncode}",
        flush=True,
    )
    assert (result.returncode == 0) == ok, (
        "synthetic command failed: "
        + repr(argv[:4])
        + "\n"
        + result.stdout.decode()
        + result.stderr.decode()
    )
    return result.stdout


def isolate_entrypoint_environment(text, root):
    # Compose writes client metadata via os.TempDir. Keep it inside the
    # Landlock-protected synthetic host, independent of caller environment.
    anchor = "'LANG':'C.UTF-8',"
    assert text.count(anchor) == 1
    # Host-wide Git config is outside the synthetic host's allowlist. Keep
    # normal repository ownership and local config checks, without allowing
    # unrelated runner files or changing the production entrypoint.
    return text.replace(
        anchor,
        anchor + "'GIT_CONFIG_NOSYSTEM':'1','TMPDIR':" + repr(str(root / "tmp")) + ",",
    )


def integration(archive=None):
    return _integration(archive, current0014=False)


def integration_current0014(archive=None):
    return _integration(archive, current0014=True)


def assert_preserved(expected, actual):
    def differences(left, right, path='state'):
        if isinstance(left, dict) and isinstance(right, dict):
            return [item for key in sorted(left.keys() | right.keys())
                    for item in differences(left.get(key), right.get(key), path+'.'+str(key))]
        if isinstance(left, (tuple, list)) and isinstance(right, (tuple, list)) and len(left)==len(right):
            return [item for index,(a,b) in enumerate(zip(left,right))
                    for item in differences(a,b,path+'.'+str(index))]
        return [] if left == right else [path]
    assert actual == expected, 'selected0014 preservation comparison failed paths='+','.join(differences(expected,actual))


def source_role_config(root, roles):
    """Use the unchanged synthetic helper's private root/path contract."""
    config = {**roles, 'password_files': {}}
    for role, source in roles['password_files'].items():
        destination = root / role
        destination.write_bytes(Path(source).read_bytes())
        destination.chmod(0o600)
        config['password_files'][role] = str(destination)
    path = root / 'roles.json'
    path.write_text(json.dumps(config))
    path.chmod(0o600)
    return path


def assert_current0014_financial(expected, actual):
    # The selected candidate physically upgrades pinned PG18.6 to pinned18.7.
    # Assert that exact metadata transition independently; all saved financial,
    # schema/authority and identity facts must still equal the original.
    before, identities_before = expected
    after, identities_after = actual
    before, after = dict(before), dict(after)
    assert re.fullmatch(r'18\.6(?: \([^)]*\))?', before.pop('server_version')), 'unexpected original server version'
    assert re.fullmatch(r'18\.7(?: \([^)]*\))?', after.pop('server_version')), 'unexpected candidate server version'
    assert_preserved((before, identities_before), (after, identities_after))


def canonical_runtime_images(data):
    """Compare every CLI field and duplicate row, independently of JSON order."""
    try:
        rows = json.loads(data)
    except json.JSONDecodeError:
        rows = [json.loads(line) for line in data.splitlines() if line.strip()]
    if isinstance(rows, dict):
        rows = [rows]
    if not isinstance(rows, list) or not rows or not all(isinstance(row, dict) for row in rows):
        raise ValueError('invalid runtime image records')
    return tuple(sorted(json.dumps(row, sort_keys=True, separators=(',', ':')) for row in rows))


def refused_rollback(target, launcher, snapshot, *, evidence_dir=None, raw_runtime=None):
    def save(name, value):
        if evidence_dir is None:
            return
        def encode(value):
            if isinstance(value, bytes):
                return {'bytes_hex': value.hex()}
            raise TypeError('unexpected snapshot value')
        path = evidence_dir / (name + '-snapshot.json')
        path.write_text(json.dumps(value, sort_keys=True, default=encode) + '\n')
        path.chmod(0o600)
        if raw_runtime is not None:
            path = evidence_dir / (name + '-runtime-raw.json')
            path.write_bytes(raw_runtime())
            path.chmod(0o600)
    before = snapshot()
    save('before', before)
    result = target([str(launcher), '--rollback'], ok=False)
    after = snapshot()
    save('after', after)
    assert b'application_schema_incompatible=true' in result.stderr, 'wrong rollback refusal'
    assert_preserved(before, after)
    print('selected0014_unsupported_rollback_refused=true revision0014=true', flush=True)


def current0014_checks(*, session, current, old, app, root, launcher, target,
                       git, dc, compose_env, compose, originals, fingerprint,
                       retained, original_canonical, original_identity,
                       runtime_saved, dividend_saved, inherited):
    # Recovery helpers invoke Compose with a clean environment. Bind the same
    # fixed fixture routing explicitly rather than inheriting operator state.
    command = ['env', *[key+'='+value for key,value in compose_env.items()], *dc]
    database = 'birja_source_test'

    def financial():
        canonical = r.canonical(command, database)
        identity = {name:r.sql(command, 'SELECT last_value,is_called FROM '+name+'_id_seq', database).strip()
                    for name in original_identity}
        return canonical, identity

    def unchanged():
        assert_current0014_financial((original_canonical, original_identity), financial())
        assert all(fingerprint(name) == value for name,value in originals.items())
        assert all(r.digest(path) == value for path,value in retained.items())

    runtime_samples = []
    def snapshot():
        runtime = compose('images', '--format', 'json')
        runtime_samples.append(runtime)
        return {
            'financial': financial(),
            'originals': {name:fingerprint(name) for name in originals},
            'head': git('rev-parse', 'HEAD'),
            'web': os.readlink(root / 'web/current'),
            'log': (root / 'history/deploys.log').read_bytes(),
            'pending': (root / 'history/deploy.pending').read_bytes() if (root / 'history/deploy.pending').exists() else None,
            'containers': compose('ps', '-q'),
            'runtime': canonical_runtime_images(runtime),
        }

    def replay():
        manifest, _ = financial()
        dump = compose('exec', '-T', 'postgres', 'pg_dump', '-U', r.BOOT,
                       '-d', database, '--format=custom', '--no-owner', '--no-acl')
        with r.restored(command, dump):
            r.verify(command, manifest)
            r.sql(command, 'GRANT CONNECT ON DATABASE birja_restore_test TO birja_app,birja_scheduler,birja_migrator', 'birja_ops_test')

            def owner(code):
                return compose('run', '--rm', '--no-deps', '-T',
                               '-e', 'ENV=test', '-e', 'EMAIL_BACKEND=console',
                               '-e', 'OTP_HMAC_SECRET=synthetic-only-otp-secret-00000000000000',
                               '-e', 'JWT_SECRET=synthetic-only-jwt-secret-00000000000000',
                               'migrate', 'python', '-', data=code.encode())

            runtime = owner(f.runtime_program(seed=False, database='birja_restore_test', expected=runtime_saved))
            assert f.runtime_receipt_digest(runtime) == runtime_saved
            assert b'runtime_current_mixed_history=true revision0014=true' in runtime
            assert b'verified_tls=true' in runtime
            dividend = owner(f.dividend_program(mode='verify', database='birja_restore_test', expected=dividend_saved))
            assert f.dividend_digest(dividend) == dividend_saved
            assert b'scheduler_quarantine=true' in dividend and b'verified_tls=true' in dividend
            r.verify(command, manifest)
        unchanged()
        print('selected0014_owner_clone_replay=true app_scheduler_42501_quarantine=true revision0014=true', flush=True)

    assert git('rev-parse', 'HEAD') == current
    assert r.canonical(command, database)['revision'] == '0014'
    unchanged()
    replay()
    f.recovery_roundtrip(session, source_revision='0014', source_release=current, inherited=inherited)
    print('selected0014_current_cutover=true verified_tls=true revision0014=true', flush=True)
    evidence_dir = Path(tempfile.mkdtemp(prefix='birja-backup-test-selected0014-evidence-'))
    evidence_dir.chmod(0o700)
    try:
        refused_rollback(target, launcher, snapshot, evidence_dir=evidence_dir,
                         raw_runtime=lambda: runtime_samples[-1])
    finally:
        print('selected0014_refusal_evidence='+str(evidence_dir), flush=True)
    # Only the existing failed-attempt marker is changed. The release log still
    # identifies the last good tested source; no schema downgrade is attempted.
    (root / 'history/deploy.pending').write_text('synthetic failed attempt\n')
    result = target([str(launcher), '--rollback'])
    assert b'Rolling back' in result.stdout and git('rev-parse', 'HEAD') == current
    assert not (root / 'history/deploy.pending').exists()
    unchanged()
    replay()
    print('selected0014_failed_attempt_rollback_to_tested_source=true revision0014=true', flush=True)
    print('selected0014_source_sha='+current+' unsupported_source_sha='+old, flush=True)


def _integration(archive=None, *, current0014):
    started = time.monotonic()
    owned = [
        PROJECT + "_cutover_" + name
        for name in ("pg_original", "pg_candidate", "redis_original", "redis_candidate")
    ]
    for kind in ("container", "network", "volume"):
        assert not call(
            [
                "/usr/bin/docker",
                kind,
                "ls",
                "-q",
                "--filter",
                "label=com.docker.compose.project=" + PROJECT,
            ]
        ).strip()
    assert not any(
        call(
            ["/usr/bin/docker", "volume", "ls", "-q", "--filter", "name=^" + name + "$"]
        ).strip()
        for name in owned
    )
    with f.installed_recovery(archive) as session:
        root = session.root
        # Preparation may read public repository source. Launcher children later
        # run under Landlock with the feature checkout denied.
        app = root / "old/app"
        assert app.parent.parent == root and str(root).startswith(
            "/tmp/birja-backup-test-"
        )
        shutil.rmtree(app)
        call(
            [
                "git",
                "-c",
                "safe.directory=" + str(ROOT),
                "clone",
                "--no-hardlinks",
                str(ROOT),
                str(app),
            ]
        )

        def git(*args):
            return call(["git", "-C", str(app), *args]).decode().strip()

        git("config", "user.email", "synthetic@example.invalid")
        git("config", "user.name", "Synthetic")
        old = git("rev-parse", "v0.3.1^{commit}")
        # Preserve the actual legacy0008 rollout/old-runtime rollback lane.
        # Only this private clone receives immutable v0.4.0 application/schema
        # bytes; reviewed current retained ops and build instructions remain.
        if not current0014:
            for directory in ("backend/app", "backend/alembic"):
                shutil.rmtree(app / directory)
            with tarfile.open(fileobj=io.BytesIO(f.source_git("archive", "v0.4.0", "backend/app", "backend/alembic"))) as legacy_archive:
                legacy_archive.extractall(app, filter="data")
            git("add", "backend/app", "backend/alembic")
        etc = root / "etc"
        etc.mkdir(mode=0o700)
        (root / "bin").mkdir(mode=0o700)
        (root / "home").mkdir(mode=0o700)
        (root / "tmp").mkdir(mode=0o700)
        (root / "web/releases/old").mkdir(parents=True)
        (root / "web/releases/old/index.html").write_text("synthetic old static\n")
        (root / "web/current").symlink_to(root / "web/releases/old")

        # A private TLS origin stands in for the host nginx boundary. Its API
        # health response is obtained from the actual backend container.
        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                if self.path == "/api/v1/health":
                    data = call(
                        dc
                        + [
                            "exec",
                            "-T",
                            "backend",
                            "python",
                            "-c",
                            "import urllib.request;print(urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health',timeout=3).read().decode())",
                        ],
                        env=compose_env,
                    )
                else:
                    data = (root / "web/current/index.html").read_bytes()
                self.send_response(200)
                self.end_headers()
                self.wfile.write(data)

        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        port = server.server_port
        replacements = {
            "/etc/nginx/certs/nist.one/fullchain.pem": str(
                etc / "db-tls/server/server.crt"
            ),
            "/srv/birja": str(app),
            "/var/lib/birja/backup": str(root / "state"),
            "/var/lib/birja/ops": str(root / "ops"),
            "/var/lib/birja/recovery": str(root / "host/var/lib/birja/recovery"),
            "/var/lib/birja": str(root / "history"),
            "/var/lock/birja-deploy.lock": str(root / "operation.lock"),
            "/usr/local/sbin/birja-deploy": str(root / "bin/birja-deploy"),
            "/var/www/birja": str(root / "web"),
            "/etc/birja": str(etc),
            "birja-prod": PROJECT,
            "/root": str(root / "home"),
        }
        names = [
            "deploy/deploy.sh",
            "deploy/deploy-entrypoint.sh",
            "deploy/datastore-bindings.py",
            "deploy/configure-db.sh",
            "deploy/provision-db-tls.sh",
            "docker-compose.prod.yml",
            "deploy/db-security.compose.yml",
        ]
        for name in names:
            text = (ROOT / name).read_text()
            text = re.sub(
                "|".join(re.escape(key) for key in replacements),
                lambda match: replacements[match[0]],
                text,
            )
            if name == "deploy/deploy-entrypoint.sh":
                text = isolate_entrypoint_environment(text, root)
            if name == "deploy/deploy.sh":
                text = text.replace("HOST=birja.nist.one", "HOST=postgres")
                text = text.replace(":443:127.0.0.1", ":" + str(port) + ":127.0.0.1")
                text = text.replace(
                    '"https://$HOST/', '"https://$HOST:' + str(port) + "/"
                )
                text = text.replace(
                    "curl -fsS", "curl --cacert " + str(etc / "db-tls/ca.crt") + " -fsS"
                )
                text = text.replace(
                    "recovery-gate \\\n",
                    "recovery-gate --synthetic " + str(session.config_path) + " \\\n",
                )
            if name == "deploy/configure-db.sh":
                text = text.replace(
                    '("birja-ops-test", "birja", "birja")',
                    '("birja-ops-test", "birja_source_test", "birja_ops_bootstrap")',
                )
            if name == "docker-compose.prod.yml":
                # Keep datastore guards/mounts/image/user/security intact. Only
                # fixture app egress/ports are isolated from host/Internet.
                text = text.replace(
                    "  app:\n    ipam:\n      config:\n        - subnet: 172.29.50.0/24",
                    "  app:\n    internal: true",
                )
                text = text.replace('"127.0.0.1:18000:8000"', '"127.0.0.1::8000"')
            (app / name).write_text(text)
        for name in ("check-nginx-config.sh", "install-nginx.sh", "cloudflare-ips.sh"):
            (app / "deploy" / name).write_text(
                "#!/bin/bash\n# Private origin fixture; no host nginx operation.\nexit 0\n"
            )
        for name in names + [
            "deploy/check-nginx-config.sh",
            "deploy/install-nginx.sh",
            "deploy/cloudflare-ips.sh",
        ]:
            if name.endswith(".sh"):
                (app / name).chmod(0o700)
        git(
            "add",
            *names,
            "deploy/check-nginx-config.sh",
            "deploy/install-nginx.sh",
            "deploy/cloudflare-ips.sh",
        )
        git("commit", "-m", "Relocate fixed synthetic host and origin endpoints")
        current = git("rev-parse", "HEAD")
        git("branch", "main", current)
        call(["git", "clone", "--bare", str(app), str(root / "origin")])
        git("remote", "set-url", "origin", str(root / "origin"))
        for role, char in (("app", "a"), ("scheduler", "b"), ("migrator", "c")):
            (etc / role).write_text(char * 64)
            (etc / role).chmod(0o600)
        roles = {
            "project": PROJECT,
            "db_name": "birja_source_test",
            "bootstrap": r.BOOT,
            "password_files": {
                role: str(etc / role) for role in ("app", "scheduler", "migrator")
            },
        }
        (etc / "db-roles.json").write_text(json.dumps(roles))
        (etc / "db-roles.json").chmod(0o600)
        env = {
            "POSTGRES_USER": r.BOOT,
            "POSTGRES_PASSWORD": "synthetic-ops-only",
            "POSTGRES_DB": "birja_source_test",
            "REDIS_PASSWORD": "synthetic-redis-only",
            "OTP_HMAC_SECRET": "synthetic-only-otp-secret-00000000000000",
            "JWT_SECRET": "synthetic-only-jwt-secret-00000000000000",
            "RESEND_API_KEY": "synthetic-unused",
            "EMAIL_FROM": "test@example.invalid",
        }
        for role, char in (("APP", "a"), ("SCHEDULER", "b"), ("MIGRATOR", "c")):
            env[role + "_DATABASE_URL"] = (
                "postgresql+asyncpg://birja_"
                + role.lower()
                + ":"
                + char * 64
                + "@postgres:5432/birja_source_test"
            )
        envfile = etc / "prod.env"
        envfile.write_text(
            "".join(key + "=" + value + "\n" for key, value in env.items())
        )
        envfile.chmod(0o600)
        original = root / "original.json"
        original.write_text(
            json.dumps(
                {
                    "services": {
                        "postgres": {
                            "image": PG_OLD,
                            "environment": {
                                **{
                                    k: v
                                    for k, v in env.items()
                                    if k.startswith("POSTGRES_")
                                },
                                "PGDATA": "/var/lib/postgresql/18/docker",
                                "POSTGRES_INITDB_ARGS": "--locale=en_US.utf8 --locale-provider=libc",
                            },
                            "volumes": [owned[0] + ":/var/lib/postgresql"],
                            "networks": ["data"],
                            "healthcheck": {
                                "test": [
                                    "CMD",
                                    "pg_isready",
                                    "-U",
                                    r.BOOT,
                                    "-d",
                                    "birja_source_test",
                                ],
                                "interval": "1s",
                                "retries": 60,
                            },
                        },
                        "redis": {
                            "image": REDIS_OLD,
                            "command": [
                                "redis-server",
                                "--requirepass",
                                env["REDIS_PASSWORD"],
                                "--appendonly",
                                "yes",
                                "--appendfsync",
                                "always",
                                "--maxmemory-policy",
                                "noeviction",
                            ],
                            "volumes": [owned[2] + ":/data"],
                            "networks": ["data"],
                            "healthcheck": {
                                "test": [
                                    "CMD-SHELL",
                                    "REDISCLI_AUTH=synthetic-redis-only redis-cli ping | grep PONG",
                                ],
                                "interval": "1s",
                                "retries": 30,
                            },
                        },
                    },
                    "volumes": {
                        name: {"external": True, "name": name}
                        for name in (owned[0], owned[2])
                    },
                    "networks": {"data": {"internal": True}},
                }
            )
        )
        original.chmod(0o600)
        dc0 = [
            "/usr/bin/docker",
            "compose",
            "--env-file",
            "/dev/null",
            "-p",
            PROJECT,
            "-f",
            str(original),
        ]
        # Keep the independently authenticated synthetic Compose bytes intact.
        # Its exec-only fixed project/service reaches the real selected source;
        # no recovery producer may use it to recreate this source container.
        dc = []
        extra_paths = []
        held = None
        try:
            for volume in owned:
                call(
                    [
                        "/usr/bin/docker",
                        "volume",
                        "create",
                        "--label",
                        "com.docker.compose.project=" + PROJECT,
                        volume,
                    ]
                )
            rows = json.loads(call(["/usr/bin/docker", "volume", "inspect", *owned]))
            byname = {row["Name"]: row for row in rows}
            binding = {"format": 1, "project": PROJECT, "volumes": {}}
            for logical, start in (("pgdata", 0), ("redisdata", 2)):
                binding["volumes"][logical] = {
                    kind: {
                        "name": owned[start + offset],
                        "created_at": byname[owned[start + offset]]["CreatedAt"],
                        "driver": "local",
                        "scope": "local",
                    }
                    for offset, kind in enumerate(("original", "candidate"))
                }
                extra_paths.append(Path(byname[owned[start + 1]]["Mountpoint"]).parent)
            (etc / "datastore-bindings.json").write_text(json.dumps(binding))
            (etc / "datastore-bindings.json").chmod(0o600)
            call(dc0 + ["up", "-d", "--wait"], timeout=120)
            seed = [
                "/usr/bin/docker",
                "run",
                "--rm",
                "-i",
                "--network",
                PROJECT + "_data",
            ]
            for key, value in {
                "ENV": "test",
                "DATABASE_URL": "postgresql+asyncpg://"
                + r.BOOT
                + ":synthetic-ops-only@postgres:5432/birja_source_test",
                "REDIS_URL": "redis://unused/0",
                "OTP_HMAC_SECRET": env["OTP_HMAC_SECRET"],
                "JWT_SECRET": env["JWT_SECRET"],
                "EMAIL_BACKEND": "console",
            }.items():
                seed += ["-e", key + "=" + value]
            call(
                seed + ["--entrypoint", "python", "birja-backend-test:phase05-07", "-"],
                f.SEED.encode(),
            )
            print("selected_cutover_originals_seeded=true", flush=True)

            def source_python(code, role=r.BOOT):
                password = 'synthetic-ops-only' if role == r.BOOT else 'c' * 64
                return call(seed + [
                    '-e', 'DATABASE_URL=postgresql+asyncpg://' + role + ':' + password + '@postgres:5432/birja_source_test',
                    '-v', str(app / 'backend/app') + ':/app/app:ro',
                    '-v', str(app / 'backend/alembic') + ':/app/alembic:ro',
                    '--entrypoint', 'python', 'birja-backend-test:phase05-07', '-'], code.encode())

            if current0014:
                source_python("from alembic import command\nfrom alembic.config import Config\ncommand.upgrade(Config('/app/alembic.ini'),'0013')")
                source_roles = source_role_config(root, roles)
                call(['bash', str(ROOT / 'deploy/configure-db.sh'), '--synthetic', str(source_roles), '--apply', '--approved-operation', 'populated-role-transition'])
                # Pre-TLS fixture clients use the existing all-a credential
                # convention; TLS provisioning below restores distinct secrets.
                # Source fixture programs select app/scheduler a*64 without TLS.
                query_roles = "ALTER ROLE birja_scheduler PASSWORD '" + 'a'*64 + "';"
                r.sql(dc0, query_roles, 'birja_source_test')
                runtime_saved = f.runtime_receipt_digest(source_python(f.runtime_program(seed=True), 'birja_migrator'))
                source_python("from alembic import command\nfrom alembic.config import Config\ncommand.upgrade(Config('/app/alembic.ini'),'0014')", 'birja_migrator')
                source_python(f.dividend_program(mode='prepare'), 'birja_migrator')
                dividend_saved = f.dividend_digest(source_python(f.dividend_program(mode='exercise'), 'birja_migrator'))
                # The unchanged clone verifier uses this fixed maintenance DB;
                # create it while preparing originals, before physical copies.
                r.sql(dc0, 'CREATE DATABASE birja_ops_test OWNER birja_ops_bootstrap', 'birja_source_test')
                original_canonical = r.canonical(dc0, 'birja_source_test')
                identity_tables = r.backup_module().identity_tables('0014')
                original_identity = {name:r.sql(dc0, 'SELECT last_value,is_called FROM '+name+'_id_seq', 'birja_source_test').strip() for name in identity_tables}

            def query(command, sql):
                return call(
                    command
                    + [
                        "exec",
                        "-T",
                        "postgres",
                        "psql",
                        "-XqAt",
                        "-v",
                        "ON_ERROR_STOP=1",
                        "-U",
                        r.BOOT,
                        "-d",
                        "birja_source_test",
                    ],
                    sql.encode(),
                ).strip()

            query(
                dc0,
                "CREATE COLLATION public.cutover_locale (provider=libc, locale='en_US.utf8'); CREATE SCHEMA transition_fixture; CREATE TABLE transition_fixture.cutover_probe(value text COLLATE public.cutover_locale PRIMARY KEY); INSERT INTO transition_fixture.cutover_probe VALUES ('ä'),('ß'),('Ω');",
            )

            def redis(command, *args, auth=True):
                return call(
                    command
                    + [
                        "exec",
                        "-T",
                        *(["-e", "REDISCLI_AUTH=synthetic-redis-only"] if auth else []),
                        "redis",
                        "redis-cli",
                        *args,
                    ]
                ).strip()

            assert (
                redis(dc0, "SET", "birja:cutover:proof", "selected-aof", "EX", "3600")
                == b"OK"
            )
            # Prepare TLS and install exact retained ops before fresh evidence.
            call(
                [
                    "bash",
                    str(app / "deploy/provision-db-tls.sh"),
                    "--production",
                    "--create",
                    "--approved-operation",
                    "production-db-tls",
                    "--approved-custody",
                    "owner-off-server-password-manager",
                ]
            )
            call(
                [
                    "bash",
                    str(app / "deploy/deploy-entrypoint.sh"),
                    "--install",
                    "--approved-operation",
                    "install-retained-deploy",
                    "--tested-source",
                    current,
                ]
            )
            release = (root / "ops/current").resolve()
            retained = {
                path: r.digest(path) for path in release.rglob("*") if path.is_file()
            }
            (root / "history").mkdir(mode=0o700)
            (root / "history/deploys.log").write_text(
                "t " + old + " " + str(root / "web/releases/old") + " v0.3.1\n"
                + ("t " + current + " " + str(root / "web/releases/old") + " main\n" if current0014 else '')
            )
            c = json.loads(session.config_path.read_text())
            c["recovery_files"] += [
                str(etc / "datastore-bindings.json"),
                str(etc / "prod.env"),
                str(etc / "db-roles.json"),
                str(etc / "custody/ca.key"),
                str(release / "MANIFEST.json"),
                *[str(etc / name) for name in ("app", "scheduler", "migrator")],
            ]
            session.config_path.write_text(json.dumps(c))
            print("selected_cutover_final_material_prepared=true", flush=True)
            held = (root / "operation.lock").open("w")
            fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)

            def target(argv, ok=True, env_extra=None):
                assert env_extra is None
                try:
                    return f.target(
                        root,
                        argv,
                        ok=ok,
                        allowed_files=extra_paths,
                        inherited=held.fileno(),
                    )
                except AssertionError as error:
                    if "datastore_bindings_failed" in str(error):
                        # Read-only diagnostic calls the unchanged module API;
                        # unlike its CLI catch, Python exposes the failing line.
                        diagnostic = """import importlib.util, subprocess, sys
s=importlib.util.spec_from_file_location('binding_diagnostic',sys.argv[1])
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
m.PROBES={key:'set -x\\n'+('cat /selected/appendonlydir/appendonly.aof.manifest >&2\\n' if key=='redisdata' else '')+value for key,value in m.PROBES.items()}
def command(argv):
 result=subprocess.run(argv,env=m.ENV,capture_output=True,check=False,timeout=45)
 if result.returncode: sys.stderr.buffer.write(result.stderr)
 m.require(result.returncode==0)
 return result.stdout
m.command=command
m.main(['--check-volumes'])
"""
                        result = f.target(
                            root,
                            [
                                "python3",
                                "-c",
                                diagnostic,
                                str(release / "deploy/datastore-bindings.py"),
                            ],
                            ok=False,
                            allowed_files=extra_paths,
                            inherited=held.fileno(),
                        )
                        print(result.stderr.decode(), flush=True)
                    raise

            def retained_shell(body):
                return target(
                    [
                        "bash",
                        "-c",
                        '. "$1"; exec 9<&"$2"; ' + body,
                        "_",
                        str(release / "deploy/deploy.sh"),
                        str(held.fileno()),
                    ]
                )

            # Required pre-start proof is real installed backup + exact restore.
            f.recovery_roundtrip(
                session,
                source_revision="0014" if current0014 else "0007",
                source_release=current if current0014 else old,
                inherited=held.fileno(),
            )
            call(dc0 + ["down"])

            def fingerprint(volume):
                data = call(
                    [
                        "/usr/bin/docker",
                        "run",
                        "--rm",
                        "--network",
                        "none",
                        "--read-only",
                        "--mount",
                        "type=volume,source=" + volume + ",target=/original,readonly",
                        "--entrypoint",
                        "sh",
                        r.REGISTRY_REF,
                        "-ec",
                        "find /original -type f -exec sha256sum '{}' ';' | sort",
                    ]
                )
                return hashlib.sha256(data).hexdigest()

            originals = {name: fingerprint(name) for name in (owned[0], owned[2])}
            for source, destination, owner in (
                (owned[0], owned[1], "70:70"),
                (owned[2], owned[3], "65532:65532"),
            ):
                call(
                    [
                        "/usr/bin/docker",
                        "run",
                        "--rm",
                        "--network",
                        "none",
                        "--read-only",
                        "--mount",
                        "type=volume,source=" + source + ",target=/original,readonly",
                        "--mount",
                        "type=volume,source=" + destination + ",target=/candidate",
                        "--entrypoint",
                        "sh",
                        r.REGISTRY_REF,
                        "-ec",
                        "cp -a /original/. /candidate/; chown -R "
                        + owner
                        + " /candidate",
                    ],
                    timeout=120,
                )
            launcher = root / "bin/birja-deploy"
            result = target([str(launcher), "--start-selected-datastores"])
            assert (
                b"selected_datastores_started=true writers_started=false"
                in result.stdout
            )
            print(
                "selected_cutover_real_retained_initial_start=true fresh_same_installed_archive=true tls_before_start=true",
                flush=True,
            )
            dc = [
                "/usr/bin/docker",
                "compose",
                "--env-file",
                str(envfile),
                "-p",
                PROJECT,
                "-f",
                str(release / "docker-compose.prod.yml"),
                "-f",
                str(release / "deploy/db-security.compose.yml"),
                "-f",
                str(root / "ops/datastore-volumes.json"),
            ]
            compose_env = {
                **r.ENV,
                "BIRJA_APP_DIR": str(app),
                "BIRJA_OPS_DIR": str(release),
                "BIRJA_MIGRATOR_CONTEXT": str(release / "backend"),
            }

            def compose(*args, data=None):
                return call(dc + list(args), data, env=compose_env)

            def selected_query(sql):
                return compose(
                    "exec",
                    "-T",
                    "postgres",
                    "psql",
                    "-XqAt",
                    "-v",
                    "ON_ERROR_STOP=1",
                    "-U",
                    r.BOOT,
                    "-d",
                    "birja_source_test",
                    data=sql.encode(),
                ).strip()

            selected_query("REINDEX DATABASE birja_source_test")
            selected_query(
                "ALTER COLLATION public.cutover_locale REFRESH VERSION; ALTER DATABASE birja_source_test REFRESH COLLATION VERSION"
            )
            # Real production role interface retains the identity guard.
            target(
                [
                    str(release / "deploy/configure-db.sh"),
                    "--production",
                    "--apply",
                    "--approved-operation",
                    "populated-role-transition",
                ]
            )
            before = compose("ps", "-q", "postgres", "redis").split()
            compose("up", "-d", "--wait", "--force-recreate", "postgres", "redis")
            assert compose("ps", "-q", "postgres", "redis").split() != before
            target(
                [
                    "python3",
                    str(release / "deploy/datastore-bindings.py"),
                    "--check-running",
                ]
            )

            def check_redis_state():
                assert (
                    compose(
                        "exec",
                        "-T",
                        "-e",
                        "REDISCLI_AUTH=synthetic-redis-only",
                        "redis",
                        "redis-cli",
                        "GET",
                        "birja:cutover:proof",
                    ).strip()
                    == b"selected-aof"
                )
                assert (
                    int(
                        compose(
                            "exec",
                            "-T",
                            "-e",
                            "REDISCLI_AUTH=synthetic-redis-only",
                            "redis",
                            "redis-cli",
                            "TTL",
                            "birja:cutover:proof",
                        )
                    )
                    > 0
                )
                assert b"NOAUTH" in compose(
                    "exec", "-T", "redis", "redis-cli", "GET", "birja:cutover:proof"
                )

            check_redis_state()
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(
                etc / "db-tls/server/server.crt", etc / "db-tls/server/server.key"
            )
            server.socket = context.wrap_socket(server.socket, server_side=True)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            # Current application deployment goes through the supported launcher;
            # source fetch is a private fixture-local Git remote, never origin.
            result = target([str(launcher)])
            assert b"Deploy complete" in result.stdout
            check_redis_state()
            if current0014:
                current0014_checks(
                    session=session, current=current, old=old, app=app,
                    root=root, launcher=launcher, target=target, git=git,
                    dc=dc, compose_env=compose_env, compose=compose,
                    originals=originals, fingerprint=fingerprint, retained=retained,
                    original_canonical=original_canonical, original_identity=original_identity,
                    runtime_saved=runtime_saved, dividend_saved=dividend_saved,
                    inherited=held.fileno(),
                )
                return
            assert selected_query("SELECT version_num FROM alembic_version") == b"0008"
            f.recovery_roundtrip(
                session,
                source_revision="0008",
                source_release=current,
                inherited=held.fileno(),
            )
            result = target([str(launcher), "--rollback"])
            assert b"Rolling back" in result.stdout and git("rev-parse", "HEAD") == old
            target(
                [
                    "python3",
                    str(release / "deploy/datastore-bindings.py"),
                    "--check-running",
                ]
            )
            check_redis_state()
            assert selected_query("SELECT version_num FROM alembic_version") == b"0008"
            assert selected_query("SELECT count(*) FROM transition_fixture.cutover_probe") == b"3"
            assert all(fingerprint(name) == value for name, value in originals.items())
            assert all(r.digest(path) == value for path, value in retained.items())
            f.recovery_roundtrip(
                session,
                source_revision="0008",
                source_release=old,
                inherited=held.fileno(),
            )
            print(
                "selected_cutover_force_recreate=true actual_old_app_rollback=true original_fingerprints_unchanged=true selected_revision_0008=true same_installed_archive_pre_post=true",
                flush=True,
            )
            print(
                f"selected_cutover_seconds={time.monotonic() - started:.3f}", flush=True
            )
        finally:
            server.server_close()
            if held is not None:
                held.close()
            if dc:
                call(dc + ["down", "--remove-orphans"], timeout=60, env=compose_env)
            else:
                call(dc0 + ["down", "--remove-orphans"], timeout=60)
            call(
                r.compose("birja-restore-check") + ["down", "-v", "--remove-orphans"],
                timeout=60,
            )
            for volume in owned:
                call(["/usr/bin/docker", "volume", "rm", volume])
            for kind in ("container", "network", "volume"):
                assert not call(
                    [
                        "/usr/bin/docker",
                        kind,
                        "ls",
                        "-q",
                        "--filter",
                        "label=com.docker.compose.project=" + PROJECT,
                    ]
                ).strip()
            print("selected_cutover_cleanup_complete=true", flush=True)
            if current0014:
                print('selected0014_cleanup_complete=true revision0014=true', flush=True)


if __name__ == "__main__":
    import argparse

    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument("--recovery-bundle")
    integration(parser.parse_args().recovery_bundle)
