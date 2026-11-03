#!/usr/bin/env python3
"""Independent synthetic PG18 fixture; never imports application test fixtures."""

import argparse
import copy
import ctypes
import fcntl
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "recovery", ROOT / "deploy/verify-restore.py"
)
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)

SEED = r"""
import asyncio, uuid
from datetime import datetime, UTC
from decimal import Decimal
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import Settings
from app.services.accounts import get_or_create_user
from app.services.auth import start_session
from app.services.trading import execute, Order
command.upgrade(Config('/app/alembic.ini'), '0007')
async def seed():
 s=Settings()
 engine=create_async_engine(s.database_url)
 session=async_sessionmaker(engine,expire_on_commit=False)
 async with session() as db:
  uid,new=await get_or_create_user(db,'synthetic-recovery@example.invalid')
  assert new
  await start_session(db,uid,s)
  await db.execute(text("INSERT INTO prices(coin_id,mid,as_of,source) SELECT id,12345.12345678,now(),'fake' FROM coins WHERE symbol='BTC'"))
  await db.commit()
  key=uuid.UUID('11111111-1111-4111-8111-111111111111')
  order=Order('BTC','buy','usd',Decimal('100.00'))
  fill,new=await execute(db,user_id=uid,order=order,expected_mid=Decimal('12345.12345678'),idempotency_key=key,settings=s)
  assert new and fill.cash_after==Decimal('9900.00')
  replay,new=await execute(db,user_id=uid,order=order,expected_mid=Decimal('12345.12345678'),idempotency_key=key,settings=s)
  assert not new and replay.trade_id==fill.trade_id
  await execute(db,user_id=uid,order=Order('BTC','sell','quantity',Decimal('0.00010000')),expected_mid=Decimal('12345.12345678'),idempotency_key=uuid.uuid4(),settings=s)
  await db.execute(text("UPDATE users SET created_at='2026-01-02T03:04:05.123456Z'"))
  await db.commit()
 await engine.dispose()
asyncio.run(seed())
print('seed_services=true buy_sell_replay=true revision=0007')
"""


def restrict_to_old_host(root, allowed_files=()):
    """Landlock denies the entire feature checkout to target launcher children.

    This is a local synthetic test boundary; no mounts or new executable.
    A missing/unsupported kernel facility fails the rehearsal.
    """
    libc = ctypes.CDLL(None, use_errno=True)
    handled = (1 << 13) - 1

    class Ruleset(ctypes.Structure):
        _fields_ = [("handled_access_fs", ctypes.c_uint64)]

    class Rule(ctypes.Structure):
        _pack_ = 1
        _fields_ = [("allowed_access", ctypes.c_uint64), ("parent_fd", ctypes.c_int)]

    fd = libc.syscall(444, ctypes.byref(Ruleset(handled)), 8, 0)
    if fd < 0:
        raise OSError("Landlock unavailable")
    try:
        for path in [
            str(root),
            "/usr",
            "/bin",
            "/lib",
            "/lib64",
            "/proc",
            "/dev",
            "/run",
            "/etc/ssl",
            "/etc/ld.so.cache",
            "/etc/passwd",
            "/etc/group",
            "/etc/nsswitch.conf",
            *[str(p) for p in allowed_files],
        ]:
            if not Path(path).exists():
                continue
            pfd = os.open(path, os.O_PATH | os.O_CLOEXEC)
            try:
                access = handled if Path(path).is_dir() else 7
                if libc.syscall(445, fd, 1, ctypes.byref(Rule(access, pfd)), 0) < 0:
                    raise OSError("Landlock rule")
            finally:
                os.close(pfd)
        if libc.prctl(38, 1, 0, 0, 0) or libc.syscall(446, fd, 0):
            raise OSError("Landlock restriction")
    finally:
        os.close(fd)


def target(root, argv, ok=True, allowed_files=()):
    result = subprocess.run(
        argv,
        check=False,
        env={**r.ENV, "HOME": str(root)},
        cwd=root / "old/app",
        capture_output=True,
        timeout=180,
        preexec_fn=lambda: restrict_to_old_host(root, allowed_files),
    )
    if ok:
        assert result.returncode == 0, result.stdout.decode() + result.stderr.decode()
    else:
        assert result.returncode != 0, "negative control passed"
    return result


def options(args):
    p = argparse.ArgumentParser()
    p.add_argument("--backup-restore", action="store_true")
    p.add_argument("--roles", action="store_true")
    p.add_argument("--recovery-bundle")
    p.add_argument("--self-test-recovery-bundle-inputs", action="store_true")
    a = p.parse_args(args)
    assert sum((a.backup_restore, a.roles, a.self_test_recovery_bundle_inputs)) == 1
    assert args.count("--roles") <= 1
    assert not a.roles or a.recovery_bundle is None
    assert args.count("--backup-restore") <= 1 and args.count("--recovery-bundle") <= 1
    assert a.recovery_bundle is None or bool(a.recovery_bundle)
    if a.recovery_bundle:
        archive = r.synthetic_path(a.recovery_bundle)
        sha = r.private(str(archive) + ".sha256").read_text().strip()
        r.bundle_verify(archive, sha)
    return a


def input_self_test():
    for args in [
        [],
        ["--backup-restore", "--recovery-bundle"],
        ["--backup-restore", "--recovery-bundle", ""],
        ["--backup-restore", "--recovery-bundle", "/srv/birja/a"],
        ["--backup-restore", "--recovery-bundle", "/tmp/missing"],
        ["--backup-restore", "--recovery-bundle", "x", "--recovery-bundle", "y"],
        ["--backup-restore", "--unknown"],
        ["--backup-restore", "--backup-restore"],
    ]:
        try:
            options(args)
        except (SystemExit, AssertionError, ValueError, OSError):
            continue
        raise AssertionError("bad input accepted")
    with tempfile.TemporaryDirectory(prefix="birja-backup-test-") as tmp:
        root = Path(tmp)
        root.chmod(0o700)
        payload = {name: b"fixture" for name in r.CORE}
        payload.update(
            {
                "tools/restic": b"not-approved-binary",
                "images/postgres.tar": b"not-image",
                "provenance/verified.json": b"{}",
            }
        )
        for name in r.PROVENANCE:
            payload["provenance/" + name] = b"not-official"
        inventory = {
            "files": sorted(payload),
            "units": [],
            "image_id": r.IMAGE_ID,
            "restic_sha256": r.RESTIC_SHA,
        }

        def create(change):
            files = dict(payload)
            files["INVENTORY.json"] = json.dumps(inventory).encode()
            files["SHA256SUMS"] = "".join(
                __import__("hashlib").sha256(value).hexdigest() + "  " + name + "\n"
                for name, value in sorted(files.items())
            ).encode()
            if change == "extra":
                files["deploy/deploy.sh"] = b"not allowed"
            if change == "missing":
                del files["deploy/backup-snapshot.py"]
            if change == "checksum":
                files["deploy/backup.sh"] = b"changed"
            if change == "traversal":
                files["../outside"] = b"escape"
            if change == "absolute":
                files["/outside"] = b"escape"
            if change == "inventory":
                files["INVENTORY.json"] = b"{}"
            path = root / "input.tar"
            with tarfile.open(path, "w") as t:
                for name, value in files.items():
                    m = tarfile.TarInfo(name)
                    m.mode = 0o600
                    m.size = len(value)
                    if change == "symlink" and name == "deploy/backup.sh":
                        m.type = tarfile.SYMTYPE
                        m.linkname = "/outside"
                        m.size = 0
                    if change == "hardlink" and name == "deploy/backup.sh":
                        m.type = tarfile.LNKTYPE
                        m.linkname = "deploy/restore-check.sh"
                        m.size = 0
                    t.addfile(m, __import__("io").BytesIO(value))
            path.chmod(0o600)
            (root / "input.tar.sha256").write_text(r.digest(path) + "\n")
            (root / "input.tar.sha256").chmod(0o600)
            return path

        saved_call = r.call

        def forbidden(*args, **kw):
            raise AssertionError("side effect reached")

        r.call = forbidden
        try:
            for change in [
                "extra",
                "missing",
                "checksum",
                "traversal",
                "absolute",
                "inventory",
                "symlink",
                "hardlink",
                "provenance",
            ]:
                path = create(change)
                try:
                    options(["--backup-restore", "--recovery-bundle", str(path)])
                except (ValueError, KeyError, OSError):
                    pass
                else:
                    raise AssertionError("invalid archive accepted: " + change)
            path = create("extra")
            (root / "input.tar.sha256").write_text("0" * 64)
            try:
                options(["--backup-restore", "--recovery-bundle", str(path)])
            except ValueError:
                pass
            else:
                raise AssertionError("wrong approval SHA accepted")
            link = root / "link.tar"
            link.symlink_to(path)
            try:
                options(["--backup-restore", "--recovery-bundle", str(link)])
            except ValueError:
                pass
            else:
                raise AssertionError("symlink path accepted")
            path.chmod(0o666)
            try:
                options(["--backup-restore", "--recovery-bundle", str(path)])
            except ValueError:
                pass
            else:
                raise AssertionError("writable archive accepted")
        finally:
            r.call = saved_call
    print("runner_input_rejections=20 docker_calls=0 package_calls=0 install_calls=0")


