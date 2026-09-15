CREATE TABLE IF NOT EXISTS ingestions (
    id UUID PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    row_count INTEGER NOT NULL DEFAULT 0
);


CREATE TABLE IF NOT EXISTS constituents (
    id BIGSERIAL PRIMARY KEY,

    ingestion_id UUID NOT NULL
        REFERENCES ingestions(id),

    index_code VARCHAR(100) NOT NULL,
    isin VARCHAR(32) NOT NULL,
    ticker VARCHAR(100) NOT NULL,
    name VARCHAR(500) NOT NULL,

    weight NUMERIC(20, 10) NOT NULL,
    shares NUMERIC(30, 10) NOT NULL,

    effective_date DATE NOT NULL,

    deleted_at TIMESTAMPTZ NULL
);


CREATE INDEX IF NOT EXISTS idx_constituents_business_key
ON constituents (
    index_code,
    isin,
    effective_date
);


CREATE INDEX IF NOT EXISTS idx_constituents_export
ON constituents (
    effective_date,
    deleted_at
);


CREATE INDEX IF NOT EXISTS idx_constituents_ingestion
ON constituents (
    ingestion_id
);