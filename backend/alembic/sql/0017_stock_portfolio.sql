-- Immutable Alembic0017 companion: stock ownership and execution authority.
-- Loaded at a fixed path by0017_portfolio_ownership; never application imports.
-- Retains0013 receipt arithmetic and independent market authority checks.
-- Root is derived from immutable trade; no overload or caller-selected cash target.
-- The application invokes assert_stock_execution_current as its last business
-- statement, after root/instrument locks and deferred integrity checks.

CREATE OR REPLACE FUNCTION public.check_stock_fill_integrity() RETURNS trigger
LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog,public,pg_temp AS $guard$
DECLARE tid bigint; t public.trades%ROWTYPE; f public.stock_fill_facts%ROWTYPE;
 m public.stock_ownership_movements%ROWTYPE; root public.accounts%ROWTYPE; kind text; n numeric; expected_basis numeric;
BEGIN
 IF TG_WHEN='BEFORE' AND TG_OP='INSERT' THEN
   IF TG_TABLE_NAME='trades' THEN
     SELECT asset_class INTO kind FROM public.coins WHERE id=NEW.coin_id;
     IF kind='crypto' THEN RETURN NEW; END IF;
   END IF;
   SELECT * INTO root FROM public.accounts
     WHERE id=NEW.portfolio_id AND user_id=NEW.user_id;
   IF NOT FOUND OR root.closed_at IS NOT NULL THEN
     RAISE EXCEPTION 'stock portfolio unavailable' USING ERRCODE='23514';
   END IF;
   RETURN NEW;
 END IF;
 IF TG_WHEN='BEFORE' THEN
   IF TG_TABLE_NAME='trades' THEN
     SELECT asset_class INTO kind FROM public.coins WHERE id=OLD.coin_id;
     IF kind<>'stock' THEN
       IF TG_OP='UPDATE' THEN RETURN NEW; ELSE RETURN OLD; END IF;
     END IF;
   END IF;
   RAISE EXCEPTION 'stock records are immutable' USING ERRCODE='23514';
 END IF;
 IF TG_TABLE_NAME='trades' THEN tid:=NEW.id;
 ELSE tid:=NEW.trade_id; END IF;
 IF tid IS NULL THEN RETURN NULL; END IF;
 SELECT * INTO t FROM public.trades WHERE id=tid;
 SELECT asset_class INTO kind FROM public.coins WHERE id=t.coin_id;
 SELECT * INTO f FROM public.stock_fill_facts WHERE trade_id=tid;
 SELECT * INTO m FROM public.stock_ownership_movements WHERE trade_id=tid;
 IF kind='crypto' AND f.trade_id IS NULL AND m.id IS NULL THEN RETURN NULL; END IF;
 SELECT * INTO root FROM public.accounts
   WHERE id=t.portfolio_id AND user_id=t.user_id;
 IF root.id IS NULL OR root.closed_at IS NOT NULL
 OR t.portfolio_id IS DISTINCT FROM f.portfolio_id
 OR t.portfolio_id IS DISTINCT FROM m.portfolio_id
 OR kind IS DISTINCT FROM 'stock' OR t.id IS NULL OR f.trade_id IS NULL OR m.id IS NULL
 OR f.coin_id<>t.coin_id OR f.user_id<>t.user_id OR m.coin_id<>t.coin_id OR m.user_id<>t.user_id
 OR m.cause_kind<>'fill' OR m.application_id IS NOT NULL
 OR t.input_kind<>'quantity' OR t.input_value<>t.quantity
 OR NOT(t.quantity>0 AND t.quantity<1e12 AND t.quantity=trunc(t.quantity))
 OR t.fee<>0 OR NOT(t.cash_after>=0 AND t.cash_after<1e12)
 OR t.exec_price<>(CASE WHEN t.side='buy' THEN f.ask ELSE f.bid END)
 OR t.price_as_of<>f.event_at
 OR m.quantity<>(CASE WHEN t.side='buy' THEN t.quantity ELSE -t.quantity END)
 OR m.after_quantity<>f.held_after
 THEN RAISE EXCEPTION 'stock fill integrity rejected' USING ERRCODE='23514'; END IF;
 -- PostgreSQL round(numeric) ties away from zero; accounting uses half-even.
 n:=t.quantity*t.exec_price;
 n:=trunc(n,2)+CASE WHEN mod(n*100,1)>0.5 OR
   (mod(n*100,1)=0.5 AND mod(trunc(n*100),2)=1) THEN 0.01 ELSE 0 END;
 IF t.cash_delta<>(CASE WHEN t.side='buy' THEN -n ELSE n END)
 OR t.mid_price<>trunc(f.exact_mid,8)+(CASE WHEN mod(f.exact_mid*1e8,1)>0.5 OR
   (mod(f.exact_mid*1e8,1)=0.5 AND mod(trunc(f.exact_mid*1e8),2)=1)
   THEN 0.00000001 ELSE 0 END)
 THEN RAISE EXCEPTION 'stock fill integrity money mismatch' USING ERRCODE='23514'; END IF;
 IF t.side='buy' THEN expected_basis:=m.before_basis-t.cash_delta;
 ELSIF m.after_quantity=0 THEN expected_basis:=0;
 ELSE
   n:=m.before_basis*t.quantity/m.before_quantity;
   expected_basis:=m.before_basis-trunc(n,2)-CASE WHEN mod(n*100,1)>0.5 OR
     (mod(n*100,1)=0.5 AND mod(trunc(n*100),2)=1) THEN 0.01 ELSE 0 END;
 END IF;
 IF m.after_basis<>expected_basis THEN
   RAISE EXCEPTION 'stock fill integrity basis mismatch' USING ERRCODE='23514';
 END IF;
 RETURN NULL;
