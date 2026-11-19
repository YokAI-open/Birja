-- Reviewed populated-object administration, invoked only by configure-db.sh.
-- psql values arrive on stdin; neither credentials nor raw errors are printed.
BEGIN;
SET LOCAL statement_timeout = '120s';
SET LOCAL lock_timeout = '5s';
SELECT set_config('birja.bootstrap', :'bootstrap', true) AS bootstrap_guard \gset
DO $preflight$
DECLARE t text; owner_name text;
BEGIN
  IF current_user <> current_setting('birja.bootstrap') OR NOT
    (SELECT rolsuper FROM pg_roles WHERE rolname=current_user) THEN
    RAISE EXCEPTION 'administrative identity mismatch';
  END IF;
  IF (SELECT version_num FROM public.alembic_version) IN ('0015','0016','0018','0019','0021','0022') THEN
    RAISE EXCEPTION 'migration_only';
  END IF;
  IF (SELECT version_num FROM public.alembic_version) NOT IN ('0007','0008','0009','0010','0011','0012','0013','0014','0017','0020','0023') THEN
    RAISE EXCEPTION 'unsupported populated revision';
  END IF;
  FOREACH t IN ARRAY ARRAY['users','accounts','auth_sessions','refresh_tokens','coins','prices','holdings','trades','alembic_version'] || CASE WHEN (SELECT version_num FROM public.alembic_version) IN ('0009','0010','0011','0012','0013','0014','0017','0020') THEN ARRAY['stock_instruments','stock_quotes','stock_sessions','stock_data_admissions'] ELSE ARRAY[]::text[] END || CASE WHEN (SELECT version_num FROM public.alembic_version) IN ('0011','0012','0013','0014','0017','0020') THEN ARRAY['stock_action_events','stock_action_sources','stock_action_revisions','stock_action_observations','stock_action_state','stock_ownership_movements','stock_split_applications','stock_dividend_entitlements','stock_action_resolutions'] ELSE ARRAY[]::text[] END || CASE WHEN (SELECT version_num FROM public.alembic_version) IN ('0013','0014','0017','0020') THEN ARRAY['stock_fill_facts','stock_status_evidence'] ELSE ARRAY[]::text[] END || CASE WHEN (SELECT version_num FROM public.alembic_version) IN ('0014','0017','0020') THEN ARRAY['stock_dividend_payments','stock_dividend_decisions'] ELSE ARRAY[]::text[] END || CASE WHEN (SELECT version_num FROM public.alembic_version)IN ('0017','0020') THEN ARRAY['portfolio_stock_closures'] ELSE ARRAY[]::text[] END || CASE WHEN (SELECT version_num FROM public.alembic_version)='0020' THEN ARRAY['portfolio_creations','portfolio_initializations'] ELSE ARRAY[]::text[] END LOOP
    SELECT pg_get_userbyid(c.relowner) INTO owner_name FROM pg_class c
      WHERE c.oid=to_regclass(format('public.%I',t)) AND c.relkind='r';
    IF owner_name IS NULL OR owner_name NOT IN (current_user,'birja_migrator') THEN
      RAISE EXCEPTION 'unexpected application owner';
    END IF;
  END LOOP;
  IF EXISTS (SELECT FROM pg_roles WHERE rolname IN ('birja_app','birja_scheduler','birja_migrator')
     AND (rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls OR rolinherit))
     OR EXISTS (SELECT FROM pg_auth_members WHERE member IN
       (SELECT oid FROM pg_roles WHERE rolname IN ('birja_app','birja_scheduler','birja_migrator'))
       OR roleid IN (SELECT oid FROM pg_roles WHERE rolname IN ('birja_app','birja_scheduler','birja_migrator'))) THEN
    RAISE EXCEPTION 'unsafe pre-existing role attributes or membership';
  END IF;
  IF EXISTS (SELECT FROM pg_roles WHERE rolname='birja_action_operator'
     AND (rolcanlogin OR rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication
          OR rolbypassrls OR rolinherit)) OR
     EXISTS (SELECT FROM pg_auth_members WHERE
       member=(SELECT oid FROM pg_roles WHERE rolname='birja_action_operator') OR
       roleid=(SELECT oid FROM pg_roles WHERE rolname='birja_action_operator')) THEN
    RAISE EXCEPTION 'unsafe action operator attributes or membership';
  END IF;
  IF EXISTS (SELECT FROM pg_class WHERE relowner IN
    (SELECT oid FROM pg_roles WHERE rolname IN ('birja_app','birja_scheduler')))
    OR EXISTS (SELECT FROM pg_namespace WHERE nspowner IN
    (SELECT oid FROM pg_roles WHERE rolname IN ('birja_app','birja_scheduler','birja_migrator')))
    OR EXISTS (SELECT FROM pg_database WHERE datdba IN
    (SELECT oid FROM pg_roles WHERE rolname IN ('birja_app','birja_scheduler','birja_migrator'))) THEN
    RAISE EXCEPTION 'unexpected runtime ownership';
  END IF;
END
$preflight$;
-- Exact0014 financial authority, authenticated before any ownership/grant changes.
DO $dividend_identity$
DECLARE expected record; actual record;
BEGIN
 IF (SELECT version_num FROM public.alembic_version)<>'0014' THEN RETURN; END IF;
 FOR expected IN SELECT * FROM (VALUES
 ('public.stock_dividend_authority(bigint,bigint,text,text,boolean,jsonb)','7861fec1e2552603ad9d5b8c9d314572dee859fa0f6d2e2247812e793e121d23',false),
 ('public.apply_stock_dividend(bigint,bigint,text,text)','4fa0589f573067ee7a870addce0e303a79152ee47cb7c857632104c9d5bd0507',true),
 ('public.record_stock_dividend_hold(bigint,text)','68b31d48ee5036cd962770b6a0be7d29a50a3d9e8a7f709faf728344d6c6072b',true),
 ('public.reject_stock_dividend_mutation()','1ed29a1005ee6925f954852f4aec69abf2f4865a3a6a0b7cab53391c4cc5c2fa',false)
 ) AS manifest(signature,body_hash,definer) LOOP
   SELECT p.*,pg_get_userbyid(p.proowner) AS owner_name,l.lanname
     INTO actual FROM pg_proc p JOIN pg_language l ON l.oid=p.prolang
     WHERE p.oid=to_regprocedure(expected.signature);
   IF NOT FOUND OR actual.owner_name<>'birja_migrator'
     OR actual.prosecdef<>expected.definer OR actual.provolatile<>'v'
     OR actual.prokind<>'f' OR actual.proparallel<>'u' OR actual.lanname<>'plpgsql'
     OR actual.proretset<>expected.definer OR actual.proisstrict OR actual.proleakproof
     OR actual.pronargdefaults<>0 OR actual.prosupport<>0
     OR actual.proallargtypes IS DISTINCT FROM (CASE
       WHEN expected.definer AND actual.proname='apply_stock_dividend'
         THEN ARRAY[20,20,25,25,20,20,25]::oid[]
       WHEN expected.definer THEN ARRAY[20,25,20,20,25]::oid[] ELSE NULL END)
     OR actual.proargmodes IS DISTINCT FROM (CASE
       WHEN expected.definer AND actual.proname='apply_stock_dividend'
         THEN ARRAY['i','i','i','i','t','t','t']::"char"[]
       WHEN expected.definer THEN ARRAY['i','i','t','t','t']::"char"[] ELSE NULL END)
     OR actual.proargnames IS DISTINCT FROM (CASE actual.proname
       WHEN 'apply_stock_dividend' THEN ARRAY['p_event','p_entitlement','p_revision',
         'p_fingerprint','payment_id','decision_id','outcome']
       WHEN 'record_stock_dividend_hold' THEN ARRAY['p_payment','p_revision',
         'payment_id','decision_id','outcome']
       WHEN 'stock_dividend_authority' THEN ARRAY['p_event','p_entitlement','p_revision',
         'p_fingerprint','p_verified','p_expected'] ELSE NULL END)
     OR actual.prorettype<>(CASE WHEN expected.definer THEN 'record'::regtype
       WHEN expected.signature='public.reject_stock_dividend_mutation()' THEN 'trigger'::regtype
       ELSE 'jsonb'::regtype END)
     OR actual.proconfig IS DISTINCT FROM ARRAY['search_path=pg_catalog, public, pg_temp']
     OR encode(sha256(convert_to(actual.prosrc,'UTF8')),'hex')<>expected.body_hash
     OR EXISTS(SELECT FROM aclexplode(coalesce(actual.proacl,acldefault('f',actual.proowner))) x
       WHERE x.is_grantable OR x.privilege_type<>'EXECUTE'
       OR x.grantee NOT IN (actual.proowner,
         CASE WHEN expected.definer THEN coalesce((SELECT oid FROM pg_roles
           WHERE rolname='birja_scheduler'),actual.proowner) ELSE actual.proowner END))
   THEN RAISE EXCEPTION 'dividend function authority mismatch'; END IF;
 END LOOP;
 IF EXISTS(SELECT FROM pg_namespace n,
   LATERAL aclexplode(coalesce(n.nspacl,acldefault('n',n.nspowner))) x
   WHERE n.nspname='public' AND x.privilege_type='CREATE' AND
     x.grantee IN (0,coalesce((SELECT oid FROM pg_roles WHERE rolname='birja_app'),0),
       coalesce((SELECT oid FROM pg_roles WHERE rolname='birja_scheduler'),0))) THEN
   RAISE EXCEPTION 'untrusted dividend schema create'; END IF;
END $dividend_identity$;

