#!/usr/bin/env python3
"""Offline exact0017 producer/consumer contracts; no provider operations."""

import copy
import hashlib
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "deploy" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PortfolioRecoveryContracts(unittest.TestCase):
    def test_final_columns_have_complete_owned_lineage_and_global_marker(self):
        producer = load("backup-snapshot")
        columns = producer.contract_columns("0017")
        self.assertEqual(len(columns), 27)
        self.assertEqual(columns["portfolio_stock_closures"], {
            "id", "portfolio_id", "user_id", "coin_id", "closed_at", "closing_sequence", "unit_epoch"
        })
        for table in ("holdings", "trades", "stock_fill_facts", "stock_ownership_movements",
                      "stock_dividend_entitlements", "stock_dividend_payments", "stock_dividend_decisions"):
            self.assertIn("portfolio_id", columns[table])
        self.assertTrue({"name", "closed_at"} <= columns["accounts"])
        self.assertIn("owner_digest_version", columns["stock_split_applications"])
        self.assertNotIn("portfolio_id", columns["stock_split_applications"])
        self.assertNotIn("user_id", columns["stock_split_applications"])

    def test_stages_refuse_explicitly(self):
        producer = load("backup-snapshot")
        for revision in ("0015", "0016"):
            for function in (producer.contract_columns, producer.manifest_sql, producer.schema_guard_sql):
                with self.assertRaisesRegex(ValueError, "migration_only"):
                    function(revision)

    def test_legacy_manifest_queries_remain_byte_exact(self):
        producer = load("backup-snapshot")
        hashes = {
            "0008": "52753d97387ec491c6494d327a6037d847cdc323bafb571c2dac6bdb0d28b5a5",
            "0011": "a4917389531c8ded7ba4e080a529490661ffdee1d3058d44efd428aa2004c72d",
            "0012": "d8ae9ab6d6d307c4b6a37b9871aa0462c6cf593a485d184f6d505ec1f93eba46",
            "0013": "2306b52d3f9f5a6bfafa60b2d475390e4ce4d7d03d2bf162e44ce338d9d72734",
        }
        for revision, expected in hashes.items():
            self.assertEqual(hashlib.sha256(producer.manifest_sql(revision).encode()).hexdigest(), expected)

    def fixture(self):
        import json
        return json.loads((ROOT / 'deploy/tests/fixtures/portfolio-recovery-0017.json').read_text())

    def test_independent_final_catalogue_and_identity_inventory(self):
        producer = load('backup-snapshot')
        manifest = self.fixture()
        producer.validate_manifest(manifest)
        self.assertEqual(len(manifest['schema']['relations']), 27)
        self.assertEqual(sum(r[2] == 'f' for r in manifest['schema']['constraints']), 65)
        self.assertEqual(len(manifest['portfolio_authority']['functions']), 10)
        self.assertEqual(len(producer.identity_tables('0017')), 20)
        expected = {'check_portfolio_financial_write()', 'lock_stock_portfolio_roots(bigint)',
                    'check_stock_split_digest_version()'}
        self.assertTrue(expected <= {r['signature'] for r in manifest['portfolio_authority']['functions']})

    def test_every_owned_projection_and_terminal_boundary_is_archived(self):
        producer = load('backup-snapshot')
        query = producer.manifest_sql('0017')
        for table in producer.PORTFOLIO_OWNED:
            line = next(line for line in query.splitlines() if "SELECT '"+table+"'," in line)
            self.assertIn('portfolio_id::text', line)
        for name in ('portfolio_stock_closures', 'closing_sequence', 'owner_digest_version',
                     'pg_get_functiondef', 'has_column_privilege', 'has_sequence_privilege'):
            self.assertIn(name, query)
        self.assertEqual(query.count('FROM portfolio_stock_closures_id_seq'), 1)

    def test_mutated_schema_marker_constraints_and_authority_fail_independently(self):
        producer = load('backup-snapshot')
        original = self.fixture()
        mutations = []
        for index, row in enumerate(original['schema']['columns']):
            if row[:2] == ['stock_split_applications','owner_digest_version']:
                for column, value in ((2,'integer'),(3,'NO'),(4,'2')):
                    mutations.append(lambda m,i=index,c=column,v=value:m['schema']['columns'][i].__setitem__(c,v))
        mutations += [lambda m:m['schema']['identities'].pop(),
            lambda m:m['schema']['constraints'].pop(),
            lambda m:m['schema']['indexes'].pop(),
            lambda m:m['schema']['relations'].append(['unreviewed','r']),
            lambda m:m['portfolio_authority']['functions'].pop(),
            lambda m:m['portfolio_authority']['functions'][0].__setitem__('definition','SELECT true'),
            lambda m:m['portfolio_authority']['functions'][0].__setitem__('owner','birja_app'),
            lambda m:m['portfolio_authority']['functions'][0].__setitem__('acl',[['PUBLIC','EXECUTE',False]]),
            lambda m:m['portfolio_authority']['functions'].append(copy.deepcopy(m['portfolio_authority']['functions'][0])),
            lambda m:m['portfolio_authority']['triggers'].pop(),
            lambda m:m['portfolio_authority']['tables'][0].__setitem__(4,True),
            lambda m:m['portfolio_authority']['columns'][0].__setitem__(5,True),
            lambda m:m['portfolio_authority']['roles'][0].__setitem__(2,True),
            lambda m:m['portfolio_state'].__setitem__('invalid',1),
            lambda m:m['portfolio_state'].__setitem__('closed',1),
            lambda m:m['portfolio_state'].__setitem__('v2_markers',1),
            lambda m:m['identity_state'].pop()]
        for mutation in mutations:
            candidate = copy.deepcopy(original)
            mutation(candidate)
            with self.assertRaises(ValueError):
                producer.validate_manifest(candidate)


if __name__ == "__main__":
    unittest.main()
