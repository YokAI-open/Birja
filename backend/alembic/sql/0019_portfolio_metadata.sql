-- PostgreSQL18 UTF8 is the sole authoritative Unicode canonicalizer.
-- C0/C1 are tested before trimming; White_Space is deliberately explicit.
CREATE OR REPLACE FUNCTION public.portfolio_display_name(raw text)
RETURNS text LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER
SET search_path=pg_catalog,public,pg_temp AS $name$
DECLARE display text;
BEGIN
 IF raw IS NULL OR EXISTS(SELECT FROM generate_series(1,char_length(raw)) i
   WHERE ascii(substr(raw,i,1)) BETWEEN 0 AND 31
      OR ascii(substr(raw,i,1)) BETWEEN 127 AND 159) THEN
   RAISE EXCEPTION 'invalid portfolio name' USING ERRCODE='22023';
 END IF;
 display := normalize(btrim(raw,U&'\0009\000A\000B\000C\000D\0020\0085\00A0\1680\2000\2001\2002\2003\2004\2005\2006\2007\2008\2009\200A\2028\2029\202F\205F\3000'),NFC);
 IF char_length(display) NOT BETWEEN 1 AND 60 THEN
   RAISE EXCEPTION 'invalid portfolio name length' USING ERRCODE='22023';
 END IF;
 RETURN display;
END $name$;

CREATE OR REPLACE FUNCTION public.portfolio_name_key(raw text)
RETURNS text LANGUAGE sql IMMUTABLE SECURITY INVOKER
SET search_path=pg_catalog,public,pg_temp AS $key$
 SELECT normalize(casefold(public.portfolio_display_name(raw)
   COLLATE pg_catalog.pg_unicode_fast),NFC)
$key$;

CREATE OR REPLACE FUNCTION public.portfolio_description(raw text)
RETURNS text LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER
SET search_path=pg_catalog,public,pg_temp AS $description$
DECLARE display text;
BEGIN
 IF raw IS NULL THEN
   RAISE EXCEPTION 'invalid portfolio description' USING ERRCODE='22023'; END IF;
 display := replace(replace(raw,E'\r\n',E'\n'),E'\r',E'\n');
 IF char_length(display)>1000 OR EXISTS(
   SELECT FROM generate_series(1,char_length(display)) i
   WHERE (ascii(substr(display,i,1)) BETWEEN 0 AND 31
     AND ascii(substr(display,i,1)) NOT IN (9,10))
   OR ascii(substr(display,i,1)) BETWEEN 127 AND 159) THEN
   RAISE EXCEPTION 'invalid portfolio description' USING ERRCODE='22023'; END IF;
 RETURN display;
END $description$;

-- Intermediate-stage authority only: closed roots gain a key, never economic
-- edits. The same function forbids ALL other row changes during backfill.
CREATE OR REPLACE FUNCTION public.associate_portfolio_metadata_only()
RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER
SET search_path=pg_catalog,public,pg_temp AS $association$
BEGIN
 IF session_user='birja_migrator' AND TG_OP='UPDATE'
 AND OLD.name_key IS NULL AND NEW.name_key=public.portfolio_name_key(OLD.name)
 AND to_jsonb(NEW)-'name_key'=to_jsonb(OLD)-'name_key' THEN RETURN NEW; END IF;
 RAISE EXCEPTION 'immutable portfolio metadata association rejected' USING ERRCODE='23514';
END $association$;

-- This is additive: the original0017 financial trigger and its source/body
-- remain intact after finalization. Existing custom baselines stay untouched.
CREATE OR REPLACE FUNCTION public.check_portfolio_management_metadata()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,public,pg_temp AS $metadata$
BEGIN
 IF TG_TABLE_NAME='accounts' THEN
   IF TG_OP='UPDATE' AND NEW.starting_cash IS DISTINCT FROM OLD.starting_cash THEN
     RAISE EXCEPTION 'immutable portfolio baseline' USING ERRCODE='23514'; END IF;
   IF NEW.name IS DISTINCT FROM public.portfolio_display_name(NEW.name)
     OR NEW.name_key IS DISTINCT FROM public.portfolio_name_key(NEW.name)
     OR NEW.description IS DISTINCT FROM public.portfolio_description(NEW.description) THEN
     RAISE EXCEPTION 'noncanonical portfolio metadata' USING ERRCODE='23514'; END IF;
 ELSIF TG_TABLE_NAME='portfolio_creations' THEN
   IF NEW.canonical_payload->>'name' IS DISTINCT FROM
       public.portfolio_display_name(NEW.canonical_payload->>'name')
     OR NEW.canonical_payload->>'description' IS DISTINCT FROM
       public.portfolio_description(NEW.canonical_payload->>'description')
     OR NEW.creation_key::text !~ '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$' THEN
     RAISE EXCEPTION 'invalid canonical creation payload' USING ERRCODE='23514'; END IF;
 ELSE
   IF NEW.origin='initial' AND NOT EXISTS(SELECT FROM public.portfolio_creations c
      WHERE (c.id,c.portfolio_id,c.user_id)=(NEW.creation_id,NEW.portfolio_id,NEW.user_id)
      AND c.origin='initial') THEN
     RAISE EXCEPTION 'invalid initial creation provenance' USING ERRCODE='23514'; END IF;
 END IF;
 RETURN NEW;
END $metadata$;

ALTER FUNCTION public.portfolio_display_name(text) OWNER TO birja_migrator;
ALTER FUNCTION public.portfolio_name_key(text) OWNER TO birja_migrator;
ALTER FUNCTION public.portfolio_description(text) OWNER TO birja_migrator;
ALTER FUNCTION public.associate_portfolio_metadata_only() OWNER TO birja_migrator;
ALTER FUNCTION public.check_portfolio_management_metadata() OWNER TO birja_migrator;
REVOKE ALL ON FUNCTION public.portfolio_display_name(text) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.portfolio_name_key(text) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.portfolio_description(text) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.associate_portfolio_metadata_only() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.check_portfolio_management_metadata() FROM PUBLIC;
