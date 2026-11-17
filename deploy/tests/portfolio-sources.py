#!/usr/bin/env python3
"""Exact source/schema/image dispatcher for synthetic recovery campaigns.

Immutable retained programs and complete trees are authenticated BEFORE import.
Images are built from those contexts and consumed by immutable content ID, never
relabelled as a preexisting image. No application test fixtures are imported.
"""

import base64
import hashlib
import io
import json
import os
import subprocess
import tarfile
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MATRIX = json.loads(Path(__file__).with_name("portfolio-retained-sources.json").read_text())
FIXED_COMMIT = "c2c7af17e2cb225fe196c5dbf843a65022a69e37"
FIXED_APP = "f5dd6a5a20dbf07a884d9ec688f621b16f922868"
FIXED_ALEMBIC = "a60941416ac7d38471930306ea4a05bc87141fdc"
FIXED_FILES = {
    'backend/Dockerfile': '91aeb06cd6e78ab1e7837eb5ce2e61bf2142d9cd',
    'backend/uv.lock': '6bb8ae67951fddd3db5c31c1a2ee5db36724e371',
    'deploy/tests/stock-execution-fixture.py': 'e8af377c6cf391a42638c54e875450977cdd6b79',
    'deploy/tests/stock-runtime-fixture.py': '18e5feaff7872a4c6e9244a5a7af6e33800a74e6',
    'deploy/tests/dividend-execution-fixture.py': '74c3fda06e53b141cfcecfa92b082419d208fd95',
}
FIXED_RELEASES = {
    "retained": (FIXED_COMMIT, "1f3a8539a796aa8fdedbc79153e449035f90a06d715c6b2e4c667caed019ae85"),
    "legacy0008": ("46d24c8591de2207cf219429aac0768962bed4c3", "09ab46937e7da0f8cf6760bd245dd960242c541f7e136b269b3fd7db98c92bdb"),
    "legacy0007": ("0107706617b8bbf9c1a069f3e3ccc9c53b9ab2f7", "f732a59390add4a7c5e538a5d04fde1b53ec6e026ee26f6a0da3e7ac00c6a312"),
}


def git(*args):
    return subprocess.check_output(["git", "-c", "safe.directory=" + str(ROOT), "-C", str(ROOT), *args])


def validate_matrix(matrix=MATRIX):
    retained = matrix["retained"]
    if (matrix["format"] != 1 or matrix["current"] != {
            "revision": "0017", "program": "deploy/tests/portfolio-execution-fixture.py"}
            or retained["commit"] != FIXED_COMMIT or retained["app_tree"] != FIXED_APP
            or retained["alembic_tree"] != FIXED_ALEMBIC
            or retained['files'] != FIXED_FILES):
        raise ValueError("untrusted source matrix")
    if any((matrix[lane]["commit"], matrix[lane]["archive_sha256"]) != identity
           for lane, identity in FIXED_RELEASES.items()):
        raise ValueError("immutable source release substituted")
    for key, path in (("app_tree", "backend/app"), ("alembic_tree", "backend/alembic")):
        if git("rev-parse", FIXED_COMMIT + ":" + path).decode().strip() != retained[key]:
            raise ValueError("source tree substitution")
    for path, blob in retained["files"].items():
        if git("rev-parse", FIXED_COMMIT + ":" + path).decode().strip() != blob:
            raise ValueError("source program/config substitution")
    return matrix


def source_archive(lane="retained", *, archive=None, archive_sha=None):
    validate_matrix()
    selected = MATRIX[lane]
    if archive is None:
        # Packaging only. Runtime consumers must supply their selected archive.
        data = git("archive", "--format=tar", selected["commit"])
    else:
        verify_archive_binding(archive, archive_sha)
        with tarfile.open(archive, "r:") as recovery:
            name = "sources/" + lane + ".tar"
            members = [m for m in recovery.getmembers() if m.name == name]
            if len(members) != 1 or not members[0].isfile():
                raise ValueError("missing or duplicate retained source payload")
            data = recovery.extractfile(members[0]).read()
    if hashlib.sha256(data).hexdigest() != selected["archive_sha256"]:
        raise ValueError("complete immutable source archive mismatch")
    return data


def archive_payloads():
    return {"sources/" + lane + ".tar": source_archive(lane)
            for lane in ("retained", "legacy0008", "legacy0007")}


