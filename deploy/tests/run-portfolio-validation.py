#!/usr/bin/env python3
"""Local CI-equivalent qualification; synthetic endpoints and one owned archive.

No dependency installation, credentials from .env, or provider access is used.
The .gz filename is the fixed campaign name; the authenticated recovery format
remains the uncompressed, strict-member USTAR used by older consumers.
"""

import argparse
import hashlib
import importlib.util
import json
import os
import shlex
import shutil
import subprocess
import tarfile
import re
import stat
import tempfile
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = Path("/tmp/birja-phase14-proof/recovery.tar.gz")
PHASE15_ARCHIVE = Path("/tmp/birja-phase15-proof/recovery.tar.gz")
PHASE21_ARCHIVE = Path("/tmp/birja-backup-test-phase21-proof/recovery.tar.gz")
PHASE24_ARCHIVE = Path("/tmp/birja-backup-test-phase24-proof/recovery.tar.gz")
PHASE14_SHA256 = "1a41c8b9a55986998e46ea6341dfea93dd2b7c8da0e0428af08251d21d6b742f"
PRESERVED_ARCHIVE = Path("/tmp/birja-phase13-proof/recovery.tar.gz")
PRESERVED_SHA256 = "6fb79a45ddcb10725b18fc756e71bd555c827a6e61a5a4a0bd2d183096114b92"
STAGES = ("image-transition", "retained-roundtrip", "current0023-cold",
          "roles", "tls-upgraded", "tls-fresh", "selected-rollback")
SUCCESSOR_STAGES = ("image-transition", "retained-roundtrip", "current0027-cold",
                    "roles", "tls-upgraded", "tls-fresh", "selected-rollback")
