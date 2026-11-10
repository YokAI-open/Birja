#!/usr/bin/env python3
"""Offline revision dispatch contracts; real PostgreSQL proof belongs to 07-04."""

import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]


def load(name):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "deploy" / (name + ".py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RevisionContracts(unittest.TestCase):
    def test_legacy_sql_bytes_and_all_new_fields(self):
        producer = load("backup-snapshot")
        legacy = producer.manifest_sql("0008")
        self.assertEqual(
            hashlib.sha256(legacy.encode()).hexdigest(),
            "52753d97387ec491c6494d327a6037d847cdc323bafb571c2dac6bdb0d28b5a5",
        )
        self.assertEqual(producer.manifest_sql("0007"), legacy)
        self.assertNotIn("stock_", legacy)
        for revision in ("0009", "0010"):
            query = producer.manifest_sql(revision)
            for table, columns in producer.STOCK_COLUMNS.items():
                self.assertIn("FROM " + table, query)
                for column in columns.split():
                    self.assertIn(column, query)
        with self.assertRaises(ValueError):
            producer.manifest_sql("0011")

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


@unittest.skipUnless(
    "--postgres" in sys.argv, "real SQL proof explicitly uses isolated birja-test"
)
class PostgreSQLContracts(unittest.TestCase):
    @classmethod
    def query(cls, query):
        result = subprocess.run(
            [
                "docker",
                "compose",
                "--env-file",
                "/dev/null",
                "-f",
                str(ROOT / "docker-compose.test.yml"),
                "exec",
                "-T",
                "postgres",
                "psql",
                "-XqAt",
                "-v",
                "ON_ERROR_STOP=1",
                "-U",
                "birja_test",
                "-d",
                "birja_test",
            ],
            input=query.encode(),
            capture_output=True,
            timeout=30,
        )
        if result.returncode:
            raise AssertionError("isolated PostgreSQL contract query failed")
        return result.stdout.decode().strip()

    @classmethod
    def migrate(cls, revision, direction="upgrade"):
        env = {
            **os.environ,
            "ENV": "test",
            "DATABASE_URL": "postgresql+asyncpg://birja_test:test@127.0.0.1:55432/birja_test",
            "REDIS_URL": "redis://:test@127.0.0.1:56379/0",
            "OTP_HMAC_SECRET": "test-only-otp-secret-not-for-prod-000000",
            "JWT_SECRET": "test-only-jwt-secret-not-for-prod-000000",
        }
        result = subprocess.run(
            [str(ROOT / "backend/.venv/bin/alembic"), direction, revision],
            cwd=ROOT / "backend",
            env=env,
            capture_output=True,
            timeout=60,
        )
        if result.returncode:
            raise AssertionError("isolated migration failed")

    def manifest(self, revision):
        producer = load("backup-snapshot")
        manifest = json.loads(
            self.query(
                "SET TIME ZONE 'UTC';\n"
                + producer.schema_guard_sql(revision)
                + producer.manifest_sql(revision)
            )
        )
        producer.validate_manifest(manifest)
        return manifest

    def verify(self, manifest):
        restore = load("verify-restore")
        with mock.patch.object(
            restore,
            "sql",
            side_effect=lambda dc, query, db=None: self.query(query).encode(),
        ):
            restore.verify([], manifest)

    def test_all_revisions_and_stock_mutation_hashes(self):
        producer = load("backup-snapshot")
        # This suite owns only fixed, disposable birja-test and is repeatable.
        if (
            self.query("SELECT to_regclass('public.alembic_version') IS NOT NULL;")
            == "t"
        ):
            self.migrate("base", "downgrade")
        for revision in producer.SUPPORTED_REVISIONS:
            self.migrate(revision)
            baseline = self.manifest(revision)
            self.verify(baseline)
            self.assertEqual(baseline["revision"], revision)
            if revision in ("0007", "0008"):
                self.assertEqual(len(baseline["tables"]), 9)
                continue
            self.assertEqual(len(baseline["tables"]), 13)
            for mutation in ("missing", "extra", "column", "sequence", "invalid"):
                damaged = copy.deepcopy(baseline)
                if mutation == "missing":
                    del damaged["tables"]["stock_quotes"]
                elif mutation == "extra":
                    damaged["tables"]["unknown"] = {"count": 0, "sha256": "0" * 64}
                elif mutation == "column":
                    damaged["schema"]["identities"].append(
                        [
                            "stock_sessions",
                            "reviewed_at",
                            "",
                            "timestamp with time zone",
                        ]
                    )
                elif mutation == "sequence":
                    damaged["schema"]["sequences"][0][1] = "stock_quotes"
                else:
                    damaged["stock_invalid"] = 1
                with self.assertRaises(ValueError, msg=mutation):
                    producer.validate_manifest(damaged)
        self.query("""INSERT INTO stock_data_admissions(product,state,generation,reviewed_at,valid_from,valid_until,evidence_ref,terms_version,calendar) VALUES ('calendar','approved',3,'2026-01-01Z','2026-01-01Z','2026-01-02Z','https://example.invalid/calendar','fixture-v1','{"official_source":"NYSE/Nasdaq","version":"fixture-v1","review_valid_until":"2026-01-02T00:00:00Z","coverage_start":"2025-12-01","coverage_end":"2026-03-01","overrides":[{"date":"2026-01-01","closed":true,"provenance":"https://example.invalid/closure"}]}');
INSERT INTO stock_sessions(exchange,session_date,coverage_start,coverage_end,calendar_admission_generation) VALUES ('NYSE','2026-01-01','2025-12-01','2026-03-01',3);
INSERT INTO stock_quotes(coin_id,bid,ask,mid,source,feed,event_at,collected_at,session_date,admission_generation) SELECT coin_id,100.00000001,100.00000003,100.00000002,'alpaca','iex','2026-01-02T15:00Z','2026-01-02T15:00:01Z','2026-01-02',2 FROM stock_instruments ORDER BY coin_id LIMIT 1;""")
        baseline = self.manifest("0010")
        self.verify(baseline)
        for corruption in (
            "CREATE TABLE unexpected_empty()",
            "CREATE SEQUENCE unexpected_sequence",
        ):
            with self.assertRaisesRegex(
                AssertionError, "isolated PostgreSQL contract query failed"
            ):
                self.query(
                    "BEGIN; "
                    + corruption
                    + ";"
                    + producer.schema_guard_sql("0010")
                    + "ROLLBACK;"
                )
        for corruption in (
            "ALTER TABLE stock_sessions ADD reviewed_at timestamptz",
            "ALTER TABLE stock_sessions DROP CONSTRAINT ck_stock_sessions_boundaries",
            "ALTER TABLE stock_sessions DROP CONSTRAINT uq_stock_sessions_exchange_date",
            "ALTER SEQUENCE stock_sessions_id_seq INCREMENT BY 2",
            "ALTER TABLE stock_quotes ALTER bid TYPE numeric(20,7)",
            "ALTER TABLE stock_quotes DROP CONSTRAINT ck_stock_quotes_source_feed; UPDATE stock_quotes SET feed='unknown'",
        ):
            value = json.loads(
                self.query(
                    "BEGIN; SET LOCAL TIME ZONE 'UTC'; "
                    + corruption
                    + ";"
                    + producer.manifest_sql("0010")
                    + "ROLLBACK;"
                )
            )
            with self.assertRaises(ValueError):
                producer.validate_manifest(value)
        damaged = copy.deepcopy(baseline)
        damaged["tables"]["stock_sessions"]["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            self.verify(damaged)
        mutations = [
            ("coins", "sort_order=sort_order+1 WHERE asset_class='stock'"),
            ("stock_data_admissions", "state='revoked'"),
            ("stock_data_admissions", "generation=generation+1"),
            ("stock_data_admissions", "reviewed_at=reviewed_at+interval '1 second'"),
            ("stock_data_admissions", "valid_from=valid_from+interval '1 second'"),
            ("stock_data_admissions", "valid_until=valid_until+interval '1 second'"),
            ("stock_data_admissions", "evidence_ref=evidence_ref||'/updated'"),
            ("stock_data_admissions", "terms_version='fixture-v2'"),
            ("stock_data_admissions", "collection_allowed=true"),
            ("stock_data_admissions", "display_allowed=true"),
            ("stock_data_admissions", "derived_allowed=true"),
            ("stock_data_admissions", "retention_allowed=true"),
            (
                "stock_data_admissions",
                "scope='{}'::jsonb||'{\"audience\":\"friends\"}'::jsonb",
            ),
            ("stock_data_admissions", "quota='{\"limit\":200}'::jsonb"),
            ("stock_data_admissions", 'allowed_fields=\'["bid","ask"]\'::jsonb'),
            ("stock_data_admissions", "attribution='IEX prices'"),
            ("stock_sessions", "calendar_admission_generation=4"),
            ("stock_sessions", "coverage_end=coverage_end+1"),
            (
                "stock_sessions",
                "opens_at='2026-01-01T14:30Z',closes_at='2026-01-01T21:00Z'",
            ),
            (
                "stock_quotes",
                "bid=bid+0.00000002,ask=ask+0.00000002,mid=mid+0.00000002",
            ),
            ("stock_quotes", "admission_generation=4"),
            ("stock_quotes", "event_at=event_at-interval '1 second'"),
            ("stock_quotes", "collected_at=collected_at+interval '1 second'"),
            ("stock_quotes", "session_date=session_date+1"),
            (
                "stock_instruments",
                "provider_asset_id='fixture-provider-id' WHERE coin_id=(SELECT min(coin_id) FROM stock_instruments)",
            ),
            ("stock_instruments", "source_ref=source_ref||'/updated'"),
        ]
        for path in (
            "official_source",
            "version",
            "review_valid_until",
            "coverage_start",
            "coverage_end",
            "overrides,0,date",
            "overrides,0,closed",
            "overrides,0,provenance",
        ):
            mutations.append(
                (
                    "stock_data_admissions",
                    "calendar=jsonb_set(calendar,'{" + path + "}','\"changed\"')",
                )
            )
        for table, change in mutations:
            with self.subTest(table=table, change=change.split("=")[0]):
                query = (
                    "BEGIN; SET LOCAL TIME ZONE 'UTC'; UPDATE "
                    + table
                    + " SET "
                    + change
                    + ";"
                    + producer.manifest_sql("0010")
                    + "ROLLBACK;"
                )
                changed = json.loads(self.query(query))
                producer.validate_manifest(changed)
                self.assertNotEqual(
                    changed["tables"][table]["sha256"],
                    baseline["tables"][table]["sha256"],
                )
        # A stale/mismatched generation is preserved, never promoted or repaired.
        self.assertEqual(baseline["stock_invalid"], 0)
        for table in ("stock_sessions", "stock_data_admissions"):
            self.query("SELECT setval('" + table + "_id_seq',1,false);")
            with self.assertRaises(ValueError):
                self.verify(baseline)
            self.query(
                "SELECT setval('"
                + table
                + "_id_seq',(SELECT max(id) FROM "
                + table
                + "),true);"
            )
        self.query(
            "DELETE FROM stock_quotes; DELETE FROM stock_sessions; DELETE FROM stock_data_admissions;"
        )


if __name__ == "__main__":
    unittest.main(
        argv=[value for value in sys.argv if value != "--postgres"], verbosity=2
    )
