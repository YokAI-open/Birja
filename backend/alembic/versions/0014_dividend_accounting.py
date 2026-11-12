"""dividend_accounting

Revision ID: 0014
Revises: 0013
Create Date: 2026-11-12 19:59:37.870925

"""

from collections.abc import Sequence

import sqlalchemy as sa  # noqa: F401
from alembic import op  # noqa: F401

# revision identifiers, used by Alembic.
revision: str = "0014"
down_revision: str | Sequence[str] | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Existing relations receive concurrent indexes before any transactional0014
# objects. Exact interrupted builds are resumable; unrelated names fail closed.
EXISTING_INDEXES = (
    (
        "uq_stock_action_revision_dividend_identity",
        "stock_action_revisions",
        ["id", "event_id", "fingerprint"],
        True,
    ),
    (
        "uq_stock_entitlement_dividend_identity",
        "stock_dividend_entitlements",
        ["id", "event_id", "user_id", "revision_id", "fingerprint"],
        True,
    ),
    (
        "ix_stock_entitlement_current_work",
        "stock_dividend_entitlements",
        ["event_id", "user_id", "id"],
        False,
    ),
    (
        "ix_stock_ownership_user_recorded_id",
        "stock_ownership_movements",
        ["user_id", "recorded_at", "id"],
        False,
    ),
)


def _prepare_existing_indexes() -> None:
    for name, table, columns, unique in EXISTING_INDEXES:
        existing = None
        if not op.get_context().as_sql:
            existing = (
                op.get_bind()
                .execute(
                    sa.text("""SELECT c.relkind::text AS kind,
              c.relowner=t.relowner AS table_owned,
              pg_get_userbyid(c.relowner)=current_user AS migration_owned,
              pg_get_indexdef(c.oid) AS definition,i.indisvalid,i.indisready,i.indislive,
              EXISTS(SELECT FROM pg_constraint WHERE conindid=c.oid) AS attached
              FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
              JOIN pg_class t ON t.oid=to_regclass(:table)
              LEFT JOIN pg_index i ON i.indexrelid=c.oid
              WHERE n.nspname='public' AND c.relname=:name"""),
                    {"table": f"public.{table}", "name": name},
                )
                .mappings()
                .one_or_none()
            )
            expected = (
                f"CREATE {'UNIQUE ' if unique else ''}INDEX {name} "
                f"ON public.{table} USING btree ({', '.join(columns)})"
            )
            if existing is not None and (
                existing["kind"] != "i"
                or not existing["table_owned"]
                or not existing["migration_owned"]
                or not existing["indislive"]
                or existing["attached"]
                or existing["definition"] != expected
            ):
                raise RuntimeError("incompatible preexisting dividend index")
        if existing is None or not (existing["indisvalid"] and existing["indisready"]):
            with op.get_context().autocommit_block():
                if existing is not None:
                    op.drop_index(name, table_name=table, postgresql_concurrently=True)
                op.create_index(name, table, columns, unique=unique, postgresql_concurrently=True)


IMMUTABILITY = """CREATE FUNCTION public.reject_stock_dividend_mutation()
RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER
SET search_path=pg_catalog,public,pg_temp AS $immutable$
BEGIN
 IF TG_OP IN ('UPDATE','DELETE') THEN
   RAISE EXCEPTION 'immutable dividend accounting' USING ERRCODE='23514';
 END IF;
 IF NEW.previous_application_id IS NOT NULL AND NOT EXISTS(
   SELECT FROM public.stock_dividend_decisions d
   WHERE d.id=NEW.previous_application_id AND d.payment_id=NEW.payment_id
     AND d.user_id=NEW.user_id AND d.event_id=NEW.event_id
     AND d.outcome IN ('applied','verified_no_change')) THEN
   RAISE EXCEPTION 'dividend previous application is not applied' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $immutable$"""

GRANTS = """DO $grants$ BEGIN
 REVOKE ALL ON public.stock_dividend_payments,public.stock_dividend_decisions FROM PUBLIC;
 REVOKE ALL ON SEQUENCE public.stock_dividend_payments_id_seq,
   public.stock_dividend_decisions_id_seq FROM PUBLIC;
 IF EXISTS(SELECT FROM pg_roles WHERE rolname='birja_app') THEN
   GRANT SELECT ON public.stock_dividend_payments,public.stock_dividend_decisions TO birja_app;
 END IF;
 IF EXISTS(SELECT FROM pg_roles WHERE rolname='birja_scheduler') THEN
   GRANT SELECT ON public.stock_dividend_payments,public.stock_dividend_decisions
     TO birja_scheduler;
 END IF;
END $grants$"""