END $guard$;


CREATE OR REPLACE FUNCTION public.assert_stock_execution_current(p_trade bigint,p_user bigint,p_expected jsonb)
RETURNS void LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog,public,pg_temp AS $final$
DECLARE r record; now_at timestamptz; a jsonb; expected_adm jsonb;
 q public.stock_quotes%ROWTYPE; st public.stock_status_evidence%ROWTYPE;
 ac public.stock_action_state%ROWTYPE; ses public.stock_sessions%ROWTYPE;
 facts public.stock_fill_facts%ROWTYPE; tr public.trades%ROWTYPE;
BEGIN
 IF p_expected IS NULL OR jsonb_typeof(p_expected)<>'object'
 OR octet_length(p_expected::text)>8192 OR jsonb_typeof(p_expected->'admissions')<>'array'
 OR jsonb_array_length(p_expected->'admissions')<>5 THEN
   RAISE EXCEPTION 'stock authority invalid' USING ERRCODE='22023';
 END IF;
 SELECT t AS trade,f AS facts,q0 AS quote,s AS status,a0 AS action,se AS session,
   root.id AS portfolio_id,root.user_id AS portfolio_owner,root.closed_at AS portfolio_closed_at,
   root.cash AS portfolio_cash,h.quantity AS portfolio_held,h.cost_basis AS portfolio_basis,
   m.portfolio_id AS movement_portfolio,m.user_id AS movement_owner,m.after_basis AS after_basis,
   i.provider_asset_id,i.provider_verified_at,c.asset_class,c.is_active,
   (SELECT jsonb_agg(to_jsonb(ad) ORDER BY ad.product) FROM public.stock_data_admissions ad)
     AS admissions,
   EXISTS(SELECT FROM public.stock_action_events ev WHERE ev.coin_id=f.coin_id
    AND (EXISTS(SELECT FROM public.stock_action_revisions rv WHERE rv.event_id=ev.id
      AND rv.classification NOT IN ('supported_dividend','supported_forward_split'))
      OR EXISTS(SELECT FROM public.stock_action_observations ob WHERE ob.event_id=ev.id
        AND ob.source_kind='missing_or_uncertain'))
    AND NOT EXISTS(SELECT FROM public.stock_action_resolutions rs
      WHERE rs.event_id=ev.id AND rs.coin_id=ev.coin_id
      AND rs.expected_revision=ev.current_revision_id
      AND rs.decision IN ('confirm_no_effect',
        'accept_corrected_supported_revision','link_verified_alias')
      AND rs.evidence->'format'='1'::jsonb
      AND rs.evidence->'held_revision_ids'=(SELECT jsonb_agg(h.id ORDER BY h.id)
        FROM (SELECT id FROM public.stock_action_revisions
          WHERE event_id=ev.id ORDER BY id LIMIT 129) h)
      AND NOT EXISTS(SELECT FROM public.stock_action_observations ob WHERE ob.event_id=ev.id
        AND ob.source_kind='missing_or_uncertain' AND ob.id>CASE WHEN
          rs.evidence->>'observation_id' ~ '^[0-9]{1,16}$'
          THEN (rs.evidence->>'observation_id')::bigint ELSE 0 END))) AS held,
   EXISTS(SELECT FROM public.stock_split_applications sp
     JOIN public.stock_action_events ev ON ev.id=sp.economic_event_id
     WHERE sp.coin_id=f.coin_id AND sp.revision_id<>ev.current_revision_id) AS changed_split,
   (SELECT min(rv.verified_cutoff) FROM public.stock_action_events ev
     JOIN public.stock_action_revisions rv ON rv.id=ev.current_revision_id
     WHERE ev.coin_id=f.coin_id
     AND rv.classification IN ('supported_dividend','supported_forward_split')
     AND NOT EXISTS(SELECT FROM public.stock_split_applications sp WHERE sp.economic_event_id=ev.id)
     AND NOT EXISTS(SELECT FROM public.stock_dividend_entitlements en WHERE en.event_id=ev.id AND en.portfolio_id=t.portfolio_id))
       AS pending_boundary
 INTO r FROM public.trades t JOIN public.stock_fill_facts f ON f.trade_id=t.id
 JOIN public.accounts root ON root.id=t.portfolio_id AND root.user_id=t.user_id
 JOIN public.holdings h ON h.portfolio_id=t.portfolio_id AND h.user_id=t.user_id
   AND h.coin_id=t.coin_id
 JOIN public.stock_ownership_movements m ON m.trade_id=t.id
 JOIN public.stock_instruments i ON i.coin_id=f.coin_id JOIN public.coins c ON c.id=i.coin_id
 JOIN public.stock_quotes q0 ON q0.coin_id=f.coin_id
 JOIN public.stock_status_evidence s ON s.coin_id=f.coin_id
 JOIN public.stock_action_state a0 ON a0.coin_id=f.coin_id
 JOIN public.stock_sessions se ON se.exchange=i.listing_exchange
   AND se.session_date=q0.session_date
 WHERE t.id=p_trade AND t.user_id=p_user;
 now_at:=clock_timestamp();
 IF NOT FOUND THEN RAISE EXCEPTION 'stock authority missing' USING ERRCODE='22023'; END IF;
 tr:=r.trade; facts:=r.facts; q:=r.quote; st:=r.status; ac:=r.action; ses:=r.session;
 IF r.portfolio_closed_at IS NOT NULL OR r.portfolio_owner<>p_user
 OR r.portfolio_id::text IS DISTINCT FROM p_expected->>'portfolio_id'
 OR facts.portfolio_id IS DISTINCT FROM tr.portfolio_id
 OR r.movement_portfolio IS DISTINCT FROM tr.portfolio_id
 OR r.movement_owner IS DISTINCT FROM tr.user_id
 OR r.portfolio_cash IS DISTINCT FROM tr.cash_after
 OR r.portfolio_held IS DISTINCT FROM facts.held_after
 OR r.portfolio_basis IS DISTINCT FROM r.after_basis
 OR r.asset_class<>'stock' OR NOT r.is_active OR r.provider_verified_at IS NULL
 OR r.provider_asset_id IS DISTINCT FROM facts.provider_asset_id
 OR facts.authority IS DISTINCT FROM p_expected
 OR p_expected->>'coin_id' IS DISTINCT FROM facts.coin_id::text
 OR p_expected->>'provider_asset_id' IS DISTINCT FROM facts.provider_asset_id
 OR facts.user_id<>p_user OR r.held OR r.changed_split
 OR (r.pending_boundary IS NOT NULL AND now_at>=r.pending_boundary)
 THEN RAISE EXCEPTION 'stock authority identity changed' USING ERRCODE='22023'; END IF;
 IF jsonb_array_length(r.admissions)<>5 OR
   (SELECT count(DISTINCT e->>'product') FROM jsonb_array_elements(p_expected->'admissions') e)<>5
 THEN RAISE EXCEPTION 'stock permission unavailable' USING ERRCODE='22023'; END IF;
 FOR a IN SELECT value FROM jsonb_array_elements(r.admissions) LOOP
   SELECT value INTO expected_adm FROM jsonb_array_elements(p_expected->'admissions')
     WHERE value->>'product'=a->>'product';
   IF expected_adm IS NULL OR a->>'state'<>'approved'
   OR expected_adm->'approved' IS DISTINCT FROM 'true'::jsonb
   OR (a->>'generation') IS DISTINCT FROM expected_adm->>'generation'
   OR encode(sha256(convert_to(a::text,'UTF8')),'hex') IS DISTINCT FROM expected_adm->>'row_hash'
   OR NOT coalesce((a->>'valid_from')::timestamptz<=now_at
     AND now_at<(a->>'valid_until')::timestamptz,false)
   OR (a->>'valid_from')::timestamptz IS DISTINCT FROM (expected_adm->>'valid_from')::timestamptz
   OR (a->>'valid_until')::timestamptz IS DISTINCT FROM (expected_adm->>'valid_until')::timestamptz
   OR a->'collection_allowed' IS DISTINCT FROM 'true'::jsonb
   OR a->'derived_allowed' IS DISTINCT FROM 'true'::jsonb
   OR (a->>'product'<>'calendar' AND a->'retention_allowed' IS DISTINCT FROM 'true'::jsonb)
   OR (a->>'product' IN ('reference','quotes','status')
       AND a->'display_allowed' IS DISTINCT FROM 'true'::jsonb)
   THEN RAISE EXCEPTION 'stock permission changed' USING ERRCODE='22023'; END IF;
   IF a->>'product'='calendar' AND NOT coalesce(
       now_at<(a->'calendar'->>'review_valid_until')::timestamptz,false) THEN
     RAISE EXCEPTION 'stock calendar expired' USING ERRCODE='22023';
   END IF;
   IF a->>'product'='actions' AND ac.admission_generation::text<>a->>'generation'
   OR a->>'product'='quotes' AND q.admission_generation::text<>a->>'generation'
   OR a->>'product'='status' AND st.admission_generation::text<>a->>'generation'
   OR a->>'product'='calendar' AND ses.calendar_admission_generation::text<>a->>'generation'
   THEN RAISE EXCEPTION 'stock generation changed' USING ERRCODE='22023'; END IF;
 END LOOP;
 IF ac.health<>'current' OR NOT coalesce(ac.checked_at<=now_at AND now_at<ac.valid_until,false)
 OR ac.coverage_start IS NULL OR ac.covered_until IS NULL
 OR NOT(ac.coverage_start<=ac.covered_until AND ac.covered_until<=now_at)
 OR ac.epoch::text IS DISTINCT FROM p_expected->>'safety_epoch'
 OR ac.unit_epoch::text IS DISTINCT FROM p_expected->>'unit_epoch'
 OR q.unit_epoch<>ac.unit_epoch
 OR (ac.next_blocking_at IS NOT NULL AND now_at>=ac.next_blocking_at)
 OR (ac.quote_not_before IS NOT NULL AND q.event_at<=ac.quote_not_before)
 OR p_expected->'action_current' IS DISTINCT FROM 'true'::jsonb
 OR NOT coalesce(now_at<(p_expected->>'action_valid_until')::timestamptz,false)
 OR (p_expected->>'next_blocking_at' IS NOT NULL
     AND now_at>=(p_expected->>'next_blocking_at')::timestamptz)
 THEN RAISE EXCEPTION 'stock action unavailable' USING ERRCODE='22023'; END IF;
 IF st.state<>'normal' OR NOT(st.bootstrap_verified AND st.continuity_current)
 OR st.provider_asset_id<>facts.provider_asset_id OR st.session_date<>ses.session_date
 OR NOT coalesce(st.event_at<=st.observed_at AND st.observed_at<=now_at
    AND now_at<st.valid_until,false)
 OR st IS DISTINCT FROM jsonb_populate_record(
    NULL::public.stock_status_evidence,p_expected->'status')
 THEN RAISE EXCEPTION 'stock status unavailable' USING ERRCODE='22023'; END IF;
 IF NOT coalesce(ses.opens_at<=now_at AND now_at<ses.closes_at,false)
 OR p_expected->>'session_state' IS DISTINCT FROM 'open'
 OR ses.session_date IS DISTINCT FROM (p_expected->>'session_date')::date
 OR ses.opens_at IS DISTINCT FROM (p_expected->>'opens_at')::timestamptz
 OR ses.closes_at IS DISTINCT FROM (p_expected->>'closes_at')::timestamptz
 OR ses.calendar_admission_generation::text IS DISTINCT FROM p_expected->>'calendar_generation'
 OR NOT coalesce(now_at<(p_expected->>'session_valid_until')::timestamptz,false)
 THEN RAISE EXCEPTION 'stock market closed' USING ERRCODE='22023'; END IF;
 IF q IS DISTINCT FROM jsonb_populate_record(NULL::public.stock_quotes,
      (p_expected->'quote')||jsonb_build_object('mid',q.mid))
 OR p_expected->'quote'->>'provider_asset_id' IS DISTINCT FROM facts.provider_asset_id
 OR NOT(q.source='alpaca' AND q.feed='iex' AND q.event_at<=q.collected_at
   AND q.collected_at<=now_at AND q.event_at>=ses.opens_at
   AND q.event_at>now_at-interval '120 seconds')
 OR facts.event_at<>q.event_at OR facts.collected_at<>q.collected_at
 OR facts.bid<>q.bid OR facts.ask<>q.ask OR facts.session_date<>q.session_date
 OR facts.opens_at<>ses.opens_at OR facts.closes_at<>ses.closes_at
 OR tr.exec_price<>(CASE WHEN tr.side='buy' THEN q.ask ELSE q.bid END)
 THEN RAISE EXCEPTION 'stock quote unavailable' USING ERRCODE='22023'; END IF;
