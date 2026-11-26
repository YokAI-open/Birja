CREATE TABLE public.portfolio_daily_values (
 id bigint GENERATED ALWAYS AS IDENTITY,
 portfolio_id bigint NOT NULL,
 user_id bigint NOT NULL,
 utc_day date NOT NULL,
 captured_at timestamptz NOT NULL,
 starting_cash numeric(20,8) NOT NULL,
 total_value numeric(48,2),
 valuation_complete boolean NOT NULL,
 CONSTRAINT pk_portfolio_daily_values PRIMARY KEY (id),
 CONSTRAINT uq_portfolio_daily_values_portfolio_day UNIQUE (portfolio_id,utc_day),
 CONSTRAINT fk_portfolio_daily_values_owner FOREIGN KEY (portfolio_id,user_id)
  REFERENCES public.accounts (id,user_id) ON DELETE RESTRICT,
 CONSTRAINT ck_portfolio_daily_values_utc_capture CHECK (
  isfinite(captured_at) AND (captured_at AT TIME ZONE 'UTC')::date=utc_day
   AND (captured_at AT TIME ZONE 'UTC')::time>=TIME '22:00'),
 CONSTRAINT ck_portfolio_daily_values_starting_cash_valid CHECK (
  starting_cash>=0 AND starting_cash<'Infinity'::numeric),
 CONSTRAINT ck_portfolio_daily_values_total_valid CHECK (
  total_value>=0 AND total_value<'Infinity'::numeric),
 CONSTRAINT ck_portfolio_daily_values_completeness CHECK (
  valuation_complete=(total_value IS NOT NULL))
);

CREATE FUNCTION public.lock_portfolio_daily_value_root(p_user bigint,p_portfolio bigint)
RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,pg_temp AS $lock$
BEGIN
 PERFORM 1 FROM public.accounts
  WHERE id=p_portfolio AND user_id=p_user AND closed_at IS NULL FOR SHARE;
 RETURN FOUND;
END $lock$;

CREATE FUNCTION public.check_portfolio_daily_value_root()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,pg_temp AS $check$
BEGIN
 IF NOT public.lock_portfolio_daily_value_root(NEW.user_id,NEW.portfolio_id) THEN
  RAISE EXCEPTION 'daily value requires an active portfolio' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $check$;

CREATE TRIGGER portfolio_daily_value_root BEFORE INSERT ON public.portfolio_daily_values
FOR EACH ROW EXECUTE FUNCTION public.check_portfolio_daily_value_root();

REVOKE ALL ON public.portfolio_daily_values
 FROM PUBLIC,birja_app,birja_scheduler,birja_action_operator;
REVOKE ALL ON SEQUENCE public.portfolio_daily_values_id_seq
 FROM PUBLIC,birja_app,birja_scheduler,birja_action_operator;
REVOKE ALL ON FUNCTION public.lock_portfolio_daily_value_root(bigint,bigint),
 public.check_portfolio_daily_value_root()
 FROM PUBLIC,birja_app,birja_scheduler,birja_action_operator;