# Private invoker helper. Only the two fixed definer entry points may call it.
# Full retained row JSON is compared, rather than trusting generation alone.
AUTHORITY = r"""CREATE FUNCTION public.stock_dividend_authority(
 p_event bigint,p_entitlement bigint,p_revision text,p_fingerprint text,
 p_verified boolean,p_expected jsonb)
RETURNS jsonb LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path=pg_catalog,public,pg_temp AS $authority$
DECLARE r record; a jsonb; n timestamptz; result jsonb; terms jsonb; v jsonb;
BEGIN
 SELECT ev AS event,rv AS revision,en AS entitlement,st AS action,
   i AS instrument,c AS coin,se AS cutoff_session,
   (SELECT coalesce(sum(m.quantity),0) FROM public.stock_ownership_movements m
    WHERE m.coin_id=ev.coin_id AND m.user_id=en.user_id
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
     WHERE newer.event_id=ev.id AND newer.user_id=en.user_id
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
 LEFT JOIN public.stock_sessions se ON se.exchange=i.listing_exchange
   AND se.session_date=CASE WHEN p_verified THEN (rv.normalized_terms->>'ex_date')::date ELSE
NULL END
 WHERE ev.id=p_event;
 n:=clock_timestamp();
 IF NOT FOUND OR p_revision IS NULL OR (r.revision).fingerprint IS DISTINCT FROM p_revision
 THEN RAISE EXCEPTION 'dividend authority changed' USING ERRCODE='22023'; END IF;
 result:=to_jsonb(r);
 IF p_expected IS NOT NULL AND result IS DISTINCT FROM p_expected THEN
   RAISE EXCEPTION 'dividend authority changed after wait' USING ERRCODE='22023';
 END IF;
 IF jsonb_array_length(r.admissions) IS DISTINCT FROM 3 THEN
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
     AND a->'scope' @> '{"application": "birja","audience": "authenticated-users","account":
"birja","server": "birja"}'::jsonb
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
END $authority$"""

APPLY = r"""CREATE FUNCTION public.apply_stock_dividend(
 p_event bigint,p_entitlement bigint,p_revision text,p_fingerprint text)
RETURNS TABLE(payment_id bigint,decision_id bigint,outcome text)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path=pg_catalog,public,pg_temp AS $apply$
DECLARE cid bigint; uid bigint; cash numeric; authority jsonb; final_authority jsonb;
 en public.stock_dividend_entitlements%ROWTYPE; rv public.stock_action_revisions%ROWTYPE;
 original public.stock_dividend_payments%ROWTYPE; prior public.stock_dividend_decisions%ROWTYPE;
 last_application bigint; desired numeric; raw numeric; cents numeric; delta numeric;
 cumulative numeric; applied numeric; result_outcome text; result_reason text; did bigint;
 terms jsonb; saved_symbol text; saved_name text; recorded timestamptz;
BEGIN
 IF current_setting('transaction_isolation')<>'read committed' THEN
   RAISE EXCEPTION 'dividend requires read committed' USING ERRCODE='22023'; END IF;
 SELECT ev.coin_id,en0.user_id INTO cid,uid FROM public.stock_action_events ev
 JOIN public.stock_dividend_entitlements en0 ON en0.event_id=ev.id
 WHERE ev.id=p_event AND en0.id=p_entitlement;
 IF NOT FOUND THEN RAISE EXCEPTION 'dividend work missing' USING ERRCODE='22023'; END IF;
 PERFORM pg_advisory_xact_lock(hashtextextended('birja.stock.instrument:'||cid::text,0));
 SELECT ac.cash INTO STRICT cash FROM public.accounts ac WHERE ac.user_id=uid FOR UPDATE;
 SELECT * INTO original FROM public.stock_dividend_payments p
 WHERE p.event_id=p_event AND p.user_id=uid;
 IF original.id IS NOT NULL AND original.revision_fingerprint=p_revision
   AND original.entitlement_id=p_entitlement AND original.entitlement_fingerprint=p_fingerprint THEN
   RETURN QUERY SELECT original.id,NULL::bigint,'original'::text; RETURN;
 END IF;
 IF original.id IS NOT NULL THEN
   SELECT * INTO prior FROM public.stock_dividend_decisions d
    WHERE d.payment_id=original.id AND d.revision_fingerprint=p_revision
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
 saved_symbol:=authority->'coin'->>'symbol'; saved_name:=authority->'coin'->>'name';
 IF original.id IS NULL THEN
   IF cash+desired>=1e12 THEN RAISE EXCEPTION 'dividend cash overflow' USING ERRCODE='22003';
END IF;
   INSERT INTO public.stock_dividend_payments(event_id,coin_id,user_id,revision_id,
    revision_fingerprint,entitlement_id,entitlement_fingerprint,symbol,company_name,
    cutoff,cutoff_rule,units_basis,unit_epoch,eligible_quantity,rate,ex_date,record_date,
    payable_date,original_amount,recorded_at,cash_after)
   VALUES(p_event,cid,uid,rv.id,rv.fingerprint,en.id,en.fingerprint,saved_symbol,saved_name,
en.cutoff,en.cutoff_rule,en.units_basis,en.unit_epoch,en.eligible_quantity,(terms->>'rate')::numeric,
    (terms->>'ex_date')::date,(terms->>'record_date')::date,(terms->>'payable_date')::date,
    desired,recorded,cash+desired) RETURNING * INTO original;
   UPDATE public.accounts SET cash=accounts.cash+desired WHERE user_id=uid;
   result_outcome:='original'; did:=NULL;
 ELSE
   SELECT original.original_amount+coalesce(sum(d.applied_delta),0) INTO cumulative
     FROM public.stock_dividend_decisions d WHERE d.payment_id=original.id;
   delta:=desired-cumulative;
   IF NOT(cumulative>=0 AND cumulative<1e12 AND cash+delta<1e12) THEN
     RAISE EXCEPTION 'dividend numeric range' USING ERRCODE='22003'; END IF;
   result_outcome:=CASE WHEN delta=0 THEN 'verified_no_change'
     WHEN cash+delta<0 THEN 'held_unaffordable' ELSE 'applied' END;
   result_reason:=CASE result_outcome WHEN 'applied' THEN 'target_applied'
     WHEN 'held_unaffordable' THEN 'insufficient_cash' ELSE 'target_unchanged' END;
   applied:=CASE WHEN result_outcome='applied' THEN delta ELSE 0 END;
   SELECT * INTO prior FROM public.stock_dividend_decisions d
     WHERE d.payment_id=original.id ORDER BY d.id DESC LIMIT 1;
   SELECT d.id INTO last_application FROM public.stock_dividend_decisions d
     WHERE d.payment_id=original.id AND d.outcome IN ('applied','verified_no_change')
     ORDER BY d.id DESC LIMIT 1;
   INSERT INTO public.stock_dividend_decisions(payment_id,user_id,event_id,coin_id,
    revision_id,revision_fingerprint,entitlement_id,entitlement_fingerprint,
    previous_decision_id,previous_application_id,desired_total,cumulative_applied_before,
    proposed_delta,applied_delta,outcome,reason,status_identity,recorded_at,cash_after,
    symbol,company_name,cutoff,cutoff_rule,units_basis,unit_epoch,eligible_quantity,rate,
    ex_date,record_date,payable_date)
   VALUES(original.id,uid,p_event,cid,rv.id,rv.fingerprint,en.id,en.fingerprint,
    prior.id,last_application,desired,cumulative,delta,applied,result_outcome,result_reason,
    'epoch:'||(authority->'action'->>'epoch')||':'||result_reason,
    recorded,cash+applied,saved_symbol,saved_name,en.cutoff,en.cutoff_rule,en.units_basis,
    en.unit_epoch,en.eligible_quantity,(terms->>'rate')::numeric,(terms->>'ex_date')::date,
    (terms->>'record_date')::date,(terms->>'payable_date')::date)
   ON CONFLICT DO NOTHING RETURNING id INTO did;
   IF did IS NULL THEN
     SELECT d.id INTO STRICT did FROM public.stock_dividend_decisions d
      WHERE d.payment_id=original.id AND d.revision_fingerprint=rv.fingerprint
      AND d.entitlement_id=en.id AND d.status_identity=
        'epoch:'||(authority->'action'->>'epoch')||':'||result_reason
      AND d.outcome=result_outcome ORDER BY d.id DESC LIMIT 1;
   ELSIF applied<>0 THEN
     UPDATE public.accounts SET cash=accounts.cash+applied WHERE user_id=uid;
   END IF;
 END IF;
 SET CONSTRAINTS ALL IMMEDIATE;
 final_authority:=public.stock_dividend_authority(
   p_event,p_entitlement,p_revision,p_fingerprint,true,authority);
 RETURN QUERY SELECT original.id,did,result_outcome;
END $apply$"""

