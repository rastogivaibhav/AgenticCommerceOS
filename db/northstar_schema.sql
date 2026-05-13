-- ACOS North-Star persistent spine schema
-- Apply after db/schema.sql when using Postgres-backed pilot/production state.

CREATE TABLE IF NOT EXISTS northstar_conversation_sessions (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    primary_channel TEXT NOT NULL,
    channel_identities_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS northstar_channel_identity_index (
    tenant_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    channel_user_id TEXT NOT NULL,
    conversation_session_id TEXT NOT NULL REFERENCES northstar_conversation_sessions(id) ON DELETE CASCADE,
    PRIMARY KEY (tenant_id, channel, channel_user_id)
);

CREATE TABLE IF NOT EXISTS northstar_journeys (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    conversation_session_id TEXT NOT NULL REFERENCES northstar_conversation_sessions(id) ON DELETE CASCADE,
    stage TEXT NOT NULL DEFAULT 'intake',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_northstar_journeys_session_status
    ON northstar_journeys(conversation_session_id, status);

CREATE TABLE IF NOT EXISTS northstar_messages (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    conversation_session_id TEXT REFERENCES northstar_conversation_sessions(id) ON DELETE SET NULL,
    journey_id TEXT REFERENCES northstar_journeys(id) ON DELETE SET NULL,
    channel TEXT NOT NULL,
    channel_user_id TEXT NOT NULL,
    customer_id TEXT,
    correlation_id TEXT NOT NULL,
    text TEXT NOT NULL,
    payload_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_northstar_messages_session
    ON northstar_messages(conversation_session_id, created_at);

CREATE TABLE IF NOT EXISTS northstar_evidence_events (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    conversation_session_id TEXT REFERENCES northstar_conversation_sessions(id) ON DELETE SET NULL,
    journey_id TEXT REFERENCES northstar_journeys(id) ON DELETE SET NULL,
    agent_id TEXT,
    workflow_id TEXT,
    tool_name TEXT,
    policy_verdict TEXT,
    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_northstar_evidence_correlation
    ON northstar_evidence_events(correlation_id, created_at);

CREATE INDEX IF NOT EXISTS idx_northstar_evidence_journey
    ON northstar_evidence_events(journey_id, created_at);

-- Optional RLS posture for enterprise tenants. Enable only after tenant context
-- is consistently applied using app.tenant_id in request transactions.
-- ALTER TABLE northstar_conversation_sessions ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY northstar_sessions_tenant_isolation ON northstar_conversation_sessions
--   USING (tenant_id = current_setting('app.tenant_id', true));


CREATE TABLE IF NOT EXISTS northstar_outbox_events (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    aggregate_id TEXT,
    idempotency_key TEXT UNIQUE,
    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'pending',
    retry_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_northstar_outbox_status_created
    ON northstar_outbox_events(status, created_at);

CREATE TABLE IF NOT EXISTS northstar_replay_runs (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    conversation_session_id TEXT,
    journey_id TEXT,
    correlation_id TEXT NOT NULL,
    request_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    result_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'captured',
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_northstar_replay_tenant_created
    ON northstar_replay_runs(tenant_id, created_at DESC);

CREATE TABLE IF NOT EXISTS northstar_api_keys (
    key_id TEXT PRIMARY KEY,
    key_hash TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    roles TEXT[] NOT NULL DEFAULT ARRAY['viewer'],
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ
);

-- Production RBAC/RLS reference posture. Enable when every request sets
-- `SET LOCAL app.tenant_id = '<tenant>'` in the DB transaction.
-- ALTER TABLE northstar_conversation_sessions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE northstar_journeys ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE northstar_messages ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE northstar_evidence_events ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE northstar_outbox_events ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE northstar_replay_runs ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY northstar_sessions_tenant_isolation ON northstar_conversation_sessions USING (tenant_id = current_setting('app.tenant_id', true));
-- CREATE POLICY northstar_journeys_tenant_isolation ON northstar_journeys USING (tenant_id = current_setting('app.tenant_id', true));
-- CREATE POLICY northstar_messages_tenant_isolation ON northstar_messages USING (tenant_id = current_setting('app.tenant_id', true));
-- CREATE POLICY northstar_evidence_tenant_isolation ON northstar_evidence_events USING (tenant_id = current_setting('app.tenant_id', true));
-- CREATE POLICY northstar_outbox_tenant_isolation ON northstar_outbox_events USING (tenant_id = current_setting('app.tenant_id', true));
-- CREATE POLICY northstar_replay_tenant_isolation ON northstar_replay_runs USING (tenant_id = current_setting('app.tenant_id', true));