SUCCESSOR_PROFILE = "deploy-recovery-v8"
DAILY_VALUE_STAGES = (*SUCCESSOR_STAGES[:2], "current0028-cold", *SUCCESSOR_STAGES[3:])
DAILY_VALUE_PREDECESSOR_BINDING = "portfolio0027-image-binding.json"
SUCCESSORS = {
    21: (SUCCESSOR_PROFILE, 7, "0027", SUCCESSOR_STAGES),
    24: ("deploy-recovery-v9", 8, "0028", DAILY_VALUE_STAGES),
}
STACK = ["docker", "compose", "--env-file", "/dev/null", "-f", "docker-compose.test.yml"]
PG = "cgr.dev/chainguard/postgres@sha256:adbf3d8db097696ed6e997b108b51393786be999c04d543502f8959e1bafa8de"
REDIS = "cgr.dev/chainguard/redis@sha256:26bb2dd4412f902f3decd44fba5dfaef4360d97004d44f6cff7f28d6aba19c48"
SCANNER = "aquasec/trivy@sha256:2e6c00d711ab4ae41d8a30c2c1fd3bd3b62704c177bb120f95012e939edfb3df"
RESTIC_SHA256 = "20d4142678d0d95ec11a4759def1b73fd9190abc9ca19e4b62d067c0b387e639"
SOURCE_SCOPES = ("backend", "frontend", "deploy", "nginx", ".github", "CLAUDE.md",
                 "docker-compose*.yml", ".gitignore", ".gitattributes")


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), Path(__file__).with_name(name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def child_path():
    # Keep the installed tools' real bin directories, never the caller's whole
    # PATH. /usr/sbin is required by the actual nginx configuration gate.
    approved_restic = Path("/tmp/birja-test-tools/restic-0.19.1/restic")
    directories = [str(approved_restic.parent)] if approved_restic.is_file() else []
    for name in ("uv", "node", "python3", "restic", "nginx", "docker"):
        executable = shutil.which(name)
        if executable:
            directories.append(str(Path(executable).resolve().parent))
    return os.pathsep.join(dict.fromkeys(directories + ["/usr/local/bin", "/usr/sbin", "/usr/bin", "/bin"]))


def environment():
    return {**{k: os.environ[k] for k in ("HOME", "LANG") if k in os.environ},
            "PATH": child_path(),
            "COMPOSE_DISABLE_ENV_FILE": "1", "ENV": "test", "PRICE_SOURCE": "fake",
            "UV_NO_SYNC": "1", "UV_OFFLINE": "1",
            "UV_CACHE_DIR": "/tmp/birja-test-tools/uv-cache",
            "EMAIL_BACKEND": "console", "DATABASE_URL": "postgresql+asyncpg://birja_test:test@127.0.0.1:55432/birja_test",
            "REDIS_URL": "redis://:test@127.0.0.1:56379/0",
            "OTP_HMAC_SECRET": "synthetic-only-validation-otp-" + "x" * 32,
            "JWT_SECRET": "synthetic-only-validation-jwt-" + "y" * 32}


def archive_for_phase(phase=14):
    if type(phase) is not int or phase not in {14, 15, 21, 24}:
        raise ValueError("explicit finite qualification phase required")
    return {14: ARCHIVE, 15: PHASE15_ARCHIVE, 21: PHASE21_ARCHIVE, 24: PHASE24_ARCHIVE}[phase]


def validate_selection(suite, phase=14):
    archive = archive_for_phase(phase)
    if suite not in {"all-security", "recovery", "recovery-current", "recovery-successor"}:
        raise ValueError("explicit qualification suite required")
    if (phase in SUCCESSORS) != (suite == "recovery-successor"):
        raise ValueError("successor recovery requires explicit phase21 or phase24 and recovery-successor")
    if suite == "recovery-current" and phase != 15:
        raise ValueError("current-only recovery requires explicit phase15")
    return archive


def preflight(suite, *, phase=14, run=subprocess.run, fixture_tail=True):
    archive = validate_selection(suite, phase)
    env = environment()
    tools = {}
    for name, args in (("uv", ["--version"]), ("node", ["--version"]),
                       ("python3", ["--version"]), ("restic", ["version"]),
                       ("nginx", ["-v"]), ("docker", ["--version"])):
        path = shutil.which(name, path=env["PATH"])
        if path is None:
            raise ValueError("required installed qualification tool missing: " + name)
        if name == "restic" and hashlib.sha256(Path(path).read_bytes()).hexdigest() != RESTIC_SHA256:
            raise ValueError("approved restic binary checksum required before execution")
        result = run([path, *args], env=env, capture_output=True, check=True, timeout=30)
        version = (result.stdout + result.stderr).decode().strip()
        if name == "node" and not version.startswith("v24."):
            raise ValueError("qualification requires installed Node24")
        if name == "restic" and not version.startswith("restic 0.19.1 "):
            raise ValueError("qualification requires approved restic0.19.1")
        tools[name] = {"path": path, "version": version}
    required = ["backend/.venv/bin/pytest", "backend/.venv/bin/ruff", "backend/.venv/bin/mypy"]
    if suite == "all-security":
        required += ["backend/.venv/bin/pip-audit"] + ["frontend/node_modules/.bin/" + name
            for name in ("prettier", "eslint", "tsc", "vitest", "vite", "playwright")]
    if any(not (ROOT / name).is_file() or not os.access(ROOT / name, os.X_OK) for name in required):
        raise ValueError("installed locked qualification binaries required; no automatic installation")
    sources = load("portfolio-sources")
    sources.validate_matrix()
    recovery = load("portfolio-smoke").load_recovery()
    if phase in SUCCESSORS:
        recovery.closure_source(ROOT, revision=SUCCESSORS[phase][2], allow_successor=False)
        successor_source_identity(sources)
    else:
        recovery.closure_source(ROOT)
    fixture = json.loads((ROOT / "deploy/tests/fixtures/portfolio-recovery-0023.json").read_text())
    if (fixture.get("format"), fixture["manifest"].get("revision"),
            len(fixture["manifest"]["tables"]), len(fixture["manifest"]["identity_state"])) != (3, "0023", 31, 24):
        raise ValueError("exact current31/24 fixture profile required")
    prior = preserved_archive()
    prior14 = preserved_phase14_archive() if phase in {15, 24} else None
    if suite != "all-security" and (archive.parent.is_symlink() or archive.parent.exists()):
        raise ValueError("exclusive new recovery archive directory must be absent")
    if fixture_tail:
        run(["bash", "deploy/tests/test-db-config.sh"], cwd=ROOT,
            env={**env, "BIRJA_TEST_PROJECT": "birja-p14-16-preflight" if phase == 14 else "birja-p15-01-preflight"}, check=True, timeout=300)
    return {"ok": True, "suite": suite, "phase": phase, "archive": str(archive), "tools": tools,
            "fixture_tail": "passed" if fixture_tail else "not-run-offline-diagnostic",
            "preserved_archive_sha256": prior, "preserved_phase14_archive_sha256": prior14,
            "path": env["PATH"]}


def security_commands():
    # Read the actual single-line critical command; never maintain a weaker copy.
    ci = (ROOT / ".github/workflows/ci.yml").read_text()
    critical = [line.strip()[5:] for line in ci.splitlines()
                if line.strip().startswith("run: uv run coverage report --include=")]
    if len(critical) != 1 or not critical[0].endswith(" --fail-under=100"):
        raise ValueError("exact CI critical coverage command required")
    commands = [("backend", shlex.split(c)) for c in (
        "uv run ruff check .", "uv run ruff format --check .", "uv run mypy app",
        "uv run pytest --cov=app --cov-branch --cov-fail-under=80", critical[0], "uv run pip-audit")]
    commands += [("frontend", shlex.split(c)) for c in (
        "npm run lint", "npm run typecheck", "npx prettier --check .",
        "npm run test -- --coverage", "npm run build", "node --test ../deploy/tests/test-frontend-audit.mjs",
        "node ../deploy/audit-frontend.mjs")]
    commands += [(".", ["python3", "deploy/tests/run-stock-browser.py"])]
    for target, tag, context in (("test-builder", "birja-backend-test:ci", "backend"),
                                 ("runtime", "birja-backend-runtime:ci", "backend"),
                                 ("toolchain", "birja-node-toolchain:ci", "frontend")):
        commands.append((".", ["docker", "build", "--target", target, "-t", tag, context]))
    commands += [(".", ["docker", "pull", "--platform", "linux/amd64", image]) for image in (PG, REDIS, SCANNER)]
    commands += [(".", ["docker", "run", "--rm", "--network", "host", "birja-backend-test:ci", "pytest", "tests/test_smoke.py", "-q"]),
                 (".", ["python3", "deploy/scan-images.py", "--output", "image-reports",
                        "--runtime", "birja-backend-runtime:ci", "--builder", "birja-backend-test:ci",
                        "--postgres", PG, "--redis", REDIS, "--node", "birja-node-toolchain:ci"])]
    # The CI image/ops contract gates remain part of the whole security graph.
    commands[-1:-1] = [(".", ["python3", "deploy/tests/" + name + ".py"]) for name in (
        "test-image-contracts", "test-ci-ops", "test-portfolio-browser-contracts",
        "test-portfolio-validation-contracts")]
    commands[-1:-1] = [(".", shlex.split(command)) for command in (
        "bash deploy/tests/test-backup.sh", "bash deploy/tests/test-deploy-compatibility.sh",
        "python3 deploy/tests/test-selected-cutover-contracts.py", "bash deploy/tests/test-restore-safety.sh",
        "bash deploy/tests/test-db-config.sh", "python3 deploy/tests/test-deploy-prerequisites.py",
        "python3 deploy/tests/test-datastore-bindings.py", "bash deploy/tests/test-reexec.sh",
        "bash deploy/tests/test-rollback-target.sh", "bash deploy/tests/test-app-services.sh",
        "bash deploy/tests/test-smoke-ports.sh", "bash deploy/tests/test-smoke-trading.sh",
        "bash deploy/check-nginx-config.sh", "python3 deploy/tests/test-stock-recovery-contracts.py --postgres",
        "docker build --target test-builder -t birja-backend-test:phase05-07 backend",
        "python3 deploy/tests/test-dev-bootstrap.py --image birja-backend-test:phase05-07")]
    return commands


def execute_security(run=subprocess.run):
    env = environment()
    frozen = security_sources()
    # Refuse to adopt somebody else's running test stack; cleanup is ours only.
    existing = run(STACK + ["ps", "-q"], cwd=ROOT, env=env, capture_output=True, check=True)
    if existing.stdout.strip():
        raise ValueError("refuse preexisting test stack")
    try:
        run(STACK + ["up", "-d", "--wait"], cwd=ROOT, env=env, check=True)
        for directory, argv in security_commands():
            if security_sources() != frozen:
                raise ValueError("security campaign source changed")
            if argv[:2] == ["python3", "deploy/scan-images.py"]:
                argv = argv.copy()
                for flag in ("--runtime", "--builder", "--node"):
                    index = argv.index(flag) + 1
                    argv[index] = run(["docker", "image", "inspect", argv[index], "--format", "{{.Id}}"],
                        cwd=ROOT, env=env, capture_output=True, check=True).stdout.decode().strip()
            try:
                run(argv, cwd=ROOT / directory, env=env, check=True)
            finally:
                if security_sources() != frozen:
                    raise ValueError("security campaign source changed")
    finally:
        run(STACK + ["down", "-v"], cwd=ROOT, env=env, check=True)


@contextmanager
def source_directory(path):
    """Open every directory component without following a root/ancestor link."""
    descriptor = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in Path(path).absolute().parts[1:]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        yield descriptor
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise ValueError('source directory disappeared or symlink refused') from exc
    finally:
        os.close(descriptor)


def source_identity(value):
    return (value.st_dev, value.st_ino, value.st_mode, value.st_size,
            value.st_mtime_ns, value.st_ctime_ns)


def source_bytes(name, *, optional=False, allow_link=True):
    path = ROOT / name
    if Path(name).is_absolute() or '..' in Path(name).parts:
        raise ValueError('source inventory escapes checkout')
    try:
        with source_directory(path.parent) as directory:
            before = os.stat(path.name, dir_fd=directory, follow_symlinks=False)
            if stat.S_ISLNK(before.st_mode):
                if not allow_link:
                    raise ValueError('source ignore metadata symlink refused')
                target = os.readlink(path.name, dir_fd=directory)
                # Inspect only metadata of a finite in-root regular leaf target.
                # Never read through the link, including its target ancestors.
                destination = Path(os.path.abspath(path.parent / target))
                if not destination.is_relative_to(ROOT):
                    raise ValueError('source symlink escapes checkout')
                with source_directory(destination.parent) as target_directory:
                    target_stat = os.stat(destination.name, dir_fd=target_directory,
                                          follow_symlinks=False)
                    if not stat.S_ISREG(target_stat.st_mode):
                        raise ValueError('source leaf symlink requires regular in-root target')
                    with source_directory(destination.parent) as target_current:
                        if source_identity(os.fstat(target_current)) != source_identity(os.fstat(target_directory)):
                            raise ValueError('source link target directory changed')
                data = b'symlink\0' + os.fsencode(target)
            else:
                descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                                     dir_fd=directory)
                with os.fdopen(descriptor, 'rb') as stream:
                    opened = os.fstat(stream.fileno())
                    if not stat.S_ISREG(opened.st_mode) or source_identity(opened) != source_identity(before):
                        raise ValueError('source inventory changed or is not a regular file')
                    data = stream.read()
                    if source_identity(os.fstat(stream.fileno())) != source_identity(opened):
                        raise ValueError('source changed while reading')
            after = os.stat(path.name, dir_fd=directory, follow_symlinks=False)
            if source_identity(before) != source_identity(after):
                raise ValueError('source changed while reading')
            # Reopen the pathname to detect replacement after opening an ancestor.
            with source_directory(path.parent) as current:
                if source_identity(os.fstat(current)) != source_identity(os.fstat(directory)):
                    raise ValueError('source directory changed while reading')
            return data
    except FileNotFoundError as exc:
        if optional:
            return None
        raise ValueError('source inventory disappeared') from exc
    except OSError as exc:
        raise ValueError('source inventory disappeared or unsafe symlink/type') from exc


