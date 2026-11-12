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


SUPPORTED_REVISIONS = ("0007", "0008", "0009", "0010", "0011", "0012", "0013", "0014")
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


def validate_dividend_authority(authority, *, quarantined=False):
    require(isinstance(authority,dict) and set(authority)=={'functions','owners','runtime_acl','runtime_columns','sequence_acl'})
    validate_dividend_functions(authority['functions'],acl_mode='quarantined' if quarantined else 'source')
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
    contract_columns(revision)
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
            if revision in ("0011", "0012", "0013", "0014"):
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


def main(argv, *, config=None):
    os.umask(0o077)
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
