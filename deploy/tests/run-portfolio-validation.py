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
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = Path("/tmp/birja-phase14-proof/recovery.tar.gz")
PRESERVED_ARCHIVE = Path("/tmp/birja-phase13-proof/recovery.tar.gz")
PRESERVED_SHA256 = "6fb79a45ddcb10725b18fc756e71bd555c827a6e61a5a4a0bd2d183096114b92"
STAGES = ("image-transition", "retained-roundtrip", "current0023-cold",
          "roles", "tls-upgraded", "tls-fresh", "selected-rollback")
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


def preflight(suite, *, run=subprocess.run, fixture_tail=True):
    if suite not in {"all-security", "recovery"}:
        raise ValueError("explicit qualification suite required")
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
    recovery.closure_source(ROOT)
    fixture = json.loads((ROOT / "deploy/tests/fixtures/portfolio-recovery-0023.json").read_text())
    if (fixture.get("format"), fixture["manifest"].get("revision"),
            len(fixture["manifest"]["tables"]), len(fixture["manifest"]["identity_state"])) != (3, "0023", 31, 24):
        raise ValueError("exact current31/24 fixture profile required")
    prior = preserved_archive()
    if suite == "recovery" and ARCHIVE.parent.exists():
        raise ValueError("exclusive new recovery archive directory must be absent")
    if fixture_tail:
        run(["bash", "deploy/tests/test-db-config.sh"], cwd=ROOT,
            env={**env, "BIRJA_TEST_PROJECT": "birja-p14-16-preflight"}, check=True, timeout=300)
    return {"ok": True, "suite": suite, "tools": tools,
            "fixture_tail": "passed" if fixture_tail else "not-run-offline-diagnostic",
            "preserved_archive_sha256": prior, "path": env["PATH"]}


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


def security_sources():
    # Ignore credential files using the repository's normal ignore rules, but
    # bind additions/renames as well as tracked edits. Never follow a source
    # symlink outside the checkout or read its target as a secret.
    exclude = ROOT / ".git/info/exclude"
    if exclude.is_symlink():
        raise ValueError("source ignore metadata symlink refused")
    env = {**environment(), "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null"}
    raw = subprocess.check_output(["git", "-c", "core.fsmonitor=false", "-c",
        "core.excludesfile=/dev/null", "ls-files", "--cached", "--others", "--exclude-standard",
        "-z", "--", *SOURCE_SCOPES], cwd=ROOT, env=env)
    names = {os.fsdecode(name) for name in raw.split(b"\0") if name}
    if exclude.is_file():
        names.add(".git/info/exclude")
    result = {}
    for name in sorted(names):
        path = ROOT / name
        if path.is_symlink():
            if not path.resolve().is_relative_to(ROOT.resolve()):
                raise ValueError("source symlink escapes checkout")
            data = b"symlink\0" + os.fsencode(os.readlink(path))
        elif path.is_file():
            data = path.read_bytes()
        else:
            raise ValueError("source inventory disappeared or is not a regular file")
        result[name] = hashlib.sha256(data).hexdigest()
    return result


def campaign_sources(ops):
    names = ops.r.CORE + ops.r.UNITS + ops.r.PORTFOLIO_PAYLOAD_V3
    # Complete current application input, separate from fixed retained sources.
    tracked = subprocess.check_output(["git", "ls-files", "backend", "deploy", "docker-compose.ops-test.yml"], cwd=ROOT).decode().splitlines()
    return {name: ops.r.digest(ROOT / name) for name in sorted(set(names + tracked))}


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


def authenticate(ops, archive, expected, source, image_records=None):
    ops.portfolio_sources().verify_archive_binding(archive, expected)
    if source != {name: ops.r.digest(ROOT / name) for name in source}:
        raise ValueError("current campaign source changed")
    with tarfile.open(archive, "r:") as retained:
        inventory = json.load(retained.extractfile("INVENTORY.json"))
        payload = inventory.get("portfolio_payload", {})
        if (inventory.get("recovery_profile"), payload.get("version"), payload.get("revision")) != (
                "deploy-recovery-v4", 3, "0023"):
            raise ValueError("current campaign requires successor inventory")
        for name in ops.r.CORE + ops.r.UNITS + ops.r.PORTFOLIO_PAYLOAD_V3:
            if retained.extractfile(name).read() != (ROOT / name).read_bytes():
                raise ValueError("packaged/current source substitution")
        for name, digest in ops.r.RETAINED_CLOSURE_SOURCE_PAYLOADS.items():
            if ops.r.sha_bytes(retained.extractfile(name).read()) != "sha256:" + digest:
                raise ValueError("fixed retained payload substitution")
    ops.portfolio_sources().validate_matrix()
    records = {p.name: p for p in archive.parent.glob("*-image-binding.json")}
    if image_records is not None:
        if any(name not in records or ops.r.digest(records[name]) != sha
               for name, sha in image_records.items()):
            raise ValueError("recorded campaign image identity disappeared/changed")
    for record in records.values():
        ops.r.private(record)
        binding = json.loads(record.read_text())
        inspect = json.loads(ops.r.call(["docker", "image", "inspect", binding["id"]]))
        ops.portfolio_sources().verify_image(binding, inspect)
        if image_records is not None:
            image_records[record.name] = ops.r.digest(record)
    load("portfolio-smoke").authenticate_campaign_images(archive, expected,
        inspect_image=lambda ref: json.loads(ops.r.call(["docker", "image", "inspect", ref])))


def execute_stages(operations, guard):
    results = {}
    guard()
    for name in STAGES:
        try:
            results[name] = operations[name]()
        finally:
            guard()
    authorities = [results[name] for name in ("current0023-cold", "tls-upgraded", "tls-fresh")]
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


def execute_recovery():
    ops = load("ops-fixtures")
    prior_archive = preserved_archive()
    # Exclusive directory ownership prevents silently reusing an earlier run.
    ARCHIVE.parent.mkdir(mode=0o700)
    ops.r.private(ARCHIVE.parent, True)
    ops.package_current_archive(ARCHIVE)
    expected = ops.r.digest(ARCHIVE)
    ops.r.bundle_verify(ARCHIVE, expected, required_profile="deploy-recovery-v4")
    source = campaign_sources(ops)
    image_records = {}
    ops.bind_source_archive(ARCHIVE, expected)
    status = {"ok": False, "archive_sha256": expected, "stages": {}}
    status_path = ARCHIVE.parent / "status.json"
    operations = recovery_operations(ops, ARCHIVE, expected)
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
        authenticate(ops, ARCHIVE, expected, source, image_records)
    try:
        execute_stages({name: recorded(name) for name in STAGES},
                       guard)
        status["ok"] = True
        status["stages"] = dict.fromkeys(STAGES, "passed-authenticated")
    finally:
        save_status()
    print("same_archive_final_ci=true sha256=" + expected, flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--suite", required=True, choices=["all-security", "recovery"])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args(argv)
    if args.dry_run and args.preflight:
        parser.error("preflight and dry-run are distinct commands")
    if args.preflight:
        print(json.dumps(preflight(args.suite), sort_keys=True))
    elif args.dry_run:
        print(json.dumps(security_commands() if args.suite == "all-security" else
                         {"archive": str(ARCHIVE), "stages": STAGES}, sort_keys=True))
    elif args.suite == "all-security":
        execute_security()
    else:
        execute_recovery()


if __name__ == "__main__":
    main()
