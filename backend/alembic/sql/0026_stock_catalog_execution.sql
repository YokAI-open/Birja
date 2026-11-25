-- All mutable proofs are scoped to the latest admitted listing of this issue.
CREATE FUNCTION public.stock_catalog_scope_current(
 p_admission bigint, p_artifact text, p_binding public.stock_catalog_instruments,
 p_listing public.stock_catalog_listings, p_at timestamptz, p_fields jsonb
) RETURNS boolean LANGUAGE sql STABLE SECURITY INVOKER
SET search_path=pg_catalog,public,pg_temp AS $scope$
 SELECT EXISTS (
   SELECT FROM public.stock_catalog_admissions permission
   JOIN public.stock_catalog_generations generation ON generation.id=p_listing.generation_id
   JOIN public.stock_catalog_admissions mapping ON mapping.id=p_listing.provider_admission_id
   WHERE permission.id=p_admission AND permission.artifact=p_artifact
   AND permission.is_fixture=(generation.mode='fixture')
   AND permission.reviewed_at<=p_at AND p_at<permission.valid_until
   AND permission.revoked_at IS NULL AND permission.fields @> p_fields
   AND generation.is_active AND generation.published_at<=p_at AND p_at<generation.valid_until
   AND p_listing.id=p_binding.listing_id AND p_listing.security_id=p_binding.catalog_id
   AND p_binding.promoted_at<=p_at AND p_listing.state='active' AND p_at<p_listing.valid_until
   AND p_listing.provider_verified_at<=p_at AND p_at<p_listing.provider_valid_until
   AND p_listing.currency='USD' AND p_listing.units_per_share=1
   AND p_listing.classification IN ('common_stock','ordinary_shares')
   AND permission.scope @> jsonb_build_object(
     'catalog_id',p_binding.catalog_id::text,'listing_id',p_listing.id::text,
     'provider_asset_id',p_listing.provider_asset_id,'feed',CASE p_artifact
       WHEN 'catalog_execution' THEN 'iex' WHEN 'catalog_mark' THEN 'iex'
       WHEN 'catalog_halt' THEN 'nasdaq-rss' WHEN 'catalog_actions' THEN 'alpaca-corporate-actions' END)
   AND p_artifact IN ('catalog_execution','catalog_mark','catalog_halt','catalog_actions')
   AND jsonb_typeof(permission.scope->'account')='string'
   AND length(permission.scope->>'account') BETWEEN 1 AND 128
   AND permission.scope->>'account'=btrim(permission.scope->>'account')
   AND jsonb_typeof(permission.scope->'server')='string'
   AND length(permission.scope->>'server') BETWEEN 1 AND 128
   AND permission.scope->>'server'=btrim(permission.scope->>'server')
   AND mapping.artifact='alpaca_assets' AND NOT mapping.is_fixture
   AND mapping.revoked_at IS NULL AND mapping.reviewed_at<=p_at AND p_at<mapping.valid_until
   AND mapping.scope->'provider' @> jsonb_build_object(
       'account',permission.scope->>'account','server',permission.scope->>'server')
   AND mapping.fields @> (SELECT jsonb_object_agg(field,'["collection","internal_use","derived_use","display","storage","backup"]'::jsonb)
     FROM unnest(ARRAY['provider_asset_id','provider_symbol','asset_evidence','currency','units_per_share','unit_evidence']) field)
   AND EXISTS (SELECT FROM jsonb_array_elements(CASE WHEN jsonb_typeof(mapping.scope->'units')='array'
       THEN mapping.scope->'units' ELSE '[]'::jsonb END) AS reviewed(unit)
     WHERE unit @> jsonb_build_object('target',jsonb_build_object(
         'catalog_id',p_binding.catalog_id,'listing_version',p_listing.id,
         'listing_exchange',p_listing.listing_exchange,'provider_symbol',p_listing.provider_symbol),
       'currency',p_listing.currency,'units_per_share',p_listing.units_per_share,
       'classification',p_listing.classification,'evidence_digest',p_listing.unit_evidence_digest)
     AND (unit->'target'->>'provider_asset_id' IS NULL
       OR unit->'target'->>'provider_asset_id'=p_listing.provider_asset_id)
     AND mapping.scope->'provider'->'targets' @> jsonb_build_array(unit->'target')
     AND (unit->>'reviewed_at')::timestamptz=p_listing.unit_evidence_at
     AND p_at<(unit->>'valid_until')::timestamptz)
   AND (generation.mode='fixture' OR (
     EXISTS (SELECT FROM public.stock_catalog_admissions source
       WHERE source.id=p_listing.directory_admission_id AND source.artifact=p_listing.source
       AND NOT source.is_fixture AND source.revoked_at IS NULL
       AND source.reviewed_at<=p_at AND p_at<source.valid_until
       AND source.fields @> '{"ticker":["display"],"listing_exchange":["display"],"share_class":["display"],"eligibility":["derived_use"]}')
     AND EXISTS (SELECT FROM public.stock_catalog_admissions source
       WHERE source.id=p_listing.name_admission_id AND source.artifact=p_listing.source
       AND NOT source.is_fixture AND source.revoked_at IS NULL
       AND source.reviewed_at<=p_at AND p_at<source.valid_until
       AND source.fields @> '{"company_name":["display"]}')
     AND EXISTS (SELECT FROM public.stock_catalog_admissions source
       WHERE source.id=p_listing.classification_admission_id AND source.artifact IN ('openfigi','issuer_exception')
       AND NOT source.is_fixture AND source.revoked_at IS NULL
       AND source.reviewed_at<=p_at AND p_at<source.valid_until
       AND source.fields @> '{"classification":["derived_use"],"identity_key":["derived_use"]}')
   ))
 );
