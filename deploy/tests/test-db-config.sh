#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
python3 - "$ROOT" <<'PY'
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
started = time.monotonic()
status = 1
try:
    subprocess.run(compose + ["up", "-d", "--wait"], cwd=root, env=env, check=True, timeout=120)
    print(f"test-db-config fixture setup: {time.monotonic() - started:.3f}s", flush=True)
    tests_started = time.monotonic()
    status = subprocess.run(
        ["uv", "run", "--locked", "--no-sync", "pytest", "-q", "tests/test_db_connection.py",
         "tests/test_config.py", "tests/test_config_scheduler.py", "tests/test_config_prices.py"],
        cwd=root / "backend", env=env, timeout=120,
    ).returncode
    print(f"test-db-config focused tests: {time.monotonic() - tests_started:.3f}s", flush=True)
finally:
    cleanup = subprocess.run(compose + ["down", "-v"], cwd=root, env=env, timeout=120)
    if status == 0 and cleanup.returncode:
        status = cleanup.returncode
sys.exit(status)
PY