DO $portfolio_identity$
DECLARE expected record; actual record;
BEGIN
 IF (SELECT version_num FROM public.alembic_version)<>'0017' THEN RETURN; END IF;
 IF (SELECT count(*) FROM pg_roles WHERE rolname IN
   ('birja_app','birja_scheduler','birja_migrator'))<>3 OR EXISTS(
   SELECT FROM pg_roles WHERE rolname IN ('birja_app','birja_scheduler','birja_migrator')
    AND (rolinherit OR rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls))
 OR EXISTS(SELECT FROM pg_auth_members WHERE roleid IN
   (SELECT oid FROM pg_roles WHERE rolname IN ('birja_app','birja_scheduler','birja_migrator'))
   OR member IN (SELECT oid FROM pg_roles WHERE rolname IN
   ('birja_app','birja_scheduler','birja_migrator'))) THEN
  RAISE EXCEPTION 'unsafe portfolio roles; refusing grants'; END IF;
 IF (SELECT count(*)<>1 OR NOT bool_and(version_num='0017') FROM public.alembic_version)
 THEN RAISE EXCEPTION 'portfolio final revision required'; END IF;
 FOR expected IN SELECT unnest(ARRAY['alembic_version','users','accounts','auth_sessions',
  'refresh_tokens','coins','prices','holdings','trades','stock_instruments','stock_quotes',
  'stock_sessions','stock_data_admissions','stock_action_events','stock_action_sources',
  'stock_action_revisions','stock_action_observations','stock_action_state',
  'stock_ownership_movements','stock_split_applications','stock_dividend_entitlements',
  'stock_action_resolutions','stock_fill_facts','stock_status_evidence',
  'stock_dividend_payments','stock_dividend_decisions','portfolio_stock_closures']) AS name LOOP
  IF NOT EXISTS(SELECT FROM pg_class c WHERE c.oid=to_regclass('public.'||expected.name)
    AND c.relkind='r' AND c.relowner='birja_migrator'::regrole) THEN
   RAISE EXCEPTION 'unexpected portfolio relation; refusing grants'; END IF;
 END LOOP;
 IF to_regprocedure('public.associate_legacy_portfolio_only()') IS NOT NULL
 OR EXISTS(SELECT FROM pg_trigger WHERE NOT tgisinternal AND
   tgfoid::regprocedure::text LIKE '%associate_legacy_portfolio_only%') THEN
   RAISE EXCEPTION 'finite portfolio exception remains'; END IF;
 FOR expected IN SELECT * FROM (VALUES
 ('public.check_stock_fill_integrity()','55c8f44882c787923bb9f1ac2e6e26fc2493d7eced19c48d40560e5f042b290b',false,''),
 ('public.assert_stock_execution_current(bigint,bigint,jsonb)','dd923d5797c95072163bd59918a95935849e9acc7af884b406706dcedfa7c158',false,'birja_app'),
 ('public.reject_stock_dividend_mutation()','bbb7ec48f270806ecc4273ce5fb5996c26d2c7a84c8edb9c47de20a9c09016d7',false,''),
 ('public.stock_dividend_authority(bigint,bigint,text,text,boolean,jsonb)','a3085991a1d8397bb446f47aabf285b6c3f97d5bf45ea72e7982ab360d34ed12',false,''),
 ('public.apply_stock_dividend(bigint,bigint,text,text)','e9b7686f3b17b5a1df89e351d01c8244a610de03346f847f5ad8c7a3d20ef99e',true,'birja_scheduler'),
 ('public.record_stock_dividend_hold(bigint,text)','cbab7352d3964e2ed79d88748cbd6c6428ba0c29bc8652fc2a3ba79d96b6612d',true,'birja_scheduler'),
 ('public.check_stock_split_digest_version()','bea15354f486b6df5fe7d3d2687c98ae5b98082aebb350cf83b12fc0b3ee833d',false,''),
 ('public.check_portfolio_financial_write()','606f8a858caf900d9e20239a2dd49575a84976a77ab73289458b51e4aad9125c',true,''),
 ('public.lock_stock_portfolio_roots(bigint)','ccd98d6b645d315b9a4b308a2dd28d7727b8a15565b36a9b83cce7a3ad4809c9',true,'birja_scheduler')
 ) AS manifest(signature,body_hash,definer,executor) LOOP
  SELECT p.*,pg_get_userbyid(p.proowner) AS owner_name,l.lanname INTO actual
   FROM pg_proc p JOIN pg_language l ON l.oid=p.prolang
   WHERE p.oid=to_regprocedure(expected.signature);
  IF NOT FOUND OR actual.owner_name<>'birja_migrator'
   OR actual.prosecdef<>expected.definer OR actual.lanname<>'plpgsql'
   OR actual.prokind<>'f' OR actual.provolatile<>'v' OR actual.proparallel<>'u'
   OR actual.proisstrict OR actual.proleakproof OR actual.pronargdefaults<>0
   OR actual.prosupport<>0
   OR actual.provariadic<>0
   OR actual.proallargtypes IS DISTINCT FROM (CASE actual.proname
     WHEN 'apply_stock_dividend' THEN ARRAY[20,20,25,25,20,20,25]::oid[]
     WHEN 'record_stock_dividend_hold' THEN ARRAY[20,25,20,20,25]::oid[] ELSE NULL END)
   OR actual.proargmodes IS DISTINCT FROM (CASE actual.proname
     WHEN 'apply_stock_dividend' THEN ARRAY['i','i','i','i','t','t','t']::"char"[]
     WHEN 'record_stock_dividend_hold' THEN ARRAY['i','i','t','t','t']::"char"[] ELSE NULL END)
   OR actual.proargnames IS DISTINCT FROM (CASE actual.proname
     WHEN 'apply_stock_dividend' THEN ARRAY['p_event','p_entitlement','p_revision',
       'p_fingerprint','payment_id','decision_id','outcome']
     WHEN 'record_stock_dividend_hold' THEN ARRAY['p_payment','p_revision',
       'payment_id','decision_id','outcome']
     WHEN 'stock_dividend_authority' THEN ARRAY['p_event','p_entitlement','p_revision',
       'p_fingerprint','p_verified','p_expected']
     WHEN 'assert_stock_execution_current' THEN ARRAY['p_trade','p_user','p_expected']
     WHEN 'lock_stock_portfolio_roots' THEN ARRAY['p_coin'] ELSE NULL END)
   OR actual.proretset<>(actual.proname IN ('apply_stock_dividend','record_stock_dividend_hold'))
   OR actual.prorettype<>(CASE
     WHEN actual.proname IN ('apply_stock_dividend','record_stock_dividend_hold')
       THEN 'record'::regtype
     WHEN actual.proname='stock_dividend_authority' THEN 'jsonb'::regtype
     WHEN actual.proname IN ('lock_stock_portfolio_roots','assert_stock_execution_current')
       THEN 'void'::regtype
     ELSE 'trigger'::regtype END)
   OR actual.proconfig IS DISTINCT FROM ARRAY['search_path=pg_catalog, public, pg_temp']
   OR encode(sha256(convert_to(actual.prosrc,'UTF8')),'hex')<>expected.body_hash
   OR EXISTS(SELECT FROM aclexplode(coalesce(actual.proacl,acldefault('f',actual.proowner))) x
      WHERE x.is_grantable OR x.privilege_type<>'EXECUTE'
      OR x.grantee NOT IN (actual.proowner,coalesce((SELECT oid FROM pg_roles
       WHERE rolname=expected.executor),actual.proowner)))
  THEN RAISE EXCEPTION 'portfolio function authority mismatch'; END IF;
 END LOOP;
 IF NOT EXISTS(SELECT FROM pg_attribute a WHERE
   a.attrelid='public.stock_split_applications'::regclass
   AND a.attname='owner_digest_version' AND a.atttypid='smallint'::regtype
   AND NOT a.attnotnull AND NOT a.atthasdef AND NOT a.attisdropped)
 OR NOT EXISTS(SELECT FROM pg_constraint c WHERE
   c.conrelid='public.stock_split_applications'::regclass
   AND c.conname='ck_stock_split_applications_owner_digest_version_known'
   AND c.convalidated AND c.contype='c'
   AND pg_get_constraintdef(c.oid)=
    'CHECK (((owner_digest_version IS NULL) OR (owner_digest_version = 2)))') THEN
   RAISE EXCEPTION 'portfolio global digest shape mismatch'; END IF;
 IF EXISTS(SELECT FROM pg_attribute WHERE
   attrelid='public.stock_split_applications'::regclass
   AND attname IN ('user_id','portfolio_id') AND NOT attisdropped) THEN
   RAISE EXCEPTION 'global split has owned association'; END IF;
 IF (SELECT count(*) FROM information_schema.columns WHERE table_schema='public'
   AND column_name='portfolio_id' AND is_nullable='NO' AND table_name IN
   ('holdings','trades','stock_fill_facts','stock_ownership_movements',
    'stock_dividend_entitlements','stock_dividend_payments','stock_dividend_decisions'))<>7
 THEN RAISE EXCEPTION 'portfolio required lineage mismatch'; END IF;
 IF NOT EXISTS(SELECT FROM pg_trigger WHERE NOT tgisinternal AND tgenabled='O'
   AND tgrelid='public.stock_split_applications'::regclass AND tgtype=7
   AND tgname='stock_split_digest_version'
   AND tgfoid='public.check_stock_split_digest_version()'::regprocedure)
 OR NOT EXISTS(SELECT FROM pg_trigger WHERE NOT tgisinternal AND tgenabled='O'
   AND tgrelid='public.stock_split_applications'::regclass AND tgtype=27
   AND tgname='portfolio_record_immutable'
   AND tgfoid='public.reject_stock_dividend_mutation()'::regprocedure)
 OR (SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal AND tgenabled='O'
   AND tgfoid='public.check_portfolio_financial_write()'::regprocedure)<>9
 THEN RAISE EXCEPTION 'portfolio trigger authority mismatch'; END IF;
 IF EXISTS(SELECT FROM pg_namespace n,
   LATERAL aclexplode(coalesce(n.nspacl,acldefault('n',n.nspowner))) x
   WHERE n.nspname='public' AND x.privilege_type='CREATE' AND
   x.grantee IN (0,'birja_app'::regrole,'birja_scheduler'::regrole)) THEN
   RAISE EXCEPTION 'untrusted portfolio schema create'; END IF;
END $portfolio_identity$;

