-- ACOS Test Data Seed Script
-- Date: 2026-04-15
-- Environment: Development
-- Purpose: Populate test database with seed workflows, agents, skills, channels, tenants for automated testing
-- Run before: Test suite execution
-- Reset: Truncate all tables before re-running

-- Note: This script uses PostgreSQL syntax. Adjust for other databases.

-- ============================================================================
-- CLEAR EXISTING DATA (CAUTION: DESTRUCTIVE)
-- ============================================================================
-- TRUNCATE TABLE workflow_executions CASCADE;
-- TRUNCATE TABLE job_results CASCADE;
-- TRUNCATE TABLE chat_messages CASCADE;
-- TRUNCATE TABLE channel_links CASCADE;
-- TRUNCATE TABLE agent_configs CASCADE;
-- TRUNCATE TABLE skills CASCADE;
-- TRUNCATE TABLE workflow_versions CASCADE;
-- TRUNCATE TABLE workflows CASCADE;
-- TRUNCATE TABLE agents CASCADE;
-- TRUNCATE TABLE channels CASCADE;
-- TRUNCATE TABLE tenants CASCADE;

-- ============================================================================
-- 1. TENANTS (Admin-only management)
-- ============================================================================

INSERT INTO tenants (id, name, domain, status, api_key, user_count, created_at, updated_at)
VALUES
  ('tenant-primary-001', 'Primary Tenant', 'primary.acos.local', 'active', 'pk_live_primary_001_secret', 5, NOW(), NOW()),
  ('tenant-secondary-002', 'Secondary Tenant', 'secondary.acos.local', 'active', 'pk_live_secondary_002_secret', 2, NOW(), NOW()),
  ('tenant-inactive-003', 'Inactive Tenant', 'inactive.acos.local', 'inactive', 'pk_live_inactive_003_secret', 0, NOW() - INTERVAL '30 days', NOW());

-- ============================================================================
-- 2. AGENTS
-- ============================================================================

INSERT INTO agents (id, name, type, description, status, config, created_at, updated_at, tenant_id)
VALUES
  ('agent-ai-claude-001', 'Claude AI Agent', 'ai', 'Claude AI model for workflow automation', 'active',
    '{"model": "claude-3-sonnet", "temperature": 0.7, "max_tokens": 2000}', NOW(), NOW(), 'tenant-primary-001'),

  ('agent-ai-gpt-002', 'GPT-4 Agent', 'ai', 'OpenAI GPT-4 for advanced reasoning', 'active',
    '{"model": "gpt-4", "temperature": 0.5, "max_tokens": 1000}', NOW(), NOW(), 'tenant-primary-001'),

  ('agent-human-support-003', 'Support Team', 'human', 'Human support agent for escalations', 'active',
    '{"team": "support@acos.com", "sla_minutes": 60}', NOW(), NOW(), 'tenant-primary-001'),

  ('agent-human-approver-004', 'Approver Agent', 'human', 'Human approver for workflow promotions', 'active',
    '{"role": "admin", "notification_channel": "slack"}', NOW(), NOW(), 'tenant-primary-001'),

  ('agent-dummy-testing-005', 'Test Dummy Agent', 'ai', 'Dummy agent for testing deletion workflows', 'active',
    '{"is_test": true}', NOW(), NOW(), 'tenant-primary-001');

-- ============================================================================
-- 3. CHANNELS
-- ============================================================================

INSERT INTO channels (id, name, type, status, config, created_at, updated_at, tenant_id)
VALUES
  ('channel-whatsapp-001', 'WhatsApp Business', 'whatsapp', 'not_configured',
    '{"phone_number_id": null, "business_account_id": null}', NOW(), NOW(), 'tenant-primary-001'),

  ('channel-telegram-002', 'Telegram Bot', 'telegram', 'not_configured',
    '{"bot_token": null, "bot_id": null, "verified": false}', NOW(), NOW(), 'tenant-primary-001'),

  ('channel-whatsapp-secondary-003', 'WhatsApp Backup', 'whatsapp', 'not_configured',
    '{"phone_number_id": null, "business_account_id": null}', NOW(), NOW(), 'tenant-secondary-002');

