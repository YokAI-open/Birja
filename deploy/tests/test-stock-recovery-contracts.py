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

ACTION_SEED = """
BEGIN;
INSERT INTO stock_action_events(coin_id,economic_key,first_observed_at) SELECT coin_id,'11111111-1111-4111-8111-111111111111',now() FROM stock_instruments ORDER BY coin_id LIMIT 1;
INSERT INTO stock_action_sources(event_id,provider,product,provider_event_id) SELECT id,'alpaca','actions','synthetic-original' FROM stock_action_events;
INSERT INTO stock_action_revisions(event_id,source_id,ordinal,fingerprint,mutation_kind,observed_at,admission_generation,normalized_terms,classification,reason) SELECT event_id,id,1,repeat('a',64),'snapshot',now(),7,'{"cash_rate":"0.25"}','uncertain','synthetic-held' FROM stock_action_sources;
UPDATE stock_action_events SET current_revision_id=(SELECT id FROM stock_action_revisions);
INSERT INTO stock_action_sources(event_id,provider,product,provider_event_id) SELECT id,'alpaca','actions','synthetic-alias' FROM stock_action_events;
INSERT INTO stock_action_observations(event_id,source_id,revision_id,observed_at,admission_generation,source_kind,cycle_id) SELECT s.event_id,s.id,r.id,now(),7,'rest','synthetic-cycle' FROM stock_action_sources s JOIN stock_action_revisions r ON r.event_id=s.event_id;
INSERT INTO stock_action_state(coin_id,epoch,unit_epoch,sequence,health,admission_generation,cursor,staged_continuation,journal_start_at,complete_from) SELECT coin_id,3,1,2,'unknown',7,'synthetic-cursor','{"page":"pending"}',now()-interval '1 day',now() FROM stock_action_events;
INSERT INTO stock_split_applications(coin_id,economic_event_id,revision_id,new_rate,old_rate,cutoff,prior_unit_epoch,new_unit_epoch,sequence_boundary,before_digest,after_digest,processed_at) SELECT e.coin_id,e.id,r.id,'2','1',now(),0,1,1,repeat('b',64),repeat('c',64),now() FROM stock_action_events e JOIN stock_action_revisions r ON r.event_id=e.id;
INSERT INTO stock_ownership_movements(coin_id,user_id,sequence,economic_at,recorded_at,quantity,before_quantity,after_quantity,before_basis,after_basis,unit_epoch,cause_kind,causal_key) SELECT a.coin_id,u.id,1,now()-interval '1 day',now(),2,0,2,0,20,0,'opening','synthetic-opening' FROM stock_split_applications a CROSS JOIN (SELECT id FROM users ORDER BY id LIMIT 1) u;
INSERT INTO stock_ownership_movements(coin_id,user_id,sequence,economic_at,recorded_at,quantity,before_quantity,after_quantity,before_basis,after_basis,unit_epoch,cause_kind,application_id,causal_key) SELECT a.coin_id,u.id,2,now(),now(),2,2,4,20,20,1,'split',a.id,'synthetic-split' FROM stock_split_applications a CROSS JOIN (SELECT id FROM users ORDER BY id LIMIT 1) u;
INSERT INTO stock_dividend_entitlements(event_id,user_id,revision_id,cutoff,cutoff_rule,version,units_basis,unit_epoch,last_movement_sequence,eligible_quantity,state,fingerprint) SELECT e.id,u.id,r.id,now(),'synthetic-cutoff',1,'post-split',1,2,4,'held',repeat('d',64) FROM stock_action_events e JOIN stock_action_revisions r ON r.event_id=e.id CROSS JOIN (SELECT id FROM users ORDER BY id LIMIT 1) u;
INSERT INTO stock_dividend_entitlements(event_id,user_id,revision_id,cutoff,cutoff_rule,version,units_basis,unit_epoch,last_movement_sequence,eligible_quantity,state,supersedes_id,fingerprint) SELECT event_id,user_id,revision_id,cutoff,cutoff_rule,2,units_basis,unit_epoch,last_movement_sequence,eligible_quantity,'cancelled',id,repeat('e',64) FROM stock_dividend_entitlements;
INSERT INTO stock_action_resolutions(event_id,coin_id,expected_revision,admission_generation,epoch,decision,decision_key,evidence,evidence_hash,before_digest,after_digest,actor_ref,created_at) SELECT e.id,e.coin_id,r.id,7,3,'hold','synthetic-decision','{"fixture":true}',repeat('f',64),repeat('a',64),repeat('b',64),'synthetic-operator',now() FROM stock_action_events e JOIN stock_action_revisions r ON r.event_id=e.id;
COMMIT;
"""