def qualified_revision(revision, kind, *, mode=None):
    if kind == "portfolio":
        if revision != "0017":
            raise ValueError("current consumer on retained schema")
        return
    if revision not in {f"{n:04}" for n in range(7, 15)}:
        raise ValueError("retained consumer on unsupported schema")
    if kind not in {"execution", "runtime", "dividend"}:
        raise ValueError("unknown proof source")
    if (kind in {"execution", "runtime"} and revision not in {"0013", "0014"}
            or kind == "dividend" and revision != "0014"
            and not (revision == "0013" and mode == "prepare")):
        raise ValueError("proof/schema mismatch")


def retained_program(kind, *, revision, archive, archive_sha, **kwargs):
    qualified_revision(revision, kind, mode=kwargs.get("mode"))
    validate_matrix()
    payload = source_archive(archive=archive, archive_sha=archive_sha)
    filename = {"execution": "stock-execution-fixture.py", "runtime": "stock-runtime-fixture.py",
                "dividend": "dividend-execution-fixture.py"}[kind]
    path = "deploy/tests/" + filename
    with tarfile.open(fileobj=io.BytesIO(payload)) as source:
        code = source.extractfile(path).read()
    blob = hashlib.sha1(b"blob " + str(len(code)).encode() + b"\0" + code).hexdigest()
    if blob != MATRIX["retained"]["files"][path]:
        raise ValueError("proof blob mismatch before import")
    module = types.ModuleType("authenticated_retained_" + kind)
    exec(compile(code, "<authenticated-v0.5.0-" + filename + ">", "exec"), module.__dict__)
    body = module.program(**kwargs)
    # The entire immutable source is embedded, not a rewritten service overlay.
    # Child schema check happens before any retained application import/write.
    prelude = r'''
import asyncio,asyncpg,os,ssl,sys,tempfile,base64,io,tarfile,hashlib
from urllib.parse import urlsplit,urlunsplit
async def declared_revision():
 value=os.environ['DATABASE_URL'].replace('postgresql+asyncpg://','postgresql://')
 parts=urlsplit(value)
 if EXPECTED_DATABASE:value=urlunsplit(parts._replace(path='/'+EXPECTED_DATABASE))
 ca=os.environ.get('DATABASE_SSL_CA_FILE')
 connection=await asyncpg.connect(value,ssl=ssl.create_default_context(cafile=ca) if ca else None)
 try:
  if await connection.fetchval('SELECT version_num FROM alembic_version')!=EXPECTED_REVISION:
   raise ValueError('retained source/schema substitution before import')
 finally:await connection.close()
asyncio.run(declared_revision())
retained=tempfile.mkdtemp(prefix='birja-retained-complete-')
payload=base64.b64decode(RETAINED_ARCHIVE)
if hashlib.sha256(payload).hexdigest()!=EXPECTED_SOURCE_ARCHIVE:
 raise ValueError('retained complete source payload changed before import')
with tarfile.open(fileobj=io.BytesIO(payload)) as archive:
 archive.extractall(retained,filter='data')
for directory,dirs,files in os.walk(retained,topdown=False):
 for name in files:
  path=os.path.join(directory,name)
  if not os.path.islink(path):os.chmod(path,0o400)
 os.chmod(directory,0o500)
sys.path.insert(0,retained+'/backend')
'''
    return ("# birja-retained-source=" + FIXED_COMMIT + "\nEXPECTED_REVISION=" + repr(revision)
            + "\nEXPECTED_DATABASE=" + repr(kwargs.get("database"))
            + "\nEXPECTED_SOURCE_ARCHIVE=" + repr(MATRIX['retained']['archive_sha256'])
            + "\nRETAINED_ARCHIVE=" + repr(base64.b64encode(payload).decode())
            + "\n" + prelude + body)


def image_binding(inspect, *, source_commit, app_tree, context_sha256):
    """Complete content identity, independently rechecked before each use."""
    if not isinstance(inspect, list) or len(inspect) != 1:
        raise ValueError("one exact image required")
    row = inspect[0]
    labels = row["Config"].get("Labels") or {}
    if labels.get("org.opencontainers.image.revision") != source_commit:
        raise ValueError("image/source substitution")
    config = json.dumps(row["Config"], sort_keys=True, separators=(",", ":")).encode()
    roots = json.dumps(row["RootFS"], sort_keys=True, separators=(",", ":")).encode()
    return {"id": row["Id"], "source_commit": source_commit, "app_tree": app_tree,
            "context_sha256": context_sha256,
            "config_sha256": hashlib.sha256(config).hexdigest(),
            "rootfs_sha256": hashlib.sha256(roots).hexdigest()}