$scope$;

CREATE FUNCTION public.check_catalog_stock_fill() RETURNS trigger
LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog,public,pg_temp AS $adjunct$
DECLARE fill_trade_id bigint; binding public.stock_catalog_instruments%ROWTYPE;
        adjunct public.stock_catalog_fill_evidence%ROWTYPE;
BEGIN
 IF TG_WHEN='BEFORE' THEN
   RAISE EXCEPTION 'catalog stock fill facts are immutable' USING ERRCODE='23514';
 END IF;
 IF TG_TABLE_NAME='trades' THEN
   IF NOT EXISTS (SELECT FROM public.coins WHERE id=NEW.coin_id AND asset_class='stock'
      AND left(symbol,1)='@') THEN RETURN NULL; END IF;
   fill_trade_id:=NEW.id;
 ELSE
   fill_trade_id:=NEW.trade_id;
 END IF;
 SELECT b.* INTO binding FROM public.trades t
 JOIN public.stock_catalog_instruments b ON b.coin_id=t.coin_id WHERE t.id=fill_trade_id;
 SELECT * INTO adjunct FROM public.stock_catalog_fill_evidence WHERE trade_id=fill_trade_id;
 IF binding.catalog_id IS NULL OR adjunct.trade_id IS NULL
 OR adjunct.catalog_id IS DISTINCT FROM binding.catalog_id
 OR adjunct.coin_id IS DISTINCT FROM binding.coin_id
 OR adjunct.listing_id IS DISTINCT FROM binding.listing_id THEN
   RAISE EXCEPTION 'catalog stock fill facts required' USING ERRCODE='23514';
 END IF;
 RETURN NULL;
END $adjunct$;

CREATE CONSTRAINT TRIGGER catalog_stock_trade_requires_fill_evidence
 AFTER INSERT ON public.trades DEFERRABLE INITIALLY DEFERRED
 FOR EACH ROW EXECUTE FUNCTION public.check_catalog_stock_fill();
