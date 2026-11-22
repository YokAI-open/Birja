#!/usr/bin/env python3
"""Private logical-backup producer (stdlib only).

No arguments selects root-owned JSON /etc/birja/backup.env (NEVER sourced).
Synthetic mode accepts only /tmp/birja-backup-test-*/config and local storage.
Required keys: CONFIG_KEYS; production additionally requires approved_host,
production_enabled, access_key_file, secret_key_file. Quota is fresh measured
account evidence, including hidden versions (B2 lifecycle cleanup lags one
day), unfinished uploads and other use. Reserves include HTTP retries,
metadata, old/new coexistence and repacking. No billing guarantee is inferred.

Routine assurance: default restic pre-upload extra verification, exact ID and
file sizes, byte-equal retrieved manifest, structural check. This does NOT
read all remote data blobs or replace initial full retrieval/restore proof.
There is no automatic repository initialization, provider setup or unlock.
"""

import argparse
import datetime as dt
import fcntl
import hashlib
import importlib.util
import json
import os
import re
import resource
import selectors
import shutil
import signal
import socket
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
DESTINATION = "s3:https://s3.eu-central-003.backblazeb2.com/Birja-backup/prod"
TAG = "birja-db-v1"
HOST = "birja-prod"
ID = re.compile(r"^[0-9a-f]{64}$")
CONFIG_KEYS = {
    "source_project",
    "state_dir",
    "restic_binary",
    "docker_binary",
    "repository",
    "password_file",
    "recovery_files",
    "release",
    "db_user",
    "db_name",
    "max_stage_bytes",
    "timeout_seconds",
    "freshness_seconds",
    "quota",
}
QUOTA_KEYS = {
    "observed_at",
    "storage_limit_bytes",
    "visible_bytes",
    "hidden_bytes",
    "unfinished_bytes",
    "other_bytes",
    "upload_reserve_bytes",
    "repack_reserve_bytes",
    "download_remaining_bytes",
    "request_remaining",
    "request_reserve",
    "free_controls_verified",
    "dedicated_repository",
}


def require(value):
    if not value:
        raise ValueError("guard")


SUPPORTED_REVISIONS = ("0007", "0008", "0009", "0010", "0011", "0012", "0013", "0014", "0017", "0020", "0023")
CLOSURE_COLUMNS = {
    'portfolio_lifecycle_closures': 'id portfolio_id user_id closed_at policy_version provenance confirmation_name intent_id',
    'portfolio_closure_intents': 'id user_id portfolio_id intent_key confirmation_name policy_version outcome recorded_at',
}
MANAGEMENT_COLUMNS = {
    'portfolio_creations': 'id user_id creation_key portfolio_id origin payload_version canonical_payload amount created_at',
    'portfolio_initializations': 'id user_id origin portfolio_id creation_id created_at',
}
# V1 is the original exact inventory. V2 extends it; no historical payload is
# interpreted as V2 merely because the running application has changed.
PORTFOLIO_PAYLOAD_V1 = [
    'backend/alembic/versions/0015_portfolio_expansion.py',
    'backend/alembic/versions/0016_portfolio_association.py',
    'backend/alembic/versions/0017_portfolio_ownership.py',
    'backend/alembic/sql/0017_dividend_portfolio.sql',
    'backend/alembic/sql/0017_stock_portfolio.sql',
    'backend/app/db/portfolio_bootstrap.py', 'backend/app/db/portfolio_migrate.py',
    'backend/app/db/dev_bootstrap.py', 'deploy/tests/portfolio-execution-fixture.py',
    'deploy/tests/portfolio-smoke.py', 'deploy/tests/portfolio-sources.py',
    'deploy/tests/portfolio-retained-sources.json', 'deploy/tests/run-portfolio-validation.py',
    'deploy/tests/ops-fixtures.py', 'deploy/tests/selected-cutover.py',
    'deploy/tests/test-rollback-db-security.sh',
]
PORTFOLIO_PAYLOAD_V2 = PORTFOLIO_PAYLOAD_V1 + [
    'backend/alembic/versions/0018_portfolio_management_expansion.py',
    'backend/alembic/versions/0019_portfolio_management_backfill.py',
    'backend/alembic/versions/0020_portfolio_management_authority.py',
    'backend/alembic/sql/0019_portfolio_metadata.sql',
    'backend/alembic/sql/0020_portfolio_management.sql',
    'backend/app/models/user.py', 'backend/app/models/portfolio_creation.py',
    'backend/app/db/schema_contract.py', 'backend/app/services/accounts.py',
    'deploy/db/bootstrap-roles.sql',
    'deploy/tests/portfolio-management-recovery-fixture.py',
    'deploy/tests/fixtures/portfolio-recovery-0020.json',
]
PORTFOLIO_PAYLOAD_V3 = PORTFOLIO_PAYLOAD_V2 + [
    'backend/alembic/versions/0021_portfolio_closure_schema.py',
    'backend/alembic/versions/0022_portfolio_closure_provenance.py',
    'backend/alembic/versions/0023_portfolio_closure_authority.py',
    'backend/alembic/sql/0023_portfolio_closure.sql',
    'backend/app/models/portfolio_lifecycle.py',
    'backend/app/models/__init__.py',
    'backend/app/models/corporate_action.py',
    'backend/app/services/portfolio_closure.py',
    'backend/app/services/stock_ownership.py',
    'backend/app/services/corporate_actions.py',
    'deploy/tests/portfolio-closure-recovery-fixture.py',
    'deploy/tests/fixtures/portfolio-recovery-0023.json',
]


def portfolio_payload_inventory(root):
    root = Path(root).resolve(strict=True)
    hashes = {}
    for name in PORTFOLIO_PAYLOAD_V2:
        path = root / name
        require(path.is_file() and not path.is_symlink() and path.resolve() == path)
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {'version': 2, 'revision': '0020', 'sha256': hashes}


def closure_payload_inventory(root):
    root = Path(root).resolve(strict=True)
    require_closure_source(root)
    hashes = {}
    for name in PORTFOLIO_PAYLOAD_V3:
        path = root / name
        require(path.is_file() and not path.is_symlink() and path.resolve() == path)
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {'version': 3, 'revision': '0023', 'sha256': hashes}


def verify_closure_inventory(root, inventory):
    require(type(inventory.get('version')) is int and inventory['version'] == 3)
    require(inventory == closure_payload_inventory(root))


def validate_payload_inventory(inventory, root):
    require(inventory == portfolio_payload_inventory(root))
BASE_COLUMNS = {
    "users": "id email created_at",
    "accounts": "id user_id cash starting_cash created_at",
    "auth_sessions": "id user_id created_at revoked_at",
    "refresh_tokens": "id session_id token_hash expires_at used_at created_at",
    "coins": "id symbol name kraken_pair sort_order is_active",
    "prices": "coin_id mid as_of source",
    "holdings": "id user_id coin_id quantity cost_basis",
    "trades": "id user_id coin_id side input_kind input_value quantity mid_price price_as_of exec_price fee cash_delta cash_after idempotency_key created_at",
    "alembic_version": "version_num",
}
STOCK_COLUMNS = {
    "stock_instruments": "coin_id provider_asset_id provider_verified_at listing_exchange currency security_type source source_ref",
    "stock_quotes": "coin_id bid ask mid source feed event_at collected_at session_date admission_generation",
    "stock_sessions": "id exchange session_date opens_at closes_at coverage_start coverage_end calendar_admission_generation",
    "stock_data_admissions": "id product state generation reviewed_at valid_from valid_until evidence_ref terms_version collection_allowed display_allowed derived_allowed retention_allowed scope quota allowed_fields attribution calendar",
}
ACTION_COLUMNS = {
    "stock_action_events": "id coin_id economic_key current_revision_id first_observed_at",
    "stock_action_state": "coin_id epoch unit_epoch sequence health checked_at valid_until admission_generation coverage_start covered_until cursor staged_continuation journal_start_at complete_from quote_not_before next_blocking_at",
    "stock_action_sources": "id event_id provider product provider_event_id",
    "stock_action_revisions": "id event_id source_id ordinal fingerprint mutation_kind source_mutation_id source_event_at observed_at admission_generation normalized_terms classification reason verified_cutoff units calendar_provenance",
    "stock_action_observations": "id event_id source_id revision_id mutation_id observed_at admission_generation source_kind cycle_id",
    "stock_action_resolutions": "id event_id coin_id expected_revision admission_generation epoch decision decision_key evidence evidence_hash before_digest after_digest actor_ref created_at",
    "stock_dividend_entitlements": "id event_id user_id revision_id cutoff cutoff_rule version units_basis unit_epoch last_movement_sequence eligible_quantity state supersedes_id fingerprint",
    "stock_split_applications": "id coin_id economic_event_id revision_id new_rate old_rate cutoff prior_unit_epoch new_unit_epoch sequence_boundary before_digest after_digest processed_at",
    "stock_ownership_movements": "id coin_id user_id sequence economic_at recorded_at quantity before_quantity after_quantity before_basis after_basis unit_epoch cause_kind trade_id application_id causal_key",
}
EXECUTION_COLUMNS = {
    "stock_fill_facts": "trade_id coin_id user_id provider_asset_id symbol company_name listing_exchange source feed bid ask exact_mid held_after event_at collected_at observed_at session_date opens_at closes_at authority schema_version",
    "stock_status_evidence": "coin_id provider_asset_id state event_at observed_at session_date admission_generation continuity_generation sequence valid_until bootstrap_verified continuity_current source source_ref",
}
# Measured independently from reviewed0013 on the guarded PostgreSQL18 fixture.
EXECUTION_SCHEMA_SHA256 = "b90ddfa6cb8c33670f5341b8bc45ec4b71d5c7bc63172d041a4c2b12575e8196"
EXECUTION_FUNCTIONS = {
    "assert_stock_execution_current": "b3fed4dfaec09d8f6174a471796795ea5a1d324037d8412efb5954f2567f5a24",
    "check_stock_fill_integrity": "dbfbbcc20567be709b34a88f1b900ac0151c27c175444914d80344c8b1322647",
}

DIVIDEND_COLUMNS = {
    'stock_dividend_payments': 'id event_id coin_id user_id revision_id revision_fingerprint entitlement_id entitlement_fingerprint symbol company_name cutoff cutoff_rule units_basis unit_epoch eligible_quantity rate ex_date record_date payable_date original_amount recorded_at cash_after',
    'stock_dividend_decisions': 'id payment_id user_id event_id coin_id revision_id revision_fingerprint entitlement_id entitlement_fingerprint previous_decision_id previous_application_id desired_total cumulative_applied_before proposed_delta applied_delta outcome reason status_identity recorded_at cash_after symbol company_name cutoff cutoff_rule units_basis unit_epoch eligible_quantity rate ex_date record_date payable_date',
}
# Independently reviewed0014 prosrc and complete declaration identities. These
# are trusted producer constants, never hashes supplied by a retained manifest.
DIVIDEND_FUNCTIONS = {
    'apply_stock_dividend': ('public.apply_stock_dividend(bigint,bigint,text,text)', '4fa0589f573067ee7a870addce0e303a79152ee47cb7c857632104c9d5bd0507', True,
        ['bigint','bigint','text','text'], ['bigint','bigint','text','text','bigint','bigint','text'], ['i','i','i','i','t','t','t'], ['p_event','p_entitlement','p_revision','p_fingerprint','payment_id','decision_id','outcome'], 'record'),
    'record_stock_dividend_hold': ('public.record_stock_dividend_hold(bigint,text)', '68b31d48ee5036cd962770b6a0be7d29a50a3d9e8a7f709faf728344d6c6072b', True,
        ['bigint','text'], ['bigint','text','bigint','bigint','text'], ['i','i','t','t','t'], ['p_payment','p_revision','payment_id','decision_id','outcome'], 'record'),
    'reject_stock_dividend_mutation': ('public.reject_stock_dividend_mutation()', '1ed29a1005ee6925f954852f4aec69abf2f4865a3a6a0b7cab53391c4cc5c2fa', False,
        [], None, None, None, 'trigger'),
    'stock_dividend_authority': ('public.stock_dividend_authority(bigint,bigint,text,text,boolean,jsonb)', '7861fec1e2552603ad9d5b8c9d314572dee859fa0f6d2e2247812e793e121d23', False,
        ['bigint','bigint','text','text','boolean','jsonb'], None, None, ['p_event','p_entitlement','p_revision','p_fingerprint','p_verified','p_expected'], 'jsonb'),
}
DIVIDEND_SCHEMA_SHA256 = '691aaca6ec9c3e386910b55849091cdaa989345bb16f177f92dc478ccee2e247'
DIVIDEND_TRIGGERS_SHA256 = '94a79eff11bd9d0db43a2d2ad38c69cda7a6a012e42f1f8a6e9291dca72c2aef'


def dividend_authority_sql():
    names = ','.join("'" + name + "'" for name in sorted(DIVIDEND_FUNCTIONS))
    # Complete declaration identity includes OUT names/modes/types; regprocedure
    # alone authenticates only input types and cannot establish a returned tuple.
    return """json_build_object(
      'functions',(SELECT json_agg(json_build_object(
        'name',p.proname,'body',p.prosrc,'owner',pg_get_userbyid(p.proowner),
        'inputs',(SELECT coalesce(json_agg(t::regtype::text ORDER BY n),'[]'::json) FROM unnest(p.proargtypes) WITH ORDINALITY x(t,n)),
        'allargs',(SELECT json_agg(t::regtype::text ORDER BY n) FROM unnest(p.proallargtypes) WITH ORDINALITY x(t,n)),
        'modes',p.proargmodes,'names',p.proargnames,'returns',p.prorettype::regtype::text,
        'definer',p.prosecdef,'set',p.proretset,'kind',p.prokind,'parallel',p.proparallel,
        'strict',p.proisstrict,'leakproof',p.proleakproof,'defaults',p.pronargdefaults,
        'support',p.prosupport::text,'language',l.lanname,'volatility',p.provolatile,
        'configuration',p.proconfig,'acl',(SELECT coalesce(json_agg(json_build_array(
          CASE WHEN a.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END,
          a.privilege_type,a.is_grantable) ORDER BY a.grantee,a.privilege_type),'[]'::json)
          FROM aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a WHERE a.grantee<>p.proowner)) ORDER BY p.proname)
        FROM pg_proc p JOIN pg_language l ON l.oid=p.prolang WHERE p.pronamespace='public'::regnamespace
        AND p.proname IN (""" + names + """)),
      'owners',(SELECT json_agg(json_build_array(c.relname,pg_get_userbyid(c.relowner)) ORDER BY c.relname)
        FROM pg_class c WHERE c.relnamespace='public'::regnamespace AND c.relname IN
        ('stock_dividend_payments','stock_dividend_decisions','stock_dividend_payments_id_seq','stock_dividend_decisions_id_seq')),
      'roles',(SELECT json_agg(json_build_array(rolname,rolinherit,rolsuper,
        rolcreatedb,rolcreaterole,rolreplication,rolbypassrls) ORDER BY rolname)
        FROM pg_roles WHERE rolname IN ('birja_app','birja_scheduler','birja_migrator')),
      'memberships',(SELECT coalesce(json_agg(json_build_array(parent.rolname,
        member.rolname,m.admin_option,m.inherit_option,m.set_option)
        ORDER BY parent.rolname,member.rolname),'[]'::json)
        FROM pg_auth_members m JOIN pg_roles parent ON parent.oid=m.roleid
        JOIN pg_roles member ON member.oid=m.member WHERE parent.rolname IN
        ('birja_app','birja_scheduler','birja_migrator') OR member.rolname IN
        ('birja_app','birja_scheduler','birja_migrator')),
      'runtime_acl',(SELECT json_agg(json_build_array(r.rolname,c.relname,
        has_table_privilege(r.oid,c.oid,'SELECT'),has_table_privilege(r.oid,c.oid,'INSERT'),
        has_table_privilege(r.oid,c.oid,'UPDATE'),has_table_privilege(r.oid,c.oid,'DELETE'),
        has_table_privilege(r.oid,c.oid,'TRUNCATE'),has_table_privilege(r.oid,c.oid,'REFERENCES'),
        has_table_privilege(r.oid,c.oid,'TRIGGER'),has_table_privilege(r.oid,c.oid,'MAINTAIN')) ORDER BY r.rolname,c.relname)
        FROM pg_roles r CROSS JOIN pg_class c WHERE r.rolname IN ('birja_app','birja_scheduler')
        AND c.relnamespace='public'::regnamespace AND c.relname IN ('stock_dividend_decisions','stock_dividend_payments')),
      'runtime_columns',(SELECT json_agg(json_build_array(r.rolname,c.relname,a.attname,
        has_column_privilege(r.oid,c.oid,a.attnum,'SELECT'),has_column_privilege(r.oid,c.oid,a.attnum,'INSERT'),
        has_column_privilege(r.oid,c.oid,a.attnum,'UPDATE'),has_column_privilege(r.oid,c.oid,a.attnum,'REFERENCES'))
        ORDER BY r.rolname,c.relname,a.attname) FROM pg_roles r CROSS JOIN pg_class c JOIN pg_attribute a ON a.attrelid=c.oid
        AND a.attnum>0 AND NOT a.attisdropped WHERE r.rolname IN ('birja_app','birja_scheduler')
        AND c.relnamespace='public'::regnamespace AND c.relname IN ('stock_dividend_decisions','stock_dividend_payments')),
      'sequence_acl',(SELECT json_agg(json_build_array(r.rolname,c.relname,
        has_sequence_privilege(r.oid,c.oid,'USAGE'),has_sequence_privilege(r.oid,c.oid,'SELECT'),
        has_sequence_privilege(r.oid,c.oid,'UPDATE')) ORDER BY r.rolname,c.relname)
        FROM pg_roles r CROSS JOIN pg_class c WHERE r.rolname IN ('birja_app','birja_scheduler')
        AND c.relnamespace='public'::regnamespace AND c.relname IN ('stock_dividend_decisions_id_seq','stock_dividend_payments_id_seq')))
    """


