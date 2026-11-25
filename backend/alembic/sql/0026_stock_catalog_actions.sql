-- Stable catalog identity for the existing stock action entry points.

CREATE FUNCTION public.stock_catalog_action_context(
 p_coin bigint,p_event bigint,p_revision bigint,p_at timestamptz,p_cutoff timestamptz,
 p_verified boolean
) RETURNS jsonb LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path=pg_catalog,public,pg_temp AS $catalog_action$
DECLARE
 binding public.stock_catalog_instruments%ROWTYPE;
 listing public.stock_catalog_listings%ROWTYPE;
 original_listing public.stock_catalog_listings%ROWTYPE;
 revision_listing public.stock_catalog_listings%ROWTYPE;
 coverage public.stock_catalog_action_coverage%ROWTYPE;
 admission record;
 original_admission record;
 action_state public.stock_action_state%ROWTYPE;
 original public.stock_action_revisions%ROWTYPE;
 target public.stock_action_revisions%ROWTYPE;
 action_fields constant jsonb := '{
   "provider_event_id":["collection","derivation","storage","backup"],
   "symbol":["collection","derivation","storage","backup"],
   "event_type":["collection","derivation","storage","backup"],
   "process_date":["collection","derivation","storage","backup"],
   "terms":["collection","derivation","storage","backup"]
 }'::jsonb;
BEGIN
 SELECT * INTO binding FROM public.stock_catalog_instruments WHERE coin_id=p_coin;
 IF NOT FOUND THEN RETURN NULL; END IF;
 SELECT * INTO listing FROM public.stock_catalog_listings WHERE id=binding.listing_id;
 SELECT * INTO coverage FROM public.stock_catalog_action_coverage WHERE coin_id=p_coin;
 SELECT * INTO action_state FROM public.stock_action_state WHERE coin_id=p_coin;
 SELECT id,artifact,reviewed_at,valid_until,revoked_at,fields,scope,is_fixture INTO admission
   FROM public.stock_catalog_admissions WHERE id=coverage.admission_id;
 SELECT rv.* INTO target FROM public.stock_action_revisions rv
   JOIN public.stock_action_events ev ON ev.id=rv.event_id AND ev.current_revision_id=rv.id
   JOIN public.stock_action_sources src ON src.id=rv.source_id AND src.event_id=ev.id
   WHERE ev.id=p_event AND ev.coin_id=p_coin AND rv.id=p_revision
     AND src.provider='alpaca' AND src.product='actions';
 SELECT rv.* INTO original FROM public.stock_action_revisions rv
   WHERE rv.event_id=p_event AND rv.ordinal=1;
 SELECT id,artifact,reviewed_at,valid_until,revoked_at,fields,scope,is_fixture
   INTO original_admission FROM public.stock_catalog_admissions
   WHERE id=original.admission_generation;
 SELECT * INTO original_listing FROM public.stock_catalog_listings
   WHERE security_id=binding.catalog_id
     AND to_jsonb(id::text)=original.normalized_terms->'listing_id';
 SELECT * INTO revision_listing FROM public.stock_catalog_listings
   WHERE security_id=binding.catalog_id
     AND to_jsonb(id::text)=target.normalized_terms->'listing_id';
 IF NOT coalesce(
   coverage.listing_id=binding.listing_id
   AND binding.promoted_at<=coverage.journal_origin
   AND coverage.journal_origin=action_state.journal_start_at
   AND coverage.observed_at<=p_at
   AND action_state.admission_generation=admission.id
   AND target.admission_generation=admission.id
   AND target.observed_at<=p_at
   AND public.stock_catalog_scope_current(admission.id,'catalog_actions',binding,listing,
                                          p_at,action_fields)
   AND target.normalized_terms->'catalog_id'=to_jsonb(binding.catalog_id::text)
   AND original.normalized_terms->'catalog_id'=to_jsonb(binding.catalog_id::text)
   AND target.normalized_terms->>'coin_id'=p_coin::text
   AND original.normalized_terms->>'coin_id'=p_coin::text
   AND target.normalized_terms->>'provider_asset_id'=revision_listing.provider_asset_id
   AND revision_listing.provider_asset_id=listing.provider_asset_id
   AND original.normalized_terms->>'provider_asset_id'=original_listing.provider_asset_id
   AND original_listing.provider_asset_id=listing.provider_asset_id
   AND original.normalized_terms->>'symbol'=original_listing.ticker
   AND original_listing.evidence_at<=original.observed_at
   AND original.observed_at<original_listing.valid_until
   AND original_admission.artifact='catalog_actions'
   AND original_admission.is_fixture=admission.is_fixture
   AND original_admission.reviewed_at<=original.observed_at
   AND (original_admission.revoked_at IS NULL
        OR original.observed_at<original_admission.revoked_at)
   AND original.observed_at<original_admission.valid_until
   AND original_admission.fields @> action_fields
   AND original_admission.scope @> jsonb_build_object(
     'catalog_id',binding.catalog_id::text,'listing_id',original_listing.id::text,
     'provider_asset_id',original_listing.provider_asset_id,
     'account',admission.scope->'account','server',admission.scope->'server',
     'feed','alpaca-corporate-actions')
   AND (original_listing.ticker=listing.ticker OR EXISTS(
     SELECT FROM public.stock_catalog_aliases a
       WHERE a.listing_id=listing.id AND a.security_id=binding.catalog_id
         AND a.namespace='former' AND a.symbol=original_listing.ticker
         AND a.verified_at<=p_at AND p_at<a.valid_until))
   AND (target.normalized_terms->>'symbol'=revision_listing.ticker
     OR EXISTS(SELECT FROM public.stock_catalog_aliases a
       WHERE a.listing_id=revision_listing.id AND a.security_id=binding.catalog_id
         AND a.namespace='former' AND a.symbol=target.normalized_terms->>'symbol'
         AND a.verified_at<=target.observed_at AND target.observed_at<a.valid_until))
   AND (revision_listing.id=listing.id OR EXISTS(
     SELECT FROM public.stock_catalog_aliases a
       WHERE a.listing_id=listing.id AND a.security_id=binding.catalog_id
         AND a.namespace='former' AND a.symbol=revision_listing.ticker
         AND a.verified_at<=p_at AND p_at<a.valid_until
     ) OR revision_listing.ticker=listing.ticker),false)
 THEN RAISE EXCEPTION 'catalog action identity unavailable' USING ERRCODE='22023'; END IF;
 IF p_verified AND NOT coalesce(
   p_cutoff IS NOT NULL AND coverage.journal_origin<=p_cutoff
   AND coverage.coverage_start<=coverage.journal_origin
   AND p_cutoff<=coverage.covered_until AND coverage.covered_until<=p_at
   AND coverage.coverage_start=action_state.coverage_start
   AND coverage.covered_until=action_state.covered_until
   AND coverage.cursor IS NOT DISTINCT FROM action_state.cursor
   AND coverage.valid_until=action_state.valid_until
   AND p_at<coverage.valid_until AND coverage.valid_until<=admission.valid_until
   AND action_state.health='current' AND action_state.checked_at=coverage.observed_at
   AND action_state.complete_from<=p_cutoff,false)
 THEN RAISE EXCEPTION 'catalog action coverage unavailable' USING ERRCODE='22023'; END IF;
 RETURN jsonb_build_object(
   'binding',to_jsonb(binding),'coverage',to_jsonb(coverage),'admission',to_jsonb(admission),
   'label',jsonb_build_object('symbol',original_listing.ticker,'name',original_listing.company_name),
   'provider_asset_id',listing.provider_asset_id);
END $catalog_action$;

ALTER FUNCTION public.stock_catalog_action_context(bigint,bigint,bigint,timestamptz,timestamptz,boolean)
 OWNER TO birja_migrator;
REVOKE ALL ON FUNCTION public.stock_catalog_action_context(bigint,bigint,bigint,timestamptz,timestamptz,boolean)
 FROM PUBLIC;


-- Keep the existing posting and operator routines and their role grants.

CREATE OR REPLACE FUNCTION public.stock_dividend_authority(
 p_event bigint,p_entitlement bigint,p_revision text,p_fingerprint text,
 p_verified boolean,p_expected jsonb)
