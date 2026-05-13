"""ACOS v2 production backbone tables

Revision ID: 20260513_0003
Revises: 20260513_0002
Create Date: 2026-05-13
"""
from __future__ import annotations
from alembic import op

revision = "20260513_0003"
down_revision = "20260513_0002"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("""
    CREATE TABLE IF NOT EXISTS v2_agent_versions (
      id TEXT PRIMARY KEY,
      tenant_id TEXT NOT NULL DEFAULT 'default',
      agent_id TEXT NOT NULL,
      version TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'draft',
      payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS v2_a2a_tasks (
      id TEXT PRIMARY KEY,
      tenant_id TEXT NOT NULL DEFAULT 'default',
      trace_id TEXT,
      agent_id TEXT,
      capability_id TEXT,
      status TEXT NOT NULL,
      request_json JSONB NOT NULL DEFAULT '{}'::jsonb,
      response_json JSONB NOT NULL DEFAULT '{}'::jsonb,
      error TEXT,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_v2_a2a_tasks_trace ON v2_a2a_tasks(trace_id);
    CREATE TABLE IF NOT EXISTS v2_tools (
      id TEXT PRIMARY KEY,
      tenant_id TEXT NOT NULL DEFAULT 'default',
      payload_json JSONB NOT NULL,
      status TEXT NOT NULL DEFAULT 'active',
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS v2_mcp_servers (
      id TEXT PRIMARY KEY,
      tenant_id TEXT NOT NULL DEFAULT 'default',
      payload_json JSONB NOT NULL,
      status TEXT NOT NULL DEFAULT 'active',
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS v2_memory_records (
      id TEXT PRIMARY KEY,
      tenant_id TEXT NOT NULL DEFAULT 'default',
      scope TEXT NOT NULL,
      subject_id TEXT NOT NULL,
      payload_json JSONB NOT NULL,
      data_classification TEXT NOT NULL DEFAULT 'internal',
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS v2_memory_access_events (
      id TEXT PRIMARY KEY,
      tenant_id TEXT NOT NULL DEFAULT 'default',
      actor_id TEXT,
      scope TEXT NOT NULL,
      subject_id TEXT,
      purpose TEXT,
      verdict TEXT NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS v2_evaluation_sets (
      id TEXT PRIMARY KEY,
      tenant_id TEXT NOT NULL DEFAULT 'default',
      payload_json JSONB NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS v2_evaluation_runs (
      id TEXT PRIMARY KEY,
      tenant_id TEXT NOT NULL DEFAULT 'default',
      agent_id TEXT,
      status TEXT NOT NULL,
      score NUMERIC(5,4),
      result_json JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS v2_approval_requests (
      id TEXT PRIMARY KEY,
      tenant_id TEXT NOT NULL DEFAULT 'default',
      agent_id TEXT,
      version_id TEXT,
      status TEXT NOT NULL,
      evidence_json JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS v2_vendor_agents (
      id TEXT PRIMARY KEY,
      tenant_id TEXT NOT NULL DEFAULT 'default',
      payload_json JSONB NOT NULL,
      enabled BOOLEAN NOT NULL DEFAULT TRUE,
      kill_switch BOOLEAN NOT NULL DEFAULT FALSE,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """)

def downgrade() -> None:
    op.execute("""
    DROP TABLE IF EXISTS v2_vendor_agents;
    DROP TABLE IF EXISTS v2_approval_requests;
    DROP TABLE IF EXISTS v2_evaluation_runs;
    DROP TABLE IF EXISTS v2_evaluation_sets;
    DROP TABLE IF EXISTS v2_memory_access_events;
    DROP TABLE IF EXISTS v2_memory_records;
    DROP TABLE IF EXISTS v2_mcp_servers;
    DROP TABLE IF EXISTS v2_tools;
    DROP TABLE IF EXISTS v2_a2a_tasks;
    DROP TABLE IF EXISTS v2_agent_versions;
    """)
