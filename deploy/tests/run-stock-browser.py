#!/usr/bin/env python3
"""Run actual browser tests on a guarded disposable stack, never the dev stack."""

import argparse
import json
import os
import re
import socket
import subprocess
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECT = "birja-phase09-e2e-test"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=("all", "stocks", "actions", "dividends"), default="all")
    parser.add_argument("--grep", help="Optional bounded Playwright test-name selector")
    args = parser.parse_args()
    if args.grep is not None and (not args.grep or len(args.grep) > 256):
        parser.error("--grep must contain1..256 characters")
    os.umask(0o077)
    work = Path(tempfile.mkdtemp(prefix="birja-phase09-browser-"))
    work.chmod(0o700)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    envfile = work / "synthetic.env"
    envfile.write_text(
        "ENV=dev\nPOSTGRES_USER=birja_e2e\nPOSTGRES_PASSWORD=synthetice2eonly\n"
        "POSTGRES_DB=birja_e2e\nREDIS_PASSWORD=syntheticredisE2E\n"
        "OTP_HMAC_SECRET=synthetic-e2e-only-otp-" + "a" * 64 + "\n"
        "JWT_SECRET=synthetic-e2e-only-jwt-" + "b" * 64 + "\n"
        "EMAIL_BACKEND=console\nPRICE_SOURCE=fake\n"
        "STOCK_DATA_ENABLED=false\nSTOCK_ACTIONS_ENABLED=false\n"
    )
    envfile.chmod(0o600)
    services = {
        name: {"restart": "no"}
        for name in ("postgres", "redis", "backend", "scheduler", "frontend")
    }
    services["postgres"].update(volumes="RESET", tmpfs=["/var/lib/postgresql:size=268435456"])
    services["redis"].update(
        volumes="RESET", tmpfs=["/data:size=67108864,uid=65532,gid=65532,mode=0750"]
    )
    services["backend"].update(
        volumes=[
            {
                "type": "bind",
                "source": str(ROOT / "frontend/e2e"),
                "target": "/e2e",
                "read_only": True,
            },
            {
                "type": "bind",
                "source": str(ROOT / "deploy/tests"),
                "target": "/browser-fixtures",
                "read_only": True,
            },
        ],
        environment={
            "BIRJA_E2E_GUARD": "phase09-isolated",
            "BIRJA_E2E_ANCHOR": datetime.now(UTC).isoformat(),
        },
        command=[
            "sh",
            "-c",
            "alembic upgrade head && exec python /e2e/stock-trade-fixture.py serve",
        ],
    )
    services["frontend"]["ports"] = [f"127.0.0.1:{port}:5173"]
    # YAML reset tags remove base persistent mounts; the rest is JSON-compatible YAML.
    # Generate each service as a JSON object, replacing only the fixed RESET sentinel.
    chunks = ["name: " + PROJECT, "volumes: !reset {}", "services:"]
    for name, config in services.items():
        chunks.append("  " + name + ":")
        for key, value in config.items():
            rendered = "!reset []" if value == "RESET" else json.dumps(value)
            chunks.append("    " + key + ": " + rendered)
    override = work / "override.yml"
    override.write_text("\n".join(chunks) + "\n")
    # Retain only process/tool access, never provider/account/Compose interpolation values.
    env = {
        key: os.environ[key]
        for key in ("PATH", "HOME", "LANG", "DOCKER_CONFIG", "XDG_RUNTIME_DIR")
        if key in os.environ
    }
    env.update(
        COMPOSE_FILE=str(ROOT / "docker-compose.yml") + ":" + str(override),
        COMPOSE_PROJECT_NAME=PROJECT,
        COMPOSE_ENV_FILES=str(envfile),
        COMPOSE_DISABLE_ENV_FILE="1",
        E2E_BASE_URL=f"http://localhost:{port}",
        PLAYWRIGHT_BROWSERS_PATH=os.environ.get(
            "PLAYWRIGHT_BROWSERS_PATH", str(Path.home() / ".cache/ms-playwright")
        ),
        CI="1",
    )
    dc = ["docker", "compose", "--env-file", str(envfile)]
    pw = [
        str(ROOT / "frontend/node_modules/.bin/playwright"),
        "test",
        "--config",
        str(ROOT / "frontend/playwright.config.ts"),
        "--workers=1",
        "--retries=0",
    ]
    if args.suite != "all":
        pw.append(
            {
                "stocks": "e2e/stock-trades.spec.ts",
                "actions": "e2e/stock-actions.spec.ts",
                "dividends": "e2e/dividends-history.spec.ts",
            }[args.suite]
        )
    if args.grep is not None:
        pw.extend(["--grep", args.grep])

    def run(name, argv, timeout=600, required=True):
        print("START " + name, flush=True)
        started = time.monotonic()
        result = subprocess.run(
            argv,
            check=False,
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
        safe = re.sub(r"code=\d{6}", "code=******", re.sub(r"to=[^\s]+", "to=***", result.stdout))
        (work / (name + ".log")).write_text(safe)
        print(
            f"{name} exit={result.returncode} seconds={time.monotonic() - started:.1f}",
            flush=True,
        )
        if required and result.returncode:
            raise RuntimeError(name + " failed; evidence=" + str(work))
        return result

    probes = (
        ("containers", ["ps", "-aq"]),
        ("networks", ["network", "ls", "-q"]),
        ("volumes", ["volume", "ls", "-q"]),
    )
    # Existing project resources belong to their caller. Never delete them to make room.
    for kind, command in probes:
        if run(
            "preexisting-" + kind,
            [
                "docker",
                *command,
                "--filter",
                "label=com.docker.compose.project=" + PROJECT,
            ],
        ).stdout.strip():
            raise RuntimeError("Existing browser project; refusing ownership and cleanup")
    print("EVIDENCE " + str(work), flush=True)
    try:
        cfg = json.loads(run("render", dc + ["config", "--format", "json"]).stdout)
        assert cfg["name"] == PROJECT and not cfg.get("volumes")
        for name, service in cfg["services"].items():
            assert not service.get("privileged") and not service.get("network_mode")
            assert service["restart"] == "no"
            if name == "backend":
                mounts = service.get("volumes", [])
                assert len(mounts) == 2 and mounts[0]["read_only"] and mounts[0]["target"] == "/e2e"
                assert mounts[0]["source"] == str(ROOT / "frontend/e2e")
                assert mounts[1]["read_only"] and mounts[1]["target"] == "/browser-fixtures"
                assert mounts[1]["source"] == str(ROOT / "deploy/tests")
            else:
                assert not service.get("volumes")
            if name != "frontend":
                assert not service.get("ports")
        assert cfg["services"]["frontend"]["ports"][0]["host_ip"] == "127.0.0.1"
        assert cfg["services"]["backend"]["environment"]["EMAIL_BACKEND"] == "console"
        assert cfg["services"]["backend"]["environment"]["STOCK_DATA_ENABLED"] == "false"
        assert cfg["services"]["scheduler"]["environment"]["PRICE_SOURCE"] == "fake"
        assert cfg["services"]["scheduler"]["environment"]["STOCK_ACTIONS_ENABLED"] == "false"
        run("build", dc + ["build", "backend", "scheduler", "frontend"], timeout=900)
        run(
            "up-data",
            dc + ["up", "--no-build", "-d", "--wait", "postgres", "redis"],
            timeout=180,
        )
        run(
            "isolated-operator",
            dc
            + [
                "exec",
                "-T",
                "postgres",
                "psql",
                "-U",
                "birja_e2e",
                "-d",
                "birja_e2e",
                "-v",
                "ON_ERROR_STOP=1",
                "-c",
                "CREATE ROLE birja_action_operator NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS; CREATE ROLE birja_migrator NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS; CREATE ROLE birja_scheduler LOGIN PASSWORD 'syntheticSchedulerE2E' NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS",
            ],
        )
        run(
            "up-app",
            dc + ["up", "--no-build", "-d", "--wait", "--wait-timeout", "180"],
            timeout=240,
        )
        run("browser-" + args.suite, pw, timeout=900)
    except Exception:
        run(
            "startup-diagnostics",
            dc + ["logs", "--no-color", "--tail", "80"],
            required=False,
        )
        raise
    finally:
        run("cleanup", dc + ["down", "--volumes", "--remove-orphans"], required=False)
        for kind, command in probes:
            assert not run(
                "remaining-" + kind,
                [
                    "docker",
                    *command,
                    "--filter",
                    "label=com.docker.compose.project=" + PROJECT,
                ],
            ).stdout.strip(), "Owned browser resources remain: " + kind


if __name__ == "__main__":
    main()