END $final$;


CREATE OR REPLACE FUNCTION public.check_stock_split_digest_version() RETURNS trigger
LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog,public,pg_temp AS $version$
BEGIN
 IF NEW.owner_digest_version IS DISTINCT FROM 2::smallint THEN
   RAISE EXCEPTION 'new stock split requires explicit digest version2' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $version$;

-- Existing NULL markers are legacy v1 and are never updated. The0015 global
-- portfolio_record_immutable UPDATE/DELETE trigger remains installed unchanged.
CREATE TRIGGER stock_split_digest_version BEFORE INSERT ON public.stock_split_applications
 FOR EACH ROW EXECUTE FUNCTION public.check_stock_split_digest_version();

-- These INSERT checks also cover split/opening movements with no trade_id.
-- Final0017 separately removes finite association guards and installs complete
-- paired owner/cause constraints; it must retain global immutable/deferred checks.
CREATE TRIGGER portfolio_stock_active_insert BEFORE INSERT ON public.trades
 FOR EACH ROW EXECUTE FUNCTION public.check_stock_fill_integrity();
CREATE TRIGGER portfolio_stock_active_insert BEFORE INSERT ON public.stock_fill_facts
 FOR EACH ROW EXECUTE FUNCTION public.check_stock_fill_integrity();
