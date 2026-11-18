#!/usr/bin/env python3
"""0020 producer/oracle contracts; offline tests never claim encrypted proof."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


producer = load("producer", "deploy/backup-snapshot.py")


class ManagementRecoveryContracts(unittest.TestCase):
    def test_versioned_exact_inventory_preserves_0017(self):
        self.assertIn("0020", producer.SUPPORTED_REVISIONS)
        v2 = producer.PORTFOLIO_PAYLOAD_V2
        for name in ("backend/app/models/portfolio_creation.py", "backend/alembic/sql/0020_portfolio_management.sql",
                     "backend/alembic/sql/0019_portfolio_metadata.sql", "deploy/tests/portfolio-management-recovery-fixture.py"):
            self.assertIn(name, v2)
        self.assertEqual(len(v2), len(set(v2)))
        self.assertEqual(len(producer.contract_columns("0017")), 27)
        self.assertEqual(len(producer.identity_tables("0017")), 20)
        self.assertEqual(len(producer.contract_columns("0020")), 29)
        self.assertEqual(len(producer.identity_tables("0020")), 22)
        for revision in ("0018", "0019", "0021", "head"):
            with self.assertRaises(ValueError):
                producer.manifest_sql(revision)

    def test_exact_populated_manifest_and_mutations(self):
        value = json.loads((ROOT / "deploy/tests/fixtures/portfolio-recovery-0020.json").read_text())
        producer.validate_manifest(value)
        self.assertEqual(value["management_state"]["initializations"], 3)
        self.assertEqual(value["management_state"]["creations"], 11)
        self.assertEqual(value["portfolio_state"]["active"], 11)
        self.assertEqual(value["portfolio_state"]["closed"], 1)
        mutations = [lambda m: m["schema"]["constraints"].pop(),
                     lambda m: m["portfolio_authority"]["functions"].pop(),
                     lambda m: m["management_state"].__setitem__("invalid", 1),
                     lambda m: m["identity_state"].pop(),
                     lambda m: m["tables"].pop("portfolio_creations"),
                     lambda m: m["management_state"].__setitem__("initializations", 2),
                     lambda m: m["management_contract"].__setitem__("unsafe", 1)]
        for mutate in mutations:
            damaged = copy.deepcopy(value)
            mutate(damaged)
            with self.assertRaises(ValueError):
                producer.validate_manifest(damaged)

    def test_source_inventory_tampering_is_rejected(self):
        inventory = producer.portfolio_payload_inventory(ROOT)
        producer.validate_payload_inventory(inventory, ROOT)
        for field, replacement in (("version", 1), ("revision", "0017")):
            changed = copy.deepcopy(inventory)
            changed[field] = replacement
            with self.assertRaises(ValueError):
                producer.validate_payload_inventory(changed, ROOT)
        for name in inventory["sha256"]:
            changed = copy.deepcopy(inventory)
            changed["sha256"][name] = "0" * 64
            with self.subTest(name=name), self.assertRaises(ValueError):
                producer.validate_payload_inventory(changed, ROOT)


if __name__ == "__main__":
    unittest.main()
