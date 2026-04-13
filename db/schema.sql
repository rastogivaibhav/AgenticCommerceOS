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
    agent_metadata JSONB NOT NULL DEFAULT '{}',
    skill_metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

ALTER TABLE runs ADD COLUMN IF NOT EXISTS workflow_id TEXT;
ALTER TABLE runs ADD COLUMN IF NOT EXISTS workflow_version TEXT;
ALTER TABLE runs ADD COLUMN IF NOT EXISTS environment_id TEXT NOT NULL DEFAULT 'dev';
ALTER TABLE runs ADD COLUMN IF NOT EXISTS agent_metadata JSONB NOT NULL DEFAULT '{}';
ALTER TABLE runs ADD COLUMN IF NOT EXISTS skill_metadata JSONB NOT NULL DEFAULT '{}';

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

CREATE TABLE IF NOT EXISTS context_sessions (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'default',
    customer_id TEXT NOT NULL DEFAULT 'anon',
    channel TEXT NOT NULL DEFAULT 'journey',
    status TEXT NOT NULL DEFAULT 'active',
    metadata JSONB NOT NULL DEFAULT '{}',
    created_by TEXT NOT NULL DEFAULT 'system',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMP DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS context_events (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES context_sessions(id) ON DELETE CASCADE,
    tenant_id TEXT NOT NULL DEFAULT 'default',
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}',
    actor TEXT NOT NULL DEFAULT 'system',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS context_memory (
    id BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'default',
    customer_id TEXT NOT NULL DEFAULT 'anon',
    memory_key TEXT NOT NULL,
    memory_value JSONB NOT NULL DEFAULT '{}',
    source TEXT NOT NULL DEFAULT 'runtime',
    freshness_score DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    expires_at TIMESTAMP DEFAULT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, customer_id, memory_key)
);

CREATE TABLE IF NOT EXISTS governance_decisions (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'default',
    subject TEXT NOT NULL DEFAULT 'system',
    action TEXT NOT NULL,
    resource TEXT NOT NULL DEFAULT '*',
    decision TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT '',
    policy_source TEXT NOT NULL DEFAULT 'builtin-rbac-v1',
    obligations JSONB NOT NULL DEFAULT '[]',
    context JSONB NOT NULL DEFAULT '{}',
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
CREATE INDEX IF NOT EXISTS idx_context_sessions_tenant_customer ON context_sessions(tenant_id, customer_id, created_at);
CREATE INDEX IF NOT EXISTS idx_context_events_session ON context_events(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_context_memory_lookup ON context_memory(tenant_id, customer_id, updated_at);
CREATE INDEX IF NOT EXISTS idx_governance_decisions_lookup ON governance_decisions(tenant_id, action, created_at);

ALTER TABLE context_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE context_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE context_memory ENABLE ROW LEVEL SECURITY;
ALTER TABLE governance_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE context_sessions FORCE ROW LEVEL SECURITY;
ALTER TABLE context_events FORCE ROW LEVEL SECURITY;
ALTER TABLE context_memory FORCE ROW LEVEL SECURITY;
ALTER TABLE governance_decisions FORCE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'context_sessions'
          AND policyname = 'tenant_isolation_context_sessions'
    ) THEN
        CREATE POLICY tenant_isolation_context_sessions ON context_sessions
            USING (
                current_setting('app.tenant_id', true) IS NULL
                OR tenant_id = current_setting('app.tenant_id', true)
            )
            WITH CHECK (
                current_setting('app.tenant_id', true) IS NULL
                OR tenant_id = current_setting('app.tenant_id', true)
            );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'context_events'
          AND policyname = 'tenant_isolation_context_events'
    ) THEN
        CREATE POLICY tenant_isolation_context_events ON context_events
            USING (
                current_setting('app.tenant_id', true) IS NULL
                OR tenant_id = current_setting('app.tenant_id', true)
            )
            WITH CHECK (
                current_setting('app.tenant_id', true) IS NULL
                OR tenant_id = current_setting('app.tenant_id', true)
            );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'context_memory'
          AND policyname = 'tenant_isolation_context_memory'
    ) THEN
        CREATE POLICY tenant_isolation_context_memory ON context_memory
            USING (
                current_setting('app.tenant_id', true) IS NULL
                OR tenant_id = current_setting('app.tenant_id', true)
            )
            WITH CHECK (
                current_setting('app.tenant_id', true) IS NULL
                OR tenant_id = current_setting('app.tenant_id', true)
            );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'governance_decisions'
          AND policyname = 'tenant_isolation_governance_decisions'
    ) THEN
        CREATE POLICY tenant_isolation_governance_decisions ON governance_decisions
            USING (
                current_setting('app.tenant_id', true) IS NULL
                OR tenant_id = current_setting('app.tenant_id', true)
            )
            WITH CHECK (
                current_setting('app.tenant_id', true) IS NULL
                OR tenant_id = current_setting('app.tenant_id', true)
            );
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    tenant_id TEXT NOT NULL DEFAULT 'default',
    items JSONB NOT NULL DEFAULT '[]',
    total DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'placed',
    placed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    shipped_at TIMESTAMP DEFAULT NULL,
    delivered_at TIMESTAMP DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);

