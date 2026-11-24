-- Stable financial bindings and typed evidence for the catalog stock lane.

ALTER TABLE public.coins DROP CONSTRAINT ck_coins_symbol_length;

ALTER TABLE public.coins ADD CONSTRAINT ck_coins_symbol_length CHECK (
    CASE WHEN asset_class = 'stock' AND left(symbol, 1) = '@' THEN CASE WHEN symbol ~ '^@[1-9][0-9]{0,18}$' THEN substring(symbol FROM 2)::numeric <= 9223372036854775807 ELSE false END ELSE length(symbol) >= 1 AND length(symbol) <= 10 END
);

CREATE TABLE public.stock_catalog_instruments (
    catalog_id BIGINT NOT NULL,
    coin_id BIGINT NOT NULL,
    listing_id BIGINT NOT NULL,
    admission_id BIGINT NOT NULL,
    promoted_at TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT pk_stock_catalog_instruments PRIMARY KEY (catalog_id),
    CONSTRAINT uq_sc_instrument_catalog_coin UNIQUE (catalog_id, coin_id),
    CONSTRAINT fk_sc_instrument_listing FOREIGN KEY(listing_id, catalog_id) REFERENCES public.stock_catalog_listings (id, security_id),
    CONSTRAINT ck_stock_catalog_instruments_promoted_finite CHECK (isfinite(promoted_at)),
    CONSTRAINT uq_stock_catalog_instruments_coin_id UNIQUE (coin_id),
    CONSTRAINT fk_sc_instrument_coin FOREIGN KEY(coin_id) REFERENCES public.stock_instruments (coin_id),
    CONSTRAINT fk_sc_instrument_admission FOREIGN KEY(admission_id) REFERENCES public.stock_catalog_admissions (id)
);

CREATE TABLE public.stock_catalog_financial_quotes (
    coin_id BIGINT NOT NULL,
    catalog_id BIGINT NOT NULL,
    listing_id BIGINT NOT NULL,
    provider_asset_id TEXT NOT NULL,
    provider_admission_id BIGINT NOT NULL,
    execution_admission_id BIGINT,
    mark_admission_id BIGINT,
    source TEXT DEFAULT 'alpaca' NOT NULL,
    feed TEXT DEFAULT 'iex' NOT NULL,
    bid NUMERIC(20, 8) NOT NULL,
    ask NUMERIC(20, 8) NOT NULL,
    unit_epoch BIGINT NOT NULL,
    event_at TIMESTAMP WITH TIME ZONE NOT NULL,
    collected_at TIMESTAMP WITH TIME ZONE NOT NULL,
    observed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    session_date DATE NOT NULL,
    calendar_generation BIGINT NOT NULL,
    opens_at TIMESTAMP WITH TIME ZONE NOT NULL,
    closes_at TIMESTAMP WITH TIME ZONE NOT NULL,
    valid_until TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT pk_stock_catalog_financial_quotes PRIMARY KEY (coin_id),
    CONSTRAINT fk_sc_fin_quote_binding FOREIGN KEY(catalog_id, coin_id) REFERENCES public.stock_catalog_instruments (catalog_id, coin_id),
    CONSTRAINT fk_sc_fin_quote_listing FOREIGN KEY(listing_id, catalog_id) REFERENCES public.stock_catalog_listings (id, security_id),
    CONSTRAINT ck_stock_catalog_financial_quotes_scope CHECK (execution_admission_id IS NOT NULL OR mark_admission_id IS NOT NULL),
    CONSTRAINT ck_stock_catalog_financial_quotes_provider CHECK (length(provider_asset_id) >= 1 AND length(provider_asset_id) <= 128 AND source = 'alpaca' AND feed = 'iex'),
    CONSTRAINT ck_stock_catalog_financial_quotes_prices CHECK (bid > 0 AND bid <= ask AND ask < 1e12),
    CONSTRAINT ck_stock_catalog_financial_quotes_units CHECK (unit_epoch >= 0 AND unit_epoch <= 9007199254740991 AND calendar_generation > 0),
    CONSTRAINT ck_stock_catalog_financial_quotes_times CHECK (isfinite(opens_at) AND opens_at <= event_at AND event_at < closes_at AND isfinite(closes_at) AND isfinite(session_date) AND event_at <= collected_at AND collected_at <= observed_at AND observed_at < valid_until AND isfinite(valid_until)),
    CONSTRAINT fk_sc_fin_quote_provider FOREIGN KEY(provider_admission_id) REFERENCES public.stock_catalog_admissions (id),
    CONSTRAINT fk_sc_fin_quote_execution FOREIGN KEY(execution_admission_id) REFERENCES public.stock_catalog_admissions (id),
    CONSTRAINT fk_sc_fin_quote_mark FOREIGN KEY(mark_admission_id) REFERENCES public.stock_catalog_admissions (id)
);

CREATE INDEX ix_sc_fin_quotes_due ON public.stock_catalog_financial_quotes (observed_at, coin_id);