RETURNS jsonb LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path=pg_catalog,public,pg_temp AS $authority$
DECLARE r record; a jsonb; n timestamptz; result jsonb; terms jsonb; v jsonb;
 catalog jsonb;
BEGIN
 SELECT ev AS event,rv AS revision,en AS entitlement,st AS action,
   ac.id AS portfolio_id,ac.user_id AS portfolio_owner,ac.closed_at AS portfolio_closed_at,
   i AS instrument,c AS coin,se AS cutoff_session,
   (SELECT coalesce(sum(m.quantity),0) FROM public.stock_ownership_movements m
    WHERE m.coin_id=ev.coin_id AND m.portfolio_id=en.portfolio_id AND m.user_id=en.user_id
    AND (m.economic_at<en.cutoff OR (m.economic_at=en.cutoff
      AND m.cause_kind='split' AND m.unit_epoch<=en.unit_epoch))) AS historical_quantity,
   (SELECT coalesce(max(m.sequence),0) FROM public.stock_ownership_movements m
    WHERE m.coin_id=ev.coin_id AND (m.economic_at<en.cutoff OR (m.economic_at=en.cutoff
      AND m.cause_kind='split' AND m.unit_epoch<=en.unit_epoch))) AS historical_sequence,
   (SELECT count(*) FROM public.stock_split_applications sp
    WHERE sp.coin_id=ev.coin_id AND sp.cutoff<en.cutoff) AS natural_units,
   EXISTS(SELECT FROM public.stock_split_applications sp WHERE sp.coin_id=ev.coin_id
     AND sp.cutoff=en.cutoff AND sp.new_unit_epoch=en.unit_epoch) AS boundary_units,
   EXISTS(SELECT FROM public.stock_action_events evs JOIN public.stock_action_revisions rvs
      ON rvs.id=evs.current_revision_id WHERE evs.coin_id=ev.coin_id
      AND rvs.classification='supported_forward_split' AND rvs.verified_cutoff<=en.cutoff
      AND NOT EXISTS(SELECT FROM public.stock_split_applications sp
        WHERE sp.economic_event_id=evs.id AND sp.revision_id=rvs.id)) AS unresolved_split,
   (SELECT jsonb_agg(to_jsonb(ad) ORDER BY ad.product)
    FROM public.stock_data_admissions ad
    WHERE ad.product IN ('actions','calendar','reference')) AS admissions,
   EXISTS(SELECT FROM public.stock_dividend_entitlements newer
     WHERE newer.event_id=ev.id AND newer.portfolio_id=en.portfolio_id
       AND newer.user_id=en.user_id
       AND (newer.version,newer.id)>(en.version,en.id)) AS newer,
   EXISTS(SELECT FROM public.stock_action_events he
    WHERE he.coin_id=ev.coin_id AND
     (EXISTS(SELECT FROM public.stock_action_revisions hr WHERE hr.event_id=he.id
       AND hr.classification NOT IN ('supported_dividend','supported_forward_split'))
      OR EXISTS(SELECT FROM public.stock_action_observations ob WHERE ob.event_id=he.id
        AND ob.source_kind='missing_or_uncertain'))
    AND NOT EXISTS(SELECT FROM public.stock_action_resolutions rs
      WHERE rs.event_id=he.id AND rs.coin_id=he.coin_id
      AND rs.expected_revision=he.current_revision_id
      AND rs.decision IN
('confirm_no_effect','accept_corrected_supported_revision','link_verified_alias')
      AND rs.evidence->'format'='1'::jsonb
      AND rs.evidence->'held_revision_ids'=(SELECT jsonb_agg(h.id ORDER BY h.id)
       FROM (SELECT id FROM public.stock_action_revisions WHERE event_id=he.id
         ORDER BY id LIMIT 129) h)
      AND NOT EXISTS(SELECT FROM public.stock_action_observations ob WHERE ob.event_id=he.id
       AND ob.source_kind='missing_or_uncertain' AND ob.id>CASE WHEN
        rs.evidence->>'observation_id' ~ '^[0-9]{1,16}$'
        THEN (rs.evidence->>'observation_id')::bigint ELSE 0 END))) AS held
 INTO r FROM public.stock_action_events ev
 JOIN public.stock_action_revisions rv ON rv.id=ev.current_revision_id AND rv.event_id=ev.id
 JOIN public.stock_instruments i ON i.coin_id=ev.coin_id
 JOIN public.coins c ON c.id=i.coin_id
 JOIN public.stock_action_state st ON st.coin_id=ev.coin_id
 LEFT JOIN public.stock_dividend_entitlements en ON en.id=p_entitlement
 LEFT JOIN public.accounts ac ON ac.id=en.portfolio_id AND ac.user_id=en.user_id
 LEFT JOIN public.stock_sessions se ON se.exchange=i.listing_exchange
   AND se.session_date=CASE WHEN p_verified THEN (rv.normalized_terms->>'ex_date')::date ELSE
NULL END
 WHERE ev.id=p_event;
 n:=clock_timestamp();
 IF NOT FOUND OR p_revision IS NULL OR (r.revision).fingerprint IS DISTINCT FROM p_revision
 THEN RAISE EXCEPTION 'dividend authority changed' USING ERRCODE='22023'; END IF;
 IF r.portfolio_id IS NULL OR r.portfolio_closed_at IS NOT NULL THEN
   RAISE EXCEPTION 'dividend portfolio unavailable' USING ERRCODE='22023'; END IF;
 catalog:=public.stock_catalog_action_context(
   (r.event).coin_id,p_event,(r.revision).id,n,(r.entitlement).cutoff,p_verified);
 IF catalog IS NOT NULL THEN
   r.admissions:=(SELECT jsonb_agg(ad) FROM jsonb_array_elements(r.admissions) ad
     WHERE ad->>'product'='calendar'
       AND ad->'scope'->'account'=catalog->'admission'->'scope'->'account'
       AND ad->'scope'->'server'=catalog->'admission'->'scope'->'server');
 END IF;
 result:=to_jsonb(r);
 IF catalog IS NOT NULL THEN result:=result||jsonb_build_object('catalog',catalog); END IF;
 IF p_expected IS NOT NULL AND result IS DISTINCT FROM p_expected THEN
   RAISE EXCEPTION 'dividend authority changed after wait' USING ERRCODE='22023';
 END IF;
 IF jsonb_array_length(r.admissions) IS DISTINCT FROM
   (CASE WHEN catalog IS NULL THEN 3 ELSE 1 END) THEN
   RAISE EXCEPTION 'dividend rights missing' USING ERRCODE='22023'; END IF;
 FOR a IN SELECT value FROM jsonb_array_elements(r.admissions) LOOP
   IF NOT coalesce(a->>'state'='approved' AND (a->>'generation')::bigint>0
     AND (a->>'reviewed_at')::timestamptz<=n
     AND (a->>'valid_from')::timestamptz<=n AND n<(a->>'valid_until')::timestamptz
     AND length(a->>'evidence_ref') BETWEEN 1 AND 2048
     AND length(a->>'terms_version') BETWEEN 1 AND 256
     AND length(a->>'attribution') BETWEEN 1 AND 2048
     AND a->'collection_allowed'='true'::jsonb
     AND a->'derived_allowed'='true'::jsonb
     AND (a->>'product'='calendar' OR
       (a->'retention_allowed'='true'::jsonb AND a->'display_allowed'='true'::jsonb))
     AND a->'scope' @> '{"application":"birja","audience":"authenticated-users"}'::jsonb
     AND (catalog IS NOT NULL OR a->'scope' @> '{"account":"birja","server":"birja"}'::jsonb)
     AND a->'scope'->>'feed'=CASE WHEN a->>'product'='actions'
       THEN 'alpaca-corporate-actions' ELSE 'iex' END
     AND a->'scope' @> '{"durable_accounting": true,"backup_restore": true,"retention_mode":
"durable-accounting"}'::jsonb
     AND jsonb_typeof(a->'quota'->'requests_per_minute')='number'
     AND (a->'quota'->>'requests_per_minute')::numeric BETWEEN 1 AND 200
     AND
(a->'quota'->>'requests_per_minute')::numeric=trunc((a->'quota'->>'requests_per_minute')::numeric)
     AND jsonb_typeof(a->'quota'->'symbols_per_request')='number'
     AND (a->'quota'->>'symbols_per_request')::numeric BETWEEN 20 AND 1000
     AND