CREATE TABLE IF NOT EXISTS loyalty_points (
    customer_id TEXT PRIMARY KEY,
    points INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tenants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    tax_rate DOUBLE PRECISION NOT NULL DEFAULT 0.08,
    promo_rules JSONB NOT NULL DEFAULT '{}',
    features JSONB NOT NULL DEFAULT '{}',
    connector_routes JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

ALTER TABLE tenants ADD COLUMN IF NOT EXISTS connector_routes JSONB NOT NULL DEFAULT '{}';

CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    subsystem TEXT NOT NULL,
    purpose TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'healthy',
    calls TEXT NOT NULL DEFAULT '0',
    uptime TEXT NOT NULL DEFAULT '100%',
    skills JSONB NOT NULL DEFAULT '[]',
    bound_skills JSONB NOT NULL DEFAULT '[]',
    connector_bindings JSONB NOT NULL DEFAULT '[]',
    used_by_workflow_ids JSONB NOT NULL DEFAULT '[]',
    runtime_provider TEXT NOT NULL DEFAULT 'local_fallback',
    model_name TEXT NOT NULL DEFAULT 'gemini-2.0-flash',
    agent_version TEXT NOT NULL DEFAULT 'v1',
    grade TEXT NOT NULL DEFAULT 'A+',
    latency TEXT NOT NULL DEFAULT '0ms',
    last_test_at TIMESTAMP DEFAULT NULL,
    last_test_status TEXT NOT NULL DEFAULT 'unknown',
    code JSONB NOT NULL DEFAULT '{}',
    scorecard JSONB NOT NULL DEFAULT '{}',
    history JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

ALTER TABLE agents ADD COLUMN IF NOT EXISTS bound_skills JSONB NOT NULL DEFAULT '[]';
ALTER TABLE agents ADD COLUMN IF NOT EXISTS purpose TEXT NOT NULL DEFAULT '';
ALTER TABLE agents ADD COLUMN IF NOT EXISTS connector_bindings JSONB NOT NULL DEFAULT '[]';
ALTER TABLE agents ADD COLUMN IF NOT EXISTS used_by_workflow_ids JSONB NOT NULL DEFAULT '[]';
ALTER TABLE agents ADD COLUMN IF NOT EXISTS runtime_provider TEXT NOT NULL DEFAULT 'local_fallback';
ALTER TABLE agents ADD COLUMN IF NOT EXISTS model_name TEXT NOT NULL DEFAULT 'gemini-2.0-flash';
ALTER TABLE agents ADD COLUMN IF NOT EXISTS agent_version TEXT NOT NULL DEFAULT 'v1';
ALTER TABLE agents ADD COLUMN IF NOT EXISTS last_test_at TIMESTAMP DEFAULT NULL;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS last_test_status TEXT NOT NULL DEFAULT 'unknown';
ALTER TABLE agents ADD COLUMN IF NOT EXISTS code JSONB NOT NULL DEFAULT '{}';
ALTER TABLE agents ADD COLUMN IF NOT EXISTS scorecard JSONB NOT NULL DEFAULT '{}';

CREATE TABLE IF NOT EXISTS channel_bindings (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    tenant_id TEXT NOT NULL DEFAULT 'default',
    environment TEXT NOT NULL DEFAULT 'dev',
    status TEXT NOT NULL DEFAULT 'sandbox',
    mode TEXT NOT NULL DEFAULT 'sandbox',
    identity TEXT NOT NULL DEFAULT '',
    default_route TEXT NOT NULL DEFAULT 'order_status',
    allowed_routes JSONB NOT NULL DEFAULT '[]',
    notification_targets JSONB NOT NULL DEFAULT '[]',
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS channel_senders (
    id TEXT PRIMARY KEY,
    channel_binding_id TEXT NOT NULL REFERENCES channel_bindings(id),
    sender_external_id TEXT NOT NULL,
    display_name TEXT NOT NULL DEFAULT '',
    customer_id TEXT DEFAULT NULL,
    approval_status TEXT NOT NULL DEFAULT 'pending',
    last_message TEXT NOT NULL DEFAULT '',
    last_seen_at TIMESTAMP NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(channel_binding_id, sender_external_id)
);

CREATE TABLE IF NOT EXISTS channel_pairings (
    id TEXT PRIMARY KEY,
    channel_binding_id TEXT NOT NULL REFERENCES channel_bindings(id),
    route_id TEXT NOT NULL,
    pair_code TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'active',
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT NULL,
    used_at TIMESTAMP DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS demo_routes (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    workflow_id TEXT NOT NULL DEFAULT '',
    workflow_family TEXT NOT NULL DEFAULT 'service',
    supported_channels JSONB NOT NULL DEFAULT '[]',
    sample_trigger TEXT NOT NULL DEFAULT '',
    systems JSONB NOT NULL DEFAULT '[]',
    preferred_runtime TEXT NOT NULL DEFAULT 'local_fallback',
    mode TEXT NOT NULL DEFAULT 'sandbox',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS crm_customers (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'default',
    name TEXT NOT NULL,
    email TEXT NOT NULL DEFAULT '',
    phone TEXT NOT NULL DEFAULT '',
    loyalty_tier TEXT NOT NULL DEFAULT 'standard',
    preferred_channel TEXT NOT NULL DEFAULT 'whatsapp',
    salesforce_contact_id TEXT NOT NULL DEFAULT '',
    shopify_customer_id TEXT NOT NULL DEFAULT '',
    last_order_id TEXT NOT NULL DEFAULT '',
    segment TEXT NOT NULL DEFAULT 'general',
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS crm_cases (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES crm_customers(id),
    tenant_id TEXT NOT NULL DEFAULT 'default',
    subject TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    priority TEXT NOT NULL DEFAULT 'medium',
    channel TEXT NOT NULL DEFAULT 'whatsapp',
    summary TEXT NOT NULL DEFAULT '',
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_channel_bindings_tenant ON channel_bindings(tenant_id, environment);
CREATE INDEX IF NOT EXISTS idx_channel_senders_lookup ON channel_senders(channel_binding_id, approval_status, last_seen_at);
CREATE INDEX IF NOT EXISTS idx_channel_pairings_lookup ON channel_pairings(channel_binding_id, status, created_at);
CREATE INDEX IF NOT EXISTS idx_demo_routes_workflow ON demo_routes(workflow_id);
CREATE INDEX IF NOT EXISTS idx_crm_customers_tenant ON crm_customers(tenant_id);
CREATE INDEX IF NOT EXISTS idx_crm_cases_customer ON crm_cases(customer_id, created_at);

CREATE TABLE IF NOT EXISTS skills (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    type TEXT NOT NULL,
    calls TEXT NOT NULL DEFAULT '0',
    code TEXT NOT NULL DEFAULT '',
    "linterWarnings" JSONB NOT NULL DEFAULT '[]',
    input_schema JSONB NOT NULL DEFAULT '{}',
    output_schema JSONB NOT NULL DEFAULT '{}',
    execution_mode TEXT NOT NULL DEFAULT 'local',
    timeout_seconds INTEGER NOT NULL DEFAULT 15,
    retries INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

ALTER TABLE skills ADD COLUMN IF NOT EXISTS input_schema JSONB NOT NULL DEFAULT '{}';
ALTER TABLE skills ADD COLUMN IF NOT EXISTS output_schema JSONB NOT NULL DEFAULT '{}';
ALTER TABLE skills ADD COLUMN IF NOT EXISTS execution_mode TEXT NOT NULL DEFAULT 'local';
ALTER TABLE skills ADD COLUMN IF NOT EXISTS timeout_seconds INTEGER NOT NULL DEFAULT 15;
ALTER TABLE skills ADD COLUMN IF NOT EXISTS retries INTEGER NOT NULL DEFAULT 0;

CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    base_price DOUBLE PRECISION NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    tags JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