def security_sources():
    # Ignore credential files using the repository's normal ignore rules, but
    # bind additions/renames as well as tracked edits. Never follow a source
    # symlink outside the checkout or read its target as a secret.
    with source_directory(ROOT) as root_directory:
        identity = source_identity(os.fstat(root_directory))
        excluded = source_bytes('.git/info/exclude', optional=True, allow_link=False)
        env = {**environment(), "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null"}
        raw = subprocess.check_output(["git", "-c", "core.fsmonitor=false", "-c",
            "core.excludesfile=/dev/null", "ls-files", "--cached", "--others", "--exclude-standard",
            "-z", "--", *SOURCE_SCOPES], cwd=ROOT, env=env)
    names = {os.fsdecode(name) for name in raw.split(b"\0") if name}
    if excluded is not None:
        names.add(".git/info/exclude")
    result = {}
    for name in sorted(names):
        data = source_bytes(name, allow_link=name != '.git/info/exclude')
        result[name] = hashlib.sha256(data).hexdigest()
    with source_directory(ROOT) as current:
        if source_identity(os.fstat(current)) != identity:
            raise ValueError('source root changed during inventory')
    if source_bytes('.git/info/exclude', optional=True, allow_link=False) != excluded:
        raise ValueError('source ignore metadata changed during inventory')
    return result