def verify_image(expected, inspect):
    actual = image_binding(inspect, source_commit=expected["source_commit"],
                           app_tree=expected["app_tree"], context_sha256=expected["context_sha256"])
    if actual != expected:
        raise ValueError("immutable image/config/rootfs mismatch")
    return expected["id"]


def verify_archive_binding(path, expected):
    import re
    path = Path(path)
    if (not isinstance(expected, str) or not re.fullmatch("[0-9a-f]{64}", expected)
            or path.is_symlink() or not path.is_file()
            or hashlib.sha256(path.read_bytes()).hexdigest() != expected):
        raise ValueError("same archive changed/rebuilt")


def verify_source_tree(directory, payload):
    """Recheck every immutable source byte before a child uses the context."""
    root = Path(directory)
    with tarfile.open(fileobj=io.BytesIO(payload)) as source:
        expected = {m.name: m for m in source.getmembers() if not m.isdir()}
        actual = {str(p.relative_to(root)) for p in root.rglob('*')
                  if p.is_file() or p.is_symlink()}
        if actual != set(expected):
            raise ValueError('complete source context inventory changed')
        for name, member in expected.items():
            path = root / name
            if member.issym():
                if not path.is_symlink() or os.readlink(path) != member.linkname:
                    raise ValueError('source symlink changed')
            elif not member.isfile() or path.is_symlink() or path.read_bytes() != source.extractfile(member).read():
                raise ValueError('immutable source bytes changed')


def record_image_binding(archive, lane, binding):
    """Persist first-use identities beside the selected immutable archive."""
    record = Path(archive).parent / (lane + '-image-binding.json')
    if record.exists():
        if (record.is_symlink() or record.stat().st_uid != os.getuid()
                or record.stat().st_mode & 0o077 or json.loads(record.read_text()) != binding):
            raise ValueError('campaign image binding replaced')
        return
    with record.open('x') as stream:
        json.dump(binding, stream, sort_keys=True)
    record.chmod(0o400)


def build_retained_image(directory, *, archive, archive_sha, lane='retained'):
    """Called only by an owned campaign, before its first retained client."""
    root = Path(directory)
    if root.exists():
        raise ValueError("retained source destination must be absent")
    root.mkdir(mode=0o700)
    payload = source_archive(lane, archive=archive, archive_sha=archive_sha)
    with tarfile.open(fileobj=io.BytesIO(payload)) as source:
        source.extractall(root, filter="data")
    for path in root.rglob("*"):
        if not path.is_symlink():
            path.chmod(0o500 if path.is_dir() or path.stat().st_mode & 0o111 else 0o400)
    selected = MATRIX[lane]
    commit = selected['commit']
    app_tree = git('rev-parse', commit+':backend/app').decode().strip()
    verify_source_tree(root, payload)
    # Archives are deterministic: separate exclusive campaigns may package the
    # same bytes. Scope the mutable build alias to this private directory's
    # identity, including when the fixed path is recreated after preservation.
    # Existing tags still require this campaign's own immutable binding below.
    campaign = Path(archive).parent.resolve(strict=True)
    identity = campaign.stat()
    namespace = hashlib.sha256(
        os.fsencode(str(campaign)) + f":{identity.st_dev}:{identity.st_ino}".encode()
    ).hexdigest()[:16]
    tag = "birja-retained-portfolio:" + commit[:12] + "-" + archive_sha[:16] + "-" + namespace
    env = {key: os.environ[key] for key in ("PATH", "HOME", "LANG") if key in os.environ}
    record = Path(archive).parent / (lane + '-image-binding.json')
    existing = subprocess.run(["docker", "image", "inspect", tag], capture_output=True, env=env)
    if existing.returncode == 0:
        if (record.is_symlink() or not record.is_file() or record.stat().st_uid != os.getuid()
                or record.stat().st_mode & 0o077):
            raise ValueError("preexisting retained image has no private campaign binding")
        binding = json.loads(record.read_text())
        if (binding['source_commit'] != commit or binding['app_tree'] != app_tree
                or binding['context_sha256'] != selected['archive_sha256']):
            raise ValueError('preexisting image source binding mismatch')
        verify_image(binding, json.loads(existing.stdout))
        return binding
    subprocess.run(["docker", "build", "--target", "runtime", "--label",
        "org.opencontainers.image.revision=" + commit, "-t", tag, str(root / "backend")],
        check=True, env=env, capture_output=True, timeout=600)
    inspect = json.loads(subprocess.check_output(["docker", "image", "inspect", tag], env=env))
    binding = image_binding(inspect, source_commit=commit, app_tree=app_tree,
                            context_sha256=selected["archive_sha256"])
    record_image_binding(archive, lane, binding)
    return binding