def validate_dividend_functions(functions, *, acl_mode='source'):
    require(acl_mode in ('source','quarantined','no_acl'))
    require(isinstance(functions,list) and len(functions)==len(DIVIDEND_FUNCTIONS))
    for row,name in zip(functions,sorted(DIVIDEND_FUNCTIONS),strict=True):
        signature,body,definer,inputs,allargs,modes,names,returns=DIVIDEND_FUNCTIONS[name]
        expected=dict(name=name,owner='birja_migrator',inputs=inputs,allargs=allargs,modes=modes,
            names=names,returns=returns,definer=definer,set=definer,kind='f',parallel='u',
            strict=False,leakproof=False,defaults=0,support='-',language='plpgsql',volatility='v',
            configuration=['search_path=pg_catalog, public, pg_temp'])
        expected['acl']=([['PUBLIC','EXECUTE',False]] if acl_mode=='no_acl' else
            [['birja_scheduler','EXECUTE',False]] if definer and acl_mode=='source' else [])
        require(isinstance(row,dict) and set(row)==set(expected)|{'body'})
        require(isinstance(row['body'],str) and hashlib.sha256(row['body'].encode()).hexdigest()==body)
        require({k:v for k,v in row.items() if k!='body'}==expected)


def validate_dividend_role_boundary(authority, *, allow_missing_runtime=False):
    # LOGIN intentionally differs between production and a quarantined clone;
    # privilege flags and isolation must not. Any first membership edge into or
    # out of a canonical role also rejects transitive SET ROLE escape paths.
    expected=[[name,*([False]*6)] for name in ('birja_app','birja_migrator','birja_scheduler')]
    roles=authority.get('roles')
    require(isinstance(roles,list) and authority.get('memberships')==[])
    if allow_missing_runtime:
        require(['birja_migrator',*([False]*6)] in roles)
        require(roles==[row for row in expected if row in roles])
    else:
        require(roles==expected)


def validate_dividend_authority(authority, *, quarantined=False):
    require(isinstance(authority,dict) and set(authority)=={'functions','owners','roles','memberships','runtime_acl','runtime_columns','sequence_acl'})
    validate_dividend_functions(authority['functions'],acl_mode='quarantined' if quarantined else 'source')
    validate_dividend_role_boundary(authority)
    require(authority['owners']==[[name,'birja_migrator'] for name in sorted([*DIVIDEND_COLUMNS,*[t+'_id_seq' for t in DIVIDEND_COLUMNS]])])
    require(authority['runtime_acl']==[[role,table,True,*([False]*7)] for role in ('birja_app','birja_scheduler') for table in sorted(DIVIDEND_COLUMNS)])
    require(authority['runtime_columns']==[[role,table,column,True,False,False,False] for role in ('birja_app','birja_scheduler') for table in sorted(DIVIDEND_COLUMNS) for column in sorted(DIVIDEND_COLUMNS[table].split())])
    require(authority['sequence_acl']==[[role,table+'_id_seq',False,False,False] for role in ('birja_app','birja_scheduler') for table in sorted(DIVIDEND_COLUMNS)])


def execution_authority_sql():
    return """json_build_object(
      'owners',(SELECT json_agg(json_build_array(relname,pg_get_userbyid(relowner)) ORDER BY relname)
        FROM pg_class WHERE relnamespace='public'::regnamespace
        AND relname IN ('stock_fill_facts','stock_status_evidence')),
      'functions',(SELECT json_agg(json_build_array(p.proname,pg_get_functiondef(p.oid),
        pg_get_userbyid(p.proowner),p.prosecdef,p.proconfig,
        (SELECT coalesce(json_agg(json_build_array(CASE WHEN a.grantee=0 THEN 'PUBLIC'
          ELSE pg_get_userbyid(a.grantee) END,a.privilege_type,a.is_grantable)
          ORDER BY a.grantee,a.privilege_type),'[]'::json)
          FROM aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a
          WHERE a.grantee<>p.proowner)) ORDER BY p.proname)
        FROM pg_proc p WHERE p.pronamespace='public'::regnamespace
        AND p.proname IN ('assert_stock_execution_current','check_stock_fill_integrity')),
      'triggers',(SELECT json_agg(json_build_array(c.relname,t.tgname,
        pg_get_triggerdef(t.oid),t.tgenabled) ORDER BY c.relname,t.tgname)
        FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
        WHERE c.relnamespace='public'::regnamespace AND NOT t.tgisinternal),
      'runtime_acl',(SELECT json_agg(json_build_array(r.rolname,c.relname,
        has_table_privilege(r.oid,c.oid,'SELECT'),has_table_privilege(r.oid,c.oid,'INSERT'),
        has_table_privilege(r.oid,c.oid,'UPDATE'),has_table_privilege(r.oid,c.oid,'DELETE'),
        has_table_privilege(r.oid,c.oid,'TRUNCATE'),has_table_privilege(r.oid,c.oid,'REFERENCES'),
        has_table_privilege(r.oid,c.oid,'TRIGGER'),has_table_privilege(r.oid,c.oid,'MAINTAIN'))
        ORDER BY r.rolname,c.relname) FROM pg_roles r CROSS JOIN pg_class c
        WHERE r.rolname IN ('birja_app','birja_scheduler') AND c.relnamespace='public'::regnamespace
        AND c.relname IN ('stock_fill_facts','stock_status_evidence')),
      'runtime_columns',(SELECT json_agg(json_build_array(r.rolname,c.relname,a.attname,
        has_column_privilege(r.oid,c.oid,a.attnum,'SELECT'),
        has_column_privilege(r.oid,c.oid,a.attnum,'INSERT'),
        has_column_privilege(r.oid,c.oid,a.attnum,'UPDATE'),
        has_column_privilege(r.oid,c.oid,a.attnum,'REFERENCES')) ORDER BY r.rolname,c.relname,a.attname)
        FROM pg_roles r CROSS JOIN pg_class c JOIN pg_attribute a ON a.attrelid=c.oid
        AND a.attnum>0 AND NOT a.attisdropped WHERE r.rolname IN ('birja_app','birja_scheduler')
        AND c.relnamespace='public'::regnamespace
        AND c.relname IN ('stock_fill_facts','stock_status_evidence')))
    """


def validate_execution_authority(authority, revision="0013"):
    require(isinstance(authority, dict) and set(authority) == {'functions','triggers','runtime_acl','runtime_columns','owners'})
    require(authority['owners'] == [[t,'birja_migrator'] for t in sorted(EXECUTION_COLUMNS)])
    require(len(authority['functions']) == 2)
    for row, name in zip(authority['functions'], sorted(EXECUTION_FUNCTIONS), strict=True):
        require(len(row) == 6 and row[0] == name)
        require(hashlib.sha256(row[1].encode()).hexdigest() == EXECUTION_FUNCTIONS[name])
        require(row[2:5] == ['birja_migrator',False,['search_path=pg_catalog, public']])
        require(row[5] == ([['birja_app','EXECUTE',False]] if name == 'assert_stock_execution_current' else []))
    require(hashlib.sha256(json.dumps(authority['triggers'],sort_keys=True,separators=(',',':')).encode()).hexdigest() == (DIVIDEND_TRIGGERS_SHA256 if revision=="0014" else EXECUTION_TRIGGERS_SHA256))
    require(authority['runtime_acl'] == [
        ['birja_app','stock_fill_facts',True,True,False,False,False,False,False,False],
        ['birja_app','stock_status_evidence',True,False,False,False,False,False,False,False],
        ['birja_scheduler','stock_fill_facts',False,False,False,False,False,False,False,False],
        ['birja_scheduler','stock_status_evidence',True,True,True,False,False,False,False,False]])
    rights = {(row[0],row[1]):row[2:5]+[row[7]] for row in authority['runtime_acl']}
    require(authority['runtime_columns'] == [[role,table,column,*rights[role,table]]
        for role in ('birja_app','birja_scheduler') for table in sorted(EXECUTION_COLUMNS)
        for column in sorted(EXECUTION_COLUMNS[table].split())])

EXECUTION_TRIGGERS_SHA256 = "0cd07680b643109ed072bb87c88215bc97b8e85b752cceb81cc5534860043545"
# Independent migrated0011 catalogue, frozen only after Plan01 review. This
# includes exact types/defaults, causal FKs, checks and complete index definitions.
ACCOUNTING_SCHEMA_SHA256 = "93cbd850d4f13148515af53f6693937886d0716d52191ac04362a974c75f0a58"
RESOLUTION_SIGNATURE = "public.apply_stock_action_resolution(bigint,bigint,bigint,bigint,bigint,text,text,text,jsonb,text)"
# Independently captured from the reviewed0012 function in actual PostgreSQL18;
# never accept a definition merely because the manifest claims its own hash.
RESOLUTION_FUNCTION_SHA256 = "a612d7fb2f5b4f50549f4d40b01e6e83a2bfaf8a7d4ce1f77ff2df22b13b2dc1"


def resolution_authority_sql():
    return """(SELECT json_build_object(
      'definition',pg_get_functiondef(p.oid),'owner',pg_get_userbyid(p.proowner),
      'security_definer',p.prosecdef,'configuration',p.proconfig,
      'function_count',(SELECT count(*) FROM pg_proc WHERE pronamespace='public'::regnamespace),
      'execute_acl',(SELECT json_agg(json_build_array(pg_get_userbyid(a.grantee),a.privilege_type,a.is_grantable)
        ORDER BY a.grantee,a.privilege_type) FROM aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a
        WHERE a.grantee<>p.proowner),
      'operator_attributes',(SELECT json_build_array(rolcanlogin,rolinherit,rolsuper,
        rolcreatedb,rolcreaterole,rolreplication,rolbypassrls) FROM pg_roles WHERE rolname='birja_action_operator'),
      'runtime_operator_membership',EXISTS(SELECT FROM pg_roles r WHERE r.rolname IN
        ('birja_app','birja_scheduler','birja_migrator') AND pg_has_role(r.oid,'birja_action_operator','MEMBER')),
      'operator_outgoing_memberships',(SELECT coalesce(json_agg(parent.rolname ORDER BY parent.rolname),'[]'::json)
        FROM pg_auth_members membership JOIN pg_roles parent ON parent.oid=membership.roleid
        WHERE membership.member=(SELECT oid FROM pg_roles WHERE rolname='birja_action_operator')),
      'operator_table_acl',(SELECT json_agg(json_build_array(c.relname,
        has_table_privilege('birja_action_operator',c.oid,'SELECT'),
        has_table_privilege('birja_action_operator',c.oid,'INSERT'),
        has_table_privilege('birja_action_operator',c.oid,'UPDATE'),
        has_table_privilege('birja_action_operator',c.oid,'DELETE'),
        has_table_privilege('birja_action_operator',c.oid,'TRUNCATE'),
        has_table_privilege('birja_action_operator',c.oid,'REFERENCES'),
        has_table_privilege('birja_action_operator',c.oid,'TRIGGER'),
        has_table_privilege('birja_action_operator',c.oid,'MAINTAIN')) ORDER BY c.relname)
        FROM pg_class c WHERE c.relnamespace='public'::regnamespace AND c.relkind='r'
        AND has_table_privilege('birja_action_operator',c.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER,MAINTAIN')),
      'operator_sequence_rights',(SELECT coalesce(json_agg(c.relname ORDER BY c.relname),'[]'::json)
        FROM pg_class c WHERE c.relnamespace='public'::regnamespace AND c.relkind='S'
        AND CASE WHEN c.relkind='S' THEN
          has_sequence_privilege('birja_action_operator',c.oid,'USAGE,SELECT,UPDATE')
          ELSE false END),
      'operator_column_acl',(SELECT json_agg(json_build_array(c.relname,a.attname,
        has_column_privilege('birja_action_operator',c.oid,a.attnum,'SELECT'),
        has_column_privilege('birja_action_operator',c.oid,a.attnum,'INSERT'),
        has_column_privilege('birja_action_operator',c.oid,a.attnum,'UPDATE'),
        has_column_privilege('birja_action_operator',c.oid,a.attnum,'REFERENCES'),
        has_column_privilege('birja_action_operator',c.oid,a.attnum,'SELECT WITH GRANT OPTION'),
        has_column_privilege('birja_action_operator',c.oid,a.attnum,'INSERT WITH GRANT OPTION'),
        has_column_privilege('birja_action_operator',c.oid,a.attnum,'UPDATE WITH GRANT OPTION'),
        has_column_privilege('birja_action_operator',c.oid,a.attnum,'REFERENCES WITH GRANT OPTION'))
        ORDER BY c.relname,a.attname) FROM pg_class c
        JOIN pg_attribute a ON a.attrelid=c.oid AND a.attnum>0 AND NOT a.attisdropped
        WHERE c.relnamespace='public'::regnamespace AND c.relkind='r'),
      'operator_catalogue_columns',(SELECT json_agg(attname ORDER BY attname) FROM pg_attribute
        WHERE attrelid='public.coins'::regclass AND attnum>0 AND NOT attisdropped
        AND has_column_privilege('birja_action_operator',attrelid,attnum,'SELECT')))
      FROM pg_proc p WHERE p.oid=to_regprocedure('""" + RESOLUTION_SIGNATURE + "'))"


