#!/usr/bin/env python3
"""Stdlib structural/behavioral CI contracts; no YAML package dependency."""

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def jobs():
    workflow = (ROOT / ".github/workflows/ci.yml").read_text().split("\njobs:\n", 1)[1]
    matches = list(re.finditer(r"^  ([a-z][a-z0-9-]*):\n", workflow, re.MULTILINE))
    return {
        m[1]: workflow[
            m.end() : matches[i + 1].start() if i + 1 < len(matches) else len(workflow)
        ]
        for i, m in enumerate(matches)
    }


def image_policy(image, aggregate):
    """Validate strict required image wiring; also used against mutations."""
    for text in [
        "target: test-builder",
        "target: runtime",
        "tags: birja-backend-runtime:ci",
        "python3 deploy/scan-images.py",
        "--runtime",
        "--builder",
        "--postgres",
        "--redis",
        "--node",
        "actions/upload-artifact@",
        "image-reports",
        "if-no-files-found: error",
        "retention-days: 7",
        "if: always()",
        "2> image-reports/runtime-resolve.log",
        "2> image-reports/builder-resolve.log",
        "2> image-reports/node-resolve.log",
    ]:
        if text not in image:
            raise ValueError("missing image policy: " + text)
    if image.count("load: true") < 2 or "load: false" in image:
        raise ValueError("both built stages must load")
    for forbidden in [
        "continue-on-error",
        "ignore-unfixed",
        "ignorefile",
        "--vex",
        "|| true",
    ]:
        if forbidden in image:
            raise ValueError("fail-open image policy")
    if not re.search(r"needs: \[[^\]]*\bimage\b", aggregate):
        raise ValueError("image is required")


def recovery_policy(ops):
    required = [
        'archive = Path("/tmp/birja-backup-test-ci-final/recovery.tar")',
        "ops.r.bundle_package(archive)", "ops.image_transition()",
        "ops.roundtrip(archive)", "ops.roles()",
        "assert ops.tls() == ops.tls(fresh_bootstrap=True)",
        '"--recovery-bundle", str(archive)], check=True)',
        "assert ops.r.digest(archive) == expected",
        "assert source == {name: ops.r.digest(ROOT / name) for name in source}",
        "assert retained.extractfile(name).read() == (ROOT / name).read_bytes()",
    ]
    for text in required:
        if text not in ops:
            raise ValueError("missing retained recovery policy: " + text)
    stages = required[1:7]
    if [ops.index(text) for text in stages] != sorted(ops.index(text) for text in stages):
        raise ValueError("recovery stages reordered")
    if ops.count("unchanged()") != 7:
        raise ValueError("every recovery stage must preserve archive and source identity")


