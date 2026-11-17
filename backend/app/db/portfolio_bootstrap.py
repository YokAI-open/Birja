"""Frozen final-schema bootstrap contract shared by local dev and ops validation.

The SQL is source-owned, never generated from the database being authorized.
Production bootstrap carries the same preflight/grants under its admin guard.
"""

PREFLIGHT_SQL = r"""
DO $portfolio_identity$
DECLARE expected record; actual record;
BEGIN
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
"""

GRANTS_SQL = r"""
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
"""
