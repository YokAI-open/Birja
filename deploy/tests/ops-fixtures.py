#!/usr/bin/env python3
"""Independent synthetic PG18 fixture; never imports application test fixtures."""

import argparse
import contextlib
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
from types import SimpleNamespace

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "recovery", ROOT / "deploy/verify-restore.py"
)
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


def source_git(*args):
    """Trust only this checkout for root-run synthetic fixture source reads."""
    return r.call(["git", "-c", "safe.directory=" + str(ROOT), "-C", str(ROOT), *args])


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

# Populate historical schemas with their actual release models even when CI's
# fixture image contains current successor code. No feature source is consulted
# by retained recovery children; the old source is embedded only in seed input.
SEED = (
    "import base64,io,sys,tarfile,tempfile\n"
    "legacy=tempfile.mkdtemp(prefix='birja-synthetic-legacy-')\n"
    "with tarfile.open(fileobj=io.BytesIO(base64.b64decode("
    + repr(__import__('base64').b64encode(source_git('archive', 'v0.3.1', 'backend/app', 'backend/alembic')).decode())
    + "))) as archive: archive.extractall(legacy,filter='data')\n"
    "sys.path.insert(0,legacy+'/backend')\n"
    + SEED.replace("command.upgrade(Config('/app/alembic.ini'), '0007')", "cfg=Config('/app/alembic.ini');cfg.set_main_option('script_location',legacy+'/backend/alembic');command.upgrade(cfg,'0007')")
)


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


def target(root, argv, ok=True, allowed_files=(), inherited=None):
    started = time.monotonic()
    result = subprocess.run(
        argv,
        check=False,
        env={
            **r.ENV,
            "HOME": str(root),
            **(
                {"BIRJA_BACKUP_LOCK_FD": str(inherited)}
                if inherited is not None
                else {}
            ),
        },
        cwd=root / "old/app",
        capture_output=True,
        timeout=180,
        preexec_fn=lambda: restrict_to_old_host(root, allowed_files),
        pass_fds=() if inherited is None else (inherited,),
    )
    print(
        f"fixture_target={Path(argv[0]).name} seconds={time.monotonic() - started:.3f} exit={result.returncode}",
        flush=True,
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
        r.bundle_verify(archive, sha, required_profile="deploy-recovery-v2")
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
        "release": source_git("rev-parse", "v0.3.1").decode().strip(),
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


@contextlib.contextmanager
def installed_recovery(archive_arg=None):
    """Install once; caller exclusively owns source server, seed and transitions."""
    with tempfile.TemporaryDirectory(prefix="birja-backup-test-") as tmp:
        root = Path(tmp)
        root.chmod(0o700)
        archive = Path(archive_arg) if archive_arg else root / "recovery.tar"
        if not archive_arg:
            r.bundle_package(archive)
        sha = r.private(str(archive) + ".sha256").read_text().strip()
        r.bundle_verify(archive, sha, required_profile="deploy-recovery-v2")
        old = root / "old"
        old.mkdir(mode=0o700)
        app = old / "app"
        app.mkdir(mode=0o700)
        old_tar = source_git("archive", "v0.3.1")
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
        # Use the trusted verifier to install the exact artifact. Target
        # launchers themselves execute with feature checkout denied.
        bootstrap = root / "bootstrap"
        bootstrap.mkdir(mode=0o700)
        shutil.copyfile(
            ROOT / "deploy/verify-restore.py", bootstrap / "verify-restore.py"
        )
        shutil.copyfile(
            ROOT / "deploy/backup-snapshot.py", bootstrap / "backup-snapshot.py"
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
                "--require-profile",
                "deploy-recovery-v2",
                "--synthetic-root",
                str(root / "host"),
            ],
            allowed_files=[archive],
        )
        release = root / "host/var/lib/birja/recovery/releases" / sha
        c = config(root, release)
        wrapper = root / "docker"
        wrapper.write_text('#!/bin/bash\nexec /usr/bin/docker "$@"\n')
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
        immutable = [
            archive,
            *tools.iterdir(),
            *[release / name for name in r.CORE],
            release / "INVENTORY.json",
            release / "SHA256SUMS",
            release / "tools/restic",
        ]
        session = SimpleNamespace(
            root=root,
            archive=archive,
            archive_sha=sha,
            release=release,
            tools=tools,
            config_path=root / "config",
            immutable={p: r.digest(p) for p in immutable},
        )
        try:
            yield session
        finally:
            assert all(
                r.digest(path) == value for path, value in session.immutable.items()
            )


def recovery_roundtrip(session, *, source_revision, source_release, inherited=None):
    """Use installed launchers and a fixed separate clone; never own the source."""
    import re

    assert re.fullmatch(r"[A-Za-z0-9_]{1,64}", source_revision)
    assert re.fullmatch(r"[0-9a-f]{40}", source_release)
    root, tools = session.root, session.tools
    assert all(r.digest(path) == value for path, value in session.immutable.items())
    c = json.loads(session.config_path.read_text())
    c["release"] = source_release
    c["quota"]["observed_at"] = int(time.time())
    session.config_path.write_text(json.dumps(c))
    common = ["--synthetic", str(session.config_path)]

    def invoke(argv):
        if inherited is None:
            return target(root, argv)
        return target(root, argv, inherited=inherited)

    invoke([str(tools / "birja-backup"), *common])
    assert not (root / "state/stage").exists()
    invoke([str(tools / "birja-backup-status"), *common])
    sid = json.loads((root / "state/last-success.json").read_text())["snapshot_id"]
    invoke(
        [
            str(tools / "birja-restore-check"),
            *common,
            "--snapshot",
            sid,
            "--isolated-clone",
        ],
    )
    invoke(
        [
            "python3",
            str(session.release / "deploy/backup-snapshot.py"),
            "recovery-gate",
            *common,
            "--snapshot",
            sid,
            "--source-release",
            source_release,
            "--source-revision",
            source_revision,
            "--bundle-sha",
            session.archive_sha,
        ],
    )
    assert all(r.digest(path) == value for path, value in session.immutable.items())
    assert not list((root / "state").glob("restore-*/*"))
    return sid


STOCK_RECOVERY_SEED = """
INSERT INTO stock_data_admissions(product,state,generation,reviewed_at,valid_from,valid_until,evidence_ref,terms_version,collection_allowed,display_allowed,derived_allowed,retention_allowed,scope,quota,allowed_fields,attribution,calendar) VALUES
 ('calendar','approved',3,'2026-11-10T10:00Z','2026-11-01Z','2026-12-01Z','https://example.invalid/calendar-evidence','fixture-v2',true,true,true,true,'{"exchanges":["NYSE","NASDAQ"]}','{"requests":20}','["opens_at","closes_at"]','Official calendar fixture','{"official_source":["https://www.nyse.com/trade/hours-calendars","https://www.nasdaqtrader.com/Trader.aspx?id=Calendar"],"version":"fixture-v2","review_valid_until":"2026-11-10T11:00:00Z","coverage_start":"2026-11-01","coverage_end":"2026-12-01","overrides":[{"date":"2026-11-26","closed":true,"revision":1,"provenance":"https://example.invalid/closure"},{"date":"2026-11-27","opens_at":"2026-11-27T14:30:00Z","closes_at":"2026-11-27T18:00:00Z","revision":2,"provenance":"https://example.invalid/shortened"}]}'),
 ('quotes','approved',7,'2026-11-10T10:00Z','2026-11-01Z','2026-12-01Z','https://example.invalid/quote-evidence','fixture-v1',true,true,true,true,'{"symbols":["AAPL","MSFT"],"feed":"iex"}','{"requests":20}','["bid","ask"]','IEX prices','{}'),
 ('status','denied',1,NULL,NULL,NULL,NULL,NULL,false,false,false,false,'{}','{}','[]','','{}'),
 ('actions','revoked',2,'2026-01-01Z','2026-01-01Z','2026-01-02Z','https://example.invalid/expired-evidence','fixture-v1',false,false,false,true,'{}','{}','[]','','{}');
INSERT INTO stock_sessions(exchange,session_date,opens_at,closes_at,coverage_start,coverage_end,calendar_admission_generation)
 SELECT exchange,'2026-11-26',NULL,NULL,'2026-11-01','2026-12-01',3 FROM (VALUES ('NYSE'),('NASDAQ')) AS x(exchange);
INSERT INTO stock_sessions(exchange,session_date,opens_at,closes_at,coverage_start,coverage_end,calendar_admission_generation)
 SELECT exchange,'2026-11-27','2026-11-27T14:30Z','2026-11-27T18:00Z','2026-11-01','2026-12-01',3 FROM (VALUES ('NYSE'),('NASDAQ')) AS x(exchange);
INSERT INTO stock_sessions(exchange,session_date,opens_at,closes_at,coverage_start,coverage_end,calendar_admission_generation)
 VALUES ('NYSE','2026-11-10','2026-11-10T14:30Z','2026-11-10T21:00Z','2026-11-01','2026-12-01',999);
"""


def identity_state(dc, db):
    names = r.backup_module().identity_tables(role_sql(dc, "SELECT version_num FROM alembic_version").decode())
    return {name: r.sql(dc, f"SELECT last_value,is_called FROM {name}_id_seq", db).strip() for name in names}


