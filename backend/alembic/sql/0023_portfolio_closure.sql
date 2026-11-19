-- End one owned experiment; no caller-supplied financial proof or boundary.
-- The application must complete the shared read-only integrity proof before
-- committing. This definer itself derives every persisted terminal input.
CREATE FUNCTION public.close_portfolio(p_user bigint,p_portfolio bigint,p_key uuid,
 p_name text,p_policy text)
RETURNS TABLE(portfolio_id bigint,outcome text,replayed boolean)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,public,pg_temp
SET lock_timeout='2s' SET statement_timeout='10s'
SET idle_in_transaction_session_timeout='30s' AS $close$
DECLARE
 prior public.portfolio_closure_intents%ROWTYPE;
 root public.accounts%ROWTYPE;
 lifecycle public.portfolio_lifecycle_closures%ROWTYPE;
 state public.stock_action_state%ROWTYPE;
 instruments bigint[]; checked bigint[]; coin bigint;
 boundary bigint; epoch bigint; terminal timestamptz;
 journal_id bigint; day_start timestamptz;
BEGIN
 IF current_setting('transaction_isolation')<>'read committed' THEN
   RAISE EXCEPTION 'read_committed_required' USING ERRCODE='22023'; END IF;
 IF p_user IS NULL OR p_user<=0 OR p_user>9007199254740991
   OR p_portfolio IS NULL OR p_portfolio<=0 OR p_portfolio>9007199254740991
   OR p_key IS NULL
   OR p_key::text !~ '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
   OR p_policy IS DISTINCT FROM 'freeze_at_closure_v1'
   OR p_name IS NULL OR public.portfolio_display_name(p_name) IS DISTINCT FROM p_name THEN
   RAISE EXCEPTION 'invalid closure intent' USING ERRCODE='22023'; END IF;
 PERFORM u.id FROM public.users u WHERE u.id=p_user FOR NO KEY UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'portfolio_unavailable' USING ERRCODE='P0002'; END IF;
 SELECT i.* INTO prior FROM public.portfolio_closure_intents i
   WHERE i.user_id=p_user AND i.intent_key=p_key;
 IF FOUND THEN
   IF (prior.portfolio_id,prior.confirmation_name,prior.policy_version)
      IS DISTINCT FROM (p_portfolio,p_name,p_policy) THEN
     RAISE EXCEPTION 'closure_intent_conflict' USING ERRCODE='23505'; END IF;
   IF prior.outcome='confirmation_changed' THEN
     RETURN QUERY SELECT p_portfolio,'confirmation_changed'::text,true; RETURN;
   END IF;
 END IF;
 -- Private owner check precedes both instrument discovery and acknowledgement.
 IF NOT EXISTS(SELECT FROM public.accounts a WHERE a.id=p_portfolio AND a.user_id=p_user) THEN
   RAISE EXCEPTION 'portfolio_unavailable' USING ERRCODE='P0002'; END IF;
 SELECT coalesce(array_agg(x.coin_id ORDER BY x.coin_id),ARRAY[]::bigint[])
 INTO instruments FROM (
   SELECT m.coin_id FROM public.stock_ownership_movements m WHERE m.portfolio_id=p_portfolio
   UNION SELECT h.coin_id FROM public.holdings h JOIN public.stock_instruments s
     ON s.coin_id=h.coin_id WHERE h.portfolio_id=p_portfolio) x;
 IF cardinality(instruments)>20 OR EXISTS(SELECT FROM unnest(instruments) AS x(id)
   WHERE NOT EXISTS(SELECT FROM public.stock_instruments s WHERE s.coin_id=x.id)) THEN
   RAISE EXCEPTION 'invalid closure instrument inventory' USING ERRCODE='23514'; END IF;
 FOREACH coin IN ARRAY instruments LOOP
   PERFORM pg_advisory_xact_lock(hashtextextended('birja.stock.instrument:' || coin::text,0));
 END LOOP;
 SELECT a.* INTO root FROM public.accounts a
   WHERE a.id=p_portfolio AND a.user_id=p_user FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'portfolio_unavailable' USING ERRCODE='P0002'; END IF;
 SELECT coalesce(array_agg(x.coin_id ORDER BY x.coin_id),ARRAY[]::bigint[])
 INTO checked FROM (
   SELECT m.coin_id FROM public.stock_ownership_movements m WHERE m.portfolio_id=p_portfolio
   UNION SELECT h.coin_id FROM public.holdings h JOIN public.stock_instruments s
     ON s.coin_id=h.coin_id WHERE h.portfolio_id=p_portfolio) x;
 IF instruments IS DISTINCT FROM checked THEN
   RAISE EXCEPTION 'closure instrument set changed' USING ERRCODE='40001'; END IF;
 SELECT c.* INTO lifecycle FROM public.portfolio_lifecycle_closures c
   WHERE c.portfolio_id=p_portfolio;
 IF root.closed_at IS NOT NULL THEN
   IF lifecycle.id IS NULL OR (lifecycle.user_id,lifecycle.closed_at)
       IS DISTINCT FROM (root.user_id,root.closed_at)
     OR (prior.id IS NOT NULL AND lifecycle.intent_id IS DISTINCT FROM prior.id)
     OR (SELECT count(*) FROM public.portfolio_stock_closures c
         WHERE c.portfolio_id=p_portfolio)<>cardinality(instruments) THEN
     RAISE EXCEPTION 'invalid closure evidence' USING ERRCODE='23514'; END IF;
   FOREACH coin IN ARRAY instruments LOOP
     IF NOT EXISTS(SELECT FROM public.portfolio_stock_closures c
       WHERE c.portfolio_id=p_portfolio AND c.user_id=p_user AND c.coin_id=coin
       AND c.closed_at=root.closed_at
       AND c.closing_sequence=coalesce((SELECT max(m.sequence)
         FROM public.stock_ownership_movements m WHERE m.coin_id=coin
         AND m.recorded_at<=root.closed_at),0)
       AND c.unit_epoch=(SELECT count(*) FROM public.stock_split_applications s
         WHERE s.coin_id=coin AND s.processed_at<=root.closed_at)) THEN
       RAISE EXCEPTION 'invalid closure stock boundary' USING ERRCODE='23514'; END IF;
   END LOOP;
   RETURN QUERY SELECT p_portfolio,'closed'::text,true; RETURN;
 END IF;
 IF prior.id IS NOT NULL OR lifecycle.id IS NOT NULL
    OR EXISTS(SELECT FROM public.portfolio_stock_closures c WHERE c.portfolio_id=p_portfolio) THEN
   RAISE EXCEPTION 'invalid active closure evidence' USING ERRCODE='23514'; END IF;
 -- Only new durable outcomes consume this finite budget, including refusals.
 day_start:=date_trunc('day',clock_timestamp() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC';
 IF (SELECT count(*) FROM public.portfolio_closure_intents i WHERE i.user_id=p_user
   AND i.recorded_at>=day_start AND i.recorded_at<day_start+interval '24 hours')>=200 THEN
   RAISE EXCEPTION 'closure_quota' USING ERRCODE='P0001'; END IF;
 IF root.name IS DISTINCT FROM p_name THEN
   INSERT INTO public.portfolio_closure_intents
     (user_id,portfolio_id,intent_key,confirmation_name,policy_version,outcome,recorded_at)
     VALUES(p_user,p_portfolio,p_key,p_name,p_policy,'confirmation_changed',clock_timestamp());
   RETURN QUERY SELECT p_portfolio,'confirmation_changed'::text,false; RETURN;
 END IF;
 -- Locks are now complete. Never use transaction/statement/request start time.
 terminal:=clock_timestamp();
 FOREACH coin IN ARRAY instruments LOOP
   SELECT a.* INTO state FROM public.stock_action_state a WHERE a.coin_id=coin;
   SELECT coalesce(max(m.sequence),0) INTO boundary
     FROM public.stock_ownership_movements m WHERE m.coin_id=coin;
   SELECT count(*) INTO epoch FROM public.stock_split_applications s WHERE s.coin_id=coin;
   IF state.coin_id IS NULL OR state.unit_epoch<>epoch OR state.sequence>boundary
     OR state.journal_start_at IS NULL OR state.journal_start_at>=terminal
     OR boundary<>(SELECT count(*) FROM public.stock_ownership_movements m WHERE m.coin_id=coin)
     OR EXISTS(SELECT FROM public.stock_ownership_movements m WHERE m.coin_id=coin
       AND (m.recorded_at>=terminal OR m.economic_at>=terminal))
     OR EXISTS(SELECT FROM public.stock_split_applications s WHERE s.coin_id=coin
       AND s.processed_at>=terminal)
     OR EXISTS(SELECT FROM public.portfolio_stock_closures c WHERE c.coin_id=coin
       AND c.closed_at>=terminal) THEN
     RAISE EXCEPTION 'invalid closure stock history or clock' USING ERRCODE='23514'; END IF;
   -- A holding-only orphan cannot be made consistent by manufacturing a bound.
   IF EXISTS(SELECT FROM public.holdings h WHERE h.portfolio_id=p_portfolio AND h.coin_id=coin
       AND (h.user_id<>p_user OR (h.quantity,h.cost_basis) IS DISTINCT FROM
         (SELECT ROW(m.after_quantity,m.after_basis) FROM public.stock_ownership_movements m
          WHERE m.portfolio_id=p_portfolio AND m.coin_id=coin ORDER BY m.sequence DESC LIMIT 1)))
     OR EXISTS(SELECT FROM public.stock_ownership_movements m WHERE m.portfolio_id=p_portfolio
       AND m.coin_id=coin AND m.user_id<>p_user)
     OR NOT EXISTS(SELECT FROM public.stock_ownership_movements m
       WHERE m.portfolio_id=p_portfolio AND m.coin_id=coin) THEN
     RAISE EXCEPTION 'invalid closure holding history' USING ERRCODE='23514'; END IF;
 END LOOP;
 INSERT INTO public.portfolio_closure_intents
   (user_id,portfolio_id,intent_key,confirmation_name,policy_version,outcome,recorded_at)
   VALUES(p_user,p_portfolio,p_key,p_name,p_policy,'closed',terminal) RETURNING id INTO journal_id;
 INSERT INTO public.portfolio_lifecycle_closures
   (user_id,portfolio_id,closed_at,policy_version,provenance,confirmation_name,intent_id)
   VALUES(p_user,p_portfolio,terminal,p_policy,'owner_confirmation',p_name,journal_id);
 FOREACH coin IN ARRAY instruments LOOP
   INSERT INTO public.portfolio_stock_closures
     (portfolio_id,user_id,coin_id,closed_at,closing_sequence,unit_epoch)
     SELECT p_portfolio,p_user,coin,terminal,
       coalesce((SELECT max(m.sequence) FROM public.stock_ownership_movements m WHERE m.coin_id=coin),0),
       (SELECT count(*) FROM public.stock_split_applications s WHERE s.coin_id=coin);
 END LOOP;
 UPDATE public.accounts a SET closed_at=terminal WHERE a.id=p_portfolio AND a.user_id=p_user;
 RETURN QUERY SELECT p_portfolio,'closed'::text,false;
END $close$;

ALTER FUNCTION public.close_portfolio(bigint,bigint,uuid,text,text) OWNER TO birja_migrator;
REVOKE ALL ON FUNCTION public.close_portfolio(bigint,bigint,uuid,text,text)
 FROM PUBLIC,birja_app,birja_scheduler;
GRANT EXECUTE ON FUNCTION public.close_portfolio(bigint,bigint,uuid,text,text) TO birja_app;