CREATE TRIGGER portfolio_stock_active_insert BEFORE INSERT ON public.stock_ownership_movements
 FOR EACH ROW EXECUTE FUNCTION public.check_stock_fill_integrity();

ALTER FUNCTION public.check_stock_fill_integrity() OWNER TO birja_migrator;
ALTER FUNCTION public.assert_stock_execution_current(bigint,bigint,jsonb) OWNER TO birja_migrator;
ALTER FUNCTION public.check_stock_split_digest_version() OWNER TO birja_migrator;
REVOKE ALL ON FUNCTION public.check_stock_fill_integrity(),
 public.assert_stock_execution_current(bigint,bigint,jsonb),
 public.check_stock_split_digest_version() FROM PUBLIC;
DO $acl$ BEGIN
 IF EXISTS(SELECT FROM pg_roles WHERE rolname='birja_app') THEN
   REVOKE ALL ON FUNCTION public.check_stock_fill_integrity(),
     public.check_stock_split_digest_version() FROM birja_app;
   GRANT EXECUTE ON FUNCTION public.assert_stock_execution_current(bigint,bigint,jsonb)
     TO birja_app;
 END IF;
 IF EXISTS(SELECT FROM pg_roles WHERE rolname='birja_scheduler') THEN
   REVOKE ALL ON FUNCTION public.check_stock_fill_integrity(),
     public.assert_stock_execution_current(bigint,bigint,jsonb),
     public.check_stock_split_digest_version() FROM birja_scheduler;
 END IF;
END $acl$;