DO $management_identity$
BEGIN
 IF (SELECT version_num FROM public.alembic_version)<>'0020' THEN RETURN; END IF;
 IF (SELECT count(*)<>1 OR NOT bool_and(version_num='0020') FROM public.alembic_version)
 THEN RAISE EXCEPTION 'management final revision required'; END IF;
 IF EXISTS(SELECT FROM pg_roles WHERE rolname IN
  ('birja_app','birja_scheduler','birja_migrator','birja_action_operator')
  AND (rolinherit OR rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls))
 OR (SELECT count(*) FROM pg_roles WHERE rolname IN
  ('birja_app','birja_scheduler','birja_migrator','birja_action_operator'))<>4
 OR EXISTS(SELECT FROM pg_auth_members m JOIN pg_roles r ON
  r.oid=m.roleid OR r.oid=m.member WHERE r.rolname IN
  ('birja_app','birja_scheduler','birja_migrator','birja_action_operator'))
 OR EXISTS(SELECT FROM pg_roles WHERE rolname='birja_action_operator' AND rolcanlogin)
 THEN RAISE EXCEPTION 'unsafe management roles'; END IF;
 IF EXISTS(SELECT FROM pg_rewrite r JOIN pg_class c ON c.oid=r.ev_class
  WHERE c.relnamespace='public'::regnamespace)
 THEN RAISE EXCEPTION 'unexpected management rewrite rule'; END IF;
 IF EXISTS(SELECT FROM pg_database d JOIN pg_roles r ON r.oid=d.datdba
  WHERE d.datname=current_database() AND r.rolname IN
  ('birja_app','birja_scheduler','birja_migrator','birja_action_operator'))
 OR EXISTS(SELECT FROM pg_namespace n JOIN pg_roles r ON r.oid=n.nspowner
  WHERE n.nspname='public' AND r.rolname IN
  ('birja_app','birja_scheduler','birja_migrator','birja_action_operator'))
 THEN RAISE EXCEPTION 'unsafe management database/schema ownership'; END IF;
 IF EXISTS(SELECT FROM pg_namespace n,
  LATERAL aclexplode(coalesce(n.nspacl,acldefault('n',n.nspowner))) x
  WHERE n.nspname='public' AND x.privilege_type='CREATE' AND
  x.grantee IN (0,'birja_app'::regrole,'birja_scheduler'::regrole))
 OR has_schema_privilege('birja_app','public','CREATE')
 OR has_schema_privilege('birja_scheduler','public','CREATE')
 THEN RAISE EXCEPTION 'unsafe management schema'; END IF;
 IF (
SELECT encode(sha256(convert_to(coalesce(jsonb_agg(v ORDER BY v::text),'[]')::text,
 'UTF8')),'hex') FROM (
 SELECT jsonb_build_array('relation',c.relname,c.relkind::text,
  pg_get_userbyid(c.relowner),c.relrowsecurity,c.relforcerowsecurity) v
 FROM pg_class c WHERE c.relnamespace='public'::regnamespace AND c.relkind IN ('r','S')
 UNION ALL SELECT jsonb_build_array('column',c.relname,a.attnum,a.attname,
  format_type(a.atttypid,a.atttypmod),a.attnotnull,a.attidentity::text,
  a.attgenerated::text,co.collname,pg_get_expr(d.adbin,d.adrelid))
 FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid
 LEFT JOIN pg_attrdef d ON d.adrelid=c.oid AND d.adnum=a.attnum
 LEFT JOIN pg_collation co ON co.oid=a.attcollation
 WHERE c.relnamespace='public'::regnamespace AND c.relkind='r'
 AND a.attnum>0 AND NOT a.attisdropped
 UNION ALL SELECT jsonb_build_array('constraint',c.relname,k.conname,
  pg_get_constraintdef(k.oid),k.convalidated)
 FROM pg_constraint k JOIN pg_class c ON c.oid=k.conrelid
 WHERE c.relnamespace='public'::regnamespace
 UNION ALL SELECT jsonb_build_array('index',c.relname,pg_get_indexdef(i.indexrelid),
  i.indisvalid,i.indisready,i.indislive)
 FROM pg_index i JOIN pg_class c ON c.oid=i.indrelid
 WHERE c.relnamespace='public'::regnamespace
 UNION ALL SELECT jsonb_build_array('trigger',c.relname,t.tgname,t.tgenabled::text,
  pg_get_triggerdef(t.oid))
 FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
 WHERE c.relnamespace='public'::regnamespace AND NOT t.tgisinternal
 UNION ALL SELECT jsonb_build_array('routine',p.oid::regprocedure::text,
  pg_get_userbyid(p.proowner),pg_get_functiondef(p.oid))
 FROM pg_proc p WHERE p.pronamespace='public'::regnamespace
 UNION ALL SELECT jsonb_build_array('sequence',c.relname,format_type(s.seqtypid,NULL),
  s.seqstart,s.seqincrement,s.seqmax,s.seqmin,s.seqcache,s.seqcycle,
  t.relname,a.attname,d.deptype::text)
 FROM pg_sequence s JOIN pg_class c ON c.oid=s.seqrelid
 LEFT JOIN pg_depend d ON d.objid=c.oid AND d.classid='pg_class'::regclass
  AND d.refclassid='pg_class'::regclass AND d.deptype='i'
 LEFT JOIN pg_class t ON t.oid=d.refobjid
 LEFT JOIN pg_attribute a ON a.attrelid=t.oid AND a.attnum=d.refobjsubid
 WHERE c.relnamespace='public'::regnamespace
) catalogue
) IS DISTINCT FROM '535cacb140a3a1753b5cf27e2eadcb80bc272a9b12772defd3936a3edc6c2209'
 THEN RAISE EXCEPTION 'management catalogue mismatch'; END IF;
 IF EXISTS(SELECT FROM pg_proc p,
  LATERAL aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) x
  WHERE p.pronamespace='public'::regnamespace AND x.grantee<>p.proowner
  AND (x.is_grantable OR x.privilege_type<>'EXECUTE' OR NOT (
   (x.grantee='birja_app'::regrole AND p.oid::regprocedure::text IN
    ('assert_stock_execution_current(bigint,bigint,jsonb)',
     'create_portfolio(bigint,uuid,text,text)','initialize_portfolio(bigint)',
     'update_portfolio_metadata(bigint,bigint,text,text,boolean,boolean)')) OR
   (x.grantee='birja_scheduler'::regrole AND p.oid::regprocedure::text IN
    ('apply_stock_dividend(bigint,bigint,text,text)','record_stock_dividend_hold(bigint,text)',
     'lock_stock_portfolio_roots(bigint)')) OR
   (x.grantee='birja_action_operator'::regrole AND p.proname='apply_stock_action_resolution'))))
 THEN RAISE EXCEPTION 'management routine ACL mismatch'; END IF;
END $management_identity$;


-- Independent complete0023 identity; qualified earlier branches remain unchanged.

