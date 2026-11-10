#!/usr/bin/env python3
"""Serial private retained-launcher proof; only fixed synthetic Docker projects."""

import fcntl
import hashlib
import http.server
import importlib.util
import json
import os
import re
import shutil
import ssl
import subprocess
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
                "CREATE COLLATION public.cutover_locale (provider=libc, locale='en_US.utf8'); CREATE TABLE public.cutover_probe(value text COLLATE public.cutover_locale PRIMARY KEY); INSERT INTO cutover_probe VALUES ('ä'),('ß'),('Ω');",
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
                source_revision="0007",
                source_release=old,
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
            assert selected_query("SELECT count(*) FROM cutover_probe") == b"3"
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


if __name__ == "__main__":
    import argparse

    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument("--recovery-bundle")
    integration(parser.parse_args().recovery_bundle)