def validate_resolution_authority(authority, revision='0012'):
    require(isinstance(authority, dict) and set(authority) == {
        'definition','owner','security_definer','configuration','function_count',
        'execute_acl','operator_attributes','runtime_operator_membership','operator_catalogue_columns',
        'operator_outgoing_memberships','operator_table_acl','operator_sequence_rights',
        'operator_column_acl'})
    require(isinstance(authority['definition'], str))
    require(hashlib.sha256(authority['definition'].encode()).hexdigest() == RESOLUTION_FUNCTION_SHA256)
    require(authority['owner'] == 'birja_migrator' and authority['security_definer'] is True)
    require(authority['configuration'] == ['search_path=pg_catalog, public'])
    require(type(authority['function_count']) is int and authority['function_count'] == (7 if revision=='0014' else 3 if revision=='0013' else 1))
    require(authority['execute_acl'] == [['birja_action_operator','EXECUTE',False]])
    require(authority['operator_attributes'] == [False]*7)
    require(authority['runtime_operator_membership'] is False)
    require(authority['operator_outgoing_memberships'] == [])
    require(authority['operator_table_acl'] == [[table,True,*([False]*7)]
        for table in sorted([*ACTION_COLUMNS,*STOCK_COLUMNS])])
    require(authority['operator_sequence_rights'] == [])
    readable=set(ACTION_COLUMNS)|set(STOCK_COLUMNS)
    coin_columns={'asset_class','id','is_active','sort_order','symbol'}
    columns=contract_columns(revision)
    require(authority['operator_column_acl'] == [[table,column,
        table in readable or (table=='coins' and column in coin_columns),*([False]*7)]
        for table in sorted(columns) for column in sorted(columns[table])])
    require(authority['operator_catalogue_columns'] == ['asset_class','id','is_active','sort_order','symbol'])


def identity_tables(revision):
    if revision in ('0015', '0016', '0018', '0019', '0021', '0022'):
        raise ValueError('migration_only')
    if revision == '0023':
        return sorted([*identity_tables('0020'), *CLOSURE_COLUMNS])
    if revision == '0020':
        return sorted([*identity_tables('0017'), *MANAGEMENT_COLUMNS])
    if revision == '0017':
        return sorted([*identity_tables('0014'), 'portfolio_stock_closures'])
    names = ["users", "accounts", "auth_sessions", "refresh_tokens", "coins", "holdings", "trades"]
    if revision in ("0009", "0010", "0011", "0012", "0013", "0014"):
        names += ["stock_sessions", "stock_data_admissions"]
    if revision in ("0011", "0012", "0013", "0014"):
        names += [table for table, columns in ACTION_COLUMNS.items() if columns.startswith("id ")]
    if revision == '0014':
        names += list(DIVIDEND_COLUMNS)
    return sorted(names)


def dump_identity_state(raw, revision="0011"):
    """Parse only the allowlisted SEQUENCE SET output; never execute dump SQL.

    Sequences are not MVCC. Their actual archived values, rather than values
    read before pg_dump, are the authoritative retained identity contract.
    """
    require(isinstance(raw, bytes) and len(raw) <= 65536)
    states = {}
    for line in raw.decode("utf-8").splitlines():
        if "pg_catalog.setval(" not in line:
            continue
        match = re.fullmatch(r"SELECT pg_catalog\.setval\('public\.([a-z_]+)_id_seq', ([0-9]{1,19}), (true|false)\);", line)
        require(match is not None)
        table, value, called = match.groups()
        require(table in identity_tables(revision) and table not in states)
        require(1 <= int(value) <= 9223372036854775807)
        states[table] = [table, int(value), called == "true"]
    require(set(states) == set(identity_tables(revision)))
    return [states[table] for table in sorted(states)]


def contract_columns(revision):
    if revision in ('0015', '0016', '0018', '0019', '0021', '0022'):
        raise ValueError('migration_only')
    if revision == '0023':
        columns = contract_columns('0020')
        columns.update({table: set(value.split()) for table, value in CLOSURE_COLUMNS.items()})
        return columns
    if revision == '0020':
        columns = contract_columns('0017')
        columns['accounts'] |= {'name_key', 'description'}
        columns.update({table: set(value.split()) for table, value in MANAGEMENT_COLUMNS.items()})
        return columns
    if revision == '0017':
        columns = contract_columns('0014')
        columns['accounts'] |= {'name', 'closed_at'}
        for table in PORTFOLIO_OWNED:
            columns[table].add('portfolio_id')
        columns['stock_split_applications'].add('owner_digest_version')
        columns['portfolio_stock_closures'] = set('id portfolio_id user_id coin_id closed_at closing_sequence unit_epoch'.split())
        return columns
    require(revision in SUPPORTED_REVISIONS)
    columns = dict(BASE_COLUMNS)
    if revision in ("0009", "0010", "0011", "0012", "0013", "0014"):
        columns["coins"] += " asset_class"
        columns.update(STOCK_COLUMNS)
    if revision in ("0011", "0012", "0013", "0014"):
        columns["stock_quotes"] += " unit_epoch"
        columns.update(ACTION_COLUMNS)
    if revision in ("0013","0014"):
        columns.update(EXECUTION_COLUMNS)
    if revision == '0014':
        columns.update(DIVIDEND_COLUMNS)
    return {table: set(value.split()) for table, value in columns.items()}


def manifest_sql(revision):
    """Select only reviewed static SQL before PostgreSQL parses absent objects.

    The standalone SQL remains the byte-identical legacy query plus comments.
    All substitutions are fixed repository fragments, never operator input.
    """
    if revision == '0023':
        return closure_manifest_sql()
    contract_columns(revision)
    if revision == '0020':
        return management_manifest_sql()
    if revision == '0017':
        return portfolio_manifest_sql()
    source = (HERE / "backup-manifest.sql").read_text()
    legacy = source.split("\n/* STOCK_COINS\n", 1)[0]
    if revision in ("0007", "0008"):
        return legacy

    def fragment(name):
        return source.split("/* " + name + "\n", 1)[1].split("\n" + name + " */", 1)[0]

    old = next(line for line in legacy.splitlines() if "SELECT 'coins'," in line)
    result = legacy.replace(old, " UNION ALL" + fragment("STOCK_COINS"))
    result = result.replace(
        "), names(name) AS (", fragment("STOCK_ROWS") + "\n), names(name) AS ("
    )
    result = result.replace(
        "('alembic_version')\n",
        "('alembic_version'),"
        + ",".join("('" + t + "')" for t in STOCK_COLUMNS)
        + "\n",
    )
    result = result.replace(
        " 'schema',json_build_object(",
        " 'stock_invalid',("
        + fragment("STOCK_INVALID")
        + "),\n 'schema',json_build_object(",
    )
    result = result.replace(
        "  'constraints',",
        "  'relations',(SELECT json_agg(json_build_array(relname,relkind) ORDER BY relname) FROM pg_class WHERE relnamespace='public'::regnamespace AND relkind IN ('r','p','v','m','f')),\n"
        "  'columns',(SELECT json_agg(json_build_array(table_name,column_name,data_type,is_nullable,column_default,numeric_precision,numeric_scale) ORDER BY table_name,ordinal_position) FROM information_schema.columns WHERE table_schema='public'),\n"
        "  'sequences',(SELECT json_agg(json_build_array(s.relname,t.relname,a.attname,q.seqtypid::regtype::text,q.seqincrement,q.seqmin,q.seqmax,q.seqcache,q.seqcycle) ORDER BY s.relname) FROM pg_class s JOIN pg_sequence q ON q.seqrelid=s.oid LEFT JOIN pg_depend d ON d.objid=s.oid AND d.deptype='i' LEFT JOIN pg_class t ON t.oid=d.refobjid LEFT JOIN pg_attribute a ON a.attrelid=t.oid AND a.attnum=d.refobjsubid WHERE s.relnamespace='public'::regnamespace),\n"
        "  'constraints',",
    )
    if revision in ("0011", "0012", "0013", "0014"):
        quote = fragment("STOCK_ROWS").splitlines()[1]
        result = result.replace(quote, quote.replace("admission_generation)::text", "admission_generation,unit_epoch)::text"))
        rows = []
        timestamps = {"cutoff", "verified_cutoff", "coverage_start", "covered_until", "complete_from", "quote_not_before", "next_blocking_at"}
        for table, columns in (ACTION_COLUMNS | (EXECUTION_COLUMNS if revision in ('0013','0014') else {}) | (DIVIDEND_COLUMNS if revision=='0014' else {})).items():
            expressions = []
            for column in columns.split():
                if column.endswith("_at") or column == "valid_until" or column in timestamps:
                    expressions.append("to_char(" + column + ",'YYYY-MM-DD\"T\"HH24:MI:SS.US\"Z\"')")
                else:
                    expressions.append(column + "::text")
            key = "trade_id" if table == "stock_fill_facts" else "id" if columns.startswith("id ") else "coin_id"
            rows.append(" UNION ALL SELECT '" + table + "'," + key + ",json_build_array(" + ",".join(expressions) + ")::text FROM " + table)
        result = result.replace("\n), names(name) AS (", "\n" + "\n".join(rows) + "\n), names(name) AS (")
        result = result.replace("('stock_data_admissions')\n", "('stock_data_admissions')," + ",".join("('" + t + "')" for t in ACTION_COLUMNS) + "\n")
        if revision in ('0013','0014'):
            result = result.replace("('stock_ownership_movements')\n", "('stock_ownership_movements')," + ",".join("('" + t + "')" for t in EXECUTION_COLUMNS) + "\n")
        if revision == '0014':
            result = result.replace("('stock_status_evidence')\n", "('stock_status_evidence')," + ",".join("('" + t + "')" for t in DIVIDEND_COLUMNS) + "\n")
        sequences = " UNION ALL ".join("SELECT '" + t + "',last_value,is_called FROM " + t + "_id_seq" for t in identity_tables(revision))
        result = result.replace(" 'schema',json_build_object(", " 'identity_state',(SELECT json_agg(json_build_array(name,last_value,is_called) ORDER BY name) FROM (" + sequences + ") AS s(name,last_value,is_called)),\n 'schema',json_build_object(")
    if revision in ('0012','0013','0014'):
        result = result.replace(" 'schema',json_build_object(",
            " 'resolution_authority'," + resolution_authority_sql() + ",\n 'schema',json_build_object(")
    if revision in ('0013','0014'):
        result = result.replace(" 'schema',json_build_object(",
            " 'execution_authority'," + execution_authority_sql() + ",\n 'schema',json_build_object(")
    if revision == '0014':
        result = result.replace(" 'schema',json_build_object(",
            " 'dividend_authority'," + dividend_authority_sql() + ",\n 'schema',json_build_object(")
    return result


def schema_guard_sql(revision):
    """Bound all public tables/sequences without changing legacy hash bytes.

    SQL identifiers derive only from reviewed constants, never operator input.
    """
    tables = contract_columns(revision)
    identities = identity_tables(revision)
    table_names = ",".join("'" + t + "'" for t in sorted(tables))
    sequence_names = ",".join("'" + t + "_id_seq'" for t in sorted(identities))
    return (
        "DO $contract$ BEGIN IF ARRAY(SELECT relname::text FROM pg_class WHERE "
        "relnamespace='public'::regnamespace AND relkind IN ('r','p','v','m','f') "
        "ORDER BY relname) IS DISTINCT FROM ARRAY[" + table_names + "]::text[] OR "
        "ARRAY(SELECT relname::text FROM pg_class WHERE relnamespace='public'::regnamespace "
        "AND relkind='S' ORDER BY relname) IS DISTINCT FROM ARRAY["
        + sequence_names
        + "]::text[] "
        "THEN RAISE EXCEPTION 'unsupported recovery catalog'; END IF; END $contract$;\n"
    )


def validate_manifest(manifest, *, quarantined=False):
    """Refuse unknown/omitted shape and invalid persisted discovery state."""
    expected = contract_columns(manifest["revision"])
    require(isinstance(manifest.get('tables'), dict) and set(manifest['tables']) == set(expected))
    if manifest['revision'] == '0023':
        validate_closure_manifest(manifest, quarantined=quarantined)
    if manifest['revision'] == '0020':
        validate_management_manifest(manifest, quarantined=quarantined)
    if manifest['revision'] == '0017':
        validate_portfolio_manifest(manifest, quarantined=quarantined)
    if manifest['revision']=='0014':
        validate_dividend_authority(manifest.get('dividend_authority'),quarantined=quarantined)
    if manifest['revision'] in ('0012','0013','0014'):
        validate_resolution_authority(manifest.get('resolution_authority'),manifest['revision'])
    if manifest['revision'] in ('0013','0014'):
        validate_execution_authority(manifest.get('execution_authority'),manifest['revision'])
    require(set(manifest["tables"]) == set(expected))
    for row in manifest["tables"].values():
        require(set(row) == {"count", "sha256"})
        require(type(row["count"]) is int and row["count"] >= 0)
        require(isinstance(row["sha256"], str) and ID.fullmatch(row["sha256"]))
    actual = {}
    for table, column, identity, data_type in manifest["schema"]["identities"]:
        require(table in expected and column not in actual.setdefault(table, set()))
        actual[table].add(column)
        require(isinstance(data_type, str) and identity in ("", "a"))
    require(actual == expected)
    for key in ("negative_cash", "fractional_cents", "negative_holdings"):
        require(
            type(manifest["financial"][key]) is int and manifest["financial"][key] == 0
        )
    for key in (
        "cash",
        "starting_cash",
        "quantity",
        "cost_basis",
        "fees",
        "cash_delta",
    ):
        require(
            isinstance(manifest["financial"][key], str)
            and Decimal(manifest["financial"][key]).is_finite()
        )
    if manifest["revision"] in ("0011", "0012", "0013", "0014"):
        require(type(manifest["stock_invalid"]) is int and manifest["stock_invalid"] == 0)
        require(hashlib.sha256(json.dumps(manifest["schema"], sort_keys=True, separators=(",", ":")).encode()).hexdigest() == (DIVIDEND_SCHEMA_SHA256 if manifest['revision']=='0014' else EXECUTION_SCHEMA_SHA256 if manifest['revision']=='0013' else ACCOUNTING_SCHEMA_SHA256))
        states = manifest["identity_state"]
        require(isinstance(states, list) and len(states) == len(identity_tables(manifest["revision"])))
        require([row[0] for row in states] == identity_tables(manifest["revision"]))
        for name, value, called in states:
            require(type(value) is int and 1 <= value <= 9223372036854775807)
            require(type(called) is bool)
    if manifest["revision"] in ("0009", "0010"):
        require(
            type(manifest["stock_invalid"]) is int and manifest["stock_invalid"] == 0
        )
        require(
            manifest["schema"]["relations"]
            == [[table, "r"] for table in sorted(expected)]
        )
        identities = {
            "users",
            "accounts",
            "auth_sessions",
            "refresh_tokens",
            "coins",
            "holdings",
            "trades",
            "stock_sessions",
            "stock_data_admissions",
        }
        found = {
            table
            for table, column, identity, kind in manifest["schema"]["identities"]
            if identity == "a" and column == "id" and kind == "bigint"
        }
        require(found == identities)
        sequences = manifest["schema"]["sequences"]
        require(len(sequences) == len(identities))
        require(
            {tuple(row) for row in sequences}
            == {
                (t + "_id_seq", t, "id", "bigint", 1, 1, 9223372036854775807, 1, False)
                for t in identities
            }
        )
        columns = manifest["schema"]["columns"]
        require(len(columns) == sum(len(value) for value in expected.values()))
        for table, column, kind, nullable, default, precision, scale in columns:
            require(table in expected and column in expected[table])
            if table in STOCK_COLUMNS or (table == "coins" and column == "asset_class"):
                optional = {
                    ("stock_instruments", "provider_asset_id"),
                    ("stock_instruments", "provider_verified_at"),
                    ("stock_sessions", "opens_at"),
                    ("stock_sessions", "closes_at"),
                    *(
                        ("stock_data_admissions", c)
                        for c in (
                            "reviewed_at",
                            "valid_from",
                            "valid_until",
                            "evidence_ref",
                            "terms_version",
                        )
                    ),
                }
                require(nullable == ("YES" if (table, column) in optional else "NO"))
                expected_type = "text"
                if column in (
                    "id",
                    "coin_id",
                    "generation",
                    "admission_generation",
                    "calendar_admission_generation",
                ):
                    expected_type = "bigint"
                elif column in ("bid", "ask", "mid"):
                    expected_type = "numeric"
                    require((precision, scale) == (20, 8))
                elif column.endswith("_at") or column in ("valid_from", "valid_until"):
                    expected_type = "timestamp with time zone"
                elif column in ("session_date", "coverage_start", "coverage_end"):
                    expected_type = "date"
                elif column.endswith("_allowed"):
                    expected_type = "boolean"
                elif column in ("scope", "quota", "allowed_fields", "calendar"):
                    expected_type = "jsonb"
                require(kind == expected_type)
        constraints = manifest["schema"]["constraints"]
        require(all(row[3] is True for row in constraints))
        require(sum(row[2] == "f" for row in constraints) == 10)
        required = {
            "ck_coins_asset_class_known",
            "ck_coins_asset_kraken_mapping",
            "uq_coins_asset_class_symbol",
            "fk_stock_instruments_coin_id_coins",
            "fk_stock_quotes_coin_id_stock_instruments",
            "uq_stock_sessions_exchange_date",
            "uq_stock_data_admissions_product",
        }
        require(required <= {row[1] for row in constraints})
        checks = {
            "stock_instruments": "usd_only exchange_known common_stock_only source_length source_ref_length provider_id_length verification_identity",
            "stock_quotes": "finite_positive source_feed generation_positive spread_mid event_not_future",
            "stock_sessions": "boundaries exchange_known generation_positive coverage",
            "stock_data_admissions": "fields_bounded calendar_bounded quota_bounded scope_bounded calendar_product_only product_known approved_evidence state_known evidence_ref_length generation_positive attribution_length terms_version_length validity",
        }
        for table, suffixes in checks.items():
            require(
                {row[1] for row in constraints if row[0] == table and row[2] == "c"}
                == {"ck_" + table + "_" + suffix for suffix in suffixes.split()}
            )
        indexes = manifest["schema"]["indexes"]
        require(all(row[1] is True and row[2] is True for row in indexes))
        require(
            {row[0] for row in indexes if row[0].startswith(("pk_stock_", "uq_stock_"))}
            == {
                "pk_stock_instruments",
                "uq_stock_instruments_provider_asset_id",
                "pk_stock_quotes",
                "pk_stock_sessions",
                "uq_stock_sessions_exchange_date",
                "pk_stock_data_admissions",
                "uq_stock_data_admissions_product",
            }
        )


