#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
python3 - "$ROOT" <<'PY'
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

root = Path(sys.argv[1]).resolve()
project = os.environ.get("BIRJA_TEST_PROJECT", "birja-test")
if not re.fullmatch(r"birja-(?:test|p14-15(?:-[a-z0-9]+)?|p14-16-preflight|p15-01-preflight)", project):
    raise ValueError("explicit owned or authenticated campaign test project required")
compose = ["docker", "compose", "--env-file", "/dev/null", "-p", project,
           "-f", str(root / "docker-compose.test.yml")]
env = {key: os.environ[key] for key in ("PATH", "HOME", "LANG") if key in os.environ}
env.update(ENV="test", PRICE_SOURCE="fake", EMAIL_BACKEND="console",
           DATABASE_URL="postgresql+asyncpg://birja_test:test@127.0.0.1:55432/birja_test",
           REDIS_URL="redis://:test@127.0.0.1:56379/0",
           OTP_HMAC_SECRET="synthetic-db-config-otp-" + "x" * 40,
           JWT_SECRET="synthetic-db-config-jwt-" + "y" * 40,
           COMPOSE_PROJECT_NAME=project, COMPOSE_DISABLE_ENV_FILE="1",
           UV_NO_SYNC="1", UV_OFFLINE="1")
def output(argv):
    return subprocess.check_output(argv, cwd=root, env=env, text=True, timeout=30)


def validate_stack(identities):
    expected = json.loads(output(compose + ["config", "--format", "json"]))["services"]
    assert set(expected) == {"postgres", "redis"}
    rows = json.loads(output(["docker", "inspect", *identities]))
    assert len(rows) == 2, "Refuse partial or foreign test stack"
    seen = set()
    for row in rows:
        labels = row["Config"]["Labels"]
        service = labels.get("com.docker.compose.service")
        assert labels.get("com.docker.compose.project") == project
        assert labels.get("com.docker.compose.project.working_dir") == str(root)
        assert labels.get("com.docker.compose.project.config_files") == str(root / "docker-compose.test.yml")
        assert service in expected and service not in seen
        seen.add(service)
        assert row["State"]["Status"] == "running"
        assert row["State"].get("Health", {}).get("Status") == "healthy"
        image = expected[service]["image"]
        assert "@sha256:" in image and row["Config"]["Image"] == image
        assert row["Image"] == output(["docker", "image", "inspect", image, "--format", "{{.Id}}"]).strip()
        ports = {str(port["target"]) + "/" + port["protocol"]:
                 [{"HostIp": port["host_ip"], "HostPort": str(port["published"])}]
                 for port in expected[service]["ports"]}
        assert row["NetworkSettings"]["Ports"] == ports
        assert set(row["NetworkSettings"]["Networks"]) == {project + "_default"}
    assert seen == set(expected)


# This script also runs inside the complete security campaign. Reuse its
# authenticated, healthy stack without adopting its cleanup ownership.
existing = output(compose + ["ps", "--all", "-q"]).splitlines()
started = time.monotonic()
status = 1
owns_stack = not existing
if owns_stack:
    for kind in ("network", "volume"):
        if output(["docker", kind, "ls", "-q", "--filter",
                   "label=com.docker.compose.project=" + project]).strip():
            raise ValueError("refuse orphaned caller resources before acquiring stack ownership")
try:
    if owns_stack:
        subprocess.run(compose + ["up", "-d", "--wait"], cwd=root, env=env, check=True, timeout=120)
        validate_stack(output(compose + ["ps", "--all", "-q"]).splitlines())
    else:
        validate_stack(existing)
    print(f"test-db-config owns_stack={str(owns_stack).lower()}", flush=True)
    print(f"test-db-config fixture setup: {time.monotonic() - started:.3f}s", flush=True)
    tests_started = time.monotonic()
    status = subprocess.run(
        ["uv", "run", "--locked", "--no-sync", "pytest", "-q", "tests/test_db_connection.py",
         "tests/test_config.py", "tests/test_config_scheduler.py", "tests/test_config_prices.py",
         "tests/test_health.py", "tests/test_scheduler_loop.py",
         "tests/test_portfolio_closure_authority.py::test_named_closure_is_atomic_immutable_and_preserves_finances",
         "tests/test_portfolio_creation.py::test_actual_app_lost_response_replay_normalization_rename_and_conflict",
         "tests/test_portfolio_management_admission.py::test_complete_current_and_actual_retained_source_refusal"],
        cwd=root / "backend", env=env, timeout=180,
    ).returncode
    print(f"test-db-config focused tests: {time.monotonic() - tests_started:.3f}s", flush=True)
finally:
    if owns_stack:
        cleanup = subprocess.run(compose + ["down", "-v"], cwd=root, env=env, timeout=120)
        if status == 0 and cleanup.returncode:
            status = cleanup.returncode
sys.exit(status)
PY