DO $closure_identity$
BEGIN
 IF (SELECT version_num FROM public.alembic_version)<>'0023' THEN RETURN; END IF;
 IF (SELECT count(*)<>1 OR NOT bool_and(version_num='0023') FROM public.alembic_version)
 THEN RAISE EXCEPTION 'management final revision required'; END IF;
 IF EXISTS(SELECT FROM pg_roles WHERE rolname IN
  ('birja_app','birja_scheduler','birja_migrator','birja_action_operator')
  AND (rolinherit OR rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls))
 OR (SELECT count(*) FROM pg_roles WHERE rolname IN
  ('birja_app','birja_scheduler','birja_migrator','birja_action_operator'))<>4
 OR EXISTS(SELECT FROM pg_auth_members m JOIN pg_roles r ON
  r.oid=m.roleid OR r.oid=m.member WHERE r.rolname IN
  ('birja_app','birja_scheduler','birja_migrator','birja_action_operator'))
 OR EXISTS(SELECT FROM pg_roles WHERE rolname='birja_action_operator' AND rolcanlogin)
 THEN RAISE EXCEPTION 'unsafe management roles'; END IF;
 IF EXISTS(SELECT FROM pg_rewrite r JOIN pg_class c ON c.oid=r.ev_class
  WHERE c.relnamespace='public'::regnamespace)
 THEN RAISE EXCEPTION 'unexpected management rewrite rule'; END IF;
 IF EXISTS(SELECT FROM pg_database d JOIN pg_roles r ON r.oid=d.datdba
  WHERE d.datname=current_database() AND r.rolname IN
  ('birja_app','birja_scheduler','birja_migrator','birja_action_operator'))
 OR EXISTS(SELECT FROM pg_namespace n JOIN pg_roles r ON r.oid=n.nspowner
  WHERE n.nspname='public' AND r.rolname IN
  ('birja_app','birja_scheduler','birja_migrator','birja_action_operator'))
 THEN RAISE EXCEPTION 'unsafe management database/schema ownership'; END IF;
 IF EXISTS(SELECT FROM pg_namespace n,
  LATERAL aclexplode(coalesce(n.nspacl,acldefault('n',n.nspowner))) x
  WHERE n.nspname='public' AND x.privilege_type='CREATE' AND
  x.grantee IN (0,'birja_app'::regrole,'birja_scheduler'::regrole))
 OR has_schema_privilege('birja_app','public','CREATE')
 OR has_schema_privilege('birja_scheduler','public','CREATE')
 THEN RAISE EXCEPTION 'unsafe management schema'; END IF;
 IF (
SELECT encode(sha256(convert_to(coalesce(jsonb_agg(v ORDER BY v::text),'[]')::text,
 'UTF8')),'hex') FROM (
 SELECT jsonb_build_array('relation',c.relname,c.relkind::text,
  pg_get_userbyid(c.relowner),c.relrowsecurity,c.relforcerowsecurity) v
 FROM pg_class c WHERE c.relnamespace='public'::regnamespace AND c.relkind IN ('r','S')
 UNION ALL SELECT jsonb_build_array('column',c.relname,a.attnum,a.attname,
  format_type(a.atttypid,a.atttypmod),a.attnotnull,a.attidentity::text,
  a.attgenerated::text,co.collname,pg_get_expr(d.adbin,d.adrelid))
 FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid
 LEFT JOIN pg_attrdef d ON d.adrelid=c.oid AND d.adnum=a.attnum
 LEFT JOIN pg_collation co ON co.oid=a.attcollation
 WHERE c.relnamespace='public'::regnamespace AND c.relkind='r'
 AND a.attnum>0 AND NOT a.attisdropped
 UNION ALL SELECT jsonb_build_array('constraint',c.relname,k.conname,
  pg_get_constraintdef(k.oid),k.convalidated)
 FROM pg_constraint k JOIN pg_class c ON c.oid=k.conrelid
 WHERE c.relnamespace='public'::regnamespace
 UNION ALL SELECT jsonb_build_array('index',c.relname,pg_get_indexdef(i.indexrelid),
  i.indisvalid,i.indisready,i.indislive)
 FROM pg_index i JOIN pg_class c ON c.oid=i.indrelid
 WHERE c.relnamespace='public'::regnamespace
 UNION ALL SELECT jsonb_build_array('trigger',c.relname,t.tgname,t.tgenabled::text,
  pg_get_triggerdef(t.oid))
 FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
 WHERE c.relnamespace='public'::regnamespace AND NOT t.tgisinternal
 UNION ALL SELECT jsonb_build_array('routine',p.oid::regprocedure::text,
  pg_get_userbyid(p.proowner),pg_get_functiondef(p.oid))
 FROM pg_proc p WHERE p.pronamespace='public'::regnamespace
 UNION ALL SELECT jsonb_build_array('sequence',c.relname,format_type(s.seqtypid,NULL),
  s.seqstart,s.seqincrement,s.seqmax,s.seqmin,s.seqcache,s.seqcycle,
  t.relname,a.attname,d.deptype::text)
 FROM pg_sequence s JOIN pg_class c ON c.oid=s.seqrelid
 LEFT JOIN pg_depend d ON d.objid=c.oid AND d.classid='pg_class'::regclass
  AND d.refclassid='pg_class'::regclass AND d.deptype='i'
 LEFT JOIN pg_class t ON t.oid=d.refobjid
 LEFT JOIN pg_attribute a ON a.attrelid=t.oid AND a.attnum=d.refobjsubid
 WHERE c.relnamespace='public'::regnamespace

 UNION ALL SELECT jsonb_build_array('rule',c.relname,r.rulename,r.ev_enabled::text,
  pg_get_ruledef(r.oid)) FROM pg_rewrite r JOIN pg_class c ON c.oid=r.ev_class
  WHERE c.relnamespace='public'::regnamespace
 UNION ALL SELECT jsonb_build_array('policy',schemaname,tablename,policyname,
  permissive,roles,cmd,qual,with_check) FROM pg_policies WHERE schemaname='public'
 UNION ALL SELECT jsonb_build_array('other_relation',c.relname,c.relkind::text,
  pg_get_userbyid(c.relowner)) FROM pg_class c
  WHERE c.relnamespace='public'::regnamespace AND c.relkind NOT IN ('r','S','i','I')
) catalogue
) IS DISTINCT FROM '3a7e0dbe6a908890a1e0e493aa025938b8f03dbd84cf5f799ea0a1895dc164ec'
 THEN RAISE EXCEPTION 'management catalogue mismatch'; END IF;
 IF EXISTS(SELECT FROM pg_proc p,
  LATERAL aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) x
  WHERE p.pronamespace='public'::regnamespace AND x.grantee<>p.proowner
  AND (x.is_grantable OR x.privilege_type<>'EXECUTE' OR NOT (
   (x.grantee='birja_app'::regrole AND p.oid::regprocedure::text IN
    ('assert_stock_execution_current(bigint,bigint,jsonb)','close_portfolio(bigint,bigint,uuid,text,text)',
     'create_portfolio(bigint,uuid,text,text)','initialize_portfolio(bigint)',
     'update_portfolio_metadata(bigint,bigint,text,text,boolean,boolean)')) OR
   (x.grantee='birja_scheduler'::regrole AND p.oid::regprocedure::text IN
    ('apply_stock_dividend(bigint,bigint,text,text)','record_stock_dividend_hold(bigint,text)',
     'lock_stock_portfolio_roots(bigint)')) OR
   (x.grantee='birja_action_operator'::regrole AND p.proname='apply_stock_action_resolution'))))
 THEN RAISE EXCEPTION 'management routine ACL mismatch'; END IF;

 IF EXISTS(SELECT FROM pg_default_acl d,
  LATERAL aclexplode(d.defaclacl) x WHERE d.defaclrole='birja_migrator'::regrole
  AND x.grantee<>d.defaclrole) THEN
  RAISE EXCEPTION 'unexpected closure default privileges'; END IF;
 IF (
SELECT encode(sha256(convert_to(coalesce(jsonb_agg(v ORDER BY v::text),'[]')::text,
 'UTF8')),'hex') FROM (
 SELECT jsonb_build_array('relation',c.relname,coalesce(r.rolname,'PUBLIC'),
  x.privilege_type,x.is_grantable) v
 FROM pg_class c CROSS JOIN LATERAL aclexplode(coalesce(c.relacl,
  acldefault(CASE WHEN c.relkind='S' THEN 'S'::"char" ELSE 'r'::"char" END,c.relowner))) x
 LEFT JOIN pg_roles r ON r.oid=x.grantee
 WHERE c.relnamespace='public'::regnamespace AND c.relkind IN ('r','S')
 AND x.grantee<>c.relowner
 UNION ALL SELECT jsonb_build_array('column',c.relname,a.attname,
  coalesce(r.rolname,'PUBLIC'),x.privilege_type,x.is_grantable)
 FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid
 CROSS JOIN LATERAL aclexplode(a.attacl) x LEFT JOIN pg_roles r ON r.oid=x.grantee
 WHERE c.relnamespace='public'::regnamespace AND a.attnum>0 AND NOT a.attisdropped
 AND x.grantee<>c.relowner
 UNION ALL SELECT jsonb_build_array('routine',p.oid::regprocedure::text,
  coalesce(r.rolname,'PUBLIC'),x.privilege_type,x.is_grantable)
 FROM pg_proc p CROSS JOIN LATERAL aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) x
 LEFT JOIN pg_roles r ON r.oid=x.grantee
 WHERE p.pronamespace='public'::regnamespace AND x.grantee<>p.proowner
) privileges
) NOT IN ('6dfc328bda8577360c8a2994cd5c1c00bd1cae1cbd542be6c1b3a0f3c4f71d76','71896f41a9310ada0af0961b78e78f5364654f1513c11bf9310c250ad545f748') THEN
  RAISE EXCEPTION 'unexpected closure privileges'; END IF;
 IF EXISTS(SELECT FROM public.accounts a
  FULL JOIN public.portfolio_lifecycle_closures c ON c.portfolio_id=a.id
  WHERE (a.closed_at IS NULL)<>(c.id IS NULL)
   OR (c.id IS NOT NULL AND (c.user_id,c.closed_at) IS DISTINCT FROM
      (a.user_id,a.closed_at)))
 OR EXISTS(SELECT FROM public.portfolio_lifecycle_closures c
  LEFT JOIN public.portfolio_closure_intents i ON i.id=c.intent_id
  JOIN public.accounts a ON a.id=c.portfolio_id
  WHERE c.policy_version<>'freeze_at_closure_v1'
   OR (c.provenance='owner_confirmation' AND
    (i.id IS NULL OR i.outcome<>'closed'
     OR c.confirmation_name IS DISTINCT FROM a.name
     OR (i.user_id,i.portfolio_id,i.confirmation_name,i.policy_version,i.recorded_at)
      IS DISTINCT FROM
      (c.user_id,c.portfolio_id,c.confirmation_name,c.policy_version,c.closed_at)))
   OR (c.provenance='retained_boundary' AND
      (c.intent_id IS NOT NULL OR c.confirmation_name IS NOT NULL)))
 OR EXISTS(SELECT FROM public.portfolio_closure_intents i
  LEFT JOIN public.portfolio_lifecycle_closures c ON c.intent_id=i.id
  WHERE (i.outcome='closed')<>(c.id IS NOT NULL))
 OR EXISTS(SELECT FROM public.portfolio_stock_closures s
  LEFT JOIN public.portfolio_lifecycle_closures c ON c.portfolio_id=s.portfolio_id
  WHERE c.id IS NULL OR (s.user_id,s.closed_at) IS DISTINCT FROM (c.user_id,c.closed_at)
   OR s.closing_sequence<>coalesce((SELECT max(m.sequence)
     FROM public.stock_ownership_movements m WHERE m.coin_id=s.coin_id
      AND m.recorded_at<=s.closed_at),0)
   OR s.unit_epoch<>(SELECT count(*) FROM public.stock_split_applications a
     WHERE a.coin_id=s.coin_id AND a.processed_at<=s.closed_at))
 OR EXISTS(SELECT FROM public.portfolio_lifecycle_closures c
  CROSS JOIN LATERAL (SELECT m.coin_id FROM public.stock_ownership_movements m
    WHERE m.portfolio_id=c.portfolio_id
   UNION SELECT h.coin_id FROM public.holdings h JOIN public.coins i ON i.id=h.coin_id
    WHERE h.portfolio_id=c.portfolio_id AND i.asset_class='stock') member
  WHERE NOT EXISTS(SELECT FROM public.portfolio_stock_closures s
    WHERE s.portfolio_id=c.portfolio_id AND s.coin_id=member.coin_id))
 THEN RAISE EXCEPTION 'closure lifecycle evidence mismatch'; END IF;
END $closure_identity$;


\if :apply
DO $roles$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='birja_migrator') THEN
    CREATE ROLE birja_migrator LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='birja_app') THEN
    CREATE ROLE birja_app LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='birja_scheduler') THEN
    CREATE ROLE birja_scheduler LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='birja_action_operator') THEN
    CREATE ROLE birja_action_operator NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
  END IF;
