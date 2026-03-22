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

ALTER TABLE runs ADD COLUMN IF NOT EXISTS workflow_id TEXT;
ALTER TABLE runs ADD COLUMN IF NOT EXISTS workflow_version TEXT;
ALTER TABLE runs ADD COLUMN IF NOT EXISTS environment_id TEXT NOT NULL DEFAULT 'dev';

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

CREATE TABLE IF NOT EXISTS workflows (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'default',
    name TEXT NOT NULL,
    workflow_family TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    business_owner TEXT NOT NULL DEFAULT 'acos-team',
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS workflow_versions (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL REFERENCES workflows(id),
    version TEXT NOT NULL,
    lifecycle_state TEXT NOT NULL DEFAULT 'draft',
    change_summary TEXT NOT NULL DEFAULT '',
    validation_status TEXT NOT NULL DEFAULT 'draft',
    input_schema JSONB NOT NULL DEFAULT '{}',
    output_schema JSONB NOT NULL DEFAULT '{}',
    step_definitions JSONB NOT NULL DEFAULT '[]',
    agent_bindings JSONB NOT NULL DEFAULT '[]',
    policy_bindings JSONB NOT NULL DEFAULT '[]',
    created_by TEXT NOT NULL DEFAULT 'system',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    approved_by TEXT DEFAULT NULL,
    approved_at TIMESTAMP DEFAULT NULL,
    UNIQUE(workflow_id, version)
);

CREATE TABLE IF NOT EXISTS workflow_promotions (
    id SERIAL PRIMARY KEY,
    workflow_id TEXT NOT NULL REFERENCES workflows(id),
    version TEXT NOT NULL,
    source_environment TEXT DEFAULT NULL,
    target_environment TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'promoted',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    requested_by TEXT NOT NULL DEFAULT 'system',
    approved_by TEXT NOT NULL DEFAULT 'system',
    note TEXT NOT NULL DEFAULT '',
    promoted_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_events (
    id SERIAL PRIMARY KEY,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    tenant_id TEXT NOT NULL DEFAULT 'default',
    environment_id TEXT NOT NULL DEFAULT 'dev',
    payload JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_runs_tenant ON runs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_runs_customer ON runs(customer_id);
CREATE INDEX IF NOT EXISTS idx_runs_workflow ON runs(workflow_id);
CREATE INDEX IF NOT EXISTS idx_events_run ON events(run_id);
CREATE INDEX IF NOT EXISTS idx_workflows_tenant ON workflows(tenant_id);
CREATE INDEX IF NOT EXISTS idx_workflow_versions_workflow ON workflow_versions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_promotions_lookup ON workflow_promotions(workflow_id, target_environment, is_active);
CREATE INDEX IF NOT EXISTS idx_audit_events_lookup ON audit_events(resource_type, resource_id, created_at);

CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    subsystem TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'healthy',
    calls TEXT NOT NULL DEFAULT '0',
    uptime TEXT NOT NULL DEFAULT '100%',
    skills JSONB NOT NULL DEFAULT '[]',
    grade TEXT NOT NULL DEFAULT 'A+',
    latency TEXT NOT NULL DEFAULT '0ms',
    history JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS skills (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    type TEXT NOT NULL,
    calls TEXT NOT NULL DEFAULT '0',
    code TEXT NOT NULL DEFAULT '',
    "linterWarnings" JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
