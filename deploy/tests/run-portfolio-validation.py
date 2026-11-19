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
import subprocess
import tarfile
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


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), Path(__file__).with_name(name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def environment():
    return {**{k: os.environ[k] for k in ("PATH", "HOME", "LANG") if k in os.environ},
            "COMPOSE_DISABLE_ENV_FILE": "1", "ENV": "test", "PRICE_SOURCE": "fake",
            "UV_NO_SYNC": "1", "UV_OFFLINE": "1",
            "EMAIL_BACKEND": "console", "DATABASE_URL": "postgresql+asyncpg://birja_test:test@127.0.0.1:55432/birja_test",
            "REDIS_URL": "redis://:test@127.0.0.1:56379/0",
            "OTP_HMAC_SECRET": "synthetic-only-validation-otp-" + "x" * 32,
            "JWT_SECRET": "synthetic-only-validation-jwt-" + "y" * 32}


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
    names = subprocess.check_output(['git', 'ls-files', 'backend', 'frontend', 'deploy',
        'nginx', '.github', 'CLAUDE.md', 'docker-compose*.yml'], cwd=ROOT).decode().splitlines()
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in names}


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


def execute_stages(operations, guard):
    results = {}
    guard()
    for name in STAGES:
        try:
            results[name] = operations[name]()
        finally:
            guard()
    if not (results["current0023-cold"] == results["tls-upgraded"] == results["tls-fresh"]):
        raise ValueError("cold/fresh/upgraded TLS authority differs")


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
        return smoke.run(archive=archive, archive_sha=expected, revision="0023",
                         fresh_bootstrap=fresh, upgraded_bootstrap=not fresh)

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
    def recorded(name):
        def execute():
            status["current_stage"] = name
            status_path.write_text(json.dumps(status, sort_keys=True))
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
        status_path.write_text(json.dumps(status, sort_keys=True))
    print("same_archive_final_ci=true sha256=" + expected, flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--suite", required=True, choices=["all-security", "recovery"])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if args.dry_run:
        print(json.dumps(security_commands() if args.suite == "all-security" else
                         {"archive": str(ARCHIVE), "stages": STAGES}, sort_keys=True))
    elif args.suite == "all-security":
        execute_security()
    else:
        execute_recovery()


if __name__ == "__main__":
    main()