def config(root, release):
    q = {
        "observed_at": int(time.time()),
        "storage_limit_bytes": 500000000,
        "visible_bytes": 0,
        "hidden_bytes": 0,
        "unfinished_bytes": 0,
        "other_bytes": 0,
        "upload_reserve_bytes": 10000000,
        "repack_reserve_bytes": 10000000,
        "download_remaining_bytes": 100000000,
        "request_remaining": 10000,
        "request_reserve": 1000,
        "free_controls_verified": True,
        "dedicated_repository": True,
    }
    c = {
        "source_project": "birja-ops-test",
        "source_compose": str(root / "old/docker-compose.ops-test.yml"),
        "state_dir": str(root / "state"),
        "restic_binary": str(release / "tools/restic"),
        "docker_binary": str(root / "docker"),
        "repository": str(root / "repository"),
        "password_file": str(root / "password"),
        "recovery_files": [str(root / "credentials")],
        "release": r.call(["git", "rev-parse", "v0.3.1"]).decode().strip(),
        "db_user": r.BOOT,
        "db_name": "birja_source_test",
        "max_stage_bytes": 10000000,
        "timeout_seconds": 120,
        "freshness_seconds": 93600,
        "quota": q,
    }
    (root / "config").write_text(json.dumps(c))
    (root / "config").chmod(0o600)
    return c