HOLD = r"""CREATE FUNCTION public.record_stock_dividend_hold(p_payment bigint,p_revision text)
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
 PERFORM
pg_advisory_xact_lock(hashtextextended('birja.stock.instrument:'||original.coin_id::text,0));
 SELECT ac.cash INTO STRICT cash FROM public.accounts ac WHERE ac.user_id=original.user_id FOR
UPDATE;
 SELECT * INTO en FROM public.stock_dividend_entitlements e
   WHERE e.event_id=original.event_id AND e.user_id=original.user_id
   ORDER BY e.version DESC,e.id DESC LIMIT 1;
 authority:=public.stock_dividend_authority(original.event_id,en.id,p_revision,NULL,false,NULL);
 rv:=jsonb_populate_record(NULL::public.stock_action_revisions,authority->'revision');
 status:='epoch:'||(authority->'action'->>'epoch')||chr(58)||'terms_unverified';
 SELECT d.id INTO did FROM public.stock_dividend_decisions d WHERE d.payment_id=original.id
   AND d.revision_fingerprint=p_revision AND d.entitlement_id IS NOT DISTINCT FROM
     CASE WHEN en.revision_id=rv.id THEN en.id ELSE NULL END
   AND d.status_identity=status AND d.outcome='held_uncertain';
 IF did IS NULL THEN
   SELECT original.original_amount+coalesce(sum(d.applied_delta),0) INTO cumulative
     FROM public.stock_dividend_decisions d WHERE d.payment_id=original.id;
   SELECT d.id INTO prior FROM public.stock_dividend_decisions d
     WHERE d.payment_id=original.id ORDER BY d.id DESC LIMIT 1;
   SELECT d.id INTO application FROM public.stock_dividend_decisions d
     WHERE d.payment_id=original.id AND d.outcome IN ('applied','verified_no_change')
     ORDER BY d.id DESC LIMIT 1;
   INSERT INTO public.stock_dividend_decisions(payment_id,user_id,event_id,coin_id,
    revision_id,revision_fingerprint,entitlement_id,entitlement_fingerprint,
    previous_decision_id,previous_application_id,cumulative_applied_before,
    applied_delta,outcome,reason,status_identity,recorded_at,cash_after,symbol,company_name)
   VALUES(original.id,original.user_id,original.event_id,original.coin_id,rv.id,rv.fingerprint,
    CASE WHEN en.revision_id=rv.id THEN en.id ELSE NULL END,
    CASE WHEN en.revision_id=rv.id THEN en.fingerprint ELSE NULL END,
    prior,application,cumulative,0,'held_uncertain','terms_unverified',status,
    clock_timestamp(),cash,original.symbol,original.company_name) RETURNING id INTO did;
 END IF;
 SET CONSTRAINTS ALL IMMEDIATE;
final_authority:=public.stock_dividend_authority(original.event_id,en.id,p_revision,NULL,false,authority);
 RETURN QUERY SELECT original.id,did,'held_uncertain'::text;
END $hold$"""

