#!/usr/bin/env python3
"""Behavioral command/oracle tests; fake transport is never a TLS/DB proof."""

import contextlib
import copy
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("portfolio_fixture", Path(__file__).with_name("portfolio-execution-fixture.py"))
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


def example():
    tables = {name: [{"id": index + 1, "portfolio_id": 1, "evidence": "saved"}]
              for index, name in enumerate(fixture.TABLES)}
    tables["stock_split_applications"] = [
        {"id": 7, "economic_event_id": 13, "coin_id": 20, "new_unit_epoch": 1,
         "owner_digest_version": None, "before_digest": "a" * 64, "after_digest": "b" * 64},
        {"id": 11, "economic_event_id": 17, "coin_id": 20, "new_unit_epoch": 2,
         "owner_digest_version": 2, "before_digest": "c" * 64, "after_digest": "d" * 64},
    ]
    return {"revision": "0017", "books": [
        ["Original", "25.00000000", "9999.00000000", False, "8.00000000", "20.00000000"],
        ["Sibling", "334.00000000", "1234.00000000", False, "4.00000000", "30.00000000"],
        ["Frozen", "123.00000000", "7777.00000000", True, "4.00000000", "20.00000000"],
    ], "tables": tables, "sequences": {"accounts": [3, True]}, "journal": [2, 3]}


class PortfolioFixtureContracts(unittest.TestCase):
    def run_command(self, args, value, calls=None):
        def transport(code):
            compile(code, "<actual-generated-program>", "exec")
            self.assertNotIn("from tests", code)
            self.assertIn("assert_ownership_consistent", code)
            self.assertIn("verified TLS required", code)
            if calls is not None:
                calls.append(code)
            return copy.deepcopy(value)
        with contextlib.redirect_stdout(io.StringIO()):
            return fixture.main(args, transport=transport)

    def test_real_dispatch_create_projection_verify_compare(self):
        with tempfile.TemporaryDirectory(prefix="birja-portfolio-contract-") as tmp:
            path = Path(tmp) / "before.json"
            calls = []
            value = example()
            self.run_command(["create"], value, calls)
            expected = self.run_command(["projection", "--snapshot", str(path)], value, calls)
            original = path.read_bytes()
            self.run_command(["verify"], value, calls)
            self.assertEqual(self.run_command(["compare", "--database", "birja_restore_test",
                "--snapshot", str(path), "--expected-sha256", expected], value, calls), expected)
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(len(calls), 4)
            with self.assertRaises(ValueError):
                self.run_command(["projection", "--snapshot", str(path)], value)

    def test_independent_money_oracle(self):
        for row in range(3):
            for column in (1, 2, 4, 5):
                value = example()
                value["books"][row][column] = "0.00000000"
                with self.subTest(row=row, column=column), self.assertRaises(ValueError):
                    self.run_command(["verify"], value)

    def test_every_evidence_mutation_refused_without_overwriting_expected(self):
        with tempfile.TemporaryDirectory(prefix="birja-portfolio-mutations-") as tmp:
            path = Path(tmp) / "expected.json"
            digest = fixture.save_snapshot(path, example())
            original = path.read_bytes()
            mutations = []
            # Independent table/cause/receipt/sequence/terminal and global key
            # changes all hit the actual compare command, not a string search.
            for table in fixture.TABLES:
                for column in ("portfolio_id", "user_id", "quantity", "cost_basis", "cash",
                               "starting_cash", "idempotency_key", "entitlement_id", "payment_id",
                               "supersedes_id", "closing_sequence", "unit_epoch", "closed_at",
                               "before_digest", "after_digest", "economic_event_id", "coin_id"):
                    value = example()
                    value["tables"][table][0][column] = "corrupt"
                    mutations.append((table + "." + column, value))
            for marker in (None, 1, 3):
                value = example()
                value["tables"]["stock_split_applications"][1]["owner_digest_version"] = marker
                mutations.append(("new-marker:" + str(marker), value))
            value = example()
            value["tables"]["stock_split_applications"][0]["owner_digest_version"] = 2
            mutations.append(("legacy-marker-rebind", value))
            value = example()
            value["sequences"]["accounts"][0] += 1
            mutations.append(("identity-tail", value))
            for label, value in mutations:
                with self.subTest(label=label), self.assertRaises(ValueError):
                    self.run_command(["compare", "--snapshot", str(path),
                                      "--expected-sha256", digest], value)
                self.assertEqual(path.read_bytes(), original)

    def test_missing_or_wrong_hash_and_unsafe_modes_databases(self):
        for mode in ("unknown", "seed", None):
            with self.assertRaises(ValueError):
                fixture.program(mode=mode)
        for database in ("birja", "birja_source_test", "production", "", "../postgres"):
            with self.assertRaises(ValueError):
                fixture.program(mode="projection", database=database)
        with self.assertRaises(ValueError):
            fixture.program(mode="create", database="birja_restore_test")
        with tempfile.TemporaryDirectory(prefix="birja-portfolio-hash-") as tmp:
            path = Path(tmp) / "expected.json"
            fixture.save_snapshot(path, example())
            for digest in (None, "", "0" * 64, "x" * 64):
                with self.assertRaises(ValueError):
                    self.run_command(["compare", "--snapshot", str(path),
                        "--expected-sha256", digest or ""], example())
        with self.assertRaises(ValueError):
            fixture.command_transport("pass")

    def test_legacy_or_incomplete_projection_refused(self):
        for revision in ("0013", "0014", "0015", "0016", "head"):
            value = example()
            value["revision"] = revision
            with self.assertRaises(ValueError):
                self.run_command(["verify"], value)
        for table in fixture.TABLES:
            value = example()
            del value["tables"][table]
            with self.assertRaises(ValueError):
                self.run_command(["verify"], value)


if __name__ == "__main__":
    unittest.main()