def roundtrip(archive_arg=None):
    dc = r.compose()
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="birja-backup-test-") as tmp:
        root = Path(tmp)
        root.chmod(0o700)
        archive = Path(archive_arg) if archive_arg else root / "recovery.tar"
        if not archive_arg:
            r.bundle_package(archive)
        sha = r.private(str(archive) + ".sha256").read_text().strip()
        r.bundle_verify(archive, sha)
        try:
            r.call(dc + ["up", "-d", "--wait"])
            r.check_running(dc)
            r.sql(dc, "CREATE DATABASE birja_source_test;", "birja_ops_test")
            env = [
                "-e",
                "ENV=test",
                "-e",
                "DATABASE_URL=postgresql+asyncpg://birja_ops_bootstrap:synthetic-ops-only@postgres:5432/birja_source_test",
                "-e",
                "REDIS_URL=redis://localhost:6379/0",
                "-e",
                "OTP_HMAC_SECRET=synthetic-only-otp-secret-00000000000000",
                "-e",
                "JWT_SECRET=synthetic-only-jwt-secret-00000000000000",
                "-e",
                "EMAIL_BACKEND=console",
                "-e",
                "PRICE_SOURCE=fake",
            ]
            print(
                r.call(
                    [
                        "docker",
                        "run",
                        "--rm",
                        "-i",
                        "--network",
                        "birja-ops-test_isolated",
                        *env,
                        "--entrypoint",
                        "python",
                        "birja-backend-test:phase05-07",
                        "-",
                    ],
                    SEED.encode(),
                )
                .decode()
                .strip()
            )
            old = root / "old"
            old.mkdir(mode=0o700)
            app = old / "app"
            app.mkdir(mode=0o700)
            old_tar = r.call(["git", "archive", "v0.3.1"])
            with tarfile.open(fileobj=__import__("io").BytesIO(old_tar)) as t:
                t.extractall(app, filter="data")
            shutil.copyfile(
                ROOT / "docker-compose.ops-test.yml",
                old / "docker-compose.ops-test.yml",
            )
            (old / "docker-compose.ops-test.yml").chmod(0o600)
            for name in ["password", "credentials"]:
                (root / name).write_text("synthetic-only")
                (root / name).chmod(0o600)
            unchanged = {
                str(p.relative_to(root)): r.digest(p)
                for p in old.rglob("*")
                if p.is_file()
            }
            unchanged["credentials"] = r.digest(root / "credentials")
            before = r.canonical(dc, "birja_source_test")
            # Use the trusted verifier to install the exact artifact. Target
            # launchers themselves execute with feature checkout denied.
            bootstrap = root / "bootstrap"
            bootstrap.mkdir(mode=0o700)
            shutil.copyfile(
                ROOT / "deploy/verify-restore.py", bootstrap / "verify-restore.py"
            )
            target(
                root,
                [
                    "python3",
                    str(bootstrap / "verify-restore.py"),
                    "bundle",
                    "install",
                    "--archive",
                    str(archive),
                    "--sha",
                    sha,
                    "--synthetic-root",
                    str(root / "host"),
                ],
                allowed_files=[archive],
            )
            release = root / "host/var/lib/birja/recovery/releases" / sha
            c = config(root, release)
            wrapper = root / "docker"
            wrapper.write_text(
                '#!/usr/bin/python3\nimport subprocess,sys\na=sys.argv[1:]\nif any(x.startswith("--snapshot=") for x in a):\n subprocess.run(["/usr/bin/docker","compose","--env-file","/dev/null","-p","birja-ops-test","-f",'
                + repr(str(old / "docker-compose.ops-test.yml"))
                + ',"exec","-T","postgres","psql","-XqAt","-v","ON_ERROR_STOP=1","-U","birja_ops_bootstrap","-d","birja_source_test","-c","INSERT INTO users(email) VALUES (\'writer-after-export@example.invalid\');"],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)\nsubprocess.run(["/usr/bin/docker",*a],check=True)\n'
            )
            wrapper.chmod(0o700)
            tools = root / "host/usr/local/sbin"
            env = {
                **r.ENV,
                "RESTIC_REPOSITORY": c["repository"],
                "RESTIC_PASSWORD_FILE": c["password_file"],
            }
            subprocess.run(
                [c["restic_binary"], "init"],
                env=env,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            target(
                root, ["python3", "-c", f"open({str(ROOT / 'CLAUDE.md')!r})"], ok=False
            )
            print("feature_checkout_denied=true")
            target(
                root, [str(tools / "birja-backup"), "--synthetic", str(root / "config")]
            )
            assert not (root / "state/stage").exists()
            target(
                root,
                [
                    str(tools / "birja-backup-status"),
                    "--synthetic",
                    str(root / "config"),
                ],
            )
            sid = json.loads((root / "state/last-success.json").read_text())[
                "snapshot_id"
            ]
            assert (
                r.canonical(dc, "birja_source_test")["tables"]["users"]["count"]
                == before["tables"]["users"]["count"] + 1
            )
            target(
                root,
                [
                    str(tools / "birja-restore-check"),
                    "--synthetic",
                    str(root / "config"),
                    "--snapshot",
                    sid,
                ],
            )
            print(
                "installed_launchers_backup_retrieval_restore=true concurrent_writer=true staging_removed=true"
            )
            # Private full retrieval for deliberate negative controls only.
            b = r.backup_module()
            job = b.Job(b.load_config(["--synthetic", str(root / "config")]))
            retrieved = root / "retrieved"
            retrieved.mkdir(mode=0o700)
            job.restic("restore", sid, "--target", str(retrieved), "--verify")
            dump = (retrieved / "database.dump").read_bytes()
            manifest = json.loads((retrieved / "manifest.json").read_text())
            assert (
                manifest["tables"] == before["tables"]
                and manifest["financial"] == before["financial"]
            )
            with r.restored(dc, dump):
                r.verify(dc, manifest)
                negative_controls(dc, manifest)
                generated_inserts(dc)
            # Corrupted encrypted snapshots exercise the installed restore
            # entrypoint, rather than just calling verifier functions.
            stage = root / "state/stage/backup"
            stage.mkdir(parents=True, mode=0o700)
            for failure in ["checksum", "manifest"]:
                for p in retrieved.iterdir():
                    shutil.copyfile(p, stage / p.name)
                changed = copy.deepcopy(manifest)
                if failure == "checksum":
                    changed["archive_sha256"] = "0" * 64
                else:
                    changed["financial"]["cash"] = "0.00000000"
                (stage / "manifest.json").write_text(json.dumps(changed))
                lines = job.restic(
                    "backup", "--host", b.HOST, "--tag", b.TAG, ".", cwd=stage
                ).splitlines()
                bad_sid = next(
                    json.loads(line)["snapshot_id"]
                    for line in lines
                    if json.loads(line).get("message_type") == "summary"
                )
                target(
                    root,
                    [
                        str(tools / "birja-restore-check"),
                        "--synthetic",
                        str(root / "config"),
                        "--snapshot",
                        bad_sid,
                    ],
                    ok=False,
                )
            shutil.rmtree(root / "state/stage")
            print("encrypted_checksum_and_manifest_negatives=true")
            for bad in [dump[:100], dump[:-100]]:
                try:
                    with r.restored(dc, bad):
                        r.verify(dc, manifest)
                except (ValueError, OSError):
                    pass
                else:
                    raise AssertionError("truncated dump accepted")
            # An unavailable local encrypted repo must never claim restore.
            os.rename(root / "repository", root / "unavailable")
            target(
                root,
                [
                    str(tools / "birja-restore-check"),
                    "--synthetic",
                    str(root / "config"),
                    "--snapshot",
                    sid,
                ],
                ok=False,
            )
            os.rename(root / "unavailable", root / "repository")
            assert all(r.digest(root / p) == h for p, h in unchanged.items())
            assert r.canonical(dc, "birja_source_test")["revision"] == "0007"
            print("old_checkout_credentials_compose_revision_unchanged=true")
            print(
                "integration_elapsed_seconds="
                + str(round(time.monotonic() - started, 3))
                + " bundle_bytes="
                + str(archive.stat().st_size)
                + " archive_sha256="
                + sha
            )
        finally:
            r.call(dc + ["down", "-v", "--remove-orphans"], timeout=60)
            assert r.call(dc + ["ps", "-q"]).strip() == b""


def negative_controls(dc, manifest):
    for query in [
        "UPDATE accounts SET cash=cash-1",
        "ALTER TABLE holdings DROP CONSTRAINT fk_holdings_user_id_users",
        "DROP INDEX ix_auth_sessions_user_id",
        "SELECT setval('users_id_seq',1,false)",
    ]:
        # A single psql session wraps mutation and verification SQL in a
        # transaction, so rollback restores source equality after each case.
        if query.startswith("SELECT setval"):
            r.sql(dc, query)
            try:
                r.verify(dc, manifest)
            except ValueError:
                pass
            else:
                raise AssertionError("sequence corruption accepted")
            r.sql(dc, "SELECT setval('users_id_seq',(SELECT max(id) FROM users),true)")
            continue
        # Catalog/data mutations are reverted explicitly from captured SQL.
        if query.startswith("UPDATE"):
            undo = "UPDATE accounts SET cash=cash+1"
        elif query.startswith("ALTER"):
            undo = "ALTER TABLE holdings ADD CONSTRAINT fk_holdings_user_id_users FOREIGN KEY(user_id) REFERENCES users(id)"
        else:
            undo = "CREATE INDEX ix_auth_sessions_user_id ON auth_sessions(user_id)"
        r.sql(dc, query)
        try:
            r.verify(dc, manifest)
        except ValueError:
            pass
        else:
            raise AssertionError("corruption accepted")
        finally:
            r.sql(dc, undo)
    changed = copy.deepcopy(manifest)
    changed["financial"]["cash"] = "0.00000000"
    try:
        r.verify(dc, changed)
    except ValueError:
        pass
    else:
        raise AssertionError("manifest corruption accepted")
    print("negative_row_manifest_fk_index_sequence=true")


def generated_inserts(dc):
    # Exercise actual generated ids and attempted FK/CHECK/UNIQUE violations.
    r.sql(
        dc,
        """BEGIN;
    INSERT INTO users(email) VALUES ('clone-insert@example.invalid');
    INSERT INTO accounts(user_id,cash,starting_cash) SELECT id,10000,10000 FROM users WHERE email='clone-insert@example.invalid';
    INSERT INTO auth_sessions(user_id) SELECT id FROM users WHERE email='clone-insert@example.invalid';
    INSERT INTO refresh_tokens(session_id,token_hash,expires_at) SELECT max(id),repeat('f',64),now()+interval '1 day' FROM auth_sessions;
    INSERT INTO holdings(user_id,coin_id,quantity,cost_basis) SELECT u.id,c.id,0.00000001,0.01 FROM users u CROSS JOIN coins c WHERE u.email='clone-insert@example.invalid' AND c.symbol='BTC';
    INSERT INTO trades(user_id,coin_id,side,input_kind,input_value,quantity,mid_price,price_as_of,exec_price,fee,cash_delta,cash_after,idempotency_key) SELECT u.id,c.id,'buy','usd',1,0.00000001,1,now(),1,0,-1,9999,gen_random_uuid() FROM users u CROSS JOIN coins c WHERE u.email='clone-insert@example.invalid' AND c.symbol='BTC';
    ROLLBACK;""",
    )
    for query in [
        "UPDATE accounts SET cash=-1",
        "UPDATE accounts SET cash=0.001",
        "INSERT INTO accounts(user_id,cash,starting_cash) VALUES (9999999,1,1)",
        "INSERT INTO users(email) SELECT email FROM users LIMIT 1",
    ]:
        try:
            r.sql(dc, query)
        except ValueError:
            continue
        raise AssertionError("constraint violation accepted")
    print("generated_ids_and_attempted_constraint_violations=true")


def smoke():
    dc = r.compose()
    try:
        r.call(dc + ["up", "-d", "--wait"], timeout=120)
        r.check_running(dc)
        assert r.sql(dc, "SHOW server_version;", "birja_ops_test").startswith(b"18.6")
        print("isolated_pg18=true")
    finally:
        r.call(dc + ["down", "-v", "--remove-orphans"], timeout=60)


ROLE_SERVICES = r"""
import asyncio, uuid
from datetime import UTC, datetime
from decimal import Decimal
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import Settings
from app.services.accounts import get_or_create_user, get_me
from app.services.auth import start_session, rotate_session, end_session, InvalidSession
from app.services.prices import AcceptedPrice, load_active_coins, upsert_prices
from app.services.trading import execute, Order
async def main():
 s=Settings()
 engine=create_async_engine(s.database_url)
 sessions=async_sessionmaker(engine,expire_on_commit=False)
 async with sessions() as db:
  role=(await db.execute(text('SELECT current_user'))).scalar_one()
  assert role in {'birja_app','birja_scheduler'}
  assert (await db.execute(text('SHOW statement_timeout'))).scalar_one()=='30s'
  assert (await db.execute(text('SHOW idle_in_transaction_session_timeout'))).scalar_one()=='30s'
  if role=='birja_scheduler':
   coins=await load_active_coins(db)
   assert coins
   prices=[AcceptedPrice(c.coin_id,Decimal('12345.12345678'),datetime.now(UTC)) for c in coins]
   await upsert_prices(db,prices,'fake')
   await db.commit()
   await upsert_prices(db,prices,'fake')
   await db.commit()
  else:
   uid,new=await get_or_create_user(db,'restricted-runtime@example.invalid')
   assert new
   same,new=await get_or_create_user(db,'restricted-runtime@example.invalid')
   assert same==uid and not new
   assert (await get_me(db,uid)).cash_usd==Decimal('10000.00')
   issued=await start_session(db,uid,s)
   await db.commit()
   rotated=await rotate_session(db,s,issued.refresh)
   await end_session(db,s,rotated.access)
   try: await rotate_session(db,s,rotated.refresh)
   except InvalidSession: pass
   else: raise AssertionError('session revocation failed')
   key=uuid.uuid4()
   order=Order('BTC','buy','usd',Decimal('100.00'))
   fill,new=await execute(db,user_id=uid,order=order,expected_mid=Decimal('12345.12345678'),idempotency_key=key,settings=s)
   assert new and fill.cash_after==Decimal('9900.00')
   replay,new=await execute(db,user_id=uid,order=order,expected_mid=Decimal('12345.12345678'),idempotency_key=key,settings=s)
   assert not new and replay.trade_id==fill.trade_id
   await execute(db,user_id=uid,order=Order('BTC','sell','quantity',Decimal('0.00010000')),expected_mid=Decimal('12345.12345678'),idempotency_key=uuid.uuid4(),settings=s)
 await engine.dispose()
asyncio.run(main())
"""


def role_python(code, role=r.BOOT):
    # Only synthetic credentials on the fixed internal network, no host ports.
    password = "synthetic-ops-only" if role == r.BOOT else "a" * 64
    return r.call(
        [
            "/usr/bin/docker",
            "run",
            "--rm",
            "-i",
            "--network",
            "birja-ops-test_isolated",
            "-e",
            "ENV=test",
            "-e",
            f"DATABASE_URL=postgresql+asyncpg://{role}:{password}@postgres:5432/birja_source_test",
            "-e",
            "REDIS_URL=redis://localhost:6379/0",
            "-e",
            "OTP_HMAC_SECRET=synthetic-only-otp-secret-00000000000000",
            "-e",
            "JWT_SECRET=synthetic-only-jwt-secret-00000000000000",
            "-e",
            "EMAIL_BACKEND=console",
            "-e",
            "PRICE_SOURCE=fake",
            "--entrypoint",
            "python",
            "birja-backend-test:phase05-07",
            "-",
        ],
        code.encode(),
    )


def role_sql(dc, query, role=r.BOOT, denied=False):
    result = subprocess.run(
        dc
        + [
            "exec",
            "-T",
            "postgres",
            "psql",
            "-XqAt",
            "-v",
            "ON_ERROR_STOP=1",
            "-v",
            "VERBOSITY=sqlstate",
            "-U",
            role,
            "-d",
            "birja_source_test",
        ],
        input=query.encode(),
        check=False,
        capture_output=True,
        env=r.ENV,
        timeout=45,
    )
    if denied:
        assert result.returncode != 0 and b"42501" in result.stderr, (
            "expected insufficient_privilege: " + role + " " + query
        )
    else:
        assert result.returncode == 0, "role SQL failed"
    return result.stdout.strip()


def roles(red_probe=False):
    dc = r.compose()
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="birja-backup-test-") as tmp:
        root = Path(tmp)
        root.chmod(0o700)
        config = root / "roles.json"
        config.write_text(
            json.dumps(
                {
                    "project": "birja-ops-test",
                    "db_name": "birja_source_test",
                    "bootstrap": r.BOOT,
                    "password_files": {
                        name: str(root / name)
                        for name in ("app", "scheduler", "migrator")
                    },
                }
            )
        )
        config.chmod(0o600)
        for name in ("app", "scheduler", "migrator"):
            (root / name).write_text("a" * 64)
            (root / name).chmod(0o600)
        admin = [
            "bash",
            str(ROOT / "deploy/configure-db.sh"),
            "--synthetic",
            str(config),
        ]
        approved = ["--apply", "--approved-operation", "populated-role-transition"]

        def rejected(argv):
            result = subprocess.run(
                argv, capture_output=True, env=r.ENV, timeout=10, check=False
            )
            assert result.returncode != 0
            assert (
                result.stdout == b""
                and result.stderr == b"db_roles_failed=true diagnostics=redacted\n"
            )

        if not red_probe:
            for tail in (
                [],
                ["--apply"],
                ["--inspect", "--apply"],
                ["--apply", "--approved-operation", "other"],
            ):
                rejected(admin + tail)
            original = config.read_text()
            for key, value in (
                ("project", "birja-prod"),
                ("db_name", "postgres"),
                ("bootstrap", "postgres"),
            ):
                changed = json.loads(original)
                changed[key] = value
                config.write_text(json.dumps(changed))
                rejected(admin + approved)
            config.write_text(original)
            config.chmod(0o666)
            rejected(admin + approved)
            config.chmod(0o600)
            for bad in ("a" * 63, "a" * 64 + "\n\\! false", "'secret-value'"):
                (root / "app").write_text(bad)
                rejected(admin + approved)
            (root / "app").write_text("a" * 64)
            with (root / "operation.lock").open("w") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                rejected(admin + approved)
            (root / "operation.lock").chmod(0o644)
            print("role_input_and_lock_rejections=12 secrets_printed=false")
        try:
            r.call(dc + ["up", "-d", "--wait"])
            r.check_running(dc)
            setup_done = time.monotonic()
            r.sql(dc, "CREATE DATABASE birja_source_test", "birja_ops_test")
            role_python(SEED)
            assert r.canonical(dc, "birja_source_test")["revision"] == "0007"
            role_sql(
                dc,
                "CREATE TABLE public.unrelated_fixture(id bigint GENERATED ALWAYS AS IDENTITY, marker text); INSERT INTO unrelated_fixture(marker) VALUES ('untouched')",
            )
            owner_query = "SELECT count(*) FROM pg_class WHERE relnamespace='public'::regnamespace AND relname IN ('users','accounts','auth_sessions','refresh_tokens','coins','prices','holdings','trades','alembic_version') AND relowner=(SELECT oid FROM pg_roles WHERE rolname='%s')"
            assert role_sql(dc, owner_query % r.BOOT) == b"9"
            identities = "SELECT c.relname,s.relname,d.deptype FROM pg_class c JOIN pg_attribute a ON a.attrelid=c.oid AND a.attidentity='a' JOIN pg_depend d ON d.refobjid=c.oid AND d.refobjsubid=a.attnum AND d.deptype='i' JOIN pg_class s ON s.oid=d.objid WHERE c.relnamespace='public'::regnamespace AND c.relname!='unrelated_fixture' ORDER BY c.relname"
            before_identity = role_sql(dc, identities)
            assert len(before_identity.splitlines()) == 7
            before = r.canonical(dc, "birja_source_test")
            if red_probe:
                assert role_sql(dc, owner_query % "birja_migrator") == b"9", (
                    "populated application objects lack restricted migration ownership"
                )
                return
            # Inspection preflights the populated schema without mutation.
            r.call(admin + ["--inspect"])
            assert role_sql(dc, owner_query % r.BOOT) == b"9"
            r.call(
                admin + ["--apply", "--approved-operation", "populated-role-transition"]
            )
            assert role_sql(dc, owner_query % "birja_migrator") == b"9"
            assert role_sql(dc, identities) == before_identity
            assert r.canonical(dc, "birja_source_test") == before
            for unsafe, undo in (
                (
                    "GRANT birja_migrator TO birja_app",
                    "REVOKE birja_migrator FROM birja_app",
                ),
                ("ALTER ROLE birja_app CREATEDB", "ALTER ROLE birja_app NOCREATEDB"),
            ):
                role_sql(dc, unsafe)
                try:
                    rejected(admin + approved)
                finally:
                    role_sql(dc, undo)
                assert r.canonical(dc, "birja_source_test") == before
            r.call(
                admin + ["--apply", "--approved-operation", "populated-role-transition"]
            )
            assert r.canonical(dc, "birja_source_test") == before
            assert (
                role_sql(
                    dc,
                    "SELECT pg_get_userbyid(relowner) FROM pg_class WHERE oid='unrelated_fixture'::regclass",
                )
                == r.BOOT.encode()
            )
            assert role_sql(dc, "SELECT marker FROM unrelated_fixture") == b"untouched"
            assert (
                role_sql(
                    dc,
                    "SELECT count(*) FROM pg_roles WHERE rolname IN ('birja_app','birja_scheduler','birja_migrator') AND (rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls OR rolinherit)",
                )
                == b"0"
            )
            assert (
                role_sql(
                    dc,
                    "SELECT count(*) FROM pg_auth_members WHERE member IN (SELECT oid FROM pg_roles WHERE rolname IN ('birja_app','birja_scheduler','birja_migrator')) OR roleid IN (SELECT oid FROM pg_roles WHERE rolname IN ('birja_app','birja_scheduler','birja_migrator'))",
                )
                == b"0"
            )
            role_python(
                "from alembic import command\nfrom alembic.config import Config\ncommand.upgrade(Config('/app/alembic.ini'),'head')",
                "birja_migrator",
            )
            assert role_sql(dc, "SELECT version_num FROM alembic_version") == b"0008"
            assert (
                role_sql(
                    dc,
                    "SELECT indisvalid AND indisready FROM pg_index WHERE indexrelid='ix_trades_user_created_id'::regclass",
                )
                == b"t"
            )
            assert (
                role_sql(
                    dc,
                    "SELECT bool_and(s.relowner=c.relowner) FROM pg_class c JOIN pg_depend d ON d.refobjid=c.oid AND d.deptype='i' JOIN pg_class s ON s.oid=d.objid AND s.relkind='S' WHERE c.relnamespace='public'::regnamespace AND c.relname!='unrelated_fixture'",
                )
                == b"t"
            )
            role_python(ROLE_SERVICES, "birja_scheduler")
            role_python(ROLE_SERVICES, "birja_app")
            negatives = 0
            for role in ("birja_app", "birja_scheduler"):
                for query in (
                    "CREATE TABLE public.forbidden(id int)",
                    "CREATE SCHEMA forbidden",
                    "ALTER TABLE prices ADD COLUMN forbidden int",
                    "ALTER TABLE prices OWNER TO " + role,
                    "CREATE ROLE forbidden",
                    "CREATE DATABASE forbidden",
                    "TRUNCATE prices",
                    "UPDATE alembic_version SET version_num='bad'",
                    "SET ROLE birja_migrator",
                    "SET ROLE "
                    + ("birja_scheduler" if role == "birja_app" else "birja_app"),
                    "SET ROLE " + r.BOOT,
                    "ALTER ROLE " + role + " BYPASSRLS",
                    "SELECT * FROM unrelated_fixture",
                    "UPDATE coins SET name=name",
                    "SELECT setval('users_id_seq',1)",
                ):
                    role_sql(dc, query, role, denied=True)
                    negatives += 1
            for table in (
                "users",
                "accounts",
                "auth_sessions",
                "refresh_tokens",
                "holdings",
                "trades",
            ):
                column = {
                    "users": "email",
                    "accounts": "cash",
                    "auth_sessions": "revoked_at",
                    "refresh_tokens": "used_at",
                    "holdings": "quantity",
                    "trades": "fee",
                }[table]
                for query in (
                    f"SELECT * FROM {table}",
                    f"DELETE FROM {table}",
                    f"INSERT INTO {table} DEFAULT VALUES",
                    f"UPDATE {table} SET {column}={column}",
                ):
                    role_sql(dc, query, "birja_scheduler", denied=True)
                    negatives += 1
            for query in (
                "UPDATE prices SET mid=mid",
                "DELETE FROM users",
                "DELETE FROM trades",
            ):
                role_sql(dc, query, "birja_app", denied=True)
                negatives += 1
            role_sql(
                dc,
                "CREATE TABLE public.defaults_fixture(id bigint GENERATED ALWAYS AS IDENTITY, marker text)",
                "birja_migrator",
            )
            for role in ("birja_app", "birja_scheduler"):
                for query in (
                    "SELECT * FROM defaults_fixture",
                    "INSERT INTO defaults_fixture(marker) VALUES ('bad')",
                    "SELECT nextval('defaults_fixture_id_seq')",
                ):
                    role_sql(dc, query, role, denied=True)
                    negatives += 1
            role_sql(
                dc,
                "INSERT INTO defaults_fixture(marker) VALUES ('private'); ALTER TABLE defaults_fixture ENABLE ROW LEVEL SECURITY; GRANT SELECT ON defaults_fixture TO birja_app,birja_scheduler",
                "birja_migrator",
            )
            for role in ("birja_app", "birja_scheduler"):
                assert (
                    role_sql(dc, "SELECT count(*) FROM defaults_fixture", role) == b"0"
                )
                role_sql(
                    dc,
                    "SET row_security=off; SELECT * FROM defaults_fixture",
                    role,
                    denied=True,
                )
                negatives += 1
            role_sql(dc, "DROP TABLE public.defaults_fixture", "birja_migrator")
            print(
                f"roles_populated_transfer=true repeatable=true identity_dependencies=true concurrent_0008_valid=true runtime_services=true scheduler_upsert=true denied_operations={negatives}"
            )
            print(
                f"fixture_setup_seconds={setup_done - started:.3f} roles_integration_seconds={time.monotonic() - started:.3f}"
            )
        finally:
            r.call(dc + ["down", "-v", "--remove-orphans"], timeout=60)
            assert r.call(dc + ["ps", "-q"]).strip() == b""


