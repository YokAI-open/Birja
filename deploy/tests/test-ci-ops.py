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


class CI(unittest.TestCase):
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