-- ============================================================================
-- 4. SKILLS
-- ============================================================================

INSERT INTO skills (id, name, category, description, implementation, status, created_at, updated_at, tenant_id)
VALUES
  ('skill-send-message-001', 'Send Message', 'communication',
    'Send formatted messages via multiple channels (email, SMS, WhatsApp, Telegram)',
    '{"type": "webhook", "endpoint": "/api/skills/send-message"}', 'active', NOW(), NOW(), 'tenant-primary-001'),

  ('skill-fetch-data-002', 'Fetch Data', 'integration',
    'Retrieve data from external APIs and databases',
    '{"type": "webhook", "endpoint": "/api/skills/fetch-data", "timeout_ms": 5000}', 'active', NOW(), NOW(), 'tenant-primary-001'),

  ('skill-transform-data-003', 'Transform Data', 'data',
    'Transform and normalize data between different formats (JSON, CSV, XML)',
    '{"type": "webhook", "endpoint": "/api/skills/transform-data"}', 'active', NOW(), NOW(), 'tenant-primary-001'),

  ('skill-generate-report-004', 'Generate Report', 'reporting',
    'Generate PDF/Excel reports from workflow data',
    '{"type": "webhook", "endpoint": "/api/skills/generate-report"}', 'active', NOW(), NOW(), 'tenant-primary-001'),

  ('skill-unused-deletion-test-005', 'Unused Skill', 'testing',
    'This skill is unused and created for deletion testing',
    '{"type": "dummy"}', 'inactive', NOW(), NOW(), 'tenant-primary-001');

-- ============================================================================
-- 5. WORKFLOWS
-- ============================================================================

-- Workflow 1: Basic 2-node workflow
INSERT INTO workflows (id, name, family, description, status, version, created_at, updated_at, tenant_id)
VALUES
  ('wf-basic-001', 'Basic Workflow', 'basic-flows', 'Simple trigger-to-action workflow for testing basic functionality',
    'draft', 1, NOW(), NOW(), 'tenant-primary-001');

-- Workflow 2: Multi-step workflow with 5+ nodes
INSERT INTO workflows (id, name, family, description, status, version, created_at, updated_at, tenant_id)
VALUES
  ('wf-multi-002', 'Multi-Step Workflow', 'complex-flows', 'Workflow with multiple sequential steps and decision branches',
    'draft', 1, NOW(), NOW(), 'tenant-primary-001');

-- Workflow 3: Error handling workflow
INSERT INTO workflows (id, name, family, description, status, version, created_at, updated_at, tenant_id)
VALUES
  ('wf-error-003', 'Error Handling Workflow', 'error-flows', 'Workflow designed to test error node handling and recovery',
    'draft', 1, NOW(), NOW(), 'tenant-primary-001');

-- Workflow 4: Channel integration workflow
INSERT INTO workflows (id, name, family, description, status, version, created_at, updated_at, tenant_id)
VALUES
  ('wf-channel-004', 'Channel Integration Workflow', 'channel-flows', 'Workflow that integrates with WhatsApp and Telegram channels',
    'draft', 1, NOW(), NOW(), 'tenant-primary-001');

-- Workflow 5: Empty workflow (no nodes)
INSERT INTO workflows (id, name, family, description, status, version, created_at, updated_at, tenant_id)
VALUES
  ('wf-empty-005', 'Empty Workflow', 'test-flows', 'Empty workflow with no nodes for validation testing',
    'draft', 1, NOW(), NOW(), 'tenant-primary-001');

-- Workflow 6: Production workflow (for promotion testing)
INSERT INTO workflows (id, name, family, description, status, version, created_at, updated_at, tenant_id)
VALUES
  ('wf-prod-006', 'Production Ready Workflow', 'production-flows', 'Fully configured workflow ready for production deployment',
    'approved', 2, NOW() - INTERVAL '7 days', NOW() - INTERVAL '1 day', 'tenant-primary-001');