def campaign_files(recovery, *, successor=False, phase=21):
    version = SUCCESSORS[phase][1] if successor else 4
    payload = getattr(recovery, "PORTFOLIO_PAYLOAD_V" + str(version))
    return recovery.CORE + recovery.UNITS + payload


def campaign_sources(ops, *, successor=False, phase=21):
    names = campaign_files(ops.r, successor=successor, phase=phase)
    # Complete current application input, separate from fixed retained sources.
    tracked = subprocess.check_output(["git", "ls-files", "backend", "deploy", "docker-compose.ops-test.yml"], cwd=ROOT).decode().splitlines()
    return {name: ops.r.digest(ROOT / name) for name in sorted(set(names + tracked))}


def successor_source_identity(sources):
    """Bind the complete clean Git checkout and the actual backend build input."""
    if sources.git("status", "--porcelain", "--untracked-files=all").strip():
        raise ValueError("successor recovery source must be a clean checkout")
    commit = sources.git("rev-parse", "HEAD").decode().strip()
    tree = sources.git("rev-parse", commit + "^{tree}").decode().strip()
    app_tree = sources.git("rev-parse", commit + ":backend/app").decode().strip()
    context = hashlib.sha256(sources.git("archive", commit, "backend")).hexdigest()
    return {"tested_source": commit, "tested_tree": tree, "app_tree": app_tree,
            "context_sha256": context}


