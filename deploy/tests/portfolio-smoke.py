#!/usr/bin/env python3
"""Owned current0020 and immutable retained0017 verified-TLS smoke."""

import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import tarfile
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECT = "birja-portfolio-fixture-test"
PG = "cgr.dev/chainguard/postgres@sha256:adbf3d8db097696ed6e997b108b51393786be999c04d543502f8959e1bafa8de"


def load(name):
    spec = importlib.util.spec_from_file_location(
        name.replace("-", "_"), Path(__file__).with_name(name + ".py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_current_runtime(sources, env, *, run=subprocess.run):
    """Build the actual declared runtime from one authenticated Git context.

    A fresh CI runner must be able to create this image without any previous
    workstation image. Only the committed backend tree is sent to Docker;
    neither host source overlays nor an alternate dependency base are used.
    """
    commit = sources.git("rev-parse", "HEAD").decode().strip()
    if sources.git("diff", "--name-only", "HEAD", "--", "backend").strip():
        raise ValueError("current source must be frozen before image build")
    app_tree = sources.git("rev-parse", commit + ":backend/app").decode().strip()
    payload = sources.git("archive", commit, "backend")
    context = hashlib.sha256(payload).hexdigest()
    tag = "birja-portfolio-current:" + commit[:12] + "-" + context[:20]
    with tempfile.TemporaryDirectory(
        prefix="birja-portfolio-current-image-"
    ) as image_tmp:
        image_root = Path(image_tmp)
        with tarfile.open(fileobj=io.BytesIO(payload)) as archive:
            archive.extractall(image_root, filter="data")
        sources.verify_source_tree(image_root, payload)
        result = run(
            [
                "docker",
                "build",
                "--target",
                "runtime",
                "--label",
                "org.opencontainers.image.revision=" + commit,
                "-t",
                tag,
                str(image_root / "backend"),
            ],
            env=env,
            capture_output=True,
            timeout=600,
        )
        if result.returncode:
            raise AssertionError(
                "declared runtime image build failed: " + result.stderr.decode()[-1200:]
            )
        sources.verify_source_tree(image_root, payload)
    if (
        sources.git("rev-parse", "HEAD").decode().strip() != commit
        or sources.git("diff", "--name-only", "HEAD", "--", "backend").strip()
    ):
        raise ValueError("current source changed during image build")
    result = run(
        ["docker", "image", "inspect", tag], env=env, capture_output=True, timeout=30
    )
    if result.returncode:
        raise AssertionError("declared runtime image inspection failed")
    binding = sources.image_binding(
        json.loads(result.stdout),
        source_commit=commit,
        app_tree=app_tree,
        context_sha256=context,
    )
    result = run(
        ["docker", "image", "inspect", binding["id"]],
        env=env,
        capture_output=True,
        timeout=30,
    )
    if result.returncode:
        raise AssertionError("declared runtime immutable image missing")
    sources.verify_image(binding, json.loads(result.stdout))
    return binding


def build_selected_runtime(
    sources, env, *, revision, archive=None, archive_sha=None, run=subprocess.run
):
    profile = sources.profile_for(revision)
    if revision == "0020":
        return build_current_runtime(sources, env, run=run)
    if revision != "0017":
        raise ValueError("unsupported portfolio smoke schema")
    payload = sources.source_archive(
        "portfolio0017", archive=archive, archive_sha=archive_sha
    )
    context = hashlib.sha256(payload).hexdigest()
    tag = "birja-portfolio-retained:" + profile["commit"][:12] + "-" + context[:20]
    with tempfile.TemporaryDirectory(prefix="birja-portfolio-retained-image-") as tmp:
        root = Path(tmp)
        with tarfile.open(fileobj=io.BytesIO(payload)) as source:
            source.extractall(root, filter="data")
        sources.verify_source_tree(root, payload)
        result = run(
            [
                "docker",
                "build",
                "--target",
                "runtime",
                "--label",
                "org.opencontainers.image.revision=" + profile["commit"],
                "-t",
                tag,
                str(root / "backend"),
            ],
            env=env,
            capture_output=True,
            timeout=600,
        )
        if result.returncode:
            raise AssertionError("retained runtime image build failed")
        sources.verify_source_tree(root, payload)
    result = run(
        ["docker", "image", "inspect", tag], env=env, capture_output=True, timeout=30
    )
    if result.returncode:
        raise ValueError("retained runtime image missing")
    binding = sources.image_binding(
        json.loads(result.stdout),
        source_commit=profile["commit"],
        app_tree=profile["app_tree"],
        context_sha256=context,
    )
    result = run(
        ["docker", "image", "inspect", binding["id"]],
        env=env,
        capture_output=True,
        timeout=30,
    )
    if result.returncode:
        raise ValueError("retained immutable image missing")
    sources.verify_image(binding, json.loads(result.stdout))
    return binding


def selected_fixture(sources, revision, *, archive=None, archive_sha=None):
    sources.profile_for(revision)
    if revision == "0020":
        return load("portfolio-management-recovery-fixture")
    if revision != "0017":
        raise ValueError("unsupported portfolio fixture schema")
    payload = sources.source_archive(
        "portfolio0017", archive=archive, archive_sha=archive_sha
    )
    with tarfile.open(fileobj=io.BytesIO(payload)) as source:
        code = source.extractfile("deploy/tests/portfolio-execution-fixture.py").read()
    fixture = types.ModuleType("immutable_portfolio0017_fixture")
    fixture.__file__ = str(Path(__file__).with_name("portfolio-execution-fixture.py"))
    exec(compile(code, "<authenticated0017-fixture>", "exec"), fixture.__dict__)  # noqa: S102 - fixed archive hash authenticated before imports
    return fixture


def admitted_program(code, revision):
    """Read exact schema through verified TLS before application imports."""
    if revision not in ("0017", "0020"):
        raise ValueError("unsupported smoke source/schema")
    create = bool(re.search(r"^MODE\s*=\s*['\"]create['\"]", code, re.MULTILINE))
    prelude = (
        "SMOKE_REVISION=" + repr(revision) + "\nSMOKE_CREATE=" + repr(create) + "\n"
    )
    prelude += r"""
import asyncio,asyncpg,os,ssl
from urllib.parse import urlsplit,urlunsplit
async def smoke_admit():
 parts=urlsplit(os.environ['DATABASE_URL'].replace('postgresql+asyncpg://','postgresql://'))
 if parts.hostname!='postgres' or parts.port!=5432 or parts.username!='birja_migrator' or parts.path!='/birja_source_test' or parts.query:
  raise ValueError('owned smoke identity required before import')
 if "DATABASE='birja_restore_test'" in SMOKE_BODY:parts=parts._replace(path='/birja_restore_test')
 conn=await asyncpg.connect(urlunsplit(parts),ssl=ssl.create_default_context(cafile=os.environ['DATABASE_SSL_CA_FILE']))
 try:
  if SMOKE_CREATE:
   if await conn.fetchval("SELECT count(*) FROM pg_tables WHERE schemaname='public'"):
    raise ValueError('empty owned schema required before import')
  elif await conn.fetchval('SELECT version_num FROM alembic_version')!=SMOKE_REVISION:
   raise ValueError('selected source/schema mismatch before application import')
 finally:await conn.close()
asyncio.run(smoke_admit())
"""
    return "SMOKE_BODY=" + repr(code) + "\n" + prelude + code


def management_role_program(code):
    """Actual restricted clients verify replay and scheduler authority via TLS."""
    checks = r"""
   if MODE=='verify':
    from sqlalchemy import text
    for role in ('app','scheduler'):
     client=create_async_engine(url.set(username='birja_'+role,password=os.environ['FIXTURE_'+role.upper()+'_PASSWORD']),connect_args={'ssl':ssl.create_default_context(cafile=os.environ['DATABASE_SSL_CA_FILE'])})
     try:
      async with client.connect() as restricted:
       assert (await restricted.execute(text('SELECT session_user'))).scalar_one()=='birja_'+role
       from app.db.schema_contract import require_schema
       assert await require_schema(restricted)=='0020'
       if role=='app':
        initial=next(r for r in value['tables']['portfolio_creations'] if r['origin']=='initial')
        replay=(await restricted.execute(text("SELECT * FROM create_portfolio(:u,:k,'My portfolio','')"),{'u':initial['user_id'],'k':initial['creation_key']})).one()
        assert replay.replayed and replay.portfolio_id==initial['portfolio_id']
        assert not (await restricted.execute(text("SELECT has_table_privilege(current_user,'accounts','INSERT')"))).scalar_one()
       else:
        assert not (await restricted.execute(text("SELECT has_function_privilege(current_user,'initialize_portfolio(bigint)','EXECUTE')"))).scalar_one()
     finally:await client.dispose()
"""
    marker = "   print('portfolio_projection='"
    if marker not in code:
        raise ValueError("management projection boundary changed")
    return code.replace(marker, checks + "\n" + marker, 1)


def run(*, archive=None, archive_sha=None, cold=False, revision="0020"):
    sources = load("portfolio-sources")
    fixture = selected_fixture(
        sources, revision, archive=archive, archive_sha=archive_sha
    )
    if cold:
        if archive is None:
            raise ValueError("cold lane requires selected recovery archive")
        sources.verify_archive_binding(archive, archive_sha)
    env = {
        key: os.environ[key] for key in ("PATH", "HOME", "LANG") if key in os.environ
    }
    env["COMPOSE_DISABLE_ENV_FILE"] = "1"

    def call(argv, *, data=None, timeout=240, fail=False):
        result = subprocess.run(
            argv, input=data, env=env, capture_output=True, timeout=timeout
        )
        if (result.returncode == 0) == fail:
            raise AssertionError(
                "owned portfolio command failed: "
                + Path(argv[0]).name
                + "\n"
                + result.stderr.decode()[-2500:]
            )
        return result.stdout

    for kind in ("container", "network", "volume"):
        if call(
            [
                "docker",
                kind,
                "ls",
                "-q",
                "--filter",
                "label=com.docker.compose.project=" + PROJECT,
            ]
        ).strip():
            raise ValueError("refuse preexisting owned fixture resources")
    binding = build_selected_runtime(
        sources, env, revision=revision, archive=archive, archive_sha=archive_sha
    )
    commit = binding["source_commit"]
    if archive is not None:
        sources.record_image_binding(archive, "current" + revision, binding)
    with tempfile.TemporaryDirectory(prefix="birja-backup-test-portfolio-") as tmp:
        root = Path(tmp)
        root.chmod(0o700)
        immutable = root / "source-image-binding.json"
        with immutable.open("x") as stream:
            json.dump(binding, stream, sort_keys=True)
        immutable.chmod(0o400)
        call(
            [
                "bash",
                str(ROOT / "deploy/provision-db-tls.sh"),
                "--synthetic",
                str(root),
                "--create",
                "--approved-custody",
                "owner-off-server-password-manager",
            ]
        )
        hba = root / "hba"
        hba.mkdir(mode=0o755)
        hba.chmod(0o755)
        (hba / "pg_hba.conf").write_text(
            "local all all trust\nhostssl all all samenet scram-sha-256\nhostnossl all all all reject\n"
        )
        (hba / "pg_hba.conf").chmod(0o644)
        compose = root / "compose.json"
        compose.write_text(
            json.dumps(
                {
                    "name": PROJECT,
                    "services": {
                        "postgres": {
                            "image": PG,
                            "pull_policy": "never",
                            "user": "70:70",
                            "environment": {
                                "PGDATA": "/var/lib/postgresql/18/docker",
                                "POSTGRES_USER": "birja_ops_bootstrap",
                                "POSTGRES_PASSWORD": "synthetic-only-ops",
                                "POSTGRES_DB": "birja_source_test",
                            },
                            "tmpfs": [
                                "/var/lib/postgresql:size=268435456,uid=70,gid=70,mode=0750"
                            ],
                            "volumes": [
                                str(root / "db-tls/server")
                                + ":/run/birja/db-server:ro",
                                str(hba) + ":/run/birja/db-hba:ro",
                            ],
                            "command": [
                                "-c",
                                "ssl=on",
                                "-c",
                                "ssl_cert_file=/run/birja/db-server/server.crt",
                                "-c",
                                "ssl_key_file=/run/birja/db-server/server.key",
                                "-c",
                                "hba_file=/run/birja/db-hba/pg_hba.conf",
                            ],
                            "networks": ["isolated"],
                            "mem_limit": "512m",
                            "pids_limit": 128,
                            "healthcheck": {
                                "test": [
                                    "CMD-SHELL",
                                    "pg_isready -U birja_ops_bootstrap -d birja_source_test",
                                ],
                                "interval": "2s",
                                "timeout": "3s",
                                "retries": 30,
                            },
                        }
                    },
                    "networks": {"isolated": {"internal": True}},
                }
            )
        )
        dc = [
            "docker",
            "compose",
            "--env-file",
            "/dev/null",
            "-p",
            PROJECT,
            "-f",
            str(compose),
        ]
        clone_project = PROJECT + "-cold"
        clone_dc = [
            "docker",
            "compose",
            "--env-file",
            "/dev/null",
            "-p",
            clone_project,
            "-f",
            str(compose),
        ]
        for kind in ("container", "network", "volume"):
            if call(
                [
                    "docker",
                    kind,
                    "ls",
                    "-q",
                    "--filter",
                    "label=com.docker.compose.project=" + clone_project,
                ]
            ).strip():
                raise ValueError("refuse preexisting cold resources")
        client_network = PROJECT + "_isolated"
        passwords = {"app": "a" * 64, "scheduler": "b" * 64, "migrator": "c" * 64}
        try:
            call(dc + ["up", "-d", "--wait"], timeout=120)
            setup = "REVOKE CREATE ON SCHEMA public FROM PUBLIC;\n"
            for role, password in passwords.items():
                setup += (
                    "CREATE ROLE birja_"
                    + role
                    + " LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD '"
                    + password
                    + "';\n"
                )
            setup += "CREATE ROLE birja_action_operator NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS; GRANT USAGE,CREATE ON SCHEMA public TO birja_migrator;\n"
            call(
                dc
                + [
                    "exec",
                    "-T",
                    "postgres",
                    "psql",
                    "-XqAt",
                    "-v",
                    "ON_ERROR_STOP=1",
                    "-U",
                    "birja_ops_bootstrap",
                    "-d",
                    "birja_source_test",
                ],
                data=setup.encode(),
            )
            client_env = {
                "ENV": "test",
                "DATABASE_URL": "postgresql+asyncpg://birja_migrator:"
                + passwords["migrator"]
                + "@postgres:5432/birja_source_test",
                "DATABASE_SSL_CA_FILE": "/run/birja/db-ca.crt",
                "REDIS_URL": "redis://localhost:6379/0",
                "OTP_HMAC_SECRET": "synthetic-portfolio-fixture-otp-" + "x" * 32,
                "JWT_SECRET": "synthetic-portfolio-fixture-jwt-" + "y" * 32,
                "EMAIL_BACKEND": "console",
                "PRICE_SOURCE": "fake",
                "FIXTURE_APP_PASSWORD": passwords["app"],
                "FIXTURE_SCHEDULER_PASSWORD": passwords["scheduler"],
            }

            def transport(code):
                if revision == "0020":
                    code = management_role_program(code)
                code = admitted_program(code, revision)
                sources.verify_image(
                    binding,
                    json.loads(call(["docker", "image", "inspect", binding["id"]])),
                )
                if revision == "0020" and (
                    sources.git("rev-parse", "HEAD").decode().strip() != commit
                    or sources.git(
                        "diff", "--name-only", "HEAD", "--", "backend"
                    ).strip()
                ):
                    raise ValueError("current source drift")
                if archive is not None:
                    sources.verify_archive_binding(archive, archive_sha)
                argv = [
                    "docker",
                    "run",
                    "--rm",
                    "-i",
                    "--network",
                    client_network,
                    "-v",
                    str(root / "db-tls/ca.crt") + ":/run/birja/db-ca.crt:ro",
                ]
                for key, value in client_env.items():
                    argv += ["-e", key + "=" + value]
                argv += ["--entrypoint", "python", binding["id"], "-"]
                output = call(argv, data=code.encode())
                rows = [
                    line.split(b"=", 1)[1]
                    for line in output.splitlines()
                    if line.startswith(b"portfolio_projection=")
                ]
                if (
                    len(rows) != 1
                    or b"portfolio_verified_tls=true" not in output.splitlines()
                ):
                    raise AssertionError("missing actual verified TLS projection")
                return json.loads(rows[0])

            fixture.main(["create"], transport=transport)
            expected = root / "immutable-before.json"
            digest = fixture.main(
                ["projection", "--snapshot", str(expected)], transport=transport
            )
            expected.chmod(0o400)
            fixture.main(["verify"], transport=transport)
            fixture.main(
                ["compare", "--snapshot", str(expected), "--expected-sha256", digest],
                transport=transport,
            )
            if cold:
                # One immutable pre-backup oracle, one encrypted repository,
                # and a genuinely new server after the source is destroyed.
                import shutil

                r = load_recovery()
                manifest = r.canonical(dc, "birja_source_test")
                r.recovery_contract().validate_manifest(manifest)
                stage = root / "backup-input"
                stage.mkdir(mode=0o700)
                dump = call(
                    dc
                    + [
                        "exec",
                        "-T",
                        "postgres",
                        "pg_dump",
                        "-U",
                        "birja_migrator",
                        "-d",
                        "birja_source_test",
                        "--format=custom",
                        "--no-owner",
                        "--no-acl",
                    ]
                )
                (stage / "database.dump").write_bytes(dump)
                (stage / "manifest.json").write_text(
                    json.dumps(manifest, sort_keys=True)
                )
                shutil.copyfile(archive, stage / "recovery.tar")
                password = root / "restic-password"
                password.write_text(os.urandom(32).hex())
                password.chmod(0o600)
                restic = Path("/tmp/birja-test-tools/restic-0.19.1/restic")
                if r.digest(restic) != r.RESTIC_SHA:
                    raise ValueError("unverified local restic")
                restic_args = [
                    str(restic),
                    "--repo",
                    str(root / "repository"),
                    "--password-file",
                    str(password),
                    "--no-cache",
                ]
                call(restic_args + ["init"])
                # Relative paths are fixed: no host/private path may enter backup.
                result = subprocess.run(
                    restic_args + ["backup", "--json", "."],
                    cwd=stage,
                    env=env,
                    capture_output=True,
                    check=True,
                    timeout=180,
                )
                rows = [json.loads(line) for line in result.stdout.splitlines()]
                ids = [
                    row["snapshot_id"]
                    for row in rows
                    if row.get("message_type") == "summary"
                ]
                if len(ids) != 1 or not re.fullmatch("[0-9a-f]{64}", ids[0]):
                    raise ValueError("missing exact encrypted snapshot")
                hashes = {p.name: r.digest(p) for p in stage.iterdir()}
                shutil.rmtree(stage)
                call(dc + ["down", "-v", "--remove-orphans"])
                call(restic_args + ["check", "--read-data"])
                recovered = root / "cold-restored"
                call(
                    restic_args
                    + ["restore", ids[0], "--target", str(recovered), "--verify"]
                )
                if {p.name: r.digest(p) for p in recovered.iterdir()} != hashes:
                    raise ValueError("encrypted cold payload changed")
                sources.verify_archive_binding(recovered / "recovery.tar", archive_sha)
                call(clone_dc + ["up", "-d", "--wait"])
                r.sql(clone_dc, "CREATE DATABASE birja_ops_test;", "birja_source_test")
                with r.restored(clone_dc, (recovered / "database.dump").read_bytes()):
                    r.verify(
                        clone_dc, json.loads((recovered / "manifest.json").read_text())
                    )
                    # Only the authenticated migration reader receives a login;
                    # application/scheduler/definer ACLs remain quarantined.
                    r.sql(
                        clone_dc,
                        "ALTER ROLE birja_migrator LOGIN PASSWORD '"
                        + passwords["migrator"]
                        + "';",
                        "birja_ops_test",
                    )
                    client_network = clone_project + "_isolated"
                    fixture.main(
                        [
                            "compare",
                            "--database",
                            "birja_restore_test",
                            "--snapshot",
                            str(expected),
                            "--expected-sha256",
                            digest,
                        ],
                        transport=transport,
                    )
                print(
                    "actual_current"
                    + revision
                    + "_encrypted_cold_restore=true source_destroyed=true immutable_before_oracle=true quarantine=true",
                    flush=True,
                )
            assert json.loads(immutable.read_text()) == binding
            print(
                "actual_current"
                + revision
                + "_portfolio_tls_restricted_roles=true immutable_snapshot_compare=true",
                flush=True,
            )
        finally:
            call(dc + ["down", "-v", "--remove-orphans"], timeout=120)
            call(clone_dc + ["down", "-v", "--remove-orphans"], timeout=120)
            for kind in ("container", "network", "volume"):
                for project in (PROJECT, clone_project):
                    if call(
                        [
                            "docker",
                            kind,
                            "ls",
                            "-q",
                            "--filter",
                            "label=com.docker.compose.project=" + project,
                        ]
                    ).strip():
                        raise AssertionError("owned portfolio resources leaked")


def load_recovery():
    spec = importlib.util.spec_from_file_location(
        "portfolio_cold_recovery", ROOT / "deploy/verify-restore.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    run()