def load(name):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "deploy" / (name + ".py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RevisionContracts(unittest.TestCase):
    def test_dividend_pregrant_structure_refuses_ambiguous_query(self):
        restore=load('verify-restore')
        producer=load('backup-snapshot')
        self.assertTrue(callable(getattr(restore,'dividend_pregrant_structure',None)))
        original=producer.manifest_sql('0014')
        fragment=producer.resolution_authority_sql()
        for query in (original.replace(fragment,'NULL'),original+fragment):
            with mock.patch.object(producer,'manifest_sql',return_value=query),mock.patch.object(restore,'recovery_contract',return_value=producer),mock.patch.object(restore,'sql') as sql:
                with self.assertRaises(ValueError):
                    restore.dividend_pregrant_structure([])
                sql.assert_not_called()

    def test_dividend_clone_authority_authenticated_before_any_grants(self):
        restore = load('verify-restore')
        self.assertTrue(callable(getattr(restore,'restore_dividend_authority',None)),
            'Clone must authenticate exact0014 authority before granting access')
        calls=[]
        def query(dc, sql, db=None):
            calls.append(sql)
            return b'{"functions":[]}'
        with mock.patch.object(restore,'sql',side_effect=query), mock.patch.object(restore,'recovery_contract',return_value=load('backup-snapshot')):
            with self.assertRaises(ValueError):
                restore.restore_dividend_authority([])
        self.assertEqual(len(calls),1)
        self.assertNotIn('GRANT', calls[0])

    def test_all_predecessor_queries_remain_byte_exact(self):
        producer=load('backup-snapshot')
        hashes={'0011':'a4917389531c8ded7ba4e080a529490661ffdee1d3058d44efd428aa2004c72d',
            '0012':'d8ae9ab6d6d307c4b6a37b9871aa0462c6cf593a485d184f6d505ec1f93eba46',
            '0013':'2306b52d3f9f5a6bfafa60b2d475390e4ce4d7d03d2bf162e44ce338d9d72734'}
        for revision,digest in hashes.items():
            self.assertEqual(hashlib.sha256(producer.manifest_sql(revision).encode()).hexdigest(),digest)

    def test_dividend_dispatch_preserves_every_original_and_nullable_decision(self):
        producer = load('backup-snapshot')
        self.assertIn('0014', producer.SUPPORTED_REVISIONS)
        columns = producer.contract_columns('0014')
        self.assertEqual(len(columns), 26)
        self.assertIn('original_amount', columns['stock_dividend_payments'])
        self.assertTrue({'previous_application_id','entitlement_fingerprint','status_identity',
            'desired_total','applied_delta'} <= columns['stock_dividend_decisions'])
        self.assertEqual(set(producer.identity_tables('0014')) - set(producer.identity_tables('0013')),
            {'stock_dividend_payments','stock_dividend_decisions'})
        query = producer.manifest_sql('0014')
        for token in ('dividend_authority','proallargtypes','proargmodes','proargnames',
                      'stock_dividend_payments','stock_dividend_decisions'):
            self.assertIn(token, query)
        self.assertNotIn('stock_dividend_payments', producer.manifest_sql('0013'))

    def test_dividend_dump_identity_contract_is_revision_selected(self):
        producer=load('backup-snapshot')
        raw='\n'.join("SELECT pg_catalog.setval('public."+table+"_id_seq', 1, false);"
            for table in producer.identity_tables('0014')).encode()
        self.assertEqual(len(producer.dump_identity_state(raw,'0014')),19)
        with self.assertRaises(ValueError):
            producer.dump_identity_state(raw,'0013')
        for table in producer.DIVIDEND_COLUMNS:
            with self.assertRaises(ValueError):
                producer.dump_identity_state(b'\n'.join(line for line in raw.splitlines() if table.encode() not in line),'0014')

    def test_dividend_authority_rejects_manifest_selected_bodies(self):
        producer=load('backup-snapshot')
        for forged in (None,{}, {'functions':[]}, {'functions':[], 'body_sha256':hashlib.sha256(b'SELECT true').hexdigest()}):
            with self.assertRaises(ValueError):
                producer.validate_dividend_authority(forged)

    def test_dump_sequence_states_are_exact_bounded_and_allowlisted(self):
        producer = load("backup-snapshot")
        rows = [f"SELECT pg_catalog.setval('public.{table}_id_seq', {index+11}, {'true' if index % 2 else 'false'});" for index,table in enumerate(producer.identity_tables("0011"))]
        raw = ("-- PostgreSQL SEQUENCE SET\n" + "\n".join(rows)).encode()
        parsed = producer.dump_identity_state(raw)
        self.assertEqual(parsed[0][1:], [11, False])
        self.assertEqual(parsed[-1][1], len(rows)+10)
        for invalid in (raw + b"\n" + rows[0].encode(), raw.replace(b"11, false", b"0, false"), b"\n".join(raw.splitlines()[:-1]), raw.replace(b"public.users_id_seq", b"public.unknown_id_seq"), raw + b"x"*65536, raw.replace(b"11, false", b"9223372036854775808, false")):
            with self.assertRaises(ValueError):
                producer.dump_identity_state(invalid)

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
            self.assertEqual(hashlib.sha256(query.encode()).hexdigest(), "30b3ab0789afa3187fdda383241dfdb115fd102471604a8bb43bf91c21e9d8c1")
            for table, columns in producer.STOCK_COLUMNS.items():
                self.assertIn("FROM " + table, query)
                for column in columns.split():
                    self.assertIn(column, query)
        with self.assertRaises(ValueError):
            producer.manifest_sql("0015")

    def test_execution_revision_is_explicit_and_preserves_predecessors(self):
        producer = load("backup-snapshot")
        # Successor support must inventory actual persisted receipt/status, not
        # silently accept an unsupported revision or reuse the older schema.
        self.assertIn("0013", producer.SUPPORTED_REVISIONS)
        columns = producer.contract_columns("0013")
        self.assertEqual(len(columns), 24)
        self.assertIn("authority", columns["stock_fill_facts"])
        self.assertIn("held_after", columns["stock_fill_facts"])
        self.assertIn("continuity_generation", columns["stock_status_evidence"])
        self.assertEqual(producer.identity_tables("0013"), producer.identity_tables("0012"))
        query = producer.manifest_sql("0013")
        for token in ("execution_authority", "pg_get_functiondef", "pg_get_triggerdef",
                      "stock_fill_facts", "stock_status_evidence"):
            self.assertIn(token, query)
        for revision in ("0011", "0012"):
            self.assertEqual(len(producer.contract_columns(revision)), 22)

    def test_execution_receipts_hash_in_unique_trade_order(self):
        producer = load("backup-snapshot")
        query = producer.manifest_sql("0013")
        # A stock can have many fills: coin_id is not a deterministic row key.
        self.assertIn("SELECT 'stock_fill_facts',trade_id,json_build_array(", query)
        self.assertNotIn("SELECT 'stock_fill_facts',coin_id,", query)

    def test_resolution_authority_has_explicit_exact_contract(self):
        producer = load("backup-snapshot")
        query = producer.manifest_sql("0012")
        self.assertIn("pg_get_functiondef", query)
        self.assertIn("resolution_authority", query)
        self.assertIn("birja_action_operator", query)
        self.assertIn("aclexplode", query)
        self.assertEqual(producer.identity_tables("0012"), producer.identity_tables("0011"))

    def test_execution_authority_refuses_forged_function_self_hash(self):
        producer = load("backup-snapshot")
        forged = {
            "functions": [["assert_stock_execution_current", "SELECT true;",
                "birja_migrator", False, ["search_path=pg_catalog, public"],
                [["birja_app", "EXECUTE", False]]]],
            "triggers": [], "runtime_acl": [], "runtime_columns": [],
            "owners": [[t,"birja_migrator"] for t in sorted(producer.EXECUTION_COLUMNS)],
        }
        for value in (forged, {**forged, "definition_sha256": hashlib.sha256(b"SELECT true;").hexdigest()},
                      None, {}):
            with self.assertRaises(ValueError):
                producer.validate_execution_authority(value)

    def test_accounting_revision_is_explicit_and_preserves_predecessors(self):
        producer = load("backup-snapshot")
        self.assertIn("0011", producer.SUPPORTED_REVISIONS)
        columns = producer.contract_columns("0011")
        self.assertEqual(len(columns), 22)
        self.assertIn("event_id", columns["stock_action_observations"])
        self.assertIn("coin_id", columns["stock_split_applications"])
        self.assertIn("unit_epoch", columns["stock_quotes"])
        query = producer.manifest_sql("0011")
        self.assertIn("identity_state", query)
        for table in producer.ACTION_COLUMNS:
            self.assertIn("FROM " + table, query)
        self.assertNotIn("stock_action_events", producer.manifest_sql("0010"))

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

    def test_fresh_restore_preprovisions_only_the_fixed_nologin_role(self):
        restore = load("verify-restore")
        contract = load("backup-snapshot")
        calls = []
        definition = "reviewed fixture definition"

        def sql(dc, query, db=restore.CLONE):
            calls.append((query, db))
            if "to_json(pg_get_functiondef" in query:
                return json.dumps(definition).encode()
            if "SELECT pg_get_userbyid" in query:
                return b"birja_migrator"
            return b"{}"

        with mock.patch.object(restore, "sql", side_effect=sql), mock.patch.object(
            restore, "recovery_contract", return_value=contract
        ), mock.patch.object(
            contract, "RESOLUTION_FUNCTION_SHA256", hashlib.sha256(definition.encode()).hexdigest()
        ), mock.patch.object(contract, "validate_resolution_authority"):
            restore.restore_resolution_authority([])
        privileged = [query for query, db in calls if db == "birja_ops_test"]
        self.assertEqual(len(privileged), 1)
        self.assertIn("CREATE ROLE birja_action_operator NOLOGIN NOINHERIT", privileged[0])
        self.assertNotIn("GRANT", privileged[0])
        self.assertTrue(all(db == restore.CLONE for query, db in calls if query not in privileged))

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
    def test_zzzz_dividend_restore_on_genuinely_fresh_cluster(self):
        """A separate cluster must not inherit source runtime/operator roles."""
        self.migrate('head')
        restore=load('verify-restore')
        producer=load('backup-snapshot')
        dump=subprocess.check_output(['docker','compose','--env-file','/dev/null','-f',
            str(ROOT/'docker-compose.test.yml'),'exec','-T','postgres','pg_dump',
            '-U','birja_test','-d','birja_test','--format=custom','--no-owner','--no-acl'])
        dc=restore.compose()
        for damage in ('none','function','schema','unsafe_runtime'):
            with self.subTest(damage=damage):
                try:
                    restore.call(dc+['up','-d','--wait'])
                    restore.check_running(dc)
                    self.assertEqual(json.loads(restore.sql(dc,
                        "SELECT json_agg(rolname ORDER BY rolname) FROM pg_roles WHERE rolname LIKE 'birja_%'",
                        'birja_ops_test')),['birja_ops_bootstrap'])
                    if damage=='unsafe_runtime':
                        restore.sql(dc,'CREATE ROLE birja_app NOLOGIN INHERIT','birja_ops_test')
                    original=restore.sql
                    def observed_sql(target,statement,db=restore.CLONE):
                        if statement=='SELECT version_num FROM public.alembic_version':
                            # Tamper after actual pg_restore, before any authority
                            # authentication or runtime/operator reconstruction.
                            if damage=='function':
                                original(target,'ALTER FUNCTION public.apply_stock_dividend(bigint,bigint,text,text) STABLE',db)
                            elif damage=='schema':
                                original(target,'ALTER TABLE stock_dividend_decisions ADD COLUMN unreviewed text',db)
                        return original(target,statement,db)
                    with mock.patch.object(restore,'sql',side_effect=observed_sql):
                        if damage=='none':
                            with restore.restored(dc,dump):
                                actual=restore.canonical(dc)
                                producer.validate_manifest(actual,quarantined=True)
                                self.assertEqual(actual['revision'],'0014')
                                for role in ('birja_app','birja_scheduler'):
                                    # The owner may SET ROLE but the target role
                                    # must have no restored financial execution.
                                    command="SET ROLE "+role+"; SELECT * FROM public.apply_stock_dividend(1,1,repeat('a',64),repeat('b',64));"
                                    result=subprocess.run(dc+['exec','-T','postgres','psql','-XqAt',
                                        '-v','ON_ERROR_STOP=1','-v','VERBOSITY=verbose','-U',restore.BOOT,
                                        '-d',restore.CLONE],input=command.encode(),capture_output=True)
                                    self.assertNotEqual(result.returncode,0)
                                    self.assertIn(b'42501',result.stderr)
                        else:
                            with self.assertRaises(ValueError):
                                with restore.restored(dc,dump):
                                    self.fail('damaged authority accepted')
                            roles=json.loads(original(dc,"SELECT coalesce(json_agg(rolname ORDER BY rolname),'[]'::json) FROM pg_roles WHERE rolname IN ('birja_app','birja_scheduler','birja_action_operator')",'birja_ops_test'))
                            self.assertEqual(roles,['birja_app'] if damage=='unsafe_runtime' else [])
                            if damage=='unsafe_runtime':
                                self.assertEqual(original(dc,"SELECT rolinherit FROM pg_roles WHERE rolname='birja_app'",'birja_ops_test').strip(),b't')
                finally:
                    restore.call(dc+['down','-v','--remove-orphans'],timeout=60)

    @classmethod
    def tearDownClass(cls):
        # Leave the owned disposable stack at the application head. Authority
        # probes below stay at their exact historical revision, not moving head.
        cls.migrate("head")

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

    def test_legacy_revisions_and_stock_mutation_hashes(self):
        producer = load("backup-snapshot")
        # This suite owns only fixed, disposable birja-test and is repeatable.
        if (
            self.query("SELECT to_regclass('public.alembic_version') IS NOT NULL;")
            == "t"
        ):
            self.migrate("base", "downgrade")
        # Accounting11 and resolution12 have separate actual SQL probes below;
        # execution13 has retained/runtime coverage in the all-lane rehearsal.
        # A moving slice silently included successor authority under the old
        # thirteen-table expectations when the supported-revision list grew.
        for revision in ("0007", "0008", "0009", "0010"):
            self.migrate(revision)
            baseline = self.manifest(revision)
            self.verify(baseline)
            self.assertEqual(baseline["revision"], revision)
            if revision in ("0007", "0008"):
                self.assertEqual(len(baseline["tables"]), 9)
                continue
            self.assertEqual(len(baseline["tables"]), 22 if revision == "0011" else 13)
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
        self.migrate("0010", "downgrade")
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

    def test_z_accounting_rows_schema_and_exact_identity_state(self):
        self.migrate("0011")
        self.query("INSERT INTO users(email) VALUES ('accounting-recovery@example.invalid') ON CONFLICT(email) DO NOTHING;")
        self.query(ACTION_SEED)
        producer = load("backup-snapshot")
        baseline = self.manifest("0011")
        self.verify(baseline)
        for table in producer.ACTION_COLUMNS:
            self.assertGreater(baseline["tables"][table]["count"], 0, table)
            damaged = copy.deepcopy(baseline)
            damaged["tables"][table]["sha256"] = "0" * 64
            with self.assertRaises(ValueError, msg=table):
                self.verify(damaged)
        for row in baseline["identity_state"]:
            damaged = copy.deepcopy(baseline)
            target = next(x for x in damaged["identity_state"] if x[0] == row[0])
            target[1] += 1
            with self.assertRaises(ValueError, msg=row[0]):
                self.verify(damaged)
        for field in ("constraints", "indexes", "columns", "identities", "sequences"):
            damaged = copy.deepcopy(baseline)
            damaged["schema"][field].pop()
            with self.assertRaises(ValueError, msg=field):
                producer.validate_manifest(damaged)
        # Held/cancelled state and continuation are durable, never normalized.
        self.assertIn("held", self.query("SELECT state FROM stock_dividend_entitlements ORDER BY id;"))
        self.query("DELETE FROM stock_action_resolutions; DELETE FROM stock_dividend_entitlements; DELETE FROM stock_ownership_movements; DELETE FROM stock_split_applications; DELETE FROM stock_action_state; DELETE FROM stock_action_observations; UPDATE stock_action_events SET current_revision_id=NULL; DELETE FROM stock_action_revisions; DELETE FROM stock_action_sources; DELETE FROM stock_action_events; DELETE FROM users WHERE email='accounting-recovery@example.invalid';")

    def test_zz_resolution_actual_operator_reads_and_outgoing_memberships(self):
        producer=load('backup-snapshot')
        # The standalone probe rebuilds empty0011/0012 role grants after
        # unrelated runtime fixtures intentionally DROP OWNED operator roles.
        self.migrate('0010','downgrade')
        self.migrate('0012')
        # Explicit synthetic ownership provision inside a rollback-only probe.
        # No runtime grants are repaired;0011/0012 supply the actual operator ACL.
        setup="""BEGIN;
DO $$ BEGIN
 IF NOT EXISTS(SELECT FROM pg_roles WHERE rolname='birja_migrator') THEN
  CREATE ROLE birja_migrator NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
 END IF;
END $$;
ALTER FUNCTION """+producer.RESOLUTION_SIGNATURE+" OWNER TO birja_migrator;\nSET LOCAL TIME ZONE 'UTC';\n"
        query=producer.manifest_sql('0012')
        raw=self.query(setup+query+";\nGRANT birja_test TO birja_action_operator;\n"+query+
            ";\nREVOKE birja_test FROM birja_action_operator;\nREVOKE SELECT ON stock_action_resolutions FROM birja_action_operator;\n"+
            query+";\nGRANT SELECT ON stock_action_resolutions TO birja_action_operator;\n"
            "GRANT UPDATE(cost_basis) ON holdings TO birja_action_operator;\n"+query+
            ";\nREVOKE UPDATE(cost_basis) ON holdings FROM birja_action_operator;\n"
            "GRANT UPDATE(reason) ON stock_action_revisions TO birja_action_operator;\n"+query+
            ";\nREVOKE UPDATE(reason) ON stock_action_revisions FROM birja_action_operator;\n"
            "GRANT SELECT(cash) ON accounts TO birja_action_operator;\n"+query+
            ";\nREVOKE SELECT(cash) ON accounts FROM birja_action_operator;\n"
            "GRANT SELECT ON stock_action_resolutions TO birja_action_operator WITH GRANT OPTION;\n"+
            query+";\nROLLBACK;")
        manifests=[json.loads(line) for line in raw.splitlines()]
        self.assertEqual(len(manifests),7)
        producer.validate_manifest(manifests[0])
        for damaged in manifests[1:]:
            with self.assertRaises(ValueError):
                producer.validate_manifest(damaged)

    def restored_owner_entry(self, *, existing_unsafe=False):
        """Use the actual restored() entry SQL against a fresh rollback role.

        Archive/database creation is deliberately outside this focused probe.
        Only the canonical role name is substituted so no existing test owner
        or owned application relation can be dropped or altered.
        """
        restore=load('verify-restore')
        producer=load('backup-snapshot')
        alias='birja_phase10_fresh_owner'
        self.assertEqual(self.query("SELECT NOT EXISTS(SELECT FROM pg_roles WHERE rolname='"+alias+"');"),'t')
        prefix=("CREATE ROLE "+alias+" LOGIN INHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;" if existing_unsafe else '')
        calls=[]
        state={}
        def query(dc,statement,db=restore.CLONE):
            calls.append(statement)
            if 'DO $$BEGIN IF NOT EXISTS' in statement and 'CREATE ROLE birja_migrator' in statement:
                self.assertNotIn('ALTER ROLE',statement)
                state['creation']=statement.replace('birja_migrator',alias)
                raw=self.query('BEGIN;'+prefix+state['creation']+"; SELECT json_build_array(rolname,rolinherit,rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls) FROM pg_roles WHERE rolname='"+alias+"'; ROLLBACK;")
                state['flags']=json.loads(raw)
                state['flags'][0]='birja_migrator'
                return b''
            if 'SELECT NOT (rolsuper' in statement:
                return self.query('BEGIN;'+prefix+state['creation']+';'+statement.replace('birja_migrator',alias)+';ROLLBACK;').encode()
            if 'SELECT NOT EXISTS(SELECT FROM pg_database' in statement:
                return b't'
            if 'SELECT version_num' in statement:
                return b'0014'
            return b''
        def pregrant(dc):
            producer.validate_dividend_role_boundary({'roles':[state['flags']],'memberships':[]},allow_missing_runtime=True)
        with mock.patch.object(restore,'call',return_value=b''),mock.patch.object(restore,'sql',side_effect=query),mock.patch.object(restore,'restore_dividend_authority',side_effect=pregrant),mock.patch.object(restore,'restore_execution_authority'),mock.patch.object(restore,'restore_resolution_authority'):
            if existing_unsafe:
                with self.assertRaises(ValueError):
                    with restore.restored([],b'synthetic-entry-probe'):
                        self.fail('unsafe owner reached restored database')
                self.assertFalse(any(statement.startswith('CREATE DATABASE') for statement in calls))
            else:
                with restore.restored([],b'synthetic-entry-probe'):
                    self.assertEqual(state['flags'],['birja_migrator',False,False,False,False,False,False])
                self.assertTrue(any(statement.startswith('CREATE DATABASE') for statement in calls))
        self.assertEqual(self.query("SELECT NOT EXISTS(SELECT FROM pg_roles WHERE rolname='"+alias+"');"),'t')

    def test_zz_fresh_restored_owner_reaches_0014_pregrant(self):
        self.restored_owner_entry()

    def test_zz_existing_unsafe_restored_owner_refused_before_database(self):
        self.restored_owner_entry(existing_unsafe=True)

    def test_zzz_dividend_exact_catalog_and_no_repair(self):
        self.migrate('head')
        producer=load('backup-snapshot')
        restore=load('verify-restore')
        # Reviewed administrative bootstrap is fixture preparation in a rollback
        # only transaction, never a repair step in the consumer under test.
        boot=(ROOT/'deploy/db/bootstrap-roles.sql').read_text().rsplit('COMMIT;',1)[0]
        for key,value in {'bootstrap':'birja_test','db_name':'birja_test',
            'app_password':'test-only-app','scheduler_password':'test-only-scheduler',
            'migrator_password':'test-only-migrator'}.items():
            boot=boot.replace(":'"+key+"'","'"+value+"'").replace(':"'+key+'"','"'+value+'"')
        boot=boot.replace('\\if :apply','\\if true')
        initial_states=None
        def capture(change='',seed=''):
            reset=''
            if initial_states is not None:
                reset='DO $reset$ BEGIN '+''.join("PERFORM setval('"+table+"_id_seq',"+str(value)+","+str(called).lower()+");" for table,value,called in initial_states)+' END $reset$;'
                self.query(reset)
            seed=seed.replace('now()',"'2026-11-01T15:00:00Z'::timestamptz")
            raw=self.query(boot+"\nSET LOCAL TIME ZONE 'UTC';\n"+seed+'\n'+change+';\n'+producer.manifest_sql('0014')+'\nROLLBACK;')
            if reset:
                self.query(reset)
            return json.loads(next(line for line in raw.splitlines() if line.startswith('{')))
        baseline=capture()
        initial_states=baseline['identity_state']
        producer.validate_manifest(baseline)
        self.assertEqual(len(baseline['tables']),26)
        self.assertEqual(len(baseline['identity_state']),19)
        # Synthetic retained storage fixtures: zero original, unknown entitlement
        # hold and separately linked applied successor. These are not a claim of
        # provider authorization or payout-function execution (proved in02/05).
        seed="INSERT INTO users(email) VALUES ('dividend-recovery@example.invalid');\n"+ACTION_SEED.replace('BEGIN;','').replace('COMMIT;','')+"""
INSERT INTO stock_dividend_payments(event_id,coin_id,user_id,revision_id,revision_fingerprint,
 entitlement_id,entitlement_fingerprint,symbol,company_name,cutoff,cutoff_rule,units_basis,
 unit_epoch,eligible_quantity,rate,ex_date,record_date,payable_date,original_amount,recorded_at,cash_after)
 SELECT e.event_id,v.coin_id,e.user_id,e.revision_id,r.fingerprint,e.id,e.fingerprint,
 'AAPL','Saved Apple',e.cutoff,e.cutoff_rule,e.units_basis,e.unit_epoch,e.eligible_quantity,0,
 '2026-11-01','2026-11-02','2026-11-03',0,now(),100 FROM stock_dividend_entitlements e
 JOIN stock_action_events v ON v.id=e.event_id JOIN stock_action_revisions r ON r.id=e.revision_id
 WHERE e.version=1;
INSERT INTO stock_dividend_decisions(payment_id,user_id,event_id,coin_id,revision_id,revision_fingerprint,
 cumulative_applied_before,applied_delta,outcome,reason,status_identity,recorded_at,cash_after,symbol,company_name)
 SELECT id,user_id,event_id,coin_id,revision_id,revision_fingerprint,0,0,'held_uncertain','terms_unverified',
 'synthetic-held',now(),100,symbol,company_name FROM stock_dividend_payments;
INSERT INTO stock_dividend_decisions(payment_id,user_id,event_id,coin_id,revision_id,revision_fingerprint,
 entitlement_id,entitlement_fingerprint,previous_decision_id,desired_total,cumulative_applied_before,
 proposed_delta,applied_delta,outcome,reason,status_identity,recorded_at,cash_after,symbol,company_name,
 cutoff,cutoff_rule,units_basis,unit_epoch,eligible_quantity,rate,ex_date,record_date,payable_date)
 SELECT p.id,p.user_id,p.event_id,p.coin_id,p.revision_id,p.revision_fingerprint,
 p.entitlement_id,p.entitlement_fingerprint,d.id,1,0,1,1,'applied','target_applied','synthetic-applied',
 now(),101,p.symbol,p.company_name,p.cutoff,p.cutoff_rule,p.units_basis,p.unit_epoch,p.eligible_quantity,
 0.25,p.ex_date,p.record_date,p.payable_date FROM stock_dividend_payments p
 JOIN stock_dividend_decisions d ON d.payment_id=p.id;
"""
        stored=capture(seed=seed)
        producer.validate_manifest(stored)
        self.assertEqual(stored['tables']['stock_dividend_payments']['count'],1)
        self.assertEqual(stored['tables']['stock_dividend_decisions']['count'],2)
        for change in [
            'ALTER TABLE stock_dividend_payments DISABLE TRIGGER stock_dividend_immutable; UPDATE stock_dividend_payments SET original_amount=0.01; ALTER TABLE stock_dividend_payments ENABLE TRIGGER stock_dividend_immutable',
            'ALTER TABLE stock_dividend_decisions DISABLE TRIGGER stock_dividend_immutable; UPDATE stock_dividend_decisions SET status_identity=status_identity||\'-changed\'; ALTER TABLE stock_dividend_decisions ENABLE TRIGGER stock_dividend_immutable',
            'ALTER TABLE stock_dividend_decisions DISABLE TRIGGER stock_dividend_immutable; UPDATE stock_dividend_decisions SET previous_decision_id=NULL; ALTER TABLE stock_dividend_decisions ENABLE TRIGGER stock_dividend_immutable',
            'ALTER TABLE stock_dividend_payments DISABLE TRIGGER stock_dividend_immutable; UPDATE stock_dividend_payments SET cash_after=999; ALTER TABLE stock_dividend_payments ENABLE TRIGGER stock_dividend_immutable',
        ]:
            changed=capture(change,seed)
            producer.validate_manifest(changed)
            with mock.patch.object(restore,'canonical',return_value=changed):
                with self.assertRaises(ValueError):
                    restore.verify([],stored,quarantined=False)
        # The genuine source data remain byte hashed and sequences exact. Every
        # original/decision column is in the independently selected row producer.
        for table in producer.DIVIDEND_COLUMNS:
            damaged=copy.deepcopy(baseline)
            damaged['tables'][table]['sha256']='0'*64
            with self.assertRaises(ValueError):
                with mock.patch.object(restore,'canonical',return_value=baseline):
                    restore.verify([],damaged,quarantined=False)
        corruptions=[
            'ALTER ROLE birja_migrator INHERIT',
            'ALTER ROLE birja_app SUPERUSER',
            'ALTER ROLE birja_scheduler CREATEROLE',
            'GRANT birja_migrator TO birja_app',
            'GRANT birja_migrator TO birja_scheduler',
            'GRANT birja_app TO birja_scheduler',
            'ALTER TABLE stock_dividend_decisions ALTER entitlement_id SET NOT NULL',
            'DROP INDEX uq_stock_dividend_decision_held_status',
            'ALTER TABLE stock_dividend_decisions DROP CONSTRAINT fk_dividend_decision_previous_owner',
            'ALTER TABLE stock_dividend_payments DISABLE TRIGGER stock_dividend_immutable',
            'ALTER SEQUENCE stock_dividend_payments_id_seq INCREMENT BY 2',
            'GRANT UPDATE(cash_after) ON stock_dividend_payments TO birja_app',
            'GRANT USAGE ON SEQUENCE stock_dividend_decisions_id_seq TO birja_scheduler',
        ]
        for name,(signature,*_) in producer.DIVIDEND_FUNCTIONS.items():
            corruptions += [
                'ALTER FUNCTION '+signature+' OWNER TO birja_test',
                'GRANT EXECUTE ON FUNCTION '+signature+' TO PUBLIC',
                'GRANT EXECUTE ON FUNCTION '+signature+' TO birja_app',
                'ALTER FUNCTION '+signature+" SET search_path='public'",
                'ALTER FUNCTION '+signature+' STABLE',
            ]
            corruptions.append("DO $tamper$ DECLARE d text; BEGIN SELECT pg_get_functiondef('"+signature+"'::regprocedure) INTO d; EXECUTE replace(d,'BEGIN',E'BEGIN\\n -- changed body'); END $tamper$")
        # Real DROP/CREATE substitutes only TABLE output type/name; prosrc and
        # input regprocedure stay byte identical, so body-only checks would pass.
        signature='public.apply_stock_dividend(bigint,bigint,text,text)'
        for old,new in [('payment_id bigint','payment_id text'),('payment_id bigint','other_id bigint')]:
            corruptions.append("DO $tamper$ DECLARE d text; BEGIN SELECT pg_get_functiondef('"+signature+"'::regprocedure) INTO d; DROP FUNCTION "+signature+"; EXECUTE replace(d,'"+old+"','"+new+"'); ALTER FUNCTION "+signature+" OWNER TO birja_migrator; GRANT EXECUTE ON FUNCTION "+signature+" TO birja_scheduler; END $tamper$")
        for change in corruptions:
            with self.subTest(change=change):
                damaged=capture(change)
                with self.assertRaises(ValueError):
                    producer.validate_manifest(damaged)
                # Pre-grant consumer must reject changed declarations/bodies/ACL
                # rather than normalizing an untrusted authority into acceptance.
                calls=[]
                def query(dc,statement,db=None):
                    calls.append(statement)
                    return json.dumps(damaged['dividend_authority']).encode()
                with mock.patch.object(restore,'sql',side_effect=query), mock.patch.object(restore,'recovery_contract',return_value=producer):
                    with self.assertRaises(ValueError):
                        restore.restore_dividend_authority([])
                self.assertEqual(len(calls),1)
        for table in producer.DIVIDEND_COLUMNS:
            row=next(row for row in baseline['identity_state'] if row[0]==table)
            damaged=capture("SELECT setval('"+table+"_id_seq',"+str(row[1]+77)+",true)")
            self.assertNotEqual(damaged['identity_state'],baseline['identity_state'])

        # Exercise the real consumer's exact statements on one rollback-only
        # PostgreSQL connection. PUBLIC EXECUTE is the actual --no-acl default;
        # no SQL financial function, grant or denial is mocked in this probe.
        command=['docker','compose','--env-file','/dev/null','-f',str(ROOT/'docker-compose.test.yml'),
            'exec','-T','postgres','psql','-XqAt','-v','ON_ERROR_STOP=1','-U','birja_test','-d','birja_test']
        with subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) as proc:
            def live(dc,statement,db=None):
                proc.stdin.write(statement+'\n;\n\\echo PHASE10_QUERY_DONE\n')
                proc.stdin.flush()
                output=[]
                while True:
                    line=proc.stdout.readline()
                    if not line:
                        raise AssertionError('isolated persistent SQL failed: '+proc.stderr.read()[-400:])
                    if line.strip()=='PHASE10_QUERY_DONE':
                        return '\n'.join(output).encode()
                    output.append(line.rstrip('\n'))
            live([],boot)
            live([],"SET LOCAL statement_timeout='30s';")
            for signature,*_ in producer.DIVIDEND_FUNCTIONS.values():
                live([],'REVOKE ALL ON FUNCTION '+signature+' FROM PUBLIC,birja_app,birja_scheduler; GRANT EXECUTE ON FUNCTION '+signature+' TO PUBLIC;')
            live([],'REVOKE ALL ON stock_dividend_payments,stock_dividend_decisions FROM PUBLIC,birja_app,birja_scheduler; REVOKE ALL ON accounts FROM birja_app,birja_scheduler;')
            # NOINHERIT does not deny SET ROLE membership. A clone must refuse
            # this noncanonical authority before making its fixed ACL changes.
            for role,grants in (
                ('birja_app', 'GRANT birja_migrator TO birja_app;'),
                ('birja_scheduler', 'GRANT birja_migrator TO birja_scheduler;'),
                ('birja_app', 'CREATE ROLE birja_phase10_recovery_link NOLOGIN NOINHERIT; GRANT birja_migrator TO birja_phase10_recovery_link; GRANT birja_phase10_recovery_link TO birja_app;'),
            ):
                live([], 'SAVEPOINT unsafe_runtime_member; '+grants)
                self.assertEqual(live([], "SELECT pg_has_role('"+role+"','birja_migrator','SET');").strip(), b't')
                with mock.patch.object(restore,'sql',side_effect=live),mock.patch.object(restore,'recovery_contract',return_value=producer):
                    with self.assertRaises(ValueError):
                        restore.restore_dividend_authority([])
                live([], 'ROLLBACK TO SAVEPOINT unsafe_runtime_member; RELEASE SAVEPOINT unsafe_runtime_member;')
            with mock.patch.object(restore,'sql',side_effect=live),mock.patch.object(restore,'recovery_contract',return_value=producer):
                restore.restore_dividend_authority([])
            for role in ('birja_app','birja_scheduler'):
                for statement in [
                    'SELECT * FROM public.apply_stock_dividend(1,1,repeat(\'a\',64),repeat(\'b\',64))',
                    'SELECT * FROM public.record_stock_dividend_hold(1,repeat(\'a\',64))',
                    'SELECT public.stock_dividend_authority(1,1,repeat(\'a\',64),repeat(\'b\',64),true,NULL)',
                    'UPDATE public.accounts SET cash=cash+1',
                    'INSERT INTO public.stock_dividend_payments DEFAULT VALUES',
                    'INSERT INTO public.stock_dividend_decisions DEFAULT VALUES',
                ]:
                    live([],'SET LOCAL ROLE '+role+'; DO $deny$ BEGIN BEGIN '+statement+'; RAISE EXCEPTION \'unexpected restored financial authority\'; EXCEPTION WHEN insufficient_privilege THEN NULL; END; END $deny$; RESET ROLE;')
            live([],'ROLLBACK;')
            proc.stdin.close()
            self.assertEqual(proc.wait(timeout=5),0)


if __name__ == "__main__":
    unittest.main(
        argv=[value for value in sys.argv if value != "--postgres"], verbosity=2
    )