def successor_roundtrips(dc, session, unchanged):
    """Fresh retained bytes perform real dump/retrieval/restore of every revision."""
    release = source_git('rev-parse', 'HEAD').decode().strip()
    source_container = r.call(dc + ['ps','-q','postgres']).strip()
    source_mounts = r.call(['/usr/bin/docker','inspect','--format','{{json .Mounts}}',source_container.decode()])
    for revision in ('0008','0009','0010','0011','0012'):
        if revision == '0012':
            # Explicit synthetic predecessor role provisioning. The source's
            # migration owner is real before0012; restore never invents it.
            role_sql(dc, 'ALTER ROLE birja_migrator NOINHERIT')
            role_config=session.root/'roles.json'
            password_files={}
            for name in ('app','scheduler','migrator'):
                file=session.root/name
                file.write_text('a'*64);file.chmod(0o600)
                password_files[name]=str(file)
            role_config.write_text(json.dumps({'project':'birja-ops-test','db_name':'birja_source_test',
                'bootstrap':r.BOOT,'password_files':password_files}));role_config.chmod(0o600)
            r.call(['bash',str(ROOT/'deploy/configure-db.sh'),'--synthetic',str(role_config),
                '--apply','--approved-operation','populated-role-transition'])
        role_python("from alembic import command\nfrom alembic.config import Config\ncommand.upgrade(Config('/app/alembic.ini')," + repr(revision) + ")", 'birja_migrator' if revision=='0012' else r.BOOT)
        if revision == '0009':
            r.sql(dc, STOCK_RECOVERY_SEED, 'birja_source_test')
        if revision == '0010':
            r.sql(dc, """UPDATE stock_instruments SET provider_asset_id='synthetic-'||coin_id,provider_verified_at='2026-11-10T14:00Z' WHERE mod(coin_id,2)=0;
INSERT INTO stock_quotes(coin_id,bid,ask,mid,source,feed,event_at,collected_at,session_date,admission_generation)
SELECT coin_id,100.00000001,100.00000003,100.00000002,'alpaca','iex','2026-11-10T15:00:00.123456Z','2026-11-10T15:00:01.654321Z','2026-11-10',7 FROM stock_instruments;""", 'birja_source_test')
        if revision == '0011':
            spec = importlib.util.spec_from_file_location('accounting_fixture', ROOT / 'deploy/tests/test-stock-recovery-contracts.py')
            fixture = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(fixture)
            r.sql(dc, fixture.ACTION_SEED, 'birja_source_test')
        if revision == '0012':
            role_sql(dc,"CREATE ROLE birja_operator_restore_fixture LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD '"+'a'*64+"'; GRANT birja_action_operator TO birja_operator_restore_fixture")
            request=json.loads(role_python(RESOLUTION_SCENARIO + RECOVERY_SEED_SCENARIO, 'birja_migrator'))
        before = r.canonical(dc, 'birja_source_test')
        if revision == '0010':
            assert before['tables']['stock_instruments']['count'] == 20
            assert before['tables']['stock_quotes']['count'] == 20
            assert before['tables']['stock_sessions']['count'] == 5
            assert before['tables']['stock_data_admissions']['count'] == 4
        sequences = identity_state(dc, 'birja_source_test')
        if revision == '0011':
            # A real independent writer advances an identity AFTER the snapshot
            # manifest read, immediately before pg_dump captures SEQUENCE SET.
            wrapper = session.root / 'docker'
            injection = dc + ['exec','-T','postgres','psql','-XqAt','-v','ON_ERROR_STOP=1','-U',r.BOOT,'-d','birja_source_test','-c',"SELECT nextval('users_id_seq')"]
            wrapper.write_text('#!/usr/bin/python3\nimport subprocess,sys,os\na=sys.argv[1:]\nif "pg_dump" in a and "--version" not in a: subprocess.run(' + repr(injection) + ',check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)\nos.execv("/usr/bin/docker",["docker",*a])\n')
            wrapper.chmod(0o700)
        sid = recovery_roundtrip(session, source_revision=revision, source_release=release)
        if revision == '0011':
            session.root.joinpath('docker').write_text('#!/bin/bash\nexec /usr/bin/docker "$@"\n')
            before_writer = sequences['users']
            sequences = identity_state(dc, 'birja_source_test')
            assert sequences['users'] != before_writer
        config_hash = r.digest(session.config_path)
        directory = session.root / ('retrieved-' + revision)
        directory.mkdir(mode=0o700)
        producer = r.backup_module()
        job = producer.Job(producer.load_config(['--synthetic',str(session.config_path)]))
        job.restic('restore', sid, '--target', str(directory), '--verify')
        manifest = json.loads((directory / 'manifest.json').read_text())
        if revision == '0011':
            assert next(row for row in manifest['identity_state'] if row[0]=='users')[1:] == [int(sequences['users'].decode().split('|')[0]), True]
            before['identity_state'] = manifest['identity_state']
        assert all(manifest[key] == before[key] for key in ('tables','financial','revision','schema'))
        with r.restored(dc, (directory / 'database.dump').read_bytes()):
            r.verify(dc, manifest)
            assert identity_state(dc, r.CLONE) == sequences
            if revision == '0011':
                accounting_negative_controls(dc, manifest)
            if revision == '0012':
                resolution_negative_controls(dc, manifest)
                # Fixture-only network entry after authority verification; no
                # function/table privilege repair or application access.
                r.sql(dc,'GRANT CONNECT ON DATABASE birja_restore_test TO birja_operator_restore_fixture','birja_ops_test')
                output=role_python(RESOLUTION_SCENARIO + RECOVERY_REPLAY_SCENARIO.replace('REPLAY_REQUEST',repr(request)), 'birja_migrator')
                assert b'restored_split_decision_replay_no_second_effect=true' in output
                r.verify(dc,manifest)
            if revision in ('0009','0010','0011','0012'):
                r.sql(dc, "UPDATE stock_data_admissions SET generation=generation+1 WHERE product='calendar'")
                try:
                    r.verify(dc, manifest)
                except ValueError:
                    pass
                else:
                    raise AssertionError('changed authoritative calendar generation accepted')
                r.sql(dc, "UPDATE stock_data_admissions SET generation=generation-1 WHERE product='calendar'")
                r.verify(dc, manifest)
                for table, query in (
                    ('stock_sessions', "INSERT INTO stock_sessions(exchange,session_date,coverage_start,coverage_end,calendar_admission_generation) VALUES ('NYSE','2026-12-01','2026-11-01','2026-12-01',3) RETURNING id"),
                    ('stock_data_admissions', "INSERT INTO stock_data_admissions(product) VALUES ('reference') RETURNING id"),
                ):
                    value, called = sequences[table].decode().split('|')
                    expected = int(value) + (called == 't')
                    assert int(r.sql(dc, query).strip()) == expected
        assert r.canonical(dc, 'birja_source_test') == before
        assert identity_state(dc, 'birja_source_test') == sequences
        assert r.digest(session.config_path) == config_hash
        assert all(r.digest(session.root / path) == digest for path,digest in unchanged.items())
        assert r.call(dc + ['ps','-q','postgres']).strip() == source_container
        assert r.call(['/usr/bin/docker','inspect','--format','{{json .Mounts}}',source_container.decode()]) == source_mounts
        shutil.rmtree(directory)
        print(f'retained_revision={revision} exact_rows_schema_sequences=true source_identity_unchanged=true stock_authority_repaired=false', flush=True)


def resolution_negative_controls(dc, manifest):
    contract=r.backup_module()
    for label,query in (
        ('public_execute','GRANT EXECUTE ON FUNCTION '+contract.RESOLUTION_SIGNATURE+' TO PUBLIC'),
        ('operator_login','ALTER ROLE birja_action_operator LOGIN'),
        ('operator_outgoing','GRANT birja_scheduler TO birja_action_operator'),
        ('operator_read_missing','REVOKE SELECT ON stock_action_resolutions FROM birja_action_operator'),
        ('operator_column_basis','GRANT UPDATE(cost_basis) ON holdings TO birja_action_operator'),
        ('operator_column_action','GRANT UPDATE(reason) ON stock_action_revisions TO birja_action_operator'),
        ('operator_column_cash','GRANT SELECT(cash) ON accounts TO birja_action_operator'),
        ('operator_delegation','GRANT SELECT ON stock_action_resolutions TO birja_action_operator WITH GRANT OPTION'),
        ('operator_catalogue','GRANT SELECT ON coins TO birja_action_operator'),
        ('wrong_owner','ALTER FUNCTION '+contract.RESOLUTION_SIGNATURE+' OWNER TO '+r.BOOT),
        ('function_configuration','ALTER FUNCTION '+contract.RESOLUTION_SIGNATURE+" SET search_path TO public"),
        ('function_body',"CREATE OR REPLACE FUNCTION "+contract.RESOLUTION_SIGNATURE.replace('bigint,bigint,bigint,bigint,bigint,text,text,text,jsonb,text',
            'p_coin bigint,p_event bigint,p_revision bigint,p_generation bigint,p_epoch bigint,p_key text,p_decision text,p_hash text,p_evidence jsonb,p_actor text')+
            " RETURNS bigint LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,public AS 'SELECT 1::bigint'"),
    ):
        print('resolution_authority_corruption='+label,flush=True)
        # Deliberate corruption is privileged fixture setup, never a grant to
        # the restricted clone owner. Target the actual clone, not the source
        # or bootstrap database; transaction rollback preserves its authority.
        raw=r.call(dc+['exec','-T','postgres','psql','-XqAt','-v','ON_ERROR_STOP=1',
            '-U',r.BOOT,'-d',r.CLONE],
            ('BEGIN; '+query+"; SET LOCAL TIME ZONE 'UTC'; "+contract.manifest_sql('0012')+'; ROLLBACK;').encode())
        try:contract.validate_manifest(json.loads(raw))
        except ValueError:pass
        else:raise AssertionError('changed0012authority accepted: '+label)
    damaged=copy.deepcopy(manifest)
    damaged['resolution_authority']['definition']+='\n-- attacker self-hash claim'
    damaged['resolution_authority']['definition_sha256']=__import__('hashlib').sha256(damaged['resolution_authority']['definition'].encode()).hexdigest()
    try:contract.validate_manifest(damaged)
    except ValueError:pass
    else:raise AssertionError('self-reported changed function accepted')
    print('resolution_authority_corruptions=13 fixed_definition_owner_acl_nologin=true',flush=True)


def accounting_negative_controls(dc, manifest):
    """Corrupt only the disposable restored clone; never source or live state."""
    changes = {
        'stock_action_events': ('first_observed_at', "interval '1 second'"),
        'stock_action_sources': ('provider_event_id', "'changed'"),
        'stock_action_revisions': ('reason', "'changed'"),
        'stock_action_observations': ('cycle_id', "'changed'"),
        'stock_action_state': ('cursor', "'changed'"),
        'stock_ownership_movements': ('recorded_at', "interval '1 second'"),
        'stock_split_applications': ('processed_at', "interval '1 second'"),
        'stock_dividend_entitlements': ('cutoff', "interval '1 second'"),
        'stock_action_resolutions': ('actor_ref', "'changed'"),
    }
    for table, (column, delta) in changes.items():
        is_time = delta.startswith('interval')
        r.sql(dc, f"UPDATE {table} SET {column}={column}" + ('+' if is_time else '||') + delta)
        try:
            r.verify(dc, manifest)
        except ValueError:
            pass
        else:
            raise AssertionError('accounting corruption accepted: ' + table)
        r.sql(dc, f"UPDATE {table} SET {column}=" + (column + '-' + delta if is_time else f"left({column},length({column})-7)"))
        r.verify(dc, manifest)
    for table, value, called in manifest['identity_state']:
        r.sql(dc, f"SELECT setval('{table}_id_seq',{value + 1},true)")
        try:
            r.verify(dc, manifest)
        except ValueError:
            pass
        else:
            raise AssertionError('accounting identity change accepted: ' + table)
        r.sql(dc, f"SELECT setval('{table}_id_seq',{value},{str(called).lower()})")
    r.verify(dc, manifest)
    # Replaying this economic application must still conflict after recovery.
    result = subprocess.run(dc + ['exec','-T','postgres','psql','-XqAt','-v','ON_ERROR_STOP=1','-v','VERBOSITY=sqlstate','-U',r.BOOT,'-d',r.CLONE], input=b"INSERT INTO stock_split_applications(coin_id,economic_event_id,revision_id,new_rate,old_rate,cutoff,prior_unit_epoch,new_unit_epoch,sequence_boundary,before_digest,after_digest,processed_at) SELECT coin_id,economic_event_id,revision_id,new_rate,old_rate,cutoff,prior_unit_epoch,new_unit_epoch,sequence_boundary,before_digest,after_digest,processed_at FROM stock_split_applications", capture_output=True, env=r.ENV, timeout=15)
    assert result.returncode != 0 and b'23505' in result.stderr
    # Failed INSERT consumes an identity; restore it explicitly in this clone.
    value, called = next((v,c) for t,v,c in manifest['identity_state'] if t=='stock_split_applications')
    r.sql(dc, f"SELECT setval('stock_split_applications_id_seq',{value},{str(called).lower()})")
    r.verify(dc, manifest)
    print('accounting_restore_corruptions=9 exact_identity_corruptions=17 duplicate_application_refused=true held_cancelled_alias_cursor_epochs_preserved=true', flush=True)