TLS_PROBE = r"""
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import Settings
from app.db.connection import database_connect_args
async def main():
 s=Settings()
 engine=create_async_engine(s.database_url,connect_args=database_connect_args(s))
 async with engine.connect() as db:
  assert (await db.execute(text('SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()'))).scalar_one(), 'production-shaped database session is plaintext'
 await engine.dispose()
asyncio.run(main())
"""


def tls_red_probe():
    """A real-session RED, without counting missing future artifacts as evidence."""
    dc = r.compose()
    try:
        r.call(dc + ["up", "-d", "--wait"])
        r.sql(dc, "CREATE DATABASE birja_source_test", "birja_ops_test")
        # Existing image predates the shared helper; bind current source explicitly.
        argv = [
            "/usr/bin/docker",
            "run",
            "--rm",
            "-i",
            "--network",
            "birja-ops-test_isolated",
            "-v",
            str(ROOT / "backend/app") + ":/app/app:ro",
            "-e",
            "ENV=test",
            "-e",
            "DATABASE_URL=postgresql+asyncpg://birja_ops_bootstrap:synthetic-ops-only@postgres:5432/birja_source_test",
            "-e",
            "REDIS_URL=redis://localhost:6379/0",
            "-e",
            "OTP_HMAC_SECRET=synthetic-only-otp-secret-00000000000000",
            "-e",
            "JWT_SECRET=synthetic-only-jwt-secret-00000000000000",
            "--entrypoint",
            "python",
            "birja-backend-test:phase05-07",
            "-",
        ]
        result = subprocess.run(
            argv,
            input=TLS_PROBE.encode(),
            capture_output=True,
            env=r.ENV,
            timeout=60,
            check=False,
        )
        assert result.returncode == 0, (
            "real_pg18_verified_tls=false plaintext_session=true"
            if b"production-shaped database session is plaintext" in result.stderr
            else "TLS RED infrastructure failed"
        )
    finally:
        r.call(dc + ["down", "-v", "--remove-orphans"], timeout=60)