def require_successor_image(binding, identity):
    if (binding.get("source_commit") != identity["tested_source"]
            or binding.get("app_tree") != identity["app_tree"]
            or binding.get("context_sha256") != identity["context_sha256"]
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", binding.get("id", ""))
            or any(not re.fullmatch(r"[0-9a-f]{64}", binding.get(name, ""))
                   for name in ("config_sha256", "rootfs_sha256"))):
        raise ValueError("Campaign image does not match the tested source")


def preserved_archive():
    """A fresh CI host may lack prior proof; existing proof is never replaced."""
    if PRESERVED_ARCHIVE.is_symlink() or PRESERVED_ARCHIVE.parent.is_symlink():
        raise ValueError("preserved archive symlink")
    if not PRESERVED_ARCHIVE.exists():
        return None
    value = hashlib.sha256(PRESERVED_ARCHIVE.read_bytes()).hexdigest()
    if value != PRESERVED_SHA256:
        raise ValueError("preserved Phase13 archive changed")
    return value


def preserved_phase14_archive():
    if ARCHIVE.is_symlink() or ARCHIVE.parent.is_symlink():
        raise ValueError("preserved Phase14 archive symlink")
    if not ARCHIVE.exists():
        return None
    value = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
    if value != PHASE14_SHA256:
        raise ValueError("preserved Phase14 archive changed")
    return value