def roundtrip(archive_arg=None):
    dc = r.compose()
    started = time.monotonic()
    with installed_recovery(archive_arg) as session:
        root, archive, sha = session.root, session.archive, session.archive_sha
        tools = session.tools
        c = json.loads(session.config_path.read_text())
        old = root / "old"
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
            unchanged = {
                str(p.relative_to(root)): r.digest(p)
                for p in old.rglob("*")
                if p.is_file()
            }
            unchanged["credentials"] = r.digest(root / "credentials")
            before = r.canonical(dc, "birja_source_test")
            wrapper = root / "docker"
            wrapper.write_text(
                '#!/usr/bin/python3\nimport subprocess,sys\na=sys.argv[1:]\nif any(x.startswith("--snapshot=") for x in a):\n subprocess.run(["/usr/bin/docker","compose","--env-file","/dev/null","-p","birja-ops-test","-f",'
                + repr(str(old / "docker-compose.ops-test.yml"))
                + ',"exec","-T","postgres","psql","-XqAt","-v","ON_ERROR_STOP=1","-U","birja_ops_bootstrap","-d","birja_source_test","-c","INSERT INTO users(email) VALUES (\'writer-after-export@example.invalid\') ON CONFLICT(email) DO NOTHING;"],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)\nsubprocess.run(["/usr/bin/docker",*a],check=True)\n'
            )
            wrapper.chmod(0o700)
            target(
                root, ["python3", "-c", f"open({str(ROOT / 'CLAUDE.md')!r})"], ok=False
            )
            print("feature_checkout_denied=true")
            sid = recovery_roundtrip(
                session, source_revision="0007", source_release=c["release"]
            )
            assert (
                r.canonical(dc, "birja_source_test")["tables"]["users"]["count"]
                == before["tables"]["users"]["count"] + 1
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
            recovery_roundtrip(
                session, source_revision="0007", source_release=c["release"]
            )
            assert all(r.digest(root / p) == h for p, h in unchanged.items())
            assert r.canonical(dc, "birja_source_test")["revision"] == "0007"
            print("old_checkout_credentials_compose_revision_unchanged=true")
            # The deliberate legacy concurrent writer has already been proven.
            # Even ON CONFLICT consumes identity values; successor equality is
            # intentionally measured with no writers in this isolated source.
            wrapper.write_text('#!/bin/bash\nexec /usr/bin/docker "$@"\n')
            successor_roundtrips(dc, session, unchanged)
            assert r.canonical(dc, "birja_source_test")["revision"] == "0012", "retained recovery rehearsal never exercised populated accounting state"
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
    result = subprocess.run(
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
            *([] if code == SEED else ["-v", str(ROOT / "backend/app") + ":/app/app:ro"]),
            "-v",
            str(ROOT / "backend/alembic") + ":/app/alembic:ro",
            "birja-backend-test:phase05-07",
            "-",
        ],
        input=code.encode(), capture_output=True, env=r.ENV, timeout=120,
    )
    assert result.returncode == 0, "synthetic role client: " + result.stderr.decode()[-2500:]
    return result.stdout


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