class CI(unittest.TestCase):
    def test_same_archive_recovery_rejects_missing_or_reordered_stages(self):
        ops = jobs()["ops"]
        recovery_policy(ops)
        for old in [
            "ops.r.bundle_package(archive)", "ops.image_transition()", "ops.roundtrip(archive)",
            "ops.roles()", "assert ops.tls() == ops.tls(fresh_bootstrap=True)",
            '"--recovery-bundle", str(archive)], check=True)',
            "assert ops.r.digest(archive) == expected",
            "assert retained.extractfile(name).read() == (ROOT / name).read_bytes()",
        ]:
            with self.assertRaises(ValueError):
                recovery_policy(ops.replace(old, "omitted_stage"))
        with self.assertRaises(ValueError):
            recovery_policy(ops.replace("ops.roles()", "ops.roundtrip(archive)", 1))
        with self.assertRaises(ValueError):
            recovery_policy(ops.replace("unchanged()", "omitted()", 1))
    def test_dividend_authority_history_and_schedulers_are_required(self):
        backend = jobs()["backend"]
        for module in [
            "services/dividend_rules", "services/dividends", "services/event_history",
            "schemas/event_history", "api/v1/event_history", "tasks/dividends",
            "tasks/scheduler", "db/dev_bootstrap",
        ]:
            self.assertIn("app/" + module + ".py", backend)
        self.assertIn("--cov-branch", backend)
        self.assertIn("test-stock-recovery-contracts.py --postgres", jobs()["ops"])
        fixture = (ROOT / "deploy/tests/ops-fixtures.py").read_text()
        for proof in [
            "actual_restored_dividend_saved_replay=true financial_quarantine=true",
            "actual_dividend_sql_verified_tls=true", "dividend_authority",
            "tls(fresh_bootstrap=True)",
        ]:
            self.assertIn(proof, fixture)
        dividend = (ROOT / "deploy/tests/dividend-execution-fixture.py").read_text()
        self.assertIn("record_stock_dividend_hold", dividend)

    def test_stock_safety_and_real_tls_evaluator_are_required(self):
        j = jobs()
        for module in ["stock_admission", "stock_quote_rules", "stock_quotes", "stock_sessions", "stocks"]:
            self.assertIn("app/services/" + module + ".py", j["backend"])
        self.assertIn("app/api/v1/stocks.py", j["backend"])
        fixture = (ROOT / "deploy/tests/ops-fixtures.py").read_text()
        self.assertIn("from app.services.stock_sessions import", fixture)
        self.assertIn("await calendar_consumer_contract(app,scheduler,migrator)", fixture)
        self.assertIn("tls(fresh_bootstrap=True)", fixture)
        self.assertIn("calendar_runtime_tls_consumer=true", fixture)
        self.assertNotIn("evaluator_proof=plan08_13", fixture)

    def test_ops_pins_compose_with_explicit_retained_dockerfile_consent(self):
        ops = jobs()["ops"]
        self.assertIn("compose_version=5.7.0-1~ubuntu.24.04~noble", ops)
        self.assertIn('"docker-compose-plugin=$compose_version"', ops)
        check = "test \"$(sudo -- env -i PATH=/usr/bin:/bin HOME=/tmp LANG=C.UTF-8 /usr/bin/docker compose version --short)\" = '5.7.0'"
        self.assertIn(check, ops)
        self.assertLess(
            ops.index(check), ops.index("- name: Build locked operations fixture image")
        )
        for bypass in [
            "BUILDX_BAKE_ENTITLEMENTS_FS",
            "COMPOSE_BAKE=false",
            "fs.read=*",
            "fs=*",
        ]:
            self.assertNotIn(bypass, ops)

    def test_ops_preserves_daemon_settings_and_checks_strict_archive_before_build(self):
        ops = jobs()["ops"]
        merge = ops.split("sudo python3 -c '\n", 1)[1].split("\n          '\n", 1)[0]
        merge = textwrap.dedent(merge)
        for initial in [None, {"log-driver": "local", "features": {"buildkit": True}}]:
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "daemon.json"
                if initial is not None:
                    path.write_text(json.dumps(initial))
                subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        merge.replace("/etc/docker/daemon.json", str(path)),
                    ],
                    check=True,
                )
                expected = initial or {}
                expected.setdefault("features", {})["containerd-snapshotter"] = True
                self.assertEqual(json.loads(path.read_text()), expected)
        self.assertLess(
            ops.index("containerd-snapshotter"),
            ops.index("sudo systemctl restart docker"),
        )
        check = "sudo -- env -i PATH=/usr/bin:/bin HOME=/tmp LANG=C.UTF-8 python3 deploy/tests/check-recovery-image.py"
        self.assertIn(check, ops)
        self.assertLess(
            ops.index(check), ops.index("- name: Build locked operations fixture image")
        )
        spec = importlib.util.spec_from_file_location(
            "image_preflight", ROOT / "deploy/tests/check-recovery-image.py"
        )
        preflight = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(preflight)
        for store in [[], [["driver-type", "io.containerd.snapshotter.v1"]]]:
            with (
                patch.object(
                    preflight.r, "call", return_value=json.dumps(store).encode()
                ),
                patch.object(preflight.subprocess, "run") as save,
                patch.object(
                    preflight.r,
                    "registry_manifests",
                    return_value=(b"index", b"manifest"),
                ) as manifests,
                patch.object(preflight.r, "verify_saved_image") as verify,
            ):
                if not store:
                    with self.assertRaises(ValueError):
                        preflight.main()
                    save.assert_not_called()
                    manifests.assert_not_called()
                    verify.assert_not_called()
                else:
                    preflight.main()
                    self.assertEqual(
                        save.call_args.args[0],
                        [
                            "/usr/bin/docker",
                            "image",
                            "save",
                            "--platform",
                            "linux/amd64",
                            preflight.r.REGISTRY_REF,
                        ],
                    )
                    self.assertEqual(verify.call_args.args[1:], (b"index", b"manifest"))

    def test_ops_prepares_default_socket_docker_platform_api_before_fixtures(self):
        ops = jobs()["ops"]
        setup = ops.index("- name: Prepare Docker platform API for recovery fixtures")
        verify = ops.index("- name: Verify recovery image platform capability")
        build = ops.index("- name: Build locked operations fixture image")
        self.assertLess(setup, verify)
        self.assertLess(verify, build)
        preparation = ops[setup:verify]
        for required in [
            "https://download.docker.com/linux/ubuntu/gpg",
            "signed-by=/etc/apt/keyrings/docker.asc",
            "docker_version=5:29.2.1-1~ubuntu.24.04~noble",
            '"docker-ce=$docker_version"',
            '"docker-ce-cli=$docker_version"',
            "sudo systemctl restart docker",
        ]:
            self.assertIn(required, preparation)
        preflight = ops[verify:build]
        for required in [
            "sudo -- /usr/bin/docker version",
            "29.2.1 29.2.1",
            "sudo -- /usr/bin/docker pull --platform linux/amd64",
            "env -i PATH=/usr/bin:/bin HOME=/tmp LANG=C.UTF-8",
            'image inspect "$postgres" --platform linux/amd64',
        ]:
            self.assertIn(required, preflight)
        for forbidden in ["trusted=yes", "--allow-unauthenticated", "DOCKER_HOST="]:
            self.assertNotIn(forbidden, ops[setup:build])

    def test_ops_prepares_locked_host_backend_before_db_config_contracts(self):
        ops = jobs()["ops"]
        self.assertIn("uses: astral-sh/setup-uv@v10.3.2", ops)
        setup = ops.index("uses: astral-sh/setup-uv@v10.3.2")
        install = ops.index("uv python install")
        sync = ops.index("uv sync --locked")
        contracts = ops.index("- name: Offline operational contracts")
        self.assertLess(setup, install)
        self.assertLess(install, sync)
        self.assertLess(sync, contracts)
        environment = ops[setup:contracts]
        self.assertIn("working-directory: backend", environment)
        self.assertIn("cache-dependency-glob: backend/uv.lock", environment)
        for excluded in ["--no-default-groups", "--no-dev", "--only-group"]:
            self.assertNotIn(excluded, environment)

    def test_image_policy_and_mutation_regressions(self):
        j = jobs()
        image_policy(j["image"], j["ci-pass"])
        for old, new in [
            ("python3 deploy/scan-images.py", "true"),
            ("--node", "--omitted"),
            ("image-reports", "other"),
            ("load: true", "load: false"),
            ("--runtime", "--ignore-unfixed --runtime"),
            ("push: false", "continue-on-error: true"),
            ("2> image-reports/node-resolve.log", "2>/dev/null"),
        ]:
            with self.assertRaises(ValueError):
                image_policy(j["image"].replace(old, new), j["ci-pass"])
        with self.assertRaises(ValueError):
            image_policy(j["image"], j["ci-pass"].replace(", image", ""))

    def test_required_aggregate_rejects_every_nonsuccess(self):
        j = jobs()
        self.assertIn("ops", j)
        needs = re.search(r"^    needs: \[([^\]]+)\]$", j["ci-pass"], re.MULTILINE)
        self.assertIsNotNone(needs)
        self.assertEqual(
            {s.strip() for s in needs[1].split(",")},
            {"backend", "frontend", "image", "e2e", "ops"},
        )
        self.assertIn("if: always()", j["ci-pass"])
        for result in ["failure", "cancelled", "skipped"]:
            self.assertIn("contains(needs.*.result, '" + result + "')", j["ci-pass"])
        self.assertRegex(j["ci-pass"], r"(?s)if \[.*exit 1")

    def test_ops_runs_real_serial_producers_with_verified_tool(self):
        ops = jobs().get("ops", "")
        rollback = (ROOT / "deploy/tests/test-rollback-db-security.sh").read_text()
        self.assertIn("selected.integration(args.recovery_bundle)", rollback)
        self.assertIn("sudo -- python3 deploy/tests/test-deploy-prerequisites.py", ops)
        self.assertIn("sudo -- python3 deploy/tests/test-datastore-bindings.py", ops)
        self.assertRegex(
            ops, r"(?m)^          sudo -- bash deploy/check-nginx-config\.sh$"
        )
        self.assertIn("sudo -- python3 - <<'PY'", ops)
        recovery_policy(ops)
        self.assertNotIn("sudo -- bash deploy/tests/test-db-config.sh", ops)
        for forbidden in ["sudo -E", "safe.directory=*", "git config --global"]:
            self.assertNotIn(forbidden, ops)
        self.assertIn("timeout-minutes: 30", ops)
        self.assertNotIn("secrets.", ops)
        self.assertIn("fetch-depth: 0", ops)
        self.assertIn("CF8F18F2844575973F79D4E191A6868BD3F7A907", ops)
        self.assertIn("VALIDSIG", ops)
        self.assertIn(
            "f415415624dcc452f2a02b8c33641791a8c6d6d3b65bbb3543fcf9a25151585c", ops
        )
        self.assertIn(
            "20d4142678d0d95ec11a4759def1b73fd9190abc9ca19e4b62d067c0b387e639", ops
        )
        self.assertIn("birja-backend-test:phase05-07", ops)
        for producer in [
            "test-backup.sh",
            "test-restore-safety.sh",
            "test-db-config.sh",
            "test-deploy-prerequisites.py",
            "test-rollback-db-security.sh",
            "test-reexec.sh",
            "test-rollback-target.sh",
            "test-app-services.sh",
            "test-smoke-ports.sh",
            "test-smoke-trading.sh",
        ]:
            self.assertIn(producer, ops)
        self.assertLess(
            ops.index("ops.roundtrip(archive)"),
            ops.index("test-rollback-db-security.sh"),
        )
        cleanup = ops.split("- name: Clean fixed synthetic projects")[-1]
        self.assertIn("if: always()", cleanup)
        self.assertIn("--env-file /dev/null", cleanup)
        self.assertIn('"$GITHUB_WORKSPACE/docker-compose.ops-test.yml"', cleanup)
        self.assertNotIn("birja-prod", cleanup)

    def test_existing_browser_coverage_audits_are_preserved(self):
        j = jobs()
        for text in [
            "--cov-fail-under=80",
            "--fail-under=100",
            "uv run pip-audit",
            "app/services/trading.py",
            "app/services/portfolio.py",
            "app/api/v1/history.py",
        ]:
            self.assertIn(text, j["backend"])
        for text in [
            "npm run test -- --coverage",
            "npm audit --audit-level=high",
            "npm run lint",
            "npm run typecheck",
        ]:
            self.assertIn(text, j["frontend"])
        self.assertIn("PRICE_SOURCE=fake", j["e2e"])
        self.assertIn("EMAIL_BACKEND=console", j["e2e"])
        self.assertRegex(j["e2e"], r"(?m)^        run: python3 deploy/tests/run-stock-browser.py$")
        browser = (ROOT / "deploy/tests/run-stock-browser.py").read_text()
        for token in ('"frontend/node_modules/.bin/playwright"', '"test"', '"--workers=1"', '"--retries=0"', 'default="all"', 'COMPOSE_DISABLE_ENV_FILE'):
            self.assertIn(token, browser)
        self.assertIn('default="all"', browser)
        self.assertIn('len(args.grep) > 256', browser)
        self.assertRegex(j["e2e"], r"(?m)^        run: python3 deploy/tests/run-stock-browser.py$")
        self.assertIn("target: test-builder", j["image"])
        self.assertIn("target: runtime", j["image"])
        self.assertIn("pytest tests/test_smoke.py -q", j["image"])