-- ============================================================================
-- 6. WORKFLOW VERSIONS
-- ============================================================================

INSERT INTO workflow_versions (id, workflow_id, version_number, data, status, created_at, created_by, tenant_id)
VALUES
  ('wv-basic-001-v1', 'wf-basic-001', 1,
    '{"nodes": [{"id": "trigger-1", "type": "trigger"}, {"id": "action-1", "type": "action"}], "connections": [{"from": "trigger-1", "to": "action-1"}]}',
    'draft', NOW(), 'dev-user', 'tenant-primary-001'),

  ('wv-multi-002-v1', 'wf-multi-002', 1,
    '{"nodes": [{"id": "t1", "type": "trigger"}, {"id": "a1", "type": "action"}, {"id": "d1", "type": "decision"}, {"id": "a2", "type": "action"}, {"id": "a3", "type": "action"}], "connections": [{"from": "t1", "to": "a1"}, {"from": "a1", "to": "d1"}, {"from": "d1", "to": "a2"}, {"from": "d1", "to": "a3"}]}',
    'draft', NOW(), 'dev-user', 'tenant-primary-001'),

  ('wv-channel-004-v1', 'wf-channel-004', 1,
    '{"nodes": [{"id": "trigger-msg", "type": "trigger", "channel": "whatsapp"}, {"id": "send-msg", "type": "action", "skill": "send-message"}], "connections": []}',
    'draft', NOW(), 'dev-user', 'tenant-primary-001'),

  ('wv-empty-005-v1', 'wf-empty-005', 1,
    '{"nodes": [], "connections": []}',
    'draft', NOW(), 'dev-user', 'tenant-primary-001'),

  ('wv-prod-006-v1', 'wf-prod-006', 1,
    '{"nodes": [{"id": "t1", "type": "trigger"}], "connections": []}',
    'approved', NOW() - INTERVAL '7 days', 'dev-user', 'tenant-primary-001'),

  ('wv-prod-006-v2', 'wf-prod-006', 2,
    '{"nodes": [{"id": "t1", "type": "trigger"}, {"id": "a1", "type": "action"}], "connections": [{"from": "t1", "to": "a1"}]}',
    'approved', NOW() - INTERVAL '1 day', 'dev-user', 'tenant-primary-001');

-- ============================================================================
-- 7. AGENT CONFIGS (Agents assigned to workflows)
-- ============================================================================

INSERT INTO agent_configs (id, workflow_id, agent_id, role, config, created_at, updated_at, tenant_id)
VALUES
  ('ac-basic-001-claude', 'wf-basic-001', 'agent-ai-claude-001', 'executor', '{}', NOW(), NOW(), 'tenant-primary-001'),
  ('ac-multi-002-claude', 'wf-multi-002', 'agent-ai-claude-001', 'executor', '{}', NOW(), NOW(), 'tenant-primary-001'),
  ('ac-multi-002-human', 'wf-multi-002', 'agent-human-approver-004', 'reviewer', '{}', NOW(), NOW(), 'tenant-primary-001'),
  ('ac-channel-004-claude', 'wf-channel-004', 'agent-ai-claude-001', 'executor', '{}', NOW(), NOW(), 'tenant-primary-001');

-- ============================================================================
-- 8. WORKFLOW EXECUTIONS (Historical data for analytics)
-- ============================================================================