CREATE TABLE public.stock_catalog_status (
    coin_id BIGINT NOT NULL,
    catalog_id BIGINT NOT NULL,
    listing_id BIGINT NOT NULL,
    admission_id BIGINT NOT NULL,
    report_digest TEXT NOT NULL,
    state TEXT NOT NULL,
    event_at TIMESTAMP WITH TIME ZONE NOT NULL,
    observed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    valid_until TIMESTAMP WITH TIME ZONE NOT NULL,
    session_date DATE NOT NULL,
    CONSTRAINT pk_stock_catalog_status PRIMARY KEY (coin_id),
    CONSTRAINT fk_sc_status_binding FOREIGN KEY(catalog_id, coin_id) REFERENCES public.stock_catalog_instruments (catalog_id, coin_id),
    CONSTRAINT fk_sc_status_listing FOREIGN KEY(listing_id, catalog_id) REFERENCES public.stock_catalog_listings (id, security_id),
    CONSTRAINT ck_stock_catalog_status_report CHECK (state IN ('normal', 'halted') AND report_digest ~ '^[a-f0-9]{64}$'),
    CONSTRAINT ck_stock_catalog_status_times CHECK (isfinite(event_at) AND event_at <= observed_at AND observed_at < valid_until AND isfinite(valid_until) AND valid_until <= event_at + interval '120 seconds' AND isfinite(session_date)),
    CONSTRAINT fk_sc_status_admission FOREIGN KEY(admission_id) REFERENCES public.stock_catalog_admissions (id)
);

CREATE TABLE public.stock_catalog_action_coverage (
    coin_id BIGINT NOT NULL,
    catalog_id BIGINT NOT NULL,
    listing_id BIGINT NOT NULL,
    admission_id BIGINT NOT NULL,
    journal_origin TIMESTAMP WITH TIME ZONE NOT NULL,
    coverage_start TIMESTAMP WITH TIME ZONE,
    covered_until TIMESTAMP WITH TIME ZONE,
    cursor TEXT,
    observed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    valid_until TIMESTAMP WITH TIME ZONE,
    CONSTRAINT pk_stock_catalog_action_coverage PRIMARY KEY (coin_id),
    CONSTRAINT fk_sc_action_coverage_binding FOREIGN KEY(catalog_id, coin_id) REFERENCES public.stock_catalog_instruments (catalog_id, coin_id),
    CONSTRAINT fk_sc_action_coverage_listing FOREIGN KEY(listing_id, catalog_id) REFERENCES public.stock_catalog_listings (id, security_id),
    CONSTRAINT ck_stock_catalog_action_coverage_window CHECK ((coverage_start IS NULL AND covered_until IS NULL) OR (coverage_start IS NOT NULL AND covered_until IS NOT NULL AND isfinite(coverage_start) AND coverage_start <= covered_until AND isfinite(covered_until))),
    CONSTRAINT ck_stock_catalog_action_coverage_lease CHECK (isfinite(journal_origin) AND isfinite(observed_at) AND journal_origin <= observed_at AND (valid_until IS NULL OR (isfinite(valid_until) AND observed_at < valid_until AND coverage_start IS NOT NULL AND coverage_start <= journal_origin AND journal_origin <= covered_until))),
    CONSTRAINT ck_stock_catalog_action_coverage_cursor CHECK (cursor IS NULL OR (length(cursor) >= 1 AND length(cursor) <= 4096)),
    CONSTRAINT fk_sc_action_coverage_admission FOREIGN KEY(admission_id) REFERENCES public.stock_catalog_admissions (id)
);

CREATE INDEX ix_sc_action_coverage_due ON public.stock_catalog_action_coverage (valid_until, coin_id);

CREATE TABLE public.stock_catalog_fill_evidence (
    trade_id BIGINT NOT NULL,
    coin_id BIGINT NOT NULL,
    catalog_id BIGINT NOT NULL,
    listing_id BIGINT NOT NULL,
    provider_admission_id BIGINT NOT NULL,
    execution_admission_id BIGINT NOT NULL,
    halt_admission_id BIGINT NOT NULL,
    action_admission_id BIGINT NOT NULL,
    unit_epoch BIGINT NOT NULL,
    action_epoch BIGINT NOT NULL,
    report_digest TEXT NOT NULL,
    report_event_at TIMESTAMP WITH TIME ZONE NOT NULL,
    report_valid_until TIMESTAMP WITH TIME ZONE NOT NULL,
    quote_valid_until TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT pk_stock_catalog_fill_evidence PRIMARY KEY (trade_id),
    CONSTRAINT fk_sc_fill_evidence_binding FOREIGN KEY(catalog_id, coin_id) REFERENCES public.stock_catalog_instruments (catalog_id, coin_id),
    CONSTRAINT fk_sc_fill_evidence_listing FOREIGN KEY(listing_id, catalog_id) REFERENCES public.stock_catalog_listings (id, security_id),
    CONSTRAINT ck_stock_catalog_fill_evidence_epochs CHECK (unit_epoch >= 0 AND unit_epoch <= 9007199254740991 AND action_epoch > 0 AND action_epoch <= 9007199254740991),
    CONSTRAINT ck_stock_catalog_fill_evidence_report CHECK (report_digest ~ '^[a-f0-9]{64}$' AND isfinite(report_event_at) AND report_event_at < report_valid_until AND isfinite(report_valid_until) AND report_valid_until <= report_event_at + interval '120 seconds' AND isfinite(quote_valid_until)),
    CONSTRAINT fk_sc_fill_evidence_receipt FOREIGN KEY(trade_id) REFERENCES public.stock_fill_facts (trade_id),
    CONSTRAINT fk_sc_fill_evidence_provider FOREIGN KEY(provider_admission_id) REFERENCES public.stock_catalog_admissions (id),
    CONSTRAINT fk_sc_fill_evidence_execution FOREIGN KEY(execution_admission_id) REFERENCES public.stock_catalog_admissions (id),
    CONSTRAINT fk_sc_fill_evidence_halt FOREIGN KEY(halt_admission_id) REFERENCES public.stock_catalog_admissions (id),
    CONSTRAINT fk_sc_fill_evidence_action FOREIGN KEY(action_admission_id) REFERENCES public.stock_catalog_admissions (id)
);

CREATE INDEX ix_sc_fill_evidence_coin ON public.stock_catalog_fill_evidence (coin_id);