def write_status(path, value):
    """Publish complete private JSON atomically for concurrent status readers."""
    if path.is_symlink():
        raise ValueError("campaign status symlink refused")
    fd, temporary = tempfile.mkstemp(prefix=".status-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if Path(temporary).exists():
            Path(temporary).unlink()


def authenticate(ops, archive, expected, source, image_records=None, *, successor_identity=None, phase=21):
    sources = ops.portfolio_sources()
    sources.verify_archive_binding(archive, expected)
    successor = successor_identity is not None
    if successor and successor_identity != successor_source_identity(sources):
        raise ValueError("tested successor commit/tree changed")
    if source != {name: ops.r.digest(ROOT / name) for name in source}:
        raise ValueError("current campaign source changed")
    with tarfile.open(archive, "r:") as retained:
        inventory = json.load(retained.extractfile("INVENTORY.json"))
        payload = inventory.get("portfolio_payload", {})
        profile = SUCCESSORS[phase][:3] if successor else ("deploy-recovery-v5", 4, "0024")
        if (inventory.get("recovery_profile"), payload.get("version"), payload.get("revision")) != profile:
            raise ValueError("current campaign requires successor inventory")
        for name in campaign_files(ops.r, successor=successor, phase=phase):
            if retained.extractfile(name).read() != (ROOT / name).read_bytes():
                raise ValueError("packaged/current source substitution")
        for name, digest in ops.r.retained_closure_sources(profile[1]).items():
            if ops.r.sha_bytes(retained.extractfile(name).read()) != "sha256:" + digest:
                raise ValueError("fixed retained payload substitution")
    sources.validate_matrix()
    records = {p.name: p for p in archive.parent.glob("*-image-binding.json")}
    if image_records is not None:
        if any(name not in records or ops.r.digest(records[name]) != sha
               for name, sha in image_records.items()):
            raise ValueError("recorded campaign image identity disappeared/changed")
    for record in records.values():
        ops.r.private(record)
        binding = json.loads(record.read_text())
        inspect = json.loads(ops.r.call(["docker", "image", "inspect", binding["id"]]))
        sources.verify_image(binding, inspect)
        if image_records is not None:
            image_records[record.name] = ops.r.digest(record)
    load("portfolio-smoke").authenticate_campaign_images(archive, expected,
        inspect_image=lambda ref: json.loads(ops.r.call(["docker", "image", "inspect", ref])))
    if successor:
        current_record = records.get("current" + profile[2] + "-image-binding.json")
        if current_record is None:
            raise ValueError("authenticated current successor image record required")
        require_successor_image(json.loads(current_record.read_text()), successor_identity)


def execute_stages(operations, guard, *, stages=STAGES):
    if set(operations) != set(stages):
        raise ValueError("missing or unrecognized recovery stage")
    results = {}
    guard()
    for name in stages:
        try:
            results[name] = operations[name]()
        finally:
            guard()
    authorities = [results[name] for name in (stages[2], "tls-upgraded", "tls-fresh")]
    if (any(not isinstance(value, (tuple, list)) or len(value) != 3
            or any(not isinstance(part, str) or not re.fullmatch(r"[0-9a-f]{64}", part)
                   for part in value) for value in authorities)
            or not (authorities[0] == authorities[1] == authorities[2])):
        raise ValueError("cold/fresh/upgraded TLS authority differs or missing exact triple")


def recovery_operations(ops, archive, expected):
    smoke = load("portfolio-smoke")

    def retained():
        ops.roundtrip(archive)
        # Complete immutable0017 is a real source/image/TLS lane, never HEAD.
        smoke.run(archive=archive, archive_sha=expected, revision="0017", cold=True)
        smoke.run(archive=archive, archive_sha=expected, revision="0020", cold=True)

    def tls(fresh):
        # Preserve every legacy transport/role refusal before current authority.
        ops.tls(fresh_bootstrap=fresh)
        legacy = None if fresh else smoke.run(archive=archive, archive_sha=expected,
            revision="0023", upgraded_bootstrap=True, upgraded_from="0014")
        current = smoke.run(archive=archive, archive_sha=expected, revision="0023",
                         fresh_bootstrap=fresh, upgraded_bootstrap=not fresh)
        if not fresh and legacy != current:
            raise ValueError("legacy14/current20 upgraded TLS authority differs")
        return current

    def roles():
        ops.roles()
        smoke.run(archive=archive, archive_sha=expected, revision="0023")

    def rollback():
        subprocess.run(["bash", str(ROOT / "deploy/tests/test-rollback-db-security.sh"),
            "--recovery-bundle", str(archive)], cwd=ROOT, env=environment(), check=True)
        # New-schema unsupported old writers must refuse against an actual
        # current server using the authenticated immutable0017 image/consumer.
        smoke.run(archive=archive, archive_sha=expected, revision="0023")

    return {
        "image-transition": ops.image_transition,
        "retained-roundtrip": retained,
        "current0023-cold": lambda: smoke.run(archive=archive, archive_sha=expected,
                                               revision="0023", cold=True),
        "roles": roles,
        "tls-upgraded": lambda: tls(False),
        "tls-fresh": lambda: tls(True),
        "selected-rollback": rollback,
    }


def successor_recovery_operations(ops, archive, expected, *, phase=21):
    smoke = load("portfolio-smoke")
    profile, _, revision, _ = SUCCESSORS[phase]

    def catalog(lane, *, requires=(), authority=False):
        if lane in {"cold", "upgraded", "rollback"}:
            if phase == 24:
                with tempfile.TemporaryDirectory(prefix="birja-retained0027-build-") as tmp:
                    ops.portfolio_sources().build_retained_image(
                        Path(tmp) / "source", archive=archive, archive_sha=expected, lane="portfolio0027",
                    )
            else:
                smoke.build_current_runtime(
                    ops.portfolio_sources(), environment(), archive=archive, archive_sha=expected,
                    revision="0023", predecessor=True,
                )
        result = subprocess.run(
            ["bash", str(ROOT / "deploy/tests/test-stock-catalog-finance-recovery.sh"),
             "--lane", lane, "--archive", str(archive), "--sha256", expected,
             *(["--revision", revision] if phase == 24 else [])],
            cwd=ROOT, env=environment(), capture_output=True, timeout=900,
        )
        if result.returncode:
            raise ValueError("owned catalog recovery failed: " + lane + "\n"
                             + result.stderr.decode()[-2000:])
        output = result.stdout.decode().splitlines()
        if any(line not in output for line in requires):
            raise ValueError("missing measured catalog result: " + lane)
        print("\n".join(output), flush=True)
        if authority:
            reports = [line.removeprefix("catalog_authority=") for line in output
                       if line.startswith("catalog_authority=")]
            if len(reports) != 1 or "catalog_runtime_verified_tls=true" not in output:
                raise ValueError("missing measured restricted TLS authority: " + lane)
            return json.loads(reports[0])

    def retained():
        ops.roundtrip(archive)
        for revision in ("0017", "0020"):
            smoke.run(archive=archive, archive_sha=expected, revision=revision, cold=True,
                      recovery_profile=profile)
        catalog("retained0025", requires=("retained_0025_exact=true",))

    def roles():
        ops.roles()
        catalog("roles", requires=("catalog_runtime_verified_tls=true",))

    def tls(fresh):
        ops.tls(fresh_bootstrap=fresh)
        return catalog("fresh" if fresh else "upgraded", authority=True)

    def rollback():
        subprocess.run(["bash", str(ROOT / "deploy/tests/test-rollback-db-security.sh"),
                        "--recovery-bundle", str(archive)], cwd=ROOT,
                       env=environment(), check=True)
        catalog("rollback", requires=(
            "prewrite_predecessor_restarted=true original_volume_and_ledger_exact=true",
            f"postwrite_{revision}_restarted=true candidate_volume_and_receipts_exact=true predecessor_on_{revision}_refused=true",
            *(("daily_value_predecessor_refused=true",) if phase == 24 else ()),
        ))

    return {
        "image-transition": ops.image_transition,
        "retained-roundtrip": retained,
        "current" + revision + "-cold": lambda: catalog(
            "cold", requires=(f"cold_encrypted_{revision}_exact=true fresh_restore_server=true",
                              *(("daily_value_upgrade_empty=true", "daily_value_capture_exact=true",
                                 "daily_value_restored_owner_reads_exact=true") if phase == 24 else ())),
            authority=True,
        ),
        "roles": roles,
        "tls-upgraded": lambda: tls(False),
        "tls-fresh": lambda: tls(True),
        "selected-rollback": rollback,
    }


def execute_current_stage(operations, guard):
    guard()
    try:
        authority = operations["current0023-cold"]()
    finally:
        guard()
    if (not isinstance(authority, (tuple, list)) or len(authority) != 3
            or any(not isinstance(part, str) or not re.fullmatch(r"[0-9a-f]{64}", part)
                   for part in authority)):
        raise ValueError("current cold authority missing exact triple")
    return authority


def execute_recovery(*, phase=14, suite="recovery"):
    archive = validate_selection(suite, phase)
    if suite == "all-security":
        raise ValueError("explicit recovery suite required")
    ops = load("ops-fixtures")
    successor = suite == "recovery-successor"
    identity = successor_source_identity(ops.portfolio_sources()) if successor else None
    prior_archive = preserved_archive()
    prior14 = preserved_phase14_archive() if phase in {15, 21, 24} else None
    # Exclusive directory ownership prevents silently reusing an earlier run.
    archive.parent.mkdir(mode=0o700)
    ops.r.private(archive.parent, True)
    profile, payload, revision, successor_stages = SUCCESSORS[phase] if successor else (
        "deploy-recovery-v5", 4, "0024", None,
    )
    if successor:
        ops.package_current_archive(archive, successor=True, phase=phase)
    else:
        ops.package_current_archive(archive)
    expected = ops.r.digest(archive)
    ops.r.bundle_verify(archive, expected, required_profile=profile)
    source = campaign_sources(ops, successor=successor, phase=phase)
    image_records = {}
    ops.bind_source_archive(archive, expected)
    full = suite != "recovery-current"
    stages = successor_stages if successor else STAGES if full else ("current0023-cold",)
    status = {"ok": False, "phase": phase, "suite": suite,
              "archive": str(archive), "archive_sha256": expected, "stages": {},
              "whole7": False, "same_archive_final_ci": False}
    status_path = archive.parent / "status.json"
    if successor:
        status.update(identity, recovery_profile=profile, payload_version=payload, revision=revision,
                      stage_order=list(stages))
    def save_status():
        write_status(status_path, status)
    def recorded(name):
        def execute():
            status["current_stage"] = name
            save_status()
            result = operations[name]()
            status["stages"][name] = "operation-returned"
            return result
        return execute
    def guard():
        if preserved_archive() != prior_archive:
            raise ValueError("preserved archive presence changed")
        if phase in {15, 21, 24} and preserved_phase14_archive() != prior14:
            raise ValueError("preserved Phase14 archive presence changed")
        if successor:
            authenticate(ops, archive, expected, source, image_records, successor_identity=identity, phase=phase)
        else:
            authenticate(ops, archive, expected, source, image_records)
    try:
        if successor:
            operations = successor_recovery_operations(ops, archive, expected, phase=phase)
            smoke = load("portfolio-smoke")
            status["current_image"] = smoke.build_selected_runtime(
                ops.portfolio_sources(), environment(), revision=revision, archive=archive,
                archive_sha=expected)
            require_successor_image(status["current_image"], identity)
            if set(operations) != set(stages):
                raise ValueError("missing or unrecognized recovery stage")
        else:
            operations = recovery_operations(ops, archive, expected)
        selected = {name: recorded(name) for name in stages}
        if full:
            execute_stages(selected, guard, stages=stages)
        else:
            status["authority"] = execute_current_stage(selected, guard)
        if phase == 24:
            predecessor_digest = image_records.get(DAILY_VALUE_PREDECESSOR_BINDING)
            if predecessor_digest is None:
                raise ValueError("authenticated 0027 predecessor image record required")
            status["predecessor_image_sha256"] = predecessor_digest
        status["ok"] = True
        status["stages"] = dict.fromkeys(stages, "passed-authenticated")
        status["whole7"] = status["same_archive_final_ci"] = full
    finally:
        save_status()
    print(("same_archive_final_ci=true" if full else
           "recovery_current_component=true whole7=false same_archive_final_ci=false")
          + " sha256=" + expected, flush=True)


def verify_successor_receipt(archive, tested_source, *, phase=21):
    """Return the two staging digests only after rechecking the completed proof."""
    ops = load("ops-fixtures")
    identity = successor_source_identity(ops.portfolio_sources())
    if tested_source != identity["tested_source"]:
        raise ValueError("hosted source does not match the tested checkout")
    expected = ops.r.private(archive.with_suffix(archive.suffix + ".sha256")).read_text().strip()
    receipt_data = ops.r.private(archive.parent / "status.json").read_bytes()
    receipt = json.loads(receipt_data)
    profile, payload, revision, stages = SUCCESSORS[phase]
    required = {
        **identity, "archive": str(archive), "archive_sha256": expected,
        "phase": phase, "suite": "recovery-successor", "recovery_profile": profile,
        "payload_version": payload, "revision": revision, "stage_order": list(stages),
        "stages": dict.fromkeys(stages, "passed-authenticated"),
        "current_stage": stages[-1],
    }
    if (any(receipt.get(name) != value for name, value in required.items())
            or any(receipt.get(name) is not True for name in
                   ("ok", "whole7", "same_archive_final_ci"))):
        raise ValueError("complete authenticated " + revision + " recovery receipt required")
    image = json.loads(ops.r.private(archive.parent / ("current" + revision + "-image-binding.json")).read_text())
    if receipt.get("current_image") != image:
        raise ValueError("receipt does not match the authenticated current successor image")
    if phase == 24:
        record = archive.parent / DAILY_VALUE_PREDECESSOR_BINDING
        pinned = ops.portfolio_sources().PORTFOLIO0027
        record_data = ops.r.private(record).read_bytes()
        retained_image = json.loads(record_data)
        require_successor_image(retained_image, {
            "tested_source": pinned["commit"], "app_tree": pinned["app_tree"],
            "context_sha256": pinned["archive_sha256"],
        })
        if receipt.get("predecessor_image_sha256") != hashlib.sha256(record_data).hexdigest():
            raise ValueError("receipt does not match the authenticated 0027 predecessor image")
    ops.r.bundle_verify(archive, expected, required_profile=profile)
    authenticate(ops, archive, expected, campaign_sources(ops, successor=True, phase=phase),
                 successor_identity=identity, phase=phase)
    return expected, hashlib.sha256(receipt_data).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--phase", type=int, choices=[14, 15, 21, 24], default=14)
    parser.add_argument("--suite", required=True,
                        choices=["all-security", "recovery", "recovery-current", "recovery-successor"])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--verify-successor-receipt", metavar="TESTED_SHA")
    args = parser.parse_args(argv)
    try:
        archive = validate_selection(args.suite, args.phase)
    except ValueError as exc:
        parser.error(str(exc))
    if args.verify_successor_receipt is not None:
        if args.suite != "recovery-successor":
            parser.error("receipt verification requires recovery-successor")
        print(*verify_successor_receipt(archive, args.verify_successor_receipt, phase=args.phase))
    elif args.preflight:
        print(json.dumps(preflight(args.suite, phase=args.phase), sort_keys=True))
    elif args.dry_run:
        print(json.dumps(security_commands() if args.suite == "all-security" else
                         {"phase": args.phase, "suite": args.suite, "archive": str(archive),
                          "stages": SUCCESSORS[args.phase][3] if args.suite == "recovery-successor"
                          else STAGES if args.suite == "recovery" else ("current0023-cold",)}, sort_keys=True))
    elif args.suite == "all-security":
        execute_security()
    else:
        execute_recovery(phase=args.phase, suite=args.suite)


if __name__ == "__main__":
    main()