def image_transition():
    """Physical clone plus independent logical recovery; original never migrated."""
    project = "birja-image-transition-test"
    old_image = "postgres:18.6-trixie@sha256:bd5dfa494a5a259704365813dbfa5fa6b3e69be7348d43b547f540c730478583"
    original_volume = project + "_original"
    clone_volume = project + "_clone"
    redis_original = project + "_redis_original"
    redis_clone = project + "_redis_clone"
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="birja-backup-test-") as tmp:
        root = Path(tmp)
        root.chmod(0o700)
        config = root / "transition.json"
        environment = {"PGDATA": "/var/lib/postgresql/18/docker", "POSTGRES_USER": r.BOOT,
                       "POSTGRES_PASSWORD": "synthetic-ops-only", "POSTGRES_DB": "birja_source_test",
                       "POSTGRES_INITDB_ARGS": "--locale=en_US.utf8 --locale-provider=libc"}
        common = {"environment": environment, "networks": ["isolated"], "mem_limit": "512m",
                  "cpus": 2, "pids_limit": 128,
                  "healthcheck": {"test": ["CMD", "pg_isready", "-U", r.BOOT, "-d", "birja_source_test"],
                                  "interval": "1s", "timeout": "3s", "retries": 60}}
        services = {
            "original": {**common, "image": old_image, "volumes": ["original:/var/lib/postgresql"]},
            "postgres": {**common, "user": "70:70", "image": r.REGISTRY_REF, "volumes": ["clone:/var/lib/postgresql"]},
            "fresh": {**common, "user": "70:70", "image": r.REGISTRY_REF, "tmpfs": ["/var/lib/postgresql:size=268435456,uid=70,gid=70,mode=0750"]},
        }
        redis_flags = ["--requirepass", "synthetic-redis-only", "--maxmemory", "64mb",
                       "--maxmemory-policy", "noeviction", "--appendonly", "yes", "--appendfsync", "always"]
        for service, image, volume, command in [
            ("redis-original", "redis:8.8.4-trixie@sha256:a008e2cb5579f3616b29bd9e9913a25f16ec09ae2f56ddab524664663b581228", "redis_original", ["redis-server", *redis_flags]),
            ("redis", "cgr.dev/chainguard/redis@sha256:26bb2dd4412f902f3decd44fba5dfaef4360d97004d44f6cff7f28d6aba19c48", "redis_clone", redis_flags),
        ]:
            services[service] = {"image": image, "command": command, "volumes": [volume + ":/data"],
                                 "networks": ["isolated"], "mem_limit": "128m", "cpus": 1, "pids_limit": 64,
                                 "healthcheck": {"test": ["CMD-SHELL", "REDISCLI_AUTH=synthetic-redis-only redis-cli ping | grep PONG"],
                                                 "interval": "1s", "timeout": "3s", "retries": 30}}
        config.write_text(json.dumps({"name": project, "services": services,
                                      "volumes": {name: {} for name in ["original", "clone", "redis_original", "redis_clone"]},
                                      "networks": {"isolated": {"internal": True}}}))
        dc = ["/usr/bin/docker", "compose", "--env-file", "/dev/null", "-p", project, "-f", str(config)]

        def query(service, sql):
            return r.call(dc + ["exec", "-T", service, "psql", "-XqAt", "-v", "ON_ERROR_STOP=1",
                                "-U", r.BOOT, "-d", "birja_source_test"], sql.encode()).strip()

        def redis(service, *args, auth=True):
            return r.call(dc + ["exec", "-T", *(["-e", "REDISCLI_AUTH=synthetic-redis-only"] if auth else []),
                                service, "redis-cli", *args]).strip()

        def canonical(service):
            revision = query(service, "SELECT version_num FROM alembic_version").decode()
            contract = r.backup_module()
            data = json.loads(query(service, "SET TIME ZONE 'UTC';\n" + contract.schema_guard_sql(revision) + contract.manifest_sql(revision)))
            # Debian appends its package build to server_version. Existing
            # recovery equality compares schema/data/money/revision, not that
            # distro label; actual PG/libc majors are separately checked.
            assert data.pop("server_version").startswith("18.6")
            return data

        def readonly_original_fingerprint(volume=original_volume):
            assert volume in {original_volume, redis_original}
            data = r.call(["/usr/bin/docker", "run", "--rm", "--network", "none", "--read-only",
                           "--mount", "type=volume,source=" + volume + ",target=/original,readonly",
                           "--entrypoint", "sh", r.REGISTRY_REF, "-c",
                           "find /original -type f -exec sha256sum '{}' ';' | sort"])
            return __import__("hashlib").sha256(data).digest()

        # Same SQL as privileged helper, executed read-only in this fixed fixture.
        embedded = (ROOT / "deploy/configure-db.sh").read_text().split("<<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]
        embedded = embedded.rsplit("\ntry:\n    main()", 1)[0]
        scope = {"__name__": "contract"}
        exec(compile(embedded, "configure-db.sh", "exec"), scope)
        check = scope["COLLATION_PREFLIGHT"]
        # Reject collisions before entering cleanup: never adopt another run.
        for kind in ["container", "volume", "network"]:
            assert not r.call(["/usr/bin/docker", kind, "ls", "-q", "--filter", "label=com.docker.compose.project=" + project]).strip()
        for volume in [original_volume, clone_volume, redis_original, redis_clone]:
            assert not r.call(["/usr/bin/docker", "volume", "ls", "-q", "--filter", "name=^" + volume + "$"]).strip()
        try:
            r.call(dc + ["up", "-d", "--wait", "original", "redis-original"], timeout=120)
            assert r.call(dc + ["exec", "-T", "redis-original", "stat", "-c", "%u", "/data"]).strip() == b"999"
            assert redis("redis-original", "SET", "birja:transition:proof", "aof-preserved", "EX", "600") == b"OK"
            r.call(dc + ["stop", "redis-original"])
            redis_hash = readonly_original_fingerprint(redis_original)
            r.call(["/usr/bin/docker", "run", "--rm", "--network", "none", "--read-only",
                    "--mount", "type=volume,source=" + redis_original + ",target=/original,readonly",
                    "--mount", "type=volume,source=" + redis_clone + ",target=/clone",
                    "--entrypoint", "sh", r.REGISTRY_REF, "-c",
                    "cp -a /original/. /clone/ && chown -R 65532:65532 /clone"], timeout=60)
            r.call(dc + ["up", "-d", "--wait", "redis"], timeout=60)
            assert b"NOAUTH" in redis("redis", "PING", auth=False)
            assert redis("redis", "GET", "birja:transition:proof") == b"aof-preserved"
            assert int(redis("redis", "TTL", "birja:transition:proof")) > 0
            assert redis("redis", "CONFIG", "GET", "maxmemory-policy").splitlines()[-1] == b"noeviction"
            assert redis("redis", "CONFIG", "GET", "appendonly").splitlines()[-1] == b"yes"
            assert r.call(dc + ["exec", "-T", "redis", "id", "-u"]).strip() == b"65532"
            assert b"Uid:\t65532\t65532\t65532\t65532" in r.call(dc + ["exec", "-T", "redis", "cat", "/proc/1/status"])
            r.call(dc + ["stop", "redis"])
            r.call(dc + ["up", "-d", "--wait", "redis"], timeout=60)
            assert redis("redis", "GET", "birja:transition:proof") == b"aof-preserved"
            assert readonly_original_fingerprint(redis_original) == redis_hash
            r.call(dc + ["up", "-d", "--wait", "redis-original"], timeout=60)
            assert redis("redis-original", "GET", "birja:transition:proof") == b"aof-preserved"
            print("redis_aof_clone_uid65532=true auth_denial=true noeviction=true persistence_restart=true untouched_original_abort=true")
            assert b"2.41" in r.call(dc + ["exec", "-T", "original", "ldd", "--version"])
            assert r.call(dc + ["exec", "-T", "original", "stat", "-c", "%u", environment["PGDATA"]]).strip() == b"999"
            seed = ["/usr/bin/docker", "run", "--rm", "-i", "--network", project + "_isolated"]
            for key, value in {"ENV": "test", "DATABASE_URL": "postgresql+asyncpg://" + r.BOOT + ":synthetic-ops-only@original:5432/birja_source_test",
                               "REDIS_URL": "redis://localhost/0", "OTP_HMAC_SECRET": "synthetic-only-otp-secret-00000000000000",
                               "JWT_SECRET": "synthetic-only-jwt-secret-00000000000000", "EMAIL_BACKEND": "console"}.items():
                seed += ["-e", key + "=" + value]
            r.call(seed + ["--entrypoint", "python", "birja-backend-test:phase05-07", "-"], SEED.encode())
            query("original", "CREATE COLLATION public.transition_locale (provider=libc, locale='en_US.utf8'); CREATE SCHEMA transition_fixture; CREATE TABLE transition_fixture.locale_probe(value text COLLATE public.transition_locale PRIMARY KEY); INSERT INTO transition_fixture.locale_probe VALUES ('a'),('A'),('ä'),('å'),('ae'),('é'),('z'),('Z'),('ß'),('ss'),('Ω'),('Ж');")
            before = canonical("original")
            versions = query("original", "SELECT datcollversion FROM pg_database WHERE datname=current_database()")
            assert query("original", check) == b"collation_ok"
            ordered = query("original", "SELECT json_agg(value ORDER BY value) FROM transition_fixture.locale_probe")
            dump = r.call(dc + ["exec", "-T", "original", "pg_dump", "-U", r.BOOT, "-d", "birja_source_test", "-Fc"])
            r.call(dc + ["stop", "original"])
            original_hash = readonly_original_fingerprint()
            refused = subprocess.run(["/usr/bin/docker", "run", "--rm", "--network", "none", "--read-only",
                                      "--user", "70:70", "-e", "PGDATA=/var/lib/postgresql/18/docker",
                                      "-e", "POSTGRES_USER=" + r.BOOT, "-e", "POSTGRES_PASSWORD=synthetic-ops-only",
                                      "-e", "POSTGRES_DB=birja_source_test",
                                      "--mount", "type=volume,source=" + original_volume + ",target=/var/lib/postgresql,readonly",
                                      r.REGISTRY_REF], capture_output=True, timeout=30, env=r.ENV)
            assert refused.returncode != 0 and b"permission denied" in (refused.stdout + refused.stderr).lower()
            assert readonly_original_fingerprint() == original_hash
            r.call(["/usr/bin/docker", "run", "--rm", "--network", "none", "--read-only",
                    "--mount", "type=volume,source=" + original_volume + ",target=/original,readonly",
                    "--mount", "type=volume,source=" + clone_volume + ",target=/clone",
                    "--entrypoint", "sh", r.REGISTRY_REF, "-c",
                    "cp -a /original/. /clone/ && chown -R 70:70 /clone/18/docker"], timeout=120)
            r.call(dc + ["up", "-d", "--wait", "postgres"], timeout=120)
            assert b"2.44" in r.call(dc + ["exec", "-T", "postgres", "ldd", "--version"])
            assert r.call(dc + ["exec", "-T", "postgres", "stat", "-c", "%u", environment["PGDATA"]]).strip() == b"70"
            assert b"Uid:\t70\t70\t70\t70" in r.call(dc + ["exec", "-T", "postgres", "cat", "/proc/1/status"])
            for service in ["original", "postgres", "redis-original", "redis"]:
                cid = r.call(dc + ["ps", "-a", "-q", service]).decode().strip()
                actual = json.loads(r.call(["/usr/bin/docker", "inspect", cid]))[0]
                assert not actual["HostConfig"].get("PortBindings")
                if service == "redis":
                    assert actual["Config"]["Entrypoint"] == ["/usr/bin/redis-server"]
                    assert actual["Config"]["Cmd"] == redis_flags
            drift = query("postgres", check) != b"collation_ok"
            assert canonical("postgres") == before
            # Rebuild BEFORE refreshing either catalog, even when no drift.
            query("postgres", "REINDEX DATABASE birja_source_test")
            query("postgres", "ALTER COLLATION public.transition_locale REFRESH VERSION; ALTER DATABASE birja_source_test REFRESH COLLATION VERSION")
            assert query("postgres", check) == b"collation_ok"
            assert query("postgres", "SET enable_seqscan=off; SELECT json_agg(value ORDER BY value) FROM transition_fixture.locale_probe") == ordered
            assert query("postgres", "SET enable_seqscan=off; SELECT count(*) FROM transition_fixture.locale_probe WHERE value IN ('ä','ß','Ω')") == b"3"
            assert canonical("postgres") == before
            # Full existing money/FK/index/identity verifier on the physical clone.
            # canonical includes complete existing financial/schema invariants;
            # reuse verifier against fixed source DB without changing its target API.
            original_sql = r.sql
            try:
                r.sql = lambda unused, sql, db=r.CLONE: query("postgres", sql)
                r.verify(dc, before)
            finally:
                r.sql = original_sql
            r.call(dc + ["up", "-d", "--wait", "fresh"], timeout=120)
            r.call(dc + ["exec", "-T", "fresh", "pg_restore", "-U", r.BOOT, "-d", "birja_source_test",
                         "--no-owner", "--no-acl", "--exit-on-error", "--single-transaction"], dump)
            assert canonical("fresh") == before
            assert query("fresh", check) == b"collation_ok"
            assert query("fresh", "SELECT json_agg(value ORDER BY value) FROM transition_fixture.locale_probe") == ordered
            assert readonly_original_fingerprint() == original_hash
            r.call(dc + ["stop", "postgres", "fresh"])
            r.call(dc + ["up", "-d", "--wait", "original"], timeout=120)
            assert canonical("original") == before
            assert query("original", check) == b"collation_ok"
            assert query("original", "SELECT datcollversion FROM pg_database WHERE datname=current_database()") == versions
            assert query("original", "SELECT json_agg(value ORDER BY value) FROM transition_fixture.locale_probe") == ordered
            assert r.call(dc + ["exec", "-T", "original", "stat", "-c", "%u", environment["PGDATA"]]).strip() == b"999"
            print("image_transition_populated=true original_uid999_glibc241=true clone_uid70_glibc244=true actual_collation_drift=" + str(drift).lower() + " reindex_before_refresh=true logical_restore=true untouched_original_abort=true")
            print(f"image_transition_seconds={time.monotonic() - started:.3f}")
        finally:
            r.call(dc + ["down", "-v", "--remove-orphans"], timeout=60)
            # The clone is created by the fixed-name helper before Compose sees it.
            for volume in [clone_volume, redis_clone]:
                if r.call(["/usr/bin/docker", "volume", "ls", "-q", "--filter", "name=^" + volume + "$"]).strip():
                    r.call(["/usr/bin/docker", "volume", "rm", volume])
            for kind in ["container", "volume", "network"]:
                assert not r.call(["/usr/bin/docker", kind, "ls", "-q", "--filter", "label=com.docker.compose.project=" + project]).strip()


def stock_role_contract(dc):
    """Actual SQL ownership/ACL proof, independent of the later calendar evaluator."""
    tables = ("stock_instruments", "stock_quotes", "stock_sessions", "stock_data_admissions")
    for role in ("birja_app", "birja_scheduler"):
        for table in tables:
            allowed = {"SELECT"}
            if role == "birja_scheduler" and table in {"stock_quotes", "stock_sessions"}:
                allowed |= {"INSERT", "UPDATE"}
            for privilege in ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER", "MAINTAIN"):
                assert role_sql(dc, f"SELECT has_table_privilege('{role}','{table}','{privilege}')") == (b"t" if privilege in allowed else b"f"), (role, table, privilege)
            assert role_sql(dc, f"SELECT count(*) FROM {table}", role).isdigit()
        for sequence in ("stock_sessions_id_seq", "stock_data_admissions_id_seq"):
            for privilege in ("USAGE", "SELECT", "UPDATE"):
                allowed = role == "birja_scheduler" and sequence == "stock_sessions_id_seq" and privilege == "USAGE"
                assert role_sql(dc, f"SELECT has_sequence_privilege('{role}','{sequence}','{privilege}')") == (b"t" if allowed else b"f")
        for query in (
            "INSERT INTO stock_data_admissions(product) VALUES ('calendar')",
            "UPDATE stock_data_admissions SET reviewed_at=now(), valid_until=now()+interval '1 day' WHERE product='calendar'",
            "UPDATE stock_data_admissions SET calendar=jsonb_build_object('review_valid_until',now()+interval '1 day','overrides',jsonb_build_array(jsonb_build_object('date','2026-11-27','closed',false))) WHERE product='calendar'",
            "UPDATE stock_instruments SET provider_asset_id='forged'",
            "SELECT nextval('stock_data_admissions_id_seq')",
        ):
            role_sql(dc, query, role, denied=True)
    assert role_sql(dc, "SELECT count(*) FROM pg_class WHERE relname IN ('stock_instruments','stock_quotes','stock_sessions','stock_data_admissions','stock_sessions_id_seq','stock_data_admissions_id_seq') AND relowner=(SELECT oid FROM pg_roles WHERE rolname='birja_migrator')") == b"6"
    assert role_sql(dc, "SELECT count(*) FROM pg_class c CROSS JOIN LATERAL aclexplode(c.relacl) a WHERE c.relname IN ('stock_instruments','stock_quotes','stock_sessions','stock_data_admissions','stock_sessions_id_seq','stock_data_admissions_id_seq') AND a.grantee=0") == b"0"
    assert role_sql(dc, "SELECT string_agg(column_name,',' ORDER BY ordinal_position) FROM information_schema.columns WHERE table_schema='public' AND table_name='stock_sessions'") == b"id,exchange,session_date,opens_at,closes_at,coverage_start,coverage_end,calendar_admission_generation"
    role_sql(dc, "INSERT INTO stock_quotes(coin_id,bid,ask,mid,source,feed,event_at,collected_at,session_date,admission_generation) SELECT coin_id,100.00000001,100.00000003,100.00000002,'alpaca','iex','2026-11-10T15:00:00.123456Z','2026-11-10T15:00:01.123456Z','2026-11-10',7 FROM stock_instruments ORDER BY coin_id LIMIT 1 ON CONFLICT(coin_id) DO UPDATE SET collected_at=excluded.collected_at", "birja_scheduler")
    next_id = role_sql(dc, "INSERT INTO stock_sessions(exchange,session_date,coverage_start,coverage_end,calendar_admission_generation) VALUES ('NYSE','2026-11-27','2026-11-01','2026-12-01',999) RETURNING id", "birja_scheduler")
    assert int(next_id) > 0
    role_sql(dc, "UPDATE stock_sessions SET calendar_admission_generation=7 WHERE exchange='NYSE'", "birja_scheduler")
    assert int(role_sql(dc, "INSERT INTO stock_sessions(exchange,session_date,coverage_start,coverage_end,calendar_admission_generation) VALUES ('NASDAQ','2026-11-27','2026-11-01','2026-12-01',7) RETURNING id", "birja_scheduler")) == int(next_id) + 1
    for table in ("stock_quotes", "stock_sessions"):
        role_sql(dc, f"INSERT INTO {table} DEFAULT VALUES", "birja_app", denied=True)
        role_sql(dc, f"UPDATE {table} SET " + ("mid=mid" if table == "stock_quotes" else "calendar_admission_generation=1"), "birja_app", denied=True)
    for field in ("reviewed_at", "review_valid_until", "overrides"):
        result = subprocess.run(dc + ["exec", "-T", "postgres", "psql", "-XqAt", "-v", "ON_ERROR_STOP=1", "-v", "VERBOSITY=sqlstate", "-U", "birja_scheduler", "-d", "birja_source_test"], input=f"UPDATE stock_sessions SET {field}=NULL".encode(), capture_output=True, env=r.ENV, timeout=15)
        assert result.returncode != 0 and b"42703" in result.stderr
    print("stock_sql_acl_exact=true calendar_authority_migrator_only=true sessions_derived_only=true session_identity_advances=true evaluator_proof=required_tls_consumer", flush=True)


def role_manifest(dc):
    # This fixture deliberately owns an unrelated relation. Recovery's strict
    # schema allowlist remains mandatory in recovery lanes, not this ACL test.
    revision = role_sql(dc, "SELECT version_num FROM alembic_version").decode()
    return json.loads(role_sql(dc, "SET TIME ZONE 'UTC';\n" + r.backup_module().manifest_sql(revision)))


def action_role_contract(dc):
    tables = sorted(r.backup_module().ACTION_COLUMNS)
    rows = []
    for role in ('birja_app', 'birja_scheduler', 'birja_action_operator'):
        for table in tables:
            allowed = {'SELECT'}
            if role == 'birja_app' and table == 'stock_ownership_movements':
                allowed.add('INSERT')
            if role == 'birja_scheduler' and table != 'stock_action_resolutions':
                allowed.add('INSERT')
                if table == 'stock_action_state':
                    allowed.add('UPDATE')
            for privilege in ('SELECT','INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER','MAINTAIN'):
                actual = role_sql(dc, f"SELECT has_table_privilege('{role}','{table}','{privilege}')")
                assert actual == (b't' if privilege in allowed else b'f'), (role, table, privilege)
                rows.append((role,table,privilege,actual.decode()))
            if table != 'stock_action_state':
                for privilege in ('USAGE','SELECT','UPDATE'):
                    allowed_sequence = privilege == 'USAGE' and ((role == 'birja_scheduler' and table != 'stock_action_resolutions') or (role == 'birja_app' and table == 'stock_ownership_movements'))
                    actual = role_sql(dc, f"SELECT has_sequence_privilege('{role}','{table}_id_seq','{privilege}')")
                    assert actual == (b't' if allowed_sequence else b'f')
                    rows.append((role,table+'_id_seq',privilege,actual.decode()))
    for column in ('quantity','cost_basis'):
        actual = role_sql(dc, f"SELECT has_column_privilege('birja_scheduler','holdings','{column}','UPDATE')")
        assert actual == (b't' if column == 'quantity' else b'f')
        rows.append(('birja_scheduler','holdings',column,actual.decode()))
    for role in ('birja_app','birja_scheduler'):
        for query in ("UPDATE stock_action_revisions SET reason=reason", "DELETE FROM stock_ownership_movements", "INSERT INTO stock_action_resolutions DEFAULT VALUES", "UPDATE stock_action_resolutions SET decision=decision", "SELECT nextval('stock_action_resolutions_id_seq')", "SET ROLE birja_action_operator"):
            role_sql(dc, query, role, denied=True)
    role_sql(dc, 'UPDATE holdings SET quantity=quantity', 'birja_scheduler')
    role_sql(dc, 'UPDATE holdings SET cost_basis=cost_basis', 'birja_scheduler', denied=True)
    for column in ('id','coin_id','user_id','side','quantity','cash_delta','cash_after','idempotency_key','created_at'):
        actual = role_sql(dc, f"SELECT has_column_privilege('birja_scheduler','trades','{column}','SELECT')")
        assert actual == (b't' if column in ('id','coin_id','user_id','side','quantity','cash_delta') else b'f')
        rows.append(('birja_scheduler','trades',column,actual.decode()))
    role_sql(dc, 'SELECT id,coin_id,user_id,side,quantity,cash_delta FROM trades LIMIT 0','birja_scheduler')
    for query in ('SELECT * FROM trades','SELECT cash_after FROM trades','UPDATE trades SET quantity=quantity','DELETE FROM trades','INSERT INTO trades DEFAULT VALUES'):
        role_sql(dc,query,'birja_scheduler',denied=True)
    assert role_sql(dc, "SELECT NOT (rolcanlogin OR rolsuper OR rolcreatedb OR rolcreaterole OR rolinherit OR rolreplication OR rolbypassrls) FROM pg_roles WHERE rolname='birja_action_operator'") == b't'
    signature=r.backup_module().RESOLUTION_SIGNATURE
    for role in ('birja_app','birja_scheduler','birja_action_operator'):
        allowed=role=='birja_action_operator'
        assert role_sql(dc,"SELECT has_function_privilege('"+role+"','"+signature+"','EXECUTE')") == (b't' if allowed else b'f')
        rows.append((role,'resolution_function','EXECUTE',str(allowed)))
    for column in ('id','symbol','asset_class','is_active','sort_order','name','kraken_pair'):
        allowed=column in ('id','symbol','asset_class','is_active','sort_order')
        assert role_sql(dc,f"SELECT has_column_privilege('birja_action_operator','coins','{column}','SELECT')") == (b't' if allowed else b'f')
    role_sql(dc,'SELECT * FROM coins','birja_action_operator',denied=True)
    for table in ('accounts','holdings','trades'):
        role_sql(dc,'SELECT * FROM '+table,'birja_action_operator',denied=True)
    return rows


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
            assert role_manifest(dc)["revision"] == "0007"
            role_python("from alembic import command\nfrom alembic.config import Config\ncommand.upgrade(Config('/app/alembic.ini'),'0008')")
            role_sql(
                dc,
                "CREATE TABLE public.unrelated_fixture(id bigint GENERATED ALWAYS AS IDENTITY, marker text); INSERT INTO unrelated_fixture(marker) VALUES ('untouched')",
            )
            role_sql(dc, "CREATE COLLATION public.role_fixture_locale (provider=libc, locale='en_US.utf8'); CREATE INDEX role_fixture_locale_idx ON unrelated_fixture(marker COLLATE role_fixture_locale)")
            owner_query = "SELECT count(*) FROM pg_class WHERE relnamespace='public'::regnamespace AND relname IN ('users','accounts','auth_sessions','refresh_tokens','coins','prices','holdings','trades','alembic_version') AND relowner=(SELECT oid FROM pg_roles WHERE rolname='%s')"
            assert role_sql(dc, owner_query % r.BOOT) == b"9"
            identities = "SELECT c.relname,s.relname,d.deptype FROM pg_class c JOIN pg_attribute a ON a.attrelid=c.oid AND a.attidentity='a' JOIN pg_depend d ON d.refobjid=c.oid AND d.refobjsubid=a.attnum AND d.deptype='i' JOIN pg_class s ON s.oid=d.objid WHERE c.relnamespace='public'::regnamespace AND c.relname!='unrelated_fixture' ORDER BY c.relname"
            before_identity = role_sql(dc, identities)
            assert len(before_identity.splitlines()) == 7
            before = role_manifest(dc)
            if red_probe:
                assert role_sql(dc, owner_query % "birja_migrator") == b"9", (
                    "populated application objects lack restricted migration ownership"
                )
                return
            # Inspection preflights the populated schema without mutation.
            r.call(admin + ["--inspect"])
            assert role_sql(dc, owner_query % r.BOOT) == b"9"
            # Synthetic catalog negatives must stop BEFORE privileged roles.
            for version in ("'synthetic-mismatch'", "NULL"):
                role_sql(dc, "UPDATE pg_database SET datcollversion=" + version + " WHERE datname=current_database()")
                rejected(admin + approved)
                assert role_sql(dc, "SELECT count(*) FROM pg_roles WHERE rolname='birja_app'") == b"0"
                role_sql(dc, "REINDEX DATABASE birja_source_test")
                if version == "NULL":
                    # Restore the deliberately removed synthetic catalog value;
                    # PG refuses REFRESH from NULL. Never a production path.
                    role_sql(dc, "UPDATE pg_database SET datcollversion=pg_database_collation_actual_version(oid) WHERE datname=current_database()")
                else:
                    role_sql(dc, "ALTER DATABASE birja_source_test REFRESH COLLATION VERSION")
                role_sql(dc, "UPDATE pg_collation SET collversion=" + version + " WHERE oid='public.role_fixture_locale'::regcollation")
                rejected(admin + approved)
                assert role_sql(dc, "SELECT count(*) FROM pg_roles WHERE rolname='birja_app'") == b"0"
                role_sql(dc, "REINDEX INDEX role_fixture_locale_idx")
                if version == "NULL":
                    role_sql(dc, "UPDATE pg_collation SET collversion=pg_collation_actual_version(oid) WHERE oid='public.role_fixture_locale'::regcollation")
                else:
                    role_sql(dc, "ALTER COLLATION public.role_fixture_locale REFRESH VERSION")
            role_sql(dc, "INSERT INTO unrelated_fixture(marker) VALUES ('untouched')")
            invalid = subprocess.run(dc + ["exec", "-T", "postgres", "psql", "-XqAt", "-v", "ON_ERROR_STOP=1", "-U", r.BOOT, "-d", "birja_source_test"], input=b"CREATE UNIQUE INDEX CONCURRENTLY role_fixture_invalid ON unrelated_fixture(marker)", capture_output=True, timeout=30, env=r.ENV)
            assert invalid.returncode != 0
            rejected(admin + approved)
            assert role_sql(dc, "SELECT count(*) FROM pg_roles WHERE rolname='birja_app'") == b"0"
            role_sql(dc, "DROP INDEX role_fixture_invalid")
            role_sql(dc, "DELETE FROM unrelated_fixture WHERE id=(SELECT max(id) FROM unrelated_fixture)")
            print("collation_mismatch_unknown_rejected_before_roles=true")
            r.call(
                admin + ["--apply", "--approved-operation", "populated-role-transition"]
            )
            assert role_sql(dc, owner_query % "birja_migrator") == b"9"
            assert role_sql(dc, identities) == before_identity
            assert role_manifest(dc) == before
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
                assert role_manifest(dc) == before
            assert role_manifest(dc) == before
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
            assert role_sql(dc, "SELECT version_num FROM alembic_version") == b"0012"
            after = role_manifest(dc)
            assert after['financial'] == before['financial']
            assert all(after['tables'][table] == state for table,state in before['tables'].items() if table not in {'coins','alembic_version'})
            stock_role_contract(dc)
            upgraded_action_acl = action_role_contract(dc)
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
                    if table == 'holdings' and query in ('SELECT * FROM holdings', 'UPDATE holdings SET quantity=quantity'):
                        role_sql(dc, query, 'birja_scheduler')
                    else:
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
            # A separate fresh schema must receive the same explicit stock ACLs.
            # Prior migration grants cannot mask an incomplete bootstrap.
            r.sql(dc, "DROP DATABASE birja_source_test WITH (FORCE)", "birja_ops_test")
            r.sql(dc, "CREATE DATABASE birja_source_test", "birja_ops_test")
            role_python(SEED)
            role_python("from alembic import command\nfrom alembic.config import Config\ncommand.upgrade(Config('/app/alembic.ini'),'head')")
            r.call(admin + approved)
            stock_role_contract(dc)
            assert action_role_contract(dc) == upgraded_action_acl
            print('accounting_acl_upgrade_fresh_parity=true operator_nologin=true immutable_audit_denied=true quantity_only_scheduler=true', flush=True)
            print(
                f"roles_populated_transfer=true fresh_bootstrap_parity=true identity_dependencies=true concurrent_0008_valid=true runtime_services=true scheduler_upsert=true denied_operations={negatives}"
            )
            print(
                f"fixture_setup_seconds={setup_done - started:.3f} roles_integration_seconds={time.monotonic() - started:.3f}"
            )
        finally:
            r.call(dc + ["down", "-v", "--remove-orphans"], timeout=60)
            assert r.call(dc + ["ps", "-q"]).strip() == b""


STOCK_TLS_CALENDAR = r"""
import asyncio, json
from dataclasses import asdict, fields, replace
from datetime import UTC, datetime, timedelta
import asyncpg
from app.core.config import SchedulerSettings
from app.db.connection import database_connect_args
from app.services.stock_admission import ProductAdmission
from app.services.stock_sessions import RegularSession, build_sessions, session_at

async def calendar_consumer_contract(app,scheduler,migrator):
 now=datetime(2026,11,10,15,tzinfo=UTC)
 authority=ProductAdmission(product='calendar',state='approved',generation=4,
  reviewed_at=now-timedelta(hours=1),valid_from=now-timedelta(hours=2),valid_until=now+timedelta(hours=8),
  evidence_ref='secure-review:synthetic-only',terms_version='synthetic-v1',collection_allowed=True,
  display_allowed=True,derived_allowed=True,retention_allowed=True,
  scope={'application':'birja','audience':'authenticated-users','account':'birja','server':'birja','feed':'iex'},
  quota={'requests_per_minute':20,'symbols_per_request':20,'max_response_bytes':262144,'retention_seconds':86400},
  allowed_fields=['exchange','session_date','opens_at','closes_at'],attribution='IEX prices',
  calendar={'exchanges':['XNYS','XNAS'],'version':'exchange-calendars-4.13.2/official-2026',
   'sources':['https://www.nyse.com/trade/hours-calendars','https://www.nasdaq.com/market-activity/stock-market-holiday-schedule'],
   'review_valid_until':(now+timedelta(hours=8)).isoformat(),
   'coverage_start':(now.date()-timedelta(days=45)).isoformat(),
   'coverage_end':(now.date()+timedelta(days=90)).isoformat(),'overrides':[]})
 await migrator.execute('DELETE FROM stock_sessions')
 await migrator.execute("DELETE FROM stock_data_admissions WHERE product='calendar'")
 names=list(asdict(authority))
 values=[json.dumps(v) if isinstance(v,(dict,list)) else v for v in asdict(authority).values()]
 await migrator.execute('INSERT INTO stock_data_admissions('+','.join(names)+') VALUES ('+','.join('$'+str(i+1) for i in range(len(names)))+')',*values)
 async def current():
  record=dict(await app.fetchrow("SELECT * FROM stock_data_admissions WHERE product='calendar'"))
  for name in ('scope','quota','allowed_fields','calendar'): record[name]=json.loads(record[name])
  return ProductAdmission(**{f.name:record[f.name] for f in fields(ProductAdmission)})
 async def decision():
  records=await app.fetch('SELECT exchange,session_date,opens_at,closes_at,coverage_start,coverage_end,calendar_admission_generation FROM stock_sessions ORDER BY exchange,session_date')
  rows=[RegularSession(**dict(row)) for row in records]
  return session_at('NYSE',now,rows,await current()).state
 async def refresh(evidence):
  rows=build_sessions(now,evidence)
  assert len(rows)==272
  await scheduler.executemany('INSERT INTO stock_sessions(exchange,session_date,opens_at,closes_at,coverage_start,coverage_end,calendar_admission_generation) VALUES ($1,$2,$3,$4,$5,$6,$7) ON CONFLICT(exchange,session_date) DO UPDATE SET opens_at=excluded.opens_at,closes_at=excluded.closes_at,coverage_start=excluded.coverage_start,coverage_end=excluded.coverage_end,calendar_admission_generation=excluded.calendar_admission_generation',[tuple(asdict(row).values()) for row in rows])
 await refresh(await current())
 assert await decision()=='open'
 await scheduler.execute('UPDATE stock_sessions SET calendar_admission_generation=999')
 assert await decision()=='unknown'
 await refresh(await current())
 assert await decision()=='open'
 await migrator.execute("UPDATE stock_data_admissions SET generation=5 WHERE product='calendar'")
 assert await decision()=='unknown'
 await refresh(await current())
 assert await decision()=='open'
 # Rewriting derived rows cannot renew the current authoritative review.
 await refresh(await current())
 await migrator.execute("UPDATE stock_data_admissions SET calendar=jsonb_set(calendar,'{review_valid_until}',to_jsonb($1::text)) WHERE product='calendar'",now.isoformat())
 assert await decision()=='unknown'
 await migrator.execute("UPDATE stock_data_admissions SET calendar=jsonb_set(calendar,'{review_valid_until}',to_jsonb($1::text)) WHERE product='calendar'",(now+timedelta(hours=8)).isoformat())
 assert await decision()=='open'
 before=await app.fetchval("SELECT calendar FROM stock_data_admissions WHERE product='calendar'")
 await refresh(await current())
 assert await decision()=='open'
 assert before==await app.fetchval("SELECT calendar FROM stock_data_admissions WHERE product='calendar'")
 for conn in (app,scheduler):
  for query in ["UPDATE stock_data_admissions SET reviewed_at=now()", "UPDATE stock_data_admissions SET calendar='{}'", "UPDATE stock_instruments SET provider_asset_id='forged'"]:
   try: await conn.execute(query)
   except asyncpg.PostgresError as exc: assert exc.sqlstate=='42501'
   else: raise AssertionError('runtime wrote authoritative evidence')
 await migrator.execute('DELETE FROM stock_sessions')

async def main():
 args=database_connect_args(SchedulerSettings())
 connections=[]
 try:
  for role,char in [('app','a'),('scheduler','b'),('migrator','c')]:
   conn=await asyncpg.connect('postgresql://birja_'+role+':'+char*64+'@postgres:5432/birja_source_test',**args)
   assert await conn.fetchval('SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()')
   connections.append(conn)
  app,scheduler,migrator=connections
  await calendar_consumer_contract(app,scheduler,migrator)
 finally:
  for conn in connections: await conn.close()
asyncio.run(main())
print('calendar_runtime_tls_consumer=true forged_generation_refused=true replacement_invalidates=true expired_authority_refused=true same_generation_refresh=true authority_write_denied=true')
"""


STOCK_TLS_UPGRADE = r"""
import asyncio, subprocess
import asyncpg
from app.core.config import SchedulerSettings
from app.db.connection import database_connect_args
async def main():
 s=SchedulerSettings()
 args=database_connect_args(s)
 connections=[]
 try:
  for role,char in [('app','a'),('scheduler','b')]:
   conn=await asyncpg.connect('postgresql://birja_'+role+':'+char*64+'@postgres:5432/birja_source_test',**args)
   assert await conn.fetchval('SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()')
   assert await conn.fetchval('SELECT count(*) FROM coins')==35, 'populated0010 predecessor is mandatory before restricted accounting upgrade'
   connections.append(conn)
  subprocess.run(['alembic','upgrade','head'],check=True,timeout=90)
  app,scheduler=connections
  for table in ['stock_instruments','stock_quotes','stock_sessions','stock_data_admissions']:
   await app.fetch('SELECT * FROM '+table)
  await scheduler.execute("INSERT INTO stock_quotes(coin_id,bid,ask,mid,source,feed,event_at,collected_at,session_date,admission_generation) SELECT coin_id,100,102,101,'alpaca','iex','2026-11-10T15:00Z','2026-11-10T15:00:01Z','2026-11-10',1 FROM stock_instruments ORDER BY coin_id LIMIT 1")
  identity=await scheduler.fetchval("INSERT INTO stock_sessions(exchange,session_date,coverage_start,coverage_end,calendar_admission_generation) VALUES ('NYSE','2026-11-10','2026-11-01','2026-12-01',999) RETURNING id")
  assert identity==1
  await scheduler.execute("UPDATE stock_sessions SET calendar_admission_generation=1 WHERE id=1")
  for conn in connections:
   for query in ["UPDATE stock_data_admissions SET reviewed_at=now()", "UPDATE stock_data_admissions SET calendar='{}'", "UPDATE stock_instruments SET provider_asset_id='forged'", "SELECT nextval('stock_data_admissions_id_seq')", "CREATE TABLE forbidden_tls(id bigint)", "SET ROLE birja_migrator"]:
    try: await conn.execute(query)
    except asyncpg.PostgresError as exc: assert exc.sqlstate=='42501'
    else: raise AssertionError('restricted TLS role escalated')
  await scheduler.execute("UPDATE holdings SET quantity=quantity")
  for query in ["UPDATE accounts SET cash=cash", "UPDATE holdings SET cost_basis=cost_basis", "UPDATE trades SET fee=fee"]:
   try: await scheduler.execute(query)
   except asyncpg.PostgresError as exc: assert exc.sqlstate=='42501'
   else: raise AssertionError('scheduler obtained financial writes')
 finally:
  for conn in connections: await conn.close()
asyncio.run(main())
print('existing_tls_connections_immediate_stock_grants=true no_postupgrade_grant_repair=true')
"""


ACTION_TLS_CONSUMER = r"""
import asyncio,uuid
import asyncpg
from app.core.config import SchedulerSettings
from app.db.connection import database_connect_args
async def main():
 args=database_connect_args(SchedulerSettings())
 connections=[]
 try:
  for role,char in [('app','a'),('scheduler','b')]:
   conn=await asyncpg.connect('postgresql://birja_'+role+':'+char*64+'@postgres:5432/birja_source_test',**args)
   assert await conn.fetchval('SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()')
   connections.append(conn)
  app,scheduler=connections
  cid=await app.fetchval('SELECT min(coin_id) FROM stock_instruments')
  uid=await app.fetchval('SELECT min(id) FROM users')
  transaction=scheduler.transaction(); await transaction.start()
  eid=await scheduler.fetchval('INSERT INTO stock_action_events(coin_id,economic_key,first_observed_at) VALUES ($1,$2,now()) RETURNING id',cid,str(uuid.uuid4()))
  sid=await scheduler.fetchval("INSERT INTO stock_action_sources(event_id,provider,product,provider_event_id) VALUES ($1,'alpaca','actions',$2) RETURNING id",eid,str(uuid.uuid4()))
  rid=await scheduler.fetchval("INSERT INTO stock_action_revisions(event_id,source_id,ordinal,fingerprint,mutation_kind,observed_at,admission_generation,normalized_terms,classification,reason) VALUES ($1,$2,1,$3,'snapshot',now(),1,'{}','uncertain','fixture') RETURNING id",eid,sid,'a'*64)
  await scheduler.execute('UPDATE stock_action_events SET current_revision_id=$1 WHERE id=$2',rid,eid)
  await scheduler.execute("INSERT INTO stock_action_observations(event_id,source_id,revision_id,observed_at,admission_generation,source_kind,cycle_id) VALUES ($1,$2,$3,now(),1,'snapshot','tls-fixture')",eid,sid,rid)
  await scheduler.execute('INSERT INTO stock_action_state(coin_id,admission_generation) VALUES ($1,1)',cid)
  await scheduler.execute('UPDATE holdings SET quantity=quantity')
  await transaction.rollback()
  transaction=app.transaction(); await transaction.start()
  value=await app.fetchval("INSERT INTO stock_ownership_movements(coin_id,user_id,sequence,economic_at,recorded_at,quantity,before_quantity,after_quantity,before_basis,after_basis,unit_epoch,cause_kind,causal_key) VALUES ($1,$2,1,now(),now(),1,0,1,0,10,0,'opening','tls-opening') RETURNING id",cid,uid)
  assert value>0
  await transaction.rollback()
  for conn in connections:
   for query in ["UPDATE stock_action_revisions SET reason=reason", "DELETE FROM stock_ownership_movements", "INSERT INTO stock_action_resolutions DEFAULT VALUES", "UPDATE stock_action_resolutions SET decision=decision", "SELECT nextval('stock_action_resolutions_id_seq')", "SET ROLE birja_action_operator"]:
    try: await conn.execute(query)
    except asyncpg.PostgresError as exc: assert exc.sqlstate=='42501'
    else: raise AssertionError('immutable/operator authority widened')
  for query in ["UPDATE accounts SET cash=cash", "UPDATE holdings SET cost_basis=cost_basis", "UPDATE trades SET fee=fee", "UPDATE stock_data_admissions SET reviewed_at=now()"]:
   try: await scheduler.execute(query)
   except asyncpg.PostgresError as exc: assert exc.sqlstate=='42501'
   else: raise AssertionError('scheduler gained financial/authority mutation')
 finally:
  for conn in connections: await conn.close()
asyncio.run(main())
print('accounting_tls_actual_append=true immutable_denials=true quantity_only=true')
"""


OWNERSHIP_TLS_CONSUMER = r"""
import asyncio,uuid
from datetime import timedelta
from decimal import Decimal
from sqlalchemy import select,func,delete,text
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
from app.core.config import SchedulerSettings
from app.db.connection import database_connect_args
from app.models.stock import StockInstrument
from app.models.user import User
from app.models.trade import Trade,Holding
from app.models.corporate_action import StockActionState,StockOwnershipMovement
from app.services.stock_ownership import append_stock_movement,assert_ownership_consistent,reconstruct_stock_quantity,StockMovementInput
from app.services.corporate_action_rules import CutoffEvidence
async def main():
 args=database_connect_args(SchedulerSettings())
 engines={role:create_async_engine('postgresql+asyncpg://birja_'+role+':'+char*64+'@postgres:5432/birja_source_test',connect_args=args) for role,char in [('app','a'),('scheduler','b'),('migrator','c')]}
 sessions={role:async_sessionmaker(engine,expire_on_commit=False) for role,engine in engines.items()}
 cid=None
 try:
  async with sessions['app']() as db:
   assert (await db.execute(text('SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()'))).scalar_one()
   cid=(await db.execute(select(func.min(StockInstrument.coin_id)))).scalar_one()
   uid=(await db.execute(select(func.min(User.id)))).scalar_one()
  async with sessions['scheduler'].begin() as db:
   now=(await db.execute(select(func.clock_timestamp()))).scalar_one()
   db.add(StockActionState(coin_id=cid,admission_generation=1,health='current',checked_at=now-timedelta(seconds=1),valid_until=now+timedelta(hours=1),journal_start_at=now-timedelta(days=1),complete_from=now-timedelta(days=1)))
  async with sessions['app'].begin() as db:
   now=(await db.execute(select(func.clock_timestamp()))).scalar_one()
   trade=Trade(user_id=uid,coin_id=cid,side='buy',input_kind='quantity',input_value=Decimal(2),quantity=Decimal(2),mid_price=Decimal(10),price_as_of=now,exec_price=Decimal(10),fee=Decimal(0),cash_delta=Decimal(-20),cash_after=Decimal(10000),idempotency_key=uuid.uuid4())
   db.add(trade);await db.flush()
   request=StockMovementInput(uid,cid,Decimal(2),Decimal(20),'tls-fill:'+str(trade.id),trade.id)
   first=await append_stock_movement(db,request)
   assert first.sequence==1 and (await append_stock_movement(db,request)).id==first.id
   now=(await db.execute(select(func.clock_timestamp()))).scalar_one()
   cutoff=CutoffEvidence(now,'NASDAQ',now.date(),1,'synthetic-reviewed-tls-calendar')
   assert (await reconstruct_stock_quantity(db,uid,cid,cutoff,0)).quantity==2
  async with sessions['scheduler'].begin() as db:
   assert (await db.execute(text('SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()'))).scalar_one()
   state,rows=await assert_ownership_consistent(db,cid)
   assert state.unit_epoch==0 and len(rows)==1 and rows[0].after_quantity==2
 finally:
  if cid is not None:
   async with sessions['migrator'].begin() as db:
    await db.execute(delete(StockOwnershipMovement).where(StockOwnershipMovement.coin_id==cid))
    await db.execute(delete(Holding).where(Holding.coin_id==cid))
    await db.execute(delete(Trade).where(Trade.coin_id==cid))
    await db.execute(delete(StockActionState).where(StockActionState.coin_id==cid))
  for engine in engines.values():await engine.dispose()
asyncio.run(main())
print('ownership_tls_actual_app_append_replay_reconstruct=true scheduler_consistency=true six_column_read_only=true')
"""


RESOLUTION_SCENARIO = r"""
import asyncio,json,uuid
from dataclasses import asdict,replace
from datetime import timedelta
from decimal import Decimal
from sqlalchemy import select,text,delete,func
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
from app.models.stock import StockInstrument,StockDataAdmission,StockSession
from app.models.price import Coin
from app.models.corporate_action import StockActionState,StockActionRevision,StockActionObservation,StockActionEvent,StockActionSource,StockActionResolution,StockOwnershipMovement,StockSplitApplication
from app.models.trade import Holding
from app.services.stock_admission import ProductAdmission
from app.services.stock_quote_rules import CURATED_SYMBOLS
from app.services.stock_sessions import build_sessions
from app.services.corporate_action_rules import NormalizedAction
from app.services.alpaca_actions import ActionBatch,ActionObservation
from app.services.corporate_actions import persist_action_batch,apply_due_actions
from app.services.stock_action_reconciliation import ResolutionRequest,reconcile,LEDGER_SQL

async def scenario_authority(db):
 now=(await db.execute(text('SELECT clock_timestamp()'))).scalar_one()
 common=dict(state='approved',generation=8,reviewed_at=now-timedelta(hours=1),
  valid_from=now-timedelta(hours=2),valid_until=now+timedelta(hours=2),
  evidence_ref='synthetic:review',terms_version='synthetic-v1',collection_allowed=True,
  display_allowed=True,derived_allowed=True,retention_allowed=True,attribution='Synthetic action rights',
  scope={'application':'birja','audience':'authenticated-users','account':'birja','server':'birja','feed':'iex'},
  quota={'requests_per_minute':20,'symbols_per_request':20,'max_response_bytes':262144,'retention_seconds':86400})
 auth=ProductAdmission(product='actions',**{**common,'scope':{**common['scope'],
  'feed':'alpaca-corporate-actions','capabilities':['rest','replay'],
  'rest_symbols':sorted(CURATED_SYMBOLS),'all_us_replay_ingress':True,'replay_region':'us',
  'durable_accounting':True,'backup_restore':True,'retention_mode':'durable-accounting'}},
  allowed_fields=['provider_event_id','symbol','event_type','process_date'])
 calendar=ProductAdmission(product='calendar',**common,
  allowed_fields=['exchange','session_date','opens_at','closes_at'],
  calendar={'exchanges':['XNYS','XNAS'],'version':'exchange-calendars-4.13.2/official-2026',
   'sources':['https://www.nyse.com/trade/hours-calendars','https://www.nasdaq.com/market-activity/stock-market-holiday-schedule'],
   'review_valid_until':(now+timedelta(hours=2)).isoformat(),
   'coverage_start':(now.date()-timedelta(days=45)).isoformat(),
   'coverage_end':(now.date()+timedelta(days=90)).isoformat(),'overrides':[]})
 await db.execute(delete(StockDataAdmission).where(StockDataAdmission.product.in_(['actions','calendar'])))
 db.add_all([StockDataAdmission(**asdict(auth)),StockDataAdmission(**asdict(calendar))]);await db.flush()
 return now,auth,calendar

async def scenario(db):
 now,auth,calendar=await scenario_authority(db)
 catalog=(await db.execute(select(StockInstrument).order_by(StockInstrument.coin_id))).scalars().all()
 instrument=catalog[2]
 instrument.provider_asset_id='synthetic-'+str(instrument.coin_id);instrument.provider_verified_at=now-timedelta(days=10)
 sessions=build_sessions(now,calendar)
 opening=next(row for row in sessions if row.exchange==instrument.listing_exchange and row.opens_at and row.opens_at>now)
 if (await db.execute(select(StockSession.id).where(StockSession.exchange==opening.exchange,StockSession.session_date==opening.session_date))).scalar_one_or_none() is None:
  db.add(StockSession(**asdict(opening)))
 symbol=(await db.execute(select(Coin.symbol).where(Coin.id==instrument.coin_id))).scalar_one()
 action=NormalizedAction('synthetic-'+str(uuid.uuid4()),instrument.coin_id,symbol,'cash_dividend',now.date(),now,
  currency='USD',rate=Decimal('.25'),ex_date=opening.session_date,record_date=opening.session_date,
  payable_date=opening.session_date+timedelta(days=5),subtype='ordinary',foreign=False,special=False,
  due_bills=False,identity_verified=True,dates_verified=True)
 async def persist(value):
  return (await persist_action_batch(db,ActionBatch(records=(value,),observations=(ActionObservation(value),),complete=True),auth))[0]
 await persist(replace(action,rate=None));current=await persist(action)
 state=await db.get(StockActionState,instrument.coin_id);revision=await db.get(StockActionRevision,current.revision_id)
 ids=list((await db.execute(select(StockActionRevision.id).where(StockActionRevision.event_id==current.event_id).order_by(StockActionRevision.id))).scalars())
 observation=(await db.execute(select(func.max(StockActionObservation.id)).where(StockActionObservation.event_id==current.event_id))).scalar_one()
 ledger=(await db.execute(text(LEDGER_SQL),{'coin':instrument.coin_id})).scalar_one()
 admission_digest=(await db.execute(text("SELECT encode(sha256(convert_to(to_jsonb(c)::text,'UTF8')),'hex') FROM stock_data_admissions c WHERE product='actions'"))).scalar_one()
 calendar_digest=(await db.execute(text("SELECT encode(sha256(convert_to(to_jsonb(c)::text,'UTF8')),'hex') FROM stock_data_admissions c WHERE product='calendar'"))).scalar_one()
 request=ResolutionRequest.model_validate({'coin_id':instrument.coin_id,'event_id':current.event_id,
  'expected_revision':current.revision_id,'admission_generation':8,'epoch':state.epoch,
  'decision_key':'synthetic-reviewed-'+str(uuid.uuid4()),'decision':'accept_corrected_supported_revision',
  'actor_ref':'synthetic:operator','evidence':{'format':1,'unit_epoch':state.unit_epoch,'ledger_digest':ledger,
   'revision_fingerprint':revision.fingerprint,'held_revision_ids':ids,'observation_id':observation,
   'account':'birja','server':'birja','calendar_generation':8,'calendar_digest':calendar_digest,'admission_digest':admission_digest,
   'review_valid_until':(now+timedelta(minutes=30)).isoformat(),'security_id':instrument.provider_asset_id,
   'cutoff':opening.opens_at.isoformat(),'alias_event_id':None}})
 return request,None,None

async def split_scenario(db,prepare=False):
 from app.services.corporate_actions import _load_admission
 if prepare:now,auth,calendar=await scenario_authority(db)
 else:
  auth=await _load_admission(db,'actions');calendar=await _load_admission(db,'calendar')
  now=(await db.execute(text('SELECT clock_timestamp()'))).scalar_one()
 sessions=build_sessions(now,calendar)
 catalog=(await db.execute(select(StockInstrument).order_by(StockInstrument.coin_id))).scalars().all()
 split_instrument=catalog[1];split_coin=split_instrument.coin_id
 split_instrument.provider_asset_id='synthetic-'+str(split_coin);split_instrument.provider_verified_at=now-timedelta(days=10)
 past=[row for row in sessions if row.exchange==split_instrument.listing_exchange and row.opens_at and row.opens_at<now]
 boundary=past[-1].opens_at;baseline=boundary-timedelta(days=2)
 uid=(await db.execute(text('SELECT min(id) FROM users'))).scalar_one()
 db.add(StockActionState(coin_id=split_coin,admission_generation=8,health='current',checked_at=now-timedelta(seconds=1),valid_until=now+timedelta(hours=1),journal_start_at=baseline,complete_from=baseline,coverage_start=baseline,covered_until=now))
 db.add(Holding(coin_id=split_coin,user_id=uid,quantity=Decimal(2),cost_basis=Decimal(20)))
 db.add(StockOwnershipMovement(coin_id=split_coin,user_id=uid,sequence=1,economic_at=boundary-timedelta(days=1),recorded_at=now,quantity=Decimal(2),before_quantity=Decimal(0),after_quantity=Decimal(2),before_basis=Decimal(0),after_basis=Decimal(20),unit_epoch=0,cause_kind='opening',causal_key='synthetic-recovery-opening'))
 symbol=(await db.execute(select(Coin.symbol).where(Coin.id==split_coin))).scalar_one()
 split=NormalizedAction('synthetic-'+str(uuid.uuid4()),split_coin,symbol,'forward_split',now.date(),now,
   new_rate=Decimal(2),old_rate=Decimal(1),units='pre_split',economic_at=boundary,
   ex_date=boundary.date(),record_date=boundary.date(),payable_date=boundary.date()+timedelta(days=1),
   due_bills=False,identity_verified=True,dates_verified=True)
 await persist_action_batch(db,ActionBatch(records=(split,),observations=(ActionObservation(split),),complete=True),auth)
 application=(await apply_due_actions(db,split_coin,auth))[0]
 return split_coin,application

"""

RECOVERY_SEED_SCENARIO = r"""
import os
async def main():
 engine=create_async_engine(os.environ['DATABASE_URL'])
 try:
  async with async_sessionmaker(engine,expire_on_commit=False).begin() as db:
   request,_,_=await scenario(db)
   resolution=await reconcile(db,request,account='birja',server='birja')
  async with async_sessionmaker(engine,expire_on_commit=False).begin() as db:
   split_coin,application=await split_scenario(db)
  print(json.dumps({'request':request.model_dump(mode='json'),'split_coin':split_coin,'application':application,'resolution':resolution}))
 finally:await engine.dispose()
asyncio.run(main())
"""

RECOVERY_REPLAY_SCENARIO = r"""
import os
from sqlalchemy.engine import make_url
async def main():
 data=REPLAY_REQUEST
 engine=create_async_engine(make_url(os.environ['DATABASE_URL']).set(database='birja_restore_test'))
 operator_engine=create_async_engine(make_url(os.environ['DATABASE_URL']).set(database='birja_restore_test',username='birja_operator_restore_fixture',password='a'*64))
 try:
  async with async_sessionmaker(operator_engine,expire_on_commit=False).begin() as db:
   await db.execute(text('SET LOCAL ROLE birja_action_operator'))
   before=(await db.execute(text('SELECT count(*) FROM stock_action_resolutions'))).scalar_one()
   request=ResolutionRequest.model_validate(data['request'])
   assert await reconcile(db,request,account='birja',server='birja')==data['resolution']
   assert await reconcile(db,request,account='birja',server='birja')==data['resolution']
   assert (await db.execute(text('SELECT count(*) FROM stock_action_resolutions'))).scalar_one()==before
  async with async_sessionmaker(engine,expire_on_commit=False).begin() as db:
   from app.services.corporate_actions import _load_admission
   auth=await _load_admission(db,'actions')
   assert await apply_due_actions(db,data['split_coin'],auth)==(data['application'],)
   assert await apply_due_actions(db,data['split_coin'],auth)==(data['application'],)
  print('restored_split_decision_replay_no_second_effect=true operator_service_reads_exact=true')
 finally:
  await operator_engine.dispose()
  await engine.dispose()
asyncio.run(main())
"""

RESOLUTION_TLS_CONSUMER = r"""
import asyncpg
from app.core.config import SchedulerSettings
from app.db.connection import database_connect_args
async def main():
 args=database_connect_args(SchedulerSettings())
 engines={name:create_async_engine('postgresql+asyncpg://'+name+':'+password+'@postgres:5432/birja_source_test',connect_args=args)
  for name,password in [('birja_migrator','c'*64),('birja_operator_fixture','d'*64)]}
 sessions={name:async_sessionmaker(engine,expire_on_commit=False) for name,engine in engines.items()}
 request=None
 try:
  async with sessions['birja_migrator'].begin() as db:
   request,_,_=await scenario(db)
  async with sessions['birja_operator_fixture'].begin() as db:
   assert (await db.execute(text('SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()'))).scalar_one()
   await db.execute(text('SET LOCAL ROLE birja_action_operator'))
   first=await reconcile(db,request,account='birja',server='birja')
  async with sessions['birja_operator_fixture'].begin() as db:
   await db.execute(text('SET LOCAL ROLE birja_action_operator'))
   assert await reconcile(db,request,account='birja',server='birja')==first
  async with sessions['birja_operator_fixture'].begin() as db:
   await db.execute(text('SET LOCAL ROLE birja_action_operator'))
   try:await reconcile(db,request.model_copy(update={'decision_key':'synthetic-stale'}),account='birja',server='birja')
   except Exception as exc:
    assert getattr(exc.orig,'sqlstate',None)=='22023'
   else:raise AssertionError('stale scoped resolution accepted')
  call='SELECT public.apply_stock_action_resolution(NULL::bigint,NULL::bigint,NULL::bigint,NULL::bigint,NULL::bigint,NULL::text,NULL::text,NULL::text,NULL::jsonb,NULL::text)'
  for role,password in [('birja_app','a'*64),('birja_scheduler','b'*64),('birja_public_fixture','e'*64)]:
   connection=await asyncpg.connect('postgresql://'+role+':'+password+'@postgres:5432/birja_source_test',**args)
   try:
    assert await connection.fetchval('SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()')
    try:await connection.execute(call)
    except asyncpg.PostgresError as exc:assert exc.sqlstate=='42501'
    else:raise AssertionError('runtime/PUBLIC obtained resolution authority')
   finally:await connection.close()
 finally:
  if request is not None:
   async with sessions['birja_migrator'].begin() as db:
    for model in (StockActionResolution,StockActionObservation):
     await db.execute(delete(model).where(model.event_id==request.event_id))
    event=await db.get(StockActionEvent,request.event_id);event.current_revision_id=None;await db.flush()
    await db.execute(delete(StockActionRevision).where(StockActionRevision.event_id==request.event_id))
    await db.execute(delete(StockActionSource).where(StockActionSource.event_id==request.event_id))
    await db.execute(delete(StockActionEvent).where(StockActionEvent.id==request.event_id))
    await db.execute(delete(StockActionState).where(StockActionState.coin_id==request.coin_id))
    instrument=await db.get(StockInstrument,request.coin_id);instrument.provider_asset_id=None;instrument.provider_verified_at=None
    await db.execute(delete(StockDataAdmission).where(StockDataAdmission.product.in_(['actions','calendar'])))
    await db.execute(delete(StockSession).where(StockSession.session_date==request.evidence.cutoff.date(),StockSession.calendar_admission_generation==8))
  for engine in engines.values():await engine.dispose()
asyncio.run(main())
print('resolution_verified_tls_operator_service_replay=true stale_denied=true public_app_scheduler_denied=true')
"""

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


def tls(fresh_bootstrap=False):
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
        assert (root / "db-tls/server/server.key").stat().st_gid == 70
        key = root / "db-tls/server/server.key"
        key.chmod(0o644)
        reject_provision(["--check"])
        reject_provision(
            ["--renew", "--approved-custody", "owner-off-server-password-manager"]
        )
        key.chmod(0o640)
        os.chown(key, 0, 0)
        reject_provision(["--check"])
        os.chown(key, 0, 70)
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
        policy = 'hostssl all birja_operator_fixture,birja_public_fixture samenet scram-sha-256\n' + (ROOT / "deploy/db/pg_hba.conf").read_text()
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
                s["tmpfs"] = ["/var/lib/postgresql:size=268435456,uid=70,gid=70,mode=0750"]
                s["volumes"] = [
                    str(root / "db-tls/server") + ":/run/birja/db-server:ro",
                    str(hba) + ":/run/birja/db-hba:ro",
                ]
            elif name == "redis":
                s["tmpfs"] = ["/data:size=16777216,uid=65532,gid=65532,mode=0750"]
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
            if service == 'migrate':
                # Preserve the real one-shot command's inert Settings fields
                # when replacing only its entrypoint with the test probe.
                command = prod['services']['migrate']['command']
                inert = dict(value.split('=', 1) for value in command[1:] if '=' in value)
                code = 'import os\nos.environ.update(' + repr(inert) + ')\n' + code
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
                "TLS synthetic client assertion failed: " + service + " " + result.stderr.decode()[-1500:]
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
                == b"70"
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
                "import ssl\n engine=create_async_engine(s.database_url,connect_args={'ssl':ssl.create_default_context(cafile='/run/birja/db-ca.crt')})",
            )
            # Populated legacy state uses its actual historical application.
            legacy = root / "legacy"
            legacy.mkdir(mode=0o755)
            with tarfile.open(fileobj=__import__('io').BytesIO(source_git('archive', 'v0.3.1', 'backend/app'))) as archive:
                archive.extractall(legacy, filter='data')
            client('migrate', "from alembic import command\nfrom alembic.config import Config\ncommand.upgrade(Config('/app/alembic.ini'),'0007')", bootstrap)
            secure_seed = secure_seed.replace("cfg=Config('/app/alembic.ini');cfg.set_main_option('script_location',legacy+'/backend/alembic');command.upgrade(cfg,'0007')", "")
            client("backend", secure_seed, [*bootstrap, '-v', str(legacy / 'backend/app') + ':/app/app:ro'])
            client('migrate', "from alembic import command\nfrom alembic.config import Config\ncommand.upgrade(Config('/app/alembic.ini')," + repr('head' if fresh_bootstrap else '0011') + ")", bootstrap)
            original = r.canonical(dc, "birja_source_test")
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
            upgraded = client('migrate', STOCK_TLS_UPGRADE) if not fresh_bootstrap else None
            if upgraded is not None:
                assert b'existing_tls_connections_immediate_stock_grants=true' in upgraded.stdout
            assert role_sql(dc, "SELECT version_num FROM alembic_version") == b"0012"
            current = r.canonical(dc, "birja_source_test")
            assert current['financial'] == original['financial']
            assert all(current['tables'][table] == state for table,state in original['tables'].items() if table not in {'coins','alembic_version','stock_quotes','stock_sessions'})
            if not fresh_bootstrap:
                assert original['tables']['stock_quotes']['count'] == original['tables']['stock_sessions']['count'] == 0
                assert current['tables']['stock_quotes']['count'] == current['tables']['stock_sessions']['count'] == 1
            stock_role_contract(dc)
            action_acl = action_role_contract(dc)
            action_consumer = client('migrate', ACTION_TLS_CONSUMER)
            assert b'accounting_tls_actual_append=true immutable_denials=true quantity_only=true' in action_consumer.stdout
            print('accounting_tls_actual_append=true immutable_denials=true quantity_only=true lane=' + ('fresh0012' if fresh_bootstrap else 'populated0011_no_grant_repair'), flush=True)
            ownership_consumer=client('migrate',OWNERSHIP_TLS_CONSUMER)
            assert b'ownership_tls_actual_app_append_replay_reconstruct=true scheduler_consistency=true six_column_read_only=true' in ownership_consumer.stdout
            print('ownership_tls_actual_app_append_replay_reconstruct=true scheduler_consistency=true six_column_read_only=true lane='+('fresh0012' if fresh_bootstrap else 'populated0011_no_grant_repair'),flush=True)
            # Dedicated isolated logins are provisioned only AFTER migration
            # authority checks. NOLOGIN operator remains a separate group role.
            role_sql(dc,"CREATE ROLE birja_operator_fixture LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD '"+'d'*64+"'; CREATE ROLE birja_public_fixture LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD '"+'e'*64+"'; GRANT birja_action_operator TO birja_operator_fixture")
            resolution_consumer=client('migrate',RESOLUTION_SCENARIO+RESOLUTION_TLS_CONSUMER)
            assert b'resolution_verified_tls_operator_service_replay=true stale_denied=true public_app_scheduler_denied=true' in resolution_consumer.stdout
            print('resolution_verified_tls_operator_service_replay=true stale_denied=true public_app_scheduler_denied=true lane='+('fresh0012' if fresh_bootstrap else 'populated0011_no_grant_repair'),flush=True)
            consumer = client('migrate', STOCK_TLS_CALENDAR)
            assert b'calendar_runtime_tls_consumer=true' in consumer.stdout
            print('calendar_runtime_tls_consumer=true lane=' + ('fresh_bootstrap' if fresh_bootstrap else 'populated0010_no_grant_repair'), flush=True)
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
            return action_acl
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
        assert tls() == tls(fresh_bootstrap=True)
    elif sys.argv[1:] == ["--image-transition"]:
        image_transition()
    elif sys.argv[1:] == ["--roles-red-probe"]:
        roles(red_probe=True)
    elif sys.argv[1:] == ["--tls"]:
        tls()
    elif sys.argv[1:] == ["--all"]:
        roundtrip()
        roles()
        assert tls() == tls(fresh_bootstrap=True)
    else:
        args = options(sys.argv[1:])
        roundtrip(args.recovery_bundle)