CREATE CONSTRAINT TRIGGER catalog_stock_fill_evidence_requires_trade
 AFTER INSERT ON public.stock_catalog_fill_evidence DEFERRABLE INITIALLY DEFERRED
 FOR EACH ROW EXECUTE FUNCTION public.check_catalog_stock_fill();
CREATE TRIGGER catalog_stock_fill_evidence_immutable
 BEFORE UPDATE OR DELETE ON public.stock_catalog_fill_evidence
 FOR EACH ROW EXECUTE FUNCTION public.check_catalog_stock_fill();

-- The writer takes the catalog, instrument, portfolio and report fences first.
CREATE FUNCTION public.assert_catalog_stock_execution_current(p_trade bigint,p_user bigint,p_expected jsonb)
RETURNS void LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog,public,pg_temp AS $final$
DECLARE r record; at_time timestamptz;
 t public.trades%ROWTYPE; f public.stock_fill_facts%ROWTYPE;
 m public.stock_ownership_movements%ROWTYPE; e public.stock_catalog_fill_evidence%ROWTYPE;
 b public.stock_catalog_instruments%ROWTYPE; l public.stock_catalog_listings%ROWTYPE;
 q public.stock_catalog_financial_quotes%ROWTYPE; s public.stock_catalog_status%ROWTYPE;
 a public.stock_action_state%ROWTYPE; coverage public.stock_catalog_action_coverage%ROWTYPE;