END
$roles$;
-- This explicitly updates existing role passwords; changing env alone does not.
ALTER ROLE birja_app PASSWORD :'app_password';
ALTER ROLE birja_scheduler PASSWORD :'scheduler_password';
ALTER ROLE birja_migrator PASSWORD :'migrator_password';
ALTER ROLE birja_app SET statement_timeout = '30s';
ALTER ROLE birja_app SET idle_in_transaction_session_timeout = '30s';
ALTER ROLE birja_scheduler SET statement_timeout = '30s';
ALTER ROLE birja_scheduler SET idle_in_transaction_session_timeout = '30s';
ALTER ROLE birja_migrator SET statement_timeout = '120s';
ALTER ROLE birja_migrator SET idle_in_transaction_session_timeout = '30s';
ALTER ROLE birja_migrator SET lock_timeout = '5s';
REVOKE CREATE ON SCHEMA public FROM PUBLIC, birja_app, birja_scheduler;
GRANT USAGE ON SCHEMA public TO birja_migrator, birja_app, birja_scheduler;
GRANT CREATE ON SCHEMA public TO birja_migrator;
GRANT CONNECT ON DATABASE :"db_name" TO birja_migrator, birja_app, birja_scheduler;
REVOKE CREATE, TEMPORARY ON DATABASE :"db_name" FROM PUBLIC, birja_migrator, birja_app, birja_scheduler;
DO $transfer$
DECLARE t text; s record;
BEGIN
  FOREACH t IN ARRAY ARRAY['users','accounts','auth_sessions','refresh_tokens','coins','prices','holdings','trades','alembic_version'] || CASE WHEN (SELECT version_num FROM public.alembic_version) IN ('0009','0010','0011','0012','0013','0014','0017','0020') THEN ARRAY['stock_instruments','stock_quotes','stock_sessions','stock_data_admissions'] ELSE ARRAY[]::text[] END || CASE WHEN (SELECT version_num FROM public.alembic_version) IN ('0011','0012','0013','0014','0017','0020') THEN ARRAY['stock_action_events','stock_action_sources','stock_action_revisions','stock_action_observations','stock_action_state','stock_ownership_movements','stock_split_applications','stock_dividend_entitlements','stock_action_resolutions'] ELSE ARRAY[]::text[] END || CASE WHEN (SELECT version_num FROM public.alembic_version) IN ('0013','0014','0017','0020') THEN ARRAY['stock_fill_facts','stock_status_evidence'] ELSE ARRAY[]::text[] END || CASE WHEN (SELECT version_num FROM public.alembic_version) IN ('0014','0017','0020') THEN ARRAY['stock_dividend_payments','stock_dividend_decisions'] ELSE ARRAY[]::text[] END || CASE WHEN (SELECT version_num FROM public.alembic_version)IN ('0017','0020') THEN ARRAY['portfolio_stock_closures'] ELSE ARRAY[]::text[] END || CASE WHEN (SELECT version_num FROM public.alembic_version)='0020' THEN ARRAY['portfolio_creations','portfolio_initializations'] ELSE ARRAY[]::text[] END LOOP
    -- ALTER TABLE transfers its identity sequences as a dependency. Never
    -- ALTER an identity-owned sequence independently or reassign other objects.
    EXECUTE format('ALTER TABLE public.%I OWNER TO birja_migrator',t);
    EXECUTE format('REVOKE SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER,MAINTAIN ON TABLE public.%I FROM PUBLIC,birja_app,birja_scheduler',t);
    FOR s IN SELECT seq.oid::regclass AS seq_name,seq.relowner
      FROM pg_class c JOIN pg_depend d ON d.refobjid=c.oid AND d.deptype='i'
      JOIN pg_class seq ON seq.oid=d.objid AND seq.relkind='S'
      WHERE c.oid=to_regclass(format('public.%I',t)) LOOP
      IF s.relowner <> (SELECT oid FROM pg_roles WHERE rolname='birja_migrator') THEN
        RAISE EXCEPTION 'identity ownership did not follow table';
      END IF;
      EXECUTE format('REVOKE USAGE,SELECT,UPDATE ON SEQUENCE %s FROM PUBLIC,birja_app,birja_scheduler',s.seq_name);
    END LOOP;
  END LOOP;
END
$transfer$;
GRANT SELECT, INSERT ON users TO birja_app;
GRANT SELECT, INSERT, UPDATE ON accounts, auth_sessions, refresh_tokens, holdings TO birja_app;
GRANT SELECT, INSERT ON trades TO birja_app;
GRANT SELECT ON coins, prices TO birja_app;
GRANT SELECT ON coins TO birja_scheduler;
GRANT SELECT, INSERT, UPDATE ON prices TO birja_scheduler;
GRANT USAGE ON SEQUENCE users_id_seq,accounts_id_seq,auth_sessions_id_seq,refresh_tokens_id_seq,holdings_id_seq,trades_id_seq TO birja_app;
-- Mirror revision0009 exactly; legacy schemas must never parse absent objects.
DO $stock_grants$
BEGIN
  IF (SELECT version_num FROM public.alembic_version) IN ('0009','0010','0011','0012','0013','0014','0017','0020') THEN
    GRANT SELECT ON stock_instruments,stock_quotes,stock_sessions,stock_data_admissions TO birja_app;
    GRANT SELECT ON stock_instruments,stock_data_admissions TO birja_scheduler;
    GRANT SELECT,INSERT,UPDATE ON stock_quotes,stock_sessions TO birja_scheduler;
    GRANT USAGE ON SEQUENCE stock_sessions_id_seq TO birja_scheduler;
  END IF;
END
$stock_grants$;
DO $action_grants$
    DECLARE t text; r text;
    BEGIN
      IF (SELECT version_num FROM public.alembic_version) NOT IN ('0011','0012','0013','0014','0017','0020') THEN RETURN; END IF;
      IF NOT EXISTS(SELECT FROM pg_roles WHERE rolname='birja_action_operator') THEN
        IF NOT EXISTS(SELECT FROM pg_roles WHERE rolname=current_user
                      AND (rolsuper OR rolcreaterole)) THEN
          RAISE EXCEPTION 'preprovision birja_action_operator before restricted 0011 upgrade';
        END IF;
        CREATE ROLE birja_action_operator NOLOGIN NOINHERIT NOSUPERUSER
          NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
      END IF;
      IF EXISTS(SELECT FROM pg_roles WHERE rolname='birja_action_operator'
                AND (rolcanlogin OR rolinherit OR rolsuper OR rolcreatedb OR rolcreaterole
                     OR rolreplication OR rolbypassrls)) OR
         EXISTS(SELECT FROM pg_auth_members WHERE
                member=(SELECT oid FROM pg_roles WHERE rolname='birja_action_operator') OR
                roleid=(SELECT oid FROM pg_roles WHERE rolname='birja_action_operator')) THEN
        RAISE EXCEPTION 'unsafe action operator attributes or membership';
      END IF;
      FOREACH t IN ARRAY ARRAY['stock_action_events','stock_action_sources',
        'stock_action_revisions','stock_action_observations','stock_action_state',
        'stock_ownership_movements','stock_split_applications',
        'stock_dividend_entitlements','stock_action_resolutions'] LOOP
        EXECUTE format('REVOKE ALL ON TABLE public.%I FROM PUBLIC',t);
        FOREACH r IN ARRAY ARRAY['birja_app','birja_scheduler','birja_action_operator'] LOOP
          IF EXISTS(SELECT FROM pg_roles WHERE rolname=r) THEN
            EXECUTE format('REVOKE ALL ON TABLE public.%I FROM %I',t,r);
            EXECUTE format('GRANT SELECT ON TABLE public.%I TO %I',t,r);
          END IF;
        END LOOP;
        IF t <> 'stock_action_state' THEN
          EXECUTE format('REVOKE ALL ON SEQUENCE public.%I FROM PUBLIC',t||'_id_seq');
          FOREACH r IN ARRAY ARRAY['birja_app','birja_scheduler','birja_action_operator'] LOOP
            IF EXISTS(SELECT FROM pg_roles WHERE rolname=r) THEN
              EXECUTE format('REVOKE ALL ON SEQUENCE public.%I FROM %I',t||'_id_seq',r);
            END IF;
          END LOOP;
        END IF;
      END LOOP;
      GRANT USAGE ON SCHEMA public TO birja_action_operator;
      GRANT SELECT ON stock_instruments,stock_data_admissions,stock_quotes,stock_sessions
        TO birja_action_operator;
      IF EXISTS(SELECT FROM pg_roles WHERE rolname='birja_app') THEN
        GRANT INSERT ON stock_ownership_movements TO birja_app;
        GRANT USAGE ON SEQUENCE stock_ownership_movements_id_seq TO birja_app;
      END IF;
      IF EXISTS(SELECT FROM pg_roles WHERE rolname='birja_scheduler') THEN
        GRANT INSERT ON stock_action_events,stock_action_sources,stock_action_revisions,
          stock_action_observations,stock_action_state,stock_ownership_movements,
          stock_split_applications,stock_dividend_entitlements TO birja_scheduler;
        GRANT UPDATE(current_revision_id) ON stock_action_events TO birja_scheduler;
        GRANT UPDATE ON stock_action_state TO birja_scheduler;
        GRANT USAGE ON SEQUENCE stock_action_events_id_seq,stock_action_sources_id_seq,
          stock_action_revisions_id_seq,stock_action_observations_id_seq,
          stock_ownership_movements_id_seq,stock_split_applications_id_seq,
          stock_dividend_entitlements_id_seq TO birja_scheduler;
        REVOKE ALL ON holdings FROM birja_scheduler;
        GRANT SELECT,UPDATE(quantity) ON holdings TO birja_scheduler;
        GRANT SELECT(id,coin_id,user_id,side,quantity,cash_delta) ON trades TO birja_scheduler;
      END IF;
    END $action_grants$;
