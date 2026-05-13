"""ACOS v2 agentic retail estate tables

Revision ID: 20260513_0002
Revises: 20260511_0001
Create Date: 2026-05-13
"""
from __future__ import annotations
from alembic import op

revision = "20260513_0002"
down_revision = "20260511_0001"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("""
    CREATE TABLE IF NOT EXISTS v2_agents (
      id TEXT PRIMARY KEY,
      tenant_id TEXT NOT NULL DEFAULT 'default',
      name TEXT NOT NULL,
      owner_team TEXT NOT NULL,
      vendor_stack TEXT NOT NULL DEFAULT 'internal',
      status TEXT NOT NULL DEFAULT 'draft',
      risk_level TEXT NOT NULL DEFAULT 'medium',
      supported_channels JSONB NOT NULL DEFAULT '[]'::jsonb,
      tools JSONB NOT NULL DEFAULT '[]'::jsonb,
      tone_profile TEXT,
      evaluation_score NUMERIC(5,4) NOT NULL DEFAULT 0,
      cost_budget_per_run NUMERIC(10,4) NOT NULL DEFAULT 0,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS v2_agent_cards (
      agent_id TEXT PRIMARY KEY REFERENCES v2_agents(id) ON DELETE CASCADE,
      card_json JSONB NOT NULL,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS v2_capabilities (
      id TEXT PRIMARY KEY,
      tenant_id TEXT NOT NULL DEFAULT 'default',
      name TEXT NOT NULL,
      owner TEXT NOT NULL,
      risk_level TEXT NOT NULL DEFAULT 'medium',
      intent_families JSONB NOT NULL DEFAULT '[]'::jsonb,
      evaluation_threshold NUMERIC(5,4) NOT NULL DEFAULT 0.85
    );
    CREATE TABLE IF NOT EXISTS v2_agent_capability_mappings (
      tenant_id TEXT NOT NULL DEFAULT 'default',
      agent_id TEXT NOT NULL,
      capability_id TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'active',
      PRIMARY KEY (tenant_id, agent_id, capability_id)
    );
    CREATE TABLE IF NOT EXISTS v2_a2a_traces (
      id TEXT PRIMARY KEY,
      tenant_id TEXT NOT NULL,
      customer_id TEXT,
      channel TEXT NOT NULL,
      actor_type TEXT NOT NULL,
      channel_mode TEXT NOT NULL,
      message TEXT NOT NULL,
      required_capabilities JSONB NOT NULL DEFAULT '[]'::jsonb,
      agents_json JSONB NOT NULL DEFAULT '[]'::jsonb,
      steps_json JSONB NOT NULL DEFAULT '[]'::jsonb,
      tool_trace_json JSONB NOT NULL DEFAULT '[]'::jsonb,
      final_response TEXT,
      cost_estimate NUMERIC(12,4) NOT NULL DEFAULT 0,
      status TEXT NOT NULL DEFAULT 'success',
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_v2_a2a_tenant_created ON v2_a2a_traces(tenant_id, created_at DESC);
    CREATE TABLE IF NOT EXISTS v2_route_to_production (
      tenant_id TEXT NOT NULL DEFAULT 'default',
      agent_id TEXT NOT NULL,
      stage TEXT NOT NULL,
      evidence_json JSONB NOT NULL DEFAULT '{}'::jsonb,
      updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
      PRIMARY KEY (tenant_id, agent_id)
    );
    CREATE TABLE IF NOT EXISTS v2_evaluation_results (
      id TEXT PRIMARY KEY,
      tenant_id TEXT NOT NULL DEFAULT 'default',
      agent_id TEXT NOT NULL,
      score NUMERIC(5,4) NOT NULL,
      threshold NUMERIC(5,4) NOT NULL,
      status TEXT NOT NULL,
      result_json JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS v2_policy_decisions (
      id TEXT PRIMARY KEY,
      tenant_id TEXT NOT NULL DEFAULT 'default',
      actor_id TEXT,
      agent_id TEXT,
      policy_id TEXT NOT NULL,
      verdict TEXT NOT NULL,
      evidence_json JSONB NOT NULL DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS v2_cost_records (
      id TEXT PRIMARY KEY,
      tenant_id TEXT NOT NULL DEFAULT 'default',
      agent_id TEXT,
      run_id TEXT,
      cost_amount NUMERIC(12,6) NOT NULL,
      currency TEXT NOT NULL DEFAULT 'GBP',
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """)

def downgrade() -> None:
    op.execute("""
    DROP TABLE IF EXISTS v2_cost_records;
    DROP TABLE IF EXISTS v2_policy_decisions;
    DROP TABLE IF EXISTS v2_evaluation_results;
    DROP TABLE IF EXISTS v2_route_to_production;
    DROP TABLE IF EXISTS v2_a2a_traces;
    DROP TABLE IF EXISTS v2_agent_capability_mappings;
    DROP TABLE IF EXISTS v2_capabilities;
    DROP TABLE IF EXISTS v2_agent_cards;
    DROP TABLE IF EXISTS v2_agents;
    """)