PORTFOLIO_OWNED = ('holdings', 'trades', 'stock_fill_facts',
    'stock_ownership_movements', 'stock_dividend_entitlements',
    'stock_dividend_payments', 'stock_dividend_decisions')
# Independently pinned from actual migration0017 and the fixed bootstrap grant
# contract. Neither the database under backup nor its manifest chooses these.
PORTFOLIO_SCHEMA_SHA256 = 'a5426b54a96f536cdf6e76dd29b897a1b51b2d8ec681d36ddced25ce24b2467e'
PORTFOLIO_AUTHORITY_SHA256 = '617fcabb4fe6d24f0cd0c306680f759f5d9dc21d970e7ed8919c8913980a9696'
PORTFOLIO_QUARANTINED_SHA256 = '7dff7b4ee651cb94592debe260bde4dd4148be3c2c977ac6324327cc23e119b6'
PORTFOLIO_NO_ACL_SHA256 = '87d1f2cd9dd78a74da974b7a5a86aaf092dc58af1b66bd53e5455c82f1e4afaa'


# Frozen reviewed0017 bootstrap grants plus retained operator read boundary.
PORTFOLIO_RESTORE_GRANTS = '\nGRANT USAGE ON SCHEMA public TO birja_app,birja_scheduler;\nGRANT SELECT,INSERT ON public.users TO birja_app;\nGRANT SELECT,INSERT,UPDATE ON public.auth_sessions,public.refresh_tokens TO birja_app;\nGRANT SELECT ON public.coins,public.prices,public.trades,public.stock_instruments,\n public.stock_quotes,public.stock_sessions,public.stock_data_admissions,\n public.stock_action_events,public.stock_action_sources,public.stock_action_revisions,\n public.stock_action_observations,public.stock_action_state,public.stock_split_applications,\n public.stock_ownership_movements,public.stock_action_resolutions,public.stock_fill_facts,\n public.stock_status_evidence TO birja_app,birja_scheduler;\nGRANT INSERT ON public.trades,public.stock_fill_facts,public.stock_ownership_movements\n TO birja_app;\nGRANT SELECT,INSERT,UPDATE ON public.prices,public.stock_quotes,public.stock_sessions,\n public.stock_action_state,public.stock_status_evidence TO birja_scheduler;\nGRANT INSERT ON public.stock_action_events,public.stock_action_sources,\n public.stock_action_revisions,public.stock_action_observations,\n public.stock_split_applications,public.stock_ownership_movements,\n public.stock_dividend_entitlements TO birja_scheduler;\nGRANT UPDATE(current_revision_id) ON public.stock_action_events TO birja_scheduler;\nGRANT USAGE ON SEQUENCE public.users_id_seq,public.accounts_id_seq,\n public.auth_sessions_id_seq,public.refresh_tokens_id_seq,public.holdings_id_seq,\n public.trades_id_seq,public.stock_ownership_movements_id_seq TO birja_app;\nGRANT USAGE ON SEQUENCE public.stock_sessions_id_seq,public.stock_action_events_id_seq,\n public.stock_action_sources_id_seq,public.stock_action_revisions_id_seq,\n public.stock_action_observations_id_seq,public.stock_split_applications_id_seq,\n public.stock_ownership_movements_id_seq,public.stock_dividend_entitlements_id_seq\n TO birja_scheduler;\nREVOKE ALL ON public.stock_dividend_payments,public.stock_dividend_decisions\n FROM PUBLIC,birja_app,birja_scheduler;\nREVOKE ALL ON SEQUENCE public.stock_dividend_payments_id_seq,\n public.stock_dividend_decisions_id_seq FROM PUBLIC,birja_app,birja_scheduler;\nREVOKE ALL ON public.accounts,public.holdings,public.portfolio_stock_closures\n FROM PUBLIC,birja_app,birja_scheduler;\nREVOKE UPDATE(id,user_id,cash,starting_cash,created_at,name,closed_at)\n ON public.accounts FROM PUBLIC,birja_app,birja_scheduler;\nREVOKE UPDATE(id,user_id,coin_id,quantity,cost_basis,portfolio_id)\n ON public.holdings FROM PUBLIC,birja_app,birja_scheduler;\nGRANT SELECT,INSERT ON public.accounts,public.holdings TO birja_app;\nGRANT UPDATE(cash) ON public.accounts TO birja_app;\nGRANT UPDATE(quantity,cost_basis) ON public.holdings TO birja_app;\nGRANT SELECT ON public.accounts,public.holdings TO birja_scheduler;\nGRANT UPDATE(quantity) ON public.holdings TO birja_scheduler;\nGRANT SELECT ON public.portfolio_stock_closures,public.alembic_version,\n public.stock_dividend_entitlements,public.stock_dividend_payments,\n public.stock_dividend_decisions TO birja_app,birja_scheduler;\nGRANT SELECT ON public.trades TO birja_scheduler;\nREVOKE ALL ON FUNCTION public.check_portfolio_financial_write(),\n public.check_stock_split_digest_version(),public.lock_stock_portfolio_roots(bigint)\n FROM PUBLIC,birja_app,birja_scheduler;\nGRANT EXECUTE ON FUNCTION public.lock_stock_portfolio_roots(bigint) TO birja_scheduler;\nGRANT EXECUTE ON FUNCTION public.assert_stock_execution_current(bigint,bigint,jsonb)\n TO birja_app;\nREVOKE ALL ON FUNCTION public.stock_dividend_authority(bigint,bigint,text,text,boolean,jsonb),\n public.reject_stock_dividend_mutation(),public.apply_stock_dividend(bigint,bigint,text,text),\n public.record_stock_dividend_hold(bigint,text) FROM PUBLIC,birja_app,birja_scheduler;\nGRANT EXECUTE ON FUNCTION public.apply_stock_dividend(bigint,bigint,text,text),\n public.record_stock_dividend_hold(bigint,text) TO birja_scheduler;\n\nGRANT USAGE ON SCHEMA public TO birja_action_operator;\nGRANT SELECT(id,symbol,asset_class,is_active,sort_order) ON public.coins TO birja_action_operator;\nGRANT SELECT ON public.stock_action_events,public.stock_action_observations,public.stock_action_resolutions,public.stock_action_revisions,public.stock_action_sources,public.stock_action_state,public.stock_data_admissions,public.stock_dividend_entitlements,public.stock_instruments,public.stock_ownership_movements,public.stock_quotes,public.stock_sessions,public.stock_split_applications TO birja_action_operator;\nREVOKE ALL ON FUNCTION public.apply_stock_action_resolution(bigint,bigint,bigint,bigint,bigint,text,text,text,jsonb,text) FROM PUBLIC;\nGRANT EXECUTE ON FUNCTION public.apply_stock_action_resolution(bigint,bigint,bigint,bigint,bigint,text,text,text,jsonb,text) TO birja_action_operator;\n'

PORTFOLIO_SIGNATURES = {
    'apply_stock_action_resolution(bigint,bigint,bigint,bigint,bigint,text,text,text,jsonb,text)',
    'apply_stock_dividend(bigint,bigint,text,text)',
    'assert_stock_execution_current(bigint,bigint,jsonb)',
    'check_portfolio_financial_write()', 'check_stock_fill_integrity()',
    'check_stock_split_digest_version()', 'lock_stock_portfolio_roots(bigint)',
    'record_stock_dividend_hold(bigint,text)', 'reject_stock_dividend_mutation()',
    'stock_dividend_authority(bigint,bigint,text,text,boolean,jsonb)',
}


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def portfolio_authority_sql():
    """Complete public routine/trigger/role/ACL inventory, including overloads."""
    return """json_build_object(
      'functions',(SELECT json_agg(json_build_object('signature',p.oid::regprocedure::text,
        'definition',pg_get_functiondef(p.oid),'owner',pg_get_userbyid(p.proowner),
        'acl',(SELECT coalesce(json_agg(json_build_array(
          CASE WHEN x.grantee=0 THEN 'PUBLIC' ELSE pg_get_userbyid(x.grantee) END,
          x.privilege_type,x.is_grantable) ORDER BY 1),'[]'::json)
          FROM aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) x WHERE x.grantee<>p.proowner))
        ORDER BY p.oid::regprocedure::text) FROM pg_proc p WHERE p.pronamespace='public'::regnamespace),
      'triggers',(SELECT json_agg(json_build_array(c.relname,t.tgname,pg_get_triggerdef(t.oid),t.tgenabled)
        ORDER BY c.relname,t.tgname) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
        WHERE c.relnamespace='public'::regnamespace AND NOT t.tgisinternal),
      'owners',(SELECT json_agg(json_build_array(c.relname,pg_get_userbyid(c.relowner)) ORDER BY c.relname)
        FROM pg_class c WHERE c.relnamespace='public'::regnamespace AND c.relkind IN ('r','S')),
      'roles',(SELECT json_agg(json_build_array(rolname,rolinherit,rolsuper,rolcreatedb,
        rolcreaterole,rolreplication,rolbypassrls) ORDER BY rolname) FROM pg_roles
        WHERE rolname IN ('birja_app','birja_scheduler','birja_migrator','birja_action_operator')),
      'memberships',(SELECT coalesce(json_agg(json_build_array(a.rolname,b.rolname,m.admin_option,m.inherit_option,m.set_option)
        ORDER BY a.rolname,b.rolname),'[]'::json) FROM pg_auth_members m JOIN pg_roles a ON a.oid=m.roleid
        JOIN pg_roles b ON b.oid=m.member WHERE a.rolname IN
        ('birja_app','birja_scheduler','birja_migrator','birja_action_operator') OR b.rolname IN
        ('birja_app','birja_scheduler','birja_migrator','birja_action_operator')),
      'tables',(SELECT json_agg(json_build_array(r.rolname,c.relname,
        has_table_privilege(r.oid,c.oid,'SELECT'),has_table_privilege(r.oid,c.oid,'INSERT'),
        has_table_privilege(r.oid,c.oid,'UPDATE'),has_table_privilege(r.oid,c.oid,'DELETE'),
        has_table_privilege(r.oid,c.oid,'TRUNCATE'),has_table_privilege(r.oid,c.oid,'REFERENCES'),
        has_table_privilege(r.oid,c.oid,'TRIGGER'),has_table_privilege(r.oid,c.oid,'MAINTAIN')) ORDER BY r.rolname,c.relname)
        FROM pg_roles r CROSS JOIN pg_class c WHERE r.rolname IN
        ('birja_app','birja_scheduler','birja_action_operator') AND c.relnamespace='public'::regnamespace AND c.relkind='r'),
      'columns',(SELECT json_agg(json_build_array(r.rolname,c.relname,a.attname,
        has_column_privilege(r.oid,c.oid,a.attnum,'SELECT'),has_column_privilege(r.oid,c.oid,a.attnum,'INSERT'),
        has_column_privilege(r.oid,c.oid,a.attnum,'UPDATE'),has_column_privilege(r.oid,c.oid,a.attnum,'REFERENCES'))
        ORDER BY r.rolname,c.relname,a.attname) FROM pg_roles r CROSS JOIN pg_class c JOIN pg_attribute a
        ON a.attrelid=c.oid AND a.attnum>0 AND NOT a.attisdropped WHERE r.rolname IN
        ('birja_app','birja_scheduler','birja_action_operator') AND c.relnamespace='public'::regnamespace AND c.relkind='r'),
      'sequences',(SELECT json_agg(json_build_array(r.rolname,c.relname,
        has_sequence_privilege(r.oid,c.oid,'USAGE'),has_sequence_privilege(r.oid,c.oid,'SELECT'),
        has_sequence_privilege(r.oid,c.oid,'UPDATE')) ORDER BY r.rolname,c.relname)
        FROM pg_roles r CROSS JOIN pg_class c WHERE r.rolname IN
        ('birja_app','birja_scheduler','birja_action_operator') AND c.relnamespace='public'::regnamespace AND c.relkind='S'),
      'schema_create',(SELECT json_agg(json_build_array(r.rolname,has_schema_privilege(r.oid,'public','CREATE')) ORDER BY r.rolname)
        FROM pg_roles r WHERE r.rolname IN ('birja_app','birja_scheduler','birja_action_operator')),
      'unsafe_acl',(SELECT count(*) FROM (
        SELECT c.relowner AS owner,x.* FROM pg_class c CROSS JOIN LATERAL
          aclexplode(coalesce(c.relacl,acldefault(CASE WHEN c.relkind='S' THEN 'S'::"char" ELSE 'r'::"char" END,c.relowner))) x
          WHERE c.relnamespace='public'::regnamespace AND c.relkind IN ('r','S')
        UNION ALL SELECT c.relowner,x.* FROM pg_class c JOIN pg_attribute a ON a.attrelid=c.oid
          CROSS JOIN LATERAL aclexplode(a.attacl) x WHERE c.relnamespace='public'::regnamespace
          AND a.attnum>0 AND NOT a.attisdropped
        ) permission LEFT JOIN pg_roles r ON r.oid=permission.grantee
        WHERE permission.grantee<>permission.owner AND NOT coalesce(r.rolsuper,false)
          AND (permission.is_grantable OR permission.grantee=0 OR r.rolname NOT IN
            ('birja_app','birja_scheduler','birja_action_operator'))))
    """