class FixtureGitIsolation(unittest.TestCase):
    def test_generated_launcher_git_ignores_denied_host_config(self):
        spec = importlib.util.spec_from_file_location(
            "selected_cutover", ROOT / "deploy/tests/selected-cutover.py"
        )
        selected = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(selected)
        with (
            tempfile.TemporaryDirectory(prefix="birja-backup-test-git-") as tmp,
            tempfile.TemporaryDirectory(
                prefix="birja-backup-test-host-config-"
            ) as host,
        ):
            root = Path(tmp)
            app = root / "old/app"
            app.mkdir(parents=True)
            (root / "home").mkdir()
            (root / "tmp").mkdir()
            subprocess.run(["git", "init", "-q", str(app)], check=True)
            subprocess.run(
                ["git", "-C", str(app), "config", "fixture.marker", "local-only"],
                check=True,
            )
            denied = Path(host) / "gitconfig"
            denied.write_text("[fixture]\nmarker=host-only\n")
            result = selected.f.target(
                root,
                [
                    "env",
                    "GIT_CONFIG_SYSTEM=" + str(denied),
                    "git",
                    "-C",
                    str(app),
                    "rev-parse",
                    "--git-dir",
                ],
                ok=False,
            )
            self.assertIn(b"Permission denied", result.stderr)
            # Execute the actual generated launcher's clean environment block,
            # not a hand-built approximation. Production source is unchanged.
            source = (
                (ROOT / "deploy/deploy-entrypoint.sh")
                .read_text()
                .replace("/root", str(root / "home"))
            )
            generated = selected.isolate_entrypoint_environment(source, root)
            block = (
                "env = {"
                + generated.split("    env = {", 1)[1].split(
                    "\n    if 'DEPLOY_REF'", 1
                )[0]
            )
            script = (
                "import os, subprocess\nfrom pathlib import Path\nrelease=Path("
                + repr(str(root / "ops"))
                + ")\n"
                + textwrap.dedent(block)
                + "\nenv['GIT_CONFIG_SYSTEM']="
                + repr(str(denied))
                + "\nsubprocess.run(['/usr/bin/git','-C',"
                + repr(str(app))
                + ",'rev-parse','--git-dir'],env=env,check=True,stdout=subprocess.DEVNULL)"
                + "\nos.execve('/usr/bin/git',['git','-C',"
                + repr(str(app))
                + ",'config','fixture.marker'],env)"
            )
            result = selected.f.target(root, ["/usr/bin/python3", "-c", script])
            self.assertEqual(result.stdout.strip(), b"local-only")
            (app / ".git").rename(app / "hidden-git")
            result = selected.f.target(
                root, ["/usr/bin/python3", "-c", script], ok=False
            )
            self.assertIn(b"not a git repository", result.stderr)
            self.assertEqual(
                (ROOT / "deploy/deploy-entrypoint.sh")
                .read_text()
                .count("GIT_CONFIG_NOSYSTEM"),
                0,
            )


if __name__ == "__main__":
    unittest.main()