BEGIN
 IF p_expected IS NULL OR jsonb_typeof(p_expected)<>'object' OR octet_length(p_expected::text)>8192 THEN
   RAISE EXCEPTION 'catalog stock authority invalid' USING ERRCODE='22023';
 END IF;
 at_time:=clock_timestamp();
 SELECT trade AS trade,facts AS facts,movement AS movement,evidence AS evidence,
   binding AS binding,listing AS listing,quote AS quote,status AS status,
   action AS action,period AS period,
   root.cash AS root_cash,holding.quantity AS held,holding.cost_basis AS basis,
   instrument.provider_asset_id AS instrument_asset,
   instrument.provider_verified_at AS instrument_verified_at,
   instrument.listing_exchange AS instrument_exchange,
   session.opens_at AS opens_at,session.closes_at AS closes_at,
   session.calendar_admission_generation AS calendar_generation
 INTO r FROM public.trades trade
 JOIN public.stock_fill_facts facts ON facts.trade_id=trade.id
 JOIN public.stock_ownership_movements movement ON movement.trade_id=trade.id
 JOIN public.stock_catalog_fill_evidence evidence ON evidence.trade_id=trade.id
 JOIN public.accounts root ON root.id=trade.portfolio_id AND root.user_id=trade.user_id
   AND root.closed_at IS NULL
 JOIN public.holdings holding ON holding.portfolio_id=root.id AND holding.user_id=root.user_id
   AND holding.coin_id=trade.coin_id
 JOIN public.stock_catalog_instruments binding ON binding.coin_id=trade.coin_id
 JOIN public.stock_catalog_listings listing ON listing.id=binding.listing_id
 JOIN public.stock_instruments instrument ON instrument.coin_id=trade.coin_id
 JOIN public.coins coin ON coin.id=trade.coin_id AND coin.asset_class='stock'
   AND coin.symbol='@'||binding.catalog_id::text
 JOIN public.stock_catalog_financial_quotes quote ON quote.coin_id=trade.coin_id
 JOIN public.stock_catalog_status status ON status.coin_id=trade.coin_id
 JOIN public.stock_action_state action ON action.coin_id=trade.coin_id
 JOIN public.stock_catalog_action_coverage period ON period.coin_id=trade.coin_id
 JOIN public.stock_sessions session ON session.exchange=listing.listing_exchange AND session.session_date=quote.session_date
 WHERE trade.id=p_trade AND trade.user_id=p_user;
 IF NOT FOUND THEN RAISE EXCEPTION 'catalog stock authority missing' USING ERRCODE='22023'; END IF;
 t:=r.trade; f:=r.facts; m:=r.movement; e:=r.evidence; b:=r.binding; l:=r.listing;
 q:=r.quote; s:=r.status; a:=r.action; coverage:=r.period;
 IF f.authority IS DISTINCT FROM p_expected OR NOT p_expected @> jsonb_build_object(
   'portfolio_id',t.portfolio_id::text,'coin_id',t.coin_id::text,'catalog_id',b.catalog_id::text,
   'listing_id',b.listing_id::text,'provider_asset_id',l.provider_asset_id)
 OR (f.portfolio_id,f.coin_id,f.user_id) IS DISTINCT FROM (t.portfolio_id,t.coin_id,t.user_id)
 OR (m.portfolio_id,m.coin_id,m.user_id) IS DISTINCT FROM (t.portfolio_id,t.coin_id,t.user_id)
 OR (r.root_cash,r.held,r.basis) IS DISTINCT FROM (t.cash_after,f.held_after,m.after_basis)
 OR (e.catalog_id,e.coin_id,e.listing_id) IS DISTINCT FROM (b.catalog_id,b.coin_id,b.listing_id)
 OR (r.instrument_asset,r.instrument_verified_at,r.instrument_exchange) IS DISTINCT FROM
    (l.provider_asset_id,l.provider_verified_at,l.listing_exchange)
 OR (f.provider_asset_id,f.symbol,f.company_name,f.listing_exchange) IS DISTINCT FROM
    (l.provider_asset_id,l.ticker,l.company_name,l.listing_exchange) THEN
   RAISE EXCEPTION 'catalog stock authority identity changed' USING ERRCODE='22023';
 END IF;

 IF e.provider_admission_id IS DISTINCT FROM l.provider_admission_id
 OR e.execution_admission_id IS DISTINCT FROM b.admission_id
 OR NOT public.stock_catalog_scope_current(e.execution_admission_id,'catalog_execution',b,l,at_time,
    (SELECT jsonb_object_agg(field,'["collection","execution","storage","backup"]'::jsonb)
     FROM unnest(ARRAY['bid','ask','event_at','collected_at']) field)) THEN
   RAISE EXCEPTION 'catalog stock execution permission changed' USING ERRCODE='22023';
 END IF;

 IF NOT coalesce(r.opens_at<=at_time AND at_time<r.closes_at,false)
 OR (q.opens_at,q.closes_at,q.calendar_generation) IS DISTINCT FROM
    (r.opens_at,r.closes_at,r.calendar_generation)
 OR NOT EXISTS (SELECT FROM public.stock_data_admissions calendar
   JOIN public.stock_catalog_admissions permission ON permission.id=e.execution_admission_id
   WHERE calendar.product='calendar' AND calendar.state='approved'
   AND calendar.generation=q.calendar_generation AND calendar.collection_allowed AND calendar.derived_allowed
   AND calendar.scope @> jsonb_build_object(
     'application','birja','audience','authenticated-users','feed','iex',
     'account',permission.scope->'account','server',permission.scope->'server')
   AND calendar.reviewed_at<=at_time
   AND calendar.valid_from<=at_time AND at_time<calendar.valid_until
   AND at_time<(calendar.calendar->>'review_valid_until')::timestamptz) THEN
   RAISE EXCEPTION 'catalog stock market closed' USING ERRCODE='22023';
 END IF;

 IF (s.catalog_id,s.listing_id,s.admission_id,s.report_digest,s.event_at,s.valid_until) IS DISTINCT FROM
    (e.catalog_id,e.listing_id,e.halt_admission_id,e.report_digest,e.report_event_at,e.report_valid_until)
 OR s.session_date<>q.session_date OR s.state<>'normal'
 OR s.observed_at>at_time OR at_time>=s.valid_until
 OR NOT public.stock_catalog_scope_current(e.halt_admission_id,'catalog_halt',b,l,at_time,
   (SELECT jsonb_object_agg(field,'["collection","execution","storage","backup"]'::jsonb)
    FROM unnest(ARRAY['report_digest','event_at','valid_until','state']) field)) THEN
   RAISE EXCEPTION 'catalog stock status unavailable' USING ERRCODE='22023';
 END IF;

 IF (q.catalog_id,q.listing_id,q.provider_asset_id,q.provider_admission_id,q.execution_admission_id,
      q.unit_epoch,q.valid_until) IS DISTINCT FROM (e.catalog_id,e.listing_id,l.provider_asset_id,
      e.provider_admission_id,e.execution_admission_id,e.unit_epoch,e.quote_valid_until)
 OR (q.bid,q.ask,q.event_at,q.collected_at,q.observed_at,q.session_date,q.opens_at,q.closes_at,q.source,q.feed)
    IS DISTINCT FROM (f.bid,f.ask,f.event_at,f.collected_at,f.observed_at,f.session_date,f.opens_at,f.closes_at,f.source,f.feed)
 OR q.event_at<=at_time-interval '120 seconds' OR q.observed_at>at_time OR at_time>=q.valid_until
 OR t.exec_price IS DISTINCT FROM (CASE WHEN t.side='buy' THEN q.ask ELSE q.bid END) THEN
   RAISE EXCEPTION 'catalog stock quote unavailable' USING ERRCODE='22023';
 END IF;

 IF (coverage.catalog_id,coverage.listing_id,coverage.admission_id) IS DISTINCT FROM
    (b.catalog_id,b.listing_id,e.action_admission_id)
 OR NOT public.stock_catalog_scope_current(e.action_admission_id,'catalog_actions',b,l,at_time,
   (SELECT jsonb_object_agg(field,'["collection","derivation","storage","backup"]'::jsonb)
    FROM unnest(ARRAY['provider_event_id','symbol','event_type','process_date','terms']) field))
 OR (a.epoch,a.unit_epoch,a.admission_generation) IS DISTINCT FROM
    (e.action_epoch,e.unit_epoch,e.action_admission_id)
 OR m.unit_epoch IS DISTINCT FROM e.unit_epoch
 OR m.economic_at IS DISTINCT FROM m.recorded_at OR m.economic_at>at_time
 OR a.health<>'current' OR NOT coalesce(a.checked_at<=at_time AND at_time<a.valid_until,false)
 OR NOT coalesce(coverage.observed_at<=at_time AND at_time<coverage.valid_until
   AND coverage.coverage_start<=coverage.journal_origin AND coverage.journal_origin<=coverage.covered_until
   AND coverage.covered_until<=at_time AND b.promoted_at<=coverage.journal_origin
   AND coverage.journal_origin=a.journal_start_at
   AND a.complete_from<=coverage.covered_until
   AND (a.coverage_start,a.covered_until,a.cursor,a.checked_at,a.valid_until) IS NOT DISTINCT FROM
       (coverage.coverage_start,coverage.covered_until,coverage.cursor,coverage.observed_at,
        coverage.valid_until),false)
 OR at_time>=a.next_blocking_at OR q.event_at<=a.quote_not_before THEN
   RAISE EXCEPTION 'catalog stock action unavailable' USING ERRCODE='22023';
 END IF;

 -- A claimed current lease cannot override an unresolved hold, old split
 -- revision or a due event which has no matching economic effect.
 IF EXISTS (SELECT FROM public.stock_action_events event WHERE event.coin_id=t.coin_id
   AND (EXISTS (SELECT FROM public.stock_action_revisions rev WHERE rev.event_id=event.id
         AND rev.classification NOT IN ('supported_dividend','supported_forward_split'))
     OR EXISTS (SELECT FROM public.stock_action_observations obs WHERE obs.event_id=event.id
         AND obs.source_kind='missing_or_uncertain'))
   AND NOT EXISTS (SELECT FROM public.stock_action_resolutions resolution
     WHERE resolution.event_id=event.id AND resolution.coin_id=event.coin_id
     AND resolution.expected_revision=event.current_revision_id
     AND resolution.decision IN ('confirm_no_effect','accept_corrected_supported_revision','link_verified_alias')
     AND resolution.evidence->'format'='1'::jsonb
     AND resolution.evidence->'held_revision_ids'=(SELECT jsonb_agg(held.id ORDER BY held.id)
       FROM (SELECT id FROM public.stock_action_revisions WHERE event_id=event.id ORDER BY id LIMIT 129) held)
     AND NOT EXISTS (SELECT FROM public.stock_action_observations obs WHERE obs.event_id=event.id
       AND obs.source_kind='missing_or_uncertain' AND obs.id>CASE WHEN
         resolution.evidence->>'observation_id' ~ '^[0-9]{1,16}$'
         THEN (resolution.evidence->>'observation_id')::bigint ELSE 0 END)))
 OR EXISTS (SELECT FROM public.stock_split_applications applied
   JOIN public.stock_action_events event ON event.id=applied.economic_event_id
   WHERE applied.coin_id=t.coin_id AND applied.revision_id<>event.current_revision_id)
 OR EXISTS (SELECT FROM public.stock_action_events event
   JOIN public.stock_action_revisions rev ON rev.id=event.current_revision_id
   WHERE event.coin_id=t.coin_id AND rev.verified_cutoff<=at_time
   AND rev.classification IN ('supported_dividend','supported_forward_split')
   AND NOT EXISTS (SELECT FROM public.stock_split_applications applied WHERE applied.economic_event_id=event.id)
   AND NOT EXISTS (SELECT FROM public.stock_dividend_entitlements entitled WHERE entitled.event_id=event.id
     AND entitled.portfolio_id=t.portfolio_id)
   -- With complete ownership history, a new buyer at/after the cutoff owes
   -- no previous dividend posting. Every unprocessed split remains blocking.
   AND NOT coalesce(rev.classification='supported_dividend'
     AND a.complete_from<=rev.verified_cutoff AND a.journal_start_at<=rev.verified_cutoff
     AND coverage.coverage_start<=rev.verified_cutoff AND rev.verified_cutoff<=coverage.covered_until
     AND NOT EXISTS (SELECT FROM public.stock_ownership_movements history
       WHERE history.portfolio_id=t.portfolio_id AND history.coin_id=t.coin_id
       AND history.economic_at<rev.verified_cutoff)
     AND NOT EXISTS (SELECT FROM public.trades history WHERE history.portfolio_id=t.portfolio_id
       AND history.coin_id=t.coin_id AND history.id<>t.id AND history.created_at<rev.verified_cutoff)
     AND m.before_quantity=coalesce((SELECT sum(history.quantity) FROM public.stock_ownership_movements history
       WHERE history.portfolio_id=t.portfolio_id AND history.coin_id=t.coin_id AND history.sequence<m.sequence),0)
     AND m.before_basis=coalesce((SELECT history.after_basis FROM public.stock_ownership_movements history
       WHERE history.portfolio_id=t.portfolio_id AND history.coin_id=t.coin_id AND history.sequence<m.sequence
       ORDER BY history.sequence DESC LIMIT 1),0),false)) THEN
   RAISE EXCEPTION 'catalog stock action cutoff unresolved' USING ERRCODE='22023';
 END IF;
END $final$;

REVOKE ALL ON FUNCTION public.stock_catalog_scope_current(bigint,text,public.stock_catalog_instruments,
 public.stock_catalog_listings,timestamptz,jsonb) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.check_catalog_stock_fill() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.assert_catalog_stock_execution_current(bigint,bigint,jsonb) FROM PUBLIC;