INSERT INTO workflow_executions (id, workflow_id, workflow_version_id, status, input, output, duration_ms, created_at, updated_at, tenant_id)
VALUES
  ('exec-001', 'wf-basic-001', 'wv-basic-001-v1', 'completed', '{"user_id": "123"}', '{"result": "success"}', 245, NOW() - INTERVAL '2 hours', NOW() - INTERVAL '2 hours', 'tenant-primary-001'),
  ('exec-002', 'wf-basic-001', 'wv-basic-001-v1', 'completed', '{"user_id": "124"}', '{"result": "success"}', 312, NOW() - INTERVAL '1.5 hours', NOW() - INTERVAL '1.5 hours', 'tenant-primary-001'),
  ('exec-003', 'wf-basic-001', 'wv-basic-001-v1', 'failed', '{"user_id": "125"}', '{"error": "timeout"}', 5000, NOW() - INTERVAL '1 hour', NOW() - INTERVAL '1 hour', 'tenant-primary-001'),
  ('exec-004', 'wf-multi-002', 'wv-multi-002-v1', 'completed', '{}', '{"branches": "both_executed"}', 1200, NOW() - INTERVAL '30 minutes', NOW() - INTERVAL '30 minutes', 'tenant-primary-001'),
  ('exec-005', 'wf-multi-002', 'wv-multi-002-v1', 'pending', '{}', null, null, NOW() - INTERVAL '5 minutes', NOW() - INTERVAL '5 minutes', 'tenant-primary-001');

-- ============================================================================
-- 9. JOB RESULTS (For async handler testing)
-- ============================================================================

INSERT INTO job_results (id, job_id, status, result, error, created_at, updated_at)
VALUES
  ('jr-001', 'job-async-001', 'completed', '{"output": "success"}', null, NOW() - INTERVAL '1 hour', NOW() - INTERVAL '1 hour'),
  ('jr-002', 'job-async-002', 'failed', null, 'Database connection timeout', NOW() - INTERVAL '30 minutes', NOW() - INTERVAL '30 minutes'),
  ('jr-003', 'job-async-003', 'pending', null, null, NOW() - INTERVAL '2 minutes', NOW() - INTERVAL '2 minutes');

-- ============================================================================
-- 10. CHAT MESSAGES (For chat endpoint testing)
-- ============================================================================

INSERT INTO chat_messages (id, session_id, user_message, assistant_response, created_at, updated_at)
VALUES
  ('msg-001', 'session-001', 'What workflows are available?', 'I found 5 workflows in your tenant...', NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day'),
  ('msg-002', 'session-001', 'Create a new workflow', 'I can help you create a workflow. Please provide...', NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day'),
  ('msg-003', 'session-002', 'Show me analytics', 'Here are your analytics for the last 7 days...', NOW() - INTERVAL '12 hours', NOW() - INTERVAL '12 hours');

-- ============================================================================
-- INDEXES FOR PERFORMANCE (Optional - adjust based on schema)
-- ============================================================================

-- CREATE INDEX idx_workflows_tenant_id ON workflows(tenant_id);
-- CREATE INDEX idx_agents_tenant_id ON agents(tenant_id);
-- CREATE INDEX idx_skills_tenant_id ON skills(tenant_id);
-- CREATE INDEX idx_channels_tenant_id ON channels(tenant_id);
-- CREATE INDEX idx_workflow_executions_status ON workflow_executions(status);
-- CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);

-- ============================================================================
-- VERIFICATION QUERIES (Run after seeding to verify data)
-- ============================================================================

-- Verify data counts
-- SELECT
--   (SELECT COUNT(*) FROM tenants) as tenant_count,
--   (SELECT COUNT(*) FROM workflows) as workflow_count,
--   (SELECT COUNT(*) FROM agents) as agent_count,
--   (SELECT COUNT(*) FROM skills) as skill_count,
--   (SELECT COUNT(*) FROM channels) as channel_count,
--   (SELECT COUNT(*) FROM workflow_versions) as version_count,
--   (SELECT COUNT(*) FROM workflow_executions) as execution_count;

-- Verify workflow status distribution
-- SELECT status, COUNT(*) FROM workflows GROUP BY status;

-- Verify agent types
-- SELECT type, COUNT(*) FROM agents GROUP BY type;

-- Verify channel configurations
-- SELECT type, status, COUNT(*) FROM channels GROUP BY type, status;