DO $resolution_grants$
BEGIN
  IF (SELECT version_num FROM public.alembic_version) IN ('0012','0013','0014','0017','0020') THEN
    GRANT SELECT(id,symbol,asset_class,is_active,sort_order) ON public.coins TO birja_action_operator;
    ALTER FUNCTION public.apply_stock_action_resolution(bigint,bigint,bigint,bigint,bigint,text,text,text,jsonb,text) OWNER TO birja_migrator;
    REVOKE ALL ON FUNCTION public.apply_stock_action_resolution(bigint,bigint,bigint,bigint,bigint,text,text,text,jsonb,text) FROM PUBLIC,birja_app,birja_scheduler;
    GRANT EXECUTE ON FUNCTION public.apply_stock_action_resolution(bigint,bigint,bigint,bigint,bigint,text,text,text,jsonb,text) TO birja_action_operator;
  END IF;
END
$resolution_grants$;
DO $execution_grants$
BEGIN
 IF (SELECT version_num FROM public.alembic_version) IN ('0013','0014','0017','0020') THEN
   ALTER FUNCTION public.check_stock_fill_integrity() OWNER TO birja_migrator;
   ALTER FUNCTION public.assert_stock_execution_current(bigint,bigint,jsonb) OWNER TO birja_migrator;
   REVOKE ALL ON FUNCTION public.check_stock_fill_integrity() FROM PUBLIC,birja_app,birja_scheduler;
   REVOKE ALL ON FUNCTION public.assert_stock_execution_current(bigint,bigint,jsonb) FROM PUBLIC,birja_app,birja_scheduler;
   GRANT SELECT,INSERT ON public.stock_fill_facts TO birja_app;
   GRANT SELECT ON public.stock_status_evidence TO birja_app;
   GRANT SELECT,INSERT,UPDATE ON public.stock_status_evidence TO birja_scheduler;
   GRANT EXECUTE ON FUNCTION public.assert_stock_execution_current(bigint,bigint,jsonb) TO birja_app;
 END IF;
END $execution_grants$;
DO $dividend_grants$
BEGIN
 IF (SELECT version_num FROM public.alembic_version) IN ('0014','0017','0020') THEN
   REVOKE ALL ON public.stock_dividend_payments,public.stock_dividend_decisions
     FROM PUBLIC,birja_app,birja_scheduler;
   GRANT SELECT ON public.stock_dividend_payments,public.stock_dividend_decisions
     TO birja_app,birja_scheduler;
   REVOKE ALL ON SEQUENCE public.stock_dividend_payments_id_seq,
     public.stock_dividend_decisions_id_seq FROM PUBLIC,birja_app,birja_scheduler;
   REVOKE ALL ON FUNCTION public.stock_dividend_authority(bigint,bigint,text,text,boolean,jsonb),
     public.reject_stock_dividend_mutation(),
     public.apply_stock_dividend(bigint,bigint,text,text),
     public.record_stock_dividend_hold(bigint,text) FROM PUBLIC,birja_app,birja_scheduler;
   GRANT EXECUTE ON FUNCTION public.apply_stock_dividend(bigint,bigint,text,text),
     public.record_stock_dividend_hold(bigint,text) TO birja_scheduler;
 END IF;
END $dividend_grants$;
DO $portfolio_grants$ BEGIN
 IF (SELECT version_num FROM public.alembic_version)<>'0017' THEN RETURN; END IF;

GRANT USAGE ON SCHEMA public TO birja_app,birja_scheduler;
GRANT SELECT,INSERT ON public.users TO birja_app;
GRANT SELECT,INSERT,UPDATE ON public.auth_sessions,public.refresh_tokens TO birja_app;
GRANT SELECT ON public.coins,public.prices,public.trades,public.stock_instruments,
 public.stock_quotes,public.stock_sessions,public.stock_data_admissions,
 public.stock_action_events,public.stock_action_sources,public.stock_action_revisions,
 public.stock_action_observations,public.stock_action_state,public.stock_split_applications,
 public.stock_ownership_movements,public.stock_action_resolutions,public.stock_fill_facts,
 public.stock_status_evidence TO birja_app,birja_scheduler;
GRANT INSERT ON public.trades,public.stock_fill_facts,public.stock_ownership_movements
 TO birja_app;
GRANT SELECT,INSERT,UPDATE ON public.prices,public.stock_quotes,public.stock_sessions,
 public.stock_action_state,public.stock_status_evidence TO birja_scheduler;
GRANT INSERT ON public.stock_action_events,public.stock_action_sources,
 public.stock_action_revisions,public.stock_action_observations,
 public.stock_split_applications,public.stock_ownership_movements,
 public.stock_dividend_entitlements TO birja_scheduler;
GRANT UPDATE(current_revision_id) ON public.stock_action_events TO birja_scheduler;
GRANT USAGE ON SEQUENCE public.users_id_seq,public.accounts_id_seq,
 public.auth_sessions_id_seq,public.refresh_tokens_id_seq,public.holdings_id_seq,
 public.trades_id_seq,public.stock_ownership_movements_id_seq TO birja_app;
GRANT USAGE ON SEQUENCE public.stock_sessions_id_seq,public.stock_action_events_id_seq,
 public.stock_action_sources_id_seq,public.stock_action_revisions_id_seq,
 public.stock_action_observations_id_seq,public.stock_split_applications_id_seq,
 public.stock_ownership_movements_id_seq,public.stock_dividend_entitlements_id_seq
 TO birja_scheduler;
REVOKE ALL ON public.stock_dividend_payments,public.stock_dividend_decisions
 FROM PUBLIC,birja_app,birja_scheduler;
REVOKE ALL ON SEQUENCE public.stock_dividend_payments_id_seq,
 public.stock_dividend_decisions_id_seq FROM PUBLIC,birja_app,birja_scheduler;
REVOKE ALL ON public.accounts,public.holdings,public.portfolio_stock_closures
 FROM PUBLIC,birja_app,birja_scheduler;
REVOKE UPDATE(id,user_id,cash,starting_cash,created_at,name,closed_at)
 ON public.accounts FROM PUBLIC,birja_app,birja_scheduler;
REVOKE UPDATE(id,user_id,coin_id,quantity,cost_basis,portfolio_id)
 ON public.holdings FROM PUBLIC,birja_app,birja_scheduler;
GRANT SELECT,INSERT ON public.accounts,public.holdings TO birja_app;
GRANT UPDATE(cash) ON public.accounts TO birja_app;
GRANT UPDATE(quantity,cost_basis) ON public.holdings TO birja_app;
GRANT SELECT ON public.accounts,public.holdings TO birja_scheduler;
GRANT UPDATE(quantity) ON public.holdings TO birja_scheduler;
GRANT SELECT ON public.portfolio_stock_closures,public.alembic_version,
 public.stock_dividend_entitlements,public.stock_dividend_payments,
 public.stock_dividend_decisions TO birja_app,birja_scheduler;
GRANT SELECT ON public.trades TO birja_scheduler;
REVOKE ALL ON FUNCTION public.check_portfolio_financial_write(),
 public.check_stock_split_digest_version(),public.lock_stock_portfolio_roots(bigint)
 FROM PUBLIC,birja_app,birja_scheduler;
GRANT EXECUTE ON FUNCTION public.lock_stock_portfolio_roots(bigint) TO birja_scheduler;
GRANT EXECUTE ON FUNCTION public.assert_stock_execution_current(bigint,bigint,jsonb)
 TO birja_app;
REVOKE ALL ON FUNCTION public.stock_dividend_authority(bigint,bigint,text,text,boolean,jsonb),
 public.reject_stock_dividend_mutation(),public.apply_stock_dividend(bigint,bigint,text,text),
 public.record_stock_dividend_hold(bigint,text) FROM PUBLIC,birja_app,birja_scheduler;
GRANT EXECUTE ON FUNCTION public.apply_stock_dividend(bigint,bigint,text,text),
 public.record_stock_dividend_hold(bigint,text) TO birja_scheduler;

END $portfolio_grants$;

DO $management_grants$
BEGIN
 IF (SELECT version_num FROM public.alembic_version)<>'0020' THEN RETURN; END IF;

DO $management_reset$
DECLARE obj record; col record;
BEGIN
 FOR obj IN SELECT c.oid,c.relname,c.relkind FROM pg_class c
  WHERE c.relnamespace='public'::regnamespace AND c.relkind IN ('r','S') LOOP
  IF obj.relkind='r' THEN
   EXECUTE format('REVOKE ALL ON TABLE public.%I FROM PUBLIC,birja_app,'
    'birja_scheduler,birja_action_operator',obj.relname);
   FOR col IN SELECT attname FROM pg_attribute WHERE attrelid=obj.oid
    AND attnum>0 AND NOT attisdropped LOOP
    EXECUTE format('REVOKE ALL (%I) ON TABLE public.%I FROM PUBLIC,birja_app,'
     'birja_scheduler,birja_action_operator',col.attname,obj.relname);
   END LOOP;
  ELSE
   EXECUTE format('REVOKE ALL ON SEQUENCE public.%I FROM PUBLIC,birja_app,'
    'birja_scheduler,birja_action_operator',obj.relname);
  END IF;
 END LOOP;
 FOR obj IN SELECT p.oid::regprocedure::text AS signature FROM pg_proc p
  WHERE p.pronamespace='public'::regnamespace LOOP
  EXECUTE format('REVOKE ALL ON FUNCTION %s FROM PUBLIC,birja_app,'
   'birja_scheduler,birja_action_operator',obj.signature);
 END LOOP;
END $management_reset$;

GRANT USAGE ON SCHEMA public TO birja_app,birja_scheduler;
GRANT SELECT,INSERT ON public.users TO birja_app;
GRANT SELECT,INSERT,UPDATE ON public.auth_sessions,public.refresh_tokens TO birja_app;
GRANT SELECT ON public.coins,public.prices,public.trades,public.stock_instruments,
 public.stock_quotes,public.stock_sessions,public.stock_data_admissions,
 public.stock_action_events,public.stock_action_sources,public.stock_action_revisions,
 public.stock_action_observations,public.stock_action_state,public.stock_split_applications,
 public.stock_ownership_movements,public.stock_action_resolutions,public.stock_fill_facts,
 public.stock_status_evidence TO birja_app,birja_scheduler;
GRANT INSERT ON public.trades,public.stock_fill_facts,public.stock_ownership_movements
 TO birja_app;
