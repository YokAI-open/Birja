#!/usr/bin/env python3
"""Run actual browser tests on a guarded disposable stack, never the dev stack."""

import argparse
import hashlib
import html
import json
import os
import re
import socket
import subprocess
import tempfile
import time
import zipfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECT = "birja-phase09-e2e-test"


def browser_specs(suite):
    retained = ('auth', 'csp', 'health', 'markets', 'trade', 'stocks',
                'stock-trades', 'stock-actions', 'dividends-history',
                'portfolio-history', 'portfolio-ownership', 'portfolio-strategies',
                'portfolio-deletion')
    selections = {'all': retained, 'stocks': ('stock-trades',),
                  'actions': ('stock-actions',), 'dividends': ('dividends-history',),
                  'portfolios': ('portfolio-ownership', 'portfolio-strategies', 'portfolio-deletion')}
    if suite not in selections:
        raise ValueError('unsupported browser suite')
    return ['e2e/' + name + '.spec.ts' for name in selections[suite]]


def require_browser_specs(specs, *, directory=None):
    directory = directory or ROOT / 'frontend'
    for name in specs:
        path = directory / name
        if path.is_symlink() or not path.is_file():
            raise ValueError('missing or unsafe required browser journey: ' + name)


def source_snapshot():
    """Bind rendered review evidence to actual source, including uncommitted files."""
    paths = [ROOT / 'frontend/package-lock.json', ROOT / 'backend/uv.lock', Path(__file__),
             ROOT / 'deploy/tests/dividend-execution-fixture.py']
    for directory in ('frontend/src', 'frontend/e2e', 'backend/app', 'backend/alembic'):
        paths.extend(p for p in (ROOT / directory).rglob('*')
                     if p.is_file() and p.suffix in {'.ts', '.tsx', '.css', '.py', '.sql'})
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(set(paths))}


def finish_review(directory, source, commit, phase=12):
    if source != source_snapshot():
        raise RuntimeError('Source drift during browser proof')
    files = sorted(directory.iterdir())
    if not files or any(p.is_symlink() or p.suffix not in {'.png', '.html'} for p in files):
        raise RuntimeError('Missing or unsafe rendered review evidence')
    manifest = {'format': 1, 'synthetic': True, 'git_commit': commit,
                'source_sha256': source, 'native_200_percent_verified': False,
                'artifacts': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    with (directory / 'manifest.json').open('x') as output:
        json.dump(manifest, output, indent=2, sort_keys=True)
    links = ''.join('<li><a href="' + html.escape(p.name, quote=True) + '">' +
                    html.escape(p.stem) + '</a></li>' for p in files if p.suffix == '.html')
    with (directory / 'index.html').open('x') as output:
        output.write(f'<!doctype html><meta charset="utf-8"><title>Phase{phase} synthetic review</title>'
                     f'<h1>Phase{phase} portfolio review</h1><p>Read-only actual rendered synthetic pages. '
                     'Open each page and use your browser menu at 200% zoom; emulated reflow is not '
                     'native zoom acceptance. No action executes.</p><ul>' + links + '</ul>')
    for p in directory.iterdir():
        p.chmod(0o400)
    archive = directory.with_suffix('.zip')
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as output:
        for p in sorted(directory.iterdir()):
            output.write(p, p.name)
    archive.chmod(0o600)
    directory.chmod(0o500)
    print('REVIEW ' + str(archive), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=("all", "stocks", "actions", "dividends", "portfolios"), default="all")
    parser.add_argument("--review-dir", type=Path, help="Exclusive synthetic Phase12 review directory under /tmp")
    parser.add_argument("--grep", help="Optional bounded Playwright test-name selector")
    args = parser.parse_args()
    required_specs = browser_specs(args.suite)
    require_browser_specs(required_specs)
    source = source_snapshot()
    if args.grep is not None and (not args.grep or len(args.grep) > 256):
        parser.error("--grep must contain1..256 characters")
    os.umask(0o077)
    if args.review_dir is not None:
        target = args.review_dir
        if (not target.is_absolute() or target.parent != Path('/tmp')
                or not target.name.startswith(('birja-phase12-ui-review-', 'birja-phase14-ui-capture-')) or target.exists()
                or target.is_symlink()):
            parser.error('review-dir must be a new /tmp/birja-phase12-ui-review-* directory')
        target.mkdir(mode=0o700)
    work = Path(tempfile.mkdtemp(prefix="birja-phase09-browser-"))
    work.chmod(0o700)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    envfile = work / "synthetic.env"
    envfile.write_text(
        "ENV=dev\nPOSTGRES_USER=birja\nPOSTGRES_PASSWORD=synthetice2eonly\n"
        "POSTGRES_DB=birja\nREDIS_PASSWORD=syntheticredisE2E\n"
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
            "COMPOSE_PROJECT_NAME": PROJECT,
        },
        command=[
            "sh",
            "-c",
            "python -m app.db.dev_bootstrap --migrate && exec python /e2e/stock-trade-fixture.py serve",
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
    if args.review_dir is not None:
        env['BIRJA_PHASE12_REVIEW_DIR'] = str(args.review_dir)
        if args.review_dir.name.startswith('birja-phase14-ui-capture-'):
            env['BIRJA_PHASE14_REVIEW_DIR'] = str(args.review_dir)
    env['BIRJA_PHASE12_SOURCE'] = subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if 'BIRJA_PHASE14_REVIEW_DIR' in env:
        env['BIRJA_PHASE14_SOURCE'] = env['BIRJA_PHASE12_SOURCE']
    dc = ["docker", "compose", "--env-file", str(envfile)]
    pw = [
        str(ROOT / "frontend/node_modules/.bin/playwright"),
        "test",
        "--config",
        str(ROOT / "frontend/playwright.config.ts"),
        "--workers=1",
        "--retries=0",
    ]
    pw.extend(required_specs)
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
                "birja",
                "-d",
                "birja",
                "-v",
                "ON_ERROR_STOP=1",
                "-c",
                "CREATE ROLE birja_action_operator NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS; CREATE ROLE birja_migrator LOGIN PASSWORD 'syntheticMigratorE2E' NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS; GRANT CREATE ON SCHEMA public TO birja_migrator",
            ],
        )
        run('legacy-seed', dc + ['run', '--rm', '--no-deps', 'backend', 'python',
                                '/e2e/portfolio-browser-fixture.py', 'legacy'])
        run(
            "up-app",
            dc + ["up", "--no-build", "-d", "--wait", "--wait-timeout", "180"],
            timeout=240,
        )
        run("browser-" + args.suite, pw, timeout=900)
        if args.review_dir is not None:
            finish_review(args.review_dir, source, env['BIRJA_PHASE12_SOURCE'],
                          phase=14 if 'BIRJA_PHASE14_REVIEW_DIR' in env else 12)
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
