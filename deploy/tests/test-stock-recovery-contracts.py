#!/usr/bin/env python3
"""Offline revision dispatch contracts; real PostgreSQL proof belongs to 07-04."""
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "deploy" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RevisionContracts(unittest.TestCase):
    def test_unknown_revision_refused_before_manifest_sql(self):
        restore = load("verify-restore")
        calls = []

        def sql(dc, query, db):
            calls.append(query)
            if "SELECT version_num" in query:
                return b"9999\n"
            return json.dumps({"revision": "9999"}).encode()

        with mock.patch.object(restore, "sql", side_effect=sql):
            with self.assertRaises(ValueError):
                restore.canonical([])
        self.assertEqual(len(calls), 1)

    def test_old_revision_selected_before_stock_columns(self):
        restore = load("verify-restore")
        for revision in ("0007", "0008"):
            calls = []

            def sql(dc, query, db):
                calls.append(query)
                if "SELECT version_num" in query:
                    return revision.encode()
                return json.dumps({"revision": revision}).encode()

            with mock.patch.object(restore, "sql", side_effect=sql):
                self.assertEqual(restore.canonical([])["revision"], revision)
            self.assertEqual(len(calls), 2)
            self.assertNotIn("stock_quotes", calls[-1])
            self.assertNotIn("asset_class", calls[-1])


if __name__ == "__main__":
    unittest.main(verbosity=2)