GRANT SELECT,INSERT,UPDATE ON public.prices,public.stock_quotes,public.stock_sessions,
 public.stock_action_state,public.stock_status_evidence TO birja_scheduler;
GRANT INSERT ON public.stock_action_events,public.stock_action_sources,
 public.stock_action_revisions,public.stock_action_observations,
 public.stock_split_applications,public.stock_ownership_movements,
 public.stock_dividend_entitlements TO birja_scheduler;
GRANT UPDATE(current_revision_id) ON public.stock_action_events TO birja_scheduler;
GRANT USAGE ON SEQUENCE public.users_id_seq,public.accounts_id_seq,
 public.auth_sessions_id_seq,public.refresh_tokens_id_seq,public.holdings_id_seq,
 public.trades_id_seq,public.stock_ownership_movements_id_seq TO birja_app;
GRANT USAGE ON SEQUENCE public.stock_sessions_id_seq,public.stock_action_events_id_seq,
 public.stock_action_sources_id_seq,public.stock_action_revisions_id_seq,
 public.stock_action_observations_id_seq,public.stock_split_applications_id_seq,
 public.stock_ownership_movements_id_seq,public.stock_dividend_entitlements_id_seq
 TO birja_scheduler;
REVOKE ALL ON public.stock_dividend_payments,public.stock_dividend_decisions
 FROM PUBLIC,birja_app,birja_scheduler;
REVOKE ALL ON SEQUENCE public.stock_dividend_payments_id_seq,
 public.stock_dividend_decisions_id_seq FROM PUBLIC,birja_app,birja_scheduler;
REVOKE ALL ON public.accounts,public.holdings,public.portfolio_stock_closures
 FROM PUBLIC,birja_app,birja_scheduler;
REVOKE UPDATE(id,user_id,cash,starting_cash,created_at,name,closed_at)
 ON public.accounts FROM PUBLIC,birja_app,birja_scheduler;
REVOKE UPDATE(id,user_id,coin_id,quantity,cost_basis,portfolio_id)
 ON public.holdings FROM PUBLIC,birja_app,birja_scheduler;
GRANT SELECT,INSERT ON public.accounts,public.holdings TO birja_app;
GRANT UPDATE(cash) ON public.accounts TO birja_app;
GRANT UPDATE(quantity,cost_basis) ON public.holdings TO birja_app;
GRANT SELECT ON public.accounts,public.holdings TO birja_scheduler;
GRANT UPDATE(quantity) ON public.holdings TO birja_scheduler;
GRANT SELECT ON public.portfolio_stock_closures,public.alembic_version,
 public.stock_dividend_entitlements,public.stock_dividend_payments,
 public.stock_dividend_decisions TO birja_app,birja_scheduler;
GRANT SELECT ON public.trades TO birja_scheduler;
REVOKE ALL ON FUNCTION public.check_portfolio_financial_write(),
 public.check_stock_split_digest_version(),public.lock_stock_portfolio_roots(bigint)
 FROM PUBLIC,birja_app,birja_scheduler;
GRANT EXECUTE ON FUNCTION public.lock_stock_portfolio_roots(bigint) TO birja_scheduler;
GRANT EXECUTE ON FUNCTION public.assert_stock_execution_current(bigint,bigint,jsonb)
 TO birja_app;
REVOKE ALL ON FUNCTION public.stock_dividend_authority(bigint,bigint,text,text,boolean,jsonb),
 public.reject_stock_dividend_mutation(),public.apply_stock_dividend(bigint,bigint,text,text),
 public.record_stock_dividend_hold(bigint,text) FROM PUBLIC,birja_app,birja_scheduler;
GRANT EXECUTE ON FUNCTION public.apply_stock_dividend(bigint,bigint,text,text),
 public.record_stock_dividend_hold(bigint,text) TO birja_scheduler;

REVOKE ALL ON public.accounts,public.portfolio_creations,public.portfolio_initializations
 FROM PUBLIC,birja_app,birja_scheduler;
REVOKE UPDATE(id,user_id,cash,starting_cash,created_at,name,name_key,description,closed_at)
 ON public.accounts FROM PUBLIC,birja_app,birja_scheduler;
REVOKE UPDATE(id,email,created_at) ON public.users FROM PUBLIC,birja_app,birja_scheduler;
REVOKE UPDATE ON public.users FROM PUBLIC,birja_app,birja_scheduler;
REVOKE ALL ON SEQUENCE public.accounts_id_seq,public.portfolio_creations_id_seq,
 public.portfolio_initializations_id_seq FROM PUBLIC,birja_app,birja_scheduler;
GRANT SELECT ON public.accounts TO birja_app,birja_scheduler;
GRANT UPDATE(cash) ON public.accounts TO birja_app;
REVOKE ALL ON FUNCTION public.portfolio_display_name(text),public.portfolio_name_key(text),
 public.portfolio_description(text),public.check_portfolio_management_metadata(),
 public.create_portfolio(bigint,uuid,text,text),public.initialize_portfolio(bigint),
 public.update_portfolio_metadata(bigint,bigint,text,text,boolean,boolean)
 FROM PUBLIC,birja_app,birja_scheduler;
GRANT EXECUTE ON FUNCTION public.create_portfolio(bigint,uuid,text,text),
 public.initialize_portfolio(bigint),
 public.update_portfolio_metadata(bigint,bigint,text,text,boolean,boolean) TO birja_app;
GRANT USAGE ON SCHEMA public TO birja_action_operator;
GRANT SELECT ON public.stock_action_events,public.stock_action_sources,
 public.stock_action_revisions,public.stock_action_observations,public.stock_action_state,
 public.stock_ownership_movements,public.stock_split_applications,
 public.stock_dividend_entitlements,public.stock_action_resolutions,
 public.stock_instruments,public.stock_data_admissions,public.stock_quotes,public.stock_sessions
 TO birja_action_operator;
GRANT SELECT(id,symbol,asset_class,is_active,sort_order) ON public.coins TO birja_action_operator;
GRANT EXECUTE ON FUNCTION public.apply_stock_action_resolution(
 bigint,bigint,bigint,bigint,bigint,text,text,text,jsonb,text) TO birja_action_operator;

 IF (
SELECT encode(sha256(convert_to(coalesce(jsonb_agg(v ORDER BY v::text),'[]')::text,
 'UTF8')),'hex') FROM (
 SELECT jsonb_build_array('relation',c.relname,coalesce(r.rolname,'PUBLIC'),
  x.privilege_type,x.is_grantable) v
 FROM pg_class c CROSS JOIN LATERAL aclexplode(coalesce(c.relacl,
  acldefault(CASE WHEN c.relkind='S' THEN 'S'::"char" ELSE 'r'::"char" END,c.relowner))) x
 LEFT JOIN pg_roles r ON r.oid=x.grantee
 WHERE c.relnamespace='public'::regnamespace AND c.relkind IN ('r','S')
 AND x.grantee<>c.relowner
 UNION ALL SELECT jsonb_build_array('column',c.relname,a.attname,
  coalesce(r.rolname,'PUBLIC'),x.privilege_type,x.is_grantable)
 FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid
 CROSS JOIN LATERAL aclexplode(a.attacl) x LEFT JOIN pg_roles r ON r.oid=x.grantee
 WHERE c.relnamespace='public'::regnamespace AND a.attnum>0 AND NOT a.attisdropped
 AND x.grantee<>c.relowner
 UNION ALL SELECT jsonb_build_array('routine',p.oid::regprocedure::text,
  coalesce(r.rolname,'PUBLIC'),x.privilege_type,x.is_grantable)
 FROM pg_proc p CROSS JOIN LATERAL aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) x
 LEFT JOIN pg_roles r ON r.oid=x.grantee
 WHERE p.pronamespace='public'::regnamespace AND x.grantee<>p.proowner
) privileges
) IS DISTINCT FROM '041a948470f9692628da43b35263a47bf58f4815310a0793d5eec099fa64c87e' THEN RAISE EXCEPTION 'management final ACL mismatch'; END IF;
END $management_grants$;
DO $closure_grants$ BEGIN
 IF (SELECT version_num FROM public.alembic_version)<>'0023' THEN RETURN; END IF;

DO $management_reset$
DECLARE obj record; col record;
BEGIN
 FOR obj IN SELECT c.oid,c.relname,c.relkind FROM pg_class c
  WHERE c.relnamespace='public'::regnamespace AND c.relkind IN ('r','S') LOOP
  IF obj.relkind='r' THEN
   EXECUTE format('REVOKE ALL ON TABLE public.%I FROM PUBLIC,birja_app,'
    'birja_scheduler,birja_action_operator',obj.relname);
   FOR col IN SELECT attname FROM pg_attribute WHERE attrelid=obj.oid
    AND attnum>0 AND NOT attisdropped LOOP
    EXECUTE format('REVOKE ALL (%I) ON TABLE public.%I FROM PUBLIC,birja_app,'
     'birja_scheduler,birja_action_operator',col.attname,obj.relname);
   END LOOP;
  ELSE
   EXECUTE format('REVOKE ALL ON SEQUENCE public.%I FROM PUBLIC,birja_app,'
    'birja_scheduler,birja_action_operator',obj.relname);
  END IF;
 END LOOP;
 FOR obj IN SELECT p.oid::regprocedure::text AS signature FROM pg_proc p
  WHERE p.pronamespace='public'::regnamespace LOOP
  EXECUTE format('REVOKE ALL ON FUNCTION %s FROM PUBLIC,birja_app,'
   'birja_scheduler,birja_action_operator',obj.signature);
 END LOOP;
END $management_reset$;

GRANT USAGE ON SCHEMA public TO birja_app,birja_scheduler;
GRANT SELECT,INSERT ON public.users TO birja_app;
GRANT SELECT,INSERT,UPDATE ON public.auth_sessions,public.refresh_tokens TO birja_app;
GRANT SELECT ON public.coins,public.prices,public.trades,public.stock_instruments,
 public.stock_quotes,public.stock_sessions,public.stock_data_admissions,
 public.stock_action_events,public.stock_action_sources,public.stock_action_revisions,
 public.stock_action_observations,public.stock_action_state,public.stock_split_applications,
 public.stock_ownership_movements,public.stock_action_resolutions,public.stock_fill_facts,
 public.stock_status_evidence TO birja_app,birja_scheduler;
