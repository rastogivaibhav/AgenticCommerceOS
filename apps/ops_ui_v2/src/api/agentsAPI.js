import { apiJson } from './client';

export async function listAgents() {
  return apiJson('/api/v1/agents');
}

export async function getAgent(agentId) {
  return apiJson(`/api/v1/agents/${agentId}`);
}

export async function createAgent(payload) {
  return apiJson('/api/v1/agents', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function testAgent(agentId, payload) {
  return apiJson(`/api/v1/agents/${agentId}/test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}
