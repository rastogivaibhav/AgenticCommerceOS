"""northstar runtime, RBAC, replay, and outbox tables

Revision ID: 20260511_0001
Revises:
Create Date: 2026-05-11
"""
from __future__ import annotations

from alembic import op

revision = "20260511_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS northstar_conversation_sessions (
            id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            customer_id TEXT NOT NULL,
            primary_channel TEXT NOT NULL,
            channel_identities_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_northstar_sessions_tenant_updated
          ON northstar_conversation_sessions(tenant_id, updated_at DESC);

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
        CREATE INDEX IF NOT EXISTS idx_northstar_journeys_tenant_updated
          ON northstar_journeys(tenant_id, updated_at DESC);

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
        CREATE INDEX IF NOT EXISTS idx_northstar_messages_tenant_created
          ON northstar_messages(tenant_id, created_at DESC);

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
        CREATE INDEX IF NOT EXISTS idx_northstar_evidence_tenant_created
          ON northstar_evidence_events(tenant_id, created_at DESC);

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
        CREATE INDEX IF NOT EXISTS idx_northstar_outbox_tenant_status
          ON northstar_outbox_events(tenant_id, status, created_at);

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
        CREATE INDEX IF NOT EXISTS idx_northstar_replay_correlation
          ON northstar_replay_runs(correlation_id);

        CREATE TABLE IF NOT EXISTS northstar_api_keys (
            key_id TEXT PRIMARY KEY,
            key_hash TEXT NOT NULL,
            tenant_id TEXT NOT NULL,
            roles TEXT[] NOT NULL DEFAULT ARRAY['viewer'],
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            expires_at TIMESTAMPTZ
        );
        CREATE INDEX IF NOT EXISTS idx_northstar_api_keys_tenant
          ON northstar_api_keys(tenant_id, status);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS northstar_api_keys;
        DROP TABLE IF EXISTS northstar_replay_runs;
        DROP TABLE IF EXISTS northstar_outbox_events;
        DROP TABLE IF EXISTS northstar_evidence_events;
        DROP TABLE IF EXISTS northstar_messages;
        DROP TABLE IF EXISTS northstar_journeys;
        DROP TABLE IF EXISTS northstar_channel_identity_index;
        DROP TABLE IF EXISTS northstar_conversation_sessions;
        """
    )