def tls():
    if not (ROOT / "deploy/provision-db-tls.sh").exists():
        return tls_red_probe()
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="birja-backup-test-") as tmp:
        root = Path(tmp)
        root.chmod(0o700)
        # Each credential route is deliberately different; fixtures never read prod.env.
        passwords = {
            name: char * 64
            for name, char in (("app", "a"), ("scheduler", "b"), ("migrator", "c"))
        }
        env = {
            **r.ENV,
            "POSTGRES_USER": r.BOOT,
            "POSTGRES_PASSWORD": "synthetic-ops-only",
            "POSTGRES_DB": "birja_source_test",
            "REDIS_PASSWORD": "synthetic-redis-only",
            "OTP_HMAC_SECRET": "synthetic-only-otp-secret-00000000000000",
            "JWT_SECRET": "synthetic-only-jwt-secret-00000000000000",
            "RESEND_API_KEY": "synthetic-not-used",
            "EMAIL_FROM": "Birja <test@example.invalid>",
        }
        for name, password in passwords.items():
            env[name.upper() + "_DATABASE_URL"] = (
                f"postgresql+asyncpg://birja_{name}:{password}@postgres:5432/birja_source_test"
            )
        prod = json.loads(
            subprocess.run(
                [
                    "/usr/bin/docker",
                    "compose",
                    "--env-file",
                    "/dev/null",
                    "-f",
                    str(ROOT / "docker-compose.prod.yml"),
                    "--profile",
                    "migrate",
                    "config",
                    "--format",
                    "json",
                ],
                env=env,
                check=True,
                capture_output=True,
                timeout=20,
            ).stdout
        )
        for name, role in (
            ("backend", "app"),
            ("scheduler", "scheduler"),
            ("migrate", "migrator"),
        ):
            service = prod["services"][name]
            assert (
                service["environment"]["DATABASE_URL"]
                == env[role.upper() + "_DATABASE_URL"]
            )
            assert (
                service["environment"]["DATABASE_SSL_CA_FILE"] == "/run/birja/db-ca.crt"
            )
            assert all(
                not key.startswith(
                    (
                        "POSTGRES_",
                        "APP_DATABASE",
                        "SCHEDULER_DATABASE",
                        "MIGRATOR_DATABASE",
                    )
                )
                for key in service["environment"]
            )
            assert len(service["volumes"]) == 1 and service["volumes"][0]["read_only"]
            assert service["volumes"][0]["target"] == "/run/birja/db-ca.crt"
            if name != "backend":
                assert not set(service["environment"]) & {
                    "JWT_SECRET",
                    "OTP_HMAC_SECRET",
                    "RESEND_API_KEY",
                    "EMAIL_FROM",
                }
        assert prod["services"]["backend"]["ports"][0]["host_ip"] == "127.0.0.1"
        assert prod["services"]["backend"]["ports"][0]["published"] == "18000"
        for name in ("postgres", "redis", "scheduler", "migrate"):
            assert not prod["services"][name].get("ports")
        assert prod["services"]["postgres"]["volumes"][0]["source"] == "pgdata"
        assert (
            prod["services"]["postgres"]["volumes"][0]["target"]
            == "/var/lib/postgresql"
        )
        assert set(prod["services"]["postgres"]["networks"]) == {"data"}
        assert prod["networks"]["data"]["internal"] is True
        assert prod["services"]["migrate"]["profiles"] == ["migrate"]
        assert "OTP_HMAC_SECRET" not in prod["services"]["migrate"]["environment"]
        provision = [
            "bash",
            str(ROOT / "deploy/provision-db-tls.sh"),
            "--synthetic",
            str(root),
        ]

        def reject_provision(tail):
            result = subprocess.run(
                provision + tail,
                env=r.ENV,
                capture_output=True,
                timeout=10,
                check=False,
            )
            assert result.returncode != 0
            assert (
                result.stdout == b""
                and result.stderr == b"db_tls_failed=true diagnostics=redacted\n"
            )

        reject_provision(["--create"])
        reject_provision(["--create", "--approved-custody", "other"])
        root.chmod(0o755)
        reject_provision(
            ["--create", "--approved-custody", "owner-off-server-password-manager"]
        )
        root.chmod(0o700)
        assert not (root / "db-tls").exists()
        r.call(
            provision
            + ["--create", "--approved-custody", "owner-off-server-password-manager"]
        )
        assert (root / "custody/ca.key").stat().st_mode & 0o777 == 0o600
        assert (root / "db-tls/server/server.key").stat().st_mode & 0o777 == 0o640
        assert (root / "db-tls/server/server.key").stat().st_uid == 0
        assert (root / "db-tls/server/server.key").stat().st_gid == 999
        key = root / "db-tls/server/server.key"
        key.chmod(0o644)
        reject_provision(["--check"])
        reject_provision(
            ["--renew", "--approved-custody", "owner-off-server-password-manager"]
        )
        key.chmod(0o640)
        os.chown(key, 0, 0)
        reject_provision(["--check"])
        os.chown(key, 0, 999)
        with (root / "operation.lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            reject_provision(
                ["--renew", "--approved-custody", "owner-off-server-password-manager"]
            )
        before = (root / "db-tls/server/server.crt").read_bytes()
        ca = (root / "db-tls/ca.crt").read_bytes()
        r.call(provision + ["--check"])
        # A genuine short-lived signed leaf trips the 30-day warning gate;
        # renewal is permitted during that window, without rotating the CA.
        r.call(
            [
                "openssl",
                "req",
                "-new",
                "-key",
                str(key),
                "-subj",
                "/CN=postgres",
                "-out",
                str(root / "short.csr"),
            ]
        )
        (root / "short.ext").write_text(
            "subjectAltName=DNS:postgres\nextendedKeyUsage=serverAuth\n"
        )
        r.call(
            [
                "openssl",
                "x509",
                "-req",
                "-in",
                str(root / "short.csr"),
                "-CA",
                str(root / "db-tls/ca.crt"),
                "-CAkey",
                str(root / "custody/ca.key"),
                "-set_serial",
                "101",
                "-days",
                "1",
                "-extfile",
                str(root / "short.ext"),
                "-out",
                str(root / "db-tls/server/server.crt"),
            ]
        )
        reject_provision(["--check"])
        r.call(
            provision
            + ["--renew", "--approved-custody", "owner-off-server-password-manager"]
        )
        r.call(provision + ["--check"])
        assert (root / "db-tls/ca.crt").read_bytes() == ca
        # Exercise init only against a fresh private synthetic directory.
        with tempfile.TemporaryDirectory(prefix="birja-backup-test-") as env_tmp:
            env_root = Path(env_tmp)
            env_root.chmod(0o700)
            init = [
                "bash",
                str(ROOT / "deploy/init-prod-env.sh"),
                "--synthetic",
                str(env_root),
            ]
            r.call(init)
            env_file = env_root / "prod.env"
            assert (
                env_file.stat().st_mode & 0o777 == 0o600 and env_file.stat().st_uid == 0
            )
            contents = env_file.read_bytes()
            fields = dict(
                line.split("=", 1)
                for line in contents.decode().splitlines()
                if line and not line.startswith("#")
            )
            secrets = [fields["POSTGRES_PASSWORD"]]
            for name in ("APP", "SCHEDULER", "MIGRATOR"):
                secrets.append(
                    fields[name + "_DATABASE_URL"].split(":", 2)[2].split("@", 1)[0]
                )
            assert len(set(secrets)) == 4 and all(len(value) == 64 for value in secrets)
            result = subprocess.run(
                init, capture_output=True, env=r.ENV, timeout=10, check=False
            )
            assert result.returncode != 0 and env_file.read_bytes() == contents
        before = (root / "db-tls/server/server.crt").read_bytes()
        duplicate = subprocess.run(
            provision
            + ["--create", "--approved-custody", "owner-off-server-password-manager"],
            env=r.ENV,
            capture_output=True,
            check=False,
        )
        assert duplicate.returncode != 0
        assert (root / "db-tls/server/server.crt").read_bytes() == before
        # Renew preserves CA and replaces only leaf material; expiry check is bounded.
        ca = (root / "db-tls/ca.crt").read_bytes()
        r.call(
            provision
            + ["--renew", "--approved-custody", "owner-off-server-password-manager"]
        )
        assert (root / "db-tls/ca.crt").read_bytes() == ca
        assert (root / "db-tls/server/server.crt").read_bytes() != before
        r.call(provision + ["--check"])
        # Mount a directory so replacing HBA below is visible on reload.
        hba = root / "hba"
        hba.mkdir(mode=0o755)
        hba.chmod(0o755)
        policy = (ROOT / "deploy/db/pg_hba.conf").read_text()
        (hba / "pg_hba.conf").write_text(
            "hostssl all " + r.BOOT + " samenet scram-sha-256\n" + policy
        )
        (hba / "pg_hba.conf").chmod(0o644)
        fixture = {
            "name": "birja-ops-test",
            "services": {},
            "networks": {"isolated": {"internal": True}},
        }
        for name, source in prod["services"].items():
            s = copy.deepcopy(source)
            for key in (
                "build",
                "ports",
                "restart",
                "logging",
                "profiles",
                "depends_on",
                "volumes",
                "networks",
            ):
                s.pop(key, None)
            s["networks"] = (
                {"isolated": {"aliases": ["wrong-host"]}}
                if name == "postgres"
                else ["isolated"]
            )
            s.update(mem_limit="512m", cpus=2, pids_limit=128)
            s["volumes"] = []
            if name == "postgres":
                s["tmpfs"] = ["/var/lib/postgresql:size=268435456"]
                s["volumes"] = [
                    str(root / "db-tls/server") + ":/run/birja/db-server:ro",
                    str(hba) + ":/run/birja/db-hba:ro",
                ]
            elif name == "redis":
                s["tmpfs"] = ["/data:size=16777216"]
            else:
                s["image"] = "birja-backend-test:phase05-07"
                s["volumes"] = [
                    str(root / "db-tls/ca.crt") + ":/run/birja/db-ca.crt:ro",
                    str(ROOT / "backend/app") + ":/app/app:ro",
                    str(ROOT / "backend/alembic") + ":/app/alembic:ro",
                ]
                # Test app real services with production trust, never real email/market network.
                if name != "migrate":
                    s["command"] = ["sleep", "infinity"]
            fixture["services"][name] = s
        file = root / "tls-compose.json"
        file.write_text(json.dumps(fixture))
        dc = [
            "/usr/bin/docker",
            "compose",
            "--env-file",
            "/dev/null",
            "-p",
            "birja-ops-test",
            "-f",
            str(file),
        ]

        def client(service, code, overrides=(), ok=True):
            result = subprocess.run(
                dc
                + ["run", "--rm", "--no-deps", "-T"]
                + list(overrides)
                + ["--entrypoint", "python", service, "-"],
                input=code.encode(),
                capture_output=True,
                check=False,
                env=r.ENV,
                timeout=120,
            )
            assert (result.returncode == 0) == ok, (
                "TLS client assertion failed: " + service
            )
            return result

        try:
            r.call(dc + ["up", "-d", "--wait", "postgres", "redis"], timeout=120)
            assert r.sql(dc, "SHOW server_version", "birja_source_test").startswith(
                b"18.6"
            )
            # Validate pinned image ownership rather than guessing uid/gid.
            assert (
                r.call(dc + ["exec", "-T", "postgres", "id", "-g", "postgres"]).strip()
                == b"999"
            )
            setup = time.monotonic()
            bootstrap = [
                "-e",
                "ENV=test",
                "-e",
                "DATABASE_URL=postgresql+asyncpg://"
                + r.BOOT
                + ":synthetic-ops-only@postgres:5432/birja_source_test",
            ]
            secure_seed = SEED.replace(
                "engine=create_async_engine(s.database_url)",
                "from app.db.connection import database_connect_args\n engine=create_async_engine(s.database_url,connect_args=database_connect_args(s))",
            )
            client("backend", secure_seed, bootstrap)
            config = root / "roles.json"
            config.write_text(
                json.dumps(
                    {
                        "project": "birja-ops-test",
                        "db_name": "birja_source_test",
                        "bootstrap": r.BOOT,
                        "password_files": {n: str(root / n) for n in passwords},
                    }
                )
            )
            config.chmod(0o600)
            for n, password in passwords.items():
                (root / n).write_text(password)
                (root / n).chmod(0o600)
            r.call(
                [
                    "bash",
                    str(ROOT / "deploy/configure-db.sh"),
                    "--synthetic",
                    str(config),
                    "--apply",
                    "--approved-operation",
                    "populated-role-transition",
                ]
            )
            (hba / "pg_hba.conf").write_text(policy)
            assert r.sql(dc, "SELECT pg_reload_conf()", "birja_source_test") == b"t\n"
            assert (
                r.sql(
                    dc,
                    "SELECT count(*) FROM pg_hba_file_rules WHERE error IS NOT NULL",
                    "birja_source_test",
                )
                == b"0\n"
            )
            # Real one-shot production migration command, with only migrator route/trust.
            r.call(dc + ["run", "--rm", "--no-deps", "-T", "migrate"])
            assert role_sql(dc, "SELECT version_num FROM alembic_version") == b"0008"
            assert (
                role_sql(
                    dc,
                    "SELECT indisvalid AND indisready FROM pg_index WHERE indexrelid='ix_trades_user_created_id'::regclass",
                )
                == b"t"
            )
            for service in ("backend", "scheduler", "migrate"):
                code = TLS_PROBE
                if service != "backend":
                    code = code.replace(
                        "from app.core.config import Settings",
                        "from app.core.config import SchedulerSettings as Settings",
                    )
                client(service, code)
            services_code = ROLE_SERVICES.replace(
                "engine=create_async_engine(s.database_url)",
                "from app.db.connection import database_connect_args\n engine=create_async_engine(s.database_url,connect_args=database_connect_args(s))",
            )
            client(
                "scheduler",
                services_code.replace(
                    "from app.core.config import Settings",
                    "from app.core.config import SchedulerSettings as Settings",
                ),
            )
            client("backend", services_code)
            # Check certificate errors themselves, not arbitrary network/settings failures.
            bad = root / "bad-ca"
            bad.mkdir(mode=0o700)
            r.call(
                [
                    "openssl",
                    "req",
                    "-x509",
                    "-newkey",
                    "rsa:2048",
                    "-nodes",
                    "-days",
                    "1",
                    "-subj",
                    "/CN=unrelated-test-ca",
                    "-keyout",
                    str(bad / "key"),
                    "-out",
                    str(bad / "ca.crt"),
                ]
            )
            (bad / "ca.crt").chmod(0o644)
            negative = client(
                "backend",
                TLS_PROBE,
                ["-v", str(bad / "ca.crt") + ":/run/birja/db-ca.crt:ro"],
                ok=False,
            )
            assert b"CERTIFICATE_VERIFY_FAILED" in negative.stderr
            wrong = env["APP_DATABASE_URL"].replace("@postgres:", "@wrong-host:")
            negative = client(
                "backend", TLS_PROBE, ["-e", "DATABASE_URL=" + wrong], ok=False
            )
            assert (
                b"CERTIFICATE_VERIFY_FAILED" in negative.stderr
                and b"Hostname mismatch" in negative.stderr
            )
            client("backend", TLS_PROBE, ["-e", "DATABASE_SSL_CA_FILE="], ok=False)
            plain = (
                "import asyncio,asyncpg\nasync def main():\n try: await asyncpg.connect(host='postgres',user='birja_app',password='"
                + passwords["app"]
                + "',database='birja_source_test',ssl=False,timeout=5)\n except asyncpg.InvalidAuthorizationSpecificationError: return\n raise AssertionError('plaintext accepted')\nasyncio.run(main())"
            )
            client("backend", plain)
            # Deployed service config and actual inspect cannot leak another credential/key.
            r.call(dc + ["up", "-d", "--no-deps", "backend", "scheduler"])
            for service, role in (("backend", "app"), ("scheduler", "scheduler")):
                container = r.call(dc + ["ps", "-q", service]).decode().strip()
                inspected = json.loads(
                    r.call(["/usr/bin/docker", "inspect", container])
                )[0]
                serialized = json.dumps(inspected)
                assert "synthetic-ops-only" not in serialized
                assert passwords["migrator"] not in serialized
                assert (
                    passwords["scheduler" if role == "app" else "app"] not in serialized
                )
                assert not inspected["HostConfig"].get("PortBindings")
                assert all(
                    m["Destination"] not in {"/run/birja/db-server", "/custody"}
                    for m in inspected["Mounts"]
                )
                assert all(not m["RW"] for m in inspected["Mounts"])
            network = json.loads(
                r.call(
                    ["/usr/bin/docker", "network", "inspect", "birja-ops-test_isolated"]
                )
            )[0]
            assert network["Internal"]
            assert len(r.call(dc + ["ps", "-q", "scheduler"]).split()) == 1
            print(
                "tls_pg18=true app_scheduler_migrator_ssl=true bad_ca_hostname_plaintext_rejected=true concurrent_0008_valid=true runtime_services=true credential_mount_isolation=true renewal=true"
            )
            print(
                f"tls_fixture_setup_seconds={setup - started:.3f} tls_integration_seconds={time.monotonic() - started:.3f}"
            )
        finally:
            r.call(dc + ["down", "-v", "--remove-orphans"], timeout=60)
            assert not r.call(dc + ["ps", "-q"]).strip()


if __name__ == "__main__":
    os.umask(0o077)
    if sys.argv[1:] == ["--smoke"]:
        smoke()
    elif sys.argv[1:] == ["--self-test-recovery-bundle-inputs"]:
        input_self_test()
    elif sys.argv[1:] == ["--roles"]:
        roles()
    elif sys.argv[1:] == ["--roles-red-probe"]:
        roles(red_probe=True)
    elif sys.argv[1:] == ["--tls"]:
        tls()
    elif sys.argv[1:] == ["--all"]:
        roundtrip()
        roles()
        tls()
    else:
        args = options(sys.argv[1:])
        roundtrip(args.recovery_bundle)