def portfolio_manifest_sql():
    query = manifest_sql('0014')
    for authority in (resolution_authority_sql(), execution_authority_sql(), dividend_authority_sql()):
        require(query.count(authority) == 1)
        query = query.replace(authority, 'NULL', 1)
    additions = {table: 'portfolio_id::text' for table in PORTFOLIO_OWNED}
    additions['accounts'] = "name,to_char(closed_at,'YYYY-MM-DD\"T\"HH24:MI:SS.US\"Z\"')"
    additions['stock_split_applications'] = 'owner_digest_version::text'
    lines = query.splitlines()
    for table, extra in additions.items():
        matches = [i for i, line in enumerate(lines) if "SELECT '"+table+"'," in line and line.endswith(' FROM '+table)]
        require(len(matches) == 1)
        i = matches[0]
        lines[i] = lines[i].replace(')::text FROM '+table, ','+extra+')::text FROM '+table)
    query = '\n'.join(lines)
    query = query.replace('\n), names(name) AS (',
        "\n UNION ALL SELECT 'portfolio_stock_closures',id,json_build_array(id,portfolio_id,user_id,coin_id,"
        "to_char(closed_at,'YYYY-MM-DD\"T\"HH24:MI:SS.US\"Z\"'),closing_sequence,unit_epoch)::text FROM portfolio_stock_closures\n), names(name) AS (")
    query = query.replace("('stock_dividend_decisions')\n", "('stock_dividend_decisions'),('portfolio_stock_closures')\n")
    query = query.replace(" 'schema',json_build_object(",
        " 'portfolio_authority',"+portfolio_authority_sql()+",\n 'portfolio_state',json_build_object("
        "'active',(SELECT count(*) FROM accounts WHERE closed_at IS NULL),"
        "'closed',(SELECT count(*) FROM accounts WHERE closed_at IS NOT NULL),"
        "'legacy_markers',(SELECT count(*) FROM stock_split_applications WHERE owner_digest_version IS NULL),"
        "'v2_markers',(SELECT count(*) FROM stock_split_applications WHERE owner_digest_version=2),"
        "'invalid',("+portfolio_invalid_sql()+")),\n 'schema',json_build_object(")
    query = query.replace("SELECT 'users',last_value,is_called FROM users_id_seq",
        "SELECT 'portfolio_stock_closures',last_value,is_called FROM portfolio_stock_closures_id_seq UNION ALL SELECT 'users',last_value,is_called FROM users_id_seq")
    return query


def portfolio_invalid_sql():
    checks = ["(SELECT count(*) FROM "+table+" r LEFT JOIN accounts a ON a.id=r.portfolio_id AND a.user_id=r.user_id WHERE a.id IS NULL)"
              for table in PORTFOLIO_OWNED]
    checks += ["(SELECT count(*) FROM portfolio_stock_closures c LEFT JOIN accounts a ON a.id=c.portfolio_id AND a.user_id=c.user_id WHERE a.id IS NULL OR a.closed_at IS DISTINCT FROM c.closed_at)",
        "(SELECT count(*) FROM stock_split_applications WHERE owner_digest_version IS NOT NULL AND owner_digest_version<>2)"]
    return '+'.join(checks)


def validate_portfolio_manifest(manifest, *, quarantined=False):
    require(canonical_hash(manifest['schema']) == PORTFOLIO_SCHEMA_SHA256)
    require(canonical_hash(manifest['portfolio_authority']) ==
            (PORTFOLIO_QUARANTINED_SHA256 if quarantined else PORTFOLIO_AUTHORITY_SHA256))
    state = manifest['portfolio_state']
    require(set(state) == {'active','closed','legacy_markers','v2_markers','invalid'})
    require(all(type(v) is int and v >= 0 for v in state.values()) and state['invalid'] == 0)
    require(state['active']+state['closed'] == manifest['tables']['accounts']['count'])
    require(state['legacy_markers']+state['v2_markers'] == manifest['tables']['stock_split_applications']['count'])
    require(manifest['stock_invalid'] == 0)
    states = manifest['identity_state']
    require(isinstance(states,list) and [row[0] for row in states] == identity_tables('0017'))
    for _,value,called in states:
        require(type(value) is int and 1 <= value <= 9223372036854775807 and type(called) is bool)


MANAGEMENT_BOOTSTRAP_SHA256 = 'b2f3326a7b19392491c7133fcc9cc34816dcf5b29360a1fc9fdd44ec68ec117c'
MANAGEMENT_SCHEMA_SHA256 = '7aa08fba535a66c8978dd19f956dc0db1c3da7c4d461f75f9d341ea1e5fe2da7'
MANAGEMENT_AUTHORITY_SHA256 = '0192d3a7222af2a91930d34b7089ef93371e849bc32f911cacc8383fd5ac5ebf'
MANAGEMENT_QUARANTINED_SHA256 = 'd6486b31f5609a6fdbeadaf4eeb7d9f0b4eaabe1de0566e646d85080a939fa26'
MANAGEMENT_QUARANTINED_ACL_SHA256 = '500ae682129bf6b3bc252d0c4f15cf41bdeed63785b17458c8d1c9ab70eb3f7c'
MANAGEMENT_NO_ACL_SHA256 = 'e88cb1971126447232f872c3b93fe18454ef58094becdcecd4d9066af44e3cfe'
MANAGEMENT_NO_ACL_PRIVILEGES_SHA256 = 'bd65d43da215a53d24b6a2a384951f57ea03efa76948d7603c953a84250b2b55'


