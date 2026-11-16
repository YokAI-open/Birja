#!/usr/bin/env python3
"""Owned current0017 verified-TLS smoke, never production configuration."""

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECT = "birja-portfolio-fixture-test"
PG = "cgr.dev/chainguard/postgres@sha256:adbf3d8db097696ed6e997b108b51393786be999c04d543502f8959e1bafa8de"


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), Path(__file__).with_name(name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run():
    fixture, sources = load("portfolio-execution-fixture"), load("portfolio-sources")
    env = {key: os.environ[key] for key in ("PATH", "HOME", "LANG") if key in os.environ}
    env["COMPOSE_DISABLE_ENV_FILE"] = "1"

    def call(argv, *, data=None, timeout=240, fail=False):
        result = subprocess.run(argv, input=data, env=env, capture_output=True, timeout=timeout)
        if (result.returncode == 0) == fail:
            raise AssertionError("owned portfolio command failed: " + Path(argv[0]).name
                                 + "\n" + result.stderr.decode()[-2500:])
        return result.stdout

    for kind in ("container", "network", "volume"):
        if call(["docker", kind, "ls", "-q", "--filter", "label=com.docker.compose.project=" + PROJECT]).strip():
            raise ValueError("refuse preexisting owned fixture resources")
    commit = sources.git("rev-parse", "HEAD").decode().strip()
    app_tree = sources.git("rev-parse", "HEAD:backend/app").decode().strip()
    if sources.git("diff", "--name-only", "HEAD", "--", "backend").strip():
        raise ValueError("current source must be frozen before image build")
    context = hashlib.sha256(sources.git("archive", "HEAD", "backend")).hexdigest()
    tag = "birja-portfolio-fixture:" + context[:20]
    # Smoke-only image: reuse the already approved exact dependency runtime.
    # Final declared Dockerfile rebuild/scans remain the separate Plan27 gate.
    cached = "sha256:e5c153f11416842a3cbd7f34c1fe9c7d3f4dec35df8478fd22fbf023d1737aec"
    locked = subprocess.run(["uv", "export", "--offline", "--locked", "--no-default-groups",
        "--no-hashes", "--no-emit-project", "--format", "requirements-txt"], cwd=ROOT / "backend",
        env={**env, "UV_CACHE_DIR": "/tmp/birja-portfolio-smoke-uv"}, capture_output=True,
        check=True, timeout=30).stdout.decode()
    expected = dict(re.findall(r"^([a-z0-9-]+)==([^ ;\n]+)", locked, re.M))
    installed = json.loads(call(["docker", "run", "--rm", "--entrypoint", "python", cached,
        "-c", "import importlib.metadata,json;print(json.dumps({d.metadata['Name'].lower().replace('_','-'):d.version for d in importlib.metadata.distributions()}))"]))
    if expected != installed:
        raise ValueError("cached runtime exact locked distribution set/version mismatch")
    # The legacy builder resolves an exact local image ID without a registry
    # lookup. This creates a new content ID; it never retags the cached image.
    with tempfile.TemporaryDirectory(prefix="birja-portfolio-image-") as image_tmp:
        image_root = Path(image_tmp)
        import io
        import tarfile
        with tarfile.open(fileobj=io.BytesIO(sources.git("archive", "HEAD", "backend"))) as source:
            source.extractall(image_root, filter="data")
        dockerfile = image_root / "Smoke.Dockerfile"
        dockerfile.write_text("FROM " + cached + "\nUSER root\nRUN rm -rf /app/app /app/alembic\n"
            "COPY --chown=1001:1001 app /app/app\nCOPY --chown=1001:1001 alembic /app/alembic\n"
            "COPY --chown=1001:1001 alembic.ini /app/alembic.ini\nUSER app\n")
        result = subprocess.run(["docker", "build", "--network=none", "--label",
            "org.opencontainers.image.revision=" + commit, "-f", str(dockerfile), "-t", tag,
            str(image_root / "backend")], env={**env, "DOCKER_BUILDKIT": "0"}, capture_output=True, timeout=180)
        if result.returncode:
            raise AssertionError("frozen no-install smoke image failed: " + result.stderr.decode()[-1200:])
    inspect = json.loads(call(["docker", "image", "inspect", tag]))
    binding = sources.image_binding(inspect, source_commit=commit, app_tree=app_tree, context_sha256=context)
    with tempfile.TemporaryDirectory(prefix="birja-backup-test-portfolio-") as tmp:
        root = Path(tmp)
        root.chmod(0o700)
        immutable = root / "source-image-binding.json"
        with immutable.open("x") as stream:
            json.dump(binding, stream, sort_keys=True)
        immutable.chmod(0o400)
        call(["bash", str(ROOT / "deploy/provision-db-tls.sh"), "--synthetic", str(root),
              "--create", "--approved-custody", "owner-off-server-password-manager"])
        hba = root / "hba"
        hba.mkdir(mode=0o755)
        hba.chmod(0o755)
        (hba / "pg_hba.conf").write_text("local all all trust\nhostssl all all samenet scram-sha-256\nhostnossl all all all reject\n")
        (hba / "pg_hba.conf").chmod(0o644)
        compose = root / "compose.json"
        compose.write_text(json.dumps({"name": PROJECT, "services": {"postgres": {
            "image": PG, "pull_policy": "never", "user": "70:70",
            "environment": {"PGDATA": "/var/lib/postgresql/18/docker", "POSTGRES_USER": "birja_ops_bootstrap",
                            "POSTGRES_PASSWORD": "synthetic-only-ops", "POSTGRES_DB": "birja_source_test"},
            "tmpfs": ["/var/lib/postgresql:size=268435456,uid=70,gid=70,mode=0750"],
            "volumes": [str(root / "db-tls/server") + ":/run/birja/db-server:ro", str(hba) + ":/run/birja/db-hba:ro"],
            "command": ["-c", "ssl=on", "-c", "ssl_cert_file=/run/birja/db-server/server.crt",
                        "-c", "ssl_key_file=/run/birja/db-server/server.key", "-c", "hba_file=/run/birja/db-hba/pg_hba.conf"],
            "networks": ["isolated"], "mem_limit": "512m", "pids_limit": 128,
            "healthcheck": {"test": ["CMD-SHELL", "pg_isready -U birja_ops_bootstrap -d birja_source_test"],
                            "interval": "2s", "timeout": "3s", "retries": 30}}},
            "networks": {"isolated": {"internal": True}}}))
        dc = ["docker", "compose", "--env-file", "/dev/null", "-p", PROJECT, "-f", str(compose)]
        passwords = {"app": "a" * 64, "scheduler": "b" * 64, "migrator": "c" * 64}
        try:
            call(dc + ["up", "-d", "--wait"], timeout=120)
            setup = "REVOKE CREATE ON SCHEMA public FROM PUBLIC;\n"
            for role, password in passwords.items():
                setup += "CREATE ROLE birja_" + role + " LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD '" + password + "';\n"
            setup += "CREATE ROLE birja_action_operator NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS; GRANT USAGE,CREATE ON SCHEMA public TO birja_migrator;\n"
            call(dc + ["exec", "-T", "postgres", "psql", "-XqAt", "-v", "ON_ERROR_STOP=1",
                       "-U", "birja_ops_bootstrap", "-d", "birja_source_test"], data=setup.encode())
            client_env = {
                "ENV": "test", "DATABASE_URL": "postgresql+asyncpg://birja_migrator:" + passwords["migrator"] + "@postgres:5432/birja_source_test",
                "DATABASE_SSL_CA_FILE": "/run/birja/db-ca.crt", "REDIS_URL": "redis://localhost:6379/0",
                "OTP_HMAC_SECRET": "synthetic-portfolio-fixture-otp-" + "x" * 32,
                "JWT_SECRET": "synthetic-portfolio-fixture-jwt-" + "y" * 32,
                "EMAIL_BACKEND": "console", "PRICE_SOURCE": "fake",
                "FIXTURE_APP_PASSWORD": passwords["app"], "FIXTURE_SCHEDULER_PASSWORD": passwords["scheduler"],
            }

            def transport(code):
                sources.verify_image(binding, json.loads(call(["docker", "image", "inspect", binding["id"]])))
                if sources.git("diff", "--name-only", "HEAD", "--", "backend").strip():
                    raise ValueError("current source drift")
                argv = ["docker", "run", "--rm", "-i", "--network", PROJECT + "_isolated",
                        "-v", str(root / "db-tls/ca.crt") + ":/run/birja/db-ca.crt:ro"]
                for key, value in client_env.items():
                    argv += ["-e", key + "=" + value]
                argv += ["--entrypoint", "python", binding["id"], "-"]
                output = call(argv, data=code.encode())
                rows = [line.split(b"=", 1)[1] for line in output.splitlines() if line.startswith(b"portfolio_projection=")]
                if len(rows) != 1 or b"portfolio_verified_tls=true" not in output.splitlines():
                    raise AssertionError("missing actual verified TLS projection")
                return json.loads(rows[0])

            fixture.main(["create"], transport=transport)
            expected = root / "immutable-before.json"
            digest = fixture.main(["projection", "--snapshot", str(expected)], transport=transport)
            fixture.main(["verify"], transport=transport)
            fixture.main(["compare", "--snapshot", str(expected), "--expected-sha256", digest], transport=transport)
            assert json.loads(immutable.read_text()) == binding
            print("actual_current0017_portfolio_tls_restricted_roles=true immutable_snapshot_compare=true", flush=True)
        finally:
            call(dc + ["down", "-v", "--remove-orphans"], timeout=120)
            for kind in ("container", "network", "volume"):
                if call(["docker", kind, "ls", "-q", "--filter", "label=com.docker.compose.project=" + PROJECT]).strip():
                    raise AssertionError("owned portfolio resources leaked")


if __name__ == "__main__":
    run()
