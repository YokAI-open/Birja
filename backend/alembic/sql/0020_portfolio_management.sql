-- Authenticated owner IDs come from the backend. Database roles are service
-- identities, not end-user identities: caller GUCs never establish ownership.
-- Management lock order is user -> account; no stock instrument locks occur.
-- Non-key owner locks serialize management without blocking ledger FK KEY SHARE.
CREATE FUNCTION public.create_portfolio(p_user bigint,p_key uuid,p_name text,p_description text)
RETURNS TABLE(portfolio_id bigint,name text,description text,creation_id bigint,replayed boolean)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,public,pg_temp SET lock_timeout='2s' AS $create$
DECLARE
 display text; details text; payload jsonb; prior public.portfolio_creations%ROWTYPE;
 root public.accounts%ROWTYPE; journal_id bigint; day_start timestamptz;
BEGIN
 IF p_user IS NULL OR p_user<=0 OR p_key IS NULL
   OR p_key::text !~ '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$' THEN
   RAISE EXCEPTION 'invalid creation intent' USING ERRCODE='22023'; END IF;
 PERFORM u.id FROM public.users u WHERE u.id=p_user FOR NO KEY UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'portfolio_unavailable' USING ERRCODE='P0002'; END IF;
 display:=public.portfolio_display_name(p_name);
 details:=public.portfolio_description(p_description);
 payload:=jsonb_build_object('name',display,'description',details);
 SELECT c.* INTO prior FROM public.portfolio_creations c
   WHERE c.user_id=p_user AND c.creation_key=p_key;
 IF FOUND THEN
   IF prior.payload_version<>1 OR prior.canonical_payload<>payload THEN
     RAISE EXCEPTION 'creation_key_conflict' USING ERRCODE='23505'; END IF;
   SELECT a.* INTO root FROM public.accounts a
     WHERE a.id=prior.portfolio_id AND a.user_id=p_user FOR UPDATE;
   IF NOT FOUND OR root.closed_at IS NOT NULL THEN
     RAISE EXCEPTION 'portfolio_unavailable' USING ERRCODE='P0002'; END IF;
   RETURN QUERY SELECT root.id,root.name,root.description,prior.id,true;
   RETURN;
 END IF;
 IF (SELECT count(*) FROM public.accounts a
     WHERE a.user_id=p_user AND a.closed_at IS NULL)>=10 THEN
   RAISE EXCEPTION 'portfolio_limit' USING ERRCODE='23514'; END IF;
 IF EXISTS(SELECT FROM public.accounts a WHERE a.user_id=p_user
     AND a.closed_at IS NULL AND a.name_key=public.portfolio_name_key(display)) THEN
   RAISE EXCEPTION 'name_taken' USING ERRCODE='23505'; END IF;
 -- Only successful new explicit grants consume this durable UTC-day budget.
 -- Replays above never consume it, including after a metadata change.
 day_start:=date_trunc('day',clock_timestamp() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC';
 IF (SELECT count(*) FROM public.portfolio_creations c WHERE c.user_id=p_user
     AND c.origin='explicit' AND c.created_at>=day_start
     AND c.created_at<day_start+interval '24 hours')>=100 THEN
   RAISE EXCEPTION 'creation_quota' USING ERRCODE='P0001'; END IF;
 INSERT INTO public.accounts(user_id,name,name_key,description,cash,starting_cash)
   VALUES(p_user,display,public.portfolio_name_key(display),details,10000,10000)
   RETURNING * INTO root;
 INSERT INTO public.portfolio_creations
   (user_id,creation_key,portfolio_id,origin,payload_version,canonical_payload,amount,created_at)
   VALUES(p_user,p_key,root.id,'explicit',1,payload,10000,clock_timestamp())
   RETURNING id INTO journal_id;
 RETURN QUERY SELECT root.id,root.name,root.description,journal_id,false;
END $create$;

CREATE FUNCTION public.initialize_portfolio(p_user bigint)
RETURNS bigint LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,public,pg_temp SET lock_timeout='2s' AS $initialize$
DECLARE root_id bigint; journal_id bigint;
BEGIN
 IF p_user IS NULL OR p_user<=0 THEN
   RAISE EXCEPTION 'invalid initialization intent' USING ERRCODE='22023'; END IF;
 PERFORM u.id FROM public.users u WHERE u.id=p_user FOR NO KEY UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'portfolio_unavailable' USING ERRCODE='P0002'; END IF;
 SELECT i.portfolio_id INTO root_id FROM public.portfolio_initializations i
   WHERE i.user_id=p_user;
 IF FOUND THEN RETURN root_id; END IF;
 -- Onboarding is solely for a genuinely new, empty identity. Explicit create
 -- never repairs onboarding, and legacy identities were all latched by0019.
 IF EXISTS(SELECT FROM public.accounts a WHERE a.user_id=p_user) THEN
   RAISE EXCEPTION 'initialization_unavailable' USING ERRCODE='P0002'; END IF;
 INSERT INTO public.accounts(user_id,name,name_key,description,cash,starting_cash)
   VALUES(p_user,'My portfolio',public.portfolio_name_key('My portfolio'),'',10000,10000)
   RETURNING id INTO root_id;
 INSERT INTO public.portfolio_creations
   (user_id,creation_key,portfolio_id,origin,payload_version,canonical_payload,amount,created_at)
   VALUES(p_user,gen_random_uuid(),root_id,'initial',1,
     jsonb_build_object('name','My portfolio','description',''),10000,clock_timestamp())
   RETURNING id INTO journal_id;
 INSERT INTO public.portfolio_initializations(user_id,origin,portfolio_id,creation_id)
   VALUES(p_user,'initial',root_id,journal_id);
 RETURN root_id;
END $initialize$;

CREATE FUNCTION public.update_portfolio_metadata(p_user bigint,p_portfolio bigint,
 p_name text,p_description text,p_has_name boolean,p_has_description boolean)
RETURNS TABLE(portfolio_id bigint,name text,description text)
LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,public,pg_temp SET lock_timeout='2s' AS $metadata$
DECLARE root public.accounts%ROWTYPE; display text; details text;
BEGIN
 IF p_user IS NULL OR p_user<=0 OR p_portfolio IS NULL OR p_portfolio<=0
   OR p_has_name IS NULL OR p_has_description IS NULL
   OR NOT(p_has_name OR p_has_description) THEN
   RAISE EXCEPTION 'invalid metadata intent' USING ERRCODE='22023'; END IF;
 PERFORM u.id FROM public.users u WHERE u.id=p_user FOR NO KEY UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'portfolio_unavailable' USING ERRCODE='P0002'; END IF;
 SELECT a.* INTO root FROM public.accounts a
   WHERE a.id=p_portfolio AND a.user_id=p_user AND a.closed_at IS NULL FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'portfolio_unavailable' USING ERRCODE='P0002'; END IF;
 display:=CASE WHEN p_has_name THEN public.portfolio_display_name(p_name) ELSE root.name END;
 details:=CASE WHEN p_has_description THEN public.portfolio_description(p_description) ELSE root.description END;
 IF EXISTS(SELECT FROM public.accounts a WHERE a.user_id=p_user
   AND a.id<>p_portfolio AND a.closed_at IS NULL
   AND a.name_key=public.portfolio_name_key(display)) THEN
   RAISE EXCEPTION 'name_taken' USING ERRCODE='23505'; END IF;
 UPDATE public.accounts a SET name=display,name_key=public.portfolio_name_key(display),description=details
   WHERE a.id=p_portfolio;
 RETURN QUERY SELECT root.id,display,details;
END $metadata$;

ALTER FUNCTION public.create_portfolio(bigint,uuid,text,text) OWNER TO birja_migrator;
ALTER FUNCTION public.initialize_portfolio(bigint) OWNER TO birja_migrator;
ALTER FUNCTION public.update_portfolio_metadata(bigint,bigint,text,text,boolean,boolean) OWNER TO birja_migrator;
REVOKE ALL ON FUNCTION public.create_portfolio(bigint,uuid,text,text) FROM PUBLIC,birja_app,birja_scheduler;
REVOKE ALL ON FUNCTION public.initialize_portfolio(bigint) FROM PUBLIC,birja_app,birja_scheduler;
REVOKE ALL ON FUNCTION public.update_portfolio_metadata(bigint,bigint,text,text,boolean,boolean) FROM PUBLIC,birja_app,birja_scheduler;
GRANT EXECUTE ON FUNCTION public.create_portfolio(bigint,uuid,text,text) TO birja_app;
GRANT EXECUTE ON FUNCTION public.initialize_portfolio(bigint) TO birja_app;
GRANT EXECUTE ON FUNCTION public.update_portfolio_metadata(bigint,bigint,text,text,boolean,boolean) TO birja_app;
-- Both onboarding and explicit creation now use fixed-grant authority.
REVOKE INSERT ON public.accounts FROM birja_app,birja_scheduler;
REVOKE USAGE ON SEQUENCE public.accounts_id_seq FROM birja_app,birja_scheduler;
