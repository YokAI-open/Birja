#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
python3 - "$ROOT" <<'PY'
import json
import os
import subprocess
import sys
import time
from pathlib import Path

root = Path(sys.argv[1]).resolve()
compose = ["docker", "compose", "--env-file", "/dev/null", "-p", "birja-test",
           "-f", str(root / "docker-compose.test.yml")]
env = {key: value for key, value in os.environ.items()
       if not key.startswith(("COMPOSE_", "DATABASE_", "TEST_DATABASE_", "REDIS_", "TEST_REDIS_"))}
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
        assert labels.get("com.docker.compose.project") == "birja-test"
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
        assert set(row["NetworkSettings"]["Networks"]) == {"birja-test_default"}
    assert seen == set(expected)


# This script also runs inside the complete security campaign. Reuse its
# authenticated, healthy stack without adopting its cleanup ownership.
existing = output(compose + ["ps", "--all", "-q"]).splitlines()
started = time.monotonic()
status = 1
owns_stack = not existing
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
         "tests/test_health.py", "tests/test_scheduler_loop.py"],
        cwd=root / "backend", env=env, timeout=120,
    ).returncode
    print(f"test-db-config focused tests: {time.monotonic() - tests_started:.3f}s", flush=True)
finally:
    if owns_stack:
        cleanup = subprocess.run(compose + ["down", "-v"], cwd=root, env=env, timeout=120)
        if status == 0 and cleanup.returncode:
            status = cleanup.returncode
sys.exit(status)
PY
