#!/usr/bin/env python3
"""Local CI-equivalent qualification; synthetic endpoints and one owned archive.

No dependency installation, credentials from .env, or provider access is used.
The .gz filename is the fixed campaign name; the authenticated recovery format
remains the uncompressed, strict-member USTAR used by older consumers.
"""

import argparse
import importlib.util
import json
import os
import shlex
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = Path("/tmp/birja-phase12-proof/recovery.tar.gz")
STAGES = ("image-transition", "retained-roundtrip", "current0017-cold",
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
        "npm run test -- --coverage", "npm run build", "npm audit --audit-level=high")]
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
    return commands


def execute_security(run=subprocess.run):
    env = environment()
    # Refuse to adopt somebody else's running test stack; cleanup is ours only.
    existing = run(STACK + ["ps", "-q"], cwd=ROOT, env=env, capture_output=True, check=True)
    if existing.stdout.strip():
        raise ValueError("refuse preexisting test stack")
    try:
        run(STACK + ["up", "-d", "--wait"], cwd=ROOT, env=env, check=True)
        for directory, argv in security_commands():
            if argv[:2] == ["python3", "deploy/scan-images.py"]:
                argv = argv.copy()
                for flag in ("--runtime", "--builder", "--node"):
                    index = argv.index(flag) + 1
                    argv[index] = run(["docker", "image", "inspect", argv[index], "--format", "{{.Id}}"],
                        cwd=ROOT, env=env, capture_output=True, check=True).stdout.decode().strip()
            run(argv, cwd=ROOT / directory, env=env, check=True)
    finally:
        run(STACK + ["down", "-v"], cwd=ROOT, env=env, check=True)


def campaign_sources(ops):
    names = ops.r.CORE + ops.r.UNITS + ops.r.PORTFOLIO_PAYLOAD_V1
    # Complete current application input, separate from fixed retained sources.
    tracked = subprocess.check_output(["git", "ls-files", "backend", "deploy", "docker-compose.ops-test.yml"], cwd=ROOT).decode().splitlines()
    return {name: ops.r.digest(ROOT / name) for name in sorted(set(names + tracked))}


def authenticate(ops, archive, expected, source, image_records=None):
    ops.portfolio_sources().verify_archive_binding(archive, expected)
    if source != {name: ops.r.digest(ROOT / name) for name in source}:
        raise ValueError("current campaign source changed")
    with tarfile.open(archive, "r:") as retained:
        inventory = json.load(retained.extractfile("INVENTORY.json"))
        if inventory.get("portfolio_payload", {}).get("version") != 1:
            raise ValueError("current campaign requires successor inventory")
        for name in ops.r.CORE + ops.r.UNITS + ops.r.PORTFOLIO_PAYLOAD_V1:
            if retained.extractfile(name).read() != (ROOT / name).read_bytes():
                raise ValueError("packaged/current source substitution")
        for name, digest in ops.r.RETAINED_SOURCE_PAYLOADS.items():
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
        results[name] = operations[name]()
        guard()
    if results["tls-upgraded"] != results["tls-fresh"]:
        raise ValueError("fresh/upgraded TLS authority differs")


def execute_recovery():
    ops = load("ops-fixtures")
    # Exclusive directory ownership prevents silently reusing an earlier run.
    ARCHIVE.parent.mkdir(mode=0o700)
    ops.r.private(ARCHIVE.parent, True)
    ops.r.bundle_package(ARCHIVE)
    expected = ops.r.digest(ARCHIVE)
    ops.r.bundle_verify(ARCHIVE, expected, required_profile="deploy-recovery-v2")
    source = campaign_sources(ops)
    image_records = {}
    ops.bind_source_archive(ARCHIVE, expected)
    execute_stages({
        "image-transition": ops.image_transition,
        "retained-roundtrip": lambda: ops.roundtrip(ARCHIVE),
        "current0017-cold": lambda: load("portfolio-smoke").run(archive=ARCHIVE, archive_sha=expected, cold=True),
        "roles": ops.roles,
        "tls-upgraded": ops.tls,
        "tls-fresh": lambda: ops.tls(fresh_bootstrap=True),
        "selected-rollback": lambda: subprocess.run(["bash", str(ROOT / "deploy/tests/test-rollback-db-security.sh"),
            "--recovery-bundle", str(ARCHIVE)], cwd=ROOT, env=environment(), check=True),
    }, lambda: authenticate(ops, ARCHIVE, expected, source, image_records))
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
