CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'default',
    customer_id TEXT NOT NULL DEFAULT 'anon',
    journey TEXT NOT NULL,
    input JSONB NOT NULL DEFAULT '{}',
    output JSONB NOT NULL DEFAULT '{}',
    cost DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    variant TEXT DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(id),
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS experiments (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    variant_a JSONB NOT NULL DEFAULT '{}',
    variant_b JSONB NOT NULL DEFAULT '{}',
    winner TEXT DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_runs_tenant ON runs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_runs_customer ON runs(customer_id);
CREATE INDEX IF NOT EXISTS idx_events_run ON events(run_id);