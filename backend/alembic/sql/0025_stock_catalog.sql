-- Additive discovery storage. The existing stock and cash ledgers are independent.

CREATE TABLE public.stock_catalog_generations (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    manifest_sha256 TEXT NOT NULL,
    mode TEXT NOT NULL,
    published_at TIMESTAMP WITH TIME ZONE NOT NULL,
    valid_until TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT false NOT NULL,
    sources JSONB NOT NULL,
    coverage JSONB NOT NULL,
    CONSTRAINT pk_stock_catalog_generations PRIMARY KEY (id),
    CONSTRAINT ck_stock_catalog_generations_digest CHECK (manifest_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT ck_stock_catalog_generations_mode_known CHECK (mode IN ('fixture', 'live')),
    CONSTRAINT ck_stock_catalog_generations_validity CHECK (
        isfinite(published_at)
        AND isfinite(valid_until)
        AND published_at < valid_until
    ),
    CONSTRAINT ck_stock_catalog_generations_sources_bounded CHECK (
        jsonb_typeof(sources) = 'object'
        AND octet_length(sources::text) <= 8192
    ),
    CONSTRAINT ck_stock_catalog_generations_coverage_bounded CHECK (
        jsonb_typeof(coverage) = 'object'
        AND octet_length(coverage::text) <= 4096
    ),
    CONSTRAINT uq_stock_catalog_generations_manifest_sha256 UNIQUE (manifest_sha256)
);

CREATE UNIQUE INDEX uq_stock_catalog_generations_active
    ON public.stock_catalog_generations (is_active)
    WHERE is_active;

CREATE TABLE public.stock_catalog_securities (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    identity_key TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT pk_stock_catalog_securities PRIMARY KEY (id),
    CONSTRAINT ck_stock_catalog_securities_identity_key CHECK (
        length(identity_key) >= 1
        AND length(identity_key) <= 192
        AND identity_key = btrim(identity_key)
    ),
    CONSTRAINT ck_stock_catalog_securities_created_at_finite CHECK (isfinite(created_at)),
    CONSTRAINT uq_stock_catalog_securities_identity_key UNIQUE (identity_key)
);

CREATE TABLE public.stock_catalog_admissions (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    artifact TEXT NOT NULL,
    reference TEXT NOT NULL,
    reviewed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    valid_until TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked_at TIMESTAMP WITH TIME ZONE,
    fields JSONB NOT NULL,
    scope JSONB NOT NULL,
    is_fixture BOOLEAN DEFAULT false NOT NULL,
    CONSTRAINT pk_stock_catalog_admissions PRIMARY KEY (id),
    CONSTRAINT ck_stock_catalog_admissions_artifact_key CHECK (artifact ~ '^[a-zA-Z0-9_.:-]{1,96}$'),
    CONSTRAINT ck_stock_catalog_admissions_reference_length CHECK (
        length(reference) >= 1
        AND length(reference) <= 2048
        AND reference = btrim(reference)
    ),
    CONSTRAINT ck_stock_catalog_admissions_validity CHECK (
        isfinite(reviewed_at)
        AND isfinite(valid_until)
        AND reviewed_at < valid_until
        AND (revoked_at IS NULL OR (isfinite(revoked_at)
        AND reviewed_at <= revoked_at))
    ),
    CONSTRAINT ck_stock_catalog_admissions_fields_bounded CHECK (
        jsonb_typeof(fields) = 'object'
        AND octet_length(fields::text) <= 16384
    ),
    CONSTRAINT ck_stock_catalog_admissions_scope_bounded CHECK (
        jsonb_typeof(scope) = 'object'
        AND octet_length(scope::text) <= 16384
    )
);

CREATE INDEX ix_stock_catalog_admissions_lookup ON public.stock_catalog_admissions (artifact, is_fixture, valid_until);

CREATE TABLE public.stock_catalog_listings (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    generation_id BIGINT NOT NULL,
    security_id BIGINT NOT NULL,
    ticker TEXT NOT NULL,
    normalized_ticker TEXT NOT NULL,
    company_name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    listing_exchange TEXT NOT NULL,
    share_class TEXT,
    classification TEXT,
    state TEXT NOT NULL,
    reason TEXT NOT NULL,
    source TEXT NOT NULL,
    row_key TEXT NOT NULL,
    row_digest TEXT NOT NULL,
    evidence_digest TEXT,
    evidence_at TIMESTAMP WITH TIME ZONE,
    valid_until TIMESTAMP WITH TIME ZONE NOT NULL,
    directory_admission_id BIGINT,
    name_admission_id BIGINT,
    classification_admission_id BIGINT,
    provider_asset_id TEXT,
    provider_symbol TEXT,
    provider_evidence_digest TEXT,
    provider_verified_at TIMESTAMP WITH TIME ZONE,
    provider_valid_until TIMESTAMP WITH TIME ZONE,
    provider_admission_id BIGINT,
    unit_evidence_digest TEXT,
    unit_evidence_at TIMESTAMP WITH TIME ZONE,
    currency TEXT,
    units_per_share SMALLINT,
    CONSTRAINT pk_stock_catalog_listings PRIMARY KEY (id),
    CONSTRAINT uq_stock_catalog_listings_generation_id UNIQUE (generation_id, security_id),
    CONSTRAINT uq_stock_catalog_listings_id UNIQUE (id, security_id),
    CONSTRAINT ck_stock_catalog_listings_venue_known CHECK (listing_exchange IN ('NYSE', 'NASDAQ')),
    CONSTRAINT ck_stock_catalog_listings_source_known CHECK (source IN ('nasdaqlisted', 'otherlisted')),
    CONSTRAINT ck_stock_catalog_listings_state_known CHECK (state IN ('active', 'review', 'retired')),
    CONSTRAINT ck_stock_catalog_listings_classification_known CHECK (
        classification IN ('common_stock', 'ordinary_shares', 'out_of_scope') OR classification IS NULL
    ),
    CONSTRAINT ck_stock_catalog_listings_active_evidence CHECK (
        state <> 'active' OR (classification IS NOT NULL
        AND classification IN ('common_stock', 'ordinary_shares')
        AND evidence_digest IS NOT NULL
        AND evidence_at IS NOT NULL)
    ),
    CONSTRAINT ck_stock_catalog_listings_ticker_shape CHECK (
        ticker ~ '^[A-Z0-9][A-Z0-9.$^+/=-]{0,13}$'
        AND normalized_ticker = ticker
    ),
    CONSTRAINT ck_stock_catalog_listings_name_bounds CHECK (
        length(company_name) >= 1
        AND length(company_name) <= 256
        AND length(normalized_name) BETWEEN 1
        AND 512
        AND (share_class IS NULL OR length(share_class) BETWEEN 1
        AND 64)
    ),
    CONSTRAINT ck_stock_catalog_listings_source_shape CHECK (
        length(reason) >= 1
        AND length(reason) <= 128
        AND length(row_key) BETWEEN 1
        AND 128
        AND row_digest ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT ck_stock_catalog_listings_evidence_validity CHECK (
        isfinite(valid_until)
        AND ((evidence_digest IS NULL
        AND evidence_at IS NULL) OR (evidence_digest IS NOT NULL
        AND evidence_at IS NOT NULL
        AND evidence_digest ~ '^[0-9a-f]{64}$'
        AND isfinite(evidence_at)
        AND evidence_at < valid_until))
    ),
    CONSTRAINT ck_stock_catalog_listings_provider_mapping CHECK (
        num_nonnulls(provider_asset_id, provider_symbol, provider_evidence_digest,
                     provider_verified_at, provider_valid_until, provider_admission_id, unit_evidence_digest,
                     unit_evidence_at, currency, units_per_share) = 0
        OR (num_nonnulls(provider_asset_id, provider_symbol, provider_evidence_digest,
                     provider_verified_at, provider_valid_until, provider_admission_id, unit_evidence_digest,
                     unit_evidence_at, currency, units_per_share) = 10
        AND state = 'active'
        AND length(provider_asset_id) BETWEEN 1
        AND 128
        AND provider_symbol ~ '^[A-Z0-9][A-Z0-9.$^+/=-]{0,13}$'
        AND provider_evidence_digest ~ '^[0-9a-f]{64}$'
        AND unit_evidence_digest ~ '^[0-9a-f]{64}$'
        AND isfinite(unit_evidence_at)
        AND isfinite(provider_verified_at)
        AND isfinite(provider_valid_until)
        AND unit_evidence_at <= provider_verified_at
        AND provider_verified_at < provider_valid_until
        AND provider_valid_until <= valid_until
        AND currency = 'USD'
        AND units_per_share = 1)
    ),
    CONSTRAINT fk_stock_catalog_listings_generation_id_stock_catalog_g_59cd FOREIGN KEY(generation_id)
        REFERENCES public.stock_catalog_generations (id),
    CONSTRAINT fk_stock_catalog_listings_security_id_stock_catalog_securities FOREIGN KEY(security_id)
        REFERENCES public.stock_catalog_securities (id),
    CONSTRAINT fk_stock_catalog_listings_directory_admission_id_stock__438a FOREIGN KEY(directory_admission_id)
        REFERENCES public.stock_catalog_admissions (id),
    CONSTRAINT fk_stock_catalog_listings_name_admission_id_stock_catal_3827 FOREIGN KEY(name_admission_id)
        REFERENCES public.stock_catalog_admissions (id),
    CONSTRAINT fk_stock_catalog_listings_classification_admission_id_s_23b5 FOREIGN KEY(classification_admission_id)
        REFERENCES public.stock_catalog_admissions (id),
    CONSTRAINT fk_stock_catalog_listings_provider_admission_id_stock_c_dec3 FOREIGN KEY(provider_admission_id)
        REFERENCES public.stock_catalog_admissions (id)
);

CREATE INDEX ix_stock_catalog_listings_name ON public.stock_catalog_listings (generation_id, normalized_name);

CREATE INDEX ix_stock_catalog_listings_security ON public.stock_catalog_listings (security_id);

CREATE INDEX ix_stock_catalog_listings_ticker ON public.stock_catalog_listings (generation_id, normalized_ticker);

CREATE UNIQUE INDEX uq_stock_catalog_listings_active_ticker
    ON public.stock_catalog_listings (generation_id, listing_exchange, normalized_ticker)
    WHERE state = 'active';

CREATE UNIQUE INDEX uq_stock_catalog_listings_provider_asset
    ON public.stock_catalog_listings (generation_id, provider_asset_id)
    WHERE provider_asset_id IS NOT NULL;

CREATE TABLE public.stock_catalog_aliases (
    id BIGINT GENERATED ALWAYS AS IDENTITY,
    listing_id BIGINT NOT NULL,
    security_id BIGINT NOT NULL,
    namespace TEXT NOT NULL,
    symbol TEXT NOT NULL,
    normalized_symbol TEXT NOT NULL,
    verified_at TIMESTAMP WITH TIME ZONE NOT NULL,
    valid_until TIMESTAMP WITH TIME ZONE NOT NULL,
    CONSTRAINT pk_stock_catalog_aliases PRIMARY KEY (id),
    CONSTRAINT fk_stock_catalog_aliases_listing_id_stock_catalog_listings FOREIGN KEY(listing_id, security_id)
        REFERENCES public.stock_catalog_listings (id, security_id),
    CONSTRAINT uq_stock_catalog_aliases_listing_id UNIQUE (listing_id, namespace, normalized_symbol),
    CONSTRAINT ck_stock_catalog_aliases_namespace_known CHECK (
        namespace IN ('act', 'cqs', 'nasdaq', 'openfigi', 'former')
    ),
    CONSTRAINT ck_stock_catalog_aliases_symbol_shape CHECK (
        symbol ~ '^[A-Z0-9][A-Z0-9.$^+/=-]{0,13}$'
        AND symbol = normalized_symbol
    ),
    CONSTRAINT ck_stock_catalog_aliases_validity CHECK (
        isfinite(verified_at)
        AND isfinite(valid_until)
        AND verified_at < valid_until
    )
);

CREATE INDEX ix_stock_catalog_aliases_symbol ON public.stock_catalog_aliases (normalized_symbol);