GRANT INSERT ON public.trades,public.stock_fill_facts,public.stock_ownership_movements
 TO birja_app;
GRANT SELECT,INSERT,UPDATE ON public.prices,public.stock_quotes,public.stock_sessions,
 public.stock_action_state,public.stock_status_evidence TO birja_scheduler;
GRANT INSERT ON public.stock_action_events,public.stock_action_sources,
 public.stock_action_revisions,public.stock_action_observations,
 public.stock_split_applications,public.stock_ownership_movements,
 public.stock_dividend_entitlements TO birja_scheduler;
GRANT UPDATE(current_revision_id) ON public.stock_action_events TO birja_scheduler;
GRANT USAGE ON SEQUENCE public.users_id_seq,public.accounts_id_seq,
 public.auth_sessions_id_seq,public.refresh_tokens_id_seq,public.holdings_id_seq,
 public.trades_id_seq,public.stock_ownership_movements_id_seq TO birja_app;
GRANT USAGE ON SEQUENCE public.stock_sessions_id_seq,public.stock_action_events_id_seq,
 public.stock_action_sources_id_seq,public.stock_action_revisions_id_seq,
 public.stock_action_observations_id_seq,public.stock_split_applications_id_seq,
 public.stock_ownership_movements_id_seq,public.stock_dividend_entitlements_id_seq
 TO birja_scheduler;
REVOKE ALL ON public.stock_dividend_payments,public.stock_dividend_decisions
 FROM PUBLIC,birja_app,birja_scheduler;
REVOKE ALL ON SEQUENCE public.stock_dividend_payments_id_seq,
 public.stock_dividend_decisions_id_seq FROM PUBLIC,birja_app,birja_scheduler;
REVOKE ALL ON public.accounts,public.holdings,public.portfolio_stock_closures
 FROM PUBLIC,birja_app,birja_scheduler;
REVOKE UPDATE(id,user_id,cash,starting_cash,created_at,name,closed_at)
 ON public.accounts FROM PUBLIC,birja_app,birja_scheduler;
REVOKE UPDATE(id,user_id,coin_id,quantity,cost_basis,portfolio_id)
 ON public.holdings FROM PUBLIC,birja_app,birja_scheduler;
GRANT SELECT,INSERT ON public.accounts,public.holdings TO birja_app;
GRANT UPDATE(cash) ON public.accounts TO birja_app;
GRANT UPDATE(quantity,cost_basis) ON public.holdings TO birja_app;
GRANT SELECT ON public.accounts,public.holdings TO birja_scheduler;
GRANT UPDATE(quantity) ON public.holdings TO birja_scheduler;
GRANT SELECT ON public.portfolio_stock_closures,public.alembic_version,
 public.stock_dividend_entitlements,public.stock_dividend_payments,
 public.stock_dividend_decisions TO birja_app,birja_scheduler;
GRANT SELECT ON public.trades TO birja_scheduler;
REVOKE ALL ON FUNCTION public.check_portfolio_financial_write(),
 public.check_stock_split_digest_version(),public.lock_stock_portfolio_roots(bigint)
 FROM PUBLIC,birja_app,birja_scheduler;
GRANT EXECUTE ON FUNCTION public.lock_stock_portfolio_roots(bigint) TO birja_scheduler;
GRANT EXECUTE ON FUNCTION public.assert_stock_execution_current(bigint,bigint,jsonb)
 TO birja_app;
REVOKE ALL ON FUNCTION public.stock_dividend_authority(bigint,bigint,text,text,boolean,jsonb),
 public.reject_stock_dividend_mutation(),public.apply_stock_dividend(bigint,bigint,text,text),
 public.record_stock_dividend_hold(bigint,text) FROM PUBLIC,birja_app,birja_scheduler;
GRANT EXECUTE ON FUNCTION public.apply_stock_dividend(bigint,bigint,text,text),
 public.record_stock_dividend_hold(bigint,text) TO birja_scheduler;

REVOKE ALL ON public.accounts,public.portfolio_creations,public.portfolio_initializations
 FROM PUBLIC,birja_app,birja_scheduler;
REVOKE UPDATE(id,user_id,cash,starting_cash,created_at,name,name_key,description,closed_at)
 ON public.accounts FROM PUBLIC,birja_app,birja_scheduler;
REVOKE UPDATE(id,email,created_at) ON public.users FROM PUBLIC,birja_app,birja_scheduler;
REVOKE UPDATE ON public.users FROM PUBLIC,birja_app,birja_scheduler;
REVOKE ALL ON SEQUENCE public.accounts_id_seq,public.portfolio_creations_id_seq,
 public.portfolio_initializations_id_seq FROM PUBLIC,birja_app,birja_scheduler;
GRANT SELECT ON public.accounts TO birja_app,birja_scheduler;
GRANT UPDATE(cash) ON public.accounts TO birja_app;
REVOKE ALL ON FUNCTION public.portfolio_display_name(text),public.portfolio_name_key(text),
 public.portfolio_description(text),public.check_portfolio_management_metadata(),
 public.create_portfolio(bigint,uuid,text,text),public.initialize_portfolio(bigint),
 public.update_portfolio_metadata(bigint,bigint,text,text,boolean,boolean)
 FROM PUBLIC,birja_app,birja_scheduler;
GRANT EXECUTE ON FUNCTION public.create_portfolio(bigint,uuid,text,text),
 public.initialize_portfolio(bigint),
 public.update_portfolio_metadata(bigint,bigint,text,text,boolean,boolean) TO birja_app;
GRANT USAGE ON SCHEMA public TO birja_action_operator;
GRANT SELECT ON public.stock_action_events,public.stock_action_sources,
 public.stock_action_revisions,public.stock_action_observations,public.stock_action_state,
 public.stock_ownership_movements,public.stock_split_applications,
 public.stock_dividend_entitlements,public.stock_action_resolutions,
 public.stock_instruments,public.stock_data_admissions,public.stock_quotes,public.stock_sessions
 TO birja_action_operator;
GRANT SELECT(id,symbol,asset_class,is_active,sort_order) ON public.coins TO birja_action_operator;
GRANT EXECUTE ON FUNCTION public.apply_stock_action_resolution(
 bigint,bigint,bigint,bigint,bigint,text,text,text,jsonb,text) TO birja_action_operator;

REVOKE ALL ON public.portfolio_lifecycle_closures,public.portfolio_closure_intents
 FROM PUBLIC,birja_app,birja_scheduler,birja_action_operator;
REVOKE ALL ON SEQUENCE public.portfolio_lifecycle_closures_id_seq,
 public.portfolio_closure_intents_id_seq
 FROM PUBLIC,birja_app,birja_scheduler,birja_action_operator;
GRANT SELECT ON public.portfolio_lifecycle_closures,public.portfolio_closure_intents
 TO birja_app,birja_scheduler;
REVOKE ALL ON FUNCTION public.check_portfolio_lifecycle_integrity(),
 public.check_portfolio_terminal_root(),public.check_stock_terminal_clock(),
 public.close_portfolio(bigint,bigint,uuid,text,text)
 FROM PUBLIC,birja_app,birja_scheduler,birja_action_operator;
GRANT EXECUTE ON FUNCTION public.close_portfolio(bigint,bigint,uuid,text,text) TO birja_app;

 IF (
SELECT encode(sha256(convert_to(coalesce(jsonb_agg(v ORDER BY v::text),'[]')::text,
 'UTF8')),'hex') FROM (
 SELECT jsonb_build_array('relation',c.relname,coalesce(r.rolname,'PUBLIC'),
  x.privilege_type,x.is_grantable) v
 FROM pg_class c CROSS JOIN LATERAL aclexplode(coalesce(c.relacl,
  acldefault(CASE WHEN c.relkind='S' THEN 'S'::"char" ELSE 'r'::"char" END,c.relowner))) x
 LEFT JOIN pg_roles r ON r.oid=x.grantee
 WHERE c.relnamespace='public'::regnamespace AND c.relkind IN ('r','S')
 AND x.grantee<>c.relowner
 UNION ALL SELECT jsonb_build_array('column',c.relname,a.attname,
  coalesce(r.rolname,'PUBLIC'),x.privilege_type,x.is_grantable)
 FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid
 CROSS JOIN LATERAL aclexplode(a.attacl) x LEFT JOIN pg_roles r ON r.oid=x.grantee
 WHERE c.relnamespace='public'::regnamespace AND a.attnum>0 AND NOT a.attisdropped
 AND x.grantee<>c.relowner
 UNION ALL SELECT jsonb_build_array('routine',p.oid::regprocedure::text,
  coalesce(r.rolname,'PUBLIC'),x.privilege_type,x.is_grantable)
 FROM pg_proc p CROSS JOIN LATERAL aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) x
 LEFT JOIN pg_roles r ON r.oid=x.grantee
 WHERE p.pronamespace='public'::regnamespace AND x.grantee<>p.proowner
) privileges
) IS DISTINCT FROM '71896f41a9310ada0af0961b78e78f5364654f1513c11bf9310c250ad545f748' THEN RAISE EXCEPTION 'closure final ACL mismatch'; END IF;
END $closure_grants$;
-- New tables stay private until a migration deliberately grants access.
-- Both global and schema defaults are reset, for the actual creator only.
ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator REVOKE SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER,MAINTAIN ON TABLES FROM PUBLIC,birja_app,birja_scheduler;
ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator IN SCHEMA public REVOKE SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER,MAINTAIN ON TABLES FROM PUBLIC,birja_app,birja_scheduler;
ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator REVOKE USAGE,SELECT,UPDATE ON SEQUENCES FROM PUBLIC,birja_app,birja_scheduler;
ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator IN SCHEMA public REVOKE USAGE,SELECT,UPDATE ON SEQUENCES FROM PUBLIC,birja_app,birja_scheduler;
ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC,birja_app,birja_scheduler;
\endif
COMMIT;