(a->'quota'->>'symbols_per_request')::numeric=trunc((a->'quota'->>'symbols_per_request')::numeric)
     AND jsonb_typeof(a->'quota'->'max_response_bytes')='number'
     AND (a->'quota'->>'max_response_bytes')::numeric BETWEEN 1 AND 1048576
     AND
(a->'quota'->>'max_response_bytes')::numeric=trunc((a->'quota'->>'max_response_bytes')::numeric)
     AND jsonb_typeof(a->'quota'->'retention_seconds')='number'
     AND (a->'quota'->>'retention_seconds')::numeric BETWEEN 1 AND
       CASE WHEN a->>'product'='actions' THEN 315360000 ELSE 86400 END
     AND
(a->'quota'->>'retention_seconds')::numeric=trunc((a->'quota'->>'retention_seconds')::numeric)
     AND jsonb_typeof(a->'allowed_fields')='array'
     AND jsonb_array_length(a->'allowed_fields') BETWEEN 1 AND 64
     AND NOT EXISTS(SELECT FROM jsonb_array_elements(a->'allowed_fields') fld
       WHERE jsonb_typeof(fld)<>'string' OR length(fld#>>'{}') NOT BETWEEN 1 AND 64)
     AND (SELECT count(DISTINCT fld) FROM jsonb_array_elements(a->'allowed_fields') fld)
       =jsonb_array_length(a->'allowed_fields')
     AND a->'allowed_fields' @> CASE a->>'product'
       WHEN 'actions' THEN '["provider_event_id","symbol","event_type","process_date"]'::jsonb
       WHEN 'reference' THEN '["symbol","name","exchange","provider_asset_id"]'::jsonb
       ELSE '["exchange","session_date","opens_at","closes_at"]'::jsonb END,false)
   THEN RAISE EXCEPTION 'dividend rights unavailable' USING ERRCODE='22023'; END IF;
   IF a->>'product'='actions' AND NOT coalesce(
      a->'scope'->'capabilities' @> '["rest"]'::jsonb
      AND jsonb_typeof(a->'scope'->'capabilities')='array'
      AND jsonb_array_length(a->'scope'->'capabilities') BETWEEN 1 AND 2
      AND NOT EXISTS(SELECT FROM jsonb_array_elements(a->'scope'->'capabilities') cap
        WHERE cap NOT IN ('"rest"'::jsonb,'"replay"'::jsonb))
      AND (NOT a->'scope'->'capabilities' @> '["replay"]'::jsonb OR
        (a->'scope'->'all_us_replay_ingress'='true'::jsonb
          AND a->'scope'->>'replay_region'='us'))
      AND a->'scope'->'rest_symbols' @> to_jsonb(ARRAY[
       'AAPL','MSFT','NVDA','AMZN','GOOGL','META','TSLA','AVGO','AMD','COST',
       'JPM','V','JNJ','PG','KO','XOM','CVX','HD','MCD','DIS'])
      AND jsonb_array_length(a->'scope'->'rest_symbols')=20
      AND (r.revision).admission_generation=(a->>'generation')::bigint
      AND (NOT p_verified OR (r.action).admission_generation=(a->>'generation')::bigint),false)
   THEN RAISE EXCEPTION 'dividend action admission changed' USING ERRCODE='22023'; END IF;
   IF a->>'product'='calendar' AND NOT coalesce(
      n<(a->'calendar'->>'review_valid_until')::timestamptz
      AND (a->'calendar'->>'review_valid_until')::timestamptz
        <=(a->>'reviewed_at')::timestamptz+interval '24 hours'
      AND (a->'calendar'->>'coverage_start')::date <= (n AT TIME ZONE 'UTC')::date
      AND (n AT TIME ZONE 'UTC')::date <= (a->'calendar'->>'coverage_end')::date
      AND (a->'calendar'->>'coverage_start')::date
        >=((a->>'reviewed_at')::timestamptz AT TIME ZONE 'UTC')::date-45
      AND (a->'calendar'->>'coverage_end')::date
        <=((a->>'reviewed_at')::timestamptz AT TIME ZONE 'UTC')::date+90
      AND a->'calendar'->'exchanges' @> '["XNYS","XNAS"]'::jsonb
      AND jsonb_array_length(a->'calendar'->'exchanges')=2
      AND length(a->'calendar'->>'version') BETWEEN 1 AND 256
      AND jsonb_typeof(a->'calendar'->'sources')='array'
      AND jsonb_array_length(a->'calendar'->'sources') BETWEEN 2 AND 8
      AND NOT EXISTS(SELECT FROM jsonb_array_elements_text(a->'calendar'->'sources') src
        WHERE src !~ '^https://(www[.])?(nyse[.]com|nasdaq[.]com)([:]443)?(/|$)')
      AND EXISTS(SELECT FROM jsonb_array_elements_text(a->'calendar'->'sources') src
        WHERE src ~ '^https://(www[.])?nyse[.]com([:]443)?(/|$)')
      AND EXISTS(SELECT FROM jsonb_array_elements_text(a->'calendar'->'sources') src
        WHERE src ~ '^https://(www[.])?nasdaq[.]com([:]443)?(/|$)')
      AND jsonb_typeof(a->'calendar'->'overrides')='array'
      AND jsonb_array_length(a->'calendar'->'overrides')<=272,false)
   THEN RAISE EXCEPTION 'dividend calendar unavailable' USING ERRCODE='22023'; END IF;
   IF a->>'product'='calendar' THEN
     IF p_verified AND NOT coalesce(
       ((r.revision).normalized_terms->>'ex_date')::date BETWEEN
         (a->'calendar'->>'coverage_start')::date AND
         (a->'calendar'->>'coverage_end')::date,false) THEN
       RAISE EXCEPTION 'dividend cutoff outside calendar horizon' USING ERRCODE='22023';
     END IF;
     IF (SELECT count(DISTINCT (o->>'exchange',o->>'date'))
         FROM jsonb_array_elements(a->'calendar'->'overrides') o)
        <>jsonb_array_length(a->'calendar'->'overrides') THEN
       RAISE EXCEPTION 'duplicate dividend calendar override' USING ERRCODE='22023'; END IF;
     FOR v IN SELECT value FROM jsonb_array_elements(a->'calendar'->'overrides') LOOP
       IF NOT coalesce(v->>'exchange' IN ('XNYS','XNAS')
         AND (v->>'date')::date BETWEEN (a->'calendar'->>'coverage_start')::date
           AND (a->'calendar'->>'coverage_end')::date
         AND v->>'source' ~ CASE WHEN v->>'exchange'='XNYS'
           THEN '^https://(www[.])?nyse[.]com([:]443)?(/|$)'
           ELSE '^https://(www[.])?nasdaq[.]com([:]443)?(/|$)' END
         AND ((v->>'state'='closed' AND v->>'opens_at' IS NULL AND v->>'closes_at' IS NULL)
           OR (v->>'state'='shortened'
             AND (v->>'opens_at')::timestamptz<(v->>'closes_at')::timestamptz
             AND (v->>'closes_at')::timestamptz-(v->>'opens_at')::timestamptz
               <interval '6 hours 30 minutes'
             AND ((v->>'opens_at')::timestamptz AT TIME ZONE 'America/New_York')::date
               =(v->>'date')::date
             AND ((v->>'closes_at')::timestamptz AT TIME ZONE 'America/New_York')::date
               =(v->>'date')::date
             AND ((v->>'opens_at')::timestamptz AT TIME ZONE 'America/New_York')::time
               =time '09:30'
             AND ((v->>'closes_at')::timestamptz AT TIME ZONE 'America/New_York')::time
               <time '16:00')),false) THEN
         RAISE EXCEPTION 'invalid dividend calendar override' USING ERRCODE='22023'; END IF;
       IF p_verified AND v->>'exchange'=(CASE (r.instrument).listing_exchange
           WHEN 'NASDAQ' THEN 'XNAS' ELSE 'XNYS' END)
         AND (v->>'date')::date=((r.revision).normalized_terms->>'ex_date')::date
         AND (v->>'state'='closed'
           OR (v->>'opens_at')::timestamptz IS DISTINCT FROM (r.cutoff_session).opens_at
           OR (v->>'closes_at')::timestamptz IS DISTINCT FROM (r.cutoff_session).closes_at)
       THEN RAISE EXCEPTION 'dividend cutoff calendar changed' USING ERRCODE='22023'; END IF;
     END LOOP;
   ELSIF a->'calendar'<>'{}'::jsonb THEN
     RAISE EXCEPTION 'unexpected dividend calendar evidence' USING ERRCODE='22023';
   END IF;
 END LOOP;
 IF p_verified THEN
   terms:=(r.revision).normalized_terms;
   IF NOT coalesce((r.revision).classification='supported_dividend'
     AND (r.entitlement).id=p_entitlement AND (r.entitlement).event_id=p_event
     AND (r.entitlement).revision_id=(r.revision).id
     AND (r.entitlement).fingerprint=p_fingerprint AND (r.entitlement).state='eligible'
     AND (r.entitlement).cutoff=(r.cutoff_session).opens_at
     AND (r.cutoff_session).calendar_admission_generation=(
       SELECT (ad->>'generation')::bigint FROM jsonb_array_elements(r.admissions) ad
       WHERE ad->>'product'='calendar')
     AND (r.entitlement).cutoff<=n
     AND (r.entitlement).cutoff_rule='exclusive-regular-session-open'
     AND (r.entitlement).units_basis='unit_epoch:'||(r.entitlement).unit_epoch::text
     AND (r.entitlement).eligible_quantity=r.historical_quantity
     AND (r.entitlement).last_movement_sequence=r.historical_sequence
     AND ((r.entitlement).unit_epoch=r.natural_units OR r.boundary_units)
     AND NOT r.unresolved_split
     AND (r.entitlement).eligible_quantity>=0
     AND (r.entitlement).eligible_quantity<1e12
     AND (r.entitlement).eligible_quantity=trunc((r.entitlement).eligible_quantity)
     AND (r.action).health='current' AND (r.action).checked_at<=n
     AND n<(r.action).valid_until
     AND (r.action).coverage_start<=(r.action).covered_until
     AND (r.action).covered_until<=n
     AND (r.action).complete_from<=(r.entitlement).cutoff
     AND (r.action).coverage_start<=(r.entitlement).cutoff
     AND (r.action).covered_until>=(r.entitlement).cutoff
     AND NOT r.held
     AND terms->>'event_type'='cash_dividend' AND terms->>'currency'='USD'
     AND terms->>'subtype'='ordinary' AND terms->'foreign'='false'::jsonb
     AND terms->'special'='false'::jsonb AND terms->'due_bills'='false'::jsonb
     AND terms->'identity_verified'='true'::jsonb AND terms->'dates_verified'='true'::jsonb
     AND terms->'cancelled'='false'::jsonb AND terms->'identity_changed'='false'::jsonb
     AND (terms->>'rate')::numeric>=0 AND (terms->>'rate')::numeric<1e12
     AND scale((terms->>'rate')::numeric)<=8
     AND (terms->>'ex_date')::date<=(terms->>'record_date')::date
     AND (terms->>'record_date')::date<=(terms->>'payable_date')::date
     AND (terms->>'payable_date')::date<=(n AT TIME ZONE 'America/New_York')::date,false)
   OR r.newer
   THEN RAISE EXCEPTION 'dividend target unverified or not due' USING ERRCODE='22023'; END IF;
 ELSE
   IF (r.revision).classification='supported_dividend' AND NOT r.held
     AND (r.action).health='current' AND n<(r.action).valid_until
     AND (r.entitlement).event_id=p_event AND (r.entitlement).id=p_entitlement
     AND (r.entitlement).revision_id=(r.revision).id AND (r.entitlement).state='eligible'
     AND NOT r.newer THEN
     RAISE EXCEPTION 'dividend hold needs uncertainty' USING ERRCODE='22023';
   END IF;
 END IF;
 RETURN result;
END $authority$;

CREATE OR REPLACE FUNCTION public.apply_stock_dividend(
 p_event bigint,p_entitlement bigint,p_revision text,p_fingerprint text)
RETURNS TABLE(payment_id bigint,decision_id bigint,outcome text)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path=pg_catalog,public,pg_temp AS $apply$
DECLARE cid bigint; uid bigint; pid bigint; cash numeric; authority jsonb; final_authority jsonb;
 en public.stock_dividend_entitlements%ROWTYPE; rv public.stock_action_revisions%ROWTYPE;
 original public.stock_dividend_payments%ROWTYPE; prior public.stock_dividend_decisions%ROWTYPE;
 last_application bigint; desired numeric; raw numeric; cents numeric; delta numeric;
 cumulative numeric; applied numeric; result_outcome text; result_reason text; did bigint;
 terms jsonb; saved_symbol text; saved_name text; recorded timestamptz;
BEGIN
 IF current_setting('transaction_isolation')<>'read committed' THEN
   RAISE EXCEPTION 'dividend requires read committed' USING ERRCODE='22023'; END IF;
 SELECT ev.coin_id,en0.user_id,en0.portfolio_id INTO cid,uid,pid FROM public.stock_action_events ev
 JOIN public.stock_dividend_entitlements en0 ON en0.event_id=ev.id
 WHERE ev.id=p_event AND en0.id=p_entitlement;
 IF NOT FOUND THEN RAISE EXCEPTION 'dividend work missing' USING ERRCODE='22023'; END IF;
 IF EXISTS(SELECT FROM public.stock_catalog_instruments WHERE coin_id=cid) THEN
   PERFORM pg_advisory_xact_lock_shared(1026019025::bigint);
 END IF;
 PERFORM pg_advisory_xact_lock(hashtextextended('birja.stock.instrument:'||cid::text,0));
 SELECT ac.cash INTO cash FROM public.accounts ac
 WHERE ac.id=pid AND ac.user_id=uid AND ac.closed_at IS NULL FOR UPDATE;
 IF NOT FOUND THEN
   RAISE EXCEPTION 'dividend portfolio unavailable' USING ERRCODE='22023'; END IF;
 SELECT * INTO original FROM public.stock_dividend_payments p
 WHERE p.event_id=p_event AND p.portfolio_id=pid AND p.user_id=uid;
 IF original.id IS NOT NULL AND original.revision_fingerprint=p_revision
   AND original.entitlement_id=p_entitlement AND original.entitlement_fingerprint=p_fingerprint THEN
   RETURN QUERY SELECT original.id,NULL::bigint,'original'::text; RETURN;
 END IF;
 IF original.id IS NOT NULL THEN
   SELECT * INTO prior FROM public.stock_dividend_decisions d
    WHERE d.payment_id=original.id AND d.portfolio_id=pid AND d.user_id=uid AND d.revision_fingerprint=p_revision
    AND d.entitlement_id=p_entitlement AND d.entitlement_fingerprint=p_fingerprint
    AND d.outcome IN ('applied','verified_no_change') ORDER BY d.id DESC LIMIT 1;
   IF FOUND THEN RETURN QUERY SELECT original.id,prior.id,prior.outcome; RETURN; END IF;
 END IF;
authority:=public.stock_dividend_authority(p_event,p_entitlement,p_revision,p_fingerprint,true,NULL);
 en:=jsonb_populate_record(NULL::public.stock_dividend_entitlements,authority->'entitlement');
 rv:=jsonb_populate_record(NULL::public.stock_action_revisions,authority->'revision');
 terms:=rv.normalized_terms;
 raw:=en.eligible_quantity*(terms->>'rate')::numeric;
 IF NOT(raw>=0 AND raw<1e12) THEN
   RAISE EXCEPTION 'dividend numeric range' USING ERRCODE='22003'; END IF;
 cents:=trunc(raw*100);
 desired:=(cents+CASE WHEN raw*100-cents>0.5 OR
   (raw*100-cents=0.5 AND mod(cents,2)=1) THEN 1 ELSE 0 END)/100;
 IF NOT(desired>=0 AND desired<1e12 AND cash>=0 AND cash<1e12 AND cash=trunc(cash,2)) THEN
   RAISE EXCEPTION 'dividend numeric range' USING ERRCODE='22003'; END IF;
 recorded:=clock_timestamp();
 IF authority ? 'catalog' THEN
   saved_symbol:=authority->'catalog'->'label'->>'symbol';
   saved_name:=authority->'catalog'->'label'->>'name';
   IF original.id IS NOT NULL AND (original.symbol,original.company_name)
       IS DISTINCT FROM (saved_symbol,saved_name) THEN
     RAISE EXCEPTION 'catalog dividend original label changed' USING ERRCODE='22023';
   END IF;
 ELSE
   saved_symbol:=authority->'coin'->>'symbol'; saved_name:=authority->'coin'->>'name';
 END IF;
 IF original.id IS NULL THEN
   IF cash+desired>=1e12 THEN RAISE EXCEPTION 'dividend cash overflow' USING ERRCODE='22003';
END IF;
   INSERT INTO public.stock_dividend_payments(event_id,coin_id,portfolio_id,user_id,revision_id,
    revision_fingerprint,entitlement_id,entitlement_fingerprint,symbol,company_name,
    cutoff,cutoff_rule,units_basis,unit_epoch,eligible_quantity,rate,ex_date,record_date,
    payable_date,original_amount,recorded_at,cash_after)
   VALUES(p_event,cid,pid,uid,rv.id,rv.fingerprint,en.id,en.fingerprint,saved_symbol,saved_name,
en.cutoff,en.cutoff_rule,en.units_basis,en.unit_epoch,en.eligible_quantity,(terms->>'rate')::numeric,
    (terms->>'ex_date')::date,(terms->>'record_date')::date,(terms->>'payable_date')::date,
    desired,recorded,cash+desired) RETURNING * INTO original;
   UPDATE public.accounts SET cash=accounts.cash+desired WHERE id=pid AND user_id=uid AND closed_at IS NULL;
   result_outcome:='original'; did:=NULL;
 ELSE
   SELECT original.original_amount+coalesce(sum(d.applied_delta),0) INTO cumulative
     FROM public.stock_dividend_decisions d WHERE d.payment_id=original.id AND d.portfolio_id=pid AND d.user_id=uid;
   delta:=desired-cumulative;
   IF NOT(cumulative>=0 AND cumulative<1e12 AND cash+delta<1e12) THEN
     RAISE EXCEPTION 'dividend numeric range' USING ERRCODE='22003'; END IF;
   result_outcome:=CASE WHEN delta=0 THEN 'verified_no_change'
     WHEN cash+delta<0 THEN 'held_unaffordable' ELSE 'applied' END;
   result_reason:=CASE result_outcome WHEN 'applied' THEN 'target_applied'
     WHEN 'held_unaffordable' THEN 'insufficient_cash' ELSE 'target_unchanged' END;
   applied:=CASE WHEN result_outcome='applied' THEN delta ELSE 0 END;
   SELECT * INTO prior FROM public.stock_dividend_decisions d
     WHERE d.payment_id=original.id AND d.portfolio_id=pid AND d.user_id=uid ORDER BY d.id DESC LIMIT 1;
   SELECT d.id INTO last_application FROM public.stock_dividend_decisions d
     WHERE d.payment_id=original.id AND d.portfolio_id=pid AND d.user_id=uid AND d.outcome IN ('applied','verified_no_change')
     ORDER BY d.id DESC LIMIT 1;
   INSERT INTO public.stock_dividend_decisions(payment_id,portfolio_id,user_id,event_id,coin_id,
    revision_id,revision_fingerprint,entitlement_id,entitlement_fingerprint,
    previous_decision_id,previous_application_id,desired_total,cumulative_applied_before,
    proposed_delta,applied_delta,outcome,reason,status_identity,recorded_at,cash_after,
    symbol,company_name,cutoff,cutoff_rule,units_basis,unit_epoch,eligible_quantity,rate,
    ex_date,record_date,payable_date)
   VALUES(original.id,pid,uid,p_event,cid,rv.id,rv.fingerprint,en.id,en.fingerprint,
    prior.id,last_application,desired,cumulative,delta,applied,result_outcome,result_reason,
    'epoch:'||(authority->'action'->>'epoch')||':'||result_reason,
    recorded,cash+applied,saved_symbol,saved_name,en.cutoff,en.cutoff_rule,en.units_basis,
    en.unit_epoch,en.eligible_quantity,(terms->>'rate')::numeric,(terms->>'ex_date')::date,
    (terms->>'record_date')::date,(terms->>'payable_date')::date)
   ON CONFLICT DO NOTHING RETURNING id INTO did;
   IF did IS NULL THEN
     SELECT d.id INTO STRICT did FROM public.stock_dividend_decisions d
      WHERE d.payment_id=original.id AND d.portfolio_id=pid AND d.user_id=uid AND d.revision_fingerprint=rv.fingerprint
      AND d.entitlement_id=en.id AND d.status_identity=
        'epoch:'||(authority->'action'->>'epoch')||':'||result_reason
      AND d.outcome=result_outcome ORDER BY d.id DESC LIMIT 1;
   ELSIF applied<>0 THEN
     UPDATE public.accounts SET cash=accounts.cash+applied WHERE id=pid AND user_id=uid AND closed_at IS NULL;
   END IF;
 END IF;
 SET CONSTRAINTS ALL IMMEDIATE;
 final_authority:=public.stock_dividend_authority(
   p_event,p_entitlement,p_revision,p_fingerprint,true,authority);
 RETURN QUERY SELECT original.id,did,result_outcome;
END $apply$;

CREATE OR REPLACE FUNCTION public.record_stock_dividend_hold(p_payment bigint,p_revision text)
RETURNS TABLE(payment_id bigint,decision_id bigint,outcome text)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path=pg_catalog,public,pg_temp AS $hold$
DECLARE original public.stock_dividend_payments%ROWTYPE;
 en public.stock_dividend_entitlements%ROWTYPE; rv public.stock_action_revisions%ROWTYPE;
 authority jsonb; final_authority jsonb; cash numeric; cumulative numeric;
 prior bigint; application bigint; did bigint; status text;
BEGIN
 IF current_setting('transaction_isolation')<>'read committed' THEN
   RAISE EXCEPTION 'dividend requires read committed' USING ERRCODE='22023'; END IF;
 SELECT * INTO STRICT original FROM public.stock_dividend_payments p WHERE p.id=p_payment;
 IF EXISTS(SELECT FROM public.stock_catalog_instruments WHERE coin_id=original.coin_id) THEN
   PERFORM pg_advisory_xact_lock_shared(1026019025::bigint);
 END IF;
 PERFORM pg_advisory_xact_lock(hashtextextended('birja.stock.instrument:'||original.coin_id::text,0));
 SELECT ac.cash INTO cash FROM public.accounts ac
 WHERE ac.id=original.portfolio_id AND ac.user_id=original.user_id
 AND ac.closed_at IS NULL FOR UPDATE;
 IF NOT FOUND THEN
   RAISE EXCEPTION 'dividend portfolio unavailable' USING ERRCODE='22023'; END IF;
 SELECT * INTO en FROM public.stock_dividend_entitlements e
   WHERE e.event_id=original.event_id AND e.portfolio_id=original.portfolio_id
   AND e.user_id=original.user_id
   ORDER BY e.version DESC,e.id DESC LIMIT 1;
 authority:=public.stock_dividend_authority(original.event_id,en.id,p_revision,NULL,false,NULL);
 IF authority ? 'catalog' AND (original.symbol,original.company_name) IS DISTINCT FROM
     (authority->'catalog'->'label'->>'symbol',authority->'catalog'->'label'->>'name') THEN
   RAISE EXCEPTION 'catalog dividend original label changed' USING ERRCODE='22023';
 END IF;
 rv:=jsonb_populate_record(NULL::public.stock_action_revisions,authority->'revision');
 status:='epoch:'||(authority->'action'->>'epoch')||chr(58)||'terms_unverified';
 SELECT d.id INTO did FROM public.stock_dividend_decisions d WHERE d.payment_id=original.id AND d.portfolio_id=original.portfolio_id
   AND d.user_id=original.user_id
   AND d.revision_fingerprint=p_revision AND d.entitlement_id IS NOT DISTINCT FROM
     CASE WHEN en.revision_id=rv.id THEN en.id ELSE NULL END
   AND d.status_identity=status AND d.outcome='held_uncertain';
 IF did IS NULL THEN
   SELECT original.original_amount+coalesce(sum(d.applied_delta),0) INTO cumulative
     FROM public.stock_dividend_decisions d WHERE d.payment_id=original.id AND d.portfolio_id=original.portfolio_id
   AND d.user_id=original.user_id;
   SELECT d.id INTO prior FROM public.stock_dividend_decisions d
     WHERE d.payment_id=original.id AND d.portfolio_id=original.portfolio_id
   AND d.user_id=original.user_id ORDER BY d.id DESC LIMIT 1;
   SELECT d.id INTO application FROM public.stock_dividend_decisions d
     WHERE d.payment_id=original.id AND d.portfolio_id=original.portfolio_id
   AND d.user_id=original.user_id AND d.outcome IN ('applied','verified_no_change')
     ORDER BY d.id DESC LIMIT 1;
   INSERT INTO public.stock_dividend_decisions(payment_id,portfolio_id,user_id,event_id,coin_id,
    revision_id,revision_fingerprint,entitlement_id,entitlement_fingerprint,
    previous_decision_id,previous_application_id,cumulative_applied_before,
    applied_delta,outcome,reason,status_identity,recorded_at,cash_after,symbol,company_name)
   VALUES(original.id,original.portfolio_id,original.user_id,original.event_id,original.coin_id,rv.id,rv.fingerprint,
    CASE WHEN en.revision_id=rv.id THEN en.id ELSE NULL END,
    CASE WHEN en.revision_id=rv.id THEN en.fingerprint ELSE NULL END,
    prior,application,cumulative,0,'held_uncertain','terms_unverified',status,
    clock_timestamp(),cash,original.symbol,original.company_name) RETURNING id INTO did;
 END IF;
 SET CONSTRAINTS ALL IMMEDIATE;
final_authority:=public.stock_dividend_authority(original.event_id,en.id,p_revision,NULL,false,authority);
 RETURN QUERY SELECT original.id,did,'held_uncertain'::text;
END $hold$;

CREATE OR REPLACE FUNCTION public.apply_stock_action_resolution(
 p_coin bigint,p_event bigint,p_revision bigint,p_generation bigint,p_epoch bigint,
 p_key text,p_decision text,p_hash text,p_evidence jsonb,p_actor text
) RETURNS bigint LANGUAGE plpgsql SECURITY DEFINER
SET search_path = pg_catalog, public AS $resolution$
DECLARE
 st public.stock_action_state%ROWTYPE;
 ev public.stock_action_events%ROWTYPE;
 rev public.stock_action_revisions%ROWTYPE;
 adm public.stock_data_admissions%ROWTYPE;
 cal public.stock_data_admissions%ROWTYPE;
 old public.stock_action_resolutions%ROWTYPE;
 now_at timestamptz;
 ledger text;
 history jsonb;
 observations bigint;
 inserted bigint;
 is_catalog boolean;
 catalog jsonb;
BEGIN
 IF p_coin IS NULL OR p_event IS NULL OR p_revision IS NULL OR p_generation IS NULL
 OR p_epoch IS NULL OR p_key IS NULL OR length(p_key) NOT BETWEEN 1 AND 256
 OR p_actor IS NULL OR length(p_actor) NOT BETWEEN 1 AND 256
 OR p_decision IS NULL OR p_decision NOT IN
 ('confirm_no_effect','accept_corrected_supported_revision','link_verified_alias')
 OR p_hash IS NULL OR p_hash !~ '^[0-9a-f]{64}$'
 OR p_evidence IS NULL OR jsonb_typeof(p_evidence) <> 'object'
 OR octet_length(p_evidence::text)>16384 THEN
   RAISE EXCEPTION 'resolution evidence rejected' USING ERRCODE='22023';
 END IF;
 IF p_evidence - ARRAY['format','unit_epoch','ledger_digest','revision_fingerprint',
 'held_revision_ids','observation_id','account','server','calendar_generation',
 'review_valid_until','security_id','cutoff','alias_event_id','calendar_digest',
 'admission_digest'] <> '{}'::jsonb
 OR NOT p_evidence ?& ARRAY['format','unit_epoch','ledger_digest','revision_fingerprint',
 'held_revision_ids','observation_id','account','server','calendar_generation',
 'review_valid_until','security_id','cutoff','alias_event_id','calendar_digest','admission_digest']
 OR p_evidence->'format' <> '1'::jsonb
 OR p_hash <> encode(sha256(convert_to(p_evidence::text,'UTF8')),'hex') THEN
   RAISE EXCEPTION 'resolution evidence rejected' USING ERRCODE='22023';
 END IF;
 SELECT EXISTS(SELECT FROM public.stock_catalog_instruments WHERE coin_id=p_coin) INTO is_catalog;
 IF is_catalog THEN PERFORM pg_advisory_xact_lock_shared(1026019025::bigint); END IF;
 PERFORM pg_advisory_xact_lock(hashtextextended('birja.stock.instrument:'||p_coin::text,0));
 SELECT * INTO old FROM public.stock_action_resolutions
   WHERE coin_id=p_coin AND decision_key=p_key;
 IF FOUND THEN
   IF old.event_id=p_event AND old.expected_revision=p_revision
   AND old.admission_generation=p_generation AND old.epoch=p_epoch
   AND old.decision=p_decision AND old.evidence_hash=p_hash
   AND old.evidence=p_evidence AND old.actor_ref=p_actor THEN RETURN old.id; END IF;
   RAISE EXCEPTION 'resolution replay conflict' USING ERRCODE='22023';
 END IF;
 SELECT * INTO st FROM public.stock_action_state WHERE coin_id=p_coin FOR UPDATE;
 SELECT * INTO ev FROM public.stock_action_events WHERE id=p_event AND coin_id=p_coin;
 SELECT * INTO rev FROM public.stock_action_revisions WHERE id=p_revision AND event_id=p_event;
 IF NOT is_catalog THEN
   SELECT * INTO adm FROM public.stock_data_admissions WHERE product='actions' FOR SHARE;
 END IF;
 SELECT * INTO cal FROM public.stock_data_admissions WHERE product='calendar' FOR SHARE;
 -- Time is read after every blocking lock, never transaction_timestamp().
 now_at := clock_timestamp();
 IF is_catalog THEN
   catalog:=public.stock_catalog_action_context(p_coin,p_event,p_revision,now_at,NULL,false);
 END IF;
 IF st.coin_id IS NULL OR ev.id IS NULL OR rev.id IS NULL
 OR ev.current_revision_id IS DISTINCT FROM p_revision
 OR st.epoch IS DISTINCT FROM p_epoch
 OR st.admission_generation IS DISTINCT FROM p_generation
 OR (is_catalog AND (
   catalog IS NULL OR catalog->'admission'->>'id' IS DISTINCT FROM p_generation::text
   OR encode(sha256(convert_to((catalog->'admission')::text,'UTF8')),'hex')
     IS DISTINCT FROM p_evidence->>'admission_digest'
   OR catalog->>'provider_asset_id' IS DISTINCT FROM p_evidence->>'security_id'
   OR catalog->'admission'->'scope'->>'account' IS DISTINCT FROM p_evidence->>'account'
   OR catalog->'admission'->'scope'->>'server' IS DISTINCT FROM p_evidence->>'server'))
 OR (NOT is_catalog AND (adm.generation IS DISTINCT FROM p_generation
   OR encode(sha256(convert_to(to_jsonb(adm)::text,'UTF8')),'hex')
     IS DISTINCT FROM p_evidence->>'admission_digest'))
 OR rev.admission_generation IS DISTINCT FROM p_generation
 OR st.unit_epoch::text IS DISTINCT FROM p_evidence->>'unit_epoch'
 OR rev.fingerprint IS DISTINCT FROM p_evidence->>'revision_fingerprint'
 OR cal.state IS DISTINCT FROM 'approved'
 OR (NOT is_catalog AND (adm.state IS DISTINCT FROM 'approved'
   OR NOT coalesce(adm.collection_allowed AND adm.derived_allowed AND adm.retention_allowed,false)))
 OR NOT coalesce(cal.collection_allowed AND cal.derived_allowed,false)
 OR (NOT is_catalog AND NOT coalesce(adm.valid_from<=now_at AND now_at<adm.valid_until,false))
 OR NOT coalesce(cal.valid_from<=now_at AND now_at<cal.valid_until,false)
 OR NOT coalesce(now_at<(cal.calendar->>'review_valid_until')::timestamptz,false)
 OR NOT coalesce(now_at<(p_evidence->>'review_valid_until')::timestamptz
     AND (p_evidence->>'review_valid_until')::timestamptz<=CASE WHEN is_catalog
       THEN (catalog->'admission'->>'valid_until')::timestamptz ELSE adm.valid_until END
     AND (p_evidence->>'review_valid_until')::timestamptz<=cal.valid_until,false)
 OR cal.generation::text IS DISTINCT FROM p_evidence->>'calendar_generation'
 OR encode(sha256(convert_to(to_jsonb(cal)::text,'UTF8')),'hex')
    IS DISTINCT FROM p_evidence->>'calendar_digest'
 OR cal.scope->>'account' IS DISTINCT FROM p_evidence->>'account'
 OR cal.scope->>'server' IS DISTINCT FROM p_evidence->>'server'
 OR (NOT is_catalog AND (adm.scope->>'application' IS DISTINCT FROM 'birja'
   OR adm.scope->>'audience' IS DISTINCT FROM 'authenticated-users'
   OR adm.scope->>'feed' IS DISTINCT FROM 'alpaca-corporate-actions'
   OR adm.scope->>'account' IS DISTINCT FROM p_evidence->>'account'
   OR adm.scope->>'server' IS DISTINCT FROM p_evidence->>'server'
   OR adm.scope->'durable_accounting' IS DISTINCT FROM 'true'::jsonb
   OR adm.scope->'backup_restore' IS DISTINCT FROM 'true'::jsonb
   OR adm.scope->>'retention_mode' IS DISTINCT FROM 'durable-accounting'
   OR NOT coalesce(adm.scope->'capabilities' ? 'rest',false)
   OR NOT EXISTS(SELECT FROM public.stock_instruments i JOIN public.coins c ON c.id=i.coin_id
     WHERE i.coin_id=p_coin AND i.provider_asset_id=p_evidence->>'security_id'
     AND i.provider_verified_at IS NOT NULL AND c.asset_class='stock' AND c.is_active
     AND rev.normalized_terms->>'coin_id'=p_coin::text
     AND rev.normalized_terms->>'symbol'=c.symbol)))
 THEN RAISE EXCEPTION 'resolution state stale' USING ERRCODE='22023'; END IF;
 SELECT encode(sha256(convert_to(coalesce(jsonb_agg(to_jsonb(m) ORDER BY m.sequence),
   '[]'::jsonb)::text,'UTF8')),'hex') INTO ledger
   FROM public.stock_ownership_movements m WHERE m.coin_id=p_coin;
 SELECT coalesce(jsonb_agg(r.id ORDER BY r.id),'[]'::jsonb) INTO history
   FROM public.stock_action_revisions r WHERE r.event_id=p_event;
 SELECT coalesce(max(o.id),0) INTO observations FROM public.stock_action_observations o
   WHERE o.event_id=p_event;
 IF ledger IS DISTINCT FROM p_evidence->>'ledger_digest'
 OR history IS DISTINCT FROM p_evidence->'held_revision_ids'
 OR jsonb_array_length(history)>128
 OR observations::text IS DISTINCT FROM p_evidence->>'observation_id'
 OR EXISTS(SELECT FROM public.stock_split_applications WHERE economic_event_id=p_event)
 OR EXISTS(SELECT FROM public.stock_dividend_entitlements WHERE event_id=p_event)
 THEN RAISE EXCEPTION 'resolution history changed' USING ERRCODE='22023'; END IF;
 -- No economic rewrite: all fills and historical ownership must precede the
 -- verified prospective cutoff. Applied or late economic changes remain held.
 IF p_evidence->>'cutoff' IS NULL
 OR (p_evidence->>'cutoff')::timestamptz<=now_at
 OR EXISTS(SELECT FROM public.stock_ownership_movements WHERE coin_id=p_coin
   AND economic_at>=(p_evidence->>'cutoff')::timestamptz)
 THEN RAISE EXCEPTION 'resolution requires financial repair' USING ERRCODE='22023'; END IF;
 IF p_decision IN ('accept_corrected_supported_revision','link_verified_alias') THEN
   IF rev.classification NOT IN ('supported_dividend','supported_forward_split')
   OR rev.normalized_terms->'identity_verified' IS DISTINCT FROM 'true'::jsonb
   OR rev.normalized_terms->'identity_changed' IS DISTINCT FROM 'false'::jsonb
   OR rev.normalized_terms->'dates_verified' IS DISTINCT FROM 'true'::jsonb
   OR rev.normalized_terms->'cancelled' IS DISTINCT FROM 'false'::jsonb
   OR NOT EXISTS(SELECT FROM public.stock_sessions s JOIN public.stock_instruments i
      ON i.listing_exchange=s.exchange WHERE i.coin_id=p_coin
      AND s.calendar_admission_generation=cal.generation
      AND s.session_date=(rev.normalized_terms->>'ex_date')::date
      AND s.opens_at=(p_evidence->>'cutoff')::timestamptz)
   OR (rev.classification='supported_dividend' AND NOT coalesce(
      rev.normalized_terms->>'event_type'='cash_dividend'
      AND rev.normalized_terms->>'currency'='USD'
      AND rev.normalized_terms->>'subtype'='ordinary'
      AND rev.normalized_terms->'foreign'='false'::jsonb
      AND rev.normalized_terms->'special'='false'::jsonb
      AND rev.normalized_terms->'due_bills'='false'::jsonb
      AND rev.normalized_terms->'same_boundary_split'='false'::jsonb
      AND rev.normalized_terms->>'rate' ~ '^[0-9]{1,12}(\.[0-9]{1,8})?$'
      AND (rev.normalized_terms->>'rate')::numeric>0
      AND (rev.normalized_terms->>'ex_date')::date <=
          (rev.normalized_terms->>'record_date')::date
      AND (rev.normalized_terms->>'record_date')::date <=
          (rev.normalized_terms->>'payable_date')::date,false))
   OR (rev.classification='supported_forward_split' AND NOT coalesce(
      rev.normalized_terms->>'event_type'='forward_split'
      AND rev.normalized_terms->>'units'='pre_split'
      AND rev.normalized_terms->'due_bills'='false'::jsonb
      AND rev.normalized_terms->>'new_rate' ~ '^[0-9]{1,9}(\.[0-9]{1,8})?$'
      AND rev.normalized_terms->>'old_rate' ~ '^[0-9]{1,9}(\.[0-9]{1,8})?$'
      AND (rev.normalized_terms->>'new_rate')::numeric>
          (rev.normalized_terms->>'old_rate')::numeric
      AND (rev.normalized_terms->>'old_rate')::numeric>0
      AND rev.verified_cutoff=(p_evidence->>'cutoff')::timestamptz,false))
   THEN RAISE EXCEPTION 'unsupported corrected terms' USING ERRCODE='22023'; END IF;
 END IF;
 IF p_decision='confirm_no_effect' THEN
   IF rev.classification<>'cancelled' OR rev.mutation_kind<>'delete'
   OR rev.normalized_terms->'identity_verified' IS DISTINCT FROM 'true'::jsonb
   OR rev.normalized_terms->'identity_changed' IS DISTINCT FROM 'false'::jsonb
   OR rev.normalized_terms->'cancelled' IS DISTINCT FROM 'true'::jsonb
   THEN RAISE EXCEPTION 'no verified cancellation' USING ERRCODE='22023'; END IF;
 ELSIF p_decision='link_verified_alias' THEN
   -- Cross-event aliases cannot be safely linked by changing only an audit
   -- row. Require an already verified same-event source alias; do not merge
   -- independent economic/application identities.
   IF p_evidence->>'alias_event_id' IS DISTINCT FROM p_event::text
   OR (SELECT count(*) FROM public.stock_action_sources WHERE event_id=p_event)<2
   OR rev.classification NOT IN ('supported_dividend','supported_forward_split')
   OR EXISTS(SELECT FROM public.stock_action_sources src
      LEFT JOIN LATERAL (SELECT other.*,o.source_kind,
          o.admission_generation AS observation_generation
        FROM public.stock_action_observations o
        JOIN public.stock_action_revisions other ON other.id=o.revision_id
        WHERE o.source_id=src.id AND o.event_id=p_event
        ORDER BY o.id DESC LIMIT 1) latest ON true
      WHERE src.event_id=p_event AND (
        src.provider<>'alpaca' OR src.product<>'actions'
        OR latest.id IS NULL OR latest.source_kind NOT IN ('rest','replay')
        OR latest.observation_generation IS DISTINCT FROM p_generation
        OR latest.normalized_terms IS DISTINCT FROM rev.normalized_terms
        OR latest.classification IS DISTINCT FROM rev.classification
        OR latest.units IS DISTINCT FROM rev.units
        OR latest.verified_cutoff IS DISTINCT FROM rev.verified_cutoff
        OR latest.admission_generation IS DISTINCT FROM p_generation))
   THEN RAISE EXCEPTION 'unverified alias' USING ERRCODE='22023'; END IF;
 END IF;
 INSERT INTO public.stock_action_resolutions(event_id,coin_id,expected_revision,
 admission_generation,epoch,decision,decision_key,evidence,evidence_hash,before_digest,
 after_digest,actor_ref,created_at)
 VALUES(p_event,p_coin,p_revision,p_generation,p_epoch,p_decision,p_key,p_evidence,p_hash,
 ledger,ledger,p_actor,clock_timestamp()) RETURNING id INTO inserted;
 UPDATE public.stock_action_state SET epoch=epoch+1,health='reconciling',valid_until=NULL
   WHERE coin_id=p_coin;
 RETURN inserted;
END
$resolution$;

CREATE OR REPLACE FUNCTION public.check_stock_split_digest_version() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public,pg_temp AS $version$
DECLARE
 catalog jsonb;
 revision public.stock_action_revisions%ROWTYPE;
 at_time timestamptz;
BEGIN
 IF NEW.owner_digest_version IS DISTINCT FROM 2::smallint THEN
   RAISE EXCEPTION 'new stock split requires explicit digest version2' USING ERRCODE='23514';
 END IF;
 IF NOT EXISTS(SELECT FROM public.stock_catalog_instruments WHERE coin_id=NEW.coin_id) THEN
   RETURN NEW;
 END IF;
 PERFORM pg_advisory_xact_lock_shared(1026019025::bigint);
 PERFORM pg_advisory_xact_lock(hashtextextended('birja.stock.instrument:'||NEW.coin_id::text,0));
 at_time:=clock_timestamp();
 catalog:=public.stock_catalog_action_context(
   NEW.coin_id,NEW.economic_event_id,NEW.revision_id,at_time,NEW.cutoff,true);
 SELECT * INTO revision FROM public.stock_action_revisions WHERE id=NEW.revision_id;
 IF NOT coalesce(
   revision.classification='supported_forward_split'
   AND revision.verified_cutoff=NEW.cutoff AND revision.units='pre_split'
   AND revision.normalized_terms->>'event_type'='forward_split'
   AND revision.normalized_terms @> '{"identity_verified":true,"identity_changed":false,
     "dates_verified":true,"cancelled":false,"due_bills":false,"units":"pre_split"}'::jsonb
   AND (revision.normalized_terms->>'new_rate')::numeric=NEW.new_rate::numeric
   AND (revision.normalized_terms->>'old_rate')::numeric=NEW.old_rate::numeric
   AND NEW.new_rate::numeric>NEW.old_rate::numeric AND NEW.old_rate::numeric>0
   AND NEW.cutoff<=NEW.processed_at AND NEW.processed_at<=at_time
   AND NEW.prior_unit_epoch=(SELECT coalesce(max(s.new_unit_epoch),0)
     FROM public.stock_split_applications s WHERE s.coin_id=NEW.coin_id)
   AND NEW.sequence_boundary=(SELECT coalesce(max(m.sequence),0)
     FROM public.stock_ownership_movements m WHERE m.coin_id=NEW.coin_id)
   AND NOT EXISTS(SELECT FROM public.stock_ownership_movements m
     WHERE m.coin_id=NEW.coin_id AND m.economic_at>=NEW.cutoff)
   AND EXISTS(SELECT FROM public.stock_sessions s
     JOIN public.stock_instruments i ON i.listing_exchange=s.exchange AND i.coin_id=NEW.coin_id
     JOIN public.stock_data_admissions a ON a.product='calendar'
     WHERE s.session_date=(revision.normalized_terms->>'ex_date')::date
       AND s.opens_at=NEW.cutoff AND s.calendar_admission_generation=a.generation
       AND a.state='approved' AND a.collection_allowed AND a.derived_allowed
       AND a.scope->'account'=catalog->'admission'->'scope'->'account'
       AND a.scope->'server'=catalog->'admission'->'scope'->'server'
       AND a.valid_from<=at_time AND at_time<a.valid_until
       AND at_time<(a.calendar->>'review_valid_until')::timestamptz),false)
 THEN RAISE EXCEPTION 'catalog split authority unavailable' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END $version$;