AUTHORITY_SIGNATURE = "public.stock_dividend_authority(bigint,bigint,text,text,boolean,jsonb)"
APPLY_SIGNATURE = "public.apply_stock_dividend(bigint,bigint,text,text)"
HOLD_SIGNATURE = "public.record_stock_dividend_hold(bigint,text)"
DIVIDEND_SIGNATURES = (AUTHORITY_SIGNATURE, APPLY_SIGNATURE, HOLD_SIGNATURE)


def _install_authority() -> None:
    for definition in (AUTHORITY, APPLY, HOLD):
        op.execute(definition)
    for signature in DIVIDEND_SIGNATURES:
        op.execute(f"REVOKE ALL ON FUNCTION {signature} FROM PUBLIC")
        op.execute(f"ALTER FUNCTION {signature} OWNER TO birja_migrator")
    op.execute("ALTER FUNCTION public.reject_stock_dividend_mutation() OWNER TO birja_migrator")
    op.execute("""DO $rights$ BEGIN
      IF EXISTS(SELECT FROM pg_roles WHERE rolname='birja_scheduler') THEN
        GRANT EXECUTE ON FUNCTION public.apply_stock_dividend(bigint,bigint,text,text),
          public.record_stock_dividend_hold(bigint,text) TO birja_scheduler;
      END IF;
    END $rights$""")


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""DO $owner$ BEGIN
      IF NOT EXISTS(SELECT FROM pg_roles WHERE rolname='birja_migrator'
        AND NOT (rolinherit OR rolsuper OR rolcreatedb OR rolcreaterole
          OR rolreplication OR rolbypassrls))
      OR EXISTS(SELECT FROM pg_auth_members WHERE
        member=(SELECT oid FROM pg_roles WHERE rolname='birja_migrator') OR
        roleid=(SELECT oid FROM pg_roles WHERE rolname='birja_migrator')) THEN
        RAISE EXCEPTION 'preprovision safe dividend migrator owner before0014'; END IF;
    END $owner$""")
    _prepare_existing_indexes()
    op.execute(
        "ALTER TABLE public.stock_action_revisions ADD CONSTRAINT "
        "uq_stock_action_revision_dividend_identity UNIQUE USING INDEX "
        "uq_stock_action_revision_dividend_identity"
    )
    op.execute(
        "ALTER TABLE public.stock_dividend_entitlements ADD CONSTRAINT "
        "uq_stock_entitlement_dividend_identity UNIQUE USING INDEX "
        "uq_stock_entitlement_dividend_identity"
    )
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "stock_dividend_payments",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("event_id", sa.BigInteger(), nullable=False),
        sa.Column("coin_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("revision_id", sa.BigInteger(), nullable=False),
        sa.Column("revision_fingerprint", sa.Text(), nullable=False),
        sa.Column("entitlement_id", sa.BigInteger(), nullable=False),
        sa.Column("entitlement_fingerprint", sa.Text(), nullable=False),
        sa.Column("symbol", sa.Text(), nullable=False),
        sa.Column("company_name", sa.Text(), nullable=False),
        sa.Column("cutoff", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cutoff_rule", sa.Text(), nullable=False),
        sa.Column("units_basis", sa.Text(), nullable=False),
        sa.Column("unit_epoch", sa.BigInteger(), nullable=False),
        sa.Column("eligible_quantity", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("rate", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("ex_date", sa.Date(), nullable=False),
        sa.Column("record_date", sa.Date(), nullable=False),
        sa.Column("payable_date", sa.Date(), nullable=False),
        sa.Column("original_amount", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cash_after", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.CheckConstraint(
            "entitlement_fingerprint ~ '^[0-9a-f]{64}$'",
            name=op.f("ck_stock_dividend_payments_entitlement_fingerprint_sha256"),
        ),
        sa.CheckConstraint(
            "revision_fingerprint ~ '^[0-9a-f]{64}$'",
            name=op.f("ck_stock_dividend_payments_revision_fingerprint_sha256"),
        ),
        sa.CheckConstraint(
            "cash_after>=0 AND cash_after<1e12 AND cash_after=trunc(cash_after,2)",
            name=op.f("ck_stock_dividend_payments_cash_after_finite_cents"),
        ),
        sa.CheckConstraint(
            "eligible_quantity>=0 AND eligible_quantity<1e12 "
            "AND eligible_quantity=trunc(eligible_quantity)",
            name=op.f("ck_stock_dividend_payments_eligible_whole_finite"),
        ),
        sa.CheckConstraint(
            "length(company_name) BETWEEN 1 AND 256",
            name=op.f("ck_stock_dividend_payments_company_name_length"),
        ),
        sa.CheckConstraint(
            "length(cutoff_rule) BETWEEN 1 AND 128",
            name=op.f("ck_stock_dividend_payments_cutoff_rule_length"),
        ),
        sa.CheckConstraint(
            "length(symbol) BETWEEN 1 AND 32", name=op.f("ck_stock_dividend_payments_symbol_length")
        ),
        sa.CheckConstraint(
            "length(units_basis) BETWEEN 1 AND 128",
            name=op.f("ck_stock_dividend_payments_units_basis_length"),
        ),
        sa.CheckConstraint(
            "original_amount>=0 AND original_amount<1e12 "
            "AND original_amount=trunc(original_amount,2)",
            name=op.f("ck_stock_dividend_payments_original_amount_finite_cents"),
        ),
        sa.CheckConstraint(
            "rate>=0 AND rate<1e12", name=op.f("ck_stock_dividend_payments_rate_finite")
        ),
        sa.CheckConstraint(
            "unit_epoch BETWEEN 0 AND 9007199254740991",
            name=op.f("ck_stock_dividend_payments_unit_epoch_safe"),
        ),
        sa.ForeignKeyConstraint(
            ["coin_id"],
            ["stock_instruments.coin_id"],
            name=op.f("fk_stock_dividend_payments_coin_id_stock_instruments"),
        ),
        sa.ForeignKeyConstraint(
            ["entitlement_id", "event_id", "user_id", "revision_id", "entitlement_fingerprint"],
            [
                "stock_dividend_entitlements.id",
                "stock_dividend_entitlements.event_id",
                "stock_dividend_entitlements.user_id",
                "stock_dividend_entitlements.revision_id",
                "stock_dividend_entitlements.fingerprint",
            ],
            name="fk_dividend_payment_entitlement_identity",
        ),
        sa.ForeignKeyConstraint(
            ["event_id", "coin_id"],
            ["stock_action_events.id", "stock_action_events.coin_id"],
            name="fk_dividend_payment_event_coin",
        ),
        sa.ForeignKeyConstraint(
            ["revision_id", "event_id", "revision_fingerprint"],
            [
                "stock_action_revisions.id",
                "stock_action_revisions.event_id",
                "stock_action_revisions.fingerprint",
            ],
            name="fk_dividend_payment_revision_identity",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_stock_dividend_payments_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_stock_dividend_payments")),
        sa.UniqueConstraint("event_id", "user_id", name="uq_stock_dividend_payment_event_user"),
        sa.UniqueConstraint(
            "id",
            "event_id",
            "user_id",
            "coin_id",
            name="uq_stock_dividend_payment_owner_event_coin",
        ),
    )
    op.create_index(
        "ix_stock_dividend_payment_owner_recorded_id",
        "stock_dividend_payments",
        ["user_id", "recorded_at", "id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_stock_dividend_payments_coin_id"),
        "stock_dividend_payments",
        ["coin_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_stock_dividend_payments_entitlement_id"),
        "stock_dividend_payments",
        ["entitlement_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_stock_dividend_payments_revision_id"),
        "stock_dividend_payments",
        ["revision_id"],
        unique=False,
    )
    op.create_table(
        "stock_dividend_decisions",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("payment_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("event_id", sa.BigInteger(), nullable=False),
        sa.Column("coin_id", sa.BigInteger(), nullable=False),
        sa.Column("revision_id", sa.BigInteger(), nullable=False),
        sa.Column("revision_fingerprint", sa.Text(), nullable=False),
        sa.Column("entitlement_id", sa.BigInteger(), nullable=True),
        sa.Column("entitlement_fingerprint", sa.Text(), nullable=True),
        sa.Column("previous_decision_id", sa.BigInteger(), nullable=True),
        sa.Column("previous_application_id", sa.BigInteger(), nullable=True),
        sa.Column("desired_total", sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column("cumulative_applied_before", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("proposed_delta", sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column("applied_delta", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("outcome", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status_identity", sa.Text(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cash_after", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("symbol", sa.Text(), nullable=False),
        sa.Column("company_name", sa.Text(), nullable=False),
        sa.Column("cutoff", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cutoff_rule", sa.Text(), nullable=True),
        sa.Column("units_basis", sa.Text(), nullable=True),
        sa.Column("unit_epoch", sa.BigInteger(), nullable=True),
        sa.Column("eligible_quantity", sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column("rate", sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column("ex_date", sa.Date(), nullable=True),
        sa.Column("record_date", sa.Date(), nullable=True),
        sa.Column("payable_date", sa.Date(), nullable=True),
        sa.CheckConstraint(
            "(outcome='applied' AND applied_delta=proposed_delta AND applied_delta<>0) "
            "OR (outcome<>'applied' AND applied_delta=0)",
            name=op.f("ck_stock_dividend_decisions_applied_effect"),
        ),
        sa.CheckConstraint(
            "(outcome='applied' AND reason='target_applied') OR "
            "(outcome='verified_no_change' AND reason='target_unchanged') OR "
            "(outcome='held_uncertain' AND reason='terms_unverified') OR "
            "(outcome='held_unaffordable' AND reason='insufficient_cash')",
            name=op.f("ck_stock_dividend_decisions_reason_matches_outcome"),
        ),
        sa.CheckConstraint(
            "entitlement_fingerprint ~ '^[0-9a-f]{64}$'",
            name=op.f("ck_stock_dividend_decisions_entitlement_fingerprint_sha256"),
        ),
        sa.CheckConstraint(
            "outcome IN ('applied','held_uncertain','held_unaffordable','verified_no_change')",
            name=op.f("ck_stock_dividend_decisions_outcome_known"),
        ),
        sa.CheckConstraint(
            "outcome<>'held_unaffordable' OR (proposed_delta<0 AND cash_after < -proposed_delta)",
            name=op.f("ck_stock_dividend_decisions_unaffordable_negative"),
        ),
        sa.CheckConstraint(
            "outcome<>'held_uncertain' OR (desired_total IS NULL AND proposed_delta IS NULL "
            "AND eligible_quantity IS NULL AND rate IS NULL AND cutoff IS NULL "
            "AND cutoff_rule IS NULL AND units_basis IS NULL AND unit_epoch IS NULL "
            "AND ex_date IS NULL AND record_date IS NULL AND payable_date IS NULL)",
            name=op.f("ck_stock_dividend_decisions_uncertainty_no_invented_terms"),
        ),
        sa.CheckConstraint(
            "outcome<>'verified_no_change' OR proposed_delta=0",
            name=op.f("ck_stock_dividend_decisions_no_change_zero"),
        ),
        sa.CheckConstraint(
            "outcome='held_uncertain' OR (entitlement_id IS NOT NULL AND desired_total IS NOT NULL "
            "AND proposed_delta IS NOT NULL AND eligible_quantity IS NOT NULL AND rate IS NOT NULL "
            "AND cutoff IS NOT NULL AND cutoff_rule IS NOT NULL AND units_basis IS NOT NULL "
            "AND unit_epoch IS NOT NULL AND ex_date IS NOT NULL AND record_date IS NOT NULL "
            "AND payable_date IS NOT NULL)",
            name=op.f("ck_stock_dividend_decisions_verified_terms_required"),
        ),
        sa.CheckConstraint(
            "revision_fingerprint ~ '^[0-9a-f]{64}$'",
            name=op.f("ck_stock_dividend_decisions_revision_fingerprint_sha256"),
        ),
        sa.CheckConstraint(
            "(entitlement_id IS NULL)=(entitlement_fingerprint IS NULL)",
            name=op.f("ck_stock_dividend_decisions_entitlement_null_pair"),
        ),
        sa.CheckConstraint(
            "applied_delta>-1e12 AND applied_delta<1e12 AND applied_delta=trunc(applied_delta,2)",
            name=op.f("ck_stock_dividend_decisions_applied_delta_finite_cents"),
        ),
        sa.CheckConstraint(
            "cash_after>=0 AND cash_after<1e12 AND cash_after=trunc(cash_after,2)",
            name=op.f("ck_stock_dividend_decisions_cash_after_finite_cents"),
        ),
        sa.CheckConstraint(
            "cumulative_applied_before>=0 AND cumulative_applied_before<1e12 "
            "AND cumulative_applied_before=trunc(cumulative_applied_before,2)",
            name=op.f("ck_stock_dividend_decisions_cumulative_applied_before_finite_cents"),
        ),
        sa.CheckConstraint(
            "desired_total>=0 AND desired_total<1e12 AND desired_total=trunc(desired_total,2)",
            name=op.f("ck_stock_dividend_decisions_desired_total_finite_cents"),
        ),
        sa.CheckConstraint(
            "eligible_quantity>=0 AND eligible_quantity<1e12 "
            "AND eligible_quantity=trunc(eligible_quantity)",
            name=op.f("ck_stock_dividend_decisions_eligible_whole_finite"),
        ),
        sa.CheckConstraint(
            "length(company_name) BETWEEN 1 AND 256",
            name=op.f("ck_stock_dividend_decisions_company_name_length"),
        ),
        sa.CheckConstraint(
            "length(cutoff_rule) BETWEEN 1 AND 128",
            name=op.f("ck_stock_dividend_decisions_cutoff_rule_length"),
        ),
        sa.CheckConstraint(
            "length(status_identity) BETWEEN 1 AND 256",
            name=op.f("ck_stock_dividend_decisions_status_identity_length"),
        ),
        sa.CheckConstraint(
            "length(symbol) BETWEEN 1 AND 32",
            name=op.f("ck_stock_dividend_decisions_symbol_length"),
        ),
        sa.CheckConstraint(
            "length(units_basis) BETWEEN 1 AND 128",
            name=op.f("ck_stock_dividend_decisions_units_basis_length"),
        ),
        sa.CheckConstraint(
            "previous_application_id IS NULL OR previous_application_id<id",
            name=op.f("ck_stock_dividend_decisions_previous_application_precedes"),
        ),
        sa.CheckConstraint(
            "previous_decision_id IS NULL OR previous_decision_id<id",
            name=op.f("ck_stock_dividend_decisions_previous_decision_precedes"),
        ),
        sa.CheckConstraint(
            "proposed_delta=desired_total-cumulative_applied_before",
            name=op.f("ck_stock_dividend_decisions_target_delta_equation"),
        ),
        sa.CheckConstraint(
            "proposed_delta>-1e12 AND proposed_delta<1e12 "
            "AND proposed_delta=trunc(proposed_delta,2)",
            name=op.f("ck_stock_dividend_decisions_proposed_delta_finite_cents"),
        ),
        sa.CheckConstraint(
            "rate>=0 AND rate<1e12", name=op.f("ck_stock_dividend_decisions_rate_finite")
        ),
        sa.CheckConstraint(
            "unit_epoch BETWEEN 0 AND 9007199254740991",
            name=op.f("ck_stock_dividend_decisions_unit_epoch_safe"),
        ),
        sa.ForeignKeyConstraint(
            ["coin_id"],
            ["stock_instruments.coin_id"],
            name=op.f("fk_stock_dividend_decisions_coin_id_stock_instruments"),
        ),
        sa.ForeignKeyConstraint(
            ["entitlement_id", "event_id", "user_id", "revision_id", "entitlement_fingerprint"],
            [
                "stock_dividend_entitlements.id",
                "stock_dividend_entitlements.event_id",
                "stock_dividend_entitlements.user_id",
                "stock_dividend_entitlements.revision_id",
                "stock_dividend_entitlements.fingerprint",
            ],
            name="fk_dividend_decision_entitlement_identity",
        ),
        sa.ForeignKeyConstraint(
            ["payment_id", "event_id", "user_id", "coin_id"],
            [
                "stock_dividend_payments.id",
                "stock_dividend_payments.event_id",
                "stock_dividend_payments.user_id",
                "stock_dividend_payments.coin_id",
            ],
            name="fk_dividend_decision_payment_owner",
        ),
        sa.ForeignKeyConstraint(
            ["previous_application_id", "payment_id", "user_id", "event_id"],
            [
                "stock_dividend_decisions.id",
                "stock_dividend_decisions.payment_id",
                "stock_dividend_decisions.user_id",
                "stock_dividend_decisions.event_id",
            ],
            name="fk_dividend_decision_application_owner",
        ),
        sa.ForeignKeyConstraint(
            ["previous_decision_id", "payment_id", "user_id", "event_id"],
            [
                "stock_dividend_decisions.id",
                "stock_dividend_decisions.payment_id",
                "stock_dividend_decisions.user_id",
                "stock_dividend_decisions.event_id",
            ],
            name="fk_dividend_decision_previous_owner",
        ),
        sa.ForeignKeyConstraint(
            ["revision_id", "event_id", "revision_fingerprint"],
            [
                "stock_action_revisions.id",
                "stock_action_revisions.event_id",
                "stock_action_revisions.fingerprint",
            ],
            name="fk_dividend_decision_revision_identity",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_stock_dividend_decisions_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_stock_dividend_decisions")),
        sa.UniqueConstraint(
            "id", "payment_id", "user_id", "event_id", name="uq_stock_dividend_decision_lineage"
        ),
    )
    op.create_index(
        "ix_stock_dividend_decision_entitlement_id",
        "stock_dividend_decisions",
        ["entitlement_id"],
        unique=False,
    )
    op.create_index(
        "ix_stock_dividend_decision_event_id",
        "stock_dividend_decisions",
        ["event_id"],
        unique=False,
    )
    op.create_index(
        "ix_stock_dividend_decision_owner_recorded_id",
        "stock_dividend_decisions",
        ["user_id", "recorded_at", "id"],
        unique=False,
    )
    op.create_index(
        "ix_stock_dividend_decision_payment_id",
        "stock_dividend_decisions",
        ["payment_id", "id"],
        unique=False,
    )
    op.create_index(
        "ix_stock_dividend_decision_previous_application_id",
        "stock_dividend_decisions",
        ["previous_application_id"],
        unique=False,
    )
    op.create_index(
        "ix_stock_dividend_decision_previous_decision_id",
        "stock_dividend_decisions",
        ["previous_decision_id"],
        unique=False,
    )
    op.create_index(
        "ix_stock_dividend_decision_revision_id",
        "stock_dividend_decisions",
        ["revision_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_stock_dividend_decisions_coin_id"),
        "stock_dividend_decisions",
        ["coin_id"],
        unique=False,
    )
    op.create_index(
        "uq_stock_dividend_decision_applied_target",
        "stock_dividend_decisions",
        [
            "payment_id",
            "revision_id",
            "entitlement_id",
            "revision_fingerprint",
            "entitlement_fingerprint",
        ],
        unique=True,
        postgresql_where=sa.text("outcome IN ('applied','verified_no_change')"),
    )
    op.create_index(
        "uq_stock_dividend_decision_held_status",
        "stock_dividend_decisions",
        ["payment_id", "revision_fingerprint", "entitlement_id", "status_identity"],
        unique=True,
        postgresql_nulls_not_distinct=True,
        postgresql_where=sa.text("outcome IN ('held_uncertain','held_unaffordable')"),
    )
    # ### end Alembic commands ###
    op.execute(IMMUTABILITY)
    op.execute("REVOKE ALL ON FUNCTION public.reject_stock_dividend_mutation() FROM PUBLIC")
    for table in ("stock_dividend_payments", "stock_dividend_decisions"):
        op.execute(
            f"CREATE TRIGGER stock_dividend_immutable BEFORE UPDATE OR DELETE "
            f"ON public.{table} FOR EACH ROW "
            "EXECUTE FUNCTION public.reject_stock_dividend_mutation()"
        )
    op.execute(
        "CREATE TRIGGER stock_dividend_application_link BEFORE INSERT "
        "ON public.stock_dividend_decisions FOR EACH ROW "
        "EXECUTE FUNCTION public.reject_stock_dividend_mutation()"
    )
    op.execute(GRANTS)
    _install_authority()


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("""DO $guard$ BEGIN
      IF EXISTS(SELECT FROM public.stock_dividend_payments)
        OR EXISTS(SELECT FROM public.stock_dividend_decisions) THEN
        RAISE EXCEPTION 'populated dividend accounting cannot be downgraded';
      END IF;
    END $guard$""")
    for signature in (APPLY_SIGNATURE, HOLD_SIGNATURE, AUTHORITY_SIGNATURE):
        op.execute(f"DROP FUNCTION IF EXISTS {signature}")
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(
        "uq_stock_dividend_decision_held_status",
        table_name="stock_dividend_decisions",
        postgresql_nulls_not_distinct=True,
        postgresql_where=sa.text("outcome IN ('held_uncertain','held_unaffordable')"),
    )
    op.drop_index(
        "uq_stock_dividend_decision_applied_target",
        table_name="stock_dividend_decisions",
        postgresql_where=sa.text("outcome IN ('applied','verified_no_change')"),
    )
    op.drop_index(
        op.f("ix_stock_dividend_decisions_coin_id"), table_name="stock_dividend_decisions"
    )
    op.drop_index("ix_stock_dividend_decision_revision_id", table_name="stock_dividend_decisions")
    op.drop_index(
        "ix_stock_dividend_decision_previous_decision_id", table_name="stock_dividend_decisions"
    )
    op.drop_index(
        "ix_stock_dividend_decision_previous_application_id", table_name="stock_dividend_decisions"
    )
    op.drop_index("ix_stock_dividend_decision_payment_id", table_name="stock_dividend_decisions")
    op.drop_index(
        "ix_stock_dividend_decision_owner_recorded_id", table_name="stock_dividend_decisions"
    )
    op.drop_index("ix_stock_dividend_decision_event_id", table_name="stock_dividend_decisions")
    op.drop_index(
        "ix_stock_dividend_decision_entitlement_id", table_name="stock_dividend_decisions"
    )
    op.drop_table("stock_dividend_decisions")
    op.drop_index(
        op.f("ix_stock_dividend_payments_revision_id"), table_name="stock_dividend_payments"
    )
    op.drop_index(
        op.f("ix_stock_dividend_payments_entitlement_id"), table_name="stock_dividend_payments"
    )
    op.drop_index(op.f("ix_stock_dividend_payments_coin_id"), table_name="stock_dividend_payments")
    op.drop_index(
        "ix_stock_dividend_payment_owner_recorded_id", table_name="stock_dividend_payments"
    )
    op.drop_table("stock_dividend_payments")
    op.execute("DROP FUNCTION public.reject_stock_dividend_mutation()")
    op.drop_index("ix_stock_ownership_user_recorded_id", table_name="stock_ownership_movements")
    op.drop_constraint(
        "uq_stock_entitlement_dividend_identity", "stock_dividend_entitlements", type_="unique"
    )
    op.drop_index("ix_stock_entitlement_current_work", table_name="stock_dividend_entitlements")
    op.drop_constraint(
        "uq_stock_action_revision_dividend_identity", "stock_action_revisions", type_="unique"
    )
    # ### end Alembic commands ###
