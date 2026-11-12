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
  IF (SELECT version_num FROM public.alembic_version) NOT IN ('0007','0008','0009','0010','0011','0012','0013','0014') THEN
    RAISE EXCEPTION 'unsupported populated revision';
  END IF;
  FOREACH t IN ARRAY ARRAY['users','accounts','auth_sessions','refresh_tokens','coins','prices','holdings','trades','alembic_version'] || CASE WHEN (SELECT version_num FROM public.alembic_version) IN ('0009','0010','0011','0012','0013','0014') THEN ARRAY['stock_instruments','stock_quotes','stock_sessions','stock_data_admissions'] ELSE ARRAY[]::text[] END || CASE WHEN (SELECT version_num FROM public.alembic_version) IN ('0011','0012','0013','0014') THEN ARRAY['stock_action_events','stock_action_sources','stock_action_revisions','stock_action_observations','stock_action_state','stock_ownership_movements','stock_split_applications','stock_dividend_entitlements','stock_action_resolutions'] ELSE ARRAY[]::text[] END || CASE WHEN (SELECT version_num FROM public.alembic_version) IN ('0013','0014') THEN ARRAY['stock_fill_facts','stock_status_evidence'] ELSE ARRAY[]::text[] END || CASE WHEN (SELECT version_num FROM public.alembic_version)='0014' THEN ARRAY['stock_dividend_payments','stock_dividend_decisions'] ELSE ARRAY[]::text[] END LOOP
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
  FOREACH t IN ARRAY ARRAY['users','accounts','auth_sessions','refresh_tokens','coins','prices','holdings','trades','alembic_version'] || CASE WHEN (SELECT version_num FROM public.alembic_version) IN ('0009','0010','0011','0012','0013','0014') THEN ARRAY['stock_instruments','stock_quotes','stock_sessions','stock_data_admissions'] ELSE ARRAY[]::text[] END || CASE WHEN (SELECT version_num FROM public.alembic_version) IN ('0011','0012','0013','0014') THEN ARRAY['stock_action_events','stock_action_sources','stock_action_revisions','stock_action_observations','stock_action_state','stock_ownership_movements','stock_split_applications','stock_dividend_entitlements','stock_action_resolutions'] ELSE ARRAY[]::text[] END || CASE WHEN (SELECT version_num FROM public.alembic_version) IN ('0013','0014') THEN ARRAY['stock_fill_facts','stock_status_evidence'] ELSE ARRAY[]::text[] END || CASE WHEN (SELECT version_num FROM public.alembic_version)='0014' THEN ARRAY['stock_dividend_payments','stock_dividend_decisions'] ELSE ARRAY[]::text[] END LOOP
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
  IF (SELECT version_num FROM public.alembic_version) IN ('0009','0010','0011','0012','0013','0014') THEN
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
      IF (SELECT version_num FROM public.alembic_version) NOT IN ('0011','0012','0013','0014') THEN RETURN; END IF;
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
  IF (SELECT version_num FROM public.alembic_version) IN ('0012','0013','0014') THEN
    GRANT SELECT(id,symbol,asset_class,is_active,sort_order) ON public.coins TO birja_action_operator;
    ALTER FUNCTION public.apply_stock_action_resolution(bigint,bigint,bigint,bigint,bigint,text,text,text,jsonb,text) OWNER TO birja_migrator;
    REVOKE ALL ON FUNCTION public.apply_stock_action_resolution(bigint,bigint,bigint,bigint,bigint,text,text,text,jsonb,text) FROM PUBLIC,birja_app,birja_scheduler;
    GRANT EXECUTE ON FUNCTION public.apply_stock_action_resolution(bigint,bigint,bigint,bigint,bigint,text,text,text,jsonb,text) TO birja_action_operator;
  END IF;
END
$resolution_grants$;
DO $execution_grants$
BEGIN
 IF (SELECT version_num FROM public.alembic_version) IN ('0013','0014') THEN
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
 IF (SELECT version_num FROM public.alembic_version)='0014' THEN
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
-- New tables stay private until a migration deliberately grants access.
-- Both global and schema defaults are reset, for the actual creator only.
ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator REVOKE SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER,MAINTAIN ON TABLES FROM PUBLIC,birja_app,birja_scheduler;
ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator IN SCHEMA public REVOKE SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER,MAINTAIN ON TABLES FROM PUBLIC,birja_app,birja_scheduler;
ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator REVOKE USAGE,SELECT,UPDATE ON SEQUENCES FROM PUBLIC,birja_app,birja_scheduler;
ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator IN SCHEMA public REVOKE USAGE,SELECT,UPDATE ON SEQUENCES FROM PUBLIC,birja_app,birja_scheduler;
ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC,birja_app,birja_scheduler;
\endif
COMMIT;