CREATE FUNCTION public.check_stock_catalog_split_movements() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public,pg_temp AS $catalog_split$
BEGIN
 IF NOT EXISTS(SELECT FROM public.stock_catalog_instruments WHERE coin_id=NEW.coin_id) THEN
   RETURN NULL;
 END IF;
 IF NOT EXISTS(SELECT FROM public.stock_action_state s WHERE s.coin_id=NEW.coin_id
     AND s.unit_epoch>=NEW.new_unit_epoch AND s.quote_not_before>=NEW.cutoff)
 OR EXISTS(
   WITH before_split AS (
     SELECT DISTINCT ON (m.portfolio_id) m.portfolio_id,m.user_id,m.after_quantity,m.after_basis
     FROM public.stock_ownership_movements m
     JOIN public.accounts a ON a.id=m.portfolio_id AND a.user_id=m.user_id
     WHERE m.coin_id=NEW.coin_id AND m.sequence<=NEW.sequence_boundary AND a.closed_at IS NULL
     ORDER BY m.portfolio_id,m.sequence DESC
   ), eligible AS (
     SELECT * FROM before_split WHERE after_quantity>0
   ), applied AS (
     SELECT * FROM public.stock_ownership_movements WHERE application_id=NEW.id
   )
   SELECT FROM eligible e FULL JOIN applied m USING(portfolio_id,user_id)
   LEFT JOIN public.holdings h
     ON (h.portfolio_id,h.user_id,h.coin_id)=(m.portfolio_id,m.user_id,NEW.coin_id)
   WHERE e.portfolio_id IS NULL OR m.id IS NULL
     OR m.cause_kind<>'split' OR m.economic_at<>NEW.cutoff
     OR m.sequence<=NEW.sequence_boundary OR m.unit_epoch<>NEW.new_unit_epoch
     OR m.before_quantity<>e.after_quantity OR m.before_basis<>e.after_basis
     OR m.after_basis<>e.after_basis
     OR m.after_quantity*NEW.old_rate::numeric<>e.after_quantity*NEW.new_rate::numeric
     OR m.after_quantity<>trunc(m.after_quantity)
     OR m.after_quantity>=1e12
     OR (h.quantity,h.cost_basis) IS DISTINCT FROM (m.after_quantity,m.after_basis)
 )
 OR EXISTS(SELECT FROM public.stock_ownership_movements WHERE application_id=NEW.id
     GROUP BY portfolio_id HAVING count(*)<>1)
 THEN RAISE EXCEPTION 'catalog split movements refused' USING ERRCODE='23514'; END IF;
 PERFORM public.stock_catalog_action_context(
   NEW.coin_id,NEW.economic_event_id,NEW.revision_id,clock_timestamp(),NEW.cutoff,true);
 RETURN NULL;
END $catalog_split$;

ALTER FUNCTION public.check_stock_catalog_split_movements() OWNER TO birja_migrator;
REVOKE ALL ON FUNCTION public.check_stock_catalog_split_movements() FROM PUBLIC;
CREATE CONSTRAINT TRIGGER stock_catalog_split_movements
 AFTER INSERT ON public.stock_split_applications DEFERRABLE INITIALLY DEFERRED
 FOR EACH ROW EXECUTE FUNCTION public.check_stock_catalog_split_movements();
