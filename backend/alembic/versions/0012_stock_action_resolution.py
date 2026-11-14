"""Add checked operator-only action resolution; no financial repair authority.

Revision ID: 0012
Revises: 0011
"""

from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None

SIGNATURE = (
    "public.apply_stock_action_resolution("
    "bigint,bigint,bigint,bigint,bigint,text,text,text,jsonb,text)"
)

# No dynamic SQL. Every application relation is qualified, including the row
# types. pg_catalog is first; callers cannot supply SQL, object names or URLs.
FUNCTION = r"""
CREATE FUNCTION public.apply_stock_action_resolution(
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
 SELECT * INTO adm FROM public.stock_data_admissions WHERE product='actions' FOR SHARE;
 SELECT * INTO cal FROM public.stock_data_admissions WHERE product='calendar' FOR SHARE;
 -- Time is read after every blocking lock, never transaction_timestamp().
 now_at := clock_timestamp();
 IF st.coin_id IS NULL OR ev.id IS NULL OR rev.id IS NULL
 OR ev.current_revision_id IS DISTINCT FROM p_revision
 OR st.epoch IS DISTINCT FROM p_epoch
 OR st.admission_generation IS DISTINCT FROM p_generation
 OR adm.generation IS DISTINCT FROM p_generation
 OR encode(sha256(convert_to(to_jsonb(adm)::text,'UTF8')),'hex')
    IS DISTINCT FROM p_evidence->>'admission_digest'
 OR rev.admission_generation IS DISTINCT FROM p_generation
 OR st.unit_epoch::text IS DISTINCT FROM p_evidence->>'unit_epoch'
 OR rev.fingerprint IS DISTINCT FROM p_evidence->>'revision_fingerprint'
 OR adm.state IS DISTINCT FROM 'approved' OR cal.state IS DISTINCT FROM 'approved'
 OR NOT coalesce(adm.collection_allowed AND adm.derived_allowed AND adm.retention_allowed,false)
 OR NOT coalesce(cal.collection_allowed AND cal.derived_allowed,false)
 OR NOT coalesce(adm.valid_from<=now_at AND now_at<adm.valid_until,false)
 OR NOT coalesce(cal.valid_from<=now_at AND now_at<cal.valid_until,false)
 OR NOT coalesce(now_at<(cal.calendar->>'review_valid_until')::timestamptz,false)
 OR NOT coalesce(now_at<(p_evidence->>'review_valid_until')::timestamptz
     AND (p_evidence->>'review_valid_until')::timestamptz<=adm.valid_until
     AND (p_evidence->>'review_valid_until')::timestamptz<=cal.valid_until,false)
 OR cal.generation::text IS DISTINCT FROM p_evidence->>'calendar_generation'
 OR encode(sha256(convert_to(to_jsonb(cal)::text,'UTF8')),'hex')
    IS DISTINCT FROM p_evidence->>'calendar_digest'
 OR adm.scope->>'application' IS DISTINCT FROM 'birja'
 OR adm.scope->>'audience' IS DISTINCT FROM 'authenticated-users'
 OR adm.scope->>'feed' IS DISTINCT FROM 'alpaca-corporate-actions'
 OR adm.scope->>'account' IS DISTINCT FROM p_evidence->>'account'
 OR adm.scope->>'server' IS DISTINCT FROM p_evidence->>'server'
 OR cal.scope->>'account' IS DISTINCT FROM p_evidence->>'account'
 OR cal.scope->>'server' IS DISTINCT FROM p_evidence->>'server'
 OR adm.scope->'durable_accounting' IS DISTINCT FROM 'true'::jsonb
 OR adm.scope->'backup_restore' IS DISTINCT FROM 'true'::jsonb
 OR adm.scope->>'retention_mode' IS DISTINCT FROM 'durable-accounting'
 OR NOT coalesce(adm.scope->'capabilities' ? 'rest',false)
 OR NOT EXISTS(SELECT FROM public.stock_instruments i JOIN public.coins c ON c.id=i.coin_id
   WHERE i.coin_id=p_coin AND i.provider_asset_id=p_evidence->>'security_id'
   AND i.provider_verified_at IS NOT NULL AND c.asset_class='stock' AND c.is_active
   AND rev.normalized_terms->>'coin_id'=p_coin::text
   AND rev.normalized_terms->>'symbol'=c.symbol)
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
"""


def upgrade() -> None:
    op.execute("""DO $$ BEGIN
      IF NOT EXISTS(SELECT FROM pg_roles WHERE rolname='birja_action_operator') THEN
        IF NOT EXISTS(SELECT FROM pg_roles WHERE rolname=current_user AND rolsuper) THEN
          RAISE EXCEPTION 'preprovision birja_action_operator before restricted 0012 upgrade';
        END IF;
        CREATE ROLE birja_action_operator NOLOGIN NOINHERIT NOSUPERUSER
          NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
      END IF;
      IF EXISTS(SELECT FROM pg_roles WHERE rolname='birja_action_operator'
        AND (rolcanlogin OR rolinherit OR rolsuper OR rolcreatedb OR rolcreaterole
             OR rolreplication OR rolbypassrls)) THEN
        RAISE EXCEPTION 'unsafe action operator role';
      END IF;
      IF EXISTS(SELECT FROM pg_roles r WHERE r.rolname IN
        ('birja_app','birja_scheduler','birja_migrator')
        AND pg_has_role(r.oid,'birja_action_operator','MEMBER'))
        OR EXISTS(SELECT FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.member
                  WHERE r.rolname='birja_action_operator') THEN
        RAISE EXCEPTION 'unsafe action operator membership';
      END IF;
    END $$""")
    op.execute(FUNCTION)
    op.execute(f"REVOKE ALL ON FUNCTION {SIGNATURE} FROM PUBLIC")
    op.execute(f"GRANT EXECUTE ON FUNCTION {SIGNATURE} TO birja_action_operator")
    op.execute(
        "GRANT SELECT(id,symbol,asset_class,is_active,sort_order) ON public.coins "
        "TO birja_action_operator"
    )


def downgrade() -> None:
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT FROM public.stock_action_resolutions) THEN
        RAISE EXCEPTION 'populated resolution authority cannot be downgraded';
      END IF; END $$""")
    op.execute(f"DROP FUNCTION {SIGNATURE}")
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT FROM pg_roles WHERE rolname='birja_action_operator') THEN
        REVOKE SELECT(id,symbol,asset_class,is_active,sort_order) ON public.coins
          FROM birja_action_operator;
      END IF;
    END $$""")