def management_bootstrap():
    """Authenticate authority source before importing even its SQL constants."""
    path = HERE.parent / 'backend/app/db/portfolio_bootstrap.py'
    require(path.is_file() and not path.is_symlink())
    require(hashlib.sha256(path.read_bytes()).hexdigest() == MANAGEMENT_BOOTSTRAP_SHA256)
    spec = importlib.util.spec_from_file_location('authenticated_management_bootstrap', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def management_manifest_sql(*, bootstrap=None):
    bootstrap = management_bootstrap() if bootstrap is None else bootstrap
    query = portfolio_manifest_sql()
    query = '\n'.join(line.replace(')::text FROM accounts', ',name_key,description)::text FROM accounts')
                      if "SELECT 'accounts'," in line else line for line in query.splitlines())
    rows = []
    for table, columns in MANAGEMENT_COLUMNS.items():
        values = ["to_char(created_at,'YYYY-MM-DD\"T\"HH24:MI:SS.US\"Z\"')" if c == 'created_at'
                  else c + '::text' for c in columns.split()]
        rows.append(" UNION ALL SELECT '"+table+"',id,json_build_array("+','.join(values)+")::text FROM "+table)
    query = query.replace('\n), names(name) AS (', '\n'+'\n'.join(rows)+'\n), names(name) AS (')
    query = query.replace("('portfolio_stock_closures')\n", "('portfolio_stock_closures'),"+
                          ','.join("('"+name+"')" for name in MANAGEMENT_COLUMNS)+'\n')
    query = query.replace("SELECT 'users',last_value,is_called FROM users_id_seq",
                          ' UNION ALL '.join("SELECT '"+name+"',last_value,is_called FROM "+name+"_id_seq"
                                            for name in MANAGEMENT_COLUMNS)+
                          " UNION ALL SELECT 'users',last_value,is_called FROM users_id_seq")
    invalid = """
      (SELECT count(*) FROM users u LEFT JOIN portfolio_initializations i ON i.user_id=u.id WHERE i.id IS NULL)
      +(SELECT count(*) FROM portfolio_creations c LEFT JOIN accounts a ON (a.id,a.user_id)=(c.portfolio_id,c.user_id)
        WHERE a.id IS NULL OR c.amount<>10000 OR c.payload_version<>1
        OR c.canonical_payload IS DISTINCT FROM jsonb_build_object(
           'name',public.portfolio_display_name(c.canonical_payload->>'name'),
           'description',public.portfolio_description(c.canonical_payload->>'description')))
      +(SELECT count(*) FROM portfolio_initializations i LEFT JOIN portfolio_creations c
        ON (c.id,c.portfolio_id,c.user_id)=(i.creation_id,i.portfolio_id,i.user_id)
        WHERE (i.origin='initial' AND (c.id IS NULL OR c.origin<>'initial'))
           OR (i.origin='legacy' AND (i.creation_id IS NOT NULL OR i.portfolio_id IS NOT NULL)))
      +(SELECT count(*) FROM accounts WHERE name IS DISTINCT FROM public.portfolio_display_name(name)
        OR name_key IS DISTINCT FROM public.portfolio_name_key(name)
        OR description IS DISTINCT FROM public.portfolio_description(description))
      +(SELECT count(*) FROM (SELECT user_id FROM accounts WHERE closed_at IS NULL
        GROUP BY user_id HAVING count(*)>10) excessive)
    """
    unsafe = """(SELECT count(*) FROM pg_rewrite r JOIN pg_class c ON c.oid=r.ev_class
        WHERE c.relnamespace='public'::regnamespace)
      +(SELECT count(*) FROM pg_roles WHERE rolname='birja_action_operator' AND rolcanlogin)
      +(SELECT count(*) FROM pg_roles WHERE rolname IN ('birja_app','birja_scheduler')
        AND has_schema_privilege(oid,'public','CREATE'))
      +(SELECT count(*) FROM pg_database WHERE datname=current_database() AND
        pg_get_userbyid(datdba) IN ('birja_app','birja_scheduler','birja_migrator','birja_action_operator'))
      +(SELECT count(*) FROM pg_namespace WHERE nspname='public' AND
        pg_get_userbyid(nspowner) IN ('birja_app','birja_scheduler','birja_migrator','birja_action_operator'))"""
    fields = " 'management_state',json_build_object('creations',(SELECT count(*) FROM portfolio_creations)," \
             "'initializations',(SELECT count(*) FROM portfolio_initializations),'invalid',("+invalid+")),\n"
    fields += " 'management_contract',json_build_object('catalogue',("+bootstrap.CATALOGUE_SQL+")," \
              "'acl',("+bootstrap.ACL_SQL+"),'unsafe',("+unsafe+")),\n"
    return query.replace(" 'schema',json_build_object(", fields+" 'schema',json_build_object(")


def validate_management_manifest(manifest, *, quarantined=False):
    require(canonical_hash(manifest['schema']) == MANAGEMENT_SCHEMA_SHA256)
    require(canonical_hash(manifest['portfolio_authority']) ==
            (MANAGEMENT_QUARANTINED_SHA256 if quarantined else MANAGEMENT_AUTHORITY_SHA256))
    contract = manifest['management_contract']
    require(set(contract) == {'catalogue', 'acl', 'unsafe'})
    require(contract['catalogue'] == '535cacb140a3a1753b5cf27e2eadcb80bc272a9b12772defd3936a3edc6c2209')
    require(contract['acl'] == (MANAGEMENT_QUARANTINED_ACL_SHA256 if quarantined else
            '041a948470f9692628da43b35263a47bf58f4815310a0793d5eec099fa64c87e'))
    require(type(contract['unsafe']) is int and contract['unsafe'] == 0)
    state = manifest['management_state']
    require(set(state) == {'creations', 'initializations', 'invalid'})
    require(all(type(v) is int and v >= 0 for v in state.values()) and state['invalid'] == 0)
    require(state['creations'] == manifest['tables']['portfolio_creations']['count'])
    require(state['initializations'] == manifest['tables']['portfolio_initializations']['count'] == manifest['tables']['users']['count'])
    states = manifest['identity_state']
    require(isinstance(states, list) and [r[0] for r in states] == identity_tables('0020'))
    for _, value, called in states:
        require(type(value) is int and 1 <= value <= 9223372036854775807 and type(called) is bool)
    state = manifest['portfolio_state']
    require(set(state) == {'active', 'closed', 'legacy_markers', 'v2_markers', 'invalid'})
    require(all(type(v) is int and v >= 0 for v in state.values()) and state['invalid'] == 0)
    require(state['active']+state['closed'] == manifest['tables']['accounts']['count'])
    require(state['legacy_markers']+state['v2_markers'] == manifest['tables']['stock_split_applications']['count'])
    require(manifest['stock_invalid'] == 0)


# Separately versioned successor. These pins authenticate reviewed authority
# BEFORE importing executable source; V1/V2 literals above are not reinterpreted.
CLOSURE_SOURCE_SHA256 = {
    'backend/app/db/portfolio_bootstrap.py': '15d84249e11bad99c8e259c54680fdc5303e6771c63b501c71f79601ab0bc071',
    'backend/app/db/portfolio_migrate.py': 'bfc2990eca9e70993b228b7ca52ab7c47fb17610719944779ad97b94dd57cd17',
    'backend/app/db/schema_contract.py': 'c48e0aee909bad9ff263d1ccc2552b17921c9a802ba0b6f75a30fdffbbfd4542',
    'backend/app/models/portfolio_lifecycle.py': 'ffa11aeeee35f0843135808f60c412fb9e327e8a1dc672a1f86bb0d5f416951c',
    'backend/app/models/__init__.py': '6856ecbbdfe51305caf3ab0fa1061b08d9f105a6eb73beb4240510508232ae9d',
    'backend/app/models/corporate_action.py': 'ec268ad87ef8b1df2509da3513932c50a6b9f007786298694f97377a23eb8077',
    'backend/app/services/portfolio_closure.py': 'ef21a9be97efdda0989e55cede877ea624ae654f0bdc74984ea118c76703e025',
    'backend/app/services/stock_ownership.py': 'fe4a317f806998a4804abcf0dbb53e5bd891227440abaa834f8a91b391ad052d',
    'backend/app/services/corporate_actions.py': 'da69ac8e46daf54bb6751bd414248402931b4693b51ec2594ecc8a1aa2a95e2e',
    'backend/alembic/versions/0021_portfolio_closure_schema.py': '737446365d1304dc3721ced552102cde4d386b07031823eaf33967961732c81c',
    'backend/alembic/versions/0022_portfolio_closure_provenance.py': '0c3467650b7b308e7e4bb3f03f1e8f58d1f1ee8fe09c3361353a9036fea48cdb',
    'backend/alembic/versions/0023_portfolio_closure_authority.py': 'd62c175438c9b1022771df1cac6e4b9333f77a2b8c3375aa365840daa78ce8b5',
    'backend/alembic/sql/0023_portfolio_closure.sql': '59577ba16c9e9ea9740c2cb0d171b7006931bb6b1b9e5d0408c9a6f673f7c920',
    'deploy/db/bootstrap-roles.sql': 'd8010e470c14cc397f29ae86eb55c1e8918fa39751083c8fa7435a8105c58265',
    'deploy/tests/portfolio-closure-recovery-fixture.py': 'b8ecf20867f61c3dabbba6ab0e55f5db1a08f5c59c220b9c38fa59da6cc3c4d3',
    'deploy/tests/portfolio-execution-fixture.py': 'b6f0e486401116535f101f3529e648690d3c7fed6324b94c3e40a06bf5f5e42f',
}
CLOSURE_CATALOGUE_SHA256 = '59aeeee9428fac73f96143cc8afdd77e3b6a8f81b30ed37b752666579d69a66e'
CLOSURE_SCHEMA_SHA256 = '64dc79e1add352d2cb53486ff2f1cce86d40e9540ad25a980c6dc07003da7d4e'
CLOSURE_AUTHORITY_SHA256 = '62e3776654a98a62bf605355e209884b32ff1247fec463d6b923f48a76f42492'
CLOSURE_QUARANTINE_AUTHORITY_SHA256 = '19c82c874e5f6362500ca4b37df367795ffc6db3cc617502b59bd20057dee399'
CLOSURE_ACL_SHA256 = '71896f41a9310ada0af0961b78e78f5364654f1513c11bf9310c250ad545f748'
CLOSURE_EMPTY_ACL_SHA256 = '4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945'


def require_closure_source(root=None):
    root = HERE.parent if root is None else Path(root)
    for name, expected in CLOSURE_SOURCE_SHA256.items():
        path = root / name
        require(path.is_file() and not path.is_symlink() and path.resolve() == path)
        require(hashlib.sha256(path.read_bytes()).hexdigest() == expected)


def closure_bootstrap():
    require_closure_source()
    path = HERE.parent / 'backend/app/db/portfolio_bootstrap.py'
    spec = importlib.util.spec_from_file_location('authenticated_closure_bootstrap', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def closure_manifest_sql():
    bootstrap = closure_bootstrap()
    query = management_manifest_sql(bootstrap=bootstrap)
    rows = []
    for table, fields in CLOSURE_COLUMNS.items():
        values = ["to_char("+c+",'YYYY-MM-DD\"T\"HH24:MI:SS.US\"Z\"')"
                  if c in {'closed_at', 'recorded_at'} else c+'::text' for c in fields.split()]
        rows.append(" UNION ALL SELECT '"+table+"',id,json_build_array("+','.join(values)+")::text FROM "+table)
    query = query.replace('\n), names(name) AS (', '\n'+'\n'.join(rows)+'\n), names(name) AS (')
    query = query.replace("('portfolio_initializations')\n", "('portfolio_initializations'),"+
                          ','.join("('"+t+"')" for t in CLOSURE_COLUMNS)+'\n')
    query = query.replace("SELECT 'users',last_value,is_called FROM users_id_seq",
                          ' UNION ALL '.join("SELECT '"+t+"',last_value,is_called FROM "+t+'_id_seq'
                                            for t in CLOSURE_COLUMNS)+
                          " UNION ALL SELECT 'users',last_value,is_called FROM users_id_seq")
    # The same independently pinned catalogue used by runtime admission covers
    # every routine/body/owner, trigger, constraint, rule, policy and relation.
    lifecycle = bootstrap.PREFLIGHT_0023_SQL.split(' IF EXISTS(SELECT FROM public.accounts a', 1)[1]
    lifecycle = 'EXISTS(SELECT FROM public.accounts a'+lifecycle.split(" THEN RAISE EXCEPTION 'closure lifecycle evidence mismatch'",1)[0]
    fields = " 'closure_contract',json_build_object('catalogue',("+bootstrap.CATALOGUE_0023_SQL+")," \
             "'acl',("+bootstrap.ACL_SQL+"),'defaults',("+bootstrap.DEFAULT_ACL_0023_SQL+")),\n"
    fields += " 'closure_state',json_build_object('closures',(SELECT count(*) FROM portfolio_lifecycle_closures)," \
              "'intents',(SELECT count(*) FROM portfolio_closure_intents)," \
              "'refused',(SELECT count(*) FROM portfolio_closure_intents WHERE outcome='confirmation_changed')," \
              "'invalid',CASE WHEN "+lifecycle+" THEN 1 ELSE 0 END),\n"
    return query.replace(" 'schema',json_build_object(", fields+" 'schema',json_build_object(")


def validate_closure_manifest(manifest, *, quarantined=False):
    require(canonical_hash(manifest['schema']) == CLOSURE_SCHEMA_SHA256)
    require(canonical_hash(manifest['portfolio_authority']) ==
            (CLOSURE_QUARANTINE_AUTHORITY_SHA256 if quarantined else CLOSURE_AUTHORITY_SHA256))
    contract = manifest['closure_contract']
    require(set(contract) == {'catalogue', 'acl', 'defaults'})
    require(contract['catalogue'] == CLOSURE_CATALOGUE_SHA256)
    require(contract['acl'] == (CLOSURE_EMPTY_ACL_SHA256 if quarantined else CLOSURE_ACL_SHA256))
    # A no-ACL clone is still required to carry private future defaults. Restore
    # must explicitly establish those defaults before admitting the quarantine.
    require(contract['defaults'] == CLOSURE_EMPTY_ACL_SHA256)
    require(manifest['schema']['relations'] == [[t, 'r'] for t in sorted(contract_columns('0023'))])
    require(len(manifest['schema']['sequences']) == 24)
    for section in ('management_state', 'portfolio_state', 'closure_state'):
        state = manifest[section]
        expected = {'creations', 'initializations', 'invalid'} if section == 'management_state' else \
                   {'active', 'closed', 'legacy_markers', 'v2_markers', 'invalid'} if section == 'portfolio_state' else \
                   {'closures', 'intents', 'refused', 'invalid'}
        require(set(state) == expected)
        require(all(type(v) is int and v >= 0 for v in state.values()) and state['invalid'] == 0)
    management = manifest['management_contract']
    require(set(management) == {'catalogue', 'acl', 'unsafe'})
    require(management['catalogue'] == CLOSURE_CATALOGUE_SHA256 and management['acl'] == contract['acl'])
    require(type(management['unsafe']) is int and management['unsafe'] == 0)
    require(manifest['management_state']['creations'] == manifest['tables']['portfolio_creations']['count'])
    require(manifest['management_state']['initializations'] == manifest['tables']['users']['count'] ==
            manifest['tables']['portfolio_initializations']['count'])
    state = manifest['closure_state']
    require(state['closures'] == manifest['tables']['portfolio_lifecycle_closures']['count'] == manifest['portfolio_state']['closed'])
    require(state['intents'] == manifest['tables']['portfolio_closure_intents']['count'])
    require(state['refused'] <= state['intents'])
    require(manifest['portfolio_state']['active']+state['closures'] == manifest['tables']['accounts']['count'])
    require(manifest['stock_invalid'] == 0)
    states = manifest['identity_state']
    require(isinstance(states, list) and [r[0] for r in states] == identity_tables('0023'))
    for _, value, called in states:
        require(type(value) is int and 1 <= value <= 9223372036854775807 and type(called) is bool)


def strict_json(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result)
            result[key] = value
        return result

    return json.loads(data, object_pairs_hook=unique)


def private_file(path):
    p = Path(path)
    s = p.lstat()
    require(stat.S_ISREG(s.st_mode) and s.st_uid == os.geteuid())
    require(s.st_mode & 0o077 == 0)
    return p


def private_dir(path):
    p = Path(path)
    s = p.lstat()
    require(stat.S_ISDIR(s.st_mode) and s.st_uid == os.geteuid())
    require(s.st_mode & 0o077 == 0)
    return p


def contained(path, root):
    p = Path(path)
    require(p.is_absolute() and not p.is_symlink())
    require(p.resolve().is_relative_to(root.resolve()))
    return p


def load_config(args):
    synthetic = len(args) == 2 and args[0] == "--synthetic"
    require(synthetic or not args)
    path = Path(args[1]) if synthetic else Path("/etc/birja/backup.env")
    if synthetic:
        require(path.parent.parent == Path("/tmp"))
        require(path.parent.name.startswith("birja-backup-test-"))
        root = private_dir(path.parent)
    else:
        require(os.geteuid() == 0)
        root = Path("/etc/birja")
    c = strict_json(private_file(path).read_text())
    expected = CONFIG_KEYS | (
        set()
        if synthetic
        else {
            "approved_host",
            "production_enabled",
            "access_key_file",
            "secret_key_file",
        }
    )
    # Recovery bundle may retain the approved fixed synthetic source definition
    # beside an archived old checkout. Never accept an arbitrary Compose target.
    require(set(c) in [expected, expected | {"source_compose"}])
    if "source_compose" in c:
        require(synthetic)
        source = Path(c["source_compose"])
        require(source == root / "old" / "docker-compose.ops-test.yml")
        require(source == source.resolve() and source.is_file())
        require(
            hashlib.sha256(source.read_bytes()).hexdigest()
            == "634eabc7c1c3e4235a2d506e7ac1b8417b5cffcca0203df6f4f578f0420ddc91"
        )
    require(c["source_project"] == ("birja-ops-test" if synthetic else "birja-prod"))
    require(re.fullmatch(r"[0-9a-f]{40}", c["release"]))
    for key in ["db_user", "db_name"]:
        require(re.fullmatch(r"[a-z][a-z0-9_]{0,62}", c[key]))
    for key, low, high in [
        ("max_stage_bytes", 1, 2_000_000_000),
        ("timeout_seconds", 1, 3600),
        ("freshness_seconds", 1, 93600),
    ]:
        require(type(c[key]) is int and low <= c[key] <= high)
    require(set(c["quota"]) == QUOTA_KEYS)
    for key in QUOTA_KEYS - {"free_controls_verified", "dedicated_repository"}:
        require(type(c["quota"][key]) is int and c["quota"][key] >= 0)
    require(type(c["recovery_files"]) is list and 1 <= len(c["recovery_files"]) <= 20)
    if synthetic:
        for key in [
            "state_dir",
            "restic_binary",
            "docker_binary",
            "repository",
            "password_file",
        ]:
            contained(c[key], root)
        for p in c["recovery_files"]:
            contained(p, root)
    else:
        require(
            c["production_enabled"] is True
            and c["approved_host"] == socket.gethostname()
        )
        require(c["state_dir"] == "/var/lib/birja/backup")
        require(c["repository"] == DESTINATION)
        require(c["docker_binary"] == "/usr/bin/docker")
        require(c["restic_binary"] == "/usr/local/bin/restic")
        for key in ["password_file", "access_key_file", "secret_key_file"]:
            contained(c[key], root)
        for p in c["recovery_files"]:
            require(
                Path(p).resolve().is_relative_to(root)
                or Path(p).resolve().is_relative_to(Path("/var/lib/birja/ops"))
            )
    private_file(c["password_file"])
    for p in c["recovery_files"]:
        private_file(p)
    require(path == path.resolve())
    c["_config_root"] = str(root)
    c["_synthetic"] = synthetic
    return c


def acquire_operation_lock(path, inherited_fd=None):
    """Return an owned handle; never unlock a parent's open-file description."""
    path = Path(path)
    production = path == Path("/var/lock/birja-deploy.lock")
    require(path.is_absolute())
    resolved = path.resolve()
    if path != resolved:
        # Ubuntu's system alias is the sole exception to canonical lock paths.
        # Its ancestors cannot be writable by other users. A shared /run/lock
        # is safe only with sticky deletion protection for the root-owned file.
        require(production and resolved == Path("/run/lock/birja-deploy.lock"))
        alias = Path("/var/lock")
        info = alias.lstat()
        require(stat.S_ISLNK(info.st_mode) and info.st_uid == 0)
        require(alias.readlink() in [Path("/run/lock"), Path("../run/lock")])
        for parent in [Path("/"), Path("/var"), Path("/run"), Path("/run/lock")]:
            info = parent.lstat()
            require(stat.S_ISDIR(info.st_mode) and info.st_uid == 0)
            require(
                info.st_mode & 0o022 == 0
                or (parent == Path("/run/lock") and info.st_mode & stat.S_ISVTX)
            )
        path = resolved

    def validate(fd):
        current, held = path.lstat(), os.fstat(fd)
        require(stat.S_ISREG(current.st_mode) and stat.S_ISREG(held.st_mode))
        require(held.st_uid == (0 if production else os.geteuid()))
        require(held.st_mode & 0o022 == 0 and os.path.samestat(current, held))

    inherited = (
        os.environ.get("BIRJA_BACKUP_LOCK_FD") if inherited_fd is None else inherited_fd
    )
    if inherited is not None:
        require(
            type(inherited) is str
            and inherited.isascii()
            and inherited.isdigit()
            and 3 <= int(inherited) <= 1024
        )
        fd = int(inherited)
        validate(fd)
        lines = Path(f"/proc/self/fdinfo/{fd}").read_text().splitlines()
        require(
            any(re.search(r"^lock:.* FLOCK +ADVISORY +WRITE ", line) for line in lines)
        )
        owned = os.dup(fd)
    else:
        owned = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    try:
        validate(owned)
        if inherited is None:
            fcntl.flock(owned, fcntl.LOCK_EX | fcntl.LOCK_NB)
        validate(owned)
        return os.fdopen(owned, "a")
    except BaseException:
        os.close(owned)
        raise


def utc(epoch=None):
    return dt.datetime.fromtimestamp(
        time.time() if epoch is None else epoch, dt.UTC
    ).strftime("%Y-%m-%dT%H:%M:%SZ")


def atomic(path, obj):
    fd, name = tempfile.mkstemp(prefix=".status-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(obj, f, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
        d = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(d)
        finally:
            os.close(d)
    finally:
        Path(name).unlink(missing_ok=True)


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def config_digest(c):
    stable = {k: v for k, v in c.items() if not k.startswith("_") and k != "quota"}
    stable["quota_policy"] = {
        k: c["quota"].get(k)
        for k in [
            "storage_limit_bytes",
            "upload_reserve_bytes",
            "repack_reserve_bytes",
            "request_reserve",
            "free_controls_verified",
            "dedicated_repository",
        ]
    }
    stable["material"] = {
        str(p): file_sha(private_file(p)) for p in c["recovery_files"]
    }
    for k in ["password_file", "access_key_file", "secret_key_file"]:
        if k in c:
            stable[k] = {"path": c[k], "sha256": file_sha(private_file(c[k]))}
    if "source_compose" in c:
        stable["source_compose_sha256"] = file_sha(c["source_compose"])
    return sha_bytes(json.dumps(stable, sort_keys=True).encode())


def recovery_binding(c):
    # Installed identity comes from the immutable release and its authenticated
    # inventory, never from an argument claiming that a restore was successful.
    release = HERE.parent
    bundle_sha = None
    inventory_hashes = {}
    if release.parent.name == "releases" and release.parent.parent.name == "recovery":
        require(ID.fullmatch(release.name) and release == release.resolve())
        private_dir(release)
        inventory = json.loads(private_file(release / "INVENTORY.json").read_text())
        for line in private_file(release / "SHA256SUMS").read_text().splitlines():
            value, name = line.split("  ")
            require(ID.fullmatch(value) and name not in inventory_hashes)
            path = release / name
            require(path == path.resolve() and path.is_relative_to(release))
            require(file_sha(path) == value)
            inventory_hashes[name] = value
        require(set(inventory_hashes) == set(inventory["files"]) | {"INVENTORY.json"})
        bundle_sha = release.name
    toolchain = {
        "inventory": inventory_hashes,
        "python": file_sha(sys.executable),
        "docker_host": file_sha("/usr/bin/docker"),
        "bash": file_sha("/bin/bash"),
    }
    for key in ["restic_binary", "docker_binary"]:
        toolchain[key] = file_sha(c[key])
    # Include actual adjacent helpers even outside an installed release.
    toolchain["helpers"] = {
        p.name: file_sha(p)
        for p in HERE.iterdir()
        if p.is_file()
        and p.name
        in {
            "backup-snapshot.py",
            "verify-restore.py",
            "backup-manifest.sql",
            "backup.sh",
            "restore-check.sh",
        }
    }
    return {
        "source_project": c["source_project"],
        "db_name": c["db_name"],
        "db_user": c["db_user"],
        "repository_sha256": sha_bytes(c["repository"].encode()),
        "config_sha256": config_digest(c),
        "toolchain_sha256": sha_bytes(json.dumps(toolchain, sort_keys=True).encode()),
        "bundle_sha256": bundle_sha,
    }


def read_state(state, name):
    return strict_json(private_file(private_dir(state) / name).read_text())


def recovery_gate(c, snapshot_id, expected):
    require(type(snapshot_id) is str and ID.fullmatch(snapshot_id))
    job = Job(c)
    with job.lock() as lock:
        binding = recovery_binding(c)
        require(set(expected) == set(binding) | {"source_release", "source_revision"})
        require(binding["bundle_sha256"] is not None)
        require(expected["source_release"] == c["release"])
        require(all(expected[k] == v for k, v in binding.items()))
        require(
            re.fullmatch(r"[0-9a-f]{40}", expected["source_release"])
            and re.fullmatch(r"[A-Za-z0-9_]{1,64}", expected["source_revision"])
        )
        backup = read_state(job.state, "last-success.json")
        backup_attempt = read_state(job.state, "last-attempt.json")
        success = read_state(job.state, "restore-last-success.json")
        attempt = read_state(job.state, "restore-last-attempt.json")
        require(
            backup["ok"] is True
            and backup_attempt["ok"] is True
            and backup["run_id"] == backup_attempt["run_id"]
        )
        require(
            set(success)
            == set(binding)
            | {
                "format",
                "run_id",
                "snapshot_id",
                "ok",
                "started_epoch",
                "started_utc",
                "completed_epoch",
                "completed_utc",
                "source_release",
                "source_revision",
                "manifest_sha256",
                "dump_sha256",
                "recovery_sha256",
            }
        )
        require(success == attempt and success["ok"] is True and success["format"] == 1)
        require(backup_attempt == backup)
        data_time(backup, c)
        require(backup["utc"] == utc(backup["epoch"]))
        require(
            type(success["format"]) is int
            and re.fullmatch(r"[0-9a-f]{32}", success["run_id"])
        )
        require(backup["snapshot_id"] == success["snapshot_id"] == snapshot_id)
        require(all(success[k] == value for k, value in expected.items()))
        now = time.time()
        for epoch in [
            backup["epoch"],
            success["started_epoch"],
            success["completed_epoch"],
        ]:
            require(
                type(epoch) is int
                and 0 <= now - epoch <= c["freshness_seconds"] <= 93600
            )
        require(
            backup["epoch"] <= success["started_epoch"] <= success["completed_epoch"]
        )
        for prefix in ["started", "completed"]:
            require(
                success[prefix + "_utc"]
                == dt.datetime.fromtimestamp(
                    success[prefix + "_epoch"], dt.UTC
                ).strftime("%Y-%m-%dT%H:%M:%SZ")
            )
        job.refresh_quota(lock)  # Fresh inventory, without changing recovery evidence.
        rows = strict_json(job.restic("snapshots", snapshot_id))
        require(job.check_scope(rows) == [snapshot_id])
        remote_time = dt.datetime.fromisoformat(rows[0]["time"])
        require(remote_time.tzinfo is not None)
        epoch = remote_time.timestamp()
        require(
            0 <= now - epoch <= c["freshness_seconds"] and epoch <= backup["epoch"] + 1
        )
        raw = job.restic("dump", snapshot_id, "/manifest.json")
        require(sha_bytes(raw) == success["manifest_sha256"])
        manifest = strict_json(raw)
        require(
            manifest["release"] == expected["source_release"]
            and manifest["revision"] == expected["source_revision"]
        )
        require(
            manifest["archive_sha256"] == success["dump_sha256"]
            and manifest["recovery_sha256"] == success["recovery_sha256"]
        )
        require(manifest["source_binding"] == binding)
        require(
            manifest["data_epoch"] == backup["data_epoch"]
            and manifest["started_utc"] == backup["data_utc"]
            and manifest["data_utc"] == backup["data_utc"]
        )
        # Inventory and remote reads can consume the last seconds of the RPO.
        # Recheck every freshness predicate at authorization, after all I/O.
        authorized_at = time.time()
        data_time(backup, c, authorized_at)
        require(
            all(
                0 <= authorized_at - value <= c["freshness_seconds"]
                for value in [
                    backup["epoch"],
                    success["started_epoch"],
                    success["completed_epoch"],
                    epoch,
                ]
            )
        )
        return {
            "snapshot_id": snapshot_id,
            "recovery_verified": True,
            "completed_utc": success["completed_utc"],
        }


def data_time(record, c, now=None):
    now = time.time() if now is None else now
    for epoch, stamp in [("data_epoch", "data_utc"), ("epoch", "utc")]:
        require(type(record[epoch]) is int and record[stamp] == utc(record[epoch]))
    require(0 <= now - record["data_epoch"] <= c["freshness_seconds"])
    require(record["data_epoch"] <= record["epoch"] <= now)
    return record["data_epoch"]


def status(c):
    try:
        state = private_dir(c["state_dir"])
        s = json.loads(private_file(state / "last-success.json").read_text())
        a = json.loads(private_file(state / "last-attempt.json").read_text())
        require(a == s and a["ok"] is True)
        require(ID.fullmatch(s["snapshot_id"]))
        data_time(s, c)
        require(
            s["utc"]
            == dt.datetime.fromtimestamp(s["epoch"], dt.UTC).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
        )
        print(f"utc={s['utc']} id={s['snapshot_id']} step=complete")
        return 0
    except (OSError, ValueError, KeyError, TypeError):
        print("step=missing-stale-or-failed")
        return 1


class Job:
    def __init__(self, c):
        self.c = c
        self.state = Path(c["state_dir"])
        self.step = "startup"
        self.started = c.setdefault("_operation_started", time.monotonic())
        self.calls = 0
        self.download_rate = None
        self.run_id = os.urandom(16).hex()
        self.env = {
            "PATH": "/usr/bin:/bin",
            "HOME": str(self.state),
            "TMPDIR": str(self.state),
            "LANG": "C.UTF-8",
            "GOMAXPROCS": "2",
            "GOMEMLIMIT": "256MiB",
        }
        if c["_synthetic"]:
            for key in ["MOCK_ROOT", "FAIL"]:
                if key in os.environ:
                    self.env[key] = os.environ[key]
        else:
            for key, target in [
                ("access_key_file", "AWS_ACCESS_KEY_ID"),
                ("secret_key_file", "AWS_SECRET_ACCESS_KEY"),
            ]:
                value = private_file(c[key]).read_text().strip()
                require(value and "\n" not in value)
                self.env[target] = value
        self.env["RESTIC_PASSWORD_FILE"] = c["password_file"]
        self.env["RESTIC_REPOSITORY"] = c["repository"]
        self.bundle = self.state / "stage" / "backup"
        self.dc = [
            c["docker_binary"],
            "compose",
            "-p",
            c["source_project"],
            "-f",
            "/srv/birja/docker-compose.prod.yml"
            if not c["_synthetic"]
            else c.get(
                "source_compose", str(HERE.parent / "docker-compose.ops-test.yml")
            ),
        ]
        if not c["_synthetic"]:
            self.dc += ["--env-file", "/etc/birja/prod.env"]
        else:
            self.dc += ["--env-file", "/dev/null"]
        self.dc += ["exec", "-T", "postgres"]

    def limit(self):
        resource.setrlimit(
            resource.RLIMIT_FSIZE,
            (self.c["max_stage_bytes"], self.c["max_stage_bytes"]),
        )

    def call(self, argv, *, data=None, input_file=None, output=None, cwd=None, capture_limit=None):
        self.calls += 1
        require(self.calls <= 20)
        left = self.c["timeout_seconds"] - (time.monotonic() - self.started)
        require(left > 0)
        def limits():
            self.limit()
            if capture_limit is not None:
                require(type(capture_limit) is int and 1 <= capture_limit <= self.c["max_stage_bytes"])
                resource.setrlimit(resource.RLIMIT_FSIZE, (capture_limit, capture_limit))
        with tempfile.TemporaryFile(dir=self.state) as capture:
            r = subprocess.run(
                argv,
                check=False,
                input=data,
                stdin=input_file,
                stdout=output or capture,
                stderr=subprocess.DEVNULL,
                env=self.env,
                cwd=cwd,
                timeout=left,
                preexec_fn=self.limit if capture_limit is None else limits,
            )
            require(r.returncode == 0)
            if output is None:
                capture.seek(0)
                return capture.read()
        return b""

    def restic(self, *args, cwd=None):
        self.quota(fresh=self.download_rate is None)
        return self.call(
            [
                self.c["restic_binary"],
                "--json",
                "--no-cache",
                "--compression",
                "auto",
                "-o",
                "s3.connections=2",
                "-o",
                "s3.retries=2",
                "--stuck-request-timeout",
                "30s",
                "--limit-upload",
                "1024",
                "--limit-download",
                str(self.download_rate),
                *args,
            ],
            cwd=cwd,
        )

    def quota(self, *, fresh=True):
        q = self.c["quota"]
        require(
            q["free_controls_verified"] is True and q["dedicated_repository"] is True
        )
        if fresh:
            require(0 <= time.time() - q["observed_at"] <= 300)
        used = sum(
            q[k]
            for k in [
                "visible_bytes",
                "hidden_bytes",
                "unfinished_bytes",
                "other_bytes",
            ]
        )
        require(
            used + q["upload_reserve_bytes"] + q["repack_reserve_bytes"]
            <= q["storage_limit_bytes"]
        )
        require(q["upload_reserve_bytes"] >= self.c["max_stage_bytes"])
        api = self.c.get("_inventory_api")
        native_bytes = api.bytes if api is not None else 0
        require(q["request_remaining"] >= q["request_reserve"] >= 1)
        # Restic has no HTTP counter. Its work is separately bounded by tool
        # calls, retries, connections and this shared whole-operation deadline.
        # Reserve 64 KiB per possible process for limiter bursts/metadata,
        # then double rate*time for protocol/retry overhead. Keep the rate
        # fixed across commands; never grant each subprocess a fresh budget.
        if self.download_rate is None:
            allowance = q["download_remaining_bytes"] - native_bytes - 20 * 65536
            self.download_rate = min(
                1024, allowance // (2 * 1024 * (self.c["timeout_seconds"] + 20))
            )
        require(self.download_rate >= 1)
        require(
            native_bytes
            + 20 * 65536
            + 2 * self.download_rate * 1024 * (self.c["timeout_seconds"] + 20)
            <= q["download_remaining_bytes"]
        )
        require(shutil.disk_usage(self.state).free >= self.c["max_stage_bytes"] * 2)

    def refresh_quota(self, lock):
        """Refresh only inventory under a validated already-held operation lock."""
        path = (
            Path(self.c["_config_root"]) / "operation.lock"
            if self.c["_synthetic"]
            else Path("/var/lock/birja-deploy.lock")
        )
        with acquire_operation_lock(path, str(lock.fileno())):
            spec = importlib.util.spec_from_file_location(
                "quota_preflight", HERE / "backup-quota.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.c["quota"] = module.refresh(self.c)
            self.quota()
            config = Path(self.c["_config_root"]) / (
                "config" if self.c["_synthetic"] else "backup.env"
            )
            private_file(config)
            atomic(config, {k: v for k, v in self.c.items() if not k.startswith("_")})

    def lock(self):
        return acquire_operation_lock(
            Path(self.c["_config_root"]) / "operation.lock"
            if self.c["_synthetic"]
            else Path("/var/lock/birja-deploy.lock")
        )

    def line(self, proc):
        with selectors.DefaultSelector() as selector:
            selector.register(proc.stdout, selectors.EVENT_READ)
            value = bytearray()
            while len(value) < self.c["max_stage_bytes"]:
                left = self.c["timeout_seconds"] - (time.monotonic() - self.started)
                require(left > 0 and selector.select(left))
                b = os.read(proc.stdout.fileno(), 1)
                require(b)
                if b == b"\n":
                    return value.decode()
                value.extend(b)
            raise ValueError("manifest-bound")

    def snapshot(self):
        self.step = "snapshot"
        version = self.call(self.dc + ["pg_dump", "--version"]).decode().strip()
        # A protected pre-upgrade backup runs in the still-old source
        # container. Accept only the two reviewed minor clients, including
        # Debian's package suffix, while retaining the pinned18.7 restore.
        require(
            re.fullmatch(
                r"pg_dump \(PostgreSQL\) 18\.(?:6|7)(?: \([^()\r\n]+\))?", version
            )
        )
        psql = self.dc + [
            "psql",
            "-X",
            "-qAt",
            "-v",
            "ON_ERROR_STOP=1",
            "-U",
            self.c["db_user"],
            "-d",
            self.c["db_name"],
        ]
        proc = subprocess.Popen(
            psql,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=self.env,
        )
        try:
            proc.stdin.write(
                b"BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;\nSET LOCAL idle_in_transaction_session_timeout='1h';\nSET LOCAL statement_timeout='60s';\nSET LOCAL TIME ZONE 'UTC';\nSELECT pg_export_snapshot();\n"
            )
            proc.stdin.flush()
            snapshot = self.line(proc)
            require(re.fullmatch(r"[0-9A-Fa-f]+-[0-9A-Fa-f]+-[0-9]+", snapshot))
            proc.stdin.write(
                b"SELECT version_num FROM alembic_version ORDER BY version_num;\n"
            )
            proc.stdin.flush()
            revision = self.line(proc)
            proc.stdin.write(
                (schema_guard_sql(revision) + manifest_sql(revision)).encode() + b"\n"
            )
            proc.stdin.flush()
            manifest = json.loads(self.line(proc))
            require(manifest["revision"] == revision)
            validate_manifest(manifest)
            archive = self.bundle / "database.dump"
            dump = self.dc + [
                "pg_dump",
                "-U",
                self.c["db_user"],
                "-d",
                self.c["db_name"],
                "-Fc",
                "--compress=none",
                "--snapshot=" + snapshot,
            ]
            with archive.open("wb") as f:
                self.call(dump, output=f)
            with archive.open("rb") as f:
                require(archive.stat().st_size > 5 and f.read(5) == b"PGDMP")
            with archive.open("rb") as f:
                require(
                    self.call(self.dc + ["pg_restore", "--list"], input_file=f).strip()
                )
            if revision in ("0011", "0012", "0013", "0014", "0017", "0020", "0023"):
                selection = ["--table=" + table + "_id_seq" for table in identity_tables(revision)]
                with archive.open("rb") as f:
                    raw_states = self.call(self.dc + ["pg_restore", "--data-only", "--file=-", *selection], input_file=f, capture_limit=65536)
                manifest["identity_state"] = dump_identity_state(raw_states, revision)
                validate_manifest(manifest)
            proc.stdin.write(b"ROLLBACK;\n")
            proc.stdin.close()
            require(proc.wait(timeout=5) == 0)
            require(
                manifest["revision"] and manifest["server_version"].startswith("18.")
            )
            with archive.open("rb") as f:
                digest = hashlib.file_digest(f, "sha256").hexdigest()
            manifest.update(
                {
                    "format": 1,
                    "snapshot": snapshot,
                    "release": self.c["release"],
                    "started_utc": self.start_utc,
                    "data_epoch": self.data_epoch,
                    "data_utc": self.start_utc,
                    "finished_utc": utc(),
                    "archive_sha256": digest,
                    "restic_version": "0.19.1",
                    "pg_dump_version": version,
                }
            )
            (self.bundle / "manifest.json").write_text(
                json.dumps(manifest, sort_keys=True, separators=(",", ":"))
            )
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)
            if proc.stdin and not proc.stdin.closed:
                proc.stdin.close()
            proc.stdout.close()

    def check_scope(self, snapshots):
        require(type(snapshots) is list)
        ids = []
        for item in snapshots:
            require(ID.fullmatch(item["id"]))
            require(item["hostname"] == HOST and item["tags"] == [TAG])
            require(item["paths"] == [str(self.bundle)])
            ids.append(item["id"])
        require(len(ids) == len(set(ids)))
        return ids

    def perform(self):
        self.state.mkdir(mode=0o700, parents=True, exist_ok=True)
        private_dir(self.state)
        with self.lock():
            self.data_epoch = int(time.time())
            self.start_utc = utc(self.data_epoch)
            attempt = {
                "run_id": self.run_id,
                "ok": False,
                "step": "running",
                "utc": self.start_utc,
            }
            atomic(self.state / "last-attempt.json", attempt)
            stage = self.state / "stage"
            created = False
            try:
                self.step = "quota"
                self.quota()
                self.step = "tools"
                require(
                    self.call([self.c["restic_binary"], "version"]).startswith(
                        b"restic 0.19.1 "
                    )
                )
                self.step = "repository-scope"
                previous = self.check_scope(json.loads(self.restic("snapshots")))
                stage.mkdir(mode=0o700)
                created = True
                self.bundle.mkdir(mode=0o700)
                self.snapshot()
                self.step = "recovery-config"
                # Tar padding/header allowance; refuse before writing config data.
                required = sum(p.stat().st_size for p in self.bundle.iterdir())
                required += sum(
                    private_file(p).stat().st_size for p in self.c["recovery_files"]
                )
                required += 20480 + len(self.c["recovery_files"]) * 2048
                require(required <= self.c["max_stage_bytes"])
                with tarfile.open(self.bundle / "recovery.tar", "w") as tar:
                    for index, name in enumerate(self.c["recovery_files"]):
                        private_file(name)
                        tar.add(
                            name,
                            arcname=f"{index:02d}-{Path(name).name}",
                            recursive=False,
                        )
                manifest_path = self.bundle / "manifest.json"
                manifest = json.loads(manifest_path.read_text())
                manifest.update(
                    source_binding=recovery_binding(self.c),
                    recovery_sha256=file_sha(self.bundle / "recovery.tar"),
                )
                manifest_path.write_text(
                    json.dumps(manifest, sort_keys=True, separators=(",", ":"))
                )
                size = sum(p.stat().st_size for p in self.bundle.iterdir())
                require(size <= self.c["max_stage_bytes"])
                self.quota()
                self.step = "upload"
                lines = self.restic(
                    "backup", "--host", HOST, "--tag", TAG, ".", cwd=self.bundle
                ).splitlines()
                summaries = [
                    j
                    for line in lines
                    if (j := json.loads(line)).get("message_type") == "summary"
                ]
                require(len(summaries) == 1)
                sid = summaries[0]["snapshot_id"]
                require(ID.fullmatch(sid))
                self.step = "verify"
                exact = self.check_scope(json.loads(self.restic("snapshots", sid)))
                require(exact == [sid])
                nodes = [
                    json.loads(line) for line in self.restic("ls", sid).splitlines()
                ]
                files = {n["path"]: n["size"] for n in nodes if n.get("type") == "file"}
                # Backing up '.' gives rooted relative snapshot contents (/name).
                expected = {
                    "/" + p.name: p.stat().st_size for p in self.bundle.iterdir()
                }
                require(files == expected)
                require(
                    self.restic("dump", sid, "/manifest.json")
                    == (self.bundle / "manifest.json").read_bytes()
                )
                self.restic("check")
                self.step = "rotation"
                current = self.check_scope(json.loads(self.restic("snapshots")))
                require(set(current) == set(previous) | {sid})
                old = [x for x in previous if x != sid]
                if old:
                    self.restic("forget", *old)
                    self.restic("prune", "--max-repack-size", "0", "--max-unused", "0")
                    self.restic("check")
                self.step = "cleanup"
                shutil.rmtree(stage)
                created = False
                self.step = "publish"
                now = int(time.time())
                result = {
                    "run_id": self.run_id,
                    "ok": True,
                    "step": "complete",
                    "utc": dt.datetime.fromtimestamp(now, dt.UTC).strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    ),
                    "epoch": now,
                    "data_epoch": self.data_epoch,
                    "data_utc": self.start_utc,
                    "snapshot_id": sid,
                    "archive_bytes": size,
                    "tool_invocations": self.calls,
                    "elapsed_ms": int((time.monotonic() - self.started) * 1000),
                    "data_added_packed": summaries[0].get("data_added_packed"),
                    "cpu_milliseconds": int(
                        (
                            resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime
                            + resource.getrusage(resource.RUSAGE_CHILDREN).ru_stime
                        )
                        * 1000
                    ),
                    "peak_child_rss_kib": resource.getrusage(
                        resource.RUSAGE_CHILDREN
                    ).ru_maxrss,
                    "network_requests_measured": False,
                    "network_bytes_measured": False,
                    "assurance": "upload-verified+metadata+manifest+structural;restore-not-proven",
                }
                atomic(self.state / "last-success.json", result)
                atomic(self.state / "last-attempt.json", result)
                print(f"utc={result['utc']} id={sid} step=complete")
                return 0
            except BaseException:  # noqa: BLE001 - publish failure for signals and all producer errors
                original_step = self.step
                cleanup_ok = True
                if created:
                    try:
                        shutil.rmtree(stage)
                    except OSError:
                        cleanup_ok = False
                attempt.update(step=original_step, utc=utc(), cleanup_ok=cleanup_ok)
                atomic(self.state / "last-attempt.json", attempt)
                print(
                    f"utc={attempt['utc']} step={original_step} failed=1 cleanup_ok={int(cleanup_ok)}"
                )
                return 1


def _bundle_package(output, *, recovery=None, payload_version):
    """Stage a finite reviewed family; transport mocks never prove recovery."""
    require(type(payload_version) is int and payload_version in (2, 3))
    closure_bootstrap() if payload_version == 3 else management_bootstrap()
    source_spec = importlib.util.spec_from_file_location('package_sources', HERE / 'tests/portfolio-sources.py')
    source_module = importlib.util.module_from_spec(source_spec)
    source_spec.loader.exec_module(source_module)
    source_module.validate_matrix()
    if recovery is None:
        spec = importlib.util.spec_from_file_location('producer_recovery_tools', HERE / 'verify-restore.py')
        recovery = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(recovery)
    synthetic_path = recovery.synthetic_path
    runtime = recovery.runtime
    digest = recovery.digest
    image_inspect = recovery.image_inspect
    registry_manifests = recovery.registry_manifests
    verify_saved_image = recovery.verify_saved_image
    CORE = recovery.CORE
    UNITS = recovery.UNITS
    PROVENANCE = recovery.PROVENANCE
    REGISTRY_REF = recovery.REGISTRY_REF
    IMAGE_PROVENANCE = recovery.IMAGE_PROVENANCE
    ENV = recovery.ENV
    IMAGE_ID = recovery.IMAGE_ID
    INDEX_DIGEST = recovery.INDEX_DIGEST
    PLATFORM_DIGEST = recovery.PLATFORM_DIGEST
    RESTIC_SHA = recovery.RESTIC_SHA
    CONTRACT_PAYLOAD = recovery.CONTRACT_PAYLOAD
    recovery_contract = recovery.recovery_contract
    output = synthetic_path(output, False)
    require(not output.exists())
    versions = runtime()
    tools = Path("/tmp/birja-test-tools/restic-0.19.1")
    require(digest(tools / "restic") == RESTIC_SHA)
    require(all(digest(tools / n) == h for n, h in PROVENANCE.items()))
    image_inspect(REGISTRY_REF)
    index_bytes, manifest_bytes = registry_manifests()
    with tempfile.TemporaryDirectory(dir=output.parent) as tmp:
        stage = Path(tmp)
        files = CORE + UNITS + (PORTFOLIO_PAYLOAD_V3 if payload_version == 3 else PORTFOLIO_PAYLOAD_V2)
        for name in files:
            src = HERE.parent / name
            require(src.is_file() and not src.is_symlink())
            dest = stage / name
            dest.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            shutil.copyfile(src, dest)
        source_payloads = source_module.archive_payloads()
        if payload_version == 2:
            source_payloads = {name: data for name, data in source_payloads.items()
                               if name != 'sources/portfolio0020.tar'}
        if source_payloads:
            RETAINED_SOURCE_PAYLOADS = {name: identity[1] for lane, identity in source_module.FIXED_RELEASES.items()
                                        for name in ['sources/' + lane + '.tar']
                                        if payload_version == 3 or lane != 'portfolio0020'}
            require(set(source_payloads) == set(RETAINED_SOURCE_PAYLOADS))
            for name, data in source_payloads.items():
                require(hashlib.sha256(data).hexdigest() == RETAINED_SOURCE_PAYLOADS[name])
                destination = stage / name
                destination.parent.mkdir(mode=0o700, exist_ok=True)
                destination.write_bytes(data)
        for directory in ["tools", "images", "provenance"]:
            (stage / directory).mkdir(mode=0o700)
        shutil.copyfile(tools / "restic", stage / "tools/restic")
        for n in PROVENANCE:
            shutil.copyfile(tools / n, stage / "provenance" / n)
        (stage / "provenance/verified.json").write_text(
            json.dumps(
                {
                    "fingerprint": "CF8F18F2844575973F79D4E191A6868BD3F7A907",
                    "binary_sha256": RESTIC_SHA,
                    "compressed_sha256": "f415415624dcc452f2a02b8c33641791a8c6d6d3b65bbb3543fcf9a25151585c",
                    "signature": "GOODSIG VALIDSIG; verified 2026-11-02; official restic 0.19.1 linux amd64",
                },
                sort_keys=True,
            )
        )
        with (stage / "images/postgres.tar").open("wb") as f:
            run = subprocess.run(
                ["docker", "image", "save", "--platform", "linux/amd64", REGISTRY_REF],
                check=False,
                stdout=f,
                stderr=subprocess.DEVNULL,
                env=ENV,
                timeout=120,
            )
            require(run.returncode == 0)
        for name, data in zip(
            IMAGE_PROVENANCE, [index_bytes, manifest_bytes], strict=True
        ):
            (stage / name).write_bytes(data)
        with (stage / "images/postgres.tar").open("rb") as saved:
            verify_saved_image(saved, index_bytes, manifest_bytes)
        files = sorted(
            p.relative_to(stage).as_posix() for p in stage.rglob("*") if p.is_file()
        )
        inventory = {
            "format": 1,
            "portfolio_payload": closure_payload_inventory(stage) if payload_version == 3 else portfolio_payload_inventory(stage),
            "recovery_profile": "deploy-recovery-v4" if payload_version == 3 else "deploy-recovery-v3",
            "files": files,
            "units": UNITS,
            "image_id": IMAGE_ID,
            "registry_reference": REGISTRY_REF,
            "registry_index_digest": INDEX_DIGEST,
            "platform_manifest_digest": PLATFORM_DIGEST,
            "restic_sha256": RESTIC_SHA,
            "runtime": versions,
            "schema_contract": {
                "revisions": [r for r in recovery_contract().SUPPORTED_REVISIONS
                              if payload_version == 3 or r != '0023'],
                "payload_sha256": {name: digest(stage / name) for name in CONTRACT_PAYLOAD},
            },
        }
        if source_payloads:
            inventory["retained_source_payloads"] = RETAINED_SOURCE_PAYLOADS
        (stage / "INVENTORY.json").write_text(json.dumps(inventory, sort_keys=True))
        files.append("INVENTORY.json")
        (stage / "SHA256SUMS").write_text(
            "".join(digest(stage / n) + "  " + n + "\n" for n in sorted(files))
        )
        files.append("SHA256SUMS")
        with tarfile.open(output, "x", format=tarfile.USTAR_FORMAT) as t:
            for name in sorted(files):
                p = stage / name
                info = tarfile.TarInfo(name)
                info.size = p.stat().st_size
                info.mode = (
                    0o700 if name.endswith(".sh") or name == "tools/restic" else 0o600
                )
                with p.open("rb") as f:
                    t.addfile(info, f)
        with tarfile.open(output, 'r:') as archive:
            require(recovery.tar_members(archive) == set(files))
    output.chmod(0o600)
    sha = digest(output)
    record = output.with_suffix(output.suffix + ".sha256")
    require(not record.exists())
    record.write_text(sha + "\n")
    record.chmod(0o600)
    print("archive_sha256=" + sha)


def bundle_package_v2(output, *, recovery=None):
    """Retained V2 semantics; use its authenticated qualified source tree."""
    return _bundle_package(output, recovery=recovery, payload_version=2)


def bundle_package_v3(output, *, recovery=None):
    """Produce current closure evidence; Plan06 owns the explicit V3 consumer."""
    return _bundle_package(output, recovery=recovery, payload_version=3)


def main(argv, *, config=None):
    os.umask(0o077)
    if argv and argv[0] in ('bundle-v2', 'bundle-v3'):
        parser = argparse.ArgumentParser(allow_abbrev=False)
        parser.add_argument('--output', required=True)
        parser.add_argument('--include-units', action='store_true')
        args = parser.parse_args(argv[1:])
        (bundle_package_v3 if argv[0] == 'bundle-v3' else bundle_package_v2)(args.output)
        return 0
    try:
        require(argv and argv[0] in ["backup", "status", "recovery-gate"])
        if argv[0] == "recovery-gate":
            require(
                len([x.split("=", 1)[0] for x in argv if x.startswith("--")])
                == len({x.split("=", 1)[0] for x in argv if x.startswith("--")})
            )
            parser = argparse.ArgumentParser(allow_abbrev=False)
            for name in ["snapshot", "source-release", "source-revision", "bundle-sha"]:
                parser.add_argument("--" + name, required=True)
            parser.add_argument("--synthetic")
            args = parser.parse_args(argv[1:])
            c = load_config(["--synthetic", args.synthetic] if args.synthetic else [])
            expected = recovery_binding(c)
            require(expected["bundle_sha256"] == args.bundle_sha)
            expected.update(
                source_release=args.source_release, source_revision=args.source_revision
            )
            result = recovery_gate(c, args.snapshot, expected)
            print("recovery_verified=true id=" + result["snapshot_id"])
            return 0
        c = load_config(argv[1:]) if config is None else config
    except (OSError, ValueError, KeyError, TypeError):
        print("step=config invalid=1")
        return 2
    if argv[0] == "status":
        return status(c)

    def interrupted(signum, frame):
        raise InterruptedError("interrupted")

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        return Job(c).perform()
    except (OSError, ValueError, KeyError, TypeError):
        print("step=lock-or-startup failed=1")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
