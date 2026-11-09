#!/usr/bin/env python3
"""Stdlib structural/behavioral CI contracts; no YAML package dependency."""

import re
import unittest
from pathlib import Path

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


class CI(unittest.TestCase):
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
        self.assertIn("sudo -- python3 deploy/tests/test-deploy-prerequisites.py", ops)
        self.assertRegex(
            ops, r"(?m)^          sudo -- bash deploy/check-nginx-config\.sh$"
        )
        for arguments in [
            "test-db-operations.sh --image-transition",
            "test-db-operations.sh --all",
            "test-rollback-db-security.sh",
        ]:
            self.assertIn("sudo -- bash deploy/tests/" + arguments, ops)
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
            "test-db-operations.sh --all",
            "test-db-operations.sh --image-transition",
            "test-rollback-db-security.sh",
            "test-reexec.sh",
            "test-rollback-target.sh",
            "test-app-services.sh",
            "test-smoke-ports.sh",
            "test-smoke-trading.sh",
        ]:
            self.assertIn(producer, ops)
        self.assertLess(
            ops.index("test-db-operations.sh --all"),
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
        self.assertRegex(j["e2e"], r"(?m)^        run: npx playwright test$")
        self.assertIn("target: test-builder", j["image"])
        self.assertIn("target: runtime", j["image"])
        self.assertIn("pytest tests/test_smoke.py -q", j["image"])


if __name__ == "__main__":
    unittest.main()
